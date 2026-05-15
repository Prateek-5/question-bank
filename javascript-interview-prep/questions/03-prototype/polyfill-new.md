# Polyfill the `new` Operator (`myNew`)

## Source
- Canonical machine-coding interview problem — asked at Atlassian, Razorpay, Microsoft, Uber.
- Reference spec: https://tc39.es/ecma262/#sec-new-operator

## Why this question matters in interviews
`myNew` is the **definitive prototype-chain interview question**. In ~10 lines you have to demonstrate (1) what `new` actually *does* under the hood, (2) `Object.create(Ctor.prototype)` to wire the prototype chain, (3) `Ctor.apply(obj, args)` to seed instance state, (4) the subtle "if constructor returned an object, use that instead" rule, and (5) familiarity with how `class`, `extends`, and `super` desugar into these mechanics. As a senior backend engineer, you'll use these same building blocks every time you write a factory, DI container, or ORM that hand-constructs instances. A candidate who answers this without referring to `Object.create` and the return-value rule is junior.

## Concepts involved

### What `new Ctor(...args)` does (the 4-step spec, abridged)
1. Create a brand-new empty object `obj`.
2. Set `Object.getPrototypeOf(obj) = Ctor.prototype`. (So `obj instanceof Ctor` becomes true.)
3. Call `Ctor.apply(obj, args)` — run the constructor body with `this = obj`. Any `this.x = ...` assignments now stick to `obj`.
4. If the constructor *explicitly returned an object* (or function), return THAT. Otherwise return `obj`.

That's it. `new` is literally those four steps. Nothing magical.

### Syntax to lock in
```js
function myNew(Ctor, ...args) {
  if (typeof Ctor !== 'function') throw new TypeError('Ctor must be a function');
  const obj = Object.create(Ctor.prototype);          // steps 1 + 2
  const result = Ctor.apply(obj, args);                // step 3
  return (result !== null && (typeof result === 'object' || typeof result === 'function'))
    ? result                                           // step 4: object/function override
    : obj;
}
```

### Runtime / engine behavior
- `Object.create(proto)` makes a new object with `proto` as its prototype, **without** invoking any constructor. Perfect for step 1+2 because we want to attach the chain *before* the constructor runs (so any `this instanceof Ctor` check inside the constructor returns `true`).
- `Ctor.apply(obj, args)` runs the function body with `this = obj`. Strict-mode constructors that assign `this.x = ...` populate `obj`.
- The "return value override" exists so you can implement factories that return a different object (e.g. singletons, frozen instances, proxies). Native `new` honors it; the polyfill must too.
- **Primitive returns are ignored** — `return 42;` from inside a constructor is dropped; `obj` is returned. `null` is dropped too (because `typeof null === 'object'` but the spec explicitly excludes it).

### Edge cases (interview traps)
1. **Constructor returns an object → that object wins.** The classic "what does `new Foo()` return?" trap. `function F(){ this.x=1; return {y:2}; }; new F()` is `{y:2}`, NOT `{x:1}`.
2. **Constructor returns a function → also wins** (functions are objects). Rare but spec-compliant.
3. **Constructor returns `null` → ignored**, `obj` is returned. `null` is a "non-object" for this purpose.
4. **Constructor returns a primitive → ignored.** `return 42` ⇒ `obj` returned.
5. **Arrow function as Ctor → throws** `TypeError: X is not a constructor`. Arrows lack `[[Construct]]`. Your polyfill should reject (`Ctor.prototype === undefined` for arrows).
6. **`class` constructors require `new`** — calling `MyClass()` without `new` throws. Your polyfill calls them with `apply`, which native engines treat as "not a `new` call" and throw. **Limitation worth mentioning.** Real implementation needs `Reflect.construct(Ctor, args)` for class support.
7. **`Reflect.construct(Ctor, args, NewTarget)`** is the only way to fully replicate `new`, including subclass scenarios where `new.target` matters. Mention it.
8. **`new.target`** inside the constructor is `Ctor` when called via `new`. Your `apply` polyfill leaves `new.target === undefined`. Caveat to flag.

## Brute force approach
"I'll just `return new Ctor(...args)`." That's not a polyfill — it's the operator you're trying to define. If the interviewer allows it (some do, jokingly), point out it doesn't teach anything.

A second wrong path: `Object.create(Ctor)` instead of `Object.create(Ctor.prototype)`. That would make the new object's prototype the *constructor function* itself, not `Ctor.prototype`. Method lookup then walks into `Function.prototype` and fails to find instance methods.

## Optimal approach
Four lines mapping directly to the four spec steps. Use `Object.create(Ctor.prototype)` to wire the prototype before running the constructor body; use `apply` to bind `this`; check the constructor's return for object/function and honor it. For production-grade `class` support, swap `apply` for `Reflect.construct`.

## Solution (JavaScript)

```js
/**
 * Polyfill the `new` operator.
 *
 *   myNew(Ctor, ...args)  ≡  new Ctor(...args)
 *
 * Steps (matching the ECMAScript [[Construct]] internal method):
 *   1. Create a fresh object whose prototype is Ctor.prototype.
 *   2. Invoke Ctor with `this = obj`, passing args.
 *   3. If Ctor explicitly returned an object/function, return THAT.
 *   4. Otherwise return obj.
 */
function myNew(Ctor, ...args) {
  if (typeof Ctor !== 'function' || !Ctor.prototype) {
    // Arrow functions have no .prototype and aren't constructors.
    throw new TypeError(`${Ctor?.name || 'value'} is not a constructor`);
  }

  // Steps 1 + 2: fresh object whose prototype chain starts at Ctor.prototype.
  const obj = Object.create(Ctor.prototype);

  // Step 3: run the constructor with our new object as `this`.
  const result = Ctor.apply(obj, args);

  // Step 4: constructor override rule.
  // If the function explicitly returned an OBJECT (incl. function),
  // that becomes the value of `new Ctor(...)`. Otherwise obj wins.
  const overrode = result !== null && (typeof result === 'object' || typeof result === 'function');
  return overrode ? result : obj;
}

/* ── Class-compatible version (bonus): handles `class` and `new.target` ──
   Use this in production code; engines treat plain `apply` on a class
   constructor as "not invoked with new" and throw.                       */
function myNewSpecCompliant(Ctor, ...args) {
  return Reflect.construct(Ctor, args);
}
```

## Step-by-step dry run

### Case 1 — normal constructor
```js
function Person(first, last) {
  this.first = first;
  this.last = last;
}
Person.prototype.full = function () { return `${this.first} ${this.last}`; };

const p = myNew(Person, 'Ada', 'Lovelace');
```
1. `Ctor = Person`, `args = ['Ada', 'Lovelace']`. Validation passes — `Person` is a function with a `.prototype`.
2. `obj = Object.create(Person.prototype)` → a fresh object `{}` whose internal `[[Prototype]]` points to `Person.prototype`.
3. `Person.apply(obj, ['Ada', 'Lovelace'])` runs the body with `this = obj`:
   - `obj.first = 'Ada'`
   - `obj.last = 'Lovelace'`
   - Returns `undefined`.
4. `result === undefined` → not an object → return `obj`.
5. `p` is `{first:'Ada', last:'Lovelace'}` with `Person.prototype` as its proto. `p.full()` walks the chain → `'Ada Lovelace'`. `p instanceof Person` → `true`.

### Case 2 — constructor returns an object (override rule)
```js
function Singleton() {
  this.greet = 'hi';
  return { iAmTheSingleton: true };
}
const s = myNew(Singleton);
```
1. `obj = Object.create(Singleton.prototype)`.
2. `Singleton.apply(obj)` runs, sets `obj.greet = 'hi'`, returns `{iAmTheSingleton:true}`.
3. `result` is a non-null object → override rule kicks in → return `{iAmTheSingleton:true}`.
4. The `obj` we created (with `greet:'hi'`) is **garbage-collected**; `s.greet` is `undefined`. The returned object also does NOT have `Singleton.prototype` on its chain → `s instanceof Singleton === false`.

This is the entire reason factories like `Map`, `Promise`, and many singletons can short-circuit `new`.

### Case 3 — constructor returns a primitive (ignored)
```js
function Weird() { this.x = 1; return 42; }
const w = myNew(Weird);
```
1. `obj` created with `Weird.prototype`.
2. Body sets `obj.x = 1`, returns `42`.
3. `typeof 42 === 'number'` → not object/function → override rule does NOT fire.
4. Return `obj` ⇒ `w.x === 1`, `w instanceof Weird` true.

### Case 4 — arrow function (rejected)
```js
const Arrow = () => {};
myNew(Arrow);     // throws TypeError: Arrow is not a constructor
```
Validation guard caught it because `Arrow.prototype === undefined`.

## Important takeaways

**Syntax to memorize**
- The four-step skeleton: `Object.create(Ctor.prototype)` → `Ctor.apply(obj, args)` → check return type → return override or obj.
- `result !== null && (typeof result === 'object' || typeof result === 'function')` — the exact "is it an object?" check the spec uses.
- `Reflect.construct(Ctor, args)` — the modern, class-safe equivalent.

**Patterns to reuse**
- Factories, DI containers, ORMs, IoC frameworks all need to construct instances dynamically. They all use either `new Ctor(...args)`, `Reflect.construct`, or the polyfill above.
- The "return an object to override" rule is what makes immutable factories work (e.g. `class Point { constructor(){ return Object.freeze(this); } }`).

**Common mistakes**
- `Object.create(Ctor)` instead of `Object.create(Ctor.prototype)`. Now the chain points at the function, not the prototype object. Methods don't resolve.
- Returning `obj` unconditionally — misses the override rule.
- Forgetting the primitive/null filter in the override check — returning `null` is ignored by spec; you'd return `null` instead.
- Using `new Ctor(...args)` inside the polyfill. Recursive and defeats the point.
- Trying to polyfill `class` constructors with `apply` — throws "Class constructor cannot be invoked without 'new'". Use `Reflect.construct` for those.

**Why interviewers ask this**
- It is the *most efficient* way to test the prototype chain, constructor semantics, and a non-obvious return-value rule in one short problem.

## Variants

1. **Subclass-aware `new`** — `Reflect.construct(Ctor, args, NewTarget)` where `NewTarget` controls which `prototype` is used. Required for correct subclass instantiation. Mention `new.target`.
2. **`class`-compatible `myNew`** — replace `Ctor.apply(obj, args)` with `Reflect.construct(Ctor, args)`. Show you know the limitation.
3. **`Object.create` polyfill** — `function fakeCreate(p){ function F(){}; F.prototype=p; return new F(); }`. The original Crockford pattern.
4. **Implement `instanceof`** — companion problem. Walk `Object.getPrototypeOf(obj)` until you hit `Ctor.prototype` or `null`.
5. **Why does `new Date()` return a `Date` object but `Date()` returns a string?** Because `Date` checks `new.target`. Demonstrates `new.target`'s role.

## Revision notes

> **myNew — 60 second recap**
> - Four spec steps: (1) make obj, (2) wire `obj.__proto__ = Ctor.prototype` via `Object.create(Ctor.prototype)`, (3) call `Ctor.apply(obj, args)`, (4) if return value is an object/function use it, else return obj.
> - `Object.create(Ctor.prototype)` — NOT `Object.create(Ctor)`. Common slip.
> - Return-value override: only fires for non-null **objects or functions**. `null`/primitives are ignored.
> - Arrow functions have no `.prototype` → not constructable. Validate up front.
> - `class` constructors throw under `apply` ("must be invoked with new"). Use `Reflect.construct(Ctor, args)` for class support.
> - `Reflect.construct(Ctor, args, NewTarget)` is the full-spec way; supports subclass `new.target`.
> - After `new`, `obj instanceof Ctor` is true because step 2 wired the chain.
> - This is the foundation of *every* factory, DI container, and ORM in JS.
> - **Trap:** returning `obj` unconditionally — breaks the singleton/factory override rule.
> - **Trap:** `Object.create(Ctor)` — wrong target; instance methods stop resolving.
