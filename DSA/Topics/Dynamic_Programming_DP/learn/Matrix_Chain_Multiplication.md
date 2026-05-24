# Matrix Chain Multiplication — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Matrix_Chain_Multiplication.md`](../Matrix_Chain_Multiplication.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/matrix-chain-multiplication-dp-8/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: THE INTERVAL DP template. `cost[i][j]` = min cost to multiply matrices i..j. Recurrence: try every SPLIT point k in (i, j); take min over `cost[i][k] + cost[k+1][j] + p[i-1]·p[k]·p[j]`. Fill by INCREASING chain length.**

**Map of this file (9 sections):**

1. Read the problem
2. Why multiplication ORDER matters
3. The "last multiplication" insight
4. Interval DP recurrence
5. Why fill by chain length
6. Code
7. Trace it
8. Common pitfalls
9. The shape — interval DP

---

## 1. Read the problem

Given dimensions `p[0], p[1], ..., p[n]` (matrix i has shape `p[i-1] × p[i]`), find the MIN scalar multiplications to multiply all n matrices.

Multiplying a `p × q` matrix by a `q × r` matrix costs `p · q · r` scalar mults and yields a `p × r` matrix.

**Example:** A is 10×30, B is 30×5, C is 5×60. Dimensions p = [10, 30, 5, 60].
- `(A·B)·C`: 10·30·5 + 10·5·60 = 1500 + 3000 = **4500**.
- `A·(B·C)`: 30·5·60 + 10·30·60 = 9000 + 18000 = 27000.

Best = 4500.

---

## 2. Why multiplication ORDER matters

Matrix multiplication is ASSOCIATIVE — different parenthesizations give the same RESULT — but the COSTS along the way differ wildly. Choosing the right order can be 10× cheaper.

---

## 3. The "last multiplication" insight

> **Mini-refresher: every parenthesization has a UNIQUE LAST multiplication.**
>
> The final mult combines TWO products: `(A_i · ... · A_k)` (shape `p[i-1] × p[k]`) and `(A_{k+1} · ... · A_j)` (shape `p[k] × p[j]`). The k is the SPLIT point.
>
> Cost = cost(left) + cost(right) + `p[i-1] · p[k] · p[j]`.
>
> So we try every k from i to j-1 and pick the min.

This "condition on the last operation" is the same DP trick as in many problems.

---

## 4. Interval DP recurrence

`cost[i][j]` = min cost to multiply matrices `A_i · ... · A_j`.

- Base: `cost[i][i] = 0`.
- For length 2..n:
  - For each (i, j) with j - i + 1 = length:
    ```
    cost[i][j] = min over k ∈ [i, j-1] of:
        cost[i][k] + cost[k+1][j] + p[i-1] · p[k] · p[j]
    ```

Answer: `cost[1][n]`.

---

## 5. Why fill by chain length

`cost[i][j]` depends on `cost[i][k]` and `cost[k+1][j]` — both have SHORTER chains than [i, j]. So when filling by INCREASING chain length, dependencies are already computed.

(Alternative: iterate `i` from `n` down to `1`, `j` from `i+1` up to `n`. Same effect.)

---

## 6. Code

**C++:**

```cpp
int matrixChainOrder(vector<int>& p) {
    int n = p.size() - 1;
    vector<vector<int>> cost(n + 1, vector<int>(n + 1, 0));

    for (int length = 2; length <= n; ++length) {
        for (int i = 1; i + length - 1 <= n; ++i) {
            int j = i + length - 1;
            cost[i][j] = INT_MAX;
            for (int k = i; k < j; ++k) {
                int trial = cost[i][k] + cost[k+1][j] + p[i-1] * p[k] * p[j];
                cost[i][j] = min(cost[i][j], trial);
            }
        }
    }
    return cost[1][n];
}
```

**Python:**

```python
def matrixChainOrder(p):
    n = len(p) - 1
    cost = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            cost[i][j] = float('inf')
            for k in range(i, j):
                trial = cost[i][k] + cost[k+1][j] + p[i-1] * p[k] * p[j]
                cost[i][j] = min(cost[i][j], trial)
    return cost[1][n]
```

Complexity: **O(n³)** time, **O(n²)** space.

---

## 7. Trace it

`p = [10, 30, 5, 60]`. n = 3 (matrices A, B, C).

Initial: cost[i][i] = 0.

**Length 2:**
- cost[1][2] = 0 + 0 + 10·30·5 = 1500.
- cost[2][3] = 0 + 0 + 30·5·60 = 9000.

**Length 3:**
- cost[1][3]: try k=1, k=2.
  - k=1: cost[1][1] + cost[2][3] + 10·30·60 = 0 + 9000 + 18000 = 27000.
  - k=2: cost[1][2] + cost[3][3] + 10·5·60 = 1500 + 0 + 3000 = 4500.
  - min = **4500**.  ✓

Return cost[1][3] = 4500.

---

## 8. Common pitfalls

1. **Indexing confusion.** Matrix i is `p[i-1] × p[i]`. The result of `A_i · ... · A_k` has shape `p[i-1] × p[k]`. Off-by-one is the #1 bug here.
2. **Wrong fill order.** Filling rows top-to-bottom or columns left-to-right doesn't respect dependencies. Use CHAIN LENGTH outer loop.
3. **Initializing `cost[i][i] != 0`.** Single matrix has no multiplications.
4. **Trying k from i+1 instead of from i.** Both endpoints of the split range are valid: k from i to j-1.
5. **Returning `cost[0][n-1]` (0-indexed).** Make sure your indexing convention is consistent throughout.
6. **Forgetting `INT_MAX` initialization.** Without it, `cost[i][j]` starts at 0, and the min comparison won't improve.

---

## 9. The shape — interval DP

The pattern: **state = (i, j) over a range; transition tries every SPLIT k in between.**

| Problem | Split cost |
|---|---|
| **This problem** | `p[i-1] · p[k] · p[j]` |
| Burst Balloons | balloon-burst score with k as LAST balloon |
| Palindrome Partitioning II | 0 if substring is palindrome |
| Optimal Binary Search Tree | sum of weights × depths |
| Stone Game variants | minimax over splits |
| Minimum Cost to Cut a Stick | length of the piece being cut |
| Strange Printer | string-printing minimization |

**Pattern to internalize:**

> "Interval DP: state `dp[i][j]`, try every split point k. The 'last operation' framing gives the recurrence. Fill by increasing chain length. O(n³)."

---

> **Self-check — the question to ask next time.**
>
> When the problem is "over a range/sequence, find optimal way to combine":
>
> > **"Interval DP. `dp[i][j]` = best for range. Try every split k. Fill chain-length first. O(n³)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Matrix_Chain_Multiplication.md`](../Matrix_Chain_Multiplication.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Palindromic_Subsequence.md`](./Longest_Palindromic_Subsequence.md).
  - Coming next: [`Unique_Binary_Search_Trees.md`](./Unique_Binary_Search_Trees.md), [`Maximal_Rectangle.md`](./Maximal_Rectangle.md), [`Dungeon_Game.md`](./Dungeon_Game.md), [`Numbers_at_Most_N_Given_Digit_Set.md`](./Numbers_at_Most_N_Given_Digit_Set.md).
