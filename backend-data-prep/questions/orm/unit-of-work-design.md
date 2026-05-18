# Explain the Unit of Work pattern — session lifecycle, dirty checking, flush ordering

## Source / Origin
- Martin Fowler, *Patterns of Enterprise Application Architecture* (2002), Chapter 11.
- Implemented in Hibernate (`Session`), SQLAlchemy (`Session`), EF Core (`DbContext`), Doctrine (`EntityManager`).
- TypeORM partially (`EntityManager` + `QueryRunner`); Prisma does **not** implement it (it's stateless / unit-of-work-less by design).

## Why this question matters in interviews
Unit of Work (UoW) is the *invisible* layer that makes ORMs feel magical — and the source of 80% of production ORM bugs. Senior interviewers ask this to separate engineers who think `repository.save(user)` does an immediate INSERT from those who understand that the session is **batching, ordering, and deduplicating** writes until flush. If you can describe the three phases (track → dirty-check → flush in dependency order), name the canonical bugs (stale entity after commit, flush during query, cascade ordering surprises), and recite when to call `flush()` explicitly, you sound like someone who has shipped ORMs.

## Concepts involved

### Syntax to lock in

```python
# SQLAlchemy 2.x
with Session(engine) as session:
    user = session.get(User, 1)          # tracked in identity map
    user.email = 'new@x.com'             # NO SQL yet — dirty-tracked
    order = Order(user=user, total=100)
    session.add(order)                   # NEW state; pending insert
    session.flush()                      # emits SQL in dependency order
    session.commit()                     # COMMIT; session expires entities
```

```typescript
// TypeORM
await dataSource.transaction(async (manager) => {
  const user = await manager.findOneByOrFail(User, { id: 1 });
  user.email = 'new@x.com';             // tracked via change detection
  const order = manager.create(Order, { user, total: 100 });
  await manager.save(order);            // flush happens here (per-call, not batched)
});
```

```java
// Hibernate
Session session = sessionFactory.openSession();
Transaction tx = session.beginTransaction();
User user = session.get(User.class, 1L);
user.setEmail("new@x.com");              // dirty flag set on flush
Order order = new Order(user, 100);
session.persist(order);                  // PENDING insert
tx.commit();                             // auto-flush + COMMIT
session.close();
```

### Edge cases / interview traps

1. **Flush is not commit.** Flush sends SQL; commit makes it durable. Many candidates conflate them — Hibernate auto-flushes before every query, which causes the "why did my UPDATE happen before my SELECT?" mystery.
2. **Identity map.** The session keeps one in-memory instance per (entity-class, PK). `session.get(User, 1)` twice returns the **same object reference**. Two sessions = two instances = `==` is false.
3. **Flush ordering.** UoW topologically sorts inserts by FK dependency. Insert `User` before `Order` even if `add(order)` came first. Updates/deletes follow class-level rules (Hibernate: inserts → updates → deletes; SQLAlchemy: dependency-based).
4. **Stale entity after commit.** Hibernate/SQLAlchemy expire entities on commit by default — touching `user.email` post-commit triggers a re-SELECT (or `DetachedInstanceError` if session closed).
5. **Cascade vs orphan removal.** `cascade=all` cascades persist/merge. `orphan_removal=true` deletes children unreferenced from the parent collection. Misconfigure and you lose data.
6. **Auto-flush in queries.** `session.query(Order).filter(...)` triggers an implicit flush so the query sees pending writes. If your pending writes violate a constraint, the query *raises*. Disable with `autoflush=False`.
7. **`session.merge()` vs `session.add()`.** `add` inserts a transient entity. `merge` copies state from a detached entity into a managed one and returns the managed one — the original detached instance stays detached.
8. **Long-lived sessions = memory leak.** The identity map grows unboundedly. Web apps use **session-per-request**.
9. **Prisma has no UoW.** Each `prisma.user.update(...)` is a separate SQL round-trip. Batching only via `prisma.$transaction([...])` (still one statement per op). Trade-off: no surprises, no batching.

## Mental Model

The UoW is a **mutable shopping cart of pending changes**, with an **identity map** to deduplicate. Three phases:

```
   ┌──────────────────────────────────────────────────────────┐
   │  Session (Unit of Work)                                  │
   │  ┌────────────────────────┐  ┌────────────────────────┐  │
   │  │   Identity Map         │  │   Change Tracker       │  │
   │  │   (class, pk) → entity │  │   NEW / DIRTY / DELETE │  │
   │  └────────────────────────┘  └────────────────────────┘  │
   │                                                          │
   │  add() / get()  →  TRACK                                 │
   │  mutation       →  MARK DIRTY (via setter / snapshot)    │
   │  flush()        →  TOPO-SORT → emit SQL                  │
   │  commit()       →  COMMIT + EXPIRE                       │
   └──────────────────────────────────────────────────────────┘
```

Dirty detection mechanisms vary:
- **Snapshot at load** (SQLAlchemy, Hibernate): on flush, compare current state to original snapshot. Memory cost; transparent for the user.
- **Proxy / setter interception** (Hibernate field interception, EF Core change tracking proxies): override property setters.
- **Explicit `save()`** (Prisma, MyBatis): no implicit tracking; you call save.

## Why interviewers care

- Reveals whether you understand **why ORMs feel slow** (it's the flush ordering and snapshot comparison, not network).
- Tests **transaction boundary discipline** — UoW couples tightly to the DB transaction.
- Differentiates engineers who know to call `session.flush()` before raw SQL (to make pending writes visible) from those whose tests randomly fail.

## Common beginner confusion

- "`save()` writes to the DB." Not always — it queues a write. Flush emits SQL.
- "If I update two fields and call save twice, I get two UPDATEs." Usually one — the UoW coalesces.
- "The order of `add()` calls is the order of INSERTs." No — dependency graph wins.
- "After commit I can keep using the entity." Often you can't — it's expired or detached.

## Brute force approach

Per-call autocommit, no session: every `repository.save(x)` issues SQL immediately, every `.find()` opens its own transaction. Works for trivial CRUD; fails on:
- Inserting `Order` with FK to `User` you just created → FK violation if user not yet committed.
- Updating five fields on the same entity → five UPDATEs.
- Cycles in entity graph → can't resolve without two-phase insert/update.

## Optimal approach

**Session-per-request** UoW:
1. **Begin** a session + transaction at request entry.
2. **Track** every entity loaded or added.
3. **Mutate** in-memory; no SQL.
4. **Flush** on demand (before a query that depends on pending state) and again at request end.
5. **Commit** the transaction → expire/detach entities → close session.

Flush algorithm:
1. Build a directed graph of pending operations using FK relationships.
2. Topo-sort: inserts of parents before children; deletes of children before parents.
3. Within a level, group by table for batch INSERT/UPDATE when the driver supports it.
4. Run SQL inside the open transaction.

## Solution

### SQLAlchemy 2.x — request-scoped session with explicit flush points

```python
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

SessionLocal = sessionmaker(engine, expire_on_commit=False, autoflush=True)

@contextmanager
def uow():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Service layer
def place_order(user_id: int, items: list[dict]):
    with uow() as s:
        user = s.get(User, user_id)               # identity-mapped
        if user is None:
            raise NotFound()
        order = Order(user=user, status='PENDING')
        s.add(order)
        s.flush()                                 # need order.id for line items
        for it in items:
            s.add(OrderItem(order_id=order.id, sku=it['sku'], qty=it['qty']))
        # commit on exit; flush of line items happens then
        return order.id
```

### Hibernate — explicit flush before a native query

```java
@Transactional
public Long placeOrder(Long userId, List<ItemDto> items) {
    User user = em.find(User.class, userId);
    Order order = new Order(user, "PENDING");
    em.persist(order);

    em.flush();                                    // force INSERT so order.id exists

    for (ItemDto it : items) {
        em.persist(new OrderItem(order.getId(), it.sku(), it.qty()));
    }

    // Native SQL view — must flush so it sees pending state
    em.flush();
    Long count = (Long) em.createNativeQuery("SELECT count(*) FROM order_items WHERE order_id = ?")
            .setParameter(1, order.getId())
            .getSingleResult();

    return order.getId();
}
```

## Step-by-step dry run

Scenario: insert one `User`, one `Order` that references the user, two `OrderItem`s referencing the order. Code calls `add` in the order: item1, order, user, item2.

```
SESSION STATE EVOLUTION

t0  add(item1)  → NEW   {item1: order=order_obj(no-id), sku=A}
t1  add(order)  → NEW   {order: user=user_obj(no-id)}
t2  add(user)   → NEW   {user}
t3  add(item2)  → NEW   {item2: order=order_obj}

DEPENDENCY GRAPH (resolved at flush):
   user  →  order  →  item1
                  →  item2

TOPO SORT:
   level 0: user
   level 1: order   (waits for user.id)
   level 2: item1, item2  (wait for order.id)

EMITTED SQL (one transaction):
   INSERT INTO users  (...) RETURNING id;          -- id=42
   INSERT INTO orders (user_id, ...) VALUES (42, ...) RETURNING id;   -- id=99
   INSERT INTO order_items (order_id, sku, qty) VALUES (99, 'A', 1);
   INSERT INTO order_items (order_id, sku, qty) VALUES (99, 'B', 2);
   COMMIT;

POST-COMMIT:
   default expire_on_commit=True   → user, order, item* are EXPIRED
   reading any attribute → re-SELECT (or DetachedInstanceError if closed)
   set expire_on_commit=False if you need to access the entity post-commit
```

If you'd called `session.flush()` between `add(order)` and `add(item1)` without first adding `user`, you'd get `IntegrityError: NOT NULL violation on orders.user_id` (or FK violation, depending on column nullability) — because the topo sort can only sort what's currently tracked.

## How to think aloud in the interview

> "Unit of Work is the session-level batching layer most ORMs implement. Three responsibilities:
>
> 1. **Identity map** — one in-memory object per (class, PK). Two `get(User, 1)` calls return the same reference. Mutations on either land in the same write.
>
> 2. **Change tracking** — snapshot at load, diff at flush. Or property interception. Either way, you don't call `save()` for updates; mutating a tracked entity is enough.
>
> 3. **Flush ordering** — topological sort of pending operations by FK dependency. Parents inserted before children; children deleted before parents; updates in between.
>
> Flush ≠ commit. Hibernate auto-flushes before queries; SQLAlchemy too if `autoflush=True`. That's why your raw SQL sometimes sees pending changes and sometimes doesn't.
>
> Trap I always mention: **post-commit, entities are expired**. If your service returns `order` and the caller reads `order.user.name`, it triggers a SELECT — and if the session is closed, you get `DetachedInstanceError`. Two fixes: `expire_on_commit=False`, or DTO-map before commit.
>
> Prisma deliberately skips UoW. Each call is a round-trip; trade-off is no surprises but no batching."

## Important takeaways

- **UoW = identity map + change tracker + flush.** All three together.
- **Flush orders by dependency**, not call order.
- **Flush ≠ commit.** Flush emits SQL; commit makes it durable. Auto-flush is the source of "phantom" SQL.
- **Session-per-request** is the standard web pattern. Don't keep sessions alive across requests.
- **Identity map is the reason** for `==` working on managed entities and the reason for `DetachedInstanceError` when accessing them outside.
- **Prisma has no UoW.** Stateless by design; batching is opt-in via `$transaction([...])`.
- **`merge` vs `add`** — different shapes. `merge` for detached, `add` for new.

## Variants

1. **"Explain `expire_on_commit`."** Default True; on commit, all attributes are invalidated so the next read re-fetches. Saves you from stale snapshots; costs an extra SELECT. Turn off only when returning entities to a request handler that DTO-maps immediately.
2. **"How does EF Core's UoW differ?"** Same three responsibilities; tracking via change-tracker proxies or snapshots; flush is `SaveChanges()`; no implicit auto-flush before queries (must call explicitly).
3. **"How does Prisma model it?"** It doesn't. Each method is a discrete query. Use `prisma.$transaction([...])` for atomicity; no identity map.
4. **"What's the cost of dirty checking on a wide entity?"** Hibernate snapshots every loaded entity; with 50 columns × 10k entities loaded, flush comparison is non-trivial. Use `@DynamicUpdate`, projections, or stateless sessions for bulk.
5. **"Why doesn't my INSERT happen until I commit?"** Because flush only ran at commit-time. Force with `em.flush()` if you need the generated ID inline.

## Revision notes

> **unit-of-work — 60 second recap**
> - Identity map + change tracker + topo-sorted flush.
> - Flush ≠ commit. Auto-flush exists in Hibernate (always) and SQLAlchemy (default).
> - Session-per-request is standard. Identity map grows; close at request end.
> - Insert order = dependency order, not call order. Children wait for parents.
> - `expire_on_commit=True` invalidates entities after commit → re-SELECTs or DetachedInstanceError.
> - `merge` (detached → managed copy) vs `add` (transient → managed).
> - Prisma has no UoW. EF Core, Hibernate, SQLAlchemy, Doctrine do.
> - **Trap:** `flush` during a query because of auto-flush → constraint violation surfaces in an unexpected line.
