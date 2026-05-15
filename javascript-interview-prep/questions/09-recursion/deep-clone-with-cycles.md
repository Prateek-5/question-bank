# Implement `deepClone(obj)` — handle cycles, Date, RegExp, Map, Set

## Source
- Canonical machine-coding interview problem (variants on every JS interview list).
- Modern reference: `structuredClone()` (Node 17+, all evergreen browsers).
- Common follow-up to "what does `JSON.parse(JSON.stringify(obj))` get wrong?"

## Why this question matters in interviews
Deep clone is the **single best** question to probe recursion depth, type-awareness, and reference identity in one sitting. The interviewer is watching for four moves: (1) immediately dismiss `JSON.parse(JSON.stringify(...))` and list its failure modes, (2) reach for `WeakMap` for cycle tracking — keyed by original, valued by clone, (3) handle the standard built-in types (Date, RegExp, Map, Set, Array, plain Object), and (4) mention `structuredClone` exists in Node 17+ but implement it manually because the interviewer wants the algorithm. As a backend engineer this comes up in: state immutability for reducer-style code, snapshotting cache entries before mutation, defensive copies before passing to untrusted handlers, event payloads.

## Concepts involved

### Syntax to lock in
```js
// The wrong default answer — interviewer wants you to reject it
const bad = JSON.parse(JSON.stringify(obj));
// Loses: functions, Date (→ string), undefined, RegExp (→ {}), Map/Set,
// BigInt (throws), Symbol keys, prototype chain. Throws on cycles.

// Modern built-in — mention but implement manually
const good = structuredClone(obj);   // Node 17+, all browsers since 2022
// Handles cycles, typed arrays, Date, RegExp, Map, Set. Doesn't clone functions/Symbols.
```

```js
// The interview-level manual version
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;  // base case
  if (seen.has(value)) return seen.get(value);                    // cycle break
  // ...dispatch on type, register clone in `seen` BEFORE recursing on children
}
```

### Runtime / engine behavior
- **Cycle handling needs a "seen" map keyed by reference identity.** A regular `Map` works, but `WeakMap` allows GC of original objects once the clone is done — best practice.
- **Register before recursing.** If A references B which references A, you must put A's clone into `seen` *before* you recurse into A's properties, otherwise the recursion on B → A loops forever.
- **`Object.keys` returns string keys only.** For Symbol keys use `Object.getOwnPropertySymbols`. For non-enumerable use `Reflect.ownKeys`. Stick with `Object.keys` for interview-level unless asked.
- **Prototype chain is usually not copied.** Plain `{}` clones lose any custom prototype. To preserve it: `Object.create(Object.getPrototypeOf(obj))`. Class instances are a deep rabbit hole — typically out of scope unless asked.
- **Stack depth = object nesting depth.** A 10k-deep linked list `{next: {next: ...}}` overflows. V8 has no TCO. For depth-safety, use an explicit stack.
- `structuredClone` runs in the structured-clone algorithm — handles a wider set than what you'd hand-roll, including TypedArray, ArrayBuffer, Blob.
- **Functions are NOT cloneable.** Neither manual versions nor `structuredClone` copy functions. Decide: copy by reference (`return value`) or throw.

### Edge cases (interview traps)
1. **Primitives** — strings, numbers, booleans, `null`, `undefined`, BigInt, Symbol are immutable; return as-is. The `typeof !== 'object'` check covers all except `null`, which must be explicit (`typeof null === 'object'`).
2. **Cycles** — `obj.self = obj`. Without `WeakMap`, recursion hangs and crashes.
3. **Multiple references to the same object** — `[a, a]` where `a` is an object. The clone should share the cloned `a` too (one allocation, two references). The `seen` map naturally handles this; without it you'd duplicate.
4. **Date** — `new Date(value.getTime())`. Don't just clone its properties (it has none enumerable).
5. **RegExp** — `new RegExp(value.source, value.flags)`. Reset `lastIndex` if state matters.
6. **Map / Set** — iterate entries, recursively clone keys and values. For `Map`, keys can be objects — recurse on them too.
7. **Arrays vs plain objects** — `Array.isArray` first; otherwise `{}` for plain. Constructors of subclasses (`new value.constructor()`) is fancier; stick with plain for interview unless asked.
8. **Functions** — usually return by reference (skip). Don't try to `eval(fn.toString())` — it loses closures.
9. **`Object.prototype.toString.call(x)`** — robust type tag (`[object Date]`, `[object RegExp]`). Use it if `instanceof` worries you across realms.
10. **Property descriptors** — getters/setters, non-enumerable, frozen objects. Out of scope unless asked; mention `Object.getOwnPropertyDescriptors` + `Object.defineProperties` for the deluxe version.

## Brute force approach
`JSON.parse(JSON.stringify(obj))`. List its failure modes upfront so the interviewer knows you know:
- Functions → omitted.
- `undefined` values → omitted (in objects) or → `null` (in arrays).
- `Date` → ISO string (not Date).
- `RegExp` → `{}`.
- `Map` / `Set` → `{}`.
- `BigInt` → throws.
- Cycles → throws.
- Class instances → plain object (prototype lost).

Use only when you know the payload is plain JSON-safe data.

## Optimal approach
Recursive type-dispatched clone. `WeakMap` tracks `original → clone` to short-circuit cycles. Register the clone in the map **before** recursing into children. Type dispatch via a series of `instanceof` checks (Date, RegExp, Map, Set, Array, plain object). O(n) time over total nodes, O(d) call stack for recursion or O(n) heap stack for iterative variant.

## Solution (JavaScript)

```js
/**
 * Deep clone an arbitrary JS value with cycle support.
 * Handles: primitives, plain objects, arrays, Date, RegExp, Map, Set.
 * Functions are returned by reference (not deep-cloned).
 *
 * @param {*} value
 * @param {WeakMap} [seen] — original → clone tracker (cycle break)
 * @returns {*} a deep copy of `value`
 */
function deepClone(value, seen = new WeakMap()) {
  // ---- Base case: primitives + null + functions ----
  if (value === null || typeof value !== 'object') return value;
  // (functions are 'function', not 'object', so they fall into the line above
  //  and are returned by reference — adjust if you need to clone them differently)

  // ---- Cycle break: already cloned this reference ----
  if (seen.has(value)) return seen.get(value);

  // ---- Type dispatch ----
  let clone;

  if (value instanceof Date) {
    clone = new Date(value.getTime());
    seen.set(value, clone);
    return clone;
  }

  if (value instanceof RegExp) {
    clone = new RegExp(value.source, value.flags);
    clone.lastIndex = value.lastIndex;
    seen.set(value, clone);
    return clone;
  }

  if (value instanceof Map) {
    clone = new Map();
    seen.set(value, clone);                  // register BEFORE recursing
    for (const [k, v] of value) {
      clone.set(deepClone(k, seen), deepClone(v, seen));
    }
    return clone;
  }

  if (value instanceof Set) {
    clone = new Set();
    seen.set(value, clone);
    for (const v of value) clone.add(deepClone(v, seen));
    return clone;
  }

  if (Array.isArray(value)) {
    clone = [];
    seen.set(value, clone);                  // BEFORE recursing
    for (let i = 0; i < value.length; i++) {
      if (i in value) clone[i] = deepClone(value[i], seen);
    }
    return clone;
  }

  // ---- Plain object (fallback) ----
  clone = Object.create(Object.getPrototypeOf(value));   // preserve prototype
  seen.set(value, clone);
  for (const key of Object.keys(value)) {
    clone[key] = deepClone(value[key], seen);
  }
  // For Symbol-keyed properties (uncommon ask, but easy add):
  // for (const sym of Object.getOwnPropertySymbols(value)) {
  //   clone[sym] = deepClone(value[sym], seen);
  // }
  return clone;
}
```

## Step-by-step dry run

Input — object with a cycle and shared reference:
```js
const shared = { x: 1 };
const original = {
  a: 1,
  d: new Date('2024-01-01'),
  arr: [shared, shared],
  m: new Map([['k', shared]]),
};
original.self = original;     // CYCLE

const copy = deepClone(original);
```

Trace:
1. Enter `deepClone(original)`. Not primitive. Not in `seen`. Not Date/RegExp/Map/Set/Array → plain object branch.
2. Create `copy = {}`. `seen.set(original, copy)`. (Registered BEFORE recursing — critical.)
3. Loop keys of `original`:
   - `a`: primitive `1` → `copy.a = 1`.
   - `d`: Date → enter recursion. Date branch: `new Date(...)`, register, return. `copy.d` is a fresh Date with same time.
   - `arr`: array → enter recursion. Create `[]`, register `seen.set(arr, [])`. Loop:
     - index 0: `shared` → not in seen → plain object branch. Create `{}`, register `seen.set(shared, sharedClone)`. `sharedClone.x = 1`. Return.
     - index 1: `shared` again → **in seen** → return existing `sharedClone`. The two array slots now point to the SAME clone. (Reference identity preserved.)
   - `m`: Map → create `new Map()`, register. Iterate `[['k', shared]]`:
     - clone key `'k'` (primitive) → `'k'`.
     - clone value `shared` → **in seen** → return existing `sharedClone`. Same reference shared with `arr[0]` / `arr[1]`.
   - `self`: `original` → **in seen** → return `copy` itself. **Cycle preserved.**

Assertions you'd run:
```js
copy !== original                        // true — different reference
copy.d !== original.d                    // true — fresh Date
copy.d.getTime() === original.d.getTime() // true — same instant
copy.arr[0] === copy.arr[1]              // true — shared identity preserved
copy.m.get('k') === copy.arr[0]          // true — shared across containers
copy.self === copy                       // true — cycle preserved
```

## Important takeaways

**Syntax to memorize**
- Base: `if (v === null || typeof v !== 'object') return v;`
- Cycle break: `if (seen.has(v)) return seen.get(v);`
- **Register BEFORE recursing**: `seen.set(original, clone);` then populate `clone`.
- Date: `new Date(v.getTime())`. RegExp: `new RegExp(v.source, v.flags)`.
- `Object.create(Object.getPrototypeOf(v))` to preserve prototype, not `{}`.

**Patterns to reuse**
- **WeakMap-as-seen-set** keyed by reference identity is the universal cycle-handling tool. Same recipe for: deep equality with cycles, JSON-with-cycles serializer, garbage-cycle-safe traversal.
- "Register first, then recurse" is the cycle-handling discipline you'll repeat in tree-with-back-edges, graph DFS, dependency-graph resolvers.
- Type-dispatch ladder via `instanceof` — same pattern as a custom serializer / `JSON.stringify` replacer.

**Common mistakes**
- Defaulting to `JSON.parse(JSON.stringify(obj))`. Even when it works, it's a tell that you don't know the edge cases. State them upfront, then walk past it.
- Forgetting to register the clone before recursing → cycles cause infinite recursion → stack overflow.
- Cloning Date by spreading: `{ ...date }` produces `{}` — Date has no enumerable own props. Use `new Date(date.getTime())`.
- Cloning RegExp by spreading: same problem; you also lose the source and flags.
- Cloning Map/Set by spreading into `{}` or `[]` — wrong type. Use `new Map()` / `new Set()` and iterate entries.
- Cloning class instances and expecting the prototype to survive — `{}` loses it. Use `Object.create(Object.getPrototypeOf(v))`.
- Not handling `null` separately — `typeof null === 'object'` will crash `Object.keys(null)`.

**Related questions**
- `structuredClone(value)` — Node 17+, native. Cite it; explain what it doesn't handle (functions, Symbol keys, prototype chain for class instances).
- Deep equality with cycle support — same WeakMap shape, but tracking `(a, b) -> bool` pairs.
- Immutable update helpers (`immer`'s `produce`) — copy-on-write deep clone.
- JSON stringifier that handles cycles (replace cycle with `"[Circular]"`).

## Variants

1. **Preserve property descriptors** — getters, non-enumerable, frozen. Use `Object.getOwnPropertyDescriptors` + `Object.defineProperties`.

2. **Clone Symbol-keyed properties** — `Object.getOwnPropertySymbols(v)` + recurse on each.

3. **Iterative deep clone** — explicit stack of `{src, dst, key, value}` work items. Survives 100k-deep linked lists where the recursive version overflows.

4. **Type-extensible clone** — accept a `cloneCustom(value, seen)` callback for unknown types (e.g. user's class instances). Library-style.

5. **Async deep clone** — values may be Promises; await them and clone the resolved value.

6. **Compare to `structuredClone`** — interviewer asks "why not just use the built-in?" Correct answer: "I would — but the exercise is to demonstrate the algorithm. In production with Node 17+, `structuredClone` is the right choice unless I need to clone functions or custom class instances."

## Revision notes

> **deepClone(obj) — 60 second recap**
> - **Base case:** primitives + null → return as-is.
> - **Cycle break:** `WeakMap(original → clone)` checked first.
> - **Register BEFORE recursing** — otherwise cycles loop forever.
> - **Type dispatch:** Date → `new Date(getTime)`, RegExp → `new RegExp(source, flags)`, Map → iterate + clone both k/v, Set → iterate + clone, Array → loop, plain → `Object.create(getPrototypeOf)`.
> - **Skip:** functions (return by reference), Symbol keys (mention but skip).
> - **Reject:** `JSON.parse(JSON.stringify(...))` — lists 7+ failure modes (functions, Date, RegExp, Map/Set, BigInt, undefined, cycles).
> - **Modern:** `structuredClone(value)` exists in Node 17+; same edges except handles TypedArray.
> - **V8 has no TCO** — recursive version stack-overflows on 10k-deep nesting. Iterative-with-stack variant if asked.
> - O(n) time, O(n) seen-map + O(d) call stack.
