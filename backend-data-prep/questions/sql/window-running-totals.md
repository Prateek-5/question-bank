# Window Functions — Running Totals & Frame Clause

## Source / Origin
- LeetCode #534, #585, #1321, #1709 "Biggest Window Between Visits".
- Stratascratch "running 7-day average revenue", "cumulative installs per region".
- Real prod: bank-statement balances, retention dashboards, anomaly detection.

## Why this question matters in interviews
Running totals are the most-asked window-function variant. Candidates who haven't seriously used window functions reach for self-joins (`O(N²)`) or app-side loops. The window solution is `O(N log N)` (sort) and reads like English. The interviewer is checking both:

1. Can you write `SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` without thinking?
2. Can you explain **why** the frame clause matters, and what the default frame is?

Bonus probe: "what's the difference between `ROWS` and `RANGE`?" Most candidates can't articulate it. Senior candidates can — and know which one bites them on duplicate-timestamp data.

## Concepts involved

### Syntax to lock in
```sql
-- Cumulative sum
SELECT date, amount,
       SUM(amount) OVER (ORDER BY date
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM   txns;

-- 7-day moving sum
SELECT date, amount,
       SUM(amount) OVER (ORDER BY date
                         ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7d
FROM   txns;

-- Partitioned running total (per account)
SELECT account_id, date, amount,
       SUM(amount) OVER (PARTITION BY account_id ORDER BY date
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS balance
FROM   txns;

-- RANGE vs ROWS (matters with duplicates)
SUM(x) OVER (ORDER BY date ROWS  BETWEEN 1 PRECEDING AND CURRENT ROW)   -- ±1 row
SUM(x) OVER (ORDER BY date RANGE BETWEEN '1 day' PRECEDING AND CURRENT ROW)  -- ±1 day worth of rows
```

### Edge cases / interview traps
1. **Default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`**, **only if** you have `ORDER BY` inside `OVER`. Without ORDER BY → frame is the full partition (so SUM = grand total).
2. **`ROWS` vs `RANGE`.** ROWS counts physical rows; RANGE counts logical values. With duplicate dates and ROWS, you pick "the row before this one"; with RANGE, you grab all rows at the same date. Different answers.
3. **`ROWS BETWEEN N PRECEDING AND CURRENT ROW` requires ORDER BY in OVER.** Forget that and you get a parse error.
4. **Frame with no PARTITION BY** spans the entire result set. Add `PARTITION BY` to scope per group.
5. **`SUM` over a window doesn't collapse rows.** That's the whole point. Don't add `GROUP BY` "just in case".
6. **`SUM(amount) OVER (PARTITION BY x)` with no ORDER BY** gives the partition total on every row — handy for ratios.
7. **NULL in the order-by column** — Postgres puts NULL at the end of ASC. The running total "jumps" when the NULL-rows come in. Often the source of confusion.
8. **Performance:** the planner does one sort per `OVER (PARTITION BY ... ORDER BY ...)` combo. Two different window definitions = two sorts. Reuse where possible.

## Mental Model

```
   txns:  date         amount        Frame: ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

   2025-01-01    100   ┐
   2025-01-02     50   │ ← when at row 3, frame covers rows 1..3
   2025-01-03     75   │
   2025-01-04   −20   ┘   running_total for row 3 = 100 + 50 + 75 = 225

   Frame: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW (sliding window of 3)

   row 3 frame = rows 1..3 (100+50+75=225)
   row 4 frame = rows 2..4 (50+75-20=105)
```

A window function says "for each row, look at a defined neighborhood and compute". The frame clause defines the neighborhood. Run the neighborhood through `SUM`/`AVG`/`MIN`/`MAX`/`COUNT` — get a running aggregate that doesn't collapse the row.

## Why interviewers care
- **Set-thinking under pressure** — window functions are how seniors avoid `O(N²)` self-joins.
- **Frame clause** is the deep cut; default-frame ignorance is the #1 source of subtle wrong answers.
- **ROWS vs RANGE** distinguishes someone who's read the manual from someone who's only googled examples.

## Common beginner confusion
- "Why is my running total wrong with `RANGE`?" — duplicate keys; ROWS is usually what you want.
- "Why is my `SUM(amount) OVER (ORDER BY date)` the full total?" — default frame is `RANGE UNBOUNDED PRECEDING`, *with ORDER BY*. Without ORDER BY it's the whole partition.
- "Do I need GROUP BY?" — no; windows preserve rows.
- "Will it use my index?" — for a window function, you need an index that can satisfy the (PARTITION BY, ORDER BY) sort.

## Brute force approach
Self-join: `SELECT t1.date, SUM(t2.amount) FROM txns t1 JOIN txns t2 ON t2.date <= t1.date GROUP BY t1.date`. Correct, `O(N²)`. For 10K rows already a slug; for 10M it's hours.

## Optimal approach
Single sort + one streaming pass with the window-aggregate algorithm. The engine maintains a running aggregate state, slides the frame, updates the state in O(1) (for SUM/COUNT) or O(log K) (for MIN/MAX with a deque). Total: `O(N log N)` from the sort, `O(N)` for the window evaluation.

## Solution (SQL)

```sql
CREATE TABLE txns (
  id         SERIAL PRIMARY KEY,
  account_id INT,
  ts         TIMESTAMPTZ,
  amount     NUMERIC
);
INSERT INTO txns (account_id, ts, amount) VALUES
 (1,'2025-01-01', 100),
 (1,'2025-01-02',  50),
 (1,'2025-01-03',  75),
 (1,'2025-01-04', -20),
 (2,'2025-01-01', 200),
 (2,'2025-01-03', -50);
```

```sql
-- Per-account running balance + 3-day moving average
SELECT
  account_id, ts, amount,
  SUM(amount) OVER (
    PARTITION BY account_id ORDER BY ts
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS balance,
  AVG(amount) OVER (
    PARTITION BY account_id ORDER BY ts
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  ) AS avg_3
FROM txns
ORDER BY account_id, ts;
```

Expected output:

```
 account_id |     ts     | amount | balance | avg_3
────────────┼────────────┼────────┼─────────┼───────
     1      | 2025-01-01 |  100   |   100   | 100.0
     1      | 2025-01-02 |   50   |   150   |  75.0
     1      | 2025-01-03 |   75   |   225   |  75.0
     1      | 2025-01-04 |  -20   |   205   |  35.0
     2      | 2025-01-01 |  200   |   200   | 200.0
     2      | 2025-01-03 |  -50   |   150   |  75.0
```

## Step-by-step dry run

After sorting by (account_id, ts):

```
Frame state for SUM, account 1:
  Row 1 (100):    frame = {100}.                   balance = 100.
  Row 2 (50):     frame = {100, 50}.               balance = 150.
  Row 3 (75):     frame = {100, 50, 75}.           balance = 225.
  Row 4 (-20):    frame = {100, 50, 75, -20}.      balance = 205.
  --- partition boundary (account_id changes) ---
  Row 1 (200):    frame = {200}.                   balance = 200.
  Row 2 (-50):    frame = {200, -50}.              balance = 150.

Frame state for AVG_3 (3-row sliding), account 1:
  Row 1:          frame = {100}.                   avg = 100.
  Row 2:          frame = {100, 50}.               avg = 75.
  Row 3:          frame = {100, 50, 75}.           avg = 75.
  Row 4:          frame slides; drop 100, add -20. frame = {50, 75, -20}. avg = 35.
```

One pass per window definition. Linear streaming algorithm.

## How to think aloud in the interview
1. *"This screams window function — running total without collapsing rows. Standard idiom: `SUM(...) OVER (ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`."*
2. *"I add `PARTITION BY account_id` so the running sum resets per account."*
3. *"I'm explicit about the frame — `ROWS BETWEEN ... ` — because the default `RANGE` frame behaves weirdly with duplicate timestamps."*
4. *"For the moving average, change the frame to `ROWS BETWEEN N PRECEDING AND CURRENT ROW`. Two window definitions = two sorts, but for `(account_id, ts)` they share."*
5. *"At scale I'd want an index on `(account_id, ts)` so the window's required sort is free."*

## Important takeaways
- Window functions = aggregate without collapse.
- Frame clause **defaults** to `RANGE UNBOUNDED PRECEDING` when ORDER BY is present; full partition otherwise.
- Prefer **ROWS** over **RANGE** unless you specifically want value-based ranges.
- `PARTITION BY` resets the running aggregate per group.
- Sort-driven plan; index on `(partition_cols, order_cols)` makes it free.
- See `backend-data-prep/sql/02-advanced-sql.md` "Window functions" for full theory.

## Variants
1. **Running max / min** — `MAX(price) OVER (PARTITION BY symbol ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` for "all-time high". Useful for trailing stops.
2. **Frame with FOLLOWING** — `ROWS BETWEEN CURRENT ROW AND 6 FOLLOWING` for "next 7 days outlook".
3. **EXCLUDE clause** — `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW EXCLUDE CURRENT ROW` for "preceding 6 only" (Postgres 11+).

## Revision notes

> **Window running total cram block**
> - `SUM(x) OVER (PARTITION BY p ORDER BY o ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`.
> - Default frame is `RANGE UNBOUNDED PRECEDING` (if ORDER BY) — NOT what you usually want.
> - Always specify `ROWS BETWEEN ... AND ...` explicitly.
> - ROWS = physical rows; RANGE = logical values; duplicates bite RANGE.
> - PARTITION BY = reset-the-aggregate boundary.
> - `OVER ()` with no ORDER BY → frame = whole partition → SUM = total.
> - Window preserves rows; never add GROUP BY.
> - Cost: one sort per distinct (PARTITION BY, ORDER BY) combo.
> - Index `(p, o)` makes the sort free.
