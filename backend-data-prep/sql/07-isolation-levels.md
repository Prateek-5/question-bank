# Isolation Levels & MVCC

## Why this matters in backend interviews

- **The single highest-signal "do you understand databases?" question.** Interviewers ask this to filter senior from mid-level engineers.
- **Every concurrent-update bug** in production traces back to an isolation-level misunderstanding.
- **System design**: you'll be asked "what isolation level for this?" — the answer should be backed by reasoning, not defaults.
- **Senior signal**: most candidates know READ COMMITTED vs SERIALIZABLE but can't explain *write skew*. That's the discriminator.

---

## Core concepts

### The four standard isolation levels

| Level | Dirty read | Non-repeatable read | Phantom | Write skew |
|---|---|---|---|---|
| READ UNCOMMITTED | ✗ allowed | ✗ allowed | ✗ allowed | ✗ allowed |
| READ COMMITTED | ✓ prevented | ✗ allowed | ✗ allowed | ✗ allowed |
| REPEATABLE READ (snapshot) | ✓ | ✓ | ✓ in Postgres / ✗ in MySQL† | ✗ allowed |
| SERIALIZABLE | ✓ | ✓ | ✓ | ✓ |

†MySQL InnoDB's REPEATABLE READ prevents phantoms via gap locks. Postgres' RR (snapshot isolation) doesn't prevent write skew.

### The four anomalies

#### 1. Dirty read
T1 reads data written by T2 that hasn't committed yet. If T2 rolls back, T1 used invalid data.

```
T1: BEGIN; UPDATE account SET balance=0 WHERE id=1;  -- still inside T1
T2: SELECT balance FROM account WHERE id=1;          -- reads 0 (dirty)
T1: ROLLBACK;                                         -- T2 acted on phantom value
```

Preventable at all real-world isolation levels (Postgres has no READ UNCOMMITTED).

#### 2. Non-repeatable read
T1 reads a row twice in the same transaction; T2 modifies it in between. T1 sees different values.

```
T1: SELECT balance FROM account WHERE id=1;  -- sees 100
T2: UPDATE account SET balance=50; COMMIT;
T1: SELECT balance FROM account WHERE id=1;  -- sees 50
```

Prevented at REPEATABLE READ and above.

#### 3. Phantom read
T1 runs the same query twice; T2 inserts/deletes rows that match the predicate. T1 sees different row sets.

```
T1: SELECT COUNT(*) FROM bookings WHERE room=5 AND day='Jan 1';  -- 0
T2: INSERT INTO bookings (room, day) VALUES (5, 'Jan 1'); COMMIT;
T1: SELECT COUNT(*) FROM bookings WHERE room=5 AND day='Jan 1';  -- 1
```

In Postgres RR (snapshot isolation), phantoms can't be observed in *reads* (snapshot is fixed). But they can lead to write skew (see below).

In MySQL RR, gap locks prevent phantoms during the transaction.

#### 4. Write skew (the senior question)
Two transactions read the same data, each makes a decision based on what they saw, both write — and the combination violates a constraint that **wouldn't have been violated by either alone**.

Classic example: doctor on-call.

```
Constraint: at least 1 doctor must remain on call.
Initial: Alice and Bob both on call.

T1 (Alice goes off):
  SELECT count(*) FROM oncall WHERE status='on';  -- sees 2 ✓
  UPDATE oncall SET status='off' WHERE name='Alice';
T2 (Bob goes off):
  SELECT count(*) FROM oncall WHERE status='on';  -- sees 2 ✓ (T1 not yet committed)
  UPDATE oncall SET status='off' WHERE name='Bob';
COMMIT both → no doctor on call. Constraint violated.
```

**Only SERIALIZABLE prevents write skew.** Snapshot isolation (Postgres RR) doesn't — both transactions see the snapshot before either wrote.

Other write-skew examples:
- Bank account: husband and wife each transfer money out, neither overdrafts alone but together they do
- Meeting room booking: two users book the same slot via different paths
- Inventory: two orders deplete a single remaining item

### MVCC (Multi-Version Concurrency Control)

Both Postgres and MySQL InnoDB use MVCC:
- Each write creates a **new version** of the row (tagged with a transaction ID / commit timestamp)
- Readers see the version visible to their snapshot — they never block on writers
- Writers may block on writers (depending on isolation level and locks)

**Postgres specifics:**
- Each row tuple has `xmin` (transaction that created it) and `xmax` (transaction that deleted/updated it)
- The transaction snapshot says which xmins are visible
- Old versions are reclaimed by **VACUUM** (autovacuum runs periodically)
- Without vacuum: table and index bloat, slowdowns

**MySQL InnoDB specifics:**
- Each row has `DB_TRX_ID` (creator) and `DB_ROLL_PTR` (pointer to undo log)
- Old versions are in the **undo log**, not in the table
- Cleanup is automatic; no `VACUUM`
- Purge thread reclaims undo log space after no snapshot needs it

### Snapshot Isolation vs Serializable

**Snapshot Isolation (SI)**: each transaction sees a consistent snapshot of the DB at its start. Reads never block. Writes detect direct conflicts (write-write on the same row).

**Serializable**: as if all transactions ran one at a time. Postgres uses **Serializable Snapshot Isolation (SSI)** — snapshot isolation + dependency tracking that aborts transactions whose interleavings could violate serializability.

In SSI, transactions don't block; they sometimes abort with `serialization_failure` (code 40001). **The application must retry.**

### Postgres isolation levels in practice

```sql
-- Default: READ COMMITTED
SHOW transaction_isolation;  -- read committed

BEGIN ISOLATION LEVEL REPEATABLE READ;
  -- snapshot fixed at this point
  -- every SELECT sees the same snapshot
COMMIT;

BEGIN ISOLATION LEVEL SERIALIZABLE;
  -- snapshot + SSI dependency tracking
  -- may abort on commit with serialization_failure
COMMIT;
```

Notes:
- Postgres does **not** support READ UNCOMMITTED (it's an alias for READ COMMITTED)
- REPEATABLE READ in Postgres = snapshot isolation
- SERIALIZABLE has overhead (predicate tracking, SIREAD locks) but no row locks beyond standard

### MySQL InnoDB isolation in practice

```sql
SELECT @@TRANSACTION_ISOLATION;  -- REPEATABLE-READ (default)

SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

- Default is **REPEATABLE READ**
- Phantoms prevented by **next-key locks** (record + gap)
- Causes more blocking than Postgres RR
- Serializable adds shared locks to every read → high contention

### Common misconceptions

- "Postgres REPEATABLE READ = MySQL REPEATABLE READ" — **they're different**. Postgres is snapshot-only; MySQL uses gap locks.
- "Higher isolation is always safer" — yes, but also slower and may cause aborts (Serializable) or blocking (MySQL)
- "Serializable means slow" — Postgres SSI is often surprisingly cheap because of optimistic detection
- "MVCC means no locks" — writers still acquire row locks; readers just don't block writers
- "Setting Serializable globally is fine" — many ORMs and apps don't handle `serialization_failure` retries

### Interview traps

1. **Write skew** — most candidates can't define it. Memorize the doctor-on-call example.
2. **Postgres RR vs MySQL RR** — different! Always specify which engine.
3. **`SELECT FOR UPDATE` upgrades isolation** — at RC, a `FOR UPDATE` blocks concurrent writes and *reads-for-update* on the same row → effectively raises consistency for that row
4. **Aborts on commit at SERIALIZABLE** — interviewer asks "how do you handle a commit error?" Retry the whole transaction.
5. **Phantom vs non-repeatable** — phantom = new rows match my predicate; non-repeatable = same row's data changed.

---

## Real examples

### Example: handle SERIALIZABLE retries (Postgres)

```javascript
async function withRetry(fn, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (err.code === '40001' /* serialization_failure */
       || err.code === '40P01' /* deadlock_detected */) {
        await new Promise(r => setTimeout(r, 50 * (1 << i))); // exponential backoff
        continue;
      }
      throw err;
    }
  }
  throw new Error('TX_RETRY_EXHAUSTED');
}
```

### Write skew — preventing it

Option 1: SERIALIZABLE
```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
  SELECT count(*) FROM oncall WHERE status='on';
  -- ... update ...
COMMIT;
```

Option 2: Lock the rows you're depending on
```sql
BEGIN;
  SELECT * FROM oncall WHERE status='on' FOR UPDATE;  -- locks all currently-on rows
  UPDATE oncall SET status='off' WHERE name='Alice';
COMMIT;
```

Option 3: Materialize the constraint into a single row
```sql
-- Single row "oncall_count" that all transactions must update
UPDATE counters SET oncall_count = oncall_count - 1 WHERE name='oncall' AND oncall_count > 1;
```

### Inventory — phantom-safe via row lock

```sql
BEGIN;
  UPDATE inventory SET qty_on_hand = qty_on_hand - 1
  WHERE product_id = 42 AND qty_on_hand > 0;
  -- If 0 rows affected: out of stock; ROLLBACK
COMMIT;
```

Conditional UPDATE is atomic; no need for higher isolation.

### Reservation system — preventing double booking

```sql
-- BAD: SELECT then INSERT race
SELECT COUNT(*) FROM bookings WHERE room=5 AND day='Jan 1';  -- 0
INSERT INTO bookings ...

-- GOOD: unique constraint
CREATE UNIQUE INDEX ON bookings (room, day);
INSERT INTO bookings (room, day) VALUES (5, 'Jan 1')
  ON CONFLICT (room, day) DO NOTHING;
-- Check rows affected
```

The unique constraint enforces serialization at the DB level — no isolation level upgrade needed.

---

## Common interview questions

1. Name the four isolation levels and the anomalies each prevents.
2. What is a dirty read? Phantom read? Non-repeatable read? Write skew?
3. Difference between Postgres RR and MySQL RR.
4. What is MVCC? How does Postgres implement it?
5. What is VACUUM and why is it needed?
6. What is Serializable Snapshot Isolation (SSI)?
7. How would you prevent double booking of a hotel room?
8. How does Postgres handle two concurrent UPDATEs on the same row at READ COMMITTED?
9. When would you use SERIALIZABLE in production?
10. What's the difference between `SELECT FOR UPDATE` and isolation levels?
11. Explain write skew with an example.
12. What happens if VACUUM doesn't run?

---

## Detailed answers

### 1. Levels and anomalies
See table at top. Memorize it.

### 2. Anomalies
See definitions above. Use the doctor-on-call example for write skew.

### 3. Postgres RR vs MySQL RR
- Postgres RR = pure snapshot isolation; phantoms can occur *between* a read and a subsequent write decision (manifesting as write skew)
- MySQL RR = snapshot + gap locks → blocks INSERTs that would create phantoms during your transaction
- Postgres is more concurrent (no gap locks) but allows more anomalies; MySQL is more correct under RR but blocks more

### 4. MVCC
Each row write creates a new tuple version. Readers see the version visible to their snapshot. In Postgres, tuples have `xmin`/`xmax`. Snapshot = set of transaction IDs visible. Readers don't block writers, writers don't block readers — only writer-writer conflicts can block.

### 5. VACUUM
Postgres-specific: old tuple versions (dead tuples) accumulate; VACUUM reclaims their space, updates statistics, and the visibility map. Without it: table/index bloat, slower scans, index-only scans fail. Autovacuum handles routine work; manual `VACUUM FULL` rebuilds the table (locks it).

### 6. SSI
Postgres' SERIALIZABLE level. Tracks read/write dependencies between concurrent transactions. If the schedule of commits could lead to a non-serializable outcome, one transaction is aborted with `serialization_failure`. The application must retry. Cheap when conflicts are rare; expensive (in retries) when not.

### 7. Double booking
- Unique constraint on (resource, slot) → enforces at DB level, no race possible
- Or: `SELECT FOR UPDATE` on the slot row + check availability + insert reservation, all in one transaction
- Discuss trade-off: unique constraint is simpler; FOR UPDATE handles more flexible logic (e.g., overlapping intervals)

### 8. Two concurrent UPDATEs at RC
```
T1: UPDATE accounts SET x=x+1 WHERE id=5;  -- acquires row lock
T2: UPDATE accounts SET x=x+1 WHERE id=5;  -- waits for T1's lock
T1: COMMIT;  -- releases lock; T2 re-reads the latest row and applies its update
```
T2 sees the latest committed version *of that row* (called "read latest" within RC). This is **not** a snapshot — RC re-fetches the row when blocked.

### 9. When to use SERIALIZABLE
- Business invariants that span multiple rows / queries
- Doctor-on-call, fraud detection, complex inventory rules
- Low-frequency hot paths where retry cost is acceptable
- Default to RC for most workloads; escalate only where needed

### 10. FOR UPDATE vs isolation
`FOR UPDATE` is a row lock; isolation levels are global rules for the transaction. Even at RC, `FOR UPDATE` serializes access to a specific row. You can mix them.

### 11. Write skew
See doctor-on-call example. Key signal: both transactions read overlapping data, each makes a decision based on what they saw, both write, the combination violates an invariant.

### 12. No VACUUM
- Dead tuples accumulate → table bloat (10x size possible)
- Indexes bloat
- Sequential scans get slower (more pages to read)
- Index-only scans degrade (visibility map stale)
- Transaction ID wraparound: catastrophic — Postgres goes read-only to prevent ID overflow. Autovacuum prevents this; if it can't keep up, monitor `pg_stat_user_tables.n_dead_tup`.

---

## Practical coding examples

### Postgres concurrent counter — RC + conditional UPDATE
```sql
UPDATE counters SET val = val + 1 WHERE name = 'orders';
```
At RC, this is safe: row lock serializes concurrent updates. No application-level retry needed.

### Postgres at RR — observe snapshot
```sql
-- Session A
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT * FROM accounts WHERE id=1;  -- balance=100

-- Session B
UPDATE accounts SET balance=50 WHERE id=1;
COMMIT;

-- Session A (still in same TX)
SELECT * FROM accounts WHERE id=1;  -- still balance=100 (snapshot fixed)
COMMIT;
```

### Detect bloat (Postgres)
```sql
SELECT relname, n_live_tup, n_dead_tup,
       round(n_dead_tup::numeric / NULLIF(n_live_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
ORDER BY dead_ratio DESC LIMIT 10;
```

### MySQL — see the InnoDB transactions
```sql
SHOW ENGINE INNODB STATUS\G
-- TRANSACTIONS section shows all open transactions, locks held, lock waits
```

### Repeating non-repeatable read demo
```sql
-- Postgres
BEGIN;  -- defaults to RC
SELECT balance FROM accounts WHERE id=1;  -- 100
-- (another session commits a change to 50)
SELECT balance FROM accounts WHERE id=1;  -- 50  -- non-repeatable
COMMIT;
```

---

## Common mistakes

- Assuming RR everywhere prevents phantoms (Postgres RR doesn't, write-skew-wise)
- Forgetting to retry on `serialization_failure` at SERIALIZABLE
- Long transactions at RR → snapshot held forever → bloat
- Mixing autocommit with intended transactions
- Using SELECT then INSERT (race) instead of unique constraint or upsert
- Not understanding that `FOR UPDATE` at RC re-reads the row after waiting (this is correct behavior, but surprises folks expecting snapshot)
- Setting global isolation to SERIALIZABLE without measuring retry rate

---

## Senior engineer discussion points

- **Why most apps run at READ COMMITTED**: throughput; explicit row locks for the few critical paths
- **The cost of long transactions**: Postgres can't vacuum dead tuples newer than the oldest open transaction
- **Postgres `idle_in_transaction_session_timeout`** — kill stale connections to allow vacuum
- **MVCC vs lock-based**: Oracle, Postgres, MySQL InnoDB are MVCC; SQL Server can do both; older systems were lock-based
- **CockroachDB / Spanner**: distributed Serializable using truetime / Hybrid Logical Clocks
- **Read-your-writes guarantees** across replicas — sticky sessions or read-from-primary
- **Eventual consistency models** in NoSQL — Cassandra, DynamoDB consistency tunables
- **Why some teams default to SERIALIZABLE in Postgres**: simpler reasoning + retry on conflict is acceptable cost; many fintechs do this

---

## Revision notes

- 4 levels: RU < RC < RR < SER
- 4 anomalies: dirty / non-repeatable / phantom / write skew
- Postgres RR = snapshot isolation (no phantoms in reads, but write skew possible)
- MySQL RR = snapshot + gap locks (phantoms blocked)
- SERIALIZABLE (Postgres SSI) = snapshot + abort-on-conflict; **must retry on 40001**
- MVCC: each write creates a new version; readers don't block writers
- Postgres needs VACUUM; MySQL InnoDB doesn't (undo log)
- Write skew = both read, both decide, both write, invariant breaks — **only SERIALIZABLE prevents**
- Long transactions = bloat (Postgres)
- For double-booking: prefer UNIQUE constraint over isolation hacks
