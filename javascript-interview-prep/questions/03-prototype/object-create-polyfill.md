# Implement `Object.create(proto, propsObj?)`

## Source
- Classic prototype-chain interview problem (BFE.dev #65, JS Polyfill series, Frontend Masters).
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create

## Why this question matters in interviews
`Object.create` is the **most direct** way to set up a prototype chain — no constructors, no `new`, just "give me an object whose `[[Prototype]]` is exactly this." Implementing it forces you to articulate the "empty constructor trick" (`function F(){}; F.prototype = proto; return new F()`), which in turn explains how `new` wires the chain. The second argument — a `propsObj` with property descriptors — pulls in `Object.defineProperties` and forces you to talk about `value/writable/enumerable/configurable/get/set`. Backend engineers use `Object.create(null)` constantly for hash-map-shaped objects without `__proto__` pollution risks.

## Concepts involved

### Syntax to lock in
```js
function objectCreate(proto, propsObj) {
  if (proto !== null && (typeof proto !== 'object' && typeof proto !== 'function')) {
    throw new TypeError('Object prototype may only be an Object or null');
  }
  function F() {}
  F.prototype = proto;
  const obj = new F();
  if (propsObj !== undefined) Object.defineProperties(obj, propsObj);
  return obj;
}
```

### Runtime / engine behavior
- `new F()` does three things: (1) create a fresh `{}`, (2) set its `[[Prototype]]` to `F.prototype`, (3) call `F` with `this = new obj`. Since `F` is empty, step 3 is a no-op — we only care about step 2.
- Assigning `F.prototype = proto` makes every `new F()` instance inherit from `proto`.
- `Object.defineProperties(obj, descriptors)` accepts a map of `{ key: { value, writable, enumerable, configurable, get, set } }`. Defaults for absent flags are `false` — distinct from plain assignment (`obj.k = v`) where flags are `true`.
- Modern engines also expose `Object.setPrototypeOf(obj, proto)`, but the empty-constructor trick predates it and is the canonical "polyfill" answer.

### Edge cases (these are the interview traps)
1. **`null` prototype** — `Object.create(null)` produces a "dictionary object" with no inherited properties (no `toString`, no `hasOwnProperty`). Don't reject `null` in the type check.
2. **Primitive prototype** — `Object.create(5)` must throw `TypeError`. Mirror that.
3. **Functions as prototypes** — `typeof fn === 'function'`, not `'object'`. Allow it (functions are valid prototypes).
4. **Descriptor defaults** — if interviewer asks "what's the difference between `Object.create(p, { x: { value: 1 } })` and `Object.create(p, { x: 1 })`?" — the second is wrong; descriptor values must be objects. And the first creates `x` as non-writable / non-enumerable / non-configurable by default.
5. **`__proto__` accessor pollution** — pre-ES2022 polyfills used `obj.__proto__ = proto`, which respects the inherited `__proto__` setter and breaks for `null` protos. Use the empty-constructor trick or `Object.setPrototypeOf`.
6. **Why not `Object.setPrototypeOf` directly?** In a polyfill scenario you're often implementing both. Also, `setPrototypeOf` mutates an existing object; `create` builds a fresh one — the trick mirrors `new` semantics exactly.
7. **Cross-realm** — each realm has its own `Object`. `Object.create.call(otherRealmObject, ...)` works only because the function isn't realm-bound to its argument.

## Brute force approach
"Just return `{ __proto__: proto }`." Works in modern engines but: (a) doesn't handle `null` prototype cleanly (well, it does in ES2015+ but breaks in older runtimes), (b) doesn't handle the second `propsObj` argument, (c) uses the legacy `__proto__` setter, which the spec discourages. Acceptable as a quick answer; not the polyfill an interviewer wants.

## Optimal approach
Empty constructor trick + `Object.defineProperties` for the second argument. Five lines, zero magic. The trick is canonical because it uses only `new`, which everyone agrees on.

## Solution (JavaScript)

```js
/**
 * Polyfill for Object.create.
 * @param {object|null} proto
 * @param {Object<string, PropertyDescriptor>} [propsObj]
 * @returns {object}
 */
function objectCreate(proto, propsObj) {
  if (proto !== null && typeof proto !== 'object' && typeof proto !== 'function') {
    throw new TypeError('Object prototype may only be an Object or null: ' + proto);
  }

  // The "empty constructor" trick — `new F()` sets the new object's
  // [[Prototype]] to F.prototype, which we've pointed at `proto`.
  function F() {}
  F.prototype = proto;
  const obj = new F();

  // For `Object.create(null)`, instances are not linked to Object.prototype
  // at all — fine, the engine handles that.

  if (propsObj !== undefined) {
    Object.defineProperties(obj, propsObj);
  }

  return obj;
}
```

## Step-by-step dry run

Input:
```js
const animal = { eats: true, walk() { console.log('walking'); } };

const rabbit = objectCreate(animal, {
  jumps:  { value: true, enumerable: true },
  secret: { value: 42 } // defaults: non-enum, non-writable, non-config
});

rabbit.eats;                    // ?
rabbit.jumps;                   // ?
Object.keys(rabbit);            // ?
rabbit.secret = 99;             // ?
```

Trace:
- `objectCreate(animal, { ... })`:
  - `animal` is an object → type guard passes.
  - `F` is created; `F.prototype = animal`.
  - `obj = new F()` — fresh `{}` with `[[Prototype]]` pointing at `animal`.
  - `Object.defineProperties(obj, { jumps: ..., secret: ... })` — adds two own props.
- `rabbit.eats` — own lookup misses, walks chain → `animal.eats` → `true`.
- `rabbit.jumps` — own prop → `true`.
- `Object.keys(rabbit)` — own + enumerable. `jumps` is enumerable, `secret` isn't → `['jumps']`.
- `rabbit.secret = 99` — in strict mode throws (non-writable); in sloppy mode silently fails. `rabbit.secret` stays `42`.

Sanity:
- `objectCreate(null)` — `F.prototype = null`; `new F()` returns an object whose chain is `[null]`. `dict.hasOwnProperty` is `undefined` because there's no `Object.prototype` to inherit from. This is exactly what you want for safe dictionaries.

## Important takeaways

**Syntax to memorize**
- `function F() {}` — must be empty. Anything inside runs on every "create."
- `F.prototype = proto` — direct assignment, not via descriptor.
- `Object.defineProperties` (plural) for the second arg — descriptors are objects with `value/writable/enumerable/configurable` or `get/set`.

**Patterns to reuse**
- The empty-constructor trick is **how `new` wires up the prototype chain** — internalize it because every class-related question is a variation.
- `Object.create(null)` for safe hash maps — no `__proto__` setter trap, no inherited `hasOwnProperty`. Use `Object.hasOwn(map, key)` (ES2022) instead of `map.hasOwnProperty(key)`.

**Common mistakes**
- Using `Object.setPrototypeOf({}, proto)` and calling it the polyfill. Functionally correct but bypasses the teaching moment.
- Forgetting that descriptor defaults are `false` — surprises candidates when their property is "missing" from `Object.keys`.
- Passing `propsObj` as a flat `{ key: value }` instead of `{ key: { value: value } }`.
- Returning `Object.assign({}, proto)` — that's a **shallow copy**, not inheritance. Mutations on `proto` won't reflect.

**Related questions**
- `instanceof` polyfill (walks the chain `Object.create` builds)
- Polyfill `new` operator (the empty-constructor trick is the same idea)
- `Object.assign` vs `Object.create` (copy vs link)

## Variants

1. **`Object.create(null)` dictionary** — "Why is `Object.create(null)` preferred over `{}` for lookup tables in backend code?" Answer: no prototype pollution risk, no inherited `__proto__` setter, `hasOwn` queries are unambiguous.

2. **Inheritance helper** — "Write `inherit(Child, Parent)` using `Object.create`." Standard pre-ES6 inheritance: `Child.prototype = Object.create(Parent.prototype); Child.prototype.constructor = Child;`.

3. **Descriptor-aware clone** — "Implement `deepCloneWithDescriptors(obj)` using `Object.create(Object.getPrototypeOf(obj), Object.getOwnPropertyDescriptors(obj))`." Preserves prototype AND descriptors — the spec-compliant clone.

## Revision notes

> **Object.create polyfill — 60 second recap**
> - Empty constructor trick: `function F(){}; F.prototype = proto; return new F();`.
> - Optional second arg → `Object.defineProperties(obj, propsObj)`.
> - Type guard: `proto` must be object, function, or `null`. Reject primitives.
> - Descriptor defaults are **false** (non-writable / non-enum / non-config). Set them explicitly.
> - `Object.create(null)` → dictionary object, no chain to `Object.prototype`. Use for safe hash maps.
> - **Trap:** passing `{ key: value }` instead of `{ key: { value } }` for the second arg.
> - **Trap:** confusing copy (`Object.assign`) with link (`Object.create`) — the former snapshots, the latter inherits live.
