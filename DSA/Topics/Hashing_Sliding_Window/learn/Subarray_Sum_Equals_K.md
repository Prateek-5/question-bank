# Subarray Sum Equals K — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subarray_Sum_Equals_K.md`](../Subarray_Sum_Equals_K.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/subarray-sum-equals-k/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subarray-sum-equals-k/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~30 minutes. **This is THE canonical prefix-sum + hashmap problem.** The technique — rewriting "subarray sum equals X" as "for each prefix, has a complement been seen before?" — appears in dozens of later problems. Take the time to internalize the algebra in section 4; it's the move you'll reuse forever.

**Map of this file (12 short sections):**

1. Read the problem
2. The natural brute force
3. Why sliding window does NOT work here
4. The pivot — rewrite "subarray sum = k" using prefix sums
5. The complement insight
6. Why we count occurrences (not just presence)
7. The hashmap algorithm
8. The crucial `count[0] = 1` seed
9. Code
10. Trace it
11. Common pitfalls
12. The shape — prefix-sum + hashmap everywhere

---

## 1. Read the problem

You're given an integer array `nums` (which **may contain negative numbers**) and an integer `k`. Return the **count** of contiguous subarrays whose sum equals `k`.

> **Mini-refresher: what's a subarray?**
>
> A **subarray** is a contiguous slice `nums[i..j]` for some `i ≤ j`. The length is `j − i + 1`. Single elements are subarrays (length 1). Subarrays are different from "subsequences" (which can skip elements) — subarrays must be contiguous.
>
> For `nums = [1, 2, 3]`, the subarrays are:
> - Length 1: `[1]`, `[2]`, `[3]`.
> - Length 2: `[1, 2]`, `[2, 3]`.
> - Length 3: `[1, 2, 3]`.
>
> Total: 6 subarrays.

**Example 1:** `nums = [1, 1, 1]`, `k = 2`. Subarrays summing to 2: `nums[0..1] = [1, 1]` (sum 2), `nums[1..2] = [1, 1]` (sum 2). Count = **2**.

**Example 2:** `nums = [1, 2, 3]`, `k = 3`. Subarrays summing to 3: `nums[0..1] = [1, 2]` (sum 3), `nums[2..2] = [3]`. Count = **2**.

**Example 3 (with negatives):** `nums = [3, 4, 7, 2, -3, 1, 4, 2]`, `k = 7`. Subarrays summing to 7:

- `nums[0..1] = [3, 4]`. Sum 7. ✓
- `nums[2..2] = [7]`. Sum 7. ✓
- `nums[2..5] = [7, 2, -3, 1]`. Sum 7. ✓
- `nums[5..7] = [1, 4, 2]`. Sum 7. ✓

Count = **4**.

Notice how negatives make subarrays summing to k arise in non-obvious places (the third one starts at index 2 and includes the -3).

---

## 2. The natural brute force

Try every subarray. Outer loop picks the start `i`; inner loop extends the end `j`, computing the running sum:

```cpp
int subarraySum(vector<int>& nums, int k) {
    int count = 0;
    int n = nums.size();
    for (int i = 0; i < n; i++) {
        int sum = 0;
        for (int j = i; j < n; j++) {
            sum += nums[j];                // running sum from i to j
            if (sum == k) count++;
        }
    }
    return count;
}
```

Two nested loops over indices, O(n²) work. For `n = 2 × 10⁴` (LeetCode's constraint), `n² = 4 × 10⁸` — borderline TLE.

We want O(n).

---

## 3. Why sliding window does NOT work here

A reasonable first thought: "this looks like a sliding window problem — slide a window, track its sum, expand or shrink based on whether the sum is bigger or smaller than `k`."

**This DOESN'T work** because `nums` can contain **negative** numbers.

Sliding window relies on a critical assumption: **adding an element MONOTONICALLY changes the metric**. For sum-of-window with non-negative numbers, adding always INCREASES the sum, and shrinking always DECREASES it. So when sum > target, we can confidently shrink; when sum < target, we can confidently expand.

With negatives, this monotonicity is broken:

- Window sum is 5, target is 7. We want bigger → expand right. New element is `-10`. Now sum is `-5`. Expanding made it SMALLER. Now what?
- Window sum is 10, target is 7. We want smaller → shrink left. The leftmost element is `-3`. Removing it makes the sum 13. Shrinking made it BIGGER. Now what?

Sliding window has no clean rule. We need a different approach.

---

## 4. The pivot — rewrite "subarray sum = k" using prefix sums

Define **prefix sums**:

```
prefix[0] = 0                        (empty prefix)
prefix[i] = nums[0] + nums[1] + ... + nums[i-1]   for i ≥ 1
```

So `prefix[i]` is "the sum of the first `i` elements." Indexing: `prefix` has `n + 1` entries (0 through n).

> **Mini-refresher: prefix sums and range sums.**
>
> Recall from [`../../1_D_and_2_D_Arrays/learn/Running_Sum_of_1D_Array.md`](../../1_D_and_2_D_Arrays/learn/Running_Sum_of_1D_Array.md):
>
> The sum of `nums[l..r]` (inclusive, both 0-indexed) equals `prefix[r+1] − prefix[l]`. The prefix sum at the END (inclusive) minus the prefix sum at the START (exclusive).
>
> Why? Because `prefix[r+1] = nums[0]+...+nums[r]` and `prefix[l] = nums[0]+...+nums[l-1]`. Subtracting gives `nums[l]+...+nums[r]` — exactly the subarray sum.

So the question "does `nums[l..r]` sum to `k`?" becomes:

```
prefix[r+1] − prefix[l] == k
```

Rearranging:

```
prefix[l] == prefix[r+1] − k
```

**This is the pivot.** "Subarray from `l` to `r` sums to `k`" is equivalent to: "there exists some earlier prefix sum equal to `prefix[r+1] − k`."

To find ALL subarrays summing to `k`, we walk forward, computing each `prefix[r+1]`. For each one, ask: "how many earlier prefix sums equal `prefix[r+1] − k`?" Each such earlier prefix is the START of a valid subarray ending at `r`.

---

## 5. The complement insight

Define `current = prefix[r+1]` (the current cumulative sum). Define `complement = current − k`.

The question is: **"how many times has `complement` appeared as a prefix sum so far (at any index ≤ r)?"**

Each occurrence corresponds to a distinct subarray ending at position `r` and summing to `k`.

> **Mini-refresher: complement-lookup, the unifying trick.**
>
> The pattern "for each position, look up a complement in a hashmap" appears in many problems. The complement is whatever value, if matched, completes the target relationship.
>
> - Two Sum: complement is `target − nums[i]`.
> - K-diff Pairs: complement is `nums[i] + k`.
> - Subarray Sum Equals K: complement is `current_prefix_sum − k`.
>
> In all three, we maintain a hashmap of "values we've seen" and for each new position, check if its complement was seen earlier.

So the algorithm becomes:

```
prefix = 0
count = 0
seen = hashmap mapping prefix-sum-value → number of times we've seen it

for each x in nums:
    prefix += x
    count += seen.get(prefix - k, default 0)     # complement lookup
    seen[prefix] = seen.get(prefix, 0) + 1       # record this prefix
```

**O(n) time, O(n) space** (the hashmap can hold up to `n + 1` distinct prefix sums).

---

## 6. Why we count occurrences (not just presence)

We track **how many times** each prefix sum has appeared, not just "has it appeared at all."

Why? Because the same prefix sum can occur at multiple positions, and each occurrence gives a DIFFERENT subarray ending at the current `r`.

**Example:** `nums = [1, -1, 1]`, `k = 1`.

Prefix sums: `prefix[0] = 0, prefix[1] = 1, prefix[2] = 0, prefix[3] = 1`.

When `r = 2`, `current = prefix[3] = 1`. `complement = 1 − 1 = 0`.

`prefix == 0` has occurred at `prefix[0]` AND `prefix[2]`. **Two occurrences** = two valid subarrays ending at `r = 2`:

- Subarray from index `0` to `2`: `[1, -1, 1]`, sum = 1. ✓
- Subarray from index `2` to `2`: `[1]`, sum = 1. ✓

So `count` increases by 2 here, not by 1. The hashmap value `seen[0] = 2` captures both occurrences.

---

## 7. The hashmap algorithm

```
seen = {0: 1}                # the "empty prefix" — see section 8 for why
prefix = 0
count = 0

for x in nums:
    prefix += x
    if (prefix - k) in seen:
        count += seen[prefix - k]
    seen[prefix] = seen.get(prefix, 0) + 1

return count
```

The order matters:

1. **Update `prefix`** first (now `prefix` represents `prefix[i+1]` — the running sum up to and including this element).
2. **Look up the complement** in `seen` BEFORE adding the current prefix.
3. **Add `prefix` to seen** for future iterations to use.

If you flipped steps 2 and 3, you'd be looking up the complement INCLUDING the current prefix — which would let a "subarray of zero elements" trivially match when `k == 0`, giving spurious counts.

---

## 8. The crucial `count[0] = 1` seed

Why does `seen` start with `{0: 1}` before processing any elements?

This represents the **empty prefix** — the prefix sum at "position 0" (before any element), which is by definition `0`.

Consider `nums = [3]`, `k = 3`. The single-element subarray `[3]` has sum 3, so the answer is 1.

Walk through:

```
seen = {}.  prefix = 0.  count = 0.

x = 3:
    prefix = 3.
    Look up prefix - k = 0. seen[0] = ?  If we didn't seed seen, this is 0 (no match) → count stays 0.   ✗ Wrong answer.
    Add prefix: seen[3] = 1.

Return 0.  ✗ (expected 1)
```

With the seed `seen = {0: 1}`:

```
seen = {0: 1}.  prefix = 0.  count = 0.

x = 3:
    prefix = 3.
    Look up prefix - k = 0. seen[0] = 1 → count = 1.   ✓
    Add prefix: seen[3] = 1.

Return 1.  ✓
```

The seed `seen[0] = 1` represents "the empty prefix sums to 0 — count it as one seen occurrence."

**Without the seed, we'd miss every subarray that starts at index 0.** (Those subarrays have `l = 0`, requiring `prefix[0] = 0` to be present in `seen`.)

The seed is the most-skipped detail in this problem. Don't skip it.

---

## 9. Code

**C++:**

```cpp
int subarraySum(vector<int>& nums, int k) {
    unordered_map<int, int> seen;
    seen[0] = 1;                           // seed: empty prefix sums to 0
    int prefix = 0;
    int count = 0;

    for (int x : nums) {
        prefix += x;

        auto it = seen.find(prefix - k);   // complement lookup
        if (it != seen.end()) {
            count += it->second;
        }

        seen[prefix]++;                    // record current prefix sum
    }

    return count;
}
```

**Python:**

```python
def subarraySum(nums, k):
    from collections import defaultdict
    seen = defaultdict(int)
    seen[0] = 1                            # seed
    prefix = 0
    count = 0
    for x in nums:
        prefix += x
        count += seen[prefix - k]          # defaultdict returns 0 if absent
        seen[prefix] += 1
    return count
```

The `defaultdict(int)` automatically returns 0 for missing keys — saves the `if key in seen` check.

**JavaScript:**

```javascript
function subarraySum(nums, k) {
    const seen = new Map();
    seen.set(0, 1);                        // seed
    let prefix = 0;
    let count = 0;
    for (const x of nums) {
        prefix += x;
        count += seen.get(prefix - k) ?? 0;
        seen.set(prefix, (seen.get(prefix) ?? 0) + 1);
    }
    return count;
}
```

All O(n) time, O(n) space.

---

## 10. Trace it

**`nums = [3, 4, 7, 2, -3, 1, 4, 2]`, `k = 7`:**

```
seen = {0: 1}.  prefix = 0.  count = 0.

x = 3:
    prefix = 3.
    prefix - k = -4. seen[-4] = 0 → no contribution. count = 0.
    seen[3] = 1.                       seen = {0:1, 3:1}.

x = 4:
    prefix = 7.
    prefix - k = 0. seen[0] = 1 → count += 1. count = 1.
                                      ← subarray nums[0..1] = [3, 4], sum 7.  ✓
    seen[7] = 1.                       seen = {0:1, 3:1, 7:1}.

x = 7:
    prefix = 14.
    prefix - k = 7. seen[7] = 1 → count += 1. count = 2.
                                      ← subarray nums[2..2] = [7].  ✓
    seen[14] = 1.

x = 2:
    prefix = 16.
    prefix - k = 9. seen[9] = 0. no change. count = 2.
    seen[16] = 1.

x = -3:
    prefix = 13.
    prefix - k = 6. seen[6] = 0. no change.
    seen[13] = 1.

x = 1:
    prefix = 14.
    prefix - k = 7. seen[7] = 1 → count += 1. count = 3.
                                      ← subarray nums[2..5] = [7, 2, -3, 1], sum 7.  ✓
    seen[14] = seen[14] + 1 = 2.       (Note: 14 was already at 1; we add to it.)

x = 4:
    prefix = 18.
    prefix - k = 11. seen[11] = 0. no change.
    seen[18] = 1.

x = 2:
    prefix = 20.
    prefix - k = 13. seen[13] = 1 → count += 1. count = 4.
                                      ← subarray nums[5..7] = [1, 4, 2], sum 7.  ✓
    seen[20] = 1.

Return count = 4.  ✓
```

Four subarrays found. Notice how `seen[14]` reaching 2 captured the fact that prefix 14 occurred at two positions — important if a later iteration had asked for it.

---

## 11. Common pitfalls

1. **Forgetting `seen[0] = 1` seed.** Missing subarrays that start at index 0. Section 8 details.

2. **Doing the lookup AFTER recording the current prefix.** Then the current prefix sum could match its own complement if `k == 0`, creating phantom counts. Always: lookup first, then record.

3. **Using sliding window when there are negatives.** Section 3 details. Negatives break the monotonicity sliding window depends on.

4. **Storing only PRESENCE in the hashmap (set instead of map).** Same prefix sum can occur multiple times — and each occurrence is a distinct subarray. Use a frequency map, not a set.

5. **Forgetting the running sum semantics.** `prefix` after the i-th iteration is `nums[0]+...+nums[i]`. NOT `prefix[i]` from the formula (which is `nums[0]+...+nums[i-1]`). It's `prefix[i+1]` in formula-speak.

6. **Trying to return the actual subarrays.** This problem only asks for the count. To return the subarrays themselves, you'd need to track positions where each prefix sum occurred — more complex.

7. **Worrying about overflow.** For LeetCode constraints (`nums[i]` in `[-1000, 1000]`, `n ≤ 2 × 10⁴`), the cumulative sum is at most `2 × 10⁷`, easily within `int`. For larger constraints, use `long long`.

---

## 12. The shape — prefix-sum + hashmap everywhere

This problem is the canonical example of the **prefix-sum + hashmap** pattern. The recipe:

1. **Reframe the problem in terms of prefix sums.** "Subarray sum = k" ↔ "two prefix sums differ by k."
2. **Identify the COMPLEMENT.** For each prefix sum `p`, ask: "what earlier prefix value would form a valid pair?" Here: `p − k`.
3. **Maintain a hashmap of `prefix-value → count`.** Walk forward; lookup complement; update map.

| Problem | Reframe | Complement lookup |
|---|---|---|
| **This problem** (Subarray Sum Equals K) | sum = k → two prefixes differ by k | `prefix − k` |
| Maximum Size Subarray Sum Equals K | longest length where sum = k | `prefix − k`; track first-occurrence position |
| Continuous Subarray Sum (multiple of k) | sum ≡ 0 (mod k) → two prefixes have same remainder | same remainder in map |
| Subarray Sums Divisible by K | count where sum % k == 0 | same |
| Largest Subarray with 0 Sum | sum = 0 | `prefix == prefix_earlier` |
| Contiguous Array (equal 0s and 1s) | translate 0 → -1, then sum = 0 | `prefix` already seen |
| Two Sum (unsorted) | not prefix-sum, but same "complement lookup" idiom | `target − nums[i]` |

**Pattern to internalize:**

> "When a problem asks about CONTIGUOUS subarrays satisfying a SUM property (= k, divisible by k, equal-counts), reach for prefix sums + hashmap. Walk forward, compute running prefix, look up the complement in the map, update count, record current prefix."

The technique handles negatives gracefully (sliding window can't). The complement-lookup idea generalizes far beyond sums — anywhere two "running values" form a pair that satisfies the target relationship.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking to **count / find contiguous subarrays with a specific sum property** (sum equals k, sum divisible by k, sum at most k, etc.), before reaching for sliding window, ask:
>
> > **"Does the array have negative numbers? If yes, sliding window won't work. Can I rewrite the property as 'two prefix sums have relationship X' and use a hashmap of prefix-sum frequencies for complement lookup?"**
>
> If yes, you've turned O(n²) into O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Subarray_Sum_Equals_K.md`](../Subarray_Sum_Equals_K.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../1_D_and_2_D_Arrays/learn/Running_Sum_of_1D_Array.md`](../../1_D_and_2_D_Arrays/learn/Running_Sum_of_1D_Array.md) — required prereq (prefix sums).
  - [`Valid_Anagram.md`](./Valid_Anagram.md), [`Valid_Sudoku.md`](./Valid_Sudoku.md) — hashmap warm-ups.
  - [`../../Two_Pointers/learn/K_diff_Pairs_in_an_Array.md`](../../Two_Pointers/learn/K_diff_Pairs_in_an_Array.md) — same complement-lookup idiom on raw values rather than prefix sums.
  - Coming next: Maximum_Size_Subarray_Sum_Equals_K (length variant), Largest_Subarray_With_0_Sum (sum = 0 special case).
