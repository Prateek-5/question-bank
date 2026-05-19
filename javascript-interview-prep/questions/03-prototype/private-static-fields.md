# Private static fields (`static #x`)

> **Difficulty:** Medium-Senior   |   **Time:** ~10 min   |   **Prereqs:** [class-to-prototype-desugar.md](./class-to-prototype-desugar.md)
>
> **Source:** ES2022 private static class members. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

`static #x = 0;` defines a class-level private field, accessible only inside the class body. Subclasses CANNOT access parent's static private.

**Verification examples**

```js
class IdGen {
  static #counter = 0;
  static next() { return ++IdGen.#counter; }
}
IdGen.next();                                                            // 1
IdGen.next();                                                            // 2
IdGen.#counter;                                                          // SyntaxError outside class

// Subclass cannot access parent's static private
class Base { static #x = 1; static get x() { return Base.#x; } }
class Sub extends Base {}
Sub.x;                                                                   // 1 (via inherited static method)
// Sub.#x;                                                                // SyntaxError — not declared in Sub
```

**Constraints**
- `static #field` on class itself, not instances.
- Lexically private — invisible outside class body.
- Subclass cannot reach parent's static private.
- Receiver-type check: `this` in static method must be the class (or subclass).

---

## 2. Plain-English restatement

Static fields belong to the constructor (the class itself), not instances. `#`-prefix makes them inaccessible outside. Useful for class-level singletons, counters, registries.

---

## 3. Why this matters in interviews

Tests modern JS (ES2022) + static-vs-instance distinction + subclassing nuance.

---

## 4. Mental model

```
   class Foo {
     #x = 1;            // instance private
     static #y = 2;     // class-level (static) private
     
     static method() { return Foo.#y; }
   }
   
   Lives where?
   - #x on each INSTANCE.
   - #y on Foo itself (the constructor).
   
   Subclass scope:
   - Sub extends Base where Base has static #x:
       Sub does NOT have its own #x slot.
       Sub.#x → SyntaxError ("#x not defined in Sub's body").
   - Inherited static method on Sub:
       Sub.staticMethod() works if it calls Base.#x via Base.staticMethod().
       But if static method uses `this.#x`, that fails with the wrong receiver.
   
   Receiver-type check:
   - Inside static method, `this` is the class (or subclass).
   - Accessing `this.#x` checks if `this` has the brand for #x.
   - Subclass `this` doesn't have parent's brand → TypeError.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Where does `static #x` live — instance or constructor?
> 2. Can a subclass access parent's `static #x`?
> 3. Why is `this.#x` in a static method risky for subclasses?

---

## 6. Brute force — walked through

### Wrong attempt 1: subclass inherits private
Sub's body doesn't declare #x; access throws SyntaxError.

### Wrong attempt 2: `Sub.staticMethod()` accesses parent's #x via this
TypeError — Sub doesn't have parent's brand.

### Wrong attempt 3: closure variable instead
Works but loses class-association; harder to introspect.

---

## 7. The unlocking insight

> **`static #x` lives on the constructor. Lexically private — only declaring class's body. Subclass CANNOT access parent's static private. Use named class reference (`Base.#x`), not `this.#x`, to avoid receiver-type traps.**

Three properties:

1. **Static private on constructor**, not instances.
2. **Lexically scoped** to declaring class.
3. **Receiver-type check** — `this.#x` may fail for subclass receiver.

---

## 8. Solution (annotated)

```js
class IdGen {
  static #counter = 0;                                                   // step 1: class-level private
  static next() { return ++IdGen.#counter; }                              // step 2: access via class name
}

IdGen.next();                                                            // 1
IdGen.next();                                                            // 2
// IdGen.#counter;                                                       // SyntaxError outside class

// Inheritance subtlety
class Base {
  static #x = 1;
  static get x() { return Base.#x; }                                     // step 3: use class name, not this
}
class Sub extends Base {}
Sub.x;                                                                   // 1 — inherited static method works

// Receiver-type trap
class Bad {
  static #y = 42;
  static getY() { return this.#y; }                                       // step 4: BAD — uses `this`
}
class SubBad extends Bad {}
Bad.getY();                                                              // 42 (this = Bad)
try { SubBad.getY(); } catch (e) { console.log(e.message); }             // TypeError: SubBad doesn't have brand for #y
```

**Try it yourself**

```js
// Singleton via static private
class Logger {
  static #instance;
  static getInstance() {
    if (!Logger.#instance) Logger.#instance = new Logger();
    return Logger.#instance;
  }
  log(msg) { console.log(msg); }
}

Logger.getInstance() === Logger.getInstance();                            // true

// Registry
class TypeRegistry {
  static #types = new Map();
  static register(name, cls) { TypeRegistry.#types.set(name, cls); }
  static resolve(name) { return TypeRegistry.#types.get(name); }
}

class Foo {}
TypeRegistry.register('foo', Foo);
TypeRegistry.resolve('foo') === Foo;                                      // true
```

---

## 9. Step-by-step dry run

```
class IdGen {
  static #counter = 0;
  static next() { return ++IdGen.#counter; }
}

At class evaluation:
  Define constructor IdGen.
  Set static #counter slot on IdGen with value 0.
  Define IdGen.next method.

IdGen.next():
  return ++IdGen.#counter:
    Lookup #counter on IdGen.
    Check: this declaration is in IdGen's body. OK.
    Read 0. Increment to 1. Store back.
    Return 1.

Sub.getY() where Bad has `static getY() { return this.#y; }`:
  Sub inherits getY via static chain.
  Invoke with this = Sub:
    Access this.#y:
      this = Sub. Check if Sub has brand for #y. NO (only Bad does).
      TypeError: Cannot read private member #y from an object whose class did not declare it.

To fix: use Bad.#y instead of this.#y inside static method.
```

---

## 10. Common confusion + traps

1. **Subclass inherits static private** — no, lexically scoped.
2. **`this.#x` in static method** — fails for subclass receiver.
3. **Use `ClassName.#x`** instead of `this.#x` for safety.
4. **Closure vs static private** — closure loses class association.
5. **`static` keyword** required; without it = instance private.
6. **TypeScript `private`** — type-only; runtime still accessible.
7. **`#name` shorthand** — actual identifier, used in code, not a string key.

---

## 11. Senior follow-ups & variants

### Variant 1 — Instance vs static private
`#x` per instance; `static #x` on constructor.

### Variant 2 — Singleton pattern
`static #instance` + `getInstance()` factory.

### Variant 3 — Registry
`static #types = new Map()` for type-name → class.

### Variant 4 — TypeScript `private` keyword
Compile-time only; runtime can access via `obj['privateField']`.

### Variant 5 — Pre-ES2022 alternatives
Module-scoped variable; WeakMap keyed by instance; Symbol property.

---

## 12. How to think aloud

> "`static #x` is a class-level private field. Lives on the CONSTRUCTOR (the class itself), not instances. Like `static x` (public) but inaccessible outside the class body. Subtlety: subclasses CANNOT access parent's static private because the slot is lexically scoped to the DECLARING class — Sub's body doesn't have a `#x` declaration, so `Sub.#x` is SyntaxError. Inheriting static methods is fine if they reference the parent class by NAME (`Base.#x`), not via `this.#x` — the latter triggers a receiver-type check which fails when invoked on a subclass. Use cases: class-level singletons (`static #instance`), counters (`static #counter`), type registries (`static #types = new Map()`). Pre-ES2022 alternatives: module-scoped variable, WeakMap keyed by class, Symbol property. Trap: subclass access; this.#x receiver mismatch; confusing static private with instance private; TypeScript `private` is type-only."

---

## 13. 60-second revision

> - **`static #x`** on CONSTRUCTOR, not instances.
> - **Lexically scoped** to declaring class body.
> - **Subclass CANNOT access** parent's static private.
> - **Use `ClassName.#x`** inside static methods, NOT `this.#x` (fails for subclass receiver).
> - **Use cases:** singleton, counter, registry.
> - **TypeScript `private`** is type-only; runtime still accessible.
> - **Trap:** subclass access; `this.#x` receiver mismatch; static vs instance.

---

**Related:** [class-to-prototype-desugar.md](./class-to-prototype-desugar.md) · [class-static-block-hoisting.md](../01-hoisting/class-static-block-hoisting.md) · [`02-closures/closure-vs-private-class-field-comparison.md`](../02-closures/closure-vs-private-class-field-comparison.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
