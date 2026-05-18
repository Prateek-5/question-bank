# Raw SQL escape hatch — when and how to drop down

## Source / Origin
- The "when does the ORM stop being your friend?" question.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md`, `02-orm-comparison.md` (when to use raw SQL).

## Why this question matters in interviews
The ORM-vs-raw-SQL debate is a senior-judgement signal. Junior candidates either avoid raw SQL or use it everywhere; mid-levels know they *can* drop down; **seniors pick deliberately** — for specific endpoints, for specific Postgres features, with parameter binding to avoid injection, and with explicit DTO mapping so the result type is clear. The interview also tests **SQL-injection awareness**, which is the failure mode of raw SQL done sloppily.

## Concepts involved

### When to drop to raw SQL

1. **Postgres-specific features**: `LATERAL JOIN`, recursive CTEs, window functions, `GIN` / `GIST` index hints, full-text search (`to_tsvector`), JSONB operators (`->`, `->>`, `@>`).
2. **Performance-critical hot paths**: 1000s of req/s where the ORM hydration cost matters.
3. **Bulk operations**: `INSERT ... SELECT`, `UPDATE ... FROM`, `DELETE ... USING`.
4. **Reports / analytics**: complex `GROUP BY ROLLUP`, percentiles (`PERCENTILE_CONT`), pivots.
5. **Migrations involving data** (backfills): easier to read in SQL than in ORM.
6. **Streaming exports**: server-side cursor; bypass hydration.

### Syntax across ORMs

```typescript
// TypeORM
const rows = await ds.query(
  'SELECT id, email FROM users WHERE id = $1 AND created_at > $2',
  [userId, since]
);
// rows: any[] — no entity hydration; cast to your DTO.

// Prisma
const rows = await prisma.$queryRaw<UserRow[]>`
  SELECT id, email FROM "User" WHERE id = ${userId} AND created_at > ${since}
`;
// Template literal interpolation is parameterized — safe.

// AVOID:
const bad = await prisma.$queryRawUnsafe(`SELECT * FROM "User" WHERE id = ${userInput}`);
// userInput goes in literally — SQL injection!

// Sequelize
const [rows] = await sequelize.query(
  'SELECT id, email FROM users WHERE id = :id AND created_at > :since',
  { replacements: { id: userId, since }, type: QueryTypes.SELECT }
);

// SQLAlchemy
from sqlalchemy import text
result = session.execute(
    text("SELECT id, email FROM users WHERE id = :id AND created_at > :since"),
    {"id": user_id, "since": since}
)

// JPA / Hibernate
@Query(value = "SELECT id, email FROM users WHERE id = ?1", nativeQuery = true)
List<Object[]> findUserRaw(Long id);
```

### Parameter binding — the only safe way

```sql
-- SAFE: parameterized
SELECT * FROM users WHERE id = $1;       -- Postgres
SELECT * FROM users WHERE id = ?;         -- MySQL / generic
SELECT * FROM users WHERE id = :id;       -- named (SQLAlchemy, JPA)

-- UNSAFE: string concatenation
const q = `SELECT * FROM users WHERE id = ${userInput}`;
// SQL injection waiting: userInput = "1 OR 1=1; DROP TABLE users; --"
```

### Edge cases / interview traps

1. **`$queryRawUnsafe` / `literal()` / `query()` with string concat** — the ORM's escape hatch's escape hatch. Easy to misuse; banned in most code bases.
2. **Identifier injection.** Parameter binding is for values, not table/column names. If you must vary identifiers, use a whitelist.
3. **Type coercion.** Raw query returns generic objects; numbers may come as strings (`DECIMAL`, `BIGINT`); JSONB may come as parsed object or string depending on driver.
4. **No entity hydration.** Raw result is `any[]`; no relations wired; no lifecycle hooks. That's the point, but be explicit about the shape.
5. **Transactions still apply** — raw queries run inside the current TX if invoked via `tx.query()` / `tx.$queryRaw`.
6. **Connection pool routing** — raw queries default to the primary; route to replica explicitly if needed.
7. **Migration / schema drift** — raw SQL references columns; if the column is renamed/dropped, your code only fails at runtime, not at TS compile.
8. **Database-specific SQL** — raw queries are not portable; tying yourself to Postgres syntax locks you in.
9. **DTO mapping.** Raw query returns raw rows; you need an explicit DTO type or risk shape mismatch.
10. **Driver-level errors** instead of ORM errors — different exception types; your error handler may need updating.

## Mental Model

```
   ORM call          ─►  generated SQL (predictable, parametrized)
                          ↑
                       ORM owns the SQL string

   Raw query         ─►  your SQL (typed yourself)
                          ↑
                       you own the SQL string

   Raw query w/ binding ─► your SQL + driver-parametrized values
                          ↑
                       you own SQL; driver owns parameter substitution

   String-concat raw ─►  your SQL + user input concatenated
                          ↑
                       INJECTION RISK — don't.
```

The discipline: **drop to raw SQL when needed; never drop to string-concatenation SQL.**

## Why interviewers care

- Tests **SQL-injection awareness** — the failure mode that's universally critical.
- Tests **judgement** about when ORM helps vs hurts.
- Catches the candidate who uses raw SQL for everything (poor maintainability) or who refuses to use raw SQL (poor performance).

## Common beginner confusion

- **"ORMs prevent SQL injection automatically."** Only if you use the parameterized methods. `$queryRawUnsafe` / `literal()` bypass that protection.
- **"Raw SQL is faster."** Sometimes; often the ORM's generated SQL is identical. Profile, don't assume.
- **"Template literals interpolate user input safely."** In Prisma, `$queryRaw\`... ${id} ...\`` is parameterized (transformed to `$1`). In JS in general, `\`SELECT ... ${userInput}\`` is just string concat — NOT SAFE.
- **"Type safety vanishes with raw SQL."** Mostly true, but tools like sqlc, kysely, drizzle, jOOQ give you typed raw SQL.
- **"I'll use raw SQL only when there's no other choice."** Reasonable bias, but for high-RPS read paths, raw + DTO is often the right default.

## Brute force approach

Write a stored procedure for everything; call it via raw SQL. Works; pushes complexity into the DB; harder to test and version. Not recommended unless you have a specific reason.

## Optimal approach

1. **Default to ORM** for CRUD with validations/hooks/transactions.
2. **Use raw SQL** for:
   - Complex queries (CTEs, window functions, set ops, full-text, JSONB ops).
   - Performance-critical hot reads (high RPS, large result sets).
   - Bulk operations (`INSERT ... SELECT`, `UPDATE ... FROM`).
   - DB-specific features without ORM equivalent.
3. **Always parameterize** — never string-concat user input.
4. **Map to explicit DTOs** — don't return raw rows from your service layer.
5. **Lint / ban `query`-style string concat** at the linter level.
6. **Keep raw SQL near the entity it queries** (in the same repository file) so it's discoverable.

## Solution

```typescript
// ============================================================
// Hot read path: report endpoint
// ============================================================
type UserRevenueRow = { userId: number; revenue: string; orderCount: number };

async function userRevenueLast30Days(): Promise<UserRevenueRow[]> {
  return ds.query<UserRevenueRow[]>(`
    SELECT u.id AS "userId",
           SUM(o.total)::text AS revenue,        -- ::text to avoid BIGINT→Number loss
           COUNT(o.id)::int AS "orderCount"
    FROM   users u
    JOIN   orders o ON o.user_id = u.id
    WHERE  o.created_at >= NOW() - INTERVAL '30 days'
      AND  o.status = 'PAID'
    GROUP BY u.id
    ORDER BY revenue DESC
    LIMIT 100
  `);
}
// Mapped to UserRevenueRow at the service-layer boundary.

// ============================================================
// Postgres-specific: full-text search
// ============================================================
async function searchPosts(query: string) {
  return prisma.$queryRaw<Post[]>`
    SELECT id, title, body
    FROM   "Post"
    WHERE  to_tsvector('english', title || ' ' || body) @@ plainto_tsquery('english', ${query})
    ORDER  BY ts_rank(to_tsvector('english', title || ' ' || body),
                      plainto_tsquery('english', ${query})) DESC
    LIMIT 50
  `;
}
// Note: ${query} is interpolated as a parameter by Prisma's tagged template.

// ============================================================
// Recursive CTE: thread / comment tree
// ============================================================
const tree = await ds.query(`
  WITH RECURSIVE thread AS (
    SELECT id, parent_id, body, 0 AS depth
    FROM   comments
    WHERE  id = $1
    UNION ALL
    SELECT c.id, c.parent_id, c.body, t.depth + 1
    FROM   comments c JOIN thread t ON c.parent_id = t.id
  )
  SELECT * FROM thread ORDER BY depth, id;
`, [rootId]);

// ============================================================
// Set operations: customers without orders
// ============================================================
const cold = await ds.query(`
  SELECT id, email FROM users
  WHERE  id NOT IN (SELECT DISTINCT user_id FROM orders WHERE status = 'PAID');
`);

// ============================================================
// DON'T DO THIS
// ============================================================
const bad = await ds.query(`SELECT * FROM users WHERE email = '${req.body.email}'`);
//                                                                ^^^^^^^^^^^^^^^
// SQL injection: email = "x' OR '1'='1"
// SAFE alternative:
const safe = await ds.query('SELECT * FROM users WHERE email = $1', [req.body.email]);
```

```python
# ============================================================
# SQLAlchemy — named parameter binding
# ============================================================
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(
        text("""
            SELECT u.id, SUM(o.total) AS revenue
            FROM users u JOIN orders o ON o.user_id = u.id
            WHERE o.created_at > :since
            GROUP BY u.id
            HAVING COUNT(*) > :min_orders
        """),
        {"since": since, "min_orders": 5}
    ).all()
```

## Step-by-step dry run

### Scenario A: hot endpoint with complex aggregation

ORM attempt:
```typescript
const users = await prisma.user.findMany({
  include: { orders: { where: { status: 'PAID' } } },
});
const result = users.map(u => ({
  userId: u.id,
  revenue: u.orders.reduce((s, o) => s + o.total, 0),
}));
```
- Loads every user + every PAID order — hundreds of MB hydrated.
- Aggregation happens in JS — 50ms+ per request for 100k orders.
- Memory pressure; GC pauses.

Raw SQL version:
```typescript
const result = await ds.query<UserRevenueRow[]>(`
  SELECT u.id AS "userId", SUM(o.total) AS revenue
  FROM   users u JOIN orders o ON o.user_id = u.id
  WHERE  o.status = 'PAID'
  GROUP BY u.id;
`);
```
- DB does the aggregation — uses index on `(user_id, status)`.
- 100 rows shipped to app.
- 5ms total at endpoint.

10x improvement. The ORM had no good way to express "aggregate in DB, ship summary."

### Scenario B: injection attempt

Buggy code:
```typescript
app.get('/user-by-email', async (req, res) => {
  const rows = await ds.query(
    `SELECT * FROM users WHERE email = '${req.query.email}'`
  );
  res.json(rows);
});
```

Attacker request:
```
GET /user-by-email?email=x' OR '1'='1
```

Resulting SQL:
```sql
SELECT * FROM users WHERE email = 'x' OR '1'='1';
-- Returns ALL users.
```

Worse attack:
```
GET /user-by-email?email=x'; DROP TABLE users; --
```

```sql
SELECT * FROM users WHERE email = 'x'; DROP TABLE users; --';
-- Two statements: empty SELECT + DROP TABLE.
```

Fix:
```typescript
const rows = await ds.query('SELECT * FROM users WHERE email = $1', [req.query.email]);
```
- Driver sends `email = $1`; the parameter is escaped/typed at the wire.
- No injection possible regardless of input.

## How to think aloud in the interview

> "I drop to raw SQL deliberately for five reasons:
>
> 1. **Postgres-specific features** the ORM can't express: recursive CTEs, window functions, JSONB operators, full-text search, LATERAL.
> 2. **Performance-critical reads**: aggregations belong in the DB, not in JS-side loops. The ORM was a bad fit when I have 100k rows and want a 100-row summary.
> 3. **Bulk operations**: `INSERT ... SELECT`, `UPDATE ... FROM`.
> 4. **Reports / analytics**: ROLLUP, PERCENTILE, pivots.
> 5. **Migrations involving data**: backfills are clearer in SQL.
>
> The unbreakable rule: **always parameterize**. `$queryRaw\`... ${id} ...\`` (Prisma) or `ds.query('... WHERE id = $1', [id])` (TypeORM). Never string-concat user input. The escape hatch's escape hatch (`$queryRawUnsafe`, `literal()`, `query()` with `\` `${input}\``) gets banned at the linter level.
>
> I map raw rows to explicit DTOs at the service-layer boundary, so the rest of the code sees typed shapes and doesn't depend on the column ordering.
>
> For type-safety inside raw SQL, tools like sqlc, kysely, or drizzle let me have parameterized queries with full TypeScript types — best of both worlds."

## Important takeaways

- Drop to raw SQL for Postgres features, hot reads, bulk ops, reports, data migrations.
- **Always parameterize** — never string-concat user input.
- Map raw rows to explicit DTOs at the service boundary; don't leak `any[]` into business logic.
- `$queryRawUnsafe`, `literal()`, raw `query()` with template strings are footguns; ban them.
- Tools (sqlc, kysely, drizzle, jOOQ) give typed raw SQL.
- Raw queries skip hydration, hooks, identity map — intentional, but be aware.
- Identifier (table/column) names cannot be parameterized; use whitelists.
- Transactions still apply: `tx.query()` runs in the current TX.

## Variants

1. **Typed raw SQL with kysely** — `db.selectFrom('users').select(...).execute()` outputs SQL with full TS types.
2. **Database functions / stored procedures** — push complex logic into the DB; call via raw `SELECT my_fn(...)`.
3. **`COPY` for streaming** — raw protocol-level access for huge imports/exports.
4. **Materialized views** — pre-compute heavy reports; refresh on schedule; query via the ORM.
5. **Read replicas with explicit routing** — `ds.query` against a `replicaPool` instance.
6. **`pg_stat_statements`** — find queries to optimize first; rank by `total_time`.
7. **Sqlc-style codegen** — write SQL files; generate typed query functions.

## Revision notes

> **raw-sql-escape-hatch — 60 second recap**
> - Use raw SQL for: Postgres-specific features, hot reads, bulk ops, reports, data migrations.
> - **Always parameterize**: `$queryRaw\`... ${id}\``, `ds.query('... = $1', [id])`. Never `'... = ' + input`.
> - Ban `$queryRawUnsafe` / `literal()` / template-string raw at the linter level.
> - Map raw rows to explicit DTOs; don't leak `any[]`.
> - Identifier names can't be parameterized — use whitelists.
> - Hydration, hooks, identity map all skipped with raw — be intentional.
> - Tools (kysely, sqlc, drizzle, jOOQ) give typed raw SQL.
> - Raw queries respect transactions when invoked via tx-scoped methods.
