# Sliding Window Maximum

**Problem Link:**
<a href="https://leetcode.com/problems/sliding-window-maximum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/sliding-window-maximum/</a>

**Topic:**
Queues / Deque / Monotonic Queue

----------------------------------------

## Step 1: Understand the Problem

You have an array `nums` and a window size `k`. The window slides from left to right, one position at a time, and you need the **maximum inside the window** at every position.

Example: `nums = [1, 3, -1, -3, 5, 3, 6, 7]`, `k = 3`. Windows and their maxes:

```
[1, 3, -1]             → 3
   [3, -1, -3]         → 3
       [-1, -3, 5]     → 5
           [-3, 5, 3]  → 5
               [5, 3, 6] → 6
                  [3, 6, 7] → 7
```

Output: `[3, 3, 5, 5, 6, 7]`.

There are `n - k + 1` windows, and we need the max of each.

----------------------------------------

## Step 2: The Brute-Force Baseline

For each window, scan all `k` elements to find the max.

```cpp
for (int i = 0; i <= n - k; ++i) {
    int best = nums[i];
    for (int j = i + 1; j < i + k; ++j) best = max(best, nums[j]);
    result.push_back(best);
}
```

O(n · k). For `n = 10^5` and `k = 10^4`, that's 10^9 — way too slow.

The obvious waste: when the window slides by one, we recompute the max from scratch. But we already know a lot about the window — we just dropped one element on the left and added one on the right. Most of the window is the same. Can we exploit that?

----------------------------------------

## Step 3: What Would It Take to Update Max in O(1)?

If the *new* element on the right is larger than the current max, the new max is the new element. Easy.

If the new element is smaller, and the *dropped* element was the max, we have to find the new max — which could be anywhere in the window.

If the new element is smaller and the dropped element was *not* the max, the max stays the same. Also easy, but we still don't know this without checking.

So the hard case is: "the max of the window was the one we're dropping." Then we need a next-best candidate.

Hmm — what if we kept a *sorted* list of candidates? Or better, what if we maintained, at all times, only the elements that *could possibly* be the max of some future window?

----------------------------------------

## Step 4: Which Elements Can Possibly Be Max Later?

Here's a sharp observation. Consider two indices `i < j` both inside the window. If `nums[i] <= nums[j]`, then `nums[i]` can **never** be the max of any future window — because `nums[j]` is larger, sits inside the same window, and will remain inside every window that still contains `nums[i]` (since `j > i`, if `i` is still in a future window, so is `j`).

So whenever a newer, bigger number arrives, all older-and-smaller numbers become **irrelevant**. We can discard them.

This means: the set of "still-useful" elements, ordered by index, forms a **strictly decreasing sequence of values**. (Any time a larger value entered, smaller older values were kicked out; so what remains is a decreasing staircase.)

Also, whenever the left end of the window passes an index, that element's usefulness ends too. We pop it from the left if it's still there.

----------------------------------------

## Step 5: The Data Structure We Need

We want:

- Insert a new index `i` on the right, possibly kicking out older smaller values.
- Remove an old index from the left when it falls out of the window.
- Answer "what's the max of the current window?" — that's the index at the left (front) of our structure.

Both ends. Both O(1). That's a **deque**.

Specifically, a **monotonic decreasing deque** of indices, where the front index always points to the current window's maximum.

----------------------------------------

## Step 6: The Algorithm in Concrete Steps

For each `i` from 0 to n-1:

1. **Remove outdated front.** If the front index `≤ i - k`, it's out of the window — pop it.
2. **Maintain monotonicity at the back.** While the deque is non-empty and `nums[dq.back()] ≤ nums[i]`, pop the back (those elements are now irrelevant).
3. **Insert i at the back.**
4. **Record answer** if `i >= k - 1`: the front's value is the window max.

----------------------------------------

## Step 7: Trace on `[1, 3, -1, -3, 5, 3, 6, 7]` with k=3

I'll show the deque (as a list of indices) with their values in parentheses for clarity.

```
i=0 (val=1):
  front stale? dq empty.
  back ≤ 1? no (empty).
  push 0. dq = [0(1)].
  i < k-1, no output.

i=1 (val=3):
  front stale? no.
  nums[back=0]=1 ≤ 3? yes. pop 0. dq = [].
  push 1. dq = [1(3)].
  i < k-1.

i=2 (val=-1):
  front stale? dq.front=1 ≤ 2-3=-1? no.
  nums[back=1]=3 ≤ -1? no.
  push 2. dq = [1(3), 2(-1)].
  i=2=k-1, output nums[dq.front]=3.  → output: [3]

i=3 (val=-3):
  front stale? dq.front=1 ≤ 3-3=0? yes. pop 1. dq = [2(-1)].
  nums[back=2]=-1 ≤ -3? no.
  push 3. dq = [2(-1), 3(-3)].
  output 3.  → [3, 3]

Wait, the output should be 3 here? No wait, I have front=2, nums[2]=-1.
Let me redo. Actually at i=3 the window is indices [1,2,3] = [3,-1,-3]. Max is 3, at index 1. But I just popped index 1 because 1 ≤ 3-3=0. Hmm, is index 1 inside the window?

Window at i=3 is [i-k+1 .. i] = [1 .. 3]. So index 1 is inside. But my stale-front check said "front ≤ i - k = 0", which evicts indices 0 and below. Index 1 is not ≤ 0. I made an arithmetic error above — let me redo.

i=3: i-k = 0. Is dq.front=1 ≤ 0? No, 1 > 0. Don't pop.
```

Let me restart the trace more carefully.

```
i=0 (v=1): dq=[], push 0. dq=[0(1)]. i<k-1.
i=1 (v=3): back val=1 ≤ 3 → pop. dq=[]. push 1. dq=[1(3)]. i<k-1.
i=2 (v=-1): back val=3 ≤ -1? no. push. dq=[1(3), 2(-1)]. i=k-1, out=3.
i=3 (v=-3): front=1 ≤ i-k=0? 1>0 → no pop. back val=-1 ≤ -3? no. push. dq=[1, 2, 3]. out=3.
i=4 (v=5): front=1 ≤ i-k=1? 1≤1 yes → pop front. dq=[2, 3]. back val=-3 ≤ 5 → pop. dq=[2]. back val=-1 ≤ 5 → pop. dq=[]. push 4. dq=[4(5)]. out=5.
i=5 (v=3): front=4 ≤ 2? no. back val=5 ≤ 3? no. push. dq=[4, 5]. out=5.
i=6 (v=6): front=4 ≤ 3? no. back val=3 ≤ 6 → pop. dq=[4]. back val=5 ≤ 6 → pop. dq=[]. push 6. dq=[6(6)]. out=6.
i=7 (v=7): front=6 ≤ 4? no. back val=6 ≤ 7 → pop. dq=[]. push 7. dq=[7(7)]. out=7.
```

Output: `[3, 3, 5, 5, 6, 7]`. ✓

The inner "while" loop looks like it could make things quadratic, but each index is pushed exactly once and popped at most once over the entire run. Amortized O(1) per step, O(n) total.

----------------------------------------

## Step 8: Invariants

- The deque holds indices currently "alive" in the window. ("Alive" = not stale and not dominated by a larger newer value.)
- Their *values* are strictly decreasing from front to back.
- The front index is always the maximum of the current window.

Both invariants follow directly from the push/pop rules.

----------------------------------------

## Step 9: Complexity

Time: each index enters and leaves the deque at most once → amortized O(1) per step → **O(n)**.
Space: the deque holds at most k indices → **O(k)**.

Went from O(n·k) brute force to O(n). The key leverage: recognizing which past elements can never be the answer again, and discarding them eagerly.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> maxSlidingWindow(vector<int>& nums, int k) {
    deque<int> dq;
    vector<int> res;
    for (int i = 0; i < (int)nums.size(); ++i) {
        // remove stale front (outside window)
        if (!dq.empty() && dq.front() <= i - k) dq.pop_front();
        // maintain decreasing order: kick out smaller-or-equal at back
        while (!dq.empty() && nums[dq.back()] <= nums[i]) dq.pop_back();
        dq.push_back(i);
        if (i >= k - 1) res.push_back(nums[dq.front()]);
    }
    return res;
}
```

A small implementation habit: store **indices**, not values. Values alone lose the position information needed to evict stale entries. It's a common beginner mistake to store pairs or just values and then struggle to detect staleness.

----------------------------------------

## Step 11: Follow-up Questions

- **Sliding window minimum.** Same pattern, but flip the comparison — maintain an increasing deque.
- **Median in a sliding window.** Much harder; requires two balanced multisets (analogous to the two-heap median technique).
- **Variable-size window max (window changes size as it slides).** Same deque works as long as the "stale front" condition is updated to reflect the new window boundary.
- **What if the input is a stream and you can't access arbitrary indices?** The deque still works — you process elements in order, one at a time.
- **First negative number in each window.** Same structure — maintain a deque of indices of negative values; remove stale ones; the front is the answer.
