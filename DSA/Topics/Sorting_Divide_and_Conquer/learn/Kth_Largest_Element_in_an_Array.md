# Kth Largest Element in an Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Kth_Largest_Element_in_an_Array.md`](../Kth_Largest_Element_in_an_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/kth-largest-element-in-an-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/kth-largest-element-in-an-array/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The introduction to Quickselect — the divide-and-conquer sibling of quicksort.** The lesson: **partition around a pivot, then recurse only into ONE side (the side containing the target rank). Average O(n).** Compare with the heap-based O(n log k) approach (Heap topic). **Read [`Sort_Colors.md`](./Sort_Colors.md) first** for the partition mindset.

**Map of this file (11 sections):**

1. Read the problem
2. The full-sort baseline
3. The quicksort partition insight
4. Recursing into ONLY ONE side
5. The partition function (Lomuto)
6. Code
7. Trace it
8. Why average O(n)
9. Random pivot (mandatory)
10. Common pitfalls
11. The shape — quickselect family

---

## 1. Read the problem

Given an integer array `nums` and an integer `k`, return the **k-th LARGEST** element in `nums`.

Note: it's the k-th largest in SORTED order — duplicates count as separate ranks.

**Examples:**

- `nums = [3, 2, 1, 5, 6, 4]`, `k = 2` → sorted descending `[6, 5, 4, 3, 2, 1]` → 2nd largest = **5**.
- `nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]`, `k = 4` → sorted desc `[6, 5, 5, 4, 3, 3, 2, 2, 1]` → 4th = **4**.
- `nums = [1]`, `k = 1` → **1**.

---

## 2. The full-sort baseline

Sort the array, return `nums[n - k]` (in ascending order, the k-th largest is at index `n - k`).

```python
def findKthLargest(nums, k):
    nums.sort()
    return nums[len(nums) - k]
```

**O(n log n) time.** Simple. Often accepted in interviews.

But we're computing a FULL sort just to read one rank. Can we do better?

---

## 3. The quicksort partition insight

> **Mini-refresher: quicksort's partition step.**
>
> Quicksort picks a PIVOT element. It rearranges the array so:
> - Elements LESS than the pivot are on the LEFT.
> - The pivot itself is at some final position.
> - Elements GREATER (or equal) are on the RIGHT.
>
> After partition, the pivot is at its FINAL sorted position. Then quicksort recurses on both sides.

**Key insight for our problem:** after partition, the PIVOT's final position tells us its rank!

If we want the element at ascending-index `target = n - k`, and after partition the pivot lands at index `p`:
- If `p == target`: the pivot IS our answer.
- If `p < target`: our target is to the RIGHT of p. Recurse RIGHT only.
- If `p > target`: target is LEFT of p. Recurse LEFT only.

Unlike quicksort, we recurse into ONLY ONE SIDE. That's the magic.

---

## 4. Recursing into ONLY ONE side

If each partition cuts the problem in roughly half, and we recurse on only one side:

```
work = n + n/2 + n/4 + ... ≈ 2n = O(n)
```

vs quicksort's `O(n log n)` (recurses on both sides at each level).

**Average case O(n).** This is the speedup.

Worst case (bad pivot choices on adversarial inputs): O(n²). Mitigated by RANDOM pivot.

> **Mini-refresher: why "only one side" is correct.**
>
> After partition with pivot at index p, ALL elements LEFT of p are LESS than the pivot, and ALL elements RIGHT are ≥. So if your target index is in `[lo, p-1]`, you know with certainty it's in the LEFT side. The RIGHT side cannot contain the target. Skip it.

---

## 5. The partition function (Lomuto)

The Lomuto partition scheme:

```
partition(nums, lo, hi, pivot_idx):
    pivot = nums[pivot_idx]
    swap nums[pivot_idx] and nums[hi]      # move pivot to the END temporarily
    store = lo
    for i in lo..hi-1:
        if nums[i] < pivot:
            swap nums[i] and nums[store]
            store += 1
    swap nums[store] and nums[hi]           # bring pivot to its final position
    return store
```

**How it works:**
1. Move the pivot to position `hi` (out of the way).
2. Walk `i` through `[lo, hi - 1]`. Maintain `store` = "next free slot for elements < pivot."
3. When we find an element < pivot, swap it to the `store` position, advance `store`.
4. At the end, swap the pivot from `hi` back into `store`. Now `store` is the pivot's final position.

After partition: `nums[lo..store-1]` < pivot, `nums[store] == pivot`, `nums[store+1..hi]` ≥ pivot.

> **Mini-refresher: Lomuto vs Hoare partition.**
>
> Two famous partition schemes:
> - **Lomuto**: simpler code; uses one pointer; pivot at end during partition; degrades on many duplicates.
> - **Hoare**: two pointers crossing inward; faster in practice; handles duplicates better; more complex code.
>
> For interviews, Lomuto is the safer bet — easier to write correctly under pressure.

---

## 6. Code

**C++:**

```cpp
class Solution {
    int partition(vector<int>& nums, int lo, int hi, int pivotIdx) {
        int pivot = nums[pivotIdx];
        swap(nums[pivotIdx], nums[hi]);
        int store = lo;
        for (int i = lo; i < hi; ++i) {
            if (nums[i] < pivot) {
                swap(nums[i], nums[store]);
                store++;
            }
        }
        swap(nums[store], nums[hi]);
        return store;
    }

    int quickselect(vector<int>& nums, int lo, int hi, int target) {
        if (lo == hi) return nums[lo];
        int pivotIdx = lo + rand() % (hi - lo + 1);    // RANDOM pivot
        pivotIdx = partition(nums, lo, hi, pivotIdx);
        if (pivotIdx == target) return nums[target];
        if (pivotIdx < target) return quickselect(nums, pivotIdx + 1, hi, target);
        return quickselect(nums, lo, pivotIdx - 1, target);
    }

public:
    int findKthLargest(vector<int>& nums, int k) {
        return quickselect(nums, 0, nums.size() - 1, nums.size() - k);
    }
};
```

**Python:**

```python
import random

def findKthLargest(nums, k):
    def partition(lo, hi, pivot_idx):
        pivot = nums[pivot_idx]
        nums[pivot_idx], nums[hi] = nums[hi], nums[pivot_idx]
        store = lo
        for i in range(lo, hi):
            if nums[i] < pivot:
                nums[i], nums[store] = nums[store], nums[i]
                store += 1
        nums[store], nums[hi] = nums[hi], nums[store]
        return store

    def quickselect(lo, hi, target):
        if lo == hi:
            return nums[lo]
        pivot_idx = random.randint(lo, hi)
        pivot_idx = partition(lo, hi, pivot_idx)
        if pivot_idx == target:
            return nums[target]
        if pivot_idx < target:
            return quickselect(pivot_idx + 1, hi, target)
        return quickselect(lo, pivot_idx - 1, target)

    return quickselect(0, len(nums) - 1, len(nums) - k)
```

Complexity:
- **Average: O(n)**.
- **Worst: O(n²)** (very rare with random pivot).
- **Space: O(log n)** recursion depth on average.

---

## 7. Trace it

**`nums = [3, 2, 1, 5, 6, 4]`, `k = 2`.**

Target ascending index = `6 - 2 = 4` (the 2nd largest sits at index 4 in sorted order).

```
quickselect(0, 5, 4).
Say random pivot_idx = 3 (value 5).
partition(0, 5, 3):
  Move 5 to position 5. Array becomes [3, 2, 1, 4, 6, 5].
  Walk i=0..4. store starts at 0.
    i=0: nums[0]=3 < 5? YES. Swap (no-op). store=1.
    i=1: nums[1]=2 < 5? YES. Swap (no-op). store=2.
    i=2: nums[2]=1 < 5? YES. Swap (no-op). store=3.
    i=3: nums[3]=4 < 5? YES. Swap (no-op). store=4.
    i=4: nums[4]=6 < 5? NO.
  Swap nums[4] and nums[5] → Array [3, 2, 1, 4, 5, 6]. Pivot at index 4.
Return 4.

pivotIdx (4) == target (4). Return nums[4] = 5.  ✓
```

(Different random pivots would give different traces, but same end result.)

---

## 8. Why average O(n)

> **Mini-refresher: T(n) for quickselect.**
>
> Suppose each partition splits the range into two parts, on average each of size ~n/2.
>
> Recurrence: `T(n) = T(n/2) + O(n)` (n work for partition, then recurse on ONE half).
>
> Solving: `T(n) = n + n/2 + n/4 + ... ≈ 2n = O(n)`.
>
> Worst case (always pivot is the smallest or largest): `T(n) = T(n-1) + O(n) = O(n²)`. This happens on sorted input with first-element pivot. Random pivot makes this nearly impossible.

---

## 9. Random pivot (mandatory)

Without random pivot, an adversarial input (e.g., already sorted) can force O(n²) behavior:

```
nums = [1, 2, 3, 4, 5, 6, ...]. Pivot = last (or first).
Each partition only "removes" the pivot — partition size shrinks by 1.
Total: n + (n-1) + (n-2) + ... = O(n²).
```

**Random pivot** ensures expected O(n). In interview code, ALWAYS use random selection (or median-of-3 for a deterministic improvement).

For TRULY deterministic O(n) worst-case: median-of-medians (BFPRT). Conceptually elegant but rarely needed in interviews.

---

## 10. Common pitfalls

1. **Forgetting to randomize the pivot.** O(n²) on sorted input. Always randomize.

2. **Wrong target index.** k-th LARGEST in ascending order is at index `n - k`. K-th SMALLEST is at `k - 1`. Don't confuse.

3. **Partition off-by-one.** Both Lomuto endpoints (lo, hi) are INCLUSIVE. The loop runs `i < hi` (exclusive of hi).

4. **Recursing into BOTH sides.** That's quicksort. Quickselect recurses only into the side containing the target.

5. **Not handling the lo == hi base case.** Without it, infinite recursion when the range is a single element.

6. **Using `<=` instead of `<` in partition.** With `<=`, the pivot itself ends up on the wrong side. Use strict `<`.

7. **Mixing Lomuto and Hoare.** Don't half-and-half; pick one scheme and stay consistent.

8. **Worrying about worst case.** With random pivot, expected case is O(n). Don't over-engineer with median-of-medians unless explicitly asked.

9. **Modifying input array.** Quickselect modifies in place. If the caller cares, copy first.

10. **Confusing this with the heap-based solution.** Heap-based is O(n log k); quickselect is O(n) average. Different complexity profiles.

---

## 11. The shape — quickselect family

Where quickselect applies:

| Problem | Target |
|---|---|
| **This problem** | k-th largest = index `n - k` |
| k-th smallest | index `k - 1` |
| Median of an array | index `n / 2` |
| Top k elements (return all k) | after quickselect at index `n - k`, take elements [n-k, n-1] |
| k-th most frequent element | apply quickselect on (frequency, value) pairs |
| Range selection (find all elements in rank range) | quickselect twice |

**Pattern to internalize:**

> "Need a SINGLE rank (or a range cap) without full sorting? Use quickselect. Partition until the pivot lands at the target index. Average O(n)."

Quickselect appears whenever "I only need the top-k or k-th element" — a common selection task.

---

> **Self-check — the question to ask next time.**
>
> When you need the k-th element (largest/smallest/median) and don't need a full sort, ask:
>
> > **"Can I use quickselect? Pick a random pivot, partition, recurse into the side containing the target."**
>
> If yes, you've got O(n) average vs O(n log n) for full sort.

---

## Cross-references

- **Reference card (post-mastery):** [`../Kth_Largest_Element_in_an_Array.md`](../Kth_Largest_Element_in_an_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Sort_Colors.md`](./Sort_Colors.md) — Dutch flag, 3-way partition.
  - Coming next: [`Minimum_Number_of_Bottles_Visible.md`](./Minimum_Number_of_Bottles_Visible.md), [`Reverse_Pairs.md`](./Reverse_Pairs.md).
  - Heap topic's `Kth_Largest` — same problem with the heap approach. Compare.
