# Max Consecutive Ones

**Problem Link:**
https://leetcode.com/problems/max-consecutive-ones/

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: The Task

Given a binary array `nums` (0's and 1's), return the length of the **longest run of consecutive 1's**.

Example: `nums = [1, 1, 0, 1, 1, 1]`. Runs of 1s: lengths 2 and 3. Max = **3**.
Example: `nums = [1, 0, 1, 1, 0, 1]`. Runs: 1, 2, 1. Max = **2**.
Example: `nums = [0, 0, 0]`. No 1s anywhere. Max = **0**.

----------------------------------------

## Step 2: Walk the Array Once

Think about what information we need at each index:
- The **length of the current run** we're inside.
- The **maximum run length** seen so far.

As we walk left to right:
- If the current element is 1, the current run extends by 1.
- If the current element is 0, the current run resets to 0.
- After each step, update the maximum with the current run's length.

Single pass. O(n) time, O(1) extra space.

----------------------------------------

## Step 3: Algorithm

```
cur = 0
best = 0
for x in nums:
    if x == 1:
        cur += 1
        best = max(best, cur)
    else:
        cur = 0
return best
```

That's it. No tricks — it's just a straightforward scan with two counters.

----------------------------------------

## Step 4: Trace

`nums = [1, 1, 0, 1, 1, 1]`:

```
x=1: cur=1, best=1.
x=1: cur=2, best=2.
x=0: cur=0, best=2.
x=1: cur=1, best=2.
x=1: cur=2, best=2.
x=1: cur=3, best=3.
```

Return **3**. ✓

Try `nums = [1, 0, 1, 1, 0, 1]`:
```
x=1: cur=1, best=1.
x=0: cur=0, best=1.
x=1: cur=1, best=1.
x=1: cur=2, best=2.
x=0: cur=0, best=2.
x=1: cur=1, best=2.
```

Return **2**. ✓

----------------------------------------

## Step 5: Why the Reset?

Every 0 ends the current run. The next 1 starts a fresh run of length 1. If we didn't reset, we'd be counting across 0s — wrong.

This is the characteristic shape of "longest run" problems: maintain a **current streak**, reset on a boundary, track the max.

Same pattern applies to:
- Longest run of any character.
- Longest monotonic subarray.
- Longest valid region (the streak criterion just changes).

----------------------------------------

## Step 6: Name It

**Single-pass streak counting**. One of the most fundamental array idioms.

Related problems:
- Max Consecutive Ones II (allow flipping one 0 to 1; use sliding window).
- Max Consecutive Ones III (flip up to k 0's; same sliding-window technique).
- Longest subarray with all equal elements.
- Longest increasing run.

The **basic** version (this problem) has no flips, so there's no sliding-window state to maintain — a single counter suffices.

----------------------------------------

## Step 7: Complexity

Time: **O(n)**. Single pass.
Space: **O(1)** extra.

Optimal — we must read every element at least once.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int findMaxConsecutiveOnes(vector<int>& nums) {
    int cur = 0, best = 0;
    for (int x : nums) {
        if (x == 1) {
            cur++;
            best = max(best, cur);
        } else {
            cur = 0;
        }
    }
    return best;
}
```

Three lines of logic. Hard to simplify further.

----------------------------------------

## Step 9: Follow-up Questions

- **Allow flipping up to k 0's to 1's (Max Consecutive Ones III).** Sliding window with "at most k zeros inside" constraint.
- **Return the starting index of the longest run too.** Track `start_of_current_run` and save it when `cur > best`.
- **Count runs of length ≥ L.** Add a counter that increments whenever a run reaches length L.
- **Streaming / online input.** Same algorithm — just two counters in memory.
- **Count of runs (instead of longest length).** Count transitions from 0 to 1.
- **Why reset `cur = 0` rather than decrement?** Because a 0 doesn't reduce the current run by 1; it ends it entirely. A single 0 between two groups of 1s separates them completely.
