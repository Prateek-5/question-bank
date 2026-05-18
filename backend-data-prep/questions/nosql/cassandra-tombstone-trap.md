# Cassandra: Tombstone trap — gc_grace_seconds, range tombstones

## Source / Origin
- Senior operations question. Asked at every Cassandra-shop interview after the basics.
- Concept reference: `backend-data-prep/nosql/05-dynamodb-cassandra.md`.

## Why this question matters in interviews
Tombstones are Cassandra's biggest production footgun. Delete-heavy workloads (queues, TTL-driven tables) accumulate tombstones, blow past `tombstone_warn_threshold`, and **kill query performance** before you notice. Senior signal: you understand the LSM model, what `gc_grace_seconds` does, why you **don't use Cassandra as a queue**, and how to fix high-tombstone tables.

## Concepts involved

### Syntax to lock in

```sql
-- Tombstone created on DELETE
DELETE FROM events WHERE user_id = ? AND event_id = ?;

-- Row tombstone (deletes a clustering row)
-- Range tombstone (deletes a range)
DELETE FROM events WHERE user_id = ? AND event_id > ? AND event_id < ?;

-- Partition tombstone
DELETE FROM events WHERE user_id = ?;

-- TTL — creates a tombstone at expiry
INSERT INTO events (user_id, event_id, body) VALUES (?, ?, ?) USING TTL 86400;

-- gc_grace_seconds (default 10 days)
ALTER TABLE events WITH gc_grace_seconds = 864000;

-- Inspect (admin)
nodetool cfstats keyspace.events | grep -i tombstone
```

### What a tombstone is

A tombstone = a marker row "this key was deleted at time T". It must live **across the cluster** for `gc_grace_seconds` so a delayed replica doesn't resurrect deleted data (Last-Write-Wins relies on this). Compaction merges SSTables and drops tombstones whose age > `gc_grace_seconds`.

### Edge cases / interview traps

1. **Read scan walks tombstones.** `SELECT ... LIMIT 50` may read 1000 tombstones to find 50 live rows. Default `tombstone_failure_threshold` (100K) aborts the query.
2. **Cassandra-as-queue anti-pattern.** Insert + delete + insert + delete = ever-growing tombstone count.
3. **TTL = automatic tombstone factory.** Long-TTL collections quietly accumulate.
4. **Range tombstones** can shadow rows that haven't been inserted yet (until compaction).
5. **`gc_grace_seconds` too low** → zombie data (deleted rows resurrect if replica was offline >gc_grace).
6. **`gc_grace_seconds` too high** → tombstones linger; performance degrades.
7. **Hinted handoff window** is part of why gc_grace defaults to 10 days.
8. **Compaction lag** keeps tombstones alive even after gc_grace; check `nodetool compactionstats`.

## Mental Model

> Cassandra writes are **append-only** (LSM tree). DELETE is just another append: a tombstone row. The actual data + the tombstone live together in SSTables until compaction merges them and drops the tombstone — but only if the tombstone is older than `gc_grace_seconds`.

```
   Timeline:
   t=0   INSERT row R                 → SSTable_A:  R (live)
   t=10  DELETE row R                 → SSTable_B:  R-tombstone(t=10)
   t=20  Read R                       → merge A+B → tombstone wins → "not found"
                                       (read still pays the cost of reading both)
   t=30  Compaction runs              → SSTable_C contains only the tombstone
   t=10d Compaction runs (gc_grace)   → tombstone dropped; SSTable_D empty for that key

   Read amplification during the 10-day window:
     "give me last 50 events" might scan 5000 rows (4950 tombstones, 50 live)
```

## Why interviewers care

- Tests **LSM literacy** — you know what compaction is and why.
- Tests **production failure modes** — tombstone overruns kill queries.
- Tests **anti-pattern recognition** — Cassandra is not a queue.

## Common beginner confusion

- "DELETE frees space immediately." It doesn't — adds a marker.
- "TTL is free." Each expiry generates a tombstone.
- "I can lower `gc_grace_seconds` to clean up faster." Yes, but risks zombie data; only safe if replicas are reliably online.
- "Tombstones don't affect reads." They do — reads merge live rows + tombstones at query time.
- "Compaction runs immediately after delete." It runs on schedule; bigger SSTables = later compaction.

## Brute force approach

`SELECT ... LIMIT 50` and hope. With heavy deletes, you might be paginating through tombstones. Crash with `TombstoneOverwhelmingException`. Don't.

## Optimal approach

Three layers of defense:
1. **Schema design**: don't model Cassandra as a queue. Use time-bucketed tables and drop old buckets with `TRUNCATE` or `DROP TABLE` — zero tombstones.
2. **TTL discipline**: bucket TTL data by time; expire whole partitions, not individual rows. Use TWCS (TimeWindowCompactionStrategy).
3. **Operational levers**: tune `gc_grace_seconds`, monitor `tombstone_warn_threshold`, force major compaction when in trouble.

## Solution (CQL + ops)

```sql
-- === Time-bucketed table (recommended for TTL workloads) ===
CREATE TABLE events_by_day (
  user_id  uuid,
  day      date,
  event_id timeuuid,
  body     text,
  PRIMARY KEY ((user_id, day), event_id)
) WITH compaction = { 'class' : 'TimeWindowCompactionStrategy',
                      'compaction_window_unit' : 'DAYS',
                      'compaction_window_size' : 1 }
   AND default_time_to_live = 2592000          -- 30 days
   AND gc_grace_seconds = 86400;               -- 1 day (whole-bucket drop)

-- Old data drops naturally with TTL; whole SSTables expire as a unit.

-- === Anti-pattern: Cassandra as a job queue ===
-- DON'T:
CREATE TABLE job_queue (
  shard int, job_id timeuuid, payload text,
  PRIMARY KEY (shard, job_id)
);
-- workers: SELECT, DELETE → INSERT/DELETE churn → tombstone explosion in days.

-- === Monitoring ===
nodetool cfstats keyspace.events | grep -E 'tombstone|partition'
-- Look for: "Maximum tombstones per slice", "Tombstone scan ratio"

-- === Repair / cleanup ===
nodetool repair                            -- syncs replicas before tombstone GC
nodetool compact keyspace events           -- forced major compaction (last resort)
ALTER TABLE events WITH gc_grace_seconds = 0;   -- DANGEROUS; only if no replica downtime

-- === Range tombstone trap ===
DELETE FROM events WHERE user_id=? AND event_id > ? AND event_id <= ?;
-- Creates a range tombstone covering an interval.
-- All future inserts in that range are SHADOWED until compaction merges.

-- === Avoid: write-then-delete pattern ===
-- BAD:
INSERT INTO state(k, v) VALUES (?, ?);
DELETE FROM state WHERE k=?;
INSERT INTO state(k, v) VALUES (?, ?);
-- Each delete leaves a tombstone; reads walk them.
```

### Operations runbook

```
1. tombstone_warn_threshold breached → investigate scan ratio.
2. Identify table: nodetool cfstats | grep -B1 'Tombstone scan'
3. Schema fix:
   - Move to time-bucketed PK.
   - Switch compaction to TWCS.
   - Plan to drop whole buckets, not individual rows.
4. Operational fix (interim):
   - Force compaction: nodetool compact ks tbl  (heavy I/O)
   - If safe: lower gc_grace_seconds temporarily, run repair, restore.
5. Verify: rerun nodetool cfstats; tombstone scan ratio should drop.
```

## Step-by-step dry run

```
Table: events, daily TTL=86400, no bucketing, SizeTieredCompactionStrategy.

t=0d   100K events inserted with TTL=86400.
t=1d   100K events have expired → 100K tombstones in SSTables.
       Compaction hasn't merged yet.
t=2d   200K events expired total. 200K tombstones.
       Query: SELECT * WHERE user_id=? ORDER BY event_id LIMIT 50;
       → reader scans 4000 rows: 3950 tombstones + 50 live.
       → tombstone_warn_threshold (1000) trips a log warning.
t=5d   500K tombstones. Query latency 10× baseline.
       tombstone_failure_threshold (100K) starts aborting queries.

FIX:
   Migrate to events_by_day with PK = ((user_id, day), event_id).
   Use TWCS with 1-day window.
   When day rolls, the whole SSTable for that day's partition expires together.
   At t+TTL, the SSTable is dropped entirely — zero per-row tombstones touched on reads.
```

## How to think aloud in the interview

> "Tombstones are how Cassandra implements DELETE without scanning the cluster. They live for `gc_grace_seconds` (default 10 days) so delayed replicas don't resurrect deleted data via last-write-wins.
>
> The trap: every DELETE and every expired TTL row adds a tombstone. Read queries merge live rows + tombstones at query time, so a delete-heavy workload scans more and more tombstones over time. `tombstone_warn_threshold` fires at 1000 per slice; `tombstone_failure_threshold` aborts at 100K.
>
> Anti-pattern: Cassandra as a queue. Repeated INSERT + DELETE churn = tombstone explosion.
>
> Proper fix: time-bucket the partition key by day or hour, and use `TimeWindowCompactionStrategy`. Old buckets expire as whole SSTables, never paying the per-row tombstone cost on reads. For ad-hoc cleanup I might force compaction or lower `gc_grace_seconds` after a successful repair, but those are temporary hacks.
>
> Range tombstones can shadow future inserts in the affected range until compaction merges them. I avoid range deletes unless I know nothing will be written back into that range."

## Important takeaways

- **DELETE = append a tombstone, not free space.**
- **TTL = automatic tombstone factory.**
- **`gc_grace_seconds` (default 10 days)** = how long tombstones must live.
- **Read merges live + tombstones** → walking tombstones is the dominant cost.
- **`tombstone_warn_threshold` 1000 / failure 100K.** Monitor both.
- **Cassandra is NOT a queue.** Time-bucketed partitions + TWCS for TTL workloads.
- **Range tombstones shadow future inserts** in their range.
- **Force compaction** = heavy-handed cleanup, not a fix.

## Variants

1. **TWCS (TimeWindowCompactionStrategy)** for time-series; SSTables expire as units.
2. **LCS (LeveledCompactionStrategy)** for read-heavy; tombstones still accumulate.
3. **`unchecked_tombstone_compaction` flag** to force tombstone-only compactions.
4. **`droppable_tombstone_threshold`** controls when compaction prioritizes tombstone removal.
5. **`tombstone_compaction_interval`** sets minimum age before re-eligible.
6. **Anti-entropy repair (`nodetool repair`)** before reducing gc_grace.

## Revision notes

> **tombstones — 60s recap**
> - DELETE/TTL = append a tombstone. Lives `gc_grace_seconds` (default 10d).
> - Reads merge live + tombstones; tombstones dominate cost in delete-heavy workloads.
> - `tombstone_warn_threshold` 1000 per slice; `tombstone_failure_threshold` 100K aborts.
> - Cassandra is not a queue. Time-bucket partitions + TWCS for TTL.
> - Range tombstones shadow future inserts in the range.
> - Lowering `gc_grace_seconds` = risk of zombie data if replica was offline.
> - Force compaction is last-resort hammer, not a fix.
> - Diagnose: `nodetool cfstats | grep -B1 'Tombstone'`.
