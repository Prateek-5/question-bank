# Database Normalization & Schema Design

## Why this matters in backend interviews

- **Every schema-design machine coding round** tests this. The interviewer hands you a problem (parking lot, hotel booking, Splitwise) and you sketch tables on a whiteboard.
- **System design**: normalization is the bedrock of any data model discussion.
- **Senior signal**: knowing *when not* to normalize — and being able to argue both sides — separates juniors from SDE2.
- **Debugging**: poorly normalized schemas cause update anomalies, inconsistencies, and bloat. Recognizing this in legacy code is a senior skill.

---

## Why interviewers care

When an interviewer hands you a "design a schema for X" prompt, they aren't testing whether you can recite 1NF/2NF/3NF definitions. They're testing **design judgment**:

- Can you decompose a messy real-world entity (an Excel sheet a PM emailed you) into well-bounded tables?
- Do you recognize the smell of redundancy before it bites — duplicate addresses, inconsistent department names, "we updated the SKU in one place but not the other"?
- Can you defend trade-offs? "I denormalized `order.total_cents` because reads dominate writes 1000:1 and the aggregation cost was real."
- Do you know which constraint goes where (NOT NULL vs CHECK vs FK vs unique index)?
- Can you smell EAV, god tables, boolean explosion — and propose the fix?

A senior engineer doesn't just normalize. A senior engineer **knows which normal form serves the workload** and can articulate why.

---

## The intuitive picture — why this even exists

Imagine your team starts with a single Google Sheet for the company:

```
| order_id | customer_name | customer_email | customer_address | product   | qty | price |
| 1        | Asha          | asha@x.com     | 12 Park St, BLR  | Headphone | 2   | 1500  |
| 2        | Asha          | asha@x.com     | 12 Park St, BLR  | Cable     | 1   | 200   |
| 3        | Asha          | asha@x.com     | 13 MG Rd,  BLR   | Mouse     | 1   | 800   |
```

Three problems immediately appear:

1. **Update anomaly** — Asha moves to "13 MG Rd". Row 1 and 2 still say "12 Park St". The DB now disagrees with itself.
2. **Insertion anomaly** — A new customer signs up but hasn't ordered yet. Where do they live? You'd have to fake an order, or leave product columns NULL.
3. **Deletion anomaly** — Order #3 is cancelled and deleted. You also just deleted Asha's only record of address "13 MG Rd". You lost data you wanted to keep.

Normalization is the formalization of one idea: **every fact should live in exactly one place**. If a fact appears twice, the two copies will eventually disagree.

The plain-English translation of each normal form:

- **1NF** — "Don't stuff lists into a single cell."
- **2NF** — "If your key is two things glued together, every column must depend on *both* halves, not one."
- **3NF** — "A non-key column can describe the row, but it can't describe *another non-key column*."
- **BCNF** — "Every dependency must come from a real key — no exceptions, even weird ones."

That's it. The rest is just rigor.

### A functional dependency, in one sentence

> "If I tell you the value of column A, you can tell me the value of column B with certainty."

Notation: `A → B`. Read as "A determines B".

- `customer_id → customer_name` ✓ (given an ID, name is fixed)
- `customer_id → customer_address` ✓ (today, ignoring history)
- `order_id → customer_id` ✓
- `product_id → product_name`, `product_id → price` ✓
- `customer_email → customer_id` ✓ (if email is unique)

A schema is "well-normalized" when every functional dependency in the data corresponds to a proper key in the table holding it. Everything else is just rules layered on top of this single idea.

```
FD graph for the messy sheet above:

  order_id ─────► customer_id ─────► customer_name
                                ────► customer_email
                                ────► customer_address
              ────► (product_id, qty)
  product_id ──► product_name
              ──► price

Different "subjects" (order, customer, product) → different tables.
```

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

##### Mental Model — 1NF

Think of 1NF as the **"one fact per cell"** rule. A cell is a (row, column) intersection — and it must hold a single, indivisible value of the column's type.

Why this rule exists: SQL operates on cells. The moment a cell contains structure (a CSV, a list, a hidden sub-record), SQL can't index it, can't enforce a foreign key on it, can't sort by it, and can't ask "give me all users whose phones include 555-9999" without resorting to string hacks like `LIKE '%555-9999%'` (which is slow and wrong if numbers contain each other as substrings).

Real-world analogy: a library card catalog where one card says "Authors: Asimov, Bradbury, Clarke" is useless if you want to search by author. You need one card per (book, author) pair.

##### Step-by-step — walking a row through 1NF

```
BEFORE (violates 1NF — "phones" holds two values):
+----+--------+---------------------+
| id | name   | phones              |
+----+--------+---------------------+
|  1 | Asha   | 555-1234,555-9999   |
|  2 | Bilal  | 555-7777            |
+----+--------+---------------------+

AFTER (1NF — atomic, indexable, FK-able):
users:                       user_phones:
+----+--------+              +---------+-----------+-------+
| id | name   |              | user_id | phone     | label |
+----+--------+              +---------+-----------+-------+
|  1 | Asha   |              |    1    | 555-1234  | home  |
|  2 | Bilal  |              |    1    | 555-9999  | work  |
+----+--------+              |    2    | 555-7777  | mob   |
                             +---------+-----------+-------+

Now you can: index phone, FK to users, enforce uniqueness per user,
add metadata (verified_at), and query "users with 2+ phones".
```

#### 2NF — No partial dependency

If the PK is composite, every non-key column must depend on the **whole** PK, not part of it.

```sql
-- BAD (PK = order_id, product_id; product_name depends on product_id only)
order_items (order_id, product_id, product_name, quantity)

-- GOOD
order_items (order_id, product_id, quantity)
products    (id, name)
```

##### Mental Model — 2NF

2NF only matters when your primary key is **composite** (two-or-more columns). If your PK is a single surrogate `id`, you're automatically in 2NF — there's no "part of the key" to depend on.

The mental check: cover up part of the composite key with your finger. Does any non-key column now have a determined value? If yes, that column belongs in a different table keyed by that part.

Real-world analogy: a school timetable keyed by `(class_id, period)` listing `subject, teacher, classroom, teacher_phone`. The teacher's phone number doesn't depend on `period` — it depends only on the teacher. Pull it out into a teachers table.

##### Step-by-step — walking a row through 2NF

```
BEFORE (PK = order_id + product_id; product_name depends on product_id ALONE):
+----------+------------+--------------+----------+
| order_id | product_id | product_name | quantity |
+----------+------------+--------------+----------+
|    101   |     42     | Headphone    |    2     |
|    101   |     43     | Cable        |    1     |
|    102   |     42     | Headphone    |    1     |  <-- "Headphone" duplicated
|    103   |     42     | Headphones   |    3     |  <-- typo creeps in
+----------+------------+--------------+----------+

The partial dependency: product_id → product_name
                         (a piece of the PK determines a non-key column)

AFTER (2NF):
order_items:                       products:
+----------+------------+-------+  +----+------------+
| order_id | product_id | qty   |  | id | name       |
+----------+------------+-------+  +----+------------+
|    101   |     42     |   2   |  | 42 | Headphone  |
|    101   |     43     |   1   |  | 43 | Cable      |
|    102   |     42     |   1   |  +----+------------+
|    103   |     42     |   3   |
+----------+------------+-------+

Fixing the headphone name once now corrects it everywhere.
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

##### Mental Model — 3NF

3NF is the "**no second-hand information**" rule. Every fact in a row must describe **the entity the row is about**, not some other entity that happens to be referenced.

The catchphrase the academic crowd uses: *"Every non-key column must depend on the key, the whole key, and nothing but the key — so help me Codd."* The third part ("nothing but the key") is 3NF.

The transitive chain to spot: `PK → non_key_A → non_key_B`. The arrow from A to B is the bug. `non_key_B` is really describing whatever A is — so it should live in A's table.

Real-world analogy: an employee's business card has their name, their employee ID, their department code, **and the department's mailing address**. The mailing address isn't about the employee — it's about the department. If the department moves, you'd have to reprint every employee's card. Pull "department" out into its own table.

##### Step-by-step — walking a row through 3NF

```
BEFORE (transitive: emp_id → dept_id → dept_name):
+--------+--------+---------+---------------+
| emp_id | name   | dept_id | dept_name     |
+--------+--------+---------+---------------+
|  1001  | Asha   |    7    | Engineering   |
|  1002  | Bilal  |    7    | Engineering   |
|  1003  | Chen   |    7    | Engg.         |  <-- drift!
|  1004  | Diya   |    9    | Marketing     |
+--------+--------+---------+---------------+

If "Engineering" rebrands to "Product Engineering",
you must UPDATE 3 rows here (and any future drift hides bugs).

AFTER (3NF — dept_name is now the responsibility of one row):
employees:                  departments:
+--------+--------+-------+ +----+---------------------+
| emp_id | name   | dept  | | id | name                |
+--------+--------+-------+ +----+---------------------+
|  1001  | Asha   |   7   | |  7 | Product Engineering |
|  1002  | Bilal  |   7   | |  9 | Marketing           |
|  1003  | Chen   |   7   | +----+---------------------+
|  1004  | Diya   |   9   |
+--------+--------+-------+

Rename a department: one UPDATE, zero drift, forever consistent.
```

#### BCNF (Boyce-Codd)

Stronger than 3NF. Every functional dependency `X → Y` must have `X` as a superkey. Rarely matters in practice; if you're at 3NF you're usually fine.

##### Mental Model — BCNF

3NF has a loophole. It says "non-key columns can't determine non-key columns" — but it's silent about a **non-key column determining part of a candidate key**. BCNF closes that loophole: *every* dependency, in *any* direction, must originate from a superkey.

In plain English: BCNF says **every arrow in your FD graph must start from a key**. If anything else is on the left side of an arrow, you have a BCNF violation.

The textbook example that distinguishes 3NF from BCNF:

```
Table: course_enrollment
Columns: (student_id, course, instructor)

Business rules:
  - A student takes one course at a time per instructor (PK = student_id, course)
  - Each instructor teaches exactly ONE course
    => instructor → course   (a non-key column determines part of the key)

This is in 3NF (no transitive dep between non-key columns),
but NOT in BCNF (instructor isn't a superkey, yet it determines course).

Anomaly: if all students drop a course, you lose the
         instructor-teaches-this-course fact entirely (deletion anomaly).

BCNF fix:
  enrollments  (student_id, instructor)
  teaches      (instructor PK, course)
```

Why interviewers rarely ask: in 95% of real schemas — especially when you use surrogate keys — 3NF and BCNF coincide. The split shows up in schemas with overlapping composite candidate keys, which are uncommon in modern OLTP design.

When to **mention** BCNF in an interview: only if you find a non-trivial FD where the left side isn't a key. Otherwise stop at 3NF and move on.

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

##### Mental Model — Denormalization tradeoffs

Normalization optimizes for **writes and correctness**. Denormalization optimizes for **reads and latency**. You cannot have both for free; you are choosing which side of the trade-off pays the cost.

Think of denormalization as **deliberately caching** a derived value inside your tables. Like every cache, it has three concerns:

1. **Staleness** — how out-of-date can the copy get before it's wrong?
2. **Invalidation** — when the source changes, what recomputes the copy?
3. **Source of truth** — which value wins if they disagree?

```
Normalized                    Denormalized
─────────────────             ─────────────────
Reads:    expensive joins     Reads:    single-table scans
Writes:   single point        Writes:   N places to update
Storage:  minimal             Storage:  larger
Drift:    impossible by       Drift:    possible if refresh
          construction                  pipeline breaks
Audit:    easy                Audit:    harder
Hot path: slower              Hot path: faster (often 10-100x)
```

The two **legitimate** kinds of denormalization in OLTP systems:

- **Historical snapshots** (e.g. `order_items.unit_price_cents`) — not really "denormalization" because the snapshot is a *different fact* than the live value. The product's current price can change; the price-at-time-of-order cannot. This is semantically correct.
- **Aggregates / counters** (e.g. `posts.like_count`, `users.unread_count`) — explicit caches that need an explicit refresh mechanism (trigger, CDC, async job).

The illegitimate kind: copying a value "just because we'll need it" with no plan for when it goes stale.

---

## Common beginner confusion

#### "Is 3NF always better than 2NF?"
For correctness, yes — 3NF eliminates more redundancy. But "better" depends on workload. A reporting table that's 90% read may be deliberately in 2NF (or below) to avoid joins. The senior framing: *normalize for correctness first, denormalize selectively for measured hot paths.*

#### "Is BCNF always better than 3NF?"
BCNF is stricter, but the difference shows up only in edge-case dependencies. In practice, with surrogate keys and reasonable design, the schemas coincide. Stop at 3NF unless you find a specific FD violation.

#### "Should I always normalize to the highest form possible?"
No. There's no medal for hitting 5NF. The goal is "as normalized as the workload needs to stay consistent, no more." Over-normalization explodes join count and hurts query planners.

#### "Why does my normalized schema have so many joins?"
That's the cost. You traded write-time simplicity (one fact per place) for read-time complexity (gather facts via joins). This trade is almost always worth it for OLTP. If a particular join becomes a hot-path bottleneck, denormalize *that join*, not everything.

#### "Aren't foreign keys slow? Should I drop them?"
The cost of FK checks in modern Postgres/MySQL is microseconds per write and is **dwarfed** by the cost of fixing referential corruption when an orphan row sneaks in. Keep them unless a benchmark proves they're the bottleneck.

#### "JSON columns are flexible — why not put everything in JSON?"
Because the schema doesn't disappear — it just moves into your application code, where the database can't help you. No FKs, no CHECK constraints, no type safety, no easy indexing. JSONB is fine for genuinely variable / optional attributes. It is not a replacement for tables.

#### "Why do my queries have NULLs everywhere?"
NULLs are usually a smell that a column belongs to a different entity. If half your `users` rows have NULL `company_address` because only half are corporate, that's a candidate for a separate `companies` table or a sparse one-to-one table.

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

## Interview storytelling — walking a design out loud

Schema-design interviews are not multiple-choice. The interviewer wants to **hear your thought process**. Use this skeleton:

1. **Restate the domain in one sentence.** ("So we're modelling a hotel booking system where users reserve rooms across multiple properties.")
2. **List the entities first, in nouns.** Property, Room, RoomType, Booking, User, Payment. Don't draw columns yet.
3. **Draw the relationships.** 1:1, 1:N, N:N. Annotate each with a real example sentence ("a Booking belongs to one User and one Room").
4. **Now add columns, justifying each.** Skip nothing — say "I'll add `created_at` because we'll need to audit and sort." Don't dump 20 columns silently.
5. **Walk through anomalies.** "If I store the room price on the booking, what happens when the rate changes? Good — I'll snapshot it." This is where you bring in 1NF/2NF/3NF naturally.
6. **Call out the denormalizations explicitly.** Don't sneak them in. "I'm storing `total_cents` on `orders` even though I could compute it from items — here's why: the receipt must freeze."
7. **State the trade-offs you didn't take.** "I considered an EAV-style attributes table for room amenities. I won't, because amenities are bounded — a junction table is cleaner."

The senior signal: you talked through **why** before **what**. You named what you optimized for. You said "I'd revisit this if reads dominate."

### A failure walk-through interviewers love

"Here's a real production bug: every customer in this table had their address overwritten because the address lived on the orders table and was copied at order time. When a customer moved, ops updated the customer record — but the trigger that fanned out to historical orders went out of order, and three months of analytics broke. Walk me through what's wrong and how you'd refactor."

The answer demonstrates:
- You recognize that **historical data and current data are different facts** (snapshot vs reference).
- You'd separate `customers.current_address_id` (a reference, mutable) from `orders.shipping_address_snapshot` (an immutable copy at order time).
- You can articulate the rule: *if a downstream system depends on the value at point-in-time, snapshot it; if it depends on "today's value", reference it.*

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

## Bridge to the next topics

Normalization tells you **how to structure data so each fact lives in one place**. But the moment you have multiple tables holding related facts, a new question arises: **how do you change them together, safely, when other users are doing the same?**

That's the next section — `06-transactions.md`. A transaction is the mechanism that makes "update three normalized tables" feel like one atomic operation. Without it, you'd see partial updates, half-committed transfers, and orphan rows everywhere. Normalization without transactions is a design half-finished.

After transactions, `07-isolation-levels.md` explains what "I" in ACID really means under concurrency, and `08-locks-concurrency.md` covers what mechanism actually delivers isolation. They build on each other in this exact order.

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
