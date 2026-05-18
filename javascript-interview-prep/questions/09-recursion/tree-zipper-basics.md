# Tree Zipper — Functional Tree Navigation

## Source / Origin
- Functional-programming pattern (Huet, 1997); used in Clojure, Haskell, Elm.
- Asked at: Stripe, Razorpay — design-pattern questions.
- Concept reference: `concepts/recursion.md`.

## Why this question matters in interviews
"Navigate this immutable tree, mutate a node, get the new tree back." Standard recursion either mutates or rebuilds the whole tree. A zipper holds a *cursor* into the tree with O(depth) updates — efficient immutable navigation. Senior bar: you can sketch the cursor (current node + crumbs/path), implement up/down/left/right, and reconstruct on `commit`.

## Concepts involved

```js
// Tree node: { value, children: [] }
// Zipper: { focus, path }
//   path = list of "crumbs" — for each ancestor, its remaining context

function makeZipper(tree) {
  return { focus: tree, path: [] };
}

function down(z, i) {
  const children = z.focus.children;
  if (i >= children.length) throw new Error('out of bounds');
  return {
    focus: children[i],
    path: [{ parent: z.focus, leftSiblings: children.slice(0, i), rightSiblings: children.slice(i + 1) }, ...z.path],
  };
}

function up(z) {
  if (z.path.length === 0) throw new Error('at root');
  const [crumb, ...rest] = z.path;
  return {
    focus: { ...crumb.parent, children: [...crumb.leftSiblings, z.focus, ...crumb.rightSiblings] },
    path: rest,
  };
}

function replace(z, newNode) {
  return { ...z, focus: newNode };
}

function commit(z) {
  let curr = z;
  while (curr.path.length > 0) curr = up(curr);
  return curr.focus;
}
```

### Edge cases / traps
1. **Immutability** — every move creates a new path entry; the focus is unmodified until `commit` (replaces immutably).
2. **Crumb captures siblings** — `leftSiblings` and `rightSiblings` so up() can rebuild parent.
3. **Up from root** — error or no-op.
4. **Down with invalid index** — error.
5. **Sibling navigation** (left/right) — adjust leftSiblings/rightSiblings.
6. **Performance** — O(depth) per move; O(depth) per commit (rebuilds spine).
7. **Generality** — works for any tree shape: HTML, AST, file systems, etc.
8. **Comparison to lenses** — zippers are stateful (current focus); lenses are pure (path-as-data).

## Mental Model

```
   tree:        zipper{ focus, path }
        A
       / \      down(1) →   focus=C
      B   C                   path=[{parent:A, leftSibs:[B], rightSibs:[]}]
         / \
        D   E   down(0) →   focus=D
                              path=[{parent:C, leftSibs:[], rightSibs:[E]},
                                    {parent:A, leftSibs:[B], rightSibs:[]}]
   
   commit: walk up rebuilding parents with new focus
```

## Why interviewers care

- **Functional immutability pattern.**
- **Path-as-data thinking.**
- **Efficient immutable updates** without full tree clone.

## Common confusion

- **"Mutate in place is fine."** Defeats the point of immutable trees.
- **"Just rebuild from root."** O(n) per update; zipper is O(depth).
- **"Same as DOM cursor."** Conceptually yes; zipper is the functional version.
- **"Need a parent pointer."** No — path stores it.

## Solution

```js
function makeZipper(tree) {
  return { focus: tree, path: [] };
}
function down(z, i) {
  const ch = z.focus.children || [];
  if (i < 0 || i >= ch.length) throw new Error('bad index');
  return {
    focus: ch[i],
    path: [{ parent: z.focus, left: ch.slice(0, i), right: ch.slice(i + 1) }, ...z.path],
  };
}
function up(z) {
  if (!z.path.length) return z;
  const [c, ...rest] = z.path;
  return {
    focus: { ...c.parent, children: [...c.left, z.focus, ...c.right] },
    path: rest,
  };
}
function left(z) {
  if (!z.path.length) throw new Error('at root');
  const [c, ...rest] = z.path;
  if (!c.left.length) throw new Error('no left sibling');
  return {
    focus: c.left[c.left.length - 1],
    path: [{ parent: c.parent, left: c.left.slice(0, -1), right: [z.focus, ...c.right] }, ...rest],
  };
}
function right(z) {
  if (!z.path.length) throw new Error('at root');
  const [c, ...rest] = z.path;
  if (!c.right.length) throw new Error('no right sibling');
  return {
    focus: c.right[0],
    path: [{ parent: c.parent, left: [...c.left, z.focus], right: c.right.slice(1) }, ...rest],
  };
}
function replace(z, fn) { return { ...z, focus: typeof fn === 'function' ? fn(z.focus) : fn }; }
function commit(z) {
  let curr = z;
  while (curr.path.length) curr = up(curr);
  return curr.focus;
}

// Usage
const tree = { v: 'A', children: [
  { v: 'B', children: [] },
  { v: 'C', children: [{ v: 'D', children: [] }, { v: 'E', children: [] }] },
] };

const z = makeZipper(tree);
const z2 = down(z, 1);              // focus C
const z3 = down(z2, 0);             // focus D
const z4 = replace(z3, n => ({ ...n, v: 'D!' }));
const newTree = commit(z4);
newTree.children[1].children[0].v;  // 'D!'
tree.children[1].children[0].v;     // 'D' (original untouched)
```

## How to think aloud

> "Zipper: focus + path. Path is a stack of crumbs — each crumb captures the parent's context minus the descended child. down(i) pushes a crumb, sets focus to child i. up() pops a crumb, reconstructs parent with current focus reinserted. replace mutates focus immutably; commit walks up to root. O(depth) per move; persistent — original tree unchanged. Used in functional-state libraries for efficient updates without cloning the whole tree."

## Important takeaways

- **`{focus, path}` cursor.**
- **Crumb captures parent + left/right siblings** (without the focused child).
- **down(i), up(), left(), right(), replace(), commit().**
- **O(depth) per move.**
- **Immutable** — original tree untouched.
- **Used in**: Clojure data manipulation, Elm tree navigation, functional editors.

## Variants

- **Multi-pane zipper** — multiple cursors into the same tree.
- **Differentiable types** — generalization in dependent-type FP.
- **Lenses** — pure-data version (path as a list of indices).
- **Persistent vector tries** — backing store for big sequences (Immutable.js).

## Revision notes

```
Zipper: {focus, path}
  path = [crumb, crumb, ...]  (top of stack = immediate parent context)
  crumb = {parent, left, right}  (siblings split around focused child)

operations:
  down(i): push crumb; focus = parent.children[i]
  up():    pop crumb; rebuild parent with focus inserted; focus = parent
  left/right: shift sibling boundary
  replace(fn): update focus (immutable)
  commit(): walk up to root; return new tree

PROPS:
  immutable
  O(depth) per move
  O(depth) per commit
  original tree untouched

USES: AST editors, undo/redo, persistent state
```
