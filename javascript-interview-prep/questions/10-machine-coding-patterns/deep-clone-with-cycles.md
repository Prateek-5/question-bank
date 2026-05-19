# Implement `deepClone(value)` with cycle handling

> **Difficulty:** Medium-Senior   |   **Time:** ~25 min   |   **Prereqs:** [memoize-ii.md](./memoize-ii.md), [`concepts/recursion.md`](../../concepts/recursion.md)
>
> **Source:** lodash `_.cloneDeep`, HTML structured-clone spec, `structuredClone` global. Asked at BFE.dev, BFE rounds, Frontend Masters.

---

## 1. Problem statement

**Signature**
```ts
function deepClone<T>(value: T, seen?: WeakMap<object, object>): T;
```

**Input / Output examples**

| Input                                                    | Behaviour                                              |
|----------------------------------------------------------|---------------------------------------------------------|
| Primitives (string, number, bool, null, undefined)       | returned as-is                                          |
| `{a: {b: 1}}`                                            | deep clone; nested object is a new ref                  |
| Cycle: `a.self = a`                                      | clone preserves cycle; `b.self === b` (not stack overflow)|
| `new Date(...)`                                          | new Date with same ms                                   |
| `new Map([[k, v]])`                                      | new Map; entries deep-cloned                            |
| `new Set([...])`                                         | new Set; values deep-cloned                             |
| `JSON.parse(JSON.stringify(x))` failure cases            | Date→string, RegExp→{}, Map/Set→{}, fn dropped, cycle throws |

**Constraints**
- Handle cycles via `WeakMap<original, clone>`.
- **Register clone in seen BEFORE recursing into children** — load-bearing.
- Type switch: Date, RegExp, Map, Set, Array, plain object.
- Preserve prototype via `Object.create(Object.getPrototypeOf(value))`.

---

## 2. Plain-English restatement

Make a structural copy of any value such that nothing in the clone shares references with the original. Handle cycles (self-referencing graphs), built-in container types (Date, RegExp, Map, Set), and preserve class prototypes. The naive `JSON.parse(JSON.stringify(x))` shortcut fails on cycles, Date, RegExp, Map, Set, functions, undefined, and BigInt — articulate this upfront.

---

## 3. Why this matters in interviews

The machine-coding question that tests **data-structure pattern reuse**. Naive candidates write recursion and get stack-overflow on a cycle. The senior answer applies the **"WeakMap tracks seen nodes"** trick — the same pattern used in graph cycle detection, DI resolution, JSON-ref serialization, React reconciliation, and Memoize II. Pattern reuse > one-off code.

---

## 4. Mental model

```
   deepClone(value, seen=WeakMap):
   ┌─────────────────────────────────────────────┐
   │ if primitive → return value                 │
   │ if seen.has(value) → return seen.get(value) │  ← cycle short-circuit
   │                                             │
   │ switch on type:                             │
   │   Date     → new Date(value.getTime())      │
   │   RegExp   → new RegExp(source, flags)      │
   │   Map      → new Map(); deep-clone entries  │
   │   Set      → new Set(); deep-clone values   │
   │   Array    → new Array(len); deep-clone idx │
   │   object   → Object.create(getProto(value)) │
   │                                             │
   │ seen.set(value, clone)  ← BEFORE recursing  │
   │ populate clone's children                   │
   │ return clone                                │
   └─────────────────────────────────────────────┘

   Cycle example:
     node.self = node
     deepClone(node):
       create clone1; seen.set(node, clone1)
       walk node.self → deepClone(node, seen)
                          seen.has(node) → return clone1
       clone1.self = clone1   ✓ cycle preserved
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `JSON.parse(JSON.stringify({d: new Date()}))` produce? Why is it wrong?
> 2. Why must `seen.set(original, clone)` happen BEFORE recursing into children?
> 3. If you clone a class instance with `Object.assign({}, instance)`, why does `instanceof` fail on the result?

---

## 6. Brute force — walked through

### Wrong attempt 1: `JSON.parse(JSON.stringify(x))`
**Fails on:**
- Cycles → throws "circular structure"
- Date → becomes string
- RegExp → `{}`
- Map/Set → `{}`
- Function → dropped
- `undefined` → dropped (or `null` in arrays)
- Symbol keys → dropped
- BigInt → throws

Mention upfront, disqualify, move on.

### Wrong attempt 2: naive recursion (no `seen`)
```js
function deepClone(value) {
  if (typeof value !== 'object' || value === null) return value;
  const clone = Array.isArray(value) ? [] : {};
  for (const k of Object.keys(value)) clone[k] = deepClone(value[k]);
  return clone;
}
```
Stack-overflows on cycles. No Date/RegExp/Map/Set handling. Doesn't preserve prototype.

### Wrong attempt 3: register clone AFTER recursing
```js
const clone = {};
for (const k of Object.keys(value)) clone[k] = deepClone(value[k], seen);
seen.set(value, clone);   // BUG: by the time we get here, recursion already infinite-looped
```
The whole point of seen is to short-circuit recursion; setting it after recursion is too late.

---

## 7. The unlocking insight

> **`WeakMap<original, clone>` to track seen refs. Register clone in `seen` BEFORE recursing into children. Type switch for Date/RegExp/Map/Set/Array/plain object. Preserve prototype with `Object.create(Object.getPrototypeOf(value))`.**

Three properties:

1. **`WeakMap`** because keys must be objects + GC-friendly.
2. **Register-before-recurse** — the entire cycle-handling mechanism.
3. **Type switch** — built-ins need constructor calls, not enumeration.

---

## 8. Solution (annotated)

```js
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;   // step 1: primitives
  if (seen.has(value)) return seen.get(value);                      // step 2: cycle short-circuit

  if (value instanceof Date) {                                       // step 3: Date
    const c = new Date(value.getTime());
    seen.set(value, c);
    return c;
  }

  if (value instanceof RegExp) {                                     // step 4: RegExp
    const c = new RegExp(value.source, value.flags);
    c.lastIndex = value.lastIndex;
    seen.set(value, c);
    return c;
  }

  if (value instanceof Map) {                                        // step 5: Map
    const c = new Map();
    seen.set(value, c);                                              // BEFORE recursion
    for (const [k, v] of value) c.set(deepClone(k, seen), deepClone(v, seen));
    return c;
  }

  if (value instanceof Set) {                                        // step 6: Set
    const c = new Set();
    seen.set(value, c);
    for (const v of value) c.add(deepClone(v, seen));
    return c;
  }

  if (Array.isArray(value)) {                                        // step 7: Array
    const c = new Array(value.length);
    seen.set(value, c);
    for (let i = 0; i < value.length; i++) c[i] = deepClone(value[i], seen);
    return c;
  }

  const c = Object.create(Object.getPrototypeOf(value));             // step 8: preserve prototype
  seen.set(value, c);
  for (const key of Reflect.ownKeys(value)) {                        // step 9: symbol keys too
    c[key] = deepClone(value[key], seen);
  }
  return c;
}
```

**Try it yourself**

```js
const node = { name: 'root', children: [] };
const child = { name: 'child', parent: node };
node.children.push(child);                           // cycle
node.created = new Date('2024-01-01');
node.tags = new Set(['a', 'b']);

const clone = deepClone(node);

clone !== node;                                       // true
clone.children !== node.children;                     // true
clone.children[0].parent === clone;                   // true (cycle preserved!)
clone.created instanceof Date;                        // true
clone.created !== node.created;                       // true
clone.tags instanceof Set && clone.tags.has('a');     // true
```

---

## 9. Step-by-step dry run

```
node = { name: 'root', children: [child], created: D, tags: S }
child.parent = node                                                  ← cycle

deepClone(node, seen={}):
  not primitive, not in seen → object
  create clone1 = Object.create(Object.prototype)
  seen.set(node, clone1)                                              ← BEFORE recursion
  walk keys: ['name', 'children', 'created', 'tags']

    'name' = 'root'  → primitive, return 'root'.  clone1.name='root'

    'children' = [child]:
      deepClone([child], seen):
        is Array → clone2 = new Array(1)
        seen.set(children, clone2)
        index 0: deepClone(child, seen):
          not primitive, not in seen → object
          create clone3, seen.set(child, clone3)
          walk keys: ['name', 'parent']
            'name' = 'child' → primitive
            'parent' = node:
              seen.has(node) → TRUE
              return seen.get(node) = clone1                          ← cycle short-circuit
          clone3.parent = clone1
        clone2[0] = clone3
        return clone2
      clone1.children = clone2

    'created' = D (Date):
      seen.has(D)? no → new Date(D.getTime()), seen.set, return new Date

    'tags' = S (Set):
      new Set, seen.set, iterate cloning values (primitives 'a','b')

  return clone1

Post-clone:
  clone1.children[0].parent === clone1                                ✓ cycle preserved
  clone1.created !== node.created                                     ✓ separate Date
  clone1.tags !== node.tags                                           ✓ separate Set
```

---

## 10. Common confusion + traps

1. **Register clone AFTER recursing** → cycle isn't caught → stack overflow.
2. **`JSON.parse(JSON.stringify(x))`** — articulate all the failure modes.
3. **`Object.assign({}, src)`** — drops prototype; `instanceof` fails.
4. **Plain object instead of WeakMap for `seen`** — can't use object refs as keys.
5. **Forgetting Date/RegExp/Map/Set** — returns `{}` for them (same bug as JSON shortcut).
6. **Cloning functions** — impossible to clone closures correctly. Pass reference; document.
7. **Forgetting symbol keys** — use `Reflect.ownKeys`, not `Object.keys`.

---

## 11. Senior follow-ups & variants

### Variant 1 — `structuredClone(value)`
Built-in (Node 17+, all modern browsers). Handles cycles, Date, RegExp, Map, Set, TypedArrays. **Does NOT handle** functions, prototypes preserved-limited. One-liner; mention but be ready to write manual version (LeetCode often forbids it).

### Variant 2 — Lossy clone (JSON shortcut)
Explicit "I know this is wrong, here are the limits." Useful for snapshot-testing plain config.

### Variant 3 — Selective clone
Clone only own enumerable props; skip symbols, non-enumerable, inherited. Matches `JSON.stringify` semantics minus the bugs.

### Variant 4 — Immutable update (clone-on-write)
What Immer does: share refs and only clone along the path being modified. Different problem; senior topic.

### Variant 5 — Cross-realm clone
For `postMessage` / Web Workers, the structured-clone algorithm handles transferable objects (`ArrayBuffer.transfer`).

### Variant 6 — Class with private fields
`#private` fields can't be cloned via property iteration. Need explicit `clone` method on the class.

---

## 12. How to think aloud

> "Recursion + `WeakMap<original, clone>` for cycle short-circuit. Register the clone in seen BEFORE recursing into children — that's how cycles get caught. Type switch: primitives pass through; Date/RegExp/Map/Set/Array each need their constructor; plain objects use `Object.create(Object.getPrototypeOf(value))` to preserve class identity. Walk both string and symbol keys via `Reflect.ownKeys`. Functions: usually NOT cloned — impossible to clone closures correctly. `JSON.parse(JSON.stringify(x))` fails on cycles, Date, RegExp, Map, Set, functions, undefined, BigInt — articulate upfront. Modern shortcut: `structuredClone(value)` (Node 17+). Same WeakMap-tracks-seen trick shows up in graph cycle detection, DI containers, Memoize II, JSON-ref serialization, React fiber."

---

## 13. 60-second revision

> - **`WeakMap<original, clone>`** for cycle tracking.
> - **Register-before-recurse** is load-bearing.
> - **Type switch:** Date → `new Date(getTime())`; RegExp → `new RegExp(source, flags)`; Map/Set → new + clone entries; Array → preallocate + clone idx; plain → `Object.create(getProto)` + `Reflect.ownKeys`.
> - **Preserve prototype** so `instanceof` works.
> - **`JSON.parse(JSON.stringify)`** breaks on: cycle, Date, RegExp, Map, Set, fn, undefined, BigInt, symbol keys.
> - **`structuredClone(value)`** modern shortcut.
> - **Pattern reuse:** WeakMap-tracks-seen is universal (DI, graph, Memoize II).
> - **Trap:** register AFTER recursing; `Object.assign`; forgetting symbol keys.

---

**Related:** [memoize-ii.md](./memoize-ii.md) · [`09-recursion/tree-traversal-iterative.md`](../09-recursion/tree-traversal-iterative.md) · [`09-recursion/graph-cycle-detection.md`](../09-recursion/graph-cycle-detection.md) · [json-parse-recursive-descent.md](./json-parse-recursive-descent.md)

**Concept primer:** [`concepts/recursion.md`](../../concepts/recursion.md)
