# Soft delete and its ORM quirks — paranoid mode, query interceptors

## Source / Origin
- The "we never actually delete data" interview question; appears in legal-compliance, audit, multi-tenant contexts.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md`, `02-orm-comparison.md`.

## Why this question matters in interviews
Soft delete looks trivial ("add a `deleted_at` column") but produces a long tail of subtle bugs: forgotten WHERE clauses, unique constraints clashing with soft-deleted rows, eager-load joins pulling deleted children, GDPR / right-to-erasure conflicts. Senior candidates discuss the **trade-offs** and the **enforcement strategy** (interceptor / mixin / global filter / DB view).

## Concepts involved

### Syntax to lock in across ORMs

```typescript
// ============================================================
// TypeORM — `@DeleteDateColumn` enables "paranoid" mode
// ============================================================
@Entity()
class User {
  @PrimaryGeneratedColumn() id!: number;
  @Column() email!: string;
  @DeleteDateColumn() deletedAt?: Date;
}

// Soft delete
await userRepo.softDelete({ id });      // UPDATE users SET deleted_at = NOW() WHERE id = ?

// Normal find — automatically filters out deleted rows
const users = await userRepo.find();    // SELECT ... WHERE deleted_at IS NULL

// Include deleted
const all = await userRepo.find({ withDeleted: true });

// Restore
await userRepo.restore({ id });          // UPDATE ... SET deleted_at = NULL

// Hard delete
await userRepo.delete({ id });           // DELETE FROM users WHERE id = ?

// ============================================================
// Prisma — manual; no built-in soft delete (yet)
// ============================================================
model User {
  id        Int       @id @default(autoincrement())
  email     String    @unique
  deletedAt DateTime?

  @@index([deletedAt])
}

// Every find must include the filter
const users = await prisma.user.findMany({ where: { deletedAt: null } });

// Recommended: extension that adds the filter automatically
prisma.$extends({
  query: {
    user: {
      async findMany({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      },
    },
  },
});

// ============================================================
// SQLAlchemy — global filter via event or query class
// ============================================================
class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)

class User(Base, SoftDeleteMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)

@event.listens_for(Session, "do_orm_execute")
def _filter_soft_deleted(execute_state):
    if execute_state.is_select and not execute_state.execution_options.get("include_deleted"):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(SoftDeleteMixin, lambda cls: cls.deleted_at.is_(None))
        )

// ============================================================
// Hibernate — @SQLDelete + @Where
// ============================================================
@Entity
@SQLDelete(sql = "UPDATE users SET deleted_at = NOW() WHERE id = ?")
@Where(clause = "deleted_at IS NULL")
public class User { ... }
```

### Edge cases / interview traps

1. **Forgotten WHERE clause.** Raw SQL queries (`dataSource.query(...)`) bypass the ORM's soft-delete filter and return deleted rows. Hard-to-catch bug.
2. **Unique constraints clash.** A user soft-deleted with `email = 'a@b.c'` blocks a new user registering the same email. Fix: partial unique index `WHERE deleted_at IS NULL`, or include `deleted_at` in the unique tuple.
3. **Eager-load JOINs include deleted rows.** TypeORM `relations: { posts }` JOINs posts; the filter applies to the root entity, not the children. Posts of a deleted user, or deleted posts of a live user, can leak.
4. **Count discrepancies.** `SELECT COUNT(*) FROM users` (raw) vs `userRepo.count()` differ; one includes soft-deleted, one doesn't. Reporting bugs.
5. **GDPR right-to-erasure.** Soft delete is not deletion. Compliance demands a true purge after a retention period.
6. **Cascade behavior.** When you soft-delete a parent, do children cascade-soft-delete? Most ORMs don't handle this; you must wire it up.
7. **Foreign key integrity.** Deleted parent + live child = orphan. The FK is still valid (parent row exists), but business logic must check `parent.deletedAt`.
8. **Indexes.** `deleted_at` should be indexed for selectivity; partial index `WHERE deleted_at IS NULL` on hot tables can shrink the index 10x.
9. **Migrations.** Adding `deleted_at` to a populated table is a simple ADD COLUMN; but switching from hard to soft delete in code requires backfilling history if you want to recover the deleted rows (you can't — they're gone).
10. **Junction tables.** Many-to-many soft delete is ambiguous: do you soft-delete the link or hard-delete? Usually hard-delete the link, soft-delete the rows.

## Mental Model

```
   Hard delete                      Soft delete
   ───────────                      ───────────

   DELETE FROM users                UPDATE users SET deleted_at = NOW()
   Row gone.                        Row remains, flagged.

   PK reusable.                     PK still occupied.
   FK to it errors.                 FK still valid.
   No audit trail.                  Audit trail in place.
   GDPR-safe by definition.         GDPR purge needed separately.
   No "show me deleted" path.       `withDeleted` flag opens it.

   ASCII filter:

      Normal find:           SELECT ... WHERE deleted_at IS NULL
      Find including:        SELECT ... (no WHERE on deleted_at)
      Find only deleted:     SELECT ... WHERE deleted_at IS NOT NULL
```

The discipline: **a deleted row is invisible by default but addressable on demand.**

## Why interviewers care

- Tests **awareness of business / compliance trade-offs** — audit, restore, GDPR.
- Tests **knowledge of enforcement mechanisms** — query interceptors, partial indexes, global filters.
- Catches the candidate who's never debugged "the deleted user reappeared because we forgot a WHERE."

## Common beginner confusion

- **"Just add `deleted_at` and we're done."** Forgetting the filter on raw queries or JOIN children leads to leaks.
- **"Soft delete fixes everything."** It introduces unique-constraint conflicts, JOIN traps, and GDPR debt.
- **"Cascades automatically follow soft delete."** They don't — most ORMs cascade hard delete only.
- **"Soft delete = GDPR-safe."** No — you still have the data; GDPR demands actual erasure on request.
- **"Unique email constraint will work."** Not if deleted users still occupy the email. Use a partial unique index.
- **"I can always restore."** Only if you don't purge; and only if no FK changes happened in the meantime.
- **"`@DeleteDateColumn` handles JOINs too."** Usually only filters the root entity, not relations.

## Brute force approach

`deletedAt IS NULL` on every query, manually. Works for small codebases; gets forgotten as the team grows.

## Optimal approach

1. **Soft-delete column** (`deleted_at TIMESTAMPTZ NULL`) indexed.
2. **Global query filter** at the ORM layer: TypeORM `@DeleteDateColumn`, Hibernate `@Where`, Prisma extension, SQLAlchemy event listener.
3. **Partial unique indexes** for constraints affected by soft delete: `CREATE UNIQUE INDEX ... ON users(email) WHERE deleted_at IS NULL`.
4. **Cascade rule** explicit: soft-delete service-layer logic recursively soft-deletes children; or rely on `ON DELETE CASCADE` only when hard-deleting.
5. **Purge job** for GDPR / compliance: scheduled job that hard-deletes rows older than retention period.
6. **Audit on raw queries** — ESLint rule banning `query()` on entities with soft delete, or a code-review checklist.
7. **Reporting**: use the raw column to differentiate analytics views (often need deleted rows) from app views.

## Solution

```typescript
// ============================================================
// TypeORM — full soft delete with partial unique index
// ============================================================
@Entity()
@Index(['email'], { unique: true, where: 'deleted_at IS NULL' }) // partial unique
class User {
  @PrimaryGeneratedColumn() id!: number;
  @Column() email!: string;
  @DeleteDateColumn() deletedAt?: Date;

  @OneToMany(() => Post, p => p.author)
  posts!: Post[];
}

@Entity()
class Post {
  @PrimaryGeneratedColumn() id!: number;
  @ManyToOne(() => User, u => u.posts) author!: User;
  @DeleteDateColumn() deletedAt?: Date;
}

// Soft delete a user + cascade-soft-delete their posts (manual)
async function softDeleteUser(id: number) {
  return ds.transaction(async (mgr) => {
    await mgr.softDelete(User, { id });
    await mgr.softDelete(Post, { author: { id } });
  });
}

// Restore
async function restoreUser(id: number) {
  return ds.transaction(async (mgr) => {
    await mgr.restore(User, { id });
    await mgr.restore(Post, { author: { id } });
  });
}

// Reporting query — include deleted
const all = await userRepo.find({ withDeleted: true });

// GDPR hard purge — after retention window
async function purgeExpired() {
  await ds.query(`
    DELETE FROM users
    WHERE deleted_at IS NOT NULL
      AND deleted_at < NOW() - INTERVAL '90 days'
  `);
}

// ============================================================
// Prisma — extension for automatic filtering
// ============================================================
import { Prisma, PrismaClient } from '@prisma/client';

const prisma = new PrismaClient().$extends({
  model: {
    user: {
      async softDelete<T>(this: T, where: Prisma.UserWhereUniqueInput) {
        return prisma.user.update({ where, data: { deletedAt: new Date() } });
      },
    },
  },
  query: {
    user: {
      async findMany({ args, query }) {
        args.where = { deletedAt: null, ...args.where };
        return query(args);
      },
      async findUnique({ args, query }) {
        const result = await query(args);
        if (result && result.deletedAt) return null;
        return result;
      },
    },
  },
});

// ============================================================
// Partial unique index migration (Postgres)
// ============================================================
CREATE UNIQUE INDEX ux_users_email_live
  ON users(email)
  WHERE deleted_at IS NULL;
-- Allows soft-deleted rows to share an email with a new live row.
```

## Step-by-step dry run

### Scenario: re-register after soft-delete

```
1. createUser({ email: 'a@b.c' })
   INSERT INTO users (email, deleted_at) VALUES ('a@b.c', NULL)
   → row id=1, deleted_at=NULL

2. softDeleteUser(1)
   UPDATE users SET deleted_at = NOW() WHERE id = 1
   → row id=1, deleted_at='2026-05-17 ...'

3. createUser({ email: 'a@b.c' })  -- new signup
   WITHOUT partial unique index:
     → ERROR: duplicate key value violates unique constraint "users_email_key"
     → User can never re-register.

   WITH partial unique index:
     INSERT succeeds → row id=2, deleted_at=NULL.
     Coexists with row id=1 (deleted_at NOT NULL).
```

### Scenario: forgotten filter in raw SQL

```
const u = await ds.query('SELECT * FROM users WHERE id = $1', [1]);
// Returns the soft-deleted row! ORM filter doesn't apply to raw queries.
// Bug: app shows "Welcome back, deleted user!"

// Fix:
const u = await ds.query('SELECT * FROM users WHERE id = $1 AND deleted_at IS NULL', [1]);
// Or, prefer the repository method.
```

### Scenario: eager-load including deleted children

```typescript
const users = await userRepo.find({ relations: { posts: true } });
// SQL: SELECT * FROM users u LEFT JOIN posts p ON p.user_id = u.id WHERE u.deleted_at IS NULL
// But p.deleted_at IS NULL is NOT applied automatically in some TypeORM versions for JOINs.
// Posts of live users may include soft-deleted posts.

// Fix:
const users = await userRepo
  .createQueryBuilder('u')
  .leftJoinAndSelect('u.posts', 'p', 'p.deleted_at IS NULL')
  .where('u.deleted_at IS NULL')
  .getMany();
```

## How to think aloud in the interview

> "Soft delete adds a `deleted_at` timestamp column and treats `NULL` as 'live.' Every read excludes `WHERE deleted_at IS NOT NULL`. The discipline is **enforcement** — there are 4-5 ORM-specific mechanisms:
>
> - TypeORM `@DeleteDateColumn` + paranoid mode.
> - Hibernate `@SQLDelete` + `@Where`.
> - SQLAlchemy event listener with `with_loader_criteria`.
> - Prisma extension that injects `where: { deletedAt: null }`.
> - Postgres view: `CREATE VIEW users_live AS SELECT * FROM users WHERE deleted_at IS NULL`.
>
> Critical traps:
> 1. **Forgotten filter on raw SQL.** ORM interceptors don't fire for `query()`.
> 2. **Unique constraints clash.** A soft-deleted email blocks re-registration. Fix with a partial unique index `WHERE deleted_at IS NULL`.
> 3. **Eager-load JOINs miss the filter.** Posts of live users may include deleted posts.
> 4. **Cascade.** Most ORMs don't cascade soft-delete; service layer must do it.
> 5. **GDPR.** Soft delete is not deletion — schedule a purge job after retention period.
>
> Decision: soft delete when audit, restore, or partial-deletion are valuable (most B2B apps). Hard delete when you truly never want the data back (GDPR-heavy consumer apps, financial transactions with strict retention rules)."

## Important takeaways

- Soft delete = `deleted_at` column + global query filter.
- Enforcement is ORM-specific; raw queries bypass it.
- Partial unique indexes (`WHERE deleted_at IS NULL`) fix the unique-constraint clash.
- Eager-load JOINs need their own filter on the child relation.
- Cascades aren't automatic — wire them in the service layer or via DB triggers.
- Soft delete ≠ GDPR-compliant deletion; schedule a purge job.
- Always have a "show me deleted" flag for admin / debugging.
- Index `deleted_at` (partial index `WHERE deleted_at IS NULL` for hot tables).

## Variants

1. **Logical delete via `is_deleted` boolean** — same idea, less info (no when). Prefer `deleted_at`.
2. **Soft-delete via separate archive table** — `INSERT INTO archive ... SELECT ... ; DELETE FROM main` in a TX. Keeps main table small.
3. **Two-stage soft delete** — `pending_delete_at` (recoverable) and `deleted_at` (final), 30-day grace window.
4. **Tombstones in event-sourced systems** — store a `Deleted` event; rebuild excludes deleted aggregates.
5. **PostgreSQL row-security policies** — `CREATE POLICY ... USING (deleted_at IS NULL)` enforces at the DB layer, even for raw queries.
6. **Bitemporal** — track both "when it happened" and "when we recorded it"; soft delete is a special case.
7. **Cascade soft-delete via triggers** — `CREATE TRIGGER ... AFTER UPDATE OF deleted_at ON users` to soft-delete children.

## Revision notes

> **soft-delete-with-orm-quirk — 60 second recap**
> - `deleted_at TIMESTAMPTZ NULL`; NULL = live.
> - TypeORM `@DeleteDateColumn`, Hibernate `@SQLDelete + @Where`, Prisma extension, SQLAlchemy event listener.
> - Raw SQL bypasses the filter — code-review trap.
> - Partial unique index `WHERE deleted_at IS NULL` to allow re-use after delete.
> - Eager-load JOINs need explicit child filter.
> - Cascades aren't automatic — service-layer or trigger.
> - Soft delete ≠ GDPR purge — separate scheduled job.
> - Postgres row-level security policies enforce at DB layer even for raw queries.
