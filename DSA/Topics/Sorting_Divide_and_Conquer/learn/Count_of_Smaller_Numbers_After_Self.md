# Count of Smaller Numbers After Self — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Count_of_Smaller_Numbers_After_Self.md`](../Count_of_Smaller_Numbers_After_Self.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/count-of-smaller-numbers-after-self/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~24 minutes. **The lesson: use merge sort on INDICES (not values) so you can track per-element contributions during the merge.** When a right-half index is placed before a left-half index in the merge, the right-half element is "smaller AND originally to the right" of the left-half element — exactly what we want to count. **Read [`Reverse_Pairs.md`](./Reverse_Pairs.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. The brute force
3. Connection to inversion counting (per-element variant)
4. Merge sort on INDICES, not values
5. The counting step during merge
6. Code
7. Trace it
8. The Fenwick-tree alternative
9. Common pitfalls
10. The shape — per-element merge-sort counting

---

## 1. Read the problem

Given an integer array `nums`, return a new array `counts` where `counts[i]` is the **number of elements TO THE RIGHT of `nums[i]` that are STRICTLY LESS than `nums[i]`**.

**Examples:**

- `nums = [5, 2, 6, 1]` → `counts = [2, 1, 1, 0]`.
  - i=0 (5): right is [2, 6, 1]. Smaller: {2, 1}. Count 2.
  - i=1 (2): right is [6, 1]. Smaller: {1}. Count 1.
  - i=2 (6): right is [1]. Smaller: {1}. Count 1.
  - i=3 (1): right is []. Count 0.

---

## 2. The brute force

```
counts = [0] * n
for i in 0..n-1:
    for j in i+1..n-1:
        if nums[j] < nums[i]:
            counts[i] += 1
return counts
```

O(n²). For n = 10⁵, that's 10¹⁰ ops — TLE.

We need O(n log n).

---

## 3. Connection to inversion counting (per-element variant)

This problem is a PER-ELEMENT version of inversion counting. Instead of returning a single TOTAL count, we return how many inversions involve EACH index.

The same merge-sort framework applies, but we need to TRACK WHICH LEFT-HALF ELEMENT gets credited each time a right-half element is placed before it.

---

## 4. Merge sort on INDICES, not values

The twist: we can't merge-sort the VALUES directly, because shuffling values loses the original positions. Instead, **merge sort an array of INDICES**, comparing by `nums[index]`.

Initial setup:
```
indices = [0, 1, 2, ..., n-1]
counts = [0, 0, ..., 0]
```

The merge sort recursively sorts `indices[lo..hi]` by their nums-values. During each merge:
- Two sorted halves of `indices`: left is `indices[lo..mid]`, right is `indices[mid+1..hi]`.
- Crucially: every original index in `right` is GREATER (in original-position order) than every original index in `left`. So elements in `right` are "to the RIGHT" of elements in `left`.

When we merge sorted-by-value, right-half elements that are SMALLER (in value) get placed first. Each such placement means: "this right-half element is smaller than the remaining left-half elements AND originally to the right of them."

So: when we place a LEFT-half element `indices[i]`, the number of right-half elements already placed before it = `j - (mid + 1)`. Those are all "smaller AND to the right" → add to `counts[indices[i]]`.

---

## 5. The counting step during merge

```
def merge(indices, lo, mid, hi, nums, counts):
    merged = []
    i, j = lo, mid + 1
    while i <= mid and j <= hi:
        if nums[indices[i]] <= nums[indices[j]]:
            # placing a left index. Number of right elements already placed = j - (mid + 1).
            counts[indices[i]] += (j - (mid + 1))
            merged.append(indices[i])
            i += 1
        else:
            merged.append(indices[j])
            j += 1
    while i <= mid:
        counts[indices[i]] += (j - (mid + 1))     # all of right placed
        merged.append(indices[i])
        i += 1
    while j <= hi:
        merged.append(indices[j])
        j += 1
    # write merged back to indices[lo..hi]
    for k, v in enumerate(merged):
        indices[lo + k] = v
```

When we place left[i], `j - (mid + 1)` is the count of right-half elements already placed (and therefore SMALLER in value AND to the RIGHT in original position). Credit it.

---

## 6. Code

**C++:**

```cpp
class Solution {
    vector<int> counts;
    vector<int> nums;

    void mergeSort(vector<int>& indices, int lo, int hi) {
        if (lo >= hi) return;
        int mid = (lo + hi) / 2;
        mergeSort(indices, lo, mid);
        mergeSort(indices, mid + 1, hi);

        vector<int> merged;
        int i = lo, j = mid + 1;
        while (i <= mid && j <= hi) {
            if (nums[indices[i]] <= nums[indices[j]]) {
                counts[indices[i]] += (j - mid - 1);
                merged.push_back(indices[i++]);
            } else {
                merged.push_back(indices[j++]);
            }
        }
        while (i <= mid) {
            counts[indices[i]] += (j - mid - 1);
            merged.push_back(indices[i++]);
        }
        while (j <= hi) {
            merged.push_back(indices[j++]);
        }
        for (int k = 0; k < (int)merged.size(); ++k) {
            indices[lo + k] = merged[k];
        }
    }

public:
    vector<int> countSmaller(vector<int>& input) {
        nums = input;
        int n = nums.size();
        counts.assign(n, 0);
        vector<int> indices(n);
        iota(indices.begin(), indices.end(), 0);
        mergeSort(indices, 0, n - 1);
        return counts;
    }
};
```

**Python:**

```python
def countSmaller(nums):
    n = len(nums)
    counts = [0] * n
    indices = list(range(n))

    def merge_sort(lo, hi):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        merge_sort(lo, mid)
        merge_sort(mid + 1, hi)

        merged = []
        i, j = lo, mid + 1
        while i <= mid and j <= hi:
            if nums[indices[i]] <= nums[indices[j]]:
                counts[indices[i]] += j - mid - 1
                merged.append(indices[i])
                i += 1
            else:
                merged.append(indices[j])
                j += 1
        while i <= mid:
            counts[indices[i]] += j - mid - 1
            merged.append(indices[i])
            i += 1
        while j <= hi:
            merged.append(indices[j])
            j += 1
        indices[lo:hi + 1] = merged

    merge_sort(0, n - 1)
    return counts
```

Complexity: **O(n log n) time, O(n) space.**

---

## 7. Trace it

**`nums = [5, 2, 6, 1]`.**

```
Initial: indices = [0, 1, 2, 3]. counts = [0, 0, 0, 0].

Split: [0, 1] and [2, 3].

Left side: split [0] and [1]. Merge [0] (value 5) with [1] (value 2):
  i=0, j=1: nums[0]=5 > nums[1]=2. Place right (index 1). j=2.
  i=0, j=2: only left left. counts[0] += j - mid - 1 = 2 - 1 - 1 = 0... 
  Wait, let me redo. mid = 0, so j - mid - 1 = j - 1.

Let me restart cleanly. For merge(0, 0, 1):
  mid = 0. left is [indices[0]=0]. right is [indices[1]=1]. j starts at 1.
  
  i=0, j=1: nums[indices[i]] = nums[0] = 5. nums[indices[j]] = nums[1] = 2.
    5 > 2 → place right (1). merged = [1]. j = 2.
  i=0, j=2: while loop exits (j > hi). Drain left.
  Drain i=0: counts[0] += j - mid - 1 = 2 - 0 - 1 = 1. merged = [1, 0]. i=1.
  indices[0..1] = [1, 0]. counts = [1, 0, 0, 0].

Right side: merge(2, 2, 3):
  mid = 2. left = [indices[2]=2]. right = [indices[3]=3].
  i=2, j=3: nums[2]=6, nums[3]=1. 6 > 1 → place right. merged=[3]. j=4.
  Drain i: counts[2] += 4 - 2 - 1 = 1. merged=[3, 2]. 
  indices[2..3] = [3, 2]. counts = [1, 0, 1, 0].

Top merge(0, 1, 3):
  mid = 1. left = indices[0..1] = [1, 0]. right = indices[2..3] = [3, 2].
  Values: nums[1]=2, nums[0]=5 (left side); nums[3]=1, nums[2]=6 (right side).
  
  i=0, j=2: nums[indices[0]] = nums[1] = 2. nums[indices[2]] = nums[3] = 1.
    2 > 1 → place right (3). merged=[3]. j=3.
  i=0, j=3: nums[1]=2 vs nums[indices[3]] = nums[2] = 6. 2 <= 6 → place left.
    counts[1] += j - mid - 1 = 3 - 1 - 1 = 1. counts=[1, 1, 1, 0].
    merged=[3, 1]. i=1.
  i=1, j=3: nums[indices[1]] = nums[0] = 5 vs nums[2] = 6. 5 <= 6 → place left.
    counts[0] += 3 - 1 - 1 = 1. counts=[2, 1, 1, 0].
    merged=[3, 1, 0]. i=2.
  Drain right (i > mid): merged=[3, 1, 0, 2].

Return counts = [2, 1, 1, 0].  ✓
```

---

## 8. The Fenwick-tree alternative

An alternative O(n log n) approach uses a **Binary Indexed Tree (BIT)** on coordinate-compressed values:

```
coord-compress nums to ranks in [0, n)
bit = BIT of size n (zero-initialized)

for i from n-1 downto 0:
    counts[i] = bit.query(rank[i] - 1)    # count of values with rank < rank[i] already seen
    bit.update(rank[i], +1)               # add this value to the BIT
```

Iterating right-to-left, for each element we ask "how many smaller values have already been processed (i.e., are to my right)?" Then we add this element to the BIT.

Both approaches are O(n log n). BIT is sometimes faster in practice but requires the BIT data structure (covered in the Segment Tree topic).

---

## 9. Common pitfalls

1. **Sorting VALUES instead of INDICES.** Then you lose original positions and can't credit per-element counts.

2. **Counting AFTER merging.** Same as Reverse Pairs — count BEFORE losing the half-distinction.

3. **Crediting the wrong element.** When you place a LEFT element, count how many RIGHT elements have ALREADY been placed (they're smaller AND to the right). When you place a RIGHT element, no credit is given (we're not asked about the right-side perspective).

4. **Off-by-one in `j - mid - 1`.** This is the count of right-half elements ALREADY in `merged`, computed as "current j minus the original start of right half." Mid is the END of the left half, so right half starts at mid + 1. Count = `j - (mid + 1) = j - mid - 1`.

5. **Forgetting to update counts during the "drain left" phase.** When right is exhausted (j > hi) but left still has elements, ALL of right has been placed → each remaining left element gets `j - mid - 1` (which is the full right half size).

6. **Using `<` instead of `<=` for the comparison.** With `<=`, equal-value elements from the RIGHT get placed BEFORE equal-value elements from the LEFT. Doesn't matter for correctness of count (they're not "strictly smaller"), but matches the standard mergesort convention.

7. **Trying to skip the merge step.** You need to merge to maintain the sorted invariant for higher levels.

---

## 10. The shape — per-element merge-sort counting

This problem is the canonical PER-ELEMENT counting variant of merge-sort-based inversion counting:

| Problem | Counting granularity |
|---|---|
| Count Inversions | total count |
| Reverse Pairs | total count (with custom predicate) |
| **This problem** | per-element count |
| Range Sum Count | per-range count |
| Smallest Range That Contains At Least K Elements From Each | complex per-range counting |

**Pattern to internalize:**

> "When you need PER-ELEMENT counts (not just a total) of pairs satisfying a predicate, MERGE SORT ON INDICES so you can track which left-half element 'absorbed' each right-half placement."

The 'sort by value, track by index' technique generalizes broadly. Use it whenever per-position attribution matters.

---

> **Self-check — the question to ask next time.**
>
> When you face a per-element counting problem with PAIR predicates, ask:
>
> > **"Can I merge-sort on INDICES, crediting each LEFT-half index when right-half elements get placed before it?"**
>
> If yes, O(n log n) with per-element accuracy.

---

## Cross-references

- **Reference card (post-mastery):** [`../Count_of_Smaller_Numbers_After_Self.md`](../Count_of_Smaller_Numbers_After_Self.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Reverse_Pairs.md`](./Reverse_Pairs.md) — total count variant.
  - Coming next: [`Open_the_Lock.md`](./Open_the_Lock.md).
