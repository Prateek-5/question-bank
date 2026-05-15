# Implement `memoize` for object-identity arguments (Memoize II)

## Source
- Canonical advanced machine-coding interview problem (LeetCode #2630 "Memoize II", Pramp, BFE.dev).
- LeetCode reference: https://leetcode.com/problems/memoize-ii/

## Why this question matters in interviews
Memoize II is the moment the interviewer separates the "I read a blog" candidates from the ones who actually understand data structures. The plain `memoize` (see memoize.md) breaks down the second you pass an object — `{a:1}` and `{a:1}` stringify identically but are **different references**. Memoize II requires you to key the cache by **identity, not value**, which means you can't stringify and you can't use a flat `Map` (object keys in a Map work, but you'd lose discrimination across multi-arg calls). The standard senior answer is a **nested Map trie**: one Map per argument position, drilling down. This is the same trie pattern that powers React's hook memoization, GraphQL DataLoader batching, and content-addressable caches. Demonstrating it gets you a tick in the "knows non-trivial data structures" column.

## Concepts involved

### Syntax to lock in
```js
const memo = memoize(fn);
const obj = { id: 1 };
memo(obj, 'x');   // miss, computes
memo(obj, 'x');   // hit — same ref!
memo({ id: 1 }, 'x'); // miss — different ref
```

The trie node shape:
```js
// Each level: one Map per argument position.
// Each node optionally holds a "result" if a function call ended here.
const root = new Map();
root.has('__result__'); // does a 0-arg call have a cached result?
// or: a node = { map: Map, hasResult: boolean, result: any }
```

### Runtime / engine behavior
- `Map` accepts **any** key — strings, numbers, objects, functions. Object keys use **reference equality**. This is what makes the trie work: `map.get(obj)` returns the entry only if you pass the *same* `obj` reference.
- A flat `Map<args, result>` doesn't work because each call has a *different* `args` array (new array literal every time). So we walk arg-by-arg.
- Depth of the trie = `args.length`. Memory per cached call ≈ `O(args.length)` map entries. Each lookup = `O(args.length)` map probes (each O(1)).
- **WeakMap vs Map**: WeakMap allows GC of the object key when no other refs exist — great for memory hygiene, but WeakMap keys **must be objects** (no primitives). So a hybrid approach is needed: WeakMap for object args, Map for primitive args. The LeetCode problem doesn't require WeakMap; mention it as a refinement.

### Edge cases (these are the interview traps)
1. **0-arg calls** — `memo()` should cache the result. Reserve a sentinel slot on the root node (e.g., `node.hasResult`).
2. **Variable arity** — `memo(a)` and `memo(a, b)` are different calls. They must land at different trie depths and not collide. The "result slot" must be **per-node**, not "deepest leaf only."
3. **Mixed primitive + object args** — `memo(1, obj, 'x')` must work. Use `Map` at every level (Map accepts both primitive and object keys).
4. **Same args repeated** — `memo(obj, obj)` — walks down twice with the same key, but each level is a separate Map, so no collision.
5. **Functions as args** — functions are objects in JS, so reference-keyed Maps work. Frequently tested.
6. **`NaN`** — `NaN === NaN` is false, but `Map` uses **SameValueZero** equality, so `map.get(NaN)` after `map.set(NaN, ...)` works. Worth knowing for the trick question.
7. **Cache invalidation** — if an object arg is mutated externally, the cached result is now stale. Mention "memoize works only for **pure** functions called with **immutable** arg shapes."
8. **WeakMap can't be iterated** — if you switch to WeakMap, you give up `cache.size` and `cache.clear()`. Trade-off worth flagging.

## Brute force approach
Flatten args to a string with `args.map(a => a.id || a).join('|')` — terrible. Brittle, leaks the implementation, dies on cycles, doesn't preserve identity. Or use `JSON.stringify` — same problem as plain `memoize`. Neither works. Go straight to the trie.

## Optimal approach
A **nested Map trie**: root is a `Map`. To look up `memo(a, b, c)`:
1. `node = root.get(a)`. If missing, miss → compute.
2. `node = node.get(b)`. If missing, miss → compute.
3. `node = node.get(c)`. If missing, miss → compute.
4. Check `node.hasResult`. If yes, hit → return `node.result`. Else miss → compute, set.

Each "node" is `{ children: Map, hasResult: boolean, result: any }`.

`O(N)` lookup where `N = args.length`. `O(N)` insertion. Memory grows with unique arg-paths.

## Solution (JavaScript)

```js
/**
 * Memoize where keys use REFERENCE equality (objects/functions) or
 * SameValueZero (primitives). Uses a nested Map trie.
 * @param {Function} fn  pure function
 * @returns {Function}
 */
function memoize(fn) {
  const root = makeNode();

  function makeNode() {
    return { children: new Map(), hasResult: false, result: undefined };
  }

  return function (...args) {
    let node = root;
    for (const arg of args) {
      if (!node.children.has(arg)) {
        node.children.set(arg, makeNode());
      }
      node = node.children.get(arg);
    }
    if (!node.hasResult) {
      node.result = fn.apply(this, args);
      node.hasResult = true;
    }
    return node.result;
  };
}
```

A more memory-friendly variant using WeakMap for object keys (so they can be GC'd when no other ref holds them):

```js
function memoizeWeak(fn) {
  const objCache = new WeakMap();   // for object/function args
  const primCache = new Map();      // for primitive args
  const resultSlot = Symbol('result');

  function getChild(node, arg) {
    const cache = (typeof arg === 'object' && arg !== null) || typeof arg === 'function'
      ? node.weak ?? (node.weak = new WeakMap())
      : node.prim ?? (node.prim = new Map());
    if (!cache.has(arg)) cache.set(arg, { weak: null, prim: null, hasResult: false, result: undefined });
    return cache.get(arg);
  }

  const root = { weak: null, prim: null, hasResult: false, result: undefined };

  return function (...args) {
    let node = root;
    for (const arg of args) node = getChild(node, arg);
    if (!node.hasResult) {
      node.result = fn.apply(this, args);
      node.hasResult = true;
    }
    return node.result;
  };
}
```

For the interview, the simple `Map`-only trie is cleaner and what graders expect.

## Step-by-step dry run

Input:
```js
let calls = 0;
const fn = (a, b) => { calls++; return a.x + b; };
const memo = memoize(fn);

const obj1 = { x: 10 };
const obj2 = { x: 10 };   // same shape, different ref

memo(obj1, 5);   // (1)
memo(obj1, 5);   // (2)
memo(obj2, 5);   // (3)
memo(obj1, 6);   // (4)
```

Trace the trie (`R` = root):

- Call (1) `memo(obj1, 5)`:
  - Walk `obj1` in `R.children` → miss → create new node `N1`. `R.children.set(obj1, N1)`. node = N1.
  - Walk `5` in `N1.children` → miss → create `N2`. node = N2.
  - `N2.hasResult` = false → invoke `fn(obj1, 5)` = `15`, calls=1. Set `N2.result = 15, N2.hasResult = true`. Return `15`.

- Call (2) `memo(obj1, 5)`:
  - `R.children.get(obj1)` = N1 (same ref!). node = N1.
  - `N1.children.get(5)` = N2. node = N2.
  - `N2.hasResult` true → return `15`. calls unchanged.

- Call (3) `memo(obj2, 5)`:
  - `R.children.get(obj2)` — **miss** (different ref from obj1) → create `N3`. node = N3.
  - `5` in N3.children → miss → create `N4`. node = N4.
  - Invoke `fn(obj2, 5)` = `15`, calls=2. Cache. Return.

- Call (4) `memo(obj1, 6)`:
  - `R.children.get(obj1)` = N1. node = N1.
  - `N1.children.get(6)` — **miss** → create `N5`. node = N5.
  - Invoke `fn(obj1, 6)` = `16`, calls=3. Cache. Return.

Final `calls === 3`. Trie shape:
```
R
├─ obj1 → N1
│   ├─ 5 → N2 (result=15)
│   └─ 6 → N5 (result=16)
└─ obj2 → N3
    └─ 5 → N4 (result=15)
```

Note how `obj1` and `obj2` get separate branches even though their shapes are identical — that's the **identity-keyed** behavior we wanted.

## Important takeaways

**Syntax to memorize**
- Trie node = `{ children: Map, hasResult: boolean, result: any }`.
- Walk args one at a time: `node = node.children.get(arg)`.
- "Result slot" lives **on the node** at the end of the walk, not deeper. This handles variable arity.

**Patterns to reuse**
- Nested Map / trie is the same structure that powers: GraphQL DataLoader keying by composite args, React `useMemo` dep arrays, Redux Reselect-style memoization with object deps, and content-addressable storage.
- WeakMap-of-WeakMap is a memory-safe variant when you know all args are objects.
- The "I have N orthogonal keys, I want O(1) lookup, but composite keys must respect identity" problem always reduces to this trie.

**Common mistakes**
- Using `JSON.stringify(args)` — defeats the purpose of identity keying.
- Using a flat `Map` keyed by `args` (the array) — every call passes a new array literal, so every call misses.
- Forgetting the "result slot" per node and only checking at the deepest level — breaks variable-arity calls.
- Using only WeakMap → primitive args crash (`WeakMap.set("foo", ...)` throws).

**Related questions**
- `memoize(fn)` — primitive-arg version (see memoize.md).
- DataLoader batching (composite keys).
- React `useMemo` deps — same identity issue.

## Variants

1. **WeakMap-backed memoize** — GC-friendly for object-only args. Cache entries vanish when the key object is no longer referenced. Trade-off: not iterable, no `size`.

2. **Bounded memoize** — wrap each trie node with an LRU eviction policy. Hard to get right (eviction at which level?), usually done at the top level only.

3. **Async memoize II** — `fn` returns a promise. Cache the promise (deduplicates concurrent calls). On rejection, evict the path so retries can succeed.

4. **`isEqual`-keyed memoize** — instead of identity, use structural equality (lodash `_.isEqual`) for keys. Slower but matches the value-equality intuition. Note: structural-equality keying is **incompatible** with hashing, so you fall back to linear scan — O(N) per lookup.

## Revision notes

> **Memoize II — 60 second recap**
> - Problem: identity-keyed memoize (objects with same shape but different refs must NOT collide).
> - Solution: **nested Map trie**, one Map per arg position. Walk arg-by-arg.
> - Each trie node has a `hasResult` flag + `result` slot — handles variable arity.
> - Map keys use reference equality for objects, SameValueZero for primitives.
> - Refinement: WeakMap for object keys (GC-friendly), Map for primitive keys (hybrid).
> - **Trap:** flat `Map<args, result>` — new array literal per call, always misses.
> - **Trap 2:** result-slot only at deepest leaf — breaks variable arity.
