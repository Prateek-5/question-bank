# Find K Pairs with Smallest Sums

**Problem Link:**
https://leetcode.com/problems/find-k-pairs-with-smallest-sums/

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Read the Problem

You have two sorted integer arrays `nums1` and `nums2` (both ascending), and an integer `k`. Return the `k` pairs `(u, v)` with `u` from `nums1` and `v` from `nums2` having the **smallest sums**.

Example: `nums1 = [1, 7, 11]`, `nums2 = [2, 4, 6]`, k = 3.

All pairs and sums:
- (1, 2) = 3
- (1, 4) = 5
- (1, 6) = 7
- (7, 2) = 9
- (7, 4) = 11
- (7, 6) = 13
- (11, 2) = 13
- (11, 4) = 15
- (11, 6) = 17

Sorted by sum: 3, 5, 7, 9, 11, 13, 13, 15, 17.

Top 3 smallest: (1,2), (1,4), (1,6).

Return these three pairs.

----------------------------------------

## Step 2: Naive Approach

Enumerate all pairs (n × m of them), sort by sum, take the first k. Time: O(n·m · log(n·m)). Space: O(n·m).

For small inputs, fine. For large n, m (say 10^5 each), we'd be enumerating 10^10 pairs — completely infeasible.

We need something smarter that exploits the fact that **both arrays are sorted**.

----------------------------------------

## Step 3: A Useful Mental Picture — 2D Grid of Sums

Imagine a grid where cell (i, j) holds `nums1[i] + nums2[j]`. Because both arrays are sorted:
- Moving right (increasing j): sums increase (nums2 is sorted).
- Moving down (increasing i): sums increase (nums1 is sorted).

So the grid is "monotone" in both directions. The **smallest sum** is at (0, 0). The **k smallest sums** form some staircase shape in the top-left.

Visualizing:
```
(0,0)=3   (0,1)=5   (0,2)=7
(1,0)=9   (1,1)=11  (1,2)=13
(2,0)=13  (2,1)=15  (2,2)=17
```

Top 3 smallest are (0,0), (0,1), (0,2) — the first row's first three. Fits the answer.

In general the k smallest won't all be on one row — they form a more complex shape. We need to efficiently explore the grid in sum order.

----------------------------------------

## Step 4: Exploring the Grid in Sum Order — Use a Min-Heap

Here's the key idea. Start at (0, 0) — definitely the smallest sum. Push it into a min-heap keyed on sum. Then pop the smallest (that's one of our answers), and push its "neighbors" — (i+1, j) and (i, j+1) — into the heap.

Repeat k times.

This is BFS-style exploration of the grid in sum order. Crucially, we only ever push neighbors of popped cells, so we don't enumerate the full grid.

Gotcha: we might push the same cell from multiple predecessors. E.g., (1, 1) could be pushed from (0, 1) or (1, 0). To avoid duplicates, **maintain a visited set**.

```
heap = min-heap
seen = empty set

push (nums1[0] + nums2[0], 0, 0)
seen.add((0, 0))

result = []
while result.size < k and heap is not empty:
    (sum, i, j) = heap.pop()
    result.append((nums1[i], nums2[j]))
    if i + 1 < n and (i + 1, j) not in seen:
        push (nums1[i+1] + nums2[j], i+1, j); seen.add((i+1, j))
    if j + 1 < m and (i, j + 1) not in seen:
        push (nums1[i] + nums2[j+1], i, j+1); seen.add((i, j+1))

return result
```

At any point, the heap contains "frontier" cells — cells that are candidates for the next smallest. We always pop the truly smallest.

----------------------------------------

## Step 5: Trace on the Example

nums1 = [1, 7, 11], nums2 = [2, 4, 6], k = 3.

```
heap: [(3, 0, 0)]. seen: {(0, 0)}.

Pop (3, 0, 0). result = [(1, 2)]. Push (1+4=5, 0, 1) and (7+2=9, 1, 0). seen: +{(0,1), (1,0)}.
heap: [(5, 0, 1), (9, 1, 0)].

Pop (5, 0, 1). result = [(1, 2), (1, 4)]. Push (1+6=7, 0, 2) and (7+4=11, 1, 1). seen: +{(0,2), (1,1)}.
heap: [(7, 0, 2), (9, 1, 0), (11, 1, 1)].

Pop (7, 0, 2). result = [(1, 2), (1, 4), (1, 6)]. 
(0, 3) out of bounds for nums2. Push (7+6=13, 1, 2). seen: +{(1,2)}.
heap: [(9, 1, 0), (11, 1, 1), (13, 1, 2)].

result.size == 3 == k. Stop.
```

Return `[(1, 2), (1, 4), (1, 6)]`. ✓

----------------------------------------

## Step 6: Why This Works Correctly

**Invariant:** at any moment, the heap contains all the "frontier" cells — cells whose predecessors have been popped but they themselves haven't. The smallest-sum frontier cell is the next overall smallest unpopped cell.

**Claim:** when we pop a cell, it's the next smallest among all unpopped cells.

*Proof sketch:* Any unpopped cell either is in the frontier (and thus in the heap) or is some descendant of a frontier cell. Descendants have sums ≥ their ancestor's sum (monotonicity). So the min of the frontier ≤ min of unpopped overall. Popping the heap top gives us that min.

This is the standard argument for grid-BFS-by-priority.

----------------------------------------

## Step 7: Complexity

Time: we pop k times. Each pop: O(log heap-size). Heap size is bounded by O(k) (we push at most 2 per pop, so heap grows by at most 1 per pop). Total: **O(k log k)**.
Space: O(k) for heap and seen set.

Dramatic improvement over O(n·m log(n·m)) for small k.

----------------------------------------

## Step 8: An Even Cleaner Initialization

An alternative: seed the heap with the first column `(nums1[0..min(k,n)-1] + nums2[0], i, 0)`. Then we only ever push "right" (j+1), never "down." Avoids the visited set because each cell can only be reached by a single path.

```
for i in 0..min(k, n)-1:
    push (nums1[i] + nums2[0], i, 0)

for _ in 1..k:
    (sum, i, j) = heap.pop()
    result.append((nums1[i], nums2[j]))
    if j + 1 < m:
        push (nums1[i] + nums2[j+1], i, j+1)
```

This is a clever compression. Equivalent result, no `seen` tracking.

Why does it work? Every cell (i, j) is reached through exactly one path: start at (i, 0), go right j steps. No duplicates possible.

----------------------------------------

## Step 9: Name It

This is **multi-source BFS / k-way merge in a priority queue**. In fact, we can view the problem as merging sorted sequences:
- For each i, the sequence `nums1[i] + nums2[0], nums1[i] + nums2[1], ..., nums1[i] + nums2[m-1]` is sorted (since nums2 is sorted).
- We have n such sequences. Merging them and taking the first k elements is classic k-way merge.

The heap-based technique is the same pattern as Merge K Sorted Lists: one head from each list, pop the smallest, advance that list.

----------------------------------------

## Step 10: C++ Implementation

Clean version with "seed first column, advance right only":

```cpp
vector<vector<int>> kSmallestPairs(vector<int>& nums1, vector<int>& nums2, int k) {
    int n = nums1.size(), m = nums2.size();
    // Priority queue: (sum, i, j)
    using T = tuple<int, int, int>;
    priority_queue<T, vector<T>, greater<T>> pq;

    for (int i = 0; i < min(k, n); ++i) {
        pq.push({nums1[i] + nums2[0], i, 0});
    }

    vector<vector<int>> result;
    while (!pq.empty() && (int)result.size() < k) {
        auto [sum, i, j] = pq.top(); pq.pop();
        result.push_back({nums1[i], nums2[j]});
        if (j + 1 < m) {
            pq.push({nums1[i] + nums2[j + 1], i, j + 1});
        }
    }
    return result;
}
```

Notes:
- `min(k, n)` avoids seeding more than we need.
- `tuple<int,int,int>` with `greater<>` makes a min-heap keyed on the first element (the sum).
- The loop exits when we've collected k pairs or run out of candidates.

----------------------------------------

## Step 11: Follow-up Questions

- **Both arrays infinite / very long.** Works — the heap version only explores enough cells to fill k.
- **Three sorted arrays instead of two.** Generalize the grid to 3D; push "right," "down," "forward" neighbors (with visited tracking).
- **K largest sums.** Symmetric — start at the bottom-right, expand toward top-left, use max-heap.
- **Count pairs whose sum ≤ threshold (not top-k).** Different problem — binary search or two-pointer sweep.
- **Unsorted arrays.** Sort them first, O(n log n + m log m), then apply this algorithm.
- **Guarantee exactly k pairs (not fewer).** Problem usually assumes n·m ≥ k; if fewer, return whatever's available.
