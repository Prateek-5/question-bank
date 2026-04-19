# DSA Cheat Sheet

One-page summaries: recognize the pattern, recall the recipe.

## Complexity Targets
| n                | Expected   |
|------------------|------------|
| ≤ 12             | O(n!)      |
| ≤ 25             | O(2^n)     |
| ≤ 500            | O(n³)      |
| ≤ 5,000          | O(n²)      |
| ≤ 10⁶            | O(n log n) |
| ≤ 10⁸            | O(n)       |

## Core Formulas
- Digital root: `1 + (n-1) % 9` for n > 0.
- Sum 1..n = `n(n+1)/2`.
- Sum of squares 1..n = `n(n+1)(2n+1)/6`.
- Number of subsets of size k in [n] = `C(n, k)`.
- Catalan number `C_n = C(2n, n) / (n+1)` — counts BSTs of size n.
- GCD(a, b) × LCM(a, b) = a · b.
- (a + b) mod m = ((a mod m) + (b mod m)) mod m.
- a^b mod m via binary exponentiation in O(log b).

## Bit Tricks
- `n & (n-1)` clears the lowest set bit.
- `n & -n` isolates the lowest set bit.
- Check power of two: `n && !(n & (n-1))`.
- Swap without temp: `a ^= b; b ^= a; a ^= b;`.
- `__builtin_popcount(x)` = number of set bits.

## Sorting Cheat
- `sort(a.begin(), a.end())` — introsort, O(n log n).
- `sort(a.begin(), a.end(), greater<int>())` — descending.
- Custom comparator must be strict weak ordering.
- Counting sort: O(n + range); good for small-range ints.

## Binary Search Recipe
```cpp
int lo = 0, hi = n - 1;
while (lo < hi) {
    int m = lo + (hi - lo) / 2;
    if (ok(m)) hi = m; else lo = m + 1;
}
// lo == smallest index with ok(m) true
```
For "largest index with ok" use `(lo + hi + 1) / 2` and swap branches.

## Pattern Pickers
| Clue                                                | Try                               |
|-----------------------------------------------------|-----------------------------------|
| "Subarray sum = k"                                  | Prefix-sum + hashmap              |
| "Contiguous window, constraint"                     | Sliding window                    |
| "Shortest steps in grid / graph"                    | BFS                               |
| "Weighted shortest path (no negatives)"             | Dijkstra                          |
| "Negative edges / limited stops"                    | Bellman-Ford                      |
| "Connectivity / components"                         | Union-Find or DFS                 |
| "Next greater / smaller"                            | Monotonic stack                   |
| "Top-k elements"                                    | Heap of size k / Quickselect      |
| "K-way merge"                                       | Min-heap of heads                 |
| "Overlapping subproblems"                           | DP                                |
| "All subsets / permutations"                        | Backtracking                      |
| "Range sum with updates"                            | Segment tree / BIT                |
| "LIS / patience sorting"                            | Binary search on tails            |
| "Matrix rotate 90°"                                 | Transpose + reverse rows          |
| "Cycle in linked list"                              | Floyd's tortoise-hare             |
| "Expression with parentheses"                       | Stack                             |
| "Game theory / win-lose recurrence"                 | DP / parity insight               |

## Recurrences to Recognize
- `f(n) = f(n-1) + f(n-2)` → Fibonacci / Climbing Stairs.
- `f(i, j) = f(i-1, j-1) + 1` when match else max of shifts → LCS / Edit Distance.
- `f(i) = max(a[i], f(i-1) + a[i])` → Kadane.
- `f(n) = Σ f(i) * f(n-1-i)` → Catalan / Unique BSTs.
- Interval DP: `f(i, j) = min_k f(i, k) + f(k+1, j) + merge_cost`.

## Graph Recipes
- Topological sort (Kahn): in-degree queue, pop and decrement.
- Dijkstra: min-heap, skip stale entries with `if (d > dist[u]) continue;`.
- Bellman-Ford with K+1 passes: shortest with ≤K+1 edges.
- Floyd-Warshall: `d[i][j] = min(d[i][j], d[i][k] + d[k][j])` with k outermost.
- MST: Kruskal (sort edges + DSU) or Prim (min-heap on frontier).

## Tree Recipes
- Balanced check: post-order height returning `-1` on imbalance.
- LCA (BT): if root matches p or q return root; else combine results.
- LCA (BST): walk down comparing values.
- Diameter: post-order returning height, update answer as `hL + hR`.

## String Tricks
- Anagram: 26-length char-count array.
- Palindrome: two-pointer from both ends.
- Longest palindromic subsequence: LCS(s, reverse(s)).
- KMP failure function for pattern matching.
- Z-array for pattern occurrences.

## Must-Remember Invariants
- Kadane's running sum never goes negative for long.
- In-order of a BST is sorted.
- Heap top is the current extremum.
- DSU's path compression keeps amortized α(n).
- BFS level = shortest unweighted distance.
