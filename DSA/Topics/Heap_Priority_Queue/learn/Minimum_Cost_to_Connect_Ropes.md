# Minimum Cost to Connect Ropes — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Cost_to_Connect_Ropes.md`](../Minimum_Cost_to_Connect_Ropes.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/minimum-cost-to-connect-sticks/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **This is HUFFMAN coding's core algorithm.** The lesson: **for "min total cost of pairwise merges where cost = sum of merged elements," GREEDILY merge the TWO SMALLEST at each step. Min-heap is the perfect tool.** **Read [`Last_Stone_Weight.md`](./Last_Stone_Weight.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. Why ordering matters
3. The greedy: merge two smallest
4. Why this greedy is optimal (exchange argument)
5. The min-heap implementation
6. Code
7. Trace it
8. Common pitfalls
9. The shape — Huffman-style greedy

---

## 1. Read the problem

You have an array `sticks` of rope lengths. In ONE operation: pick two ropes, connect them into one. The cost = SUM of the two lengths.

Continue until ONE rope remains. Return the **MINIMUM TOTAL COST**.

**Example:** `sticks = [2, 4, 3]`. Multiple orderings:

- (2+4=6 → 6+3=9): total = 6 + 9 = **15**.
- (2+3=5 → 5+4=9): total = 5 + 9 = **14**. ← min!
- (4+3=7 → 7+2=9): total = 7 + 9 = **16**.

Return **14**.

Note: each rope's length, EACH TIME it's involved in a merge, contributes to that merge's cost. So we want LONG ROPES merged LAST (involved in FEWER total merges).

---

## 2. Why ordering matters

> **Mini-refresher: each rope contributes once per merge it's in.**
>
> A rope of length L combined in K merges contributes L × K to the total cost.
>
> To minimize total: SMALL ropes should be in MANY merges, LARGE ropes in FEW.
>
> Strategy: at each step, merge the TWO SMALLEST. This keeps large ropes out of intermediate sums as long as possible.

---

## 3. The greedy: merge two smallest

At each step:
1. Pop the two smallest ropes from a min-heap.
2. Combined = sum. Add to total cost.
3. Push combined back.

Continue until one rope left.

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

O(n log n) time. O(n) space.

---

## 4. Why this greedy is optimal (exchange argument)

> **Mini-refresher: exchange argument for Huffman-style greedy.**
>
> Suppose an optimal solution does NOT merge the two smallest first. Show we can REARRANGE to merge them first without increasing cost.
>
> Let `a`, `b` be the two smallest. Suppose optimal first merges `c`, `d` where `(c, d) ≠ (a, b)`.
>
> Swap: do `a + b` first, then incorporate `c, d` later. The intermediate sums change, but the FINAL ones don't (total length is preserved). Specifically, the SUM `a + b` is ≤ ANY OTHER pair sum, so using it as the FIRST sum minimizes how much "growing" carries forward.
>
> Total cost in the swapped version ≤ original. So always-merge-two-smallest is optimal.

This is the SAME argument used to prove Huffman coding's optimality.

---

## 5. The min-heap implementation

```
import heapq

heap = sticks.copy()
heapq.heapify(heap)         # O(n)
cost = 0
while len(heap) > 1:
    a = heapq.heappop(heap)
    b = heapq.heappop(heap)
    s = a + b
    cost += s
    heapq.heappush(heap, s)
return cost
```

`heapify` is O(n) (faster than n pushes).

---

## 6. Code

**C++:**

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

**Python:**

```python
import heapq

def connectSticks(sticks):
    heapq.heapify(sticks)
    cost = 0
    while len(sticks) > 1:
        a = heapq.heappop(sticks)
        b = heapq.heappop(sticks)
        s = a + b
        cost += s
        heapq.heappush(sticks, s)
    return cost
```

Complexity: **O(n log n) time, O(n) space.**

---

## 7. Trace it

**`sticks = [2, 4, 3]`:**

```
heap = [2, 3, 4] (min-heap).

Pop 2, pop 3. combined = 5. cost = 5. Push 5. heap = [4, 5].
Pop 4, pop 5. combined = 9. cost = 5 + 9 = 14. Push 9. heap = [9].

Size 1 → exit. Return 14.  ✓
```

**`sticks = [1, 8, 3, 5]`:**

```
heap = [1, 3, 5, 8].

Pop 1, pop 3. combined = 4. cost = 4. Push 4. heap = [4, 5, 8].
Pop 4, pop 5. combined = 9. cost = 4 + 9 = 13. Push 9. heap = [8, 9].
Pop 8, pop 9. combined = 17. cost = 13 + 17 = 30. Push 17. heap = [17].

Return 30.
```

Verify contributions:
- 1 is in 3 merges (steps 1, 2, 3): contribution 1 × 3 = 3.
- 3: 3 × 3 = 9.
- 5: 5 × 2 = 10.
- 8: 8 × 1 = 8.

Total: 3 + 9 + 10 + 8 = 30. ✓

The SMALLEST ropes (1, 3) participate in the most merges — but their contribution stays small. The LARGEST (8) participates only ONCE.

---

## 8. Common pitfalls

1. **Using a max-heap.** Merges largest first → maximum cost (opposite of what we want).

2. **Trying greedy on UNSORTED iteration.** Doesn't work — we need DYNAMIC access to "current smallest." That's heap territory.

3. **Forgetting to push the COMBINED rope back.** That rope MIGHT be merged again.

4. **Off-by-one in loop condition.** Continue while size > 1 (not ≥ 2 — both mean the same). Mistakes with size ≤ 0 are common.

5. **Computing combined more than once.** Compute once, then use in both `cost +=` and `push`.

6. **Building the heap one push at a time.** O(n log n) for the build vs O(n) for heapify. Use the latter.

---

## 9. The shape — Huffman-style greedy

The pattern:

> **"For 'minimize sum of merge costs where cost = sum of merged elements,' greedily merge the TWO SMALLEST at each step. Min-heap supports this in O(n log n)."**

| Problem | Application |
|---|---|
| **This problem** | rope lengths |
| Huffman coding | character frequencies → optimal prefix codes |
| Merge K sorted files (minimum I/O) | file sizes |
| Minimum cost to build a tree | weighted leaves |
| K-way merging cost | similar |

**Pattern to internalize:**

> "Greedy two-smallest = Huffman. When each step's cost equals the sum of the items, processing the smallest first minimizes how many times each item gets 'absorbed.'"

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Cost_to_Connect_Ropes.md`](../Minimum_Cost_to_Connect_Ropes.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Last_Stone_Weight.md`](./Last_Stone_Weight.md) — pop-pop-push family.
  - Coming next: Find_K_Pairs_with_Smallest_Sums, Kth_Smallest_in_Sorted_Matrix, Merge_K_Sorted_Lists, Find_Median.
