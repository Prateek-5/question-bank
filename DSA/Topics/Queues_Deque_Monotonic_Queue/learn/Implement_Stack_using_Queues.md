# Implement Stack using Queues — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Implement_Stack_using_Queues.md`](../Implement_Stack_using_Queues.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/implement-stack-using-queues/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-stack-using-queues/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. The lesson: **the reverse direction (stack-from-queues) is asymmetric — you can't get amortized O(1) for free; one operation MUST be O(n).** Either push pays the cost (rotate on every push) or pop does. **Read [`Implement_Queue_using_Stacks.md`](./Implement_Queue_using_Stacks.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. Why this is asymmetric
3. Strategy A — costly push, cheap pop
4. Strategy B — cheap push, costly pop
5. Code
6. Trace it
7. Common pitfalls
8. The shape — asymmetric trade-offs

---

## 1. Read the problem

Implement a **stack** (LIFO) using only **queue** operations.

Your `MyStack` class must support:
- `push(x)`: add `x` on top.
- `pop()`: remove and return the top.
- `top()`: return the top (don't remove).
- `empty()`: return whether the stack is empty.

You can only use queue operations: `push(x)` at the back, `pop()` from the front, `front()`/`back()`/`size()`/`empty()`.

---

## 2. Why this is asymmetric

In Implement Queue using Stacks, we got **amortized O(1)** for all operations using two stacks with lazy transfer. The trick was that each element passed through 3 stack operations across its lifetime.

For Implement Stack using Queues, you CAN'T get amortized O(1) for both push and pop with simple methods. The trade-off:
- **Strategy A:** push is O(n); pop/top are O(1).
- **Strategy B:** push is O(1); pop/top are O(n).

In both cases, one operation is O(n). The total work for n operations is O(n²) in the worst case if all are the expensive type.

There ARE more elaborate schemes that achieve better complexity, but they're overkill for an interview.

---

## 3. Strategy A — costly push, cheap pop

Use ONE queue. On `push(x)`:
1. Enqueue x at the back.
2. ROTATE: dequeue every OTHER element (the ones that were there before) from the front, and re-enqueue them at the back.

After this, the most recently pushed element (`x`) is at the FRONT. Future `pop` and `top` just read the front.

**Visualization:**

```
push(1):  q = [1].
push(2):  q = [1, 2]. Rotate the existing 1 to the back:
            dequeue 1, enqueue 1 → q = [2, 1].
push(3):  q = [2, 1, 3]. Rotate 2 to back: q = [1, 3, 2]. Rotate 1 to back: q = [3, 2, 1].

top()  = q.front() = 3.   ✓
pop() removes 3.
```

> **Mini-refresher: why rotate?**
>
> The queue's "front" is where dequeue happens. We want the LATEST element to be at the front. So after enqueuing it, we rotate every other element (which were the OLDER ones) past it.
>
> Each rotation step preserves the relative order of older elements but moves the newest to the front.

push is O(n) (n - 1 rotations). pop, top are O(1).

---

## 4. Strategy B — cheap push, costly pop

Use TWO queues, `q1` (the "main") and `q2` (auxiliary).

- `push(x)`: just enqueue x onto q1.
- `pop()`: move all but the last element of q1 to q2; the last element is the answer; swap q1 and q2.
- `top()`: similar but re-enqueue the last element back to q2 first.

push is O(1). pop, top are O(n).

This strategy is more complex code-wise and rarely preferred.

---

## 5. Code

**C++ — Strategy A (preferred):**

```cpp
class MyStack {
    queue<int> q;
public:
    MyStack() {}

    void push(int x) {
        q.push(x);
        int n = q.size();
        for (int i = 0; i < n - 1; ++i) {
            q.push(q.front());
            q.pop();
        }
    }

    int pop() {
        int x = q.front();
        q.pop();
        return x;
    }

    int top() {
        return q.front();
    }

    bool empty() {
        return q.empty();
    }
};
```

**Python:**

```python
from collections import deque

class MyStack:
    def __init__(self):
        self.q = deque()

    def push(self, x):
        self.q.append(x)
        for _ in range(len(self.q) - 1):
            self.q.append(self.q.popleft())

    def pop(self):
        return self.q.popleft()

    def top(self):
        return self.q[0]

    def empty(self):
        return len(self.q) == 0
```

Complexity (Strategy A):
- push: **O(n)**.
- pop, top, empty: **O(1)**.

---

## 6. Trace it

```
Operations: push(1), push(2), push(3), top, pop, push(4), top, pop, pop.

push(1):
  q = [1]. Rotate 0 times.
  q after: [1].

push(2):
  q.push(2) → [1, 2]. Rotate 1 time: dequeue 1, enqueue 1 → [2, 1].
  q after: [2, 1].

push(3):
  q.push(3) → [2, 1, 3]. Rotate 2 times:
    dequeue 2, enqueue 2 → [1, 3, 2].
    dequeue 1, enqueue 1 → [3, 2, 1].
  q after: [3, 2, 1].

top: q.front() = 3.   ✓

pop: q.pop_front() = 3. q after: [2, 1].

push(4):
  q.push(4) → [2, 1, 4]. Rotate 2 times:
    dequeue 2, enqueue 2 → [1, 4, 2].
    dequeue 1, enqueue 1 → [4, 2, 1].
  q after: [4, 2, 1].

top: 4.  ✓
pop: 4.  q after: [2, 1].
pop: 2.  q after: [1].
```

Pop sequence: 3, 4, 2 — matches the LIFO order of pushes (3 pushed last, 4 pushed after 3 was popped, 2 was deeper). ✓

---

## 7. Common pitfalls

1. **Wrong rotation count.** Rotate `n - 1` times, not `n` (else you'd rotate the just-pushed element away from the front).

2. **Trying to claim amortized O(1).** With simple queue ops, you CAN'T get amortized O(1) for both push and pop. One is always linear.

3. **Mixing strategies.** Pick one and stick with it; mixing causes bugs.

4. **Forgetting `empty` check before pop/top.** In LeetCode this problem promises valid input, but defensive code returns 0 or raises an error on empty stack.

5. **Using `std::stack` to "cheat."** The exercise prohibits this. Use only queue.

6. **Inefficient rotation in C++.** `q.push(q.front()); q.pop();` is correct but a tight loop. For very large stacks, this is O(n) per push.

---

## 8. The shape — asymmetric trade-offs

> **Mini-refresher: when one direction is amortized O(1) and the reverse isn't.**
>
> Queue-from-Stacks: amortized O(1) for everything. ✓
> Stack-from-Queues: NOT amortized O(1) — one op must be O(n).
>
> The asymmetry comes from the structure of the data flow:
> - Stack-to-queue: pop from one stack and push onto another REVERSES order — exactly the FIFO need.
> - Queue-to-stack: there's no "natural reverse" you get from queue operations alone. You have to ROTATE explicitly.

The lesson: **not all conversions between data structures are equally cheap.** When the source's natural access pattern doesn't reverse into the target's, you pay a per-operation linear cost somewhere.

Where this matters in practice:
- Choosing data structures for a system based on access patterns.
- API design — exposing operations that allow O(1) implementation later.
- Translating between abstract interfaces (queue, stack, deque, priority queue).

**Pattern to internalize:**

> "Implement-X-using-Y" challenges reveal asymmetries between data structure access patterns. Memorize which direction is cheap and which isn't."

---

> **Self-check — the question to ask next time.**
>
> When you face an "implement X using Y" challenge, ask:
>
> > **"Does Y's natural operation order REVERSE into X's needs? If yes, two instances of Y with lazy transfer give amortized O(1). If no, one operation will be O(n)."**
>
> If yes, amortized O(1). If no, accept the linear cost on one operation.

---

## Cross-references

- **Reference card (post-mastery):** [`../Implement_Stack_using_Queues.md`](../Implement_Stack_using_Queues.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Queue_using_Stacks.md`](./Implement_Queue_using_Stacks.md) — the easier direction.
  - Coming next: [`Gas_Station.md`](./Gas_Station.md) — circular array greedy.
  - Coming after: [`Sliding_Window_Maximum.md`](./Sliding_Window_Maximum.md) — monotonic deque.
