# Sliding Window Maximum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Sliding_Window_Maximum.md`](../Sliding_Window_Maximum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/sliding-window-maximum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/sliding-window-maximum/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~28 minutes. **This is the crown jewel of the Queues topic — the MONOTONIC DEQUE pattern.** The lesson: **maintain a deque of indices where the corresponding values are STRICTLY DECREASING. The front is always the current window's max. Pop the back when a larger value arrives; pop the front when an index falls out of window.** Same template solves Sliding Window Minimum, "First Negative in Each Window," and many DP-with-window optimizations. **Read [`Implement_Queue_using_Stacks.md`](./Implement_Queue_using_Stacks.md) (deque basics) and the monotonic-stack family (Next Greater Element, Daily Temperatures) first.**

**Map of this file (12 sections):**

1. Read the problem
2. The brute force
3. The naive heap approach (and why it's suboptimal)
4. The pivot — which old elements still matter?
5. The structural invariant — strictly decreasing values
6. The data structure — a deque
7. The algorithm
8. Code
9. Trace it
10. Amortized O(n) analysis
11. Common pitfalls
12. The shape — monotonic deque pattern

---

## 1. Read the problem

Given an array `nums` and a positive integer `k`, the **window** slides from left to right over `nums`, one position at a time. Each window contains `k` consecutive elements. Return an array containing the **MAXIMUM of each window**.

**Required:** O(n) time (or O(n log k)).

**Example:**

```
nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3

Windows:
  [1, 3, -1]       → max 3
  [3, -1, -3]      → max 3
  [-1, -3, 5]      → max 5
  [-3, 5, 3]       → max 5
  [5, 3, 6]        → max 6
  [3, 6, 7]        → max 7

Output: [3, 3, 5, 5, 6, 7].
```

There are `n - k + 1` windows.

---

## 2. The brute force

For each window, scan all k elements to find the max.

```
for i in 0..n-k:
    m = max(nums[i..i+k-1])
    result.append(m)
```

O(n × k). For n = 10^5, k = 10^4, that's 10^9 ops — TLE.

We need O(n) or O(n log k).

---

## 3. The naive heap approach (and why it's suboptimal)

Idea: maintain a max-heap of the current window. On window slide:
- Add the new element (O(log k)).
- The current max is the heap's top.
- Removing the outgoing element is tricky — a normal heap doesn't support arbitrary removal in O(log k).

Workarounds: lazy deletion (mark elements as stale, pop them when they bubble to the top). Or use a sorted-set (e.g., `std::multiset`) which supports O(log k) insert/delete.

Either way: **O(n log k)**. Better than brute force, but still log-factor.

We can do **O(n)** with a smarter data structure.

---

## 4. The pivot — which old elements still matter?

Look at two elements `nums[i]` and `nums[j]` in the current window with `i < j`. If **`nums[i] <= nums[j]`**, then `nums[i]` can NEVER be the max of any future window (because):
- `nums[j]` is at least as large.
- `nums[j]`'s position is to the RIGHT of `nums[i]`.
- Any future window containing `nums[i]` also contains `nums[j]` (since `j > i`, `j` falls out of window LATER than `i`).
- So `nums[j]` dominates `nums[i]` forever.

**Conclusion:** smaller-and-older elements can be DISCARDED.

> **Mini-refresher: the perspective shift.**
>
> Instead of asking "what's the max?", ask "which elements could POSSIBLY be the max of some future window?"
>
> Elements that arrive LATER and are LARGER make ALL earlier-and-smaller elements obsolete. Discarding them aggressively keeps our state small.

What remains? A sequence of elements where, going from older to newer, values are **STRICTLY DECREASING** (any time a newer larger value arrived, smaller older values got kicked out).

---

## 5. The structural invariant — strictly decreasing values

If the "useful" elements have strictly decreasing values from front (oldest) to back (newest), then:
- The **FRONT** is the LARGEST. It's the current window's MAX.
- The **BACK** is the smallest (so far). Newer arrivals might kick it out.

This sounds like... a stack? But we also need to remove from the FRONT (when the front's index falls out of window). Both ends needed → **deque**.

> **Mini-refresher: deque (double-ended queue).**
>
> A **deque** supports O(1) operations on BOTH ends:
> - `push_front`, `pop_front`, `front`.
> - `push_back`, `pop_back`, `back`.
>
> In C++: `std::deque<T>`. Python: `collections.deque`. JS: array with shift/pop/unshift/push (the front ops aren't O(1); use a real deque library for performance).

So we use a **monotonic decreasing deque of indices**. Why indices, not values? Because we need to know WHEN an element falls out of the window (which requires its position).

---

## 6. The data structure — a deque

Maintain a deque `dq` of INDICES with the invariant: `nums[dq[0]] >= nums[dq[1]] >= ... >= nums[dq[-1]]` (strictly, since we pop equal-or-smaller).

**Operations as we slide:**

1. **Eject stale front.** If `dq.front() <= i - k`, that index has fallen out of the window. Pop it from the front.

2. **Maintain monotonicity at the back.** While `dq` is non-empty and `nums[dq.back()] <= nums[i]`, the back is now obsolete (we just got a newer, ≥ value). Pop it.

3. **Push the new index.** `dq.push_back(i)`.

4. **Record max.** If `i >= k - 1` (we've seen enough elements for a full window), the front of the deque is the max: `result.append(nums[dq.front()])`.

---

## 7. The algorithm

```
dq = empty deque
result = []
for i in 0..n-1:
    # 1. Eject stale front
    if dq and dq[0] <= i - k:
        dq.popleft()

    # 2. Maintain monotonicity (pop equal/smaller from back)
    while dq and nums[dq[-1]] <= nums[i]:
        dq.pop()

    # 3. Push new index
    dq.append(i)

    # 4. Record max
    if i >= k - 1:
        result.append(nums[dq[0]])
return result
```

> **Mini-refresher: the order of steps matters.**
>
> 1. **Stale front check FIRST** — clear out the old before we look at the new.
> 2. **Back monotonicity** — make room for the new element.
> 3. **Push** new index.
> 4. **Record** the front (now correctly reflects the current window).

---

## 8. Code

**C++:**

```cpp
vector<int> maxSlidingWindow(vector<int>& nums, int k) {
    deque<int> dq;
    vector<int> result;
    for (int i = 0; i < (int)nums.size(); ++i) {
        // Step 1: stale front
        if (!dq.empty() && dq.front() <= i - k) {
            dq.pop_front();
        }
        // Step 2: maintain decreasing order
        while (!dq.empty() && nums[dq.back()] <= nums[i]) {
            dq.pop_back();
        }
        // Step 3: push
        dq.push_back(i);
        // Step 4: record
        if (i >= k - 1) {
            result.push_back(nums[dq.front()]);
        }
    }
    return result;
}
```

**Python:**

```python
from collections import deque

def maxSlidingWindow(nums, k):
    dq = deque()
    result = []
    for i, x in enumerate(nums):
        if dq and dq[0] <= i - k:
            dq.popleft()
        while dq and nums[dq[-1]] <= x:
            dq.pop()
        dq.append(i)
        if i >= k - 1:
            result.append(nums[dq[0]])
    return result
```

**JavaScript:**

```javascript
function maxSlidingWindow(nums, k) {
    const dq = [];        // store indices
    const result = [];
    for (let i = 0; i < nums.length; i++) {
        if (dq.length > 0 && dq[0] <= i - k) {
            dq.shift();    // O(n) for arrays — use a real deque library for perf
        }
        while (dq.length > 0 && nums[dq[dq.length - 1]] <= nums[i]) {
            dq.pop();
        }
        dq.push(i);
        if (i >= k - 1) {
            result.push(nums[dq[0]]);
        }
    }
    return result;
}
```

(JS `Array.shift` is O(n). For real production code, use a circular buffer or two-stack deque.)

Complexity: **O(n) time, O(k) space.** Each index is pushed at most once and popped at most once.

---

## 9. Trace it

**`nums = [1, 3, -1, -3, 5, 3, 6, 7]`, `k = 3`.**

I'll show the deque as a list of indices with their values in parentheses.

```
i=0 (val=1):
  Stale? dq empty → skip.
  Back ≥ 1? dq empty → skip.
  Push 0. dq = [0(1)].
  i < k-1 = 2 → no output.

i=1 (val=3):
  Stale? dq[0]=0 ≤ 1-3=-2? No → skip.
  Back monotonic? nums[0]=1 ≤ 3 → pop. dq=[]. Loop ends.
  Push 1. dq = [1(3)].
  i < 2 → no output.

i=2 (val=-1):
  Stale? dq[0]=1 ≤ 2-3=-1? No → skip.
  Back? nums[1]=3 ≤ -1? No → skip.
  Push 2. dq = [1(3), 2(-1)].
  i = 2 = k-1 → output nums[1] = 3. result = [3].

i=3 (val=-3):
  Stale? dq[0]=1 ≤ 3-3=0? No (1 > 0). Wait, 1 ≤ 0 is FALSE. Skip.
  Back? nums[2]=-1 ≤ -3? No. Skip.
  Push 3. dq = [1, 2, 3].
  output nums[1] = 3. result = [3, 3].

i=4 (val=5):
  Stale? dq[0]=1 ≤ 4-3=1? YES (1 ≤ 1). Pop front. dq = [2, 3].
  Back monotonic loop:
    nums[3]=-3 ≤ 5? YES → pop. dq = [2].
    nums[2]=-1 ≤ 5? YES → pop. dq = [].
  Push 4. dq = [4(5)].
  output nums[4] = 5. result = [3, 3, 5].

i=5 (val=3):
  Stale? dq[0]=4 ≤ 5-3=2? No. Skip.
  Back? nums[4]=5 ≤ 3? No. Skip.
  Push 5. dq = [4, 5(3)].
  output nums[4] = 5. result = [3, 3, 5, 5].

i=6 (val=6):
  Stale? dq[0]=4 ≤ 6-3=3? No. Skip.
  Back loop:
    nums[5]=3 ≤ 6? YES → pop. dq = [4].
    nums[4]=5 ≤ 6? YES → pop. dq = [].
  Push 6. dq = [6(6)].
  output 6. result = [3, 3, 5, 5, 6].

i=7 (val=7):
  Stale? dq[0]=6 ≤ 7-3=4? No.
  Back: nums[6]=6 ≤ 7? YES → pop. dq = [].
  Push 7. dq = [7(7)].
  output 7. result = [3, 3, 5, 5, 6, 7].

Return [3, 3, 5, 5, 6, 7].  ✓
```

The trace confirms the algorithm. Notice at i=4, ONE iteration ejected the stale front AND popped 2 back elements — yet across the FULL run, each index is touched O(1) times amortized.

---

## 10. Amortized O(n) analysis

> **Mini-refresher: amortized cost.**
>
> Each index is PUSHED at most once (in step 3) and POPPED at most once (in step 1 or step 2). So total push + pop operations across the entire run ≤ 2n.
>
> Combined with n iterations of the outer loop, total work = O(n).
>
> A single iteration might pop multiple elements from the back (looks like O(n)), but the total POP COUNT across all iterations is at most n. Amortized O(1) per iteration.

Same analysis as monotonic stack problems (Next Greater Element, Daily Temperatures, Largest Rectangle in Histogram).

---

## 11. Common pitfalls

1. **Storing values instead of indices.** Then you can't detect when an element falls out of the window. Always store INDICES.

2. **Using `<` vs `<=` in the back-pop comparison.** Use `<=` (pop equal-or-smaller). With `<`, equal-value elements stay in the deque, wasting space — but algorithm still correct. `<=` is cleaner.

3. **Forgetting to check stale front.** Then old indices linger; the "front" might be outside the window.

4. **Off-by-one in the stale check.** Use `dq.front() <= i - k`. Or equivalently, `dq.front() < i - k + 1`. Both check "is dq.front() outside the window `[i - k + 1, i]`?".

5. **Off-by-one in the recording step.** Output starts at `i = k - 1` (the first complete window).

6. **Forgetting that the result has `n - k + 1` elements.** Not `n` or `n - k`.

7. **Using a heap thinking it's O(n).** Heap is O(n log k). Deque is O(n).

8. **JS: using `Array.shift()` (O(n))**. Defeats the O(1) deque property. Use a real deque or maintain a circular buffer.

9. **Popping the front MULTIPLE times** for staleness. The stale check needs to happen ONCE per iteration (at most one new index becomes stale per step, since the window slides by 1).

---

## 12. The shape — monotonic deque pattern

The MONOTONIC DEQUE is the workhorse of sliding-window optimization problems.

| Problem | Variant |
|---|---|
| **This problem** | sliding window MAX → decreasing deque |
| Sliding Window Minimum | increasing deque |
| First Negative in Each Window | deque of indices of negatives |
| Constrained Subsequence Sum (DP) | window of "best subarray ending at i - 1 to i - k" |
| Jump Game VI (DP) | similar — window of "best previous position" |
| Shortest Subarray with Sum ≥ K | monotonic deque on prefix sums |
| Maximum Sum of K Consecutive Numbers (variant) | monotonic deque |

**Pattern to internalize:**

> "When you need MAX or MIN of a sliding window in O(n), use a monotonic deque of INDICES. The invariant is decreasing (for max) or increasing (for min). Three operations per step: stale-front pop, back-pop for monotonicity, push current. Read front for the window's extreme."

Same template, sometimes applied to derived sequences (prefix sums, DP values) for elegant O(n) solutions to problems that look harder.

---

> **Self-check — the question to ask next time.**
>
> When you face a sliding window with MAX/MIN extraction, ask:
>
> > **"Can I maintain a monotonic deque of indices, popping the back when newer-larger arrives and the front when its index falls out of window? Read the front to get the extreme."**
>
> If yes, you've got O(n) amortized.

---

## Cross-references

- **Reference card (post-mastery):** [`../Sliding_Window_Maximum.md`](../Sliding_Window_Maximum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Queue_using_Stacks.md`](./Implement_Queue_using_Stacks.md), [`Gas_Station.md`](./Gas_Station.md) — earlier in topic.
  - [`../../Stack/learn/Next_Greater_Element_I.md`](../../Stack/learn/Next_Greater_Element_I.md), [`../../Stack/learn/Daily_Temperatures.md`](../../Stack/learn/Daily_Temperatures.md) — monotonic STACK cousins.
  - [`../../Stack/learn/Largest_Rectangle_in_Histogram.md`](../../Stack/learn/Largest_Rectangle_in_Histogram.md) — the monotonic-structure climax.
  - Queues_Deque topic complete! Next: Sorting_Divide_and_Conquer.
