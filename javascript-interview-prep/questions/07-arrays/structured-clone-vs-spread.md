# `structuredClone` vs Spread/`Object.assign`

## Source / Origin
- ES2022 `structuredClone()` global.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/arrays.md`, sibling `05-event-loop/structured-clone-cost.md`.

## Why this question matters in interviews
"Deep-clone this object." Naive `{...obj}` only copies one level. `JSON.parse(JSON.stringify(obj))` is the legacy trick but drops Date/Map/Set/undefined and breaks on cycles. `structuredClone` (ES2022) is now the right answer. Senior bar: list 4 deep-clone strategies and their tradeoffs.

## Concepts involved

```js
const o = { a: 1, b: { c: 2 }, d: new Date(), e: new Map([[1, 'x']]) };

// 1. Shallow
const s1 = { ...o };           // b is shared, mutating s1.b.c also changes o.b.c
const s2 = Object.assign({}, o); // same

// 2. JSON trick (deep, lossy)
const j = JSON.parse(JSON.stringify(o));
j.b !== o.b;                    // true (deep)
j.d instanceof Date;            // false — Date became string
j.e;                            // {} — Map became empty object

// 3. structuredClone (deep, faithful)
const c = structuredClone(o);
c.b !== o.b;                    // true
c.d instanceof Date;            // true
c.e instanceof Map;             // true
c.e.get(1);                     // 'x'

// 4. Lodash _.cloneDeep
const l = _.cloneDeep(o);
```

### Comparison
| Method | Depth | Date/Map/Set | Cycles | Functions | Speed |
|---|---|---|---|---|---|
| `{...obj}` | shallow | preserve | n/a | preserve | fastest |
| `Object.assign({}, obj)` | shallow | preserve | n/a | preserve | fast |
| `JSON.parse(JSON.stringify())` | deep | LOSE | throw | LOSE | slow |
| `structuredClone()` | deep | preserve | preserve | THROW | fast |
| `_.cloneDeep()` | deep | preserve | preserve | preserve* | slower |

### Edge cases / traps
1. **Shallow spread** is fine when you only need to mutate top-level properties.
2. **`JSON` trick** silently loses Date (→ ISO string), Map/Set, undefined, functions, Symbol-keys, +Infinity/NaN (→ null).
3. **`structuredClone` throws on functions, DOM nodes** (not cloneable). Cycles fine.
4. **`structuredClone` is synchronous** — blocks for big objects.
5. **Performance**: structuredClone is ~2-3x faster than `JSON.parse(JSON.stringify)` for typical objects.
6. **Transferables option**: `structuredClone(obj, { transfer: [buf] })` moves an ArrayBuffer zero-copy *within* the result.
7. **Lodash cloneDeep** is the most permissive but slowest; uses ~500x more code than structuredClone.

## Mental Model

```
   shallow:     newObj.x = obj.x      ← references shared
   deep JSON:   serialize → parse     ← lossy
   structuredClone: HTML structured-clone algorithm (faithful for cloneable types)
   _.cloneDeep: hand-rolled recursive walk (most flexible)
```

## Why interviewers care

- **Knows the modern answer (`structuredClone`).**
- **Knows the JSON trick's pitfalls.**
- **Choice by use case** — shallow when sufficient, deep when needed.

## Common confusion

- **"Spread is deep."** It isn't; only top-level.
- **"`JSON.parse(JSON.stringify)` is safe."** No — drops Date, Map, Set, undefined; throws on cycles.
- **"`structuredClone` clones functions."** It doesn't — throws.
- **"Deep clone is always needed."** Usually shallow is enough; clone the path you mutate.

## Solution

```js
// Pick by use case
function update(state, path, value) {
  const next = { ...state };       // shallow new top
  let curr = next;
  const keys = path.split('.');
  for (let i = 0; i < keys.length - 1; i++) {
    curr[keys[i]] = { ...curr[keys[i]] };   // shallow at each step
    curr = curr[keys[i]];
  }
  curr[keys[keys.length - 1]] = value;
  return next;
}

// Deep clone for snapshot
const snapshot = structuredClone(state);

// Detect cloneability
function tryClone(x) {
  try { return structuredClone(x); }
  catch (e) {
    if (e.name === 'DataCloneError') return null;
    throw e;
  }
}

// Array deep clone preserving types
const arr = [new Date(), new Map(), new Set(), /regex/];
const arr2 = structuredClone(arr);
arr2.every((v, i) => v instanceof arr[i].constructor);   // true

// Performance comparison (rough)
function bench(fn, obj, iters = 100_000) {
  const start = performance.now();
  for (let i = 0; i < iters; i++) fn(obj);
  return performance.now() - start;
}
bench(o => ({ ...o }), state);                    // ~30ms
bench(o => structuredClone(o), state);            // ~300ms
bench(o => JSON.parse(JSON.stringify(o)), state); // ~700ms
```

## Dry run

```js
const o = { a: new Map([[1, 'x']]), b: new Date('2024-01-01') };

const j = JSON.parse(JSON.stringify(o));
// j = { a: {}, b: '2024-01-01T00:00:00.000Z' }   (lossy)

const c = structuredClone(o);
// c = { a: Map(1){1=>'x'}, b: Date('2024-01-01') }   (faithful)
```

## How to think aloud

> "Four deep-clone options. Spread/Object.assign — shallow; fine for immutable updates path-by-path. JSON.parse(JSON.stringify) — old trick, lossy and slow. structuredClone — ES2022 standard; deep, preserves Date/Map/Set/cycles, throws on functions. _.cloneDeep — most permissive, slowest. Pick by what's in the object: if there's only data, use structuredClone; if there are functions, you can't deep-clone faithfully — refactor or accept lossy."

## Important takeaways

- **`structuredClone()` is the modern deep-clone.**
- **Spread is shallow.**
- **JSON trick loses Date/Map/Set/undefined; throws on cycles.**
- **`structuredClone` throws on functions.**
- **For path-mutation, shallow at each level is usually enough.**

## Variants

- **`globalThis.structuredClone`** in workers too.
- **`postMessage(obj, [transferables])`** — same algorithm, different API.
- **`_.cloneDeep`** for legacy or function-cloning support.
- **Custom replacer/reviver** with JSON for selective cloning.

## Revision notes

```
shallow:
  {...obj}
  Object.assign({}, obj)
  → references shared at depth >1

deep:
  JSON.parse(JSON.stringify(obj))  — lossy (Date→string, Map→{}, undefined→null, throws cycle)
  structuredClone(obj)             — faithful for cloneable types; throws on functions
  _.cloneDeep(obj)                 — slow, very permissive

PICK:
  shallow → immutable path update
  structuredClone → snapshot, deep equal of state
  _.cloneDeep → legacy or functions/proxies needed
```
