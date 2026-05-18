# `Reflect.construct` vs `new`

## Source / Origin
- ES2015 `Reflect` API.
- Asked at: Razorpay, Atlassian; framework-internals interviews.
- Concept reference: `concepts/prototype.md`.

## Why this question matters in interviews
`new C(...)` is sugar; `Reflect.construct(C, args, newTarget)` is the underlying primitive. The third argument `newTarget` lets you construct an instance whose `[[Prototype]]` comes from a *different* class than the one whose constructor runs. That's how class-extension actually works internally. Senior bar: you can use it to extend built-ins (Error, Array) correctly, simulate `super()`, and explain `new.target`.

## Concepts involved

### Syntax to lock in
```js
class A {}
const a1 = new A();
const a2 = Reflect.construct(A, []);     // same thing
a2 instanceof A;                         // true

// The interesting form: newTarget different from constructor
class A { constructor() { this.fromA = true; } }
class B {}

const b = Reflect.construct(A, [], B);   // run A's constructor, but [[Prototype]] = B.prototype
b.fromA;                                 // true (A's body ran)
b instanceof B;                          // true
b instanceof A;                          // false
```

### Edge cases / traps
1. **`new.target`** — inside a constructor, this is the actual class being constructed (the `newTarget` from `Reflect.construct`). Without `new`, it's `undefined`.
2. **Extending built-ins** — pre-2015 patterns like `class MyError extends Error { constructor(msg) { super(msg); }` work in modern engines but historically (Babel transpilation) needed `Reflect.construct`.
3. **Subclassing without `extends`** — `Reflect.construct(Base, args, Sub)` simulates extension.
4. **Arrow functions** — can't be `new`'d; `Reflect.construct` on an arrow throws.
5. **`Reflect.construct(C, args)` ≡ `new C(...args)`** when third arg omitted.
6. **Performance** — slower than `new` by ~10-30%; don't use in hot paths.
7. **Used by mixin libraries** to graft class hierarchies dynamically.

## Mental Model

`new` does three things, in order:

```
   new C(args):
     1. obj = Object.create(C.prototype)
     2. result = C.call(obj, ...args)         // or: C's constructor body runs with this=obj
     3. return result if object, else obj

Reflect.construct(C, args, newTarget):
     1. obj = Object.create(newTarget.prototype)    ← here's the difference
     2. result = C.call(obj, ...args)
     3. return result if object, else obj
```

```
   prototype chain after Reflect.construct(A, [], B):
     obj → B.prototype → Object.prototype
   (A's body ran but didn't determine the chain)
```

## Why interviewers care

- **Spec depth** — knowing `new` is decomposable.
- **`new.target` literacy** — exotic but real.
- **Framework-internals signal** — Babel and TypeScript downleveling use this.

## Common confusion

- **"`Reflect.construct` is the same as `new`."** Only when third arg is omitted.
- **"newTarget = the constructor."** No — it's *who is being constructed*; often the same, but separable.
- **"`new.target` is `this`."** It's `this.constructor`, but more precisely it's whoever started the new chain.
- **"Arrow functions can be constructed."** They cannot — no `[[Construct]]` internal slot.

## Brute force

`new C(...args)` — fine for normal cases.

## Optimal approach

Reach for `Reflect.construct` when you need:
1. Subclass-from-runtime-decided base.
2. Extend built-ins correctly under transpiled code.
3. Reflective construction (factory by string name).

## Solution

```js
// 1. Reflective factory
const classes = { User: class User {}, Admin: class Admin extends User {} };
function create(name, ...args) {
  return Reflect.construct(classes[name], args);
}
create('Admin', /* ... */);

// 2. Pre-2017 Babel "extending Error" workaround
class MyError extends Error {
  constructor(msg) {
    super(msg);
    // Without proper transpilation, `this.name === 'Error'` and stack is wrong.
    // Manually fix:
    Object.setPrototypeOf(this, new.target.prototype);
    this.name = new.target.name;
  }
}

// 3. Subclassing via Reflect.construct (no `extends`)
function Subclass(Base, extras) {
  function Sub(...args) {
    const inst = Reflect.construct(Base, args, Sub);     // newTarget = Sub
    Object.assign(inst, extras);
    return inst;
  }
  Sub.prototype = Object.create(Base.prototype);
  Sub.prototype.constructor = Sub;
  return Sub;
}

// 4. Detect call without `new`
class Strict {
  constructor() {
    if (new.target === undefined) throw new Error('Must use new');
  }
}
new Strict();           // OK
Strict();               // TypeError (class without `new` always throws, but illustrative)

function Loose() {
  if (new.target === undefined) throw new Error('Must use new');
}
Loose();                // throws
new Loose();            // OK
```

## Dry run

```
Reflect.construct(A, [1, 2], B):
  newTarget = B
  obj = Object.create(B.prototype)
  call A's constructor with this=obj, args=[1,2]
  (inside A's body, new.target === B)
  return obj

obj instanceof B  → true
obj instanceof A  → false (unless B.prototype is in A.prototype's chain)
```

## How to think aloud

> "`new C(args)` is sugar for `Reflect.construct(C, args, C)`. The third arg, newTarget, is `new.target` inside the constructor — controls which prototype the new object gets. Useful for: subclassing without `extends`, extending built-ins under transpiled code, reflective construction by class name. Slower than `new` so reserve for genuine reflection needs. Inside a constructor, `new.target` lets the function detect 'was I called with new?' — useful for misuse-resistant APIs."

## Important takeaways

- **`new C(args) === Reflect.construct(C, args, C)`** (no third arg).
- **`newTarget` controls the result's `[[Prototype]]`.**
- **`new.target` inside constructor = newTarget**, undefined for plain calls.
- **Used for reflective construction, subclassing without `extends`, built-in extension under transpilers.**
- **Slower than `new`** — don't use in hot loops.

## Variants

- **`new.target.prototype` for prototype assignment** — common in Error subclass.
- **`Reflect.apply`** — same trick for non-construct calls.
- **`Proxy + Reflect.construct`** — wrap class construction for instrumentation.

## Revision notes

```
new C(args)            ≡ Reflect.construct(C, args, C)
Reflect.construct(C, args, NT):
  obj = Object.create(NT.prototype)
  C.call(obj, ...args)
  return obj if not object, else result

new.target:
  inside ctor — the newTarget (often === C; can differ via Reflect.construct)
  outside `new` — undefined
  detect plain call: if (!new.target) throw

USES:
  - reflective construction (by class name string)
  - extend built-ins under Babel-transpiled code (Object.setPrototypeOf(this, new.target.prototype))
  - subclass without `extends`

CAVEATS:
  - cannot construct arrow functions
  - slower than `new`
```
