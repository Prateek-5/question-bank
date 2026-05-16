# Isolation Levels & MVCC

## Intuition first — read this before anything else

Before any formalism, hold this picture in your head:

**Two cashiers, one inventory.** Imagine a store with exactly one Nintendo Switch left on the shelf. Two cashiers — Alice and Bob — each have a customer who wants it. They both glance at the shelf at the same moment (count = 1), both nod "yes we have it in stock", both ring up the sale, both promise delivery. You just sold the same console twice. Notice nothing weird happened from *each cashier's individual point of view*. Each one did a perfectly correct read-then-write. The bug is in the **interleaving**, not in either transaction alone. That is the entire reason isolation levels exist.

**The snapshot vs. reality problem.** When you walk into a coffee shop and look at the pastry case, you form a mental snapshot: "two croissants left". You decide to grab one after ordering. While you order, somebody else takes the last two. When you reach for yours, reality has moved on, but your *snapshot* hasn't. The database faces this exact problem with every transaction: it can show you a consistent snapshot (cheap, fast, but possibly stale by the time you write) OR it can show you reality (always correct, but expensive — readers have to wait for writers). Isolation levels are the dials that pick the trade-off.

**Why interviewers care so much:** correctness under concurrency is the *one* property that web frameworks, ORMs, and language runtimes cannot fix for you. It lives in the database. If you don't reason about it explicitly, you ship silent corruption.

### Progressive build — from one transaction to chaos

1. **One transaction, no concurrency.** Trivially correct. This is the world a junior engineer pretends to live in.
2. **Two transactions, never overlap in time.** Still trivially correct — they happened serially.
3. **Two transactions overlap, but touch *different* rows.** Almost always fine. MVCC engines handle this without blocking.
4. **Two transactions overlap, both *read* the same rows.** Always fine. Readers never conflict with readers.
5. **Two transactions overlap; one reads, one writes the same row.** First anomaly territory: dirty read / non-repeatable read.
6. **Two transactions overlap; both write the same row.** Lost update territory. The database typically serializes this via a row lock.
7. **Two transactions overlap; both read the same range; both insert into it.** Phantom territory.
8. **Two transactions overlap; both read overlapping data, both make a decision, both write *different* rows that collectively break an invariant.** Write skew — the senior-level final boss.

Levels 1-3 are free. Level 4 is free. Levels 5-8 are where every production bug you've debugged lives.

---

## Why this matters in backend interviews

- **The single highest-signal "do you understand databases?" question.** Interviewers ask this to filter senior from mid-level engineers.
- **Every concurrent-update bug** in production traces back to an isolation-level misunderstanding.
- **System design**: you'll be asked "what isolation level for this?" — the answer should be backed by reasoning, not defaults.
- **Senior signal**: most candidates know READ COMMITTED vs SERIALIZABLE but can't explain *write skew*. That's the discriminator.

---

## Why interviewers care

- They are testing your **reasoning about anomalies**, not your memory of a table. Anyone can recite four levels; few can explain *which anomaly* a given level still allows and *why*.
- They want to see you **pick a tradeoff**: stronger isolation costs throughput, sometimes correctness via aborts the app must retry. The senior answer is "it depends, here is how I'd decide".
- They want to see **first-principles thinking**: can you derive that snapshot isolation prevents non-repeatable reads but allows write skew, without looking it up?
- They want to see **production literacy**: do you know what `VACUUM`, `40001`, `idle_in_transaction_session_timeout` mean operationally?

## Common beginner confusion

- **"SERIALIZABLE means the database runs transactions one at a time."** Not literally. It means the final state must be *equivalent to* some serial order. The DB can still execute them concurrently — it only aborts schedules that aren't equivalent to any serial order.
- **"REPEATABLE READ prevents phantom reads."** It depends. **ANSI standard:** no. **Postgres RR (snapshot isolation):** phantoms are invisible to reads inside the snapshot, but the write that would have been a phantom can still cause write skew. **MySQL InnoDB RR:** yes, gap locks block phantom inserts entirely.
- **"`SELECT FOR UPDATE` in autocommit mode is fine."** It's worse than useless — the lock is released the instant the statement returns, before you do the follow-up `UPDATE`. The whole point is to hold the lock across multiple statements *inside* a transaction.
- **"My ORM hides this so I don't have concurrency bugs."** Wrong. The ORM hides the *SQL*, not the *concurrency semantics*. `User.find(1); user.balance -= 10; user.save()` reads, computes, and writes through an interactive language — between `find` and `save` someone else may have updated the row. The race exists regardless of ORM.
- **"MVCC means there are no locks."** MVCC means *readers don't block writers and writers don't block readers* for the read path. Writers still take row-level X locks against other writers.
- **"Higher isolation = always safer."** Higher isolation may **convert silent corruption into noisy aborts**. That is safer in principle, but the application must implement retry. If you set SERIALIZABLE globally without retry logic, you turn corruption bugs into 5xx errors.

---

## First principles — what is serializability really?

A **schedule** is the actual interleaving of operations from concurrent transactions, e.g., `R1(x), R2(x), W1(x), W2(x), C1, C2`.

A schedule is **serializable** if it produces the same final state as *some* serial schedule (all of T1 then all of T2, OR all of T2 then all of T1). Note: not necessarily either particular order — any serial order that yields the same result counts.

**Conflict graph (precedence graph):** draw a node per transaction. Draw an edge `Ti → Tj` whenever Ti executes an operation that conflicts with a later operation of Tj (write-read, read-write, or write-write on the same item). A schedule is **conflict-serializable** if and only if this graph has no cycles. This is the formal correctness criterion every DB textbook proves.

**Two-phase locking (2PL)** is the canonical algorithm guaranteeing serializability:
- *Growing phase*: a transaction may acquire locks but not release any.
- *Shrinking phase*: a transaction may release locks but not acquire any new ones.
- *Strict 2PL*: all locks are held until commit/rollback.

Strict 2PL produces serializable schedules because once Ti releases a lock on x, no later acquire can interleave back and break the order. The cost: lots of blocking.

**Why MVCC was invented:** 2PL kills throughput because readers block writers and writers block readers. In OLTP workloads with many short reads and few writes, this is catastrophic. MVCC observes: if every write *creates a new version* instead of overwriting, readers can safely consume old versions in parallel with writers creating new ones. The price: extra storage (Postgres dead tuples, InnoDB undo log), and *write skew* anomalies that pure 2PL would have prevented.

**Postgres' SSI** (Serializable Snapshot Isolation) is the clever synthesis: keep MVCC's read-never-blocks behaviour, but track read/write dependencies between live transactions, and abort one if the dependency graph forms a "dangerous structure" that could produce a non-serializable outcome. Cheap when conflicts are rare, expensive (in aborts/retries) when not.

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

## Mental Model for each isolation level

### READ UNCOMMITTED — "the open notebook"
Imagine your colleague is editing a document. You're peeking over their shoulder while they type. You see partial sentences, typos, half-formed thoughts. They might delete it all in a second. That's READ UNCOMMITTED — you can see writes that haven't been committed yet. Postgres treats this as READ COMMITTED (it doesn't bother implementing it). Practically: never use it intentionally.

### READ COMMITTED — "the published version"
You only see things your colleague has saved. But every time you look, you might see a *newer* saved version than the last time you looked. The world updates around you. Each statement gets a fresh snapshot.

Analogy: refreshing a news website. Each page-load shows the latest, but the same article you reloaded might be different now.

This is the default in Postgres and most modern DBs. It prevents dirty reads cheaply, accepts non-repeatable reads as a normal cost of life.

### REPEATABLE READ — "the photograph"
You take a photograph of the document the moment your transaction starts. For the rest of your transaction, every time you "look at the document" you actually look at your photo. Reality moves on; you don't see it. When you write, you write *against* your photo (and the DB checks at commit whether anyone else changed what you depended on).

In Postgres this is **snapshot isolation**. In MySQL InnoDB, it's snapshot + gap locks (which extends the photograph into the *range* of rows, so phantoms also can't appear).

### SERIALIZABLE — "as if we took turns"
The strongest level. The database promises that whatever sequence of transactions you ran concurrently, the outcome is identical to *some* sequential ordering. It doesn't say which one — just that one exists.

Two implementation flavors:
- **Lock-based** (MySQL SERIALIZABLE): every read takes a shared lock. Lots of blocking.
- **Optimistic / SSI** (Postgres): snapshot isolation plus dependency tracking; abort on detected risk.

The mental model: you submit your transaction, the DB pretends it stood in line, and if standing in line wouldn't have given the same answer, the DB tells you "try again".

### SNAPSHOT (named level in some DBs, conceptual in Postgres)
A specific implementation strategy: at transaction start, capture a list of "transactions visible to me" and only see rows whose creating txnid is in that set. Reads never block. Writes use first-committer-wins to resolve write-write conflicts. This is what Postgres RR actually *is*. SQL Server exposes SNAPSHOT and SERIALIZABLE as separate named levels; Oracle's SERIALIZABLE is actually snapshot isolation.

The key takeaway: "snapshot isolation" is a real, well-defined level distinct from ANSI SERIALIZABLE — and it is *not* serializable (allows write skew). Different DBs label it differently.

---

### The four anomalies

#### 1. Dirty read
T1 reads data written by T2 that hasn't committed yet. If T2 rolls back, T1 used invalid data.

```
T1: BEGIN; UPDATE account SET balance=0 WHERE id=1;  -- still inside T1
T2: SELECT balance FROM account WHERE id=1;          -- reads 0 (dirty)
T1: ROLLBACK;                                         -- T2 acted on phantom value
```

Preventable at all real-world isolation levels (Postgres has no READ UNCOMMITTED).

**Timeline (T1 writes uncommitted, T2 reads, T1 rolls back):**

```
time →
T1:  |--BEGIN--|--UPDATE bal=0--|------------|--ROLLBACK--|
                                  ^
T2:                  |--BEGIN--|--SELECT bal--|--(saw 0)--|--use that 0!--|
                                  reads uncommitted dirty value
```

**Why it's dangerous in plain English:** T2 paid out a refund based on "balance is 0", but T1's rollback means the customer's true balance was always 100. T2 just gave away money based on a value that never officially existed.

**The fix:** every modern DB prevents dirty reads even at READ COMMITTED. Postgres goes further — it doesn't even *implement* READ UNCOMMITTED. So in practice this anomaly is solved-by-default. You should still be able to define it on demand because interviewers ask.

#### 2. Non-repeatable read
T1 reads a row twice in the same transaction; T2 modifies it in between. T1 sees different values.

```
T1: SELECT balance FROM account WHERE id=1;  -- sees 100
T2: UPDATE account SET balance=50; COMMIT;
T1: SELECT balance FROM account WHERE id=1;  -- sees 50
```

Prevented at REPEATABLE READ and above.

**Timeline (T1 reads the same row twice; T2 changes it between):**

```
time →
T1:  |--BEGIN--|--R(bal)=100--|------------------------|--R(bal)=50--|--COMMIT--|
                                                         ^ value changed!
T2:                |--BEGIN--|--W(bal=50)--|--COMMIT--|
```

**Why it bites real code:** consider this Python:
```python
balance = db.execute("SELECT balance FROM account WHERE id=1").scalar()
# ... 20 lines of business logic computing fees and limits ...
if balance >= fee:
    db.execute("UPDATE account SET balance = ? WHERE id=1", balance - fee)
```
At READ COMMITTED, the balance you computed against may already be stale by the time you write. Your `balance - fee` arithmetic uses a number that no longer exists in the database. Welcome to the lost-update flavor of non-repeatable read.

**The fix:** REPEATABLE READ pins your snapshot at transaction start, so the second SELECT inside T1 still returns 100. (T2's update still happens; you just don't see it until your transaction ends.)

#### 3. Phantom read
T1 runs the same query twice; T2 inserts/deletes rows that match the predicate. T1 sees different row sets.

```
T1: SELECT COUNT(*) FROM bookings WHERE room=5 AND day='Jan 1';  -- 0
T2: INSERT INTO bookings (room, day) VALUES (5, 'Jan 1'); COMMIT;
T1: SELECT COUNT(*) FROM bookings WHERE room=5 AND day='Jan 1';  -- 1
```

In Postgres RR (snapshot isolation), phantoms can't be observed in *reads* (snapshot is fixed). But they can lead to write skew (see below).

In MySQL RR, gap locks prevent phantoms during the transaction.

**Timeline (phantom row appears between two predicate queries):**

```
time →
T1:  |--BEGIN--|--COUNT(*)=0--|--------------------|--COUNT(*)=1--|--COMMIT--|
                                                    ^ ghost row appeared
T2:               |--BEGIN--|--INSERT match--|--COMMIT--|
```

**Phantom vs non-repeatable — the precise distinction:**
- *Non-repeatable read*: a specific row I already read has had its values changed.
- *Phantom*: rows matching my predicate have appeared or disappeared. The row I previously read may be unchanged.

You can defeat non-repeatable reads with a row-level snapshot. Phantoms require *range* protection — either MVCC over the predicate (Postgres SSI tracks read sets) or a lock on the gap between index keys (MySQL InnoDB next-key locks).

**Where it bites:** any "check before insert" pattern — booking systems, username uniqueness, unique-by-business-rule constraints not enforced by an index.

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

**Timeline (the doctor-on-call write skew — the classic):**

```
time →
T1 (Alice):  |--BEGIN--|--R: count=2 (Alice & Bob on)--|--W: Alice=off--|--COMMIT--|
                                                           ^ decision based on stale view
T2 (Bob):    |--BEGIN--|--R: count=2 (Alice & Bob on)--|--W: Bob=off--|--COMMIT--|
                                                           ^ also based on stale view

Final state: count=0. Constraint violated. Both transactions saw "2 on call" — true at the moment of read — and each decided "I can go off". Neither wrote the same row. Neither would have failed alone. They corrupted the invariant *together*.
```

**Why this is the senior question:** every junior knows lost update (two writers to the same row, one is silently overwritten). Write skew is different — *two writers to different rows* whose decisions both depended on a shared read set. There is no row-level lock that catches it because no row is contested. Only:
1. **Materialize the constraint** into a single row (counter table) that both transactions must update — converts write skew into write-write conflict.
2. **Lock the read set** explicitly with `SELECT ... FOR UPDATE`.
3. **Use SERIALIZABLE** and let SSI detect the read/write cycle and abort one.
4. **Use a unique index / exclusion constraint** that physically forbids the bad state.

**Conflict graph view of write skew:**
```
   T1 reads {Alice, Bob}, writes Alice
   T2 reads {Alice, Bob}, writes Bob

   Edges in the conflict graph:
     T1 --(rw on Bob)--> T2     (T1 read Bob, T2 wrote Bob)
     T2 --(rw on Alice)--> T1   (T2 read Alice, T1 wrote Alice)

   Cycle! → not serializable. SSI detects this and aborts one.
```

#### 5. Lost update (the read-modify-write hazard)
Not in the original ANSI list, but the most common bug in interactive code. T1 reads a value into application memory, T2 reads the same value, T1 writes back its modification, T2 writes back its (separately computed) modification. T2 silently obliterates T1's work.

```
T1: SELECT qty FROM stock WHERE id=5;   -- 100
T2: SELECT qty FROM stock WHERE id=5;   -- 100
T1: UPDATE stock SET qty=99 WHERE id=5; -- T1 thinks it's 100→99
T2: UPDATE stock SET qty=99 WHERE id=5; -- T2 also thinks it's 100→99 (lost!)
COMMIT both → qty=99 (should be 98)
```

**Timeline:**
```
time →
T1:  |--R(100)--|----------|--compute 100-1=99--|--W(99)--|--COMMIT--|
T2:        |--R(100)--|---------|--compute 100-1=99--|--W(99)--|--COMMIT--|

Two decrements applied; only one took effect. One sale "disappeared".
```

**Fixes:**
- **SQL-level decrement** instead of read-modify-write: `UPDATE stock SET qty = qty - 1 WHERE id=5 AND qty > 0`. The DB serializes the row lock automatically.
- **`SELECT ... FOR UPDATE`** to acquire the lock before reading.
- **Optimistic concurrency**: include a `version` column and `WHERE version = $expected_version` in the UPDATE.

The ORM trap: `obj.qty -= 1; obj.save()` is *exactly* a lost-update bug. Most ORMs default to it.

### MVCC (Multi-Version Concurrency Control)

Both Postgres and MySQL InnoDB use MVCC:
- Each write creates a **new version** of the row (tagged with a transaction ID / commit timestamp)
- Readers see the version visible to their snapshot — they never block on writers
- Writers may block on writers (depending on isolation level and locks)

**Version chain — what a row really looks like under MVCC:**

```
Row id=42, conceptual versions over time:

   tuple v1                 tuple v2                tuple v3 (current)
  ┌──────────┐    update   ┌──────────┐   update   ┌──────────┐
  │ bal=100  │ ──────────> │ bal=80   │ ─────────> │ bal=50   │
  │ xmin=10  │             │ xmin=20  │            │ xmin=30  │
  │ xmax=20  │             │ xmax=30  │            │ xmax=∞   │
  └──────────┘             └──────────┘            └──────────┘
   (dead)                   (dead)                  (live)

Visibility rules (Postgres):
- A reader at snapshot {txnids visible} sees the *first* version where xmin is visible AND xmax is not visible.
- Reader running at txnid=25 (sees txns ≤ 25) → sees v2 (bal=80): xmin=20 visible, xmax=30 NOT visible.
- Reader running at txnid=35 → sees v3 (bal=50).
- Reader running at txnid=15 → sees v1 (bal=100).

This is how three different transactions can each "see" a different value of the *same row* with no locks involved.
```

**Bridge:** the version chain explains *every* MVCC behavior — why readers don't block, why long transactions cause bloat (old versions can't be pruned while someone might still see them), why VACUUM exists (Postgres reclaims dead tuples once no snapshot needs them), and why write-write conflicts still need locks (only one transaction can be the next `xmin`).

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

## Interview storytelling — "tell me about a concurrency bug"

Interviewers love when you can frame a race in narrative form: *here is the scenario, here is the race, here is the anomaly, here is the fix and its cost*. Practice the cadence.

**Story 1 — the double-booked meeting room.**
> "Two users hit 'book' on the same room/time slot. Each runs a transaction that SELECTs to check availability (count = 0), then INSERTs. Both see 0 because each is on its own snapshot. Both INSERTs succeed. That's a phantom + write skew compound."
>
> "Three fixes, ranked by elegance:
> 1. Add a `UNIQUE(room_id, slot_start)` index. The second INSERT fails at the DB. Cheapest. Doesn't need isolation upgrade.
> 2. SERIALIZABLE — Postgres SSI will detect the read/write dependency cycle and abort one with `40001`. App must retry.
> 3. `SELECT ... FOR UPDATE` on the slot's parent row before INSERT. Pessimistic, works at any isolation level."

**Story 2 — the disappearing decrement.**
> "Inventory page shows 'qty=10'. Two customers click Buy at the same instant. Each Node process reads qty=10, computes qty-1=9, UPDATEs qty=9. Two sales, one decrement. Classic lost update."
>
> "Fix: do the math in SQL — `UPDATE items SET qty = qty - 1 WHERE id=? AND qty > 0`. The row lock the DB takes for the UPDATE serializes the two writes. Check rows-affected; if zero, it's sold out."

**Story 3 — the silent overdraft.**
> "Joint account at $100. Wife withdraws $80, husband withdraws $80, simultaneously. Each transaction: SELECT total balance (sees $100, both valid), check $100 >= $80, INSERT withdrawal of $80. Two separate INSERTs into a `transactions` table. No row lock conflict. End state: balance = -$60."
>
> "This is write skew. The fix at Postgres is SERIALIZABLE or to lock the parent account row with FOR UPDATE before reading. MySQL InnoDB RR doesn't fix it either — gap locks only stop phantoms on indexes."

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
