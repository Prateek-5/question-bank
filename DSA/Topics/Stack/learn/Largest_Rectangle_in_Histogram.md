# Largest Rectangle in Histogram — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Largest_Rectangle_in_Histogram.md`](../Largest_Rectangle_in_Histogram.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/largest-rectangle-in-histogram/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/largest-rectangle-in-histogram/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~35 minutes. **This is the masterpiece of the monotonic-stack pattern**, and a frequent senior-bar interview question. The lesson is a chain of TWO key reformulations: (1) parameterize rectangles by their **shortest bar** instead of by left/right boundaries, and (2) use monotonic stack to find **both previous and next smaller** boundaries in O(n). Don't rush — this problem rewards careful walking. **Read [`Next_Greater_Element_I.md`](./Next_Greater_Element_I.md) and [`Daily_Temperatures.md`](./Daily_Temperatures.md) first.**

**Map of this file (13 sections):**

1. Read the problem
2. The brute force
3. Reformulation 1 — parameterize by the SHORTEST bar
4. Why this reformulation captures every rectangle
5. Reduction to "previous and next smaller index"
6. The two-pass approach (cleaner to think about)
7. The single-pass approach (cleaner to code)
8. Why the single-pass approach gets next-smaller for free
9. Code
10. Trace it on the canonical example
11. Why amortized O(n) (one more time)
12. Common pitfalls
13. The shape — histogram is the unlock for many problems

---

## 1. Read the problem

You're given an array `heights` of non-negative integers. Each entry represents a bar in a histogram. Each bar has width **1**. Find the area of the **largest axis-aligned rectangle** that fits entirely WITHIN the histogram.

The rectangle is formed by some **contiguous range** of bars, and its height equals the **shortest bar** in that range.

**Example:** `heights = [2, 1, 5, 6, 2, 3]`.

```
        █
      █ █
      █ █
      █ █     █
      █ █   █ █
  █   █ █ █ █ █
  ─ ─ ─ ─ ─ ─
  2 1 5 6 2 3
```

The largest rectangle is **10**, formed by bars at indices 2 and 3 (heights 5 and 6). Take the shorter of the two (5) as the rectangle's height, multiply by width (2): `5 × 2 = 10`.

Other candidate rectangles:
- Bar at index 3 alone: `6 × 1 = 6`.
- Bars at indices 2-3 with height min(5,6)=5: `5 × 2 = 10`. ✓ winner.
- Bars at indices 0-5 with height min(2,1,5,6,2,3)=1: `1 × 6 = 6`.
- Bars at indices 2-5 with height min(5,6,2,3)=2: `2 × 4 = 8`.
- Bars at indices 4-5 with height min(2,3)=2: `2 × 2 = 4`.

Max: 10. Answer: 10.

---

## 2. The brute force

The naïve formulation: try every `(left, right)` pair as rectangle boundaries.

```
best = 0
for l in 0..n-1:
    min_h = infinity
    for r in l..n-1:
        min_h = min(min_h, heights[r])    # running min
        area = min_h * (r - l + 1)
        best = max(best, area)
return best
```

Time: O(n²). For `n = 10⁵`, that's `10¹⁰` ops — TLE.

We need O(n log n) or better. Can we do O(n)? Yes — with monotonic stacks. But the reformulation is non-obvious.

---

## 3. Reformulation 1 — parameterize by the SHORTEST bar

Instead of "for each (left, right) range, compute its min and area," flip:

> **For each bar `i`, find the LARGEST rectangle where `heights[i]` is the SHORTEST bar.**

That is: pretend each bar is the rectangle's height-determining bar, and find how far left and right we can extend.

**For a bar `i` to be the rectangle's shortest:**
- Extend left as far as possible while all bars are `≥ heights[i]`. Stop at the first bar with height `< heights[i]` (or the start of the array).
- Same to the right.

Define:
- `L[i]` = index of the **nearest bar to the left** of `i` with height **strictly less** than `heights[i]`. If none exists, `L[i] = -1`.
- `R[i]` = index of the **nearest bar to the right** of `i` with height strictly less than `heights[i]`. If none, `R[i] = n`.

Then the largest rectangle where `i` is the shortest bar has:
- **Height** = `heights[i]`.
- **Left edge** at column `L[i] + 1`.
- **Right edge** at column `R[i] - 1`.
- **Width** = `R[i] - L[i] - 1`.
- **Area** = `heights[i] × (R[i] - L[i] - 1)`.

The answer is `max` of these areas over all `i`.

> **Mini-refresher: this reformulation is a classic "parameterize by the limiting factor."**
>
> Many optimization problems become tractable when you parameterize by the bottleneck:
> - Container With Most Water: water level = shorter of the two walls.
> - Trapping Rain Water: water at position i = `min(left_max, right_max) - height[i]`.
> - This problem: rectangle height = shortest bar in the range.
>
> The pattern: "for each candidate bottleneck, find the largest configuration where it IS the bottleneck."

---

## 4. Why this reformulation captures every rectangle

You might wonder: does considering each bar as "the shortest" actually cover every rectangle?

**Yes.** Take any rectangle in the histogram. It has some bar that is THE shortest (or tied for shortest) within its span. Call that bar's index `j`. By definition, no strictly shorter bar lies within the rectangle's range. So the rectangle's range is some subset of `(L[j], R[j])` (the interval of bars all ≥ heights[j], bounded by strictly-smaller bars or the array edges).

Within `(L[j], R[j])`, the WIDEST rectangle with height `heights[j]` is the full interval. That gives area `heights[j] × (R[j] - L[j] - 1)`, which is ≥ the area of the original rectangle.

So the largest rectangle in the histogram is captured by SOME bar's "shortest-bar parameterization." Trying all bars finds it.

(If multiple bars tie for shortest, we still find the answer because we try EACH one as the shortest.)

---

## 5. Reduction to "previous and next smaller index"

We've reduced the problem to: **for every `i`, compute `L[i]` and `R[i]`** — the previous-smaller and next-smaller indices.

Both are classic monotonic-stack problems:

- **`L[i]` (previous smaller):** scan left-to-right with a monotonic increasing stack. When you encounter `i`, pop everything `≥ heights[i]` from the top. The new top (or -1) is `L[i]`. Push `i`.
- **`R[i]` (next smaller):** scan right-to-left, mirror image.

Each scan is O(n). Total preprocessing: O(n). Then computing all areas: O(n). Grand total: **O(n)**.

> **Mini-refresher: previous-smaller via monotonic increasing stack.**
>
> A monotonic INCREASING stack (bottom-to-top, values increase) is the right structure for "previous smaller."
>
> When new value `v` arrives:
> - Pop everything on top with value `≥ v` (they cannot be a "previous smaller" for `v` since they're not smaller).
> - After popping, the top (if any) has value `< v` — that's `L[i]`.
> - Push `v`'s index.
>
> For "previous strictly smaller," pop while `top ≥ v`. For "previous less-or-equal," pop while `top > v`. Match comparison to whether you want strictness.
>
> Same shape as Daily Temperatures, with comparison direction flipped.

---

## 6. The two-pass approach (cleaner to think about)

```
# Pass 1: compute L[i] for all i.
L = [0] * n
stack = []
for i in 0..n-1:
    while stack and heights[stack.top()] >= heights[i]:
        stack.pop()
    L[i] = stack.top() if stack else -1
    stack.push(i)

# Pass 2: compute R[i] for all i.
R = [0] * n
stack = []
for i in n-1 down to 0:
    while stack and heights[stack.top()] >= heights[i]:
        stack.pop()
    R[i] = stack.top() if stack else n
    stack.push(i)

# Pass 3: compute max area.
best = 0
for i in 0..n-1:
    best = max(best, heights[i] * (R[i] - L[i] - 1))
return best
```

Three passes, each O(n). Total O(n). Easy to reason about.

But you can do it in **ONE pass**, computing the answer as we go. That's more elegant and what most implementations show.

---

## 7. The single-pass approach (cleaner to code)

The key insight: when we pop bar `j` from a monotonic increasing stack (because a smaller bar `i` arrived), `i` is the **next smaller** for `j`. And the new top of the stack (after the pop) is `j`'s **previous smaller**.

So at the moment of POP, we have BOTH boundaries for `j`. Compute its area immediately.

```
stack = []                    # monotonic INCREASING stack of INDICES
best = 0

for i in 0..n:                 # NOTE: loop goes to n, NOT n-1
    h = heights[i] if i < n else 0    # treat virtual bar past end as height 0
    while stack and heights[stack.top()] >= h:
        j = stack.pop()
        left = stack.top() if stack else -1
        width = i - left - 1
        best = max(best, heights[j] * width)
    stack.push(i)

return best
```

Two tricks:
1. **Virtual sentinel bar of height 0 at position n.** This forces every remaining bar in the stack to get popped (height 0 is strictly less than any positive height). Cleans up the "leftover" stack at the end.
2. **At each pop, the new top is `L[j]`, and `i` is `R[j]`** — both boundaries known at the moment of pop.

---

## 8. Why the single-pass approach gets next-smaller for free

This is the heart of the algorithm. Why does popping `j` give us `R[j]`?

**When does `j` get popped?** When some incoming `i` has `heights[i] < heights[j]` (specifically, `heights[i] ≤ heights[j]` due to our `>=` pop rule, but more on the equality case in a moment). That `i` is the FIRST index AFTER `j` with such a property, because:

- All indices between `j` and `i` were ALSO pushed after `j` and popped before `i` (so they had heights `≥ heights[i]`, and hence `≥ heights[j]`).
- Wait, that's not quite right. Let me reframe.

A cleaner argument: consider the stack right BEFORE `i` arrives. It contains some indices in increasing order of height. `j` is on top (or near top), meaning `j` was pushed after every index BELOW it in the stack.

If `j` is on top right before `i` arrives and `i` causes the pop, then:
- All indices between `j` and `i` (in array order) that were ever on the stack got popped by indices BEFORE `i`. So they all had heights ≥ those that came after them in the stack, including ≥ `heights[i]`. So they had heights ≥ `heights[i]`. So they're NOT smaller than `j`'s "next smaller" — they couldn't have served that role for `j`.
- Therefore the FIRST smaller-than-`heights[j]` after `j` is `i` itself. So `R[j] = i`. ✓

Similarly, when `j` was on top, the index just below `j` in the stack was the most recent index with height < `heights[j]` (otherwise `j` would have popped it). So that's `L[j]`. ✓

> **Mini-refresher: ties.**
>
> When `heights[i] == heights[j]`, our pop rule (`>=`) pops `j`. Is that correct? Let's check.
>
> If we pop `j` even though `i` isn't STRICTLY smaller, we compute `j`'s area as `heights[j] × (i - L[j] - 1)`. The "real" next-strictly-smaller for `j` is somewhere ≥ `i`. So we're using a SMALLER width than the true maximum for `j`. We undercount `j`'s area.
>
> BUT — `i` has the same height as `j`. So when `i` eventually gets popped, we compute `i`'s area with a width that INCLUDES the territory `j` would have covered. Since `heights[i] = heights[j]`, this catches the bigger rectangle.
>
> So `>=` (pop on equal) is correct: we might undercount individual ties, but the eventual area for the rightmost tied bar covers the full territory. The MAX over all bars is correct.

---

## 9. Code

**C++ — single-pass with sentinel:**

```cpp
int largestRectangleArea(vector<int>& heights) {
    int n = heights.size();
    stack<int> st;                          // indices; heights at these indices are non-decreasing bottom-to-top
    int best = 0;

    for (int i = 0; i <= n; ++i) {
        int h = (i == n) ? 0 : heights[i];  // virtual sentinel of height 0 at position n
        while (!st.empty() && heights[st.top()] >= h) {
            int j = st.top(); st.pop();
            int left = st.empty() ? -1 : st.top();
            int width = i - left - 1;
            best = max(best, heights[j] * width);
        }
        st.push(i);
    }

    return best;
}
```

About 12 lines of real logic.

**Python:**

```python
def largestRectangleArea(heights):
    n = len(heights)
    stack = []
    best = 0
    for i in range(n + 1):
        h = 0 if i == n else heights[i]
        while stack and heights[stack[-1]] >= h:
            j = stack.pop()
            left = stack[-1] if stack else -1
            width = i - left - 1
            best = max(best, heights[j] * width)
        stack.append(i)
    return best
```

**JavaScript:**

```javascript
function largestRectangleArea(heights) {
    const n = heights.length;
    const stack = [];
    let best = 0;
    for (let i = 0; i <= n; i++) {
        const h = (i === n) ? 0 : heights[i];
        while (stack.length && heights[stack[stack.length - 1]] >= h) {
            const j = stack.pop();
            const left = stack.length ? stack[stack.length - 1] : -1;
            const width = i - left - 1;
            best = Math.max(best, heights[j] * width);
        }
        stack.push(i);
    }
    return best;
}
```

Complexity: **O(n) time, O(n) space.**

---

## 10. Trace it on the canonical example

`heights = [2, 1, 5, 6, 2, 3]`. With sentinel, we loop `i = 0..6`, treating `i = 6` as `h = 0`.

```
stack = [] (will store indices; heights[stack] strictly increasing top is rightmost-pushed).
best = 0.

i=0, h=2:  stack empty. push 0. stack=[0].

i=1, h=1:  top is 0 (h=2). 2 >= 1 → pop 0.
             j=0, left=(stack empty)→-1, width=1-(-1)-1=1, area=2*1=2. best=2.
           stack empty. push 1. stack=[1].

i=2, h=5:  top is 1 (h=1). 1 < 5 → no pop. push 2. stack=[1, 2].

i=3, h=6:  top is 2 (h=5). 5 < 6 → no pop. push 3. stack=[1, 2, 3].

i=4, h=2:  top is 3 (h=6). 6 >= 2 → pop 3.
             j=3, left=2 (stack[-1] after pop), width=4-2-1=1, area=6*1=6. best=6.
           top is 2 (h=5). 5 >= 2 → pop 2.
             j=2, left=1, width=4-1-1=2, area=5*2=10. best=10.   ← THE WINNER
           top is 1 (h=1). 1 < 2 → no pop. push 4. stack=[1, 4].

i=5, h=3:  top is 4 (h=2). 2 < 3 → no pop. push 5. stack=[1, 4, 5].

i=6, h=0:  (sentinel)
           top is 5 (h=3). 3 >= 0 → pop 5.
             j=5, left=4, width=6-4-1=1, area=3*1=3. best=10.
           top is 4 (h=2). 2 >= 0 → pop 4.
             j=4, left=1, width=6-1-1=4, area=2*4=8. best=10.
           top is 1 (h=1). 1 >= 0 → pop 1.
             j=1, left=(stack empty)→-1, width=6-(-1)-1=6, area=1*6=6. best=10.
           stack empty. push 6. stack=[6].

Return best = 10.  ✓
```

Watch how the **5×2 = 10 rectangle** got found at `i=4`: when bar 2 popped from a state where bar 1 was its predecessor, width became `4 - 1 - 1 = 2`, and the height (5) gave the answer.

Also notice the **8 area rectangle** at the end — bars [1, 5, 6, 2] all ≥ height 2, so a rectangle of height 2 × width 4 = 8 was correctly identified.

---

## 11. Why amortized O(n) (one more time)

Same argument as before:
- Each index is pushed **exactly once** (in the outer loop).
- Each index is popped **at most once** (in the inner loop or at the sentinel).
- Total pop work across the entire run is ≤ n.
- Plus n pushes.

Total = O(n) regardless of how nested the loops LOOK.

> **Mini-refresher: monotonic stack = amortized O(n).**
>
> Burn this into your brain. Every monotonic-stack problem you encounter has this property. The "scary nested loop" is amortized linear, never quadratic.

---

## 12. Common pitfalls

1. **Storing values instead of indices on the stack.** Won't work — we need indices for the width formula. ALWAYS store indices in this problem.

2. **Forgetting the sentinel bar of height 0.** Without it, bars left on the stack at the end never get popped, and their rectangles never get computed. Either use the sentinel OR add a cleanup loop after the main loop.

3. **Computing width as `i - j` instead of `i - left - 1`.** Wrong. The rectangle excludes the boundary bars (the smaller bars at `L[j]` and `R[j] = i`). So width is the count of bars STRICTLY BETWEEN them, which is `i - left - 1`.

4. **Using `<` instead of `>=` in the pop condition.** Need to revisit the "ties" analysis (Section 8). Use `>=` to pop on equal — the ties are handled correctly because the largest tied bar's area covers the territory of earlier ties.

5. **Initializing `left` to `0` when stack is empty.** Should be `-1` to indicate "no previous smaller — extends all the way to the left." Width formula `i - (-1) - 1 = i` correctly gives "all bars from 0 to i-1."

6. **Trying to handle the "stack empty at end" case ad-hoc.** Use the sentinel — much cleaner than ad-hoc.

7. **Solving with O(n log n) divide-and-conquer.** Works, but monotonic stack is O(n) and simpler in code. Use the stack approach.

8. **Modifying the input array** (e.g., appending the sentinel to `heights`). If the input is read-only or the caller cares, restore it (or use a separate index `n` that triggers the sentinel without modifying the array).

9. **Confusing this with "Maximal Square" / "Maximal Rectangle" (2D).** Related but different. Maximal Square uses DP. Maximal Rectangle (in a binary 2D matrix) reduces to THIS problem per row.

10. **Off-by-one in the width.** Test on a single bar of height 5: should return 5. If you get 0, your width formula's wrong.

11. **Trying to pop both same-height-bars at once.** Don't. Process one at a time; correctness comes from the rightmost equal-height bar capturing the full width.

12. **Reading the problem as "find the largest sub-rectangle of the bounding box."** No — bars are vertical lines of fixed widths. We're finding a rectangle in the SHAPE made by the bars, not in the bounding box.

---

## 13. The shape — histogram is the unlock for many problems

This problem isn't just an interview puzzle — it's a foundational building block.

**Where this exact algorithm reappears:**

| Problem | How |
|---|---|
| **This problem** | direct |
| **Maximal Rectangle (LC #85)** in a 0/1 matrix | per row, build a "heights" array (consecutive 1s above row r) → run Largest Rectangle in Histogram per row → O(m·n) total |
| Maximum Sum of Submatrix | similar projection idea |
| Trapping Rain Water (one O(n) approach) | uses indices of "wall" bars, similar monotonic-stack reasoning |
| Sum of Subarray Minimums | similar L[i], R[i] preprocessing |

**Pattern to internalize:**

> "Whenever you face a problem about RECTANGLES, BUCKETS, or SLABS where the limiting dimension is a SINGLE VALUE (height, depth, wealth, ...), parameterize by 'for each element, what's the largest configuration where this element is the bottleneck?' Then use monotonic stacks to find both-sided boundaries in O(n)."

The reformulation "for each candidate bottleneck, find its extent" + monotonic stack for boundaries = decisive O(n) algorithms for problems that look O(n²).

---

> **Self-check — the question to ask next time.**
>
> When you face a "largest rectangle/region in histogram-like data" problem, before reaching for divide-and-conquer or O(n²), ask:
>
> > **"For each bar/element, can I find the previous-smaller and next-smaller index using monotonic stacks? Then the largest rectangle with that bar as height is `height × (R - L - 1)`. Max over all bars."**
>
> If yes, you've turned a brute-force quadratic into amortized O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Largest_Rectangle_in_Histogram.md`](../Largest_Rectangle_in_Histogram.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Next_Greater_Element_I.md`](./Next_Greater_Element_I.md), [`Daily_Temperatures.md`](./Daily_Temperatures.md) — monotonic stack basics.
  - Coming later: Maximal_Rectangle (in Dynamic_Programming_DP) — applies THIS algorithm per row of a binary matrix.
  - Cross-link to Trapping_Rain_Water — same monotonic-stack toolbox, different shape.
