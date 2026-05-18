# Class Static Blocks — Initialization Order & Hoisting

## Source / Origin
- ES2022 (`static { ... }` blocks).
- Asked at: Stripe, Atlassian, anywhere modern-JS knowledge is graded.
- Concept reference: `concepts/hoisting.md`, `concepts/prototype.md`.

## Why this question matters in interviews
Static blocks let a class run *imperative initialization code* once, in declaration order, with access to private members. They're a *new* construct (2022); senior interviews use them to test whether you've kept up with modern JS. Subtler: static blocks interact with hoisting and class-evaluation order in non-obvious ways. Get this right and you signal "I read the spec recently."

## Concepts involved

### Syntax to lock in
```js
class Config {
  static URL = 'http://x.com';
  static defaults;

  static {                              // runs once, at class definition time
    Config.defaults = { url: Config.URL, retries: 3 };
  }

  // Multiple static blocks allowed; run in source order
  static {
    Config.defaults.timeout = 5000;
  }
}
console.log(Config.defaults);            // {url, retries: 3, timeout: 5000}
```

### Edge cases / interview traps
1. **Run once, at class evaluation time.** Like a constructor for the class object.
2. **Multiple blocks, in source order.** Each runs in its own (block-scoped) `this` referring to the class.
3. **Access to private members** — `static { #x = 1 }` is allowed; useful for "friend" patterns.
4. **`this` in a static block** = the class itself (constructor function).
5. **TDZ for fields above.** Within a static block, fields *declared above* are accessible; fields *declared below* are TDZ.
6. **Class itself is in TDZ at the moment of evaluating the block.** Don't reference `Config` (the binding) before it's bound — but you usually use `this` inside.
7. **Cannot use `await`** in a static block; it's synchronous.
8. **Order vs inheritance**: a derived class's static block runs *after* the base class is fully evaluated.

## Mental Model

A class evaluation is a **mini-script**:

```
   class Foo {
     static a = 1;            // step 1: define static field a
     static b = a + 1;        // step 2: define b, can read a
     static { ... }           // step 3: run static block
     static c = something();  // step 4: define c after the block
   }
```

```
   evaluation order:
     1. evaluate base class (if extends)
     2. define class binding in TDZ
     3. in source order, evaluate each class element:
          a. static field with initializer
          b. static block { ... }
          c. instance fields don't run yet — they run per `new`
     4. class binding leaves TDZ; available externally
```

## Why interviewers care

- **Spec currency** — senior candidates know ES2022 features.
- **Initialization order** awareness.
- **Private member friendliness** — static blocks unlock the "expose private to a sibling helper" pattern.

## Common beginner confusion

- **"Static block runs on every instantiation."** No — once, at class evaluation.
- **"`this` in static block is `undefined`."** No — it's the class.
- **"`await` works."** It doesn't — synchronous only.
- **"Can call instance methods."** No — instances don't exist yet.
- **"Fields below are visible."** No — TDZ.

## Brute force approach

```js
// Pre-ES2022 alternative — IIFE outside the class
class Config {
  static URL = 'http://x.com';
}
(function init() {
  Config.defaults = { url: Config.URL, retries: 3 };
})();
```

Works, but pollutes module scope and can't see private members.

## Optimal approach

A `static { ... }` block inside the class body. Source-ordered, can see private and prior fields, runs once.

## Solution (JavaScript)

```js
class Cache {
  static #defaultTTL = 60_000;          // private static field
  static instances;

  static {
    Cache.instances = new Map();
    Cache.installDefaultLogger();
  }

  static installDefaultLogger() {
    console.log(`Cache module loaded; ttl=${Cache.#defaultTTL}ms`);
  }

  static get(name) {
    if (!Cache.instances.has(name)) Cache.instances.set(name, new Cache(name));
    return Cache.instances.get(name);
  }

  #name;
  constructor(name) { this.#name = name; }
}

// Static block at evaluation:
//   Cache.instances = new Map(); installDefaultLogger runs
// Later:
Cache.get('user-cache');               // new instance pushed to map
```

The "friend access" pattern — expose a class's private to a sibling:

```js
let getPrivate;
class Vault {
  #secret = 'sekret';
  static {
    getPrivate = (v) => v.#secret;     // captures private accessor
  }
}
// outside the class
console.log(getPrivate(new Vault()));  // 'sekret'
```

## Step-by-step dry run

```js
class A {
  static x = 1;
  static y = A.x + 1;
  static { A.z = A.x + A.y; }
  static w = A.z + 1;
}
console.log(A.x, A.y, A.z, A.w);       // 1, 2, 3, 4
```

```
evaluate class A:
  step 1: A binding enters TDZ
  step 2: in source order
    x: A.x = 1
    y: A.y = A.x + 1 = 2
    static block: A.z = A.x + A.y = 1 + 2 = 3
    w: A.w = A.z + 1 = 3 + 1 = 4
  step 3: A binding leaves TDZ

console.log(A.x, A.y, A.z, A.w):
  1, 2, 3, 4
```

Trap version:

```js
class B {
  static y = B.x + 1;     // B.x doesn't exist yet → NaN (undefined + 1)
  static x = 1;
  static { B.late = B.x + B.y; }
}
console.log(B.x, B.y, B.late);         // 1, NaN, NaN
```

## How to think aloud in the interview

> "Static block runs once at class evaluation, in source order, with `this` = the class. Can see private members and prior static fields. Useful for: complex one-time init that can't fit in a field initializer; exposing private accessors to friend modules. No `await`. TDZ rules apply for forward references. Multiple blocks run in source order, each as its own block scope."

## Important takeaways

- **Runs once, at class evaluation.**
- **Source order.** Multiple blocks allowed.
- **`this` = the class.**
- **Can see private members and prior fields.**
- **No `await`** (synchronous).
- **TDZ rules**: backward references OK, forward = error.
- **Friend pattern**: capture a closure over a private accessor.

## Variants

- **Decorator-driven init** — decorators (also ES2022/2023) can register the class; static block runs after decorators apply.
- **Inheritance** — base class fully evaluated before subclass; subclass static block can see inherited statics.
- **Mix with `Symbol.for`** — register the class globally during static init.
- **No async** — for async init at module level, use top-level await outside the class.

## Revision notes

```
class C {
  static a = ...;
  static b = ...;
  static { ... }       // runs ONCE, at class definition; this = C
  static c = ...;
}

Order:
  base class (if extends) → fields/blocks in source order
  fields ABOVE the block are accessible
  fields BELOW are TDZ
  
Constraints:
  - no await
  - this = class
  - multiple blocks OK; run in source order
  - can read/write private static fields
  
Patterns:
  - complex one-time init
  - friend access: let helper; static { helper = (x) => x.#priv; }
```
