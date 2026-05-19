# Implement `memoize` for object-identity arguments (Memoize II)

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [memoize.md](./memoize.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** [LeetCode 2630 — Memoize II](https://leetcode.com/problems/memoize-ii/). The Memoize follow-up that separates value-keyed from identity-keyed.

---

## 1. Problem statement

**Signature**
```ts
function memoize<F extends (...args: any[]) => any>(fn: F): F;
```

**Input / Output examples**

| Setup                                          | Behaviour                                              |
|-------------------------------------------------|---------------------------------------------------------|
| `memo(obj, 'x'); memo(obj, 'x')`               | second call: cached (same `obj` ref)                   |
| `memo({a:1}); memo({a:1})`                     | two different refs → both miss                         |
| `memo(1, 2); memo(1, 2)`                       | primitives keyed by SameValueZero → second cached      |
| `memo(a); memo(a, b)`                          | variable arity — different paths, both cached separately |
| `memo()` (zero args)                            | result slot at root                                    |
| `memo(NaN); memo(NaN)`                         | second cached (Map uses SameValueZero, NaN === NaN under it) |

**Constraints**
- Cache by **identity** for objects/functions, by **SameValueZero** for primitives.
- Handle variable arity.
- O(N) lookup where N = `args.length`.
- Each trie node has its own `result` slot.

---

## 2. Plain-English restatement

Like `memoize`, but keys use **reference equality** for objects (not structural equality). `memo(obj1, 'x')` and `memo(obj2, 'x')` are different calls even if `obj1` and `obj2` are structurally identical. The plain `memoize` fails because `JSON.stringify({a:1}) === JSON.stringify({a:1})` collapses distinct refs. The senior answer: nested Map trie, one Map per argument position.

---

## 3. Why this matters in interviews

Memoize II is the moment the interviewer separates "I read a blog" from "I understand data structures." The nested-Map trie pattern is the same structure that powers React `useMemo` deps, GraphQL DataLoader composite keys, content-addressable caches. Identity-keyed > value-keyed is a senior distinction.

---

## 4. Mental model

A **trie of Maps**, one level per argument:

```
   memo(obj1, 5)              memo(obj1, 6)              memo(obj2, 5)
                          R (root Map)
                          │
       ┌──────────────────┼──────────────────┐
     obj1 (ref)         obj2 (ref)         ...
       │                  │
   ┌───┼───┐              │
   5   6                  5
   │   │                  │
   result(15)  result(16) result(15)   ← per-node result slots
   ↑           ↑          ↑
   path 1      path 2     path 3 (obj2 ≠ obj1, separate branch!)
```

Each node: `{ children: Map, hasResult: boolean, result: any }`. Walk arg-by-arg; consume the result slot at the end of the walk.

**Identity matters:** Map keys use reference equality for objects, so `obj1` and `obj2` (same shape, different refs) land at different children.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does flat `Map<args, result>` (with `args` as the key) always miss?
> 2. If `memo(a); memo(a, b)` both cache, where does each result live in the trie?
> 3. What happens with `memo(NaN); memo(NaN)` — same or different cache entries?

---

## 6. Brute force — walked through

### Wrong attempt 1: stringify args
```js
const key = args.map(a => a.id ?? a).join('|');
```
Doesn't preserve identity. `obj1` and `obj2` with same `id` collide.

### Wrong attempt 2: flat `Map<args, result>` using args array as key
```js
this.cache.set(args, result);
this.cache.get(args);     // BUG: new array literal per call → never matches
```
Every call passes a fresh array reference → Map.get always misses.

### Wrong attempt 3: result-slot only at deepest leaf
```js
// Only check `hasResult` at the bottom of the trie
```
Breaks variable arity. `memo(a)` and `memo(a, b)` need separate result slots, both on the same path.

---

## 7. The unlocking insight

> **Nested Map trie: one Map per argument position. Walk arg-by-arg; each trie node has its own `hasResult`/`result` slot for that arity. Map keys use reference equality for objects, SameValueZero for primitives — exactly what we want.**

Three properties:

1. **Trie of Maps** — `O(N)` walk per call (N = args.length); each level O(1) lookup.
2. **Per-node result slot** — handles variable arity.
3. **Map equality semantics** — reference for objects/functions, SameValueZero for primitives.

---

## 8. Solution (annotated)

```js
function memoize(fn) {
  const root = makeNode();                                          // step 1: root trie node

  function makeNode() {
    return { children: new Map(), hasResult: false, result: undefined };
  }

  return function (...args) {
    let node = root;
    for (const arg of args) {                                        // step 2: walk arg-by-arg
      if (!node.children.has(arg)) {
        node.children.set(arg, makeNode());
      }
      node = node.children.get(arg);
    }
    if (!node.hasResult) {                                            // step 3: per-node result slot
      node.result = fn.apply(this, args);
      node.hasResult = true;
    }
    return node.result;
  };
}

// WeakMap-backed variant (GC-friendly for object args; Map for primitives)
function memoizeWeak(fn) {
  const makeNode = () => ({ weak: null, prim: null, hasResult: false, result: undefined });
  const root = makeNode();

  const getChild = (node, arg) => {
    const isRef = (typeof arg === 'object' && arg !== null) || typeof arg === 'function';
    const cache = isRef
      ? (node.weak ?? (node.weak = new WeakMap()))
      : (node.prim ?? (node.prim = new Map()));
    if (!cache.has(arg)) cache.set(arg, makeNode());
    return cache.get(arg);
  };

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

**Try it yourself**

```js
let calls = 0;
const fn = (a, b) => { calls++; return a.x + b; };
const memo = memoize(fn);

const obj1 = { x: 10 };
const obj2 = { x: 10 };                       // same shape, different ref

memo(obj1, 5);   // miss, calls=1, returns 15
memo(obj1, 5);   // HIT, calls=1, returns 15
memo(obj2, 5);   // MISS (different ref), calls=2
memo(obj1, 6);   // miss, calls=3, returns 16

console.log(calls);   // 3
```

---

## 9. Step-by-step dry run

```
Setup: memo = memoize(fn). root = {children: Map{}, hasResult: false}

(1) memo(obj1, 5):
    node = root
    arg=obj1: children.has? no → create N1; node = N1
    arg=5:    N1.children.has? no → create N2; node = N2
    N2.hasResult? no → fn(obj1, 5) = 15. calls=1. N2.result=15, hasResult=true.
    return 15

(2) memo(obj1, 5):
    walk: root → N1 (obj1) → N2 (5)
    N2.hasResult? yes → return 15. calls unchanged.

(3) memo(obj2, 5):
    arg=obj2: root.children.has(obj2)? NO (different ref from obj1) → create N3
    arg=5:    N3.children.has(5)? no → create N4
    fn(obj2, 5) = 15. calls=2. N4.result=15.

(4) memo(obj1, 6):
    arg=obj1: → N1
    arg=6:    N1.children.has(6)? no → create N5
    fn(obj1, 6) = 16. calls=3. N5.result=16.

Final trie:
  root
  ├─ obj1 → N1
  │  ├─ 5 → N2 (result=15)
  │  └─ 6 → N5 (result=16)
  └─ obj2 → N3
     └─ 5 → N4 (result=15)
```

Variable arity:
```
memo(a):     walk root → N_a; consume N_a.result
memo(a, b):  walk root → N_a → N_a_b; consume N_a_b.result
```
Both paths share the prefix `root → N_a` but the result slots are on different nodes.

---

## 10. Common confusion + traps

1. **Flat `Map<args, result>`** — new array literal per call, always misses.
2. **`JSON.stringify(args)`** — defeats identity keying.
3. **Result slot only at deepest leaf** — breaks variable arity.
4. **`WeakMap` only** — primitive args throw (`WeakMap.set("foo", ...)`).
5. **Forgetting cache invalidation when an arg mutates** — memoize works only for **pure** fns with immutable arg shapes.
6. **NaN behavior** — Map uses SameValueZero, so `NaN` keys work; `===`-based caches don't.
7. **WeakMap iteration** — WeakMaps aren't iterable; you lose `size` / `clear` if you go pure-Weak.

---

## 11. Senior follow-ups & variants

### Variant 1 — WeakMap-backed (GC-friendly)
Trie uses WeakMap for object args, Map for primitive args. Entries vanish when key object loses all refs. Trade-off: not iterable, no `size`.

### Variant 2 — Bounded memoize (LRU at trie root)
LRU evict whole arg-paths when memory grows. Hard to get right at deeper levels.

### Variant 3 — Async Memoize II
`fn` returns a Promise. Cache the Promise (dedupes concurrent calls). On reject, evict the path so retries can succeed.

### Variant 4 — Structural-equality keying
Use `_.isEqual` for keys. Incompatible with hashing → O(N) linear scan per lookup. Useful when caller can't preserve refs.

---

## 12. How to think aloud

> "Plain memoize fails for objects because `JSON.stringify({a:1}) === JSON.stringify({a:1})` collapses distinct refs. Solution: nested Map trie, one Map per argument position. Walk arg-by-arg; each trie node has its own `hasResult`/`result` slot (handles variable arity). Map keys use reference equality for objects and SameValueZero for primitives — exactly the semantics we want. O(N) per lookup where N = args.length. Same shape as React hook deps, DataLoader composite keys. Refinement: WeakMap for object positions so cache entries GC when keys are dropped. Trap: flat Map<args, result> always misses (new array per call). Trap: result slot only at deepest leaf breaks variable arity."

---

## 13. 60-second revision

> - **Nested Map trie**, one Map per argument position.
> - **Each node:** `{children: Map, hasResult, result}`.
> - **Walk arg-by-arg;** consume per-node result slot.
> - **Map keys:** reference for objects/functions, SameValueZero for primitives.
> - **Variable arity** handled by per-node result slots.
> - **WeakMap refinement** for object args (GC-friendly).
> - **Async variant:** cache the Promise; evict on reject.
> - **Trap:** flat Map (new array per call); result slot only at leaf; WeakMap-only (primitives throw).

---

**Related:** [memoize.md](./memoize.md) · [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) · [lru-cache.md](./lru-cache.md) · [`04-promises/async-memoize.md`](../04-promises/async-memoize.md) · [dataloader-batch-cache.md](./dataloader-batch-cache.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
