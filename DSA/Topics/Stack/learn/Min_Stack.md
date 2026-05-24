# Min Stack — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Min_Stack.md`](../Min_Stack.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/min-stack/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. The lesson: **a side-by-side auxiliary structure can give you O(1) access to a derived property (here, the min) that would otherwise require a scan.** This "auxiliary stack" pattern reappears in: max stack, two-stack queue, sliding-window max with deque, and persistent data structures. **Read [`Valid_Parentheses.md`](./Valid_Parentheses.md) first** so you know what a stack is.

**Map of this file (11 short sections):**

1. Read the problem
2. The trivial start that fails the constraint
3. Why a single `minVal` doesn't work
4. The pivot question
5. The two-stack design
6. Why this gives O(1) for getMin
7. The duplicate-min subtle bug
8. Code
9. Trace it
10. Common pitfalls
11. The shape — auxiliary structures for derived properties

---

## 1. Read the problem

Design a class `MinStack` supporting four operations:

| Operation | Effect |
|---|---|
| `push(x)` | add `x` to the top |
| `pop()` | remove the top |
| `top()` | return the top value |
| `getMin()` | return the SMALLEST value currently in the stack |

**The hard constraint:** all four operations must run in **O(1)** time.

Without the O(1) constraint, this would be trivial — a normal stack with a scan for `getMin`. The constraint is the whole problem.

**Example:**

```
push(-2); push(0); push(-3);
getMin()  → -3
pop();
top()      → 0
getMin()   → -2
```

After popping `-3`, the min among the remaining `{-2, 0}` becomes `-2`. So `getMin` must adapt as pop changes the contents.

---

## 2. The trivial start that fails the constraint

A normal stack gives O(1) for `push`, `pop`, `top` — but `getMin` needs to scan. For `n` elements, that's O(n) per call.

```
class MinStack {
    stack<int> st;
    int getMin() {                       // O(n) — fails the constraint!
        // copy stack, scan, restore — yuck
    }
}
```

We need to AVOID the scan. The question is: how?

---

## 3. Why a single `minVal` doesn't work

**First instinct:** maintain a single variable `minVal` that holds the current minimum. Update on push. Read on `getMin`. O(1).

```
push(x):
    st.push(x)
    if x < minVal: minVal = x          # update if x is the new min

getMin():
    return minVal                       # O(1) read
```

This works UNTIL you pop. Suppose the minimum element gets popped. What's the NEW minimum? `minVal` no longer reflects truth — but to find the new min, we'd have to scan. **Back to O(n).**

> **Mini-refresher: why a single state variable breaks under pop.**
>
> When you push, only one variable matters (the new value's relation to the current min). But when you pop, the state has BRANCHED — popping requires you to RESTORE the previous min, which was overwritten when the current min came in.
>
> A single `minVal` **forgets history**. We need a way to remember "what was the min BEFORE this push?" so that pop can restore it.

---

## 4. The pivot question

Instead of "what is the min RIGHT NOW," ask:

> **"What is the min AT EVERY LEVEL of the stack?"**

If, at every level of the stack, we knew the min of everything from that level downward, then when an element is popped the LEVEL BELOW it already knows ITS min — and that becomes the new min.

So alongside each value, store "the min of this value and everything below it on the stack."

```
push(-2):  stack: [(-2, min=-2)]
push(0):   stack: [(-2, min=-2), (0, min=-2)]            # 0 doesn't beat -2
push(-3):  stack: [(-2, min=-2), (0, min=-2), (-3, min=-3)]   # -3 IS the new min

getMin() = top's stored min = -3.  ✓

pop():  remove (-3, -3).  stack: [(-2, min=-2), (0, min=-2)]
getMin() = top's stored min = -2.  ✓
```

Two values per stack slot, but every operation is still O(1).

---

## 5. The two-stack design

A cleaner way to think about it: use **two parallel stacks**.

- `mainSt`: holds the actual values (a normal stack).
- `minSt`: holds the running minimum. At every index `i`, `minSt[i]` = `min(mainSt[0..i])`.

The two stacks are ALWAYS the same size and represent the same "slice" of history.

**Operations:**

```
push(x):
    mainSt.push(x)
    if minSt.empty():
        minSt.push(x)
    else:
        minSt.push(min(x, minSt.top()))

pop():
    mainSt.pop()
    minSt.pop()                                  # always pop both

top():
    return mainSt.top()

getMin():
    return minSt.top()
```

Why does this work? The top of `minSt` always reflects the minimum of the entire current `mainSt`. When we pop, BOTH stacks shrink by one — the new top of `minSt` reflects the min of the (now smaller) `mainSt`.

---

## 6. Why this gives O(1) for getMin

- `push`: one comparison, two pushes. O(1).
- `pop`: two pops. O(1).
- `top`: one stack-top read. O(1).
- `getMin`: one stack-top read on `minSt`. O(1).

We've traded SPACE for TIME. The min stack uses O(n) extra space (one entry per element in the main stack). In return, we get O(1) `getMin`.

> **Mini-refresher: space-time tradeoff.**
>
> A recurring algorithm-design move. If a derived property (min, max, sum, max-so-far, …) is expensive to recompute, store it alongside the data. The extra memory typically grows linearly with the data, and the derived property becomes O(1) to read.
>
> Other examples:
> - **Prefix sum array** stores `sum[0..i]` so range sums become O(1).
> - **Hash set alongside a list** for O(1) membership.
> - **Doubly linked list** stores both prev and next pointers so removal of any node is O(1).

---

## 7. The duplicate-min subtle bug

A natural optimization: "only push to `minSt` when `x` is a NEW minimum." Saves memory when minimums are rare.

```
push(x):
    mainSt.push(x)
    if minSt.empty() or x < minSt.top():
        minSt.push(x)

pop():
    if mainSt.top() == minSt.top():
        minSt.pop()
    mainSt.pop()
```

Looks fine. But there's a subtle bug — **what about duplicate minimums?**

Consider: `push(2); push(2); pop()`. After two pushes, `mainSt = [2, 2]`, `minSt = [2]` (because the second 2 was NOT strictly less than the current min). Now pop. The current min is 2, so we'd pop `minSt` too — `minSt = []`. But there's STILL a 2 on the main stack! `getMin` would now read an empty stack — crash.

**Fix:** use `<=` instead of `<` on push. That way, equal-to-min elements ALSO get pushed onto `minSt`, and the pop logic stays correct.

```
push(x):
    mainSt.push(x)
    if minSt.empty() or x <= minSt.top():        // ← <= not <
        minSt.push(x)
```

> **Mini-refresher: the off-by-equality trap.**
>
> Whenever you build a structure that tracks "the current best" alongside data, and elements can tie, using `<` vs `<=` becomes load-bearing. Same applies to monotonic stacks/deques (next-greater problems). When in doubt, test the equal case explicitly.

---

## 8. Code

**C++:**

```cpp
class MinStack {
    stack<int> st;
    stack<int> minSt;
public:
    MinStack() {}

    void push(int x) {
        st.push(x);
        if (minSt.empty() || x <= minSt.top()) {
            minSt.push(x);
        }
    }

    void pop() {
        if (st.top() == minSt.top()) {
            minSt.pop();
        }
        st.pop();
    }

    int top() { return st.top(); }

    int getMin() { return minSt.top(); }
};
```

**Python:**

```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []

    def push(self, x):
        self.stack.append(x)
        if not self.min_stack or x <= self.min_stack[-1]:
            self.min_stack.append(x)

    def pop(self):
        if self.stack[-1] == self.min_stack[-1]:
            self.min_stack.pop()
        self.stack.pop()

    def top(self):
        return self.stack[-1]

    def getMin(self):
        return self.min_stack[-1]
```

**JavaScript:**

```javascript
class MinStack {
    constructor() {
        this.stack = [];
        this.minStack = [];
    }
    push(x) {
        this.stack.push(x);
        if (this.minStack.length === 0 || x <= this.minStack[this.minStack.length - 1]) {
            this.minStack.push(x);
        }
    }
    pop() {
        if (this.stack[this.stack.length - 1] === this.minStack[this.minStack.length - 1]) {
            this.minStack.pop();
        }
        this.stack.pop();
    }
    top() {
        return this.stack[this.stack.length - 1];
    }
    getMin() {
        return this.minStack[this.minStack.length - 1];
    }
}
```

All operations: **O(1) worst case time, O(n) space.**

---

## 9. Trace it

Sequence: `push(2); push(2); push(1); push(2); getMin; pop; getMin; pop; getMin; pop; getMin`.

```
push(2):  st=[2]        minSt=[2]            (empty before — push to minSt)
push(2):  st=[2,2]      minSt=[2,2]          (2 <= 2 — push to minSt)
push(1):  st=[2,2,1]    minSt=[2,2,1]        (1 <= 2 — push to minSt)
push(2):  st=[2,2,1,2]  minSt=[2,2,1]        (2 NOT <= 1 — do NOT push to minSt)

getMin() = top of minSt = 1.  ✓

pop():    st.top()=2, minSt.top()=1. 2 != 1, so DON'T pop minSt. Pop st.
          st=[2,2,1]    minSt=[2,2,1]

getMin() = 1.  ✓

pop():    st.top()=1, minSt.top()=1. EQUAL — pop minSt too. Pop st.
          st=[2,2]      minSt=[2,2]

getMin() = 2.  ✓ (and note the duplicate min was preserved!)

pop():    st.top()=2, minSt.top()=2. EQUAL — pop both.
          st=[2]        minSt=[2]

getMin() = 2.  ✓ (still 2 — the OTHER 2 is still there)
```

The duplicate-min handling worked correctly because of `<=`. With `<`, after `push(2); push(2)` we'd have `minSt=[2]`, and the first pop would empty `minSt` even though a 2 remained on the main stack. Crash on the next `getMin`.

---

## 10. Common pitfalls

1. **Using `<` instead of `<=` on push.** Breaks duplicate minimums (Section 7 trap). Always `<=`.

2. **Trying to use a single variable for `minVal`.** Fails on pop. Section 3.

3. **Trying to scan in `getMin`.** Violates the O(1) constraint. The whole point is to avoid this.

4. **Forgetting to push to `minSt` when the main stack is empty.** The first push must initialize `minSt` to `[x]`. Check `minSt.empty()` first.

5. **Popping `minSt` unconditionally** (in the optimized version). If the popped value isn't the current min, `minSt` shouldn't change. Compare first.

6. **The "encode differences" trick.** Some solutions use a SINGLE stack of differences from the running min. Clever but error-prone — int overflow on `INT_MIN`. Two stacks are safer.

7. **Confusing with a priority queue.** A min-heap gives O(1) min but O(log n) pop. Different data structure with different semantics — pop from a heap removes the MIN, but pop from MinStack removes the TOP (last in). Don't mix.

8. **Returning the min from `top()`.** Read carefully. `top()` returns the most recently pushed value (LIFO). `getMin()` returns the smallest.

---

## 11. The shape — auxiliary structures for derived properties

The pattern this problem teaches:

> **"When you need O(1) access to a property derived from the stack contents (min, max, sum, …), maintain a side-by-side auxiliary structure that stores that property at each level."**

Where this generalizes:

| Problem | Main structure | Auxiliary | Property tracked |
|---|---|---|---|
| **This problem** | stack | min stack | running min |
| Max Stack | stack | max stack | running max |
| Stack with O(1) average | stack | sum at each level | running sum |
| Queue using two stacks | stack(s) | second stack | FIFO order |
| Sliding window max | deque | deque holds candidate max indices | window max |
| LRU cache | hash + DLL | the DLL acts as auxiliary recency ordering | recency |

**Pattern to internalize:**

> "Push and pop are O(1) opportunities to UPDATE auxiliary state. Use them to maintain any derived property you'll need to read in O(1)."

The space cost is typically a constant factor times the main structure. The time savings (from O(n) scans down to O(1) reads) is usually decisive.

---

> **Self-check — the question to ask next time.**
>
> When a problem says "support all these stack/queue operations in O(1)" and one of them computes a derived property (min, max, sum, …) that normally requires a scan, ask:
>
> > **"Can I maintain a parallel auxiliary structure that updates O(1) on push/pop, so the derived property is O(1) to read?"**
>
> If yes, the constraint is satisfied.

---

## Cross-references

- **Reference card (post-mastery):** [`../Min_Stack.md`](../Min_Stack.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Parentheses.md`](./Valid_Parentheses.md), [`Remove_Outermost_Parentheses.md`](./Remove_Outermost_Parentheses.md), [`Remove_All_Adjacent_Duplicates_in_String.md`](./Remove_All_Adjacent_Duplicates_in_String.md) — stack basics.
  - Coming next: Baseball_Game, Evaluate_Reverse_Polish_Notation — stack as simulation.
