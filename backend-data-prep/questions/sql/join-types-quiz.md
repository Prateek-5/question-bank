# Join Types Quiz — Predict the Output

## Source / Origin
- Classic warm-up at Amazon, Walmart, Atlassian SQL screens.
- LeetCode #175 "Combine Two Tables", #181, #183 — same `LEFT JOIN`/anti-join muscle.
- Stratascratch interview tag "Joins · easy/medium".

## Why this question matters in interviews
Joins are the single most-tested SQL primitive. Interviewers don't ask "what's a LEFT JOIN?" — they show you two tiny tables and ask **predict every row in the output for each of six join flavours**. Getting any wrong (especially the FULL OUTER + null-side rows) signals the candidate hasn't actually used joins in anger.

The reason this matters: nearly every non-trivial query is a chain of joins. If you can't predict the output of one join over 4-row inputs, you cannot debug a join over 4M-row inputs — you'll add filters that silently turn outer joins into inner joins, ship a query that drops 30% of users, and get paged at 2 AM.

This problem also tests **set-thinking** (which tuples survive each operator) and **NULL discipline** (outer joins introduce NULLs; subsequent `WHERE` clauses may eat the very rows you outer-joined for).

## Concepts involved

### Syntax to lock in
```sql
-- 1. INNER JOIN     — intersection on join key
SELECT * FROM A INNER JOIN B ON A.k = B.k;

-- 2. LEFT  OUTER    — A's rows always; B's columns NULL on no-match
SELECT * FROM A LEFT  JOIN B ON A.k = B.k;

-- 3. RIGHT OUTER    — mirror of LEFT (most teams ban it for readability)
SELECT * FROM A RIGHT JOIN B ON A.k = B.k;

-- 4. FULL OUTER     — every row from both; NULLs on the unmatched side
SELECT * FROM A FULL  JOIN B ON A.k = B.k;

-- 5. CROSS JOIN     — Cartesian product, no ON
SELECT * FROM A CROSS JOIN B;

-- 6. SELF JOIN      — table joined to itself, requires aliases
SELECT e.name, m.name FROM emp e LEFT JOIN emp m ON e.mgr_id = m.id;
```

### Edge cases / interview traps
1. **`WHERE` on the right-table column after a LEFT JOIN** silently degrades it to an INNER JOIN. `LEFT JOIN B ON A.k=B.k WHERE B.status='x'` — rows where B is NULL fail the filter. Move the predicate into the `ON`.
2. **Duplicates on either side multiply rows.** If `B.k` has 3 rows with `k=5` and `A.k` has 2, you get 6 output rows. Most candidates forget the multiplication.
3. **NULLs never equal NULLs in `ON`.** Rows where both sides have `NULL` in the join key do NOT match. Use `IS NOT DISTINCT FROM` or `COALESCE(k,-1)` if you really want NULL-equates-NULL.
4. **CROSS JOIN with a WHERE that's actually a join condition** is a code smell — the planner often still figures it out, but readers won't.
5. **FULL OUTER not supported in MySQL** (pre-8.0.31 emulated via `UNION` of LEFT + RIGHT). Mention this if asked.
6. **`USING(k)` collapses the join column** to one output column; `ON A.k = B.k` keeps both. Affects `SELECT *`.
7. **RIGHT JOIN is technically equivalent to a flipped LEFT JOIN.** Most style guides ban it because reading right-to-left is unnatural.
8. **Three-or-more-table joins are left-associative.** `A LEFT JOIN B INNER JOIN C` — `C`'s inner join condition may filter out the NULL-side rows from the LEFT JOIN. Parenthesize if you mean it.

## Mental Model

```
   A           B            INNER       LEFT        FULL
 ┌───┐       ┌───┐         ┌─────┐    ┌──────┐    ┌──────┐
 │ a │       │   │         │     │    │ a    │    │ a    │
 │ b │   ∩   │ b │   =     │  b  │    │ b ⋈  │    │ b ⋈  │
 │ c │       │ c │         │  c  │    │ c ⋈  │    │ c ⋈  │
 └───┘       │ d │         └─────┘    └──────┘    │   d  │
             └───┘                                └──────┘
```

Joins are **filtered Cartesian products**. Start with all (a,b) pairs (CROSS JOIN). Apply the `ON` predicate (INNER). Then, depending on the outer flavour, **re-attach** the unmatched rows from one or both sides with NULLs in the foreign columns.

## Why interviewers care
- Tests **set semantics** — predicting outputs forces the candidate to think in tuples, not loops.
- Probes the **NULL-after-outer-join** landmine — the most common production bug in analytics SQL.
- Reveals whether the candidate knows the **logical execution order** (FROM → ON → WHERE), without which join-vs-filter is incomprehensible.

## Common beginner confusion
- "INNER vs OUTER" — outer means "*keep unmatched outer rows too*"; inner means "intersection only".
- Believing `LEFT JOIN ... WHERE B.col = x` is still a left join. It isn't.
- Thinking `NULL = NULL` is `TRUE` in `ON` clauses. It's `UNKNOWN`.
- Believing `SELECT *` after `USING` and after `ON` produce the same column list. They don't (USING collapses the key).

## Brute force approach
Mentally walking every pair of `(a,b)` rows, checking the predicate, then re-attaching unmatched rows by hand. Works for 4-row tables; impossible for real ones. The "brute force" is exactly what the interview is testing — the goal is to do it *correctly* on paper.

## Optimal approach
Memorize the **set diagram** for each join flavour and process the tables column-major: list every join-key value across both tables, then for each value mark which side has it and how many copies. The output rows follow mechanically.

## Solution (SQL)

Sample tables:

```sql
CREATE TABLE A (id INT, val TEXT);
INSERT INTO A VALUES (1,'a1'), (2,'a2'), (3,'a3'), (NULL,'aN');

CREATE TABLE B (id INT, val TEXT);
INSERT INTO B VALUES (2,'b2'), (2,'b2b'), (3,'b3'), (4,'b4'), (NULL,'bN');
```

```sql
-- 1. INNER JOIN
SELECT A.id, A.val, B.val FROM A INNER JOIN B ON A.id = B.id;
-- (2,a2,b2) (2,a2,b2b) (3,a3,b3)   -- 3 rows. NULL ids dropped on both sides.

-- 2. LEFT JOIN
SELECT A.id, A.val, B.val FROM A LEFT JOIN B ON A.id = B.id;
-- inner-rows + (1,a1,NULL) + (NULL,aN,NULL)    -- 5 rows

-- 3. RIGHT JOIN
SELECT A.id, A.val, B.val FROM A RIGHT JOIN B ON A.id = B.id;
-- inner-rows + (NULL,NULL,b4) + (NULL,NULL,bN) -- 5 rows

-- 4. FULL JOIN
SELECT A.id, A.val, B.val FROM A FULL JOIN B ON A.id = B.id;
-- inner-rows + LEFT-only + RIGHT-only          -- 7 rows

-- 5. CROSS JOIN
SELECT A.val, B.val FROM A CROSS JOIN B;
-- 4 × 5 = 20 rows

-- 6. SELF JOIN (find pairs in A with same val length)
SELECT a1.val, a2.val FROM A a1 JOIN A a2
  ON length(a1.val) = length(a2.val) AND a1.id < a2.id;
```

## Step-by-step dry run

Walk LEFT JOIN row by row:

```
A rows:                          For each, scan B for matches on id:
(1, a1)        id=1 → no match in B → emit (1, a1, NULL, NULL)
(2, a2)        id=2 → two matches  → emit (2,a2,2,b2) and (2,a2,2,b2b)
(3, a3)        id=3 → one match    → emit (3,a3,3,b3)
(NULL, aN)     id=NULL → NULL=NULL is UNKNOWN, no match → emit (NULL,aN,NULL,NULL)
```

Total: 5 rows. Notice `aN` is preserved (it's an A-row) but `bN` is gone (it's a B-row, and we don't keep B-only rows in a LEFT JOIN).

For FULL JOIN, add the two B-only rows `(NULL,NULL,4,b4)` and `(NULL,NULL,NULL,bN)`.

## How to think aloud in the interview
1. *"Let me list the join-key values in both tables: A has {1,2,3,NULL}; B has {2,2,3,4,NULL}. Note NULL won't match NULL."*
2. *"INNER first — the intersection is {2,3}. Multiplicity: 2 appears once in A, twice in B → two rows. 3 appears once each → one row. Total three."*
3. *"For LEFT, I add A's unmatched rows back: id=1 and id=NULL. So inner + 2 = 5 rows."*
4. *"For FULL, I also add B's unmatched: id=4 and id=NULL. 5 + 2 = 7 rows."*
5. *"If the interviewer slaps a `WHERE B.val IS NOT NULL` on top, my LEFT JOIN collapses back to the INNER result — that's the classic trap I'd flag."*

## Important takeaways
- **Logical order:** FROM → ON → WHERE. ON happens during the join; WHERE happens after. Anything on the nullable side belongs in ON.
- **Multiplicity bites.** Always know your join-key uniqueness; if either side has duplicates on the key, expect row inflation.
- **NULL-safe equality:** Postgres `IS NOT DISTINCT FROM`, MySQL `<=>`. Use sparingly.
- **`USING` vs `ON`:** USING collapses the key column; great for chains of joins on the same name.
- Cross-reference: see `backend-data-prep/sql/01-sql-fundamentals.md` "Joins" section for the full theory.

## Variants
1. **"Make this LEFT JOIN return only A-rows with no match in B"** → anti-join. Switch to `WHERE B.id IS NULL` (the legitimate use). See `anti-join.md`.
2. **"Same query in MySQL without FULL OUTER JOIN"** → `LEFT JOIN ... UNION ALL ... RIGHT JOIN ... WHERE A.id IS NULL`.
3. **"What if I want NULL=NULL to match?"** → `ON A.id IS NOT DISTINCT FROM B.id`.

## Revision notes

> **Joins cram block**
> - INNER = intersection on `ON`.
> - LEFT  = INNER + A-only rows (B cols NULL).
> - RIGHT = INNER + B-only rows.
> - FULL  = INNER + A-only + B-only.
> - CROSS = full Cartesian, no ON.
> - SELF  = same table aliased twice.
> - **Trap 1:** `WHERE B.col = x` after LEFT JOIN → silently becomes INNER. Push it into ON.
> - **Trap 2:** Duplicates on the join key multiply rows.
> - **Trap 3:** `NULL = NULL` is UNKNOWN; outer joins do NOT match NULLs.
> - **Trap 4:** FULL OUTER absent from MySQL < 8.0.31.
> - Always state row counts row-by-row in interview to prove you understood the multiplicity.
