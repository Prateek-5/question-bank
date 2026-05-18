# Private Static Fields (`static #x`)

## Source / Origin
- ES2022 private static class members.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/prototype.md`, sibling `closure-vs-private-class-field-comparison.md`.

## Why this question matters in interviews
Static fields on a class belong to the constructor, not instances. The `#static` variant makes them inaccessible outside the class — perfect for class-level singletons, registries, or counters. Senior bar: you understand the inheritance subtlety (a *subclass* can't access the parent's `static #x`), and the receiver-type check (`this` in a static method must be the class itself).

## Concepts involved

### Syntax to lock in
```js
class IdGen {
  static #counter = 0;
  static next() { return ++IdGen.#counter; }
}
IdGen.next(); IdGen.next();   // 1, 2
IdGen.#counter;               // SyntaxError outside class
```

### Edge cases / traps
1. **Subclass cannot access parent's static private.**
   ```js
   class Base { static #x = 1; static get x() { return Base.#x; } }
   class Sub extends Base {}
   Sub.x;            // 1 (via inherited method)
   Sub.#x;           // SyntaxError — Sub's body doesn't declare #x
   ```
2. **Static methods on subclass with `this` referring to subclass.**
   ```js
   class Base { static #count = 0; static inc() { this.#count++; } }
   class Sub extends Base {}
   Sub.inc();        // TypeError: this (= Sub) doesn't have private field #count
   ```
   Fix: `Base.#count++` (use the class explicitly).
3. **Initializer evaluation order** — fields in source order, before static blocks unless they come before in source.
4. **`this` in static method** — refers to the class on direct call; can change with `call`/`apply`. Always use the class name for private static access.
5. **Memory** — one slot per class definition, shared across all instances (they don't have it).
6. **Reflection** — invisible to `Object.getOwnPropertyNames(ClassName)`.

## Mental Model

```
   class C {
     static #x = 0;       // belongs to C (the constructor object)
     #y = 0;              // belongs to each instance

     static method() {    // `this` = C (when called as C.method())
       C.#x++;            // OK
     }
   }

   slot table on the class object:
     C → { static #x: 0, ... }
   slot table on each instance:
     inst → { #y: 0 }
```

## Why interviewers care

- **Private + static = class-level singleton/counter** — common pattern.
- **Inheritance pitfall awareness** — the receiver-type check.
- **Static field initialization** — order, semantics.

## Common confusion

- **"`Sub.#x` should work because Sub extends Base."** No — private fields are looked up on `this`'s class, and `Sub` doesn't declare `#x`.
- **"`static` methods can read sibling instances' privates."** Yes if they're the same class (`#` is scoped to class definition).
- **"`#` and `static` are independent."** They are — combine for class-level privacy.

## Brute force

A module-level `let counter = 0` + factory — works, but exposes the counter to the module scope.

## Optimal approach

`static #field` keeps it strictly inside the class body. Accessor methods if external read is needed.

## Solution

```js
// Singleton with private static state
class Logger {
  static #instance = null;
  static #defaultLevel = 'info';
  level;
  constructor(level) { this.level = level; }
  static getInstance() {
    if (!Logger.#instance) Logger.#instance = new Logger(Logger.#defaultLevel);
    return Logger.#instance;
  }
  static setDefaultLevel(l) { Logger.#defaultLevel = l; }
}

Logger.getInstance() === Logger.getInstance();   // true

// Registry pattern
class PluginRegistry {
  static #plugins = new Map();
  static register(name, factory) {
    if (PluginRegistry.#plugins.has(name)) throw new Error(`dup ${name}`);
    PluginRegistry.#plugins.set(name, factory);
  }
  static create(name, ...args) {
    const f = PluginRegistry.#plugins.get(name);
    if (!f) throw new Error(`no plugin ${name}`);
    return f(...args);
  }
}

PluginRegistry.register('cache', () => new Cache());
PluginRegistry.create('cache');

// ID generator with subclass-safe static
class IdGen {
  static #counter = 0;
  static next() { return ++IdGen.#counter; }     // use IdGen, not this
}
class TaggedIdGen extends IdGen {
  static next() { return `t-${IdGen.next()}`; }  // calls parent via class name
}
TaggedIdGen.next();   // 't-1'
IdGen.next();         // 2 (shared counter)
```

## Dry run

```
class IdGen { static #counter = 0; static next() { return ++IdGen.#counter; } }

class evaluation:
  define IdGen as a function
  set static slot #counter = 0 on IdGen
  set IdGen.next = static method

IdGen.next():
  this = IdGen
  ++IdGen.#counter → reads private slot 0, writes 1, returns 1
```

Inheritance trap:

```js
class IdGen { static #counter = 0; static inc() { this.#counter++; } }
class Sub extends IdGen {}
Sub.inc();
  this = Sub
  Sub.#counter → SyntaxError at parse (#counter not declared in Sub's class body)
                or TypeError at runtime (no private slot on Sub)
```

Fix: `inc() { IdGen.#counter++; }`.

## How to think aloud

> "`static #x` is class-level private. Access via `ClassName.#x` from inside the class; trying from outside or from subclass body throws. Subclasses can call inherited static methods that internally access the parent's private — but if those methods use `this.#x`, the call from subclass fails. Always reference the declaring class by name for private statics. Use cases: singletons, registries, ID counters, default config."

## Important takeaways

- **`static #x`** — class-level slot, syntax-private.
- **Subclasses don't inherit private slots.**
- **Access via class name** (`ClassName.#x`), not `this.#x` in static methods.
- **Patterns**: singleton, registry, ID gen, defaults.
- **Invisible to reflection** (`Object.getOwnPropertyNames`).

## Variants

- **`static` block** with private statics — see `01-hoisting/class-static-block-hoisting.md`.
- **Public static + closure encapsulation** (older pattern).
- **WeakMap-keyed-by-class** (rare, pre-2022).

## Revision notes

```
class C {
  static #x = 0;        // class-level private slot
  static getX() { return C.#x; }
}

C.getX();   // 0
C.#x;       // SyntaxError outside class

INHERITANCE:
  Sub extends C — Sub does NOT have its own #x
  Sub.getX() — works IF method uses C.#x (not this.#x)
  this.#x in static method called from Sub → fails

USES: singleton, registry, ID gen, defaults

best practice: ALWAYS use ClassName.#x in static methods (not this.#x)
```
