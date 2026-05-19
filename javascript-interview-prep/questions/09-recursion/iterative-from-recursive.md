# Converting recursive → iterative (explicit stack)

> **Difficulty:** Medium-Senior   |   **Time:** ~12 min   |   **Prereqs:** [trampoline-pattern.md](./trampoline-pattern.md), [tree-bfs-dfs.md](./tree-bfs-dfs.md)
>
> **Source:** Standard CS interview drill.

---

## 1. Problem statement

Mechanically convert recursion to iteration via explicit stack/queue. Handle pre/in/post-order.

**Verification examples**

```js
// Recursive preorder
function preorderRec(root, out = []) {
  if (!root) return out;
  out.push(root.value);
  preorderRec(root.left, out);
  preorderRec(root.right, out);
  return out;
}

// Iterative preorder
function preorderIter(root) {
  if (!root) return [];
  const out = [];
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    out.push(node.value);
    if (node.right) stack.push(node.right);    // reverse — left pops first
    if (node.left)  stack.push(node.left);
  }
  return out;
}
```

**Constraints**
- Stack (LIFO) for DFS.
- Queue (FIFO) for BFS.
- Push reverse for natural order.
- Post-order trickier — two-stack or "visited" flag.

---

## 2. Plain-English restatement

Replace call stack with explicit array stack. Push frames (= subproblems) in reverse so pop order = recursion order.

---

## 3. Why this matters in interviews

Senior bar: mechanical conversion, all traversal orders, reason about when worth it (deep input).

---

## 4. Mental model

```
   Conversion table:
     Recursion shape         | Iterative shape
     -----------------------+-----------------------
     tail recursion          | while loop
     linear recursion (one)  | while + accumulator
     bifurcating (two)       | explicit stack (DFS) or queue (BFS)
     pre-order DFS           | stack, push reverse
     post-order DFS          | two stacks OR "visited" flag
     in-order DFS (binary)   | "leftmost-first" stack pattern
     level-order BFS         | queue
   
   Why iterative?
     V8 doesn't TCO → recursive blows at deep input.
     Iterative uses heap stack (much bigger than call stack).
     Sometimes also slightly faster (no function-call overhead).
   
   Trampoline alternative: pure tail-recursive style with thunks.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why push children in REVERSE?
> 2. Difference between two-stack post-order and visited-flag?
> 3. When is iterative slower than recursive?

---

## 6. Brute force — walked through

Recursive elegant; just blows on deep. Conversion is mechanical.

---

## 7. The unlocking insight

> **Stack for DFS, queue for BFS. Push reverse for natural order. Post-order needs two-stack or visited flag.**

Three properties:

1. **Stack (LIFO)** = recursion frames.
2. **Push reverse** for original order.
3. **Post-order tricky** — two-stack idiom.

---

## 8. Solution (annotated)

```js
// Pre-order: visit, then children. Iterative.
function preorderIter(root) {
  if (!root) return [];
  const out = [];
  const stack = [root];                                                    // step 1: explicit stack
  while (stack.length) {
    const node = stack.pop();
    out.push(node.value);                                                  // step 2: visit
    if (node.right) stack.push(node.right);                                // step 3: push REVERSE
    if (node.left)  stack.push(node.left);
  }
  return out;
}

// In-order (binary tree): leftmost-first
function inorderIter(root) {
  const out = [];
  const stack = [];
  let curr = root;
  while (curr || stack.length) {
    while (curr) {                                                          // step 4: dive left
      stack.push(curr);
      curr = curr.left;
    }
    curr = stack.pop();
    out.push(curr.value);                                                  // step 5: visit
    curr = curr.right;                                                      // step 6: now right
  }
  return out;
}

// Post-order: two stacks (cleanest)
function postorderIter(root) {
  if (!root) return [];
  const stack = [root];
  const out = [];
  while (stack.length) {
    const node = stack.pop();
    out.push(node.value);                                                  // step 7: visit later reversed
    if (node.left)  stack.push(node.left);                                 // step 8: forward push
    if (node.right) stack.push(node.right);
  }
  return out.reverse();                                                    // step 9: reverse for post-order
}

// BFS — queue
function bfs(root) {
  if (!root) return [];
  const out = [];
  const queue = [root];                                                    // step 10: queue not stack
  while (queue.length) {
    const node = queue.shift();   // O(n) — use circular buffer for big trees
    out.push(node.value);
    for (const child of node.children ?? []) queue.push(child);
  }
  return out;
}

// Generic — recursive flatten → iterative
function flattenIterative(arr) {
  const out = [];
  const stack = [];
  for (let i = arr.length - 1; i >= 0; i--) stack.push(arr[i]);
  while (stack.length) {
    const item = stack.pop();
    if (Array.isArray(item)) {
      for (let i = item.length - 1; i >= 0; i--) stack.push(item[i]);
    } else {
      out.push(item);
    }
  }
  return out;
}
```

**Try it yourself**

```js
const root = {
  value: 1,
  left: { value: 2, left: { value: 4 }, right: { value: 5 } },
  right: { value: 3 },
};

preorderIter(root);                                           // [1, 2, 4, 5, 3]
inorderIter(root);                                            // [4, 2, 5, 1, 3]
postorderIter(root);                                          // [4, 5, 2, 3, 1]

bfs(root);                                                     // [1, 2, 3, 4, 5] (if children-array)

// Deep tree safety
const deep = { value: 0 };
let cur = deep;
for (let i = 1; i < 100_000; i++) {
  cur.left = { value: i }; cur = cur.left;
}
// preorderRec(deep);   // RangeError
preorderIter(deep);     // OK (heap stack)

// Visit-flag post-order
function postorderVisited(root) {
  if (!root) return [];
  const out = [];
  const stack = [[root, false]];
  while (stack.length) {
    const [node, visited] = stack.pop();
    if (visited) { out.push(node.value); continue; }
    stack.push([node, true]);
    if (node.right) stack.push([node.right, false]);
    if (node.left)  stack.push([node.left, false]);
  }
  return out;
}
```

---

## 9. Step-by-step dry run

```
preorderIter for tree(1, 2, 3, 4, 5):
  Tree:
        1
       / \
      2   3
     / \
    4   5
  
  stack = [1].
  Pop 1: visit 1. Push 3, then 2 (reverse). stack=[3, 2].
  Pop 2: visit 2. Push 5, then 4 (reverse). stack=[3, 5, 4].
  Pop 4: visit 4. (no children).
  Pop 5: visit 5.
  Pop 3: visit 3.
  out = [1, 2, 4, 5, 3]. ✓ matches recursive.

postorderIter (two-stack):
  stack = [1].
  Pop 1: out.push(1). out=[1]. Push left (2), right (3). stack=[2, 3].
  Pop 3: out=[1,3]. (no children).
  Pop 2: out=[1,3,2]. Push 4, 5. stack=[4, 5].
  Pop 5: out=[1,3,2,5].
  Pop 4: out=[1,3,2,5,4].
  Reverse: [4, 5, 2, 3, 1]. ✓ post-order.

inorderIter:
  curr=1, stack=[].
  Inner: dive left → stack=[1, 2, 4]. curr=4.left=null → exit.
  Pop 4: out=[4]. curr=4.right=null.
  Outer: curr=null && stack=[1, 2].
  Pop 2: out=[4, 2]. curr=2.right=5.
  Inner: dive left → stack=[1, 5]. curr=5.left=null.
  Pop 5: out=[4, 2, 5]. curr=null.
  Pop 1: out=[4, 2, 5, 1]. curr=1.right=3.
  Inner: dive → stack=[3]. curr=null.
  Pop 3: out=[4, 2, 5, 1, 3]. curr=null. Stack empty. Exit.
```

---

## 10. Common confusion + traps

1. **Push children forward** — reverses order.
2. **`Array.shift()` for queue** — O(n); large BFS becomes O(n²).
3. **In-order on non-binary** — needs different shape.
4. **Post-order without reverse** — wrong order.
5. **Mix stack/queue** — confused order.
6. **Iterative not always faster** — heap stack alloc + manual frame mgmt.
7. **Generator alternative** — `yield*` for clean style with stack safety still iffy.

---

## 11. Senior follow-ups & variants

### Variant 1 — BFS queue with circular buffer
For million-node trees.

### Variant 2 — Morris traversal
O(1) extra space; mutates pointers temporarily.

### Variant 3 — Generator + iterative
`function*` + explicit stack.

### Variant 4 — Trampoline alternative
Thunk-returning for tail recursion.

### Variant 5 — CPS (continuation-passing)
Convert via continuations.

---

## 12. How to think aloud

> "Mechanical conversion of recursion to iteration via explicit stack. DFS uses stack (LIFO), BFS uses queue (FIFO). Pre-order: push root, pop and visit, push children in REVERSE order (right then left) so left pops first. In-order on binary: dive left repeatedly pushing onto stack, pop and visit, then go right (recursive structure 'visit left subtree, visit self, visit right subtree' maps to this). Post-order: two cleanest patterns — (1) two-stack: push root, pop and PUSH TO OUTPUT, push left then right (FORWARD this time), then reverse output at end; (2) visited-flag: stack of `[node, visited]` pairs, first encounter pushes with visited=true and re-pushes children, second encounter visits. BFS: queue, but `Array.shift()` is O(n) — for million-node trees use circular buffer or linked list. Why iterative: V8 doesn't TCO, so recursive blows at deep input (~10-15k frames); iterative uses heap stack (millions of entries OK). Sometimes also faster (no function-call overhead per node), sometimes slower (manual frame management overhead). Variants: Morris traversal (O(1) extra, mutates pointers temporarily — academic); generator wrapper; trampoline for tail recursion. Trap: push children forward (reverses order); Array.shift for big BFS (O(n²) total); post-order without reverse."

---

## 13. 60-second revision

> - **DFS: stack (LIFO).** BFS: queue (FIFO).
> - **Push children REVERSE** for original order.
> - **Pre-order:** push, pop, visit, push reverse.
> - **In-order (binary):** dive left, pop visit, go right.
> - **Post-order:** two-stack + reverse OR visited-flag.
> - **`Array.shift` O(n)** — circular buffer for big BFS.
> - **Why iterative:** V8 no TCO; heap stack safer.
> - **Morris** = O(1) space (mutate pointers).
> - **Trap:** forward children push; shift O(n); post-order order.

---

**Related:** [trampoline-pattern.md](./trampoline-pattern.md) · [tree-bfs-dfs.md](./tree-bfs-dfs.md) · [flatten-deeply-nested-array.md](./flatten-deeply-nested-array.md) · [backtracking-template.md](./backtracking-template.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
