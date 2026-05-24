# Daily Temperatures — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Daily_Temperatures.md`](../Daily_Temperatures.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/daily-temperatures/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. The lesson: **the monotonic-stack pattern can store INDICES instead of values when the answer is a distance.** Once you understand this variant, the entire next-greater/previous-smaller family is unlocked. **Read [`Next_Greater_Element_I.md`](./Next_Greater_Element_I.md) first** — that file builds the monotonic-stack mental model.

**Map of this file (10 short sections):**

1. Read the problem
2. The brute force
3. The flip — "who does today resolve?"
4. Why a stack of INDICES (not values) is right
5. The invariant — strictly decreasing temperatures
6. The algorithm
7. Code
8. Trace it
9. Common pitfalls
10. The shape — index-based monotonic stacks

---

## 1. Read the problem

You're given an array `temperatures` where `temperatures[i]` is the temperature on day `i`. For each day, return how many days you have to wait until a **warmer** day. If no future day is warmer, return `0` for that day.

**Example:** `temperatures = [73, 74, 75, 71, 69, 72, 76, 73]` → `[1, 1, 4, 2, 1, 1, 0, 0]`.

Let's verify a few:
- Day 0 (73): day 1 (74) is warmer. Wait `1 - 0 = 1` day. ✓
- Day 2 (75): days 3, 4, 5 are all ≤ 75. Day 6 (76) is warmer. Wait `6 - 2 = 4` days. ✓
- Day 6 (76): no future day. 0. ✓

The answer is a **distance** (number of days), not the warmer temperature itself. That changes what we store.

---

## 2. The brute force

For each day `i`, scan forward until we find a warmer day:

```
for i from 0 to n-1:
    ans[i] = 0
    for j from i+1 to n-1:
        if temperatures[j] > temperatures[i]:
            ans[i] = j - i
            break
```

O(n²). For `n = 10⁵`, that's `10¹⁰` ops — TLE.

The waste is most obvious on monotone data. For `[5, 4, 3, 2, 1]`, every day scans the entire rest of the array and returns 0. We're checking the same indices repeatedly.

---

## 3. The flip — "who does today resolve?"

Same flip as in Next Greater Element I.

Instead of asking "for each day, scan forward," ask, when each new day arrives:

> **"Which past days does TODAY resolve (i.e., today is the warmer day they were waiting for)?"**

Imagine a waiting list of "days that haven't yet found a warmer day." When day `i` arrives with temperature `T`:

- For each day on the waiting list with temperature `< T`: today resolves them. Their answer = `i - their_index`.
- For each day with temperature `≥ T`: today doesn't help them. They keep waiting.
- Day `i` itself joins the waiting list (its warmer day not yet found).

> **Mini-refresher: same flip as Next Greater Element.**
>
> The mental shift from "I look forward" to "I get resolved when something bigger arrives" is the heart of monotonic stacks. Once you internalize this, the rest is just bookkeeping.

---

## 4. Why a stack of INDICES (not values) is right

Critical difference from Next Greater Element I: **the answer is a DISTANCE**, not the warmer temperature.

To compute `i - their_index`, we need to KNOW the index `j` of the waiting day. If we stored only temperatures, we'd lose that.

**So we store INDICES** on the stack. When we need a temperature for comparison, we look it up: `temperatures[stack.top()]`.

> **Mini-refresher: storing indices vs values on a monotonic stack.**
>
> - Store **values** when the answer is the value itself or the count of greater/smaller items (Next Greater Element I).
> - Store **indices** when the answer involves DISTANCE between positions (this problem, Largest Rectangle in Histogram).
> - In a few problems you might even store `(index, value)` pairs.
>
> The rule: store whatever the answer formula needs. Look up values via `arr[stack.top()]` when comparing.

---

## 5. The invariant — strictly decreasing temperatures

Claim: at any point, the **temperatures of the indices on the stack** form a **strictly decreasing** sequence from bottom to top.

Why? When index `i` arrives:
- We pop every index `j` from the top while `temperatures[j] < temperatures[i]`.
- After popping, the new top (if any) has temperature ≥ `temperatures[i]`.
- Then we push `i` with its temperature `temperatures[i]`.

So the new top has temperature `temperatures[i]`, and the one below (if any) has temperature **strictly greater** (since we popped any that weren't strictly greater? Let me check the precise comparison).

Wait — we pop while top's temp **is less than** current temp. So after popping, top's temp is **≥** current temp. If we want a STRICTLY decreasing stack, we'd need top's temp > current. Let me re-examine.

> **Mini-refresher: the exact comparison matters.**
>
> Two natural definitions:
> - Pop while `T[top] < T[i]` (strict less): after popping, `T[top] ≥ T[i]`. Push `i`. Now stack from bottom to top has temperatures that are **non-strictly decreasing** (could have ties).
> - Pop while `T[top] <= T[i]` (less-or-equal): after popping, `T[top] > T[i]`. Push `i`. Now stack is **strictly decreasing**.
>
> Which one matches the problem? The problem says "until a WARMER (strictly greater) day." We resolve day `j` only when we find a day with `T > T[j]`. So if `T[i] == T[j]`, day `j` is NOT yet resolved. We don't pop on equality.
>
> Use `temperatures[top] < temperatures[i]` (strict less). The stack will be **non-strictly decreasing** (equal-temp indices can coexist).
>
> Both consecutive entries `j` (older) and `k` (newer) on the stack satisfy `T[j] ≥ T[k]`. If we ever encounter a future day with `T > T[k]`, that future day must also be `> T[j]` — but `j` was below `k`, meaning `j` was inserted earlier. So when the resolving day arrives, `k` is popped first, then `j` if they share a resolver... actually `j` is popped if `T[future] > T[j]` which is a stricter requirement. Equal-temp ties cluster correctly. The algorithm stays correct.

For simplicity: imagine all temperatures distinct. Then the stack is strictly decreasing top-down. Ties handled correctly via the strict-less pop rule.

---

## 6. The algorithm

```
stack = []                        # stack of INDICES
ans = [0] * n                     # default: no warmer day found

for i in 0..n-1:
    while stack and temperatures[stack.top()] < temperatures[i]:
        j = stack.pop()
        ans[j] = i - j            # i is the warmer day for index j; distance i - j
    stack.push(i)

# indices still on the stack at the end never found a warmer day → ans stays 0
return ans
```

Note: `ans` is initialized to `0`, which is the correct default for indices that never get popped (no warmer day found). No need to drain the stack at the end.

---

## 7. Code

**C++:**

```cpp
vector<int> dailyTemperatures(vector<int>& temperatures) {
    int n = temperatures.size();
    vector<int> ans(n, 0);
    stack<int> st;                        // stack of indices

    for (int i = 0; i < n; ++i) {
        while (!st.empty() && temperatures[st.top()] < temperatures[i]) {
            int j = st.top(); st.pop();
            ans[j] = i - j;
        }
        st.push(i);
    }

    return ans;
}
```

**Python:**

```python
def dailyTemperatures(temperatures):
    n = len(temperatures)
    ans = [0] * n
    stack = []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            ans[j] = i - j
        stack.append(i)
    return ans
```

**JavaScript:**

```javascript
function dailyTemperatures(temperatures) {
    const n = temperatures.length;
    const ans = new Array(n).fill(0);
    const stack = [];
    for (let i = 0; i < n; i++) {
        while (stack.length && temperatures[stack[stack.length - 1]] < temperatures[i]) {
            const j = stack.pop();
            ans[j] = i - j;
        }
        stack.push(i);
    }
    return ans;
}
```

Complexity: **O(n) time, O(n) space** (stack can hold up to n indices in the worst case — strictly decreasing input).

---

## 8. Trace it

`temperatures = [73, 74, 75, 71, 69, 72, 76, 73]`. Initial: `ans = [0,0,0,0,0,0,0,0]`.

I'll show each iteration. `stack` will hold indices; I'll annotate with `index:temp` for clarity.

```
i=0, T=73: stack empty. push.                       stack = [0:73].

i=1, T=74: top is 0 (T=73) < 74 → pop 0. ans[0] = 1-0 = 1.
           stack empty. push 1.                      stack = [1:74].

i=2, T=75: top is 1 (T=74) < 75 → pop 1. ans[1] = 2-1 = 1.
           stack empty. push 2.                      stack = [2:75].

i=3, T=71: top is 2 (T=75) NOT < 71. push 3.        stack = [2:75, 3:71].

i=4, T=69: top is 3 (T=71) NOT < 69. push 4.        stack = [2:75, 3:71, 4:69].

i=5, T=72: top is 4 (T=69) < 72 → pop 4. ans[4] = 5-4 = 1.
           top is 3 (T=71) < 72 → pop 3. ans[3] = 5-3 = 2.
           top is 2 (T=75) NOT < 72. push 5.         stack = [2:75, 5:72].

i=6, T=76: top is 5 (T=72) < 76 → pop 5. ans[5] = 6-5 = 1.
           top is 2 (T=75) < 76 → pop 2. ans[2] = 6-2 = 4.
           stack empty. push 6.                      stack = [6:76].

i=7, T=73: top is 6 (T=76) NOT < 73. push 7.        stack = [6:76, 7:73].

End. Indices 6 and 7 still on stack — ans[6] and ans[7] stay 0.

ans = [1, 1, 4, 2, 1, 1, 0, 0].  ✓
```

Watch i=5: ONE iteration popped TWO indices. That's where amortized cost beats worst-case-per-iteration. Across the full run, total pop count ≤ total push count = n, so it's O(n).

Watch the stack's temperatures stay decreasing top-down: `[73]`, `[74]`, `[75]`, `[75, 71]`, `[75, 71, 69]`, `[75, 72]`, `[76]`, `[76, 73]`. ✓

---

## 9. Common pitfalls

1. **Storing temperatures instead of indices.** Then you can't compute `i - j`. ALWAYS store indices for "distance" type answers.

2. **Forgetting to look up temperatures via `temperatures[stack.top()]`.** Comparing the INDEX itself (e.g., `stack.top() < i`) is meaningless — you want to compare TEMPERATURES.

3. **Using `<=` instead of `<` in the pop condition.** Subtle. The problem wants STRICTLY warmer. A tied temperature does NOT resolve. Use `<`.

4. **Forgetting to initialize `ans` to 0.** Indices that never get popped keep their default — must be 0. Most languages default-initialize to 0 for int arrays, but explicit is safer.

5. **Trying to walk right-to-left.** That works for a different formulation but is harder to get right. Left-to-right with monotonic stack is the standard approach.

6. **Thinking the algorithm is O(n²) because of the nested while.** Be ready to defend O(n) via amortized analysis: each index is pushed once, popped at most once.

7. **Pushing the current index BEFORE the while loop.** No — push AFTER. The while compares the incoming temperature against waiting ones; pushing first would include the current index in its own comparison.

8. **Confusing "next greater" with "next warmer or equal."** Problem says STRICTLY warmer.

---

## 10. The shape — index-based monotonic stacks

The lesson: **when the answer involves a DISTANCE or RELATIONSHIP between positions, store INDICES on the monotonic stack.**

Where this generalizes:

| Problem | What "warmer" means | Store on stack |
|---|---|---|
| **This problem** | next strictly greater value | indices |
| Next Greater Element I | next strictly greater value | values (since answer is the value) |
| Largest Rectangle in Histogram | previous & next strictly smaller | indices (need width = right - left - 1) |
| Trapping Rain Water | walls | indices |
| Sum of Subarray Minimums | each element's range as minimum | indices |
| Online Stock Span | previous greater (count) | (price, span) pairs |
| Sliding Window Maximum (deque variant) | max in window | indices |

**Pattern to internalize:**

> "Monotonic stack of INDICES = O(n) computation of 'how far / how many' relationships between positions."

The recognition cue: ANSWER is a DISTANCE → STORE INDICES.

---

> **Self-check — the question to ask next time.**
>
> When you face "for each position, find the distance to the next greater/smaller value," before nesting loops, ask:
>
> > **"Can I use a monotonic stack OF INDICES, popping each index when a future position resolves it (and computing distance = future_index - popped_index)?"**
>
> If yes, you've turned O(n²) into O(n) — and gotten distance-based answers for free.

---

## Cross-references

- **Reference card (post-mastery):** [`../Daily_Temperatures.md`](../Daily_Temperatures.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Next_Greater_Element_I.md`](./Next_Greater_Element_I.md) — same pattern with VALUES.
  - Coming next: [`Largest_Rectangle_in_Histogram.md`](./Largest_Rectangle_in_Histogram.md) — monotonic stack at its hardest (BOTH previous and next smaller).
