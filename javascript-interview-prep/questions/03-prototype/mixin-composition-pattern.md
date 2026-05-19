# Mixin composition pattern

> **Difficulty:** Medium-Senior   |   **Time:** ~12 min   |   **Prereqs:** [extends-super-implementation.md](./extends-super-implementation.md), [class-to-prototype-desugar.md](./class-to-prototype-desugar.md)
>
> **Source:** Justin Fagnani "Real Mixins with JS Classes" (2015). Stripe, Atlassian design-pattern depth.

---

## 1. Problem statement

Compose behavior across classes without single inheritance. The subclass-factory mixin pattern.

**Verification examples**

```js
const Serializable = (Base) => class extends Base {
  toJSON() { return { ...this, __type: this.constructor.name }; }
};

const Auditable = (Base) => class extends Base {
  constructor(...args) { super(...args); this.createdAt = Date.now(); }
};

class User { constructor(name) { this.name = name; } }
class AuditableUser extends Auditable(Serializable(User)) {}

const u = new AuditableUser('alice');
u.name;                                                                  // 'alice'
u.createdAt;                                                              // <timestamp>
JSON.stringify(u);                                                        // includes __type
```

**Constraints**
- Mixin = function `(Base) => class extends Base { ... }`.
- Chains via composition: `M1(M2(Base))`.
- Preserves `super` (unlike `Object.assign(prototype, mixin)`).
- `instanceof` works for each mixin in chain.

---

## 2. Plain-English restatement

JS doesn't have multiple inheritance. Instead, the "subclass factory" mixin is a function that takes a base class and returns a new class extending it with additional behavior. Compose multiple mixins by nesting calls: `Final extends M1(M2(M3(Base)))`. Preserves `super` calls naturally.

---

## 3. Why this matters in interviews

Design-pattern depth. Avoid naive `Object.assign(prototype, ...)` pitfalls.

---

## 4. Mental model

```
   Mixin = (Base) => class extends Base { /* additions */ }
   
   Compose:
   class Final extends M1(M2(M3(Base))) {}
   
   Chain at runtime:
   Final ──extends──▶ M1 (anonymous class) ──extends──▶ M2 (anon) ──extends──▶ M3 (anon) ──extends──▶ Base
   
   super(...) inside Final goes to M1's constructor.
   super(...) inside M1 goes to M2's, etc.
   
   instanceof works for ALL of them:
   final instanceof Base       → true
   final instanceof Final       → true
   
   Why NOT Object.assign(Target.prototype, Mixin):
   - Loses super (no class extension).
   - Breaks instanceof (Target doesn't extend Mixin).
   - Class methods are non-enumerable; Object.assign skips them.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `(Base) => class extends Base` better than `Object.assign(Target.prototype, mixin)`?
> 2. Does `super(...)` work in mixin constructors?
> 3. What's the order of execution for `M1(M2(M3(Base)))`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Object.assign(Target.prototype, mixin)`
Loses super; breaks instanceof; skips non-enumerable class methods.

### Wrong attempt 2: multiple `extends`
Not supported in JS.

### Wrong attempt 3: separate utility functions
Loses class identity; can't use instanceof.

---

## 7. The unlocking insight

> **Mixin = function returning a class that extends its `Base` argument. Compose via nesting. Preserves super, instanceof, and method non-enumerability.**

Three properties:

1. **Function returning class** — higher-kinded type.
2. **Compose by nesting** — `M1(M2(Base))`.
3. **`super` chain works** — uses class extends.

---

## 8. Solution (annotated)

```js
const Serializable = (Base) => class extends Base {                     // step 1: subclass factory
  toJSON() { return { ...this, __type: this.constructor.name }; }
};

const Auditable = (Base) => class extends Base {
  constructor(...args) {
    super(...args);                                                      // step 2: preserves super
    this.createdAt = Date.now();
  }
  audit() { return `created at ${this.createdAt}`; }
};

const Disposable = (Base) => class extends Base {
  dispose() {
    if (this._disposed) return;
    this._disposed = true;
    super.dispose?.();                                                   // step 3: optional super
  }
};

class User {
  constructor(name) { this.name = name; }
}

class AuditableUser extends Auditable(Serializable(Disposable(User))) {} // step 4: compose

const u = new AuditableUser('alice');
u.name;                                                                   // 'alice'
u.createdAt;                                                              // <timestamp>
u.audit();                                                                // 'created at ...'
u.dispose();                                                              // OK
JSON.stringify(u);                                                        // {"_disposed":true, "name":"alice", "createdAt":..., "__type":"AuditableUser"}

u instanceof User;                                                        // true
u instanceof AuditableUser;                                               // true
```

**Try it yourself**

```js
// Naive Object.assign — broken
class Bad {}
Object.assign(Bad.prototype, { method() { return 'hi'; } });
new Bad().method();                                                       // 'hi' BUT:
//  - method is enumerable (vs class method non-enumerable)
//  - no super support
//  - new Bad() instanceof <mixin source> → false
//  - inheritance chains break

// Mixin with constructor-running order
const M1 = (B) => class extends B {
  constructor(...a) { super(...a); console.log('M1'); }
};
const M2 = (B) => class extends B {
  constructor(...a) { super(...a); console.log('M2'); }
};
class Base { constructor() { console.log('Base'); } }
class C extends M1(M2(Base)) {
  constructor() { super(); console.log('C'); }
}
new C();
// Output: Base, M2, M1, C
// (super calls propagate up first)
```

---

## 9. Step-by-step dry run

```
class AuditableUser extends Auditable(Serializable(Disposable(User))) {}

Evaluation:
  Disposable(User) → anonymous class extends User, adds dispose.
  Serializable(...) → anonymous class extends previous, adds toJSON.
  Auditable(...) → anonymous class extends previous, adds constructor + audit.
  AuditableUser extends ...

Chain:
  AuditableUser → Auditable(...) → Serializable(...) → Disposable(...) → User → Object.prototype

new AuditableUser('alice'):
  AuditableUser constructor (default):
    super('alice')                              ← chains up
  Auditable constructor (mixin):
    super('alice')
  Serializable constructor (default — inherited Base's):
    super('alice')
  Disposable constructor (default — inherited):
    super('alice')
  User constructor:
    this.name = 'alice'.
  
  Then back down:
    Disposable, Serializable: no body work after super.
    Auditable: this.createdAt = Date.now().
    AuditableUser: no body work.
  
  Result: instance with name, createdAt, prototype chain through all mixins.

u.dispose():
  Walk chain to Disposable.prototype.dispose. Invoke.

u.toJSON():
  Walk chain to Serializable.prototype.toJSON. Invoke.

instanceof checks pass for ALL classes in chain.
```

---

## 10. Common confusion + traps

1. **`Object.assign(prototype, mixin)`** — loses super, instanceof, enumerability.
2. **Multiple `extends`** — not allowed in JS.
3. **Forget super() in mixin constructor** — breaks chain.
4. **State on prototype** — mixin instance state goes on `this`, not prototype.
5. **Mixin order matters** — methods can shadow.
6. **`this.constructor.name`** in mixin — refers to FINAL class, not anonymous mixin class.
7. **Static methods don't compose** — only instance.

---

## 11. Senior follow-ups & variants

### Variant 1 — Higher-kinded mixin
TypeScript: `<T extends new(...args:any[])=>any>(Base: T) => class extends Base { ... }`.

### Variant 2 — Mixin with private fields
Can use class private fields inside mixin body.

### Variant 3 — Static method composition
Mixins can add static methods; chain via `Object.assign(Class, mixinStatics)` or static factory.

### Variant 4 — Trait-like behavior
TC39 proposal for trait composition; not standard.

### Variant 5 — Composition over inheritance
Sometimes plain object composition (delegate methods) is cleaner than mixins.

---

## 12. How to think aloud

> "JS doesn't support multiple inheritance. The 'subclass factory' mixin is the canonical alternative: a function taking a base class and returning a new class extending it. `const M = (Base) => class extends Base { /* additions */ }`. Compose by nesting: `class Final extends M1(M2(M3(Base))) {}`. This preserves `super` (chain works naturally), `instanceof` (each layer is a real class), and method non-enumerability (class semantics). Naive `Object.assign(Target.prototype, mixin)` is WORSE because it loses super support, doesn't extend instanceof, and skips non-enumerable class methods. Order: constructors run bottom-up via super calls (Base → M3 → M2 → M1 → Final). State goes on `this`; methods on the anonymous class's prototype. Trap: Object.assign approach; multiple extends (illegal); forgetting super() in mixin constructor."

---

## 13. 60-second revision

> - **Mixin = `(Base) => class extends Base { ... }`**.
> - **Compose by nesting:** `M1(M2(Base))`.
> - **Preserves super, instanceof, non-enumerability** (vs Object.assign).
> - **Constructor order:** Base → ... → Final (via super chain).
> - **State on `this`**, methods on anonymous class prototype.
> - **Static methods don't compose** through subclass factory.
> - **Trap:** Object.assign approach; multiple extends; forget super().

---

**Related:** [extends-super-implementation.md](./extends-super-implementation.md) · [class-to-prototype-desugar.md](./class-to-prototype-desugar.md) · [method-chaining-builder.md](./method-chaining-builder.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
