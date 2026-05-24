# Ugly Number II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Ugly_Number_II.md`](../Ugly_Number_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/ugly-number-ii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~25 minutes. This is **the atypical two-pointer** problem in the topic. Instead of two pointers at the ends of an array, you'll use **THREE pointers**, each advancing through the SAME growing array, generating values multiplicatively. The technique is sometimes called **k-way merge with self-reference** — it's elegant once you see it.

**Map of this file (11 short sections):**

1. Read the problem
2. What's an "ugly number"? (with examples)
3. The brute force — check each integer
4. Why brute force fails
5. The pivot — generate ugly numbers directly
6. Heap-based generation (O(n log n))
7. The three-pointer trick (O(n))
8. Why three pointers correctly produce the next ugly number
9. Code
10. Trace it
11. Common pitfalls + the shape

---

## 1. Read the problem

You're given an integer `n`. Return the **n-th ugly number** (1-indexed — the 1st ugly number is `1`, the 2nd is `2`, etc.).

Definition of "ugly" comes next.

---

## 2. What's an "ugly number"?

> **Mini-refresher: prime factorization.**
>
> Every positive integer > 1 can be written as a product of prime numbers (numbers like 2, 3, 5, 7, 11, ... that have no divisors other than 1 and themselves).
>
> Examples:
> - `12 = 2 × 2 × 3` — prime factors: 2, 2, 3 (i.e., 2 and 3).
> - `30 = 2 × 3 × 5` — prime factors: 2, 3, 5.
> - `15 = 3 × 5` — prime factors: 3, 5.
> - `7 = 7` — prime factor: 7 (7 is itself prime).
> - `14 = 2 × 7` — prime factors: 2, 7.
> - `1` — has NO prime factors (by convention; the empty product is 1).

An **ugly number** is a positive integer whose **only prime factors** are in `{2, 3, 5}`. That means:

- 1 (no prime factors — vacuously satisfies) → **ugly**.
- 2, 3, 5 (single prime factor each, in {2, 3, 5}) → **ugly**.
- 4 = 2 × 2 → ugly (only prime factor is 2).
- 6 = 2 × 3 → ugly.
- 7 = 7 → NOT ugly (prime factor 7 is not in {2, 3, 5}).
- 10 = 2 × 5 → ugly.
- 12 = 2 × 2 × 3 → ugly.
- 14 = 2 × 7 → NOT ugly.
- 15 = 3 × 5 → ugly.

So ugly numbers are: `1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, 16, 18, 20, 24, 25, ...`. Note: `7, 11, 13, 14` skipped.

**Sample answers:**

- `n = 1` → `1` (the 1st ugly number).
- `n = 10` → `12` (the 10th ugly number — count from the list above).
- `n = 1690` → `2123366400` (a large value — brute force takes too long here).

---

## 3. The brute force — check each integer

For each integer `k = 1, 2, 3, ...`, check if it's ugly. Count ugly numbers until we hit the n-th.

```cpp
bool isUgly(int k) {
    for (int p : {2, 3, 5}) {
        while (k % p == 0) k /= p;
    }
    return k == 1;
}

int nthUglyNumber(int n) {
    int k = 0, count = 0;
    while (count < n) {
        k++;
        if (isUgly(k)) count++;
    }
    return k;
}
```

`isUgly` divides out all factors of 2, 3, 5; if the residue is 1, the original number's prime factors were all in {2, 3, 5}.

- Time: for each integer up to the answer, we do O(log) divisions.
- For `n = 1690`, the answer is ~2 billion, so we iterate ~2 × 10⁹ times. TLE.

---

## 4. Why brute force fails

Ugly numbers get **sparse** as values grow. Among integers from 1 to 100, about 35 are ugly (35%). From 1 to 10,000, about 1,400 are ugly (14%). From 1 to 10⁹, only about 0.05% are ugly.

So to find the n-th ugly number for large `n`, we sift through huge stretches of non-ugly integers. **Wasteful.** We should generate ugly numbers directly — never look at a non-ugly value.

**Pivot question:** how can we generate the (k+1)-th ugly number directly from the first k ugly numbers?

---

## 5. The pivot — generate ugly numbers directly

Look at the sequence of ugly numbers: `1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 15, ...`.

**Observation:** every ugly number `> 1` is some earlier ugly number multiplied by `2`, `3`, or `5`.

- `2 = 1 × 2`.
- `3 = 1 × 3`.
- `4 = 2 × 2`.
- `5 = 1 × 5`.
- `6 = 2 × 3` (or `3 × 2` — same value).
- `8 = 4 × 2`.
- `9 = 3 × 3`.
- `10 = 2 × 5` (or `5 × 2`).
- `12 = 4 × 3` (or `6 × 2`, etc.).

So the (k+1)-th ugly number is the **smallest value of the form `previous_ugly × p` for `p ∈ {2, 3, 5}`** that hasn't already been added to our list.

This is the generation idea. Two implementations.

---

## 6. Heap-based generation (O(n log n))

Maintain a min-heap of candidate ugly numbers and a set of already-seen values:

```python
import heapq
def nthUglyNumber(n):
    heap = [1]
    seen = {1}
    for _ in range(n):
        x = heapq.heappop(heap)
        for p in [2, 3, 5]:
            v = x * p
            if v not in seen:
                seen.add(v)
                heapq.heappush(heap, v)
    return x
```

Pop the smallest, push its three multiples (deduplicated by the `seen` set). After popping `n` values, the last one popped is the n-th ugly number.

- Time: O(n log n) — n heap operations, each O(log size).
- Space: O(n) for the heap and the set.

Works, but heap operations and set lookups have overhead. There's a faster algorithm.

---

## 7. The three-pointer trick (O(n))

Maintain an array `ugly[]` of ugly numbers being built up. Start with `ugly[0] = 1`.

We need to figure out `ugly[k]` for each `k = 1, 2, ..., n-1`. Each new entry is the smallest "new" value of the form `(some earlier ugly) × 2`, `(some earlier ugly) × 3`, or `(some earlier ugly) × 5`.

Maintain three pointers `i2`, `i3`, `i5` (all start at 0). These point into the `ugly[]` array:

- `i2`: index of the smallest ugly number that, multiplied by 2, hasn't yet been used.
- `i3`: same but for multiplier 3.
- `i5`: same but for multiplier 5.

At each step, compute the three candidates:

- `next2 = ugly[i2] × 2`
- `next3 = ugly[i3] × 3`
- `next5 = ugly[i5] × 5`

The next ugly number is `min(next2, next3, next5)`. Record it. Advance whichever pointer(s) produced the min (advance ALL of them if there's a tie — important for dedup).

```
ugly = array of size n, ugly[0] = 1
i2 = i3 = i5 = 0
for k in 1..n-1:
    next2 = ugly[i2] * 2
    next3 = ugly[i3] * 3
    next5 = ugly[i5] * 5
    next_ugly = min(next2, next3, next5)
    ugly[k] = next_ugly
    if next_ugly == next2: i2++
    if next_ugly == next3: i3++
    if next_ugly == next5: i5++
return ugly[n - 1]
```

- Time: **O(n)**.
- Space: O(n) for the `ugly` array.

No heap. No set. Beautiful.

---

## 8. Why three pointers correctly produce the next ugly number

> **Claim:** at each step, `min(ugly[i2]×2, ugly[i3]×3, ugly[i5]×5)` is the next ugly number after the ones already in `ugly[]`.

**Why:**

1. Every ugly number `> 1` is some earlier ugly number times 2, 3, or 5. (Section 5.)
2. The pointers track, for each multiplier `p`, "the smallest existing ugly number `u` such that `u × p` hasn't been used yet."
3. The smallest candidate among `ugly[i2]×2`, `ugly[i3]×3`, `ugly[i5]×5` is the next ugly number that hasn't been added.
4. After we add `next_ugly`, we advance the pointer(s) corresponding to whichever candidate(s) matched — those `u × p` values are now used, so the next candidate for that multiplier is `ugly[i_p + 1] × p`.

**Why advance ALL pointers on ties:**

When two candidates tie (e.g., `next2 = ugly[2]×2 = 6` and `next3 = ugly[1]×3 = 6` both produce 6), they refer to the SAME ugly number (just two ways to construct it). We add 6 to the array once. If we only advanced ONE pointer, the other would still produce 6 next time — a duplicate. Advancing both pointers marks both constructions of 6 as "used."

---

## 9. Code

**C++:**

```cpp
int nthUglyNumber(int n) {
    vector<int> ugly(n);
    ugly[0] = 1;
    int i2 = 0, i3 = 0, i5 = 0;

    for (int k = 1; k < n; k++) {
        int next2 = ugly[i2] * 2;
        int next3 = ugly[i3] * 3;
        int next5 = ugly[i5] * 5;
        int next_ugly = min({next2, next3, next5});
        ugly[k] = next_ugly;

        // Advance ALL matching pointers (handles duplicates)
        if (next_ugly == next2) i2++;
        if (next_ugly == next3) i3++;
        if (next_ugly == next5) i5++;
    }

    return ugly[n - 1];
}
```

Twelve lines. Concise.

**Python:**

```python
def nthUglyNumber(n):
    ugly = [1] * n
    i2 = i3 = i5 = 0
    for k in range(1, n):
        next2 = ugly[i2] * 2
        next3 = ugly[i3] * 3
        next5 = ugly[i5] * 5
        next_ugly = min(next2, next3, next5)
        ugly[k] = next_ugly
        if next_ugly == next2: i2 += 1
        if next_ugly == next3: i3 += 1
        if next_ugly == next5: i5 += 1
    return ugly[n - 1]
```

**JavaScript:**

```javascript
function nthUglyNumber(n) {
    const ugly = new Array(n);
    ugly[0] = 1;
    let i2 = 0, i3 = 0, i5 = 0;
    for (let k = 1; k < n; k++) {
        const next2 = ugly[i2] * 2;
        const next3 = ugly[i3] * 3;
        const next5 = ugly[i5] * 5;
        const next_ugly = Math.min(next2, next3, next5);
        ugly[k] = next_ugly;
        if (next_ugly === next2) i2++;
        if (next_ugly === next3) i3++;
        if (next_ugly === next5) i5++;
    }
    return ugly[n - 1];
}
```

---

## 10. Trace it

`n = 10` — find the 10th ugly number.

```
ugly = [1, _, _, _, _, _, _, _, _, _]
i2 = i3 = i5 = 0.

k = 1:
    next2 = ugly[0]*2 = 2.
    next3 = ugly[0]*3 = 3.
    next5 = ugly[0]*5 = 5.
    next_ugly = min(2, 3, 5) = 2.
    ugly[1] = 2.   i2++. (i2=1, i3=0, i5=0)

k = 2:
    next2 = ugly[1]*2 = 4.
    next3 = ugly[0]*3 = 3.
    next5 = ugly[0]*5 = 5.
    next_ugly = min(4, 3, 5) = 3.
    ugly[2] = 3.   i3++. (i2=1, i3=1, i5=0)

k = 3:
    next2 = ugly[1]*2 = 4.
    next3 = ugly[1]*3 = 6.
    next5 = ugly[0]*5 = 5.
    next_ugly = min(4, 6, 5) = 4.
    ugly[3] = 4.   i2++. (i2=2, i3=1, i5=0)

k = 4:
    next2 = ugly[2]*2 = 6.
    next3 = ugly[1]*3 = 6.
    next5 = ugly[0]*5 = 5.
    next_ugly = min(6, 6, 5) = 5.
    ugly[4] = 5.   i5++. (i2=2, i3=1, i5=1)

k = 5:
    next2 = ugly[2]*2 = 6.
    next3 = ugly[1]*3 = 6.
    next5 = ugly[1]*5 = 10.
    next_ugly = min(6, 6, 10) = 6.
    ugly[5] = 6.   i2++, i3++.   ← TIE: both pointers advance.   (i2=3, i3=2, i5=1)

k = 6:
    next2 = ugly[3]*2 = 8.
    next3 = ugly[2]*3 = 9.
    next5 = ugly[1]*5 = 10.
    next_ugly = 8.
    ugly[6] = 8.   i2++. (i2=4, i3=2, i5=1)

k = 7:
    next2 = ugly[4]*2 = 10.
    next3 = ugly[2]*3 = 9.
    next5 = ugly[1]*5 = 10.
    next_ugly = 9.
    ugly[7] = 9.   i3++. (i2=4, i3=3, i5=1)

k = 8:
    next2 = ugly[4]*2 = 10.
    next3 = ugly[3]*3 = 12.
    next5 = ugly[1]*5 = 10.
    next_ugly = 10.
    ugly[8] = 10.  i2++, i5++.   ← TIE.   (i2=5, i3=3, i5=2)

k = 9:
    next2 = ugly[5]*2 = 12.
    next3 = ugly[3]*3 = 12.
    next5 = ugly[2]*5 = 15.
    next_ugly = 12.
    ugly[9] = 12.  i2++, i3++.   ← TIE.

Return ugly[9] = 12.   ✓
```

The ugly sequence built: `[1, 2, 3, 4, 5, 6, 8, 9, 10, 12]`. The 10th (index 9) is `12`. Matches our hand-count from §2.

Notice the tie-handling at k=5, k=8, k=9 — advancing both pointers prevents duplicates.

---

## 11. Common pitfalls + the shape

**Common pitfalls:**

1. **Advancing only ONE pointer on a tie.** If `next2 == next3`, you must advance BOTH `i2` and `i3` — otherwise the next iteration will produce the same value again (duplicate in the ugly array). This is the #1 bug in the three-pointer approach.

2. **Starting `ugly[0] = 0` or skipping the base case.** The smallest ugly number is `1`. Initialize `ugly[0] = 1`, not 0.

3. **Integer overflow on `ugly[i] * 5`.** For `n = 1690` (LeetCode's constraint), the answer is `2,123,366,400` — about `2.1 × 10⁹`. Fits in unsigned int32 but NOT in signed int32 (max ~`2.15 × 10⁹`). Use `long long` if multiplying could overflow.

4. **Trying the heap approach when O(n) is requested.** Both work; the three-pointer is just faster and cleaner.

5. **Forgetting that `1` is ugly.** It is — `1` has no prime factors at all, so trivially none of them are outside `{2, 3, 5}`.

**The shape — k-way merge with self-reference:**

The three-pointer technique is a special case of a more general pattern: **merging k sorted infinite sequences with a finite number of pointers**.

| Problem | Sequences being merged |
|---|---|
| **This problem** (Ugly Number II) | `{ugly × 2}`, `{ugly × 3}`, `{ugly × 5}` — three sequences |
| Super Ugly Number (LC #313) | `{ugly × p}` for each prime in a custom prime list — k sequences |
| Merge k sorted arrays | k pre-built sorted arrays |
| Median of two sorted arrays | two sorted arrays |
| K-th smallest in sorted matrix | rows or columns as sorted sequences |

**Pattern to internalize:**

> "When you need to generate items in sorted order from multiple monotonically-increasing source sequences, use **one pointer per source sequence**. Each step: pick the minimum across the pointers' current candidates. Advance that pointer (or all pointers tied for the minimum, to dedup)."

The self-referential twist in this problem — the source sequences reference the BUILDING array itself — makes it especially elegant: we generate the next ugly number using only the ones we've generated before, with three small pointers and no extra data structures.

---

> **Self-check — the question to ask next time.**
>
> When asked to generate the n-th value of a sequence where **each new value is the smallest-not-yet-used result of multiplying earlier values by a small fixed set of multipliers**, before reaching for a heap, ask:
>
> > **"Can I maintain one pointer per multiplier, and pick the smallest candidate, advancing all pointers tied for the minimum?"**
>
> If yes, you've turned O(n log n) into O(n) without auxiliary data structures.

---

## Cross-references

- **Reference card (post-mastery):** [`../Ugly_Number_II.md`](../Ugly_Number_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Other Two_Pointers problems in this topic — though Ugly Number II is the atypical one (3 forward-moving pointers vs the usual 2 converging pointers).
  - Coming later in Heap topic: Merge K Sorted Lists, Find K Pairs with Smallest Sums, Find Median from Data Stream — all use the same multi-pointer / heap-based "merge sorted sequences" idea.
  - Coming later: Super Ugly Number (Heap topic) — generalizes this problem to k custom primes via a heap.
