# Object vs Map vs Set — when to use which

## Source
- Canonical conceptual interview question. Surfaces in every senior JS round.
- MDN reference: Map / Set / WeakMap / WeakSet docs.

## Why this question matters in interviews
This is the question that separates "I use JavaScript" from "I understand JavaScript." Every senior engineer has reached for `{}` as a hash and gotten burned by **prototype pollution**, by **string-only keys**, by **`for...in` walking the prototype**, by **`.length` being O(n)**, or by **JSON serialization breaking on Maps**. The interviewer wants you to articulate the trade-offs *crisply* and pick the right tool. Backend engineers feel this most when modeling caches (Map), dedup sets (Set), config lookups (Object), and per-request state (WeakMap). A clean decision table — memorized — is your edge.

## Concepts involved

### Syntax to lock in

```js
// --- Object as map (legacy / config / JSON-friendly) ---
const o = Object.create(null);   // null-prototype = no inherited keys
o['foo'] = 1;
Object.keys(o).length;            // size = O(n)
'foo' in o;                       // has = O(1) but walks prototype if not Object.create(null)

// --- Map (general-purpose keyed collection) ---
const m = new Map();
m.set({}, 1);                     // ANY key type — even objects, NaN
m.size;                           // O(1)
m.has(k); m.get(k); m.delete(k);
for (const [k, v] of m) { /* insertion order */ }

// --- Set (dedup / membership) ---
const s = new Set([1, 2, 2, 3]);  // -> {1, 2, 3}
s.has(2);  s.size;                // both O(1)
const unique = [...new Set(arr)]; // canonical dedup idiom

// --- WeakMap / WeakSet (GC-friendly, object keys only) ---
const wm = new WeakMap();         // entries vanish when key is GC'd
const ws = new WeakSet();         // membership test for objects with auto-cleanup
```

### Runtime / engine behavior
- **Object**: implemented as a hidden-class + inline-cache-friendly property bag in V8. Fast for static shapes (declared keys at construction time, never deleted), slow when treated as a dictionary with churn. JS engines deoptimize objects with dynamic key insertion/deletion into a slower "dictionary mode" hash table.
- **Map**: always a hash table with parallel insertion-order index. Predictable O(1) — no shape-based deopt risk.
- **Set**: same backing as Map but stores only keys.
- **Object key coercion**: every key is stringified (except symbols). `o[1] === o['1']`. `o[{}] === o['[object Object]']` — all object keys collide on a single bucket.
- **Map key identity**: no coercion. `m.set(1, 'a'); m.set('1', 'b')` are distinct entries. `m.set(NaN, 'x'); m.get(NaN)` works (SameValueZero equality).
- **Iteration order**: Map and Set iterate in **insertion order**. Object property iteration order is "integer-like keys ascending, then strings in insertion order, then symbols in insertion order" — annoying gotcha when keys look like numbers.
- **JSON**: `JSON.stringify({a:1})` → `'{"a":1}'`. `JSON.stringify(new Map([['a',1]]))` → `'{}'`. Map needs `JSON.stringify([...m])`.

### The decision table

| Question | Object | Map | Set | WeakMap | WeakSet |
|---|---|---|---|---|---|
| **Key types allowed** | string, symbol | **any** value | n/a (values are the "keys") | object, symbol | object |
| **Iterates in insertion order?** | Mostly, but integer-like keys sort numerically | **Yes, strictly** | Yes, strictly | **No — not iterable** | No |
| **Walks prototype chain on `in` / `for...in`?** | Yes (use `Object.hasOwn` or `Object.create(null)`) | No | No | No | No |
| **`size` lookup** | `Object.keys(o).length` — **O(n)** | **`m.size` — O(1)** | **`s.size` — O(1)** | None | None |
| **Has/Get/Set/Delete** | O(1) avg, slow path on shape churn | **O(1) avg, predictable** | O(1) avg | O(1) avg | O(1) avg |
| **Serializable via `JSON.stringify`?** | **Yes, natively** | No — `[...m]` first | No — `[...s]` first | No (and you can't iterate) | No |
| **Prototype pollution risk?** | **Yes** (`o.__proto__ = ...`) unless `Object.create(null)` | No | No | No | No |
| **GC-friendly (keys auto-released)?** | No | No | No | **Yes** | Yes (for values) |
| **Allows `NaN` as a key?** | No (coerced to `"NaN"`) | **Yes** (SameValueZero) | Yes | n/a (object keys only) | n/a |
| **Best for** | Static config, JSON, fixed-shape records | Dynamic dictionaries, caches, frequent add/remove, non-string keys | Membership/dedup | Per-object cache, private data, DOM-attached state | Object membership with auto-cleanup |
| **Worst for** | Dynamic-key churn (deopt), object keys, JSON-unfriendly key strings | Anything needing JSON round-trip | Anything needing key→value lookup | Anything needing iteration/size | Anything needing iteration/size |

### Edge cases (the interview traps)
1. **`{}.toString = ...`** — every plain object inherits `toString`, `hasOwnProperty`, `__proto__` etc. `o.hasOwnProperty` collides with a user-supplied `'hasOwnProperty'` key. Use `Object.hasOwn(o, k)` or `Object.create(null)`.
2. **Integer-like keys reorder** — `{2:'a', 1:'b', 10:'c'}` iterates as `1, 2, 10`. Map preserves your literal insertion order.
3. **`Map` key identity** — `m.set({}, 1); m.get({})` is `undefined`. Two object literals are different keys. Same trap as `===` on objects.
4. **`Set` membership for objects** — `new Set([{},{}]).size === 2`. Same identity rule.
5. **`JSON.stringify(map)` is `'{}'`** — silently. Senior bug bait. Convert: `JSON.stringify([...m])` then parse back with `new Map(parsed)`.
6. **Cloning** — `structuredClone` handles Map/Set; `JSON.parse(JSON.stringify(...))` does not. Spread `[...m]` is shallow.
7. **`Object.create(null)`** — has no `toString`, no `valueOf`. `console.log` may print oddly. Iteration works fine, but `${o}` throws.
8. **`for...in` vs `for...of`** — `for...in` is for object string keys (walks prototype!). `for...of` is for iterables (Map, Set, Array). Mixing them up is a top-tier mistake.
9. **Map's spread `{...m}`** — does **nothing useful**. Map isn't a plain object; spreading a Map into an object literal yields `{}`. Use `Object.fromEntries(m)`.
10. **`Object.fromEntries(m)` ↔ `new Map(Object.entries(o))`** — the two bridges between the worlds. Memorize them.

## Brute force approach
Use `{}` for everything. It "works" until your keys aren't strings, until they collide with `Object.prototype`, until you need O(1) size, until you need ordered iteration, until you have to deal with a user-supplied `__proto__` key. Then you fix bugs forever.

## Optimal approach
Pick the data structure by the **constraints** you have:

- **Need JSON round-trip + static keys?** → Object (preferably `Object.create(null)` if keys come from user input).
- **Need dynamic add/remove, predictable O(1), non-string keys, or insertion-order iteration?** → Map.
- **Need to test membership / dedup?** → Set.
- **Need per-object data with automatic cleanup?** → WeakMap (or WeakSet for membership-only).

If unsure, **default to `Map`**. It's strictly more powerful than `Object`-as-dict in every dimension except JSON-friendliness and direct property syntax.

## Solution (JavaScript)

```js
/* -------- Object as a record (static shape, JSON-shaped) -------- */
const config = {
  host: 'localhost',
  port: 5432,
  ssl: false,
};
JSON.stringify(config); // works natively

/* -------- Object as a safe dictionary (user-supplied keys) -------- */
const lookup = Object.create(null);
for (const { key, value } of userInput) {
  lookup[key] = value;       // safe: no inherited __proto__
}

/* -------- Map: cache with dynamic non-string keys -------- */
const sessionByUser = new Map();   // key = user object
sessionByUser.set(user, { token, expiresAt });
sessionByUser.size;                // O(1)

/* -------- Set: dedup / membership -------- */
const visited = new Set();
function bfs(start) {
  const queue = [start];
  while (queue.length) {
    const node = queue.shift();
    if (visited.has(node)) continue;   // O(1)
    visited.add(node);
    queue.push(...node.children);
  }
}

/* -------- WeakMap: per-object private state -------- */
const _priv = new WeakMap();
class Connection {
  constructor(socket) {
    _priv.set(this, { socket, buffered: [] });
  }
  send(msg) { _priv.get(this).buffered.push(msg); }
}
// When a Connection instance is GC'd, its _priv entry is auto-released.

/* -------- Bridges -------- */
const obj = Object.fromEntries(map);        // Map -> plain object (lossy if non-string keys)
const map2 = new Map(Object.entries(obj));  // Plain object -> Map
const jsonable = [...map];                  // Map -> serializable [[k,v],...]
const map3 = new Map(JSON.parse(jsonStr));  // round-trip
```

## Step-by-step dry run

Scenario — "Build a frequency counter for user IDs streaming in." Compare the four options:

**Option A — plain object** (the rookie answer):
```js
const counts = {};
for (const id of stream) {
  counts[id] = (counts[id] || 0) + 1;
}
Object.keys(counts).length; // O(n) just to know "how many unique"
```
Problem: if `id === '__proto__'`, you pollute `Object.prototype`. If IDs are integers, iteration reorders them numerically — bad if you needed first-seen order.

**Option B — null-prototype object** (safer rookie):
```js
const counts = Object.create(null);
// same code; no prototype pollution. But still O(n) size and integer-key reorder.
```

**Option C — `Map`** (the right answer):
```js
const counts = new Map();
for (const id of stream) {
  counts.set(id, (counts.get(id) || 0) + 1);
}
counts.size;          // O(1)
// Iteration is in first-seen insertion order. Works with object IDs too.
```

**Option D — `Map<string, Set<...>>`** if values are also collections:
```js
const usersByRole = new Map(); // role -> Set<userId>
for (const { role, id } of stream) {
  if (!usersByRole.has(role)) usersByRole.set(role, new Set());
  usersByRole.get(role).add(id);
}
// O(1) membership inside each bucket. Set dedupes for free.
```

The interviewer wants you to land on C or D and **explain why** A/B are worse: O(n) size, prototype pollution risk, integer-key reorder, string-only keys.

## Important takeaways

**Syntax to memorize**
- Bridges: `Object.fromEntries(map)` and `new Map(Object.entries(obj))`.
- Map → JSON: `JSON.stringify([...m])`. JSON → Map: `new Map(JSON.parse(s))`.
- Dedup: `[...new Set(arr)]`.
- Safe dict: `Object.create(null)`.

**Patterns to reuse**
- Default to `Map` for dynamic key/value collections.
- `Object.create(null)` whenever **user input** decides keys.
- `WeakMap` for "per-object data" that should clean up automatically.
- `Map<K, Set<V>>` for one-to-many relationships.
- `Map<K, V[]>` when order or duplicates matter; `Map<K, Set<V>>` when uniqueness matters.

**Common mistakes**
- Reaching for `{}` and getting bitten by `__proto__` pollution.
- `JSON.stringify(map)` returning `'{}'` and assuming a bug elsewhere.
- `Object.keys(o).length` on a hot path — should be `map.size`.
- `for...in` on a Map (does nothing useful) or `for...of` on a plain object (throws — not iterable).
- Spreading a Map into an object literal: `{...m}` is empty. Use `Object.fromEntries(m)`.
- Storing objects in a `Set` and expecting structural dedup — only identity is checked.

**Related questions**
- LRU Cache using Map (insertion-order trick).
- WeakMap memoize (per-object cache).
- `groupBy` returning Map vs Object (ES2024 added both).
- Implement Set using object (`{[k]: true}`) — what's wrong with that.

## Variants

1. **Set operations (union / intersection / difference)** — ES2025 ships native `Set.prototype.union/intersection/difference/symmetricDifference/isSubsetOf/isSupersetOf/isDisjointFrom`. Until you can rely on them: `new Set([...a].filter(x => b.has(x)))` for intersection, etc.

2. **Ordered set / unique-by-key** — `Set` is already insertion-ordered. For "unique by extracted key," reduce into a `Map` keyed by `keyFn(item)`: `const byKey = new Map(items.map(i => [keyFn(i), i]))`.

3. **Object pool with WeakSet** — track which objects in a pool are "checked out" using a WeakSet so they don't leak when the consumer forgets to release.

## Revision notes

> **Object vs Map vs Set — 60 second recap**
> - **Object**: string/symbol keys only, prototype chain, `Object.keys().length` is O(n), JSON-native. Best for static records and config.
> - **Map**: any key type (incl. objects, NaN), insertion-ordered iteration, `.size` is O(1), no prototype, no native JSON. Best for dynamic dicts and caches.
> - **Set**: insertion-ordered membership/dedup. `[...new Set(arr)]` is the idiom.
> - **WeakMap / WeakSet**: keys must be objects, entries auto-GC'd, NOT iterable, NO size. Best for per-object data + DOM tagging.
> - **Bridges**: `Object.fromEntries(m)` and `new Map(Object.entries(o))`. `JSON.stringify([...m])` to round-trip.
> - **Traps**: `{}` and prototype pollution; integer-like object keys reorder; `JSON.stringify(map) === '{}'`; `for...in` on Map does nothing.
> - Default to **Map** when in doubt; reach for **Object** only for static/JSON-shaped data.
