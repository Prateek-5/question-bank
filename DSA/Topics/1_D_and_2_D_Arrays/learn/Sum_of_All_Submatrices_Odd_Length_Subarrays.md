# Sum of All Odd-Length Subarrays — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Sum_of_All_Submatrices_Odd_Length_Subarrays.md`](../Sum_of_All_Submatrices_Odd_Length_Subarrays.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/sum-of-all-odd-length-subarrays/
>
> **Note on the filename:** The folder name says "Submatrices" but the problem is about subarrays (1D). The original file's content matches the LeetCode problem (odd-length **subarrays**); the filename is a small mismatch in the repo.

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~25 minutes. The big lesson: **per-element contribution counting** — instead of iterating over all subarrays and summing them, ask "how many subarrays does each element appear in?" and multiply. This trick turns many O(n²) or O(n³) "sum-over-subarrays" problems into O(n).

**Map of this file (11 short sections):**

1. Read the problem
2. The natural brute force (O(n³))
3. Prefix-sum speed-up (O(n²))
4. The pivot — flip the perspective
5. Counting "subarrays that contain index `i`"
6. Among those, how many have ODD length?
7. The clean formula
8. Code
9. Trace it
10. Common pitfalls
11. The shape — contribution counting everywhere

---

## 1. Read the problem

You're given an integer array `arr`. Consider every **contiguous subarray** with odd length (1, 3, 5, ...). For each, compute its sum. Return the **total** of all those sums.

> **Mini-refresher: contiguous subarrays.**
>
> A subarray is a slice of consecutive elements: `arr[i..j]` for some `i ≤ j`. The length is `j − i + 1`.
>
> For `arr = [a, b, c, d]`:
> - Length 1: `[a]`, `[b]`, `[c]`, `[d]` — 4 of these.
> - Length 2: `[a,b]`, `[b,c]`, `[c,d]` — 3 of these.
> - Length 3: `[a,b,c]`, `[b,c,d]` — 2 of these.
> - Length 4: `[a,b,c,d]` — 1 of these.
>
> Total: 10 subarrays. Note "contiguous" — no skipping elements.

**Example:** `arr = [1, 4, 2, 5, 3]`. Odd-length subarrays and their sums:

```
Length 1 (5 subarrays):
    [1] = 1
    [4] = 4
    [2] = 2
    [5] = 5
    [3] = 3
    sum of these = 15

Length 3 (3 subarrays):
    [1, 4, 2] = 7
    [4, 2, 5] = 11
    [2, 5, 3] = 10
    sum of these = 28

Length 5 (1 subarray):
    [1, 4, 2, 5, 3] = 15
    sum of these = 15

Grand total = 15 + 28 + 15 = 58
```

Answer: **58**.

---

## 2. The natural brute force (O(n³))

The most direct translation:

```cpp
int sumOddLengthSubarrays(vector<int>& arr) {
    int n = arr.size();
    int total = 0;
    for (int len = 1; len <= n; len += 2) {        // odd lengths only: 1, 3, 5, ...
        for (int start = 0; start + len <= n; start++) {
            int s = 0;
            for (int k = start; k < start + len; k++) {   // sum the subarray
                s += arr[k];
            }
            total += s;
        }
    }
    return total;
}
```

Three nested loops:

- Outer: O(n/2) odd lengths.
- Middle: O(n) start positions.
- Inner: O(n) elements per subarray.

Total: **O(n³)**.

For `n = 100`, that's 10⁶ ops — fine. For `n = 1000`, 10⁹ — too slow.

We can do better.

---

## 3. Prefix-sum speed-up (O(n²))

> **Mini-refresher: prefix sums for O(1) range sums.**
>
> Build `prefix[i+1] = arr[0] + arr[1] + ... + arr[i]` (with `prefix[0] = 0`). Then the sum of `arr[l..r]` equals `prefix[r+1] − prefix[l]` — one subtraction.
>
> Building the prefix array is one linear pass. Each range-sum query becomes O(1) afterwards. (See `Running_Sum_of_1D_Array.md` for the introduction.)

Replace the inner summing loop with a prefix-sum lookup:

```cpp
int sumOddLengthSubarrays(vector<int>& arr) {
    int n = arr.size();
    vector<int> prefix(n + 1, 0);
    for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + arr[i];

    int total = 0;
    for (int len = 1; len <= n; len += 2) {
        for (int start = 0; start + len <= n; start++) {
            int end = start + len;
            total += prefix[end] - prefix[start];     // sum of arr[start..end-1] in O(1)
        }
    }
    return total;
}
```

Two nested loops, each O(n). Total: **O(n²)**.

For `n = 1000`, that's 10⁶ — fast. For `n = 10⁵`, 10¹⁰ — too slow again.

For LeetCode's constraints (`n ≤ 100`), this is more than enough. But for the sake of learning, let me push further.

---

## 4. The pivot — flip the perspective

So far we've been iterating over **subarrays** and summing them. The total is:

```
Total = sum over all odd-length subarrays S of (sum of elements in S)
      = sum over all odd-length subarrays S of (sum over elements e in S of arr[e])
```

That's a double sum. **What if we swap the order?**

```
Total = sum over elements e of (sum over odd-length subarrays S containing e of arr[e])
      = sum over elements e of (arr[e] × (count of odd-length subarrays containing e))
```

Same total — same numbers added — just grouped differently. (Same trick as Total Hamming Distance: addition doesn't care about grouping; swap the order of summation if it makes counting easier.)

The new question is:

> **"For each index `i`, how many odd-length subarrays contain `arr[i]`?"**

If we can compute that count efficiently for each `i`, then:

```
Total = sum over i of arr[i] × count_odd_containing(i)
```

This is O(n) per element if the count is O(1). Hello O(n) total.

---

## 5. Counting "subarrays that contain index `i`"

Let's start with the easier question first: **how many TOTAL subarrays (of any length) contain index `i`?**

A subarray is `arr[start..end]`. It contains `i` iff `start ≤ i ≤ end`.

- Choices of `start`: `0, 1, 2, ..., i`. That's `i + 1` options.
- Choices of `end`: `i, i + 1, i + 2, ..., n − 1`. That's `n − i` options.
- Each (start, end) pair gives one subarray, and they're independent.

So the **total number of subarrays containing index `i` is `(i + 1) × (n − i)`**.

> **Mini-refresher: multiplication rule for counting.**
>
> If you're forming a combination by picking one item from set A and one from set B, the total count is `|A| × |B|`. (Same idea as outfits = shirts × pants.)
>
> Here: a subarray is determined by (start, end). Start has `i + 1` choices, end has `n − i` choices, and they're independent. Total: their product.

Let me verify on a small case. `arr = [a, b, c]` (n = 3), index `i = 1` (the middle element `b`):

- Subarrays containing `b`:
  - `[b]`
  - `[a, b]`
  - `[b, c]`
  - `[a, b, c]`

4 subarrays. Formula: `(1 + 1) × (3 − 1) = 2 × 2 = 4`. ✓

Good. Now the harder question.

---

## 6. Among those, how many have ODD length?

Among the `(i + 1) × (n − i)` total subarrays containing index `i`, we want only the ones with **odd length**.

A subarray's length is `end − start + 1`. Odd iff `end − start` is even — meaning `start` and `end` have the **same parity**.

So we need: count of (start, end) pairs with `start ≤ i ≤ end` **AND** `start ≡ end (mod 2)`.

Let's split by parity:

- `start` ranges over `[0, i]`. Among these, how many are even? How many odd?
- `end` ranges over `[i, n − 1]`. Same split.

A pair has same parity iff (both even) OR (both odd). So:

```
odd_length_count = (even starts × even ends) + (odd starts × odd ends)
```

That's a closed form, but it depends on details (whether `i`, `0`, `n − 1` are even or odd). Fiddly to compute case-by-case.

**Lucky observation:** there's a clean closed form. Let `T = (i + 1) × (n − i)` (total subarrays containing `i`). Then:

```
odd_length_count = (T + 1) / 2     using integer division (floor)
```

This works for all `i` and `n`. It's the formula we'll use.

> **Why does the simple formula `(T + 1) / 2` work?**
>
> Think about subarrays of every length containing `i`, listed by length:
> - Length 1: exactly 1 (just `[arr[i]]` itself).
> - Length 2: subarrays `arr[i-1..i]` and `arr[i..i+1]` — up to 2, fewer at the array edges.
> - Length 3: subarrays `arr[i-2..i]`, `arr[i-1..i+1]`, `arr[i..i+2]` — up to 3, fewer at edges.
> - ...
>
> For each length L, the count of subarrays of that length containing `i` is some small number ≤ L. **Odd-length counts add up to one more than (or equal to) even-length counts**, because length 1 always counts as odd and adds 1.
>
> Specifically: if T is even, odds and evens split evenly: odd_count = T / 2 + 1, even_count = T / 2 − 1 (something close to this — exact bookkeeping involves cases). Approximation: `(T + 1) / 2` rounds up, and it turns out to be the EXACT count of odd-length subarrays.
>
> Rather than belabor a proof, let me just verify it on small cases.

**Verify the formula on `arr = [a, b, c]` (n = 3), `i = 1` (middle):**

- T = 2 × 2 = 4.
- Formula gives `(4 + 1) / 2 = 2` (integer division).
- Hand-count: among the 4 subarrays containing `b` (`[b], [a,b], [b,c], [a,b,c]`), the odd-length ones are `[b]` (length 1) and `[a,b,c]` (length 3) — **2 of them**. ✓

**Verify on `i = 0` (first element) of n = 3:**

- T = 1 × 3 = 3.
- Formula: `(3 + 1) / 2 = 2`.
- Subarrays containing `arr[0] = a`: `[a], [a,b], [a,b,c]`. Odd lengths: `[a]` (length 1), `[a,b,c]` (length 3). **2.** ✓

**Verify on `i = 2` (last element) of n = 5:**

- T = 3 × 3 = 9.
- Formula: `(9 + 1) / 2 = 5`.
- Subarrays containing `arr[2]`: 9 total. Among those, odd-length ones — let me count:
  - Length 1: `[arr[2]]`. 1.
  - Length 3: `[arr[0..2]], [arr[1..3]], [arr[2..4]]`. 3.
  - Length 5: `[arr[0..4]]`. 1.
  - Total: 1 + 3 + 1 = 5. ✓

The formula works.

---

## 7. The clean formula

So the per-element contribution is:

```
For each index i:
    T = (i + 1) × (n − i)               # total subarrays containing i
    odd_count = (T + 1) / 2              # subarrays of odd length containing i (integer div)
    contribution = arr[i] × odd_count
total = sum of contributions
```

One linear pass over the array. **O(n) time, O(1) space.**

---

## 8. Code

```cpp
int sumOddLengthSubarrays(vector<int>& arr) {
    int n = arr.size();
    int total = 0;
    for (int i = 0; i < n; i++) {
        int T = (i + 1) * (n - i);
        int oddCount = (T + 1) / 2;
        total += arr[i] * oddCount;
    }
    return total;
}
```

Six lines.

**Python:**

```python
def sumOddLengthSubarrays(arr):
    n = len(arr)
    total = 0
    for i, x in enumerate(arr):
        T = (i + 1) * (n - i)
        odd_count = (T + 1) // 2          # // for integer division in Python
        total += x * odd_count
    return total
```

**JavaScript:**

```javascript
function sumOddLengthSubarrays(arr) {
    const n = arr.length;
    let total = 0;
    for (let i = 0; i < n; i++) {
        const T = (i + 1) * (n - i);
        const oddCount = Math.floor((T + 1) / 2);
        total += arr[i] * oddCount;
    }
    return total;
}
```

All three: single pass, constant extra state.

---

## 9. Trace it

`arr = [1, 4, 2, 5, 3]`, n = 5.

```
total = 0

i = 0, arr[0] = 1:
    T = 1 × 5 = 5
    odd_count = (5 + 1) / 2 = 3
    contribution = 1 × 3 = 3
    total = 3

i = 1, arr[1] = 4:
    T = 2 × 4 = 8
    odd_count = (8 + 1) / 2 = 4
    contribution = 4 × 4 = 16
    total = 19

i = 2, arr[2] = 2:
    T = 3 × 3 = 9
    odd_count = (9 + 1) / 2 = 5
    contribution = 2 × 5 = 10
    total = 29

i = 3, arr[3] = 5:
    T = 4 × 2 = 8
    odd_count = 4
    contribution = 5 × 4 = 20
    total = 49

i = 4, arr[4] = 3:
    T = 5 × 1 = 5
    odd_count = 3
    contribution = 3 × 3 = 9
    total = 58

Return 58.  ✓
```

Matches the hand-count from §1.

Notice how each element's contribution is "how many odd-length subarrays it's part of, weighted by its value." `arr[2] = 2` is in the middle, so it's in the most subarrays (T = 9), hence the highest odd-count (5). Edge elements like `arr[0]` and `arr[4]` are in fewer subarrays.

---

## 10. Common pitfalls

1. **Confusing odd-length subarrays with subarrays of odd values.** The problem is about subarrays whose LENGTH is odd — not subarrays whose elements are odd. `[2, 4, 6]` has length 3 (odd) regardless of its values.

2. **Off-by-one in the total count formula.** `T = (i + 1) × (n − i)`. The `i + 1` counts choices `[0..i]` (inclusive of both endpoints). The `n − i` counts `[i..n − 1]` (inclusive). Skipping the `+ 1` or the `−` gives wrong counts.

3. **Floating-point divide.** In Python, `T / 2` is floating-point — gives 4.5 for T = 9. Use `T // 2` for integer division. In JavaScript, `Math.floor((T + 1) / 2)`.

4. **Forgetting the `+ 1` in `(T + 1) / 2`.** The formula needs to round up. With integer division, `(T + 1) / 2` is the correct "ceiling of T/2." Skipping the `+ 1` gives floor of T/2 — which undercounts by 1 when T is odd.

5. **Using O(n²) when interviewer asks O(n).** For LeetCode this passes, but if the interviewer says "now do it in O(n)" and you're stuck, this is the trick they want to see.

6. **Trying to derive `(T + 1) / 2` rigorously by hand under interview pressure.** Memorize the small-case verification approach: pick i = 0 and i = (n-1)/2, count by hand, confirm the formula matches.

---

## 11. The shape — contribution counting everywhere

The technique you just learned is one of the most reused "secret weapons" in array problems:

> **Per-element contribution counting:**
>
> Instead of iterating over all groups (subarrays, pairs, intervals) and summing some quantity, ask "for each ELEMENT, how many groups does it participate in?" — then multiply by its value and sum. This swap-the-order-of-summation trick collapses many "O(n²)-looking" problems to O(n).

Examples in the wild:

| Problem | Per-element contribution | Total |
|---|---|---|
| **This problem** (sum of odd-length subarrays) | element × (# odd-length subarrays containing it) | sum over elements |
| Sum of subarray ranges (LC #2104) | element × (count of subarrays where it's the MAX or MIN) | requires monotonic stack |
| Total Hamming Distance | bit × (pairs differing at that bit) | sum over bits |
| Sum of Subarray Minimums (LC #907) | element × (count of subarrays where it's the min) | monotonic stack |
| Count of triplets with constraints (various) | element × (combinatorial count of triplets containing it) | depends on constraint |
| Subarray Product Less Than K (LC #713) | sliding window + per-position contribution | sum during window slide |

The general recipe:

1. **Restate** the problem as a sum over groups.
2. **Swap** the order of summation: sum over elements × (count of groups containing them).
3. **Find a closed form** for the count (combinatorial, or via monotonic stack, or via a small pattern).
4. **Linear-time** loop computes the answer in O(n) per element.

---

> **Self-check — the question to ask next time.**
>
> When a problem asks for **"sum over all subarrays / pairs / groups of some property,"** before nesting loops, ask:
>
> > **"Can I swap the order of summation — iterate over ELEMENTS, and for each element compute how many groups it appears in?"**
>
> If yes, you've reduced O(n²) (or O(n³)) to O(n) (assuming the count is O(1) per element, possibly with help from precomputed structures).

---

## Cross-references

- **Reference card (post-mastery):** [`../Sum_of_All_Submatrices_Odd_Length_Subarrays.md`](../Sum_of_All_Submatrices_Odd_Length_Subarrays.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) (prefix sums — the underlying O(n²) speed-up before we got to O(n))
  - [`Total_Hamming_Distance.md`](../../Arrays_and_Matrices/learn/Total_Hamming_Distance.md) (the canonical "swap-order-of-summation" example in this repo)
  - Coming later: Sum of Subarray Minimums (Stack topic) — same shape, different count, uses monotonic stack.
