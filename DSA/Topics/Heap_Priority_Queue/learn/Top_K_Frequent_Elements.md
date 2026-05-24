# Top K Frequent Elements — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Top_K_Frequent_Elements.md`](../Top_K_Frequent_Elements.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/top-k-frequent-elements/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: combine FREQUENCY COUNTING (hashmap) with a SIZE-K BOUNDED HEAP. Also: when frequencies are BOUNDED, BUCKET SORT beats heap.** Three viable solutions; understand tradeoffs. **Read [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md) first.**

**Map of this file (9 sections):**

1. Read the problem
2. The two-phase approach
3. Counting frequencies
4. Picking top K — heap version O(n log k)
5. Picking top K — bucket sort O(n)
6. Code
7. Trace it
8. Comparing approaches
9. The shape — frequency-based top-K

---

## 1. Read the problem

Given an integer array `nums` and integer `k`, return the **K MOST FREQUENT ELEMENTS**. Order doesn't matter.

**Example:** `nums = [1, 1, 1, 2, 2, 3]`, `k = 2`.

Frequencies: 1 → 3 times, 2 → 2 times, 3 → 1 time.

Top 2 most frequent: 1 and 2. Return `[1, 2]` (any order).

---

## 2. The two-phase approach

**Phase 1:** count frequencies (hashmap).
**Phase 2:** pick the K elements with highest frequencies.

Phase 1 is O(n). Phase 2 has multiple options.

---

## 3. Counting frequencies

```
freq = empty hashmap
for x in nums: freq[x] += 1
```

After this, `freq` has each unique value mapped to its count. O(n) time.

For `[1, 1, 1, 2, 2, 3]`, `freq = {1: 3, 2: 2, 3: 1}`.

---

## 4. Picking top K — heap version O(n log k)

> **Mini-refresher: size-K min-heap for top-K-largest.**
>
> Use a MIN-HEAP keyed by FREQUENCY, capped at size K. For each `(value, freq)`:
> 1. Push `(freq, value)` onto heap.
> 2. If heap size > k, pop the smallest (least frequent).
>
> At the end, the heap holds the K most frequent.

```
heap = empty min-heap
for value, freq in freq.items():
    heap.push((freq, value))
    if heap.size() > k:
        heap.pop()
return [value for (freq, value) in heap]
```

Time: O(n log k). Space: O(n + k).

---

## 5. Picking top K — bucket sort O(n)

> **Mini-refresher: bucket sort when frequencies are bounded.**
>
> Frequencies are AT MOST `n` (no value can appear more times than the array length). So we can bucket by frequency.
>
> `buckets[f]` = list of values appearing exactly `f` times.
>
> Scan `f` from HIGH to LOW, collecting K values.

```
buckets = list of n+1 empty lists
for value, freq in freq.items():
    buckets[freq].append(value)

result = []
for f in range(n, 0, -1):
    for value in buckets[f]:
        result.append(value)
        if len(result) == k:
            return result
```

Time: **O(n)**. Optimal — strictly faster than heap when k is large.

---

## 6. Code

**C++ — bucket sort (optimal):**

```cpp
vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int, int> freq;
    for (int x : nums) freq[x]++;

    int n = nums.size();
    vector<vector<int>> buckets(n + 1);
    for (auto& [val, f] : freq) buckets[f].push_back(val);

    vector<int> result;
    for (int f = n; f >= 1 && (int)result.size() < k; --f) {
        for (int val : buckets[f]) {
            result.push_back(val);
            if ((int)result.size() == k) return result;
        }
    }
    return result;
}
```

**C++ — heap version:**

```cpp
vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int, int> freq;
    for (int x : nums) freq[x]++;

    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> heap;
    for (auto& [val, f] : freq) {
        heap.push({f, val});
        if ((int)heap.size() > k) heap.pop();
    }

    vector<int> result;
    while (!heap.empty()) {
        result.push_back(heap.top().second);
        heap.pop();
    }
    return result;
}
```

**Python — bucket sort:**

```python
def topKFrequent(nums, k):
    from collections import Counter
    freq = Counter(nums)
    n = len(nums)
    buckets = [[] for _ in range(n + 1)]
    for val, f in freq.items():
        buckets[f].append(val)
    result = []
    for f in range(n, 0, -1):
        for val in buckets[f]:
            result.append(val)
            if len(result) == k:
                return result
    return result
```

Complexity: **bucket sort O(n); heap O(n log k); full sort O(n log n).**

---

## 7. Trace it

`nums = [1, 1, 1, 2, 2, 3]`, `k = 2`.

**Phase 1:** `freq = {1: 3, 2: 2, 3: 1}`.

**Phase 2 (bucket sort):**

```
n = 6.
buckets = [[], [3], [2], [1], [], [], []]   (size 7)

Scan f from 6 down:
f=6: empty.
f=5: empty.
f=4: empty.
f=3: [1] → append 1. result = [1].
f=2: [2] → append 2. result = [1, 2]. SIZE = K = 2. RETURN.
```

Return `[1, 2]`. ✓

**Phase 2 (heap):**

```
heap = [].

Push (3, 1): heap = [(3, 1)]. size 1.
Push (2, 2): heap = [(2, 2), (3, 1)]. size 2.
Push (1, 3): heap = [(1, 3), (3, 1), (2, 2)]. size 3 > 2. Pop (1, 3). heap = [(2, 2), (3, 1)]. size 2.

Drain: result = [2, 1] (or [1, 2]).
```

Either order is acceptable.

---

## 8. Comparing approaches

| Approach | Time | Space | When to use |
|---|---|---|---|
| **Bucket sort** | **O(n)** | O(n) | Best when frequencies are bounded; **optimal** |
| **Heap (size k)** | O(n log k) | O(n + k) | When k << n; streaming compatible |
| **Full sort** | O(n log n) | O(n) | Simplest; fine for small n |

For LeetCode, **bucket sort** is the senior-bar answer. **Heap** is also accepted.

> **Mini-refresher: when bucket sort doesn't apply.**
>
> Bucket sort requires BOUNDED key range (here, frequencies in [1, n]). If keys are unbounded (e.g., real numbers), bucket sort breaks. Use heap then.

---

## 9. The shape — frequency-based top-K

The pattern:

> **"FREQUENCY-COUNTING (hashmap) + TOP-K SELECTION (heap or bucket sort). Choose by complexity needs."**

| Problem | Variation |
|---|---|
| **This problem** | top k by frequency |
| Top K Frequent Words | tie-break alphabetically (heap with custom comparator) |
| Sort Characters By Frequency | full sort by frequency |
| Least Frequent Subarray Element | flip polarity |
| K-th Most Frequent Element (single answer) | quickselect on frequencies |
| Top-K in Streaming | heap-only (bucket sort needs full data) |

**Pattern to internalize:**

> "Two-phase: COUNT (hashmap), then SELECT (heap/bucket/sort). Pick the selection method based on whether frequencies are bounded and whether you need streaming."

---

## Cross-references

- **Reference card (post-mastery):** [`../Top_K_Frequent_Elements.md`](../Top_K_Frequent_Elements.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md), [`Last_Stone_Weight.md`](./Last_Stone_Weight.md).
  - Coming next: K_Closest_Points + Kth_Largest_Array + Find_K_Closest_Elements.
