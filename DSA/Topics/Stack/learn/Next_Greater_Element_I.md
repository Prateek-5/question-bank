# Next Greater Element I — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Next_Greater_Element_I.md`](../Next_Greater_Element_I.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/next-greater-element-i/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/next-greater-element-i/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **This is THE introduction to the monotonic-stack pattern.** Master this and you'll see it everywhere: Daily Temperatures, Largest Rectangle in Histogram, Trapping Rain Water (alternate solution), Sum of Subarray Minimums, Sliding Window Maximum (with deque). The mental shift required is: **instead of "for each element, scan forward," ask "for each new element, which past elements does it RESOLVE?"**

**Map of this file (12 short sections):**

1. Read the problem
2. The brute force
3. Why the brute force wastes work
4. The pivot — who does the new element RESOLVE?
5. The waiting list must be decreasing
6. Meet the monotonic decreasing stack
7. The algorithm
8. Amortized analysis — why this is O(n)
9. Code
10. Trace it
11. Common pitfalls
12. The shape — monotonic-stack pattern

---

## 1. Read the problem

You're given two **arrays of distinct integers**, `nums1` and `nums2`. Critically, **`nums1` is a SUBSET of `nums2`** (every element of `nums1` appears somewhere in `nums2`).

For each element `x` in `nums1`:
1. Find `x` inside `nums2`.
2. Look to its right in `nums2`.
3. Return the FIRST element to its right that is **strictly greater than `x`**, or **`-1`** if none.

Return all answers as a list, in the order of `nums1`.

**Example:** `nums1 = [4, 1, 2]`, `nums2 = [1, 3, 4, 2]`.

- `4` is at index 2 of `nums2`. To its right: `[2]`. No element > 4. → `-1`.
- `1` is at index 0. To its right: `[3, 4, 2]`. First > 1: `3`. → `3`.
- `2` is at index 3. To its right: `[]`. → `-1`.

Output: `[-1, 3, -1]`.

> **Mini-refresher: "first to the right that's greater" — why it's tricky.**
>
> The straightforward read: for each `x`, scan right until you find something bigger. That's O(n) per element. With many queries, that's O(n²) overall. We want a way to PREPROCESS `nums2` so each query is O(1).

---

## 2. The brute force

For each `x` in `nums1`:
1. Find `x` in `nums2` (linear scan: O(n2)).
2. Walk right from there until a larger element appears (linear scan: O(n2)).

```
for x in nums1:
    idx = index of x in nums2     # O(n2)
    ans = -1
    for j from idx+1 to n2-1:     # O(n2)
        if nums2[j] > x:
            ans = nums2[j]; break
    result.append(ans)
```

Total: **O(n1 · n2)**. Acceptable for small inputs but slow for `n2 ≈ 10⁴+`.

The wasted work: for each query, we re-walk `nums2`. We're computing the same "next greater" answers over and over.

---

## 3. Why the brute force wastes work

Observation: the answer for each value in `nums2` is **independent of `nums1`**. If we PRECOMPUTED, for every position in `nums2`, the next-greater value, then each `nums1` query is just a **lookup**.

So the real problem isn't "answer n1 queries on nums2." It's:

> **"Given `nums2`, find the next-greater value for EVERY element of `nums2`. Then answer queries in O(1) via a hashmap."**

If we can do that preprocessing in O(n2), the total cost becomes **O(n1 + n2)** — and the queries are essentially free.

The question becomes: can we compute next-greater-for-all in O(n2)?

---

## 4. The pivot — who does the new element RESOLVE?

The naïve "for each i, scan right to find the next greater" is **forward-looking** — we ask, from position i's perspective, "where's my next greater?"

**Flip it.** As we scan `nums2` left to right, ask, from the NEW element's perspective:

> **"Which past elements does THIS NEW element resolve (i.e., become the 'next greater' for)?"**

Suppose we maintain a **waiting list** of elements we've seen but haven't yet found a "next greater" for. When a new value `v` arrives:

- Every element in the waiting list that is **smaller than `v`** now has its answer: `v`. Remove them from the waiting list.
- Add `v` to the waiting list (we haven't found ITS next-greater yet).

> **Mini-refresher: the perspective shift.**
>
> Backward-looking (push current) vs forward-looking (pull future) is a common algorithmic move. Examples:
> - **DP "for each i, what's f(i)?"** vs "for each i, what does it CONTRIBUTE to future f(j)?"
> - **Graph traversal "what can reach me?"** vs "what can I reach?"
> - **Scheduling "when do I run?"** vs "what does my completion unblock?"
>
> The backward → forward flip often reveals a cleaner algorithm. Here, it turns a forward-scanning approach into one where each element's answer is computed at the moment it gets RESOLVED.

---

## 5. The waiting list must be decreasing

What does the waiting list look like at any moment?

**Claim:** if we keep removing every element smaller than the newcomer when it arrives, the waiting list (ordered oldest to newest) is **strictly decreasing**.

Why? Consider two consecutive elements `A` (older) and `B` (newer) both on the waiting list. If `A < B`, then when `B` arrived, `A` should have been resolved and removed. So `A` must be > `B`. Thus: oldest on the list is largest; newest is smallest.

**Visual:**

```
Walk nums2 = [1, 3, 4, 2]:

After 1:     waiting list = [1].                           (just 1)
After 3:     newcomer 3 > 1 → resolve 1 (ans[1]=3).        waiting = [3].
After 4:     newcomer 4 > 3 → resolve 3 (ans[3]=4).        waiting = [4].
After 2:     newcomer 2 < 4 → don't resolve 4. add 2.     waiting = [4, 2].

End. Anyone left has no next-greater → ans[4]=-1, ans[2]=-1.
```

Notice the waiting list is always decreasing: `[1]`, `[3]`, `[4]`, `[4, 2]`. Never increasing.

---

## 6. Meet the monotonic decreasing stack

A waiting list where:
- **You only add** to one end (the "newest" end).
- **You remove** from that same end, multiple at a time, when a newcomer "kicks out" elements.

That's exactly a **stack** (LIFO). And because the contents are always in decreasing order from bottom to top, we call it a **monotonic decreasing stack**.

> **Mini-refresher: what makes a stack "monotonic"?**
>
> A **monotonic stack** is a normal stack with an **invariant**: its contents are always in monotonic (increasing or decreasing) order. We MAINTAIN the invariant by popping any element that would violate it BEFORE pushing the new element.
>
> - **Monotonic decreasing stack** (bottom > top): use it to find next greater elements. Pop everything smaller than the newcomer before pushing.
> - **Monotonic increasing stack** (bottom < top): use it to find next smaller elements. Pop everything greater than the newcomer.
>
> "Bottom > top" vs "bottom < top" is just a matter of which side you call "the bottom." The IDEA is: the stack is sorted, and you maintain that order on push.

For our problem: monotonic decreasing stack. When newcomer `v` arrives, pop everything smaller. Whatever was popped now has `v` as its next-greater. Then push `v`.

---

## 7. The algorithm

```
stack = []                       # monotonic decreasing stack of nums2 VALUES
ans_map = {}                     # value → its next-greater value (or -1)

for v in nums2:
    while stack and stack.top() < v:
        popped = stack.pop()
        ans_map[popped] = v
    stack.push(v)

# elements never popped have no next-greater → -1
while stack:
    ans_map[stack.pop()] = -1

# answer queries
return [ans_map[x] for x in nums1]
```

Three phases:
1. Walk `nums2`, building `ans_map`.
2. Anything left on the stack at the end never found a "next greater" — assign `-1`.
3. Look up each `nums1` element in the map.

> **Mini-refresher: why we store VALUES (not indices) here.**
>
> In some "next greater" problems we store INDICES on the stack (e.g., Daily_Temperatures, where we need `i - j` for the answer). Here, the answer is the VALUE itself, and `nums1` gives queries by value (since values are distinct). So storing values is sufficient and lets us use a value-keyed map.

---

## 8. Amortized analysis — why this is O(n)

Looking at the code:

```
for v in nums2:                  # O(n)
    while ...:                   # ← could this be O(n) each? Looks O(n²)!
        ...
```

The inner `while` could pop multiple elements. Could the total work be O(n²)?

**No — and here's why.** Each element of `nums2` is **pushed exactly once** (in the outer loop) and **popped at most once** (in the inner loop, or at the end). The TOTAL number of pop operations across the entire algorithm is ≤ `n`. Combined with `n` pushes, the total work is `≤ 2n = O(n)`.

> **Mini-refresher: amortized analysis.**
>
> **Amortized cost** = total work across a sequence of operations / number of operations. Even if a single operation is occasionally expensive, the AVERAGE per operation can be small.
>
> Classic example: a dynamic array's `push_back`. Sometimes the array doubles in size (O(n) work), but most pushes are O(1). Total work across n pushes: O(n). Amortized O(1) per push.
>
> Same idea here. A single `while` iteration could pop many elements. But across the whole run, the total pop count ≤ push count ≤ n. So each `nums2` element contributes O(1) amortized work.

This is the secret sauce of monotonic-stack algorithms. They look quadratic but are linear.

---

## 9. Code

**C++:**

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

**Python:**

```python
def nextGreaterElement(nums1, nums2):
    ans = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ans[stack.pop()] = v
        stack.append(v)
    while stack:
        ans[stack.pop()] = -1
    return [ans[x] for x in nums1]
```

**JavaScript:**

```javascript
function nextGreaterElement(nums1, nums2) {
    const ans = new Map();
    const stack = [];
    for (const v of nums2) {
        while (stack.length && stack[stack.length - 1] < v) {
            ans.set(stack.pop(), v);
        }
        stack.push(v);
    }
    while (stack.length) {
        ans.set(stack.pop(), -1);
    }
    return nums1.map(x => ans.get(x));
}
```

Complexity: **O(n1 + n2) time, O(n2) space.**

---

## 10. Trace it

`nums1 = [4, 1, 2]`, `nums2 = [1, 3, 4, 2]`.

**Phase 1: walk `nums2`.**

```
stack = [], ans = {}.

v=1: stack empty. push.            stack = [1].
v=3: top is 1 < 3 → pop 1. ans[1]=3.
                                    stack = [].
     push 3.                        stack = [3].
v=4: top is 3 < 4 → pop 3. ans[3]=4.
                                    stack = [].
     push 4.                        stack = [4].
v=2: top is 4 ≥ 2 → don't pop. push 2.  stack = [4, 2].

After loop: ans = {1:3, 3:4}.
```

**Phase 2: drain stack.**

```
pop 2 → ans[2] = -1.
pop 4 → ans[4] = -1.
```

`ans = {1:3, 3:4, 2:-1, 4:-1}`.

**Phase 3: queries.**

```
nums1 = [4, 1, 2]:
  ans[4] = -1
  ans[1] = 3
  ans[2] = -1

Result: [-1, 3, -1].  ✓
```

Verify visually: the stack at each step was `[1]`, `[3]`, `[4]`, `[4, 2]` — always decreasing top-down. ✓

---

## 11. Common pitfalls

1. **Confusing "greater" with "greater or equal."** This problem says STRICTLY greater. Use `<` (strict) in the pop condition. If duplicates were allowed (they aren't here), `<=` would behave differently.

2. **Iterating in the wrong direction.** "Next" greater means RIGHT of the current position. Iterating right-to-left would compute "previous" greater. Iterate left-to-right.

3. **Storing indices when values would suffice (or vice versa).** Here we store VALUES because `nums1` queries by value (distinct values). For Daily Temperatures, we store INDICES because we need `j - i` distances. Match the storage to what the answer needs.

4. **Forgetting to drain the stack at the end.** Elements still on the stack after the main loop NEVER found a next-greater — they need `-1`. Don't forget the drain phase.

5. **Building a separate "answer per nums2 position" list.** Unnecessary since values are distinct — a value → answer map suffices. (If `nums2` had duplicates, you'd need indices.)

6. **Using a sorted set or BIT for next-greater.** Overkill. The monotonic stack is O(n); a sorted set would be O(n log n).

7. **Not appreciating why it's O(n).** Many candidates write the code correctly but say "it's O(n·m)." Be ready to explain the amortized argument (Section 8) — interviewers ask.

---

## 12. The shape — monotonic-stack pattern

The pattern this problem teaches:

> **"For each element, find the next/previous greater/smaller element."** → **monotonic stack**.

Four variants, all the same shape with comparison direction flipped:

| What you want | Iteration direction | Stack invariant | Pop condition |
|---|---|---|---|
| **Next greater** (this problem) | left → right | decreasing (top is smallest) | top < newcomer |
| Next smaller | left → right | increasing (top is largest) | top > newcomer |
| Previous greater | right → left | decreasing | top < newcomer |
| Previous smaller | right → left | increasing | top > newcomer |

Where this generalizes:

| Problem | Variant |
|---|---|
| **This problem** | next greater |
| Daily Temperatures | next greater (by INDEX distance) |
| Next Greater Element II (circular) | iterate `2n` positions (wrap around) |
| Stock Span Problem | previous greater |
| Sum of Subarray Minimums | previous & next smaller |
| Largest Rectangle in Histogram | previous & next smaller |
| Trapping Rain Water (stack version) | previous & next greater |
| Remove K Digits | previous smaller (with limited removals) |
| Maximum Width Ramp | previous smaller (right to left) |

**Pattern to internalize:**

> "When a problem asks for 'next/previous X-er element' for every position, reach for the monotonic stack. Push on each element; pop everything that the newcomer 'resolves.' Total O(n)."

The mental cue: "for every element, find the next..." → monotonic stack.

---

> **Self-check — the question to ask next time.**
>
> When you face "for each element, find the nearest later element that's larger/smaller," before nesting loops, ask:
>
> > **"Can I keep a stack of 'unresolved' elements that the next-arriving element either resolves (pop) or joins (push)? Maintain monotonic order to ensure each element is popped at most once → O(n) total."**
>
> If yes, you've turned O(n²) into O(n) via a monotonic stack.

---

## Cross-references

- **Reference card (post-mastery):** [`../Next_Greater_Element_I.md`](../Next_Greater_Element_I.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Parentheses.md`](./Valid_Parentheses.md), [`Min_Stack.md`](./Min_Stack.md) — stack basics.
  - Coming next: [`Daily_Temperatures.md`](./Daily_Temperatures.md) — same pattern, INDICES.
  - Coming after that: [`Largest_Rectangle_in_Histogram.md`](./Largest_Rectangle_in_Histogram.md) — monotonic stack at its hardest.
