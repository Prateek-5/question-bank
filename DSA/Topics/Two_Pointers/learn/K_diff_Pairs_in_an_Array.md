# K-diff Pairs in an Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../K_diff_Pairs_in_an_Array.md`](../K_diff_Pairs_in_an_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/k-diff-pairs-in-an-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/k-diff-pairs-in-an-array/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. This problem teaches **two distinct approaches to "count pairs satisfying a property":** the **hash-frequency** approach (O(n) time, O(n) space) and the **sorted two-pointer** approach (O(n log n) time, O(1) space). It also has a notorious edge case (`k = 0`) that catches lots of candidates off-guard.

**Map of this file (10 short sections):**

1. Read the problem
2. The "unique pair" subtlety
3. Two cases — k = 0 vs k > 0
4. Approach A — hashmap (frequency map)
5. Approach B — sorted two-pointer
6. Code (both approaches)
7. Trace it
8. Why "for each x, check x + k" doesn't double-count
9. Common pitfalls
10. The shape — "for each value, check the complement"

---

## 1. Read the problem

You're given an integer array `nums` and a non-negative integer `k`. Count the number of **unique k-diff pairs**.

A **k-diff pair** is `(nums[i], nums[j])` where:

- `i ≠ j` (different array positions),
- `|nums[i] − nums[j]| == k` (absolute difference equals k).

"Unique" means: pairs are compared by their **unordered VALUES**, not by their indices. So `(3, 1)` and `(1, 3)` are the same pair; we count it once.

**Example 1:** `nums = [3, 1, 4, 1, 5]`, `k = 2`.

Look for pairs with `|a − b| == 2`:

- `(3, 1)`: |3 − 1| = 2. ✓ Pair as unordered values: `{1, 3}`.
- `(3, 5)`: |3 − 5| = 2. ✓ Pair: `{3, 5}`.
- `(1, 1)`: |1 − 1| = 0. ✗ (not 2)
- Other pairs: check each — but only the above match.

Unique pairs: `{1, 3}` and `{3, 5}`. Count: **2**.

**Example 2:** `nums = [1, 3, 1, 5, 4]`, `k = 0`.

`k = 0` means we need pairs with **equal** values (`|a − a| = 0`).

- The two `1`s form a pair `(1, 1)`. ✓ Unique pair: `{1, 1}`.
- No other duplicates.

Count: **1**.

---

## 2. The "unique pair" subtlety

> **Mini-refresher: what "unique pair" means.**
>
> "Unique" is by the unordered multiset of VALUES, not by index positions.
>
> For `nums = [3, 1, 4, 1, 5]` and `k = 2`:
> - Index pairs `(0, 1) → values (3, 1)` and `(0, 3) → values (3, 1)` both produce pair `{1, 3}`.
> - We count `{1, 3}` ONCE, even though it can be formed two different ways.
>
> When `k = 0`, the pair is two copies of the SAME value. The "pair" `{1, 1}` is a single unique pair — we count it once if the value 1 appears at least twice in the array.

So:

- For `k > 0`: count **distinct value pairs `(x, y)` with `y = x + k`** that BOTH appear in the array.
- For `k = 0`: count **distinct values that appear at least twice** in the array.

---

## 3. Two cases — k = 0 vs k > 0

The two sub-cases have slightly different logic.

**Case `k > 0`:**

For each distinct value `x` in the array, check if `x + k` also appears. If yes, the pair `{x, x + k}` is a valid k-diff pair. Count it once.

We only check `x + k` (not also `x − k`) to avoid double-counting: every k-diff pair `{a, b}` with `a < b` has `b = a + k`, and we encounter it once when iterating `x = a`.

**Case `k = 0`:**

For each distinct value `x` with frequency ≥ 2, the pair `{x, x}` is valid. Count it once.

The problem guarantees `k ≥ 0`, but defensively: if `k < 0`, return 0 (absolute differences are always ≥ 0).

---

## 4. Approach A — hashmap (frequency map)

> **Mini-refresher: frequency map.**
>
> A frequency map (or "count map") stores, for each distinct value, how many times it appeared. Implementation: `unordered_map<int, int>` (C++), `dict` or `Counter` (Python), `Map` or plain object (JS).
>
> Build in one O(n) pass: walk the array, increment `count[x]` for each element.
>
> Queries:
> - "Does value `v` appear in the array?" → `count.count(v) > 0` (C++) or `v in count` (Python). O(1) amortized.
> - "How many times does value `v` appear?" → `count[v]` (default 0 if absent).

Algorithm:

```
build count = frequency map of nums

if k < 0:
    return 0

if k == 0:
    answer = 0
    for each (x, c) in count:
        if c >= 2:
            answer += 1
    return answer

# k > 0
answer = 0
for each x in count.keys():
    if (x + k) in count:
        answer += 1
return answer
```

- Build: O(n).
- Iterate keys: O(distinct count) ≤ O(n).
- Total: **O(n) time, O(n) space**.

---

## 5. Approach B — sorted two-pointer

If you want **O(1) extra space** (ignoring the sort), here's the two-pointer approach.

Sort `nums` first. Walk two pointers `lo` and `hi` (both moving forward), where `lo < hi`:

- If `nums[hi] − nums[lo] < k`: the difference is too small. Move `hi` right to find a larger value.
- If `nums[hi] − nums[lo] > k`: too big. Move `lo` right (advance the smaller side toward the larger).
- If `nums[hi] − nums[lo] == k`: found a pair. Count it, then skip past duplicates of `nums[lo]` (and advance `lo` once more so we move past the current value).

```
sort nums
lo = 0, hi = 1, count = 0
while hi < n:
    if lo == hi or nums[hi] - nums[lo] < k:
        hi++
    elif nums[hi] - nums[lo] > k:
        lo++
    else:    # equals k
        count++
        lo++
        while lo < hi and nums[lo] == nums[lo - 1]:
            lo++
return count
```

The `lo == hi` check guards against the case where `lo` catches up to `hi`; in that case advance `hi` to keep them separated.

- Sort: O(n log n).
- Two-pointer scan: O(n).
- Total: **O(n log n) time, O(1) extra space**.

---

## 6. Code (both approaches)

**Hashmap (C++):**

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

**Two-pointer (C++):**

```cpp
int findPairs(vector<int>& nums, int k) {
    if (k < 0) return 0;
    sort(nums.begin(), nums.end());
    int n = nums.size();
    int lo = 0, hi = 1, count = 0;
    while (hi < n) {
        if (lo == hi || nums[hi] - nums[lo] < k) {
            hi++;
        } else if (nums[hi] - nums[lo] > k) {
            lo++;
        } else {     // == k
            count++;
            lo++;
            while (lo < hi && nums[lo] == nums[lo - 1]) lo++;
        }
    }
    return count;
}
```

**Python (hashmap):**

```python
def findPairs(nums, k):
    if k < 0:
        return 0
    from collections import Counter
    count = Counter(nums)
    answer = 0
    if k == 0:
        for x, c in count.items():
            if c >= 2:
                answer += 1
    else:
        for x in count:
            if x + k in count:
                answer += 1
    return answer
```

---

## 7. Trace it

**Example 1: `nums = [3, 1, 4, 1, 5]`, `k = 2` (hashmap).**

```
count = {3: 1, 1: 2, 4: 1, 5: 1}.

k > 0 branch. Iterate keys:
    x = 3:  count.has(3 + 2 = 5)?  Yes.  answer = 1.
    x = 1:  count.has(1 + 2 = 3)?  Yes.  answer = 2.
    x = 4:  count.has(4 + 2 = 6)?  No.
    x = 5:  count.has(5 + 2 = 7)?  No.

Return 2.  ✓
```

**Example 2: `nums = [1, 3, 1, 5, 4]`, `k = 0` (hashmap).**

```
count = {1: 2, 3: 1, 5: 1, 4: 1}.

k == 0 branch. Iterate keys:
    x = 1:  c = 2 ≥ 2 → answer = 1.
    x = 3:  c = 1 < 2 → skip.
    x = 5:  skip.
    x = 4:  skip.

Return 1.  ✓
```

**Example 1 with the two-pointer:**

```
Sorted: [1, 1, 3, 4, 5].  n = 5.  k = 2.
lo = 0, hi = 1.

Iter 1: lo=0, hi=1.  nums[1] - nums[0] = 1 - 1 = 0 < 2. hi++. hi = 2.
Iter 2: lo=0, hi=2.  nums[2] - nums[0] = 3 - 1 = 2 == 2.  count = 1.
         lo++. lo = 1.  while lo < hi && nums[1] == nums[0]?  1 == 1, yes. lo = 2.
Iter 3: lo=2, hi=2.  lo == hi → hi++. hi = 3.
Iter 4: lo=2, hi=3.  nums[3] - nums[2] = 4 - 3 = 1 < 2. hi++. hi = 4.
Iter 5: lo=2, hi=4.  nums[4] - nums[2] = 5 - 3 = 2 == 2.  count = 2.
         lo++. lo = 3. while lo < hi && nums[3] == nums[2]? 4 == 3, no.
Iter 6: lo=3, hi=4.  nums[4] - nums[3] = 5 - 4 = 1 < 2. hi++. hi = 5. Loop ends.

Return 2.  ✓
```

Same answer via either approach.

---

## 8. Why "for each x, check x + k" doesn't double-count

In the hashmap approach, for `k > 0`, we iterate every distinct value `x` and ask "is `x + k` also in the array?"

Why not also check `x − k` (the value `k` less than x)?

**Because pairs are unordered**, every pair `{a, b}` with `a < b` and `b - a = k` is visited EXACTLY ONCE — when we iterate `x = a`. We never need to check both directions.

If we ALSO checked `x − k`, the pair `{a, b}` would be counted at `x = a` (asking for `a + k = b`) AND at `x = b` (asking for `b − k = a`). Double-counted.

So checking just one direction (`x + k`) is correct AND simpler.

---

## 9. Common pitfalls

1. **For `k = 0`, counting `c × (c − 1) / 2` (number of index pairs) instead of `1` per distinct value.** That's the count of ORDERED INDEX pairs that match. The problem asks for unique VALUE pairs. For `k = 0`, each value with ≥ 2 occurrences gives ONE unique pair, regardless of how many times it appears.

2. **Forgetting the `k == 0` special case.** If you only handle `k > 0`, you'd ask "is `x + 0 = x` in the count?" — trivially yes, so you'd count every distinct value (wrong).

3. **Not handling `k < 0`.** The problem says `k ≥ 0` so this shouldn't arise, but for defensive coding return 0 immediately if `k < 0`.

4. **Counting ordered pairs in the hashmap approach.** Checking BOTH `x + k` and `x − k` double-counts each pair.

5. **In the two-pointer, forgetting to skip duplicates of `nums[lo]` after a match.** Without skipping, you'd count the same value pair multiple times (e.g., if there are three `1`s and a `3`, you'd count `{1, 3}` three times).

6. **Initializing `hi = 0` instead of `hi = 1`.** With both pointers at 0, `nums[hi] - nums[lo] = 0`, and you'd accidentally count "pair of the same element with itself." The `lo == hi` guard in the loop handles this, but starting `hi = 1` makes the intent clearer.

7. **Integer overflow on `x + k`.** For typical constraints (`nums[i]` up to `10⁷`, `k` up to `10⁷`), `x + k` fits in `int32`. Use `long long` if constraints are extreme.

---

## 10. The shape — "for each value, check the complement"

The hashmap approach generalizes to a family of "find pairs with a specific relationship" problems:

| Problem | Per-value check | Complement |
|---|---|---|
| **This problem** (K-diff Pairs) | `x + k` in count? | `x + k` |
| Two Sum (unsorted) | `target − x` in seen-set? | `target − x` |
| Pairs with given sum (count distinct) | `target − x` in count, and `2 × x ≠ target` (avoid double-counting if equal) | `target − x` |
| Reverse-pair count (e.g., LeetCode 493) | for each x, count of `y` with `y < x / 2` already seen | requires sorted data structure |
| Count of subarrays with sum equal to k | prefix sum `s − k` seen before? | `s − k` |

**Pattern to internalize:**

> "When asked to count PAIRS satisfying a relationship `f(x, y) = constant`, rewrite `y = g(x)` for some function `g`. Build a frequency map. For each `x` in the map, check if `g(x)` is in the map. O(n) time."

The hardest part is **deduplication** — counting each unique pair exactly once. The trick is to **iterate only one direction** (e.g., `x + k`, not also `x − k`), so each pair is encountered exactly once.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking to **count pairs (or tuples) with some relational property** in an array, before nesting loops, ask:
>
> > **"Can I build a frequency map of values, then for each value `x` check whether its 'complement' (the value that would form a valid pair with `x`) is also in the map?"**
>
> If yes, you've reduced O(n²) pair-checking to O(n) value-checking. Handle deduplication by iterating in one direction only.

---

## Cross-references

- **Reference card (post-mastery):** [`../K_diff_Pairs_in_an_Array.md`](../K_diff_Pairs_in_an_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) — sum (sorted) instead of diff (unsorted): same two-pointer shape.
  - [`3Sum.md`](./3Sum.md) — generalizes "value-pair lookup" to 3-element search.
  - Coming later in Hashing topic: Subarray_Sum_Equals_K (prefix-sum + hashmap — same complement-lookup trick on cumulative sums).
