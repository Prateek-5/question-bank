# Matrix Chain Multiplication

**Problem Link:**
<a href="https://www.geeksforgeeks.org/matrix-chain-multiplication-dp-8/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/matrix-chain-multiplication-dp-8/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Recall Matrix Multiplication

Multiplying a `p × q` matrix by a `q × r` matrix yields a `p × r` matrix and requires `p · q · r` scalar multiplications.

Note that **order of multiplication matters for cost**, even though the result is the same (matrix multiplication is associative but not commutative). Example:

Three matrices: A is 10×30, B is 30×5, C is 5×60.
- `(A · B) · C`: A·B is 10×5 (cost 10·30·5 = 1500). Then (10×5)·(5×60) = 10×60 (cost 10·5·60 = 3000). Total = **4500**.
- `A · (B · C)`: B·C is 30×60 (cost 30·5·60 = 9000). Then (10×30)·(30×60) (cost 10·30·60 = 18000). Total = **27000**.

The *order* we multiply dramatically changes the cost. The problem: given dimensions `p[0], p[1], ..., p[n]` (so matrix i is `p[i-1] × p[i]`), find the **minimum** total cost to multiply all n matrices.

----------------------------------------

## Step 2: Hand-Computing for Small Cases

**n = 1**: a single matrix, no multiplications needed. Cost 0.

**n = 2**: one multiplication. Cost `p[0] · p[1] · p[2]`. No choice.

**n = 3**: two multiplications. Two orderings:
- `(A·B)·C`: cost = `p[0]·p[1]·p[2] + p[0]·p[2]·p[3]`.
- `A·(B·C)`: cost = `p[1]·p[2]·p[3] + p[0]·p[1]·p[3]`.

Pick the cheaper.

**n = 4**: three multiplications. Five orderings (Catalan(3) = 5). Enumerating gets tedious fast — that's the combinatorial explosion.

For general n, there are **Catalan(n-1)** orderings. Brute force is exponential.

----------------------------------------

## Step 3: The Structural Insight

Consider multiplying matrices `A_i · A_{i+1} · ... · A_j`. Any valid ordering can be described by the **last multiplication**: at some split point `k`, we compute `(A_i · ... · A_k)` and `(A_{k+1} · ... · A_j)` separately, then multiply these two.

The result of `A_i · ... · A_k` has dimensions `p[i-1] × p[k]`.
The result of `A_{k+1} · ... · A_j` has dimensions `p[k] × p[j]`.
Final multiplication: `p[i-1] × p[k] × p[j]` scalar multiplications.

So the cost with split at k is:
```
cost(i, k) + cost(k+1, j) + p[i-1] · p[k] · p[j]
```

where `cost(i, j)` is the min cost to multiply `A_i · ... · A_j`.

To find `cost(i, j)`, try every possible split k from i to j-1 and pick the min.

```
cost(i, j) = min over k in [i, j-1] of:
    cost(i, k) + cost(k+1, j) + p[i-1] · p[k] · p[j]
```

Base: `cost(i, i) = 0` (a single matrix needs no multiplications).

----------------------------------------

## Step 4: DP by Chain Length

The subproblems form a 2D structure indexed by (i, j) with i ≤ j. Since `cost(i, j)` depends on smaller ranges, we iterate by increasing chain length.

```
for length in 2..n:
    for i in 1..n - length + 1:
        j = i + length - 1
        cost[i][j] = ∞
        for k in i..j-1:
            trial = cost[i][k] + cost[k+1][j] + p[i-1] * p[k] * p[j]
            cost[i][j] = min(cost[i][j], trial)
return cost[1][n]
```

Length starts at 2 (any chain of length 1 is trivially 0). For each length, we fill all pairs (i, j) with that chain length.

----------------------------------------

## Step 5: Trace on p = [10, 30, 5, 60]

n = 3 (matrices A, B, C with the dimensions I gave in Step 1).

```
cost[i][i] = 0 for all i.

Length 2:
  cost[1][2] = cost[1][1] + cost[2][2] + p[0]·p[1]·p[2] = 0 + 0 + 10·30·5 = 1500.
  cost[2][3] = 0 + 0 + p[1]·p[2]·p[3] = 30·5·60 = 9000.

Length 3:
  cost[1][3]: try k=1 and k=2.
    k=1: cost[1][1] + cost[2][3] + p[0]·p[1]·p[3] = 0 + 9000 + 10·30·60 = 27000.
    k=2: cost[1][2] + cost[3][3] + p[0]·p[2]·p[3] = 1500 + 0 + 10·5·60 = 4500.
    min = 4500.
```

`cost[1][3] = 4500`. ✓ (Matches our hand calculation for (A·B)·C.)

The DP correctly identifies that splitting after matrix 2 (i.e., (A·B)·C) is cheaper than splitting after matrix 1 (A·(B·C)).

----------------------------------------

## Step 6: Why It's an Interval DP

The state `cost[i][j]` represents an interval of the chain `[i, j]`. The recurrence splits the interval at every possible k, recursing on two smaller intervals and combining their results with a fixed cost.

This shape — **interval DP** — appears in many problems:
- Matrix Chain Multiplication (this).
- Burst Balloons.
- Palindrome Partitioning (min cuts).
- Optimal Binary Search Tree.
- Stone Game variants.

The key pattern: **state = (left, right) of an interval**; transition tries every split point k in between.

----------------------------------------

## Step 7: Name It

**Matrix Chain Multiplication** is *the* textbook interval DP. The recurrence "try every split k, take min" is the paradigm. Once you recognize it, you recognize it in every interval-based problem.

Complexity analysis:
- States: O(n²) pairs (i, j).
- Per-state work: O(n) split points to try.
- Total: O(n³).

For typical chain sizes (n ≤ few hundred), this is very tractable.

----------------------------------------

## Step 8: Complexity

Time: **O(n³)**.
Space: **O(n²)** for the DP table.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int matrixChainOrder(vector<int>& p) {
    int n = p.size() - 1;   // number of matrices
    vector<vector<int>> cost(n + 1, vector<int>(n + 1, 0));

    // cost[i][i] = 0 for all i (single matrix, no multiplications)
    for (int length = 2; length <= n; ++length) {
        for (int i = 1; i + length - 1 <= n; ++i) {
            int j = i + length - 1;
            cost[i][j] = INT_MAX;
            for (int k = i; k < j; ++k) {
                int trial = cost[i][k] + cost[k + 1][j] + p[i - 1] * p[k] * p[j];
                cost[i][j] = min(cost[i][j], trial);
            }
        }
    }
    return cost[1][n];
}
```

Reading the code:
- 1-indexed matrices (matrix i uses dimensions `p[i-1] × p[i]`). The 0-index of `p` is the first dimension of matrix 1.
- Outer loop: chain length from 2 (smallest non-trivial) up to n.
- Inner loop: starting index i.
- Innermost: split point k.

----------------------------------------

## Step 10: Follow-up Questions

- **Reconstruct the optimal parenthesization.** Track the best split `k` at each (i, j); recurse to print.
- **O(n log n) algorithm?** Exists (Hu and Shing 1981), but extremely complex. O(n³) DP is the standard.
- **Cost function other than `p[i-1] · p[k] · p[j]`.** Same DP shape, plug in whatever combine-cost you have.
- **Chain with variable numbers of matrices (multiple chains to pick from).** 2D or 3D DP with additional choice dimension.
- **What's the best way to explain this in 60 seconds?** "Interval DP: pick the last multiplication, compute left and right parts optimally, combine with cost of their product."
- **Variation: Burst Balloons.** A different interval DP where we pick the *last* balloon to burst; the reasoning flips cleverly but follows the same skeleton.
