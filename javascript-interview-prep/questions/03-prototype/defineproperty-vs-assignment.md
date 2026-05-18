# `Object.defineProperty` vs Plain Assignment

## Source / Origin
- ES5 property descriptors.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/prototype.md`.

## Why this question matters in interviews
`obj.x = 1` and `Object.defineProperty(obj, 'x', { value: 1 })` look equivalent but aren't. The defaults are different: `defineProperty` makes the property *non-writable*, *non-enumerable*, *non-configurable* unless you say otherwise. Senior bar: you can list all 4 descriptor flags, predict `for...in`/`Object.keys` output, and explain when you'd reach for `defineProperty` (read-only fields, hidden internal props, getters/setters).

## Concepts involved

### Syntax to lock in
```js
const obj = {};

// Plain assignment — defaults all four flags to true (writable, enumerable, configurable)
obj.a = 1;
Object.getOwnPropertyDescriptor(obj, 'a');
// { value: 1, writable: true, enumerable: true, configurable: true }

// defineProperty — defaults are all FALSE
Object.defineProperty(obj, 'b', { value: 2 });
Object.getOwnPropertyDescriptor(obj, 'b');
// { value: 2, writable: false, enumerable: false, configurable: false }
obj.b = 99;        // strict: TypeError; sloppy: silently fails
Object.keys(obj);  // ['a']  — b is not enumerable
delete obj.b;      // strict: TypeError; sloppy: false
```

### Edge cases / traps
1. **The four flags** —
   - `value`: the actual value (data descriptor).
   - `writable`: can be reassigned.
   - `enumerable`: shows in `for...in`, `Object.keys`, `JSON.stringify`.
   - `configurable`: can be redefined/deleted.
2. **Defaults differ.** Assignment = all true; defineProperty = all false (unless specified).
3. **Accessor descriptors** don't have `value`/`writable`; they have `get`/`set` instead. Mutually exclusive.
4. **Strict mode throws** on bad operations (assign to non-writable, delete non-configurable, redefine non-configurable). Sloppy mode silently fails.
5. **Sealing/freezing** sets `configurable: false`. `Object.freeze` also sets `writable: false`.
6. **`Object.defineProperties`** (plural) for batch.
7. **`Reflect.defineProperty`** returns boolean instead of throwing.
8. **`__proto__`** is one of the few cases where assignment behaves specially (calls `Object.setPrototypeOf`).

## Mental Model

Every property has a **4-flag passport**:

```
   data property:                        accessor property:
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │ value: <V>               │          │ get: <function>          │
   │ writable: T/F            │          │ set: <function>          │
   │ enumerable: T/F          │          │ enumerable: T/F          │
   │ configurable: T/F        │          │ configurable: T/F        │
   └──────────────────────────┘          └──────────────────────────┘

   obj.x = v          → if x doesn't exist, create with {value:v, w:T, e:T, c:T}
                         if exists and writable, set value
                         if exists and not writable, fail (strict throws)
   defineProperty()   → explicit flags; merges with existing if configurable
```

## Why interviewers care

- **Descriptor literacy** — non-obvious but spec-level.
- **Predicting `Object.keys` and `JSON.stringify`** output.
- **API design** — building read-only or hidden internal props.

## Common confusion

- **"`defineProperty` with `{value}` is the same as assignment."** No — the other three flags default to `false`.
- **"`Object.keys` returns all properties."** Only enumerable own properties.
- **"`for...in` iterates enumerable own properties."** It iterates enumerable own *and inherited* (walks the prototype chain).
- **"You can't change a non-configurable property."** You can change `value` if it's writable; you can't delete it or change the other flags.
- **"`JSON.stringify` ignores accessor properties."** It invokes getters; the result becomes data in JSON.

## Brute force

Just `obj.x = v`. Fine for trivial cases. Lose control over the four flags.

## Optimal approach

Use `Object.defineProperty` when you need:
1. Read-only (`writable: false`).
2. Hidden (`enumerable: false`).
3. Locked (`configurable: false`).
4. Accessor (`get`/`set`).

## Solution

```js
// Hidden internal slot
const cache = {};
Object.defineProperty(cache, '_internalId', {
  value: Symbol('id'),
  writable: false, enumerable: false, configurable: false,
});
Object.keys(cache);    // [] — hidden
JSON.stringify(cache); // '{}' — non-enumerable skipped

// Read-only constant
class Config {
  constructor(env) {
    Object.defineProperty(this, 'env', {
      value: env, writable: false, enumerable: true, configurable: false,
    });
  }
}
const c = new Config('prod');
c.env = 'dev';   // strict: TypeError; sloppy: silently fails

// Multiple at once
Object.defineProperties(obj, {
  a: { value: 1, enumerable: true, writable: true, configurable: true },
  b: { get() { return this.a * 2; }, enumerable: true, configurable: true },
});

// Convert defineProperty fails
const frozen = Object.freeze({ x: 1 });
try { Object.defineProperty(frozen, 'x', { value: 2 }); } catch (e) { console.log(e.message); }
// TypeError in strict; silent in sloppy

// Inspect all (including non-enumerable, including symbols)
Reflect.ownKeys(obj);                                    // all keys (string + symbol)
Object.getOwnPropertyNames(obj);                         // own string keys (enum and non-enum)
Object.getOwnPropertySymbols(obj);                       // own symbol keys
```

## Dry run

```js
const o = {};
Object.defineProperty(o, 'x', { value: 1 });
//   { value:1, writable:false, enumerable:false, configurable:false }

o.x = 99;                  // strict: TypeError; sloppy: silently fails
Object.keys(o);            // []
'x' in o;                  // true
delete o.x;                // strict: TypeError; sloppy: false
Object.defineProperty(o, 'x', { value: 2 });  // re-define on non-configurable
  // — strict: TypeError UNLESS we keep value-only and writable was true
  // — here writable: false, so even value change throws
```

```js
const o2 = {};
o2.x = 1;
Object.defineProperty(o2, 'x', { value: 2 });    // OK — existing is configurable (assignment default)
// existing flags preserved for unspecified fields
Object.getOwnPropertyDescriptor(o2, 'x');
// { value: 2, writable: true, enumerable: true, configurable: true }
```

(`defineProperty` on an existing configurable property merges; on a non-configurable, the rules are tight.)

## How to think aloud

> "Plain assignment defaults all 4 descriptor flags to true. `defineProperty` defaults to all false. So `Object.defineProperty(obj, 'x', {value:1})` creates a non-writable, non-enumerable, non-configurable property — surprising. Use defineProperty for hidden internal props, read-only constants, accessors. `Object.keys` skips non-enumerable; `for...in` does too. `Reflect.ownKeys` gets everything including symbols and non-enumerable."

## Important takeaways

- **Four flags**: value, writable, enumerable, configurable (data); get, set, enumerable, configurable (accessor).
- **Assignment defaults to all true** for new properties.
- **`defineProperty` defaults to all false** unless specified.
- **`Object.keys` / `for...in` / `JSON.stringify` honor `enumerable`.**
- **`configurable: false` is mostly one-way** — locks the property.
- **`Reflect.ownKeys`** sees everything (string + symbol, enum + non-enum).

## Variants

- **`Object.defineProperties`** — plural; batch.
- **`Reflect.defineProperty`** — Boolean return.
- **`Object.freeze` / `seal` / `preventExtensions`** — broad locking.
- **Symbol-keyed properties** — same descriptor model.
- **Proxy `defineProperty` trap** — intercept the operation.

## Revision notes

```
obj.x = v        → if new: {value, w:T, e:T, c:T}; if exists: set value (if writable)
defineProperty   → defaults all false (or unspecified = preserve existing if reconfiguring)

four flags:
  value, writable, enumerable, configurable  (data)
  get, set,                       enumerable, configurable  (accessor)

visibility:
  Object.keys / for...in / JSON.stringify  → enumerable only
  Reflect.ownKeys                          → ALL (string+symbol, enum+non-enum)
  Object.getOwnPropertyNames                → strings only (enum + non-enum)
  Object.getOwnPropertySymbols              → symbols only

USES:
  - hidden internal slot (enumerable: false)
  - read-only (writable: false)
  - locked (configurable: false)
  - accessor (get/set)
  - batch (defineProperties)

TRAPS:
  - defineProperty defaults are FALSE
  - non-configurable is one-way
  - strict vs sloppy mode (throw vs silent fail)
```
