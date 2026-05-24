# Largest Subarray With 0 Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Largest_Subarray_With_0_Sum.md`](../Largest_Subarray_With_0_Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/find-the-largest-subarray-with-0-sum/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. This problem is the **`k = 0` special case** of "longest subarray with sum equal to k." The mathematical condition simplifies nicely: instead of "two prefix sums differ by k," we need "two prefix sums are EQUAL." Once you see that, the algorithm is a clean application of the prefix-sum + first-occurrence hashmap pattern. **Read [`Maximum_Size_Subarray_Sum_Equals_K.md`](./Maximum_Size_Subarray_Sum_Equals_K.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. Why `k = 0` simplifies the math
3. The algorithm — look for repeated prefix sums
4. Why first-occurrence storage matters here too
5. Code
6. Trace it
7. Common pitfalls
8. The shape — variants built on the "find equal prefix sums" trick

---

## 1. Read the problem

You're given an integer array `arr` (can contain negatives). Find the **length of the longest contiguous subarray** that sums to **zero**. Return 0 if no such subarray exists.

**Example:** `arr = [15, -2, 2, -8, 1, 7, 10, 23]`.

Subarrays summing to 0:

- `[-2, 2]` (indices 1-2): sum = 0, length 2.
- `[-2, 2, -8, 1, 7]` (indices 1-5): sum = -2 + 2 - 8 + 1 + 7 = 0, length 5.

Longest: **5**.

**Other examples:**

- `arr = [1, 2, 3]`: no zero-sum subarray. Return 0.
- `arr = [0]`: the subarray `[0]` sums to 0, length 1. Return 1.
- `arr = [1, -1]`: sums to 0, length 2. Return 2.

---

## 2. Why `k = 0` simplifies the math

Recall from `Subarray_Sum_Equals_K.md`: the sum of `arr[l..r]` equals `k` iff `prefix[r+1] − prefix[l] = k`.

With `k = 0`, this becomes:

```
prefix[r+1] − prefix[l] = 0
```

Or:

```
prefix[r+1] == prefix[l]
```

**Two prefix sums are equal.** That's it.

So the question reduces to: **"In the sequence of prefix sums, find the pair of EQUAL values that are MAXIMALLY FAR APART."** The subarray between them sums to zero, and its length is the gap between their indices.

---

## 3. The algorithm — look for repeated prefix sums

Walk through `arr`, computing prefix sums. Use a hashmap `first[prefix_value → first index where this prefix appeared]`.

For each position `r`:

- Compute the current prefix sum (call it `p`).
- If `p` is ALREADY in the hashmap at some earlier index `i`, the subarray from `i+1` to `r` sums to zero. Length = `r − i`.
- If `p` is NEW, record `first[p] = r`.

Track the maximum length seen.

```
first = {0: -1}                # seed: empty prefix at index -1
current = 0
best = 0

for r in 0..n-1:
    current += arr[r]
    if current in first:
        best = max(best, r - first[current])
    else:
        first[current] = r

return best
```

Same shape as `Maximum_Size_Subarray_Sum_Equals_K`, just simpler: no `complement` computation, because the complement is the prefix value itself.

**O(n) time, O(n) space.**

---

## 4. Why first-occurrence storage matters here too

> **Mini-refresher: first occurrence vs latest for length problems.**
>
> If the same prefix sum value `p` appears at indices `i1 < i2 < ... < ik`, then for any later position `r` where `prefix[r+1] = p`, the matching subarrays have lengths `r − i1`, `r − i2`, ..., `r − ik`. The LONGEST is `r − i1` (using the EARLIEST occurrence).
>
> So: store the FIRST occurrence only. Don't overwrite when a duplicate appears.

In our code that's the `else: first[current] = r` line — we only record if `current` is NOT already in the map.

---

## 5. Code

**C++:**

```cpp
int maxLen(vector<int>& arr) {
    unordered_map<int, int> first;
    first[0] = -1;                              // seed
    int sum = 0;
    int best = 0;

    for (int i = 0; i < (int)arr.size(); i++) {
        sum += arr[i];
        auto it = first.find(sum);
        if (it != first.end()) {
            best = max(best, i - it->second);   // length = i - first occurrence
        } else {
            first[sum] = i;                     // record first occurrence
        }
    }

    return best;
}
```

Ten lines.

**Python:**

```python
def maxLen(arr):
    first = {0: -1}
    s = 0
    best = 0
    for i, x in enumerate(arr):
        s += x
        if s in first:
            best = max(best, i - first[s])
        else:
            first[s] = i
    return best
```

**JavaScript:**

```javascript
function maxLen(arr) {
    const first = new Map([[0, -1]]);
    let sum = 0, best = 0;
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
        if (first.has(sum)) {
            best = Math.max(best, i - first.get(sum));
        } else {
            first.set(sum, i);
        }
    }
    return best;
}
```

All O(n) time, O(n) space.

---

## 6. Trace it

**`arr = [15, -2, 2, -8, 1, 7, 10, 23]`:**

```
first = {0: -1}. sum = 0. best = 0.

i = 0, arr[0] = 15:
    sum = 15.
    15 not in first → first[15] = 0.

i = 1, arr[1] = -2:
    sum = 13.
    13 not in first → first[13] = 1.

i = 2, arr[2] = 2:
    sum = 15.
    15 IS in first at 0. length = 2 - 0 = 2. best = 2.
                                ← subarray [1, 2] = [-2, 2], sum 0.  ✓
    (Don't overwrite first[15].)

i = 3, arr[3] = -8:
    sum = 7.
    7 not in first → first[7] = 3.

i = 4, arr[4] = 1:
    sum = 8.
    8 not in first → first[8] = 4.

i = 5, arr[5] = 7:
    sum = 15.
    15 IS in first at 0. length = 5 - 0 = 5. best = 5.
                                ← subarray [1..5] = [-2, 2, -8, 1, 7], sum 0.  ✓

i = 6, arr[6] = 10:
    sum = 25.
    25 not in first → first[25] = 6.

i = 7, arr[7] = 23:
    sum = 48.
    48 not in first → first[48] = 7.

Return 5.  ✓
```

**`arr = [1, 2, 3]`:**

```
first = {0: -1}. sum = 0.

i=0: sum=1.   first[1]=0.
i=1: sum=3.   first[3]=1.
i=2: sum=6.   first[6]=2.

Loop ends, best stays 0. Return 0.  ✓ (No zero-sum subarray.)
```

**`arr = [0]`:**

```
first = {0: -1}. sum = 0.

i=0, arr[0]=0:
    sum = 0.
    0 IS in first at -1. length = 0 - (-1) = 1. best = 1.
                                ← subarray [0], sum 0.  ✓

Return 1.  ✓
```

The seed `first[0] = -1` is what enables the single-element zero match.

---

## 7. Common pitfalls

1. **Overwriting `first[sum]` on duplicates.** Use `if not in first: first[sum] = i` to preserve the EARLIEST occurrence. Otherwise you get shorter subarrays.

2. **Forgetting the seed `first[0] = -1`.** Misses zero-sum subarrays starting at index 0.

3. **Negative running sums.** The hashmap key is an integer, possibly negative. Most languages handle this fine. In Python, use `dict`; in C++, `unordered_map<int, int>` works.

4. **Off-by-one on length.** Length is `i - first[sum]`. With the seed at `-1`, a subarray from index 0 to `i` has length `i - (-1) = i + 1`. Correct.

5. **Integer overflow.** If `arr` values are large and the array is long, cumulative sum can overflow `int`. Use `long long` if needed.

6. **Trying to use sliding window.** Negatives break sliding window's monotonicity (same reason as Subarray Sum Equals K). Don't try.

---

## 8. The shape — variants built on the "find equal prefix sums" trick

The `k = 0` special case generalizes to many "equal counts of two categories" problems via a clever transformation:

| Problem | Transformation |
|---|---|
| **This problem** (Largest Subarray With 0 Sum) | Use prefix sum directly |
| Contiguous Array (LC #525) — equal 0s and 1s | Treat 0 as -1, 1 as +1, then find longest zero-sum subarray |
| Longest Subarray with Sum K | Look for `prefix - k` instead of `prefix` |
| Find Pivot Index | First position where left-sum equals right-sum (different but related) |
| Subarrays Sums Divisible by K | Two prefix sums share the same `(sum mod K)` |

**Pattern to internalize:**

> "Whenever a problem reduces to **'find the longest contiguous segment where some running quantity returns to its starting value,'** use prefix-sum (or running counter) + hashmap of first-occurrence."

The classic application: replace `0`s with `-1`s in a binary array, then find the longest zero-sum subarray. The resulting subarray has an equal count of `0`s and `1`s (because their `-1`/`+1` contributions cancel). One transformation, infinite mileage.

---

> **Self-check — the question to ask next time.**
>
> When a problem asks for the **longest contiguous segment where some balanced condition holds** (equal counts, sums to zero, returns to start, etc.), before writing nested loops, ask:
>
> > **"Can I encode the 'balance' as a RUNNING quantity (prefix sum, count difference) and look for the EARLIEST repeat of any value in a hashmap?"**
>
> If yes, you've turned O(n²) into O(n) and unlocked dozens of variants of the same trick.

---

## Cross-references

- **Reference card (post-mastery):** [`../Largest_Subarray_With_0_Sum.md`](../Largest_Subarray_With_0_Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Subarray_Sum_Equals_K.md`](./Subarray_Sum_Equals_K.md) — the count variant.
  - [`Maximum_Size_Subarray_Sum_Equals_K.md`](./Maximum_Size_Subarray_Sum_Equals_K.md) — the general length variant; this problem is the `k = 0` case.
