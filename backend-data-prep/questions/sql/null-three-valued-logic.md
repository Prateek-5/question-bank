# NULL & Three-Valued Logic

## Source / Origin
- Universal SQL interview probe. Often disguised as "find users with no email" or "why does my filter exclude rows".
- Real prod incident: every senior engineer has lost data to a NULL trap at least once.

## Why this question matters in interviews
NULL handling is **the single highest-signal SQL topic**. Candidates who don't deeply understand three-valued logic (TRUE / FALSE / UNKNOWN) ship queries that silently drop rows in production — billing, fraud, recon, compliance. Interviewers test it because production reality is unforgiving here.

The classic question: "given this table, which of these queries return 0 rows and why?" The candidate who can answer "because `NULL = NULL` is UNKNOWN, and `WHERE UNKNOWN` filters the row out" without flinching demonstrates senior-grade SQL literacy in one sentence.

## Concepts involved

### Syntax to lock in
```sql
-- NULL is "unknown", not "missing". You compare it with IS NULL / IS NOT NULL.
SELECT * FROM t WHERE x IS NULL;
SELECT * FROM t WHERE x IS NOT NULL;

-- = and <> NEVER match NULL. Both return UNKNOWN.
SELECT NULL = NULL;          -- UNKNOWN (rendered as NULL)
SELECT NULL <> NULL;         -- UNKNOWN
SELECT NULL = 1;             -- UNKNOWN

-- NULL-safe equality
SELECT a IS NOT DISTINCT FROM b;   -- Postgres / SQL-standard. TRUE if both NULL.
SELECT a <=> b;                    -- MySQL spaceship operator.

-- COALESCE picks first non-NULL
SELECT COALESCE(nickname, name, 'anon') FROM users;

-- NULLIF is the inverse: returns NULL when args equal
SELECT NULLIF(score, 0) FROM games;  -- divide-by-zero guard
```

### Edge cases / interview traps
1. **`WHERE col = NULL` returns zero rows.** Use `IS NULL`. Most common SQL bug.
2. **`NOT IN (subquery)` with NULL inner row** returns zero rows for everyone — see `anti-join.md`.
3. **Aggregates ignore NULL** (except `COUNT(*)`). `AVG`, `SUM`, `MIN`, `MAX`, `COUNT(col)` all skip NULL rows. This is **usually** what you want, but check.
4. **`GROUP BY` treats all NULLs as the same group.** Counterintuitive: `NULL = NULL` is UNKNOWN, but GROUP BY puts them together. Standard SQL behavior.
5. **`ORDER BY` puts NULLs at the end (asc) in Postgres / Oracle**, but at the **start** in MySQL. Use `NULLS FIRST | NULLS LAST` explicitly.
6. **`UNIQUE` constraint allows multiple NULLs** (one constraint can have many "unknown" rows). Postgres 15+ has `NULLS NOT DISTINCT` to fix.
7. **`CHECK (col > 0)` allows NULL** because `NULL > 0` is UNKNOWN, not FALSE. CHECK only blocks FALSE.
8. **Concatenation `col1 || col2`** produces NULL if either is NULL in standard SQL (but MySQL/SQL Server differ). Always `COALESCE`.
9. **Boolean logic with NULL.** `TRUE AND NULL = NULL`; `TRUE OR NULL = TRUE`; `FALSE AND NULL = FALSE`. Memorize the truth table.

## Mental Model

```
   Three-valued logic truth tables:

   AND |  T   F   N             OR  |  T   F   N             NOT
   ----+-----------             ----+-----------             T → F
    T  |  T   F   N              T  |  T   T   T             F → T
    F  |  F   F   F              F  |  T   F   N             N → N
    N  |  N   F   N              N  |  T   N   N

   Read "N" as "unknown" / "we don't know yet".
   WHERE keeps rows whose predicate is TRUE; it rejects FALSE *and* UNKNOWN.
```

NULL means **"the value is unknown, possibly anything"**. So `NULL = NULL` cannot be TRUE — they might both be unknowns referring to different real values. That's why all NULL comparisons via `=`/`<>` collapse to UNKNOWN.

## Why interviewers care
- Production correctness. NULL bugs are silent, expensive, and never raise an error.
- Three-valued logic is the **single concept that distinguishes SQL from imperative code** the most. Mastery here means you've thought relationally.
- Most SQL screens have at least one NULL-trap question disguised as something else.

## Common beginner confusion
- "NULL means zero / empty string" — no, it means *unknown*.
- "I can use `= NULL`" — never. Use `IS NULL`.
- "Aggregates count NULLs" — no, except `COUNT(*)`.
- "NULL is its own group in GROUP BY but not equal to itself" — yes, contradictory but true.
- "UNIQUE prevents two NULL rows" — usually no (Postgres default behaviour).

## Brute force approach
"Just check IS NULL everywhere." Works for simple cases but doesn't handle:
- Anti-join NOT IN trap.
- Boolean operator chains with NULL.
- Joins where the key is nullable.
The right approach is to **classify each column as nullable or not** and write predicates that handle both branches.

## Optimal approach
- Use `IS NULL` / `IS NOT NULL` for explicit checks.
- `COALESCE(col, default)` when you want a fallback.
- `IS [NOT] DISTINCT FROM` for NULL-safe equality.
- Mark columns `NOT NULL` in DDL whenever possible — eliminates the problem at the source.
- Add explicit `NULLS LAST` in `ORDER BY`.

## Solution (SQL)

```sql
CREATE TABLE users (
  id      INT PRIMARY KEY,
  name    TEXT NOT NULL,
  email   TEXT,           -- nullable
  manager INT              -- nullable FK
);
INSERT INTO users VALUES
 (1,'Alice','a@x.com',NULL),
 (2,'Bob',  NULL,     1),
 (3,'Carol','c@x.com',1),
 (4,'Dave', NULL,     2);
```

```sql
-- 1. Users with no email — the right way
SELECT id FROM users WHERE email IS NULL;          -- ✓ Bob, Dave

-- 2. WRONG: silently empty result
SELECT id FROM users WHERE email = NULL;           -- 0 rows. Classic bug.

-- 3. Group users by manager — NULLs land in one bucket
SELECT manager, COUNT(*) FROM users GROUP BY manager;
-- NULL | 1   (Alice — top of org)
--    1 | 2   (Bob, Carol)
--    2 | 1   (Dave)

-- 4. COUNT(*) vs COUNT(col)
SELECT COUNT(*)     AS total,     -- 4
       COUNT(email) AS with_email -- 2 (NULL emails skipped)
FROM   users;

-- 5. NULL-safe equality (find duplicate (name, manager) pairs even when manager IS NULL)
SELECT a.id, b.id
FROM   users a JOIN users b
  ON   a.id < b.id
  AND  a.name = b.name
  AND  a.manager IS NOT DISTINCT FROM b.manager;
```

## Step-by-step dry run

`WHERE email = NULL`:

```
Alice (email='a@x.com'):   'a@x.com' = NULL → UNKNOWN → row rejected.
Bob (email=NULL):           NULL    = NULL → UNKNOWN → row rejected.
Carol (email='c@x.com'):   'c@x.com'= NULL → UNKNOWN → row rejected.
Dave  (email=NULL):         NULL    = NULL → UNKNOWN → row rejected.
```

Result: 0 rows. Every row's predicate evaluated to UNKNOWN, and `WHERE` keeps only TRUE.

Vs `WHERE email IS NULL`:

```
Alice → 'a@x.com' IS NULL → FALSE → reject.
Bob   →  NULL       IS NULL → TRUE  → keep.
Carol → 'c@x.com' IS NULL → FALSE → reject.
Dave  →  NULL       IS NULL → TRUE  → keep.
```

Result: Bob, Dave.

## How to think aloud in the interview
1. *"Quick reminder: `NULL = NULL` is UNKNOWN, not TRUE. WHERE keeps only TRUE rows, so any predicate involving `= NULL` filters everything out."*
2. *"For NULL checks, use `IS NULL` / `IS NOT NULL`. For NULL-safe equality, Postgres has `IS NOT DISTINCT FROM`; MySQL has `<=>`."*
3. *"In GROUP BY, all NULLs cluster into one group — even though they're not equal to each other. Standard quirk."*
4. *"`COUNT(*)` counts everything; `COUNT(col)` skips NULL. Pick deliberately."*
5. *"If the column is conceptually never NULL, declare it `NOT NULL` in DDL. Eliminates a whole class of bugs."*

## Important takeaways
- NULL = unknown, not missing.
- Three-valued logic: TRUE / FALSE / UNKNOWN.
- WHERE keeps only TRUE → UNKNOWN rows are dropped.
- `IS NULL` / `IS NOT NULL` are the only safe NULL tests with comparison semantics.
- `COALESCE`, `NULLIF`, `IS NOT DISTINCT FROM` are your toolbox.
- See `backend-data-prep/sql/01-sql-fundamentals.md` "NULLs" section for deeper theory.

## Variants
1. **`UNIQUE` and NULL.** "Why does my unique index allow 5 NULL rows?" — explain three-valued logic; recommend Postgres 15+ `NULLS NOT DISTINCT`.
2. **`CHECK` and NULL.** "Why doesn't `CHECK (age > 0)` reject NULL?" — UNKNOWN ≠ FALSE; add `NOT NULL` or `CHECK (age IS NOT NULL AND age > 0)`.
3. **JSONB NULL vs SQL NULL.** `'{"a":null}'::jsonb -> 'a'` returns `'null'::jsonb`, not SQL NULL. Use `->> 'a' IS NULL` carefully.

## Revision notes

> **NULL / 3VL cram block**
> - NULL = "unknown".
> - 3-valued logic: TRUE / FALSE / UNKNOWN.
> - `NULL = NULL` → UNKNOWN. Use `IS [NOT] NULL`.
> - WHERE rejects UNKNOWN and FALSE.
> - GROUP BY treats all NULLs as one group.
> - ORDER BY: Postgres `NULLS LAST` default for ASC; MySQL the opposite. Be explicit.
> - `COUNT(*)` counts all; `COUNT(col)` skips NULL; `SUM/AVG/MIN/MAX` skip NULL.
> - UNIQUE allows multiple NULLs (unless `NULLS NOT DISTINCT`).
> - CHECK passes NULL (UNKNOWN ≠ FALSE).
> - NULL-safe equality: `IS NOT DISTINCT FROM` (PG) / `<=>` (MySQL).
> - `NOT IN (NULL,…)` → always empty result. Use `NOT EXISTS`.
> - Toolbox: `COALESCE`, `NULLIF`, `IS NOT DISTINCT FROM`.
