# Special Positions in a Binary Matrix — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Special_Positions_in_a_Binary_Matrix.md`](../Special_Positions_in_a_Binary_Matrix.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/special-positions-in-a-binary-matrix/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/special-positions-in-a-binary-matrix/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. This is the gateway to a powerful pattern: **precompute aggregates once, then answer queries in O(1)**. The pattern shows up in dozens of later problems (2D prefix sums, frequency maps, range queries, even ML feature engineering). The "special position" framing is just the excuse to teach it.

**Map of this file (10 short sections):**

1. Read the problem
2. Walk through small examples
3. The naive approach (and why it wastes work)
4. The pivot — precompute row and column sums
5. Why row-sum-of-1 plus column-sum-of-1 is the right test
6. Code
7. Trace it
8. Complexity comparison
9. Common pitfalls
10. The shape — "precompute once, query in O(1)" everywhere

---

## 1. Read the problem

You're given an `m × n` matrix `mat` where every cell is `0` or `1` (a **binary matrix**).

A position `(r, c)` is called **"special"** when ALL THREE of these hold:

1. `mat[r][c] == 1` (the cell itself contains a 1)
2. **Every other cell in row `r`** is `0` (no other 1 in this row)
3. **Every other cell in column `c`** is `0` (no other 1 in this column)

Return the **count of special positions**.

---

## 2. Walk through small examples

**Example A:**

```
mat =
  1 0 0
  0 0 1
  1 0 0
```

Let me check each cell that has `1`:

- `(0, 0) = 1`:
  - Row 0 = `[1, 0, 0]`. Just one 1 (at column 0). ✓
  - Column 0 = `[1, 0, 1]`. **Two 1s** (rows 0 and 2). ✗
  - Not special.

- `(1, 2) = 1`:
  - Row 1 = `[0, 0, 1]`. Just one 1. ✓
  - Column 2 = `[0, 1, 0]`. Just one 1. ✓
  - **Special.**

- `(2, 0) = 1`:
  - Row 2 = `[1, 0, 0]`. Just one 1. ✓
  - Column 0 = `[1, 0, 1]`. **Two 1s.** ✗
  - Not special.

Count = **1**.

**Example B:**

```
mat =
  1 0 0
  0 1 0
  0 0 1
```

Every cell on the main diagonal is `1`, and each row and column has exactly one `1`. All three are special.

Count = **3**.

So "special" means the `1` is **uniquely alone in its row AND uniquely alone in its column**.

---

## 3. The naive approach (and why it wastes work)

The most literal translation:

```cpp
int numSpecial(vector<vector<int>>& mat) {
    int m = mat.size(), n = mat[0].size();
    int count = 0;
    for (int r = 0; r < m; r++) {
        for (int c = 0; c < n; c++) {
            if (mat[r][c] != 1) continue;
            // Check row r for other 1s
            bool rowOk = true;
            for (int cc = 0; cc < n; cc++) {
                if (cc != c && mat[r][cc] == 1) { rowOk = false; break; }
            }
            if (!rowOk) continue;
            // Check column c for other 1s
            bool colOk = true;
            for (int rr = 0; rr < m; rr++) {
                if (rr != r && mat[rr][c] == 1) { colOk = false; break; }
            }
            if (colOk) count++;
        }
    }
    return count;
}
```

For each cell with value `1`, we scan its entire row (n operations) and its entire column (m operations). So for each "1" cell that's a candidate, we do O(m + n) work.

In the worst case (mostly 1s), there are up to `m × n` candidates, giving total work **O(m × n × (m + n))** — roughly `O(n³)` for square matrices. For `n = 100`, that's `10⁶` — fine. For `n = 1000`, that's `10⁹` — TLE risk.

**Pivot question:** can we avoid scanning each row and column from scratch every time?

Look at the work. The same row (say row 5) gets scanned many times — once for every `1` in it. The same column likewise. We're redoing the same sums.

**What if we compute each row sum and each column sum just ONCE, then look them up?**

---

## 4. The pivot — precompute row and column sums

> **Mini-refresher: aggregate precomputation.**
>
> When a query "is row `r` clean?" (or "what's the sum of row `r`?") gets asked many times, computing the answer from scratch each time wastes work. The fix is: **compute the answer for every row once, store the m results in an array. Look up the answer in O(1).**
>
> Same for columns.
>
> The tradeoff: you pay O(m × n) upfront to build the arrays (one full sweep of the matrix). After that, every query is O(1). For problems that issue many queries, the upfront cost amortizes to nothing per query.

Define:

```
rowSum[r] = number of 1s in row r       (m of these, sized [m])
colSum[c] = number of 1s in column c    (n of these, sized [n])
```

How to compute them? One sweep of the matrix, adding each cell's value to its row's running sum AND to its column's running sum:

```
initialize rowSum[i] = 0 for all i
initialize colSum[j] = 0 for all j

for r in 0..m-1:
    for c in 0..n-1:
        rowSum[r] += mat[r][c]
        colSum[c] += mat[r][c]
```

One pass over the matrix → O(m × n) time. Storage is O(m + n).

Now, for each cell `(r, c)`:

- "Is row r clean except possibly at (r, c)?" ← row has exactly one 1, and it's at this cell ← `rowSum[r] == 1` AND `mat[r][c] == 1`
- Same for column: `colSum[c] == 1` AND `mat[r][c] == 1`

So the special check becomes:

```
mat[r][c] == 1 AND rowSum[r] == 1 AND colSum[c] == 1
```

Three O(1) lookups. No more scanning rows/columns per cell.

---

## 5. Why row-sum-of-1 plus column-sum-of-1 is the right test

Let me be careful here — there's a subtle reasoning step.

A cell `(r, c)` is **special** when:
- `mat[r][c] == 1`
- The only `1` in row `r` is at column `c` (no other column has a 1 in this row).
- The only `1` in column `c` is at row `r`.

Claim: `rowSum[r] == 1 AND mat[r][c] == 1` together imply "the only 1 in row r is at column c."

Proof: `rowSum[r]` counts all 1s in row r. If it equals 1, there's exactly one 1 in the row. And we know one of them is at `(r, c)` (since `mat[r][c] == 1`). So the only 1 in row r is at column c. ✓

Symmetrically for the column.

So the three conditions are:

```
mat[r][c] == 1
AND rowSum[r] == 1
AND colSum[c] == 1
```

All three together. If any is false, the cell isn't special.

---

## 6. Code

```cpp
int numSpecial(vector<vector<int>>& mat) {
    int m = mat.size(), n = mat[0].size();

    // Step 1: precompute row sums and column sums
    vector<int> rowSum(m, 0);
    vector<int> colSum(n, 0);
    for (int r = 0; r < m; r++) {
        for (int c = 0; c < n; c++) {
            rowSum[r] += mat[r][c];
            colSum[c] += mat[r][c];
        }
    }

    // Step 2: check each cell with the three-part test
    int count = 0;
    for (int r = 0; r < m; r++) {
        for (int c = 0; c < n; c++) {
            if (mat[r][c] == 1 && rowSum[r] == 1 && colSum[c] == 1) {
                count++;
            }
        }
    }

    return count;
}
```

Two passes through the matrix:

- **First pass** fills `rowSum` and `colSum` simultaneously. Single nested loop.
- **Second pass** checks each cell against the three-part test using only O(1) lookups.

Both passes are O(m × n). Total: **O(m × n) time, O(m + n) extra space.**

---

## 7. Trace it

```
mat =
  1 0 0
  0 0 1
  1 0 0
```

**Step 1: build rowSum and colSum.**

```
Start:  rowSum = [0, 0, 0],  colSum = [0, 0, 0]

(r=0, c=0): mat=1.  rowSum[0]+=1 → 1.  colSum[0]+=1 → 1.
(r=0, c=1): mat=0.  rowSum[0]+=0.      colSum[1]+=0.
(r=0, c=2): mat=0.  rowSum[0]+=0.      colSum[2]+=0.
(r=1, c=0): mat=0.  rowSum[1]+=0.      colSum[0]+=0.
(r=1, c=1): mat=0.  rowSum[1]+=0.      colSum[1]+=0.
(r=1, c=2): mat=1.  rowSum[1]+=1 → 1.  colSum[2]+=1 → 1.
(r=2, c=0): mat=1.  rowSum[2]+=1 → 1.  colSum[0]+=1 → 2.
(r=2, c=1): mat=0.  rowSum[2]+=0.      colSum[1]+=0.
(r=2, c=2): mat=0.  rowSum[2]+=0.      colSum[2]+=0.

After Step 1:
  rowSum = [1, 1, 1]
  colSum = [2, 0, 1]
```

**Step 2: count special positions.**

```
count = 0.

(r=0, c=0): mat=1, rowSum[0]=1, colSum[0]=2.  All == 1? colSum[0] is 2. → not special.
(r=0, c=1): mat=0. → not special.
(r=0, c=2): mat=0. → not special.
(r=1, c=0): mat=0. → not special.
(r=1, c=1): mat=0. → not special.
(r=1, c=2): mat=1, rowSum[1]=1, colSum[2]=1.  All == 1? YES. → SPECIAL. count = 1.
(r=2, c=0): mat=1, rowSum[2]=1, colSum[0]=2.  colSum[0] is 2. → not special.
(r=2, c=1): mat=0.
(r=2, c=2): mat=0.

Return count = 1.  ✓
```

Matches the hand-counted answer from §2.

---

## 8. Complexity comparison

**Naive:**

- Time: O(m × n × (m + n)). For square matrix `n = 100`: 10⁶ ops. For `n = 1000`: 10⁹ ops (slow).
- Space: O(1).

**Precomputed:**

- Time: O(m × n). For `n = 1000`: 10⁶ ops. **1000× faster** at this size.
- Space: O(m + n). Cheap.

The precompute version is strictly better on every dimension that matters (except a tiny bit of extra memory). For LeetCode's constraints (small matrices), both pass — but the lesson is the technique, not the speed.

---

## 9. Common pitfalls

1. **Forgetting to check `mat[r][c] == 1` before checking the sums.** A cell with `mat[r][c] == 0` could still have `rowSum[r] == 1` and `colSum[c] == 1` (the 1 in this row is at some other column, and the 1 in this column is at some other row). The "special" definition requires the cell itself to BE the 1.

2. **Adding `mat[r][c]` to ONLY rowSum or ONLY colSum on the first pass.** Both arrays need updating per cell. The first loop should add the same value to both.

3. **Mixing up `m` and `n`.** Rows are indexed `0..m-1`; columns are `0..n-1`. `rowSum` has size `m`, not `n`. Always re-check.

4. **Confusing "exactly one 1" with "at least one 1".** The special check uses `== 1`, not `>= 1`. A row with two 1s fails the check.

5. **Trying to merge the two passes into one.** It's tempting to compute sums AND check specials in one pass, but you'd need the full row/col sums before checking — which requires finishing the matrix scan. The clean version uses two passes. (A clever single-pass version is possible but loses clarity for no real win.)

6. **Recomputing sums in the second pass.** Once `rowSum` and `colSum` are built, just look them up. Don't re-sum.

---

## 10. The shape — "precompute once, query in O(1)" everywhere

The pattern from this problem — **build aggregate structures up front, then answer many queries against them quickly** — is one of the most generally useful techniques in algorithms. It appears in:

| Problem / Domain | What gets precomputed | Query becomes |
|---|---|---|
| **This problem** | row sums, column sums | check (r, c) is special in O(1) |
| Range Sum Query Immutable | 1D prefix sums | sum(l..r) in O(1) |
| Range Sum Query 2D Immutable | 2D prefix sums | sum of any submatrix in O(1) |
| Subarray Sum Equals K | prefix sum + hash of seen prefixes | count subarrays in O(n) |
| Find Smallest Letter Greater Than Target | sorted array | binary search in O(log n) |
| Lookup tables in compilers, JIT | translation tables | symbol → address in O(1) |
| ML feature engineering | precomputed counts, means, embeddings | model query is O(1) per feature |
| Database indexes (B-trees, hash indexes) | sorted/hashed structure | row lookup in O(log n) or O(1) |
| Caching layers | result of expensive compute | repeat queries are O(1) |

**Pattern to internalize:**

> "When the same expensive question is asked many times, compute the answer ONCE — preprocess into a structure that answers in O(1) — and then issue queries cheaply."

Knowing when to reach for precomputation is half the battle. The other half is choosing the right structure (sum array? hash map? sorted list? tree?). For "row and column membership" — like this problem — separate `rowSum` and `colSum` arrays are perfect.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem where **the same aggregate question is asked of many cells / positions / queries**, before nesting loops to recompute, ask:
>
> > **"Can I precompute the aggregate once (in O(m × n) or O(n)) and then answer each query in O(1)?"**
>
> If yes, you've replaced a quadratic-or-worse approach with a linear-preprocess + constant-per-query approach. This is the difference between "passes the small test" and "passes the large test."

---

## Cross-references

- **Reference card (post-mastery):** [`../Special_Positions_in_a_Binary_Matrix.md`](../Special_Positions_in_a_Binary_Matrix.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) (the 1D version of "precompute once, query in O(1)")
  - [`Richest_Customer_Wealth.md`](./Richest_Customer_Wealth.md) (simpler 2D scan, no precompute needed)
  - Coming later: Range_Sum_Query_2D_Immutable — generalizes this pattern to arbitrary submatrix sums via 2D prefix sums.
