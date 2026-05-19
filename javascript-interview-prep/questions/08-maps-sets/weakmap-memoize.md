# `WeakMap`-backed memoization + private fields

> **Difficulty:** Senior   |   **Time:** ~12 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md), [weakref-finalization-registry.md](./weakref-finalization-registry.md)
>
> **Source:** Pre-private-fields private-data pattern. Lodash `_.memoize` for object keys.

---

## 1. Problem statement

Memoize per-object without preventing GC of that object. Also: attach private metadata to instances.

**Verification examples**

```js
const cache = new WeakMap();
function memoizedHash(obj) {
  if (cache.has(obj)) return cache.get(obj);
  const h = expensiveHash(obj);
  cache.set(obj, h);
  return h;
}

let req = {url: '/api'};
memoizedHash(req);                       // compute + cache
req = null;                              // last strong ref dropped
// GC reclaims req AND cache entry — no leak

// Private fields pattern
const _privates = new WeakMap();
class User {
  constructor(name) {
    _privates.set(this, { passwordHash: hash(name) });
    this.name = name;
  }
  check(pass) { return _privates.get(this).passwordHash === hash(pass); }
}
```

**Constraints**
- Keys MUST be objects (or symbols in ES2023+).
- Entries are weakly held — GC'd when key has no other refs.
- Not iterable; no size; no clear().
- `wm.set('a', 1)` throws TypeError.

---

## 2. Plain-English restatement

`WeakMap` lets you attach data to an object without preventing its garbage collection. When the only reference to the key is the WeakMap, both vanish together.

---

## 3. Why this matters in interviews

Under-explained data structure. Senior signal: articulate (a) object-key constraint, (b) GC, (c) non-iterable. Use cases: per-request cache, per-instance private data.

---

## 4. Mental model

```
   WeakMap:
     keys MUST be objects (or symbols ES2023+).
     held weakly — Map doesn't count as a reference.
     entries GC'd when key has no other strong refs.
     NOT iterable: no size, keys(), values(), entries(), for..of.
   
   Why not iterable?
     GC timing is unspecified.
     If you could iterate, snapshot inconsistency: an entry might vanish mid-loop.
   
   Difference from Map:
     Map: strong keys; explicit lifecycle; iterable.
     WeakMap: weak keys; GC-managed; private/internal use.
   
   Use cases:
     1. Per-object memoization — cache derived data without leaking.
     2. Private state — attach #-data to instances pre-class-fields.
     3. Per-request context — req → metadata.
     4. DOM node mapping — node → handler state; auto-released on remove.
   
   Anti-patterns:
     Iterating WeakMap (impossible).
     WeakMap keyed by primitives (TypeError).
     Using WeakMap to track instances (no way to list them).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why must keys be objects?
> 2. What's the GC observability of WeakMap?
> 3. Why no `.size`?

---

## 6. Brute force — walked through

```js
// Map for memoization — LEAKS
const cache = new Map();
function memo(obj) {
  if (cache.has(obj)) return cache.get(obj);
  const v = compute(obj);
  cache.set(obj, v);    // ← strong ref; obj never GC'd while cache lives
  return v;
}
// Long-lived cache → all objects ever passed in stay forever. Memory leak.
```

WeakMap fixes the leak.

---

## 7. The unlocking insight

> **`WeakMap` keys must be objects, are held weakly, entries auto-GC'd. Non-iterable by design (GC observability). Perfect for per-instance memoization / private fields.**

Three properties:

1. **Object-only keys**.
2. **Weakly held** — GC reclaims.
3. **Non-iterable** by design.

---

## 8. Solution (annotated)

```js
// Memoization keyed by object
const memoCache = new WeakMap();

function memoizeByObject(fn) {
  return function (obj) {
    if (memoCache.has(obj)) return memoCache.get(obj);                     // step 1: cached
    const result = fn(obj);
    memoCache.set(obj, result);                                            // step 2: store
    return result;
  };
}

// Multi-arg memo using WeakMap-of-WeakMap (pre-Record/Tuple)
function memoizeMultiArg(fn) {
  const root = new WeakMap();
  return function (...args) {
    let m = root;
    for (let i = 0; i < args.length - 1; i++) {
      if (!m.has(args[i])) m.set(args[i], new WeakMap());                  // step 3: chain
      m = m.get(args[i]);
    }
    const last = args[args.length - 1];
    if (m.has(last)) return m.get(last);
    const result = fn(...args);
    m.set(last, result);
    return result;
  };
}

// Private fields via WeakMap
const _state = new WeakMap();
class Connection {
  constructor(url) {
    _state.set(this, {                                                      // step 4: private bag
      url,
      isOpen: false,
      socket: null,
    });
  }
  open() {
    const s = _state.get(this);
    s.socket = createSocket(s.url);
    s.isOpen = true;
  }
  close() {
    const s = _state.get(this);
    if (s.socket) s.socket.close();
    s.isOpen = false;
  }
}
// _state invisible from outside. Entries GC'd when Connection instance is.
```

**Try it yourself**

```js
// Per-request context (Express-like middleware)
const reqContext = new WeakMap();
app.use((req, res, next) => {
  reqContext.set(req, { traceId: genTraceId(), startTime: Date.now() });
  next();
});
// When req is GC'd after response, context auto-cleaned.

// DOM node → handler state
const handlerState = new WeakMap();
function attachHandler(node) {
  handlerState.set(node, { clicks: 0 });
  node.addEventListener('click', () => {
    handlerState.get(node).clicks++;
  });
}
// Remove node from DOM + drop refs → entry GC'd.

// Won't work — primitive key
try {
  new WeakMap().set('string', 1);                            // TypeError
} catch (e) { console.error(e); }

// Won't work — iteration
try {
  for (const [k, v] of new WeakMap()) {}                     // TypeError
} catch (e) {}

// No size property
new WeakMap().size;                                          // undefined

// ES2023: symbol keys allowed
const wm = new WeakMap();
wm.set(Symbol('key'), 'value');                               // works in modern engines
```

---

## 9. Step-by-step dry run

```
function memo with Map vs WeakMap:

Map version:
  const cache = new Map();
  let req = {url:'/a'};
  memo(req) → cache.set(req, result).
  req = null;
  cache still holds req strongly.
  GC: cannot collect req. Memory leak.

WeakMap version:
  const cache = new WeakMap();
  let req = {url:'/a'};
  memo(req) → cache.set(req, result).
  req = null;     ← drop last user reference.
  GC: req is now unreferenced (WeakMap doesn't count).
  GC reclaims req. cache entry also dropped.
  No way to observe this directly — by design.

Private fields:
  const _p = new WeakMap();
  class C {
    constructor() { _p.set(this, {secret: 42}); }
    get() { return _p.get(this).secret; }
  }
  const c = new C();
  c.get();    // 42
  _p          // not exported; consumers can't reach _p.
  c = null;   // C instance GC'd; _p entry vanishes.

  Compare to public field:
    class C { secret = 42; }
    c.secret    // exposed.

  Compare to # private (ES2022):
    class C { #secret = 42; get() { return this.#secret; } }
    Native; same effect; no WeakMap needed.
```

---

## 10. Common confusion + traps

1. **Primitive key** — TypeError.
2. **Iterate / size** — impossible.
3. **Use to track all instances** — wrong tool; use plain Map.
4. **Holding strong ref elsewhere** — pins object alive; WeakMap can't help.
5. **`clear()`** — not available; replace WeakMap with new one.
6. **`delete()`** works but no `size` change observable.
7. **GC timing** — non-deterministic; tests are flaky.

---

## 11. Senior follow-ups & variants

### Variant 1 — Class private fields (ES2022)
`class { #foo = 1 }` — native, replaces WeakMap-private-bag pattern.

### Variant 2 — WeakRef + FinalizationRegistry
For cleanup callbacks on GC.

### Variant 3 — WeakSet
Same idea, set semantics — `visited.has(node)`.

### Variant 4 — Symbol keys (ES2023)
WeakMap can use symbols.

### Variant 5 — DOM node → state
Auto-cleanup when node removed.

---

## 12. How to think aloud

> "WeakMap solves 'attach data to objects without preventing GC.' Keys MUST be objects (or symbols in ES2023+) — primitive keys throw TypeError. Entries are weakly held: the WeakMap doesn't count as a reference, so when the only reference to a key is the WeakMap itself, GC reclaims both. Not iterable by design (no `size`, `keys()`, `values()`, `entries()`, `for..of`) — GC timing is unspecified, so you can't safely enumerate. Two killer use cases: (1) Per-object memoization — `WeakMap<obj, derivedResult>`; long-lived cache without leaking objects ever passed in. (2) Private state pre-class-fields — `WeakMap<instance, {private bag}>`; class methods read via the closure; consumers can't reach the WeakMap. ES2022 native `#field` mostly replaces this pattern, but WeakMap pattern still useful for cross-class private state. Anti-patterns: WeakMap to track all instances (can't iterate, can't list); WeakMap keyed by primitives (TypeError); using WeakMap where strong refs exist elsewhere (no GC benefit). Compare to WeakSet: same semantics, set-of-objects — useful for 'visited' flags. ES2023 symbol keys allowed. WeakRef + FinalizationRegistry for finer cleanup. Trap: primitive key; iteration; tracking via WeakMap; assuming GC timing."

---

## 13. 60-second revision

> - **Keys MUST be objects** (or symbols ES2023+).
> - **Weakly held** — GC reclaims.
> - **Not iterable** — no `size`, no `keys()`, etc.
> - **Per-object memo** — no leak.
> - **Private state bag** — pre-#-fields.
> - **`# private fields` (ES2022)** replaces many uses.
> - **WeakSet** for membership.
> - **GC timing non-deterministic.**
> - **Trap:** primitive key; iterate; track instances; assume timing.

---

**Related:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [weakref-finalization-registry.md](./weakref-finalization-registry.md) · [`10-machine-coding-patterns/memoize.md`](../10-machine-coding-patterns/memoize.md) · [`02-closures/private-state-with-closure.md`](../02-closures/private-state-with-closure.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
