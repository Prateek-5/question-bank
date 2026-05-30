# Prisma vs TypeORM — Node ORM decision framework

## Source / Origin
- Real-world Node.js backend decision in every greenfield project since ~2021.
- Prisma docs: <a href="https://www.prisma.io/docs" target="_blank" rel="noopener noreferrer">https://www.prisma.io/docs</a>
- TypeORM docs: <a href="https://typeorm.io" target="_blank" rel="noopener noreferrer">https://typeorm.io</a>
- Honorable mentions: Drizzle (rising), Sequelize (legacy but alive), Kysely (query builder, not ORM), MikroORM (the closest Node has to a real Unit-of-Work ORM).

## Why this question matters in interviews
Senior Node engineers are expected to make this choice with reasons, not vibes. Picking Prisma for a 100-table legacy DB without thinking through migrations, raw SQL, or transaction nesting will burn you 6 months in. Picking TypeORM for a greenfield Postgres app means you'll waste a sprint debugging change-detection vs `save()` confusion. The interviewer wants to hear a **decision framework**: schema source-of-truth, transaction model, type safety, migration strategy, raw-SQL escape hatch, ecosystem fit.

## Concepts involved

### The 30-second elevator pitch

| Dimension | Prisma | TypeORM |
|---|---|---|
| Paradigm | Query builder + generated client | Active Record / Data Mapper ORM |
| Schema source of truth | `schema.prisma` (DSL) | TypeScript decorators / entities |
| Type safety | Generated client, exhaustive | Decorator-inferred, weaker on complex queries |
| Migrations | `prisma migrate` (declarative diff) | `typeorm migration:generate` (imperative) |
| Transaction model | Stateless; `$transaction([...])` array or interactive callback | Unit-of-Work via `EntityManager` + `QueryRunner` |
| Identity map | None | Yes (in `EntityManager`) |
| Change tracking | None — explicit `update()` | Yes — `save()` diffs against load snapshot |
| Raw SQL | `$queryRaw` (tagged template, typed) | `query()` (untyped) |
| Joins/N+1 | `include` / `select` — clear, but rigid | Eager / lazy / join builder — flexible, footgun-prone |
| Multi-tenant | Awkward (per-tenant DB URL or middleware) | Easier (per-request EntityManager) |
| Ecosystem | Studio, Pulse, Accelerate (managed) | Mature, no managed services |
| Bundle size | Larger (rust engine binary) | Smaller |
| Learning curve | Flat | Steep (decorators, metadata, sync surprises) |

### Edge cases / interview traps

1. **Prisma has no identity map.** Two `prisma.user.findUnique({where:{id:1}})` calls return two distinct objects. `===` is false.
2. **Prisma `$transaction([...])` is a batch, not a session.** Each operation is independent SQL within one DB transaction. No dirty checking, no cascades you didn't write.
3. **Prisma `$transaction(async (tx) => {...})` is interactive.** That's the right mode for "read then write" logic. Default timeout 5s — long-running transactions need `timeout` option.
4. **TypeORM `save()` is overloaded** — INSERT if no PK, UPSERT if PK exists. People expect `update()` semantics; they get UPSERTs that overwrite columns to null.
5. **TypeORM cascade is decorator-driven** and triggers on `save()`. Easy to ship a bug where saving a User wipes its Orders.
6. **TypeORM `synchronize: true`** — DDL run on app start. Convenient in dev, catastrophic if accidentally enabled in prod.
7. **Prisma migrations are declarative**: change the schema file, run `prisma migrate dev`. Migration history file is generated. Production: `prisma migrate deploy`.
8. **TypeORM migrations are imperative**: `migration:generate` diffs, but you maintain a `up()` / `down()` file by hand.
9. **Prisma doesn't support DB views or stored procedures natively.** Use `prisma.$queryRaw` or generate views via SQL migrations and `@map`.
10. **TypeORM relations require `relations: ['orders']`** at query time OR `eager: true` on the decorator. Forget both → relation is undefined, not lazy-loaded (since v0.3).

## Mental Model

```
                  ┌────────────────────────────────────┐
                  │             Your app               │
                  └────────────────┬───────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
   ┌──────────▼──────────┐                ┌─────────────▼─────────────┐
   │      PRISMA         │                │         TYPEORM           │
   │                     │                │                           │
   │   schema.prisma     │                │   @Entity decorators       │
   │       ↓             │                │       ↑ (TS reflects)      │
   │   codegen           │                │   EntityMetadata           │
   │       ↓             │                │       ↓                   │
   │   typed client      │                │   EntityManager           │
   │       ↓             │                │   ├─ Identity map         │
   │   query engine      │                │   ├─ Change tracker       │
   │   (Rust binary)     │                │   └─ Cascade/flush logic  │
   │       ↓             │                │       ↓                   │
   │   one SQL per call  │                │   QueryRunner             │
   └─────────────────────┘                └───────────────────────────┘

   "Statelessness + types"               "Stateful + flexible"
```

Choose Prisma when you want **predictability, type safety, and migrations as code**. Choose TypeORM when you want **change tracking, cascades, and richer transaction shapes** — and you're willing to accept the foot-guns.

## Why interviewers care

- Reveals whether you choose tools by **constraint** or by **fashion**.
- Tests knowledge of UoW vs stateless ORMs (general concept).
- Shows you've felt real production pain — `synchronize: true` deletes, Prisma raw-SQL escape, schema drift.

## Common beginner confusion

- "Prisma is type-safe, TypeORM isn't." Both are typed. Prisma's types are *exhaustive* and generated; TypeORM's are decorator-inferred and weaker on complex query builders.
- "Prisma is faster." Wire-format identical; difference is microseconds. Choose for ergonomics, not speed.
- "TypeORM is dead." Not maintained as aggressively as Prisma but still active. Drizzle is the rising challenger.
- "Prisma can't do raw SQL." It can — `$queryRaw` is tagged-template, type-safe with generics.

## Brute force approach

Pick one because a tweet liked it. Six months later you're rewriting because the choice doesn't fit the constraints. Don't.

## Optimal approach — decision framework

Answer these in order:

1. **Schema source of truth: code or DB?**
   - DB-first / legacy schema → TypeORM (entity classes can `synchronize: false` and reflect DB).
   - Code-first / greenfield → Prisma (schema.prisma is one file, easy diff review).
2. **Do you need identity map / change tracking / cascades?**
   - Yes (rich domain models) → TypeORM or MikroORM.
   - No (CRUD-heavy, RPC-style services) → Prisma.
3. **Migration discipline.**
   - You want declarative diffs, generated history → Prisma.
   - You want fine-grained imperative `up/down` → TypeORM.
4. **Raw SQL frequency.**
   - Often → TypeORM (or Kysely/Drizzle) — easier query builder fallback.
   - Rare → Prisma is fine; `$queryRaw` handles edge cases.
5. **Multi-tenant.**
   - Per-tenant DB → both work; Prisma needs a client cache by URL.
   - Per-tenant schema → TypeORM's EntityManager swapping is cleaner.
6. **Team familiarity.**
   - Java/.NET background → TypeORM feels familiar (Active Record / Data Mapper).
   - Rails / functional background → Prisma's mental model lighter.

## Solution

### Prisma — canonical service

```typescript
// schema.prisma
generator client { provider = "prisma-client-js" }
datasource db   { provider = "postgresql"; url = env("DATABASE_URL") }

model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  orders    Order[]
  createdAt DateTime @default(now())
}

model Order {
  id      Int    @id @default(autoincrement())
  userId  Int
  user    User   @relation(fields: [userId], references: [id])
  total   Int
  items   Item[]
}
```

```typescript
// service.ts
import { PrismaClient, Prisma } from '@prisma/client';
const prisma = new PrismaClient();

export async function placeOrder(userId: number, items: ItemInput[]) {
  return prisma.$transaction(async (tx) => {
    const user = await tx.user.findUniqueOrThrow({ where: { id: userId } });

    const order = await tx.order.create({
      data: {
        userId: user.id,
        total: items.reduce((s, i) => s + i.price * i.qty, 0),
        items: { create: items.map(i => ({ sku: i.sku, qty: i.qty, price: i.price })) },
      },
      include: { items: true },
    });

    return order;   // exhaustively typed: { id, userId, total, items: Item[] }
  }, { timeout: 10_000, isolationLevel: Prisma.TransactionIsolationLevel.RepeatableRead });
}
```

### TypeORM — canonical service

```typescript
// entities/User.ts
@Entity()
export class User {
  @PrimaryGeneratedColumn() id!: number;
  @Column({ unique: true }) email!: string;
  @OneToMany(() => Order, o => o.user, { cascade: ['insert'] })
  orders!: Order[];
}

// service.ts
export class OrderService {
  constructor(private ds: DataSource) {}

  async placeOrder(userId: number, items: ItemInput[]) {
    return this.ds.transaction(async (manager) => {
      const user = await manager.findOneByOrFail(User, { id: userId });

      const order = manager.create(Order, {
        user,
        total: items.reduce((s, i) => s + i.price * i.qty, 0),
        items: items.map(i => manager.create(Item, i)),
      });

      await manager.save(order);    // cascade inserts items via decorator
      return order;
    });
  }
}
```

### Migrations

```bash
# Prisma — declarative
# 1. Edit schema.prisma
# 2. Generate + apply migration
prisma migrate dev --name add_orders

# CI/CD
prisma migrate deploy
```

```bash
# TypeORM — imperative
# 1. Edit entity
# 2. Generate migration file (diff of current vs desired)
typeorm migration:generate -n AddOrders
# 3. Inspect and edit the .ts file
# 4. Run
typeorm migration:run
```

## Step-by-step design walk-through

Scenario: 4-engineer team, Postgres, greenfield SaaS, ~30 tables, multi-tenant (one DB per tenant).

1. **Schema source**: code-first → Prisma is favored.
2. **Domain richness**: order/payment domain has cascades and computed state → tilt toward TypeORM.
3. **Migrations**: team wants reviewable PRs of schema changes → Prisma's single-file schema wins.
4. **Multi-tenant**: per-DB. Both can do it; Prisma needs a `Map<TenantId, PrismaClient>` cache. TypeORM has built-in per-tenant `DataSource` registry.
5. **Raw SQL**: ~10% of queries — analytics aggregates. Prisma's `$queryRaw` handles it.
6. **Team experience**: 2 ex-Rails, 1 ex-Java, 1 junior. Prisma's flat curve helps the junior; ex-Java engineer can mentor on advanced patterns.

Decision: **Prisma**, with `Map<TenantId, PrismaClient>` and connection-pool bounding. Cascade behavior re-implemented explicitly in service code (no magic).

If the scenario flipped — DB-first migration of a 200-table legacy system with rich domain logic — switch to TypeORM.

## How to think aloud in the interview

> "I don't pick by reputation; I pick by constraint. Six dimensions:
>
> 1. **Schema source of truth.** Code-first → Prisma. DB-first → TypeORM.
> 2. **Need identity map / change tracking / cascades?** Yes → TypeORM (Active Record / Data Mapper). No → Prisma.
> 3. **Migration model.** Declarative diff → Prisma. Imperative up/down → TypeORM.
> 4. **Raw SQL frequency.** Heavy → TypeORM or Kysely. Light → Prisma's `$queryRaw`.
> 5. **Multi-tenant shape.** Per-DB → either. Per-schema → TypeORM.
> 6. **Team background.**
>
> Default for greenfield Postgres + small team: **Prisma**, because the schema-as-one-file model produces reviewable migrations and the generated client is exhaustively typed. I lose identity map and change tracking — fine, I write services that explicitly call `update()`.
>
> Default for brownfield with rich domain: **TypeORM**, because I get the UoW for cascades and the EntityManager for multi-tenant.
>
> Two things I always do regardless: turn off `synchronize: true` in TypeORM, and cap the Prisma connection pool below DB max."

## Important takeaways

- **Decision framework, not religion.** Six dimensions: schema source, change-tracking need, migrations, raw SQL, multi-tenant, team.
- **Prisma = stateless + types.** No identity map. Explicit operations. Migrations as declarative diffs.
- **TypeORM = stateful UoW.** Identity map, change tracking, cascades, decorator-driven.
- **Critical foot-guns**: TypeORM `save()` overload, `synchronize: true`, Prisma transaction default 5s timeout, Prisma's lack of identity map breaking `===`.
- **Raw SQL escape hatches**: Prisma `$queryRaw` (typed via generics), TypeORM `query()` (untyped) or `createQueryBuilder` (typed).
- **Drizzle is the rising third option** — typed query builder, no ORM-style UoW.

## Variants

1. **"Why not Sequelize?"** Older API, weaker TS support, callback legacy. Maintained but rarely chosen for new projects.
2. **"Why not Kysely / Drizzle?"** Both are query builders, not ORMs. No change tracking, no migrations as part of the package (Drizzle has its own). Great if you want SQL-shaped code with types.
3. **"How do you avoid N+1 in each?"** Prisma: `include` / `select` at query time. TypeORM: `relations: [...]` option or `leftJoinAndSelect` in builder.
4. **"How does each handle soft-delete?"** Prisma: middleware (extension) + `deletedAt` column. TypeORM: `@DeleteDateColumn` and `softDelete()` method.
5. **"What about Edge runtimes (Cloudflare Workers, Vercel Edge)?"** Prisma supports via Accelerate or Driver Adapters. TypeORM is Node-only — no Edge story.
6. **"Connection pooling in serverless?"** Both need a pooler (PgBouncer/Prisma Accelerate). TypeORM connection-per-DataSource scales worse than Prisma's Rust engine.

## Revision notes

> **prisma-vs-typeorm — 60 second recap**
> - Prisma = stateless query builder + generated client + declarative migrations.
> - TypeORM = Unit-of-Work ORM with identity map, change tracking, decorator cascades.
> - Decision: schema source, need UoW?, migration style, raw SQL %, multi-tenant, team.
> - Prisma default for greenfield small team; TypeORM default for brownfield rich domain.
> - Foot-guns: TypeORM `save()` is INSERT-or-UPSERT, `synchronize: true` in prod = disaster. Prisma `$transaction` default 5s timeout. Prisma no identity map.
> - Raw SQL: Prisma `$queryRaw` (typed), TypeORM `query()`.
> - Drizzle/Kysely = typed query builders, not ORMs — viable third path.
