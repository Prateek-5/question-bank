# Cross-Store Data Modeling, CDC, Event Sourcing

When a single database stops fitting, the question becomes: **how do you model data across multiple stores while keeping them consistent?**

This file covers the patterns interviewers ask about in senior system design rounds.

---

## Why this matters in backend interviews

- Almost every "design X at scale" question forces a multi-store answer (Postgres + Redis + Elasticsearch + Kafka + ...)
- The hard part is **consistency between stores** — not the stores themselves
- Senior signal: knowing the outbox pattern, CDC, and event sourcing trade-offs

---

## 1. Polyglot persistence

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
