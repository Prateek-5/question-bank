# Top 80 SDE2 Backend Data-Layer Interview Questions

The 80 questions most often asked at SDE2 / senior backend interviews at product companies (Amazon, Google, Microsoft, Atlassian, Stripe, Razorpay, Swiggy, Flipkart, Uber, Booking, Linkedin, Meta, MongoDB-like shops, etc.).

Each question has a short, **interview-ready answer**. Aim for 60–90 seconds per question out loud.

> Drill format: cover the answer, read the question, speak the answer aloud, then check.

---

## How to use this file (read this first)

This is a **drill book**, not a textbook. You will *not* learn SQL or distributed systems from skimming the answers; you will learn the *vocabulary an interviewer expects you to wield in 90 seconds*. Treat each entry like a flashcard with a whiteboard moment attached.

**The mental loop the file is designed for:**

```
   read question  ──▶  cover the answer  ──▶  speak aloud for 60s
        ▲                                          │
        │                                          ▼
   mark "weak"  ◀──  compare against written ◀── self-grade
```

The written answer is the **floor** — what you must at minimum say to not lose signal. A strong candidate also adds: a real-world example, a trade-off, and a "but actually it depends on…" qualifier. That last part is what separates an SDE2 from an SDE1.

**Three rules for using this list well:**

1. **Don't memorize. Internalize.** If your answer is verbatim the bullet here, the interviewer can tell. Restate it in your own words every time.
2. **Speak it out loud.** Reading silently feels productive but doesn't train the muscle that matters in an interview — your mouth, under pressure.
3. **Time yourself.** 60s is shockingly short. Most candidates ramble past it without realizing. A clean 60s answer signals seniority more than a thorough 3-minute one.

---

## Why interviewers care about these 80

The interviewer is not really asking "do you know what `INNER JOIN` is". They're triangulating four signals at once:

1. **Mental model** — do you describe the *mechanism* (B-tree fanout, MVCC versions, WAL flush) or only the *interface*?
2. **Calibrated trade-offs** — every answer should end with "…but X if Y". Absolutism is junior; qualified preference is senior.
3. **Production instinct** — have you actually seen this in prod, or are you reciting a blog post? Real-world specifics (numbers, failure modes, monitoring) signal experience.
4. **Communication under time pressure** — can you structure a 60-second answer with a clear claim → reason → example shape, or do you ramble?

These 80 questions are dense in signal because each has a "trap" — a common wrong answer that confidently-wrong candidates give. The interviewer is listening for whether you walk into the trap. Knowing the trap is half the battle.

---

## How to think aloud (STAR-lite for technical Q&A)

A great spoken technical answer has a predictable shape. Use this skeleton when you're nervous and your mind blanks:

```
  CLAIM        →   "INNER JOIN keeps only matched rows; LEFT keeps all left rows."
       │
  MECHANISM    →   "Internally it's hash/merge/nested-loop, planner picks based on size & indexes."
       │
  EXAMPLE      →   "Use LEFT when you want every user even if they have no order."
       │
  TRADE-OFF    →   "LEFT can hide bugs — a missing FK looks like a NULL row."
       │
  QUALIFIER    →   "But in OLAP, INNER is the default; LEFT is more for nullable optional relations."
```

**When you don't know:** *do not bluff*. Senior signal is graceful uncertainty:

> "I haven't worked with X directly, but my mental model is Y — does that line up, or should I think about it differently?"

That single sentence often scores higher than a confident wrong answer. It shows you know the edge of your knowledge — a senior trait.

**When to ask clarifying questions:** for any system-design or "design X" question (77–80), always ask:

- Scale (QPS reads vs writes, data volume)
- Read/write ratio
- Consistency requirements (strict, read-your-writes, eventual is fine)
- Latency budget (p50, p99)

Skipping clarification is the #1 way candidates fail design questions. Without numbers, every answer is "it depends" and you can't pick trade-offs.

---

## Cluster index — what each section is testing

| Cluster | Q# | What the interviewer is grading |
|---|---|---|
| SQL — Joins, Subqueries, GROUP BY | 1–10 | Do you understand the *logical model* of SQL, not just the syntax? |
| SQL — Window Functions & CTEs | 11–20 | Can you do analytical SQL without dropping into procedural code? |
| SQL — Indexing | 21–30 | Do you reason about disk I/O, B-tree mechanics, and write amplification? |
| SQL — Query Optimization | 31–40 | Can you read a plan and form a hypothesis from it? |
| SQL — Transactions, Isolation, Locks | 41–50 | Do you understand correctness under concurrency? (Most senior-cut) |
| NoSQL & Distributed Systems | 51–60 | Can you pick the right store and shard wisely? |
| ORM | 61–68 | Do you treat the ORM as a leaky abstraction with known failure modes? |
| Caching & Redis | 69–76 | Do you reason about staleness, eviction, and stampedes? |
| System Design & Senior | 77–80 | Can you compose all of the above into a real system? |

**Suggested drill order if you're behind on prep:** 41–50 (transactions) → 21–30 (indexing) → 31–40 (optimization) → 61–68 (ORM) → 69–76 (caching) → the rest. The first four clusters are where most rejections happen.

---

## Common beginner confusion (skim before drilling)

These are the traps the questions are *specifically designed* to expose. If any of these still feel fuzzy after one read, the related question will catch you in an interview:

- **WHERE vs HAVING** — people who don't know logical execution order say things like "HAVING is just an alias for WHERE on aggregates". Senior answer: HAVING runs *after* GROUP BY because aggregates don't exist until then.
- **Index column order doesn't matter** — wrong. A composite `(a,b,c)` index helps `WHERE a=?`, `WHERE a=? AND b=?`, but *not* `WHERE b=?` alone. Equality → range → sort.
- **ACID = correctness always** — wrong. ACID is per-transaction. Across transactions you still need to pick an isolation level. Default Read Committed allows surprises.
- **REPEATABLE READ is the same everywhere** — Postgres RR ≠ MySQL RR. Postgres is snapshot only; MySQL uses gap locks (blocks phantoms).
- **CAP means pick two** — wrong. Partition tolerance isn't optional. The real choice is what to do *during* a partition: CP or AP. PACELC adds the normal-operation trade-off.
- **N+1 happens at the ORM** — partly true. It happens whenever you loop and query per item, ORM or not. Fix is batching/eager loading, not "switching ORM".
- **Cache stampede is just "lots of misses"** — wrong. It's *correlated* misses, often after deploy or synchronized TTL expiry. The fix is decorrelation (jitter, singleflight), not just more cache.
- **Idempotency = the same response every time** — wrong. It means the same *side effect* every time. Returning a cached response is not enough; the underlying action must be guarded by a key.

If three or more of these are new to you, slow down — read the answers carefully, not just for memorization.

---

## SQL — Joins, Subqueries, GROUP BY (1–10)

> **Cluster intro — the "do you actually understand SQL semantics?" round.**
>
> This section looks easy and is therefore the most dangerous. Every junior knows what a JOIN is; very few can articulate *why* `NOT IN` breaks with NULL, or *what* logical execution order means for alias scoping. Interviewers use this cluster as a filter — getting even one of these wrong tells them you copy-paste SQL without understanding it.
>
> **Mental model to lock in:** SQL is a declarative language with a fixed *logical* execution order (FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT). The physical plan can do whatever, but the *semantics* always behave as if that order is followed. Almost every "weird SQL behavior" question is a logical-order question in disguise.
>
> **Why interviewers care:** SQL semantic bugs are silent. A `NOT IN` with NULL returns "no rows" instead of crashing — so it ships to prod. The interviewer wants to know you'd catch it in code review.
>
> **Common beginner confusion in this cluster:**
> - Believing `WHERE` and `HAVING` are interchangeable (they're not — see Q5).
> - Treating `NULL` as a value instead of "unknown" (breaks `NOT IN`, `=`, `<>` — see Q4).
> - Assuming `LIMIT 1 OFFSET 1` correctly gets "second" (it doesn't handle ties — see Q6).
> - Forgetting `UNION` deduplicates and is expensive (see Q7).
>
> Read each answer twice. The traps are subtle.

**1. What's the difference between INNER JOIN and LEFT JOIN, and when would each be appropriate?**

> *How to think aloud:* start with the set-theoretic intuition (intersection vs left-set), then give a concrete use case, then the gotcha (LEFT JOIN can hide missing FK rows as NULLs — useful or bug-causing depending on intent).

INNER JOIN returns only rows with a match on both sides; LEFT JOIN keeps all rows from the left even when the right has no match (NULL-filled). Use INNER when you want intersection; LEFT when you need every left row plus optional related data (e.g., users + their latest order, where some users have no orders).

**2. Explain anti-joins. Show two SQL ways to write one.**

> *How to think aloud:* the keyword "anti" means "absence". Two idioms exist; one is NULL-safe and the other is a trap. Mention both.

An anti-join returns left rows that have **no** match on the right. Use cases: find churned users, find unmatched records.
```sql
-- Way 1
SELECT u.* FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;
-- Way 2 (NULL-safe, often preferred)
SELECT u.* FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
```

**3. What's the logical order of SQL execution?**

> *How to think aloud:* memorize FROM-WHERE-GROUP-HAVING-SELECT-ORDER-LIMIT as a chant. Then explain *why* it matters: it's the reason aliases work in ORDER BY but not WHERE.

FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT. Aliases from SELECT can be referenced in ORDER BY but not WHERE — because WHERE runs before SELECT.

**4. Why is `NOT IN` dangerous with NULL?**

> *Common mistake:* candidates say "NOT IN is fine, just filter out NULLs". Wrong — the issue is three-valued logic. Mention that NULL means "unknown", and `x NOT IN (1, NULL)` evaluates to "x ≠ 1 AND x ≠ unknown" = NULL.

If the subquery returns any NULL, `NOT IN` evaluates to NULL (unknown), so the row is excluded — typically returning zero rows. Switch to `NOT EXISTS`, which is NULL-safe.

**5. WHERE vs HAVING — what's the difference?**

> *How to think aloud:* tie this back to Q3's execution order. WHERE runs before aggregation exists; HAVING runs after. Then mention: filtering in WHERE is almost always cheaper because it reduces rows before aggregation work.

WHERE filters rows *before* aggregation; cannot reference aggregates. HAVING filters *after* GROUP BY and operates on aggregate or group-key values.

**6. Find the second-highest salary three different ways.**

> *How to think aloud:* mention three approaches and call out which handles ties correctly. The interviewer is testing whether you think about edge cases (two employees with the same top salary) before writing code.

```sql
-- Window
SELECT salary FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) rk FROM emp) t WHERE rk=2;
-- Subquery (no ties)
SELECT MAX(salary) FROM emp WHERE salary < (SELECT MAX(salary) FROM emp);
-- LIMIT/OFFSET (ties dangerous)
SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1;
```
Window with `DENSE_RANK` handles ties correctly.

**7. UNION vs UNION ALL?**

> *Common mistake:* defaulting to `UNION` "just in case". Senior answer: default to `UNION ALL`; only use `UNION` when dedup is semantically required, because dedup costs a sort or hash pass over everything.

UNION concatenates and deduplicates (requires sort/hash). UNION ALL just concatenates — much faster. Default to UNION ALL unless you specifically need dedup.

**8. `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`?**

> *How to think aloud:* three different things, all called COUNT — that's the trap. The discriminating factor is NULL handling and distinct-set computation.

`COUNT(*)` = every row. `COUNT(col)` = non-NULL `col`. `COUNT(DISTINCT col)` = unique non-NULL values (expensive due to hashing/sorting).

**9. What does GROUP BY do under the hood?**

> *How to think aloud:* show that "GROUP BY" is a physical operation with two strategies (hash vs sort). Knowing that hash needs `work_mem` is the kind of detail that signals you've debugged this in prod.

The planner either hash-aggregates (build a hash keyed by group columns; fast for unsorted data) or sort-aggregates (sort by group columns; then aggregate adjacent rows). Hash needs work_mem; sort can spill but uses less memory.

**10. Write a self-join: employees and their managers (both columns from `employees`).**

> *Common mistake:* using INNER JOIN here — that drops the CEO (no manager). Use LEFT JOIN. The interviewer is checking whether you notice the edge case.
```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e LEFT JOIN employees m ON m.id = e.manager_id;
```

---

## SQL — Window Functions & CTEs (11–20)

> **Bridge from previous cluster:** if 1–10 tested whether you understand *set-based* SQL, this cluster tests whether you can do *row-relational* SQL — computations that look at one row in the context of its neighbors. Window functions are the SQL-native answer to "how would I do this without dumping to a loop in Python".
>
> **Mental model:** a window function is a regular aggregate that *doesn't collapse rows*. Instead of producing one row per group, it produces a value per input row, computed over some "window" (frame) around it. Three knobs: `PARTITION BY` (the group), `ORDER BY` (sort within group), `frame` (which rows inside the partition count).
>
> ```
>   partition: ┌──────── user A ────────┐ ┌──── user B ────┐
>   order by:   r1   r2   r3   r4   r5    r1   r2   r3
>                          ▲
>                       current row
>   frame "1 PRECEDING / CURRENT": [r2, r3] ← window slides per row
> ```
>
> **Why interviewers care:** candidates who can't do window functions write awful procedural code in app servers for things that should be one SQL query. Senior signal: you reach for `ROW_NUMBER OVER (PARTITION BY …)` before reaching for a loop.
>
> **Common beginner confusion:**
> - Conflating `ROW_NUMBER`, `RANK`, `DENSE_RANK` (Q11 — they differ in how they handle ties).
> - Using `ROWS` when you wanted `RANGE` for date windows (Q14, Q19).
> - Forgetting `LAST_VALUE` needs an explicit frame to behave intuitively (Q20).
> - Assuming CTEs are an optimization fence in modern Postgres — they aren't, since Postgres 12 (Q17).

**11. ROW_NUMBER vs RANK vs DENSE_RANK?**

> *How to think aloud:* always answer with the canonical example "100, 100, 90" — it instantly demonstrates the three behaviors. Then say *when* you'd pick each.

For salaries 100,100,90: ROW_NUMBER → 1,2,3 (unique); RANK → 1,1,3 (gap); DENSE_RANK → 1,1,2 (no gap). Use ROW_NUMBER for "pick exactly one" per group; DENSE_RANK for "top N with ties sharing rank."

**12. How do you get the top N records per group?**

> *How to think aloud:* this is *the* canonical window-function pattern. Memorize the `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` template. Mention LATERAL as the faster alternative when an index supports the order.
```sql
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) rn FROM orders
) t WHERE rn <= 3;
```
Or via `LATERAL` join — often faster with an index on `(user_id, created_at DESC)`.

**13. Running total per user?**
```sql
SUM(amount) OVER (PARTITION BY user_id ORDER BY ts ROWS UNBOUNDED PRECEDING)
```

**14. 7-day rolling average over events?**
```sql
AVG(value) OVER (ORDER BY day RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW)
```
Use RANGE (logical) not ROWS (physical) for date-based windows so missing days don't shift the window.

**15. Find consecutive login days (gaps and islands)?**

> *How to think aloud:* this is the "gaps and islands" trick. Mention the trick by name — interviewers love that it has one. The trick: `date - ROW_NUMBER()` is constant across consecutive dates, so it becomes a natural group key.
Subtract `ROW_NUMBER()` from each date — consecutive dates yield the same offset, so GROUP BY that offset gives the runs.

**16. What's a recursive CTE? Use case?**

> *How to think aloud:* a recursive CTE = anchor + recursive part + UNION ALL. Mention the killer use cases (org chart, comment threads). Don't write it from scratch in your head — point at the template and explain.

Walks a tree/graph by iterating. Use for org charts, comment threads, dependency graphs, category trees, BOM.
```sql
WITH RECURSIVE tree AS (
  SELECT id, parent_id, 0 AS depth FROM cats WHERE id = $root
  UNION ALL
  SELECT c.id, c.parent_id, t.depth+1 FROM cats c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree;
```

**17. CTE vs subquery — performance?**

> *Common mistake:* "CTEs are always slower because they're optimization fences" — this is *old* (Postgres < 12) folklore. Senior answer: it depends on version; modern Postgres inlines by default.

Modern Postgres (12+) inlines CTEs by default, so performance is similar to subqueries. Use `WITH … AS MATERIALIZED` to pin the boundary. Pre-12 Postgres always materialized — beware on old systems.

**18. What is a LATERAL join and when to use?**

> *How to think aloud:* think of LATERAL as "a subquery that can see the row it's joining to". The killer use case is top-N-per-group with an index.

A `LATERAL` subquery in FROM can reference columns from preceding FROM items. Perfect for top-N-per-group, per-row aggregation, or unnesting:
```sql
SELECT u.id, recent.*
FROM users u
LEFT JOIN LATERAL (SELECT * FROM orders WHERE user_id = u.id ORDER BY created_at DESC LIMIT 3) recent ON true;
```

**19. ROWS vs RANGE in a window frame?**

ROWS = physical row offset. RANGE = logical value-based (requires sortable type and ORDER BY). They differ on ties: ROWS may include only some tied rows; RANGE includes all.

**20. Default frame for window functions?**

Aggregate functions with ORDER BY: `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Without ORDER BY: entire partition. Ranking functions: entire partition. Watch out — `LAST_VALUE` without explicit frame returns the current row.

---

## SQL — Indexing (21–30)

> **Bridge from previous cluster:** windowed analytical SQL helps you *write* a query; indexes determine whether it returns in 10 ms or 10 seconds. The shift is from "what does this query mean?" to "what does this query *cost on disk*?". Every senior backend engineer should be able to predict, within an order of magnitude, how many disk pages a query will touch.
>
> **Mental model — the B-tree as a sorted phone book:**
>
> ```
>            [   root: 1...1M     ]
>           /        |        \
>      [1..100k] [100k..500k] [500k..1M]    ← internal nodes (keys + pointers)
>        / \         / \          / \
>      ...           ...           ...
>     [   leaf pages: keys + row pointers, doubly linked   ]
> ```
>
> Each "node" is one disk page (~8 KB). Fanout is high (hundreds of pointers per page), so 3–5 hops cover billions of rows. *That* is why indexed lookups feel "instant" even on huge tables.
>
> **Why interviewers care:** the indexing cluster separates engineers who think "I'll add an index" (junior) from engineers who think "I'll add a *partial* index on `(status, created_at)` because 90% of rows are archived and we always query open orders by time" (senior). The senior answer reasons about *selectivity, column order, and write cost simultaneously*.
>
> **Common beginner confusion:**
> - "More indexes = faster" — wrong. Each index slows down writes (Q29).
> - "Composite index column order doesn't matter" — wrong. Equality → range → sort (Q22).
> - "An index always gets used if it exists" — wrong, seven reasons it won't (Q25).
> - "UUIDs are fine as PKs because they're unique" — fine in Postgres heap, painful in InnoDB clustered (Q27).
> - "JSONB needs a full-text index" — no, GIN with `jsonb_path_ops` (Q30).

**21. How does a B-tree index work?**

> *How to think aloud:* draw the tree mentally (root → internal → leaf). Mention fanout, page size, and the doubly-linked leaves (which make range scans cheap).

A balanced multi-way tree where each node fits a disk page. Internal nodes hold keys + child pointers; leaves hold keys + row IDs. Fanout is high (hundreds), so 3–5 levels cover billions of rows. Leaves are doubly linked for fast range scans. O(log N) lookup.

**22. Why is the column order in a composite index important?**

> *How to think aloud:* the chant: **Equality → Range → Sort**. Then explain why — a B-tree is sorted lexicographically, so you can only "skip" to a position if the prefix is fully constrained.

A B-tree is sorted lexicographically by (col1, col2, …). The leading column must appear in an equality (or range) for the index to be used. Order columns by: **Equality → Range → Sort**.

**23. Difference between clustered and non-clustered index?**

> *Common mistake:* assuming Postgres has clustered indexes — it doesn't. The `CLUSTER` command does a one-time reorder; it doesn't keep things sorted.

Clustered (InnoDB PK, SQL Server clustered) stores table data physically in PK order — PK lookups are 1 read. Non-clustered (any secondary) stores key → pointer; lookups require an extra hop to the heap. Postgres has no clustered indexes — all are secondary.

**24. What's a covering index / index-only scan?**

> *How to think aloud:* "covering" means the index has *every column you need*, so the DB never touches the heap. Mention the Postgres-specific catch: visibility map must say page is all-visible.

An index that contains every column the query needs. The DB serves the query without touching the table heap. In Postgres, use `INCLUDE` to add non-key columns. Visibility map must say the page is all-visible for index-only scan to skip the heap.

**25. Seven reasons an existing index isn't used?**

> *How to think aloud:* memorize this list — it's an interviewer favorite. They want to see you list 4–5 reasons without prompting. Number-2 (implicit type cast) is the #1 cause in production.

1. Function or cast on the column (`WHERE LOWER(email)=…`)
2. Implicit type cast (`WHERE varchar_col = 123`)
3. Leading wildcard (`LIKE '%abc'`)
4. Low selectivity — seq scan cheaper
5. Stale statistics → planner mis-estimates
6. ORDER BY direction mismatch (mixing ASC/DESC)
7. `NOT` / `<>` operator

**26. Partial index — when useful?**

> *How to think aloud:* the killer use case is "skewed status columns" — most rows are in some terminal state, you only ever query the hot subset. A partial index gives 100x speedup and reduces storage at the same time.

Index only rows matching a predicate. Saves space, faster updates. Great for skewed columns (e.g., 99% rows are `status='ARCHIVED'`):
```sql
CREATE INDEX ON orders(created_at) WHERE status = 'OPEN';
```

**27. UUID v4 vs auto-increment as PK?**

> *Common mistake:* "UUIDs are always better because they're distributed-friendly". Senior answer: it depends on engine. InnoDB (clustered) suffers heavily; Postgres heap less so. UUID v7 is the modern compromise.

UUID v4 is random → in InnoDB (clustered) causes page splits and write amplification; bigger secondary indexes. Auto-increment (BIGINT) is small and monotonic — appends cleanly. Modern alternative: UUID v7 (timestamp-ordered).

**28. B-tree vs Hash vs GIN vs BRIN?**

> *How to think aloud:* a one-line story per type: B-tree = "default", Hash = "rarely useful", GIN = "multi-valued things", BRIN = "huge naturally-sorted tables". The interviewer is checking breadth, not depth.

B-tree: default; equality + range + sort. Hash: equality only, rarely better. GIN: multi-valued columns (JSONB, arrays, full-text). BRIN: append-only/naturally-sorted data (time-series); tiny on disk.

**29. How do indexes affect write performance?**

> *How to think aloud:* concretize with a number — "5–15% per index, so a table with 10 indexes can be 2x slower to write". Auditing unused indexes is a senior task many candidates have never done.

Each INSERT/UPDATE touching an indexed column triggers an index update — random I/O and possible page splits. Rule of thumb: 5–15% write slowdown per index. A table with 10 indexes can be 2x slower to write. Audit indexes regularly.

**30. How to index a JSON column for fast lookup?**

Postgres: GIN on JSONB with `jsonb_path_ops` operator class:
```sql
CREATE INDEX ON users USING gin (data jsonb_path_ops);
SELECT * FROM users WHERE data @> '{"role":"admin"}';
```
Or a functional B-tree index on a specific path: `CREATE INDEX ON users ((data->>'email'))`.

---

## SQL — Query Optimization (31–40)

> **Bridge from previous cluster:** indexes determine the *possible* fast plans; the optimizer decides which one to *actually* use. This cluster tests whether you can read the optimizer's mind through `EXPLAIN`.
>
> **Mental model — a query's life:**
>
> ```
>   SQL text  →  parser  →  rewriter  →  planner (cost-based)  →  executor
>                                              ▲
>                                              │
>                                       stats (pg_statistic)
> ```
>
> The planner picks the cheapest plan it *thinks* exists, based on stats. When stats are stale or the planner mis-estimates, you get a 100x slowdown for no apparent reason. That's why "is ANALYZE recent?" is question #1 in any slow-query investigation.
>
> **Why interviewers care:** anyone can add an index. Senior engineers can read a plan, spot the row-estimate-vs-actual mismatch, and know the fix is `ANALYZE`, not another index. This cluster is the highest-signal section for "have you debugged real prod slowness".
>
> **Common beginner confusion:**
> - "EXPLAIN tells you what really happened" — no, only `EXPLAIN ANALYZE` runs the query.
> - "Seq Scan is always bad" — wrong; on small tables it's optimal (Q34).
> - "Just add an index" — sometimes the predicate prevents index usage (Q25, Q40).
> - "OFFSET pagination scales" — no, it's O(N+offset) (Q37).

**31. How do you debug a slow query?**

> *How to think aloud:* lead with `EXPLAIN (ANALYZE, BUFFERS)`. Then list 3–4 things you'd look for in priority order. Mention the row-estimate mismatch — that's the #1 senior tell.

Run `EXPLAIN (ANALYZE, BUFFERS)`. Look for: Seq Scans on large tables, large estimate vs actual row count mismatch, high `loops` on nested loop inner side, "Rows Removed by Filter" indicating missing index, high disk reads (`Buffers: read`). Verify statistics fresh (`ANALYZE`). Adjust predicates, add indexes, rewrite as needed.

**32. Walk through reading an `EXPLAIN ANALYZE` plan.**

Read from leaves up. Each node has cost (planner estimate), actual time, rows expected vs actual, and loops. Big estimate-actual gaps mean stale stats. Nested loop with high loops × inner cost = problem. Look at the join algorithms (hash/nested-loop/merge) and whether they're appropriate.

**33. Difference between nested loop, hash, and merge join?**

> *How to think aloud:* nested loop = "small outer + indexed inner"; hash = "big unsorted equi-join"; merge = "both sides pre-sorted". The planner's job is to pick — yours is to know *why* it picked.

- Nested loop: outer × inner; good when outer is small + inner has an index
- Hash join: build hash on smaller side; good for big unsorted equi-joins (needs work_mem)
- Merge join: both sides pre-sorted on join key; cheap

**34. Why does Postgres choose Seq Scan even when an index exists?**

Predicate is unselective (low cardinality, planner expects most rows match), stats are stale, type cast/function disables index, or table is so small seq scan is cheaper. Verify with `SET enable_seqscan = off` to force; check the cost.

**35. How to optimize an `OR` query?**

Rewrite as `UNION ALL` of the two branches, each using its own index. Or rely on a bitmap-or if multiple suitable indexes exist:
```sql
SELECT … WHERE a = 1
UNION ALL
SELECT … WHERE b = 2 AND a <> 1;
```

**36. What is parameter sniffing?**

A parameterized query gets a plan based on the first parameter value, which may be a poor fit for other values. Fix via custom plan (`plan_cache_mode='force_custom_plan'`), inlining literals, or query hints.

**37. How would you paginate a 100M-row table?**

> *How to think aloud:* the keyword is **keyset pagination**. OFFSET grows linearly; keyset is logarithmic. Mention the tie-breaker — without it, sorting ties produce skipped/duplicate rows across pages.

Keyset pagination using a unique tie-breaker:
```sql
SELECT * FROM events
WHERE (created_at, id) < ($cursor_ts, $cursor_id)
ORDER BY created_at DESC, id DESC LIMIT 50;
```
OFFSET is O(N+offset); keyset is O(log N).

**38. How to find which queries to optimize first?**

Postgres: `pg_stat_statements` → top queries by total_exec_time. MySQL: slow query log + `performance_schema`. Focus on total time consumed (not just average). Watch p99 not just p50.

**39. When to denormalize?**

> *Common mistake:* "denormalize for performance" (too vague). Senior answer: name the criteria — read/write ratio, join depth, change frequency of the duplicated value — and explicitly call out the *cost* (write amplification, drift risk).

When reads dominate writes, joins are on the hot path (3+ tables), the duplicated value rarely changes, or the access pattern won't fit a clean normalized schema. Always document the source of truth and refresh mechanism.

**40. Why is `LIKE '%abc%'` slow and how do you fix it?**

Leading wildcard means no sorted-prefix lookup. Fixes: `LIKE 'abc%'` if business permits, trigram index (`pg_trgm` + GIN), or full-text search / Elasticsearch.

---

## SQL — Transactions, Isolation, Locks (41–50)

> **Bridge from previous cluster:** so far, single-user queries. Now we add the hardest variable: *concurrency*. This is the cluster where senior backend engineers earn their salary. Every nasty production bug — double charges, oversold inventory, deadlock storms — lives here.
>
> **Mental model — the four anomalies and what protects against them:**
>
> ```
>   Anomaly                  | RU | RC | RR (PG) | RR (MySQL) | Serializable
>   -------------------------|----|----|---------|------------|-------------
>   Dirty read               | ✗  | ✓  | ✓       | ✓          | ✓
>   Non-repeatable read      | ✗  | ✗  | ✓       | ✓          | ✓
>   Phantom read             | ✗  | ✗  | ✗ (snap)| ✓ (gap lk) | ✓
>   Write skew               | ✗  | ✗  | ✗       | ✗          | ✓
> ```
>
> The catch nobody tells juniors: Postgres and MySQL `REPEATABLE READ` behave differently (Q44). And `Serializable` is the only level that prevents write skew (Q43) — the bug that breaks "doctor on call" and "available inventory" rules.
>
> **Why interviewers care:** every staff-level backend incident I've seen had a concurrency root cause. Knowing the names (write skew, phantom, serialization failure) and the fixes (SELECT FOR UPDATE, atomic update, retry loop) is *table stakes* for SDE2.
>
> **Common beginner confusion:**
> - "ACID means I'm safe" — only per-transaction. Concurrency still bites at lower isolation.
> - "REPEATABLE READ is identical everywhere" — Postgres ≠ MySQL (Q44).
> - "MVCC means no locks" — wrong, writer-writer still locks (Q45).
> - "Deadlocks mean a bug" — sometimes, but mostly normal; the bug is lack of retry (Q47).
> - "Serializable is just slow" — it's also *abort-prone*; needs mandatory retry logic.

**41. Explain ACID.**

> *How to think aloud:* expand each letter with one sentence. Add: "ACID is *per-transaction*; concurrency safety across transactions is what isolation levels are for". That bridge to Q42 signals senior thinking.

Atomicity (all-or-nothing), Consistency (constraints hold at commit), Isolation (concurrent transactions don't see each other's partial work, per isolation level), Durability (committed changes survive crashes via WAL).

**42. List the four isolation levels and the anomalies each prevents.**

Read Uncommitted (none), Read Committed (no dirty read), Repeatable Read (no non-repeatable read; phantoms blocked in MySQL InnoDB only), Serializable (all four, including write skew).

**43. What's write skew? Give an example.**

> *How to think aloud:* this is a senior signal question. Use the doctor-on-call example (or bank account, or inventory). The point: two transactions each read consistent data, each makes a valid decision, both commit — and the *invariant across them* breaks.

Two transactions read overlapping data, each makes a decision based on what they saw, both write, and the combination violates an invariant. Classic: two on-call doctors each going off call simultaneously, with a "≥ 1 doctor on call" rule. Only Serializable prevents it.

**44. Postgres REPEATABLE READ vs MySQL REPEATABLE READ?**

> *Common mistake:* assuming SQL standard isolation levels behave the same across vendors. They don't. This is an interview classic precisely because most candidates don't know it.

Postgres RR is pure snapshot isolation; doesn't prevent phantoms because writes acting on observations can still differ. MySQL InnoDB RR uses next-key (gap) locks → blocks INSERTs that would create phantoms during your transaction.

**45. What is MVCC?**

> *How to think aloud:* "each write creates a new version; readers see snapshots". Mention the engine-specific detail: Postgres tags tuples with `xmin/xmax`; MySQL uses an undo log. Conclude with: "readers don't block writers and vice versa — *but writers still block writers*".

Multi-Version Concurrency Control: each write creates a new tuple version (Postgres: tagged with xmin/xmax; MySQL: undo log). Readers see versions visible to their snapshot. Readers don't block writers; writer-writer conflicts still acquire row locks.

**46. Walk through a money transfer transaction.**

> *How to think aloud:* this is the "show me you've actually built something real" question. Two things to nail: (1) lock rows in consistent order to avoid deadlocks, (2) check `rows affected = 1` after the debit to prevent overdraft.
```sql
BEGIN;
SELECT * FROM accounts WHERE id IN ($from, $to) ORDER BY id FOR UPDATE;
UPDATE accounts SET balance = balance - $amt WHERE id = $from AND balance >= $amt;
-- 0 rows → ROLLBACK
UPDATE accounts SET balance = balance + $amt WHERE id = $to;
INSERT INTO transactions (idempotency_key, …) VALUES (…) ON CONFLICT DO NOTHING;
COMMIT;
```
Lock both rows in consistent order to avoid deadlocks.

**47. What's a deadlock and how is it resolved?**

Two transactions waiting on each other's locks → cycle. DB detects via deadlock_timeout (Postgres) or detector (MySQL) and aborts one transaction. Application must retry. Prevention: acquire locks in consistent order, keep transactions short.

**48. Optimistic vs pessimistic concurrency control?**

> *How to think aloud:* "pessimistic = locks; optimistic = version checks + retry". The right choice depends on conflict probability. Hot inventory row → pessimistic. Edit-document workflow → optimistic.

Pessimistic: `SELECT FOR UPDATE` locks the row; safest for high-contention. Optimistic: version column checked on update (`WHERE version = ?`); zero locks; retry on conflict. Pick based on conflict probability.

**49. How would you build a job queue in Postgres?**

> *How to think aloud:* `SELECT FOR UPDATE SKIP LOCKED` is the magic phrase. Mention it lets multiple workers pull *different* jobs concurrently without locking each other. Bonus: visibility timeout via "lease until" column.

`SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1`. Multiple workers can pull jobs concurrently without contention.

**50. What is the outbox pattern?**

> *How to think aloud:* the core idea: "publishing to Kafka and writing to DB can't be atomic — solve it by writing the *intent to publish* in the same transaction". Then a worker reads and publishes. Eliminates the dual-write problem.

Write the "event-to-publish" row to a DB table inside the same transaction as the business change. A worker (or CDC) reads outbox and publishes externally. Solves the dual-write problem (DB write + Kafka publish atomically).

---

## NoSQL & Distributed Systems (51–60)

> **Bridge from previous cluster:** transactions and isolation gave you single-node correctness. Now we go multi-node — and the rules change. The CAP/PACELC theorems describe what *must* break in a distributed system: you can't have everything.
>
> **Mental model — every distributed store sits somewhere on this 2x2:**
>
> ```
>                          During Partition
>                  AP (available)         CP (consistent)
>                  ────────────────       ─────────────────
>   Normal: EL    Cassandra, Dynamo      MongoDB (CP-tunable)
>   (latency)    Riak                    
>
>   Normal: EC    (rare — most CP        Spanner, FaunaDB,
>   (consist.)    optimize for latency)  CockroachDB
> ```
>
> When asked "why did you pick Mongo over Postgres?", a junior says "schema flexibility"; a senior says "we needed PA/EL because our cross-AZ writes had to stay available during partition, and we modeled invariants outside the DB".
>
> **Why interviewers care:** distributed-systems thinking is the single biggest leap from SDE1 to SDE2. The interviewer wants to hear you reason about *what fails first* and *what you can tolerate*.
>
> **Common beginner confusion:**
> - "CAP says pick two" — wrong (Q51). P isn't optional.
> - "NoSQL = no schema" — wrong; you have a schema, it's just unenforced.
> - "Eventual consistency = data loss" — wrong; it's propagation delay (Q59).
> - "Sharding is automatic" — only if your key distributes well (Q55, hot partition).
> - "Mongo is web-scale; SQL isn't" — false dichotomy; Postgres scales further than most people realize.

**51. State the CAP theorem precisely. Why is "pick two" wrong?**

> *How to think aloud:* lead with "P is not optional — networks fail". The real choice during partition is C vs A. Mention PACELC as the more honest extension (Q52).

When a partition occurs in a distributed system, you must choose between consistency (refuse stale reads) or availability (serve responses). Partition tolerance isn't optional — networks fail. "Pick two" implies a static choice; the real choice is *what to do during a partition*: CP or AP.

**52. What's PACELC?**

Extends CAP: during Partition choose A or C; Else (normal operation) choose L (low latency) or C (consistency). Useful: Spanner is PC + EC; Cassandra is PA + EL; DynamoDB default is PA + EL.

**53. Quorum reads/writes — explain R + W > N.**

> *How to think aloud:* the formula is pigeonhole — if R+W > N, any read set must intersect with any write set in at least one node. That overlapping node has the latest write. Mention common config: W=quorum, R=quorum (both > N/2).

For N replicas, if R + W > N, any read overlaps with the latest write → strong consistency for single-key reads. Common: W=quorum, R=quorum, balanced for latency and availability.

**54. Hash vs range vs directory sharding?**

Hash: even distribution; no efficient range queries. Range: range queries efficient; hotspot risk (monotonic IDs). Directory: lookup service maps key→shard; flexible but SPOF.

**55. What's a hot partition and how do you mitigate it?**

> *How to think aloud:* describe the canonical causes — celebrity user, monotonic timestamp as PK, bad shard key. Then list mitigations in order of intrusiveness: cache → hash-prefix → sub-shard → redesign.

One partition gets disproportionate traffic (bad shard key, celebrity user, sequential timestamps). Mitigations: hash-prefix the key, cache aggressively, L1 in-process cache, sub-shard, redesign.

**56. When would you choose Mongo over Postgres?**

> *Common mistake:* defending Mongo on "schema flexibility" or "scale". Senior answer: most apps don't need it; pick Mongo only when measured, citing specifics (document model, multi-region writes). The honest answer wins more interviews than the Mongo-fanboy answer.

Truly nested document model (deep arrays, varied schemas across tenants), multi-region writes you can't get in Postgres, large schema flexibility that JSONB can't satisfy. Honest answer: most apps are better off with Postgres + JSONB. Only choose Mongo when measured.

**57. Difference between DynamoDB GSI and LSI?**

GSI = global secondary index, any (PK, SK), created/dropped any time, eventually consistent. LSI = local secondary index, same PK as base table with different SK, defined at table creation, can be strongly consistent, shares the 10GB partition limit.

**58. Cassandra: how would you model a chat message store?**
```sql
CREATE TABLE messages (
  conv_id UUID, sent_at TIMESTAMP, msg_id UUID, sender UUID, body TEXT,
  PRIMARY KEY ((conv_id), sent_at, msg_id)
) WITH CLUSTERING ORDER BY (sent_at DESC);
```
Partition by conversation; clustering by time DESC for fast "latest N". For very wide conversations, bucket by month: PK `((conv_id, month))`.

**59. What's eventual consistency and is it dangerous?**

> *How to think aloud:* "data isn't lost — just propagating". Then frame the *real* danger: invariants that span replicas (money, locks, stock counts) break. UX-only features (feeds, search results) survive eventual consistency just fine.

Replicas converge "eventually" after writes. Not data loss — propagation delay. Most internet-scale features (feeds, search, sessions) are fine with it. Not OK for: money invariants, locks, anything where invariants span replicas.

**60. How does Redis Cluster handle multi-key operations?**

Each node owns a range of 16384 hash slots; key → slot via CRC16. Multi-key operations require all keys on the same slot — use hashtags `{}`: `user:{42}:profile` and `user:{42}:cart` hash to the same slot. Multi-key across slots is rejected.

---

## ORM (61–68)

> **Bridge from previous cluster:** distributed systems gave you "what data store to pick"; ORM is "what mistakes you make once you've picked SQL". This cluster grades whether you treat the ORM as a *leaky abstraction with known failure modes* — or as a magic black box.
>
> **Mental model:** an ORM is a query *generator*. Every line of `orm.user.findMany(...)` becomes one or more SQL statements. If you don't have intuition for which SQL it produces, you'll ship bugs. The senior posture: read the generated SQL in dev; never ship a query you haven't seen.
>
> **Why interviewers care:** ORM bugs are the #1 source of production slowness in modern backend teams. The interviewer wants confidence that you'd catch N+1 in code review, know when to drop to raw SQL, and understand connection lifecycle.
>
> **Common beginner confusion:**
> - "The ORM optimizes the queries for me" — no, it generates literal queries.
> - "Lazy loading is fine, I'll just be careful" — you won't (Q63 — Prisma's stance).
> - "Active Record is always simpler" — for simple CRUD yes; complex domains argue for Data Mapper (Q64).
> - "More connections = more throughput" — wrong; oversized pools cause contention (Q68).

**61. What is the N+1 problem and how do you fix it?**

> *How to think aloud:* describe with a number — "N child queries plus 1 parent query = N+1". Then list three fixes in order: eager load (`include`), batched IN query, DataLoader pattern.

A parent query returns N rows; each parent triggers a child query → N+1 queries total. Fixes: eager loading (`include`/`relations`), separate batched query with `IN (ids)`, DataLoader pattern (batches + caches per-request), or raw SQL.

**62. Lazy vs eager loading?**

Lazy: relation loaded on access (risks N+1). Eager: loaded with the parent in one query (JOIN or follow-up SELECT). Eager prevents N+1 but can over-fetch or cause cartesian explosion. Mix per use case; Prisma intentionally has no lazy mode.

**63. Why doesn't Prisma have lazy loading?**

By design — lazy loading is the #1 source of accidental N+1 in production. Forcing explicit `include`/`select` makes the query cost visible at the call site.

**64. Active Record vs Data Mapper?**

Active Record: object has `save()`/`delete()` (Rails, Sequelize). Data Mapper: a separate repository persists plain objects (Hibernate, TypeORM Repository). Data Mapper separates domain from persistence; better for testing and complex domains.

**65. How do you write a transaction with retry on serialization failure?**
```javascript
async function withTx(fn, attempts = 3) {
  for (let i = 0; i < attempts; i++) {
    try { return await prisma.$transaction(fn, { isolationLevel: 'Serializable' }); }
    catch (e) {
      if (e.code === 'P2034' || e.meta?.code === '40001' || e.code === '40P01') {
        await sleep(50 * Math.random() * (i+1)); continue;
      }
      throw e;
    }
  }
  throw new Error('TX_RETRY_EXHAUSTED');
}
```

**66. When would you drop down to raw SQL in an ORM project?**

Complex SQL features (window functions, recursive CTEs, JSONB ops, full-text), bulk operations (10k+ rows), performance-critical hot paths, reports/exports, DB-specific features the ORM doesn't expose.

**67. How do you safely add a NOT NULL column to a 100M-row table?**

> *How to think aloud:* this is the "you've done migrations in prod" tell. Walk through the 4-phase pattern. Mention that adding a column with constant default is fast in modern Postgres; the trap is non-trivial defaults or type changes (rewrite).

Phase: 1) add nullable column; 2) backfill in batches (`UPDATE ... LIMIT 10000` in a loop, sleep between); 3) add CHECK NOT NULL as NOT VALID, then VALIDATE; 4) ALTER COLUMN SET NOT NULL. For huge ALTERs in MySQL: `pt-online-schema-change` or `gh-ost`.

**68. How does connection pooling work and how do you size it?**

> *Common mistake:* "more connections is always better". Senior answer: bounded pool; total connections across instances must stay below DB `max_connections`; oversizing causes contention (CPU thrashing in the DB). Mention PgBouncer for thousands of app instances.

A bounded set of DB connections reused across requests. Per app instance: 10–25 typical. Total connections (instances × pool) must stay under DB `max_connections`. For thousands of instances: PgBouncer in transaction-mode multiplexes connections. Monitor wait time.

---

## Caching & Redis (69–76)

> **Bridge from previous cluster:** ORMs reduce app-code-to-DB friction; caching reduces DB-roundtrip frequency. But every cache introduces a new problem: *staleness*. This cluster tests how you reason about correctness under cache layers.
>
> **Mental model — the three axes of cache design:**
>
> ```
>            Consistency (how stale is acceptable?)
>            │
>            │            ┌── write-through (tightest)
>            │            │
>            │   cache-aside ──┐
>            │                 │
>            │   write-behind ─┘  (loosest)
>            └────────────────────── Throughput / Latency
> ```
>
> Plus two failure modes: **eviction** (the cache forgets things; how do you handle the new miss?) and **stampede** (the cache forgets many things at once; how do you avoid a DB tidal wave?).
>
> **Why interviewers care:** caching is where "I read a blog post about Redis" meets "I've handled a production stampede at 3am". The specifics matter: jittered TTL, singleflight, stale-while-revalidate, and "what happens if Redis dies" are senior tells.
>
> **Common beginner confusion:**
> - "Just add Redis" — no. Caching changes correctness; you must reason about consistency (Q75).
> - "Cache stampede = many misses" — no, it's *correlated* misses (Q70).
> - "Pub/Sub is reliable" — wrong; it's fire-and-forget (Q74). Use Streams for durability.
> - "Redlock works for correctness locks" — controversial (Q72). Use ZooKeeper/etcd if correctness matters.

**69. Compare cache-aside, write-through, write-behind.**

> *How to think aloud:* describe each pattern in one sentence, then the use case. Default to cache-aside unless you have a reason; write-behind is risky and worth its complexity only for counter-style workloads.

- Cache-aside: app reads from cache, falls back to DB, populates cache. Most common.
- Write-through: writes go to cache + DB synchronously. Cache always consistent.
- Write-behind: writes ack'd by cache; DB write async. Fast, risky on cache crash. Use for high-volume non-critical (counters).

**70. What's a cache stampede and how do you prevent it?**

> *How to think aloud:* the cause is *correlated misses*. List fixes in order: singleflight (one computes, others wait), probabilistic early refresh (re-fetch before TTL), stale-while-revalidate (serve stale while async refresh), jittered TTL.

When a popular key expires, many concurrent requests miss → all hit DB simultaneously. Fixes: singleflight (one client computes via SETNX lock, others wait or serve stale), probabilistic early refresh, stale-while-revalidate, jittered TTL.

**71. LRU vs LFU vs TTL eviction?**

LRU evicts least-recently used (general default). LFU evicts least-frequently used (good for stable hot keys). TTL evicts by expiry only. W-TinyLFU (Caffeine) combines LRU + LFU + admission filter for top-tier hit rates.

**72. How would you build a distributed lock in Redis?**

> *Common mistake:* defending Redlock without nuance. Senior answer: it works for *advisory* mutual exclusion under most conditions; for *correctness* locks (money, state machines), use ZooKeeper or etcd with their fencing token guarantees.

Basic: `SET key value NX EX 30`; release via Lua to atomically check the owner before deleting. For cluster: Redlock — controversial (Kleppmann argues it doesn't ensure mutual exclusion in all failure modes). For correctness-critical locks, ZooKeeper or etcd.

**73. How would you build a rate limiter in Redis?**

Fixed window: `INCR key EX 60`; reject if > limit. Sliding window: sorted set with timestamps + Lua to atomically expire + count + add. Token bucket: hash with tokens + refill via Lua.

**74. Pub/Sub vs Streams?**

Pub/Sub: fire-and-forget broadcast; messages dropped if no subscriber; no replay. Streams: durable append-only log with consumer groups, ACKs, and replay (Kafka-lite). Use Streams for anything resembling event processing.

**75. How do you keep cache and DB consistent?**

> *How to think aloud:* there's no "always consistent" answer — pick by staleness tolerance. List the options on a spectrum: TTL (loosest, simplest) → invalidate on write → versioned keys → CDC-based invalidation (tightest, most complex).

Choose by staleness tolerance. Options: TTL (best-effort), explicit invalidation on write, versioned keys (bump version on change), CDC-based invalidation (Debezium → invalidator). Strict consistency is hard; embrace bounded staleness for most workloads.

**76. What happens if Redis goes down?**

> *How to think aloud:* the architectural answer: the app must *function* without cache, just slower. Then: circuit breaker, rate-limited DB fallback, pre-warm on recovery. Junior answer is "we'd be down" — senior answer treats cache as optional.

Detect via circuit breaker / timeout. Gracefully fall back to DB with rate limiting (to avoid stampede). Pre-warm on recovery. Architectural rule: app must still function without cache (degraded performance, not broken).

---

## System Design & Senior Topics (77–80)

> **Bridge from previous clusters:** the last four questions integrate everything. A system design answer that doesn't mention indexing strategy, transactions, sharding, caching, and idempotency is missing pieces. These four are mini system-design rounds embedded in the Q&A drill.
>
> **Mental model — every system design has 5 dimensions to address:**
>
> ```
>   1. Data model       (what's stored, in what form, where?)
>   2. Access patterns  (read vs write ratio, hot keys, query shapes)
>   3. Scale path       (vertical → horizontal; what shards on what key?)
>   4. Failure modes    (what breaks first; how do we degrade?)
>   5. Consistency      (where do we need strict vs eventual?)
> ```
>
> Walk these dimensions out loud in interview. Even a rough answer on each is better than a deep answer on one.
>
> **Why interviewers care:** these final four reveal whether you can *compose*. Anyone can name an LRU cache; few can describe how it interacts with replication lag, idempotency keys, and DB connection limits in a real deploy.
>
> **Common beginner confusion:**
> - Jumping to "use microservices" — that's not a design, it's a deployment style.
> - Forgetting idempotency for anything with retries (Q79).
> - Ignoring read/write ratio — the single most important number for choosing a store.
> - Skipping clarifying questions — never start designing before asking about scale, latency budgets, and consistency requirements.

**77. Design a URL shortener that handles 100k QPS reads.**

> *How to think aloud:* lead with the read/write ratio (URL shortener is wildly read-heavy). Then: CDN/cache layer takes 95% of traffic; KV store behind. Mention base62 codes, hash collisions, abuse (rate limit by IP), and analytics offload (async).

- Store `short_code → long_url` in KV (Redis or DynamoDB)
- CDN in front for cacheable redirects (huge hit rate)
- Hash-based code (random) + base62 encoding
- Counter or DB sequence to generate codes; collisions checked
- Analytics: log to Kafka → ClickHouse for aggregations
- Postgres canonical store; Redis as read cache with TTL
- Discuss hot links (cache more aggressively) and abuse (rate limit by IP/user)

**78. Design Instagram's "Recent Photos" feed.**

> *How to think aloud:* the central trade-off is fan-out-on-write vs fan-out-on-read. Pure fan-out-on-write fails for celebrities (millions of followers). Pure fan-out-on-read is slow for active scrollers. Real systems use a *hybrid* — that detail wins points.

- Fan-out write: when user posts, push to followers' feed lists in Redis (sorted set, capped at N)
- Cold users (no recent reads): fan-out lazily on demand
- Mixed: pull from celebs (millions of followers — fan-out write expensive)
- Postgres canonical: posts, follows
- Cassandra/Redis per-user feed
- CDN for image delivery
- Discuss fan-out at write vs read trade-offs

**79. Design a payment system. What goes wrong if you skip idempotency?**

> *How to think aloud:* lead with "every external call needs an idempotency key". Then double-entry ledger, outbox pattern for webhooks, sagas for cross-service flow. The "what goes wrong" prompt is asking you to *narrate disasters*: double charges, double inventory, double notifications.

- Postgres for accounts + transactions (ACID)
- Double-entry ledger
- Idempotency keys for every external call
- Outbox pattern for webhooks/events
- Sagas for cross-service flow (charge → reserve inventory → confirm order)
Without idempotency: network retries → double charges, double inventory deductions, double notifications. Disaster.

**80. You're seeing tail latency spikes only on writes. What do you check?**

> *How to think aloud:* this is the "did you do real debugging in prod" question. List your hypotheses in priority order and call out *what you'd query first*. Mention `pg_stat_activity`, `pg_blocking_pids`, `iostat`, and replication lag. See file 2 for the full debugging methodology.

1. Lock contention (`pg_stat_activity`, `pg_blocking_pids`)
2. Long-running transactions blocking VACUUM (Postgres) → bloat → slower writes
3. Replication lag holding sync replica → primary stalls on sync_commit
4. Disk I/O (iostat) — write amplification, fsync wait
5. Connection pool exhaustion
6. WAL bottleneck (consider faster disk, bigger WAL buffers)
7. Index bloat — REINDEX CONCURRENTLY
8. Lock waits visible in `pg_stat_database.deadlocks` and `wait_event`

---

## How to use this list

- Day 14 morning: read silently, mark questions you stumbled on
- Day 14 afternoon: redo the marked ones out loud
- Day 15: mock interview — partner asks questions in random order; 60s/question, no fumbling
- Day of interview: skim only the questions where you previously fumbled

---

## Revision strategy

| Round | Goal |
|---|---|
| 1 | Read all 80; pick 20 weakest |
| 2 | Master the 20 weakest |
| 3 | Random-order practice; time yourself 60s/question |
| 4 | Day-before lightning round |

> The interviewer doesn't reward perfect recall; they reward **clear, structured, confidently-stated answers**. Practice talking through these, not just reading.
