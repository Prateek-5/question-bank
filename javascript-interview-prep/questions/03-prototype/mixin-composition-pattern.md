# Mixin Composition Pattern

## Source / Origin
- "Real Mixins with JavaScript Classes" (Justin Fagnani, 2015).
- Asked at: Stripe, Atlassian — design pattern depth questions.
- Concept reference: `concepts/prototype.md`.

## Why this question matters in interviews
"How do you compose behavior across classes without single inheritance?" Languages with multiple inheritance get it for free; JS doesn't. The mixin pattern uses functions that return classes extending a base. Senior bar: you avoid the naive `Object.assign(prototype, mixin)` (loses `super`, breaks `instanceof`) and use the higher-kinded "subclass factory" pattern.

## Concepts involved

### Syntax to lock in
```js
// Subclass-factory mixin
const Serializable = (Base) => class extends Base {
  toJSON() { return { ...this, __type: this.constructor.name }; }
};

const Auditable = (Base) => class extends Base {
  constructor(...args) { super(...args); this.createdAt = Date.now(); }
  audit() { return `created at ${this.createdAt}`; }
};

class User { constructor(name) { this.name = name; } }

class AuditableUser extends Auditable(Serializable(User)) {}

const u = new AuditableUser('alice');
u.audit();                       // 'created at ...'
JSON.stringify(u);               // includes name, createdAt, __type
u instanceof User;               // true
u instanceof AuditableUser;      // true
```

### Edge cases / traps
1. **Don't `Object.assign(Base.prototype, mixin)`.** Loses `super`, breaks `instanceof`, modifies shared prototype.
2. **Constructor chaining.** Each mixin's constructor must `super(...args)` to pass through.
3. **Method conflicts.** Last one wins (mixin order matters). Document or rename.
4. **`instanceof` against the mixin itself** — `u instanceof Auditable` fails because `Auditable` is a function returning a class. Mark with a Symbol or expose `static [Symbol.hasInstance]`.
5. **TypeScript** has its own mixin pattern (similar shape; uses higher-kinded types).
6. **Stateful mixins** — adding instance fields requires constructor; otherwise `this.x` is `undefined`.
7. **Composition order** — `A(B(C))` reads right-to-left; outermost is "most derived."
8. **Static methods** are inherited via class-to-class extension; no special handling needed.

## Mental Model

A mixin is a **subclass factory** — a function that takes a base class and returns a subclass with extra behavior:

```
   Auditable(Serializable(User))
   │         │         │
   │         │         └── concrete base class
   │         └── returns subclass of User with toJSON
   └── returns subclass of (Serializable(User)) with audit

   resulting prototype chain:
     u → AuditableUser.prototype → AnonAuditableClass.prototype → AnonSerializableClass.prototype → User.prototype → Object.prototype
```

## Why interviewers care

- **Composition over inheritance** — design principle senior signal.
- **Prototype chain manipulation** without the pitfalls.
- **Knowing the wrong way** (Object.assign) and the right way (subclass factory).

## Common confusion

- **"Object.assign mixin works."** It does for stateless methods but breaks `super`, can't pass constructor args, breaks `instanceof` for the mixin.
- **"Diamond problem."** JS's linearized chain avoids it; method resolution is left-to-right in `extends`.
- **"Mixins replace inheritance."** They complement — you still have single inheritance; mixins layer onto it.
- **"You can't do private state in mixins."** With `#` fields you can.

## Brute force

```js
// Object.assign hack — breaks super, instanceof
Object.assign(User.prototype, {
  toJSON() { return { ...this }; }
});
```

## Optimal approach

Subclass factories: `(Base) => class extends Base { ... }`. Stackable, preserves `super`, supports state via constructor.

## Solution

```js
// Define
const Serializable = (Base) => class extends Base {
  toJSON() { return { ...this, __type: this.constructor.name }; }
};
const Auditable = (Base) => class extends Base {
  constructor(...args) { super(...args); this.createdAt = Date.now(); }
  audit() { return `created at ${this.createdAt}`; }
};
const Cacheable = (Base) => class extends Base {
  #cache = new Map();
  cached(key, fn) {
    if (this.#cache.has(key)) return this.#cache.get(key);
    const v = fn(); this.#cache.set(key, v); return v;
  }
};

// Compose
class User { constructor(name) { this.name = name; } }
class FancyUser extends Cacheable(Auditable(Serializable(User))) {}

const u = new FancyUser('alice');
u.name;                          // 'alice'
u.audit();                       // 'created at ...'
u.cached('greeting', () => `hi ${u.name}`);
JSON.stringify(u);               // serializes
u instanceof User;               // true
u instanceof FancyUser;          // true

// Symbol-based instanceof
const Serializable = (Base) => {
  const C = class extends Base { toJSON() { return { ...this }; } };
  C[Symbol.hasInstance] = (inst) => 'toJSON' in inst;
  return C;
};
```

## Dry run

```
class User { constructor(name) { this.name = name; } }

A = Serializable(User):
  returns class extends User { toJSON() {} }
B = Auditable(A):
  returns class extends A { constructor(...args) { super(...args); this.createdAt = ... } audit() {} }
FancyUser = class extends B {}

new FancyUser('alice'):
  FancyUser.constructor — default; calls super('alice')
  B.constructor: super('alice') → A.constructor (none, falls to User) → User.constructor: this.name = 'alice'
  back to B.constructor: this.createdAt = Date.now()
  done

u.audit() → B.prototype.audit → exists
u.toJSON() → A.prototype.toJSON → exists
u.name → User.constructor set it
```

## How to think aloud

> "Subclass-factory mixins. Each mixin is `(Base) => class extends Base { ... }`. Compose by nesting: `M1(M2(Concrete))`. Each constructor must `super(...args)`. `instanceof` works for the resulting class and any in its chain. Object.assign is the wrong way — breaks `super`, mutates shared prototype. State via `#` fields inside the mixin. Order: outer = more derived. For `instanceof` against the mixin itself, custom `Symbol.hasInstance`."

## Important takeaways

- **Subclass factory `(Base) => class extends Base {}`** — the correct pattern.
- **`super(...args)`** required in every mixin constructor.
- **`Object.assign(proto, mixin)`** breaks `super` and `instanceof`.
- **Compose by nesting**; outer = derived.
- **State via `#` fields** or instance fields.
- **`Symbol.hasInstance`** for `instanceof` against the mixin itself.

## Variants

- **TypeScript higher-kinded mixin** — same shape with type guards.
- **Decorators (legacy)** — class decorators that wrap and add behavior.
- **Composition without classes** — pure functions that wrap object instances.
- **`Reflect.construct`** for dynamic mixin chains.

## Revision notes

```
mixin = (Base) => class extends Base {
  constructor(...args) { super(...args); /* init state */ }
  newMethod() {}
};

compose: Outer(Inner(Concrete))   // outer = more derived
  prototype chain: instance → Outer.proto → Inner.proto → Concrete.proto → Object

TRAPS:
  Object.assign(proto, mixin) → breaks super, instanceof
  forgot super(...args) → fields undefined
  
EXTRAS:
  static [Symbol.hasInstance] for instanceof-against-mixin
  #private fields work inside mixin
  composition order matters (last-wins on method conflict)
```
