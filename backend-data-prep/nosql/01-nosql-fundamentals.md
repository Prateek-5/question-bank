# NoSQL Fundamentals

## Why this matters in backend interviews

- **Every system design round** at SDE2+ asks a "would you use NoSQL here?" question. The right answer requires you to know the trade-offs by heart.
- **Architectural decision-making** is a senior signal. Cargo-culting "we use Mongo because it scales" gets you rejected; understanding when Postgres would have been simpler gets you hired.
- **Debugging**: NoSQL system failures (replica lag, hot partitions, eventual consistency) come up often.
- **System design**: every read-heavy / global / unstructured-data problem (chat, feed, geolocation, sessions, IoT) involves NoSQL choices.

---

## Intuitive teaching layer — start here before the formalisms

Before any definitions, hold these pictures in your head. The rest of the page is just precise language for them.

- **SQL (relational)** is a **strict library card catalog**. Every book has the same set of fields on the same shape of card (title, author, ISBN, year). To find "all books by author X published after 2010" you don't search the shelves — you walk the catalog, which is sorted and validated. The librarian refuses to file a card that's missing required fields. That refusal is your `NOT NULL`. The cross-reference cards are your foreign keys. Joins exist because each entity is split across many tightly-validated cards.
- **Document store (Mongo, Firestore)** is a **bin of paper folders**. Each folder is one entity, and it can contain whatever you want — receipts, sub-receipts, notes stapled together. Two folders for "user" don't need the same shape. You retrieve a whole folder at once, which is fast — but cross-folder questions ("which users bought product X?") require either folding that info into the folder up front (denormalize) or scanning many folders.
- **Key-Value store (Redis, Memcached)** is a **bank of numbered lockers**. You give a key, you get whatever's inside the locker. The locker doesn't care if it's a coin, a JPG, or a list of numbers — that's your problem. Lookups are O(1) and feel instant. But you can't ask "which lockers contain red items?" without opening every one.
- **Wide-column / columnar (Cassandra, Bigtable, ClickHouse)** is **ledger paper read column-by-column instead of row-by-row**. If you only ever ask "what was the temperature at sensor 7 every hour today," you don't want to read whole rows containing 200 columns — you want to slide down one column. Storing data column-wise makes that ridiculously fast and compressible. Tradeoff: random single-record updates are painful.
- **Graph (Neo4j, Neptune)** is a **friendship map drawn on a whiteboard**. Each person is a circle, each relationship is a line. "Friends of friends of Alice within 3 hops who like sushi" is a literal walk along the lines. In SQL that's 3 self-joins and a query planner crying. In a graph DB it's a native traversal.
- **Search engine (Elasticsearch, OpenSearch)** is a **library's index card system at the back of the building** — built for fuzzy / partial / ranked text lookup, not for being the canonical store.
- **Time-series (InfluxDB, TimescaleDB)** is a **strip-chart recorder**: paper rolls forward, you mostly append at the head and query "the last N hours."

If you understand the analogy, you already know *why* each family exists and *what it's bad at*. The rest is vocabulary.

### Why does NoSQL exist at all (first principles)

A relational database was built for an era when:
1. Data was small enough to fit on one machine.
2. Schemas changed slowly (banking, ERP, payroll).
3. You wanted the database to *enforce* invariants because hardware was unreliable but networks were short.

The internet broke all three assumptions:
1. Data became petabytes — bigger than any single box.
2. Schemas evolved per-deploy (a SaaS app adding a new field every Tuesday).
3. Networks became long, lossy, and global — and the database had to keep working through that.

NoSQL is not "SQL minus features." It's **a family of databases that picked a different combination of {scale, flexibility, latency, availability}** and accepted the costs that fall out (no joins, weaker consistency, model-your-queries-first). Knowing which combination they picked is the entire skill.

### Progressive build — read these in order

1. **Simplest mental model:** a NoSQL DB is a fast hashmap that lives on many machines.
2. **Add:** the hashmap is *partitioned* — the key decides which machine owns the value.
3. **Add:** each value is *replicated* to a few other machines so a single node loss doesn't lose data.
4. **Add:** reads and writes can hit any replica; the system decides how strict to be about freshness (this is the consistency knob).
5. **Add:** values can be richer than a single string — JSON documents, sorted columns, graph edges.
6. **Add:** because there are no joins, you must shape the data for the queries you'll run (denormalization).

If you can recite that ladder, you can talk about *any* NoSQL system fluently.

---

## Core concepts

### What "NoSQL" actually means

Originally "Not Only SQL." A loose category covering databases that:
- Don't fit the relational model (or fit it loosely)
- Often relax ACID for scale (BASE: Basically Available, Soft state, Eventually consistent)
- Are designed around specific access patterns rather than ad-hoc queries
- Typically horizontally scalable (sharded by default)

But: many modern SQL databases (CockroachDB, Spanner, YugabyteDB) scale horizontally with ACID. And many NoSQL stores (MongoDB, DynamoDB) now have transactions. The line is blurred.

### Why interviewers care about this topic

Interviewers don't actually care if you can recite "NoSQL = Not Only SQL." They use this topic as a probe for three senior-engineer signals:

1. **Schema judgment.** Can you tell when data is naturally relational vs naturally a document vs naturally a stream? Juniors pick whatever the latest blog post praised. Seniors look at the access pattern and the invariants.
2. **Data-model fit.** Given a workload, can you map it to the *right family* and explain the tradeoff in one sentence? "Chat → wide-column because the access pattern is `(conversation_id, time-range)` and writes are append-only" is the kind of answer that moves an interview from a SDE2 to a SDE3 signal.
3. **Tradeoff fluency.** Every NoSQL choice gives something up. If you describe Dynamo without mentioning hot partitions, or Mongo without mentioning index discipline, you sound like you read the marketing page. Real engineers know the *failure modes*.

A weak candidate names systems. A strong candidate names *which property of the system* matches *which property of the workload*.

### ASCII taxonomy — the family tree

```
                            NoSQL family tree
                                   |
   +---------------+---------------+---------------+----------------+--------------+
   |               |               |               |                |              |
Key-Value      Document       Wide-column        Graph         Time-series      Search
(locker)       (folder bin)   (ledger paper)   (friend map)   (strip-chart)   (back-index)
   |               |               |               |                |              |
Redis          MongoDB        Cassandra         Neo4j         InfluxDB         Elasticsearch
Memcached      Couchbase      HBase             Neptune       TimescaleDB      OpenSearch
DynamoDB(KV)   Firestore      ScyllaDB          Dgraph        QuestDB          Solr
etcd           DynamoDB(doc)  Bigtable          JanusGraph    Prometheus       Vespa
                              ClickHouse(OLAP)
                                   |
                              (column-store
                              cousin: OLAP)

   Access pattern shorthand:
     Key-Value     -> get(k), set(k,v)               -> "I know the exact key"
     Document      -> findByFilter({...})            -> "I want the whole entity"
     Wide-column   -> range(partition, sort_range)   -> "I want a slice of a partition"
     Graph         -> traverse(node, depth, filter)  -> "I want a walk over edges"
     Time-series   -> range(metric, time_range)      -> "I want a window of time"
     Search        -> match(text, score, filter)     -> "I want ranked text matches"
```

### The four families

#### 1. Key-Value (KV)
- Just `key → value` (value can be anything)
- O(1) lookup, no secondary indexes (usually), no queries
- Examples: **Redis**, **Memcached**, **DynamoDB (single-PK)**, **etcd**
- Use cases: cache, session store, leaderboards, feature flags

##### Mental model — Key-Value
A wall of numbered lockers. You either know the locker number (key) or you don't — there's no librarian to help you find lockers "with red things inside." Because the lookup is just "go to locker N," it's the fastest family by far (microseconds). The price you pay: zero ability to ask anything other than "give me what's at K." This is why KV stores end up almost always being **caches, sessions, or coordination state** — situations where the application already knows the key (user id, session id, flag name).

Beginner pitfall: people see "Redis has lists and sorted sets" and think it's a general DB. It isn't. Those structures live *inside one key*. Cross-key queries still don't exist.

#### 2. Document
- Stores nested JSON/BSON documents per key
- Secondary indexes, ad-hoc queries
- Examples: **MongoDB**, **Couchbase**, **Firestore**, **DynamoDB (in document mode)**
- Use cases: catalogs, user profiles, content management, semi-structured data

##### Mental model — Document
A bin of paper folders. Each folder represents one entity (one user, one product, one article). Inside a folder you can staple receipts, sub-receipts, annotations — i.e. nested arrays and objects. You retrieve the *whole folder* in one operation, which means a single fetch can return everything you need to render a screen.

The reason document stores are popular for product catalogs, user profiles, and CMS content is that those entities are **naturally tree-shaped** — a product has many variants, each variant has many images, each image has many tags. In SQL that's 4 tables and 3 joins. In Mongo, it's one document.

The catch: when an *embedded* thing also needs to live independently (e.g. an order line that needs to be queried by product), you've now denormalized and you must keep multiple copies in sync. This is where Mongo beginners run aground.

#### 3. Wide-column (column family)
- Rows are keyed; each row has a flexible set of columns grouped into families
- Optimized for huge scale, append-heavy, time-series-like patterns
- Examples: **Cassandra**, **HBase**, **ScyllaDB**, **Bigtable**
- Use cases: time-series, IoT, message storage, ad tech

##### Mental model — Wide-column
Imagine a giant accountant's ledger that's so wide that *most rows leave most columns blank*. Storing it row-by-row would waste massive space. Instead, the DB stores **each column as its own file**, sorted within partitions.

Two consequences fall out for free:
- Reading "the temperature for sensor 7 from 2pm to 4pm" reads a tight contiguous slice of one column — incredibly cheap, incredibly compressible.
- The data is **partitioned by a chosen partition key** and **sorted by a clustering key**. Cassandra/Dynamo people call this "modeling for the access pattern" — you literally pick partition + sort columns to match the query you'll run a million times a day.

That's also why wide-column hates ad-hoc queries: any access pattern *not* on the partition+sort key requires a scan or a second materialized table.

#### 4. Graph
- Nodes + edges as first-class citizens
- Optimized for traversals (`MATCH (u)-[:FRIEND*1..3]->(f)`)
- Examples: **Neo4j**, **JanusGraph**, **Amazon Neptune**, **Dgraph**
- Use cases: social networks, fraud detection, recommendations, knowledge graphs

##### Mental model — Graph
A whiteboard with circles and arrows. Each circle is a node (a person, a company, a transaction). Each arrow is an edge (`:FRIEND_OF`, `:OWNS`, `:PAID_TO`). When the question is "starting from this circle, walk N hops along arrows matching some condition," the graph DB *physically* walks those edges — no joins.

The differentiator vs SQL is **the cost of multi-hop traversal**. In Postgres, 4-hop friend-of-friend on a 100M-edge graph is multiple self-joins on a junction table and an explosion of intermediate rows. In a graph DB, traversal is pointer-chasing — each hop is O(degree).

When NOT to choose graph: if you only have one or two hops (just store edges in a SQL junction table). Graph DBs earn their cost at 3+ hops, recursive shortest-path queries, and pattern matching like fraud rings.

##### Beyond the four — when to reach for specialized stores
- **Time-series** (InfluxDB, TimescaleDB, Prometheus): metric data with a timestamp and a few tags. Append-only, range-by-time queries. A wide-column DB *can* do this; a time-series DB does it with better compression and built-in retention/downsampling.
- **Search** (Elasticsearch, OpenSearch, Vespa): inverted index for full-text + relevance scoring. **Not a source of truth.** Used alongside a primary DB.
- **OLAP / columnar analytics** (ClickHouse, BigQuery, Snowflake, DuckDB): scan billions of rows for aggregations. Inserts are bulk; queries are huge scans with predicate pushdown.

These are all "NoSQL adjacent" — the same instinct (model for a specific access pattern) applied to specialized workloads.

(Other useful but specialized stores: **Elasticsearch** for search; **ClickHouse** for OLAP; **InfluxDB / TimescaleDB** for time-series; **Redis Streams / Kafka** for log/event.)

### How NoSQL achieves scale

1. **Horizontal partitioning (sharding)** — data split across many nodes by a partition key
2. **Replication** — each piece of data lives on multiple nodes (quorum reads/writes)
3. **No cross-shard joins** — queries usually target one shard
4. **Eventual consistency** as the default trade-off for availability
5. **Denormalization** — data shaped for read patterns, not write patterns

### When to choose NoSQL

✅ **Choose NoSQL when:**
- Access pattern is fixed and well-known (you can model around it)
- You need single-digit-ms latency at huge scale (Dynamo, Cassandra)
- Data is naturally hierarchical/nested (MongoDB, Firestore)
- You need geo-distributed multi-region writes
- You need a flexible, schemaless extension (often: just use JSONB in Postgres instead)
- Workload is write-heavy time-series / append-only (Cassandra, ScyllaDB)
- You need graph traversals at scale (Neo4j)

❌ **Don't choose NoSQL when:**
- You need ad-hoc analytical queries (use a SQL warehouse)
- Strong ACID across multiple entities is required (use a real RDBMS)
- Your data is highly relational (joins everywhere) — Postgres is faster and simpler
- You're picking it because "Mongo scales" without understanding why
- The schema isn't actually unknown — you just haven't designed it yet
- You can fit in one Postgres instance (most workloads can)

> **Senior take:** Default to Postgres. Add Redis for cache. Add a search engine if needed. Reach for Dynamo/Cassandra only when you genuinely outgrow Postgres at the access-pattern level, not just at row count.

#### When NOT to choose NoSQL — the harder list

Knowing when *not* to use a tool is a stronger signal than knowing when to use it. Be ready to articulate these in interviews:

1. **You have invariants across multiple entities.** "An order cannot exceed the user's credit limit; reserve stock when the order is placed; debit the wallet only if both succeed." That's a multi-row ACID transaction. Postgres does it natively in a few lines. Mongo can do it, but it's heavier, and Cassandra/Dynamo essentially can't (you'd build sagas).
2. **The access patterns are still being discovered.** Early-stage products iterate weekly. SQL's ad-hoc query power is your best friend during that phase. Picking Dynamo before you know the access pattern is committing to the wrong shard key.
3. **You need analytics on the operational data.** "How many orders by region this week?" In Postgres: one `GROUP BY`. In Cassandra: forbidden without a pre-materialized table. NoSQL forces you to add an OLAP store *too*.
4. **Compliance / audit requirements.** Strong audit trails, immutable ledgers, regulatory consistency — SQL ecosystems have decades of tooling. NoSQL bolts this on awkwardly.
5. **Your data volume fits on one box.** A modern Postgres instance handles 50–100k QPS, terabytes of data, and JSONB nesting. If you're under that, you don't have a scale problem; you have a *desire to be cool* problem.
6. **Your team doesn't have ops capacity.** Running Cassandra is its own job. Mongo replica sets require monitoring. Self-hosted Redis cluster failovers need careful tuning. Postgres is boring. Boring is good when you're a 4-person team.
7. **You need cross-shard transactions.** This is where almost every "let's just use Dynamo" project hits the wall.

If a candidate can list *these* with conviction, the interviewer thinks: "this person has been burned, they know."

### Schema design philosophy

#### SQL: model your data, then query it
You design tables that reflect entities and relationships. Joins assemble the queries.

#### NoSQL: model your queries, then store the data
You list every query you'll ever run, then design tables/collections so each query is a single-key lookup. This is **denormalization on purpose**.

Example: In an e-commerce app, if you frequently load "user + their last 5 orders" together, a SQL design joins users and orders. A document design embeds the last 5 orders in the user document (and writes are duplicated when an order is placed).

#### Schema-on-write vs schema-on-read (the deeper distinction)

This is the term you'll be expected to know.

- **Schema-on-write** (SQL, classic RDBMS): the schema is enforced *when the data is inserted*. The DB refuses bad rows. The schema lives in the DB. Migrations are explicit (`ALTER TABLE`). Reads are cheap because the data shape is guaranteed.
- **Schema-on-read** (most NoSQL, data lakes, Mongo by default): the schema is enforced *when the application reads the data*. The DB accepts almost anything; your application code (or a validation layer) decides what's valid at read time. The schema *still exists* — it just lives in your code, your TypeScript types, your Pydantic models, your protobuf definitions, your Mongoose schema.

**The senior take:** "schemaless" is a marketing word. Every meaningful system has a schema. The choice is *where it's enforced* and *who pays the cost*:

| | Schema-on-write | Schema-on-read |
|---|---|---|
| Migrations | DB-level, costly, planned | App-level, gradual, per-document |
| Bad data | Rejected at write | Discovered at read, often in prod |
| Iteration speed | Slower (need migration) | Faster (add a field, ship) |
| Operational risk | "Migration locks the table" | "Old documents missing field X" |
| Best for | Stable invariants (money, identity) | Evolving products (SaaS features) |

A real-world example: a SaaS app that adds a new feature flag per customer every week is *miserable* in schema-on-write (200 migrations a year). The same app on Mongo just starts writing new fields. The cost: every read path must defensively handle missing fields. You pay the schema cost *somewhere*.

#### Why denormalization is rational (not lazy)

In SQL school we're taught normalization is virtuous (3NF, BCNF). In NoSQL, denormalization is the *default* and it's not because NoSQL is "primitive." It's because the math changed:

1. **Storage is cheap, network round-trips are not.** Copying a user's name into every order row costs micropennies in disk; saving one cross-shard join costs hundreds of ms in latency.
2. **Joins don't scale across machines.** A 5-way join on a sharded dataset means fan-out to N shards per table. Embedding the data avoids that entirely.
3. **Reads are 100–1000x more frequent than writes** in most consumer apps. Paying once at write time to make every read O(1) is a great trade.
4. **The data shape on disk = the screen shape in the app.** "Render user profile" → fetch one document. No assembly required.

The cost you accept:
- Duplicated data must be kept consistent (write to all copies, or accept staleness).
- If the embedded data changes shape, you must migrate many documents.
- Some queries become impossible — you can't ask a question the data wasn't shaped for.

Senior heuristic: **denormalize for the top-10 access patterns; keep a normalized canonical source if you need it for the long tail.**

### Consistency models

(Detailed in `02-cap-theorem.md`.)

- **Strong**: every read sees the latest committed write
- **Linearizable**: strong + real-time ordering
- **Sequential**: writes ordered consistently across all observers
- **Causal**: if A causally precedes B, every observer sees A first
- **Eventual**: replicas converge "soon"

### Partitioning strategies

- **Hash-based**: hash(key) → shard. Even distribution, but range queries fan out.
- **Range-based**: keys assigned to contiguous ranges. Good for range scans, but hot-spot risk if writes cluster at one end (monotonic IDs).
- **Directory-based**: a lookup service maps key → shard. Flexible, but the directory is a SPOF.
- **Composite**: hash on partition key + sort key for ordering within the partition (Dynamo, Cassandra).

### Replication strategies

- **Leader-follower (master-replica)**: writes go to leader, reads can go to followers (with lag). Mongo replica sets, Postgres streaming replication.
- **Multi-leader**: any node accepts writes; conflicts must be resolved (Cassandra "all leaders", CouchDB, multi-region).
- **Leaderless (Dynamo-style)**: clients send to any N nodes; quorum R + W > N for strong consistency.

### Common misconceptions

- "NoSQL = no schema" — every store has a schema; it just lives in your application code instead of the DB
- "NoSQL is faster" — sometimes; depends on the workload. Postgres can do 50k QPS on commodity hardware.
- "Mongo is schemaless so we don't have to think about indexes" — wrong; Mongo indexes are critical and easy to forget
- "Eventual consistency = data loss" — no, it's a propagation delay; writes are durable
- "Cassandra scales linearly" — it does, but it doesn't help if your data model is wrong; hot partitions kill performance regardless of node count

### Common beginner confusion — what people get wrong

These are the misunderstandings that derail real interviews. Each one has a corrected mental model.

1. **"NoSQL means no schema."**
   - Wrong. It means *schema-on-read* — the schema lives in your application code instead of the database. The DB will accept anything; your code is responsible for handling the variations. Every production NoSQL system ends up with explicit validation (Mongo `$jsonSchema`, Mongoose, Pydantic, TypeScript types, Avro). The schema is just relocated, not deleted.
2. **"MongoDB doesn't have transactions."**
   - Stale folklore. Mongo got multi-document ACID transactions on replica sets in 4.0 (2018) and on sharded clusters in 4.2. They exist, they're scoped, and they're more expensive than Postgres transactions (because they require coordination across replicas). The correct answer to the interview question is "yes, since 4.x, but I'd avoid them in hot paths and prefer designing the document boundary to contain the atomic unit."
3. **"NoSQL is always faster than SQL."**
   - Misleading. NoSQL is faster *for specific access patterns at huge scale*. For most workloads under 50k QPS, single-region Postgres is faster, more flexible, and cheaper because it doesn't need any of the distribution machinery. A single Postgres box with good indexes embarrasses a misconfigured Mongo cluster.
4. **"NoSQL means I don't need to plan my data model."**
   - The exact opposite. SQL is forgiving because joins let you ask new questions after the fact. NoSQL forces you to **commit to your access patterns up front**, because you literally shape the data for them. Wrong commitment = full re-shard = months of work.
5. **"Mongo is schemaless, so I don't need indexes."**
   - Catastrophic. Without indexes, Mongo does a full collection scan, which is fine for 10k docs and a nightmare at 10M. Every query path in production must have a matching index, exactly like Postgres.
6. **"Eventual consistency means I'll lose data."**
   - No. Durability is orthogonal to consistency. An eventually-consistent system *commits the write durably*; it just doesn't promise that all replicas reflect it instantly. You see stale reads briefly; you don't lose the write.
7. **"Redis is a database."**
   - Be careful. Redis *can* persist (RDB snapshots, AOF append-only files), but treating it as a system of record is risky — its persistence semantics aren't as tight as a real DB. It's primarily a cache, queue, or coordination store.
8. **"Cassandra is web-scale, so I should use it."**
   - Cassandra is web-scale *if your data model fits its rules*. If you bring SQL habits (joins, ad-hoc queries, secondary indexes everywhere), Cassandra is web-painful. Hot partitions and tombstone storms will eat your weekend.

### Learning bridges — connect this to what you already know

If you already understand X, NoSQL family Y is just X with one twist:

- **You know hashmaps** → Key-Value store is a hashmap that spans many machines. The partition key picks which machine owns the slot.
- **You know JSON / nested objects** → A document store is a hashmap where each value is a JSON object that you can index *into* (Mongo can index `address.city`). Just like indexing a Python dict deeply, but with B-tree indexes underneath.
- **You know Pandas DataFrames** → A wide-column store is a DataFrame partitioned by one column and sorted by another, stored column-by-column on disk. ClickHouse is basically "a distributed Pandas optimized for big aggregations."
- **You know recursive SQL CTEs / adjacency lists** → A graph DB is the same idea but the engine is built around `(node, [edges])` pointer-chasing instead of join tables.
- **You know SQL VIEWs / materialized views** → NoSQL denormalization is "the materialized view IS the table, because we have no source-of-truth to derive from."
- **You know `git`** → Conflict resolution in AP systems (Dynamo, Cassandra, Riak) is conceptually like git merge: concurrent edits on different replicas converge with a rule (LWW, vector clocks, CRDT).

### Interview traps

1. **"Why would you use Mongo over Postgres?"** — most answers are wrong. Good answer: "I usually wouldn't; I'd use Postgres with JSONB. I'd choose Mongo only if multi-region writes or a truly schemaless document model with millions of nested arrays is required."
2. **"What's the difference between Redis and Memcached?"** — Redis has data structures, persistence, replication, scripting, pub/sub, streams. Memcached is pure KV with simpler eviction.
3. **"What's a good partition key for X?"** — high cardinality, even distribution, matches access pattern. Bad: customer_id where one customer is 80% of traffic.
4. **"Can Mongo do transactions?"** — yes, since 4.0 (single replica set) and 4.2 (sharded). But they're more expensive than a Postgres transaction.

### Interview storytelling — workload → store, narrated out loud

Interviewers don't want a list; they want to hear you *reason*. Practice this template, then internalize it so you can apply it to any workload they throw at you.

**Template (say this out loud in the interview):**
> "Let me first figure out the *access pattern* and the *invariants*. Then I'll pick the store family, then the specific product, then call out the failure mode."

Now run it on a few canonical prompts:

**Prompt 1: "Design a URL shortener."**
> "Two access patterns: (a) `create(long_url) -> short_code`, (b) `lookup(short_code) -> long_url`. The lookup is the hot path — billions of times the create rate. The invariant is uniqueness of the short_code. This is **Key-Value at heart**. I'd pick Redis (or DynamoDB if multi-region) for the hot lookup, fronting a Postgres source-of-truth for the bookkeeping (analytics, abuse logs). Failure mode: a viral link becomes a hot key — solve with client-side caching and CDN."

**Prompt 2: "Design WhatsApp message storage."**
> "Access pattern: `messages_by_conversation(conv_id, time_range)`. Append-heavy. Need ordering by time. Need to scale across billions of conversations. This is the canonical **wide-column** workload — Cassandra or DynamoDB. Partition by `conv_id`, cluster by `sent_at DESC`. One conversation lives on a small set of nodes; the read is a sliced range. Failure mode: a 500-person group with constant typing is a hot partition — solve by sub-partitioning if it gets bad."

**Prompt 3: "Design an Instagram-style product catalog with filters."**
> "Access pattern: rich filtering — category, price range, attributes, brand. Two valid paths. (a) Postgres + GIN index on JSONB attrs — works to millions of products and ad-hoc filters are easy. (b) Document store (Mongo) if the schema varies dramatically per category (electronics vs apparel attributes differ). For real production scale I'd also add Elasticsearch alongside for full-text search and faceting. Failure mode: stale ES index after a price change — solve with CDC (Debezium) and accept a few seconds of search staleness."

**Prompt 4: "Design fraud detection for credit-card transactions."**
> "I need to ask 'is this card connected to a known fraud ring within N hops of relationship — shared device, shared IP, shared billing address?' That's a multi-hop traversal query. **Graph DB** (Neo4j) is the natural fit, fed by Kafka from the transaction stream. The transactional source-of-truth is still Postgres; the graph is a derived view. Failure mode: the graph grows unboundedly — solve with edge expiration / archival."

**Prompt 5: "Design a session store for a web app."**
> "Access pattern: `get(session_id)`, `set(session_id, blob, ttl)`, called on every authenticated request. Latency budget: single-digit ms. Durability requirement: low (losing some sessions on crash just means users re-login). **Key-Value, Redis**. Failure mode: Redis OOM if sessions accumulate — solve with TTL and `maxmemory-policy allkeys-lru`."

**The meta-pattern:** access pattern → invariants → family → product → failure mode. If you say all five out loud, you sound senior. If you skip "failure mode," you sound junior — because not naming the failure is the giveaway that you've never operated it.

---

## Real examples

### When to use what (production picks)

| Workload | Choice | Why |
|---|---|---|
| User accounts + orders + items + payments | **Postgres** | Relational, ACID, joins, mature |
| Hot session store | **Redis** | Sub-ms latency, TTL, simple data |
| Product catalog with rich filtering | **Postgres + Elasticsearch** | SQL for canonical, ES for search |
| Real-time analytics dashboard | **ClickHouse / BigQuery** | OLAP, columnar |
| Time-series IoT sensor data | **TimescaleDB / Cassandra / InfluxDB** | Time-range queries, compression |
| Multi-region chat messages | **DynamoDB / Cassandra** | Global tables, write availability |
| Social graph (friend-of-friend) | **Neo4j** | Traversal performance |
| User feed (timeline) | **Cassandra / Redis + Postgres** | Fan-out write, sorted reads |
| Rate limiter | **Redis** | Atomic counters, TTL |
| Ad-impressions ingestion | **Kafka → Cassandra / ClickHouse** | Append-heavy, analytics |

### Schema modeling examples

#### Chat messages — Cassandra

```
PRIMARY KEY ((conversation_id), sent_at, message_id)
```
- Partition by `conversation_id` → all messages of a conversation on one node
- Clustering by `sent_at DESC` → newest messages first
- Single query returns latest N messages in one read

#### User feed — DynamoDB

```
Table: user_feed
PK: user_id (partition)
SK: created_at#post_id (sort)
```
- Query: `WHERE user_id = $me ORDER BY created_at DESC LIMIT 50` → one partition read

#### Catalog — MongoDB

```javascript
{
  _id: "sku-A1",
  name: "Mechanical Keyboard",
  category: ["electronics", "computers", "peripherals"],
  price: 12000,
  attributes: { switches: "MX-Brown", layout: "TKL" },
  variants: [{sku: "A1-RED", color: "red", stock: 12}, ...]
}
```
- Index on `category`, `price`
- One document per product, embedded variants

### Postgres + JSONB alternative

```sql
CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT UNIQUE,
  attrs JSONB,
  price_cents INT
);
CREATE INDEX ON products USING gin (attrs);
SELECT * FROM products WHERE attrs @> '{"color":"red"}';
```

In most cases this is enough — you keep ACID, joins, and SQL — and you skip the Mongo operational complexity.

---

## Common interview questions

1. What are the four NoSQL families? Give examples and use cases.
2. When would you use NoSQL over SQL?
3. SQL vs MongoDB — when does each win?
4. What is sharding? Strategies?
5. What's a good partition key?
6. What is eventual consistency?
7. Schemaless vs schema — pros and cons.
8. How do you model a chat application?
9. Difference between Cassandra and DynamoDB.
10. How does Redis differ from Memcached?
11. What is a hot partition?
12. How do NoSQL databases handle joins?

---

## Detailed answers

### 1. Four families
KV (Redis), Document (Mongo), Wide-column (Cassandra), Graph (Neo4j). Plus specialized: search (ES), OLAP (ClickHouse), time-series (Influx).

### 2. NoSQL over SQL
When: extreme scale per access pattern, geo-distributed writes, flexible nested schema, append-heavy, single-digit-ms latency at scale. Otherwise, default to Postgres.

### 3. SQL vs Mongo
- **SQL wins**: relational data, joins, ad-hoc analytics, ACID, mature ecosystem, lower ops cost at modest scale
- **Mongo wins**: deeply nested documents, schema flexibility (multi-tenant SaaS with varying customer fields), single-document atomic writes on big nested structures
- Postgres JSONB closes most of the gap

### 4. Sharding
Splitting data across nodes by a partition key. Strategies: hash, range, directory, composite. Hash distributes evenly; range supports range scans but risks hotspots; directory is flexible.

### 5. Good partition key
- High cardinality (millions of distinct values)
- Even access distribution (no "celebrity user" hot key)
- Aligned with primary access pattern (one query = one partition)
- Bad: timestamp alone (all new writes hit one partition); single tenant ID where one tenant dominates

### 6. Eventual consistency
After a write, replicas converge to the same value "eventually." Reads from lagging replicas may see stale data temporarily. Most NoSQL systems offer tunable consistency: Cassandra/Dynamo let you choose strong, quorum, or eventual per request.

### 7. Schemaless vs schema
- **Schemaless**: faster iteration, no migrations, but schema lives in app code and breaks silently
- **Schema**: enforced at DB, safer, but migrations required
- Truly "schemaless" is rare — most apps have an implicit schema. Mongo has schema validation; Postgres has JSONB with optional checks. Pick the safety/flexibility point you want.

### 8. Chat app schema
- Cassandra: `((conv_id), sent_at DESC, msg_id)` — partition by conversation, sort by time
- DynamoDB: PK=conv_id, SK=sent_at#msg_id
- Postgres: messages table with `(conv_id, sent_at DESC)` index
Discuss trade-offs: Postgres simpler, Cassandra better for huge global scale.

### 9. Cassandra vs DynamoDB
| | Cassandra | DynamoDB |
|---|---|---|
| Ops | Self-managed (or DataStax) | Fully managed AWS |
| Consistency | Tunable (R, W, ALL, QUORUM) | Eventually consistent by default; strongly available |
| Pricing | Server costs | Pay-per-request or provisioned |
| Schema | CQL tables with clustering keys | PK + SK + GSI/LSI |
| Geo | Multi-DC replication | Global tables |
| Hot spots | Partition-based | Adaptive capacity (auto-rebalance) |
Both wide-column at heart. Dynamo is simpler ops, more constrained query API.

### 10. Redis vs Memcached
- Redis: rich data structures (lists, sets, sorted sets, hashes, streams), persistence (RDB/AOF), replication, clustering, pub/sub, Lua scripting
- Memcached: pure KV, multi-threaded, simpler, slightly faster for plain GET/SET, no persistence
- Pick Redis by default unless you need extreme simplicity

### 11. Hot partition
A single partition receiving disproportionate traffic (e.g., 90% of reads). Symptoms: latency spikes, throttling on one node. Causes: bad partition key (low cardinality, skewed), "celebrity" users. Mitigation: add randomness/sharding to the partition key, cache reads, redesign.

### 12. NoSQL joins
Most NoSQL stores don't support cross-document/row joins. You either:
- Embed related data (denormalization)
- Do client-side joins (fetch from one store, then another)
- Use a secondary system (e.g., a graph DB for graph queries)
- Pre-compute join results into a "materialized" form

---

## Practical coding examples

### Redis: cache-aside in Node
```javascript
async function getUser(id) {
  const cacheKey = `user:${id}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const user = await db.query('SELECT * FROM users WHERE id=$1', [id]);
  await redis.setex(cacheKey, 300, JSON.stringify(user));
  return user;
}
```

### MongoDB: aggregation pipeline
```javascript
db.orders.aggregate([
  { $match: { status: 'PAID', createdAt: { $gte: ISODate("2026-01-01") } } },
  { $group: { _id: "$userId", total: { $sum: "$amount" }, count: { $sum: 1 } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
]);
```

### DynamoDB: query a single partition
```javascript
const out = await ddb.query({
  TableName: "messages",
  KeyConditionExpression: "conv_id = :c AND sent_at > :t",
  ExpressionAttributeValues: { ":c": convId, ":t": since },
  ScanIndexForward: false, // newest first
  Limit: 50
}).promise();
```

### Cassandra: write & query
```sql
CREATE TABLE messages (
  conv_id UUID,
  sent_at TIMESTAMP,
  msg_id  UUID,
  sender  TEXT,
  body    TEXT,
  PRIMARY KEY ((conv_id), sent_at, msg_id)
) WITH CLUSTERING ORDER BY (sent_at DESC, msg_id DESC);

SELECT * FROM messages WHERE conv_id = ? LIMIT 50;
```

---

## Common mistakes

- Choosing NoSQL for "future scale" you haven't measured
- Using Mongo for highly relational data (then complaining about manual joins)
- Picking a partition key that creates hot partitions
- Using auto-increment ID as partition key in Dynamo (every write hits one shard)
- Forgetting to model secondary access patterns (then doing scans)
- Treating Redis as primary durable store without persistence configured
- Ignoring cross-region replication latency
- Building "polyglot persistence" too early — 2 stores instead of 1, with consistency headaches

---

## Senior engineer discussion points

- **Polyglot persistence**: when one DB stops fitting, add another for specific workloads (Redis for cache, Elasticsearch for search). Operational overhead grows superlinearly with store count.
- **CDC** (Debezium) to keep multiple stores in sync from one source of truth
- **The cost of NoSQL ops** — DynamoDB cost surprises, Cassandra repair operations, Mongo replica-set fail-overs
- **Multi-region trade-offs** — global tables are great, but conflict resolution semantics matter
- **DynamoDB single-table design** — controversial, dense, but key to top-tier Dynamo performance
- **Why Mongo lost ground to Postgres** in many shops: JSONB + the SQL ecosystem
- **When to migrate off NoSQL** — usually when you start needing analytics or relational integrity that the chosen store doesn't provide. Plan for it; lock-in is real.

---

## Revision notes

- Families: KV (Redis) / Document (Mongo) / Wide-column (Cassandra/Dynamo) / Graph (Neo4j)
- NoSQL: model your queries → design data shape
- Default = Postgres + Redis; reach for NoSQL when measured
- Sharding strategies: hash / range / directory / composite
- Hot partition = bad partition key
- Eventual vs strong consistency = latency vs correctness
- Redis ≠ Memcached (data structures, persistence)
- Mongo since 4.x has transactions (limited)
- DynamoDB = managed wide-column; partition + sort key; GSI for alternate access patterns
- Cassandra = self-managed; tunable consistency
- Polyglot persistence costs operational complexity — earn it with measurement
