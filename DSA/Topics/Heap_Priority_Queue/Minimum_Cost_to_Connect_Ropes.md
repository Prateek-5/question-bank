# Minimum Cost to Connect Ropes

**Problem Link:**
<a href="https://leetcode.com/problems/minimum-cost-to-connect-sticks/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/minimum-cost-to-connect-sticks/</a>

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: The Rules

You have an array of rope lengths `sticks`. In one operation, you pick any **two ropes** of lengths x and y, connect them into one rope of length x + y. The **cost** of this operation is `x + y` — the combined length.

You keep connecting until a single rope remains. Return the **minimum total cost**.

Example: `sticks = [2, 4, 3]`.
- Option A: combine 2 and 4 → cost 6, remaining {6, 3}. Then 6 + 3 → cost 9. Total = 6 + 9 = **15**.
- Option B: combine 2 and 3 → cost 5, remaining {5, 4}. Then 5 + 4 → cost 9. Total = 5 + 9 = **14**.
- Option C: combine 4 and 3 → cost 7, remaining {7, 2}. Then 7 + 2 → cost 9. Total = 7 + 9 = **16**.

Minimum = **14** (option B).

Notice: every choice ends with a final cost of 9 (total length stays fixed = 2 + 4 + 3 = 9). The intermediate costs vary.

----------------------------------------

## Step 2: Why Intermediate Costs Matter

Think about a rope of length x. Every time x is involved in a combine, x contributes to that combine's cost. If x is combined early and then the result is combined again and again, x's length appears in every subsequent cost.

**Each rope's length gets added to the total cost once per time it's "absorbed" into a growing rope.** A rope combined once contributes only in that one step. A rope combined 5 times contributes 5 times.

If we want to minimize total cost, we want to combine **short ropes frequently** (they add little each time) and **long ropes rarely** (they add a lot each time).

The optimal strategy: **always combine the two shortest ropes first.** This keeps big ropes out of the mix until late, minimizing how many times they're re-added.

----------------------------------------

## Step 3: This Is Huffman Coding

The problem structure is **exactly Huffman coding**: repeatedly merging the two smallest elements. The optimality proof mirrors Huffman's classical proof (exchange argument).

Huffman's greedy: min-heap of frequencies; pop two smallest; push their sum. Repeat until one element left. Total work done = total cost.

Our problem maps one-to-one. The min-heap (priority queue) is the natural tool.

----------------------------------------

## Step 4: Algorithm

```
heap = min-heap of sticks
cost = 0
while heap.size() > 1:
    a = heap.pop()
    b = heap.pop()
    combined = a + b
    cost += combined
    heap.push(combined)
return cost
```

Each iteration reduces heap size by 1, so n-1 iterations. Each pop/push is O(log n). Total: **O(n log n)**.

----------------------------------------

## Step 5: Trace on `[2, 4, 3]`

```
heap = [2, 3, 4] (min-heap).
cost = 0.

Pop 2, pop 3. Combined = 5. cost = 5. Push 5. heap = [4, 5].

Pop 4, pop 5. Combined = 9. cost = 5 + 9 = 14. Push 9. heap = [9].

Size = 1, stop.
```

Total cost: **14**. ✓

Let's sanity check: the rope of length 2 was combined once (into 5). The 3 was combined once (into 5). The 4 was combined once (into 9). The intermediate 5 was combined once (into 9). So:
- 2 appears in cost of step 1 (5 → cost 5) and step 2 (as part of 5 inside 9 → cost 9). So 2 appears 2 times.
- 3 appears 2 times (same reason).
- 4 appears 1 time (only in step 2).

Total contribution: 2·2 + 3·2 + 4·1 = 4 + 6 + 4 = 14. ✓

The shortest sticks (2, 3) are combined early and thus appear more often — but since they're small, their total contribution stays small.

----------------------------------------

## Step 6: Trace on `[1, 8, 3, 5]`

```
heap = [1, 3, 5, 8]. cost = 0.

Pop 1, pop 3 → 4. cost = 4. heap = [4, 5, 8].
Pop 4, pop 5 → 9. cost = 4 + 9 = 13. heap = [8, 9].
Pop 8, pop 9 → 17. cost = 13 + 17 = 30. heap = [17].
```

Total = **30**.

Contribution check:
- 1 used in step 1, 2, 3 → 3 times.
- 3 used in step 1, 2, 3 → 3 times.
- 5 used in step 2, 3 → 2 times.
- 8 used in step 3 → 1 time.

Sum: 1·3 + 3·3 + 5·2 + 8·1 = 3 + 9 + 10 + 8 = 30. ✓

Notice: the smallest rope (1) is combined the most (3 times), but contributes only 3 to the cost. The largest (8) is combined only once (final step), contributing 8. Huffman's greedy is "feed small things into the furnace often, save the big ones."

----------------------------------------

## Step 7: Why "Always Pick Two Smallest" Is Optimal

Proof sketch (exchange argument): suppose the optimal combines c and d first, where c and d are NOT the two smallest. Let the two smallest be a and b.

You can swap: combine a and b first, then incorporate c and d later. Each subsequent combine's cost either decreases or stays the same. (The combined `a + b` is ≤ any other pair's sum, so using it first "carries" less forward.)

This exchange produces a strategy no worse than the original. By induction, always combining the two smallest is optimal.

----------------------------------------

## Step 8: Name It

**Huffman coding / greedy two-smallest merging**. A foundational algorithm.

Applications:
- Huffman coding for data compression.
- Minimum cost to merge k files.
- Tree construction where frequent symbols should be near the root.

Related problems:
- Merge k sorted lists (also min-heap but different structure — we pick min across heads, not the two smallest).
- Minimum cost to connect arrays.
- Build a Huffman tree.

----------------------------------------

## Step 9: Complexity

Time: **O(n log n)** — n-1 iterations, each with O(log n) heap ops.
Space: **O(n)** for the heap.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int connectSticks(vector<int>& sticks) {
    priority_queue<int, vector<int>, greater<int>> pq(sticks.begin(), sticks.end());
    int cost = 0;
    while (pq.size() > 1) {
        int a = pq.top(); pq.pop();
        int b = pq.top(); pq.pop();
        int combined = a + b;
        cost += combined;
        pq.push(combined);
    }
    return cost;
}
```

`priority_queue<..., greater<int>>` is a min-heap in C++. Build from the initial array, then loop merging the two smallest.

----------------------------------------

## Step 11: Follow-up Questions

- **Only one stick given.** Cost = 0 (no merging needed). The while loop naturally handles it.
- **Merge exactly k sticks at a time (instead of 2).** Pop k smallest, merge. Variant of k-way Huffman; same idea.
- **Maximize cost instead of minimize.** Combine two LARGEST (max-heap). Symmetric.
- **Return the sequence of merges.** Track each (a, b) merge as you go.
- **Large n (10^7).** Use array-based heap; same complexity, lower constants.
- **Why is this Huffman?** Because the cost equals the weighted path length from root to leaves in a binary tree, and Huffman minimizes exactly that.
