# Converting Recursive → Iterative (Explicit Stack)

## Source / Origin
- Standard CS interview drill.
- Asked at: every senior interview where recursion comes up.
- Concept reference: `concepts/recursion.md`, sibling `trampoline-pattern.md`.

## Why this question matters in interviews
Recursive code is clean but blows the stack at scale; iterative code is awkward but unbounded. Senior bar: you can mechanically convert any recursion to iteration via an explicit stack (LIFO) or queue (FIFO), handle pre/in/post order traversal, and reason about when conversion is worth it.

## Concepts involved

### Syntax to lock in
```js
// Recursive tree pre-order
function preorderRec(root, out = []) {
  if (!root) return out;
  out.push(root.value);
  preorderRec(root.left, out);
  preorderRec(root.right, out);
  return out;
}

// Iterative pre-order
function preorderIter(root) {
  const out = [];
  if (!root) return out;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    out.push(node.value);
    if (node.right) stack.push(node.right);   // push right first so left pops first
    if (node.left)  stack.push(node.left);
  }
  return out;
}
```

### Conversion recipes
| Recursion shape | Iterative shape |
|---|---|
| Tail recursion | `while` loop with state update |
| Pre-order traversal | Stack: push children right-then-left |
| In-order traversal | Stack + "go left, pop, visit, go right" |
| Post-order traversal | Two stacks OR mark-visited flag |
| Backtracking | Stack of partial solutions |
| Divide-and-conquer | Stack of (lo, hi) intervals |
| BFS | Queue (FIFO) instead of stack |

### Edge cases / traps
1. **Order of pushes.** Stack is LIFO — push right first if you want left visited first.
2. **Post-order is trickiest.** Two common patterns: (a) two stacks; (b) mark "visited" bit on each frame.
3. **Backtracking** needs to *undo* state when popping; track the action per stack frame.
4. **Mutual recursion** — combine into one stack with frame discriminator (which "function" should run).
5. **Local variables** become explicit stack-frame objects.
6. **Tail-call optimization** — if you can find a tail position, `while`-loop is cleanest.
7. **Performance** — iteration is ~10-30% faster than recursion in V8 (avoiding call overhead).
8. **Memory** — same big-O; explicit stack on heap instead of call stack.

## Mental Model

The call stack is a stack of stack frames; conversion makes that explicit:

```
   recursive:  call stack is the data structure
   iterative:  array-as-stack is the data structure (on the heap)

   recursive frame                    iterative frame object
   ┌────────────────────────┐         ┌──────────────────────┐
   │ params: node           │         │ {node, phase, locals}│
   │ locals: i              │         │                      │
   │ return PC (where to    │         │ phase: 0=before-left │
   │  resume after callee)  │         │        1=after-left  │
   └────────────────────────┘         │        2=after-right │
                                      └──────────────────────┘
```

## Why interviewers care

- **Mechanical skill** — should be muscle memory for senior.
- **Stack overflow awareness** — iterative scales.
- **State-machine thinking** — frames as records, phase as PC.

## Common confusion

- **"Recursion is always cleaner."** Often is, but for very deep trees or chosen-by-interviewer "convert to iterative," you need the recipe.
- **"Iteration uses less memory."** Same big-O; the explicit stack just lives on the heap.
- **"Tail recursion is automatic in V8."** Nope — see `trampoline-pattern.md`.
- **"BFS uses a stack."** No — queue (FIFO).

## Brute force

Just go iterative from scratch. Hard if the recursion is non-trivial; mechanical conversion is the reliable path.

## Optimal approach

Identify the recursion shape (tail/pre/in/post/divide-conquer). Apply the corresponding stack/queue recipe. For complex local state, use frame objects with a phase field.

## Solution

```js
// In-order traversal (iterative)
function inorderIter(root) {
  const out = [], stack = [];
  let curr = root;
  while (curr || stack.length) {
    while (curr) { stack.push(curr); curr = curr.left; }
    curr = stack.pop();
    out.push(curr.value);
    curr = curr.right;
  }
  return out;
}

// Post-order — phase flag pattern
function postorderIter(root) {
  if (!root) return [];
  const out = [];
  const stack = [{ node: root, phase: 0 }];
  while (stack.length) {
    const top = stack[stack.length - 1];
    if (top.phase === 0) {
      top.phase = 1;
      if (top.node.left) stack.push({ node: top.node.left, phase: 0 });
    } else if (top.phase === 1) {
      top.phase = 2;
      if (top.node.right) stack.push({ node: top.node.right, phase: 0 });
    } else {
      out.push(top.node.value);
      stack.pop();
    }
  }
  return out;
}

// Backtracking — generate permutations iteratively
function permutationsIter(arr) {
  const out = [];
  const stack = [{ current: [], remaining: arr.slice() }];
  while (stack.length) {
    const { current, remaining } = stack.pop();
    if (!remaining.length) { out.push(current); continue; }
    for (let i = 0; i < remaining.length; i++) {
      const next = remaining.slice(0, i).concat(remaining.slice(i + 1));
      stack.push({ current: [...current, remaining[i]], remaining: next });
    }
  }
  return out;
}

// Quicksort iterative (divide-conquer with interval stack)
function quicksortIter(arr) {
  const stack = [[0, arr.length - 1]];
  while (stack.length) {
    const [lo, hi] = stack.pop();
    if (lo >= hi) continue;
    const p = partition(arr, lo, hi);
    stack.push([lo, p - 1]);
    stack.push([p + 1, hi]);
  }
  return arr;
}
```

## Dry run

Pre-order of tree A(B(D,E),C):

```
recursive:
  pre(A) → push A, pre(B) → push B, pre(D) → push D, pre(E) → push E, pre(C) → push C
  out: [A, B, D, E, C]

iterative:
  stack=[A]; pop A → out=[A]; push C, push B → stack=[C, B]
  pop B → out=[A,B]; push E, push D → stack=[C, E, D]
  pop D → out=[A,B,D]; no children
  pop E → out=[A,B,D,E]; no children
  pop C → out=[A,B,D,E,C]; no children
  done
```

## How to think aloud

> "I'd identify the recursion shape — pre/in/post/tail/divide-conquer/backtracking. Each maps to a stack pattern. Pre-order: stack, push children right-then-left. In-order: while curr or stack, drill left, pop, visit, go right. Post-order: phase-flag pattern (0=before-left, 1=after-left, 2=after-right). Tail recursion: just a `while` loop. Backtracking: stack of partial solutions, each frame has its own state. Performance same big-O; slightly faster in practice since no call overhead. Use iteration for very deep recursion or when interviewer asks."

## Important takeaways

- **Stack for DFS-shape, queue for BFS.**
- **Pre-order**: push right then left.
- **In-order**: drill left, pop, visit, drill right.
- **Post-order**: phase flag (0→1→2) or two stacks.
- **Backtracking**: stack of partial-solution frames.
- **Divide-conquer**: stack of intervals.
- **Tail recursion**: pure `while` loop.

## Variants

- **BFS via queue** — `Array.shift()` is O(n); use a real ring buffer or 2-stack queue.
- **Generators** for pause/resume traversal: `function* preorder(node) { yield node; yield* preorder(left); ... }`.
- **Async traversal** with `for await` over an async generator.
- **Continuations** (heavyweight; uncommon in JS).

## Revision notes

```
Conversion recipes:
  tail recursion → while-loop
  pre-order      → stack, push right then left
  in-order       → while (curr || stack): drill left, pop, visit, go right
  post-order     → phase flag {0,1,2} or 2-stack
  BFS            → queue (FIFO)
  divide+conquer → stack of intervals (lo, hi)
  backtracking   → stack of partial-solution frames

WHY:
  - recursion blows stack at scale (no TCO in V8)
  - same big-O memory, heap vs call stack
  - iteration ~10-30% faster (no call overhead)

ALWAYS: state per frame becomes an object on the stack
```
