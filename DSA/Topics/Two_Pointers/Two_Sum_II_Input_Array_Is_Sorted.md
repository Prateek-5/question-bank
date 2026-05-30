# Two Sum II — Input Array Is Sorted

**Problem Link:**
<a href="https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/</a>

**Topic:**
Two Pointers

----------------------------------------

## Step 1: Read the Problem Carefully

Given a **sorted** 1-indexed array `numbers` and a target integer `target`, return the 1-indexed positions of two numbers in `numbers` that add up exactly to `target`.

You're guaranteed exactly one solution, and you may not use the same element twice.

Example: `numbers = [2, 7, 11, 15]`, `target = 9`. We need two numbers summing to 9. `2 + 7 = 9`. Indices 1 and 2. Answer: `[1, 2]`.

The crucial detail — "sorted" — is the whole point of the problem. Without it, it's the regular Two Sum (solved with a hashmap).

----------------------------------------

## Step 2: What Does Sorted Buy Us?

Without sorting, the best I know is O(n) with a hashmap. Can we do better on a sorted array? Or at least O(n) without the hashmap's space overhead?

Let me think about what "sorted" means for pair sums. If I pick the smallest number `numbers[0]` and pair it with the largest `numbers[n-1]`, I get some sum. If that sum is larger than the target, every pair involving `numbers[n-1]` is too big (pairing with smaller first numbers gives even bigger sums... wait no, smaller first numbers give smaller sums). Hmm, let me re-think.

Actually: `numbers[0] + numbers[n-1]` is neither the max nor the min of pair sums. The max pair sum is the two biggest; the min is the two smallest.

But there's something useful here. If `numbers[0] + numbers[n-1] > target`, then `numbers[n-1]` paired with *any* element is ≥ `numbers[0] + numbers[n-1] > target`. So `numbers[n-1]` is too big to be part of the answer. We can eliminate it and look at indices `0..n-2`.

Symmetrically, if the sum is too small, `numbers[0]` is too small and can be eliminated.

This is a **shrinking window** argument. Let me formalize it.

----------------------------------------

## Step 3: The Two-Pointer Insight

Put two pointers, one at each end: `l = 0`, `r = n - 1`.

- If `numbers[l] + numbers[r] == target`: done.
- If `numbers[l] + numbers[r] < target`: we need a bigger sum. The current `l` can never make a bigger sum with any smaller `r`, and all `r'` with `r' > r` don't exist. So `l` cannot be part of the answer — move `l` right.
- If `numbers[l] + numbers[r] > target`: symmetric. `r` cannot be part of the answer — move `r` left.

Each step eliminates one candidate endpoint. After at most `n - 1` steps, the pointers meet and we have an answer (problem guarantees one exists).

This is the **two-pointer sweep** — beautifully simple once you see it.

----------------------------------------

## Step 4: Why It Can't Miss the Answer

Let me make the elimination argument airtight.

**Claim:** When we advance `l`, the answer pair cannot involve the current `numbers[l]`.

*Proof:* Suppose the answer is `(l, k)` for some `k > l`. Then `numbers[l] + numbers[k] = target`. But we decided to advance `l` because `numbers[l] + numbers[r] < target`. Since `k ≤ r`, we have `numbers[k] ≤ numbers[r]` (sorted array). So `numbers[l] + numbers[k] ≤ numbers[l] + numbers[r] < target`. Contradiction.

So moving `l` right doesn't discard the solution. Symmetric argument for moving `r` left.

Since every step preserves the solution *and* shrinks the window, and the problem guarantees a solution exists, the pointers will meet at the answer.

----------------------------------------

## Step 5: Trace on a Concrete Example

`numbers = [2, 3, 4, 7, 11, 15]`, target = 18.

```
l=0, r=5: 2 + 15 = 17 < 18. l++.
l=1, r=5: 3 + 15 = 18 = target! Return [2, 6] (1-indexed).
```

Done in 2 iterations.

Another: `numbers = [1, 2, 3, 4, 4, 9, 56, 90]`, target = 8.

```
l=0, r=7: 1 + 90 = 91 > 8. r--.
l=0, r=6: 1 + 56 > 8. r--.
l=0, r=5: 1 + 9 = 10 > 8. r--.
l=0, r=4: 1 + 4 = 5 < 8. l++.
l=1, r=4: 2 + 4 = 6 < 8. l++.
l=2, r=4: 3 + 4 = 7 < 8. l++.
l=3, r=4: 4 + 4 = 8! Return [4, 5].
```

----------------------------------------

## Step 6: Complexity

Time: each iteration moves one pointer, and they meet after at most n-1 moves. **O(n)**.
Space: two pointers. **O(1)**.

No hashmap, no extra arrays. We trade O(n) extra space (in hashmap-Two-Sum) for exploiting the sorted order.

----------------------------------------

## Step 7: Name It

This is the canonical **two-pointer technique on sorted data**, sometimes called the "opposite-end" or "converging" two-pointer. Any time you see "pair sum/diff/product equals X on a sorted array," your first instinct should be two pointers.

The same pattern solves:
- 3Sum (fix one element, two-pointer the rest).
- Container With Most Water (slightly different — pick two heights to max an area).
- Valid Palindrome check.
- Remove duplicates from sorted array.

----------------------------------------

## Step 8: C++ Implementation

```cpp
vector<int> twoSum(vector<int>& numbers, int target) {
    int l = 0, r = numbers.size() - 1;
    while (l < r) {
        int sum = numbers[l] + numbers[r];
        if (sum == target) return {l + 1, r + 1};   // 1-indexed
        if (sum < target) l++;
        else r--;
    }
    return {};   // shouldn't reach here per problem guarantee
}
```

One gotcha: the problem asks for **1-indexed** positions. I return `l + 1` and `r + 1`. If you miss this, your answer is always off by one.

Another implementation detail: watch for integer overflow in `numbers[l] + numbers[r]` if elements are large. For typical constraints, int is fine; for extreme cases, use `long long`.

----------------------------------------

## Step 9: Follow-up Questions

- **Two Sum (unsorted input).** Use a hashmap — for each element, check if `target - x` has been seen. O(n) time, O(n) space.
- **What if the array has duplicates and we want all unique pairs summing to target?** After finding a match, advance both pointers past equal values.
- **Two Sum with distinct elements and we want the number of such pairs.** After finding a match, just count and continue.
- **Three Sum equals target.** Sort, fix each `i`, two-pointer on the remaining range. O(n²).
- **Two Sum in a sorted matrix.** Row-by-row two-pointer, or use the staircase trick from "Search a 2D Matrix II."
- **Can we solve in O(log n)?** Only if the target is constrained to be a specific function of indices; in general no — we need to examine Ω(n) elements.
