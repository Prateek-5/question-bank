# Running Sum of 1D Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Running_Sum_of_1D_Array.md`](../Running_Sum_of_1D_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/running-sum-of-1d-array/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. The problem itself is one line of code — but it introduces **prefix sums**, the single most important array preprocessing technique. Every "subarray sum" problem you'll meet later (Subarray Sum Equals K, Range Sum Query, contribution counting) builds on this. Take the time to internalize the recurrence and what it represents.

**Map of this file (9 short sections):**

1. Read the problem
2. The natural first attempt
3. Spotting the wasted work
4. The pivot — each answer builds on the previous
5. The recurrence (and what "prefix sum" means)
6. Code (new-array + in-place)
7. Trace it
8. Common pitfalls
9. The shape — where prefix sums appear later

---

## 1. Read the problem

You're given an integer array `nums`. Return a new array `result` where `result[i]` is the sum of all elements of `nums` from index `0` through index `i` (inclusive).

Formally: `result[i] = nums[0] + nums[1] + ... + nums[i]`.

Example: `nums = [1, 2, 3, 4]`.

```
result[0] = 1                       = 1
result[1] = 1 + 2                   = 3
result[2] = 1 + 2 + 3               = 6
result[3] = 1 + 2 + 3 + 4           = 10
```

Return `[1, 3, 6, 10]`.

Another example: `nums = [3, 1, 2, 10, 1]`.

```
result[0] = 3                       = 3
result[1] = 3 + 1                   = 4
result[2] = 3 + 1 + 2               = 6
result[3] = 3 + 1 + 2 + 10          = 16
result[4] = 3 + 1 + 2 + 10 + 1      = 17
```

Return `[3, 4, 6, 16, 17]`.

> **What this is also called:** *running total*, *cumulative sum*, *prefix sum*. The last name is the one most algorithms textbooks use, and it's what you'll see in later problems built on this.

---

## 2. The natural first attempt

The most literal translation of the problem statement:

```cpp
vector<int> runningSum(vector<int>& nums) {
    int n = nums.size();
    vector<int> result(n);
    for (int i = 0; i < n; i++) {
        int sum = 0;
        for (int j = 0; j <= i; j++) {        // sum nums[0..i] from scratch
            sum += nums[j];
        }
        result[i] = sum;
    }
    return result;
}
```

Two nested loops. For each output position `i`, we re-sum elements `nums[0..i]` from scratch.

For `nums = [1, 2, 3, 4]`:

```
i = 0:  sum = 0; add nums[0]=1.                                    result[0] = 1.
i = 1:  sum = 0; add nums[0]=1, nums[1]=2.                         result[1] = 3.
i = 2:  sum = 0; add nums[0]=1, nums[1]=2, nums[2]=3.              result[2] = 6.
i = 3:  sum = 0; add nums[0]=1, nums[1]=2, nums[2]=3, nums[3]=4.   result[3] = 10.
```

Correct, but look at the inner work. `nums[0]` got added 4 times. `nums[1]` got added 3 times. Lots of repeated arithmetic.

---

## 3. Spotting the wasted work

The number of additions in the brute force:

```
position 0:  1 addition
position 1:  2 additions
position 2:  3 additions
position 3:  4 additions
...
position i:  i + 1 additions
```

Total additions: `1 + 2 + 3 + ... + n = n(n+1)/2` — that's **O(n²)** time.

For `n = 10⁴`, that's `~5 × 10⁷` additions. Probably still fast enough for the judge, but wasteful. For `n = 10⁵`, that's `5 × 10⁹` — too slow.

**Question for us:** can we compute `result[i]` from `result[i-1]` using just ONE more addition, instead of re-summing from scratch?

---

## 4. The pivot — each answer builds on the previous

Look at consecutive entries of `result`:

```
result[0] = nums[0]
result[1] = nums[0] + nums[1]
result[2] = nums[0] + nums[1] + nums[2]
result[3] = nums[0] + nums[1] + nums[2] + nums[3]
```

The difference between consecutive results:

```
result[1] − result[0] = nums[1]
result[2] − result[1] = nums[2]
result[3] − result[2] = nums[3]
```

Or rearranged:

```
result[1] = result[0] + nums[1]
result[2] = result[1] + nums[2]
result[3] = result[2] + nums[3]
```

That's the pivot question answered:

> **"Each `result[i]` is just the previous `result[i-1]` plus `nums[i]`."**

So we compute each position with **one** addition (not `i + 1`). Total work for the whole array: `n` additions = **O(n)**. We just turned O(n²) into O(n) by NOT throwing away the previous answer.

This pattern — "use the previous result to compute the current one in O(1)" — is so central it has a name.

---

## 5. The recurrence (and what "prefix sum" means)

> **Mini-refresher: what is a recurrence?**
>
> A **recurrence** is a rule for defining each entry of an array (or function) in terms of earlier entries. The most famous example is `f(n) = f(n-1) + f(n-2)` (Fibonacci).
>
> Recurrences turn "compute this thing from scratch" into "compute this thing using the answer one step back." That's the engine of dynamic programming.

Our recurrence:

```
result[0] = nums[0]
result[i] = result[i-1] + nums[i]     for i ≥ 1
```

Two lines. The first sets a **base case**. The second defines every other entry in terms of the previous one. A single pass left-to-right fills the whole array.

> **Mini-refresher: what "prefix sum" means.**
>
> A **prefix** of an array is "the first few elements." `[1, 2, 3]` is a prefix of `[1, 2, 3, 4, 5, 6]`. A **prefix sum** is the sum of one such prefix.
>
> So `result[i]` is the prefix sum **up to and including index `i`**. The output of our problem is the list of all prefix sums, position by position.
>
> Why is this so useful? Because of one beautiful identity:
>
> ```
> sum of nums[l..r]  =  prefix[r]  −  prefix[l-1]
> ```
>
> If you have all prefix sums precomputed, **any subarray sum becomes one subtraction — O(1)**. We won't use that here, but it's why prefix sums are foundational — you'll meet that identity in Range Sum Query, Subarray Sum Equals K, Maximum Size Subarray Sum Equals K, and many more.

---

## 6. Code (new-array + in-place)

**Version 1 — write into a new `result` array:**

```cpp
vector<int> runningSum(vector<int>& nums) {
    int n = nums.size();
    vector<int> result(n);
    result[0] = nums[0];
    for (int i = 1; i < n; i++) {
        result[i] = result[i-1] + nums[i];
    }
    return result;
}
```

Three lines of logic. Read it: base case at `result[0]`; recurrence in the loop.

**Version 2 — in-place mutation of `nums`:**

```cpp
vector<int> runningSum(vector<int>& nums) {
    for (int i = 1; i < (int)nums.size(); i++) {
        nums[i] += nums[i-1];
    }
    return nums;
}
```

Two lines of logic. Why does this work?

- After `nums[1] += nums[0]`, `nums[1]` holds the original `nums[0] + nums[1]`. That's `result[1]`.
- Now `nums[1]` IS `result[1]`. So `nums[2] += nums[1]` computes `result[1] + nums[2] = result[2]`. ✓
- And so on. Each iteration uses the previously-overwritten value (which is now the previous prefix sum).

The key insight: **after the i-th iteration, `nums[0..i]` holds the prefix sums, and `nums[i+1..n-1]` is untouched (still the original values).** Because we only ever read `nums[i-1]` (already overwritten) and `nums[i]` (not yet overwritten), there's no conflict.

In-place is O(1) extra space; new-array is O(n) extra. For LeetCode tests both pass.

**STL one-liner (C++):**

```cpp
partial_sum(nums.begin(), nums.end(), nums.begin());
```

`std::partial_sum` is literally the prefix-sum operation built into the standard library. Worth knowing exists, but the by-hand version is more instructive.

---

## 7. Trace it

`nums = [3, 1, 2, 10, 1]`. Using the in-place version:

```
Initially: nums = [3, 1, 2, 10, 1]

i = 1:  nums[1] += nums[0]  →  nums[1] = 1 + 3 = 4.        nums = [3, 4, 2, 10, 1]
i = 2:  nums[2] += nums[1]  →  nums[2] = 2 + 4 = 6.        nums = [3, 4, 6, 10, 1]
i = 3:  nums[3] += nums[2]  →  nums[3] = 10 + 6 = 16.      nums = [3, 4, 6, 16, 1]
i = 4:  nums[4] += nums[3]  →  nums[4] = 1 + 16 = 17.      nums = [3, 4, 6, 16, 17]

Return nums = [3, 4, 6, 16, 17].  ✓
```

Notice how `nums[i-1]` at the time of read is always the freshly-updated prefix sum, not the original value. That's exactly what we want.

Compare to the brute force on the same input: brute force does `1 + 2 + 3 + 4 + 5 = 15` additions; the prefix-sum version does `4` additions. For larger `n` the savings become enormous.

---

## 8. Common pitfalls

1. **Trying to "vectorize" without thinking.** Some people see this problem and reach for `numpy.cumsum` or `std::partial_sum` immediately. That's fine for production, but it hides the recurrence. Write the loop at least once to internalize the pattern.

2. **Forgetting the base case in version 1.** If you write `result[0] = result[-1] + nums[0]` thinking the recurrence applies uniformly, you'll get out-of-bounds (or garbage in some languages). The base case `result[0] = nums[0]` is the loop's anchor.

3. **Overwriting too early in the in-place version.** If you wrote `nums[i-1] += nums[i]` (wrong direction!), you'd be reading the wrong value next iteration. The correct form is `nums[i] += nums[i-1]` — write into the **right** position, read from the LEFT.

4. **Integer overflow on large arrays.** If `nums` has many large values, the running sum can exceed `INT_MAX`. The LeetCode constraints here are mild (sum fits in `int`), but in real life prefer `long long` for prefix sums of arbitrary integer arrays.

5. **Modifying the input when not allowed.** Some interviewers explicitly want a fresh array returned — clarify before mutating in place. The problem statement here says "return the running sum," which most permit in-place behavior for; but it's worth asking.

---

## 9. The shape — where prefix sums appear later

The technique is the **most useful array-preprocessing tool in interviews**. Every problem listed below uses some variant of "build a prefix-sum array once, then query":

| Problem | What the prefix sum buys you |
|---|---|
| **This problem** (Running Sum) | the prefix sums ARE the answer |
| Range Sum Query Immutable | `sum(l..r) = prefix[r+1] - prefix[l]` — O(1) range query |
| Range Sum Query 2D Immutable | 2D prefix sum via inclusion-exclusion |
| Subarray Sum Equals K | combine prefix sum with a hashmap of seen prefix counts |
| Maximum Size Subarray Sum Equals K | same idea, find first occurrence of `prefix - k` |
| Continuous Subarray Sum (divisible by K) | track prefix sum mod K |
| Pivot Index / Find the Pivot Integer | left and right prefix sums |
| Product of Array Except Self | "prefix" applied to PRODUCT instead of SUM |
| Difference array → prefix sum (range update + point query) | inverse pattern: build diffs, prefix-sum to materialize |

**Pattern to internalize:**

> "When the problem involves repeated *aggregation queries over ranges* — sum, product, max, XOR, etc. — almost always precompute a prefix structure. Pay O(n) once; pay O(1) per query thereafter."

---

> **Self-check — the question to ask next time.**
>
> When you face a problem that **repeatedly asks for aggregates (sum / product / XOR) over a prefix or a range**, before doing the aggregate from scratch each time, ask:
>
> > **"Can I precompute prefix-aggregates in one linear pass, and then answer each query with arithmetic on two prefix values?"**
>
> If yes, every subsequent query becomes O(1), and the total cost drops from O(n × q) to O(n + q).

---

## Cross-references

- **Reference card (post-mastery):** [`../Running_Sum_of_1D_Array.md`](../Running_Sum_of_1D_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs (coming):** Range_Sum_Query_2D_Immutable (2D prefix sum), Sum_of_All_Submatrices_Odd_Length_Subarrays (contribution counting on prefix sums)
