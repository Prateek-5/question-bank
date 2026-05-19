# Polyfill the `new` operator

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md), [polyfill-call-apply.md](./polyfill-call-apply.md)
>
> **Source:** ECMA-262 §13.3.5. Atlassian, Razorpay, Microsoft, Uber.

---

## 1. Problem statement

`myNew(Ctor, ...args) ≡ new Ctor(...args)`. Replicate the 4-step `[[Construct]]` algorithm.

**Verification examples**

```js
function Person(first, last) {
  this.first = first;
  this.last = last;
}
Person.prototype.full = function () { return `${this.first} ${this.last}`; };

const p = myNew(Person, 'Ada', 'Lovelace');
p.full();                                                                // 'Ada Lovelace'
p instanceof Person;                                                     // true
```

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| Normal constructor                                  | obj.[[Proto]] = Ctor.prototype; Ctor.apply(obj, args)  |
| Constructor returns an object                       | that object wins (override rule)                       |
| Constructor returns a primitive                     | ignored; obj returned                                  |
| Constructor returns null                            | ignored; obj returned                                  |
| Arrow function as Ctor                              | TypeError (no [[Construct]])                           |
| Class constructor                                   | throws under `apply`; use `Reflect.construct` instead  |

**Constraints**
- 4 steps: create obj, wire prototype, apply, return-with-override.
- Override rule: only objects/functions override; null/primitives don't.
- `Object.create(Ctor.prototype)` — NOT `Object.create(Ctor)`.

---

## 2. Plain-English restatement

`new Ctor(args)` does 4 things: (1) creates fresh object, (2) wires its prototype to `Ctor.prototype`, (3) calls `Ctor` with `this = obj`, (4) returns obj unless the constructor explicitly returned an object/function (then that wins).

---

## 3. Why this matters in interviews

The definitive prototype-chain interview question. Tests `Object.create`, `apply`, return-value override rule, `Reflect.construct`.

---

## 4. Mental model

```
   `new Ctor(...args)` = [[Construct]] internal:
   
   Step 1. obj = {} (fresh object).
   Step 2. obj.[[Prototype]] = Ctor.prototype.
   Step 3. result = Ctor.apply(obj, args).
   Step 4. if result is non-null object/function:
              return result   ← OVERRIDE rule
            else:
              return obj
   
   Why Object.create(Ctor.prototype):
   - Wire the chain BEFORE running constructor.
   - Constructor body can do `this instanceof Ctor` check correctly.
   
   Override rule examples:
     function F() { this.x=1; return {y:2}; }
     new F() → {y:2}   ← override (object returned)
   
     function G() { this.x=1; return 42; }
     new G() → {x:1}   ← primitive ignored, obj wins
   
     function H() { this.x=1; return null; }
     new H() → {x:1}   ← null ignored (typeof null is 'object' but spec excludes)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `new (function(){ return [1,2]; })()` return?
> 2. What does `new (function(){ this.x=1; return null; })()` return?
> 3. Why doesn't `myNew` work with class constructors?

---

## 6. Brute force — walked through

### Wrong attempt 1: `return new Ctor(...args)`
Not a polyfill — uses the operator you're defining.

### Wrong attempt 2: `Object.create(Ctor)` instead of `Object.create(Ctor.prototype)`
Wrong target; methods don't resolve.

### Wrong attempt 3: skip override rule
Singletons / factories break.

---

## 7. The unlocking insight

> **Four steps: `Object.create(Ctor.prototype)` → `Ctor.apply(obj, args)` → check return type → return override or obj. Override only for non-null object/function. For `class` support: `Reflect.construct(Ctor, args)`.**

Three properties:

1. **`Object.create(Ctor.prototype)`** wires the chain.
2. **`apply` runs constructor** with `this = obj`.
3. **Override rule** for objects/functions only.

---

## 8. Solution (annotated)

```js
function myNew(Ctor, ...args) {
  if (typeof Ctor !== 'function' || !Ctor.prototype) {
    throw new TypeError(`${Ctor?.name || 'value'} is not a constructor`);
  }

  const obj = Object.create(Ctor.prototype);                            // step 1+2: create + wire proto
  const result = Ctor.apply(obj, args);                                 // step 3: run constructor

  const overrode = result !== null && (
    typeof result === 'object' || typeof result === 'function'
  );                                                                      // step 4: override check
  return overrode ? result : obj;
}

// Class-compatible version (production)
function myNewSpecCompliant(Ctor, ...args) {
  return Reflect.construct(Ctor, args);
}
```

**Try it yourself**

```js
// Normal constructor
function Person(first, last) {
  this.first = first;
  this.last = last;
}
Person.prototype.full = function () { return `${this.first} ${this.last}`; };

const p = myNew(Person, 'Ada', 'Lovelace');
p.full();                                                                // 'Ada Lovelace'
p instanceof Person;                                                     // true

// Override rule — singleton pattern
function Singleton() {
  this.greet = 'hi';
  return { iAmTheSingleton: true };
}
const s = myNew(Singleton);
s;                                                                       // { iAmTheSingleton: true } — override
s.greet;                                                                 // undefined (obj garbage-collected)

// Primitive return ignored
function Weird() { this.x = 1; return 42; }
const w = myNew(Weird);
w;                                                                       // { x: 1 } — primitive ignored

// Arrow rejected
const Arrow = () => {};
try { myNew(Arrow); } catch (e) { e.message; }                          // 'Arrow is not a constructor'
```

---

## 9. Step-by-step dry run

```
const p = myNew(Person, 'Ada', 'Lovelace'):

  Ctor = Person, args = ['Ada', 'Lovelace'].
  typeof Ctor === 'function' ✓; Person.prototype exists ✓.
  
  Step 1+2: obj = Object.create(Person.prototype)
    obj = {}; obj.[[Proto]] = Person.prototype.
  
  Step 3: Person.apply(obj, ['Ada', 'Lovelace'])
    Run Person body with this = obj:
      obj.first = 'Ada'
      obj.last = 'Lovelace'
    Implicit return undefined.
    result = undefined.
  
  Step 4: typeof undefined === 'undefined' → not object/function.
    overrode = false.
    Return obj.

p = { first: 'Ada', last: 'Lovelace' } with Person.prototype as proto.

p.full():
  Walk p chain → Person.prototype.full found.
  Invoke with this=p → 'Ada Lovelace'.

Override case:
  myNew(Singleton):
    obj = Object.create(Singleton.prototype).
    Singleton.apply(obj, []):
      obj.greet = 'hi'.
      Return { iAmTheSingleton: true }.
    result = {iAmTheSingleton: true} (object).
    overrode = true.
    Return result (NOT obj).
  obj is garbage-collected.
  s.greet is undefined.
```

---

## 10. Common confusion + traps

1. **`Object.create(Ctor)`** — wrong target; use `Ctor.prototype`.
2. **Return obj unconditionally** — breaks override rule.
3. **Forget primitive/null filter** — would return primitives/null.
4. **Recursive `new Ctor(...args)`** — defeats purpose.
5. **Apply on class constructor** — "Class constructor cannot be invoked without 'new'"; use `Reflect.construct`.
6. **Arrow function as Ctor** — no `[[Construct]]`; reject up-front.
7. **`new.target`** undefined under polyfill; affects subclass behavior.

---

## 11. Senior follow-ups & variants

### Variant 1 — Subclass-aware `new`
`Reflect.construct(Ctor, args, NewTarget)` — controls `new.target`.

### Variant 2 — `class`-compatible
Replace `apply` with `Reflect.construct`.

### Variant 3 — `Object.create` polyfill
`function fakeCreate(p){ function F(){}; F.prototype=p; return new F(); }`.

### Variant 4 — Implement `instanceof`
Companion polyfill — walk chain looking for `Ctor.prototype`.

### Variant 5 — `new Date()` vs `Date()`
`Date` checks `new.target` — returns string without `new`, Date object with.

---

## 12. How to think aloud

> "Four spec steps: (1) create fresh obj, (2) `obj.[[Prototype]] = Ctor.prototype` via `Object.create(Ctor.prototype)`, (3) `Ctor.apply(obj, args)` runs constructor body with `this=obj`, (4) if constructor returned a non-null object/function, return THAT (override rule); otherwise return obj. Override only for non-null object/function — null and primitives are ignored. This is how singletons, factories, and the immutable-instance pattern work. Limitations: arrow functions have no `.prototype` → can't be `new`'d; class constructors throw under `apply` ('must be invoked with new'). For full spec fidelity and class support: `Reflect.construct(Ctor, args, NewTarget)`. Trap: `Object.create(Ctor)` instead of `Object.create(Ctor.prototype)`; returning obj unconditionally (misses override); calling `apply` on class constructors."

---

## 13. 60-second revision

> - **4 spec steps:** create obj → wire proto → apply → return-with-override.
> - **`Object.create(Ctor.prototype)`** — NOT `Object.create(Ctor)`.
> - **`Ctor.apply(obj, args)`** runs constructor with `this=obj`.
> - **Override rule:** non-null object/function wins; null/primitive ignored.
> - **Arrow** → no `[[Construct]]`; reject.
> - **Class constructors** throw under apply; use `Reflect.construct`.
> - **`Reflect.construct(Ctor, args, NewTarget)`** is spec-complete.
> - **Trap:** Object.create(Ctor); unconditional obj return; class via apply.

---

**Related:** [polyfill-bind.md](./polyfill-bind.md) · [polyfill-call-apply.md](./polyfill-call-apply.md) · [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [instanceof-polyfill.md](./instanceof-polyfill.md) · [reflect-construct-vs-new.md](./reflect-construct-vs-new.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
