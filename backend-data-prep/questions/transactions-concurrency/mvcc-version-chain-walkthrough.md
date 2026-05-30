# Walk an MVCC version chain in Postgres (xmin / xmax / visibility)

## Source / Origin
- Standard "explain MVCC internals" senior question.
- Reference: Postgres internals doc (<a href="https://www.postgresql.org/docs/current/mvcc-intro.html" target="_blank" rel="noopener noreferrer">https://www.postgresql.org/docs/current/mvcc-intro.html</a>), Bruce Momjian's MVCC slides.
- Concept reference: `backend-data-prep/sql/07-isolation-levels.md`.

## Why this question matters in interviews
Saying "Postgres uses MVCC" is mid-level. **Drawing the version chain** with xmin/xmax/visibility on a whiteboard — and explaining why VACUUM exists, why long transactions cause bloat, and why readers never block writers — is senior. This question separates engineers who've debugged Postgres in production from those who've read the marketing page.

## Concepts involved

### Syntax to lock in

```sql
-- Inspect tuple header (Postgres-specific magic)
SELECT xmin, xmax, ctid, * FROM accounts WHERE id = 1;
-- xmin = creating tx ID; xmax = deleting/updating tx ID; ctid = physical (page, offset)

-- Inspect dead tuples / bloat
SELECT relname, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 10;

-- Force vacuum
VACUUM (VERBOSE) accounts;

-- The "oldest snapshot" that's blocking vacuum
SELECT pid, age(backend_xmin), state, query
FROM pg_stat_activity
WHERE backend_xmin IS NOT NULL
ORDER BY backend_xmin LIMIT 5;
```

### Edge cases / interview traps

1. **Postgres updates are not in-place.** An UPDATE is internally: insert a new tuple, mark the old tuple's `xmax` with your XID. The old tuple stays on the page until VACUUM reclaims it.
2. **HOT updates** (Heap-Only Tuples) — when no indexed column changes, Postgres can chain the new tuple on the same page without touching indexes. Critical optimisation.
3. **MVCC creates bloat.** Every UPDATE = old tuple becomes dead. Without VACUUM, table grows unbounded.
4. **A long-running transaction prevents vacuum of newer dead tuples.** VACUUM can only reclaim tuples whose xmax is older than the *oldest* live snapshot. One idle transaction = global vacuum stall.
5. **xmin/xmax are 32-bit.** Wraparound exists. Autovacuum has wraparound prevention; if it can't keep up, the DB goes read-only ("autovacuum: must be done to prevent wraparound data loss").
6. **InnoDB uses an undo log, not in-place versions.** Old versions stored separately; cleanup is automatic via the purge thread. Postgres needs explicit VACUUM.
7. **`ctid` changes on UPDATE** (unless HOT). Triggers and replication that depend on ctid see different values pre/post-update.

## Mental Model

The **"sticky-note stack on a paper file"** model. Every UPDATE doesn't erase the existing record — it puts a new sticky note on top with the new values, and writes "(superseded at tx 30)" on the old one. Readers from older transactions read the bottom sticky note; newer readers read the top one. A janitor (VACUUM) periodically removes sticky notes nobody can reach.

```
   tuple v1 (oldest)        tuple v2                  tuple v3 (current)
   ┌──────────┐ update     ┌──────────┐ update       ┌──────────┐
   │ bal=100  │ ─────────► │ bal=80   │ ───────────► │ bal=50   │
   │ xmin=10  │            │ xmin=20  │              │ xmin=30  │
   │ xmax=20  │ (deleted)  │ xmax=30  │ (superseded) │ xmax=∞   │ (live)
   │ ctid=A   │            │ ctid=B   │              │ ctid=C   │
   └──────────┘            └──────────┘              └──────────┘

   Visibility rule (Postgres):
     A reader at snapshot S sees a tuple if:
        xmin ∈ S.committed  AND  (xmax = ∞  OR  xmax ∉ S.committed)
     Translation: created by a tx I can see, AND either not deleted or deleted by a tx I can't see.

   Reader at tx=15: sees v1 (xmin=10 ✓, xmax=20 not yet committed in their view) — bal=100
   Reader at tx=25: sees v2 (xmin=20 ✓, xmax=30 not visible) — bal=80
   Reader at tx=35: sees v3 (xmin=30 ✓, xmax=∞) — bal=50
```

This is how three different transactions running concurrently each see a *different* value of the *same row* with **zero locks involved**.

## Why interviewers care

- It's the **mechanism** behind every read-doesn't-block-write claim. Without understanding the version chain, "MVCC" is a buzzword.
- It explains **why long transactions are dangerous in Postgres** — the connection between snapshot age and bloat.
- It maps to operational pain (VACUUM, wraparound, bloat ratios) the candidate likely has or will encounter.

## Common beginner confusion

- "MVCC means no locks." Writers still acquire X locks against other writers. MVCC unblocks the *read-write* paths.
- "Vacuum is just compaction." It's primarily *visibility*: reclaim tuples no snapshot can see. Compaction is a side-effect.
- "Postgres updates rows in place." It doesn't. It inserts a new tuple and marks the old one dead.
- "InnoDB and Postgres MVCC are the same." Both are MVCC, but storage differs: Postgres keeps versions in the heap (needs VACUUM); InnoDB keeps them in the undo log (cleaned automatically).

## Brute force approach

Lock-based concurrency: every read takes a shared lock. Every write needs all readers to release. Throughput collapses. MVCC was invented to fix exactly this.

## Optimal approach

Snapshot-based visibility via xmin/xmax. Reads check tuple headers against their snapshot; never block. Writers acquire row X locks only against other writers. VACUUM reclaims tuples whose xmax is older than every live snapshot.

## Solution

```sql
-- ============================================================
-- Walkthrough: trace a row through three updates
-- ============================================================

CREATE TABLE accounts (id INT PRIMARY KEY, balance INT);
INSERT INTO accounts VALUES (1, 100);  -- tx 10
SELECT xmin, xmax, ctid, * FROM accounts WHERE id=1;
-- xmin=10, xmax=0 (i.e. ∞), ctid=(0,1), balance=100

-- tx 20: deduct 20
BEGIN;
UPDATE accounts SET balance=80 WHERE id=1;
-- Internally: old tuple's xmax := 20 ; new tuple inserted with xmin=20, xmax=0
COMMIT;
SELECT xmin, xmax, ctid, * FROM accounts WHERE id=1;
-- xmin=20, xmax=0, ctid=(0,2)  -- new tuple
-- The old tuple still exists at ctid=(0,1) with xmin=10, xmax=20 — dead.

-- tx 30: deduct 30
BEGIN;
UPDATE accounts SET balance=50 WHERE id=1;
COMMIT;
-- Now three tuples exist on disk:
--   (0,1): xmin=10, xmax=20, balance=100 — dead
--   (0,2): xmin=20, xmax=30, balance=80  — dead
--   (0,3): xmin=30, xmax=0,  balance=50  — live

-- ============================================================
-- Concurrent readers see different versions
-- ============================================================

-- Session A (started before tx 20 committed)
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT balance FROM accounts WHERE id=1;  -- 100 (snapshot pinned at tx ~15)
-- ... tx 20, tx 30 run + commit in other sessions ...
SELECT balance FROM accounts WHERE id=1;  -- still 100 (snapshot)
COMMIT;

-- Session B (started after tx 30 committed)
SELECT balance FROM accounts WHERE id=1;  -- 50 (current)

-- ============================================================
-- VACUUM: reclaim dead tuples
-- ============================================================
VACUUM accounts;
-- Now only the live tuple (0,3) remains.

-- ============================================================
-- The "long transaction blocks vacuum" trap
-- ============================================================

-- Session A: leaves a transaction idle for an hour
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT * FROM accounts WHERE id=1;  -- snapshot pinned

-- Meanwhile session B does 1M UPDATEs on other rows.
-- All 1M old tuple versions are KEPT because session A's snapshot might need them.
-- Result: massive bloat; auto-vacuum can't help until session A commits.
```

Inspecting tuple visibility via `pageinspect`:

```sql
CREATE EXTENSION pageinspect;
SELECT lp, t_xmin, t_xmax, t_ctid
FROM heap_page_items(get_raw_page('accounts', 0));
```

## Step-by-step dry run

Timeline showing concurrent readers and writers:

```
Wall clock     │ tx 10     │ tx 20      │ tx 25 (reader)        │ tx 30      │ tx 35 (reader) │ VACUUM
───────────────┼───────────┼────────────┼───────────────────────┼────────────┼────────────────┼─────────
Heap state:    │ +v1       │ v1.xmax=20 │                       │ v2.xmax=30 │                │ delete v1,v2
               │           │ +v2        │                       │ +v3        │                │
               │           │            │                       │            │                │
v1 (xmin=10,   │ live      │ dead (20)  │ readable (xmax∉snap)  │ dead       │ unreadable     │ reclaimed
xmax=20):      │           │            │ → sees bal=100        │            │                │
               │           │            │                       │            │                │
v2 (xmin=20,   │ —         │ live       │ unreadable (xmin∉snap)│ dead (30)  │ unreadable     │ reclaimed
xmax=30):      │           │            │ unless snap includes  │            │                │
               │           │            │ 20                    │            │                │
               │           │            │                       │            │                │
v3 (xmin=30):  │ —         │ —          │ —                     │ live       │ readable       │ live

Reader at tx 25 with snapshot {10 committed, 20 not committed yet, ...}:
  v1: xmin=10 ✓ committed; xmax=20 ∉ committed-in-snapshot → visible. Returns bal=100.

Reader at tx 35 with snapshot including 10,20,30 committed:
  v1: xmax=20 ∈ committed → invisible.
  v2: xmax=30 ∈ committed → invisible.
  v3: xmin=30 ∈ committed, xmax=∞ → visible. Returns bal=50.

VACUUM later: identifies v1 and v2 as "no snapshot needs them" (oldest snapshot xmin > 30).
              Reclaims their tuple slots.
```

## How to think aloud in the interview

> "Postgres MVCC: every write creates a new tuple version tagged with `xmin` (creator XID) and `xmax` (deleter XID, ∞ if live). An UPDATE is internally an insert of a new tuple plus a stamp of the old tuple's xmax. Readers see tuples whose xmin is committed-in-their-snapshot and whose xmax is not committed-in-their-snapshot.
>
> Two concurrent readers at different snapshots can see two different values of the same row — no locks, no blocking, just header math.
>
> The cost is dead tuples accumulate. VACUUM (autovacuum) reclaims them. The trap: a long-running transaction holds a snapshot that pins all dead tuples newer than its snapshot — autovacuum can't reclaim them. One idle transaction at REPEATABLE READ for an hour can balloon a 1 GB table to 10 GB.
>
> InnoDB does MVCC differently — versions live in the undo log, cleaned automatically by the purge thread. No VACUUM required, but the undo log can blow up under similar conditions."

## Important takeaways

- Every UPDATE = new tuple + xmax stamp on old. Not in-place.
- xmin = creator, xmax = deleter (∞ for live).
- Visibility rule: tuple visible if xmin ∈ snapshot.committed AND xmax ∉ snapshot.committed.
- Readers never block writers via MVCC; writers block other writers.
- VACUUM reclaims dead tuples no snapshot can see.
- Long transactions pin the oldest snapshot → block vacuum → bloat.
- InnoDB: same idea, different storage (undo log + purge thread).
- HOT updates: same-page update when no indexed column changes; doesn't touch indexes.

## Variants

1. **"What's wraparound?"** XID is 32-bit. Postgres compares XIDs modulo 2^31; if half the space is used, it appears in the "future" and breaks visibility. Autovacuum freezes old tuples (rewrites xmin=FrozenXID) to prevent this.
2. **"What blocks vacuum besides long tx?"** Replication slots that haven't advanced (xmin held back), prepared transactions (orphan 2PC).
3. **MySQL undo log analogue.** UPDATE writes the old version to the undo log; current tuple has a pointer (DB_ROLL_PTR) to the undo entry. Reader walks the chain backwards if their snapshot needs an older view.
4. **`VACUUM FULL`** rewrites the entire table, acquiring ACCESS EXCLUSIVE. Blocks all reads. Use `pg_repack` for online repack.
5. **Index visibility map** — bitmap of pages where all tuples are visible-to-all. Enables index-only scans. Updated by VACUUM.

## Revision notes

> **mvcc-version-chain — 60 second recap**
> - UPDATE = new tuple insert + old tuple xmax stamp. No in-place writes in Postgres.
> - xmin = creator XID, xmax = deleter/updater XID (∞ for live).
> - Visibility: xmin ∈ snap.committed AND xmax ∉ snap.committed.
> - Readers and writers don't block each other (only writer-writer can block).
> - VACUUM reclaims dead tuples; required in Postgres.
> - **Long tx = oldest snapshot held = vacuum can't reclaim newer dead tuples = bloat.**
> - InnoDB: versions in undo log, purged automatically; no VACUUM.
> - HOT update: same-page update with no index change; doesn't touch indexes.
> - Wraparound: 32-bit XID; autovacuum freezes old tuples to prevent disaster.
