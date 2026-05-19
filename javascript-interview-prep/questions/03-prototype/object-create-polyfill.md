# Polyfill `Object.create(proto, propsObj?)`

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md)
>
> **Source:** BFE.dev #65. Classic prototype-chain polyfill.

---

## 1. Problem statement

`objectCreate(proto, propsObj?)` returns a fresh object whose `[[Prototype]] === proto`, plus optional descriptors.

**Verification examples**

```js
const proto = { greet() { return 'hi' } };
const obj = objectCreate(proto);
Object.getPrototypeOf(obj) === proto;                                   // true
obj.greet();                                                            // 'hi'

const dict = objectCreate(null);                                        // null prototype
dict.toString;                                                          // undefined

const withProps = objectCreate(proto, {
  x: { value: 1, enumerable: true, writable: true, configurable: true },
});
withProps.x;                                                            // 1
```

**Constraints**
- Throw TypeError for non-object/non-null prototype.
- Allow functions as prototype (typeof 'function').
- Optional `propsObj` is a descriptor map (defaults: all false).

---

## 2. Plain-English restatement

Make a fresh object with the given prototype. The classic "empty constructor trick" abuses `new F()` to wire the prototype chain — same mechanism `new` uses, just with an empty function.

---

## 3. Why this matters in interviews

Forces "empty constructor trick" articulation + property-descriptor literacy.

---

## 4. Mental model

```
   Object.create(proto, propsObj?):
   
   Trick:
     function F() {}
     F.prototype = proto;
     const obj = new F();    // new wires obj.__proto__ = F.prototype = proto
   
   Why `new`?
   - `new F()` does: create obj, set obj.__proto__ = F.prototype, call F.
   - F is empty → no constructor side effects.
   - We only care about the prototype wiring.
   
   propsObj (optional):
   - Map of descriptors: { key: { value, writable, enumerable, configurable, get, set } }.
   - Defaults: all false (different from plain assignment).
   - Delegate to Object.defineProperties.
   
   Special cases:
   - proto === null → dictionary object (no toString, no hasOwnProperty).
   - typeof proto !== 'object' && typeof proto !== 'function' && proto !== null → TypeError.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why use the "empty constructor trick" instead of `obj.__proto__ = proto`?
> 2. What does `Object.create(null)` give you?
> 3. What's the difference between `{x: 1}` (assignment) and `Object.create({}, {x: {value: 1}})` (defineProperty)?

---

## 6. Brute force — walked through

### Wrong attempt 1: `{ __proto__: proto }`
Works in modern engines but uses legacy `__proto__` setter; breaks for `null`.

### Wrong attempt 2: skip type guard
`objectCreate(5)` should throw; missing guard returns silently broken object.

### Wrong attempt 3: ignore propsObj
Misses second argument entirely.

---

## 7. The unlocking insight

> **Empty constructor trick: `function F(){}; F.prototype = proto; return new F()`. Delegate `propsObj` to `Object.defineProperties`. Throw TypeError for invalid prototype.**

Three properties:

1. **Empty constructor trick** — abuses `new` for prototype wiring.
2. **`Object.defineProperties`** for descriptor map.
3. **Type guard** — null allowed; primitives throw.

---

## 8. Solution (annotated)

```js
function objectCreate(proto, propsObj) {
  if (proto !== null && typeof proto !== 'object' && typeof proto !== 'function') {
    throw new TypeError('Object prototype may only be an Object or null: ' + proto);
  }

  function F() {}                                                       // step 1: empty constructor
  F.prototype = proto;                                                  // step 2: set prototype
  const obj = new F();                                                  // step 3: new wires chain

  if (propsObj !== undefined) {
    Object.defineProperties(obj, propsObj);                              // step 4: descriptor map
  }
  return obj;
}
```

**Try it yourself**

```js
const proto = { greet() { return 'hi'; } };
const obj = objectCreate(proto);
Object.getPrototypeOf(obj) === proto;                                   // true
obj.greet();                                                            // 'hi'

// null prototype
const dict = objectCreate(null);
dict.toString;                                                          // undefined (no chain)
'toString' in dict;                                                     // false

// With descriptors
const o = objectCreate(proto, {
  x: { value: 1, enumerable: true },                                    // writable, configurable default false
});
o.x;                                                                    // 1
Object.getOwnPropertyDescriptor(o, 'x');
// { value: 1, writable: false, enumerable: true, configurable: false }

// Primitive throws
try { objectCreate(5); } catch (e) { e.message; }                       // 'may only be an Object or null'
```

---

## 9. Step-by-step dry run

```
objectCreate(proto):
  proto is an object → guard passes.
  function F() {} declared.
  F.prototype = proto.
  obj = new F():
    [[Construct]] creates obj.
    obj.[[Prototype]] = F.prototype = proto.
    F.apply(obj, []) → empty fn, no-op.
    return obj.
  Object.getPrototypeOf(obj) === proto ✓

objectCreate(null):
  proto === null → guard allows.
  F.prototype = null.
  new F() creates obj with obj.__proto__ = null.
  obj has NO inherited methods.

objectCreate({x:1}, {y: {value: 2, enumerable: true}}):
  obj = new F() with proto = {x:1}.
  Object.defineProperties(obj, {y: {...}}):
    Defines y with value 2, writable: false (default), enumerable: true.
  Result: obj inherits x from proto, has own y.
```

---

## 10. Common confusion + traps

1. **`{ __proto__: proto }`** — legacy setter; breaks for null.
2. **Skip null** in guard — `Object.create(null)` must work.
3. **Ignore propsObj** — second argument is real.
4. **Descriptor values must be objects** — `{x: 1}` is wrong; `{x: {value: 1}}` is right.
5. **Defaults all false** — `defineProperty` differs from assignment.
6. **`Object.setPrototypeOf`** — modern alternative; deopts engines.
7. **Cross-realm** — each realm has own `Object`; `.call` works.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Object.setPrototypeOf` alternative
Modern but deopts engines.

### Variant 2 — `Object.create(null)` use cases
Dictionaries; no `__proto__` collisions with user keys.

### Variant 3 — Descriptor defaults
`defineProperty` defaults all false; assignment defaults all true.

### Variant 4 — `Reflect.construct(F, args, new.target)`
Modern construct with explicit prototype.

### Variant 5 — Polyfill for ES5 target
Babel emits the empty-constructor trick when targeting ES5.

---

## 12. How to think aloud

> "Empty constructor trick: declare an empty `function F(){}`, set `F.prototype = proto`, return `new F()`. The `new` operator does 4 things — create obj, wire `obj.__proto__ = F.prototype`, run constructor (empty no-op), return obj. We piggyback on the prototype-wiring step. Why not `obj.__proto__ = proto`? That's a legacy setter that breaks for `null` prototype. Why not `Object.setPrototypeOf`? Polyfill scenario — and it deopts engines. Optional `propsObj` is a descriptor map (`{key: {value, writable, enumerable, configurable}}`); delegate to `Object.defineProperties`. Defaults are all FALSE in defineProperty (differs from assignment, where they're all true). Type guard: allow object/function/null; throw TypeError for primitives. `Object.create(null)` is the canonical 'dictionary' pattern — no inherited methods, safe for user-controlled keys (no `__proto__` pollution). Trap: legacy `__proto__` setter; ignoring propsObj; descriptor values not being objects."

---

## 13. 60-second revision

> - **Empty constructor trick:** `function F(){}; F.prototype = proto; return new F()`.
> - **Type guard:** allow object/function/null; throw for primitives.
> - **`propsObj`** → delegate to `Object.defineProperties`.
> - **Descriptor defaults all FALSE** (differs from assignment).
> - **`Object.create(null)`** = dictionary; no `__proto__`, no `toString`.
> - **vs `{ __proto__: proto }`** — legacy setter; breaks for null.
> - **vs `Object.setPrototypeOf`** — modern but deopts.
> - **Trap:** ignore propsObj; primitive value as descriptor (must be object).

---

**Related:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [polyfill-new.md](./polyfill-new.md) · [defineproperty-vs-assignment.md](./defineproperty-vs-assignment.md) · [object-setprototypeof-perf-trap.md](./object-setprototypeof-perf-trap.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
