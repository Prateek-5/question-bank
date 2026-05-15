# Schema Design Case Studies

Four full walk-throughs you can replay in interviews: **e-commerce**, **chat**, **payments**, **analytics**. For each: requirements → entities → schema → indexes → trade-offs → scaling.

> Interview tip: always start by clarifying access patterns and scale before writing tables. Senior signal.

---

## 1. E-commerce platform

### Requirements
- Browse products by category, search by name, filter by attributes
- Add to cart (per user), persist across sessions
- Checkout: address, payment, place order, reserve inventory
- View order history; support order status transitions
- Read scale: 100k QPS catalog browse; 1k QPS order writes

### Entities
Users, Addresses, Products, Categories, Inventory, Carts, CartItems, Orders, OrderItems, Payments.

### Schema (Postgres)

```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE addresses (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  line1 TEXT NOT NULL, line2 TEXT,
  city TEXT NOT NULL, state TEXT, country TEXT NOT NULL, postal TEXT,
  is_default BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_addresses_user ON addresses(user_id);

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
  description TEXT,
  category_id BIGINT NOT NULL REFERENCES categories(id),
  price_cents INT NOT NULL CHECK (price_cents >= 0),
  attrs JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_attrs ON products USING gin (attrs);
CREATE INDEX idx_products_name_trgm ON products USING gin (name gin_trgm_ops);

CREATE TABLE inventory (
  product_id BIGINT PRIMARY KEY REFERENCES products(id),
  qty_on_hand INT NOT NULL CHECK (qty_on_hand >= 0),
  qty_reserved INT NOT NULL DEFAULT 0 CHECK (qty_reserved >= 0)
);

CREATE TABLE carts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT UNIQUE REFERENCES users(id),
  session_id TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_carts_session ON carts(session_id) WHERE session_id IS NOT NULL;

CREATE TABLE cart_items (
  cart_id BIGINT NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (cart_id, product_id)
);

CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('PLACED','PAID','SHIPPED','DELIVERED','CANCELLED','REFUNDED')),
  total_cents INT NOT NULL,
  shipping_address_id BIGINT REFERENCES addresses(id),
  payment_id BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  paid_at TIMESTAMPTZ,
  shipped_at TIMESTAMPTZ
);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_status_created ON orders(created_at) WHERE status IN ('PLACED','PAID');

CREATE TABLE order_items (
  order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id BIGINT NOT NULL REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price_cents INT NOT NULL,  -- snapshot at purchase time
  PRIMARY KEY (order_id, product_id)
);

CREATE TABLE payments (
  id BIGSERIAL PRIMARY KEY,
  order_id BIGINT NOT NULL REFERENCES orders(id),
  amount_cents INT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('INITIATED','SUCCESS','FAILED','REFUNDED')),
  provider TEXT NOT NULL,
  provider_ref TEXT,
  idempotency_key TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Hot-path queries + index reasoning

| Query | Index | Plan |
|---|---|---|
| Category listing `WHERE category_id = ?` ORDER BY name | `idx_products_category` + sort | Index scan |
| Product search `name ILIKE '%abc%'` | `idx_products_name_trgm` | GIN trigram |
| Filter by attribute `attrs @> '{"color":"red"}'` | `idx_products_attrs` (GIN) | GIN match |
| User orders `WHERE user_id=? ORDER BY created_at DESC LIMIT 20` | `idx_orders_user_created` | Index range scan |
| Recent placed orders | `idx_orders_status_created` (partial) | Index scan |
| Cart by session | `idx_carts_session` (partial) | Index scan |

### Trade-offs & senior discussion
- **`unit_price_cents` snapshot in `order_items`** — denormalized intentionally; price can change later
- **`total_cents` in `orders`** — could be derived from items; kept for fast list-page queries
- **Inventory reservation**: `qty_reserved` separates "reserved by cart" from "available"; helps with timeouts
- **Cart for guest users**: keyed by `session_id` (cookie); merge into user cart on login
- **JSONB `attrs`** — flexible product attributes (color, size); indexed via GIN
- **Search** — trigram index for fast `ILIKE`; if scale grows, move to Elasticsearch
- **Scale-out** — read replicas for catalog browse; shard orders by `user_id` if you outgrow one Postgres
- **Caching** — Redis for product detail page; CDN for images; warm popular categories

### Inventory reservation flow (transactional)
```sql
BEGIN;
UPDATE inventory
  SET qty_reserved = qty_reserved + 2
  WHERE product_id = 42 AND (qty_on_hand - qty_reserved) >= 2;
-- 0 rows? out of stock; ROLLBACK
INSERT INTO orders ...;
INSERT INTO order_items ...;
INSERT INTO outbox (topic, payload) VALUES ('order.placed', ...);
COMMIT;
```

---

## 2. Chat / messaging system

### Requirements
- 1:1 and group conversations
- Send/receive messages in real time
- Show last 50 messages, paginate older
- Read receipts / unread counts
- 10M conversations, 1B messages, 10k QPS writes

### Schema (Postgres for canonical + Redis/Cassandra for hot data)

```sql
CREATE TABLE conversations (
  id BIGSERIAL PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('DM','GROUP')),
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversation_participants (
  conv_id BIGINT NOT NULL REFERENCES conversations(id),
  user_id BIGINT NOT NULL REFERENCES users(id),
  joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_read_msg_id BIGINT,
  PRIMARY KEY (conv_id, user_id)
);
CREATE INDEX idx_part_user ON conversation_participants(user_id);

CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  conv_id BIGINT NOT NULL REFERENCES conversations(id),
  sender_id BIGINT NOT NULL REFERENCES users(id),
  body TEXT NOT NULL,
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_conv_sent ON messages(conv_id, sent_at DESC);
```

### Cassandra alternative (for scale)
```sql
CREATE TABLE messages (
  conv_id UUID,
  sent_at TIMESTAMP,
  msg_id  UUID,
  sender  UUID,
  body    TEXT,
  PRIMARY KEY ((conv_id), sent_at, msg_id)
) WITH CLUSTERING ORDER BY (sent_at DESC, msg_id DESC);
```

### Hot-path queries

| Query | How |
|---|---|
| List user's conversations | Join `conversation_participants` + recent message timestamp from cache |
| Latest 50 messages of a convo | `WHERE conv_id=? ORDER BY sent_at DESC LIMIT 50` |
| Unread count | `last_read_msg_id` in `conversation_participants` vs max id |
| Search messages | Postgres FTS or Elasticsearch (latter at scale) |

### Senior discussion
- **Per-conversation partitioning**: messages cluster by `conv_id`; perfect partition key in Cassandra/Dynamo
- **Wide conversations**: a hyperactive group may grow > 1M messages → bucket by month
- **Real-time delivery**: WebSocket layer + Redis pub/sub for fan-out
- **Unread count caching**: per-(conv, user) in Redis; update on every send
- **At-rest encryption**: column-level for body; client-side for E2EE
- **Soft delete vs hard delete**: legal/compliance question (GDPR right-to-erasure)
- **Attachments**: store in S3, reference URL in messages

---

## 3. Payments

### Requirements
- Initiate payment (idempotent)
- Webhook from gateway updates status
- Money transfer between accounts
- Strict ACID; auditability; double-entry accounting
- 1k QPS writes; correctness over throughput

### Schema (Postgres, ACID)

```sql
CREATE TABLE accounts (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(id),
  balance_cents BIGINT NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'USD',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Double-entry ledger: every transaction is a pair of credit/debit entries
CREATE TABLE ledger_entries (
  id BIGSERIAL PRIMARY KEY,
  transaction_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL REFERENCES accounts(id),
  amount_cents BIGINT NOT NULL,  -- positive = credit, negative = debit
  balance_after_cents BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ledger_acct_created ON ledger_entries(account_id, created_at DESC);

CREATE TABLE transactions (
  id BIGSERIAL PRIMARY KEY,
  idempotency_key TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('TRANSFER','PAYMENT','REFUND','TOPUP')),
  status TEXT NOT NULL CHECK (status IN ('PENDING','SUCCESS','FAILED','REVERSED')),
  amount_cents BIGINT NOT NULL,
  currency TEXT NOT NULL,
  from_account_id BIGINT REFERENCES accounts(id),
  to_account_id BIGINT REFERENCES accounts(id),
  external_ref TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE webhook_events (
  external_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);
```

### Transfer flow

```sql
BEGIN;
-- Idempotency check (acquire lock on transaction key)
INSERT INTO transactions (idempotency_key, type, status, amount_cents, currency, from_account_id, to_account_id)
  VALUES ($1, 'TRANSFER', 'PENDING', $2, 'USD', $3, $4)
  ON CONFLICT (idempotency_key) DO NOTHING
  RETURNING id;
-- If null, return existing transaction status (idempotent)

-- Lock accounts in deterministic order
SELECT id, balance_cents FROM accounts WHERE id IN (LEAST($3,$4), GREATEST($3,$4)) ORDER BY id FOR UPDATE;

-- Validate balance
UPDATE accounts SET balance_cents = balance_cents - $2 WHERE id = $3 AND balance_cents >= $2;
-- If 0 rows: ROLLBACK, mark txn FAILED

UPDATE accounts SET balance_cents = balance_cents + $2 WHERE id = $4;

-- Append ledger entries
INSERT INTO ledger_entries (transaction_id, account_id, amount_cents, balance_after_cents)
SELECT $tx_id, id, CASE WHEN id=$3 THEN -$2 ELSE $2 END, balance_cents
FROM accounts WHERE id IN ($3, $4);

-- Mark transaction success
UPDATE transactions SET status='SUCCESS', completed_at=NOW() WHERE id=$tx_id;

-- Outbox event
INSERT INTO outbox (topic, payload) VALUES ('payment.completed', ...);

COMMIT;
```

### Senior discussion
- **Idempotency** mandatory; webhook retries are routine
- **Double-entry ledger** = source of truth; balances can be reconstructed from ledger
- **Lock ordering** prevents deadlocks
- **SERIALIZABLE isolation** sometimes warranted for fraud-detection cross-account logic (write skew prevention)
- **Money type**: BIGINT cents (never FLOAT); decimal in some systems (Postgres NUMERIC)
- **Auditability**: every state change recorded; never UPDATE in place beyond status fields
- **Outbox for downstream events**: notifications, fraud, analytics
- **PCI compliance**: card data never stored; tokenize via Stripe / Adyen
- **Scaling**: one Postgres can do 1-2k TPS easily; shard by user_id only when measured. Beyond: distributed SQL (CockroachDB / Spanner).

---

## 4. Analytics / events ingestion

### Requirements
- 100k events/sec ingest
- Query: events per user per day, funnel analysis, time-series rollups
- Ad-hoc analytical queries
- 1-year retention

### Architecture
```
[Producers] → Kafka → [Stream consumers] → ClickHouse / TimescaleDB / Cassandra
                                                ↓
                                          Materialized rollups
                                                ↓
                                          BI tools / dashboards
```

### Schema (TimescaleDB — Postgres + time-series)

```sql
CREATE TABLE events (
  id BIGSERIAL,
  user_id BIGINT NOT NULL,
  event_type TEXT NOT NULL,
  ts TIMESTAMPTZ NOT NULL,
  session_id TEXT,
  props JSONB,
  PRIMARY KEY (id, ts)
);
SELECT create_hypertable('events', 'ts', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_events_user_ts ON events(user_id, ts DESC);
CREATE INDEX idx_events_type_ts ON events(event_type, ts DESC);

-- Continuous aggregate (TimescaleDB feature; like materialized view, incremental)
CREATE MATERIALIZED VIEW events_hourly
WITH (timescaledb.continuous) AS
SELECT user_id, event_type, time_bucket('1 hour', ts) AS hour, COUNT(*) AS n
FROM events
GROUP BY user_id, event_type, hour;
```

### Schema (Cassandra — wide column)

```sql
CREATE TABLE events_by_user (
  user_id UUID,
  bucket DATE,
  ts TIMESTAMP,
  event_id UUID,
  event_type TEXT,
  props TEXT,  -- JSON
  PRIMARY KEY ((user_id, bucket), ts, event_id)
) WITH CLUSTERING ORDER BY (ts DESC);
```

### Schema (ClickHouse — columnar OLAP)

```sql
CREATE TABLE events (
  user_id UInt64,
  event_type LowCardinality(String),
  ts DateTime64(3, 'UTC'),
  session_id String,
  props String  -- JSON
) ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (user_id, ts);

-- Aggregation
CREATE MATERIALIZED VIEW events_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, event_type)
AS SELECT toDate(ts) AS day, event_type, count() AS n FROM events GROUP BY day, event_type;
```

### Senior discussion
- **Pick by query pattern**:
  - Hot per-user lookups → Cassandra/Dynamo
  - Time-series with SQL → TimescaleDB
  - Ad-hoc analytics over billions → ClickHouse / BigQuery / Snowflake
- **Ingest path**: Kafka decouples producers from sinks; consumers can write to multiple stores
- **Retention**: drop old partitions (Postgres / Timescale / Cassandra TTL / ClickHouse `TTL`)
- **Schema evolution**: schemaless `props` JSON allows new event fields without migration
- **Backpressure**: Kafka holds load if consumers stall
- **At-rest compression**: huge wins for event data (columnar shines: 10–50x compression)

---

## Common interview questions

1. Design an e-commerce schema.
2. Walk through a money transfer transaction.
3. How would you store a billion chat messages?
4. How do you handle inventory reservation correctly?
5. Where do you cache, and how do you invalidate?
6. When would you shard your DB? By what key?
7. How would you handle search across products?
8. Why double-entry ledger?
9. What goes in Postgres vs ClickHouse for analytics?
10. How do you support both read and write scale?

---

## Detailed answers

### 1. E-commerce
See above. Walk through entities → relationships → indexes → trade-offs. Mention denormalizations (price snapshot, total). Discuss caching + search separately.

### 2. Money transfer
ACID transaction with deterministic lock order, conditional debit, idempotency key, double-entry ledger, outbox for events. Discuss isolation (RC + locks is usually enough; SERIALIZABLE for cross-account rules).

### 3. Billion chat messages
- Partition by `conv_id`; clustering by time
- Cassandra/DynamoDB for hot data; Postgres for canonical/lookups
- Time-bucket within partition for very active convos
- Hot/cold tiers (recent in fast store, old in object storage / archive)

### 4. Inventory reservation
- `qty_on_hand` and `qty_reserved` columns
- Atomic `UPDATE … WHERE qty_on_hand - qty_reserved >= N`
- Reservation timeout (release after 15 min if cart abandoned)
- For very hot SKUs: Redis-backed counter + periodic reconciliation

### 5. Caching
- Read-heavy: product details, category listings → Redis with TTL
- Write invalidation on price/stock change
- L1 in-process + L2 Redis
- CDN for images and even API responses with proper cache-control

### 6. Shard when
- One Postgres can't handle write volume (typically > 10k writes/sec)
- Data size > a few TB per table
- Geographic isolation needed
- Shard key: user_id for B2C, tenant_id for B2B SaaS

### 7. Product search
- Small scale: Postgres FTS or trigram index
- Medium-large: Elasticsearch / OpenSearch / Meilisearch
- Sync via CDC (Debezium → Kafka → ES)
- Discuss ranking, typo tolerance, filters as faceted search

### 8. Double-entry ledger
Every transaction = paired entries (debit one, credit another). Balances are sums. Pros: auditability, can reconstruct state, easier to find bugs (sum of all entries = 0). Used by every serious financial system (banks, Stripe, Razorpay).

### 9. Postgres vs ClickHouse
- Postgres: OLTP, transactions, joins, single-row updates
- ClickHouse: OLAP, columnar, scan-and-aggregate, append-mostly
- Use both: Postgres for canonical state, CDC to ClickHouse for analytics

### 10. Read + write scale
- Reads: replicas, caching, CDN, materialized views
- Writes: shard by key, write-back caches, batch (microbatch), Kafka in front
- Both: pick the right store per workload (polyglot persistence)

---

## Revision notes

- Always: clarify access patterns and scale BEFORE designing
- E-commerce: snapshot prices in `order_items`; index `(user_id, created_at DESC)`; partial indexes for hot statuses
- Chat: partition by `conv_id`; time-bucket wide conversations
- Payments: idempotency keys, double-entry ledger, lock-ordered transactions
- Analytics: Kafka in, columnar/timeseries out; rollups for fast dashboards
- Money = BIGINT cents
- Snapshot historical values (price, name)
- Caching layer is a design concern from day 1, not bolted on
- Polyglot persistence costs ops complexity — earn it with measurement
