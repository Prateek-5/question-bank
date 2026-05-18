# Reproduce a dirty read and explain why every modern DB defaults to preventing it

## Source / Origin
- Canonical isolation-level interview opener.
- Appears in Joe Hellerstein's Berkeley CS186 and every "Database Internals" book (Petrov chapter 5).
- Companion: `backend-data-prep/sql/07-isolation-levels.md` (anomaly definitions).

## Why this question matters in interviews
Dirty read is the entry-level isolation anomaly. Interviewers ask it not because they expect you to have seen one in Postgres (you can't; Postgres has no real READ UNCOMMITTED), but because they want you to **define the anomaly precisely**, **draw the timeline**, and **explain why a refund computed against a rolled-back balance is catastrophic in fintech**. A confident definition here sets you up for the rest of the isolation conversation. A muddled definition kills the round in 60 seconds.

## Concepts involved

### Syntax to lock in

```sql
-- MySQL InnoDB (only place you can actually demonstrate a dirty read)
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- Postgres: silently maps to READ COMMITTED, you cannot demonstrate
BEGIN ISOLATION LEVEL READ UNCOMMITTED;  -- behaves as RC
```

The anomaly in symbol form:
```
W1(x), R2(x), A1     -- T1 writes x, T2 reads x, T1 aborts
                     -- T2 has acted on a value that was never committed
```

### Edge cases / interview traps

1. **Postgres can't reproduce it.** Postgres maps RU to RC. If asked to demonstrate, you must switch to MySQL with `SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED`.
2. **Dirty read is not the same as non-repeatable read.** Dirty read = T2 sees *uncommitted* data; non-repeatable = T2 sees two different *committed* values. Don't conflate.
3. **"Reading your own writes" is not a dirty read.** Inside a single transaction, you must see your own uncommitted writes. The anomaly is specifically *cross-transaction* visibility.
4. **A dirty read is only an anomaly when T1 rolls back.** If T1 ultimately commits, T2's read is correct (just out-of-order). The semantic violation only materialises on T1's ROLLBACK.
5. **"Cascading rollback" trap.** If T2 reads T1's dirty data and writes based on it, T1's rollback should logically force T2 to abort too. RU systems don't do this — they let T2 commit garbage. This is why RU is forbidden in finance.
6. **It's the cheapest anomaly to prevent.** Just don't show readers another transaction's pre-commit buffers. MVCC engines do this for free; lock-based engines need an S lock on the row before reading.

## Mental Model

The **"glance at a half-typed text message"** mental model. Imagine you're peeking over a colleague's shoulder as they compose a message: "I quit, effective immedi—". You panic, run to HR. Two seconds later they delete the half-message and type "I love this job." You acted on something that never officially existed.

```
   T1 writer's keyboard:     "balance = 0"   "ROLLBACK"
   T2 reader's eyeballs:                 ↑ peeked here, saw 0
                                                              ↑ T1 says "nope, was 100 all along"
   T2's downstream effect:   already refunded $100 to user
```

The fix is trivial: the engine should never expose pre-commit buffers across transactions. That's it.

## Why interviewers care

- They're checking your **vocabulary precision** — can you say "the read of uncommitted data" without slipping into "the read of stale data"?
- They want to see you **distinguish dirty read from non-repeatable read** — these are different anomalies with different remedies.
- They want a **production answer**, not a textbook one: "RU is forbidden in finance; Postgres doesn't even implement it; the only place you see this in 2025 is a misconfigured analytics dashboard with `nolock` hints in SQL Server."

## Common beginner confusion

- "Dirty read means stale data." No — it means **uncommitted data**. Stale data is non-repeatable read or just a snapshot at an old timestamp.
- "Postgres at RU shows dirty reads." It doesn't; Postgres silently runs RU as RC.
- "Read uncommitted is fast." The speedup vs RC is negligible because RC is already MVCC-based.
- "Dirty read is harmless if I retry." If T1 rolled back and T2 already issued a refund, the side effect is already in the world.

## Brute force approach

"Just take an S lock on every row before reading." Works (this is the lock-based RC implementation) but kills throughput — every reader blocks writers and vice versa. This is exactly what MVCC was invented to avoid.

## Optimal approach

MVCC: every write creates a *new tuple version* tagged with the writer's XID. Readers see only versions whose `xmin` is *committed* and visible in their snapshot. Pre-commit versions are invisible to readers from other transactions. Zero locks on the read path. This is what every modern OLTP engine (Postgres, InnoDB, Oracle, SQL Server with `READ_COMMITTED_SNAPSHOT=ON`) does.

## Solution

```sql
-- ============================================================
-- Dirty read demo (MySQL InnoDB; Postgres won't reproduce it)
-- ============================================================

-- Setup
CREATE TABLE accounts (id INT PRIMARY KEY, balance INT);
INSERT INTO accounts VALUES (1, 100);

-- Session A (T1: tries to set to 0, then rolls back)
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;
UPDATE accounts SET balance = 0 WHERE id = 1;
-- DO NOT COMMIT YET

-- Session B (T2: reads while T1 is mid-flight, at RU)
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1;
-- → 0   ← dirty read! Real committed value is still 100.
COMMIT;

-- Session A: changes its mind
ROLLBACK;

-- Session A again: real value
SELECT balance FROM accounts WHERE id = 1;
-- → 100  ← T2's read of 0 was never reality.

-- ============================================================
-- Prevention: just run at READ COMMITTED (Postgres default)
-- ============================================================
BEGIN ISOLATION LEVEL READ COMMITTED;
SELECT balance FROM accounts WHERE id = 1;
-- → 100 always; never sees T1's uncommitted 0
COMMIT;
```

## Step-by-step dry run

T1/T2 timeline:

```
time →

T1 (writer):   |--BEGIN--|--UPDATE bal=0--|----------------------|--ROLLBACK--|
                          (uncommitted)                            (undone)
                                            ^
T2 (reader):                |--BEGIN--|----|--SELECT bal=0--|--issue refund--|--COMMIT--|
                                            ^ dirty: read T1's pre-commit buffer
                                                              ^
                                                              T2 paid out $100 of fictional money

Final DB state:  balance = 100   (T1 rolled back; T1's "0" was never real)
External effect: refund of $100 already sent — irreversible.
```

Allowed at: READ UNCOMMITTED. Prevented at: READ COMMITTED and above. Postgres never allows it (RU is aliased).

The fix in one line: **default Postgres behaviour, or set MySQL session to RC+**.

## How to think aloud in the interview

> "Dirty read is the anomaly where T2 reads data T1 wrote but never committed. The timeline is W1, R2, A1 — T1 writes, T2 reads, T1 aborts. T2 acted on a value that never officially existed. The danger isn't the read itself — it's the downstream effect: T2 might have already issued a refund, sent a webhook, fired a Kafka event. Postgres prevents this for free at the default level; it doesn't even implement READ UNCOMMITTED. MySQL InnoDB will reproduce it if you explicitly opt into RU. The fix is to run at READ COMMITTED, which every modern OLTP DB does by default. No locks needed — MVCC just makes pre-commit tuple versions invisible to other transactions."

## Important takeaways

- Dirty read = read of *uncommitted* data; danger materialises if the writer rolls back.
- Only allowed at READ UNCOMMITTED. Postgres has no real RU.
- MVCC makes prevention free — no locks on the read path.
- Distinguish from non-repeatable read (same row, two different committed values) and read skew (two rows, mutually inconsistent committed values).
- In finance, RU is forbidden by policy regardless of throughput claims.

## Variants

1. **"Reproduce it in Postgres" — trap.** You can't. The interviewer is testing whether you know this. Reply: "Postgres aliases RU to RC; this requires MySQL or SQL Server with `READ UNCOMMITTED`/`NOLOCK`".
2. **"Show me a dirty read across replicas."** Different problem — that's *read-your-writes* / replica lag, not isolation level. Worth flagging as a related-but-distinct concept.
3. **"Why doesn't Postgres implement RU?"** Because MVCC's RC is already as fast as RU would be — no read locks either way. Implementing RU would be code complexity for zero benefit.
4. **"SQL Server `NOLOCK` hint" variant.** SQL Server's `WITH (NOLOCK)` is RU-on-one-query — still produces dirty reads. Senior interviewers love asking about this because so many DBAs ship it as a "performance fix" and silently corrupt reports.

## Revision notes

> **dirty-read — 60 second recap**
> - W1(x), R2(x), A1 — T2 read T1's uncommitted write; T1 rolled back; T2 acted on a value that never existed.
> - Allowed at READ UNCOMMITTED only. Postgres can't reproduce — RU aliases to RC.
> - Prevented by MVCC (free) — pre-commit tuple versions invisible to other tx snapshots.
> - Danger = side effects T2 already emitted (refund, webhook).
> - Cousin: SQL Server `WITH (NOLOCK)` produces dirty reads per-query.
> - Distinguish from non-repeatable read and read skew.
