# Multi-tenant ORM strategy — schema-per-tenant, row-level, DB-per-tenant

## Source / Origin
- SaaS architecture canon: Microsoft Azure SaaS guidance, AWS SaaS Lens, Salesforce's multi-tenant whitepaper.
- Postgres Row Level Security (RLS) docs: <a href="https://www.postgresql.org/docs/current/ddl-rowsecurity.html" target="_blank" rel="noopener noreferrer">https://www.postgresql.org/docs/current/ddl-rowsecurity.html</a>
- Real-world reference: how Notion, Slack, Linear, GitHub partition tenant data.

## Why this question matters in interviews
Every B2B SaaS interview asks some flavor of this. The candidate who picks "row-level + tenant_id column" without thinking through index size, blast-radius of a missing WHERE clause, and per-tenant operations (deletes, backups, migrations) reveals they've never operated multi-tenant at scale. Seniors should know the **three canonical strategies**, their **isolation/cost trade-offs**, and the **ORM mechanisms** to enforce them (Hibernate filters, SQLAlchemy events, Prisma extensions, RLS policies).

## Concepts involved

### The three strategies

```
                           ISOLATION  ←──────────────────→  DENSITY
                                                            (tenants/$ )

  DB-per-tenant      ━━━━━━━━━━━━━━●                       ●          ←──────
  Schema-per-tenant         ━━━━━━━━●                ●            ←──────
  Row-level (shared)              ━━━●         ●                    ←──────


  ┌────────────────────────┐ ┌────────────────────────┐ ┌─────────────────────────┐
  │  DB-PER-TENANT         │ │  SCHEMA-PER-TENANT     │ │  ROW-LEVEL (shared)     │
  │                        │ │                        │ │                         │
  │  tenant_a → db_a       │ │  tenant_a → schema_a   │ │  one DB, one schema     │
  │  tenant_b → db_b       │ │  tenant_b → schema_b   │ │  every row has          │
  │  ...                   │ │  ...                   │ │     tenant_id           │
  │                        │ │                        │ │                         │
  │  Strongest isolation   │ │  Strong isolation,     │ │  Weakest isolation,     │
  │  Costliest             │ │  per-schema migrations │ │  cheapest, densest      │
  │  Per-tenant backup     │ │  Catalog bloat at 1000+│ │  WHERE tenant_id needed │
  │  Per-tenant scale      │ │  schemas               │ │  on every query         │
  │  Hardest cross-tenant  │ │  Connection sharing OK │ │  Hot tenants noisy-     │
  │     analytics          │ │                        │ │     neighbor risk       │
  └────────────────────────┘ └────────────────────────┘ └─────────────────────────┘
```

### Edge cases / interview traps

1. **A missing `WHERE tenant_id = ?`** in row-level model is a **data leak**, not a bug. Defense-in-depth via RLS, ORM filters, or query interceptors is mandatory.
2. **Postgres RLS** is the gold standard for row-level — enforced at the DB, can't be bypassed by app bugs. Costs a planner step per query.
3. **Schema-per-tenant catalog bloat** — Postgres `pg_class` and `pg_attribute` grow with `N_tenants × N_tables`. At ~5000 tenants × 50 tables = 250k rows; planner slows down, autovacuum overhead spikes.
4. **Per-tenant migrations** in schema/DB models — runs N times; needs orchestration with progress tracking; partial-failure handling.
5. **Cross-tenant analytics** is easy in row-level (one query), painful in DB-per-tenant (federation / ETL).
6. **Connection pool exhaustion** — DB-per-tenant means N pools or one pool with constant reconnect. Use a connection multiplexer (PgBouncer transaction mode) or per-tenant routing.
7. **GDPR / data deletion** — DB-per-tenant: drop database. Schema-per-tenant: drop schema. Row-level: cascade DELETE across N tables with potential FK ordering pain.
8. **Tenant ID in JWT vs URL vs subdomain** — pick one source of truth and enforce in middleware before any query runs.
9. **Hot tenants** in row-level need per-tenant rate limits and sometimes partition-pruning (Postgres declarative partitioning by tenant_id).
10. **ORM identity map vs tenants** — if you cache User#1 from tenant A and then serve tenant B, you've leaked. ORM caches must be tenant-aware.

## Mental Model

Think of multi-tenancy as a **directory** problem:

- **DB-per-tenant** = each customer has their own building.
- **Schema-per-tenant** = same building, different floors.
- **Row-level** = same floor, color-coded desks.

The tighter the share, the higher the density, the easier the noisy-neighbor problem and the heavier the must-not-leak burden.

```
   User logs in
        │
        ▼
  ┌────────────┐
  │ Identify   │   from JWT claim / subdomain / URL path
  │ tenant_id  │
  └────┬───────┘
       ▼
  ┌─────────────────────┐
  │ Route to data       │
  │  - DB pool          │  (DB-per-tenant)
  │  - search_path SET  │  (Schema-per-tenant)
  │  - SET app.tenant_id │ (Row-level w/ RLS)
  └─────────────────────┘
```

## Why interviewers care

- Tests architectural reasoning across cost, isolation, ops complexity.
- Reveals whether you've thought about **migrations, backups, compliance, blast radius**.
- The right answer is "it depends" — but you must say what it depends on.

## Common beginner confusion

- "Row-level is just adding a `tenant_id` column." It's also adding it to **every index**, **every FK**, **every WHERE**, and enforcing it at multiple layers.
- "Schema-per-tenant scales linearly." Postgres catalog cost is non-linear; pg_dump time grows; backups become harder.
- "DB-per-tenant solves all problems." It also creates a connection-pooling problem and an analytics problem.
- "I'll add the tenant_id later." You won't — backfilling is a multi-week migration.

## Brute force approach

Start row-level, ship fast, hope nobody forgets a WHERE clause. Often fine for early SaaS — until the first incident or compliance audit.

## Optimal approach

Pick by **isolation requirement** and **tenant size distribution**:

| Constraint | Pick |
|---|---|
| Strict per-tenant SLA / encryption keys / data residency | DB-per-tenant |
| Compliance (HIPAA, FedRAMP) demands schema isolation | Schema-per-tenant |
| Many small tenants, low isolation requirement | Row-level + RLS |
| Mixed (a few huge tenants + many tiny) | **Hybrid**: big tenants on dedicated DBs, small on shared row-level |

Implementation rule: **defense-in-depth**. Even row-level should have RLS policies + ORM filters + middleware guards.

## Solution

### Strategy A — Postgres RLS for row-level

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON users
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- App sets the GUC per session/transaction
SET app.tenant_id = '7c1b...';

-- Now any SELECT/UPDATE/DELETE on users transparently filtered
SELECT * FROM users;   -- only this tenant's rows, no WHERE needed
```

```python
# SQLAlchemy — set GUC at session start
from sqlalchemy import event, text

@event.listens_for(Session, 'after_begin')
def set_tenant(session, transaction, connection):
    tenant_id = current_tenant_var.get()    # contextvar populated by middleware
    if tenant_id:
        connection.execute(text("SET LOCAL app.tenant_id = :t"), {'t': str(tenant_id)})
```

### Strategy B — Schema-per-tenant with SQLAlchemy

```python
def get_db(request: Request) -> Iterator[Session]:
    tenant_schema = request.state.tenant_schema  # e.g., 'tenant_42'
    with SessionLocal() as db:
        db.execute(text(f"SET search_path TO {tenant_schema}, public"))
        yield db
```

```python
# Hibernate — MultiTenantConnectionProvider + CurrentTenantIdentifierResolver
public class SchemaTenantConnectionProvider extends AbstractDataSourceBasedMultiTenantConnectionProviderImpl {
    @Override
    protected DataSource selectDataSource(Object tenantIdentifier) {
        return defaultDataSource;
    }

    @Override
    public Connection getConnection(Object tenantId) throws SQLException {
        Connection c = defaultDataSource.getConnection();
        c.createStatement().execute("SET search_path TO " + tenantId + ", public");
        return c;
    }
}
```

### Strategy C — DB-per-tenant routing

```typescript
// TypeORM — per-tenant DataSource cache
const dataSources = new Map<string, DataSource>();

async function getDS(tenantId: string): Promise<DataSource> {
    let ds = dataSources.get(tenantId);
    if (!ds) {
        ds = new DataSource({
            type: 'postgres',
            url: lookupDbUrl(tenantId),
            entities: [...],
            poolSize: 5,    // small per tenant to limit aggregate
        });
        await ds.initialize();
        dataSources.set(tenantId, ds);
    }
    return ds;
}
```

```typescript
// Prisma — per-tenant client cache (one client per DB URL)
const clients = new Map<string, PrismaClient>();
function getPrisma(tenantId: string): PrismaClient {
    let c = clients.get(tenantId);
    if (!c) {
        c = new PrismaClient({ datasources: { db: { url: lookupDbUrl(tenantId) } } });
        clients.set(tenantId, c);
    }
    return c;
}
```

### Defense-in-depth: ORM filter for row-level (Hibernate)

```java
@Entity
@FilterDef(name = "tenantFilter", parameters = @ParamDef(name = "tenantId", type = "uuid"))
@Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
public class User { ... }

// Apply per session
session.enableFilter("tenantFilter").setParameter("tenantId", tenantId);
```

### Defense-in-depth: SQLAlchemy global event

```python
@event.listens_for(Query, "before_compile", retval=True)
def add_tenant_filter(query):
    tid = current_tenant_var.get()
    if tid is None:
        return query
    for desc in query.column_descriptions:
        entity = desc['entity']
        if entity and hasattr(entity, 'tenant_id'):
            query = query.filter(entity.tenant_id == tid)
    return query
```

## Step-by-step design walk-through

### Greenfield SaaS: 200 tenants today, 10k expected, B2B project management tool

1. **Isolation requirement**: standard B2B, no HIPAA, but legal-hold and per-customer deletion needed.
2. **Tenant size distribution**: 80% small (<1MB data), 15% medium, 5% large (>10GB).
3. **Cross-tenant analytics**: must aggregate usage metrics → row-level is easiest.
4. **Compliance**: GDPR delete-on-request.
5. **Pick**: **Row-level + Postgres RLS**, with hybrid escape hatch — large tenants migrated to dedicated DBs as they grow.
6. **Schema**: every table has `tenant_id UUID NOT NULL`. Composite indexes `(tenant_id, ...)` for primary access paths.
7. **Enforcement**: RLS policy on every table + ORM filter + middleware guard. If `app.tenant_id` not set, deny.
8. **Deletion**: cascade DELETE on FK to `tenants(id)` + RLS bypass for the delete operation.
9. **Migration**: standard migrations, applied once.

### Brownfield: existing row-level app outgrew shared DB

1. Identify hot tenants (top 5% by query volume).
2. Provision dedicated DB per hot tenant.
3. Run dual-writes during cutover, verify, swap reads, decommission shared rows.
4. Routing layer determines which DB by tenant_id.

## How to think aloud in the interview

> "Three strategies on an isolation-vs-density axis:
>
> 1. **DB-per-tenant** — strongest isolation, easy per-tenant ops (backup, delete, scale), hard cross-tenant analytics, connection-pool pain. Pick when isolation is required (residency, BAA, dedicated keys) or when tenants are large.
>
> 2. **Schema-per-tenant** — same DB, separate schemas. Decent isolation, connection sharing works, per-tenant migrations are an ops concern. Postgres catalog grows linearly; breaks past ~5000 schemas.
>
> 3. **Row-level (shared)** — one schema, `tenant_id` on every table, every index, every query. Densest, cheapest, but a missing WHERE is a data leak.
>
> For row-level I always insist on **defense-in-depth**: Postgres RLS at the DB + ORM filter + middleware guard. RLS alone is enough; the others catch programming errors before they hit the DB.
>
> My default for greenfield B2B SaaS: row-level + RLS, with an escape hatch to dedicated DBs for whales. Cross-tenant analytics stay simple, ops stays manageable, and isolation is enforced where it matters.
>
> Trap I always raise: **caching across tenants**. The ORM identity map, Redis caches, even CDN caches must include tenant_id in the key — otherwise the densest model becomes the leakiest."

## Important takeaways

- **Three strategies**: DB-per-tenant, schema-per-tenant, row-level.
- **Trade-off axis**: isolation ↔ density (cost per tenant).
- **Row-level must use defense-in-depth**: RLS + ORM filter + middleware.
- **Postgres RLS** is the gold standard for row-level enforcement.
- **Cache keys must include tenant_id** — identity maps, Redis, CDN.
- **Migrations**: row-level = once. Schema/DB = per-tenant orchestration.
- **Cross-tenant analytics** is hard in DB-per-tenant; easy in row-level.
- **Hybrid model** for large enterprise tenants + many small ones.

## Variants

1. **"What's the storage cost of `tenant_id UUID` on every row?"** 16 bytes plus index overhead. Add it to every composite index instead of as a single-column index — much smaller footprint.
2. **"How do you prevent a missing WHERE clause?"** RLS. Or query interceptor that fails closed on missing tenant context.
3. **"How do you migrate one tenant out to its own DB?"** Dual-write window: replicate via logical decoding or app-level dual-write, cutover reads, drain writes, delete original.
4. **"How do you handle data residency (EU vs US)?"** Region-keyed routing. Often forces DB-per-region-tenant.
5. **"How do you keep autovacuum healthy in row-level with hot tenants?"** Per-table autovacuum tuning; consider declarative partitioning by tenant_id for the largest tables.
6. **"Connection pooling with DB-per-tenant?"** PgBouncer per DB, or single PgBouncer with prepared-statement-aware multiplexing. Watch aggregate DB connection count.

## Revision notes

> **multi-tenant-orm — 60 second recap**
> - 3 strategies: DB-per-tenant, schema-per-tenant, row-level. Isolation↔density.
> - Row-level: `tenant_id` everywhere, in every index, in every query.
> - **Defense-in-depth** for row-level: Postgres RLS + ORM filter + middleware.
> - Schema-per-tenant: Postgres catalog bloats past ~5000 schemas.
> - DB-per-tenant: strongest isolation, hardest connection pooling and analytics.
> - Caches MUST be tenant-aware: identity map, Redis, CDN.
> - Default for greenfield B2B SaaS: row-level + RLS; whales onto dedicated DBs.
> - **Trap:** missing WHERE clause = data leak. RLS makes it physically impossible.
