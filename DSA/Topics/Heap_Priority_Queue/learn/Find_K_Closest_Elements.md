# Find K Closest Elements — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_K_Closest_Elements.md`](../Find_K_Closest_Elements.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/find-k-closest-elements/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-k-closest-elements/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: when input is SORTED, the K closest elements form a CONTIGUOUS WINDOW. Binary-search for the window's LEFT BOUNDARY in O(log(n-k)).** Don't use a heap when the input is sorted — use the structure. **Read [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](../../Searching_Binary_Search/learn/Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. The heap approach (works but suboptimal)
3. Why the answer is a CONTIGUOUS WINDOW
4. Binary search the window's left edge
5. Code
6. Trace it
7. Common pitfalls
8. The shape — binary search on window position

---

## 1. Read the problem

Given a **SORTED** array `arr`, integer `k`, and integer `x`, return the **K CLOSEST** elements to `x`, in ASCENDING order.

Distance = `|arr[i] - x|`. Ties broken by preferring SMALLER values.

**Example:** `arr = [1, 2, 3, 4, 5]`, `k = 4`, `x = 3`.

Distances: |1-3|=2, |2-3|=1, |3-3|=0, |4-3|=1, |5-3|=2.

4 smallest distances: 0, 1, 1, 2 → values 3, 2, 4, 1. Sorted: `[1, 2, 3, 4]`.

(Tie at distance 2 between 1 and 5; prefer 1 because smaller.)

---

## 2. The heap approach (works but suboptimal)

Use a max-heap of size K keyed by distance. O(n log k).

```
heap = max-heap of size k, keyed by (distance, value)
for v in arr:
    push (|v - x|, v) onto heap
    if heap.size > k: pop
return sorted([v for _, v in heap])
```

Works on UNSORTED input. But we're ignoring that `arr` IS sorted — a missed opportunity.

---

## 3. Why the answer is a CONTIGUOUS WINDOW

> **Mini-refresher: K closest on sorted array = contiguous window.**
>
> Suppose the answer is some subset S of K elements from `arr`. Sort S by INDEX (they're already in arr-order). Let L be S's leftmost index, R be S's rightmost.
>
> **Claim:** S MUST CONSIST OF arr[L..R] — i.e., S is a contiguous slice.
>
> Why? Suppose some index `m` with `L < m < R` is NOT in S. Then `arr[m]` lies BETWEEN `arr[L]` and `arr[R]` (since sorted). So `arr[m]` is at most as far from x as max(distance from `arr[L]`, distance from `arr[R]`). But arr[L] and arr[R] are in S — meaning S contains an element at least as FAR as arr[m]. Replace that farther element with arr[m] → strict improvement. Contradiction.

So the K closest elements form a CONTIGUOUS slice `arr[L..L+k-1]`. We just need to find the right L.

---

## 4. Binary search the window's left edge

> **Mini-refresher: binary search on the WINDOW POSITION.**
>
> Possible windows: L = 0, 1, ..., n-k. For each L, the window is `arr[L..L+k-1]`.
>
> Compare the LEFT element `arr[L]` (distance `x - arr[L]`) to the element JUST PAST the window `arr[L+k]` (distance `arr[L+k] - x`):
> - If `x - arr[L] > arr[L+k] - x`: LEFT element is FARTHER. Shift window RIGHT — drop arr[L], gain arr[L+k].
> - Else: LEFT element is at least as close as the next-right element. Window's good as is (or better).
>
> Binary-search L in [0, n - k].

```
lo, hi = 0, n - k
while lo < hi:
    mid = (lo + hi) // 2
    if x - arr[mid] > arr[mid + k] - x:
        lo = mid + 1
    else:
        hi = mid
return arr[lo : lo + k]
```

**O(log(n - k)) time + O(k) for the output.**

> **Mini-refresher: tie-break direction.**
>
> When `x - arr[mid] == arr[mid + k] - x` (tie), we DON'T shift (use `else: hi = mid`, the strict-less-than `>` in the condition). This keeps the LEFTMOST window — preferring SMALLER values on ties.

---

## 5. Code

**C++:**

```cpp
vector<int> findClosestElements(vector<int>& arr, int k, int x) {
    int lo = 0, hi = arr.size() - k;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (x - arr[mid] > arr[mid + k] - x) lo = mid + 1;
        else hi = mid;
    }
    return vector<int>(arr.begin() + lo, arr.begin() + lo + k);
}
```

**Python:**

```python
def findClosestElements(arr, k, x):
    lo, hi = 0, len(arr) - k
    while lo < hi:
        mid = (lo + hi) // 2
        if x - arr[mid] > arr[mid + k] - x:
            lo = mid + 1
        else:
            hi = mid
    return arr[lo:lo + k]
```

Complexity: **O(log(n - k) + k) time, O(k) space.**

---

## 6. Trace it

**`arr = [1, 2, 3, 4, 5]`, `k = 4`, `x = 3`.**

`n = 5`, `n - k = 1`. So L ∈ [0, 1].

```
lo=0, hi=1.
mid=0. x - arr[0] = 3 - 1 = 2. arr[0+4] - x = 5 - 3 = 2. 2 > 2? NO. hi = 0.
Loop exits. L = 0.

Return arr[0:4] = [1, 2, 3, 4].  ✓
```

**`arr = [1, 2, 3, 4, 5]`, `k = 4`, `x = 4`.**

```
lo=0, hi=1.
mid=0. x - arr[0] = 4 - 1 = 3. arr[4] - x = 5 - 4 = 1. 3 > 1? YES. lo = 1.
Loop exits. L = 1.

Return arr[1:5] = [2, 3, 4, 5].  ✓
```

---

## 7. Common pitfalls

1. **Using a heap when input is sorted.** Wastes the sortedness. Binary search is faster.

2. **Comparing WITH absolute values.** Don't need — use `x - arr[mid]` and `arr[mid+k] - x` (subtracted in the natural direction; for sorted arr, these are unsigned distances).

3. **Off-by-one in `arr[mid + k]`.** This is the element JUST PAST the window's right edge. NOT `arr[mid + k - 1]`.

4. **Wrong tie-break direction.** `>` (strict) keeps the LEFTMOST window on ties. `>=` would shift to right on ties — wrong for "prefer smaller values."

5. **Initializing `hi = n` instead of `hi = n - k`.** L's max valid value is n - k (so window ends at n - 1).

6. **Forgetting to sort the output.** Since `arr[L:L+k]` is already sorted (the slice of a sorted array), no extra sort needed.

---

## 8. The shape — binary search on window position

The pattern:

> **"Binary-searching not over array INDICES but over a PARAMETER (here, the window's left edge). The 'monotonic structure' is in the comparison of window boundaries."**

| Problem | Binary-searched parameter |
|---|---|
| **This problem** | window's left index |
| Search Insert Position | the array index |
| Find First and Last Position | the boundary index |
| Koko Eating Bananas | eating rate K |
| Capacity to Ship Packages | ship capacity |
| Find Peak Element | the local max's index |

**Pattern to internalize:**

> "BINARY SEARCH can apply to PARAMETERS, not just array indices. If a monotonic comparison tells you which direction to move, binary-search it in O(log range)."

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_K_Closest_Elements.md`](../Find_K_Closest_Elements.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`K_Closest_Points_to_Origin.md`](./K_Closest_Points_to_Origin.md) — unsorted version, heap.
  - [`../../Searching_Binary_Search/learn/Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](../../Searching_Binary_Search/learn/Find_First_and_Last_Position_of_Element_in_Sorted_Array.md).
  - Coming next: [`Minimum_Cost_to_Connect_Ropes.md`](./Minimum_Cost_to_Connect_Ropes.md).
