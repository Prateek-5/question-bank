# Dirty tracking edge cases — JSON columns, nested objects, collections

## Source / Origin
- The "why didn't my save persist?" debugging classic.
- Concept refs: `backend-data-prep/orm/01-orm-internals.md` (change tracking section).

## Why this question matters in interviews
Dirty tracking is one of those ORM features that **works invisibly when it works** and produces baffling bugs when it doesn't. Every senior backend engineer has hit "I changed `user.metadata.foo`, called save, the DB didn't update." The interview signal: do you know **how each ORM decides "this is dirty"**, and the canonical workarounds (reassign, mark dirty, immer / structured clone)?

## Concepts involved

### Three dirty-tracking models

```
   1. Snapshot diff           — Hibernate, SQLAlchemy
      └─ ORM stores a copy of the loaded row; at flush, diffs each field.
      └─ Catches in-place mutations IF the snapshot was deep-copied.

   2. Setter interception     — TypeORM (active record style), ActiveRecord, Eloquent
      └─ Every property setter flips a "dirty" bit.
      └─ Misses in-place mutations on objects/arrays (the setter never fires).

   3. Explicit update fields  — Prisma, Drizzle, Knex
      └─ You pass the fields to update; no magic.
      └─ Most predictable; most verbose.
```

### Syntax to lock in

```typescript
// ============================================================
// TypeORM — setter interception (with snapshot for JSON)
// ============================================================
const u = await repo.findOneByOrFail({ id });
u.email = "new@x.com";           // setter fires → dirty
u.metadata.foo = "bar";          // in-place mutation; setter does NOT fire → NOT DIRTY
await repo.save(u);              // metadata change SILENTLY LOST.

// Fix: reassign
u.metadata = { ...u.metadata, foo: "bar" };  // setter fires; dirty bit set
await repo.save(u);              // OK

// ============================================================
// Prisma — explicit; no magic
// ============================================================
await prisma.user.update({
  where: { id },
  data: {
    email: "new@x.com",
    metadata: { ...u.metadata, foo: "bar" },   // must pass entire field
  },
});

// ============================================================
// SQLAlchemy — snapshot diff, but JSON in-place isn't tracked unless flagged
// ============================================================
class User(Base):
    metadata = Column(MutableDict.as_mutable(JSONB))   # ◄── critical
# Without MutableDict, in-place dict mutation isn't detected.

# Then:
u = session.get(User, id)
u.metadata["foo"] = "bar"           # MutableDict notices; flush picks it up.
session.commit()
```

### Edge cases / interview traps

1. **JSON / JSONB in-place mutation**. The single most common bug. `user.metadata.foo = "bar"` mutates the object reference. ORM has no way to know unless you opt in (SQLAlchemy `MutableDict`) or reassign.
2. **Arrays in-place** (`user.tags.push("new")`). Same story. Reassign with a new array or use `mark*Dirty` if your ORM exposes it.
3. **Date columns** — comparing dates by reference can produce false dirty flags if you re-construct `new Date()` from the same value.
4. **BigInt / Decimal precision** — some ORMs hydrate as strings; comparing the strings to numbers can produce phantom diffs.
5. **Collection associations**: adding to `user.orders` when `orders` is lazy-loaded might just hydrate, then add — depending on cascade settings, the new order may or may not save.
6. **Partial updates from REST PATCH**: applying `Object.assign(user, body)` overwrites only provided fields, but does it overwrite to `undefined` for absent fields? Depends on your spread / strip-undefined logic.
7. **Optimistic locking + dirty tracking** — version column bumps even if only an in-place JSON change happened, only if the change is detected.
8. **`@BeforeUpdate` hooks** — run only if dirty. Silent in-place mutation skips hooks too.
9. **TypeORM `save()` vs `update()`** — `save()` runs hydration, hooks, and dirty diff; `update()` is a raw UPDATE that bypasses dirty tracking, returning no entity.
10. **Repeated `save()` of unchanged entity** — Hibernate flushes a no-op UPDATE in some configs (`select-before-update` off). Generates write traffic for no reason.

## Mental Model

```
   Entity in session:                 Entity at flush:
   ┌──────────────────┐               ┌──────────────────┐
   │ id: 5            │      diff     │ id: 5            │  → no change
   │ email: a@b.c     │   ─────────►  │ email: new@x.com │  → DIRTY (different)
   │ metadata: {…}    │               │ metadata: {…}    │  → ??? (same ref or content?)
   └──────────────────┘               └──────────────────┘

   Setter interception: looks at "did property X get assigned?"
                        → email = "new" fires, metadata.foo = "bar" doesn't.

   Snapshot diff:       looks at "is field X !== original snapshot?"
                        → if snapshot was shallow-copied, in-place change is invisible.

   Explicit (Prisma):   you tell it what to write. Period.
```

The trap shape is universal: **ORMs that watch references can't see content changes; ORMs that watch content might miss in-place changes if their snapshot is shallow.**

## Why interviewers care

- Tests **understanding of how the ORM implements its core feature** — not just usage.
- Tests **production debugging instincts** — "the save was called but DB didn't change" requires this model.
- Tests **knowing which ORM you're in** — Prisma, TypeORM, Hibernate behave differently.

## Common beginner confusion

- **"`save()` always persists every field."** False — most ORMs UPDATE only dirty columns.
- **"In-place mutation works because the object is the same."** Wrong — that's exactly the problem; same reference, no change signal.
- **"Prisma has dirty tracking."** No — Prisma is explicit. You pass the fields to update.
- **"`Object.assign(user, patch)` is safe for PATCH endpoints."** Only if patch omits fields you don't want to overwrite; explicit field allowlist is safer.
- **"Reassigning to the same value is a no-op."** Some ORMs still mark it dirty (the setter fired). Either OK (idempotent UPDATE) or wasteful (no-op write traffic).
- **"Hibernate notices everything."** Hibernate notices because it deep-snapshots in some modes, but it still misses in-place changes in lazy proxies / collection unless they're tracked.

## Brute force approach

After every mutation, call `markModified` / `markDirty` / `Object.assign` to force-update. Works but pollutes business logic with persistence hints.

## Optimal approach

1. **Pick a discipline by ORM**:
   - TypeORM / Active Record style: always **reassign** for JSON / arrays.
   - SQLAlchemy: use **MutableDict / MutableList** for mutable JSON columns.
   - Hibernate: prefer **immutable values** (records, value objects) for JSON; or `@DynamicUpdate` + setter.
   - Prisma: pass explicit `data` with the full new value.
2. **Strip undefined from PATCH bodies** before applying to entities; whitelist allowed fields.
3. **Convert "patch" to "merge intent"** explicitly: `applyPatch(entity, patch)` is a function that decides which keys to overwrite.
4. **Test for it.** Unit test: load → mutate → save → re-load → assert.
5. **Detect at runtime in dev**: hook into `@AfterUpdate` and warn if a save produced no SQL when you expected one.

## Solution

```typescript
// ============================================================
// TypeORM — reassign pattern for JSON
// ============================================================
@Entity()
class User {
  @PrimaryGeneratedColumn() id!: number;
  @Column() email!: string;
  @Column('jsonb') metadata!: Record<string, unknown>;
  @Column('text', { array: true }) tags!: string[];
}

// BAD — silent loss
async function setPreference_BAD(id: number, key: string, value: unknown) {
  const u = await repo.findOneByOrFail({ id });
  u.metadata[key] = value;          // setter NEVER fires
  await repo.save(u);               // no UPDATE
}

// GOOD — reassign
async function setPreference(id: number, key: string, value: unknown) {
  const u = await repo.findOneByOrFail({ id });
  u.metadata = { ...u.metadata, [key]: value };  // setter fires
  await repo.save(u);
}

// ============================================================
// Prisma — explicit JSON update with `Json` value
// ============================================================
import type { Prisma } from '@prisma/client';
async function setPreference(id: number, key: string, value: unknown) {
  const u = await prisma.user.findUniqueOrThrow({ where: { id } });
  await prisma.user.update({
    where: { id },
    data: {
      metadata: { ...(u.metadata as object), [key]: value } as Prisma.InputJsonValue,
    },
  });
}

// ============================================================
// SQLAlchemy — MutableDict for proper in-place tracking
// ============================================================
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True)
    email    = Column(String)
    metadata = Column(MutableDict.as_mutable(JSONB), default=dict)

def set_pref(session, user_id, key, value):
    u = session.get(User, user_id)
    u.metadata[key] = value     # MutableDict signals dirty
    session.commit()

// ============================================================
// PATCH-handler discipline
// ============================================================
const ALLOWED_KEYS = ['email', 'name', 'metadata'] as const;
type PatchKey = typeof ALLOWED_KEYS[number];

function applyPatch(entity: User, patch: Partial<User>) {
  for (const k of ALLOWED_KEYS) {
    if (patch[k] !== undefined) (entity as any)[k] = patch[k];
  }
}
```

## Step-by-step dry run

### Bug reproduction (TypeORM):
```typescript
const u = await repo.findOneByOrFail({ id: 5 });
// Initial: u.metadata = { theme: "dark" }

u.metadata.theme = "light";       // in-place mutation
// Setter for `metadata` did NOT fire — same object reference.
// Dirty set: {} (no fields marked)

await repo.save(u);
// Emits: nothing (or `SELECT version`, no UPDATE).
// DB still has { theme: "dark" }.

const u2 = await repo.findOneByOrFail({ id: 5 });
console.log(u2.metadata.theme);   // "dark" — your change is gone.
```

### Fix:
```typescript
u.metadata = { ...u.metadata, theme: "light" };
// Setter for `metadata` fires. Dirty set: { metadata }.

await repo.save(u);
// Emits: UPDATE users SET metadata = $1 WHERE id = 5.
// DB now has { theme: "light" }.
```

### Snapshot diff trap (Hibernate):
```java
User u = em.find(User.class, 5);
u.getMetadata().put("theme", "light");   // in-place on the Map reference
em.flush();
// Whether this works depends on:
// - Hibernate has a snapshot of `metadata` at load time.
// - At flush, it compares u.getMetadata() (current) with the snapshot.
// - If snapshot was shallow (same Map reference), diff sees no change.
// - If snapshot was deep (different Map), diff sees a change.
// Default behavior: shallow → in-place mutation NOT detected.

// Workaround: replace
u.setMetadata(new HashMap<>(u.getMetadata()) {{ put("theme", "light"); }});
em.flush();   // detected
```

## How to think aloud in the interview

> "Dirty tracking is one of three styles depending on the ORM:
>
> 1. **Setter interception** — TypeORM, ActiveRecord. Property assignment flips a dirty bit. The gotcha: in-place mutation (`user.metadata.foo = 'bar'`) doesn't fire any setter, so the change is silently lost.
> 2. **Snapshot diff** — Hibernate, SQLAlchemy. The ORM stores a copy at load time and diffs at flush. If the copy was shallow, in-place still escapes.
> 3. **Explicit** — Prisma. You pass the field. No magic, no surprises.
>
> The discipline:
> - **TypeORM**: always reassign JSON / arrays — `user.metadata = { ...user.metadata, foo: 'bar' }`.
> - **SQLAlchemy**: declare the column as `MutableDict.as_mutable(JSONB)` and in-place works.
> - **Hibernate**: prefer immutable value objects, or replace the whole map / list.
> - **Prisma**: pass the entire new JSON in `data`.
>
> Bug triage flow when 'save didn't persist':
> 1. Check if the save actually emitted SQL (enable query logging).
> 2. If no SQL, the field wasn't dirty — in-place mutation suspect.
> 3. Check the ORM's dirty-tracking model and apply the right fix."

## Important takeaways

- Three dirty-tracking models: setter interception, snapshot diff, explicit.
- **JSON / array in-place mutation is the canonical bug** across all setter-interception ORMs.
- Fix: reassign with a new object/array reference, or opt in (`MutableDict` in SQLAlchemy).
- Prisma is immune by design — explicit `data` field.
- ORMs UPDATE only dirty columns; unchanged fields are skipped (good for write traffic).
- Hooks (`@BeforeUpdate`) only fire if dirty — silent in-place mutation skips them too.
- For REST PATCH, use an explicit allowlist + reassign rather than `Object.assign` magic.

## Variants

1. **Optimistic locking + in-place JSON** — version bumps only if dirty; in-place mutation can both lose the change *and* skip the version bump, allowing two clients to silently overwrite.
2. **Cascade saves on collections** — adding to a lazy collection may or may not propagate depending on `cascade` settings.
3. **Audit log via hooks** — if the hook needs to know "what changed," requires snapshot diff. Pure setter interception can give "which fields are dirty" but not "old values."
4. **CRDT-style merge** for JSON — instead of last-write-wins, merge structurally. Out of scope for ORM but worth mentioning.
5. **Computed columns** — Postgres `GENERATED ALWAYS AS (expr) STORED`. ORM thinks it's writable; DB rejects writes. Mark as read-only on the entity.
6. **Replacing entire arrays** in JPA — `user.setTags(newList)` vs `user.getTags().clear(); user.getTags().addAll(newList)` — Hibernate handles the latter as an orphan-removal/addition sequence; the former replaces the collection reference (may break orphan tracking).

## Revision notes

> **dirty-tracking-edge-cases — 60 second recap**
> - 3 models: setter interception, snapshot diff, explicit.
> - Canonical bug: in-place JSON / array mutation isn't detected in setter-interception ORMs.
> - Fix: reassign with spread / new array. Or use `MutableDict` (SQLAlchemy) / `@DynamicUpdate` configs (Hibernate).
> - Prisma is explicit, no magic, no traps.
> - Hooks fire only if dirty — silent in-place mutation skips them.
> - Symptom: save emits no SQL; enable query logging to detect.
> - For PATCH: explicit allowlist + reassign over `Object.assign`.
