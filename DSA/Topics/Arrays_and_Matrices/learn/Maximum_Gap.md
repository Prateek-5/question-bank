# Maximum Gap — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Gap.md`](../Maximum_Gap.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/maximum-gap/

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~35 minutes. This problem teaches **the pigeonhole principle as an algorithmic tool** — a piece of plain counting reasoning that powers many "beat the obvious sort" tricks in linear-time algorithms. The pigeonhole argument is genuinely subtle the first time. Take it slow; do the small example by hand.

**Map of this file (12 short sections):**

1. Read the problem
2. The obvious approach: sort and scan
3. Why "sort and scan" might not be enough
4. The pivot — average gap vs max gap
5. The pigeonhole principle (the engine of the trick)
6. The bucket-sort plan
7. Why the max gap must lie ACROSS buckets, not within
8. Bucket-width arithmetic (the tricky bit)
9. Code
10. Trace it on `[3, 6, 9, 1]`
11. Common pitfalls
12. The shape — where pigeonhole appears later

---

## 1. Read the problem

You're given an unsorted integer array `nums`. Imagine sorting it. Then look at the differences between consecutive elements in that sorted order. Return the **largest such difference**.

If the array has fewer than 2 elements, return `0` (there are no "consecutive pairs").

Example: `nums = [3, 6, 9, 1]`.

```
sorted:        [1,  3,  6,  9]
gaps:           ↑──↑──↑──↑
                  2   3   3
max gap = 3
```

Return **3**.

The twist the problem adds: **your solution should run in linear time and use linear extra space — O(n) and O(n).** No `n log n` sorting allowed (officially).

---

## 2. The obvious approach: sort and scan

The most natural code:

```
sort nums
best = 0
for i in 1..n-1:
    gap = nums[i] - nums[i-1]
    best = max(best, gap)
return best
```

`O(n log n)` time (because of the sort), `O(1)` extra space (most sort algorithms sort in place).

For `n ≤ 10⁵`, this is fast enough in practice — about `10⁵ × 17 ≈ 2 × 10⁶` operations, milliseconds.

> **Mini-refresher: why is sorting O(n log n)?**
>
> Comparison-based sorts (quicksort, mergesort, heapsort) make about `n × log₂(n)` comparisons. The reason is information-theoretic: there are `n!` possible orderings of `n` items, and each comparison gives you 1 bit of information about which ordering you have. So you need at least `log₂(n!) ≈ n log₂(n)` comparisons. This is a hard lower bound — no comparison-based sort can beat it.
>
> But this lower bound is for **comparison-based** sorting. If you can use the **structure of the data** (like "these are integers in a known range"), you can sometimes do better — and that's the door we're about to walk through.

---

## 3. Why "sort and scan" might not be enough

For the typical interviewer, "O(n log n)" is fine and you might get away with it. But the problem **explicitly** asks for linear time. Why? Because:

- It's a way to surface the senior-bar trick (which we're about to derive).
- In real life, when n gets huge (billions), `n log n` becomes meaningful — `n log n` is ~30× slower than `n` at `n = 10⁹`.

So we need an `O(n)` algorithm. This rules out comparison-based sorting entirely. What else do we have?

The structure we can exploit: we have **n numbers in a range `[min, max]`**. We can find `min` and `max` in `O(n)`. Then maybe we can use that range somehow.

But how does knowing the range help us find the max gap? Let's think.

---

## 4. The pivot — average gap vs max gap

The `n` numbers sorted lie somewhere in `[min, max]`. The total distance from `min` to `max` is `max - min`. Between them, in the sorted order, there are `n - 1` gaps. Their sum equals `max - min` exactly (telescoping: the gaps add up to the full span).

```
sorted:    min ──gap₁── x ──gap₂── y ──gap₃── ... ──gapₙ₋₁── max
total:     (gap₁ + gap₂ + ... + gapₙ₋₁) = max - min
average:   (max - min) / (n - 1)
```

So the **average** gap is `(max - min) / (n - 1)`.

Here's the key observation: **the maximum gap must be ≥ the average gap.** That's just math — you can't have all `n - 1` gaps below the average; some must be at or above it.

So:

```
max_gap ≥ (max - min) / (n - 1)
```

Call this value `w` (the average gap). The max gap is at least `w`. Important!

That gives us a lower bound on what we're searching for. Where does pigeonhole come in?

> **The pivot question:** What if I divide the range `[min, max]` into buckets of width `w`? Then any gap within a single bucket is small — at most `w`. And we just established that the max gap is at least `w`. So **the max gap can't lie within a bucket — it must lie across buckets.** That means we can ignore within-bucket details entirely.

This is the central insight. Let me unpack it carefully because the argument has multiple moving parts.

---

## 5. The pigeonhole principle (the engine of the trick)

> **Mini-refresher: the pigeonhole principle.**
>
> If you have `k + 1` items and only `k` boxes, then at least one box has 2 or more items. That's the formal statement.
>
> A more useful version for algorithms: **if you spread `n` items across `m` "buckets" (where `m < n`), at least one bucket has at least `⌈n / m⌉` items.**
>
> Example: 13 pigeons in 12 holes → some hole has ≥ 2 pigeons. (You can't avoid it; there's no way to give each pigeon its own hole.)
>
> The reasoning we'll use is the dual: **if `n` items are spread across `m` buckets WITH `m ≥ n`, some bucket must be EMPTY** (when `m > n`) — or at the boundary `m = n - 1` for our problem, some buckets are guaranteed to be sparse.
>
> Pigeonhole is the workhorse of "there must exist a thing with property X" arguments in counting.

For our problem: we'll create `n - 1` buckets and place `n` numbers into them. By pigeonhole, some bucket holds ≥ 2 numbers, but also — crucially — there's enough room that **some buckets may be empty** when the numbers are spread out. The empty buckets become the location of the max gap.

(More on this in the next two sections.)

---

## 6. The bucket-sort plan

Here's the algorithm. We're going to:

1. Find `min` and `max` of the array in one pass.
2. Divide `[min, max]` into `n - 1` buckets of width `w = (max - min) / (n - 1)`.
3. For each number in `nums`, figure out which bucket it falls into, and track that bucket's **min and max value** (we don't care about everything in between).
4. Walk the buckets left to right. For each non-empty bucket, the max gap candidate is `(this bucket's min) - (previous non-empty bucket's max)`. Track the largest such candidate.
5. Return it.

That's it. The whole algorithm is three linear passes. Total work: `O(n)`.

Now I owe you a careful justification for why step 4 finds the **true** max gap. That's section 7.

---

## 7. Why the max gap must lie ACROSS buckets, not within

This is the heart of the algorithm. Pay close attention.

**Claim:** if you choose bucket width `w = (max - min) / (n - 1)`, then **no gap WITHIN a single bucket can be the maximum gap.** The max gap must lie between the max of one bucket and the min of the next non-empty bucket to its right.

**Proof, step by step:**

(a) **Average gap formula.** As we worked out, sorted gaps `g₁ + g₂ + ... + gₙ₋₁ = max - min`. There are `n - 1` of them. Their average is `(max - min) / (n - 1) = w`.

(b) **Max gap ≥ average.** You cannot have all `n - 1` gaps strictly below the average — that would make their sum strictly less than `(n - 1) × average = max - min`, contradicting (a). So at least one gap is ≥ `w`. Hence `max_gap ≥ w`.

(c) **Within a bucket, any gap is < w.** A bucket has width `w` and holds numbers in some range `[bucket_low, bucket_low + w)`. Any two numbers in the same bucket differ by **strictly less than** `w`. So a within-bucket gap is strictly less than `w`.

(d) **Combine (b) and (c).** Max gap is ≥ `w`. Within-bucket gaps are < `w`. So **the max gap is strictly greater than any within-bucket gap, meaning the max gap is NOT a within-bucket gap.** It must be a between-bucket gap.

That's the entire argument. With width `w`, within-bucket gaps are "too small to be the max." Cross-bucket gaps are where the action is.

**Therefore:** to find the max gap, we only need to look at, for each pair of adjacent non-empty buckets, the gap from one bucket's max to the next bucket's min. We don't need to know anything else about what's inside.

That's why **we only store each bucket's min and max value**, not all the numbers in it. Brilliant compression.

---

## 8. Bucket-width arithmetic (the tricky bit)

Here's where the implementation gets fiddly. We need to:

- Choose `width` such that we get exactly `n - 1` buckets (or close enough that the pigeonhole argument still works).
- Decide which bucket a value `x` falls into.
- Handle edge cases (`min == max`, integer division issues).

**Choosing width.**

```
width = (max - min) / (n - 1)
```

Using **integer division** in C++/Java, this can round down. To avoid creating too many buckets, take the larger of this and 1:

```
width = max(1, (max - min) / (n - 1))
```

(Width 0 would create an infinite number of buckets — bad. Width 1 is the floor for integer arrays.)

**Bucket index for value `x`.**

```
bucket_idx = (x - min) / width
```

Translate `x` to `0`-based ("how much above `min` is `x`?"), divide by width, integer-divide to get an integer index. The smallest value `min` lands in bucket 0; the largest value `max` lands in the last bucket.

**Number of buckets.**

The last bucket contains `max`, whose index is `(max - min) / width`. So we need `(max - min) / width + 1` buckets total.

**Edge case: `min == max`.** All elements identical. Max gap is `0` — return early to dodge division-by-zero.

> **Mini-refresher: integer division in different languages.**
>
> `7 / 2` in C++ / Java integer context is `3` (truncates toward zero). In Python, that operator gives `3.5` — use `7 // 2` for integer division (which gives `3`). In JavaScript, all `/` is floating-point — use `Math.floor(7 / 2)` for the integer result.
>
> For Maximum Gap, the C++ behavior (`/` truncates) is exactly what we want. In Python, write `//`. In JavaScript, use `Math.floor`.

---

## 9. Code

```cpp
int maximumGap(vector<int>& nums) {
    if (nums.size() < 2) return 0;

    int mn = *min_element(nums.begin(), nums.end());
    int mx = *max_element(nums.begin(), nums.end());
    if (mn == mx) return 0;                       // all elements identical

    int n = nums.size();
    int width = max(1, (mx - mn) / (n - 1));      // bucket width
    int numBuckets = (mx - mn) / width + 1;       // last bucket holds mx

    vector<int> bucketMin(numBuckets, INT_MAX);
    vector<int> bucketMax(numBuckets, INT_MIN);

    // Pass 1: distribute numbers into buckets, tracking per-bucket min/max
    for (int x : nums) {
        int idx = (x - mn) / width;
        bucketMin[idx] = min(bucketMin[idx], x);
        bucketMax[idx] = max(bucketMax[idx], x);
    }

    // Pass 2: walk buckets left to right, compute cross-bucket gaps
    int prevMax = mn;        // start with the smallest possible "previous"
    int maxGap = 0;
    for (int i = 0; i < numBuckets; i++) {
        if (bucketMin[i] == INT_MAX) continue;    // empty bucket — skip
        maxGap = max(maxGap, bucketMin[i] - prevMax);
        prevMax = bucketMax[i];
    }

    return maxGap;
}
```

Key implementation details:

- `width = max(1, …)` prevents both division-by-zero (when `mx - mn` is small) and zero-width buckets.
- Empty buckets are detected by `bucketMin[i] == INT_MAX` (still at the sentinel we initialized to). They're skipped — no cross-bucket gap is computed against them as the "current" bucket.
- `prevMax` starts at `mn`, which corresponds to the "min of the first non-empty bucket" being compared against an imaginary "0th bucket" containing `mn`. On the first non-empty bucket, the first gap candidate `bucketMin[0] - mn = 0` (since the first bucket always contains `mn`). That's correct — no actual gap there.

---

## 10. Trace it on `[3, 6, 9, 1]`

```
nums = [3, 6, 9, 1]
n = 4

Pass 0: find min/max.
    mn = 1, mx = 9.
    mn ≠ mx, continue.

Bucket setup:
    width = max(1, (9 - 1) / (4 - 1)) = max(1, 8/3) = max(1, 2) = 2.
    numBuckets = (9 - 1) / 2 + 1 = 4 + 1 = 5.

    Actually, let me adopt width = 2, numBuckets = 5:
        Bucket 0:  values in [1, 3)  →  {1}
        Bucket 1:  values in [3, 5)  →  {3}
        Bucket 2:  values in [5, 7)  →  {6}
        Bucket 3:  values in [7, 9)  →  {} (empty!)
        Bucket 4:  values in [9, 11) →  {9}

Pass 1: bucket each number.
    x = 3:   idx = (3-1)/2 = 1.   bucketMin[1] = 3.   bucketMax[1] = 3.
    x = 6:   idx = (6-1)/2 = 2.   bucketMin[2] = 6.   bucketMax[2] = 6.
    x = 9:   idx = (9-1)/2 = 4.   bucketMin[4] = 9.   bucketMax[4] = 9.
    x = 1:   idx = (1-1)/2 = 0.   bucketMin[0] = 1.   bucketMax[0] = 1.

After pass 1:
    bucketMin = [1, 3, 6, INT_MAX, 9]
    bucketMax = [1, 3, 6, INT_MIN, 9]

Pass 2: walk buckets left to right.
    prevMax = mn = 1.
    maxGap = 0.

    i = 0:  bucketMin[0] = 1 (not empty).
        gap candidate = 1 - 1 = 0.
        maxGap = max(0, 0) = 0.
        prevMax = bucketMax[0] = 1.

    i = 1:  bucketMin[1] = 3 (not empty).
        gap candidate = 3 - 1 = 2.
        maxGap = max(0, 2) = 2.
        prevMax = bucketMax[1] = 3.

    i = 2:  bucketMin[2] = 6 (not empty).
        gap candidate = 6 - 3 = 3.
        maxGap = max(2, 3) = 3.
        prevMax = bucketMax[2] = 6.

    i = 3:  bucketMin[3] = INT_MAX (EMPTY). Skip.

    i = 4:  bucketMin[4] = 9 (not empty).
        gap candidate = 9 - 6 = 3.
        maxGap = max(3, 3) = 3.
        prevMax = bucketMax[4] = 9.

Return maxGap = 3.   ✓
```

Compare to brute force (sort and scan):

```
sorted: [1, 3, 6, 9]
gaps: 2, 3, 3
max gap: 3
```

Same answer. ✓

Notice how the empty bucket (bucket 3) was the gap-creator — the `5..7` and `7..9` regions span what would be the within-bucket-3 territory. We correctly identified `6 → 9` as the max gap because bucket 3 between them is empty.

---

## 11. Common pitfalls

1. **Division by zero when `mn == mx`.** All elements equal → max gap is 0. Return early before computing `width`. The code above does this with `if (mn == mx) return 0;`.

2. **Integer overflow on `mx - mn`.** If `nums` can contain `INT_MIN` and `INT_MAX`, then `mx - mn` overflows in 32-bit. Use `long long` (C++) or 64-bit integers explicitly.

3. **Off-by-one in number of buckets.** `(mx - mn) / width + 1` is correct (last bucket index plus 1). Forgetting the `+ 1` undersizes the array and the largest value's bucket index is out of bounds.

4. **Choosing `width = (mx - mn) / (n - 1)` without the `max(1, …)`.** When `mx - mn < n - 1` (lots of duplicates close together), integer division gives 0. Buckets of width 0 break everything.

5. **Starting `prevMax = INT_MIN`.** Tempting, but then the first non-empty bucket gives a huge spurious `bucketMin - prevMax`. Start `prevMax = mn` instead — the first bucket's `bucketMin` will be exactly `mn` (or higher), giving `0` as the first "gap" — correctly indicating no gap before `min`.

6. **Forgetting why this is `O(n)`.** Pass 1 is `O(n)` (n numbers, one bucket update each). Pass 2 is `O(numBuckets)` = `O(n)`. Total `O(n)`. If you accidentally do something `O(n)` inside the inner loop of pass 1, you've slid back to `O(n²)` without realizing.

---

## 12. The shape — where pigeonhole appears later

The pigeonhole-meets-bucket idiom shows up in several "beat the obvious" algorithms:

| Problem | Pigeonhole argument | Trick |
|---|---|---|
| **Maximum Gap** (this problem) | Max gap ≥ avg gap = bucket width, so max gap lies cross-bucket | bucket sort with per-bucket min/max |
| **Find Missing Positive** (LC #41) | n numbers, at least one of `1..n+1` is missing — pigeonhole | in-place index marking |
| **Contains Duplicate III** (LC #220) | Buckets of width `t`, equal-bucket pairs are within distance `t` | bucket of value, sliding window |
| **First Missing Number in Stream** | n numbers in n buckets → some bucket sparse | hashing / bitset |
| **Linked List Cycle II** (Floyd's) | After `μ + λ` steps in cycle of length `λ`, pointers must meet | tortoise-and-hare |

The pattern: **you have a counting argument (pigeonhole, average ≤ max, etc.) that tells you something must exist with a particular property. Once you know "where" such a thing lives, you don't need to search exhaustively — you can use the structure to find it in linear time.**

---

> **Self-check — the question to ask next time.**
>
> When you see a problem that **looks like it needs sorting (O(n log n))**, but the constraints insist on **O(n)**, ask:
>
> > **"Can I use a counting argument — pigeonhole, averaging, or the range of the data — to prove that the answer lives in a small subset of possibilities? If so, can I bucket the data so the within-bucket details don't matter?"**
>
> If yes, you've turned a comparison-sort problem into a bucket-sort problem, and the constants of "O(n) extra space" buy you "O(n) time."

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Gap.md`](../Maximum_Gap.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs (when written):** Sorting topic has bucket sort relatives; Searching topic has "beat O(n log n) with structural arguments."
