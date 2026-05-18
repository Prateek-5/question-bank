# Eager load vs JOIN vs batched select-IN — pick the right strategy

## Source / Origin
- The natural follow-up to "fix this N+1." Differentiates senior from mid candidates.
- Concept reference: `backend-data-prep/orm/01-orm-internals.md` (Eager loading strategies under the hood).

## Why this question matters in interviews
"How would you fix this N+1?" is the gateway. The discriminator is **which fix and why**. Mid-level candidates answer "add eager loading" and move on. Senior candidates know that eager-loading is a category with **three concrete implementations** (JOIN, select-IN, subquery), and the right pick depends on **cardinality, child set size, indexing, and access pattern**. Picking the wrong strategy can make the "fix" slower than the bug.

## Concepts involved

### Three fetch strategies and their SQL signatures

```sql
-- Strategy 1: JOIN-based eager (TypeORM default, Hibernate JOIN FETCH, Django select_related)
SELECT u.*, o.*
FROM   users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE  u.active = true;

-- Strategy 2: select-IN / batched (Prisma default, SQLAlchemy selectinload, Hibernate @BatchSize, Django prefetch_related)
SELECT * FROM users WHERE active = true;                       -- query 1
SELECT * FROM orders WHERE user_id IN (1, 2, 3, ..., 250);     -- query 2 (chunked if >IN-limit)

-- Strategy 3: subquery-based (Hibernate @Fetch(SUBSELECT))
SELECT * FROM users WHERE active = true;
SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE active = true);
```

### Syntax across ORMs

```typescript
// TypeORM — JOIN-based (one query, cartesian risk)
userRepo.find({ relations: { orders: true } });

// TypeORM — manual select-IN via QueryBuilder + custom mapping (no built-in)
const users = await userRepo.find();
const orders = await orderRepo.find({ where: { userId: In(users.map(u => u.id)) } });

// Prisma — select-IN by design
prisma.user.findMany({ include: { orders: true } });

// SQLAlchemy — explicit choice
from sqlalchemy.orm import joinedload, selectinload
session.scalars(select(User).options(joinedload(User.orders)))       // JOIN
session.scalars(select(User).options(selectinload(User.orders)))     // select-IN

// Hibernate — JPQL
"SELECT u FROM User u JOIN FETCH u.orders WHERE u.active = true"      // JOIN
@OneToMany @BatchSize(size=50)                                        // batched (similar to select-IN)

// Django
User.objects.select_related('profile')        // JOIN (only for FK / OneToOne)
User.objects.prefetch_related('orders')       // separate query, IN clause
```

### Edge cases / interview traps

1. **Cartesian explosion on JOIN.** 1 user × 50 orders × 5 addresses = 250 rows for 1 user. Bandwidth, hydration cost, and ORM dedupe overhead grow multiplicatively.
2. **`IN` clause size limits.** Postgres handles ~32k easily; older Oracle capped at 1000; some drivers fail past 65k parameters. Real ORMs chunk automatically; verify yours does.
3. **`LIMIT` + JOIN don't compose intuitively.** `find({ relations: { orders }, take: 10 })` in TypeORM does *not* mean "10 users with all their orders" — it means "first 10 rows of the JOIN result." You must use `take` with `relationLoadStrategy: 'query'` (select-IN) or apply `DISTINCT` carefully.
4. **`ORDER BY` on the child collection.** JOIN-based eager can't easily limit "top 5 orders per user" — that's a `LATERAL JOIN` or window function. Select-IN can: a separate query per parent, or one query with `ROW_NUMBER()` partitioning.
5. **Nullable LEFT JOIN.** Users with zero orders still produce one row with NULL order columns; the ORM must filter these during hydration.
6. **JOIN over many-to-many.** Goes through the link table; you JOIN three tables; cartesian risk is even worse.
7. **Index requirements.** Select-IN's child query needs an index on `(user_id)`; without it, you do a seq scan per IN list.

## Mental Model

```
   Cardinality of relation:
   ─────────────────────────

         1:1 / many-to-one              one-to-many               many-to-many
         ────────────────────           ───────────                ───────────────

   Best   JOIN                          select-IN                  select-IN via link
   pick:  (no row explosion;            (avoids cartesian;         (3 tables would blow
          1 child per parent)            2 queries always)          up cartesian)

   Why:   parent row + 1 child         parent rows + N children   parents + link rows
          per parent. JOIN is          fan out → JOIN multiplies   + leaf rows
          natural.                     rows.

   ASCII:
                                                                     users
            users                          users                       │
              │                              │                     link_table
            JOIN                            \│/                        │
              │                          orders (IN ids)             tags
           profile

   Round    1 query                       2 queries                  2-3 queries
   trips:
```

The Prisma team's stance: select-IN is the safer default; JOIN is an optimization for narrow cases (1:1 or known-tiny children).

## Why interviewers care

- Tests the **next level beyond "eager loading fixes N+1"** — you must know the *kind* of eager loading.
- Tests **bandwidth thinking**: 100MB of duplicated user columns over a JOIN is a real prod issue.
- Tests **knowing each ORM's defaults**: Prisma select-IN; TypeORM JOIN; Hibernate JOIN unless `@BatchSize`; Django `prefetch_related` vs `select_related`.

## Common beginner confusion

- **"One query is always better than two."** False. A single JOIN that ships 100MB of duplicated parent columns is worse than two queries shipping 10MB.
- **"`select_related` and `prefetch_related` are the same."** No — `select_related` is JOIN (FK / one-to-one only); `prefetch_related` is separate query (any relation type, including many-to-many).
- **"Subquery fetch is just a fancier select-IN."** Similar shape, but pushes the IDs filter into the DB rather than serializing them in the IN clause. Useful for huge ID lists where the IN clause becomes a parameter-count problem.
- **"Always eager-load."** Eager-loading 8 relations when only 1 is needed wastes bandwidth and hydration cost. Pick based on the endpoint.
- **"JOIN is faster because the DB can optimize."** The DB *can*, but JOIN forces row-multiplication; the optimizer can't avoid that. Two queries with proper indexes are often faster end-to-end.

## Brute force approach

Default to JOIN-based eager loading everywhere. Watch endpoints break under load when a popular user accumulates 10k orders and the JOIN ships 500k rows. Migrate hot endpoints to raw SQL.

## Optimal approach

Decision tree:

1. **Is it 1:1 or many-to-one?** → JOIN. Single child row per parent; no explosion.
2. **Is it one-to-many or many-to-many?** → Select-IN unless child count per parent is tiny and bounded.
3. **Do you need only counts/sums, not rows?** → Aggregate SQL with `GROUP BY` (no children loaded).
4. **Are calls scattered across resolvers (GraphQL)?** → DataLoader on top of select-IN.
5. **Is the relation rarely accessed?** → Stay lazy; eager loading would waste effort.
6. **Top-N per parent (e.g., last 5 orders per user)?** → Window function + `ROW_NUMBER() OVER (PARTITION BY user_id)` in raw SQL, or select-IN with per-parent sub-LIMIT (Prisma supports `take` inside `include`).

## Solution

```typescript
// ============================================================
// Scenario A: 1:1 — JOIN wins
// ============================================================
// 1000 users, each with 1 profile row.
const usersWithProfile = await prisma.user.findMany({
  where: { active: true },
  include: { profile: true },
});
// SQL: SELECT u.*, p.* FROM "User" u LEFT JOIN "Profile" p ON p."userId" = u.id;
// 1 round trip, no cartesian (1:1).

// ============================================================
// Scenario B: one-to-many w/ small bounded children — JOIN OK
// ============================================================
// Users with their 1-2 active subscriptions (small bounded set).
const usersWithSubs = await userRepo
  .createQueryBuilder('u')
  .leftJoinAndSelect('u.subscriptions', 's', "s.status = 'ACTIVE'")
  .where('u.active = true')
  .getMany();

// ============================================================
// Scenario C: one-to-many w/ large children — select-IN wins
// ============================================================
// Users with their orders (could be 1000s each).
const users = await prisma.user.findMany({
  where: { active: true },
  include: {
    orders: { where: { status: 'PAID' }, orderBy: { createdAt: 'desc' }, take: 10 },
  },
});
// SQL (2 queries):
//   SELECT * FROM "User" WHERE active = true;
//   SELECT * FROM "Order" WHERE "userId" IN (...) AND status = 'PAID' ORDER BY ... ;
// Prisma takes care of the per-user TAKE via a smart query.

// ============================================================
// Scenario D: only counts needed — aggregate SQL
// ============================================================
const counts = await ds.query(`
  SELECT u.id, u.email, COUNT(o.id) AS order_count
  FROM   users u
  LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'PAID'
  WHERE  u.active = true
  GROUP BY u.id, u.email;
`);
// No child rows shipped; just the count. Fastest path when rows aren't needed.

// ============================================================
// Scenario E: top-N per parent — LATERAL JOIN (Postgres)
// ============================================================
const top5OrdersPerUser = await ds.query(`
  SELECT u.id, u.email, o.id AS order_id, o.total
  FROM   users u
  LEFT JOIN LATERAL (
    SELECT id, total FROM orders WHERE user_id = u.id
    ORDER BY created_at DESC LIMIT 5
  ) o ON true
  WHERE u.active = true;
`);
```

## Step-by-step dry run

Workload: 4 active users, each with 100 orders. We need the user list + all their orders.

### Path 1: JOIN
```
SELECT u.*, o.*
FROM users u LEFT JOIN orders o ON o.user_id = u.id;
```
- Rows shipped: 4 × 100 = **400 rows**, each duplicating the user columns.
- Bandwidth: if user row is 1KB and order row is 0.5KB, total = 400 × 1.5KB = **600 KB**.
- Hydration: ORM iterates 400 rows, dedupes users into 4 objects, attaches 100 orders each.

### Path 2: select-IN
```
SELECT * FROM users WHERE active = true;        -- 4 rows × 1KB = 4 KB
SELECT * FROM orders WHERE user_id IN (1,2,3,4); -- 400 rows × 0.5KB = 200 KB
```
- Rows shipped: 4 + 400 = **404 rows**, no duplication.
- Bandwidth: 4 + 200 = **204 KB** (3x cheaper than JOIN).
- Hydration: simpler — no dedupe needed.
- Round trips: 2 vs 1.

### Verdict
JOIN ships 3x more bytes despite 1 less round trip. On a 1ms RTT, JOIN saves 1ms but pays 400KB of wire time (~1ms extra at 1Gbps). On slow networks, **bytes matter more than round trips**.

Same workload, but each user has 2 orders:
- JOIN ships 4 × 2 = 8 rows × 1.5KB = **12 KB**. Cheap.
- Select-IN ships 4 + 8 rows = **8 KB**. Marginal win.
- JOIN wins here on round trips because rows are few.

### General rule
**Crossover**: when child count per parent exceeds ~5-10, select-IN wins on total bytes. Below that, JOIN wins on round trips.

## How to think aloud in the interview

> "I treat 'eager loading' as a family with three concrete strategies, picked by relationship shape:
>
> - **JOIN** for many-to-one and 1:1 — one query, no row explosion because each parent has one child row.
> - **Select-IN** for one-to-many and many-to-many — two queries, but no cartesian explosion. Prisma uses this by default; SQLAlchemy via `selectinload`; Django via `prefetch_related`.
> - **Subquery / batched fetch** when the parent ID list is huge — push the filter into a subquery rather than serialize an IN list of 50k params.
>
> The discriminator is **child set size**. A user with 1 profile? JOIN. A user with 10k orders? Select-IN. The same code path can flip from 'fast' to 'cartesian death' depending on which user you query.
>
> I also keep a few non-eager options on the table: aggregate-only SQL when rows aren't needed (just `COUNT`), `LATERAL JOIN` for top-N per parent, DataLoader for cross-resolver batching in GraphQL. The fix isn't always 'eager-load harder.'"

## Important takeaways

- "Eager loading" is not one thing — it's at least three strategies: JOIN, select-IN, subquery.
- JOIN wins for 1:1 and many-to-one; select-IN wins for one-to-many and many-to-many.
- Bytes shipped matters more than round trips when child counts are large (cartesian explosion).
- Defaults differ by ORM — Prisma select-IN, TypeORM JOIN, Django explicit per call, Hibernate JOIN unless `@BatchSize`.
- `LIMIT` and `ORDER BY` over JOIN-eager are footguns; select-IN or window functions handle them cleanly.
- For aggregates, skip eager loading entirely — use `GROUP BY` SQL.

## Variants

1. **`LATERAL JOIN` for top-N per parent.** Postgres-specific; cleanly fetches last 5 orders per user in a single query.
2. **Materialized views for stable read shapes.** Pre-join in the DB; refresh on schedule.
3. **Hibernate `@Fetch(SUBSELECT)`** — selects children via a subquery rather than `IN (...)`; useful when parent ID list is huge.
4. **`@BatchSize(size=50)`** — Hibernate's "fetch N parents' children at a time" mode; sits between lazy and select-IN.
5. **DataLoader with cache** — batches *and* deduplicates per request; classic GraphQL solution.
6. **Two-phase rendering** — fetch parents, render skeleton, async-fetch children. Useful for huge lists where partial render is acceptable.

## Revision notes

> **eager-load-vs-join-vs-batch — 60 second recap**
> - Three strategies: JOIN, select-IN, subquery — pick by relationship cardinality.
> - JOIN: best for 1:1 and many-to-one. Risk: cartesian on one-to-many.
> - Select-IN: best for one-to-many and many-to-many. 2 queries, no row blow-up.
> - Prisma → select-IN default; TypeORM → JOIN default; Django → explicit; Hibernate → JOIN unless `@BatchSize`.
> - Bytes shipped vs round trips: bytes win for large child sets.
> - `LIMIT`/`ORDER BY` over JOIN-eager doesn't compose cleanly. Use select-IN or `LATERAL JOIN`.
> - Counts-only? Skip eager loading, use `GROUP BY` aggregate SQL.
