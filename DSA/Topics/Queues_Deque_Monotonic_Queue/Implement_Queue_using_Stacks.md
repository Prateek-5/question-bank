# Implement Queue using Stacks

**Problem Link:**
<a href="https://leetcode.com/problems/implement-queue-using-stacks/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-queue-using-stacks/</a>

**Topic:**
Queues / Deque / Monotonic Queue

----------------------------------------

## Step 1: The Task

Implement the **queue** interface (push, pop, peek, empty) using only **stack** operations (push, pop, top, empty).

Stack is LIFO; queue is FIFO. So when we want to remove "the oldest" element from a queue, we have to reach into the "bottom" of a stack somehow.

----------------------------------------

## Step 2: Key Trick — Two Stacks Reverse the Order

If we push elements 1, 2, 3 onto stack A, they sit as [1, 2, 3] with 3 on top. Popping A one-by-one gives 3, 2, 1. If we push those pops onto stack B, B becomes [3, 2, 1] with 1 on top.

**Stack B now has the oldest element (1) at the top.** Popping B gives 1, 2, 3 — exactly queue order.

So the strategy: maintain two stacks, `inStack` (for pushes) and `outStack` (for pops). Whenever outStack is empty and we need to pop, transfer all of inStack to outStack (reversing order). The oldest element is now on top of outStack.

----------------------------------------

## Step 3: Algorithm

```
push(x):
    inStack.push(x)

pop():
    if outStack is empty:
        while inStack not empty:
            outStack.push(inStack.pop())
    return outStack.pop()

peek():
    if outStack is empty:
        while inStack not empty:
            outStack.push(inStack.pop())
    return outStack.top()

empty():
    return inStack is empty AND outStack is empty
```

----------------------------------------

## Step 4: Trace

```
push(1). inStack = [1]. outStack = [].
push(2). inStack = [1, 2].
push(3). inStack = [1, 2, 3].

peek(): outStack empty → transfer.
  Pop 3 from inStack, push to outStack. outStack = [3].
  Pop 2, push. outStack = [3, 2].
  Pop 1, push. outStack = [3, 2, 1].
  inStack = [], outStack = [3, 2, 1]. Top = 1.

pop() = 1. outStack = [3, 2].

push(4). inStack = [4]. (outStack untouched.)

pop(): outStack not empty. Pop top = 2. outStack = [3].

pop(): outStack not empty. Pop 3. outStack = [].

pop(): outStack empty → transfer from inStack = [4].
  Pop 4, push to outStack. outStack = [4]. inStack = [].
  Pop top = 4.
```

Sequence of pops: 1, 2, 3, 4. Exactly queue FIFO order. ✓

----------------------------------------

## Step 5: Amortized Complexity

Each element is pushed to inStack once, then moved to outStack once (via transfer), then popped once. That's 3 stack operations per element.

**Amortized O(1) per queue operation.** Even though a single pop can be O(n) (when it triggers a transfer of n elements), the total work over any sequence of k operations is O(k).

----------------------------------------

## Step 6: Why Two Stacks and Not One?

With one stack, we can either:
- Push in order and pop in reverse (LIFO natively — wrong).
- Rearrange on every op (O(n) per op).

Two stacks give us **amortized O(1)** because each transfer is free on average — we only transfer when outStack is empty, and each element takes part in at most one transfer.

If we tried to use one stack, we'd have to rearrange after every push (or every pop), giving O(n) per op, not amortized O(1).

----------------------------------------

## Step 7: Why Lazy Transfer (Not Eager)?

Eager version: after every push, immediately rearrange to keep outStack sorted for FIFO. That would force O(n) per push.

Lazy: transfer only when outStack is empty AND we need to pop. This lets multiple pushes accumulate without touching outStack. Over the lifetime of each element, only 3 constant-work operations — O(1) amortized.

----------------------------------------

## Step 8: Name It

**Amortized analysis via two-stack queue simulation.** A classical textbook example of amortization.

Related problems:
- Implement Stack using Queues (symmetric; harder to get O(1) amortized).
- Design Browser History (two stacks for forward/back).
- Implement Deque from stacks.
- Online algorithms where amortized complexity matters.

The two-stack pattern appears whenever you need to reverse the access order of a stream of data.

----------------------------------------

## Step 9: Complexity

- **push**: O(1) always.
- **pop**: O(1) amortized, O(n) worst-case.
- **peek**: same as pop.
- **empty**: O(1).
- **Space**: O(n) total across both stacks.

----------------------------------------

## Step 10: C++ Implementation

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

Transfer only when outSt is empty — that's the key to amortized O(1).

----------------------------------------

## Step 11: Follow-up Questions

- **Amortized vs. worst-case O(1).** Can we achieve O(1) worst-case? Yes, with more bookkeeping (incremental transfer), but code is much more complex.
- **Thread-safe queue from stacks.** Needs locks; concurrent modifications may require lock-free techniques.
- **Queue size in O(1).** Keep a running count: increment on push, decrement on pop.
- **Get the k-th oldest element.** Need additional structure (e.g., indexed access).
- **Priority queue from stacks.** Heap-like behavior is harder; usually pair with explicit ordering.
- **Why not simply use a std::queue?** The exercise is to build it from primitives — demonstrating data-structure abstraction.
