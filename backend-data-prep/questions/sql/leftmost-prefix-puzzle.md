# Leftmost-Prefix Puzzle — Composite Index Column Order

## Source / Origin
- Senior interview classic at Atlassian, Walmart Labs, Razorpay.
- Real prod: a 4-column index that doesn't help the most-common query because of column order.

## Why this question matters in interviews
Composite indexes are the **single largest source of "wait, we have an index, why is it slow?" tickets**. The leftmost-prefix rule says: an index `(a, b, c)` can serve queries that filter on `a`, on `a,b`, or on `a,b,c` — but **not** on `b` alone, **not** on `c`, and only partially on `a,c`. Candidates who can't sketch this on a whiteboard ship indexes that double their write cost without helping reads.

The interviewer's deeper goal: probe whether you can **design the index for the query mix**, not the other way around. They'll show you three queries and one index and ask "which queries use it, and how?"

## Concepts involved

### Syntax to lock in
```sql
CREATE INDEX ix_o_ucat ON orders (user_id, category, created_at);

-- Q1: SARGable on (user_id) prefix     → uses index fully for seek + leaf walk.
SELECT * FROM orders WHERE user_id = 42;

-- Q2: SARGable on (user_id, category)  → uses both columns to narrow seek.
SELECT * FROM orders WHERE user_id = 42 AND category = 'book';

-- Q3: SARGable on (user_id, category, created_at) → full prefix
SELECT * FROM orders WHERE user_id = 42 AND category = 'book' AND created_at > '2024-01-01';

-- Q4: gap in prefix → can use user_id only; created_at must filter after fetch
SELECT * FROM orders WHERE user_id = 42 AND created_at > '2024-01-01';

-- Q5: skips the leading column → CANNOT use this index (without skip-scan)
SELECT * FROM orders WHERE category = 'book';

-- Q6: skips the leading column → CANNOT use this index
SELECT * FROM orders WHERE created_at > '2024-01-01';
```

### Edge cases / interview traps
1. **Leftmost-prefix is hard.** No "leftmost prefix with gaps" — the engine seeks the index by walking from leftmost column. If you skip `user_id`, the index ordering is meaningless to the predicate.
2. **Equality vs range vs sort.** An index `(a,b,c)` supports `WHERE a=? AND b=? ORDER BY c` for a single user (a) and category (b) — range scan of `c`. The rule: **all equality columns first, range/sort last**.
3. **Range column kills further prefix usage.** `(a,b,c)` with `WHERE a=? AND b > ? AND c = ?` — only `a` and `b` participate; `c` becomes a post-filter.
4. **Skip-scan (Oracle, MySQL 8.0+) and "index-only scan" tricks** can partially salvage non-prefix queries, but performance is bad for many distinct leading values.
5. **`ORDER BY` matches the index** only if the prefix of ORDER BY columns matches the prefix of the index — including direction.
6. **`SELECT col` not in index** → fetch from heap (extra IO). Cover with INCLUDE (Postgres 11+). See `covering-index-design.md`.
7. **Cardinality matters.** Leading column should be high cardinality for selectivity. Putting `is_deleted` (boolean) first wastes the index.
8. **Multiple single-column indexes vs one composite.** Composite usually wins for AND-predicates with a stable column set; multiple indexes win for OR / variable predicate sets (with bitmap-OR).

## Mental Model

```
   Composite index (user_id, category, created_at):

   user_id  category   created_at
   ───────  ────────   ──────────
        7   audio      2025-01-01     ┐
        7   audio      2025-01-02     │  ← contiguous for user 7
        7   book       2024-12-30     │
        7   book       2025-01-04     │
       42   audio      2024-11-11     ┘
       42   book       2024-12-15
       42   book       2025-02-02

   "WHERE user_id=42 AND category='book'"
   → seek (42,'book',-∞), scan until (42,'book',+∞). ~1-2 ms.

   "WHERE category='book'"
   → category appears scattered across all users; engine has no way to
     jump to all book rows. Falls back to full scan.

   Mental picture: phone book sorted (last, first, middle).
   "Find Smiths" — easy (seek to S).
   "Find people whose first name is John" — useless, John is everywhere.
```

## Why interviewers care
- Index design is **the** intermediate-to-senior DBA skill.
- This is a daily-decision: every new query forces a "do we need a new index, and which columns first?" review.
- Reveals whether the candidate has read the EXPLAIN output of their own code.

## Common beginner confusion
- "An index covers any column it contains" — no, only leftmost prefixes.
- "Order doesn't matter" — order is everything.
- "I'll just create N indexes for N queries" — write amplification + storage explosion. Composite + careful column order is usually better.
- "Skip-scan saves me" — only for very low-cardinality leading columns.

## Brute force approach
One index per column. Works for read perf on single-column predicates but wastes huge amounts of space and slows every write proportionally. Also forces the planner into bitmap-OR / bitmap-AND merges that are slower than a single composite scan.

## Optimal approach
1. Inventory your top-5 queries by call rate.
2. For each, write the WHERE columns in **equality-first, range-last** order.
3. Build the *smallest set* of composite indexes that covers them. Often 2-3 indexes serve dozens of queries.
4. Validate with `EXPLAIN ANALYZE`.

## Solution (SQL)

```sql
CREATE TABLE orders (
  id          BIGSERIAL PRIMARY KEY,
  user_id     INT,
  category    TEXT,
  created_at  TIMESTAMPTZ,
  amount      NUMERIC
);
CREATE INDEX ix_o_ucat ON orders(user_id, category, created_at);
```

Quiz table — which queries use the index?

| Query | Predicate                                            | Uses Index? | How                                   |
|-------|------------------------------------------------------|-------------|---------------------------------------|
| Q1    | `user_id = 42`                                       | Yes         | Full prefix seek on column 1          |
| Q2    | `user_id = 42 AND category = 'book'`                  | Yes         | Seek on columns 1+2                   |
| Q3    | `user_id = 42 AND category = 'book' AND created_at > 'x'` | Yes    | Seek on 1+2; range scan on 3          |
| Q4    | `user_id = 42 AND created_at > 'x'`                   | Partial     | Seek on 1; col 3 post-filter          |
| Q5    | `category = 'book'`                                   | No (or skip-scan) | Leading column not constrained  |
| Q6    | `created_at > 'x'`                                    | No          | Leading column not constrained        |
| Q7    | `user_id IN (1,2,3) AND category='book'`              | Yes         | Multiple index seeks (one per user)   |
| Q8    | `user_id = 42 ORDER BY created_at`                    | Yes         | Seek + walk in index order, no sort   |
| Q9    | `user_id = 42 AND category IN ('a','b') ORDER BY created_at` | Partial | Multiple seeks; ORDER BY may still sort |

## Step-by-step dry run

Q5 `WHERE category = 'book'`:

```
Engine asks: "Can I seek the (user_id, category, created_at) B-tree to all 'book' entries?"
Answer: NO. The B-tree is sorted by user_id first, so 'book' entries are scattered
        across every user's section. Need full scan or skip-scan over distinct user_ids.

Result with MySQL 8.0 skip-scan + ~1K users: 1K index range scans, one per user_id,
each seeking (u, 'book', -∞)..(u, 'book', +∞). Often slower than seq scan.

The real fix: add ix_o_cat (category) or reverse to (category, user_id, ...).
```

## How to think aloud in the interview
1. *"Composite index follows the leftmost-prefix rule — you must constrain columns left-to-right; gaps disable further usage."*
2. *"Best practice: equality columns first, range/sort columns last. So `(user_id, category, created_at)` works for `user=, cat=, date>`."*
3. *"Query Q5 filters on `category` alone — skips the leading `user_id`. Can't use this index without skip-scan, which works only for low-cardinality leading columns."*
4. *"For Q5 specifically, I'd add a second index `(category, user_id, created_at)` only if Q5 is hot enough to justify the write cost."*
5. *"Always verify with `EXPLAIN ANALYZE` — look for 'Index Scan' vs 'Index Range Scan' vs 'Seq Scan'."*

## Important takeaways
- Leftmost-prefix rule: index `(a,b,c)` serves `a`, `(a,b)`, `(a,b,c)` — not lone `b`, lone `c`, or `(b,c)`.
- Equality first, range/sort last in column order.
- Range column ends the prefix.
- `ORDER BY` matches index → no sort step.
- Skip-scan exists but only helps with low-cardinality leading columns.
- See `backend-data-prep/sql/04-indexing.md` "Composite indexes" for theory.

## Variants
1. **Multi-column UNIQUE constraint.** Same prefix rule; design with anticipated query patterns.
2. **Index for `IN(...)` lookups.** Postgres turns small IN-lists into multiple seeks; large IN-lists into hash anti/semi join.
3. **Descending columns.** `INDEX(a, b DESC)` matches `ORDER BY a, b DESC` and `ORDER BY a DESC, b ASC` (reverse-scan).

## Revision notes

> **Leftmost-prefix cram block**
> - Index `(a,b,c)` → serves `a`, `(a,b)`, `(a,b,c)` only.
> - Equality first, range/sort last.
> - Range column = end of prefix.
> - ORDER BY must match index prefix to avoid sort step.
> - Skip-scan helps only for low-card leading columns.
> - Multiple single-col indexes ≠ one composite.
> - Cardinality + selectivity dictate column order.
> - Verify: `EXPLAIN ANALYZE`.
> - Phone book mental model: sorted by (last, first, mid).
