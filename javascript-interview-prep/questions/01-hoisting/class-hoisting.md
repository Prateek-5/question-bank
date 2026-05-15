# Class declaration hoisting

## Source
Canonical senior-JS interview problem. MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes#hoisting

## Why this question matters in interviews
Senior screens love this one because it's a "gotcha" that filters out candidates who pattern-match `class` to `function`. Most engineers know function declarations are fully hoisted; they assume `class` is too, since both create constructable callables. Wrong — `class` follows `let`/`const`/TDZ semantics. As a backend engineer working with TypeScript / NestJS / Mongoose / TypeORM models, you'll occasionally hit "Cannot access 'Foo' before initialization" in a circular dependency or a misordered import, and the fix requires knowing exactly how class hoisting works. This question also stress-tests your understanding of the broader TDZ concept.

## Concepts involved

### Syntax to lock in
```js
// Function declaration — fully hoisted, callable before its line
greet();                          // works
function greet() { console.log('hi'); }

// Class declaration — hoisted but in TDZ
new Foo();                        // ReferenceError: Cannot access 'Foo' before initialization
class Foo {}

// Class expression — only the binding is hoisted (per var/let/const rules)
new Bar();                        // ReferenceError (TDZ on const)
const Bar = class { };

// Named class expression
const C = class NamedC {
  who() { return NamedC.name; }   // NamedC is locally visible inside the class body
};
new C().who();                    // 'NamedC'
// console.log(NamedC);            // ReferenceError outside
```

### Runtime / engine behavior
- During the **creation phase** of an Execution Context, `class` declarations register a binding in the **Lexical Environment** as `<uninitialized>` — identical to `let`/`const`.
- The class binding remains in TDZ until the `class Foo {}` line runs in the execution phase.
- This is **distinct from function declarations**, which register with the full function object during creation and are callable immediately.
- The reason: classes can have computed property keys, `extends` clauses with arbitrary expressions, and static initializers — all of which must run in source order. Hoisting the full body would change the meaning of `extends getBase()` if `getBase` had side effects.
- A class declaration is essentially `const ClassName = class {...}` with a few extra rules (the class body is implicitly strict-mode; the class name binds twice — once outside, once inside the body).
- Classes are **block-scoped**. `if (cond) { class X {} } typeof X` → `'undefined'`.

### Edge cases (interview traps)
1. **`typeof Foo` before declaration throws** (TDZ), just like `let`.
2. **Inheritance + TDZ** — `class Child extends Parent {} class Parent {}` → `ReferenceError` when evaluating `extends Parent`, because `Parent` is in TDZ when `Child`'s `extends` clause runs.
3. **Re-declaration is SyntaxError** at parse — `class Foo {}; class Foo {};` won't run.
4. **Hoisting inside a block** — `class` declarations are strictly block-scoped (no sloppy-mode escape hatch like function decls).
5. **Implicit strict mode** — the body of a class is always strict, even if the surrounding code isn't. This affects `this`, `with`, octal literals, etc.
6. **Static blocks and class fields** — they execute during the `class Foo {}` evaluation, top-to-bottom. Any TDZ violation inside (e.g., a static block referencing the class itself before its initializer) throws.
7. **`new.target`** — inside the constructor, `new.target` is the class being instantiated (useful for abstract-class enforcement).

## Brute force approach
Rusty candidate: *"Classes are hoisted like functions, so you can use them before declaration."* Wrong, but a very common answer. The interviewer is probing exactly this misconception. Corollary mistake: *"Classes aren't hoisted at all."* Also wrong — they are, but in TDZ. The right answer threads the needle: hoisted (binding registered) + uninitialized (TDZ) = ReferenceError on early access.

## Optimal approach
Frame `class` as **syntactic sugar over `const ClassName = class {...}` with extra rules**. Then `class` hoisting follows the `const` rules: binding registered during creation, in TDZ until the declaration line runs. Mention the **why**: classes contain arbitrary expressions (`extends`, computed keys, static initializers) that must run in source order — hoisting the body would break that contract.

## Solution (JavaScript)

```js
// === The classic trap ===
try {
  new Animal();                       // ReferenceError — TDZ
} catch (e) {
  console.log('Pre-decl:', e.message); // 'Cannot access ...'
}

class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} makes a sound`; }
}

console.log(new Animal('rex').speak()); // 'rex makes a sound'

// === Inheritance + TDZ ===
try {
  class Dog extends Mammal {}         // Mammal in TDZ at this moment
} catch (e) {
  console.log('Inherit:', e.message);
}

class Mammal extends Animal {}

// Now this works:
class Dog extends Mammal {
  speak() { return `${this.name} barks`; }
}
console.log(new Dog('rex').speak());  // 'rex barks'

// === Class expression with named binding ===
const Cat = class FelineImpl {
  static who() { return FelineImpl.name; }  // local name visible inside
};
console.log(Cat.who());                // 'FelineImpl'
// console.log(typeof FelineImpl);     // ReferenceError — not in outer scope
```

## Step-by-step dry run

**Module Execution Context — Creation phase**

| Binding   | Environment | Initial value         |
|-----------|-------------|-----------------------|
| `Animal`  | LE          | `<uninitialized>` (TDZ) |
| `Mammal`  | LE          | `<uninitialized>` (TDZ) |
| `Dog`     | LE          | `<uninitialized>` (TDZ) |
| `Cat`     | LE          | `<uninitialized>` (TDZ) |

(The class names live in the LE just like `let`/`const`.)

**Execution phase**

1. `try { new Animal() }` → resolve `Animal` → binding in `<uninitialized>` → `ReferenceError: Cannot access 'Animal' before initialization`. Catch prints `Pre-decl: ...`.
2. `class Animal {...}` line executes:
   - Evaluate the class body (define methods, set up prototype).
   - Bind `Animal` to the class object. TDZ for `Animal` ends.
3. `new Animal('rex').speak()` → works → `'rex makes a sound'`.
4. `try { class Dog extends Mammal {} }`:
   - Engine begins evaluating the `class Dog` declaration.
   - The `extends` clause evaluates `Mammal` → still in TDZ → `ReferenceError`. Catch prints.
   - The first `Dog` declaration was **inside a try block** — the binding for `Dog` in the outer LE was already registered during creation, but the **assignment to it never happens**, so the second `class Dog` below can still complete. *(In practice, you'd avoid wrapping a class declaration in a try block — this is purely for illustration.)*
5. `class Mammal extends Animal {}` → `Animal` is initialized → succeeds. `Mammal` binding initialized.
6. `class Dog extends Mammal {...}` → succeeds. `Dog` initialized.
7. `new Dog('rex').speak()` → `'rex barks'`.
8. `const Cat = class FelineImpl {...}` → evaluates the class expression. The expression itself binds `FelineImpl` inside its own scope (the class body's LE), and binds `Cat` in the outer LE.
9. `Cat.who()` → calls the static method. Inside, `FelineImpl.name === 'FelineImpl'`. Prints `'FelineImpl'`.

## Important takeaways

**Syntax to memorize**
- `class` declaration → hoisted to enclosing **block** as `<uninitialized>` (TDZ).
- TDZ semantics: read/write/`typeof`/`new` before declaration line all throw `ReferenceError: Cannot access 'X' before initialization`.
- Class body is **always strict mode**.
- Class expression with a name: the inner name is local to the class body (useful for self-references).

**Patterns to reuse**
- Treat `class Foo {}` mentally as `const Foo = class {...}` — same hoisting and TDZ rules.
- For abstract classes, check `new.target === AbstractClass` in the constructor and throw.
- For circular dependencies between class modules, restructure imports — don't try to "hoist around" TDZ.

**Common mistakes**
- Assuming `class` hoists like `function`. It doesn't.
- Writing `class Child extends Parent {} class Parent {}` and getting a confusing TDZ error. Order matters.
- Forgetting that class bodies are strict — code that worked outside (e.g., implicit globals, `arguments.callee`) breaks inside.

**Related questions**
- TDZ with `let`/`const`
- Function declaration vs expression hoisting
- ES module hoisting and circular imports
- Prototype chain and `extends`

## Variants

1. **Why is `class` not hoisted like `function`?** — Because class bodies contain arbitrary expressions (`extends getBase()`, computed keys `[expr]() {}`, static initializers) that must execute in source order with their side effects. Hoisting the body would change observable behavior.

2. **TDZ + static block self-reference** — inside `static { ... }`, can you reference the class name? Yes, but only after the static block runs (mostly fine in practice since the body is evaluated top-to-bottom). Computed keys evaluated BEFORE static blocks may hit TDZ.

3. **Circular import + class TDZ** — in Node ESM, file A `import { B } from './b.js'`; file B `import { A } from './a.js'`; both export classes that extend each other. The later-loaded module sees the other in TDZ → `ReferenceError`. Fix: refactor to break the cycle or lazy-load.

## Revision notes

> **class hoisting — 60 second recap**
> - `class` is hoisted into the enclosing block's LE as `<uninitialized>` — same as `let`/`const`. **TDZ applies.**
> - Pre-declaration access (`new Foo`, `typeof Foo`, `Foo.prop`) → `ReferenceError: Cannot access 'Foo' before initialization`.
> - **Not** like `function` declaration (which is fully hoisted).
> - Mental model: `class Foo {}` ≈ `const Foo = class {...}` + extra rules.
> - Class body is **always strict mode**, even in sloppy surroundings.
> - `extends ParentClass` evaluates the parent expression at the declaration line → if `Parent` is in TDZ, throws.
> - Block-scoped; no sloppy-mode escape hatch.
> - **Trap:** ordering matters for inheritance: declare parents before children.
> - **Trap:** named class expression (`class Foo {}` as RHS) — `Foo` is visible only inside the class body, not outside.
