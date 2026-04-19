# Find Median from Data Stream

**Problem Link:**
https://leetcode.com/problems/find-median-from-data-stream/

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: The Problem

Numbers arrive one at a time. After each arrival, we want to know the median of everything we've seen so far.

Median refresher:
- If we've seen an odd count, median is the middle value.
- If we've seen an even count, median is the average of the two middle values.

We need to support two operations:
- `addNum(x)` — add a new number.
- `findMedian()` — return the median so far.

Both should be efficient, ideally faster than O(n) per call, because they might be invoked many times.

----------------------------------------

## Step 2: What Would a Naïve Approach Look Like?

Keep all the numbers in a list. When asked for the median, sort the list and pick the middle.

```cpp
vector<int> data;
void addNum(int x) { data.push_back(x); }
double findMedian() {
    sort(data.begin(), data.end());
    int n = data.size();
    return n % 2 ? data[n/2] : (data[n/2 - 1] + data[n/2]) / 2.0;
}
```

`addNum` is O(1), but `findMedian` is O(n log n). If the stream has millions of numbers and we ask for the median after every add, total cost is O(n² log n). Unusable.

A mild improvement: keep the list *sorted* by inserting each new number in the right place. Binary search finds the insertion point in O(log n), but the insertion itself shifts up to n elements, so `addNum` becomes O(n). Median query is then O(1). Still O(n²) total if we add n numbers.

We want *both* operations in O(log n). What structure lets me do that?

----------------------------------------

## Step 3: The Key Observation

I actually don't care about the exact sorted order of every number. I only care about the *middle*. Specifically:

- The "lower half" of the data.
- The "upper half" of the data.
- The two boundary values between them.

If I maintain those two halves separately, and I can always access the largest in the lower half and the smallest in the upper half, I can compute the median in O(1).

Now, which structure lets me quickly get the largest of a set? A **max-heap**. Largest of a set of low values is at its root.

Which structure lets me quickly get the smallest of a set? A **min-heap**. Smallest of a set of high values is at its root.

So the idea: use two heaps.
- `lo` = max-heap holding the smaller half of the numbers. Its top is the largest of the lower half.
- `hi` = min-heap holding the larger half. Its top is the smallest of the upper half.

Visual after seeing `1, 3, 5, 2, 4`:

```
lo (max-heap):  [3, 1, 2]   top = 3
hi (min-heap):  [4, 5]      top = 4
```

When the combined size is odd, by convention we keep `lo` one larger than `hi`. Median is `lo.top()`.
When even, both have the same size. Median is `(lo.top() + hi.top()) / 2`.

----------------------------------------

## Step 4: Keeping the Halves Balanced

Every `addNum(x)` must place `x` in the right half *and* keep the sizes balanced. Here's a clean way:

1. Push `x` into `lo` unconditionally.
2. Then pop `lo`'s top and push it into `hi`. (This ensures the ordering invariant — whatever is largest in `lo` gets pushed up to `hi`.)
3. If `hi` is now larger than `lo`, pop `hi`'s top and push it back to `lo`. (Keeps size invariant: `lo.size() ≥ hi.size()`.)

Why the two-step dance? Because `x` may not belong in `lo` — it could actually belong in `hi`. Pushing then popping-transferring guarantees correct placement regardless. It's a small redundancy for a big simplification in code.

----------------------------------------

## Step 5: Trace a Real Stream

Stream: `[41, 35, 62, 5, 97, 108, 0]`. I'll track both heaps and the median after each add.

```
add 41:
  lo.push(41) → lo=[41]
  move lo.top to hi: hi=[41], lo=[]
  hi bigger → move back: lo=[41], hi=[]
  median = 41.

add 35:
  lo.push(35) → lo=[41,35]
  move lo.top (41) to hi: lo=[35], hi=[41]
  hi not bigger. Sizes: lo=1, hi=1.
  median = (35 + 41) / 2 = 38.

add 62:
  lo.push(62) → lo=[62,35]
  move lo.top (62) to hi: lo=[35], hi=[41,62]
  hi bigger (2>1) → move back: pop 41 from hi, push to lo: lo=[41,35], hi=[62]
  median = 41.

add 5:
  lo.push(5) → lo=[41,35,5]
  move lo.top (41) to hi: lo=[35,5], hi=[41,62]
  hi not bigger. Sizes: 2,2.
  median = (35 + 41) / 2 = 38.

add 97:
  lo.push(97) → lo=[97,35,5]
  move lo.top (97) to hi: lo=[35,5], hi=[41,62,97]
  hi bigger → move back: pop 41, push to lo: lo=[41,35,5], hi=[62,97]
  median = 41.

add 108:
  lo.push(108) → lo=[108,41,5,35]
  move lo.top (108) to hi: lo=[41,35,5], hi=[62,97,108]
  hi not bigger. Sizes 3,3.
  median = (41 + 62) / 2 = 51.5.

add 0:
  lo.push(0) → lo=[41,35,5,0]  (depending on heap shape)
  move lo.top (41) to hi: lo=[35,0,5], hi=[41,62,97,108]
  hi bigger (4>3) → pop 41, push to lo: lo=[41,35,0,5], hi=[62,97,108]
  median = 41.
```

Let me sanity-check by sorting what we've seen: `[0, 5, 35, 41, 62, 97, 108]`. Median of 7 sorted values is the 4th, which is `41`. ✓

The invariants held the whole way: `lo.size()` is either equal to or exactly one larger than `hi.size()`, and every value in `lo` is ≤ every value in `hi` (because we always "push up" the max of `lo` to `hi` before rebalancing).

----------------------------------------

## Step 6: Why This Works — Formal Invariants

**Invariant 1 (ordering):** After every operation, `lo.top() ≤ hi.top()`.

Why? Each `addNum(x)` does:
1. Push x into lo.
2. Move lo.top to hi.

After step 2, the value we just moved to hi is ≥ every remaining value in lo (since we moved lo's maximum). So `max(lo) ≤ hi.top()` (because hi.top() is the smallest in hi, and we just added something there that was ≥ everything in lo). The pop-back-from-hi step only pulls hi's min down, which is still ≥ lo's max. Invariant preserved.

**Invariant 2 (size):** `lo.size() == hi.size()` or `lo.size() == hi.size() + 1`.

Why? Every add increases the combined size by 1. Our rebalance step forces `lo.size() ≥ hi.size()`, and the transfer phase never lets `lo.size()` exceed `hi.size()` by more than 1.

Median formula follows: if sizes are equal (even total), median is `(lo.top() + hi.top()) / 2`. If `lo` is one larger (odd total), median is `lo.top()`.

----------------------------------------

## Step 7: Complexity

`addNum`: we do a constant number of heap pushes and pops, each O(log n). **O(log n) per add.**

`findMedian`: just reading one or two heap tops. **O(1).**

Space: everything we've added, stored across the two heaps. **O(n).**

Before this technique, we were at O(n) per `addNum` or O(n log n) per `findMedian`. Now both are fast. That's the payoff of the two-heap structure.

----------------------------------------

## Step 8: C++ Implementation

```cpp
class MedianFinder {
    priority_queue<int> lo;                                        // max-heap
    priority_queue<int, vector<int>, greater<int>> hi;             // min-heap
public:
    void addNum(int x) {
        lo.push(x);
        hi.push(lo.top()); lo.pop();          // move max of lo into hi
        if (hi.size() > lo.size()) {          // keep lo ≥ hi in size
            lo.push(hi.top()); hi.pop();
        }
    }
    double findMedian() {
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + hi.top()) / 2.0;
    }
};
```

Nine effective lines. The two-heap structure does all the work.

----------------------------------------

## Step 9: Follow-up Questions

- **All numbers are between 0 and 100.** Use a bucket array `cnt[0..100]` plus a running total. Median lookup scans the buckets. O(1) space per add, O(range) per query — fast because the range is constant.
- **99% of numbers in [0,100], 1% outside.** Hybrid: bucket for common range, heap for outliers.
- **Remove a number too (support `removeNum`).** A plain heap doesn't support arbitrary deletion. Use two multisets instead of two heaps, or use lazy deletion with a stale-entry cache.
- **Sliding median (median of the last k numbers).** A pair of `multiset`s with balance maintenance, or two heaps with lazy deletion keyed on insertion index.
- **Weighted median.** Each element has a weight; median splits the total weight in half. Use an order-statistic tree or segment tree.
