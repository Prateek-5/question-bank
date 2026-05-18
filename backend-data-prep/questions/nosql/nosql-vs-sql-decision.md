# NoSQL vs SQL — Choosing the Right Database for the Workload

## Source / Origin
- Standard senior architecture interview question.
- Companion concept docs: `backend-data-prep/sql/01-acid-properties.md`, `backend-data-prep/nosql/01-cap-theorem.md`.
- Common prompts: "We're building Twitter — Mongo or Postgres?", "When would you NOT pick Postgres?", "Why pick DynamoDB over RDS?"

## Why this question matters in interviews
This is where a senior shows whether they have **decision frameworks** or just **brand preferences**. Junior candidates pick the database they've used. Mid-level candidates list features. Seniors say: "Show me your access patterns, your scale, your consistency requirements, and your team's operational maturity — then I'll tell you." The interviewer wants to see that you (a) refuse to pick blindly, (b) ask the right questions, (c) explain the tradeoffs in terms of access patterns, not features, and (d) push back on the wrong-tool-for-the-job when warranted.

The dirty secret: **Postgres is the right answer 80% of the time.** The senior signal is knowing the 20% when it isn't.

## Concepts involved

### The decision dimensions (memorize these)

| Dimension | SQL favors | NoSQL favors |
|-----------|-----------|--------------|
| **Access patterns** | Ad-hoc joins, OLAP, BI queries | Known queries, single-entity lookups |
| **Schema** | Stable, normalized, evolving slowly | Schemaless, polymorphic, per-tenant variation |
| **Consistency** | Multi-row transactions, FK enforcement | Single-key, last-write-wins acceptable |
| **Scale** | Up to ~10TB single instance | TB-PB horizontal scale |
| **Throughput** | < 50K QPS without read replicas | > 100K QPS expected |
| **Latency p99** | 5-50ms typical | < 10ms required at high QPS |
| **Joins** | First-class | Manual / denormalize / app-side |
| **Operational maturity** | Mature tooling, ops know-how | Specialized expertise needed |

### Per-database "when to use it"

- **PostgreSQL** — default OLTP, complex queries, JSONB for hybrid workloads, GIS (PostGIS), strong invariants. Handles up to ~10TB and 50K QPS gracefully.
- **MySQL** — similar to Postgres; weaker SQL semantics but well understood; pick if your team already runs it.
- **MongoDB** — document model, schema flexibility, single-collection queries, change streams, multi-tenant per-document shape. Handles ~1TB-10TB per shard.
- **DynamoDB** — predictable single-digit-ms at any scale, fully managed, key-value + GSI access patterns. Cost-effective at high throughput; expensive at low throughput.
- **Cassandra** — time-series, write-heavy, multi-DC active-active, eventual consistency acceptable. PB scale.
- **Redis** — in-memory; cache or fast ephemeral state; queues, leaderboards, rate limits.
- **Elasticsearch** — full-text search, analytics aggregations, log search. Not a primary store.
- **ClickHouse / BigQuery** — OLAP / columnar, multi-billion-row scans, dashboards.
- **Neo4j** — graph queries (recommendations, fraud, social networks).
- **Kafka** — append-only log of events; source of truth for event-sourced systems.

### Edge cases / interview traps
1. **"Mongo is faster than Postgres."** Not at the same access pattern. Mongo wins on schema flexibility and shard-key-aligned queries; Postgres wins on joins and indexes that span columns.
2. **"NoSQL doesn't have transactions."** False. Mongo has multi-document ACID since 4.0. DynamoDB has TransactGetItems/TransactWriteItems (up to 100 items, single region). Cassandra has LWT (Paxos, per-partition only).
3. **"SQL doesn't scale."** Postgres handles tens of TB and tens of thousands of QPS on commodity hardware. Citus, Vitess, AlloyDB extend horizontally. Most "scale" stories aren't.
4. **"Schema is rigid in SQL."** JSONB columns in Postgres give you most of Mongo's flexibility without losing transactions and joins.
5. **"Pick the new shiny thing."** Operational cost of an unfamiliar DB usually dwarfs the technical benefit. Choose the boring one unless the new one solves a real problem.
6. **"Microservices = one DB per service."** True in principle, false in practice — many teams share Postgres clusters across services using schemas/namespacing. Cost vs purity tradeoff.
7. **"NoSQL is cheaper."** DynamoDB is cheap at 100K QPS, very expensive at 100M QPS without careful capacity planning. Self-hosted Cassandra is operationally heavy.

## Mental Model

### The decision tree

```
                  Start: What's the workload?
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   OLTP single-key   OLTP multi-row    OLAP / BI
        │                 │                 │
        ▼                 ▼                 ▼
  Hot read path?    Need FK / joins?    ClickHouse / 
        │                 │              BigQuery / 
        ▼              YES│NO            Snowflake
  DynamoDB / Mongo        │ │
  / Cassandra            ▼ ▼
                    Postgres  Mongo / Dynamo
                    /MySQL    (single-collection)

  Special-purpose:
    Full-text       → Elasticsearch / Postgres tsvector
    Graph traversal → Neo4j
    Time series     → InfluxDB / TimescaleDB / Cassandra
    Event log       → Kafka + downstream materialized views
    Cache           → Redis / Memcached
    Geo             → PostGIS / Mongo geo / Redis geo
```

### The "questions I ask before recommending" list

```
1. What are your access patterns? List them in priority order.
2. What's your read:write ratio?
3. What's your QPS today, in 6 months, in 2 years?
4. What's your dataset size today, projected?
5. Do you need multi-row transactions? Across what entities?
6. What's your p99 latency budget?
7. Multi-region requirement? Active-active or active-passive?
8. What does your team operate today? What's their on-call experience?
9. What's your consistency tolerance? Can a read be 5s stale? 5ms?
10. Compliance / audit requirements? (Some NoSQL stores lack point-in-time recovery.)
```

## Why interviewers care
- **Real architecture decisions** at senior levels boil down to picking the right primary datastore. Wrong choice = 6-month migration project later.
- The question reveals whether you have **production experience** or just textbook knowledge. Junior answers list features; senior answers cite incidents.
- The follow-ups ("we picked Mongo and now we need joins, what now?") test resilience under bad-decision recovery scenarios.
- **Polyglot persistence** — sophisticated answers mix stores. "Postgres for the transactional core, Redis for the cache, Elasticsearch for search, Kafka for the event bus" — this combination is the senior signal.

## Common beginner confusion
- **"NoSQL = no SQL."** It's "Not Only SQL" — many NoSQL stores have SQL-like query languages (CQL, N1QL).
- **"Schemaless = no schema."** There's always a schema — it just lives in the application, which is often worse than letting the DB enforce it.
- **"Horizontal scale solves everything."** Most apps never need it. Vertical scale + read replicas + caching covers 95% of workloads.
- **"ACID vs BASE is a hard choice."** Mongo, Dynamo, and even Cassandra (per-partition) support transactions now. The boundaries have blurred.
- **"CAP theorem says you pick 2 of 3."** It says during a *network partition*, you pick C or A. Without partition, you have all three.

## Brute force approach
"Use Postgres for everything." Not bad! Covers 80% of cases. The 20% it fails: extreme write throughput (>100K QPS sustained), multi-region active-active, time-series at PB scale, full-text search at scale, graph traversals.

"Use Mongo for everything." Falls apart the moment you need a join between collections or a cross-document transaction at scale. Schema drift becomes a maintenance nightmare.

## Optimal approach

### A workable rubric

1. **Default to Postgres.** Unless a hard requirement breaks it.
2. **Add Redis as the cache** when latency budget < 5ms or DB QPS > 5K/s.
3. **Add Elasticsearch / Postgres `tsvector`** when full-text search is needed.
4. **Move to DynamoDB / Mongo / Cassandra** only when one of these is true:
   - Sustained > 100K QPS that won't fit a single Postgres + replicas.
   - Multi-region active-active with low RTO.
   - Time-series at TB+ scale.
   - Schema is genuinely polymorphic (multi-tenant SaaS with per-tenant fields).
   - Cost-per-QPS at your scale favors DynamoDB (do the math).
5. **Add Kafka** when more than 2 systems consume the same event.
6. **Add ClickHouse / BigQuery** when analytics queries on the OLTP DB are degrading OLTP performance.

### The "is this NoSQL-worthy?" test

If the access pattern is "**get all data for user U for screen S**" and is well-known at design time, NoSQL document modeling shines. If the access pattern is "**joining 4 tables filtered by 3 conditions for an ad-hoc dashboard**", SQL shines. If both, polyglot.

## Solution (decision walkthroughs)

### Case A: "We're building a chat app, 10M DAU, expected 100K messages/sec peak"

Access patterns:
- Get most recent 50 messages for chat C (write-heavy, time-ordered).
- Get user presence (write-heavy ephemeral).
- Search message history (rare).

Recommendation:
- **Cassandra** or **DynamoDB** for messages (write-heavy, time-series, partition by `chat_id`, sort by `(timestamp DESC)`).
- **Redis** for presence (ephemeral, in-memory).
- **Elasticsearch** for message search (asynchronously indexed from the primary store).
- **Postgres** for user accounts, settings (small, transactional).

### Case B: "We're building an e-commerce backend, 1M DAU, 1K orders/min"

Access patterns:
- Order placement is multi-step (inventory check, payment, fulfillment).
- Customer history, returns, refunds.
- Catalog search, product recommendations.

Recommendation:
- **Postgres** for orders, inventory, customer (FK enforcement, multi-row ACID). 1K orders/min is trivial.
- **Redis** for cart state (ephemeral, fast).
- **Elasticsearch** for product search.
- **Kafka** for event bus to downstream systems (analytics, recommendations).

### Case C: "We're building a social feed, 100M MAU, fan-out reads"

Access patterns:
- Get feed for user U (top N posts from followed users).
- Post creation (one author, fans out to N followers).
- Profile lookups.

Recommendation:
- **Cassandra** or **Mongo** for posts (write-heavy, per-user partition).
- **Redis sorted sets** for materialized feeds (fan-out-on-write pattern for non-celebrities).
- **Postgres** for users, follows, settings.

### Case D: "We're a B2B SaaS, 1000 tenants, ~10K users each"

Access patterns:
- All queries scoped by tenant.
- Schema varies per tenant (custom fields).
- Strong consistency for billing.

Recommendation:
- **Postgres** with `tenant_id` on every table OR schema-per-tenant. JSONB column for custom fields.
- **Redis** cache.
- Don't reach for Mongo unless custom fields are truly explosive in variety.

## Step-by-step dry run

A real conversation a senior would have:

```
PM: We need to store user activity events. 10K events/sec. Pick a DB.

Senior:
  Q: Are these events queried online or only batched?
  PM: Mostly batched. Some online for "show user's last action."

  Q: How long do we keep them?
  PM: 90 days hot, archive forever.

  Q: Read patterns?
  PM: Get all events for user X in last 7 days; aggregate per-event-type counts.

  Decision:
  - Primary store: Cassandra. Partition by user_id, clustering by timestamp DESC.
    Hot 90 days fits in main keyspace; older rotated to S3 via TTL.
  - Aggregations: materialized via Kafka → ClickHouse for dashboards.
  - Reasons: write-heavy, known partition key, time-ordered reads, scales horizontally.

  Why not Postgres? 10K writes/sec sustained is ~860M rows/day. Indexes blow up.
  Could work with TimescaleDB + aggressive partitioning, but Cassandra is purpose-built.

  Why not DynamoDB? Cost. At 10K writes/sec sustained DynamoDB is ~$30K/month
  before you factor in storage; self-hosted Cassandra is one-tenth that. The team
  has on-call experience with Cassandra. If they didn't, I'd flip to DynamoDB.
```

The senior signal: cost analysis, on-call awareness, naming the second-best option, explaining why the rejected ones were rejected.

## How to think aloud in the interview

> "Before I pick, let me ask about the access patterns. What are the top 3-5 queries we need to support, what's the read:write ratio, and what's the scale today and projected?
>
> Default for me is Postgres. It handles up to ~50K QPS and ~10TB on commodity hardware, supports joins and transactions, has the best tooling, and most teams already know how to operate it. I only move off Postgres for specific reasons.
>
> Those reasons are: sustained throughput beyond what a Postgres cluster handles, multi-region active-active, write-heavy time series at TB-PB scale, or schema that's genuinely polymorphic across tenants.
>
> For each of those I'd reach for a different store. Multi-region active-active with low RTO → Cassandra. Predictable single-digit-ms latency at any scale → DynamoDB. Document model with schema flexibility → MongoDB. Time-series → Timescale or Cassandra. Full-text search → Elasticsearch. Graph traversals → Neo4j.
>
> Most production systems aren't one DB — they're polyglot. Postgres as the transactional core, Redis for cache, Elasticsearch for search, Kafka as the event bus. The art is knowing where each one fits without over-engineering. I'd push back on starting with three stores when one would do."

## Important takeaways

- **Default to Postgres.** Move off only with specific evidence.
- **Access patterns first**, not features.
- **Polyglot persistence** is the senior model — different stores for different access patterns.
- **JSONB in Postgres** covers most "we need schema flexibility" cases.
- **Operational cost** of unfamiliar DBs usually dwarfs technical benefit.
- **Mongo / Dynamo / Cassandra** all have transactions now — old "ACID vs BASE" framing is outdated.
- **Always estimate** QPS, dataset size, latency budget, dollar cost — don't pick blind.

## Variants

1. **"Which DB for a queue?"** — Kafka if event log is the source of truth, RabbitMQ for task queues, Redis Streams for lightweight. Don't use Postgres unless throughput is low.
2. **"Which DB for sessions?"** — Redis (TTL, fast). Postgres if you need querying or audit trail.
3. **"Microservices DB per service vs shared?"** — Per service is the textbook answer; shared with schema isolation is the pragmatic answer for small teams.
4. **"When do we migrate to NoSQL?"** — When the current store is the bottleneck for a specific query class that NoSQL is structurally better at. Not before.
5. **"Postgres or MySQL?"** — Postgres for richer SQL, better JSON, better extensibility. MySQL if team operates it.
6. **"DynamoDB vs Mongo for a startup?"** — DynamoDB for serverless / variable load. Mongo for document model + change streams + self-hosted control.

## Revision notes

> **NoSQL vs SQL — 60 second recap**
> - **Default to Postgres.** 80% of workloads fit.
> - **Move off** only for: >100K QPS sustained, multi-region active-active, TB-PB time series, truly polymorphic schema.
> - **Polyglot is the production reality**: Postgres + Redis + Elasticsearch + Kafka.
> - **Access patterns drive the choice**, not features.
> - **Mongo / Dynamo / Cassandra** all support transactions now — old framing outdated.
> - **JSONB** covers most "schema flexibility" needs without leaving SQL.
> - **Operational cost** matters as much as technical fit.
> - **Trap:** picking by brand, not by access pattern; under-counting team familiarity cost.
