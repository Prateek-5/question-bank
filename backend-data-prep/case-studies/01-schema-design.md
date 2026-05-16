# Schema Design Case Studies

Four full walk-throughs you can replay in interviews: **e-commerce**, **chat**, **payments**, **analytics**. For each: requirements → entities → schema → indexes → trade-offs → scaling.

> Interview tip: always start by clarifying access patterns and scale before writing tables. Senior signal.

---

## Plain-English orientation: why schema design is hard

A schema is the **blueprint of a building**. Once you've built the foundation and walls, you cannot easily add a wing on the third floor — you'd have to demolish parts that are already load-bearing. In databases, "demolishing" means migrations on tables that already hold millions of rows, taken under production traffic, with foreign keys and indexes everywhere. The blueprint you draw on day one constrains years of your team's velocity.

Three mental anchors before any table is written:

1. **Schema = the contract between your app and your storage.** Both sides must agree on the language: column names, types, nullability, relationships. Break the contract and either reads return nonsense or writes start failing.
2. **Entities = nouns of the business; relationships = verbs.** "A user PLACES an order; an order CONTAINS items; an item BELONGS TO a product." If you can't say it in plain English, you can't model it in tables.
3. **Access patterns drive design.**
   - SQL/OLTP: start normalized (one fact in one place), denormalize only where a hot read forces you.
   - NoSQL/wide-column: start with the query, then design the partition key and clustering so a single read materializes the answer.

> A normalized schema asks "where does this fact live?" — a denormalized one asks "what does this query need?" The senior engineer's job is to navigate between them with intent, not by default.

## ## Mental Model: entity-relationship modeling

Think of an ER model as a sentence diagram for the business domain.

```
+------------+   places   +---------+   contains   +------------+
|   User     |1--------- *|  Order  |1--------- * |  OrderItem |
+------------+            +---------+              +------------+
                                                          | *
                                                          | refers to
                                                          v 1
                                                    +-----------+
                                                    |  Product  |
                                                    +-----------+
```

Cardinality labels (`1` and `*`) are not decoration — they constrain queries and storage:
- `1:1` → can collapse into one table (rarely useful unless one side is optional/sparse).
- `1:N` → foreign key on the "many" side.
- `N:M` → join table with a composite primary key.

If you cannot label the cardinality of every line on your ER diagram, you do not understand the domain yet — pause the interview and ask the interviewer.

## ## Mental Model: surrogate vs natural keys

A **natural key** is a value that already identifies the row in the real world (email, ISBN, SKU). A **surrogate key** is an arbitrary identifier you mint (a `BIGSERIAL`, a UUID).

- Use **surrogate** as the primary key for almost every operational table — natural keys change (people change emails, products get re-SKU'd) and you do not want your foreign keys to cascade-update across the whole database.
- Keep the natural key as a `UNIQUE` constraint so business rules are still enforced.
- For lookup/reference tables (country codes, currency codes), the natural key (`'USD'`) is often fine as the primary key — it's stable and human-readable in joins.

**UUID v4 vs BIGSERIAL:**

```
BIGSERIAL  : monotonic, 8 bytes, index locality is excellent,
             leaks row counts to clients
UUID v4    : random, 16 bytes, fragments B-tree on insert,
             safe to expose externally
UUID v7    : time-ordered, 16 bytes, preserves locality, modern default
```

Senior signal: knowing UUID v4 inserts cause B-tree page splits and write amplification on hot tables, and that v7 (or ULID) fixes it.

## ## Mental Model: soft delete vs hard delete

- **Hard delete** = `DELETE FROM ...`. Row is gone. Storage reclaimed (eventually). Foreign keys that reference it must either CASCADE or fail.
- **Soft delete** = `UPDATE ... SET deleted_at = NOW()`. Row stays. Every other query must remember to filter `WHERE deleted_at IS NULL`.

There is no free lunch:
- Soft delete preserves history, supports undo, simplifies compliance reviews — but pollutes every query and index in the table.
- Hard delete is clean — but irreversible, dangerous for billing/audit, and may violate "right to be informed" if you have no copy.

The middle ground used by most production systems: **archive tables**. Move soft-deleted rows out to `<table>_archive` periodically so the live table stays lean.

## ## Mental Model: polymorphic associations

You have `comments` that can attach to `posts`, `photos`, or `videos`. The tempting schema:

```sql
CREATE TABLE comments (
  id BIGSERIAL PRIMARY KEY,
  parent_type TEXT NOT NULL,   -- 'post' | 'photo' | 'video'
  parent_id   BIGINT NOT NULL,
  body        TEXT
);
```

It looks clean. It is a **code smell** in SQL because:
- No real foreign key (the FK target depends on `parent_type`).
- `JOIN` requires `CASE` logic.
- The query planner cannot use a single index across three relations.

Cleaner alternatives:
- One comments table per parent type (`post_comments`, `photo_comments`).
- A `commentables` table with a surrogate ID; every commentable thing has a row there; comments reference it.
- In NoSQL, embed the comments inside the parent document.

## ## Mental Model: schema versioning and evolution

A schema is never "done" — it evolves. Plan migrations as **phases**, never as a single deploy:

```
V1: ADD COLUMN new_field NULLABLE   (no app reads yet)
     |
     v  deploy app code that writes new_field
     |
V2: backfill new_field for historical rows
     |
     v  deploy app code that reads new_field
     |
V3: ADD CONSTRAINT NOT NULL / UNIQUE / FK    (now safe)
     |
     v  optional: drop the old column once nothing reads it
V4: ...
```

The rule: **producers and consumers must never break in lockstep within the same deploy.** A senior engineer will think in terms of compatible windows, not flag days.

## ## Why interviewers care

Schema design questions are the highest-signal whiteboard problem because they reveal:
- **Design judgment** — did you ask access patterns before reaching for tables?
- **Foresight** — did you plan for evolution (versioning, additive migrations), scale (sharding key choice), and failure (idempotency, soft delete)?
- **Translation skill** — can you turn ambiguous business requirements ("users can place orders that they can later refund partially") into precise schema artifacts?
- **Operational empathy** — do you know which decisions will haunt the on-call engineer at 3 AM?

A candidate who immediately scribbles tables fails. A candidate who pauses to ask "what are the read patterns? how does it grow?" already passes the first bar.

## ## Common beginner confusion

| Belief | Reality |
|---|---|
| "Normalize first, then optimize." | Yes, but **only after you know the access patterns**. Pure 3NF on a read-heavy product catalog is malpractice. |
| "Use UUIDs everywhere — they're safer." | UUID v4 destroys B-tree index locality; on insert-heavy tables this is measurable. Prefer UUID v7 / ULID, or keep BIGSERIAL internally and expose a UUID externally. |
| "Soft delete is always safer." | Every read query now pays the `WHERE deleted_at IS NULL` tax forever — and partial indexes have to be maintained on every column you filter by. |
| "Add an index, problem solved." | Each index slows writes proportionally. The planner may ignore an index it thinks is unselective. Watch out for low-cardinality columns. |
| "Polymorphic associations are clean OOP." | They throw away referential integrity and are a query nightmare. Almost always worth splitting tables. |
| "I'll add multi-tenancy later." | The tenant ID belongs in every row from day one. Bolting it on later means rewriting every query and index. |
| "Money in FLOAT is fine for now." | It is never fine. Use `BIGINT` cents (or `NUMERIC`). Floats lose precision the moment you sum them. |

## ## First-principles: what is a "relation"?

A **relation** is mathematically a set of tuples where each tuple has the same attribute schema. A table is a relation; a row is a tuple. From this come the laws everything else inherits:
- **No duplicates** — a primary key uniquely names a tuple.
- **Atomic attributes** — a column holds one value, not a list (JSON columns are a deliberate exception, with costs).
- **No ordering** — the optimizer is free to scan in any order; you cannot rely on insertion order without `ORDER BY`.

**Third Normal Form (3NF)** exists to eliminate **update anomalies** — situations where one logical change requires updating many rows, with the risk of leaving the data inconsistent if the update is partial. The rule: every non-key attribute depends on the key, the whole key, and nothing but the key.

An **access pattern**, formally, is a triple: `(query shape, frequency, latency budget)`. You design indexes and denormalizations against this triple — not against vague gut feel. "Users will list their orders" is incomplete; "users list their last 20 orders sorted by date, 50× per second, with p99 < 50 ms" is a schema requirement.

## Bridge to the case studies

The four walkthroughs below — e-commerce, chat, payments, analytics — are not isolated puzzles. They are four different shapes of the same question: **given these access patterns and this scale, what schema minimizes future pain?** As you read each one, re-apply the 7-step walkthrough:

1. What are we storing? (entities)
2. How is it read? (queries + frequencies)
3. How is it written? (rates + invariants)
4. How is it queried for analytics? (rollups, BI)
5. How will it grow? (rows over 1, 2, 5 years)
6. Where are the hot paths? (which queries dominate?)
7. Where do we denormalize / index / cache / shard?

---

## 1. E-commerce platform

### Storytelling walkthrough — how to think aloud

Pretend you are at the whiteboard with the interviewer. Speak in this order:

> "We're storing a **catalog**, **users**, and **orders**. The hottest read is browsing — 100k QPS — so the catalog has to be index-friendly and probably cache-frontable. The hottest correctness path is checkout — 1k QPS writes — so inventory and orders must be transactional. Search across products is its own beast; I'll plan for trigram-on-Postgres now and Elasticsearch later. Carts span sessions so they need a stable identity even for anonymous users."

Now apply the 7-step walk:

1. **Entities** — `users`, `addresses`, `categories`, `products`, `inventory`, `carts`, `cart_items`, `orders`, `order_items`, `payments`.
2. **Relationships** — user 1:N addresses, user 1:1 cart, cart 1:N cart_items, product 1:1 inventory, order N:1 user, order 1:N order_items, payment N:1 order.
3. **Access patterns** — list products by category, full-text search, fetch cart, place order (transactional), list user's orders (recent first), update order status, idempotent payment writes.
4. **Normalize** — every fact (product name, address line, order status) lives in exactly one row.
5. **Hot paths** — product listings, cart fetch, order list page.
6. **Denormalize** — `unit_price_cents` in `order_items` (price is a snapshot — it must not change retroactively), `total_cents` in `orders` (avoids summing items on every list page).
7. **Index for read patterns** — `(user_id, created_at DESC)` for order history, GIN on `attrs` for facet filters, trigram on `name` for typeahead, partial index on hot order statuses.

```
Why snapshot price?
  Without snapshot:  order_items.unit_price = JOIN products.price  -> changes break receipts
  With snapshot:     order_items.unit_price = TEXT at purchase     -> immutable, audit-safe
```

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

### ER diagram — e-commerce

```
+----------+        +-----------+        +---------+
|  users   |1----- *| addresses |        |categories| (self ref: parent_id)
+----------+        +-----------+        +---------+
     |1                                      |1
     |                                       |
     | *                                     | *
+--------+         +-----------+        +---------+
| orders |* ----- 1| order_items|*------|products | -- 1:1 -- inventory
+--------+         +-----------+        +---------+
     |1                                      ^
     |                                       |
     v *                                     |
+----------+                          +-----------+
| payments |                          | cart_items|*--- 1 carts ---1 users
+----------+                          +-----------+
```

### Common interviewer follow-ups (e-commerce)

- "What if a product price changes mid-cart?" → Snapshot at order-place time, not at cart-add time. Cart shows live price; receipt shows snapshot.
- "How do you support variants (S/M/L)?" → A `product_variants` table; SKU lives on the variant, not the product.
- "Multi-currency?" → store amount + currency code; never mix currencies in one column; FX is a separate concern.
- "How do you support B2B with per-customer pricing?" → `price_lists` table joined by `(customer_id, product_id)`.

### Multi-tenancy escape hatch

If this catalog were SaaS (multiple merchants on one platform), every table above needs a `tenant_id BIGINT NOT NULL`, indexed first in every composite index, and ideally enforced via Postgres Row Level Security. Bolting it on later is one of the most expensive migrations a startup can do — that is why senior engineers ask "is this multi-tenant?" before writing a single `CREATE TABLE`.

### Bridge to the next study

E-commerce taught us **denormalization for read speed** and **transactional invariants for correctness**. Chat will push on a different axis: **partitioning data so that each conversation lives on one shard**, and choosing a store whose physics match append-heavy, time-ordered writes.

---

## 2. Chat / messaging system

### Storytelling walkthrough

> "Messages are append-only, time-ordered, and almost always read in the context of one conversation. That suggests a partition key of `conv_id`, with messages clustered by time inside the partition. Postgres works fine until conversations get hyperactive — then we time-bucket. For 1B+ messages, Cassandra's storage engine is a better physical match."

7-step pass:

1. **Entities** — `conversations`, `conversation_participants`, `messages`, optionally `attachments`, `reactions`.
2. **Relationships** — conversation N:M users (via participants), conversation 1:N messages.
3. **Access patterns** — last 50 messages of a conversation, list a user's conversations, unread count per conversation, full-text search across messages.
4. **Normalize** — message body lives once.
5. **Hot paths** — `WHERE conv_id=? ORDER BY sent_at DESC LIMIT 50` dominates everything.
6. **Denormalize** — `last_read_msg_id` on the participant row instead of a separate reads table; cache `unread_count` in Redis.
7. **Index / partition** — `(conv_id, sent_at DESC)` as the clustering pair; in Cassandra this is the *partition + clustering key*, in Postgres a btree index.

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

### ASCII: time-bucketing a wide conversation

```
Conversation 99 (1.5M messages over 2 years)

Without bucketing:
  partition(conv=99) holds 1.5M rows -> hot partition, scans slow

With monthly bucket:
  partition(conv=99, bucket='2025-01') -> ~60k rows
  partition(conv=99, bucket='2025-02') -> ~60k rows
  ...
  query "latest 50" -> read newest bucket only (cheap)
```

### Bridge to the next study

Chat taught us **partition key choice** and **time bucketing**. Payments will push on a different axis still: **strict ACID correctness, double-entry accounting, and idempotency for retries** — where being eventually consistent is a bug, not a feature.

---

## 3. Payments

### Storytelling walkthrough

> "Money is the strictest correctness domain. Two non-negotiables: idempotency (retries are routine) and double-entry accounting (every transfer must conserve total balance). I'll use `BIGINT` cents — never floats. Locks must be acquired in a deterministic order to avoid deadlocks. The ledger is the source of truth; the `accounts.balance_cents` is a denormalized cache that can always be recomputed."

7-step pass:

1. **Entities** — `accounts`, `transactions`, `ledger_entries`, `webhook_events`.
2. **Relationships** — account 1:N ledger_entries, transaction 1:N ledger_entries (two entries per transfer), account N:M transactions (`from_account_id`, `to_account_id`).
3. **Access patterns** — initiate transaction (idempotent), process webhook (idempotent), look up balance, list account history.
4. **Normalize** — each ledger entry is one fact.
5. **Hot paths** — balance reads (denormalized), idempotency checks (unique index on idempotency_key).
6. **Denormalize** — `balance_cents` on `accounts`, `balance_after_cents` on each ledger entry (snapshot, helps reconciliation).
7. **Index** — `(account_id, created_at DESC)` for statements; `UNIQUE(idempotency_key)`.

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

### Why double-entry feels redundant (and why it isn't)

Naive single-entry: `UPDATE accounts SET balance = balance - 100 WHERE id = A; UPDATE accounts SET balance = balance + 100 WHERE id = B;`. If anything between those statements crashes you have a missing $100. Even worse: if a developer tomorrow writes an ad-hoc UPDATE on `accounts.balance`, you can't tell from the table that history was rewritten.

Double-entry: every change is **two ledger rows whose amounts sum to zero**. The sum of all ledger entries is always zero — if it isn't, your books are broken and you can detect it immediately. The balance becomes a `SUM` query (cached in `accounts.balance_cents`), not a writeable column. You can prove correctness at any time:

```sql
SELECT account_id, SUM(amount_cents) AS computed_balance
FROM ledger_entries
GROUP BY account_id;
-- must equal accounts.balance_cents for every row
```

This is the test every fintech runs nightly.

### Bridge to the next study

Payments was about correctness at low scale. Analytics is the opposite axis: **eventual consistency is fine, but the volume is enormous** (100k events/sec). The store, the schema, and the indexing all change shape.

---

## 4. Analytics / events ingestion

### Storytelling walkthrough — OLTP vs OLAP mindset

> "OLTP is row-oriented: I write one row, I read one row. OLAP is column-oriented: I write billions of rows, I scan a few columns at a time and aggregate. Postgres is great at OLTP; ClickHouse is purpose-built for OLAP. For 100k events/sec, the choice is not 'which database' but 'which architecture' — Kafka decouples ingest from storage so we can fan out to multiple sinks."

7-step pass:

1. **Entities** — events (`user_id`, `event_type`, `ts`, `props`).
2. **Relationships** — events reference users, but the relationship is observational, not enforced (no FK; users may be deleted).
3. **Access patterns** — per-user timeline (Cassandra-shaped), funnel analysis (OLAP-shaped), hourly/daily rollups (materialized view-shaped).
4. **Normalize?** — barely. Events are denormalized by design. `event_type` may be a `LowCardinality(String)` for compression but is otherwise embedded.
5. **Hot paths** — daily rollups, top-N queries by event type.
6. **Denormalize / rollup** — `events_hourly` continuous aggregate, `events_daily_mv` SummingMergeTree view.
7. **Index / partition** — partition by day (Timescale chunk), partition by month (ClickHouse), partition by `(user_id, bucket)` (Cassandra).

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

### ASCII: row store vs column store

```
ROW STORE (Postgres)         COLUMN STORE (ClickHouse)
+-+-+-+-+                    +-----+   +-----+   +-----+
|1|A|x|10|  row 1            | 1   |   | A   |   | x   |  col user_id
+-+-+-+-+                    | 2   |   | A   |   | y   |  col event_type
|2|A|y|20|  row 2            | 3   |   | B   |   | x   |  col session
+-+-+-+-+                    | ... |   | ... |   | ... |
|3|B|x|15|  row 3            +-----+   +-----+   +-----+
+-+-+-+-+                    Scan: read only columns you need
Scan: read every column      Compression: same-domain values
even if you only want one    deflate 10-50x
```

For "count events by type for last 30 days" — column store reads just `event_type` and `ts`, blows past the row store.

---

## Cross-case-study patterns: schema evolution

Every one of the four schemas above will outgrow its original shape. The senior-engineer skill is **making evolution painless**.

### Schema evolution timeline (visual)

```
Day 1     V1: orders (id, user_id, total_cents, status)
            \
             \  business adds "partial refund" support
              v
Week 12   V1.5: ADD COLUMN refunded_cents INT NULL DEFAULT 0
            \   (additive — old code keeps working)
             \  backfill = 0 for historical rows
              v
Week 16   V2: app code starts reading refunded_cents
            \
             \  finance asks for "tax_cents" breakdown
              v
Week 24   V3: ADD COLUMN tax_cents INT NULL
            \  dual-write old total_cents + tax_cents
             \  finance queries new column
              v
Week 40   V4: ADD CHECK (refunded_cents <= total_cents) -- constraint
            \  once data is clean
             v
```

**Golden rules of online schema change:**
- Migrations must be **additive in step 1** (NULL columns, new tables, new indexes — never DROP, RENAME, or NOT NULL in one go).
- Use `CREATE INDEX CONCURRENTLY` in Postgres to avoid blocking writes.
- For breaking changes (rename, type change), do dual-write: old column + new column, migrate readers, then drop old.
- Have a rollback path for every migration in production.

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

## Whiteboard interview script — what to say first

When the interviewer says "design X", do **not** start writing tables. Say:

1. "Who are the users and what are the read patterns?"
2. "What's the write rate and the read rate?"
3. "What's the data growth over a year?"
4. "Any strict consistency requirements (money, inventory, identity)?"
5. "Any compliance constraints (GDPR, audit, multi-tenant isolation)?"
6. "Any analytics or BI requirements that I should plan a sink for?"

Only after these do you reach for `CREATE TABLE`. The first 30 seconds of the interview decide the rest of it.

## Final mental anchors

- **Tables are forever.** Code is rewritten; data outlives every refactor. Be skeptical of cleverness.
- **Indexes are not free.** Each one adds write cost; redundant indexes are silently expensive.
- **Foreign keys protect the invariant; cascades protect the cleanup.** Always know what happens on parent delete.
- **A composite key tells a story.** `(user_id, created_at DESC)` says "this table is browsed per-user, newest first". Read every PK as a sentence.
- **Don't model for today; model for the question they'll ask in 18 months.** Refunds, soft deletes, multi-currency, multi-tenancy — these almost always come back.

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
- Surrogate PK (BIGSERIAL or UUID v7) + UNIQUE on natural key is the standard pattern
- Soft delete has an ongoing cost — every query, every index, every backup
- Multi-tenancy: tenant_id in row from day one, not later
- Polymorphic associations are usually a smell — prefer one table per parent type
- Schema evolution is phased: additive → dual-write → migrate readers → drop old
- Whiteboard order: requirements → entities → relationships → access patterns → schema → indexes → trade-offs → scale
