# Prisma vs Sequelize vs TypeORM (and others)

## Why this matters in backend interviews

- Backend candidates are expected to know at least one ORM deeply and **be able to justify the choice**.
- "Why Prisma over TypeORM?" is a real interview question at Node-heavy shops.
- Migration strategy in production is a senior-signal topic.

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

If your interview is Java-side:
- Most mature ORM ecosystem; powerful but complex
- Heavily relies on **JPA spec** (Hibernate is the most popular implementation)
- **Common interview Q**: difference between `EntityManager.find` (cache + DB) vs `getReference` (lazy proxy)
- **LazyInitializationException** — accessing a lazy relation outside a session
- **Caching layers**: L1 (session/identity map), L2 (shared across sessions; Ehcache/Hazelcast)
- N+1 fixes: `@BatchSize`, `JOIN FETCH` in JPQL, `@EntityGraph`
- **Open Session In View** anti-pattern: keeps session open during view rendering; hides query cost, easy N+1

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
