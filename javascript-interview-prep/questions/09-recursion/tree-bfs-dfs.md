# Tree traversal — BFS and DFS, recursive + iterative

## Source
- Canonical interview problem; appears as preorder/inorder/postorder/levelOrder traversals on every coding site.
- LeetCode #102 (level order BFS), #144/#94/#145 (DFS preorder/inorder/postorder).
- codedamn "Tree traversal" articles and labs.

## Why this question matters in interviews
Tree traversal is the **most-asked recursion problem**. In one question the interviewer probes: (1) **DFS vs BFS** — when each is appropriate, (2) **recursive vs iterative** DFS — and whether you can convert between them with an explicit stack, (3) **queue choice** for BFS — and whether you know `Array#shift` is O(n) so a million-node BFS with a naive array is O(n²), (4) **cycle handling** — `visited` Set for graphs (trees don't have cycles, but interviewers love sliding into "what if it's a graph?"). As a backend engineer: walking dependency graphs in build tools, traversing recursive S3 prefixes, level-order processing of org-chart hierarchies, shortest-path checks.

## Concepts involved

### Syntax to lock in
```js
// Tree node shape used throughout
const node = {
  value: 1,
  children: [
    { value: 2, children: [{ value: 4, children: [] }] },
    { value: 3, children: [] },
  ],
};

// DFS recursive (preorder)
function dfs(node, visit) {
  if (!node) return;
  visit(node);                      // visit BEFORE children = preorder
  for (const child of node.children) dfs(child, visit);
}

// DFS iterative
function dfsIter(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    // Reverse children when pushing so popping yields left-to-right
    for (let i = n.children.length - 1; i >= 0; i--) stack.push(n.children[i]);
  }
}

// BFS iterative
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  let head = 0;                     // index-pointer to avoid O(n) shift
  while (head < queue.length) {
    const n = queue[head++];
    visit(n);
    for (const c of n.children) queue.push(c);
  }
}
```

### Runtime / engine behavior
- **DFS recursive** uses the JS call stack. One frame per node along the current path. Depth = tree height. **V8 has no TCO** — a 50,000-deep skewed tree stack-overflows.
- **DFS iterative** uses a heap-allocated array as stack. Same O(h) memory but on the heap, which is much larger.
- **BFS** uses a queue. The classic mistake: `queue.shift()` is **O(n)** because V8 has to compact the array. For 1M nodes that's O(n²) total. Use one of:
  - **Index pointer**: `head` cursor + `queue[head++]`; memory grows but reads are O(1).
  - **Two-stack queue** (Okasaki): push to one stack, pop from the other; amortized O(1).
  - **Linked-list queue**: explicit head/tail; truly O(1) per op.
- **Visit ordering**:
  - Preorder = visit before children. Postorder = visit after. Inorder is only meaningful for binary trees.
  - DFS iterative naturally yields preorder. For postorder iteratively you typically use 2-stack trick or a "visited" flag per frame.
- **Cycles**: trees have none by definition. The moment the structure can have shared references (a graph), you need a `visited: WeakSet` keyed by node identity. Without it, BFS/DFS hang on cycles.
- **BFS guarantees shortest-edge-count path** from root (if edges have equal weight). DFS does not.

### Edge cases (interview traps)
1. **Null root** — `dfs(null)` / `bfs(null)` should no-op, not throw.
2. **Missing `children`** — defend with `node.children || []` or normalize the input.
3. **Cycles in a graph version** — `visited.has(node)` check using a `Set` (or `WeakSet`) before enqueuing/pushing.
4. **`Array#shift` performance** — interviewers will ask "why is your BFS slow on 100k nodes?" Answer: shift is O(n).
5. **Iterative postorder** — surprisingly tricky. Trick: do "reverse preorder" (push children left-to-right, prepend each visit to output), then reverse at the end.
6. **Stack overflow** — recursive DFS on a deeply skewed tree. Switch to iterative.
7. **Order of children** — iterative DFS with `pop()` reverses the order unless you push reverse. Test with `[1, [2, 3]]` to verify.
8. **Visit side effects modifying the tree** — usually out of scope, but mention if asked.

## Brute force approach
For most "find a node / collect all values" tasks the brute force IS the answer — a single traversal. The "wrong default" trap is using `Array#shift` for BFS without realizing the cost. Or writing recursive DFS without acknowledging stack depth risk. Or forgetting `visited` when the structure could be a graph.

## Optimal approach
- Tree DFS preorder: recursive for clarity; iterative with explicit stack for safety.
- Tree BFS: queue with index pointer (or proper FIFO).
- Graph traversal: same shape + `visited` Set keyed by node identity.

All are O(n) time and O(n) memory in the worst case.

## Solution (JavaScript)

```js
// ---------- DFS (recursive) ----------
/**
 * Preorder DFS. Visit BEFORE recursing into children.
 */
function dfsRecursive(node, visit) {
  if (!node) return;                     // base case
  visit(node);                            // preorder
  for (const child of node.children || []) {
    dfsRecursive(child, visit);          // recursive case
  }
}

// Postorder variant — visit AFTER children
function dfsPostorder(node, visit) {
  if (!node) return;
  for (const child of node.children || []) dfsPostorder(child, visit);
  visit(node);
}

// ---------- DFS (iterative, explicit stack) ----------
/**
 * Iterative preorder DFS. Heap-allocated stack — safe for deeply skewed trees.
 */
function dfsIterative(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    visit(node);
    // Push children in REVERSE so pop() yields them left-to-right
    const kids = node.children || [];
    for (let i = kids.length - 1; i >= 0; i--) stack.push(kids[i]);
  }
}

// ---------- BFS (queue with index pointer) ----------
/**
 * Level-order BFS. Uses an index pointer instead of Array#shift to keep dequeue O(1).
 */
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  let head = 0;                          // dequeue cursor
  while (head < queue.length) {
    const node = queue[head++];
    visit(node);
    for (const child of node.children || []) queue.push(child);
  }
}

// BFS with explicit level boundaries (useful for "print each level on a line")
function bfsByLevel(root) {
  if (!root) return [];
  const levels = [];
  let current = [root];
  while (current.length) {
    const next = [];
    const values = [];
    for (const node of current) {
      values.push(node.value);
      for (const child of node.children || []) next.push(child);
    }
    levels.push(values);
    current = next;
  }
  return levels;
}

// ---------- Graph traversal (with cycle handling) ----------
/**
 * DFS over a graph. WeakSet of visited node identities prevents infinite loops.
 */
function graphDfs(start, visit) {
  if (!start) return;
  const visited = new WeakSet();
  const stack = [start];
  while (stack.length) {
    const node = stack.pop();
    if (visited.has(node)) continue;     // already seen → skip
    visited.add(node);
    visit(node);
    const neighbors = node.neighbors || node.children || [];
    for (let i = neighbors.length - 1; i >= 0; i--) {
      if (!visited.has(neighbors[i])) stack.push(neighbors[i]);
    }
  }
}

function graphBfs(start, visit) {
  if (!start) return;
  const visited = new WeakSet([start]);
  const queue = [start];
  let head = 0;
  while (head < queue.length) {
    const node = queue[head++];
    visit(node);
    for (const n of node.neighbors || node.children || []) {
      if (!visited.has(n)) {
        visited.add(n);                  // mark when ENQUEUED, not when visited
        queue.push(n);
      }
    }
  }
}
```

## Step-by-step dry run

Tree:
```
        1
       / \
      2   3
     / \
    4   5
```
Encoded:
```js
const root = {
  value: 1,
  children: [
    { value: 2, children: [
        { value: 4, children: [] },
        { value: 5, children: [] },
    ]},
    { value: 3, children: [] },
  ],
};
```

**DFS recursive (preorder)** — visit order: 1, 2, 4, 5, 3.
- Visit 1, recurse into children [2, 3].
  - Visit 2, recurse into [4, 5].
    - Visit 4, no children.
    - Visit 5, no children.
  - Visit 3, no children.

**DFS iterative** — stack trace:
- stack=[1]. Pop 1, visit. Push children reversed → stack=[3, 2].
- Pop 2, visit. Push [4, 5] reversed → stack=[3, 5, 4].
- Pop 4, visit. No children → stack=[3, 5].
- Pop 5, visit. → stack=[3].
- Pop 3, visit. → stack=[].
- Visit order: 1, 2, 4, 5, 3. **Matches recursive preorder.**

**BFS** — queue trace (head pointer in brackets):
- queue=[1] head=0. Read 1, visit. Push children → queue=[1, 2, 3] head=1.
- Read 2, visit. Push [4, 5] → queue=[1, 2, 3, 4, 5] head=2.
- Read 3, visit. No children → head=3.
- Read 4 → head=4. Read 5 → head=5. head === length, stop.
- Visit order: 1, 2, 3, 4, 5. **Level-order, as promised.**

**Performance note**: if we'd used `queue.shift()` instead of the head pointer, each shift would re-index the remaining array. On 1M nodes that's ~500B array moves total. The index pointer keeps it O(n).

## Important takeaways

**Syntax to memorize**
- DFS recursive base case: `if (!node) return;`. Recursive case: loop over `node.children`.
- DFS iterative: `const stack = [root]; while (stack.length) { const n = stack.pop(); ... push children REVERSED; }`.
- BFS: `const queue = [root]; let head = 0; while (head < queue.length) { ...queue[head++]... queue.push(child); }`. **Never** `queue.shift()` in tight loops.
- Graph: add `visited` Set; mark **when enqueuing** in BFS (prevents double-enqueue), mark **when popping** is also valid for DFS but slightly less efficient.

**Patterns to reuse**
- Stack-of-frames as recursive-to-iterative converter — same recipe as flatten, deep clone, JSON serializer.
- Index-pointer queue (or two-stack queue) is the standard fix for `Array#shift` cost. Use everywhere you need a FIFO.
- "Mark on enqueue" vs "mark on dequeue" — pick mark-on-enqueue for BFS (cheaper, simpler proof of correctness).
- Level-by-level processing (`bfsByLevel`) is the same loop with a snapshot of the current frontier — reuse for "print each level", "find depth of node X", "rightmost element at each level".

**Common mistakes**
- `queue.shift()` for BFS — O(n) per call, O(n²) overall. Always mention this.
- Recursive DFS on a deeply skewed tree without acknowledging stack overflow risk. V8 has no TCO; offer the iterative variant when input depth is unbounded.
- Iterative DFS pushing children in forward order → output reversed sibling order. Push reversed.
- Marking `visited` on dequeue in BFS — node gets enqueued multiple times from different parents → memory waste. Mark on enqueue.
- Forgetting `visited` when the structure has cycles (graph not tree) → infinite loop.
- Using `instanceof TreeNode` checks across realms or for plain objects — just check shape (`node && Array.isArray(node.children)`).

**Related questions**
- Inorder traversal of a binary tree (left, root, right) — only meaningful for binary trees; uses `node.left` / `node.right`.
- Iterative inorder using a stack and a "current" pointer (LeetCode #94).
- Lowest common ancestor — typically post-order DFS that returns the LCA up the recursion.
- Shortest path in an unweighted graph — BFS with parent map and reconstruction.
- Topological sort — DFS post-order on a DAG, reverse output.

## Variants

1. **Async DFS / BFS** — `children` returned by `await node.getChildren()`. Drives a `for ... of` with `await`. Sequential by default; can be parallelized with `Promise.all`.

2. **Bidirectional BFS** — search from both ends, meet in the middle. Halves the explored frontier.

3. **DFS with depth limit** — `dfs(node, depth)` that returns when `depth === 0`. Same skeleton as `flat(arr, depth)`.

4. **Iterative postorder** — two-stack trick: push to stack1, pop and push to stack2 along with children; finally pop stack2. Or use a `visited` flag per frame.

5. **Generator-based traversal** — `function* dfs(node) { yield node; for (const c of node.children) yield* dfs(c); }`. Lazy, drives via `for ... of`. Pair with `break` for early termination.

6. **Parent pointers / path reconstruction** — keep a `parent` map during BFS so you can walk back from any visited node to the root.

## Revision notes

> **Tree BFS / DFS — 60 second recap**
> - **DFS recursive**: base `if (!node) return`, visit + recurse on children. Stack depth = tree height. **V8 no TCO** → deeply skewed tree overflows.
> - **DFS iterative**: explicit stack, push children REVERSED so pop yields left-to-right.
> - **BFS**: queue with **index pointer**, NOT `Array#shift` (which is O(n)).
> - **Graph**: add `visited` Set/WeakSet; mark **on enqueue** (BFS) to prevent double-enqueue.
> - **Preorder** = visit before children, **postorder** = after, **level-order** = BFS.
> - O(n) time, O(n) memory worst case. DFS recursive O(h) call stack; iterative O(h) heap.
> - **Traps:** `shift()` O(n) cost; recursion stack overflow on skewed trees; missing `visited` on cyclic graphs; pushing children in wrong order in iterative DFS.
