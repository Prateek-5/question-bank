# Implement `deepClone(value)` with cycle handling

## Source
- Canonical machine-coding interview problem (LeetCode "Convert Object to JSON String" adjacent, BFE.dev, lodash `_.cloneDeep`).
- Reference: lodash source, structured-clone algorithm (HTML spec).

## Why this question matters in interviews
Deep clone with cycles is the **machine-coding question that tests data-structure pattern reuse**. Naively candidates write recursion and call it done — until the interviewer hands them an object that references itself, and the function stack-overflows. The senior answer applies the same **"WeakMap to track seen nodes"** pattern used in: cycle detection in graphs, dependency-injection resolution, JSON serialization with refs, and React reconciliation. Done well, the implementation also handles **non-plain types** (Date, RegExp, Map, Set), which separates it from `JSON.parse(JSON.stringify(x))` — a trick every junior knows but which corrupts Dates, drops functions/undefined, and crashes on cycles. Backend engineers run into this every time they snapshot config, fork a request context, or build immutable update helpers.

In this bucket, focus on **pattern reuse** — the WeakMap-tracking-seen-refs trick is a building block, not just a one-off for clone. Identical structure to graph traversal, dependency resolution, and memoize-II's identity-keyed map.

## Concepts involved

### Syntax to lock in
```js
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;     // primitive
  if (seen.has(value)) return seen.get(value);                       // cycle short-circuit
  // ... clone container, register in seen BEFORE recursing
}

const a = { name: 'a' };
a.self = a;                       // cycle
const b = deepClone(a);
b === a;        // false
b.self === b;   // true — cycle preserved
```

### Runtime / engine behavior
- `WeakMap` keys must be objects, which is exactly what we want (we only need to track objects, since primitives are passed by value).
- **Register the clone in `seen` BEFORE recursing into its children.** This is the load-bearing step: if a child references back to its parent, the recursion finds the in-progress clone and returns it instead of looping infinitely.
- `Object.getPrototypeOf` + `Object.create` preserves the prototype chain — important for class instances. `Object.assign({}, src)` does NOT preserve prototype.
- `Object.getOwnPropertyDescriptors` + `Object.defineProperties` preserves getters/setters and `enumerable`/`writable` flags. Lodash does this; for an interview a plain key loop is fine if you state the trade-off.
- Symbol-keyed properties: walk `Object.getOwnPropertySymbols` too. Often omitted; mention.

### Edge cases (these are the interview traps)
1. **Cycles** — the headline. Without WeakMap, infinite recursion → stack overflow. With WeakMap, register-before-recurse handles it.
2. **`JSON.parse(JSON.stringify(x))`** — the junior trap. **Fails on**: cycles (throws), Date (becomes string), RegExp (becomes `{}`), Map/Set (becomes `{}`), Function (dropped), `undefined` (dropped from objects, becomes `null` in arrays), Symbol keys (dropped), BigInt (throws). State this upfront.
3. **Date** — `new Date(value.getTime())` or `new Date(value)`. Plain recursion would clone its internal slots as enumerable props, which doesn't exist.
4. **RegExp** — `new RegExp(value.source, value.flags)`. Optionally preserve `lastIndex`.
5. **Map / Set** — iterate entries, clone keys (if Map) and values, build a new container. **Register the new container in `seen` before iterating** so cyclic refs work.
6. **Array** — preallocate with `new Array(value.length)` (preserves length), then clone each index. Holes (sparse arrays) — usually OK to skip; mention.
7. **Class instances** — preserve prototype with `Object.create(Object.getPrototypeOf(value))`. Otherwise the clone is a plain object that looks like the original but `instanceof` fails.
8. **Functions** — usually NOT cloned (impossible to clone closures correctly). Lodash copies the reference. State your choice.
9. **TypedArray / Buffer / ArrayBuffer** — `slice()` or constructor copy. Worth a one-liner mention.
10. **Symbol-keyed properties** — `Object.getOwnPropertySymbols(value)` to enumerate, copy explicitly.

## Brute force approach
**`JSON.parse(JSON.stringify(x))`** — one-liner, works for plain JSON-safe data. Failure modes listed above. Always mention this so the interviewer knows you know it; immediately disqualify it for general use.

**Naive recursion**: walks own enumerable keys, recurses. Works for trees, **stack-overflows on cycles**. Show this as the brute-force pass before adding the WeakMap.

## Optimal approach
Recursion + `WeakMap<original, clone>` for cycle short-circuit. Register the new container in the map **before** populating its children. Switch on type to handle Date, RegExp, Map, Set, Array, plain object. Preserve prototype. Skip / passthrough functions and symbols based on requirements.

## Solution (JavaScript)

```js
/**
 * Deep clone arbitrary value. Handles cycles, Date, RegExp, Map, Set, Array.
 * Preserves prototype chain. Does NOT clone Functions (returns the same reference).
 *
 * @param {any} value
 * @param {WeakMap<object, object>} [seen]  internal — tracks cycles
 * @returns {any} a deep clone
 */
function deepClone(value, seen = new WeakMap()) {
  // Primitives (string, number, boolean, null, undefined, bigint, symbol) — clone is the value itself.
  if (value === null || typeof value !== 'object') return value;

  // Cycle short-circuit: we've seen this ref before, return its clone-in-progress.
  if (seen.has(value)) return seen.get(value);

  // Date
  if (value instanceof Date) {
    const cloned = new Date(value.getTime());
    seen.set(value, cloned);
    return cloned;
  }

  // RegExp
  if (value instanceof RegExp) {
    const cloned = new RegExp(value.source, value.flags);
    cloned.lastIndex = value.lastIndex;
    seen.set(value, cloned);
    return cloned;
  }

  // Map
  if (value instanceof Map) {
    const cloned = new Map();
    seen.set(value, cloned);   // BEFORE recursion
    for (const [k, v] of value) cloned.set(deepClone(k, seen), deepClone(v, seen));
    return cloned;
  }

  // Set
  if (value instanceof Set) {
    const cloned = new Set();
    seen.set(value, cloned);
    for (const v of value) cloned.add(deepClone(v, seen));
    return cloned;
  }

  // Array
  if (Array.isArray(value)) {
    const cloned = new Array(value.length);
    seen.set(value, cloned);
    for (let i = 0; i < value.length; i++) cloned[i] = deepClone(value[i], seen);
    return cloned;
  }

  // Plain object / class instance — preserve prototype.
  const cloned = Object.create(Object.getPrototypeOf(value));
  seen.set(value, cloned);
  for (const key of Reflect.ownKeys(value)) {   // includes symbol keys
    cloned[key] = deepClone(value[key], seen);
  }
  return cloned;
}
```

## Step-by-step dry run

Input:
```js
const node = { name: 'root', children: [] };
const child = { name: 'child', parent: node };
node.children.push(child);   // cycle: node → children[0].parent → node

const created = new Date('2024-01-01');
const tags = new Set(['a', 'b']);
node.created = created;
node.tags = tags;

const clone = deepClone(node);
```

Trace:

- `deepClone(node, seen={})`:
  - `typeof node === 'object'`, not seen. It's a plain object.
  - Create `clone1 = Object.create(Object.prototype)`. `seen.set(node, clone1)`.
  - Walk keys of node: `['name', 'children', 'created', 'tags']`.
    - `name`: primitive `'root'` → clone[1].name = `'root'`.
    - `children`: array `[child]`. Recurse:
      - `deepClone(children)`: not seen → `clone2 = []`. `seen.set(children, clone2)`.
        - Index 0: `deepClone(child)`: not seen → `clone3 = Object.create(Object.prototype)`. `seen.set(child, clone3)`.
          - keys: `['name', 'parent']`.
            - `name`: `'child'` (primitive).
            - `parent`: this is `node`. **`seen.has(node)` is TRUE** (set in step 1). Return `clone1`. **Cycle short-circuited.** clone3.parent = clone1.
        - clone2[0] = clone3.
      - Return clone2.
    - clone1.children = clone2.
    - `created`: Date instance. `deepClone(created)`: not seen → `new Date(created.getTime())`. `seen.set(...)`. Return new Date. clone1.created = new Date copy.
    - `tags`: Set. `deepClone(tags)`: not seen → `clone4 = new Set()`. `seen.set(tags, clone4)`.
      - Iterate: clone4.add(deepClone('a')) = 'a'. clone4.add(deepClone('b')) = 'b'.
      - Return clone4.
    - clone1.tags = clone4.
  - Return clone1.

Post-clone assertions:
- `clone !== node` → true (different refs).
- `clone.children !== node.children` → true (cloned).
- `clone.children[0].parent === clone` → TRUE (cycle preserved correctly).
- `clone.created.getTime() === node.created.getTime()` → true, but `clone.created !== node.created` → true (separate Date).
- `clone.tags !== node.tags` → true. `clone.tags.has('a')` → true.

The cycle preservation in step 4 — where `parent` resolves to `clone1` rather than recursing into `node` again — is THE behavior interviewers care about.

## Important takeaways

**Pattern reuse — the WeakMap-tracks-seen trick**
The same trick appears in:
- Cycle detection in graph traversal (mark visited, skip).
- Dependency injection container (registry tracks resolved instances).
- JSON serialization with refs (`$ref: 1` style).
- Memoize II (identity-keyed cache — see memoize-ii.md).
- React fiber reconciliation (track work in progress).

If you see "do something recursive over an object graph that might have cycles or shared refs," reach for a `WeakMap<original, result>` and register-before-recurse.

**Syntax to memorize**
- `WeakMap` because object keys + GC-friendly + no risk of stringification.
- `if (seen.has(value)) return seen.get(value);` — the cycle short-circuit, every time.
- `seen.set(original, clone)` **before** populating clone's children.
- `Object.create(Object.getPrototypeOf(value))` to preserve class identity.
- `Reflect.ownKeys(value)` to walk both string and symbol keys.

**Common mistakes**
- Registering the clone AFTER recursing → cycle isn't detected → stack overflow.
- Using `JSON.parse(JSON.stringify(x))` and not articulating its failure modes.
- Using `Object.assign({}, src)` for objects → drops the prototype, breaks `instanceof`.
- Using a plain object for `seen` → can't use object refs as keys (and `WeakMap` is cleaner for GC anyway).
- Forgetting Date / RegExp / Map / Set → returns empty `{}` for them (the same bug as `JSON.stringify`).
- Cloning functions — usually wrong (can't clone closures). Pass by reference.

**Related questions**
- **Memoize II** — same WeakMap-keyed identity trick.
- Graph cycle detection — same "mark visited" pattern.
- `structuredClone(value)` — the browser/Node 17+ built-in. Handles cycles, Date, RegExp, Map, Set, ArrayBuffer, TypedArrays, but NOT functions, Error subclasses preserved limited. Mention it; LeetCode often forbids it.

## Variants

1. **`structuredClone(value)`** — built-in (Node 17+, all modern browsers). Implements the HTML structured-clone algorithm. One line. State why you'd still write the manual version (control over function/symbol handling, support for legacy runtimes, learning).

2. **Lossy clone (`JSON.parse(JSON.stringify(x))`)** — explicit "I know this is wrong, here are the limits." Useful for snapshot-testing plain config.

3. **Selective clone** — clone only own enumerable props, omit symbols / non-enumerable / inherited. Lighter; matches `JSON.stringify` semantics minus the bugs.

4. **Immutable update (clone-on-write)** — instead of fully cloning, share refs and only clone along the path being modified. This is what Immer does. Different problem; mention as a senior topic.

5. **Cross-realm clone** — for postMessage / Web Workers, the structured-clone algorithm handles transferable objects (`ArrayBuffer.transfer`). Out of scope for in-process clone.

6. **Class instances with private fields** — `#private` fields can't be cloned via property iteration. Need explicit clone method on the class. Trade-off worth flagging.

## Revision notes

> **deepClone with cycles — 60 second recap**
> - `WeakMap<original, clone>` to track seen refs.
> - **Register clone in `seen` BEFORE recursing** — that's how cycles short-circuit.
> - Type switch: primitive → return value; Date / RegExp / Map / Set / Array / plain object → cloned form.
> - Preserve prototype: `Object.create(Object.getPrototypeOf(value))`.
> - `Reflect.ownKeys` walks symbol keys too.
> - **`JSON.parse(JSON.stringify(x))`** is wrong for: cycles (throws), Date (stringified), RegExp (`{}`), Map/Set (`{}`), undefined (dropped), functions (dropped), symbols (dropped), BigInt (throws).
> - **Pattern reuse:** WeakMap-tracks-seen is the same trick used in graph traversal, DI, memoize-II, JSON-ref serialization.
> - Modern shortcut: `structuredClone(value)` (Node 17+) — mention but be ready to write manual.
> - **Trap:** registering clone AFTER recursing → infinite loop on cycles.
