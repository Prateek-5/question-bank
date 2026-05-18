# Gaps and Islands — consecutive runs, missing IDs, login streaks

## Source / Origin
- Itzik Ben-Gan's *T-SQL Window Functions* coined the modern "gaps and islands" framing.
- LeetCode #601 "Human Traffic of Stadium", #1454 "Active Users", #1369 "Get the Second Most Recent Activity".
- Reference: PostgreSQL docs on window functions; Markus Winand's articles.
- Companion doc: `backend-data-prep/sql/04-query-patterns.md` — "Gaps and islands" section.
- Classic prompt: *"Find the longest streak of consecutive days a user logged in."*

## Why this question matters in interviews
Gaps-and-islands is the **window-function fluency test**. It's the second question after top-N-per-group: once the interviewer knows you can do `ROW_NUMBER`, they ask for streaks. The pattern requires a *non-obvious* application of window functions — the "row_number difference trick" — that you either know or you don't. There's no way to bluff it.

This question appears in:
- Login streaks / engagement (analytics teams, growth teams)
- Time-series sensor data (IoT, monitoring)
- Consecutive missing IDs (data quality audits)
- Continuous discount runs / promotional periods (commerce)
- DNA sequence problems (bioinformatics)

If you can write the row-number-difference trick cold, you've passed a real senior bar.

## Concepts involved

### Syntax to lock in

```sql
-- The canonical "islands" pattern: group consecutive rows
-- by row_number_difference.
WITH numbered AS (
  SELECT user_id, login_date,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
  FROM logins
)
SELECT user_id,
       MIN(login_date)   AS streak_start,
       MAX(login_date)   AS streak_end,
       COUNT(*)          AS streak_length
FROM (
  SELECT *, login_date - rn * INTERVAL '1 day' AS grp
  FROM numbered
) g
GROUP BY user_id, grp
ORDER BY user_id, streak_start;

-- Find gaps in a sequence of IDs (1, 2, 4, 5, 7, 8) → gaps at 3, 6.
SELECT id + 1 AS missing_start,
       next_id - 1 AS missing_end
FROM (
  SELECT id, LEAD(id) OVER (ORDER BY id) AS next_id
  FROM things
) t
WHERE next_id > id + 1;
```

### Edge cases / interview traps

1. **Date arithmetic gotchas.** Postgres `date - rn * INTERVAL '1 day'` returns a timestamp; cast appropriately. MySQL uses `DATE_SUB(date, INTERVAL rn DAY)`.
2. **Time zones for "consecutive days"** — bug magnet. A user at UTC+9 logging at 23:00 local sees a different "day" boundary than UTC. Convert to user's local time *before* grouping.
3. **Duplicates within a day** — two logins at 09:00 and 23:00 same day count as one day, not two. `SELECT DISTINCT date(login_at)` first.
4. **Discrete vs continuous.** "Consecutive days" is discrete (gap = >1 day apart). "Continuous sessions" might mean "gap < 30 minutes apart" — different problem, different solution.
5. **Multiple users.** Always `PARTITION BY user_id`. Forgetting this is the canonical interview slip.
6. **Off-by-one in gap detection.** `LEAD(id) > id + 1` means a gap exists; the missing IDs are `id+1 .. next_id-1`.
7. **Tied dates / ties in ORDER BY.** Use a stable second sort column.
8. **Sparse vs dense input.** If your input is `(user, date)` rows only on login days, use the row_number trick. If you have one row per day with a boolean `did_login`, use a different "first/last" approach.

## Mental Model

### The row-number-difference trick

The fundamental insight: for a *consecutive* run of integers, `value - row_number()` is **constant**. For non-consecutive runs, it changes. Group by that constant.

```
Input (user=1):                  rn   date - rn*INTERVAL '1 day'
  date         rn                ───  ─────────────────────────
  2026-01-01   1                  1   2025-12-31     ←┐
  2026-01-02   2                  2   2025-12-31     ←┤ same group
  2026-01-03   3                  3   2025-12-31     ←┘
  2026-01-05   4                  4   2026-01-01     ←┐ new group
  2026-01-06   5                  5   2026-01-01     ←┘
  2026-01-10   6                  6   2026-01-04     ← new group (gap broke it)

GROUP BY (user_id, grp):
  user=1, grp=2025-12-31 → streak 2026-01-01 to 2026-01-03 (3 days)
  user=1, grp=2026-01-01 → streak 2026-01-05 to 2026-01-06 (2 days)
  user=1, grp=2026-01-04 → streak 2026-01-10 to 2026-01-10 (1 day)
```

### The LAG/conditional sum alternative

```
Input:
  rn  date         prev_date    is_new_island   island_id (running sum)
  1   01-01        NULL         1               1
  2   01-02        01-01        0               1
  3   01-03        01-02        0               1
  4   01-05        01-03        1               2   ← gap → new island
  5   01-06        01-05        0               2
  6   01-10        01-06        1               3

is_new_island = (prev_date IS NULL OR date - prev_date > 1) ? 1 : 0
island_id     = SUM(is_new_island) OVER (ORDER BY date)
```

Both approaches give the same answer; pick whichever you can write fastest.

## Why interviewers care

- It's a **non-obvious window-function application** — you either know the trick or don't; no way to derive it under time pressure.
- It generalises to **sessionisation** (web analytics' bread and butter), **outage detection** in monitoring, and **dense reporting** for billing.
- It tests whether you can **think in arithmetic over windowed columns**, not just rank-and-filter.
- The "gaps" twin pattern tests `LEAD` and self-joins — checking your window function toolkit's breadth.

## Common beginner confusion

- *"Use a loop / cursor."* Procedural is always wrong for set-based interview questions; you'll fail the perf bar.
- *"`COUNT(*)` per user."* Counts total login days, not consecutive streak length.
- *"`GROUP BY` adjacent rows."* SQL has no native concept of "adjacent in sort order"; you must construct the group key explicitly.
- *"`MAX(date) - MIN(date)`."* Gives the span, not the consecutive streak. A user logging on day 1 and day 30 has span 30 but streak 1.
- *"Self-join on `date = date + 1`."* Works for "any 2-day streak" but explodes for longer streaks (need recursive CTE).

## Brute force approach

Procedural / loop in application code: pull all logins, sort, iterate, track current streak length, reset on gap. Works, kills the network on large datasets, and shows the interviewer you don't know window functions.

Self-join approach: `JOIN logins l1 ON l2.date = l1.date + 1` finds 2-day pairs; extend recursively. Pre-window-function era. Don't do this in 2026.

## Optimal approach

**Two equivalent patterns:**

### Pattern A — Row-number-difference (recommended)

```sql
WITH per_day AS (
  SELECT DISTINCT user_id, date(login_at) AS d FROM logins
),
numbered AS (
  SELECT user_id, d,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d) AS rn,
         d - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d)) * INTERVAL '1 day' AS grp
  FROM per_day
)
SELECT user_id,
       MIN(d) AS streak_start, MAX(d) AS streak_end,
       COUNT(*) AS streak_length
FROM numbered
GROUP BY user_id, grp;
```

### Pattern B — LAG + conditional running sum

```sql
WITH per_day AS (
  SELECT DISTINCT user_id, date(login_at) AS d FROM logins
),
flagged AS (
  SELECT user_id, d,
         CASE WHEN d - LAG(d) OVER (PARTITION BY user_id ORDER BY d) > 1 OR
                   LAG(d) OVER (PARTITION BY user_id ORDER BY d) IS NULL
              THEN 1 ELSE 0 END AS new_island
  FROM per_day
),
islands AS (
  SELECT user_id, d,
         SUM(new_island) OVER (PARTITION BY user_id ORDER BY d) AS island_id
  FROM flagged
)
SELECT user_id, island_id,
       MIN(d) AS streak_start, MAX(d) AS streak_end,
       COUNT(*) AS streak_length
FROM islands
GROUP BY user_id, island_id;
```

### Finding gaps (missing IDs)

```sql
SELECT id + 1 AS missing_from,
       next_id - 1 AS missing_to
FROM (
  SELECT id, LEAD(id) OVER (ORDER BY id) AS next_id
  FROM orders
) t
WHERE next_id > id + 1;
```

### Longest streak per user

```sql
WITH islands AS (
  -- ... pattern A or B ...
),
streak_lengths AS (
  SELECT user_id, grp, COUNT(*) AS len
  FROM islands
  GROUP BY user_id, grp
)
SELECT DISTINCT ON (user_id) user_id, len
FROM streak_lengths
ORDER BY user_id, len DESC;
```

## Solution (PostgreSQL — full working example)

```sql
-- Setup
CREATE TABLE logins (
  user_id INT,
  login_at TIMESTAMPTZ
);
INSERT INTO logins VALUES
  (1, '2026-01-01 08:00'),
  (1, '2026-01-02 09:00'),
  (1, '2026-01-03 10:00'),
  (1, '2026-01-05 11:00'),
  (1, '2026-01-06 12:00'),
  (1, '2026-01-10 13:00'),
  (2, '2026-01-01 08:00'),
  (2, '2026-01-02 09:00');

-- "All login streaks per user"
WITH per_day AS (
  SELECT DISTINCT user_id, login_at::date AS d FROM logins
),
numbered AS (
  SELECT user_id, d,
         (d - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d))::int) AS grp
  FROM per_day
)
SELECT user_id, MIN(d) AS streak_start, MAX(d) AS streak_end, COUNT(*) AS streak_length
FROM numbered
GROUP BY user_id, grp
ORDER BY user_id, streak_start;

-- Output:
-- user_id | streak_start | streak_end  | streak_length
-- --------+--------------+-------------+--------------
--       1 | 2026-01-01   | 2026-01-03  | 3
--       1 | 2026-01-05   | 2026-01-06  | 2
--       1 | 2026-01-10   | 2026-01-10  | 1
--       2 | 2026-01-01   | 2026-01-02  | 2

-- "Longest streak per user"
WITH per_day AS (SELECT DISTINCT user_id, login_at::date AS d FROM logins),
numbered AS (
  SELECT user_id, d, (d - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d))::int) AS grp
  FROM per_day
),
lengths AS (
  SELECT user_id, COUNT(*) AS len FROM numbered GROUP BY user_id, grp
)
SELECT user_id, MAX(len) AS longest_streak FROM lengths GROUP BY user_id;
```

## Step-by-step dry run

Walking through Pattern A for user_id=1:

```
Step 1: per_day (deduplicated by date):
  (1, 2026-01-01)
  (1, 2026-01-02)
  (1, 2026-01-03)
  (1, 2026-01-05)
  (1, 2026-01-06)
  (1, 2026-01-10)

Step 2: assign rn ordered by d:
  d              rn
  2026-01-01     1
  2026-01-02     2
  2026-01-03     3
  2026-01-05     4
  2026-01-06     5
  2026-01-10     6

Step 3: compute grp = d - rn (treating rn as days):
  d              rn   grp
  2026-01-01     1    2025-12-31  ←┐
  2026-01-02     2    2025-12-31   │ same grp → island 1
  2026-01-03     3    2025-12-31  ←┘
  2026-01-05     4    2026-01-01  ←┐
  2026-01-06     5    2026-01-01  ←┘ island 2
  2026-01-10     6    2026-01-04  ←  island 3 (singleton)

Step 4: GROUP BY (user_id, grp), aggregate:
  (1, 2025-12-31): min=01-01, max=01-03, count=3
  (1, 2026-01-01): min=01-05, max=01-06, count=2
  (1, 2026-01-04): min=01-10, max=01-10, count=1

The longest streak for user 1 is 3 days, from 01-01 to 01-03.
```

The arithmetic insight: for consecutive integers (or dates), `value - position` is constant. The gap at 01-04 jumps `rn` ahead of `d` by one, so the difference shifts, and every row after the gap belongs to a new group.

## How to think aloud in the interview

> "This is a gaps-and-islands problem. The trick is the row-number-difference: for a consecutive run of dates, `date - row_number()` is constant. Where there's a gap, `row_number` advances but the date jumps, so the difference shifts. Group by that difference and you get one group per island.
>
> Setup: I'll dedupe to one row per (user, date) — multiple logins same day don't make two days. Then `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY d)` gives me a per-user counter. The group key is `d - rn::int` — or in Postgres, `d - rn * INTERVAL '1 day'`. Then `GROUP BY user_id, grp` and aggregate `MIN`, `MAX`, `COUNT` per group.
>
> Alternative: use `LAG` to detect 'is this row the start of a new island?' — flag with a `CASE` returning 1 when `d - LAG(d) > 1` — then `SUM` over the window to compute a running island id. Same result, slightly more verbose, sometimes easier to extend when 'consecutive' isn't '1 apart'.
>
> Edge cases to mention: time zones for daily streaks; duplicates within a day; what 'consecutive' means — if the interviewer says 'session = gap < 30 min' that's a different group key based on a session timeout, not row_number difference."

## Important takeaways

- **Row-number-difference trick:** `value - row_number()` is constant inside an island. Group by it.
- **LAG + running-sum trick:** flag new islands with `CASE`, `SUM OVER ORDER BY` to make an island id.
- **Always dedupe before counting consecutive units** — same day twice shouldn't extend the streak.
- **PARTITION BY the grouping key** (user_id, device_id, etc.) — forgetting this is the most common slip.
- **Gaps = LEAD - 1** pattern: `WHERE LEAD(id) > id + 1` exposes missing IDs.
- **Procedural / cursor solutions fail the perf bar** — windows are the only acceptable answer.

## Variants

1. **Sessionisation by timeout.** "A session is a run of events with gaps < 30 min." Replace `d - rn` with `SUM(CASE WHEN ts - LAG(ts) > '30 min' THEN 1 ELSE 0 END) OVER (ORDER BY ts)`.
2. **Active users for N consecutive days.** Filter `streak_length >= N` from the islands query.
3. **Consecutive missing IDs.** `LEAD(id) OVER (ORDER BY id)` and report `id+1 .. next_id-1`.
4. **Continuous discount/promotion runs.** Same pattern; group key is `start_date - row_number * INTERVAL '1 day'`.
5. **Multiple "value" islands** — e.g. consecutive rows where `status = 'open'`. Add `PARTITION BY status` to the row_number, or pre-filter to status='open' rows then apply gaps-and-islands.
6. **Per-day densification first.** If your input is sparse and you need "X days in last 30", join against `generate_series` to fill in non-login days as 0, then apply gaps-and-islands on the dense series.
7. **MySQL 8.0+ syntax.** Same approach, `DATE_SUB(d, INTERVAL rn DAY)`.

## Revision notes

> **gaps-and-islands — 60 second recap**
> - "Streaks of consecutive X."
> - **Trick: `value - row_number()` is constant inside an island.** Group by it.
> - Alt: `LAG` + `CASE` + `SUM OVER` to assign island ids.
> - Always `PARTITION BY` the entity (user_id, sensor_id).
> - **Dedupe before counting** — two logins same day shouldn't extend a streak.
> - Gaps twin: `LEAD(id) > id + 1` exposes missing IDs.
> - Generalises to sessionisation (`gap > timeout`).
> - Procedural cursor approach = junior signal; window functions only.
