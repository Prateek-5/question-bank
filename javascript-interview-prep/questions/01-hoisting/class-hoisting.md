# Class declaration hoisting

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [tdz-let-const.md](./tdz-let-const.md), [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md)
>
> **Source:** MDN Classes hoisting. Senior JS gate question.

---

## 1. Problem statement

Does `class` hoist like `function` or like `let`/`const`?

**Verification examples**

| Setup                                              | Result                                              |
|----------------------------------------------------|------------------------------------------------------|
| `greet(); function greet(){}`                       | works (function decl fully hoisted)                |
| `new Foo(); class Foo {}`                           | **ReferenceError** (class is TDZ — like `let`)     |
| `class Child extends Parent {}; class Parent {}`    | ReferenceError (Parent in TDZ at extends eval)     |
| `class Foo {}; class Foo {}` (same scope)           | SyntaxError (redeclaration)                         |
| Class body inside `if (cond) { class X {} }`        | block-scoped; invisible outside                    |

**Constraints**
- `class` hoists like `let`/`const` — into TDZ.
- Class body is always strict mode.
- `extends ParentExpr` evaluates at declaration line; Parent must be initialized.
- Block-scoped (no sloppy escape hatch).

---

## 2. Plain-English restatement

`class Foo {}` is roughly equivalent to `const Foo = class {...}` — the binding hoists into TDZ. Any access (read, write, `new`, `typeof`) before the declaration line throws ReferenceError. **NOT** like function declarations (fully hoisted with body).

---

## 3. Why this matters in interviews

Gotcha question. Most engineers know function declarations are fully hoisted; assume `class` is too. Senior bar: knows it's TDZ + can explain WHY (extends clauses, computed keys, static initializers must run in source order).

---

## 4. Mental model

```
   Mental shortcut: class Foo {} ≈ const Foo = class {...}
   
   Both hoist the BINDING but not the value (until declaration line runs).
   
   ┌─────────────────────────────────────────────────────────┐
   │ function decl   → fully hoisted (body + name)            │
   │                   callable from line 1                   │
   ├─────────────────────────────────────────────────────────┤
   │ class decl      → hoisted to LE as <uninitialized> (TDZ) │
   │                   ReferenceError on access before line   │
   ├─────────────────────────────────────────────────────────┤
   │ let/const decl  → hoisted to LE as <uninitialized> (TDZ) │
   └─────────────────────────────────────────────────────────┘
   
   Why class isn't fully hoisted:
   - extends ParentExpr can have side effects.
   - Computed keys [expr]() {} may need surrounding state.
   - Static initializers run during class evaluation.
   - Hoisting body would change observable order.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `new Foo(); class Foo {}` throw?
> 2. `class Child extends Parent {} class Parent {}` — what happens?
> 3. Is class body strict mode automatically?

---

## 6. Brute force — walked through

### Wrong attempt 1: "class hoists like function"
WRONG. Classes hoist like let/const (TDZ).

### Wrong attempt 2: "classes aren't hoisted"
Also wrong. They ARE — into TDZ.

### Wrong attempt 3: "extends accepts string"
`extends` evaluates an arbitrary expression — must result in a constructor.

---

## 7. The unlocking insight

> **`class` hoists binding into Lexical Environment as `<uninitialized>` (TDZ). Same as `let`/`const`. Access before declaration line throws. Class body is always strict mode. `extends ParentExpr` evaluates at declaration line — if Parent in TDZ, throws.**

Three properties:

1. **TDZ like `let`/`const`** — NOT like function.
2. **Strict by default** — class body always strict.
3. **`extends` evaluates at declaration line** — ordering matters.

---

## 8. Solution (annotated)

```js
// THE classic trap
try {
  new Animal();                                                       // step 1: TDZ → ReferenceError
} catch (e) {
  console.log('Pre-decl:', e.message);                                 // 'Cannot access ...'
}

class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a sound`; }
}

new Animal('rex').speak();                                              // 'rex makes a sound'

// Inheritance + TDZ
try {
  class Dog extends Mammal {}                                          // step 2: Mammal in TDZ
} catch (e) {
  console.log('Inherit:', e.message);
}

class Mammal extends Animal {}

class Dog extends Mammal {
  speak() { return `${this.name} barks`; }
}
new Dog('rex').speak();                                                 // 'rex barks'

// Class expression with named binding
const Cat = class FelineImpl {
  static who() { return FelineImpl.name; }                              // step 3: inner name local
};
Cat.who();                                                              // 'FelineImpl'
// FelineImpl outside → ReferenceError
```

**Try it yourself**

```js
// Mental shortcut: class ≈ const + class expression
class Foo {}
// ≈
const Foo = class {};

// Both hoist binding, not value.

// Class body strict mode
class Bar {
  method() {
    octals = 0o7;                                                       // SyntaxError in body
  }
}

// extends with arbitrary expression
function makeBase() { return class { hi() { return 'hi'; } }; }
class Sub extends makeBase() {}
new Sub().hi();                                                         // 'hi'

// Redeclaration
class A {}
// class A {}                                                            // SyntaxError (same scope)

// Block scope
if (true) { class X {} }
typeof X;                                                                // 'undefined' (block-scoped)
```

---

## 9. Step-by-step dry run

```
Module creation phase:
  Animal → LE: <uninitialized> (TDZ)
  Mammal → LE: <uninitialized> (TDZ)
  Dog    → LE: <uninitialized> (TDZ)
  Cat    → LE: <uninitialized> (TDZ)

Module execution phase:
  1. try { new Animal() } → resolve Animal → <uninitialized> → ReferenceError
     catch: log 'Pre-decl: Cannot access Animal before initialization'
  
  2. class Animal {...}:
     evaluate class body (methods, prototype).
     bind Animal to class object. TDZ ends.
  
  3. new Animal('rex').speak() → 'rex makes a sound'
  
  4. try { class Dog extends Mammal {} }:
     evaluate Dog declaration.
     evaluate extends Mammal → Mammal in TDZ → ReferenceError.
     catch logs.
  
  5. class Mammal extends Animal {}:
     evaluate extends Animal (Animal initialized) → succeeds.
     bind Mammal.
  
  6. class Dog extends Mammal {...} → succeeds.
  
  7. new Dog('rex').speak() → 'rex barks'
  
  8. const Cat = class FelineImpl {...}:
     evaluate class expression.
     FelineImpl is bound INSIDE the class body's LE.
     Cat is bound in outer LE.
  
  9. Cat.who() → 'FelineImpl' (inner name visible via Function.name).
```

---

## 10. Common confusion + traps

1. **`class` hoists like `function`** — no, like `let`/`const`.
2. **`class` isn't hoisted** — it is, into TDZ.
3. **Class body not strict** — always strict.
4. **`extends` accepts any value** — must be constructor or null.
5. **Block-scoped sloppy escape** — none (unlike function decls in blocks).
6. **Named class expression's inner name visible outside** — no, local to body.
7. **Circular import + class** — late-loaded module sees other class in TDZ.

---

## 11. Senior follow-ups & variants

### Variant 1 — Why not hoist body?
Computed keys, `extends`, static initializers must run in source order; hoisting body would change observable behavior.

### Variant 2 — Static block self-reference
Inside `static {}`, can reference class name (after the block evaluates). Computed keys before static blocks may hit TDZ.

### Variant 3 — Circular ESM import + class
A imports B; B imports A; both export classes extending each other → ReferenceError at runtime. Restructure or lazy-load.

### Variant 4 — `class X extends null`
Valid; prototype chain ends. `new X()` throws by default.

### Variant 5 — Class expression for IIFE
`const C = (class { ... })()` — class expressions can be called immediately (rare).

---

## 12. How to think aloud

> "Mental shortcut: `class Foo {}` ≈ `const Foo = class {...}` + extra rules. Hoists binding into Lexical Environment as `<uninitialized>` — TDZ until declaration line. Same as `let`/`const`, NOT like function decl (which fully hoists). Pre-declaration access (read, write, `new`, `typeof`) throws ReferenceError. Why not hoist body? Class body contains arbitrary expressions — `extends` clauses, computed keys, static initializers — that must run in source order. Hoisting would change observable behavior. `extends ParentExpr` evaluates at declaration line; if Parent is in TDZ, throws. Class body is always strict mode. Block-scoped — no sloppy escape. Named class expression's inner name is local to body (good for self-reference). Trap: 'classes hoist like functions'; circular ESM imports."

---

## 13. 60-second revision

> - **`class Foo {}` ≈ `const Foo = class {...}`** + extras.
> - **Hoisted into LE as TDZ** — same as `let`/`const`.
> - **Pre-decl access** (read, write, `new`, `typeof`) → ReferenceError.
> - **NOT like function decl** (which fully hoists).
> - **Class body always strict mode** (implicit).
> - **`extends ParentExpr`** evaluates at decl line — Parent must be initialized.
> - **Block-scoped;** no sloppy escape.
> - **Named class expression inner name** local to body.
> - **Trap:** "class hoists like function"; circular ESM imports.

---

**Related:** [tdz-let-const.md](./tdz-let-const.md) · [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md) · [class-static-block-hoisting.md](./class-static-block-hoisting.md) · [circular-import-live-binding-quiz.md](./circular-import-live-binding-quiz.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md), [`concepts/prototype.md`](../../concepts/prototype.md)
