# Implement Queue using Stacks — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Implement_Queue_using_Stacks.md`](../Implement_Queue_using_Stacks.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/implement-queue-using-stacks/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The introduction to amortized analysis.** The lesson: **two stacks together can simulate a queue with O(1) AMORTIZED time per operation, by reversing the order of elements lazily.** This is a textbook example of "the worst case is bad, but the total is fine." Master this and you understand amortized complexity.

**Map of this file (10 short sections):**

1. Read the problem
2. Stack vs queue — different access patterns
3. The two-stack insight
4. Lazy transfer
5. The algorithm
6. Code
7. Trace it
8. Amortized complexity argument
9. Common pitfalls
10. The shape — amortization via batching

---

## 1. Read the problem

Implement a **first-in-first-out (FIFO) queue** using only **stack** operations. Your `MyQueue` class must support:
- `push(x)`: push `x` at the back.
- `pop()`: remove and return the front element.
- `peek()`: return the front element (don't remove).
- `empty()`: return whether the queue is empty.

You can only use standard stack operations: `push`, `peek/top`, `pop`, `empty`.

**Example:**

```
push(1); push(2); peek(); pop(); empty();
→        →        → 1      → 1     → false
```

---

## 2. Stack vs queue — different access patterns

> **Mini-refresher: stack vs queue.**
>
> | Structure | Order | Add at | Remove from |
> |---|---|---|---|
> | **Stack** | LIFO (last-in-first-out) | top | top |
> | **Queue** | FIFO (first-in-first-out) | back | front |
>
> Stack: like a stack of plates — add and remove on top.
> Queue: like a checkout line — add at the back, serve at the front.

The challenge: stack only gives us access to the TOP (the most recent element). But a queue's `pop()` should return the OLDEST element. The oldest is at the BOTTOM of a stack.

So we need a way to "reach the bottom" of a stack using only top operations.

---

## 3. The two-stack insight

> **Mini-refresher: reversing a stack with another stack.**
>
> If stack A has elements [1, 2, 3] (1 at bottom, 3 on top), and we pop all of A while pushing onto stack B, then B has [3, 2, 1] (3 at bottom, 1 on top).
>
> **The original BOTTOM (1) of A is now the TOP of B.**
>
> So to access the OLDEST element of a queue (which sits at the bottom of stack A), transfer everything from A to a SECOND stack B. The oldest is now on top of B — accessible via standard stack operations.

Two stacks:
- `inStack`: receives new elements via `push`. Newest on top.
- `outStack`: serves removals via `pop` and `peek`. Oldest on top.

When `outStack` is empty and we need to access the front: transfer everything from `inStack` to `outStack` (reversing the order in the process).

---

## 4. Lazy transfer

The key efficiency trick: **only transfer when `outStack` is empty**. Multiple pushes can accumulate on `inStack` without touching `outStack`. Only when a `pop` or `peek` is requested AND `outStack` is empty do we trigger the transfer.

> **Mini-refresher: why lazy beats eager.**
>
> An EAGER approach would rearrange the stacks on every push to maintain FIFO order. That's O(n) per push.
>
> LAZY transfer: each element is pushed once to inStack, transferred once to outStack, and popped once from outStack. That's 3 stack operations per element across its lifetime.
>
> Spread across all operations, the average cost is O(1) per queue operation — even though a SINGLE pop might do O(n) work when it triggers a transfer.

---

## 5. The algorithm

```
class MyQueue:
    inStack, outStack = stack(), stack()

    push(x):
        inStack.push(x)

    pop():
        if outStack is empty:
            while inStack not empty:
                outStack.push(inStack.pop())
        return outStack.pop()

    peek():
        if outStack is empty:
            transfer (same as in pop)
        return outStack.top()

    empty():
        return inStack and outStack are both empty
```

Transfer logic is identical for pop and peek; can factor into a helper.

---

## 6. Code

**C++:**

```cpp
class MyQueue {
    stack<int> inSt, outSt;

    void transfer() {
        while (!inSt.empty()) {
            outSt.push(inSt.top());
            inSt.pop();
        }
    }

public:
    MyQueue() {}

    void push(int x) {
        inSt.push(x);
    }

    int pop() {
        if (outSt.empty()) transfer();
        int x = outSt.top();
        outSt.pop();
        return x;
    }

    int peek() {
        if (outSt.empty()) transfer();
        return outSt.top();
    }

    bool empty() {
        return inSt.empty() && outSt.empty();
    }
};
```

**Python:**

```python
class MyQueue:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def _transfer(self):
        while self.in_stack:
            self.out_stack.append(self.in_stack.pop())

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        if not self.out_stack:
            self._transfer()
        return self.out_stack.pop()

    def peek(self):
        if not self.out_stack:
            self._transfer()
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack
```

Complexity: **amortized O(1) per operation, O(n) worst-case for a single pop/peek.**

---

## 7. Trace it

```
push(1):  inSt = [1].         outSt = [].
push(2):  inSt = [1, 2].      outSt = [].
push(3):  inSt = [1, 2, 3].   outSt = [].

peek():   outSt empty → transfer:
            pop 3 from inSt, push to outSt. outSt = [3].
            pop 2, push. outSt = [3, 2].
            pop 1, push. outSt = [3, 2, 1].
          inSt = [], outSt = [3, 2, 1] (top is 1).
          Return outSt.top() = 1.  ✓

pop():    outSt not empty. Return 1. outSt = [3, 2].

push(4):  inSt = [4]. outSt = [3, 2].

pop():    outSt not empty. Return 2. outSt = [3].
pop():    outSt not empty. Return 3. outSt = [].
pop():    outSt empty → transfer:
            pop 4 from inSt. outSt = [4].
          Return 4.
```

Pop sequence: 1, 2, 3, 4. Exactly the order they were pushed. FIFO behavior ✓.

---

## 8. Amortized complexity argument

> **Mini-refresher: amortized analysis.**
>
> **Worst-case** complexity: max cost of a SINGLE operation.
> **Amortized** complexity: AVERAGE cost across a SEQUENCE of operations.
>
> Even when a single op is expensive, the SEQUENCE can be cheap on average. We "amortize" the expensive op's cost across many cheap ones.

**Why two-stack queue is amortized O(1):**

Each element undergoes EXACTLY THREE stack operations across its lifetime:
1. Pushed onto `inStack` (during `push`).
2. Moved from `inStack` to `outStack` (during the transfer).
3. Popped from `outStack` (during `pop`).

For `k` total queue operations involving `m` elements, the total work is at most `3m`, which is at most `3k` (since each operation moves at most 1 element). So total work = O(k), giving **amortized O(1) per operation**.

A single `pop` can be O(n) (when it triggers a transfer of n elements). But that's followed by n-1 cheap pops. The expensive op "earned" the upcoming cheap ones.

---

## 9. Common pitfalls

1. **Transferring on every push.** Eager transfer makes push O(n) — defeats amortization.

2. **Transferring when `outStack` is NOT empty.** That would re-sort elements wrongly. Only transfer when `outStack` is EMPTY.

3. **Forgetting `empty()` must check both stacks.** Either could hold elements.

4. **Using one stack and trying to fake FIFO.** Doesn't achieve O(1) amortized. Two stacks are needed.

5. **Claiming worst-case O(1).** It's worst-case O(n) for a single pop/peek. The amortized claim is the O(1) one.

6. **Confusing this with implementing a stack using queues.** Symmetric problem; different code; achievable amortized only with extra effort.

7. **Transferring inside peek and not popping after.** Don't forget that pop ACTUALLY removes; peek just inspects.

---

## 10. The shape — amortization via batching

The pattern:

> **"Defer expensive work; do it in bulk only when needed. The expensive bulk work is amortized across many cheap deferred operations."**

| Problem | Deferred work |
|---|---|
| **This problem** | transfer between stacks |
| Dynamic array (vector) doubling | reallocation on capacity exceeded |
| Union-Find with path compression | flattening on find |
| Lazy evaluation in functional languages | computation on demand |
| Garbage collection | mark/sweep in bulk |
| Database batching | bulk commit |

**Pattern to internalize:**

> "When per-operation work would be expensive but is similar across operations, BATCH it. Each operation pays a small fixed cost, and an occasional one pays a big cost — total stays linear."

This is one of the most common patterns in algorithm design, data structures, and system design.

---

> **Self-check — the question to ask next time.**
>
> When you face an "implement X using Y" challenge where Y has different access semantics, ask:
>
> > **"Can I use two instances of Y, lazily transferring between them? Each element pays a fixed multi-step cost across its lifetime — amortized O(1)."**
>
> If yes, you've got an amortized solution.

---

## Cross-references

- **Reference card (post-mastery):** [`../Implement_Queue_using_Stacks.md`](../Implement_Queue_using_Stacks.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Implement_Stack_using_Queues.md`](./Implement_Stack_using_Queues.md) — symmetric problem.
  - Coming later: [`Sliding_Window_Maximum.md`](./Sliding_Window_Maximum.md) — monotonic deque, the topic's centerpiece.
