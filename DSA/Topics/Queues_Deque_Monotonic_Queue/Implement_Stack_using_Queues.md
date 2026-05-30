# Implement Stack using Queues

**Problem Link:**
<a href="https://leetcode.com/problems/implement-stack-using-queues/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-stack-using-queues/</a>

**Topic:**
Queues / Deque / Monotonic Queue

----------------------------------------

## Step 1: Understand the Contrast

A **stack** is LIFO: push on top, pop from top.
A **queue** is FIFO: enqueue at back, dequeue from front.

Task: implement a stack's interface (`push`, `pop`, `top`, `empty`) using only queue operations.

Queues only expose: `push(x)` at the back, `front()`, `pop()` from the front. We're forbidden from direct random-access or LIFO tricks.

----------------------------------------

## Step 2: Why This Is a Puzzle

The latest element pushed to a queue sits at the **back**, but stack's pop must return it. To access the back via queue operations, we have to dequeue from the front — losing those elements unless we re-enqueue them.

Two main strategies:
- **Costly push**: on every push, rearrange so the newest element is at the front.
- **Costly pop**: on every pop, dance all but the last element to the back.

Either way, one operation is O(n) and the other is O(1).

----------------------------------------

## Step 3: Strategy A — Costly Push

Use one queue `q`. On push(x):
1. Enqueue x at the back of q.
2. Dequeue and re-enqueue all earlier elements. (In effect, rotate x to the front.)

After push, front of q is always the most recently pushed element.

push is O(n). pop and top are O(1) — just operate on the front.

```
push(x):
    q.enqueue(x)
    for i in 0..size(q) - 2:
        q.enqueue(q.dequeue())   # rotate

pop():
    return q.dequeue()

top():
    return q.front()
```

Trace: push 1, 2, 3.
- After push(1): q = [1].
- After push(2): enqueue 2 → [1, 2]. Rotate 1 to back: dequeue 1, enqueue 1 → [2, 1].
- After push(3): enqueue 3 → [2, 1, 3]. Rotate 2 to back: dequeue 2, enqueue → [1, 3, 2]. Rotate 1 to back: dequeue 1, enqueue → [3, 2, 1].

Now front is 3. pop → 3 (stack's last-pushed). Then front is 2. pop → 2. ✓

----------------------------------------

## Step 4: Strategy B — Costly Pop (Two Queues)

Use two queues `q1` and `q2`. Push always goes to `q1`. On pop:
1. Dequeue all but the last element of `q1` into `q2`.
2. Dequeue the last element of `q1` → that's the answer.
3. Swap q1 and q2 (so q1 is the main again).

```
push(x):
    q1.enqueue(x)

pop():
    while size(q1) > 1:
        q2.enqueue(q1.dequeue())
    result = q1.dequeue()
    swap(q1, q2)
    return result
```

push is O(1). pop is O(n). top is also O(n) — similar dance, but re-enqueue the last element back to keep state.

----------------------------------------

## Step 5: Which Strategy to Use?

**One-queue, costly push** (Strategy A) is usually preferred:
- Cleaner code (no swap, single queue).
- pop / top are O(1), which matters in many use cases.

**Two-queue, costly pop** (Strategy B) has symmetric trade-offs but more state.

Interview answer often highlights Strategy A with the "rotate after push" explanation.

----------------------------------------

## Step 6: Trace Strategy A in Detail — Mixed Operations

```
push(1): q = [1]. No rotation needed (size = 1).
push(2): q = [1, 2]. Rotate: dequeue 1, enqueue 1. q = [2, 1].
top() = 2. ✓
pop() = 2. q = [1]. ✓
push(3): q = [1, 3]. Rotate: dequeue 1, enqueue 1. q = [3, 1].
push(4): q = [3, 1, 4]. Rotate 2 times: dequeue 3, enqueue 3 → [1, 4, 3]; dequeue 1, enqueue 1 → [4, 3, 1].
top() = 4. ✓
pop() = 4. q = [3, 1].
top() = 3. ✓
```

Matches stack behavior exactly.

----------------------------------------

## Step 7: Why the Rotation Works

The invariant we maintain: after every push, the queue is in **stack order** — the most recently pushed element is at the front, the earliest at the back.

When we enqueue a new x, it goes to the back. To restore the invariant, we rotate every earlier element from front to back — their relative order is preserved, but x now occupies the front.

Think of it as "inserting at the front" by simulating with only tail-enqueue.

----------------------------------------

## Step 8: Name It

**Data structure simulation via operation reassignment.** A classic exercise in API transformation. Forces you to think about what operations a structure actually exposes and how to build richer behavior from them.

Related puzzles:
- Implement Queue using Stacks (symmetric — the Queue topic has this).
- Implement Min Stack (add getMin in O(1) to a stack).
- Implement LRU cache.
- Implement Deque from stack.

The conversion between stack and queue reveals the equivalence of FIFO and LIFO with enough operations.

----------------------------------------

## Step 9: Complexity

**Strategy A (one queue, costly push):**
- push: O(n).
- pop, top, empty: O(1).

**Strategy B (two queues, costly pop):**
- push: O(1).
- pop, top: O(n).
- empty: O(1).

Space: O(n) for the elements in the queue(s).

----------------------------------------

## Step 10: C++ Implementation (Strategy A)

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

Push rotates the queue so the new element is at front. Other operations trivially read/pop the front.

----------------------------------------

## Step 11: Follow-up Questions

- **Implement a queue using a single stack.** Harder (can't be done with single stack and O(1) amortized); two stacks give O(1) amortized (the symmetric problem).
- **Amortized complexity of Strategy A.** Push is O(n) worst-case. But if we never push more than once between pops, amortized can't be smaller here — each element must be "lifted" over all older ones.
- **Constant-time push AND pop via queues.** Provably impossible with just queue ops — some operation must be O(n).
- **Using a deque instead of a queue.** Deque exposes both ends; then stack is trivial (use only one end).
- **Thread safety?** Not addressed here; would need locking around the rotation.
- **Why not just keep two queues and transfer on every op?** That's Strategy B; it's correct but slower on pop.
