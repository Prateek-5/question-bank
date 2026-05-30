# Daily Temperatures

**Problem Link:**
<a href="https://leetcode.com/problems/daily-temperatures/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/daily-temperatures/</a>

**Topic:**
Stack

----------------------------------------

## Step 1: Read the Problem Carefully

You have an array `T` of daily temperatures. For each day `i`, return the number of days you have to wait until a warmer day. If no future day is warmer, return 0 for that day.

Example: `T = [73, 74, 75, 71, 69, 72, 76, 73]` → `[1, 1, 4, 2, 1, 1, 0, 0]`.

Let me read the expected output for day 0: `T[0] = 73`, `T[1] = 74`, and 74 > 73, so we wait 1 day. ✓
Day 2: `T[2] = 75`. Looking forward, `T[3], T[4], T[5] = 71, 69, 72` are all ≤ 75. `T[6] = 76 > 75`. So we wait `6 - 2 = 4` days. ✓

So we're essentially asking, for each index, "where's the nearest later index with a strictly larger value?"

----------------------------------------

## Step 2: The Obvious Approach

For each index `i`, scan right until we find a larger value. That's two nested loops.

```cpp
for (int i = 0; i < n; ++i)
    for (int j = i + 1; j < n; ++j)
        if (T[j] > T[i]) { ans[i] = j - i; break; }
```

Time: O(n²). Fine for small inputs, too slow for `n = 10^5`.

What's wasteful here? Suppose I'm at day 2 (temp 75). I scan forward through 71, 69, 72 and find nothing larger yet. Now I move to day 3 (temp 71). I scan forward again through 69, 72... but 72 is larger than 71, so I stop quickly. The inefficiency is not huge in this case, but in a *descending* array like `[5, 4, 3, 2, 1]`, every day re-scans the entire rest of the array even though they all return 0.

Can we avoid re-scanning? That's the key question.

----------------------------------------

## Step 3: Flip the Question

Instead of thinking "for each day, find the next warmer day", flip it:

> "When a new day arrives, which previous days does it *resolve*?"

Think of the days we've seen so far as a waiting list — days that haven't yet found a warmer day. When today's temperature comes in, it might be warmer than some of those waiting days, and for those, today is the answer.

Example. Suppose I've just seen days with temperatures `75, 71, 69`. All three are waiting for a warmer day. Today is 72. Then:
- Is 72 > 69? Yes → day with temp 69 is resolved. Today is the warmer day for it.
- Is 72 > 71? Yes → day with temp 71 is resolved too.
- Is 72 > 75? No → day with temp 75 still waits.

So today resolved two days. Notice something important: the waiting days in order (75, 71, 69) are **decreasing**. That's not a coincidence — any day that was *at most* as warm as some earlier waiting day would have been resolved *by* that earlier day on arrival. Since the later day is still waiting, it means no earlier waiting day was larger than it. So the waiting list is always in strictly decreasing temperature order (reading from oldest to newest).

That structure — "always decreasing" — is a hint.

----------------------------------------

## Step 4: We Need a Decreasing Stack of Indices

Let's maintain a stack of indices whose temperatures are still waiting for a warmer day. As we walk through each new index `i`:

1. While the stack is non-empty and `T[i] > T[stack.top()]`, the current day resolves the day on top of the stack. Pop it, record `ans[popped] = i - popped`.
2. Push `i` onto the stack.

At the end, whatever indices remain on the stack never found a warmer day — their `ans` stays `0`.

Each index is pushed exactly once and popped at most once. Total work is O(n), even though at first glance there's a "while" loop inside the "for" loop.

----------------------------------------

## Step 5: Trace It on the Example

`T = [73, 74, 75, 71, 69, 72, 76, 73]`, `ans = [0,0,0,0,0,0,0,0]` initially.

Stack stores indices; I'll show the temperatures next to them for clarity.

```
i=0, T=73: stack empty, push 0.                stack = [0:73]
i=1, T=74: 74 > 73, pop 0, ans[0] = 1-0 = 1.   stack = []
           push 1.                              stack = [1:74]
i=2, T=75: 75 > 74, pop 1, ans[1] = 2-1 = 1.   stack = []
           push 2.                              stack = [2:75]
i=3, T=71: 71 < 75, don't pop. push 3.         stack = [2:75, 3:71]
i=4, T=69: 69 < 71, don't pop. push 4.         stack = [2:75, 3:71, 4:69]
i=5, T=72: 72 > 69, pop 4, ans[4] = 5-4 = 1.   stack = [2:75, 3:71]
           72 > 71, pop 3, ans[3] = 5-3 = 2.   stack = [2:75]
           72 < 75, stop. push 5.              stack = [2:75, 5:72]
i=6, T=76: 76 > 72, pop 5, ans[5] = 6-5 = 1.   stack = [2:75]
           76 > 75, pop 2, ans[2] = 6-2 = 4.   stack = []
           push 6.                              stack = [6:76]
i=7, T=73: 73 < 76, don't pop. push 7.         stack = [6:76, 7:73]
```

End of array. Stack is `[6, 7]`. Their `ans` values stay `0`.

Final: `ans = [1, 1, 4, 2, 1, 1, 0, 0]`. ✓

Look at what happened at `i=5` — one iteration resolved *two* old days in a row. That's the magic of the stack: the amortized cost is O(1) per index, because each index gets popped at most once across the entire run.

----------------------------------------

## Step 6: Why This Works — The Invariant

The stack always holds indices in **strictly decreasing** temperature order from bottom to top. Here's why that invariant is maintained:

- Before pushing `i`, we pop every index on top whose temperature is ≤ `T[i]`.
- What's left on top is either the stack was empty (nothing to pop), or some index whose temperature is strictly greater than `T[i]`.
- So when we push `i`, the new top is `T[i]`, and the one below (if any) is strictly greater. Invariant holds.

This invariant is what makes the algorithm work. When a new `T[i]` arrives, the indices on the stack whose temperatures are less than `T[i]` are exactly contiguous from the top. We pop them all.

----------------------------------------

## Step 7: Naming What We Built

This is the classic **monotonic stack** pattern — a stack where elements are kept in monotonic order (increasing or decreasing) by popping violators on insertion. Monotonic stacks are the go-to technique for "next greater / previous smaller"-style problems. The name isn't what matters; the invariant does.

But again, notice: we didn't start by saying "oh this needs a monotonic stack". We started by asking "why re-scan?" and "who does today resolve?" The monotonic-decreasing structure emerged from those questions.

----------------------------------------

## Step 8: Complexity

Time: each index is pushed once and popped at most once. The total work across the entire loop is **O(n)**, even though the inner `while` looks like it could make things quadratic.

Space: the stack can hold up to n indices (all decreasing). **O(n)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
vector<int> dailyTemperatures(vector<int>& T) {
    int n = T.size();
    vector<int> ans(n, 0);
    stack<int> st;                   // indices of days waiting for a warmer day
    for (int i = 0; i < n; ++i) {
        while (!st.empty() && T[i] > T[st.top()]) {
            int j = st.top(); st.pop();
            ans[j] = i - j;
        }
        st.push(i);
    }
    return ans;
}
```

The `while` loop looks scary but, as argued, is amortized O(1).

----------------------------------------

## Step 10: Follow-up Questions

- **Next *strictly smaller* day.** Flip the comparison to `T[i] < T[st.top()]` and keep the stack monotonically increasing.
- **Next greater or equal (not strictly greater).** Change `>` to `>=`.
- **Circular array (next greater element II).** Run the loop twice (indices 0 to 2n-1, mod n). Don't push the second time around — just resolve.
- **What if temperatures can be updated later (streaming)?** Harder problem — you'd need segment tree with monotonic queries, or an indexed structure.
- **Previous warmer day instead of next warmer?** Run the same idea right-to-left, or swap "next" and "previous" by iterating in reverse.
