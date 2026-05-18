# Optimistic locking with a version column

## Source / Origin
- The "classic concurrency without a lock" interview question.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md`, `transactions-concurrency/optimistic-vs-pessimistic-decision.md`.

## Why this question matters in interviews
Optimistic locking shows you understand **concurrency without serialization**. It's the right tool for low-contention writes (user profiles, catalog items, orders being updated by humans). Senior candidates can:
1. Explain the version-column protocol from scratch.
2. Show the exact `UPDATE ... WHERE id = ? AND version = ?` mechanic.
3. Wire it through TypeORM `@VersionColumn`, JPA `@Version`, or Prisma's manual pattern.
4. Articulate when *not* to use it (high-contention rows, bank transfers).

## Concepts involved

### Syntax to lock in

```typescript
// TypeORM
@Entity()
class Product {
  @PrimaryGeneratedColumn() id: number;
  @Column() name: string;
  @Column('int') price: number;
  @VersionColumn() version: number;   // ORM auto-increments on save
}

// Usage
const p = await repo.findOneByOrFail({ id });
p.price = newPrice;
try { await repo.save(p); }            // emits UPDATE ... WHERE id = ? AND version = ?
catch (e) {
  if (e instanceof OptimisticLockVersionMismatchError) {
    // retry: re-read, re-apply, re-save
  }
}

// JPA / Hibernate
@Entity
class Product {
  @Id Long id;
  String name;
  @Version Long version;   // ORM manages
}
// Throws OptimisticLockException on stale update.

// Prisma — manual (no built-in @VersionColumn)
const updated = await prisma.product.updateMany({
  where: { id, version: expectedVersion },
  data: { price: newPrice, version: { increment: 1 } },
});
if (updated.count === 0) throw new ConflictError();   // someone else won
```

### The SQL emitted

```sql
-- ORM-issued SQL (TypeORM/Hibernate with @Version):
UPDATE products
SET    name = $1, price = $2, version = version + 1
WHERE  id = $3 AND version = $4;

-- If 0 rows updated: stale write detected → OptimisticLockException.
```

### Edge cases / interview traps

1. **Version must be in the WHERE clause AND the SET clause.** Forgetting to bump version means every save loses the protection.
2. **Manual version skew via raw SQL.** Updates done outside the ORM (`UPDATE products SET price = $1 WHERE id = $2`) don't bump `version` → next ORM write sees stale version → false conflict (or worse, silent corruption if both manual updates skip the version check).
3. **Long sessions, stale entities.** User loads product at t=0, saves at t=10min. Lots of opportunity for a conflict on a busy row.
4. **Retry must re-fetch.** A naive retry that reuses the in-memory object will fail again; you must `find()` fresh, re-apply the diff, then save.
5. **Optimistic + many-to-many** — version is on parent; child collection changes don't always bump it. Hibernate has `OPTIMISTIC_FORCE_INCREMENT` for this.
6. **Detached entity** (Hibernate) — `merge()` is required; version check happens on flush.
7. **Conflict on a hot row** — optimistic locking degrades into a busy-retry loop. If conflicts > 10%, switch to pessimistic locking.
8. **TimeStamp-based versioning** is fragile — clock skew, second-precision can both bump simultaneously. Prefer integer counters.

## Mental Model

Optimistic = **"I bet nobody else changed this row while I was thinking."** If you lose the bet, retry. No locks held, max throughput when conflicts are rare.

```
   Pessimistic (SELECT FOR UPDATE):
   ───────────────────────────────
   T1: lock row 5  ──────────────────────► write ─► commit (lock released)
   T2:               wait....................write ─► commit

   Optimistic (version column):
   ───────────────────────────
   T1: read row 5 (v=7)  ─► compute  ─► UPDATE WHERE v=7 ─► OK (v=8)
   T2: read row 5 (v=7)  ─► compute  ─► UPDATE WHERE v=7 ─► 0 rows → CONFLICT
        retry: read v=8 ─► compute  ─► UPDATE WHERE v=8 ─► OK (v=9)

   No locks. No waiting. Conflicts cost a retry instead of blocking.
```

The version column is just a **proof-of-no-change** token. Whoever submits it first wins.

## Why interviewers care

- Tests **concurrency-control vocabulary**: optimistic vs pessimistic; compare-and-swap; ABA-style protection.
- Tests **understanding of UPDATE row-count semantics** — 0 rows updated is signal, not error.
- Tests **retry strategy** — re-fetch, re-apply, re-save is not the same as blind retry.
- Tests **trade-off thinking** — when to choose this vs `FOR UPDATE` vs serializable isolation.

## Common beginner confusion

- **"Optimistic locking prevents concurrent updates."** No — it *detects* them. Concurrency still happens; conflicts get caught and retried.
- **"I'll just keep retrying forever."** Hot rows can cause retry storms; cap retries (3–5) and fall back to pessimistic or user error.
- **"Bumping version on every column update."** Most ORMs handle it. If you're rolling your own, include `version = version + 1` in **every** UPDATE.
- **"The exception means the data was corrupted."** No — it means another transaction beat you. Re-read and try again.
- **"Updating a child collection should bump parent's version."** Not automatic in most ORMs; opt into `OPTIMISTIC_FORCE_INCREMENT` if needed.
- **"Timestamps are fine for versioning."** Two concurrent updates can produce the same millisecond timestamp. Use an integer counter.

## Brute force approach

`SELECT FOR UPDATE` every time. Correct but blocks unrelated workers; degrades throughput when conflicts are rare. Use only when conflict probability is high.

## Optimal approach

1. Add a `version` integer column to the table.
2. ORM (or manual code) issues `UPDATE ... WHERE id = ? AND version = ?` with `version = version + 1`.
3. On 0 rows affected (or `OptimisticLockException`), enter a **retry-with-refresh** loop: re-fetch latest row, re-apply the user's intent, re-save.
4. Cap retries (e.g., 3) — fall back to telling the user "this item changed; refresh and try again."
5. Monitor conflict rate; if > 5–10% on a hot row, **switch to pessimistic** or redesign the data model (e.g., split hot row into shards / counters).

## Solution

```typescript
// ============================================================
// TypeORM — full example with retry
// ============================================================
import { OptimisticLockVersionMismatchError, DataSource, EntityManager } from 'typeorm';

@Entity()
class Product {
  @PrimaryGeneratedColumn() id!: number;
  @Column() name!: string;
  @Column('int') price!: number;
  @VersionColumn() version!: number;
}

class ProductService {
  constructor(private ds: DataSource) {}

  async updatePrice(id: number, newPrice: number, intent: 'set' | 'discount' = 'set') {
    return this.withConflictRetry(async () => {
      return this.ds.transaction(async (mgr) => {
        const p = await mgr.findOneByOrFail(Product, { id });
        p.price = intent === 'set' ? newPrice : Math.round(p.price * (1 - newPrice));
        await mgr.save(p);    // UPDATE products SET ..., version = version+1 WHERE id=? AND version=?
        return p;
      });
    });
  }

  private async withConflictRetry<T>(fn: () => Promise<T>, max = 3): Promise<T> {
    for (let i = 0; i < max; i++) {
      try { return await fn(); }
      catch (e) {
        if (e instanceof OptimisticLockVersionMismatchError) {
          await new Promise(r => setTimeout(r, 25 * (1 << i) + Math.random() * 10));
          continue;
        }
        throw e;
      }
    }
    throw new ConflictError('Item changed while you were editing. Please refresh.');
  }
}

// ============================================================
// Prisma — manual version pattern
// ============================================================
async function updatePrice(id: number, expectedVersion: number, newPrice: number) {
  const result = await prisma.product.updateMany({
    where: { id, version: expectedVersion },
    data: { price: newPrice, version: { increment: 1 } },
  });
  if (result.count === 0) {
    // someone else won — fetch and re-try at caller
    throw new ConflictError();
  }
}

// ============================================================
// SQLAlchemy — version_id_col
// ============================================================
class Product(Base):
    __tablename__ = "products"
    id      = Column(Integer, primary_key=True)
    price   = Column(Integer)
    version = Column(Integer, nullable=False)
    __mapper_args__ = {
        "version_id_col": version,        # ORM bumps on flush
    }
# StaleDataError raised on conflict.

// ============================================================
// JPA / Hibernate — @Version
// ============================================================
@Entity
public class Product {
  @Id Long id;
  Integer price;
  @Version Long version;          // Hibernate emits version-aware UPDATE
}
```

## Step-by-step dry run

State: `Product#5` has `{ price: 100, version: 7 }`.

Two clients edit simultaneously:

```
T1 (Alice):  reads Product#5 → {price:100, version:7}
T2 (Bob):    reads Product#5 → {price:100, version:7}     ← both see v=7

T1: sets price=120.
    Emits: UPDATE products SET price=120, version=8 WHERE id=5 AND version=7
    DB returns: 1 row affected. v is now 8.

T2: sets price=90.
    Emits: UPDATE products SET price=90, version=8 WHERE id=5 AND version=7
    DB returns: 0 rows affected. (Row's version is now 8, not 7.)
    ORM throws OptimisticLockException.

T2 retry path:
    Re-fetch: Product#5 → {price:120, version:8}
    Re-apply: setPrice(90)
    Emits: UPDATE products SET price=90, version=9 WHERE id=5 AND version=8
    DB returns: 1 row affected. v is now 9.

Final state: {price:90, version:9}. Both updates conceptually applied; the last-write-wins resolved.
```

If the intent is "discount 10%" rather than "set to 90":
- After T2 retries with fresh state, the discount applies to the **new** price (120), not the original (100). Result: 108, not 90. This is *semantic correctness* — important to think about in the interview.

If the conflict probability is high (10 concurrent editors), expect:
- 1 winner, 9 retries.
- 1 of those wins on retry, 8 retry again.
- And so on. Retry storm. **Switch to pessimistic** for this row.

## How to think aloud in the interview

> "Optimistic locking is the right default for **low-contention writes** — profile edits, catalog items, drafts. The mechanic: add a `version` integer column; every UPDATE includes `WHERE version = ?` and sets `version = version + 1`. If the row count is 0, someone else won — throw a conflict.
>
> Retry handling is **re-fetch, re-apply, re-save**, not blind retry. The user's intent might be 'set price to 90' or 'discount 10%' — those resolve differently after a fresh read.
>
> When *not* to use it:
> - High-contention hot rows (counter rows, bank balances) — retry storm.
> - Long-edit sessions on a row many people touch — conflict almost guaranteed.
> - Multi-row invariants (write skew) — version column is per-row; doesn't help.
>
> For high contention I switch to `SELECT FOR UPDATE`; for multi-row invariants, serializable isolation; for monotonically increasing counters, atomic UPDATE without read.
>
> ORM support: TypeORM `@VersionColumn`, JPA `@Version`, SQLAlchemy `version_id_col`, Hibernate `@OptimisticLocking`. Prisma doesn't have a built-in — you do it manually via `updateMany` + `where: { version }` and check `count`."

## Important takeaways

- Version column = compare-and-swap on a row. `UPDATE ... WHERE id = ? AND version = ?` + `version = version + 1`.
- 0 rows affected = conflict; throw and retry with fresh state.
- Use for low-contention writes; switch to pessimistic if conflict rate > 5–10%.
- Retry = re-fetch, re-apply intent, re-save. Never blind retry the stale entity.
- Avoid timestamps for versioning — clock skew, collisions.
- Manual writes via raw SQL must bump version too, or invariant breaks.
- Doesn't help with multi-row invariants (write skew) — use serializable or `FOR UPDATE` on read set.

## Variants

1. **Detached entity merge** (Hibernate) — `entityManager.merge(detached)` performs the version check at flush; UI flows often use this.
2. **`OPTIMISTIC_FORCE_INCREMENT`** — bump version even on read-only access; useful when the entity's child collection changed.
3. **ETag / If-Match HTTP** — same idea over REST. The `ETag` header is the version; `If-Match` is the conditional update. Maps cleanly to DB-level optimistic locking.
4. **Conditional writes in NoSQL** — DynamoDB's `ConditionExpression`, Mongo's `findOneAndUpdate` with version filter, Cassandra LWT.
5. **CRDTs as the alternative** — for collaborative editing, optimistic locking causes constant retries; switch to CRDT-based merge.
6. **Soft optimistic locking** — check `updated_at` instead of `version` when you can't add a column. Fragile; prefer integer.

## Revision notes

> **optimistic-locking-version-column — 60 second recap**
> - Add `version` int column; UPDATE includes `WHERE version=?` and sets `version=version+1`.
> - 0 rows affected = conflict; throw, retry with fresh state.
> - Use for low-contention writes; switch to pessimistic if conflicts > 5–10%.
> - Retry = re-fetch + re-apply + re-save. Not blind retry.
> - Raw SQL must bump version too; otherwise invariant breaks.
> - ORM support: TypeORM `@VersionColumn`, JPA `@Version`, SQLAlchemy `version_id_col`. Prisma = manual.
> - Maps to HTTP `ETag` / `If-Match` semantics at the API layer.
