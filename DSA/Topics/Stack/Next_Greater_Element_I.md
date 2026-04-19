# Next Greater Element I

**Problem Link:**
https://leetcode.com/problems/next-greater-element-i/

**Topic:**
Stack

----------------------------------------

## Step 1: Understand the Two Arrays

You get two arrays: `nums1` and `nums2`. `nums1` is a **subset** of `nums2`. Both contain distinct integers.

For each element `x` in `nums1`:
- Find `x` inside `nums2`.
- Look at the elements to the **right** of `x` in `nums2`.
- Return the first one that is **greater than** `x`.
- If no such element exists, return -1.

The final output is a list of answers, one per `nums1` element, in the same order.

Example: `nums1 = [4, 1, 2]`, `nums2 = [1, 3, 4, 2]`.

- For 4 in nums2: it's at index 2. To its right: [2]. Nothing greater than 4. Answer: -1.
- For 1 in nums2: at index 0. To its right: [3, 4, 2]. First greater than 1: 3. Answer: 3.
- For 2 in nums2: at index 3. Nothing to its right. Answer: -1.

Output: `[-1, 3, -1]`.

----------------------------------------

## Step 2: The Naïve Approach

For each query `x`, find its index in `nums2`, then scan right looking for a larger value.

```cpp
for (int x : nums1) {
    int idx = find(x in nums2);
    int ans = -1;
    for (int j = idx + 1; j < nums2.size(); ++j) {
        if (nums2[j] > x) { ans = nums2[j]; break; }
    }
    result.push_back(ans);
}
```

Per query: O(n) to find `x`, O(n) to scan. Total: O(n1 · n2) in the worst case. For large inputs, slow.

But here's the thing — if we knew, for *every* element of `nums2`, what its next-greater element is, we could answer any query about a subset of `nums2` in O(1) (just look up from a hashmap). So the real work is computing next-greater-for-all in `nums2` efficiently.

----------------------------------------

## Step 3: Precompute Next-Greater for Every Element of nums2

Focus on `nums2 = [1, 3, 4, 2]`. Let me compute next-greater for each position:

- Position 0 (value 1): look right. First greater: 3. Answer: 3.
- Position 1 (value 3): look right. First greater: 4. Answer: 4.
- Position 2 (value 4): look right. Only 2. Nothing greater. Answer: -1.
- Position 3 (value 2): nothing to the right. Answer: -1.

Naively: O(n²). But we can do O(n) with a stack.

----------------------------------------

## Step 4: Rethink the Scan Direction

Instead of "for each element, scan forward to find its next greater," flip it: **"for each new element coming in, which past elements does it resolve?"**

As I walk `nums2` left to right, I maintain a "waiting list" of elements I've seen but haven't resolved yet (their next-greater not yet found).

When I encounter a new value `v`, any element in the waiting list that's smaller than `v` has its answer: `v`. I resolve those and remove them from the waiting list.

What stays on the waiting list? Elements larger than or equal to `v`. They still wait.

The waiting list at any moment is therefore in **decreasing order** (bottom to top): larger elements at the bottom, smaller ones at top. Because we always kick out anything smaller than the newcomer — what's left can only be larger.

A waiting list with "only push smaller on top" and "pop from top when a new big value arrives" is exactly a **stack maintaining decreasing order** — aka monotonic decreasing stack.

----------------------------------------

## Step 5: The Algorithm

```
stack = []
ans_map = {}

for v in nums2:
    while stack and stack.top() < v:
        x = stack.pop()
        ans_map[x] = v
    stack.push(v)

# any elements still on the stack have no next greater
for x in stack: ans_map[x] = -1

# answer queries using the map
return [ans_map[x] for x in nums1]
```

Each element in `nums2` is pushed once and popped at most once — total O(n2) work. For each query in `nums1`, map lookup is O(1) average. Total: O(n1 + n2).

----------------------------------------

## Step 6: Trace on `nums2 = [1, 3, 4, 2]`

```
stack: [], ans: {}

v=1: stack empty. push. stack=[1].
v=3: 3 > 1 (top). pop 1. ans[1]=3. push 3. stack=[3].
v=4: 4 > 3. pop 3. ans[3]=4. push 4. stack=[4].
v=2: 2 < 4. push. stack=[4, 2].

End. Remaining on stack: 4 and 2 → ans[4]=-1, ans[2]=-1.
```

ans = {1: 3, 3: 4, 4: -1, 2: -1}.

Query for `nums1 = [4, 1, 2]`: answers are `[-1, 3, -1]`. ✓

----------------------------------------

## Step 7: Why This Is O(n) — Amortization

The inner `while` loop inside the for-loop looks like it could make things O(n²). But each element is pushed exactly once and popped at most once across the **entire** outer loop. The total number of pop operations is at most `n2`. Combined with `n2` pushes, total work is O(n2).

This is the classic **amortized analysis** of monotonic stacks: per-step looks scary but total work is linear.

----------------------------------------

## Step 8: Name What We Built

This is a **monotonic decreasing stack** — a stack maintained so its values decrease from bottom to top. The defining use case: "next greater element" problems. Flip the comparison direction for "next smaller," "previous greater," etc.

Also notice: the problem's two-array setup is just dressing. The core work — computing next-greater-for-all in `nums2` — is the interesting part. `nums1` is just specifying which subset of answers to return.

----------------------------------------

## Step 9: Complexity

Time: **O(n1 + n2)**. Each `nums2` element touched a constant number of times; each `nums1` query is an O(1) map lookup.

Space: **O(n2)** for the map. The stack is bounded by `nums2` size.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> nextGreaterElement(vector<int>& nums1, vector<int>& nums2) {
    unordered_map<int, int> ans;
    stack<int> st;

    for (int v : nums2) {
        while (!st.empty() && st.top() < v) {
            ans[st.top()] = v;
            st.pop();
        }
        st.push(v);
    }
    // anything left has no greater to the right
    while (!st.empty()) {
        ans[st.top()] = -1;
        st.pop();
    }

    vector<int> result;
    result.reserve(nums1.size());
    for (int x : nums1) result.push_back(ans[x]);
    return result;
}
```

Note: since `nums1` is guaranteed to be a subset of `nums2`, we don't need a special "not found" case — every query is in the map.

----------------------------------------

## Step 11: Follow-up Questions

- **Next Greater Element II (nums is circular — indices wrap around).** Iterate `2n` positions (`i % n`), processing each; the elements not resolved after one full pass get resolved in the second pass.
- **Previous greater element.** Scan right-to-left with the same monotonic-stack idea.
- **Next smaller element.** Flip the comparison (`> v` instead of `< v`).
- **If `nums1` and `nums2` contain duplicates.** Map by index rather than by value — each element's answer is position-specific.
- **Support updates to `nums2`.** Online problem — requires a segment tree with max queries, more complex.
- **Answer both next-greater and previous-greater for every element.** Two passes with monotonic stacks, or a single two-pass algorithm.
