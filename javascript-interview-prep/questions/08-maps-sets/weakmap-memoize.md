# `WeakMap`-backed memoization and private fields

## Source
- Canonical interview problem.
- Mirrors the use case behind ES private class fields (`#name`) and lodash `_.memoize` with object keys.

## Why this question matters in interviews
`WeakMap` is the most under-explained data structure in JavaScript and the interviewer knows it. If you can articulate **(a) keys must be objects, (b) entries are garbage-collected when the key has no other references, (c) WeakMap is not iterable**, you're already in the top quartile. The two killer use cases — **memoizing computed results per-object without leaking** and **attaching private data to user-supplied objects (DOM nodes, request contexts)** — are exactly the patterns senior engineers reach for in real code. As a backend engineer, you'll use `WeakMap` for per-request caches keyed by `req` object, per-connection state, lazy-loaded transformers, and prototype-clean "private slots" before classes. The follow-up is always "why not just `Map`?" — answer: GC. Always GC.

## Concepts involved

### Syntax to lock in
```js
const cache = new WeakMap();

function memoize(fn) {
  return function (obj) {
    if (cache.has(obj)) return cache.get(obj);
    const result = fn(obj);
    cache.set(obj, result);
    return result;
  };
}

// Killer use case 2 — private data per object
const _privates = new WeakMap();
class User {
  constructor(name, pass) {
    _privates.set(this, { passwordHash: hash(pass) });
    this.name = name;
  }
  verify(p) { return _privates.get(this).passwordHash === hash(p); }
}
// _privates is invisible from outside; entries vanish when User instance is GC'd.
```

### Runtime / engine behavior
- **Keys MUST be objects** (or symbols in ES2023+). `weakMap.set('a', 1)` throws `TypeError`.
- **Entries are weakly held**: the WeakMap does NOT count as a reference to the key. When the only thing pointing at `key` is the WeakMap itself, the GC reclaims both `key` and its associated `value`.
- **Not iterable**: no `.size`, no `.keys()`, no `.values()`, no `.entries()`, no `for...of`. By design — you can't safely enumerate something that may vanish mid-loop.
- Methods: `get`, `set`, `has`, `delete`. That's it.
- V8 implements WeakMap with ephemeron tables — special GC machinery that handles the "value is reachable iff key is reachable" semantic correctly. Don't roll your own; you can't.
- **`WeakRef`** is a different primitive (single-target weak ref); WeakMap is multi-entry.

### Edge cases (these are the interview traps)
1. **Primitive key throws** — `wm.set(42, 'x')` → `TypeError`. Wrap primitives in objects only if you really need this (and at that point use `Map`).
2. **You can't list contents** — no `wm.size`, no iteration. If you need to know "all cached keys," WeakMap is wrong. Use `Map` + manual eviction.
3. **GC timing is non-deterministic** — `wm.has(key)` may return `true` long after `key`'s last visible reference goes out of scope. The spec only guarantees the entry is "eligible" for collection; engines decide when. Don't test by polling.
4. **Symbols as keys (ES2023)** — `Symbol('x')` works (well-known symbols like `Symbol.iterator` are forbidden). Useful for token-shaped keys without allocating objects.
5. **`delete` returns boolean** — `true` if the key existed, `false` otherwise. Same as `Map`.
6. **No clear() in spec** — there's no `weakMap.clear()`. Allocate a fresh `WeakMap` if you need to wipe.
7. **Re-entrancy** — if `fn(obj)` is recursive and calls back into the memoized version with the same `obj`, you'd loop forever. Set a sentinel before calling: `cache.set(obj, IN_PROGRESS); const r = fn(obj); cache.set(obj, r);`.
8. **Cross-realm objects** — iframe / VM context boundaries: an object from another realm still works as a key. Identity is preserved across realms.
9. **Memoize without WeakMap** — using a `Map` keeps every key alive forever. Classic memory leak. Use WeakMap unless you have a reason not to.
10. **DOM-node use case** — `const data = new WeakMap(); data.set(domNode, { ...stuff });` — when the node is removed from the DOM and dereferenced, the data goes with it. Was the original motivation for adding WeakMap to the spec.

## Brute force approach
Memoize with a plain object: `cache[key.id] = result`. Forces `key` to have an `id`, forces a stringification step, and **leaks** indefinitely. Plain `Map` is better but still leaks. Both are wrong when you want per-object cache that respects object lifetime.

## Optimal approach
`WeakMap` keyed by the input object. `has → get → return` happy path is O(1). On miss, compute, store, return. Memory footprint is bounded by **alive caller objects** — the cache rightsizes itself.

For the private-data variant: one module-level `WeakMap`, keyed by `this` inside class methods. Same shape.

## Solution (JavaScript)

```js
/**
 * Memoize a function whose single argument is an object.
 * Cached results are released when the argument object is GC'd.
 *
 * @template {object} T
 * @template R
 * @param {(arg: T) => R} fn
 * @returns {(arg: T) => R}
 */
function memoizeByObject(fn) {
  const cache = new WeakMap();
  return function memoized(arg) {
    if (typeof arg !== 'object' || arg === null) {
      throw new TypeError('memoizeByObject expects an object argument');
    }
    if (cache.has(arg)) return cache.get(arg);
    const result = fn.call(this, arg);
    cache.set(arg, result);
    return result;
  };
}

/**
 * Multi-arg memoize where SOME args are objects.
 * Uses a nested WeakMap/Map chain so object-args participate as identity keys.
 * Mirrors LeetCode Memoize-II semantics.
 */
function memoizeManyArgs(fn) {
  const root = new Map();
  return function (...args) {
    let node = root;
    for (const a of args) {
      const next = node.get(a);
      if (next) { node = next; continue; }
      const fresh = (typeof a === 'object' && a !== null) ? new WeakMap() : new Map();
      node.set(a, fresh);
      node = fresh;
    }
    const RESULT = Symbol.for('memo.result');
    if (node.has(RESULT)) return node.get(RESULT);
    const r = fn.apply(this, args);
    node.set(RESULT, r);
    return r;
  };
}

/* ---------- Killer use case: per-object private data ---------- */
const _priv = new WeakMap();

class RequestContext {
  constructor(req) {
    _priv.set(this, { startedAt: Date.now(), userId: null });
    this.req = req;
  }
  markUser(id) { _priv.get(this).userId = id; }
  elapsedMs()  { return Date.now() - _priv.get(this).startedAt; }
}
// _priv is invisible from outside; entries vanish when the RequestContext is GC'd.
```

## Step-by-step dry run

Input — memoize an expensive feature flag computation keyed by a `User` object:
```js
const computeFlags = (user) => { /* heavy lookups */ return { canEdit: true }; };
const cached = memoizeByObject(computeFlags);

let u1 = { id: 1 };
let u2 = { id: 1 };           // different object, same shape

cached(u1);                   // miss -> compute -> store
cached(u1);                   // hit -> return cached
cached(u2);                   // miss -> different identity -> compute again

u1 = null;                    // user logs out; no more refs to that object
// at some indeterminate GC time, the WeakMap entry for u1 is reclaimed.
// cached's internal map shrinks WITHOUT us having to call .delete().
```

Trace of the first two calls:
1. `cached(u1)`: `cache.has(u1)` → false. Run `computeFlags(u1)` → `{canEdit:true}`. `cache.set(u1, ...)`. Return.
2. `cached(u1)`: `cache.has(u1)` → true. `cache.get(u1)` → `{canEdit:true}`. Return without recomputing.
3. `cached(u2)`: `u2 !== u1` (different identity even though equal shape). `cache.has(u2)` → false. Recompute. Store.

Why **not `Map`**? After `u1 = null`, the entry would remain in a `Map` forever (the Map's internal reference keeps `u1` alive too — classic leak). WeakMap explicitly avoids this.

## Important takeaways

**Syntax to memorize**
- `new WeakMap()`. Methods: `get/set/has/delete`. That's all.
- **Keys must be objects** (or non-registered symbols in ES2023+).
- No `.size`, no iteration. If you need them, you need `Map`.
- "Memoize per-object" pattern: `if(has) return get; result = fn(...); set; return.`

**Patterns to reuse**
- **Private data per object** — module-level `WeakMap`, keyed by `this` inside methods. Predates `#privateField` and still works in ESM modules without classes.
- **Per-request scoped caches** in Express/Fastify middleware: `req` as the key, derived data as the value. Auto-cleaned at request end.
- **DOM-node tagging** — attach event-handler maps, observer state, or framework metadata without polluting the node itself.
- **Identity-keyed memoization** — when args are objects and you don't want to stringify (and break on cycles).

**Common mistakes**
- Trying to use a primitive key. Fails loudly.
- Trying to iterate a WeakMap. Fails silently (there's no method to call).
- Relying on GC timing for tests. Spec doesn't guarantee any specific moment.
- Caching with `Map` where you really want WeakMap → silent memory growth.
- Forgetting `WeakMap` has no `.clear()`. Reassign a new one if you need a fresh slate.
- Using `WeakMap` as a Set proxy with sentinel values — that's what `WeakSet` exists for.

**Related questions**
- `Map` vs `WeakMap` decision (see `object-vs-map-vs-set.md`).
- LRU Cache — why is **Map** the right tool and WeakMap the **wrong** one? (LRU needs ordering + sized eviction; WeakMap has neither.)
- LeetCode "Memoize II" — multi-arg memoization with object keys.
- `WeakRef` + `FinalizationRegistry` — adjacent primitives.

## Variants

1. **WeakMap-backed memoize with manual invalidation** — expose `.invalidate(obj)` that calls `cache.delete(obj)`. Useful when the input mutates and you want to bust the cache eagerly.

2. **Multi-arg memoize (nested WeakMap chain)** — LeetCode #2630. Each argument is a level in a chain of WeakMap/Map nodes; object args use WeakMap, primitive args use Map. The leaf node stores the result under a sentinel symbol. Solves the "memoize function with mixed object + primitive args without losing GC."

3. **Per-request request-scoped memoize** — Express middleware: `const get = (req, fn) => { let m = scopes.get(req); if (!m) scopes.set(req, m = new Map()); ... }`. Combined with WeakMap on `req`, gives you free cleanup when the response is sent.

## Revision notes

> **WeakMap — 60 second recap**
> - Keys MUST be objects (or non-well-known symbols). Primitive keys throw.
> - Entries are **weakly held**: GC'd when the key has no other references.
> - **Not iterable.** No `.size`, no `keys()`, no `values()`. No `clear()`.
> - Methods: `get`, `set`, `has`, `delete`. Period.
> - Killer use cases: (1) per-object memoize without leaks, (2) private data on user-supplied objects (DOM nodes, request contexts).
> - **Trap:** trying to iterate or count entries. **Trap:** primitive key. **Trap:** caching with `Map` where you wanted WeakMap → unbounded growth.
> - Pair with `WeakRef` / `FinalizationRegistry` for advanced lifecycle hooks.
