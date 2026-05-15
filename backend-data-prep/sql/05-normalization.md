# Database Normalization & Schema Design

## Why this matters in backend interviews

- **Every schema-design machine coding round** tests this. The interviewer hands you a problem (parking lot, hotel booking, Splitwise) and you sketch tables on a whiteboard.
- **System design**: normalization is the bedrock of any data model discussion.
- **Senior signal**: knowing *when not* to normalize — and being able to argue both sides — separates juniors from SDE2.
- **Debugging**: poorly normalized schemas cause update anomalies, inconsistencies, and bloat. Recognizing this in legacy code is a senior skill.

---

## Core concepts

### Why normalize

Three goals:
1. **No redundancy** — the same fact shouldn't live in multiple rows
2. **Consistency** — update one place, not many
3. **Integrity** — constraints enforce truth at the DB level

The cost: more joins. Trade-off is at the heart of schema design.

### The forms

#### 1NF — Atomic columns

- No multi-valued columns (no `tags: "red,blue,green"` in a single VARCHAR)
- No repeating groups (`phone1`, `phone2`, `phone3`)
- Each row identifiable (have a PK)

Fix: move to a child table.

```sql
-- BAD
users (id, name, phones VARCHAR)  -- "555-1234,555-9999"

-- GOOD
users (id, name)
user_phones (user_id FK, phone, label)
```

Postgres array columns technically violate 1NF strictly, but in practice are fine for small bounded lists with **no need to query individual elements**.

#### 2NF — No partial dependency

If the PK is composite, every non-key column must depend on the **whole** PK, not part of it.

```sql
-- BAD (PK = order_id, product_id; product_name depends on product_id only)
order_items (order_id, product_id, product_name, quantity)

-- GOOD
order_items (order_id, product_id, quantity)
products    (id, name)
```

#### 3NF — No transitive dependency

Non-key columns must depend on the PK, not on other non-key columns.

```sql
-- BAD
employees (id, name, dept_id, dept_name)  -- dept_name depends on dept_id, not id

-- GOOD
employees   (id, name, dept_id)
departments (id, name)
```

#### BCNF (Boyce-Codd)

Stronger than 3NF. Every functional dependency `X → Y` must have `X` as a superkey. Rarely matters in practice; if you're at 3NF you're usually fine.

#### 4NF / 5NF

Theoretical, rarely come up in interviews. Mention only if asked.

### Denormalization — when to break the rules

Reasons to denormalize:
- **Performance**: a 4-way join on a hot path can be collapsed to 1 table read
- **Read-heavy workloads** (analytics, dashboards)
- **Reporting tables** (precomputed daily aggregates)
- **Materialized views** for slow queries
- **Caching layer**: cache the joined result

Costs:
- Risk of inconsistency (must update multiple places)
- Larger row size → fewer rows per page → more I/O for scans
- Schema change is harder

**Rules:**
1. Always document the source of truth (which table is canonical)
2. Build a refresh / sync mechanism (triggers, jobs, CDC)
3. Don't denormalize until you measure the join cost

### Common patterns

#### Star schema (analytics)
Fact tables (orders, events) + dimension tables (products, users, dates). Heavily denormalized facts to avoid joins. Used in data warehouses (Snowflake, BigQuery, Redshift).

#### Snowflake schema
Star schema but with normalized dimensions. Less common.

#### Audit / event sourcing
Append-only event log; current state derived. Pure normalization is impossible; trade audit for query complexity.

#### Soft deletes
Add `deleted_at TIMESTAMPTZ`. Pros: history, recoverable. Cons: every query needs `WHERE deleted_at IS NULL`, indexes inflate. Use partial indexes.

### Anti-patterns

#### EAV (Entity-Attribute-Value)
```sql
entities (id, type)
attributes (id, name)
entity_attribute_values (entity_id, attribute_id, value)  -- value as TEXT
```
- Looks flexible
- Reality: terrible joins, no types, no constraints, no indexes work well
- Use JSONB instead (Postgres) for genuinely schemaless extension data

#### "God table"
A single table with 80 columns covering 5 concepts. Update anomalies, lock contention.

#### Boolean explosion
`is_active`, `is_verified`, `is_premium`, `is_admin`, `is_deleted`, … → use ENUM or proper status tables.

#### "id, type" polymorphic FKs without enforcement
```sql
comments (id, target_type VARCHAR, target_id BIGINT)  -- target = post|user|video
```
Can't have a FK constraint. Use:
- Multiple nullable FKs (one per target type) — DB enforces integrity
- Or accept the trade-off if the design genuinely needs polymorphism

### Surrogate vs natural keys

- **Natural key** (`email`, `SSN`, `ISBN`) — already exists in the domain. Drawback: business value can change (people change emails).
- **Surrogate key** (`id BIGSERIAL`) — internal, stable, opaque. **Preferred default.**
- Use both: surrogate as PK, unique constraint on natural key.

### Common misconceptions

- "Always normalize to 3NF" — pragmatic engineers stop at the right level for the workload
- "Denormalization is faster" — only if the join was actually slow, and the duplication is maintainable
- "Foreign keys slow writes too much, drop them" — usually a bad trade. Drop only if measurements demand it.
- "JSON columns mean no schema" — schema lives in the application; you just lose the DB safety net

### Interview traps

1. **Normalizing for normalization's sake** — interviewer will push back. Defend the design with workload reasoning.
2. **Composite PKs** — you'll be asked when they're appropriate (e.g., `order_items(order_id, product_id)`). Answer: when the natural identity is the combination and there's no benefit to a surrogate.
3. **Polymorphic association** — interviewer asks how to handle "comments can be on posts or videos." Discuss trade-offs.
4. **Many-to-many** — always create a join table; never store as array unless truly small + bounded + non-queryable.
5. **Audit history** — separate audit table vs `deleted_at` vs event sourcing.

---

## Real examples

### E-commerce — normalized schema

```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE addresses (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  line1 TEXT, line2 TEXT, city TEXT, state TEXT, country TEXT, postal TEXT,
  is_default BOOLEAN DEFAULT false
);

CREATE TABLE categories (
  id BIGSERIAL PRIMARY KEY,
  parent_id BIGINT REFERENCES categories(id),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category_id BIGINT NOT NULL REFERENCES categories(id),
  price_cents INT NOT NULL CHECK (price_cents >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE inventory (
  product_id BIGINT PRIMARY KEY REFERENCES products(id),
  qty_on_hand INT NOT NULL CHECK (qty_on_hand >= 0),
  qty_reserved INT NOT NULL DEFAULT 0 CHECK (qty_reserved >= 0)
);

CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('CART','PLACED','PAID','SHIPPED','CANCELLED')),
  total_cents INT NOT NULL DEFAULT 0,
  shipping_address_id BIGINT REFERENCES addresses(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  paid_at TIMESTAMPTZ
);

CREATE TABLE order_items (
  order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price_cents INT NOT NULL,  -- copied at order time (denormalization for history)
  PRIMARY KEY (order_id, product_id)
);
```

Notes:
- `unit_price_cents` in `order_items` is intentional denormalization — the order should remember the price at the time of purchase, even if the product's price changes later.
- `total_cents` in `orders` is also denormalized — could be computed from items, but kept for fast reads and snapshot integrity.

### Payments — schema with audit

```sql
CREATE TABLE accounts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(id),
  balance_cents BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE transactions (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key TEXT UNIQUE NOT NULL,
  from_account BIGINT REFERENCES accounts(id),
  to_account   BIGINT REFERENCES accounts(id),
  amount_cents BIGINT NOT NULL CHECK (amount_cents > 0),
  status TEXT NOT NULL CHECK (status IN ('PENDING','SUCCESS','FAILED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

- `balance_cents` denormalized for fast reads; updated atomically within transactions
- `idempotency_key` makes retries safe

### Chat — many-to-many participants

```sql
CREATE TABLE conversations (
  id BIGSERIAL PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('DM','GROUP')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversation_participants (
  conv_id BIGINT NOT NULL REFERENCES conversations(id),
  user_id BIGINT NOT NULL REFERENCES users(id),
  joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_read_at TIMESTAMPTZ,
  PRIMARY KEY (conv_id, user_id)
);

CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  conv_id BIGINT NOT NULL REFERENCES conversations(id),
  sender_id BIGINT NOT NULL REFERENCES users(id),
  body TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON messages (conv_id, sent_at DESC);
```

### Polymorphic comments — two solutions

```sql
-- Option A: separate FKs (DB-enforced integrity)
CREATE TABLE comments (
  id BIGSERIAL PRIMARY KEY,
  post_id  BIGINT REFERENCES posts(id),
  video_id BIGINT REFERENCES videos(id),
  body TEXT NOT NULL,
  CHECK (
    (post_id IS NOT NULL)::int + (video_id IS NOT NULL)::int = 1
  )
);

-- Option B: target_type + target_id (no FK; flexibility)
CREATE TABLE comments (
  id BIGSERIAL PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id   BIGINT NOT NULL,
  body TEXT NOT NULL
);
CREATE INDEX ON comments (target_type, target_id);
```

Option A is preferred when target types are bounded and known. Option B is for truly open polymorphism (CMS-like systems).

---

## Common interview questions

1. Explain 1NF, 2NF, 3NF with examples.
2. What is denormalization? When is it appropriate?
3. Surrogate key vs natural key — which to choose?
4. How would you design a schema for [a hotel booking system / parking lot / chat / Splitwise]?
5. How do you model many-to-many?
6. How do you handle polymorphic associations?
7. Audit trail design.
8. Soft delete vs hard delete vs archive table.
9. EAV — why is it an anti-pattern?
10. When to use JSON columns.
11. How would you handle product price changes in an e-commerce order?
12. Composite PK vs surrogate PK — when?

---

## Detailed answers

### 1. Normal forms
- **1NF**: atomic columns, no repeating groups
- **2NF**: no partial dependency on a composite key
- **3NF**: no transitive dependency between non-key columns
Walk through each with `order_items` example.

### 2. Denormalization
Acceptable when:
- Reads dominate writes
- A specific join is on a hot path (measured)
- The duplicated data has a clear source of truth and refresh mechanism
- Example: order total snapshot, product price snapshot on order_item

### 3. Surrogate vs natural
Default: surrogate. Add UNIQUE constraint on natural key. Surrogates are stable, opaque, performant. Natural keys leak business semantics and break when domain changes.

### 4. Schema design (parking lot example)
```
ParkingLot   (id, name, capacity, address)
Floor        (id, lot_id FK, floor_number)
ParkingSpot  (id, floor_id FK, spot_no, size ENUM(SMALL,MED,LARGE), is_occupied)
Vehicle      (id, plate, type ENUM)
Ticket       (id, vehicle_id FK, spot_id FK, entry_time, exit_time, fee)
```
Walk through:
- 3NF (no transitive deps)
- `is_occupied` is denormalized; could be derived from Ticket.exit_time IS NULL — discuss trade-off
- Index on `(spot_id) WHERE is_occupied = false` for find-empty-spot

### 5. Many-to-many
Always a join table: `user_role(user_id, role_id)` with composite PK. Optionally add metadata (granted_at, granted_by).

### 6. Polymorphic
Two options as shown above. Prefer multiple FKs when bounded.

### 7. Audit trail
Three approaches:
- **Audit columns**: `created_at`, `updated_at`, `updated_by` — minimal, no history
- **Audit table**: `entity_audit(entity_id, action, old_json, new_json, ts, actor)` — separate table, populated by triggers or app
- **Event sourcing**: events are the source of truth; current state derived. Heavyweight but auditable by design.

### 8. Soft vs hard delete
- **Hard delete** (`DELETE`): row gone, GDPR-friendly
- **Soft delete** (`deleted_at`): retains history; every query needs filter; partial indexes help
- **Archive table**: move row to `..._archive` table; clean separation, slower restores

### 9. EAV
Each attribute is a row → joins explode, no types, no real constraints, indexes ineffective. Use JSONB for schemaless extensions instead.

### 10. JSON columns
Use for: optional metadata, third-party API responses, feature-flag configs, semi-structured data.
Don't use for: required fields, fields you'll query/filter by frequently. Index with GIN or generated columns.

### 11. Product price changes
Snapshot the price at order time → `order_items.unit_price_cents`. Even though it duplicates data, the order must remember what was paid.

### 12. Composite vs surrogate
- Composite PK: natural identity is a combination (join tables, time-bucketed facts)
- Surrogate PK: everything else
- Modern advice: always surrogate; add unique constraint on the natural combination

---

## Practical coding examples

### Idempotency / dedup
```sql
CREATE TABLE webhook_events (
  external_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Insert with ON CONFLICT DO NOTHING for idempotent ingestion
```

### Hierarchical (tree) — three modeling options
```sql
-- 1. Adjacency list (simplest)
categories (id, parent_id REFERENCES categories(id), name)
-- Query with recursive CTE

-- 2. Path enumeration
categories (id, path TEXT)  -- '/electronics/computers/laptops'

-- 3. Closure table (best for read-heavy)
categories       (id, name)
category_closure (ancestor_id, descendant_id, depth)
```

### Time-series partitioning
```sql
CREATE TABLE events (
  id BIGSERIAL,
  ts TIMESTAMPTZ NOT NULL,
  data JSONB
) PARTITION BY RANGE (ts);

CREATE TABLE events_2026_01 PARTITION OF events
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## Common mistakes

- Stuffing CSV / arrays in a VARCHAR (kills 1NF and queries)
- 80-column "god" table
- Using `is_*` booleans everywhere instead of a single status enum
- Not snapshotting historical values (prices, names)
- Soft delete without partial indexes → indexes balloon
- Storing money as FLOAT (use BIGINT cents or NUMERIC)
- Storing TIME without TZ (`TIMESTAMP` not `TIMESTAMPTZ`)
- No constraints (CHECK, NOT NULL, UNIQUE, FK)

---

## Senior engineer discussion points

- **Schema evolution**: additive-only migrations; never destructive in prod; use views/columns to refactor in stages
- **Data contracts** with downstream consumers — schema is an API
- **CDC (Change Data Capture)** with Debezium / wal2json for syncing denormalized read stores
- **Polyglot persistence**: Postgres for canonical, Redis for cache, Elasticsearch for search, ClickHouse for analytics — different normalizations per store
- **Lookup tables vs ENUMs**: ENUMs are fast and constrained but schema-locked; lookup tables are flexible but cost a join
- **Snake_case vs camelCase** — pick one and enforce via linter; doesn't matter which
- **Naming**: singular vs plural table names (consistency > correctness)
- **Constraint placement**: app-level vs DB-level. DB-level wins for correctness; app-level is more flexible

---

## Revision notes

- 1NF: atomic • 2NF: no partial dep on composite PK • 3NF: no transitive dep
- Denormalize for reads, document SoT, automate refresh
- Surrogate PK + UNIQUE on natural key = default
- M2M = join table, composite PK
- Polymorphic: prefer multiple nullable FKs with CHECK
- Snapshot historical values (price, name) on the child row
- EAV is a trap; use JSONB
- Soft delete needs partial indexes
- Money = BIGINT cents (never FLOAT)
- Time = TIMESTAMPTZ
- Hierarchical: adjacency list + recursive CTE, or closure table for read-heavy
