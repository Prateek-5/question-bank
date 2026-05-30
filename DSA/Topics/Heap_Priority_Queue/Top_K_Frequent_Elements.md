# Top K Frequent Elements

**Problem Link:**
<a href="https://leetcode.com/problems/top-k-frequent-elements/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/top-k-frequent-elements/</a>

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Read the Problem

Given an integer array and an integer k, return the `k` most frequent elements. The answer can be in any order.

Example: `nums = [1, 1, 1, 2, 2, 3]`, k = 2.
- 1 appears 3 times.
- 2 appears 2 times.
- 3 appears 1 time.

Top 2 most frequent: 1 and 2. Return `[1, 2]` (order doesn't matter).

If `nums = [1]`, k = 1: return `[1]`.

The problem is specifically about **frequency**, not values. Two steps implied: count frequencies, then pick the top k.

----------------------------------------

## Step 2: Count Frequencies First

A simple hashmap: iterate the array, increment `count[num]`.

```cpp
unordered_map<int, int> count;
for (int x : nums) count[x]++;
```

Now `count` has each unique value mapped to its frequency. For the example, `count = {1: 3, 2: 2, 3: 1}`.

Next question: given these frequency pairs, how do we find the top k?

----------------------------------------

## Step 3: Three Ways to Pick the Top K

Let n = number of unique elements (size of count). The simple approaches:

**Approach A: Sort by frequency, take the first k.** O(n log n) for sorting. Simple, but we might be doing more than necessary — we don't care about the full sort, just the top k.

**Approach B: Use a heap of size k.** Maintain a *min-heap* keyed on frequency, capped at k elements. For each (value, freq), push it. If heap grows beyond k, pop the smallest. At the end, the heap holds the top-k by frequency. O(n log k).

Why min-heap for top-k? Because we kick out the smallest when the heap is full — and we want to keep the largest. So "smallest" on top is the one to discard.

**Approach C: Bucket sort on frequencies.** Because frequencies range from 1 to n (they can't exceed the array length), we can bucket them. Create an array of lists where index f holds all values with frequency f. Then scan from high to low, collecting k values. O(n) time — optimal.

Let me work through all three, since each teaches something.

----------------------------------------

## Step 4: Approach B (Heap) in Detail

Min-heap keyed on frequency. For each `(value, freq)`:
- Push into heap.
- If heap size > k, pop (this removes the minimum-frequency entry, which we don't want).

After processing all pairs, the heap contains exactly k entries — the top-k by frequency.

Pseudocode:
```
heap = empty min-heap (keyed by frequency)
for (value, freq) in count.items():
    heap.push((freq, value))
    if heap.size() > k:
        heap.pop()
result = [value for (freq, value) in heap]
```

For the example:
```
heap: [] → push (3, 1) → [(3, 1)] → push (2, 2) → [(2, 2), (3, 1)] 
(heap order: min at top, so (2,2) is top) → push (1, 3) → [(1, 3), (3, 1), (2, 2)]
size = 3 > k=2, pop (1, 3) → [(2, 2), (3, 1)].
```

Result: values 2 and 1. ✓

Time: O(n log k). Good enough for most cases.

----------------------------------------

## Step 5: Approach C (Bucket Sort) — O(n) Time

Here's a clever observation: **frequencies are bounded by `n`** (nothing can appear more times than the array has elements). So we can make a bucket for each possible frequency.

`buckets[f]` = list of values with frequency exactly f.

After filling buckets, scan from `f = n` down to `f = 1`, collecting values until we have k.

```cpp
vector<vector<int>> buckets(n + 1);
for (auto& [val, freq] : count) buckets[freq].push_back(val);

vector<int> result;
for (int f = n; f >= 1 && (int)result.size() < k; --f) {
    for (int val : buckets[f]) {
        result.push_back(val);
        if ((int)result.size() == k) break;
    }
}
return result;
```

O(n) time. The key insight is that bucket indices are bounded, so we can use a straight array instead of a sorted structure.

For the example, buckets after filling:
- buckets[3] = [1]
- buckets[2] = [2]
- buckets[1] = [3]

Scan from f=6 down: empty buckets skipped. At f=3, add 1. At f=2, add 2. Result = [1, 2]. Done.

Why is this worth knowing over the heap version? Because it's **optimal** — O(n) beats O(n log k) when k is large. Also, it's often simpler to implement once you see the pattern.

----------------------------------------

## Step 6: Which Approach to Use?

If the problem asked for strictly optimal, Approach C (bucket sort) wins. In practice:
- **Heap version** is more general — extends to streaming input, handles unknown n, generalizes to arbitrary sortable keys.
- **Bucket version** is faster when `n` is moderate and we're processing static data.
- **Full sort** is fine for small n or when the input isn't just about top-k.

For an interview, either B or C is a strong answer; C edges out slightly on asymptotic grounds.

----------------------------------------

## Step 7: Name the Techniques

- Heap-based: **"bounded heap" pattern** (heap of size k as a filter). Used for top-k and k-closest problems.
- Bucket-based: **counting-sort variant** exploiting bounded key ranges. Used whenever the "score" (frequency here) is naturally bounded.
- Full-sort: standard but often overkill.

Knowing all three and when to pick each is more valuable than mastering just one.

----------------------------------------

## Step 8: Complexity

| Approach | Time | Space |
|---|---|---|
| Full sort | O(n log n) | O(n) |
| Min-heap size k | O(n log k) | O(n + k) |
| Bucket sort | O(n) | O(n) |

For k small (say log n), the heap version is nearly as fast as bucket. For large k, bucket dominates.

----------------------------------------

## Step 9: C++ Implementation

**Bucket-sort version (preferred for optimality):**

```cpp
vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int, int> count;
    for (int x : nums) count[x]++;
    int n = nums.size();
    vector<vector<int>> buckets(n + 1);
    for (auto& [val, freq] : count) buckets[freq].push_back(val);

    vector<int> result;
    for (int f = n; f >= 1 && (int)result.size() < k; --f) {
        for (int val : buckets[f]) {
            result.push_back(val);
            if ((int)result.size() == k) break;
        }
    }
    return result;
}
```

**Heap version (for flexibility):**

```cpp
vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int, int> count;
    for (int x : nums) count[x]++;
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> heap;
    for (auto& [val, freq] : count) {
        heap.push({freq, val});
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

----------------------------------------

## Step 10: Follow-up Questions

- **Top k frequent words (ties broken alphabetically).** The heap's comparator needs a two-key sort: frequency descending, then word alphabetically ascending.
- **Streaming (elements arrive over time, report top-k at any moment).** Heap version adapts; bucket version doesn't (frequencies change).
- **Top k frequent in a range of indices.** Much harder — requires segment trees with frequency tracking.
- **What if frequencies can be huge (not bounded by n)?** Bucket sort still works as long as the frequency range is small; otherwise use heap.
- **Concurrent top-k with parallel updates.** Uses atomics and careful synchronization; beyond basic interview scope.
