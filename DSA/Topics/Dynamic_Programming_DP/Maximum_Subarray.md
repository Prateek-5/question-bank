# Maximum Subarray

**Problem Link:**
https://leetcode.com/problems/maximum-subarray/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Understand the Problem

Given an integer array (which can contain negatives), find a **contiguous** subarray whose sum is as large as possible. Return that maximum sum.

"Contiguous" is the word to pay attention to. We aren't picking any subset — we're picking a single continuous window `a[i..j]` and summing it.

Example: `[-2, 1, -3, 4, -1, 2, 1, -5, 4]`. The best contiguous window is `[4, -1, 2, 1]`, whose sum is `6`.

----------------------------------------

## Step 2: The Brute-Force Instinct

If I had to solve this without any cleverness, I'd just try every possible subarray. Two loops: one for the start `i`, one for the end `j ≥ i`. Sum them up, track the max.

```cpp
int best = INT_MIN;
for (int i = 0; i < n; ++i)
    for (int j = i; j < n; ++j) {
        int s = 0;
        for (int k = i; k <= j; ++k) s += a[k];
        best = max(best, s);
    }
```

That's O(n³), which dies quickly. We can make it O(n²) by computing the running sum as we extend `j`:

```cpp
for (int i = 0; i < n; ++i) {
    int s = 0;
    for (int j = i; j < n; ++j) {
        s += a[j];
        best = max(best, s);
    }
}
```

Better, but still slow for `n = 10^5`. There must be an O(n) approach. What are we re-doing?

----------------------------------------

## Step 3: The Critical Question

Instead of asking "what's the best subarray overall?" let's ask a more local question:

> **What's the best subarray that ends exactly at index `i`?**

This feels weird at first — we're fixing one endpoint and only asking about the other. But it turns out to be the key. Once we know the answer for every `i`, the overall answer is just the max over all of them.

Let `best_ending(i)` = maximum sum of a subarray ending at index `i`.

Now here's the magical part. The subarray ending at `i` has exactly two possibilities:

1. It's just `a[i]` by itself (length 1).
2. It's the best subarray ending at `i-1`, extended by `a[i]`.

That's it. No third option. Every contiguous subarray that ends at `i` either starts at `i`, or it extends from a subarray that ended at `i-1`.

So:

```
best_ending(i) = max(a[i], best_ending(i-1) + a[i])
```

Which we can rewrite as:

```
best_ending(i) = a[i] + max(0, best_ending(i-1))
```

Read the second form slowly. It says: "Start fresh at `a[i]`, *unless* the previous running sum was positive, in which case add it on."

**This is a beautiful observation.** A negative running sum is never worth carrying forward — it only hurts us. So the moment the accumulated sum would go negative, we "reset" and start a new subarray.

----------------------------------------

## Step 4: Let's Verify With a Real Example

Take `[-2, 1, -3, 4, -1, 2, 1, -5, 4]`.

```
i=0, a[i]=-2:  best_ending = max(-2, 0 + -2) = -2.   global best = -2
i=1, a[i]=1:   best_ending = max(1, -2 + 1) = 1.     global best = 1
i=2, a[i]=-3:  best_ending = max(-3, 1 + -3) = -2.   global best = 1
i=3, a[i]=4:   best_ending = max(4, -2 + 4) = 4.     global best = 4   ← reset!
i=4, a[i]=-1:  best_ending = max(-1, 4 + -1) = 3.    global best = 4
i=5, a[i]=2:   best_ending = max(2, 3 + 2) = 5.      global best = 5
i=6, a[i]=1:   best_ending = max(1, 5 + 1) = 6.      global best = 6   ← the real answer
i=7, a[i]=-5:  best_ending = max(-5, 6 + -5) = 1.    global best = 6
i=8, a[i]=4:   best_ending = max(4, 1 + 4) = 5.      global best = 6
```

Final answer: **6**. That matches the known best subarray `[4, -1, 2, 1]`.

Watch what happened at `i = 3`. Our running sum was `-2` (unhelpful), and `a[3] = 4` was much larger than `-2 + 4 = 2`. So we threw away the past and started fresh at index 3. That "throw away the past when it's negative" move is the entire algorithm.

----------------------------------------

## Step 5: Naming What We Discovered

This is **Kadane's algorithm**. But notice how we got here: we didn't memorize its name — we asked a smarter question ("best ending at `i`") and the recurrence dropped out. The name is a label, not an insight.

In the DP vocabulary, our **state** is the index `i`, our **transition** is `best_ending(i) = a[i] + max(0, best_ending(i-1))`, and our **answer** is `max over i of best_ending(i)`. Because we only need `best_ending(i-1)` to compute `best_ending(i)`, we don't even need an array — one rolling variable suffices.

----------------------------------------

## Step 6: The Code

```cpp
int maxSubArray(vector<int>& a) {
    int cur = a[0];
    int best = a[0];
    for (int i = 1; i < (int)a.size(); ++i) {
        cur = max(a[i], cur + a[i]);   // best subarray ending at i
        best = max(best, cur);          // track global max
    }
    return best;
}
```

Three variables. Eleven lines. That's the whole thing.

One thing worth pointing out: we initialize `cur` and `best` to `a[0]`, not to `0` or `INT_MIN`. The reason is that the answer might be a single negative number (if all elements are negative), in which case we still need to return the least-negative one. Starting at `a[0]` handles this naturally.

----------------------------------------

## Step 7: Complexity

Time: a single pass through the array. **O(n)**.

Space: two variables. **O(1)**.

We went from O(n³) brute force to O(n) just by asking a better question. That's a huge lesson: reformulating the subproblem often matters more than inventing a fancy data structure.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int maxSubArray(vector<int>& a) {
    int cur = a[0], best = a[0];
    for (int i = 1; i < (int)a.size(); ++i) {
        cur = max(a[i], cur + a[i]);
        best = max(best, cur);
    }
    return best;
}
```

----------------------------------------

## Step 9: Follow-up Questions

- **Return the actual subarray, not just the sum.** Track the start index. When we "reset" (choose `a[i]` over `cur + a[i]`), update the tentative start. When we update `best`, snapshot the start and end.
- **What if the array is circular (wraps around)?** The answer is either a normal max subarray, or the total sum minus the minimum subarray (the complement). Handle the all-negative edge case separately.
- **Maximum subarray product instead of sum?** Multiplication with negatives flips signs — track both current min and current max at each position.
- **2D version — maximum sum submatrix?** Fix a pair of rows, collapse the rows between them into a 1D array of column sums, run Kadane on that. O(n³).
- **What if we allow deleting at most one element?** Track two running sums: with and without a deletion used so far.
