# Queue Reconstruction by Height — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Queue_Reconstruction_by_Height.md`](../Queue_Reconstruction_by_Height.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/queue-reconstruction-by-height/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **A clever GREEDY problem.** The lesson: **sort people TALLEST FIRST, then INSERT each at position k. Shorter people inserted later DON'T DISTURB taller-already-placed counts.** A classic "process in a smart order so later inserts don't break invariants." **Read [`Sort_Colors.md`](../../Sorting_Divide_and_Conquer/learn/Sort_Colors.md) for greedy intuition.**

**Map of this file (9 short sections):**

1. Read the problem
2. Why it's not just sort
3. The "tallest first" insight
4. Why later inserts don't break k
5. Within-same-height ordering
6. Code
7. Trace it
8. Common pitfalls
9. The shape — order-of-processing tricks

---

## 1. Read the problem

You have a list of people. Each is described as `[h, k]`:
- `h`: their HEIGHT.
- `k`: the COUNT of people IN FRONT of them in the queue who are at LEAST AS TALL.

The queue is shuffled. Reconstruct the queue.

**Example:** `people = [[7,0], [4,4], [7,1], [5,0], [6,1], [5,2]]`.

Reconstructed queue:
```
[[5,0], [7,0], [5,2], [6,1], [4,4], [7,1]]
```

Verify [4,4]: in front are [5,0], [7,0], [5,2], [6,1] — all height ≥ 4. Count = 4. ✓

---

## 2. Why it's not just sort

Sorting by height alone doesn't determine where each person goes — we need to compute their EXACT INDEX based on k.

But k depends on WHICH OTHER PEOPLE ARE IN FRONT — circular dependency if we don't process in the right order.

We need an ordering of inserts such that each person, when placed, has its k condition immediately satisfied.

---

## 3. The "tallest first" insight

> **Mini-refresher: process tallest first.**
>
> Sort people: by HEIGHT DESCENDING, with k ASCENDING within the same height.
>
> Process the sorted list one at a time. For each person `[h, k]`:
> - INSERT them at INDEX `k` in the answer list.

When we place `[h, k]`, ALL already-placed people are TALLER OR EQUAL (we sorted descending). Putting this person at index k means EXACTLY k taller-or-equal people are in front. ✓

```
result = []
for [h, k] in sorted_people:
    result.insert(k, [h, k])
return result
```

---

## 4. Why later inserts don't break k

> **Mini-refresher: later (shorter) inserts don't disturb earlier k counts.**
>
> After we place `[h, k]` at index k, later inserts are SHORTER (or equal-with-smaller-k). What if a shorter person inserts at index ≤ k?
>
> The taller person moves to index k+1. Now there are k+1 people in front of them. But the new entry is SHORTER, so it does NOT count toward this person's k. The k taller-or-equal people are STILL the k people positioned at front. **k is preserved.**

This is the magical invariant: later, shorter inserts don't affect earlier, taller people's k. The "tallest first" ordering breaks the dependency cycle.

---

## 5. Within-same-height ordering

For two people of the SAME height, why sort by k ASCENDING?

Consider two people of height 7: `[7, 0]` and `[7, 1]`.

- `[7, 0]` should be placed FIRST (lower k → fewer people in front of equal/taller).
- `[7, 1]` placed AFTER.

If we processed `[7, 1]` first: place at index 1. But there's nothing yet → index 0 only. Off-by-one.

By processing `[7, 0]` first (placed at index 0), then `[7, 1]` (placed at index 1), both correctly land.

**Sort by `(h DESC, k ASC)`.**

---

## 6. Code

**C++:**

```cpp
vector<vector<int>> reconstructQueue(vector<vector<int>>& people) {
    sort(people.begin(), people.end(), [](const vector<int>& a, const vector<int>& b) {
        if (a[0] != b[0]) return a[0] > b[0];     // height descending
        return a[1] < b[1];                         // k ascending within same height
    });

    vector<vector<int>> result;
    for (auto& p : people) {
        result.insert(result.begin() + p[1], p);
    }
    return result;
}
```

**Python:**

```python
def reconstructQueue(people):
    people.sort(key=lambda p: (-p[0], p[1]))
    result = []
    for p in people:
        result.insert(p[1], p)
    return result
```

Complexity: **O(n²) time** (n inserts at arbitrary positions in a list, each O(n)), **O(n) space.**

For O(n log n), use a balanced BST with order-statistic queries — but the naive O(n²) is fine for typical n ≤ 1000.

---

## 7. Trace it

**`people = [[7,0], [4,4], [7,1], [5,0], [6,1], [5,2]]`.**

Sort by (-h, k):

```
[(7, 0), (7, 1), (6, 1), (5, 0), (5, 2), (4, 4)]
```

Insert into result:

```
Insert [7, 0] at index 0: [[7,0]].
Insert [7, 1] at index 1: [[7,0], [7,1]].
Insert [6, 1] at index 1: [[7,0], [6,1], [7,1]].
Insert [5, 0] at index 0: [[5,0], [7,0], [6,1], [7,1]].
Insert [5, 2] at index 2: [[5,0], [7,0], [5,2], [6,1], [7,1]].
Insert [4, 4] at index 4: [[5,0], [7,0], [5,2], [6,1], [4,4], [7,1]].
```

**Final:** `[[5,0], [7,0], [5,2], [6,1], [4,4], [7,1]]`. ✓

Verify [4, 4]: in front are [5,0], [7,0], [5,2], [6,1] — all ≥ 4 (heights 5, 7, 5, 6). Count = 4. ✓

---

## 8. Common pitfalls

1. **Sorting by k first.** Wrong — height-descending is the primary order.

2. **Sorting by height ASCENDING.** Then taller people inserted later would push earlier (shorter) ones — destroying their k.

3. **Sorting by k DESCENDING within same height.** Wrong order; off-by-one.

4. **Forgetting that "≥" includes equal heights.** k counts taller-OR-EQUAL people in front, not strictly taller.

5. **Trying to use a sliding window or two-pointer.** This is a placement problem with global structure; greedy + sort is the right approach.

6. **Underestimating insertion cost.** `list.insert(k, x)` is O(n) — overall O(n²). For larger n, use a more sophisticated data structure.

---

## 9. The shape — order-of-processing tricks

The pattern:

> **"For greedy placement problems with mutual constraints, find an ORDER OF PROCESSING such that each placement immediately satisfies its constraint AND LATER PLACEMENTS DON'T DISTURB EARLIER ONES."**

| Problem | Process in order... |
|---|---|
| **This problem** | tallest first, k ascending within |
| Interval Scheduling (Maximum) | sort by end time, pick greedily |
| Activity Selection | similar — sort by end time |
| Job Sequencing with Deadlines | sort by profit DESC, fill earliest deadline |
| Course Schedule II | topological sort (process prerequisites first) |
| Two-pointer on sorted data | left-right pointers exploit ordering |

**Pattern to internalize:**

> "When constraints depend on neighbors, look for an ordering where you can place items ONE AT A TIME without violating constraints for already-placed items."

---

## Cross-references

- **Reference card (post-mastery):** [`../Queue_Reconstruction_by_Height.md`](../Queue_Reconstruction_by_Height.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Convert_Sorted_Array_to_BST.md`](./Convert_Sorted_Array_to_BST.md), [`Range_Sum_of_BST.md`](./Range_Sum_of_BST.md).
  - BST topic complete (will be marked after this).
