# Tree traversal — BFS and DFS

> **Difficulty:** Foundation-Medium   |   **Time:** ~15 min   |   **Prereqs:** [iterative-from-recursive.md](./iterative-from-recursive.md), [directory-walk-async.md](./directory-walk-async.md)
>
> **Source:** LeetCode #102, #144, #94, #145.

---

## 1. Problem statement

DFS (pre/in/post-order) recursive + iterative. BFS level-order. Handle cycles via visited Set for graphs.

**Verification examples**

```js
// DFS recursive preorder
function dfs(node, visit) {
  if (!node) return;
  visit(node);
  for (const child of node.children) dfs(child, visit);
}

// DFS iterative
function dfsIter(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    for (let i = n.children.length - 1; i >= 0; i--) stack.push(n.children[i]);
  }
}

// BFS
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  while (queue.length) {
    const n = queue.shift();   // O(n) — circular buffer for big trees
    visit(n);
    for (const c of n.children) queue.push(c);
  }
}
```

**Constraints**
- DFS: stack; BFS: queue.
- Visit order: pre/in/post.
- `Array.shift` O(n) — use circular buffer for big BFS.
- Graphs: `visited` Set to break cycles.

---

## 2. Plain-English restatement

DFS goes deep first; BFS goes wide. Pick by problem: "shortest path / level k" → BFS; "explore one branch fully" → DFS.

---

## 3. Why this matters in interviews

Most-asked recursion problem. Tests: DFS vs BFS, recursive vs iterative, queue choice, cycle handling.

---

## 4. Mental model

```
   DFS (depth-first):
     Recursive: clean; stack depth = tree height.
     Iterative: explicit stack; push children reverse for natural order.
     Orders:
       Preorder:  visit, then children (recurse).
       Inorder:   binary only — left, visit, right.
       Postorder: children first, then visit.
   
   BFS (breadth-first):
     Queue; level-by-level.
     For level-grouped: track size of queue per level.
   
   `Array.shift()` is O(n) — for million-node BFS, use circular buffer.
   
   Cycle handling:
     Trees: no cycles, no visited.
     Graphs: visited Set; check before push.
   
   Use cases:
     Shortest path in unweighted: BFS.
     Connected components: DFS or BFS.
     Topological sort: DFS post-order or Kahn's BFS.
     Cycle detection: DFS with white/gray/black coloring.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. DFS vs BFS — which for shortest path?
> 2. Why `Array.shift` slow for BFS?
> 3. How handle cycles in graph BFS?

---

## 6. Brute force — walked through

```js
// Recursive BFS — wrong shape; BFS needs queue
function badBfs(node, visit) {
  visit(node);
  for (const c of node.children) badBfs(c, visit);   // depth-first, not BFS
}
```

That's DFS preorder, not BFS.

---

## 7. The unlocking insight

> **DFS = stack (or recursion); BFS = queue. Push reverse for natural DFS order. Use circular buffer for big BFS. Visited Set for graph cycles.**

Three properties:

1. **Stack DFS; queue BFS.**
2. **Reverse-push children** for natural order.
3. **Visited Set** for graphs.

---

## 8. Solution (annotated)

```js
// Tree node
const root = {
  value: 1,
  children: [
    { value: 2, children: [{ value: 4 }, { value: 5 }] },
    { value: 3, children: [] },
  ],
};

// DFS recursive preorder
function dfsPreorder(node, visit) {
  if (!node) return;
  visit(node);                                                              // step 1: pre
  for (const child of node.children) dfsPreorder(child, visit);
}

// DFS iterative
function dfsIter(root, visit) {
  if (!root) return;
  const stack = [root];
  while (stack.length) {
    const n = stack.pop();
    visit(n);
    for (let i = n.children.length - 1; i >= 0; i--) {                     // step 2: reverse
      stack.push(n.children[i]);
    }
  }
}

// BFS level-order
function bfs(root, visit) {
  if (!root) return;
  const queue = [root];
  while (queue.length) {
    const n = queue.shift();                                                // step 3: queue
    visit(n);
    for (const c of n.children) queue.push(c);
  }
}

// BFS with level grouping
function bfsByLevels(root) {
  if (!root) return [];
  const result = [];
  let queue = [root];
  while (queue.length) {
    const level = [];
    const next = [];
    for (const n of queue) {                                                // step 4: snapshot level
      level.push(n.value);
      next.push(...n.children);
    }
    result.push(level);
    queue = next;
  }
  return result;
}

// Graph DFS with cycle detection
function graphDfs(start, neighbors, visit) {
  const visited = new Set();
  function dfs(node) {
    if (visited.has(node)) return;                                          // step 5: cycle break
    visited.add(node);
    visit(node);
    for (const n of neighbors(node)) dfs(n);
  }
  dfs(start);
}

// Binary inorder iterative
function inorderBinary(root, visit) {
  const stack = [];
  let curr = root;
  while (curr || stack.length) {
    while (curr) { stack.push(curr); curr = curr.left; }
    curr = stack.pop();
    visit(curr);                                                            // step 6: visit mid
    curr = curr.right;
  }
}

// Circular buffer queue for big BFS
class FastQueue {
  constructor() { this.data = []; this.head = 0; }
  push(v) { this.data.push(v); }
  shift() { return this.head < this.data.length ? this.data[this.head++] : undefined; }
  get length() { return this.data.length - this.head; }
}
```

**Try it yourself**

```js
const values = [];
dfsPreorder(root, n => values.push(n.value));
values;                                                        // [1, 2, 4, 5, 3]

const bfsValues = [];
bfs(root, n => bfsValues.push(n.value));
bfsValues;                                                     // [1, 2, 3, 4, 5]

bfsByLevels(root);                                            // [[1], [2, 3], [4, 5]]

// Shortest path in unweighted graph
function shortestPath(start, target, neighbors) {
  if (start === target) return [start];
  const queue = [[start, [start]]];
  const visited = new Set([start]);
  while (queue.length) {
    const [node, path] = queue.shift();
    for (const next of neighbors(node)) {
      if (visited.has(next)) continue;
      if (next === target) return [...path, next];
      visited.add(next);
      queue.push([next, [...path, next]]);
    }
  }
  return null;
}

// Big tree benchmark
const big = { children: [] };
let cur = big;
for (let i = 0; i < 1_000_000; i++) {
  const n = { children: [] };
  cur.children.push(n);
  cur = n;
}
// BFS with Array.shift: O(n²) — slow.
// BFS with FastQueue: O(n) — fast.
```

---

## 9. Step-by-step dry run

```
Tree:
      1
     / \
    2   3
   / \
  4   5

dfsPreorder visit order:
  1, recurse 2:
    2, recurse 4:
      4 (no children).
    recurse 5:
      5.
  recurse 3:
    3.
  Order: 1, 2, 4, 5, 3.

dfsIter:
  stack=[1].
  Pop 1: visit. Push children REVERSE: 3, then 2. stack=[3, 2].
  Pop 2: visit. Push 5, 4. stack=[3, 5, 4].
  Pop 4: visit. No children.
  Pop 5: visit.
  Pop 3: visit.
  Order: 1, 2, 4, 5, 3. ✓

BFS:
  queue=[1].
  Shift 1: visit. Push 2, 3. queue=[2, 3].
  Shift 2: visit. Push 4, 5. queue=[3, 4, 5].
  Shift 3: visit. queue=[4, 5].
  Shift 4: visit.
  Shift 5: visit.
  Order: 1, 2, 3, 4, 5.

Cycle detection:
  Graph: a → b → c → a.
  dfs(a): visited={a}. neighbors(a) = [b].
    dfs(b): visited={a,b}. neighbors(b) = [c].
      dfs(c): visited={a,b,c}. neighbors(c) = [a]. a visited → return.
    return.
  return.
```

---

## 10. Common confusion + traps

1. **`Array.shift` for big BFS** — O(n²) total.
2. **Forward push DFS children** — reverses order.
3. **No visited for graphs** — infinite cycles.
4. **Confuse pre/in/post** — recursive position matters.
5. **`Array.shift` vs Map for visited** — Set is right.
6. **Recursive DFS on deep tree** — stack overflow.
7. **BFS without level tracking** when needed.

---

## 11. Senior follow-ups & variants

### Variant 1 — Level grouping BFS
Snapshot per level.

### Variant 2 — Bidirectional BFS
For shortest path; two-front search.

### Variant 3 — Iterative deepening
DFS with depth bound, increasing.

### Variant 4 — Topological sort
DFS post-order or Kahn's BFS.

### Variant 5 — Cycle coloring (white/gray/black)
For directed graph cycle detection.

---

## 12. How to think aloud

> "DFS uses stack (recursion's implicit stack OR explicit). BFS uses queue. Picking: shortest path in unweighted graph → BFS; explore-one-branch-fully (backtracking, topological sort) → DFS. Pre/in/post-order for DFS: pre visits before children; in visits between left and right subtrees (binary only); post visits after children — useful for 'delete bottom-up' or computing height. Iterative DFS: explicit stack, push children in REVERSE (right then left) so left pops first. BFS: queue, but `Array.shift()` is O(n) — for million-node trees you get O(n²) total. Use a circular buffer (head index advances; don't shift). Level-grouped BFS: snapshot queue size at start of each level OR track levels separately. Graph cycle handling: `visited` Set; check before recursing/queueing. Variants: bidirectional BFS (search from both ends, meet in middle — sqrt speedup for unweighted shortest path); iterative deepening DFS (depth-limit, increase); topological sort via DFS post-order or Kahn's BFS (in-degree zero queue); white/gray/black coloring for directed cycle detection. Trap: Array.shift big BFS O(n²); forward children push reverses DFS order; no visited Set on graphs (infinite); recursive DFS on deep tree (V8 stack overflow)."

---

## 13. 60-second revision

> - **DFS stack; BFS queue.**
> - **Reverse-push children** for natural DFS order.
> - **Pre/in/post-order** differ by visit timing.
> - **`Array.shift` O(n)** — circular buffer for big BFS.
> - **Visited Set** for graphs.
> - **Iterative deepening** for memory-bounded.
> - **Topo sort:** DFS post-order or Kahn's BFS.
> - **Trap:** Array.shift; forward push; no visited; stack overflow.

---

**Related:** [iterative-from-recursive.md](./iterative-from-recursive.md) · [directory-walk-async.md](./directory-walk-async.md) · [tree-zipper-basics.md](./tree-zipper-basics.md) · [`07-arrays/sliding-window-helper.md`](../07-arrays/sliding-window-helper.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
