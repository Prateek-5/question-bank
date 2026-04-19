# Quick Revision Guide

Short, skimmable reminders per topic. Use this before an interview or contest to refresh your mental model.

---

## Heap / Priority Queue
- Max-heap is default in C++; use `greater<>` for min-heap.
- Top-k: bounded heap of size k with opposite polarity to the target.
- Streaming median: two heaps balanced by size.
- Merge k sorted lists: push heads, pop-push next.
- Dijkstra's: `priority_queue` of `(distance, node)`.

## Math
- Digital root shortcut: `1 + (n-1) % 9`.
- Sums divisible by k: prefix-sum mod-count bucket.
- Euclid's GCD; LCM = a * b / gcd(a, b).
- Tournament matches = n - 1 (single elimination).
- GCD over array = fold with `__gcd`.

## Graph (BFS / DFS / Dijkstra / DSU)
- BFS → shortest unweighted path.
- Multi-source BFS → distance field to nearest source.
- DSU → components, cycle detection, equations.
- Bellman-Ford with K+1 iterations for "≤K stops".
- Topological sort = Kahn's BFS on in-degree.
- Bipartite = 2-coloring via BFS/DFS.

## BST
- In-order yields sorted keys.
- LCA: walk down comparing values until split.
- Balanced BST from sorted array: pick median recursively.
- BST iterator: stack holding left spine.
- Kth smallest: in-order with counter.

## Trees
- Post-order aggregates from children (height, sum, balance).
- Reconstruct from traversals using inorder-index map.
- Level order = BFS with level-size loop.
- Path sum III = prefix-sum on DFS path with hashmap.
- Invert = swap children recursively.

## Greedy
- Interval scheduling: sort by end time.
- Huffman-style pair the two smallest with a min-heap.
- Min platforms: sort arrivals/departures; sweep counts.
- Maximum product of 3 = max(top3, low2·top1) — beware negatives.

## 1-D & 2-D Arrays
- 1D flat index to 2D: `(i/n, i%n)`.
- Prefix sums for range sum in O(1).
- Running sum is in-place accumulation.
- Stair search on sorted-row/col matrix: top-right drop.

## Segment Tree / Range Queries
- Segment tree supports range query + update in O(log n).
- Lazy propagation: defer range updates until push on descent.
- Sparse table: immutable RMQ in O(1) after O(n log n) build.
- Fenwick/BIT: easier for prefix-sum mutations.

## Arrays & Matrices
- Trapping rain water: two-pointer min(maxLeft, maxRight).
- Maximum gap: bucket / pigeonhole sort.
- Spiral traversal: 4-boundary shrinkage.
- Max absolute value expression: 4 sign combos on prefix/suffix.

## Searching / Binary Search
- Binary search on answer: define `feasible(m)` monotonic.
- Rotated sorted array: detect which half is sorted.
- Find peak: compare mid with mid+1, shift accordingly.
- Capacity / rate problems: BS on minimum capacity.

## Two Pointers
- Sorted arrays: opposite-end shrink.
- Sliding window for contiguous constraints.
- Fast/slow pointers for middle, cycle, k-th from end.
- 3Sum = sort + fix-i + two-pointer.

## Linked List
- Dummy head simplifies edge cases.
- Floyd's tortoise-hare for cycle detection / middle.
- Reverse: walk with `prev=null` pointer.
- Palindrome: find middle, reverse half, compare.
- Remove nth-from-end: gap of n+1 pointers.

## Number Theory / Misc
- Count primes via Sieve of Eratosthenes.
- Divisor count via prime factorization.
- Fast exponentiation in O(log n).
- Divisor-pair parity determines perfect-square counting problems.
- Digit DP handles count-over-range.

## Trie / Bit Trie
- Standard trie for prefix queries and dictionary lookups.
- Bit trie for maximum XOR by greedy opposite-bit traversal.
- Use `suffix#prefix` trick for Prefix/Suffix search.
- Wildcard '.' via DFS over all 26 children.

## Dynamic Programming
- 1D: Climbing Stairs, House Robber, Min Cost.
- 2D: LCS, Edit Distance, Interleaving.
- Knapsack (0/1, unbounded, bounded sum).
- Interval DP for Matrix Chain, Palindrome Partitioning.
- LIS in O(n log n) via patience sorting.
- Space optimization: rolling arrays; often O(m) instead of O(n·m).

## Bit Manipulation
- XOR cancels pairs — Single Number.
- Bit counting via `n & (n-1)` loop.
- Reverse bits in 32 iterations.
- State-machine trick for Single Number II.

## Hashing / Sliding Window
- Subarray sum = k: prefix-sum count map with m[0]=1.
- Longest substring without repeats: last-index map.
- Min window substring: expand-then-shrink with need/have counts.
- Longest consecutive sequence: set-based anchor starts.

## Queues / Deque / Monotonic Queue
- Sliding window max: decreasing deque of indices.
- Gas station: total ≥ 0 ⇒ answer exists; reset start on negatives.
- Implement stack via 1-queue rotation; queue via 2 stacks.

## Stack
- Monotonic stack = next/previous greater or smaller.
- Valid parentheses: push opens, match closes, end empty.
- Largest histogram rectangle via stack of increasing bars.
- Reverse Polish evaluation.

## Recursion
- Backtracking: try, recurse, undo.
- Subset/permutation templates with skip-duplicate rule.
- N-Queens: track columns and two diagonal keys.
- Palindrome partitioning: DFS with palindrome check at each split.

## Backtracking
- Generate parentheses with open/close counts.
- Sudoku: bitmasks for rows/cols/boxes.
- Gray code: reflect-and-prefix or `i ^ (i >> 1)` formula.

## Sorting / Divide & Conquer
- Merge sort counting inversions / reverse pairs.
- Quickselect for k-th element in O(n) average.
- Dutch flag 3-way partition for 0/1/2 values.
- Counting/bucket sort for bounded integer keys.
