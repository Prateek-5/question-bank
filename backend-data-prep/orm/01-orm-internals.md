# ORM Internals

## Why this matters in backend interviews

- Every backend SDE2 interview involving an ORM (Sequelize, TypeORM, Prisma, Hibernate, GORM, ActiveRecord) tests the **N+1 problem**, transaction boundaries, and lazy vs eager loading.
- **Production debugging**: 70% of slow APIs at high-growth companies trace back to ORM misuse.
- **Senior signal**: knowing when to drop into raw SQL and when to trust the ORM.

This is a high-ROI topic because most candidates only know surface-level ORM use.

---

## Core concepts

### What an ORM does (and doesn't do)

An ORM (Object-Relational Mapper):
- Maps rows ↔ objects (hydration)
- Generates SQL from method calls
- Manages connections / transactions
- Tracks changes (in some patterns)

It does **not**:
- Replace SQL knowledge
- Optimize queries (you must understand the generated SQL)
- Handle complex joins gracefully
- Substitute for DB-level constraints

### Active Record vs Data Mapper

- **Active Record** (Rails, Sequelize, Eloquent): the object carries its own persistence (`user.save()`). Simple, but mixes domain and infra.
- **Data Mapper** (TypeORM Repository, Doctrine, Hibernate, Prisma): a separate repository / mapper persists the object. Cleaner separation; better for DDD.
- Prisma is a different beast — query builder + types, not classic OOP "models."

### Unit of Work pattern

- Track all changes within a session (created, updated, deleted objects)
- Flush them to DB in one transaction at the end
- Avoids partial writes
- Examples: Hibernate, EntityManager (TypeORM), DbContext (EF Core)

Prisma/Sequelize use a simpler "immediate-write" model.

### Identity map

- Within a session, the same row always maps to the same object instance
- Prevents duplicate hydration and stale state
- Hibernate's first-level cache is an identity map

### Lazy vs eager loading

- **Lazy**: related objects loaded on access (`user.orders` triggers a query)
- **Eager**: related objects loaded with the parent in one query (JOIN or follow-up SELECT)

```javascript
// Lazy (TypeORM): N+1 disaster waiting to happen
const users = await userRepo.find();
for (const u of users) {
  const orders = await u.orders;  // N additional queries
}

// Eager (TypeORM)
const users = await userRepo.find({ relations: ['orders'] });
```

### The N+1 problem

**The most-asked ORM interview question.**

Pattern:
```javascript
const users = await User.findAll();  // 1 query
for (const user of users) {
  console.log(user.profile.bio);     // lazy-loaded → 1 query per user → N
}
// Total: N + 1 queries
```

Fixes:
1. **Eager loading**: `User.findAll({ include: [Profile] })` → JOIN
2. **Separate batch fetch**:
   ```javascript
   const users = await User.findAll();
   const profiles = await Profile.findAll({ where: { userId: users.map(u => u.id) } });
   ```
3. **DataLoader pattern**: batched + memoized loaders (Facebook's DataLoader library)
4. **Raw SQL**: hand-written JOIN

### Eager loading strategies under the hood

- **JOIN-based**: one SQL statement with JOINs. Pro: one round trip. Con: row duplication when one-to-many ("cartesian explosion").
- **Select-IN**: parent query returns IDs; child query fetches `WHERE parent_id IN (...)`. Pro: no row duplication. Con: two round trips.

Hibernate, TypeORM, and Prisma offer both. Prisma uses select-IN-style by default (no cartesian explosion).

### Hydration cost

For each row returned by SQL, the ORM:
1. Allocates an object
2. Sets properties (often via reflection / decorators)
3. Wires up associations
4. Possibly runs lifecycle hooks

For thousands of rows, this is a real cost. Raw SQL is sometimes 5-10x faster for large reads (analytics, exports). Use `raw()` or `pluck()` to skip hydration.

### Change detection

- ORMs track dirty fields and only UPDATE changed columns
- Subtle bug: changing a JSON column in place might not be detected; force-mark dirty
- TypeORM, Sequelize, Hibernate all have this caveat

### Transaction boundaries

- Implicit per-statement (autocommit) by default
- Explicit transactions via `transaction()` / `withTransaction()` / decorator
- **Anti-pattern**: external API call inside transaction (locks held during network I/O)
- **Anti-pattern**: nested transactions silently become savepoints — be aware

### Migrations

- ORMs typically generate migrations from schema diff (Prisma, Sequelize CLI, TypeORM)
- Generated migrations are starting points, not gospel — review for production safety:
  - Adding NOT NULL columns without default → table rewrite
  - Renaming columns → can cause downtime if old code reads the old name
  - Dropping columns → break running instances of old code
  - Index creation → must be `CONCURRENTLY` in Postgres
- Always: additive migrations in production; rollout in phases (add column → deploy → backfill → mark required → deploy → drop old)

### Query builders vs ORMs

- **Query builder** (Knex, jOOQ, Kysely): typed SQL construction; you still think in SQL
- **ORM** (Sequelize, TypeORM, Hibernate): object-centric API
- **Hybrid** (Prisma): types + nested queries; not an OOP model

Most modern projects benefit from a builder + light ORM mix. Heavy mappers (Hibernate, TypeORM Repository) come at a complexity cost.

### Connection pooling

- ORMs use a pool (HikariCP for Java; node-postgres for Node; etc.)
- Pool size: ~10–50 connections per app instance, ~ less than (DB max_connections / app instance count)
- Too small → request queueing
- Too large → DB context switching, lock contention
- Behind a pooler (PgBouncer, RDS Proxy) for thousands of connections

### Common misconceptions

- "ORM optimizes SQL for me" — no, it just generates SQL based on your method calls
- "ORM is always slower than raw SQL" — for simple CRUD, the overhead is negligible; for reads with hydration of thousands of rows, it can be significant
- "Eager loading is always the fix" — sometimes the JOIN is the slowness; pick select-IN or raw SQL
- "Lazy loading is bad" — it's fine when you actually access the relation; bad when you forget you're in a loop
- "Prisma is just a query builder" — close, but it does hydration + relations; the distinction is real

### Interview traps

1. **"How would you fix N+1 in this code?"** — multiple right answers; show that you understand the trade-offs (eager JOIN vs select-IN vs DataLoader vs raw).
2. **"Show me the SQL your ORM call generates"** — always be ready to predict the SQL.
3. **"Transactions with retry"** — must handle `40001` / `40P01` retries.
4. **"How would you handle 10M-row export?"** — stream from DB, no hydration; cursor or COPY.
5. **"What if the ORM doesn't support a Postgres feature you need?"** — drop to raw SQL via `query()`; this is fine and common.

---

## Real examples

### N+1 (the canonical example)

```javascript
// BAD — N+1 (Sequelize)
const users = await User.findAll();
for (const u of users) {
  const orders = await Order.findAll({ where: { userId: u.id } });
  console.log(u.email, orders.length);
}

// GOOD — eager loading (JOIN under the hood)
const users = await User.findAll({ include: [{ model: Order }] });

// GOOD — separate batched query
const users = await User.findAll();
const userIds = users.map(u => u.id);
const orders = await Order.findAll({ where: { userId: userIds } });
const ordersByUser = groupBy(orders, 'userId');
for (const u of users) {
  console.log(u.email, (ordersByUser[u.id] || []).length);
}
```

### Cartesian explosion

```sql
-- Joining users to orders to order_items to products:
-- 1 user with 10 orders, each with 5 items → 50 rows for 1 user
-- The ORM has to dedupe by user; bandwidth wasted
```

Fix: do separate batched queries, not a single JOIN. Prisma does this automatically.

### Transaction with retry

```javascript
async function withTx(fn, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try {
      return await sequelize.transaction({ isolationLevel: 'SERIALIZABLE' }, fn);
    } catch (e) {
      if (e.original?.code === '40001' || e.original?.code === '40P01') {
        await sleep(Math.random() * 100 * (i + 1));
        continue;
      }
      throw e;
    }
  }
  throw new Error('TX_RETRY_EXHAUSTED');
}
```

### Big export — bypass ORM

```javascript
// Sequelize raw stream
const stream = sequelize.connectionManager
  .getConnection()
  .query('SELECT * FROM events WHERE created_at > $1', [since])
  .stream();

stream.on('data', row => write(row));
stream.on('end', () => done());
```

Or use COPY for tens of millions of rows.

### DataLoader pattern

```javascript
const userLoader = new DataLoader(async (ids) => {
  const users = await User.findAll({ where: { id: ids } });
  // Return users in same order as ids
  const map = new Map(users.map(u => [u.id, u]));
  return ids.map(id => map.get(id));
});

// In any handler:
const user = await userLoader.load(userId);  // batched + cached per-request
```

Used heavily in GraphQL resolvers to avoid N+1.

---

## Common interview questions

1. What is the N+1 problem? How do you fix it?
2. Lazy vs eager loading — pros and cons.
3. What is a unit of work?
4. What's an identity map?
5. How does an ORM detect changes?
6. When would you drop down to raw SQL?
7. Active Record vs Data Mapper.
8. How do migrations work?
9. How do you handle transactions in an ORM?
10. ORM connection pooling — sizing concerns.
11. What is DataLoader and why is it useful?
12. Common ORM anti-patterns in production.

---

## Detailed answers

### 1. N+1
Initial query returns N parents; for each, a query fetches the child → N + 1 queries total. Fixes: eager loading (JOIN or select-IN), batched fetches, DataLoader, raw SQL.

### 2. Lazy vs eager
Lazy: load when accessed; risk of N+1; minimizes initial query weight. Eager: load relations up front; one or few queries; risk of over-fetching and cartesian explosion. Choice depends on access pattern.

### 3. Unit of Work
Tracks all entity changes during a session; flushes them in one transaction. Reduces round trips; ensures atomicity. Hibernate, EntityManager.

### 4. Identity map
A cache within a session that ensures one row = one object instance. Prevents duplicate hydration; ensures consistent state during a session.

### 5. Change detection
- Snapshot model: ORM stores initial state and diffs on flush (Hibernate)
- Property accessors: track sets via setters (TypeORM, ActiveRecord)
- Explicit calls: `update()` with fields (Prisma)
- Pitfall: mutating in place (JSON columns, arrays) — change isn't always detected

### 6. Raw SQL when needed
- Complex window functions / recursive CTEs / DB-specific features
- Bulk operations (10k+ rows)
- Performance-critical hot paths
- Reports / analytics queries
Use `query()` / `raw()` API; still benefit from ORM's connection pool and parameter binding (avoid SQL injection).

### 7. Active Record vs Data Mapper
- Active Record: object has `save()`, `delete()`. Easy, but couples domain to persistence.
- Data Mapper: domain object is plain; a repository persists it. Better for testing and complex domains.

### 8. Migrations
Generated from schema diff or written manually. Tracked in a meta table. Forward (apply) and backward (rollback) functions. **Always review generated migrations** before applying to prod; the generator doesn't know about uptime, locks, data backfill.

### 9. Transactions in ORM
```javascript
// Sequelize
await sequelize.transaction(async (t) => { /* use t */ });
// TypeORM
await dataSource.transaction(async manager => { ... });
// Prisma
await prisma.$transaction(async tx => { ... });
```
Set isolation level explicitly when needed. Handle retries on conflict.

### 10. Pool sizing
- App instance pool size × number of instances ≤ DB's max_connections (with headroom)
- For Postgres, use PgBouncer (transaction-mode) to multiplex
- Per-instance pool typically 10–25 for Node, 10–20 for HikariCP
- Monitor wait time; if high → increase pool or move work

### 11. DataLoader
Library that batches and caches per-request loads:
- Multiple `load(id)` calls in the same tick are batched into one DB query
- Cache within request scope prevents duplicate fetches
- Common in GraphQL; useful anywhere you have nested data loading

### 12. ORM anti-patterns
- Doing business logic in hooks (hidden side effects)
- N+1 by accident in loops
- External API calls inside transactions
- Unused eager loads (over-fetching)
- Ignoring generated SQL — run `.toSQL()` / `EXPLAIN` regularly
- Long-running transactions
- Storing JSONB without indexes
- Building queries dynamically with string concatenation (SQL injection)

---

## Practical coding examples

### Sequelize: detecting N+1 in dev
```javascript
// Log all queries
new Sequelize(url, { logging: console.log });
// Count queries per request; alert if > threshold
```

### TypeORM: avoid loading huge text columns
```javascript
const users = await userRepo.find({
  select: ['id', 'email', 'name']  // skip 'bio', 'avatar'
});
```

### Prisma: nested writes (atomic by default)
```javascript
await prisma.order.create({
  data: {
    userId,
    status: 'PLACED',
    items: {
      create: items.map(i => ({ sku: i.sku, qty: i.qty }))
    }
  }
});
// Single transaction: order + items
```

### Hibernate: batch fetch size
```java
@OneToMany(fetch = FetchType.LAZY)
@BatchSize(size = 50)
private List<Order> orders;
// On access, fetches 50 parents' orders in one query
```

### Stream large result set (Postgres + pg + Node)
```javascript
const QueryStream = require('pg-query-stream');
const query = new QueryStream('SELECT * FROM events WHERE ts > $1', [since]);
const stream = client.query(query);
stream.pipe(process.stdout);
```

### Detect dirty in TypeORM
```javascript
const post = await postRepo.findOne(1);
post.body = 'new content';
await postRepo.save(post);  // only updates body
```

---

## Common mistakes

- N+1 (you'll see it in every legacy code base)
- Forgetting `relations`/`include` and then doing manual fetches in loops
- Loading entire entities when you only need 2 columns (use `select`/`pluck`)
- Storing dates as strings (use the ORM's date type)
- Forgetting transaction retries on serialization failure
- Migrations dropping columns immediately (must coordinate with deploys)
- Trusting auto-generated indexes (often missing — review schema)
- ORMs hiding query slowness — always profile

---

## Senior engineer discussion points

- **When the ORM becomes the bottleneck** — heavy hydration, lots of relations; consider DTO projections
- **CQRS** — different models for reads and writes; ORM for writes, raw SQL for reads
- **Read replicas + ORM** — configure read replica connection separately; route SELECTs there
- **Generated SQL audit** — log every query in dev; pg_stat_statements in prod; fix top offenders
- **Prisma's design** — types-first, no lazy loading, explicit relation loading; reduces footguns
- **Hibernate horror stories** — proxy lazy-loading issues, LazyInitializationException, complex caching layers
- **GraphQL + DataLoader** — necessary, not optional, for N+1 prevention
- **Migrations across services** — coordinate when shared schema, prefer per-service when not

---

## Revision notes

- N+1 = 1 parent query + N child queries; fix with eager / select-IN / DataLoader / raw
- Lazy = on-demand, risk of N+1; Eager = up-front, risk of over-fetch
- Unit of Work = batch changes, flush in transaction
- Identity Map = one row → one object per session
- JOIN-based eager → cartesian explosion (many parents × many children)
- Select-IN eager → 2 queries, no explosion (Prisma default)
- Drop to raw SQL for: bulk ops, complex SQL, hot paths, exports
- Transactions: handle retry on 40001 / 40P01; never call external APIs inside
- Migrations: additive in prod; deploy → backfill → enforce → deploy → drop
- Pool sizing: app instances × pool size ≤ DB max_connections
- DataLoader: batches loads in same tick + caches per request
