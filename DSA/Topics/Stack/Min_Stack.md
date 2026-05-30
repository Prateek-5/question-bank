# Min Stack

**Problem Link:**
<a href="https://leetcode.com/problems/min-stack/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/min-stack/</a>

**Topic:**
Stack

----------------------------------------

## Step 1: The Specification

Design a data structure that supports:
- `push(x)` — add x to the top.
- `pop()` — remove the top.
- `top()` — return the top.
- `getMin()` — return the minimum element currently in the structure.

And critically: **all four operations must run in O(1)** time.

That last word — "all" — is the crux. A normal stack gives us push/pop/top in O(1), but not getMin without a scan.

Example operations:
```
push(-2), push(0), push(-3)
getMin()  → -3
pop()
top()     → 0
getMin()  → -2
```

After popping -3, the min among the remaining `{-2, 0}` is -2. So getMin must adapt as the stack shrinks.

----------------------------------------

## Step 2: What Makes getMin Hard?

If I just store values in a single stack, `getMin()` requires scanning — O(n). The minimum changes as elements are popped; there's no way around that with a plain stack.

What if I maintain a **separate variable** `minVal` that always holds the current min? That gives O(1) `getMin()`. But when we pop the minimum, we need to restore the previous minimum. The previous minimum could be anywhere in the stack — so we'd need to scan. Back to O(n).

The problem with a single `minVal` is: it forgets history. When the current minimum disappears, we have no record of who was second-smallest, third-smallest, etc.

So we need to store enough history to reconstruct the min as elements come and go.

----------------------------------------

## Step 3: Idea — Track Min at Every Level

What if, alongside each value, we also remembered "what is the minimum among this value and everything below it in the stack"?

In other words, when we push value `x`:
- If the stack was empty (or `x` is the new global min), the min-so-far for this level is `x`.
- Otherwise, the min-so-far is `min(x, min-so-far of the level below)`.

When we pop, we also pop this stored min. So the min-so-far at the new top reflects the min of everything that remains.

Let me visualize with the example above:

```
push(-2):  stack: [(-2, min=-2)]
push(0):   stack: [(-2, min=-2), (0, min=-2)]          (0 didn't beat -2)
push(-3):  stack: [(-2, min=-2), (0, min=-2), (-3, min=-3)]

getMin() looks at the top's stored min: -3. ✓

pop() removes (-3, -3).
stack: [(-2, min=-2), (0, min=-2)]
top() returns 0 (the value component). ✓
getMin() returns -2 (the top's stored min). ✓
```

Every operation is O(1): push pushes one pair, pop pops one pair, top and getMin read the top pair's components.

----------------------------------------

## Step 4: Simpler — Two Stacks

A cleaner phrasing uses **two stacks**: the main one holds values, and a second stack holds the running minimum.

- `push(x)`: push `x` onto the main stack. Push `min(x, top of min stack)` onto the min stack. (If min stack is empty, push `x`.)
- `pop()`: pop both.
- `top()`: return top of the main stack.
- `getMin()`: return top of the min stack.

This works because at every moment the top of the min stack reflects the minimum of all values currently present in the main stack. The two stacks are always the same size and represent the same "slice" of history.

Some folks prefer the "one stack of pairs" version (Step 3); others prefer the "two parallel stacks" version. They're algorithmically equivalent. I lean toward two stacks for clarity, but either works.

----------------------------------------

## Step 5: Can We Do It With Less Memory?

Yes — there's a clever **encoding trick** that uses one stack of plain numbers but stores *differences* from the running minimum. Whenever we push a new min, we store `(new_value - old_min)` (a negative sentinel), and update the running `minVal`.

The math is clever but brittle — watch for overflow when values can be `INT_MIN`. For most interview settings, the two-stack version is clearer and always correct.

----------------------------------------

## Step 6: Trace the Two-Stack Version

Operations: `push(-2), push(0), push(-3), getMin, pop, top, getMin`.

```
push(-2):  main=[-2]    min=[-2]
push(0):   main=[-2, 0] min=[-2, -2]       (min(0, -2) = -2)
push(-3):  main=[-2, 0, -3] min=[-2, -2, -3] (min(-3, -2) = -3)

getMin() = -3 (top of min) ✓

pop():    main=[-2, 0] min=[-2, -2]

top() = 0 ✓
getMin() = -2 ✓
```

Every step is O(1) and correct.

----------------------------------------

## Step 7: Why Push Duplicates in the Min Stack?

A natural question: can we save memory by only pushing to the min stack when the new value is actually a new minimum?

Answer: yes, it works, but pop becomes slightly more involved. If the popped value equals the current min, pop the min stack too; otherwise leave it alone.

```cpp
void push(int x) {
    main.push(x);
    if (min_stack.empty() || x <= min_stack.top()) min_stack.push(x);
}
void pop() {
    if (main.top() == min_stack.top()) min_stack.pop();
    main.pop();
}
```

Saves memory when minimums are rare, at the cost of a tiny bit more code. Always uses `<=` (not `<`) to handle duplicate minimums correctly.

----------------------------------------

## Step 8: Complexity

Each operation: **O(1)** worst case.

Space: **O(n)** with the straightforward two-stack approach (min stack grows with main stack). **O(k)** with the "push duplicates only when new min" optimization, where `k` is the number of distinct minimums encountered.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class MinStack {
    stack<int> st;
    stack<int> minSt;
public:
    MinStack() {}

    void push(int x) {
        st.push(x);
        if (minSt.empty() || x <= minSt.top()) minSt.push(x);
    }

    void pop() {
        if (st.top() == minSt.top()) minSt.pop();
        st.pop();
    }

    int top() { return st.top(); }

    int getMin() { return minSt.top(); }
};
```

Important style note: when checking `x <= minSt.top()` during push, I use `<=` (not `<`). This ensures that if there are duplicate minimums and one gets popped, the other remains on the min stack. A common bug is using `<`, which loses duplicates.

----------------------------------------

## Step 10: Follow-up Questions

- **Max stack (same operations but track max).** Symmetric — swap all `min` for `max`.
- **Both min and max in one stack.** Two auxiliary stacks or pair-tuples.
- **Stack that supports middle-element access in O(1).** Use a doubly-linked list with explicit middle pointer; moves one step per push/pop.
- **Implement a queue with the same "getMin in O(1)" property.** Harder — you'd need two stacks with min-tracking, or a monotonic deque.
- **If pop returns "the minimum" instead of "the top", it's a priority queue.** Different data structure — O(log n), not O(1).
