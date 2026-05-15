# Prototype, `this`, and Inheritance

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
JS inheritance is **delegation**: when you read `obj.x`, the engine checks `obj`, then `Object.getPrototypeOf(obj)`, then *its* prototype, until `null`. Writing always goes on `obj` itself (unless setter on the chain).

```
literal {}    --> Object.prototype --> null
[]            --> Array.prototype  --> Object.prototype --> null
function(){}  --> Function.prototype --> Object.prototype --> null
new Foo()     --> Foo.prototype    --> Object.prototype --> null
```

V8 uses **hidden classes** (a.k.a. shapes) to optimize property access. Objects with the same property layout share a hidden class, enabling inline caches that turn `obj.x` into a single offset load. Adding/removing properties changes the shape and invalidates the IC — *don't* dynamically add fields in hot code; initialize in the constructor.

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
1. **Default**: bare call `fn()` → `this` is `undefined` (strict) or `globalThis` (sloppy).
2. **Implicit**: `obj.fn()` → `this` is `obj`.
3. **Explicit**: `fn.call(ctx, ...)` / `fn.apply(ctx, [...])` / `fn.bind(ctx)`.
4. **`new`**: `new Foo()` → `this` is a fresh object whose `[[Prototype]]` is `Foo.prototype`.
5. **Arrow**: lexical — captures `this` from enclosing scope; cannot be rebound (`.call` ignored for `this`).

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

## Interview worked examples

### Example 1 — Predict `this` in 5 contexts
**Asked as:** "Walk me through what `this` is in each of these calls."

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

**What the interviewer is testing:** All five `this` binding rules and their precedence.
**Sharp follow-up they often ask:** "Which rule wins when you `new` a `bind`-ed function?" → `new` wins; bound `this` is ignored, but bound *args* are preserved.

### Example 2 — `instanceof` chain walk
**Asked as:** "Why does `arr instanceof Object` return true? Walk the chain."

I'd say: "`instanceof` checks if `Object.prototype` from the right-hand constructor appears anywhere on the left's prototype chain. An array's chain is `arr → Array.prototype → Object.prototype → null`, so both `Array` and `Object` succeed."

```js
const arr = [];
Object.getPrototypeOf(arr) === Array.prototype;            // true
Object.getPrototypeOf(Array.prototype) === Object.prototype; // true
arr instanceof Array;   // true
arr instanceof Object;  // true
```

**What the interviewer is testing:** Prototype chain walking; understanding `instanceof` semantics.
**Sharp follow-up they often ask:** "How would you spoof `instanceof`?" → Implement `Symbol.hasInstance` on the constructor.

### Example 3 — Augment `Array.prototype` with `last`
**Asked as:** "Add a `last()` method to all arrays. Then critique it."

I'd say: "I add a function to `Array.prototype` — every array inherits it. But polluting built-in prototypes is risky: clashes with future spec methods (this exact one was proposed and conflicts arose), breaks `for...in`, and surprises consumers of your code."

```js
Array.prototype.last = function () { return this[this.length - 1]; };
[1, 2, 3].last(); // 3
// Risks: forbidden in some style guides; conflicts with ES proposals;
// shows up in for...in iteration of arrays.
```

**What the interviewer is testing:** Prototype mutation power and its drawbacks.
**Sharp follow-up they often ask:** "Make it non-enumerable so `for...in` skips it." → `Object.defineProperty(Array.prototype, 'last', { value: fn, enumerable: false })`.

### Example 4 — Class-to-prototype desugar
**Asked as:** "Rewrite this ES6 class without using `class`."

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

**What the interviewer is testing:** Confidence that class is purely syntactic.
**Sharp follow-up they often ask:** "Where does `class Dog extends Animal` differ from the function/prototype version?" → `super` and `extends` set both `Dog.__proto__ = Animal` (static inheritance) and `Dog.prototype.__proto__ = Animal.prototype`.

### Example 5 — Method extracted from object loses `this`
**Asked as:** "Predict the output."

I'd say: "When you assign `obj.method` to a free variable, the `this` binding is lost — calling it is now a 'default' call, which is undefined in strict mode. Fix with `bind`, an arrow wrapper, or call it as `obj.method()`."

```js
"use strict";
const user = { name: "Ada", hi() { return this.name; } };
const f = user.hi;
f();                      // TypeError: Cannot read property 'name' of undefined
user.hi.bind(user)();     // "Ada"  — fix
(() => user.hi())();      // "Ada"  — fix via arrow wrapper
```

**What the interviewer is testing:** `this` is bound at call site, not definition site (for regular functions).
**Sharp follow-up they often ask:** "What if `hi` were defined as an arrow class field?" → It would always return the instance's name; arrow methods lock `this` to the instance.

### Example 6 — Method-chaining builder
**Asked as:** "Build a fluent QueryBuilder where `.where().select().limit()` chains."

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
