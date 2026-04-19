# K-diff Pairs in an Array

**Problem Link:**
https://leetcode.com/problems/k-diff-pairs-in-an-array/

**Topic:**
Two Pointers

----------------------------------------

## Step 1: Define "K-diff Pair"

Given an array `nums` and a non-negative integer `k`, count the number of **unique** pairs `(a, b)` from the array satisfying:
- `|a - b| == k`.
- i < j (different array positions).

"Unique" means if `(a, b)` and `(a', b')` have the same unordered values, count once.

Example: `nums = [3, 1, 4, 1, 5]`, k = 2. Pairs with difference 2:
- (3, 1), (1, 3): same unordered pair {1, 3}. Count once.
- (3, 5), (5, 3): pair {3, 5}. Count once.
- Nothing else.

Answer: **2**.

Example: `nums = [1, 3, 1, 5, 4]`, k = 0. Difference 0 means pair of equal values.
- The two 1's form pair (1, 1). Only one unique value "1" has duplicates — count = 1.

Answer: **1**.

----------------------------------------

## Step 2: Two Cases — k > 0 and k = 0

The problem splits into two shapes:

**k > 0:** we need two *different* values differing by k. For each distinct value `x` in the array, check if `x + k` also appears. Every such pair contributes 1.

**k = 0:** we need two copies of the *same* value. For each distinct value, if it appears **≥ 2 times**, count 1.

Handling k < 0: the problem guarantees k ≥ 0, but if not, we'd return 0 (absolute difference is always ≥ 0).

----------------------------------------

## Step 3: Hashmap Approach

Build a frequency map: `count[x] = number of times x appears`.

Then:
- If k > 0: for each key x in count, if `x + k` is also a key, increment answer.
- If k = 0: for each key x with `count[x] >= 2`, increment answer.

One pass to build count, one pass over keys. O(n) time, O(n) space.

----------------------------------------

## Step 4: Sorted + Two Pointers Approach

Alternative: sort nums, then use two pointers `lo` and `hi`:

```
sort(nums)
lo = 0, hi = 1
while hi < n:
    if lo == hi or nums[hi] - nums[lo] < k:
        hi++
    elif nums[hi] - nums[lo] > k:
        lo++
    else:   # equals k
        count++
        lo++
        while lo < hi and nums[lo] == nums[lo - 1]: lo++   # skip duplicates
```

Each pointer moves forward only, so O(n log n) with the sort.

The hashmap is usually faster in practice; two-pointers is nicer when in-place or when we also want to enumerate the pairs in sorted order.

----------------------------------------

## Step 5: Hashmap Algorithm

```
count = frequency map of nums
answer = 0
if k == 0:
    for x, c in count.items():
        if c >= 2: answer++
else:
    for x in count.keys():
        if (x + k) in count: answer++
return answer
```

One subtle thing: when k > 0, we only check `x + k`, not also `x - k`, because every pair {x, y} with y = x + k is captured exactly once when we iterate x = smaller element.

----------------------------------------

## Step 6: Trace

**`nums = [3, 1, 4, 1, 5]`, k = 2.**

count = {3:1, 1:2, 4:1, 5:1}.

k > 0 branch. Iterate keys:
- x = 3: 3 + 2 = 5 in count? Yes. answer = 1.
- x = 1: 1 + 2 = 3 in count? Yes. answer = 2.
- x = 4: 4 + 2 = 6 in count? No.
- x = 5: 5 + 2 = 7 in count? No.

Answer: **2**. ✓

**`nums = [1, 3, 1, 5, 4]`, k = 0.**

count = {1:2, 3:1, 5:1, 4:1}.

k = 0 branch. Iterate:
- x = 1: count = 2 ≥ 2. answer = 1.
- Others: count = 1. Skip.

Answer: **1**. ✓

**Edge case: `nums = [1, 2, 3, 4, 5]`, k = 1.**

count = {1:1, 2:1, 3:1, 4:1, 5:1}.

Iterate:
- x = 1: x + 1 = 2 in count. answer = 1.
- x = 2: 3 in count. answer = 2.
- x = 3: 4. answer = 3.
- x = 4: 5. answer = 4.
- x = 5: 6 no.

Answer: **4**. ✓

----------------------------------------

## Step 7: Why Not Enumerate All Pairs?

Brute force: nested loops, check |a - b| = k. O(n²). For n = 10⁴ that's 10⁸ — borderline. For n = 10⁵, too slow.

Hashmap reduces to O(n). The saving comes from "lookup by value" instead of "lookup by index."

----------------------------------------

## Step 8: Name It

**Frequency map for pair counting.** A generic tool:
- Two-sum counting variants.
- Pairs with given difference.
- Pairs with given sum.

The "difference" and "sum" variants both boil down to: "for each x, is the complement (x ± k or target - x) present?" A hashmap answers in O(1).

Related: sliding window works when "k-diff" means consecutive. Here order doesn't matter — pure set/map.

----------------------------------------

## Step 9: Complexity

Hashmap: Time **O(n)**, Space **O(n)**.
Two pointers: Time **O(n log n)** (due to sort), Space **O(1)** (ignoring sort stack).

For numeric comparison of "unique pairs," hashmap is the common choice.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int findPairs(vector<int>& nums, int k) {
    if (k < 0) return 0;

    unordered_map<int, int> count;
    for (int x : nums) count[x]++;

    int answer = 0;
    if (k == 0) {
        for (auto& [x, c] : count) {
            if (c >= 2) answer++;
        }
    } else {
        for (auto& [x, c] : count) {
            if (count.count(x + k)) answer++;
        }
    }
    return answer;
}
```

Three cases baked in: k < 0 → 0, k = 0 → duplicate values, k > 0 → check presence of x + k.

----------------------------------------

## Step 11: Follow-up Questions

- **Count ordered pairs (a, b) with i < j and a - b = k.** More involved; track positions.
- **Count pairs with |a - b| ≤ k.** Sort; sliding window on sorted array.
- **Return the pairs themselves, not just count.** Store (x, x + k) tuples; deduplicate.
- **Why absolute difference? Signed difference?** If problem asks signed a - b = k, the trick still works: `count[x + k]` counts pairs where y = x + k. No absolute-value double-counting.
- **Multiple differences (list of k's).** For each k, run the pair count. Or precompute all pairwise differences in a frequency map.
- **Why O(n) instead of O(n²) brute force?** Hashmap lookups are amortized O(1); no need to check all n² pairs individually.
