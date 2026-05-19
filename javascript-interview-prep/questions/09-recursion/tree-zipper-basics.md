# Tree zipper — functional tree navigation

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [tree-bfs-dfs.md](./tree-bfs-dfs.md), [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)
>
> **Source:** Huet (1997). Clojure, Haskell, Elm. Stripe, Razorpay — design-pattern questions.

---

## 1. Problem statement

Navigate an immutable tree with O(depth) updates. Cursor = current node + "crumbs" of context for each ancestor.

**Verification examples**

```js
const tree = {
  value: 'root',
  children: [
    { value: 'a', children: [{ value: 'a1', children: [] }] },
    { value: 'b', children: [] },
  ],
};

const z = makeZipper(tree);
const z2 = down(z, 0);        // focus 'a'
const z3 = down(z2, 0);       // focus 'a1'
const z4 = replace(z3, { value: 'a1!', children: [] });
const z5 = up(z4);             // back to 'a' with replaced child
const z6 = up(z5);             // back to root with replaced descendant
const newTree = commit(z6);
// newTree differs from tree only along the path to a1.
```

**Constraints**
- Immutable: each op returns new zipper.
- O(depth) per update (only rebuild ancestors).
- Operations: down, up, left, right, replace, commit.
- "Crumbs" store sibling context.

---

## 2. Plain-English restatement

A zipper holds a cursor into a tree. Moving "down" steps into a child; moving "up" reconstructs the parent from a stored "crumb" (left siblings + right siblings + parent-without-children). Updates touch only the path from root to cursor.

---

## 3. Why this matters in interviews

Tests: immutable updates, cursor pattern, FP idiom. Real use: React state with deep updates, AST transforms.

---

## 4. Mental model

```
   Zipper:
     {
       focus: currentNode,
       path: [crumb, crumb, ...]   ← stack of ancestors
     }
   
   Crumb (for each ancestor):
     {
       parent: parent node WITHOUT children,
       leftSiblings: siblings before me,
       rightSiblings: siblings after me,
     }
   
   Operations:
     makeZipper(tree): { focus: tree, path: [] }
     down(z, i): step to i-th child; push crumb.
     up(z): pop crumb; reconstruct parent with focus inserted.
     left(z) / right(z): move among siblings.
     replace(z, newNode): swap focus.
     commit(z): up until path empty; return focus = full tree.

   Why O(depth):
     Only ancestors rebuilt (immutability constraint).
     Untouched subtrees shared by reference.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does a "crumb" store?
> 2. Why O(depth) not O(n)?
> 3. Where do unchanged subtrees go?

---

## 6. Brute force — walked through

```js
// Naive: walk path, deep-clone and replace
function naiveReplace(tree, path, newNode) {
  if (path.length === 0) return newNode;
  const [i, ...rest] = path;
  return {
    ...tree,
    children: tree.children.map((c, idx) =>
      idx === i ? naiveReplace(c, rest, newNode) : c
    ),
  };
}
```

Works for single replace. Multiple in sequence: clone-on-write repeatedly; same O(depth) per update but no cursor.

---

## 7. The unlocking insight

> **Cursor = node + crumbs. Down pushes crumb; up reconstructs parent. Updates O(depth) — only ancestors rebuilt.**

Three properties:

1. **Crumbs** carry sibling context.
2. **O(depth) updates**.
3. **Untouched subtrees shared**.

---

## 8. Solution (annotated)

```js
function makeZipper(tree) {
  return { focus: tree, path: [] };                                         // step 1: cursor at root
}

function down(z, i) {
  const children = z.focus.children;
  if (i >= children.length) throw new Error('out of bounds');
  return {
    focus: children[i],                                                     // step 2: descend
    path: [{
      parent: z.focus,                                                       // step 3: capture context
      leftSiblings: children.slice(0, i),
      rightSiblings: children.slice(i + 1),
    }, ...z.path],
  };
}

function up(z) {
  if (z.path.length === 0) throw new Error('at root');
  const [crumb, ...rest] = z.path;
  return {
    focus: {
      ...crumb.parent,                                                       // step 4: rebuild parent
      children: [...crumb.leftSiblings, z.focus, ...crumb.rightSiblings],
    },
    path: rest,
  };
}

function left(z) {
  if (z.path.length === 0) throw new Error('no parent');
  const [crumb, ...rest] = z.path;
  if (crumb.leftSiblings.length === 0) throw new Error('no left sibling');
  const newFocus = crumb.leftSiblings[crumb.leftSiblings.length - 1];
  return {
    focus: newFocus,
    path: [{
      ...crumb,
      leftSiblings: crumb.leftSiblings.slice(0, -1),
      rightSiblings: [z.focus, ...crumb.rightSiblings],
    }, ...rest],
  };
}

function right(z) {
  if (z.path.length === 0) throw new Error('no parent');
  const [crumb, ...rest] = z.path;
  if (crumb.rightSiblings.length === 0) throw new Error('no right sibling');
  const newFocus = crumb.rightSiblings[0];
  return {
    focus: newFocus,
    path: [{
      ...crumb,
      leftSiblings: [...crumb.leftSiblings, z.focus],
      rightSiblings: crumb.rightSiblings.slice(1),
    }, ...rest],
  };
}

function replace(z, newNode) {
  return { focus: newNode, path: z.path };                                  // step 5: swap focus
}

function commit(z) {
  while (z.path.length) z = up(z);                                          // step 6: unwind
  return z.focus;
}
```

**Try it yourself**

```js
const tree = {
  value: 'root',
  children: [
    { value: 'a', children: [{ value: 'a1', children: [] }] },
    { value: 'b', children: [] },
  ],
};

const z = makeZipper(tree);
const z2 = down(z, 0);                                        // 'a'
console.log(z2.focus.value);                                  // 'a'
const z3 = down(z2, 0);                                       // 'a1'
const z4 = replace(z3, { value: 'A1!', children: [] });
const newTree = commit(z4);
console.log(newTree.children[0].children[0].value);          // 'A1!'

// Original unchanged
console.log(tree.children[0].children[0].value);              // 'a1'

// Untouched 'b' shared by reference
newTree.children[1] === tree.children[1];                     // true (structural sharing)

// Map over tree (apply fn to each node)
function mapTree(z, fn) {
  z = replace(z, fn(z.focus));
  for (let i = 0; i < z.focus.children.length; i++) {
    z = mapTree(down(z, i), fn);
    z = up(z);
  }
  return z;
}

const upper = commit(mapTree(makeZipper(tree), node => ({
  ...node,
  value: node.value.toUpperCase(),
})));
// All nodes uppercased.

// Find by predicate (walks left-deep)
function find(z, pred) {
  if (pred(z.focus)) return z;
  for (let i = 0; i < z.focus.children.length; i++) {
    try {
      const found = find(down(z, i), pred);
      if (found) return found;
    } catch {}
  }
  return null;
}
```

---

## 9. Step-by-step dry run

```
tree = { value: 'r', children: [{value:'a', children:[]}, {value:'b', children:[]}] }

z = makeZipper(tree):
  { focus: tree, path: [] }

z2 = down(z, 1):    // step into 'b'
  children = [a, b].
  focus = children[1] = b.
  crumb = { parent: r, leftSiblings: [a], rightSiblings: [] }.
  path = [crumb].

z3 = replace(z2, {value:'B!', children:[]}):
  focus = {value:'B!', children:[]}.
  path unchanged.

z4 = up(z3):
  crumb = path[0]. rest = [].
  focus = {
    ...crumb.parent (r without children mention),
    children: [a, {value:'B!', ...}]   // leftSiblings + focus + rightSiblings.
  }.
  path = [].

commit(z4): path empty → return focus = full new tree.

Result:
  { value:'r', children: [a, {value:'B!', children:[]}] }

  'a' is SAME REFERENCE as in original tree.children[0] (shared).
  'r' is NEW object (rebuilt because its children changed).

Compare to naive deep clone:
  Whole tree cloned → O(n).
  Zipper: only path rebuilt → O(depth).

For a 1M-node tree with one update:
  Naive: 1M objects allocated.
  Zipper: log(1M) ≈ 20 objects.

Tradeoff: zipper API is verbose. Use cases:
  - Editors with undo history (immutable trees).
  - AST transforms in compilers.
  - React state with deep nested updates (Immer is conceptually similar).
```

---

## 10. Common confusion + traps

1. **Untouched subtrees not shared** — broken structural sharing.
2. **Mutate during navigation** — should be immutable.
3. **Up from root** — throw or return null.
4. **Left/right at edges** — guard with checks.
5. **Crumbs incorrectly assembled** — wrong sibling order.
6. **Performance assumption** — only ancestors rebuilt; subtrees shared.
7. **Recursive map** — wrap with try/finally for navigation safety.

---

## 11. Senior follow-ups & variants

### Variant 1 — Generalized zipper
For any inductive data structure (lists, trees, ASTs).

### Variant 2 — Lens / optics
More general "focused update" abstraction.

### Variant 3 — Immer
Mutates-in-place draft; commits to immutable.

### Variant 4 — Persistent data structures
Bagwell HAMTs, RRB-trees.

### Variant 5 — Cursor for React state
Useful for deep nested forms.

---

## 12. How to think aloud

> "Tree zipper: cursor-based functional navigation of an immutable tree. State = `{focus: currentNode, path: [crumb, ...]}` where each crumb captures parent context (parent node minus its children, leftSiblings array, rightSiblings array). Operations: `down(z, i)` descends to i-th child, pushing crumb; `up(z)` pops crumb and reconstructs the parent by interleaving leftSiblings + focus + rightSiblings; `left(z)` / `right(z)` move among siblings (rotates crumb); `replace(z, newNode)` swaps focus; `commit(z)` calls `up` until path empty. Why O(depth) updates: only nodes along the path from root to cursor are rebuilt; all untouched subtrees are shared by reference (structural sharing). For a 1M-node tree with one update, that's ~20 new objects vs 1M for a naive deep clone. Use cases: immutable AST transforms (compilers), editors with undo history, React deep state updates (Immer is conceptually similar but uses Proxy + draft mutation). Tradeoff: API is verbose; helpers like Lens/optics generalize. Trap: not sharing untouched subtrees (defeats benefit); mutating during navigation; missing edge guards (up from root, left at start)."

---

## 13. 60-second revision

> - **Cursor = `{focus, path}`.**
> - **Crumbs** store parent + sibling context.
> - **Down pushes, up reconstructs.**
> - **O(depth) updates** — ancestors rebuilt.
> - **Untouched subtrees shared.**
> - **`commit`** unwinds to root.
> - **Use:** AST transforms, immutable editors.
> - **Immer-like** for ergonomics.
> - **Trap:** broken sharing; mutate during nav; edge cases.

---

**Related:** [tree-bfs-dfs.md](./tree-bfs-dfs.md) · [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) · [`08-maps-sets/object-deep-diff.md`](../08-maps-sets/object-deep-diff.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
