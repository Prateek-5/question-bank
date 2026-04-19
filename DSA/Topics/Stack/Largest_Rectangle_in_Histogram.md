# Largest Rectangle in Histogram

**Problem Link:**
https://leetcode.com/problems/largest-rectangle-in-histogram/

**Topic:**
Stack

----------------------------------------

## Step 1: Read the Problem

You have an array `heights` representing bar heights of a histogram (each bar has width 1). Find the area of the largest rectangle that fits entirely within the histogram. The rectangle must be **axis-aligned** and formed by a contiguous span of bars, with height equal to the shortest bar in that span.

Example: `heights = [2, 1, 5, 6, 2, 3]`.

The largest rectangle has area **10**, formed by bars at indices 2 and 3 (heights 5 and 6). Rectangle dimensions: height = min(5, 6) = 5, width = 2 → area = 10.

----------------------------------------

## Step 2: The Brute-Force Idea

Every rectangle in the histogram is characterized by:
- A left boundary `l`.
- A right boundary `r`.
- A height = `min(heights[l..r])`.

So we try every `(l, r)` pair and compute its min. That's O(n³) naively, or O(n²) if we extend `r` and track the running min incrementally.

```cpp
int best = 0;
for (int l = 0; l < n; ++l) {
    int min_h = INT_MAX;
    for (int r = l; r < n; ++r) {
        min_h = min(min_h, heights[r]);
        best = max(best, min_h * (r - l + 1));
    }
}
```

O(n²). For `n = 10^5`, too slow. We need better.

----------------------------------------

## Step 3: Change the Lens

Instead of parameterizing rectangles by their left/right boundaries, parameterize them by their **height-determining bar**.

Every rectangle in the histogram has one (or more) bar that's the shortest in its span. Let's say bar `i` is "the shortest bar" in some candidate rectangle. Then:

- The rectangle has height `heights[i]`.
- Its left boundary extends as far left as possible without encountering a strictly shorter bar.
- Its right boundary extends as far right as possible without encountering a strictly shorter bar.

If we define:
- `L[i]` = index of the nearest bar to the left of `i` with height **strictly less** than `heights[i]` (or -1 if none).
- `R[i]` = index of the nearest bar to the right of `i` with height strictly less than `heights[i]` (or `n` if none).

Then the largest rectangle where `i` is the shortest bar has:
- Height = `heights[i]`.
- Width = `R[i] - L[i] - 1`.
- Area = `heights[i] * (R[i] - L[i] - 1)`.

The overall answer is the max over all `i`.

Why does this work? Every rectangle has some bar that's tied for shortest. For that bar, the rectangle's width can't extend past any strictly shorter bar (else that bar would be the shortest). So each rectangle gets counted when we process its shortest bar.

This reduces the problem to: **find `L[i]` and `R[i]` for every `i`**. If we can do that in O(n) total, we're done.

----------------------------------------

## Step 4: Finding Previous / Next Smaller with a Monotonic Stack

"Previous smaller element" and "next smaller element" are textbook monotonic-stack problems. The same trick we used for Daily Temperatures, in the opposite direction.

Let me construct `L[]`. Scan left to right, maintaining a stack of indices whose heights are strictly increasing (from bottom to top).

- When we process `i`, pop the stack while its top's height is **≥** `heights[i]`. The top after popping (if any) is the first index to the left with height strictly less than `heights[i]` — that's `L[i]`.
- Push `i`.

Wait — let me get the comparison right. We want previous *strictly smaller*, so we pop everything that's ≥ `heights[i]`. After popping, the top (if it exists) has height < `heights[i]`, which is exactly `L[i]`.

Symmetric for `R[]`: scan right to left.

----------------------------------------

## Step 5: A Cleaner One-Pass Version

We can avoid two passes with a single pass that resolves `R[]` as we go. Here's the idea:

- Maintain a stack of indices whose heights form a strictly increasing sequence (bottom to top).
- When we see a new height `heights[i]` that's smaller than the stack's top height, the top's rectangle is **done**: its right boundary is `i` (the first strictly smaller element to the right).
- Pop it, compute its rectangle: height = the popped bar, width = `i - new_top - 1` (where `new_top` is the index below the popped one, or -1 if stack is now empty).
- Keep popping while the top is ≥ current.

At the end, add a sentinel bar of height 0 at the right to force all remaining bars out of the stack.

This is the classic single-pass O(n) algorithm.

----------------------------------------

## Step 6: Trace on `[2, 1, 5, 6, 2, 3]` with Sentinel

I'll append a 0 at the end so the final pops happen naturally. Heights: `[2, 1, 5, 6, 2, 3, 0]`.

```
i=0 (h=2): stack empty. push. stack=[0].
i=1 (h=1): top is 0 (h=2) ≥ 1. pop. popped_h=2; new_top is empty → width = i-(-1)-1 = 1. area = 2*1 = 2. best=2.
          stack empty, push 1. stack=[1].
i=2 (h=5): top is 1 (h=1) < 5. push. stack=[1, 2].
i=3 (h=6): top is 2 (h=5) < 6. push. stack=[1, 2, 3].
i=4 (h=2): top is 3 (h=6) ≥ 2. pop. popped_h=6; new_top is 2 → width = 4-2-1 = 1. area = 6*1 = 6. best=6.
          top is 2 (h=5) ≥ 2. pop. popped_h=5; new_top is 1 → width = 4-1-1 = 2. area = 5*2 = 10. best=10.
          top is 1 (h=1) < 2. push. stack=[1, 4].
i=5 (h=3): top is 4 (h=2) < 3. push. stack=[1, 4, 5].
i=6 (h=0): top is 5 (h=3) ≥ 0. pop. popped_h=3; new_top=4 → width = 6-4-1 = 1. area = 3. best=10.
          top is 4 (h=2) ≥ 0. pop. popped_h=2; new_top=1 → width = 6-1-1 = 4. area = 2*4 = 8. best=10.
          top is 1 (h=1) ≥ 0. pop. popped_h=1; new_top empty → width = 6-(-1)-1 = 6. area = 6. best=10.
          stack empty, push 6. stack=[6].
```

Final best = **10**. ✓

Notice the rectangle of area 8 (bars [1,5,6,2] with height 2) — that's the "width=4" rectangle from popping the bar of height 2. And of course the 5×2 = 10 rectangle is the answer.

----------------------------------------

## Step 7: Why This Works

When we pop bar `j` from the stack:
- The stack's new top (or -1 if empty) is the **previous strictly smaller index** for `j`.
- The current `i` is the **next strictly smaller or equal index** for `j` (we pop when top is ≥ current).

Wait — "smaller or equal"? Let me re-check. Yes, we pop when `heights[top] >= heights[i]`. That means `i` might have height equal to `heights[j]`. Does that break correctness?

No. Here's why: if bar `j` and bar `i` have equal heights, and there are no strictly smaller bars between them, then the rectangle spanning both with height `heights[j]` has the same height. We might compute `j`'s rectangle with a narrower width, and `i`'s rectangle with a wider width. We'd miss `j`'s "true" rectangle only if no larger rectangle is later computed — but the wider rectangle containing `i` will have the same height and larger width, so it strictly dominates. So we never miss the best.

Proof of correctness at the right boundary mirrors this argument.

----------------------------------------

## Step 8: Complexity

Time: each index is pushed at most once and popped at most once. **O(n)**.
Space: stack can hold up to n indices. **O(n)**.

From O(n²) brute force to O(n) via the "for each bar, find how far it can extend left and right" reformulation. The monotonic stack is how we compute both boundaries cheaply.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int largestRectangleArea(vector<int>& h) {
    h.push_back(0);                  // sentinel to flush the stack at the end
    stack<int> st;
    int best = 0;
    for (int i = 0; i < (int)h.size(); ++i) {
        while (!st.empty() && h[st.top()] >= h[i]) {
            int top = st.top(); st.pop();
            int left = st.empty() ? -1 : st.top();
            int width = i - left - 1;
            best = max(best, h[top] * width);
        }
        st.push(i);
    }
    h.pop_back();                    // leave input unchanged
    return best;
}
```

----------------------------------------

## Step 10: Follow-up Questions

- **Maximal Rectangle (in a binary matrix):** treat each row as a histogram where heights[j] = consecutive 1s above position j; apply this algorithm per row. O(m·n).
- **Return the rectangle's actual bounds (left, right, height).** Track them when updating `best`.
- **Largest square (rather than rectangle).** Can be done with a simpler DP (O(m·n)) — you don't need this stack trick.
- **What if heights can be very large (10^9)?** Use `long long` for the area; other logic unchanged.
- **Minimum rectangle area containing at least k ones (for 2D).** Builds on this pattern with an extra constraint.
- **2D version — largest sub-rectangle in a histogram of histograms.** This problem extends naturally to higher dimensions via the same "flatten" trick.
