# `Object.defineProperty` vs plain assignment

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [getter-setter-via-prototype.md](./getter-setter-via-prototype.md)
>
> **Source:** ES5 property descriptors. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Why do `obj.x = 1` and `Object.defineProperty(obj, 'x', {value: 1})` behave differently?

**Verification examples**

```js
const obj = {};

obj.a = 1;
Object.getOwnPropertyDescriptor(obj, 'a');
// { value: 1, writable: true, enumerable: true, configurable: true }

Object.defineProperty(obj, 'b', { value: 2 });
Object.getOwnPropertyDescriptor(obj, 'b');
// { value: 2, writable: false, enumerable: false, configurable: false }

obj.b = 99;                                                              // strict: TypeError; sloppy: silent fail
Object.keys(obj);                                                        // ['a'] — b not enumerable
delete obj.b;                                                            // strict: TypeError
```

**Constraints**
- 4 flags: `value`, `writable`, `enumerable`, `configurable`.
- Assignment defaults all TRUE; defineProperty defaults all FALSE.
- Strict mode throws on bad ops; sloppy silently fails.
- Accessor descriptors have `get`/`set`, NOT `value`/`writable`.

---

## 2. Plain-English restatement

Every property has a 4-flag "passport". Plain assignment makes them all true (writable, enumerable, configurable). `Object.defineProperty` makes them all false unless you specify — so the property is locked down by default. Use defineProperty for read-only fields, hidden internal props, and getters/setters.

---

## 3. Why this matters in interviews

Tests property-descriptor literacy. Subtle bug source.

---

## 4. Mental model

```
   Every property has a 4-flag descriptor:
   
   Data property:                  Accessor property:
   ┌──────────────────────┐         ┌──────────────────────┐
   │ value: <V>           │         │ get: <function>      │
   │ writable: T/F        │         │ set: <function>      │
   │ enumerable: T/F      │         │ enumerable: T/F      │
   │ configurable: T/F    │         │ configurable: T/F    │
   └──────────────────────┘         └──────────────────────┘
   
   obj.x = v:
     - if not exists: create with {value:v, w:T, e:T, c:T}.
     - if exists and writable: update value.
     - if exists and not writable: fail (strict throws).
   
   Object.defineProperty(obj, 'x', desc):
     - merges desc with defaults (all false).
     - throws if configurable: false and you try to redefine.
   
   Three flags:
   - writable: can reassign via assignment.
   - enumerable: shows in for..in, Object.keys, JSON.stringify.
   - configurable: can redefine descriptor OR delete property.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `Object.defineProperty(obj, 'x', {value: 1})`, what's `Object.keys(obj)`?
> 2. Can you `obj.x = 99` afterward (strict)?
> 3. Can you `delete obj.x`?

---

## 6. Brute force — walked through

### Wrong attempt 1: "they're the same"
Different defaults; different lock-down.

### Wrong attempt 2: "writable means enumerable"
Independent flags.

### Wrong attempt 3: "delete on non-configurable in sloppy throws"
Strict throws; sloppy returns false silently.

---

## 7. The unlocking insight

> **Assignment defaults flags TRUE; `defineProperty` defaults FALSE. Use `defineProperty` for read-only fields, hidden props, getters/setters. Use `Object.defineProperties` (plural) for batch.**

Three properties:

1. **4 flags:** value, writable, enumerable, configurable.
2. **Default differs** assignment vs defineProperty.
3. **Accessor descriptors** mutually exclusive with data.

---

## 8. Solution (annotated)

```js
const obj = {};

// Plain assignment — all true
obj.a = 1;                                                              // step 1: flags all true
Object.getOwnPropertyDescriptor(obj, 'a');
// { value: 1, writable: true, enumerable: true, configurable: true }

// defineProperty — defaults all false
Object.defineProperty(obj, 'b', { value: 2 });                          // step 2: locked-down
Object.getOwnPropertyDescriptor(obj, 'b');
// { value: 2, writable: false, enumerable: false, configurable: false }

obj.b = 99;                                                              // step 3: strict TypeError; sloppy silent
Object.keys(obj);                                                        // ['a'] — b not enumerable

// Accessor descriptor
Object.defineProperty(obj, 'doubled', {
  get() { return this.a * 2; },
  enumerable: true,
  configurable: true,
});                                                                      // step 4: get/set, NO value/writable
obj.doubled;                                                             // 2 (computed)

// Batch
Object.defineProperties(obj, {
  x: { value: 10, writable: true },
  y: { value: 20, writable: false },
});

// Reflect.defineProperty returns boolean instead of throwing
Reflect.defineProperty(obj, 'frozen', { value: 1, configurable: false });
Reflect.defineProperty(obj, 'frozen', { value: 2 });                    // returns false
```

**Try it yourself**

```js
// Sealing / freezing locks descriptors
const o = { a: 1 };
Object.seal(o);                                                          // configurable: false
o.a = 2;                                                                 // OK (still writable)
o.b = 3;                                                                 // strict TypeError; sloppy silent
delete o.a;                                                              // strict TypeError

Object.freeze(o);                                                        // also writable: false
o.a = 5;                                                                 // strict TypeError

// __proto__ assignment is special — calls setPrototypeOf
const x = { __proto__: { greet() { return 'hi' } } };
x.greet();                                                               // 'hi'
```

---

## 9. Step-by-step dry run

```
obj.a = 1:
  obj has no own 'a'.
  Create with {value:1, writable:true, enumerable:true, configurable:true}.

Object.defineProperty(obj, 'b', {value:2}):
  Default descriptor: {writable:false, enumerable:false, configurable:false}.
  Merge with {value:2}.
  Define b: {value:2, w:false, e:false, c:false}.

obj.b = 99 in strict:
  Lookup 'b' descriptor: writable false.
  TypeError 'Cannot assign to read only property b'.

Object.keys(obj):
  Iterate own enumerable.
  'a' enumerable: include.
  'b' not enumerable: skip.
  Return ['a'].

delete obj.b in strict:
  Lookup 'b' descriptor: configurable false.
  TypeError 'Cannot delete property b'.
```

---

## 10. Common confusion + traps

1. **"Same as assignment"** — defaults differ.
2. **`writable` for accessor** — only data; accessor has no writable.
3. **Sloppy mode silent fail** — strict throws.
4. **`__proto__` assignment** is special (calls setPrototypeOf).
5. **`Object.freeze` is shallow** — nested objects still mutable.
6. **Redefine non-configurable** throws even with same value (mostly).
7. **`Reflect.defineProperty` boolean** vs `Object.defineProperty` throws.

---

## 11. Senior follow-ups & variants

### Variant 1 — Sealing / freezing
`Object.seal` (configurable: false). `Object.freeze` (also writable: false). Shallow.

### Variant 2 — Accessor descriptors
`get`/`set` mutually exclusive with `value`/`writable`.

### Variant 3 — `Object.defineProperties` (plural)
Batch define.

### Variant 4 — `Reflect.defineProperty`
Returns boolean instead of throwing.

### Variant 5 — `__proto__` accessor
Plain assignment to `__proto__` calls `setPrototypeOf`. Special case.

---

## 12. How to think aloud

> "Every property has a 4-flag descriptor: `value`, `writable`, `enumerable`, `configurable`. Plain assignment defaults them all TRUE — easy and ergonomic. `Object.defineProperty` defaults all FALSE — locked-down unless you specify. Why use defineProperty? Read-only fields (writable: false), hidden internal props (enumerable: false, won't show in for...in / Object.keys / JSON.stringify), preventing redefinition (configurable: false), and getter/setter installation. Accessor descriptors have `get`/`set` INSTEAD of `value`/`writable` — mutually exclusive. Sealing sets configurable false; freezing also sets writable false. Both shallow. `Object.defineProperties` for batch. `Reflect.defineProperty` returns boolean instead of throwing. `__proto__` assignment is special — calls setPrototypeOf. Trap: assuming defaults; mixing data + accessor flags; sloppy mode silent fails; assuming freeze is deep."

---

## 13. 60-second revision

> - **4 flags:** value, writable, enumerable, configurable.
> - **Assignment defaults TRUE**; **defineProperty defaults FALSE**.
> - **Data vs accessor** descriptors mutually exclusive.
> - **`enumerable: false`** → invisible to for...in, Object.keys, JSON.stringify.
> - **`writable: false`** → assignment fails (strict throws).
> - **`configurable: false`** → can't redefine or delete.
> - **`Object.seal` / `Object.freeze`** are shallow.
> - **`Reflect.defineProperty`** returns boolean.
> - **Trap:** defaults; accessor + writable; freeze depth.

---

**Related:** [getter-setter-via-prototype.md](./getter-setter-via-prototype.md) · [object-create-polyfill.md](./object-create-polyfill.md) · [hasownproperty-vs-in.md](./hasownproperty-vs-in.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
