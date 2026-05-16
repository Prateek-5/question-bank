# Prototype, `this`, and Inheritance

> **Senior-mentor framing:** Most languages do inheritance via *classes* — blueprints that define a type, and instances that are minted from those blueprints. JavaScript was originally designed differently: objects inherit directly from other objects via a chain of links called *prototypes*. ES6 `class` syntax was layered on top, but **underneath it's still prototype delegation**. Mastering this distinction is what separates a JS user from a JS engineer.

## Why this concept exists (first principles)

Imagine a library where every book has a slip pointing to "if I don't have this chapter, look in this *other* book." That second book might also have a slip pointing to a third, and so on until you reach a book with no slip (`null`). Reading a chapter means: check this book → if missing, follow the slip → check the next book → keep going until found or you run out of books.

That chain of slips is the **prototype chain**.

- The "book" is an object.
- The "slip" is its internal `[[Prototype]]` link (accessible as `Object.getPrototypeOf(obj)`).
- "Looking up a chapter" is property access (`obj.x`).
- The bottommost book (`Object.prototype`) has a `null` slip — end of chain.

**Why design it this way?** Sharing. If 10,000 user objects each had their own copy of `greet()`, that's 10,000 function allocations. Instead, the function lives on `User.prototype` *once*, and every user object delegates to it via the slip. Memory-efficient and dynamic — you can patch `User.prototype.greet` and every existing instance instantly sees the new version.

> **Mental Model:** Objects don't "have" inherited methods — they **borrow** them via the chain. Writing `user.greet()` triggers a lookup walk; the lookup finds `greet` on `User.prototype` and calls it with `user` as `this`. The method *lives elsewhere but runs as if it lived on `user`*.

## Why interviewers care

- ORM models, Express middleware, and many Node libs rely on prototype-based inheritance (`util.inherits`, `EventEmitter`, `stream` classes).
- Method-lookup performance and shape transitions (V8 hidden classes) affect hot paths.
- `this` confusion in callbacks is the #1 source of subtle bugs in route handlers and class-based services.
- "Implement `new`" / "implement `bind`" / "implement `instanceof`" are interview classics — they test whether you understand the mechanics under the syntax.

## Common beginner confusion

- "`prototype` and `__proto__` are the same thing." — **No.** `__proto__` (legacy) / `Object.getPrototypeOf(obj)` is the slip *on any object*. `Function.prototype` (the property) only exists on *functions*; it's the object that will *become* the slip-target of any instance created with `new`.
- "`class` is a new kind of object." — **No.** It's syntactic sugar over a constructor function plus prototype assignments.
- "Arrow functions are just shorter regular functions." — **No.** They have **no own `this`**, no `prototype` property, can't be `new`'d, and lexically capture `this` from definition site.
- "`this` depends on where the function is defined." — **For regular functions: no.** It depends on **how it's called** (call site). For arrow functions: yes, lexical.
- "`instanceof` checks the type." — Half-true. It checks if the constructor's `prototype` is *anywhere on the chain*. Spoofable via `Symbol.hasInstance` or `Object.setPrototypeOf`.

## Progressive concept building

**Beginner level:** "Every object has a prototype (its 'parent'). When you read `obj.foo`, JS first checks `obj`, then its prototype, then up the chain."

**Intermediate level:** "`new Foo()` creates an object whose `[[Prototype]]` is `Foo.prototype`. Methods on `Foo.prototype` are shared among all instances. `class` is sugar for this pattern."

**Advanced level:** "Hidden classes (V8 shapes) are how the engine optimizes property access. Adding/deleting properties dynamically deopts. `this` is determined by 5 binding rules with a strict precedence (new > explicit > implicit > default; arrow ignores all of these and uses lexical)."

**Interview expectation:** You can desugar a class to constructor + prototype, implement `new`/`bind`/`instanceof` from scratch, predict `this` in any context, and explain V8 hidden classes' relevance.

## TL;DR
- **Every JS object has an internal `[[Prototype]]`** linking to another object (or `null`). Property lookup walks this chain.
- `obj.__proto__` (legacy accessor) === `Object.getPrototypeOf(obj)` === the prototype object.
- `Function.prototype` is the object that becomes the `[[Prototype]]` of instances created with `new Function()`. **`prototype` (on a function) ≠ `__proto__` (on any object).**
- `class` is **syntactic sugar** over prototype + constructor function. Methods go on `Class.prototype`; arrow methods go per-instance (no `this` binding via prototype).
- `this` has 5 binding rules: default, implicit, explicit (`call`/`apply`/`bind`), `new`, and arrow (lexical).

## Why backend interviewers care
- ORM models, Express middleware, and many Node libs rely on prototype-based inheritance (`util.inherits`, `EventEmitter`, `stream` classes).
- Method-lookup performance and shape transitions (V8 hidden classes) affect hot paths.
- `this` confusion in callbacks is the #1 source of subtle bugs in route handlers and class-based services.

## Core mental model

> **Mental Model — Prototype chain = lookup linked list:** Property access is a *walk* up a singly-linked list of objects ending in `null`. Found → return. End of list → `undefined`. Writing always goes on the *bottom* object (the one you're holding), never on an intermediate prototype, unless a setter intercepts.

JS inheritance is **delegation**: when you read `obj.x`, the engine checks `obj`, then `Object.getPrototypeOf(obj)`, then *its* prototype, until `null`. Writing always goes on `obj` itself (unless setter on the chain).

### The four canonical chains — visualized

```
literal {}      ──[[Prototype]]──>  Object.prototype  ──>  null

[]              ──[[Prototype]]──>  Array.prototype   ──>  Object.prototype  ──>  null

function(){}    ──[[Prototype]]──>  Function.prototype ──> Object.prototype  ──>  null

new Foo()       ──[[Prototype]]──>  Foo.prototype     ──>  Object.prototype  ──>  null
```

```
literal {}    --> Object.prototype --> null
[]            --> Array.prototype  --> Object.prototype --> null
function(){}  --> Function.prototype --> Object.prototype --> null
new Foo()     --> Foo.prototype    --> Object.prototype --> null
```

### Class instance chain — visualized

```
class Animal {}
class Dog extends Animal {}
const d = new Dog();

d
│
│ [[Prototype]]
▼
Dog.prototype  ──[[Prototype]]──>  Animal.prototype  ──[[Prototype]]──>  Object.prototype  ──>  null
   │                                  │                                     │
   │ .constructor                     │ .constructor                        │ .constructor
   ▼                                  ▼                                     ▼
  Dog                               Animal                                Object

(Static chain — separate!)
Dog ──[[Prototype]]──> Animal ──[[Prototype]]──> Function.prototype ──> Object.prototype ──> null
```

When you call `d.bark()`:
1. Look on `d` — not there.
2. Walk to `Dog.prototype` — found! Call it with `this = d`.

When you call `d.toString()`:
1. Look on `d` — not there.
2. Walk to `Dog.prototype` — not there.
3. Walk to `Animal.prototype` — not there.
4. Walk to `Object.prototype` — found! Call it with `this = d`.

### V8 hidden classes (shapes)

V8 uses **hidden classes** (a.k.a. shapes) to optimize property access. Objects with the same property layout share a hidden class, enabling inline caches that turn `obj.x` into a single offset load. Adding/removing properties changes the shape and invalidates the IC — *don't* dynamically add fields in hot code; initialize in the constructor.

> **Intuition:** V8 treats objects with the same property *order* as "the same type" internally — even though JS pretends every object is dynamic. Two objects created with the same constructor and same property additions in the same order share a shape. The instant you add a property `obj.foo` *after* the fact, V8 creates a new shape. Hot loops hate shape churn.

```js
class User {
  constructor(id, name) {
    this.id = id;
    this.name = name;
  }
  greet() { return `hi ${this.name}`; }
}
// Equivalent (pre-class):
function User(id, name) { this.id = id; this.name = name; }
User.prototype.greet = function () { return `hi ${this.name}`; };
```

`greet` lives once on `User.prototype` — shared by all instances → memory-efficient. If you defined `greet = () => ...` as a class field, each instance gets its own copy (but `this` is permanently lexically bound).

### `this` — five rules

> **Mental Model for `this`:** Stop asking "what is `this`?" at the function's *definition* site. Ask: **"how is this function being CALLED right now?"** The call site determines `this` for regular functions; the definition site only matters for arrow functions.

```
       ┌─────────────────────────────────────────────────────┐
       │   Determining `this` for a regular function call    │
       └────────────────────┬────────────────────────────────┘
                            │
            ┌───────────────┼────────────────┐
            │               │                │
       called with     called with         called as
        `new`?         `.call/.apply/      `obj.fn()`?
                       .bind`?              (dot syntax)
            │               │                │
            ▼               ▼                ▼
       new object      provided ctx          obj
       (rule 4)        (rule 3)            (rule 2)
            │               │                │
            └───────┬───────┴────────┬───────┘
                    │                │
                  none of the above?
                    │
                    ▼
           strict mode? → undefined  (rule 1)
           sloppy mode? → globalThis (rule 1)

   Arrow functions ignore ALL of this — they capture `this` lexically
   from where they were DEFINED (rule 5).
```

1. **Default**: bare call `fn()` → `this` is `undefined` (strict) or `globalThis` (sloppy).
2. **Implicit**: `obj.fn()` → `this` is `obj`.
3. **Explicit**: `fn.call(ctx, ...)` / `fn.apply(ctx, [...])` / `fn.bind(ctx)`.
4. **`new`**: `new Foo()` → `this` is a fresh object whose `[[Prototype]]` is `Foo.prototype`.
5. **Arrow**: lexical — captures `this` from enclosing scope; cannot be rebound (`.call` ignored for `this`).

## Bridge: from theory to syntax

Each section of the cheat sheet below has a *chain implication* — what it does to the prototype graph or to `this` binding. As you read, mentally trace: "where does this end up on the chain?" or "what's `this` at the call site?"

## Syntax cheat sheet
```js
// Object literal — proto is Object.prototype
const o = { a: 1 };
Object.getPrototypeOf(o) === Object.prototype; // true

// Constructor function
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { return `${this.name} speaks`; };
const a = new Animal("dog");
a.speak();                            // "dog speaks"
a instanceof Animal;                  // true
Object.getPrototypeOf(a) === Animal.prototype; // true

// ES6 class
class Dog extends Animal {
  constructor(name) {
    super(name);
    this.kind = "dog";
  }
  bark() { return `${this.name} barks`; }
}

// Object.create — set prototype directly, no constructor
const proto = { greet() { return "hi"; } };
const x = Object.create(proto);

// __proto__ get/set (avoid setting at runtime — deopt)
Object.setPrototypeOf(o, proto);

// Method shorthand vs arrow as class field
class A {
  m() { return this; }          // on A.prototype, dynamic this
  arrow = () => this;           // own property, lexical this (= instance)
  static s() { return "static"; }
}

// call / apply / bind
function show(a, b) { return [this, a, b]; }
show.call({x:1}, 1, 2);          // [{x:1}, 1, 2]
show.apply({x:1}, [1, 2]);       // [{x:1}, 1, 2]
const bound = show.bind({x:1}, 1);
bound(2);                        // [{x:1}, 1, 2]

// Arrow ignores this binding
const arr = () => this;
arr.call({x:1});                 // this === enclosing scope

// hasOwnProperty (safer: Object.hasOwn)
Object.hasOwn(a, "name");        // true
"speak" in a;                    // true (chain)
a.hasOwnProperty("speak");       // false

// Object spread copies own enumerable; does NOT copy prototype
const clone = { ...a };          // proto = Object.prototype

// Static methods live on the class itself, not prototype
Dog.s;                           // undefined
Animal.s;                        // undefined (no static defined on Animal)

// Private fields (ES2022)
class Secret { #key = 42; reveal() { return this.#key; } }
```

## Bridge: edge cases reveal the *real* model

These traps almost always come up when an interviewer probes whether you *truly* understand the underlying machinery vs. just memorizing syntax. Each trap below reveals a piece of the model that's invisible until it bites you.

## Edge cases & interview traps
1. **`Function.prototype.bind` returns a new function whose `prototype` is undefined** — you can still `new` it (uses target's prototype chain).
2. **Arrow functions have no `prototype` property** — cannot be used with `new`.
3. **`class` declarations are NOT hoisted like functions** — TDZ.
4. **Class methods run in strict mode** even without `"use strict"`.
5. **`super` in a class method is bound to `[[HomeObject]]`**, not dynamically — moving the method to another object breaks `super`.
6. **`instanceof` checks the prototype chain**, not the constructor — can be fooled by `Object.setPrototypeOf` or `Symbol.hasInstance`.
7. **Setting `obj.__proto__ = something` is slow** and deopts V8 — prefer `Object.create` at construction.
8. **`this` in a callback passed to `setTimeout`/array methods loses binding** unless arrow or explicitly bound.
9. **Method extracted from object loses `this`**: `const f = obj.method; f()` → undefined this.
10. **Class fields (`x = 1`) are set in the constructor per instance**, after `super()` — they shadow prototype properties.
11. **`new`-invoking an arrow function throws TypeError** — "X is not a constructor".
12. **`Object.create(null)` makes a prototype-less object** — no `toString`, `hasOwnProperty`, etc. (great for dictionaries to avoid prototype pollution).
13. **Prototype pollution**: assigning to `Object.prototype` via `obj["__proto__"]["x"]` in user-controlled JSON parsing is a real CVE pattern. Use `Object.create(null)` or freeze.
14. **`Symbol.hasInstance`** can customize `instanceof`.
15. **`util.inherits` (Node)** sets the prototype chain but does NOT copy static members — use `extends` instead.
    ```js
    // util.inherits(Child, Parent); — Parent.staticFn won't appear on Child
    class Child extends Parent {} // copies statics + chain
    ```

## Bridge: from traps to live interview practice

In the worked examples below, every code snippet has an accompanying **chain diagram** so you can *see* exactly which slip points where. Practice tracing the chain in your head — it's the difference between "I think the answer is X" and "I know the answer is X because the chain goes A → B → C."

## Interview worked examples

### Example 1 — Predict `this` in 5 contexts
**Asked as:** "Walk me through what `this` is in each of these calls."

> **How to think aloud (interview storytelling):**
> "I apply the five rules in precedence order — `new` > explicit (`call`/`apply`/`bind`) > implicit (dot) > default (bare). Arrow functions are a separate category — they ignore all four rules and use lexical `this` from definition site. Strict mode matters for the default rule: undefined instead of globalThis."

I'd say: "Five rules govern `this`: default (undefined or globalThis), implicit (the dot), explicit (call/apply/bind), `new` (the freshly-created object), and arrow (lexical from definition site). Let me apply each."

```js
"use strict";
function show() { return this; }
const obj = { show, x: 1 };
const arrow = () => this; // lexical — captures module/global this

show();                  // undefined  (default, strict mode)
obj.show();              // obj        (implicit)
show.call({ y: 2 });     // {y:2}      (explicit)
new show();              // fresh {}   (new)
arrow();                 // global/module this (lexical, ignores caller)
```

> **Step-by-step walkthrough of each call:**
> 1. `show()` — bare function call, strict mode → `this` = `undefined`. Rule 1.
> 2. `obj.show()` — dot syntax → `this` = `obj`. Rule 2.
> 3. `show.call({y:2})` — explicit binding → `this` = `{y:2}`. Rule 3.
> 4. `new show()` — `new` creates a fresh object linked to `show.prototype` → `this` = that fresh object. Rule 4. Overrides any other rule.
> 5. `arrow()` — arrow function captures `this` lexically from where it was defined (the module scope). The `.call(...)` would NOT change it. Rule 5.

**What the interviewer is testing:** All five `this` binding rules and their precedence.
**Sharp follow-up they often ask:** "Which rule wins when you `new` a `bind`-ed function?" → `new` wins; bound `this` is ignored, but bound *args* are preserved.

### Example 2 — `instanceof` chain walk
**Asked as:** "Why does `arr instanceof Object` return true? Walk the chain."

> **How to think aloud:**
> "`instanceof` is not 'is left an instance of right'. It's literally: 'does `right.prototype` appear ANYWHERE on the left's prototype chain?' For an array, the chain is `arr → Array.prototype → Object.prototype → null`. Both `Array.prototype` and `Object.prototype` are on it, so both `arr instanceof Array` and `arr instanceof Object` are true."

I'd say: "`instanceof` checks if `Object.prototype` from the right-hand constructor appears anywhere on the left's prototype chain. An array's chain is `arr → Array.prototype → Object.prototype → null`, so both `Array` and `Object` succeed."

```js
const arr = [];
Object.getPrototypeOf(arr) === Array.prototype;            // true
Object.getPrototypeOf(Array.prototype) === Object.prototype; // true
arr instanceof Array;   // true
arr instanceof Object;  // true
```

> **Chain diagram for `arr`:**
> ```
> arr  ──[[Prototype]]──>  Array.prototype  ──[[Prototype]]──>  Object.prototype  ──>  null
> ```
> `instanceof Array` checks: is `Array.prototype` on the chain? **Yes** (one hop).
> `instanceof Object` checks: is `Object.prototype` on the chain? **Yes** (two hops).

**What the interviewer is testing:** Prototype chain walking; understanding `instanceof` semantics.
**Sharp follow-up they often ask:** "How would you spoof `instanceof`?" → Implement `Symbol.hasInstance` on the constructor.

### Example 3 — Augment `Array.prototype` with `last`
**Asked as:** "Add a `last()` method to all arrays. Then critique it."

> **How to think aloud:**
> "Adding to `Array.prototype` means every array — past, present, future — instantly gains the method via the chain. That's the power and the danger. Cons: name collisions if ECMAScript later proposes the same method (this actually happened with `Array.prototype.flatten` becoming `flat` to avoid breaking sites). Also leaks into `for...in` loops (which are bad on arrays anyway). Most teams ban built-in prototype extension entirely."

I'd say: "I add a function to `Array.prototype` — every array inherits it. But polluting built-in prototypes is risky: clashes with future spec methods (this exact one was proposed and conflicts arose), breaks `for...in`, and surprises consumers of your code."

```js
Array.prototype.last = function () { return this[this.length - 1]; };
[1, 2, 3].last(); // 3
// Risks: forbidden in some style guides; conflicts with ES proposals;
// shows up in for...in iteration of arrays.
```

> **Chain diagram after augmentation:**
> ```
> [1,2,3]  ──[[Prototype]]──>  Array.prototype  ──[[Prototype]]──>  Object.prototype  ──>  null
>                                  │
>                                  └── last() now lives here ← every array sees it
> ```

**What the interviewer is testing:** Prototype mutation power and its drawbacks.
**Sharp follow-up they often ask:** "Make it non-enumerable so `for...in` skips it." → `Object.defineProperty(Array.prototype, 'last', { value: fn, enumerable: false })`.

### Example 4 — Class-to-prototype desugar
**Asked as:** "Rewrite this ES6 class without using `class`."

> **How to think aloud:**
> "Class is sugar. The constructor body becomes a regular function. Methods defined with shorthand syntax become properties on `Ctor.prototype`. `extends` does two things: (1) `Object.setPrototypeOf(Child.prototype, Parent.prototype)` for instance method inheritance, and (2) `Object.setPrototypeOf(Child, Parent)` for static method inheritance. `super(...)` becomes a direct `Parent.call(this, ...)`."

I'd say: "Class is sugar: the constructor body becomes a regular function, methods land on `Function.prototype`, and `extends` is `Object.setPrototypeOf(Child.prototype, Parent.prototype)` plus a Parent call inside the child constructor."

```js
class Animal {
  constructor(name) { this.name = name; }
  speak() { return `${this.name} speaks`; }
}
// Desugared:
function Animal2(name) { this.name = name; }
Animal2.prototype.speak = function () { return `${this.name} speaks`; };

new Animal2("dog").speak(); // "dog speaks"
```

> **Chain diagram:**
> ```
> new Animal2("dog")  ──[[Prototype]]──>  Animal2.prototype  ──>  Object.prototype  ──>  null
>                                              │
>                                              └── speak() lives here
> ```

**What the interviewer is testing:** Confidence that class is purely syntactic.
**Sharp follow-up they often ask:** "Where does `class Dog extends Animal` differ from the function/prototype version?" → `super` and `extends` set both `Dog.__proto__ = Animal` (static inheritance) and `Dog.prototype.__proto__ = Animal.prototype`.

### Example 5 — Method extracted from object loses `this`
**Asked as:** "Predict the output."

> **How to think aloud:**
> "`this` is determined by the **call site**, not the definition. When I assign `obj.hi` to a free variable `f`, the function object itself is the same — but calling `f()` is now a bare call, not a method call. Bare call in strict mode → `this = undefined` → reading `.name` throws. This is the most common `this` bug in callbacks (`setTimeout(obj.method, 100)` has the same issue)."

I'd say: "When you assign `obj.method` to a free variable, the `this` binding is lost — calling it is now a 'default' call, which is undefined in strict mode. Fix with `bind`, an arrow wrapper, or call it as `obj.method()`."

```js
"use strict";
const user = { name: "Ada", hi() { return this.name; } };
const f = user.hi;
f();                      // TypeError: Cannot read property 'name' of undefined
user.hi.bind(user)();     // "Ada"  — fix
(() => user.hi())();      // "Ada"  — fix via arrow wrapper
```

> **Step-by-step walkthrough:**
> 1. `user.hi` — accessing the function object. Just a reference.
> 2. `const f = user.hi` — `f` holds the same function. No `this` is attached.
> 3. `f()` — bare call. Rule 1 (strict) → `this = undefined`.
> 4. `this.name` → reading `name` on `undefined` → TypeError.
> 5. Fix via `bind`: returns a new function with `this` permanently set to `user`. Calling it is fine.
> 6. Fix via arrow wrapper: arrow ignores its own `this`; inside, it calls `user.hi()` which IS a method call → `this = user`.

**What the interviewer is testing:** `this` is bound at call site, not definition site (for regular functions).
**Sharp follow-up they often ask:** "What if `hi` were defined as an arrow class field?" → It would always return the instance's name; arrow methods lock `this` to the instance.

### Example 6 — Method-chaining builder
**Asked as:** "Build a fluent QueryBuilder where `.where().select().limit()` chains."

> **How to think aloud:**
> "The whole 'fluent API' trick is one line: every method returns `this`. Each call returns the same builder instance, so you can keep dotting methods. The methods live on `Query.prototype` so all instances share them — efficient. Then `build()` is the terminal that returns the actual artifact."

I'd say: "Every method mutates internal state and `return this`. That's the entire trick — chainability falls out of returning the receiver. Methods live on the prototype, so all instances share them without per-instance allocation."

```js
class Query {
  constructor() { this.parts = { where: [], select: ["*"], limit: null }; }
  where(c)  { this.parts.where.push(c); return this; }
  select(f) { this.parts.select = f;     return this; }
  limit(n)  { this.parts.limit = n;      return this; }
  build()   { return this.parts; }
}
new Query().where("id=1").select(["id","name"]).limit(10).build();
```

> **Chain diagram + execution flow:**
> ```
> new Query()  ──[[Prototype]]──>  Query.prototype  ──>  Object.prototype  ──>  null
>                                       │
>                                       └── where, select, limit, build live here
>
> Call sequence:
>   q = new Query()                  → builder instance with parts state
>   q.where("id=1")  → returns q     → same instance, parts.where updated
>   q.select([...])  → returns q     → parts.select updated
>   q.limit(10)      → returns q     → parts.limit updated
>   q.build()        → returns parts → terminates the chain
> ```

**What the interviewer is testing:** Returning `this`; prototype methods vs per-instance fields.
**Sharp follow-up they often ask:** "Make it immutable so each call returns a new builder." → Spread state, construct new `Query`, set, return.

## Common machine-coding patterns
- **Implement `new` operator** — when used: classic interview. Sketch:
  ```js
  function myNew(Ctor, ...args) {
    const obj = Object.create(Ctor.prototype);
    const ret = Ctor.apply(obj, args);
    return (ret && typeof ret === "object") ? ret : obj;
  }
  ```
- **Implement `Object.create`** —
  ```js
  function myCreate(proto) {
    function F() {}
    F.prototype = proto;
    return new F();
  }
  ```
- **Implement `bind`** —
  ```js
  Function.prototype.myBind = function (ctx, ...bound) {
    const fn = this;
    return function (...args) {
      // handle `new`: if called as constructor, ignore ctx
      return fn.apply(new.target ? this : ctx, [...bound, ...args]);
    };
  };
  ```
- **Implement `instanceof`** —
  ```js
  function myInstanceof(obj, Ctor) {
    let p = Object.getPrototypeOf(obj);
    while (p) { if (p === Ctor.prototype) return true; p = Object.getPrototypeOf(p); }
    return false;
  }
  ```
- **Inheritance without classes (pre-ES6)** — `Child.prototype = Object.create(Parent.prototype); Child.prototype.constructor = Child;`.

## Backend-specific notes
Node's `EventEmitter`, `stream.Readable`, `http.IncomingMessage` all use prototype-based inheritance. When extending them, prefer `class X extends EventEmitter` over `util.inherits` — cleaner, supports `super()`. Be careful: methods you add via class fields (`handler = () => {}`) become per-instance and break shared-shape optimization; for high-throughput servers (e.g. 50k req/s), define methods on the prototype.

For request-scoped data, avoid stuffing it on `this` in long-lived service objects. The service is one instance; many requests run concurrently. Use `AsyncLocalStorage` instead.

Prototype pollution: when parsing user JSON into a config or merging into an existing object (`_.merge`), validate keys or use `Object.create(null)` to avoid `__proto__` overwrites — a 2018 CVE class.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ PROTOTYPE & THIS — DAY-BEFORE CRAM                       │
├──────────────────────────────────────────────────────────┤
│ • Every obj has [[Prototype]] → lookup chain ends at null│
│ • fn.prototype = the proto of `new fn()` instances       │
│ • class = sugar; methods → prototype, fields → instance  │
│ • this rules: default, implicit, explicit, new, arrow    │
│ • arrow has NO this/arguments/prototype; can't `new`     │
│ • bind returns new fn; `new` overrides bound this        │
│ • instanceof walks proto chain                           │
│ • Object.create(null) → no proto; safe dict              │
│ • Class methods auto strict; super uses [[HomeObject]]   │
│ • V8 hidden classes: init all fields in constructor      │
│ • Method extracted from obj loses this binding           │
│ • Prototype pollution: validate keys / null-proto objs   │
│ • myNew, myBind, myInstanceof — write under 5 lines      │
│ • extends > util.inherits in modern Node                 │
└──────────────────────────────────────────────────────────┘
```
