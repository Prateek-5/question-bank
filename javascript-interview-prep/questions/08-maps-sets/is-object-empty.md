# Implement `isEmpty(obj)` — detect empty object or array

## Source
- LeetCode #2727 "Is Object Empty" — https://leetcode.com/problems/is-object-empty/
- Variants on codedamn, BFE.dev, Frontend Masters.

## Why this question matters in interviews
This is the 30-second warm-up before the real interview begins. It looks trivial, but every senior candidate who reaches for `Object.keys(obj).length === 0` without thinking is silently scored down because it misses three things: it's **O(n)** when O(1) is possible, it skips **symbol keys**, and it blows up on **arrays vs plain objects vs Maps/Sets**. Backend engineers see this in real life — short-circuiting `if (!isEmpty(filters)) buildWhereClause(filters)` runs on every request, so the O(1) version is the right answer. The follow-up question is always "what if it's a Map?" — that's the bridge into the maps-sets bucket.

## Concepts involved

### Syntax to lock in
```js
// Bad — allocates a whole array of keys
Object.keys(obj).length === 0;

// Better — O(1), short-circuits on first key
for (const _ in obj) return false;
return true;

// Best — handles Map/Set/Array uniformly
function isEmpty(o) {
  if (o == null) return true;
  if (Array.isArray(o)) return o.length === 0;
  if (o instanceof Map || o instanceof Set) return o.size === 0;
  for (const _ in o) return false;          // O(1) short-circuit
  return Object.getOwnPropertySymbols(o).length === 0;
}
```

### Runtime / engine behavior
- `Object.keys(o)` walks **own enumerable string keys**, allocates an array, returns it. **O(n)** in keys + heap alloc.
- `for...in` walks own + **inherited** enumerable string keys. The first hit short-circuits — **O(1)** if any key exists. Skips symbols.
- `Object.getOwnPropertySymbols(o)` is needed because symbols are invisible to both `for...in` and `Object.keys`.
- Arrays are objects whose own-key set is `['0','1',...,'length']`. `Object.keys([])` is `[]`, so the polyfill also accidentally works on `[]` — but `length` is the canonical check.
- `Map` / `Set` don't expose keys as own-properties at all; you **must** use `.size`. `Object.keys(new Map([['a',1]]))` returns `[]` and lies.

### Edge cases (these are the interview traps)
1. **`null` / `undefined` input** — `Object.keys(null)` throws `TypeError`. Always guard first.
2. **Arrays vs objects** — `Object.keys([1,2,3])` returns `['0','1','2']`, so the keys check works, but `length` is faster and intent-clearer.
3. **Map and Set** — `Object.keys(map)` returns `[]` because map entries are internal slots, not properties. Always use `.size`.
4. **Symbol keys** — `{ [Symbol('x')]: 1 }` is **not empty** but `Object.keys` says it is. Bonus-point territory.
5. **Inherited keys** — `for...in` walks the prototype chain. `Object.create({ foo: 1 })` is "empty" by own-keys but `for...in` will see `foo`. Use `Object.hasOwn(o, k)` inside the loop if strict own-only is required.
6. **Object.create(null)** — has no prototype, no inherited keys. Works fine with both methods.
7. **Class instances with only methods** — methods on the prototype are not own-keys, so `Object.keys(new MyClass())` may legitimately be empty.
8. **Frozen / sealed objects** — irrelevant to emptiness but interviewers may bait you. Frozen empty is still empty.

## Brute force approach
`JSON.stringify(obj) === '{}'`. Works for plain JSON-safe objects but: (a) O(n) serialization, (b) silently drops symbol/function/undefined values, (c) throws on cycles, (d) lies about Map/Set (returns `'{}'`). Don't ship it.

## Optimal approach
Type-discriminate, then use the cheapest emptiness check for each type:
- `null/undefined` → empty.
- Array → `.length === 0`.
- Map/Set → `.size === 0`.
- Plain object → `for...in` + short-circuit, optionally check own-symbols.

O(1) for all cases. No allocations.

## Solution (JavaScript)

```js
/**
 * Returns true if the value is "empty":
 *   - null / undefined
 *   - [] for arrays
 *   - Map/Set of size 0
 *   - object with no own enumerable string OR symbol keys
 *
 * O(1) — short-circuits on the first key.
 */
function isEmpty(value) {
  if (value == null) return true;

  if (Array.isArray(value)) return value.length === 0;

  if (value instanceof Map || value instanceof Set) {
    return value.size === 0;
  }

  // Plain object (or class instance)
  if (typeof value === 'object') {
    // Short-circuit string-keyed scan over OWN keys only.
    for (const key in value) {
      if (Object.hasOwn(value, key)) return false;
    }
    // Symbols are invisible to for...in
    return Object.getOwnPropertySymbols(value).length === 0;
  }

  // Primitives — strings/numbers/etc are not "objects"; throw or return true
  // depending on contract. LeetCode expects: assume input is array or object.
  return true;
}
```

## Step-by-step dry run

Input cases:
```js
isEmpty({});                        // -> true
isEmpty({ x: 1 });                  // -> false
isEmpty([]);                        // -> true
isEmpty([undefined]);               // -> false (length is 1)
isEmpty(new Map());                 // -> true
isEmpty(new Map([['a', 1]]));       // -> false
isEmpty(new Set());                 // -> true
isEmpty(null);                      // -> true
isEmpty({ [Symbol('s')]: 1 });      // -> false (symbol-only)
isEmpty(Object.create({ x: 1 }));   // -> true (inherited, not own)
```

Trace of `isEmpty({ [Symbol('s')]: 1 })`:
1. Not `null`. Not array. Not Map/Set. typeof is `'object'`.
2. `for...in` loops over enumerable string keys. There are none — loop body doesn't execute.
3. Fall through to `getOwnPropertySymbols(value)` → `[Symbol('s')]`, length 1 → return `false`. Correct.

Trace of `isEmpty(Object.create({ x: 1 }))`:
1. typeof is `'object'`. `for...in` sees the inherited `x`.
2. `Object.hasOwn(value, 'x')` is `false` → we **don't** return false; loop continues.
3. No more keys. `getOwnPropertySymbols` is empty → return `true`. Correct.

## Important takeaways

**Syntax to memorize**
- Guard `null/undefined` first — `Object.keys(null)` throws.
- `for (const k in o) if (Object.hasOwn(o, k)) return false; return true;` — the O(1) own-keys check.
- `.size` for Map/Set, `.length` for arrays. **Never** `Object.keys()` on them.
- `Object.getOwnPropertySymbols(o).length` for the symbol-aware version.

**Patterns to reuse**
- "Type-discriminate then dispatch" — recurring shape for any utility that has to handle Object / Array / Map / Set uniformly (deep clone, deep diff, deep equal, serializer).
- Short-circuit iteration via `for...in return false` — same pattern beats `array.some(...)` for hot paths.

**Common mistakes**
- Reaching for `Object.keys(o).length === 0` — works on the LeetCode test but burns O(n) and misses symbols.
- Forgetting Map/Set have no own enumerable keys. `Object.keys(map)` is `[]`. Burned.
- `JSON.stringify(o) === '{}'` — see brute force section.
- Forgetting `null` is `typeof === 'object'`. `Object.keys(null)` throws.

**Related questions**
- Deep equality (`isEqual`)
- Deep diff (`differencesBetween(a, b)`) — same keyset walk
- `Object.fromEntries(Object.entries(o).filter(...))` for pruning
- `Object.groupBy` (ES2024)

## Variants

1. **Strict own-only** — "Don't peek at the prototype chain." Drop the `for...in` and use `Object.keys(o).length + Object.getOwnPropertySymbols(o).length === 0`. Slower (allocates two arrays) but explicit.

2. **Deep-empty** — "Return true if all leaf values are also empty: `{ a: {}, b: [] }` is empty." Recurse into nested objects/arrays; mind cycles via `WeakSet`.

3. **Map of empties** — "Given a Map<string, T>, return true if every value is empty." Combine `isEmpty` with `Array.from(map.values()).every(isEmpty)`.

## Revision notes

> **isEmpty — 60 second recap**
> - Guard `null/undefined` first.
> - Array → `.length`. Map/Set → `.size`. Object → `for...in` short-circuit.
> - `Object.keys(o).length === 0` is O(n) and **lies about Map/Set/symbols**.
> - Inherited keys: skip with `Object.hasOwn(o, k)`.
> - Symbol keys: `Object.getOwnPropertySymbols(o).length`.
> - **Trap:** `Object.keys(new Map([...]))` returns `[]`. Map entries are internal slots.
