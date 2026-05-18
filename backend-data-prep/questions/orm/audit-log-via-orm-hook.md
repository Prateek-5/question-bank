# Audit log via ORM hook — interceptors, signals, listeners

## Source / Origin
- Hibernate Envers (https://hibernate.org/orm/envers/) — the JVM standard.
- SQLAlchemy events: `before_flush`, `after_insert`, etc.
- Django `pre_save`/`post_save` signals.
- Prisma extensions (formerly middleware): https://www.prisma.io/docs/concepts/components/prisma-client/client-extensions
- TypeORM Subscribers / `EventSubscriberInterface`.

## Why this question matters in interviews
Every regulated industry (fintech, healthcare, gov) requires an audit trail. The naive answer ("I'll add `created_by` and `updated_at` columns") misses the real problem: capturing **what changed**, **who changed it**, and **when**, *transactionally* with the write. Senior engineers should know:
1. The three classes of audit logs (column-level metadata, append-only event log, full row-versioning).
2. Why ORM hooks are the right place (or sometimes the wrong place) to do this.
3. How to keep the audit log consistent with the main write (same transaction or outbox pattern).

## Concepts involved

### Three classes of audit log

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. METADATA COLUMNS                                                 │
│     created_at, updated_at, created_by, updated_by, version          │
│     - Cheap, on every row.                                           │
│     - Doesn't capture "what was the old value".                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  2. APPEND-ONLY EVENT LOG (audit_logs table)                         │
│     (id, entity, entity_id, action, actor, at, before, after)        │
│     - One row per change, JSON diff/snapshot.                        │
│     - Easy to query "show me all changes by user X".                 │
│     - Written via ORM hook in the same transaction.                  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  3. FULL VERSION TABLES (Hibernate Envers, temporal tables)          │
│     users + users_aud, with rev_id, rev_type (I/U/D)                 │
│     - Reconstruct entity at any past point.                          │
│     - Storage heavy; queryable like a normal table.                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Syntax to lock in

```python
# SQLAlchemy — before_flush event
from sqlalchemy import event
from sqlalchemy.orm import Session

@event.listens_for(Session, 'before_flush')
def capture_audit(session, flush_context, instances):
    actor = current_actor_var.get()
    for obj in session.new:
        session.add(AuditLog(
            entity=type(obj).__name__,
            entity_id=None,            # PK not yet assigned for INSERTs
            action='INSERT',
            actor=actor,
            after=to_dict(obj),
        ))
    for obj in session.dirty:
        if not session.is_modified(obj, include_collections=False):
            continue
        diff = compute_diff(obj)        # uses attribute history API
        session.add(AuditLog(
            entity=type(obj).__name__,
            entity_id=obj.id,
            action='UPDATE',
            actor=actor,
            before=diff['before'],
            after=diff['after'],
        ))
    for obj in session.deleted:
        session.add(AuditLog(
            entity=type(obj).__name__,
            entity_id=obj.id,
            action='DELETE',
            actor=actor,
            before=to_dict(obj),
        ))
```

```java
// Hibernate Envers
@Entity
@Audited
public class User {
    @Id Long id;
    @Column String email;
}
// Auto-generates users_aud table; access via AuditReader.
AuditReader reader = AuditReaderFactory.get(em);
List<Number> revs = reader.getRevisions(User.class, userId);
User asOf = reader.find(User.class, userId, revs.get(0));
```

```typescript
// TypeORM — EntitySubscriber
@EventSubscriber()
export class AuditSubscriber implements EntitySubscriberInterface {
    afterInsert(event: InsertEvent<any>) {
        this.write(event.manager, 'INSERT', event.entity, null);
    }
    afterUpdate(event: UpdateEvent<any>) {
        this.write(event.manager, 'UPDATE', event.databaseEntity, event.entity);
    }
    afterRemove(event: RemoveEvent<any>) {
        this.write(event.manager, 'DELETE', event.databaseEntity, null);
    }
    private write(em: EntityManager, action: string, before: any, after: any) {
        return em.save(em.create(AuditLog, {
            action,
            actor: contextVar.get('actor'),
            before, after,
            at: new Date(),
        }));
    }
}
```

```typescript
// Prisma — extension (recommended over deprecated middleware)
const audited = prisma.$extends({
    query: {
        $allModels: {
            async update({ model, operation, args, query }) {
                const before = await prisma[model].findUnique({ where: args.where });
                const after = await query(args);
                await prisma.auditLog.create({
                    data: {
                        entity: model, entityId: after.id,
                        action: operation, actor: actorCtx.get(),
                        before, after,
                    },
                });
                return after;
            },
        },
    },
});
```

### Edge cases / interview traps

1. **`actor` is request-scoped.** Pulling it inside an ORM hook requires a `contextvar` / `ThreadLocal` / `AsyncLocalStorage` populated by middleware. Don't pass it via global mutable state.
2. **`before_flush` runs before SQL.** PK for new rows isn't assigned yet — must defer audit row creation to `after_insert` or `after_flush_postexec`.
3. **Cascade deletes** trigger many ORM events; audit rows balloon. Decide whether bulk soft-delete should emit one log row or N.
4. **Bulk operations bypass ORM hooks** — `executemany`, `INSERT ... SELECT`, `BulkOperations`. Either restrict bulk writes or implement DB-level triggers.
5. **Raw SQL bypasses ORM hooks** — same story. DB triggers are the safety net.
6. **Audit log writes share the transaction** with the audited write — atomicity guarantee. But if your DB is split (audit in a different store), use the **transactional outbox** pattern.
7. **PII in audit logs** — passwords, SSNs. Either redact in the hook or mark fields with `@AuditIgnore` and skip them.
8. **`updated_at` only changes if a field was actually modified**, not on `session.add(unchanged_user)`. Use `session.is_modified()` to filter.
9. **High-volume audit** crushes the main DB. Either partition by month, move audit to a separate cluster, or pipe to an append-only store (Kafka → ClickHouse, S3).
10. **Reads of audit logs** must enforce access control — sometimes more sensitive than the data they describe.

## Mental Model

The ORM gives you **three intercept points**: before flush, after each row operation, after the whole flush. Audit logs ride along by inserting their own rows into the same transaction.

```
   APP CODE
     │ user.email = 'new'
     ▼
   ┌──────────────────────────────────────────────┐
   │ ORM Session                                  │
   │   change detected                            │
   │   ┌────────────────────────────────────┐     │
   │   │ on flush:                          │     │
   │   │   1. compute diff                  │     │
   │   │   2. write audit row to session    │     │
   │   │   3. emit SQL: UPDATE + INSERT     │     │
   │   └────────────────────────────────────┘     │
   │   COMMIT (both atomically)                   │
   └──────────────────────────────────────────────┘
                  │
                  ▼
           [ users table ]  [ audit_logs table ]
```

The crucial property is **atomicity**: if the audit insert fails, the whole transaction rolls back. No "I updated the user but didn't log it" failure mode.

## Why interviewers care

- Compliance / regulated workloads always need this. Reveals whether you've shipped to those environments.
- ORM hooks are a leaky abstraction — knowing the boundaries (raw SQL, bulk ops bypass them) is senior-level.
- Forces you to think about transaction scope and consistency.

## Common beginner confusion

- "I'll add `before_save` triggers in the DB." Possible, but loses the ORM context (actor, request ID). Use a hybrid: trigger for the bypass cases, ORM hook for the rich data.
- "Logging to stdout is good enough." Not queryable, not transactional, lost on restart.
- "I'll add a `last_modified_by` column instead of a log table." Captures the latest but not the history.
- "Audit logs in the same table as data — just version columns." Works for low-volume; bloats the main table for high-volume.

## Brute force approach

`logging.info(...)` in every service method. Loses 5% of writes to crashes, isn't queryable, no atomicity with the DB write. Don't.

## Optimal approach

Three layers:

1. **Metadata columns** on every table (`created_at`, `updated_at`, `created_by`, `updated_by`, `version`). Cheap.
2. **Append-only `audit_logs` table** populated by ORM hook, in the same transaction.
3. **DB triggers** as defense for the bypass paths (bulk inserts, raw SQL, admin tools).

For high-volume:
- Partition `audit_logs` by month.
- Periodically archive to S3/cold storage.
- Or ship to ClickHouse / Kafka / OpenSearch out-of-band via **transactional outbox**.

## Solution

### Layer 1 — metadata columns via mixin

```python
# SQLAlchemy
from sqlalchemy import Column, DateTime, String, Integer, func

class AuditMixin:
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String)
    updated_by = Column(String)
    version    = Column(Integer, default=1)

class User(Base, AuditMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String)
```

### Layer 2 — append-only audit table + hook (SQLAlchemy)

```python
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id        = Column(BigInteger, primary_key=True)
    entity    = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action    = Column(String, nullable=False)    # INSERT/UPDATE/DELETE
    actor     = Column(String)
    at        = Column(DateTime, server_default=func.now())
    before    = Column(JSONB)
    after     = Column(JSONB)
    request_id = Column(String, index=True)

def _to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def _diff(obj):
    before, after = {}, {}
    state = inspect(obj)
    for attr in state.mapper.column_attrs:
        hist = state.attrs[attr.key].history
        if hist.has_changes():
            before[attr.key] = hist.deleted[0] if hist.deleted else None
            after[attr.key]  = hist.added[0]   if hist.added   else None
    return before, after

PII_FIELDS = {'password_hash', 'ssn', 'card_number'}

def _redact(d):
    return {k: ('***' if k in PII_FIELDS else v) for k, v in (d or {}).items()}

@event.listens_for(Session, 'before_flush')
def capture(session, flush_context, instances):
    actor = current_actor.get()
    request_id = current_request_id.get()

    for obj in session.new:
        if isinstance(obj, AuditLog): continue
        session.add(AuditLog(
            entity=type(obj).__name__,
            entity_id=str(getattr(obj, 'id', None) or 'PENDING'),
            action='INSERT', actor=actor, request_id=request_id,
            after=_redact(_to_dict(obj)),
        ))

    for obj in session.dirty:
        if isinstance(obj, AuditLog): continue
        if not session.is_modified(obj): continue
        before, after = _diff(obj)
        session.add(AuditLog(
            entity=type(obj).__name__,
            entity_id=str(obj.id),
            action='UPDATE', actor=actor, request_id=request_id,
            before=_redact(before), after=_redact(after),
        ))

    for obj in session.deleted:
        if isinstance(obj, AuditLog): continue
        session.add(AuditLog(
            entity=type(obj).__name__,
            entity_id=str(obj.id),
            action='DELETE', actor=actor, request_id=request_id,
            before=_redact(_to_dict(obj)),
        ))

# resolve PENDING entity_ids after PKs assigned
@event.listens_for(Session, 'after_flush_postexec')
def resolve_pks(session, flush_context):
    for obj in session.new:
        if isinstance(obj, AuditLog) and obj.entity_id == 'PENDING':
            # the original entity is also in session.new, with its PK now set
            obj.entity_id = str(_lookup_target(obj))
```

### Layer 3 — DB trigger as safety net

```sql
CREATE OR REPLACE FUNCTION audit_users_trigger()
RETURNS trigger AS $$
BEGIN
    INSERT INTO audit_logs (entity, entity_id, action, actor, before, after, at)
    VALUES (
        'User',
        COALESCE(NEW.id::text, OLD.id::text),
        TG_OP,
        current_setting('app.actor', true),
        to_jsonb(OLD),
        to_jsonb(NEW),
        now()
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_audit
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION audit_users_trigger();
```

App sets `SET LOCAL app.actor = 'u_123'` at session start so the trigger has the actor.

### High-volume — transactional outbox to Kafka

```sql
CREATE TABLE outbox (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    published_at TIMESTAMPTZ
);
```

ORM hook writes to `audit_logs` AND `outbox` in the same transaction. A separate worker tails `outbox`, ships to Kafka, marks `published_at`. Audit log remains queryable from Postgres; warm reads go to ClickHouse/OpenSearch index.

## Step-by-step dry run

Scenario: A `PATCH /users/1` sets `email = 'new@x.com'` while `name` is unchanged.

```
T0  middleware sets current_actor='u_admin', current_request_id='r_42'
T1  controller: user = db.get(User, 1)  → loaded; snapshot {email='old', name='Alice'}
T2  user.email = 'new@x.com'             → SQLAlchemy marks dirty, history captured
T3  db.commit()  → before_flush event fires
      session.dirty = {user}
      session.is_modified(user) = True
      diff: before={'email':'old'}, after={'email':'new@x.com'}
      adds AuditLog(entity='User', entity_id='1', action='UPDATE',
                    actor='u_admin', before=..., after=..., request_id='r_42')
    flush emits:
       UPDATE users SET email='new@x.com', updated_at=NOW(), updated_by='u_admin' WHERE id=1 AND version=N
       INSERT INTO audit_logs(...) VALUES (...)
    COMMIT (atomically)

If COMMIT fails (deadlock, constraint), neither row persists.
If audit insert raises (PII redaction bug), the user UPDATE rolls back too — preserves consistency.
```

Bulk path (bypass):

```
db.execute(update(User).where(User.tenant_id == X).values(active=False))
  → no ORM hook fired. ORM doesn't load the rows, so no diff can be computed.
  → DB trigger catches it: writes one audit_logs row per affected row.
```

## How to think aloud in the interview

> "Three layers, three jobs:
>
> 1. **Metadata columns** on every table — `created_at/by`, `updated_at/by`, `version`. Cheap and always-on.
>
> 2. **Append-only `audit_logs` table** populated by ORM hooks. SQLAlchemy `before_flush`, Hibernate `EmptyInterceptor` or Envers, TypeORM subscribers, Prisma extensions. Writes the audit row in the **same transaction** as the change — atomic.
>
> 3. **DB triggers** as a safety net for paths that bypass the ORM — bulk ops, raw SQL, admin tools. The actor comes from `SET LOCAL app.actor` at session start.
>
> Two operational notes:
> - **PII redaction** in the hook before serializing the diff.
> - **High volume**: partition `audit_logs` by month, archive cold partitions to S3. For real scale, use **transactional outbox** to Kafka → ClickHouse for queries.
>
> Trap I always raise: **bulk ops bypass ORM hooks**. If you need 100% coverage, you either restrict bulk writes to specific code paths that emit audit rows manually, or you accept the cost of DB triggers."

## Important takeaways

- **Three layers** of audit: metadata columns, append-only log, DB-trigger safety net.
- **Hook in `before_flush`** for change detection; resolve PKs in `after_flush_postexec`.
- **Same transaction** as the main write → atomicity.
- **Actor context** from middleware via contextvar / ThreadLocal / AsyncLocalStorage.
- **PII redaction** is non-negotiable — whitelist or denylist sensitive fields.
- **Bulk ops + raw SQL bypass ORM hooks** — DB triggers or restricted code paths.
- **High volume** → partition + archive, or transactional outbox to Kafka.
- **Read access control** on audit logs is often stricter than on the data.

## Variants

1. **"Use Hibernate Envers?"** Great for "show me User#1 at revision 17". Creates `_aud` tables, generates revision IDs. Storage cost is meaningful; can't customize easily.
2. **"How would you do this with event sourcing?"** Audit log IS the source of truth; current state is a projection. Big architectural shift; only do it for the parts of the domain that truly need it.
3. **"What if the audit table is the bottleneck?"** Partition, move to a separate disk/cluster, or async via transactional outbox.
4. **"How do you handle GDPR's right-to-delete on audit logs?"** Either mark logs as tombstoned (replace PII with hash) or have a retention policy that drops cold partitions.
5. **"Postgres temporal tables / system versioning?"** SQL:2011 system-versioned tables — Postgres doesn't have it natively, but extensions exist; MySQL 8 doesn't either; SQL Server / MariaDB do.
6. **"Audit reads, not writes?"** Add to API gateway / service layer; ORM doesn't see reads well.

## Revision notes

> **audit-log-orm — 60 second recap**
> - 3 layers: metadata columns, append-only `audit_logs`, DB triggers.
> - ORM hook in `before_flush` (SQLAlchemy), `EmptyInterceptor`/Envers (Hibernate), Subscriber (TypeORM), `$extends` (Prisma).
> - **Same transaction** as the audited write → atomic.
> - Actor from contextvar/ThreadLocal populated by middleware.
> - PII redaction is mandatory.
> - **Bulk + raw SQL bypass ORM hooks** → use DB triggers as the safety net.
> - High-volume: partition, archive, or outbox-to-Kafka.
> - Envers = full row versioning, queryable past states; storage cost.
> - **Trap:** PK isn't assigned in `before_flush` for INSERTs — resolve in `after_flush_postexec`.
