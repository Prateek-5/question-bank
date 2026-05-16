# Prisma vs Sequelize vs TypeORM (and others)

## Why this matters in backend interviews

- Backend candidates are expected to know at least one ORM deeply and **be able to justify the choice**.
- "Why Prisma over TypeORM?" is a real interview question at Node-heavy shops.
- Migration strategy in production is a senior-signal topic.

---

## Plain-English intuition — picking an ORM is picking a paradigm

> Choosing between Hibernate, Prisma, TypeORM, Sequelize, SQLAlchemy, Django ORM, and ActiveRecord is **not** like choosing between three brands of identical hammers. It is closer to choosing between **a power drill, a hand screwdriver, and a nail gun** — they all attach things, but the workflow, ergonomics, and failure modes are very different.

The core differences come down to:

1. **Architectural pattern** — Active Record (object knows how to save itself) vs Data Mapper (a repository persists plain objects).
2. **Schema source of truth** — schema file, class decorators, or hand-written migrations.
3. **Lazy loading available?** — Hibernate/TypeORM yes; Prisma no.
4. **Unit of Work / Session state** — heavy (Hibernate, SQLAlchemy) vs lightweight (Prisma, Sequelize).
5. **Type safety** — Prisma generates types; others retrofit them.

### Why interviewers care

- **You'll use at least one in production.** Picking poorly costs months of refactoring.
- **The trade-offs are universal.** Even if you only know TypeORM, you should articulate *why* you'd pick Prisma for a fresh project — that's senior judgement.
- **Migration risk** affects every deploy. Knowing safe-rename and zero-downtime patterns is a senior-engineer marker.

### Real-world mapping analogy

> Think of building a house:
>
> - **Active Record (Rails, Eloquent, Sequelize)** = pre-fab kit homes. Fast, opinionated, you trust the kit.
> - **Data Mapper (Hibernate, SQLAlchemy, TypeORM Repository, Doctrine)** = architect-led custom builds. Slower upfront, much more control, easier to test.
> - **Prisma** = a modern modular system — types-first, no surprises, but you must declare every relation explicitly.
> - **Raw SQL + thin query builder (Kysely, Knex, jOOQ)** = bricks and mortar. Maximum control, maximum responsibility.
>
> None is "the best." A startup MVP can ship 3× faster with Active Record. A 5-year-old financial app may be unmaintainable without Data Mapper. A high-throughput analytics endpoint may need raw SQL inside an otherwise-ORM codebase.

---

## ASCII diagram — Active Record vs Data Mapper

```
   ACTIVE RECORD                                  DATA MAPPER
   ──────────────                                 ────────────

   ┌──────────────────────┐                      ┌──────────────────────┐
   │ class User           │                      │ class User           │
   │  - id, email, name   │                      │  - id, email, name   │   ◄── pure domain
   │  + save()  ◄────┐    │                      │  (no save())         │       no DB awareness
   │  + delete()    │    │                      └──────────┬───────────┘
   │  + find(id)    │    │                                 │
   └──────────┬─────┘    │                      ┌──────────▼───────────┐
              │ uses     │                      │ class UserRepository │
              ▼          │                      │  + save(user)        │
   ┌──────────────────────┐                      │  + delete(user)      │
   │ implicit global      │                      │  + findById(id)      │
   │ connection / session │                      └──────────┬───────────┘
   └──────────────────────┘                                 │ uses
                                                            ▼
                                                  ┌──────────────────────┐
                                                  │ Session/EntityMgr    │
                                                  │  (explicit, passed)  │
                                                  └──────────────────────┘

   Examples: Rails AR, Eloquent,                 Examples: Hibernate, SQLAlchemy,
             Sequelize (default mode)                       TypeORM (Repository mode),
                                                            Doctrine, EF Core,
                                                            Prisma (closest to this)

   Pros: minimal boilerplate, fast to ship       Pros: testable, separation of concerns,
                                                       supports rich domain models / DDD

   Cons: domain coupled to DB, hard to test      Cons: more code, steeper learning curve,
                                                       slower for simple CRUD
```

When in doubt: **start with Active Record for prototypes; reach for Data Mapper when the domain logic grows complex enough that you'd rather not see SQL leaking into business code.**

---

## Snapshot comparison

| | **Prisma** | **Sequelize** | **TypeORM** |
|---|---|---|---|
| Style | Query builder + types | Active Record (older) + Repository | Data Mapper or Active Record |
| TS support | First-class (generated types) | Decent (community types) | Decorator-heavy; sometimes broken |
| Lazy loading | ❌ (explicit `include`) | ✓ | ✓ |
| Migrations | Built-in (Prisma Migrate) | Sequelize CLI | TypeORM CLI |
| Raw SQL | `$queryRaw`, `$executeRaw` | `sequelize.query` | `manager.query` |
| Relation loading | Select-IN by default (no cartesian explosion) | JOIN or separate query | JOIN |
| Transactions | `$transaction(async tx => …)` and array form | `sequelize.transaction(async t => …)` | `dataSource.transaction(async m => …)` |
| Schema source | `.prisma` schema file | JS/TS models | TS classes + decorators |
| Maturity | Newer (2019+); fast-evolving | Oldest, lots of legacy | Mid-maturity, slowing development |
| Production safety | Strong (typed + no N+1 by default) | Easy to footgun | Footgun-prone (decorators, eager defaults) |

**Modern default for greenfield Node:** Prisma (best DX + safety). For complex domain models or legacy: TypeORM Repository or Sequelize.

---

## Prisma

### Mental Model — Prisma's design philosophy

> Prisma decided that **most ORM bugs come from invisible work** — lazy loads, implicit eager loads, mutating in-place without dirty tracking. So it makes everything **explicit and typed**.
>
> - No lazy loading → you can't accidentally N+1 by iterating.
> - `include` and `select` are required to pull relations → query cost is visible.
> - Generated client types match the schema 1:1 → if you remove a column, your code stops compiling.
> - Select-IN strategy by default → no cartesian explosion.
>
> Conceptually, Prisma is a **typed query builder with hydration**, not a traditional ORM. There's no session, no identity map, no dirty tracking. You read, you mutate locally, you call `update()` with exact fields.

### Schema-first

```prisma
generator client { provider = "prisma-client-js" }
datasource db { provider = "postgresql"; url = env("DATABASE_URL") }

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  name      String
  createdAt DateTime @default(now())
  orders    Order[]
}

model Order {
  id        Int      @id @default(autoincrement())
  user      User     @relation(fields: [userId], references: [id])
  userId    Int
  status    String
  total     Int
  createdAt DateTime @default(now())

  @@index([userId, createdAt])
}
```

`prisma generate` produces a fully typed client.

### Queries

```typescript
// Find with relations
const users = await prisma.user.findMany({
  where: { email: { contains: '@acme.com' } },
  include: { orders: { where: { status: 'PAID' }, orderBy: { createdAt: 'desc' }, take: 5 } }
});

// Aggregations
const stats = await prisma.order.groupBy({
  by: ['userId'],
  _sum: { total: true },
  _count: true,
  having: { _count: { _all: { gt: 5 } } }
});

// Transactions (interactive)
await prisma.$transaction(async (tx) => {
  await tx.account.update({ where: { id: from }, data: { balance: { decrement: amt } } });
  await tx.account.update({ where: { id: to   }, data: { balance: { increment: amt } } });
}, { isolationLevel: 'Serializable', timeout: 5000 });

// Transactions (array — atomic but no logic)
await prisma.$transaction([
  prisma.account.update({...}),
  prisma.account.update({...}),
]);

// Raw SQL
const result = await prisma.$queryRaw`SELECT id, email FROM "User" WHERE id = ${id}`;
```

### Migrations

```bash
prisma migrate dev --name add_orders
prisma migrate deploy
```

In production: `migrate deploy` only applies committed migrations (no schema diff). Generated SQL lives in `prisma/migrations/`. Review them.

### Pros
- Typed queries; refactoring is safe
- No N+1 by default (select-IN strategy)
- Schema is one file; clear
- Excellent error messages
- Studio (GUI) included

### Cons
- No lazy loading (some find this restrictive)
- Less suited to deep OOP / DDD modeling
- Less mature for niche features (complex CTEs, custom types) — fallback to `$queryRaw`
- Schema file is the single source of truth — can't easily co-locate with code

---

## Sequelize

### Mental Model — Sequelize's heritage

> Sequelize is the **Rails ActiveRecord of Node** — born when Node was new, modeled after the patterns of mid-2000s ORMs. That means: classes have `save()`, defaults are forgiving, JS dynamism is leaned on heavily.
>
> The strength is **familiarity** — if you know Rails or Eloquent, you can start. The weakness is **leakiness** — its eager loading uses JOIN by default, which causes cartesian explosion in one-to-many relationships, and you have to know to break it into separate queries.
>
> TypeScript support is bolted on (not generated), so refactoring is less safe than Prisma. Stick with Sequelize when: legacy codebase, team familiarity, or you need the AR style.

### Models

```javascript
const User = sequelize.define('User', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  email: { type: DataTypes.STRING, unique: true, allowNull: false },
  name: DataTypes.STRING
}, { timestamps: true });

const Order = sequelize.define('Order', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  status: DataTypes.STRING,
  total: DataTypes.INTEGER
});

User.hasMany(Order);
Order.belongsTo(User);
```

### Queries

```javascript
// Find with include (JOIN)
const users = await User.findAll({
  where: { email: { [Op.like]: '%@acme.com' } },
  include: [{ model: Order, where: { status: 'PAID' } }]
});

// Aggregation
const counts = await Order.findAll({
  attributes: ['userId', [sequelize.fn('count', sequelize.col('id')), 'cnt']],
  group: ['userId'],
  having: sequelize.where(sequelize.fn('count', sequelize.col('id')), { [Op.gt]: 5 })
});

// Transaction
await sequelize.transaction(async (t) => {
  await Account.update({ balance: literal('balance - 100') }, { where: { id: from }, transaction: t });
  await Account.update({ balance: literal('balance + 100') }, { where: { id: to },   transaction: t });
});

// Raw SQL
const [results] = await sequelize.query('SELECT * FROM Users WHERE id = :id', {
  replacements: { id: 5 }, type: QueryTypes.SELECT
});
```

### Migrations
- Hand-written in `migrations/` folder
- `sequelize-cli` to generate, run, undo

### Pros
- Mature; lots of plugins
- Active Record familiarity (Rails-like)
- Flexible — both Active Record and instance methods

### Cons
- TS types are community-maintained (varies)
- Eager loading default → JOINs can explode rows
- Implicit timestamps / hooks can hide behavior
- The `literal()` escape hatch is needed often

---

## TypeORM

### Mental Model — TypeORM's dual personality

> TypeORM tries to be **both Active Record and Data Mapper**, with **decorator-based schema** baked into class definitions. That sounds flexible, but it's the source of most TypeORM pain:
>
> - Decorators predate stable TS decorator semantics → upgrading TS sometimes breaks things.
> - Active Record style (`user.save()`) and Repository style (`userRepo.save(user)`) coexist; team conventions drift.
> - Eager-by-default on some relations bites you; lazy proxies bite you the rest of the time.
> - Maintenance has been spotty; some bugs sit for years.
>
> Reach for TypeORM when you want **decorator-style entities in TS and rich relations**. Be ready to write `QueryBuilder` for anything non-trivial.

### Entity definition

```typescript
@Entity()
class User {
  @PrimaryGeneratedColumn() id: number;
  @Column({ unique: true }) email: string;
  @Column() name: string;
  @OneToMany(() => Order, o => o.user) orders: Order[];
}

@Entity()
class Order {
  @PrimaryGeneratedColumn() id: number;
  @Column() status: string;
  @Column() total: number;
  @ManyToOne(() => User, u => u.orders) user: User;
}
```

### Queries

```typescript
// Repository
const userRepo = dataSource.getRepository(User);

// Find with relations
const users = await userRepo.find({
  where: { email: Like('%@acme.com') },
  relations: { orders: true }
});

// QueryBuilder (more SQL-like)
const users = await userRepo
  .createQueryBuilder('u')
  .leftJoinAndSelect('u.orders', 'o', 'o.status = :s', { s: 'PAID' })
  .where('u.email LIKE :pattern', { pattern: '%@acme.com' })
  .orderBy('u.createdAt', 'DESC')
  .getMany();

// Transaction
await dataSource.transaction(async (manager) => {
  await manager.update(Account, { id: from }, { balance: () => 'balance - 100' });
  await manager.update(Account, { id: to },   { balance: () => 'balance + 100' });
});

// Raw SQL
const rows = await dataSource.query('SELECT * FROM "user" WHERE id = $1', [id]);
```

### Migrations
```bash
typeorm migration:generate -n AddOrders -d data-source.ts
typeorm migration:run
```

### Pros
- Two styles: Repository (Data Mapper) or Active Record
- Decorator-based entities are concise
- QueryBuilder is powerful when needed

### Cons
- TS decorators sometimes lag TS itself (breakage on TS upgrades)
- Maintenance has been spotty
- Subtle eager-loading footguns
- Some migrations generated incorrectly — review heavily

---

## Hibernate / JPA (Java)

### Mental Model — Hibernate's worldview

> Hibernate is the **most-fully-formed ORM in any ecosystem**. It implements every classic pattern — Unit of Work, Identity Map (L1 cache), L2 shared cache, snapshot-diff dirty checking, lazy proxies, multi-level fetch strategies, optimistic + pessimistic locking, batch flushes.
>
> The price is **complexity**. Hibernate has its own query language (HQL/JPQL), its own session lifecycle states (Transient → Managed → Detached → Removed), and a reputation for "spooky action at a distance" — a property change inside one service can flush an UPDATE 200 lines later when the transaction commits.
>
> If you treat Hibernate like a CRUD library you'll be miserable. If you understand sessions, fetch strategies, and the cache layers, it's exceptionally powerful.

If your interview is Java-side:
- Most mature ORM ecosystem; powerful but complex
- Heavily relies on **JPA spec** (Hibernate is the most popular implementation)
- **Common interview Q**: difference between `EntityManager.find` (cache + DB) vs `getReference` (lazy proxy)
- **LazyInitializationException** — accessing a lazy relation outside a session
- **Caching layers**: L1 (session/identity map), L2 (shared across sessions; Ehcache/Hazelcast)
- N+1 fixes: `@BatchSize`, `JOIN FETCH` in JPQL, `@EntityGraph`
- **Open Session In View** anti-pattern: keeps session open during view rendering; hides query cost, easy N+1

---

## SQLAlchemy (Python)

### Mental Model — SQLAlchemy's two-layer design

> SQLAlchemy is uniquely split into two layers, and understanding the split is half the battle:
>
> - **Core** (lower layer) — a SQL expression language and query builder. Tables, columns, `select()`, `insert()`. No ORM. You think in SQL.
> - **ORM** (upper layer, built on Core) — `Session`, mapped classes, Unit of Work, Identity Map, lazy loading. Conceptually a Python Hibernate.
>
> Most Python projects use the ORM. Heavy-read or analytics code drops to Core. Both share the same connection / transaction layer.

### Example (ORM layer, 2.x style)

```python
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

with Session(engine) as session:
    stmt = (
        select(User)
        .options(selectinload(User.orders))   # avoids N+1
        .where(User.email.endswith("@acme.com"))
    )
    users = session.scalars(stmt).all()
    users[0].name = "Bob"        # dirty tracked
    session.commit()             # UPDATE flushed
```

### Pros
- Most powerful Python ORM; full Unit of Work + Identity Map
- Excellent low-level escape hatch (Core)
- Mature, well-documented, used by FastAPI/Flask shops
- `selectinload` / `joinedload` give explicit control over fetch strategy

### Cons
- Steep learning curve; two layers + many ways to do the same thing
- Async support is recent (2.x); ecosystem still catching up
- Sessions and transactions are easy to misuse outside a web framework

---

## Django ORM (Python)

### Mental Model — Django's pragmatic Active Record

> Django ORM is **opinionated Active Record bundled with the web framework**. Models live in `models.py`, queries are `Model.objects.filter(...)`, and there's no separate session — the connection is request-scoped by the framework.
>
> Django emphasizes **convenience over flexibility**. Migrations are auto-generated from model diffs (`makemigrations`); admin UI comes for free; querysets are lazy and chainable.
>
> Pain points:
> - N+1 is rampant unless you remember `select_related` (FK JOIN) and `prefetch_related` (separate SELECT IN).
> - Hard to use outside Django (it's tightly coupled).
> - Complex queries devolve into `.extra()` or raw SQL.

### Example

```python
# Naive — N+1
for user in User.objects.all():
    print(user.profile.bio)   # one extra query per user

# Fixed with select_related (JOIN)
for user in User.objects.select_related("profile"):
    print(user.profile.bio)   # 1 query total

# Fixed with prefetch_related (select-IN for many-to-many / reverse FK)
users = User.objects.prefetch_related("orders")
for user in users:
    print(len(user.orders.all()))   # 2 queries total
```

### Pros
- Tightest framework integration (admin, auth, forms all wired in)
- Auto migrations (with caveats)
- Querysets are lazy + chainable — composable views

### Cons
- Coupled to Django; can't use cleanly outside
- N+1 is the default mistake; juniors hit it constantly
- Less powerful than SQLAlchemy for complex queries

---

## When to use raw SQL (despite having an ORM)

> The rule is: **drop to SQL when the ORM is fighting you, not before.** Premature raw-SQL is hard to maintain and hides behind the abstraction.

Drop down when:

1. **DB-specific features** — Postgres `LATERAL JOIN`, recursive CTEs, JSONB operators, full-text search, window functions. ORMs cover ~80% of SQL; 20% is awkward or impossible.
2. **Bulk operations** — inserting / updating 10k+ rows. ORM per-object overhead becomes the bottleneck; use `COPY` or multi-row INSERTs.
3. **Hot read paths** — endpoints that run 1000s of times per minute. Hand-tuned SQL plus a thin DTO is often 5–10× faster than full hydration.
4. **Reports / analytics** — complex aggregations with GROUP BY ROLLUP, percentiles, pivots. The ORM model is the wrong abstraction.
5. **Migrations involving data** — backfills, restructures. SQL is more readable here.
6. **Streaming exports** — bypass hydration entirely; use cursor / server-side cursor.

### Stay with the ORM when:

- CRUD endpoints with simple relations
- Writes that go through domain validation / hooks
- Anywhere type safety + refactoring matters more than the last 5% of perf

### Hybrid pattern: CQRS at the data layer

```
   ┌──────────────────────────┐         ┌──────────────────────────┐
   │       Write side         │         │        Read side          │
   │  - Domain models         │         │  - Raw SQL / projections  │
   │  - ORM (Prisma/Hibernate)│         │  - Kysely / hand SQL      │
   │  - Unit of Work          │         │  - DTOs (no hydration)    │
   │  - Validations + hooks   │         │  - Optimized for endpoint │
   └──────────────┬───────────┘         └──────────────┬────────────┘
                  │                                    │
                  └───────────► same DB ◄──────────────┘
```

Use the ORM where correctness matters; use raw SQL where performance matters. Don't pick one for the whole app.

---

## Migrations strategy (any ORM)

Production-safe sequence for changes:

1. **Add column (nullable, no default)** — fast, additive
2. **Backfill in batches** — `UPDATE … LIMIT 10000` in a loop with sleep
3. **Add NOT NULL / default** — quick, since data is filled
4. **Deploy new code that uses the column**
5. **Remove old code paths**
6. **Drop old column (in a later release)**

Renames are similar: add new column → dual-write → backfill → swap reads → drop old.

Avoid generated migrations that:
- Recreate tables (`DROP TABLE` then `CREATE TABLE`)
- Add NOT NULL columns without default
- Create indexes without `CONCURRENTLY` (Postgres)
- Lock tables for long

### Online schema change tools

- **Postgres**: native `CREATE INDEX CONCURRENTLY`, `pg_repack`, `pg-osc`
- **MySQL**: `pt-online-schema-change` (Percona), `gh-ost` (GitHub) — make ALTER online for large tables

---

## Connection pooling

### Node (Postgres)
- `node-postgres` pool: default 10 connections
- Tune via `max`
- Behind **PgBouncer** in transaction-mode for many app instances

### Java
- HikariCP: default 10
- Idle timeout, max lifetime, leak detection
- Rule of thumb: pool size = ((core_count * 2) + effective_spindle_count) per instance, conservatively

### Pool exhaustion
- Symptoms: request timeouts; lots of `acquireConnection` waits
- Causes: long-running queries, leaked connections (not released), pool too small
- Tools: pool stats in metrics; `pg_stat_activity` showing many idle-in-transaction

---

## Common interview questions

1. Compare Prisma, Sequelize, TypeORM.
2. Why does Prisma not have lazy loading?
3. How do you handle a long-running migration in production?
4. What is the difference between Active Record and Data Mapper?
5. How do transactions work in Prisma's interactive vs array mode?
6. When would you use raw SQL despite having an ORM?
7. How do connection pools work?
8. How do you avoid N+1 in each ORM?
9. How do you do an additive-only column rename?
10. What's `Open Session In View` and why is it bad?
11. How do you stream a million rows?
12. Migration rollback strategy.

---

## Detailed answers

### 1. Compare
- **Prisma**: typed, schema-first, safer; no lazy loading; query builder feel
- **Sequelize**: Active Record, mature, loose types, easy footguns
- **TypeORM**: decorator entities, two styles, decorator/TS friction
Default: Prisma for greenfield.

### 2. Prisma no lazy loading
By design — lazy loading is the #1 source of accidental N+1. Prisma forces you to declare relations explicitly via `include`/`select`, making query cost visible.

### 3. Long-running migration
1. Generate migration; review SQL
2. Use `CONCURRENTLY` for index creation
3. Add columns nullable; backfill in batches; then add NOT NULL
4. For huge ALTERs, use gh-ost / pt-online-schema-change
5. Deploy migration *before* code that needs the new column (additive)
6. Test in staging with prod-like data size

### 4. Active Record vs Data Mapper
Active Record: object knows how to persist itself (`user.save()`). Data Mapper: separate repository/mapper persists plain objects. Data Mapper is cleaner for complex domains.

### 5. Prisma transactions
- **Interactive** (`async tx => …`): you can branch, read, decide. Holds a connection. Use for business logic.
- **Array**: list of operations atomically applied. Faster, but no conditional logic.
- Pick interactive when needed; array for simple multi-write atomicity.

### 6. Raw SQL despite ORM
- Complex queries (CTEs, window functions, set ops)
- Performance-critical hot paths
- Bulk INSERT/UPDATE (10k+ rows)
- DB-specific features (Postgres LATERAL, JSONB ops, full-text search)
- Reports

### 7. Connection pool
A bounded set of DB connections reused across requests. Sized per app instance. Total connections to DB = pool size × app instances. Must stay under DB `max_connections`. Use PgBouncer for thousands of app instances.

### 8. N+1 prevention per ORM
- **Prisma**: `include` / `select`; default select-IN strategy avoids cartesian
- **Sequelize**: `include: [Model]`; or batch fetch with `where: { fk: [...ids] }`
- **TypeORM**: `relations: { foo: true }` or `leftJoinAndSelect`; `@BatchSize` on entity for Hibernate-like
- All: DataLoader pattern at the resolver level for GraphQL

### 9. Additive column rename
1. Add `new_name` column
2. Deploy app reading from `old_name` and writing to both (dual-write)
3. Backfill `new_name` from `old_name`
4. Deploy app reading from `new_name` and writing to both
5. Deploy app reading and writing only `new_name`
6. Drop `old_name`

Never rename in a single migration in production.

### 10. Open Session In View
Spring pattern: keep Hibernate session open until the view renders. Causes lazy queries during template rendering — hidden N+1, hard to test, leaks DB connections in slow views. Disable in modern apps.

### 11. Stream a million rows
- Postgres: server-side cursor; in Node use `pg-query-stream`
- Mongo: cursor with `batchSize`
- All ORMs offer a streaming API; bypass hydration for huge result sets
- For DB-to-file export: `COPY TO` is even faster

### 12. Rollback strategy
- Forward-only migrations in many shops (no down-migration)
- If rollback needed: revert code, then revert schema in a follow-up migration
- Backups + PITR as the ultimate safety net
- Avoid destructive ops in single migration; multi-step rollouts allow rollback at each step

---

## Practical coding examples

### Prisma: pagination (keyset)
```typescript
const items = await prisma.event.findMany({
  where: { ts: { lt: cursorTs } },
  orderBy: { ts: 'desc' },
  take: 50
});
```

### Sequelize: bulk insert
```javascript
await Order.bulkCreate(orders, { ignoreDuplicates: true });
```

### TypeORM: query with parameters (avoid SQL injection)
```typescript
await dataSource.query('SELECT * FROM users WHERE email = $1', [email]);
```

### Prisma: optimistic lock (manual)
```typescript
const updated = await prisma.product.updateMany({
  where: { id, version: expectedVersion },
  data: { price, version: { increment: 1 } }
});
if (updated.count === 0) throw new ConflictError();
```

### Migration: safe NOT NULL add (Postgres ≥ 11)
```sql
-- Step 1
ALTER TABLE orders ADD COLUMN currency TEXT;
-- Step 2: backfill
UPDATE orders SET currency = 'USD' WHERE currency IS NULL;
-- Step 3: add CHECK
ALTER TABLE orders ADD CONSTRAINT chk_currency_not_null CHECK (currency IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT chk_currency_not_null;
-- Step 4: convert to NOT NULL using the validated constraint
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;
ALTER TABLE orders DROP CONSTRAINT chk_currency_not_null;
```

### PgBouncer in transaction mode caveats
- No session-level features (`SET LOCAL` is fine; `PREPARE` is not)
- Advisory locks must be transaction-scoped (`pg_advisory_xact_lock`)
- Some libraries need adjustments (Sequelize is fine; older JDBC drivers can break)

---

## Common mistakes

- Picking an ORM by popularity instead of by team familiarity
- Letting ORM defaults bite you (eager loading, autocommit assumptions)
- Generated migrations applied without review
- Renaming or dropping columns in a single migration
- Pool too small / too large
- Decorators conflicting with TypeScript versions (TypeORM-specific pain)
- Storing all dates in app timezone instead of UTC
- Calling external APIs inside a transaction

---

## Senior engineer discussion points

- **Schema as source of truth** — schema file (Prisma) vs decorators on classes (TypeORM) vs migrations (Sequelize). Each has trade-offs.
- **CQRS pattern** — write through ORM, read through raw SQL / projections
- **Connection pool through PgBouncer** — required for serverless / many instances
- **Migration safety** — every migration reviewed for: lock duration, backfill cost, dependency on app deploy order
- **Generated client size / cold start** — Prisma client is large; matters for Lambda
- **ORM vs no-ORM debate** — Kysely / Drizzle for type-safe builders without ORM overhead; gaining traction
- **Logical replication for cross-system sync** — beyond ORM scope, often the right answer for read replicas / analytics

---

## Common beginner confusion

### "Prisma is just a fancy Sequelize"
**No** — they share *zero* design philosophy. Prisma is a schema-first, typed, no-lazy-loading query builder + hydrator. Sequelize is a classic Active Record ORM with mutable models, lazy proxies, and JOIN-based eager loading. Their bugs and pain points are entirely different.

### "Hibernate, TypeORM, SQLAlchemy are basically the same"
**Half-true.** They share the Data Mapper + Unit of Work pattern, but:
- Hibernate has the deepest cache layers (L1 + L2 shared cache, query cache).
- SQLAlchemy splits cleanly between Core (SQL builder) and ORM (mapped classes).
- TypeORM tries to be both AR and DM, with decorator-driven metadata.

### "Django ORM is good enough for everything"
**Up to mid-scale.** Past ~50 RPS sustained or complex query needs, you'll be writing `.extra()` or raw SQL inside Django patterns. SQLAlchemy gives more headroom in the same ecosystem.

### "I should pick the ORM with the best benchmarks"
**Wrong question.** ORM throughput is rarely the bottleneck; **misuse** is. A team that knows TypeORM well will out-ship a team learning Prisma, even if Prisma "benches" faster. Pick what the team can use safely.

### "Once we pick an ORM we're locked in"
**Less than you think for reads, more than you think for writes.** Domain models, decorators, and migrations are sticky. But the read layer can usually be migrated piecemeal (start writing raw SQL or Kysely for new endpoints; leave existing ORM code as-is).

### "Prisma's lack of lazy loading is a downside"
**It's a feature.** Lazy loading is the #1 source of accidental N+1 in TypeORM / Hibernate codebases. Prisma's explicit `include` makes the cost visible.

### "Migrations are auto-generated, so I trust them"
**Never.** Auto-generated migrations don't know about uptime, locking, table size, or running app instances. They may `DROP TABLE; CREATE TABLE` for trivial changes. Always review and rewrite for safety.

---

## Step-by-step walkthrough — picking an ORM for a new Node service

> Scenario: greenfield Node + TypeScript backend, Postgres, ~10 entities, will ship to production in 3 months.

```
1. Do we need DDD-grade domain modeling, aggregates, complex invariants?
   ├─ Yes → TypeORM Repository (Data Mapper) or NestJS + TypeORM
   └─ No → continue
2. Is type safety a priority? (Most teams: yes)
   ├─ Yes → Prisma is the leading candidate
   └─ No → Sequelize remains viable
3. Do we have many one-to-many relations we'll fetch together?
   ├─ Yes → Prisma's select-IN is a big win
   └─ No → either works
4. Do we have unusual SQL needs (LATERAL, full-text, recursive CTE)?
   ├─ Yes → ensure the ORM has a clean raw-SQL escape hatch
   │         (Prisma $queryRaw is good; TypeORM .query() is OK; Sequelize is OK)
   └─ No → continue
5. Will we deploy via Lambda / cold-start sensitive?
   ├─ Yes → Prisma client is large (~50MB) — measure cold start;
   │         Sequelize/Kysely are lighter
   └─ No → Prisma OK
6. Team familiarity?
   └─ Pick what you can ship safely.
```

For most modern Node services: **Prisma**, with `$queryRaw` for the 5% that needs it.

---

## Interview storytelling — comparison conversations

### Story 1: "Compare Prisma vs TypeORM vs Sequelize for a Node service"

> "Prisma is my default for greenfield because it's schema-first, generates types from the schema, has no lazy loading (so no accidental N+1), and uses select-IN by default (no cartesian explosion). The trade-off is that the client is large and there's no traditional session / Unit of Work — every query is its own round trip.
>
> TypeORM I'd reach for if I needed decorator-style entities, two-style flexibility (AR + Repository), or rich `QueryBuilder` for complex SQL. The cost is decorator-TS friction, eager-loading footguns, and slower maintenance. I'd be careful around upgrades.
>
> Sequelize I'd use for legacy code or if the team is steeped in Rails/Active Record. Its types are weak, eager loads JOIN by default, and footguns are plentiful — but it's mature and well-known.
>
> If the project needs lots of complex SQL, I might pair Prisma (writes) with Kysely (reads) — CQRS at the data layer."

### Story 2: "Walk me through how you'd add a NOT NULL column safely in production"

> "Never in one step. Sequence is:
> 1. Add the column as **nullable**, no default. This is a fast metadata change.
> 2. Deploy code that **writes** to the new column on inserts/updates, but doesn't read it.
> 3. **Backfill** existing rows in batches — `UPDATE … WHERE id BETWEEN x AND y` in chunks of 10k, with a sleep between batches to avoid replication lag.
> 4. Add a `CHECK ... NOT VALID` constraint, then `VALIDATE` it — this avoids locking the table.
> 5. Switch the constraint to `SET NOT NULL` once validated.
> 6. Deploy code that **reads** from the new column.
> 7. Drop the old column in a later release if it's a rename.
>
> If the table is huge and the migration must be online, I'd use `pg_repack` or, on MySQL, `gh-ost` / `pt-online-schema-change`."

### Story 3: "Why did you pick Hibernate over a query builder?"

> "We had ~150 entities, complex aggregates (Order → LineItems → Discounts → AppliedPromos), and the domain logic was the heart of the product. With a query builder, every save would require manually orchestrating inserts and updates in the right order to satisfy FKs. Unit of Work plus dirty tracking made the domain code clean — `order.applyPromo(p)` just mutated the in-memory graph and the commit handled persistence.
>
> Cost was complexity: we trained the team on session lifecycle, disabled Open Session In View, set fetch defaults to lazy with explicit `JOIN FETCH` or `@EntityGraph` for known access patterns, and added L2 cache (Hazelcast) for read-mostly reference data."

---

## Senior engineer mental model — when each ORM "fits"

```
   Complexity of domain →

   Low                    Medium                  High
   ─────────────────────────────────────────────────────────
   Prototype              Production web         Enterprise / DDD
   Active Record          Prisma + raw SQL       Hibernate / SQLAlchemy
   Sequelize / Eloquent   TypeORM (Repository)   Data Mapper + Unit of Work
   Django ORM             Django ORM + raw       (with care)

   ←——— ship faster ——————————————— maintain longer ———→
```

There is no universal "best ORM." There is only "best given your team, domain, and lifespan."

---

## Revision notes

- **Prisma**: typed, schema-first, no lazy, select-IN by default → safe
- **Sequelize**: AR-style, mature, eager-JOIN risks
- **TypeORM**: decorators, two styles, decorator/TS friction
- All three: support transactions; choose `Serializable` for write-skew-prone ops; retry on conflict
- Drop to raw SQL when ORM is fighting you
- Migrations: additive only in prod; multi-step renames; review generated SQL
- Connection pools: tune sizes; PgBouncer for many instances
- `CREATE INDEX CONCURRENTLY` (Postgres) / gh-ost (MySQL) for online schema changes
- Generated migrations are starting points, not gospel
