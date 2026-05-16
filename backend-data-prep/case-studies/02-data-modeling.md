# Cross-Store Data Modeling, CDC, Event Sourcing

When a single database stops fitting, the question becomes: **how do you model data across multiple stores while keeping them consistent?**

This file covers the patterns interviewers ask about in senior system design rounds.

---

## Plain-English orientation: what is "data modeling"?

A **data model** is the language your application and your storage agree to speak. The schema you saw in `01-schema-design.md` is one dialect of that language — the one a single relational database speaks. But once your system grows past one box, you find yourself speaking *several* dialects: SQL to Postgres, key-value to Redis, JSON documents to Elasticsearch, event records to Kafka. Data modeling is the discipline of keeping all those dialects mutually intelligible.

Two senior-engineer instincts to internalize:

1. **The model is not the database.** The same business fact can live in many stores at once (the canonical user in Postgres, the search-shaped user in Elasticsearch, the cached user in Redis, the analytics-shaped user in ClickHouse). They are all projections of the same conceptual entity. Your job is to keep them consistent enough for the business.
2. **Modeling is choosing what to store, not just how to store it.** "Should this be a state column or an event log?" "Should I keep the current balance or derive it from a ledger?" "Should this be one fact in 3NF or one denormalized document?" These choices are *modeling*; they precede the choice of database.

> Schema design is "what are the columns?" Data modeling is "what does the business actually mean by this entity, across time and across stores?"

## ## Mental Model: OLTP vs OLAP data modeling

These are the two great families of data modeling, and confusing them costs careers.

```
OLTP (online transactional processing)
  Workload     : many small writes/reads of single rows
  Optimized for: ACID, low-latency single-row access
  Storage      : row-oriented (Postgres, MySQL)
  Schema       : highly normalized (3NF)
  Key question : "what is the current state of this entity?"

OLAP (online analytical processing)
  Workload     : few queries that scan millions/billions of rows
  Optimized for: aggregations, scans, throughput
  Storage      : column-oriented (ClickHouse, BigQuery, Snowflake)
  Schema       : denormalized (star, snowflake, wide tables)
  Key question : "what is the trend across many entities over time?"
```

OLTP models the **present** of one entity at a time. OLAP models the **history** of many entities at once. Almost every modern stack has both: Postgres for the live app, ClickHouse/BigQuery for the dashboards, with CDC or batch ETL gluing them.

## ## Mental Model: star schema

The star schema is the dominant OLAP modeling pattern. One **fact table** in the middle, surrounded by **dimension tables**.

```
                 +---------------+
                 |  dim_customer |
                 +---------------+
                         |
+-------------+          |          +-----------+
| dim_product |----+ +---+---+ +----| dim_date  |
+-------------+    | | fact  | |    +-----------+
                   +-| sales |-+
                   | | _    | |
+-------------+    | +-------+ |    +-----------+
| dim_store   |----+           +----| dim_promo |
+-------------+                     +-----------+

fact_sales : (sale_id, date_id, product_id, customer_id, store_id,
              promo_id, units_sold, revenue_cents)
```

- **Fact rows** are the events ("a sale happened"). Numeric measures (revenue, units) live here.
- **Dimension rows** are the descriptive context ("which product? which customer?"). Strings, hierarchies live here.
- Joins are always fact → dimension, never dimension → dimension. The pattern is shaped like a star.

Why columnar engines love it:
- Fact tables are wide and long; columnar storage compresses them brilliantly.
- Dimensions are small enough to fit in memory; the engine broadcasts them.
- Queries become "scan fact, filter, aggregate, lookup dimension labels" — exactly what columnar engines are tuned for.

## ## Mental Model: snowflake schema

A snowflake schema is a star where dimensions are themselves normalized further.

```
star:                          snowflake:
  fact_sales                    fact_sales
    -> dim_product               -> dim_product
       (category text)              -> dim_category
                                       -> dim_department
```

- Star: one wide dimension table per dimension (denormalized).
- Snowflake: dimensions normalized into multiple linked tables (more joins).

Trade-off: snowflake saves a tiny bit of storage and avoids update anomalies in dimension hierarchies. Star is simpler to query and faster. **Most modern OLAP teams pick star** because storage is cheap and join performance is what users feel.

```
STAR (one hop, fast)        SNOWFLAKE (multiple hops)
fact -- dim                 fact -- dim -- subdim -- subsubdim
```

## ## Mental Model: slowly changing dimensions (SCD)

A customer changes address. A product changes its category. How do you record that history without breaking last year's reports?

- **SCD Type 1** — overwrite. No history kept. Old reports show the new address. Cheap, wrong-feeling.
- **SCD Type 2** — new row per change, with `valid_from` / `valid_to` and `is_current` flag. Reports as-of any date stay accurate. Standard for finance/audit.
- **SCD Type 3** — store the previous value in an additional column. Limited history (just the latest two).

```
SCD Type 2 example:

customer_id  name    address      valid_from   valid_to    is_current
123          Alice   Main St      2023-01-01   2024-06-15  false
123          Alice   Park Ave     2024-06-15   9999-12-31  true
```

Senior signal: knowing that fact tables should reference the **specific SCD-2 row that was current at the time of the fact** — not the latest one. That is what makes "January's revenue" reproduce identically next year.

## ## Mental Model: bi-temporal tables

Two time axes — **when something happened** (valid time) and **when we recorded it** (transaction/system time). Used heavily in finance and insurance where you must answer "what did we *believe* on June 1st about the balance on May 1st?"

```
UNI-TEMPORAL (one time axis)
  +----+--------+-----------+
  | id | value  | valid_at  |
  +----+--------+-----------+

BI-TEMPORAL (two time axes)
  +----+--------+-----------+--------------+
  | id | value  | valid_at  | recorded_at  |
  +----+--------+-----------+--------------+
```

- A correction to a past fact appends a new row with the same `valid_at` but a later `recorded_at`.
- You can query "what did we know on date X?" by filtering `recorded_at <= X` and taking the latest per `valid_at`.

This is the modeling foundation for accurate retroactive corrections without rewriting history.

## ## Mental Model: event-sourced models

In an event-sourced model, the **events are the source of truth**, not the current-state row. The current state is a projection — recomputable, replaceable, multiply-emittable.

```
Event log (append-only):
  +-----------------------------+
  | OrderPlaced     (id=1)      |  --- events are immutable facts
  | ItemAdded       (id=1, sku) |
  | DiscountApplied (id=1, 10%) |
  | OrderShipped    (id=1)      |
  +-----------------------------+
              |
              v
   (replay) -> current_state_projection
              -> shipping_projection
              -> analytics_projection
```

Compare with a CRUD model:
- CRUD: one mutable row; UPDATE rewrites; history lost (or kept in audit tables).
- Event sourcing: history is the model; current state is derived.

Trade-offs are covered in detail in section 4 below, but the modeling perspective is: in event sourcing, **the entity is its history**, not its latest snapshot.

## ## Why interviewers care

Cross-store data modeling is the highest-signal senior topic because:
- It separates engineers who think "one database" from those who think in **systems of stores**.
- It reveals whether you understand **consistency boundaries** (within one DB you have ACID; across DBs you don't, and pretending otherwise causes bugs).
- It tests whether you know the canonical patterns (outbox, CDC, sagas, event sourcing) by name *and* by trade-off.
- It surfaces operational maturity: can you reason about lag, idempotency, schema evolution across teams?

A junior answers "use Kafka." A senior answers "outbox in the OLTP database, Debezium reads the WAL, partition by entity-id for ordering, idempotent consumers keyed on event-id, and a reconciliation job that periodically diffs canonical vs derived stores."

## ## Common beginner confusion

| Belief | Reality |
|---|---|
| "Just call two writes in sequence — what could go wrong?" | The dual-write problem. The second write can fail silently and leave drift forever. |
| "Eventual consistency = no guarantees." | Wrong — it means the system *will* converge, given finite delay. With idempotent consumers and CDC, that delay is often <1s. |
| "Event sourcing is just an audit log." | An audit log records what happened; event sourcing makes events the only writes — current state is *derived*. Audit logs are easier; event sourcing is heavier. |
| "Sagas replace transactions." | They simulate them across services using compensations — they do not give you ACID. Intermediate states are visible. |
| "Schema registry is overkill." | At <5 services maybe; at 50 services it's the only thing keeping the org alive. |
| "Use a star schema for OLTP too." | No — star sacrifices update consistency for read speed; OLTP cannot tolerate update anomalies. |
| "Event sourcing means I get free time travel." | Only if you also write the snapshotting strategy. Replaying 10M events for a balance read is not free. |
| "CDC replaces my outbox." | CDC reads raw row changes; outbox lets you publish *business intents* (with meaningful payloads). Often you use both. |

## ## First-principles: what is "consistency" between stores?

Inside one database, consistency is enforced by transactions: a write either makes the entire change visible or none of it. Across databases, there is no shared transaction. So "consistency between stores" must be a different kind of guarantee:

- **Convergent** — given enough time and no further writes, all stores will hold the same projection of the data. (Eventual consistency.)
- **Causal** — if write A happened before write B in one store, no other store will show B without A.
- **Read-your-writes** — a client that wrote will see its own write back, regardless of replica lag (often by routing reads to the primary briefly).
- **Bounded staleness** — derived stores lag the canonical store by at most N seconds.

A senior engineer doesn't just say "eventually consistent" — they specify *which* of these guarantees they need, and design the pipeline (outbox, CDC, idempotency keys, reconciliation jobs) to deliver it.

---

## Why this matters in backend interviews

- Almost every "design X at scale" question forces a multi-store answer (Postgres + Redis + Elasticsearch + Kafka + ...)
- The hard part is **consistency between stores** — not the stores themselves
- Senior signal: knowing the outbox pattern, CDC, and event sourcing trade-offs

---

## 1. Polyglot persistence

### Why this section comes first

Once you accept that one database cannot serve every workload, you accept polyglot persistence. The rest of this file (outbox, CDC, sagas, event sourcing) exists *because* polyglot is the reality of modern systems. Each pattern is an answer to: "we have N stores; how do we keep them in sync?"

Use the right store for each access pattern.

| Concern | Store |
|---|---|
| Canonical user / order state | Postgres |
| Session, cache, rate limits | Redis |
| Full-text search | Elasticsearch / OpenSearch |
| Analytics / dashboards | ClickHouse / BigQuery / Snowflake |
| Real-time event stream | Kafka / Redis Streams |
| Time-series metrics | TimescaleDB / InfluxDB / Prometheus |
| Geospatial | PostGIS / Redis Geo |
| Graph | Neo4j |

### Trade-off
Each extra store costs:
- Operational overhead (monitoring, backup, failure modes)
- Sync complexity (consistency between stores)
- Cognitive load (engineers learning each system)

**Add stores when measured workload demands them, not on speculation.**

---

## 2. The dual-write problem

### Intuition first

Imagine you're a clerk in two offices that don't talk to each other. A customer pays you in office A; you must also record the payment in office B. You write it down in A, walk to B — and on the way, B's electricity goes out. A says "paid"; B says "unpaid". Both are now "wrong" — and worse, you don't even know they disagree until the customer complains.

This is the dual-write problem in plain English. The two offices are your database and your search index (or your cache, or your downstream service). The walk between them is the network. You cannot solve this with cleverness in application code; you must change the *protocol* so that the second write is reconstructible from the first.

**Naive multi-store write:**
```python
db.commit_order()      # ✓
search.index_order()   # ✗ throws
# Now Postgres has the order; Elasticsearch doesn't. Drift forever.
```

Even with try/catch, you can't make two unrelated systems atomically commit. This is the **dual-write problem**.

Solutions in increasing order of robustness:

### A) Retry queue
Write to DB; enqueue async job for the second write. Job retries with backoff.
- Pros: simple
- Cons: queue can also fail; dedup needed; eventual consistency

### B) Outbox pattern
Write the second-write *intent* to an `outbox` table inside the same DB transaction:
```sql
BEGIN;
INSERT INTO orders ...;
INSERT INTO outbox (topic, payload) VALUES ('order.placed', ...);
COMMIT;
```
A worker (or CDC stream) reads `outbox` and publishes externally.

- Pros: DB write + intent atomic
- Cons: requires a worker; at-least-once delivery (idempotent consumers)

### C) CDC (Change Data Capture)
Subscribe to the DB's WAL/oplog via Debezium / wal2json / MongoDB change streams. Publish to Kafka.
- Pros: no app-level change; captures all changes; resilient to missed events
- Cons: infra complexity; schema evolution coordination

### D) Event sourcing
Events are the only writes; current state is derived. (See section 4.)

### Visual: the four solutions on one axis

```
Robustness ->

retry queue  --->  outbox  --->  CDC  --->  event sourcing
  (weak)         (good)        (strong)      (paradigm shift)

  app code       app code +    infra-heavy   redesign the
  + queue        DB table      (Debezium,    write model
                 + worker      Kafka, etc.)
```

Most production teams land at **outbox** or **outbox + CDC**. Event sourcing is rare and deliberate.

---

## 3. Eventual consistency in practice

Most "real-time" features tolerate seconds of inconsistency:
- Search index updated within ~1s of write → acceptable
- Cache invalidation within 1-5s → acceptable
- Analytics warehouse 5-minute lag → acceptable
- Money in two accounts not matching → **never acceptable** (use ACID or distributed SQL)

Design checks:
- Is there a moment when this looks wrong to the user?
- Does the staleness affect a business invariant?
- Can the user retry / refresh?

---

## 4. Event sourcing + CQRS

### When does event sourcing pay for itself?

Before any code: ask yourself which side of the line you're on.

```
PAYS OFF                          DOESN'T PAY OFF
+ regulated finance               - simple CRUD app
+ complex state transitions       - 90% of microservices
+ multiple read projections       - team without ops capacity
+ "how did we get here?" matters  - one read model, simple writes
+ time-travel queries needed      - time-travel = nice-to-have
```

Event sourcing is **paradigm-shifting** — it isn't a feature you bolt on, it's a different way of thinking about what an entity *is*. Adopt it when the business demands an audit-true history, not because you read a blog post.

### Event sourcing
- Store **events**, not state
- Current state derived by replaying events
- Events are immutable; never updated

```
Events table (append-only):
  account_created   (id=1, owner=Alice)
  deposit           (id=1, amount=100)
  withdraw          (id=1, amount=30)
  deposit           (id=1, amount=50)

Current balance = 100 - 30 + 50 = 120
```

Pros:
- Full audit trail (every change is recorded)
- Time travel (replay state at any moment)
- Multiple projections (different views of same events)
- Easier to add new features (just project existing events)

Cons:
- Higher complexity
- Schema evolution (event versioning)
- Snapshot needed for large histories (don't replay 1M events on each read)
- Query is harder (must materialize projections)

### CQRS (Command Query Responsibility Segregation)
- Writes go through commands → events → write model
- Reads served from separate, denormalized read model
- Read model updated asynchronously from events
- Eventually consistent

```
                 Events
   Command      ─────────►    Write store
    Side                       (e.g., events table)
                                    │
                                    ▼
                              Projector
                                    │
                                    ▼
   Read         ─────────►    Read store (per query)
    Side                       (e.g., Postgres, ES, Redis)
```

### When to use
- High audit / regulatory requirements (banking, healthcare)
- Complex business processes with many state transitions
- Need for multiple read models from the same source of truth

### When NOT to use
- Simple CRUD apps (overkill)
- Team doesn't have ops capability for the additional infrastructure

### Snapshotting — the practical detail interviewers probe

Replaying 10 million events to compute one balance is unacceptable. The standard fix: **periodic snapshots**.

```
Events:
  E1   E2   E3   E4   E5   E6   E7   E8   E9   E10
                       |                          |
                       Snapshot                   Snapshot
                       (state at E5)              (state at E10)

To rebuild current state:
  load latest snapshot (E10) -> 0 events to replay
  or
  load earlier snapshot (E5) + replay E6..E10 -> 5 events
```

Senior signal: knowing that snapshots are derived, throwable, and rebuildable from the event log at any time. They are a *cache*, not a source of truth.

---

## 5. Multi-store consistency patterns

### Pattern: Postgres → Elasticsearch (search index)

```
Write path:
  BEGIN;
  INSERT INTO products ...;
  INSERT INTO outbox (topic='product.changed', payload=...);
  COMMIT;

Worker (or CDC):
  Read outbox row;
  PUT to Elasticsearch index;
  Mark outbox row processed.
```

Search results lag by < 1s in normal operation; can lag more under load. Acceptable for most catalogs.

### Pattern: Postgres → Redis (cache invalidation)

Options:
1. **TTL only**: accept 60s staleness
2. **Write path invalidation**: `cache.delete(key)` after DB commit
3. **CDC**: subscribe to changes; invalidate accordingly

```
On write:
  UPDATE products SET price=$new WHERE id=$id;
  redis.del(`product:${id}`);
```

For multi-instance L1 caches: pub/sub-based invalidation.

### Pattern: Postgres → ClickHouse (analytics)

- CDC stream (Debezium) → Kafka → ClickHouse Kafka engine
- Lag: 1-10s
- Read model is denormalized, columnar, optimized for aggregation

### Pattern: Outbox + Kafka

```
Producer (your service):
  BEGIN;
  business writes;
  INSERT INTO outbox (topic, payload);
  COMMIT;

Debezium reads `outbox` via WAL, publishes to Kafka.

Consumers (other services):
  Subscribe to Kafka topics;
  React idempotently.
```

Variants:
- **Polling outbox** worker (no CDC): simpler, slightly slower
- **Transactional outbox + manual marker**: worker marks rows processed

---

## 6. Idempotent consumers

Any cross-store sync must be **idempotent**:

```python
def handle_order_placed(event):
    # Check if already processed
    if redis.set(f"processed:order.placed:{event.id}", "1", NX=True, EX=86400):
        # First time; process
        search_index.put(event.payload)
    else:
        # Already processed; skip
        return
```

Or:
- Conditional `INSERT ... ON CONFLICT DO NOTHING`
- Version-checked updates
- Sequence numbers per stream (skip out-of-order)

At-least-once delivery + idempotency = effectively-once semantics. Don't chase exactly-once at the transport layer.

---

## 7. Schema evolution across stores

Adding a field:
1. Add column in canonical store (additive migration)
2. CDC propagates the new field
3. Consumers handle both old + new shapes (forward compatibility)
4. Once all writers emit new shape, consumers can drop old handling

Renaming or breaking changes:
- Phase: dual-write old + new fields
- Phase: update all consumers
- Phase: stop writing old field
- Phase: drop old field

**Never break consumers in lockstep with producers in production.**

### Cross-store schema evolution timeline

```
V1 (everyone agrees on shape A)

   Producer ──── Kafka ──── Consumer1, Consumer2, Consumer3
   writes A                  read A

V1.1 (additive: producer adds optional field B)

   Producer ──── Kafka ──── Consumer1 (ignores B)
   writes A,B?               Consumer2 (ignores B)
                             Consumer3 (ignores B)

V1.2 (consumers upgrade one at a time, still backward compatible)

   Producer ──── Kafka ──── Consumer1 (reads B)
   writes A,B                Consumer2 (ignores B)
                             Consumer3 (reads B)

V2 (breaking: producer wants to remove A)

   PHASE 1: dual-write A and new_A
   PHASE 2: migrate every consumer to read new_A
   PHASE 3: stop writing A
   PHASE 4: drop A from schema
```

There is no shortcut. Skipping phases breaks consumers.

### Schema registry — the keystone

A **schema registry** (Confluent, Apicurio, AWS Glue) enforces compatibility before a producer can publish a breaking change. Producers register V2; the registry checks "is V2 backward-compatible with V1 consumers?" and either accepts or rejects. This converts "we'll be careful in PR review" into "the system refuses to deploy if it would break consumers."

---

## 8. Sagas (cross-service transactions)

When a business operation spans multiple services with their own DBs, ACID across them is impractical (no shared transaction context). Use a saga.

### Choreography (event-driven)
```
Service A: places order; emits "OrderPlaced"
Service B: charges payment on OrderPlaced; emits "PaymentSucceeded" or "PaymentFailed"
Service A: on PaymentFailed → cancels order
```

### Orchestration (central coordinator)
```
Orchestrator state machine:
  1. Reserve inventory (call Inventory service)
  2. Charge payment (call Payment service)
  3. Confirm order (call Order service)
  On failure at step N → run compensations in reverse
```

Tools: **Temporal**, **Camunda**, **AWS Step Functions**, **Cadence**.

### Saga visualized (orchestration with compensation)

```
       +-----------+
       | Step 1    |    Reserve inventory
       +-----------+
             | ok
             v
       +-----------+
       | Step 2    |    Charge payment
       +-----------+
             | FAIL
             |
   compensate v
       +-----------+
       | C1        |    Release inventory  <- undo Step 1
       +-----------+

Orchestrator must persist saga state (in DB or workflow engine)
so a restart resumes from the right step.
```

The hidden cost: **compensations are not "rollback"**. A real rollback undoes work atomically. A compensation is another forward transaction that *cancels out the business effect*. If you released the inventory but a notification email already went out, the email exists forever. Sagas trade ACID for availability — that trade has visible scars.

### Pros
- No 2PC; each service owns its DB
- Resilient (steps can retry)

### Cons
- Intermediate states visible
- Compensations are app-level logic (not DB rollback)
- Hard to reason about (state machine + many failure paths)

---

## 9. Change Data Capture (CDC)

Read the DB's write-ahead log to capture every change, publish as event stream.

- **Postgres**: logical decoding → wal2json / pgoutput → Debezium → Kafka
- **MySQL**: binlog → Debezium → Kafka
- **MongoDB**: oplog → MongoDB connector → Kafka
- **DynamoDB**: Streams → Lambda or Kinesis

### Why CDC over app-level events
- Captures every change, even those by ad-hoc scripts or other apps
- No code changes; opt-in retroactively
- No "we forgot to publish an event" bugs
- Replayable from a position

### Caveats
- Schema changes require coordination
- Initial snapshot for new pipelines (huge load)
- Connector failures need monitoring
- Consumer ordering guarantees per-key (within a partition)

---

## 9b. Dimensional modeling for analytics warehouses

The OLTP world models entities; the OLAP world models **measurements**. Dimensional modeling is the canonical OLAP technique (originated by Kimball).

### The four steps of a Kimball model

1. **Pick the business process** — e.g., "sales", "page views", "support tickets".
2. **Declare the grain** — what does one row in the fact table represent? "One sale-line of one product to one customer in one transaction." Grain must be the lowest level of detail you'll ever need to roll up from.
3. **Identify the dimensions** — who, what, where, when, why? (`dim_customer`, `dim_product`, `dim_store`, `dim_date`, `dim_promo`).
4. **Identify the facts** — the numeric measures (units_sold, revenue_cents, discount_cents). Additive facts (you can SUM them) are gold.

### Fact table types

- **Transaction fact** — one row per business event. Most common. (`fact_sales`)
- **Periodic snapshot fact** — one row per entity per time period. (`fact_inventory_daily`)
- **Accumulating snapshot fact** — one row per entity, updated as it moves through a pipeline. (`fact_order` with columns `placed_at`, `paid_at`, `shipped_at`, `delivered_at`).

### Bi-temporal in OLAP

Combining SCD Type 2 with bi-temporal modeling lets a warehouse answer questions like "what did the dashboard say about Q1 revenue on April 15 vs today?" — essential for regulated reporting and for debugging dashboards after-the-fact.

### Why this pattern wins for analytics

- Wide, infrequent reads dominate; storage is cheap; star schemas optimize the scan side.
- Business users (analysts) can write SQL against a clear `fact + dim` model without understanding microservices boundaries.
- BI tools (Tableau, Looker, Metabase) assume this shape natively.

---

## 10. Patterns by problem

### Problem: "Search results lag too far behind catalog updates"
- Reduce CDC lag (more consumers, smaller batches)
- Push critical updates synchronously (write-through to ES)
- Move from polling outbox to CDC

### Problem: "Some cache reads return stale data after writes"
- Add explicit invalidation on write path
- Short TTL + CDC-based invalidation
- Read-after-write: serve from primary for N seconds

### Problem: "Analytics doesn't match OLTP totals"
- Ensure CDC captures every change, including deletes
- Check for ordering issues; re-snapshot
- Reconcile periodically (run a check job)

### Problem: "User saw their write disappear after refresh"
- Read-your-writes violation (replica lag)
- Route reads to primary briefly after write
- Or use causal consistency tokens

### Problem: "Cross-service order failed midway"
- Implement saga compensation
- Make each step idempotent
- Persist saga state for resumability

---

## Common interview questions

1. What is the outbox pattern?
2. What is CDC? When to use it?
3. Event sourcing vs CRUD — trade-offs.
4. Saga: choreography vs orchestration.
5. How do you keep cache consistent with DB?
6. How do you handle the dual-write problem?
7. CQRS — when and why?
8. How do you sync Postgres to Elasticsearch?
9. Idempotent consumers — how?
10. Schema evolution across services.

---

## Detailed answers

### 1. Outbox pattern
Write the "intent to publish" to a DB table inside the same transaction as the business change. A worker reads the outbox and publishes externally. Solves the dual-write atomically.

### 2. CDC
Capture DB changes via WAL/oplog → emit as events. Use for: replication to other stores, analytics pipelines, cache invalidation, audit. Tools: Debezium, Maxwell, Mongo change streams.

### 3. Event sourcing
Store events, derive state. Pro: full audit, time travel, multiple projections. Con: complexity, snapshotting, harder queries. Use for high-audit domains; otherwise CRUD + outbox is simpler.

### 4. Saga
Cross-service transaction modeled as a sequence of local transactions with compensations. Choreography (services react to events) = decentralized; Orchestration (coordinator drives steps) = centralized. Use orchestration for complex flows.

### 5. Cache consistency
- TTL = best-effort
- Explicit `cache.delete` on write
- CDC-based invalidation = strongest with low lag
Read `caching/01-caching-strategies.md` for details.

### 6. Dual-write
The problem of atomic writes across two unrelated systems. Solutions: retry queue (weak), outbox (strong), CDC (strongest), event sourcing.

### 7. CQRS
Separate read and write models. Use when read patterns differ wildly from write model, or when you need many projections from one source. Pairs naturally with event sourcing.

### 8. Postgres → ES
Outbox + Debezium → Kafka → ES indexer. Lag <1s in normal operation. Re-index from canonical on bugs or schema changes.

### 9. Idempotent consumer
- Track processed event IDs (Redis SET with TTL, or DB unique index on event_id)
- Conditional INSERT ON CONFLICT DO NOTHING
- Version checks
- Sequence-aware skipping

### 10. Schema evolution
Phase changes: add nullable / dual-write / update consumers / make required / drop old. Coordinate via versioned events. Never break consumers and producers in the same release.

---

## Common mistakes

- Naive multi-store writes (no outbox)
- Trying to make eventual consistency feel like ACID (fight the tool)
- Skipping idempotency (duplicates everywhere)
- One huge "service" that owns multiple data stores directly (no SoT)
- Event payload bloats over time (versioning never planned)
- Outbox worker single-threaded → backlog grows
- Schema changes break consumers in lockstep with producers

---

## Senior engineer discussion points

- **Schema registry** (Confluent) for evolving event types safely
- **Avro / Protobuf** for compact, versioned event payloads
- **Snapshotting** in event sourcing to bound replay time
- **Saga state in a DB** (Temporal/Cadence handles this for you)
- **Cost of CDC pipelines** — Kafka cluster, Debezium ops, schema registry
- **PostgreSQL logical replication** as a poor man's CDC (per-table subscription)
- **The "data mesh" concept** — domain teams own their data products, expose via well-defined contracts
- **Strong consistency boundaries**: keep within one DB; cross-DB = embrace eventual

---

## Whiteboard storytelling — data modeling answers

A clean order to speak in for any cross-store modeling question:

1. "What's the canonical source of truth for this entity?" (one store owns writes.)
2. "What other stores need a projection of it, and why?"
3. "What's the acceptable lag between them?"
4. "How do I get changes from the canonical store to the derived stores?" (outbox, CDC, batch ETL.)
5. "How do consumers handle duplicates and out-of-order events?" (idempotency, version checks.)
6. "How does the schema evolve when one team needs to change a field?" (additive, dual-write, deprecate.)
7. "How do I reconcile if the pipeline ever breaks?" (re-snapshot, diff job.)

If you answer all seven without prompting, you've passed the senior bar.

## Putting it all together — the senior mental loop

Whenever you face a data-modeling question, run this loop:

```
   +----------------------------------+
   | 1. Identify the bounded context  |
   |    (which service owns this?)    |
   +-----------------+----------------+
                     v
   +----------------------------------+
   | 2. Pick canonical store          |
   |    (Postgres? Dynamo? Events?)   |
   +-----------------+----------------+
                     v
   +----------------------------------+
   | 3. Enumerate derived projections |
   |    (search, cache, analytics)    |
   +-----------------+----------------+
                     v
   +----------------------------------+
   | 4. Pick a sync mechanism         |
   |    (outbox / CDC / batch / saga) |
   +-----------------+----------------+
                     v
   +----------------------------------+
   | 5. Make consumers idempotent     |
   |    (dedup key, version check)    |
   +-----------------+----------------+
                     v
   +----------------------------------+
   | 6. Plan schema evolution         |
   |    (additive, dual-write phases) |
   +-----------------+----------------+
                     v
   +----------------------------------+
   | 7. Plan reconciliation           |
   |    (periodic diff, replay path)  |
   +----------------------------------+
```

Every senior system design answer is some traversal of this loop. Practice it until it feels automatic.

## Revision notes

- Dual-write problem: two systems can't be atomically updated
- Outbox = DB write + event-intent in one transaction; worker publishes
- CDC = subscribe to WAL; emit changes as events; Debezium is canonical
- Event sourcing: store events, derive state, audit-friendly
- CQRS: separate read/write models; pairs with event sourcing
- Sagas for cross-service transactions; choreography or orchestration
- Idempotent consumers always — at-least-once delivery is the world
- Schema evolution: additive, dual-write, deprecate, drop
- Polyglot persistence costs ops complexity; earn it
- Eventual consistency in seconds is fine; in money it isn't
- Data model = the language app + storage agree to speak across stores
- OLTP models the present of one entity; OLAP models the history of many
- Star schema = fact + dimensions; snowflake = normalized dimensions
- SCD Type 2 = new row per dimension change with valid_from/valid_to
- Bi-temporal = valid_time + transaction_time; needed for retroactive corrections
- Snapshots in event sourcing are a cache, not source of truth
- Schema registry converts careful PR review into hard compile-time guarantees
- Sagas trade ACID for availability; compensations are forward transactions, not rollbacks
- Senior loop: bounded context -> canonical store -> projections -> sync -> idempotency -> evolution -> reconciliation
