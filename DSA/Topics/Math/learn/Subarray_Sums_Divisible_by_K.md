# Subarray Sums Divisible by K — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subarray_Sums_Divisible_by_K.md`](../Subarray_Sums_Divisible_by_K.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/subarray-sums-divisible-by-k/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subarray-sums-divisible-by-k/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **This is the "prefix sum + hash" pattern with a MODULAR twist.** The lesson: **two prefix sums sharing the same remainder mod k mean the subarray between them is divisible by k.** Same shape as Subarray Sum Equals K, with `% k` added. Bridge from Math into Hashing. **Read Subarray_Sum_Equals_K (in Hashing_Sliding_Window/learn) first.**

**Map of this file (11 short sections):**

1. Read the problem
2. The brute force
3. The prefix-sum reformulation
4. Why "same remainder mod k" works
5. The counting-pairs trick
6. The negative-mod gotcha
7. The sentinel for `remainder == 0`
8. Code
9. Trace it
10. Common pitfalls
11. The shape — congruent prefix sums

---

## 1. Read the problem

Given an integer array `nums` (can contain NEGATIVE numbers) and an integer `k`, return the COUNT of NON-EMPTY contiguous subarrays whose sum is divisible by `k`.

**Examples:**

- `nums = [4, 5, 0, -2, -3, 1]`, `k = 5`.

Subarrays whose sum is divisible by 5:
- `[4, 5, 0, -2, -3, 1]` — sum 5. ✓
- `[5]` — sum 5. ✓
- `[5, 0]` — sum 5. ✓
- `[5, 0, -2, -3]` — sum 0. ✓
- `[0]` — sum 0. ✓
- `[0, -2, -3]` — sum -5. ✓
- `[-2, -3]` — sum -5. ✓

Count: **7**.

> **Mini-refresher: "divisible by k" includes 0 and negatives.**
>
> "Divisible by k" means the sum mod k equals 0. So sum = 0, sum = 5, sum = -5, sum = 10, sum = -10 all qualify (for k = 5).
>
> 0 is divisible by every k. Negative multiples of k (like -5) are also divisible by k.

---

## 2. The brute force

For every `(l, r)` pair, compute the subarray sum and check divisibility:

```
count = 0
for l in 0..n-1:
    s = 0
    for r in l..n-1:
        s += nums[r]
        if s % k == 0:
            count += 1
return count
```

O(n²). For n = 30,000, that's 9 × 10^8 — TLE.

We need O(n). Hash-based prefix sum trick.

---

## 3. The prefix-sum reformulation

> **Mini-refresher: prefix sums.**
>
> Define `prefix[i] = nums[0] + nums[1] + ... + nums[i-1]` (with `prefix[0] = 0`).
>
> The sum of `nums[l..r]` (inclusive) is `prefix[r+1] - prefix[l]`.
>
> So:
> - Subarray sum divisible by k
> - `iff (prefix[r+1] - prefix[l]) % k == 0`
> - `iff prefix[r+1] % k == prefix[l] % k`

So: **the subarray `nums[l..r]` is divisible by k iff `prefix[l]` and `prefix[r+1]` have the SAME REMAINDER mod k.**

This converts a 2D problem ("for each (l, r) pair") into a 1D one ("count prefixes sharing the same remainder").

---

## 4. Why "same remainder mod k" works

If `prefix[l] ≡ prefix[r+1] (mod k)`, then `prefix[r+1] - prefix[l] ≡ 0 (mod k)`. And `prefix[r+1] - prefix[l]` is the SUM of `nums[l..r]`. So that sum is divisible by k.

Conversely, if the sum is divisible, the difference of prefix sums is 0 mod k, so they're congruent.

The mapping is bijective: **for every pair (l, r) with subarray sum divisible by k, the prefix sums at l and r+1 are congruent.**

So we count "pairs of prefix sums with same remainder mod k."

---

## 5. The counting-pairs trick

> **Mini-refresher: counting same-bucket pairs.**
>
> If we have `n` items distributed into buckets, and the counts are `c_1, c_2, ..., c_B`, then the number of PAIRS within the same bucket is:
>
> `sum over b of c_b · (c_b - 1) / 2`
>
> Equivalently, as we add items one at a time, the running "pair count" is incremented by the CURRENT BUCKET COUNT (before adding this item).

We walk prefix sums, maintain a count of how many we've seen at each remainder. When we reach a new prefix sum with remainder `r`:
- The number of NEW pairs created = the current count at remainder `r`.
- Then increment the count.

```
count = 0
remainders[0..k-1] = all 0
remainders[0] = 1     # sentinel — see Section 7

prefix = 0
for x in nums:
    prefix += x
    r = prefix mod k       # with negative-mod fix; see Section 6
    count += remainders[r]
    remainders[r] += 1

return count
```

---

## 6. The negative-mod gotcha

In many languages, `(-3) % 5` is NOT `2`. It's `-3` in C++/Java, or `2` in Python.

We want the remainder in `[0, k - 1]` consistently. The trick:

```
r = ((prefix % k) + k) % k
```

- Inner `% k`: may give negative.
- Add `k`: makes positive.
- Outer `% k`: normalize to `[0, k)`.

In Python, `prefix % k` always gives non-negative remainder, so the trick is optional but harmless. In C++, JavaScript, Java — it's mandatory.

> **Mini-refresher: how different languages handle negative mod.**
>
> | Expression | Python | C++/Java/JS |
> |---|---|---|
> | `-3 % 5` | `2` | `-3` |
> | `-7 % 5` | `3` | `-2` |
>
> Python's `%` returns the same sign as the DIVISOR. C++/Java/JS return the same sign as the DIVIDEND.
>
> For consistency, use `((a % k) + k) % k`. Safe in all languages.

---

## 7. The sentinel for `remainder == 0`

The sentinel `remainders[0] = 1` represents the "empty prefix" (`prefix = 0` before reading any element).

Why we need it: a subarray `nums[0..r]` is divisible by k iff `prefix[r+1] % k == 0`. This subarray doesn't pair with ANOTHER prefix — it pairs with the EMPTY prefix at index 0 (which has prefix sum 0, remainder 0).

By pre-seeding `remainders[0] = 1`, the first prefix sum with remainder 0 finds a "partner" in this sentinel.

Without the sentinel, you'd undercount subarrays starting at index 0.

---

## 8. Code

**C++:**

```cpp
int subarraysDivByK(vector<int>& nums, int k) {
    vector<int> remainders(k, 0);
    remainders[0] = 1;
    int prefix = 0;
    int count = 0;
    for (int x : nums) {
        prefix += x;
        int r = ((prefix % k) + k) % k;     // non-negative mod
        count += remainders[r];
        remainders[r]++;
    }
    return count;
}
```

**Python:**

```python
def subarraysDivByK(nums, k):
    remainders = [0] * k
    remainders[0] = 1
    prefix = 0
    count = 0
    for x in nums:
        prefix += x
        r = prefix % k                    # Python: always non-negative for positive k
        count += remainders[r]
        remainders[r] += 1
    return count
```

**JavaScript:**

```javascript
function subarraysDivByK(nums, k) {
    const remainders = new Array(k).fill(0);
    remainders[0] = 1;
    let prefix = 0;
    let count = 0;
    for (const x of nums) {
        prefix += x;
        const r = ((prefix % k) + k) % k;
        count += remainders[r];
        remainders[r]++;
    }
    return count;
}
```

Complexity: **O(n) time, O(k) space.**

---

## 9. Trace it

**`nums = [4, 5, 0, -2, -3, 1]`, `k = 5`.**

Walk through, tracking `prefix`, `r`, `remainders`, and running `count`:

```
remainders = [1, 0, 0, 0, 0]. prefix = 0. count = 0.

x=4: prefix=4. r=4. remainders[4]=0 → count+=0. remainders=[1,0,0,0,1].
x=5: prefix=9. r=4. remainders[4]=1 → count+=1, total 1. remainders=[1,0,0,0,2].
x=0: prefix=9. r=4. remainders[4]=2 → count+=2, total 3. remainders=[1,0,0,0,3].
x=-2: prefix=7. r=2. remainders[2]=0 → count+=0. remainders=[1,0,1,0,3].
x=-3: prefix=4. r=4. remainders[4]=3 → count+=3, total 6. remainders=[1,0,1,0,4].
x=1: prefix=5. r=0. remainders[0]=1 → count+=1, total 7. remainders=[2,0,1,0,4].

Return 7.  ✓
```

The sentinel at `remainders[0] = 1` got used at the end (x=1): the full-array sum 5 paired with the empty prefix.

Notice how the remainder-4 bucket accumulated 3 entries by step 5, and that step added 3 pairs all at once — each PREVIOUS prefix with remainder 4 paired with the current one.

---

## 10. Common pitfalls

1. **Forgetting the sentinel `remainders[0] = 1`.** Then subarrays starting at index 0 with sum divisible by k get undercounted. Common bug.

2. **Negative-mod handling.** In C++/Java/JS, `-3 % 5 = -3`. Use `((a % k) + k) % k`.

3. **Forgetting that 0 is divisible by k.** `prefix = 0` with `r = 0` counts. The sentinel handles this.

4. **Confusing this with "Subarray Sum Equals K."** That problem uses `target - prefix[l]` as key. This problem uses `prefix mod k`. Different hash, same template.

5. **Using a HashMap when `remainders[0..k-1]` (array) suffices.** Array is faster (cache-friendly, O(1) hash, no allocation). Use array if k is bounded.

6. **Incrementing remainder count BEFORE looking up.** Order matters: look up FIRST (count pairs with PREVIOUS prefixes), THEN increment.

7. **Overflow on prefix sum.** For very large n and large nums, the prefix sum can exceed `int`. Use `long long` in C++.

8. **Trying to slide a window.** Windows work for non-negative arrays. Here, nums can be negative — sliding windows don't have monotonic sum behavior. Use prefix sum + hash.

9. **Sorting nums.** WRONG — destroys subarray contiguity.

10. **Trying to enumerate all subarrays.** O(n²). The point of this problem is to avoid that.

---

## 11. The shape — congruent prefix sums

The pattern this problem teaches:

> **"Count CONTIGUOUS subarrays with property P on their sum" → prefix sum + hash, where the hash key encodes whatever makes P true.**

| Problem | Key in hash |
|---|---|
| **This problem** (sum % k == 0) | `prefix % k` |
| Subarray Sum Equals K | `prefix - target` |
| Subarray Sum Equals 0 | `prefix` itself |
| Largest Subarray with Sum 0 | `prefix` itself; track first-seen index |
| Continuous Subarray Sum (any subarray length ≥ 2 with sum % k == 0) | same as this, with extra length check |
| Count Subarrays with Sum ≡ x mod k | `(prefix - x) mod k` |

**Pattern to internalize:**

> "Whenever you need to find/count contiguous subarrays satisfying an arithmetic property on their sum, define the prefix sum, identify which TWO prefix-sum values would imply the property, and hash by that key. O(n)."

---

> **Self-check — the question to ask next time.**
>
> When you face "count subarrays with sum satisfying some arithmetic property," ask:
>
> > **"Which prefix-sum values, when paired, would yield a subarray with this property? Use a hash on that key."**
>
> If yes, O(n) solution.

---

## Cross-references

- **Reference card (post-mastery):** [`../Subarray_Sums_Divisible_by_K.md`](../Subarray_Sums_Divisible_by_K.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../Hashing_Sliding_Window/learn/Subarray_Sum_Equals_K.md`](../../Hashing_Sliding_Window/learn/Subarray_Sum_Equals_K.md) — same template, different key.
  - Math topic complete. Next: Bit_Manipulation.
