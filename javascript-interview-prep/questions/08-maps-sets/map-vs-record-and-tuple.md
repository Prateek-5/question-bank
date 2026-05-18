# Map vs Record / Tuple (Future Proposal)

## Source / Origin
- TC39 Records and Tuples proposal (Stage 2 since 2020).
- Asked at: Razorpay, Cloudflare — modern-spec-awareness questions.
- Concept reference: `concepts/maps-sets.md`.

## Why this question matters in interviews
JS has no value-typed immutable composite. Maps and arrays compare by identity, not content. Record/Tuple would add `#{a: 1}` and `#[1, 2]` with structural equality and deep immutability — game-changer for state management, memoization, set membership of objects. Senior bar: you know the proposal exists, its semantics, and what you do *today* in its absence.

## Concepts involved

```js
// Today
{a: 1} === {a: 1};                    // false (identity)
[1, 2] === [1, 2];                     // false

// Map with object as key
const m = new Map();
m.set({id:1}, 'a');
m.get({id:1});                         // undefined (different object)

// Future (Record/Tuple)
#{a: 1} === #{a: 1};                   // true (structural)
#[1, 2] === #[1, 2];                   // true
typeof #{a:1};                         // 'record'
typeof #[1,2];                         // 'tuple'

// Records and tuples can contain only primitives, other records, and tuples
// Cannot contain objects or functions
```

### Today's workarounds
1. **String canonicalization** — `JSON.stringify({a:1})` as key; brittle to key order.
2. **WeakMap with shared identity** — works if you cache the object: `cache.get(JSON.stringify(...)).objRef`.
3. **Symbol-interned tuples** — see `composite-key-strategies.md`.
4. **Immutable.js / Immer** — third-party value-typed structures.

### Edge cases / traps
1. **Proposal is Stage 2** — not in any engine yet. Use polyfills (`@bloomberg/record-tuple-polyfill`) only for prototypes.
2. **Cannot contain objects or functions** — only primitives, records, tuples (and primitive arrays).
3. **Strict equality (`===`) becomes structural.** Major change in language semantics.
4. **Identity** preserved via interning (engines share equal records).
5. **Mutation** — every "update" returns a new record (`#{...r, b: 2}`).
6. **Symbols** — primitive but not allowed in records (debated).

## Mental Model

```
   Today:
     object === object iff same reference
     Map key on object → identity
     deep equal needs explicit walk

   With Record/Tuple:
     #{...} and #[...] are values, not references
     === is structural deep equality
     usable as Map key with content-based equality
     immutable by construction
```

## Why interviewers care

- **TC39 currency.**
- **Functional-state-management intuition.**
- **Awareness of limitations** of today's Map/Object/Array for value semantics.

## Common confusion

- **"Records are objects."** They're a new primitive type — value semantics, not reference.
- **"Tuples are immutable arrays."** Yes, but more: deep-frozen, structurally compared.
- **"Use Object.freeze for the same effect."** Frozen objects still compare by identity.

## Solution (today, until R/T ships)

```js
// Canonical-string-as-key
function canon(obj) {
  // sort keys recursively
  if (Array.isArray(obj)) return '[' + obj.map(canon).join(',') + ']';
  if (obj && typeof obj === 'object') {
    return '{' + Object.keys(obj).sort().map(k => JSON.stringify(k) + ':' + canon(obj[k])).join(',') + '}';
  }
  return JSON.stringify(obj);
}

const m = new Map();
m.set(canon({a:1, b:2}), 'x');
m.get(canon({b:2, a:1}));   // 'x' (key order doesn't matter)

// Polyfill flavor (Bloomberg)
import { Record, Tuple } from '@bloomberg/record-tuple-polyfill';
const r1 = Record({a: 1});
const r2 = Record({a: 1});
Record.equal(r1, r2);   // true

// Memoization with structural keys (today)
function memoStructural(fn) {
  const cache = new Map();
  return (arg) => {
    const k = canon(arg);
    if (cache.has(k)) return cache.get(k);
    const r = fn(arg);
    cache.set(k, r);
    return r;
  };
}
```

## How to think aloud

> "Records and Tuples are a TC39 proposal (Stage 2) for value-typed immutable composites: `#{a:1}` and `#[1,2]`. They use === for deep structural equality. Today's equivalents are awkward — canonicalize to string for Map keys, or use Immutable.js. The proposal would simplify memoization, state management, and 'Map with content-keyed objects' patterns. Until it ships, the patterns are: canonicalize-to-string, intern tuples with Symbols, or use a polyfill in prototypes."

## Important takeaways

- **TC39 Stage 2** — not in production engines yet.
- **Value semantics**: `#{a:1} === #{a:1}` is true.
- **Deep immutable** by construction.
- **Cannot contain objects/functions.**
- **Today's substitutes**: string canonicalization, Symbol interning, Immutable.js.

## Variants

- **Immer / Mutable** — third-party deep-immutable abstractions.
- **Immutable.js** — battle-tested but heavy.
- **Symbol-interned tuple** — handcrafted approximation.
- **Polyfills** for R/T proposal — experimental.

## Revision notes

```
Records & Tuples (TC39 Stage 2):
  #{a: 1}                    record
  #[1, 2, 3]                 tuple
  #{a:1} === #{a:1}          true (structural)
  contain only primitives, other records, tuples
  deep immutable
  
TODAY (no native):
  canonicalize to string for Map keys
  Symbol interning for tuple-like keys
  Immutable.js for big needs

USES (when shipped):
  Map keys with content equality
  memoization with deep keys
  Set membership for object values
  React state with === comparison
```
