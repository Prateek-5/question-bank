# Detect and fix the N+1 query problem

## Source / Origin
- The #1 ORM interview question across Node, Java, Python, Ruby shops.
- Concept reference: `backend-data-prep/orm/01-orm-internals.md` (N+1 section), `02-orm-comparison.md` (per-ORM fixes).
- Real-world: 70% of "why is my endpoint slow?" production tickets reduce to N+1.

## Why this question matters in interviews
N+1 is the single most-asked ORM question because it instantly reveals whether a candidate has ever **read the SQL their ORM emitted**. Juniors describe it abstractly ("too many queries"). Mid-levels can spot it in code. Seniors can:
1. Name the three canonical fixes (eager JOIN, batched select-IN, DataLoader).
2. Pick between them based on relationship cardinality and access pattern.
3. Predict the exact SQL emitted and the cartesian-row-blowup risk.
4. Show how they'd *prevent* it (per-request query budget, dev-mode middleware).

If you stumble here, the interviewer assumes you've never owned production.

## Concepts involved

### Syntax to lock in

```javascript
// TypeORM — the bug
const users = await userRepo.find();             // 1 SELECT users
for (const u of users) {
  console.log(u.orders.length);                  // lazy proxy → N SELECTs
}

// TypeORM — fix #1: eager JOIN
const users = await userRepo.find({ relations: { orders: true } });  // 1 query, LEFT JOIN

// Prisma — fix #2: select-IN (the default strategy)
const users = await prisma.user.findMany({ include: { orders: true } });
// Emits: SELECT users; SELECT orders WHERE user_id IN (...)  → 2 queries total

// Sequelize — fix #3: batched manual fetch
const users = await User.findAll();
const orders = await Order.findAll({ where: { userId: users.map(u => u.id) } });
const byUser = groupBy(orders, 'userId');
```

### The exact SQL emitted

```sql
-- N+1 path (4 users):
SELECT id, email, name FROM users;
SELECT id, user_id, total FROM orders WHERE user_id = 1;
SELECT id, user_id, total FROM orders WHERE user_id = 2;
SELECT id, user_id, total FROM orders WHERE user_id = 3;
SELECT id, user_id, total FROM orders WHERE user_id = 4;
-- Total: 5 round trips, 5x planner overhead

-- Eager JOIN path:
SELECT u.id, u.email, u.name, o.id, o.user_id, o.total
FROM   users u
LEFT JOIN orders o ON o.user_id = u.id;
-- 1 round trip, but cartesian risk: 4 users × avg 25 orders = 100 rows shipped

-- Select-IN path:
SELECT id, email, name FROM users;
SELECT id, user_id, total FROM orders WHERE user_id IN (1,2,3,4);
-- 2 round trips, no cartesian explosion
```

### Edge cases / interview traps

1. **N+1 hides behind serializers.** `JSON.stringify(user)` or a `@Expose()` decorator can trigger lazy property access. The N+1 happens in your response serializer, not your controller.
2. **GraphQL is N+1 by design.** Each nested resolver fires its own DB call. Without DataLoader you get N+1+N+1+... at every level.
3. **Cartesian explosion.** A user with 50 orders and 5 addresses joined together produces 250 rows. Multi-relation JOINs are not the cheap fix juniors think.
4. **`Promise.all` doesn't fix N+1.** It just runs the N queries concurrently. The DB still does N planner runs and the pool still gets N connections.
5. **Eager-by-default is also a trap.** Loading 8 relations every time wastes bandwidth when most endpoints need only 1.
6. **Counts via N+1.** `users.map(u => u.orders.length)` triggers loads just to call `.length`. Use `loadRelationCountAndMap` (TypeORM) or `_count` (Prisma) instead.
7. **Polymorphic relations** (Rails `polymorphic: true`, TypeORM single-table inheritance) — eager loading is much harder; sometimes you must batch fetch per type.

## Mental Model

Think of the kitchen-order analogy:

```
   N+1                        Eager JOIN                  Select-IN
   ───                        ──────────                  ─────────

   ┌────┐                     ┌────────────┐              ┌────┐
   │User│ ──────► DB          │User+Orders │ ──► DB       │User│ ─► DB
   └────┘                     └────────────┘              └────┘
   ┌────┐                                                 ┌────┐
   │Ord1│ ──────► DB           1 round trip               │Ord │ ─► DB (IN clause)
   └────┘                      But row explosion          └────┘
   ┌────┐                      possible                    2 round trips
   │Ord2│ ──────► DB                                       Clean row count
   └────┘
   ┌────┐
   │Ord3│ ──────► DB
   └────┘
   ...

   N+1 round trips           1 round trip                 2 round trips
   Low row count             Cartesian × children         Linear row count
```

The mental shortcut: **the number of SQL statements should be a small constant in the number of entity types involved, not in the number of rows.**

## Why interviewers care

- It tests whether you read **generated SQL**, not just call ORM methods.
- It tests **trade-off thinking**: eager-JOIN vs select-IN vs DataLoader vs raw SQL are all "correct," each wrong for some workload.
- It tests **prevention mindset**: a senior adds tooling (query-count assertion, slow-query alerts), not just fixes the one endpoint.

## Common beginner confusion

- **"I'll just add `Promise.all` and it'll be fast."** It will be faster wall-clock but still N queries. The DB sees no improvement.
- **"Eager loading fixes N+1 always."** No — for many-to-many or one-to-many, JOIN-based eager loading causes cartesian row explosion. Use select-IN instead.
- **"My ORM is slow."** No — your access pattern is slow. The ORM emitted exactly what you asked for via lazy proxy traversal.
- **"DataLoader is GraphQL-specific."** No — it's just a batched-loader library; useful in REST too, especially in BFF aggregations.
- **"I caught N+1 in code review."** Maybe — but unless you have a runtime query-count assertion or pg_stat_statements alert, the next N+1 ships unnoticed.

## Brute force approach

Run, watch the SQL log, and add `include` / `relations` until the query count drops. Works for one endpoint; doesn't prevent regressions; doesn't think about row blow-up.

## Optimal approach

1. **Detect** in dev with SQL logging + a per-request query-count assertion middleware. Fail tests at >10 queries / request.
2. **Detect** in prod with `pg_stat_statements` ranked by `calls` per minute — N+1 leaders shoot to the top.
3. **Fix** with the right strategy:
   - **Eager JOIN** when the relation is many-to-one or one-to-one (no row explosion).
   - **Select-IN** when the relation is one-to-many or many-to-many (avoids cartesian).
   - **DataLoader** when calls originate from independent sources (GraphQL resolvers, microservice BFF).
   - **Raw SQL with aggregates** when only counts/sums are needed (`SELECT user_id, COUNT(*) ... GROUP BY user_id`).
4. **Prevent** regressions: ESLint rule banning `.find()` inside loops on entities; load tests with query-count budget.

## Solution

```typescript
// ============================================================
// Detection: dev-mode middleware (Express + TypeORM)
// ============================================================
import { DataSource } from 'typeorm';
import type { Request, Response, NextFunction } from 'express';

export function queryBudget(ds: DataSource, max = 10) {
  return (req: Request, res: Response, next: NextFunction) => {
    let count = 0;
    const orig = ds.driver.afterQuery;
    ds.driver.afterQuery = (...args: any[]) => { count++; return orig?.apply(ds.driver, args); };
    res.on('finish', () => {
      if (count > max) {
        console.warn(`[N+1?] ${req.method} ${req.url} -> ${count} queries`);
      }
      ds.driver.afterQuery = orig;
    });
    next();
  };
}

// ============================================================
// Fix #1: eager JOIN (TypeORM) — best for many-to-one
// ============================================================
const users = await userRepo.find({
  where: { active: true },
  relations: { profile: true },   // 1 query w/ LEFT JOIN
  // profile is 1:1 — no cartesian explosion
});

// ============================================================
// Fix #2: select-IN (Prisma) — best for one-to-many
// ============================================================
const users = await prisma.user.findMany({
  where: { active: true },
  include: {
    orders: {
      where: { status: 'PAID' },
      orderBy: { createdAt: 'desc' },
      take: 10,
    },
  },
});
// Emits:
//   SELECT * FROM "User" WHERE active = $1;
//   SELECT * FROM "Order" WHERE "userId" IN ($1,$2,...) AND status = 'PAID' ...;

// ============================================================
// Fix #3: DataLoader (Node, framework-agnostic)
// ============================================================
import DataLoader from 'dataloader';

const orderLoader = new DataLoader<number, Order[]>(async (userIds) => {
  const orders = await orderRepo.find({ where: { userId: In(userIds as number[]) } });
  const byUser = new Map<number, Order[]>();
  orders.forEach(o => {
    if (!byUser.has(o.userId)) byUser.set(o.userId, []);
    byUser.get(o.userId)!.push(o);
  });
  return userIds.map(id => byUser.get(id) ?? []);
});

// Anywhere in the same tick:
const userOrders = await Promise.all(users.map(u => orderLoader.load(u.id)));
// Behind the scenes, just 1 SELECT orders WHERE user_id IN (...).

// ============================================================
// Fix #4: aggregate-only via raw SQL — best when you don't need the rows
// ============================================================
const counts = await ds.query(`
  SELECT u.id, COUNT(o.id) AS order_count
  FROM users u LEFT JOIN orders o ON o.user_id = u.id
  WHERE u.active = true
  GROUP BY u.id
`);
```

## Step-by-step dry run

Endpoint: `GET /dashboard` returns 4 users + their orders.

Buggy code:
```typescript
const users = await userRepo.find();          // t=0  SELECT users
for (const u of users) {
  const orders = await u.orders;              // t=1..4  SELECT orders WHERE user_id = ?
  out.push({ user: u, orderCount: orders.length });
}
```

Trace:
- `t=0` — `userRepo.find()` emits `SELECT * FROM users` → 4 rows hydrated, identity map populated.
- `t=1` — `u.orders` is a lazy proxy. First access fires `SELECT * FROM orders WHERE user_id = 1`.
- `t=2..4` — same for `user_id = 2, 3, 4`. **5 round trips total.**

Now apply fix #2 (Prisma select-IN):
```typescript
const users = await prisma.user.findMany({ include: { orders: true } });
out = users.map(u => ({ user: u, orderCount: u.orders.length }));
```

Trace:
- `t=0` — `SELECT * FROM "User"` → 4 rows.
- `t=1` — Prisma collects IDs (`[1,2,3,4]`) and emits `SELECT * FROM "Order" WHERE "userId" IN (1,2,3,4)`.
- `t=2` — hydration merges orders into each user. **2 round trips total.**

P50 latency: 5×4ms → 2×4ms (≈60% reduction at the DB layer) plus avoided planner overhead.

If you'd used Fix #1 (TypeORM JOIN) instead:
- `t=0` — `SELECT u.*, o.* FROM users u LEFT JOIN orders o ON o.user_id = u.id`.
- 4 users × avg 25 orders = 100 rows shipped. Network cost higher than select-IN, and the ORM has to dedupe users.

Verdict: select-IN wins when the child collection is large; eager JOIN wins when it's small (≤5 children/parent) or 1:1.

## How to think aloud in the interview

> "N+1 is when one parent query is followed by one child query per parent. Classic symptom: an endpoint that fires a SELECT for the list, then a SELECT per item inside a loop or serializer.
>
> Three fixes, picked by relationship shape:
>
> 1. **Eager JOIN** — collapse to 1 query. Right for many-to-one or 1:1. Wrong for one-to-many because of cartesian row blow-up.
> 2. **Select-IN** — 2 queries total: parents first, children with `WHERE fk IN (...)`. Right for one-to-many. Prisma does this by default; SQLAlchemy via `selectinload`; Hibernate via `@BatchSize`.
> 3. **DataLoader** — batched + cached per request. Right for GraphQL or BFF aggregation where the calls originate from independent resolvers.
>
> I also default to **prevention**: a dev-mode middleware that logs a warning when a request fires more than N queries, plus `pg_stat_statements` in prod ranked by call count. The point isn't fixing this N+1; it's making sure the next one doesn't ship silently."

## Important takeaways

- N+1 = 1 parent query + N child queries; symptom is query count proportional to row count.
- Three canonical fixes: eager JOIN (1 query), select-IN (2 queries), DataLoader (batched).
- **Pick by cardinality**: 1:1 / many-to-one → JOIN; one-to-many → select-IN; nested / cross-source → DataLoader.
- Cartesian explosion is the JOIN-side gotcha; row count = parents × children.
- Prevent regressions with a per-request query-count budget; don't rely on code review.
- N+1 inside serializers and GraphQL resolvers is invisible to your controller — instrument both.

## Variants

1. **N+1 inside a serializer/decorator** — `@Expose() get fullName() { return this.profile.firstName + ... }` — the lazy load fires during JSON serialization. Fix: eager-include `profile` at the query layer.
2. **N+1+N (3-level)** — users → orders → items. Each level multiplies. Fix: deep `include` or per-level batching.
3. **N+1 across services** — service A returns user IDs, service B fetches per-user data. Fix: bulk endpoint `POST /users/bulk { ids }`.
4. **N+1 on counts** — `.length` triggers loads. Fix: `_count` (Prisma), `loadRelationCountAndMap` (TypeORM), `Count(*)` in SQLAlchemy.
5. **N+1 in GraphQL** — every field with a resolver. Fix: DataLoader per request, not global (to avoid cross-request leakage).

## Revision notes

> **detect-n-plus-1 — 60 second recap**
> - 1 parent query + N child queries; ORM lazy proxies are the usual culprit.
> - Detect in dev with SQL log + query-count middleware; in prod with `pg_stat_statements`.
> - Three fixes: eager JOIN (1:1 / many-to-one), select-IN (one-to-many), DataLoader (GraphQL/BFF).
> - JOIN risk: cartesian row blow-up = parents × children.
> - GraphQL is N+1 by design — DataLoader is not optional.
> - Prevention beats reaction: ban `.find()` in loops; assert query budget per request.
