# Implement `Function.prototype.bind` (polyfill)

## Source
- Canonical machine-coding interview problem (BFE.dev, Frontend Masters, MDN reference implementation).
- Reference: ECMA-262 §20.2.3.2 (Function.prototype.bind).

## Why this question matters in interviews
Polyfilling `bind` is the **classic prototype-chain interview problem**. It looks like "easy, just `fn.apply(thisArg, ...args)` inside a wrapper" — but the *real* test is a single follow-up: **"What happens if I do `new (foo.bind(obj))()`?"** A correct answer must detect when the bound function is invoked as a constructor (`new`) and **ignore** the bound `this`, using the new instance as `this` instead. This catches 80% of candidates. The senior version also handles partial application (curried args), preserves the prototype chain, and uses `new.target` correctly. Backend interviewers especially love this question because Node code is full of `bind` usage — callback wiring, event handlers, class methods passed to async libraries — and getting it wrong leaks `this`-binding bugs everywhere.

## Concepts involved

### Syntax to lock in
```js
Function.prototype.myBind = function (thisArg, ...boundArgs) {
  const targetFn = this;
  function Bound(...callArgs) {
    // If invoked with `new`, `this` is the new instance — ignore thisArg.
    const ctx = new.target ? this : thisArg;
    return targetFn.apply(ctx, [...boundArgs, ...callArgs]);
  }
  // Preserve prototype chain so `new Bound()` produces an instance of targetFn.
  if (targetFn.prototype) {
    Bound.prototype = Object.create(targetFn.prototype);
  }
  return Bound;
};
```

### Runtime / engine behavior
- `new.target` is `undefined` when the function is called normally, and a reference to the **constructor** when invoked with `new`. It's the cleanest way to detect constructor calls inside a polyfill.
- Native `Function.prototype.bind` returns an **exotic** function object whose `[[Prototype]]` is the original `fn.prototype`. Polyfills can't exactly replicate this — best we can do is set `Bound.prototype = Object.create(targetFn.prototype)` so `instanceof` works.
- Partial application: native bind freezes the leading args. Calling the bound function appends more args on top. Order: `[...boundArgs, ...callArgs]`.
- `arrow functions` cannot be bound. `arrow.bind(x)` ignores `x` because arrows have lexical `this`. The polyfill above silently does the same because `targetFn.apply(ctx, ...)` on an arrow ignores `ctx`. Mention this — it's a senior nuance.

### Edge cases (these are the interview traps)
1. **`new` on a bound function** — `const Bound = Foo.bind(ctx); new Bound()`. `this` must be the new instance, **not** `ctx`. Use `new.target`. This is THE test interviewers care about.
2. **`instanceof Foo`** — `new Bound() instanceof Foo` must be `true`. Requires `Bound.prototype = Object.create(Foo.prototype)`.
3. **Partial application order** — `fn.bind(ctx, 1, 2)(3, 4)` → `fn.call(ctx, 1, 2, 3, 4)`. Bound args go first.
4. **`bind`ing already-bound functions** — `fn.bind(a).bind(b)` — `b` is ignored; the first bind wins. Native behavior; polyfill above replicates because the inner `Bound` uses the captured `thisArg`, ignoring later attempts.
5. **`bind` on arrow functions** — `thisArg` is ignored; arrow `this` is lexical. Polyfill above silently no-ops correctly.
6. **`bind` on `class` methods extracted from instance** — `const f = obj.method; f()` loses `this`. `const bf = obj.method.bind(obj); bf()` retains it. Classic Node callback wiring.
7. **Length and name properties** — native bind produces a function with `.name === 'bound ' + fn.name` and `.length === Math.max(0, fn.length - boundArgs.length)`. Polish for senior cred; not strictly required.
8. **`function.bind(null)` in strict vs sloppy** — in strict mode, `this` is `null` inside `fn`. In sloppy, `this` becomes `globalThis`. Don't try to override native semantics.

## Brute force approach
Naive: `return function (...callArgs) { return fn.apply(thisArg, [...boundArgs, ...callArgs]); }`. Works for normal calls but **fails the `new` test**: `new (fn.bind(ctx))()` calls `fn.apply(ctx, ...)`, which means `this` inside `fn` becomes `ctx`, NOT a new instance. Interviewer pounces. Always include `new.target` handling from the start.

## Optimal approach
- Capture `targetFn = this` (the function bind is being called on).
- Return a `Bound` function that:
  - Checks `new.target`; if truthy, uses `this` (the freshly constructed instance); else uses `thisArg`.
  - Calls `targetFn.apply(ctx, [...boundArgs, ...callArgs])`.
- Set `Bound.prototype = Object.create(targetFn.prototype)` for `instanceof` correctness.

## Solution (JavaScript)

```js
/**
 * Polyfill of Function.prototype.bind.
 * - Sets `this` to thisArg for normal calls.
 * - Sets `this` to the new instance for `new`-style calls (ignoring thisArg).
 * - Partial-applies boundArgs ahead of callArgs.
 * - Preserves prototype chain so `instanceof` works.
 */
Function.prototype.myBind = function (thisArg, ...boundArgs) {
  if (typeof this !== 'function') {
    throw new TypeError('myBind must be called on a function');
  }
  const targetFn = this;

  function Bound(...callArgs) {
    // `new.target` is truthy when invoked via `new Bound(...)`.
    const ctx = new.target ? this : thisArg;
    return targetFn.apply(ctx, [...boundArgs, ...callArgs]);
  }

  // Preserve prototype chain so `new Bound() instanceof targetFn`.
  if (targetFn.prototype) {
    Bound.prototype = Object.create(targetFn.prototype);
  }

  // Polish: name + length to match native bind output (optional).
  Object.defineProperty(Bound, 'name', {
    value: `bound ${targetFn.name || ''}`,
    configurable: true,
  });
  Object.defineProperty(Bound, 'length', {
    value: Math.max(0, (targetFn.length || 0) - boundArgs.length),
    configurable: true,
  });

  return Bound;
};
```

## Step-by-step dry run

Input:
```js
function Greeter(greeting, name) {
  this.greeting = greeting;
  this.name = name;
}
Greeter.prototype.say = function () {
  return `${this.greeting}, ${this.name}!`;
};

const ctx = { tag: 'wrongCtx' };
const BoundGreeter = Greeter.myBind(ctx, 'Hello');

// Test 1: normal call — should set props on ctx (because no `new`).
BoundGreeter('Prateek');
console.log(ctx.greeting, ctx.name);   // 'Hello' 'Prateek'

// Test 2: `new` call — should IGNORE ctx, create fresh instance.
const g = new BoundGreeter('Prateek');
console.log(g.greeting, g.name);       // 'Hello' 'Prateek'
console.log(g instanceof Greeter);     // true
console.log(g.say());                  // 'Hello, Prateek!'
console.log(ctx.greeting);             // still 'Hello' from Test 1, NOT overwritten
```

Trace Test 1 (normal call):
- `BoundGreeter('Prateek')` invokes `Bound`. `new.target` is `undefined`.
- `ctx = thisArg = { tag: 'wrongCtx' }`.
- `targetFn.apply(ctx, ['Hello', 'Prateek'])` → `Greeter.call({tag:'wrongCtx'}, 'Hello', 'Prateek')`.
- Inside Greeter: `this = ctx`. Assigns `ctx.greeting = 'Hello'`, `ctx.name = 'Prateek'`. Mutates ctx (yikes, but that's what bind does).

Trace Test 2 (`new` call):
- `new BoundGreeter('Prateek')`. JS creates a fresh object whose `[[Prototype]]` is `Bound.prototype` (which is `Object.create(Greeter.prototype)`).
- Inside `Bound`: `new.target` is `Bound` (truthy). So `ctx = this` (the fresh object).
- `targetFn.apply(this, ['Hello', 'Prateek'])` → `Greeter.call(freshObj, 'Hello', 'Prateek')`.
- Inside Greeter: `this = freshObj`. Assigns `freshObj.greeting`, `freshObj.name`.
- `Bound` returns whatever Greeter returns (`undefined`), so `new` uses `freshObj` as the result.
- `g instanceof Greeter` — walks `g`'s prototype chain: `g.[[Proto]] === Bound.prototype === Object.create(Greeter.prototype)`, whose `[[Proto]] === Greeter.prototype`. Match. `true`.
- `g.say()` — finds `say` on Greeter.prototype via the chain. Works.

This is the dry run interviewers want to hear walked through — specifically that **`new.target` flips the `this` source** and **`Object.create(targetFn.prototype)` makes `instanceof` work**.

## Important takeaways

**Syntax to memorize**
- `const targetFn = this;` — capture the function bind is being called on.
- `const ctx = new.target ? this : thisArg;` — the magic line.
- `Bound.prototype = Object.create(targetFn.prototype);` — instanceof support.
- `targetFn.apply(ctx, [...boundArgs, ...callArgs]);` — partial application order.

**Patterns to reuse**
- `new.target` detection: same trick used to enforce "must call with `new`" (`if (!new.target) throw ...`) or polyfill `Reflect.construct`. Senior-level JS knowledge.
- `Object.create(parent.prototype)` is THE way to set up prototypal inheritance without invoking the parent constructor. Used in ES5 inheritance idioms before `class`.
- Closures-over-captured-args is the same pattern as `partial`, `curry`, `memoize` — bind is just a specialized partial that also captures `this`.

**Common mistakes**
- Forgetting `new.target` → bound constructors send `this` to the wrong object on `new`.
- Skipping `Object.create(targetFn.prototype)` → `instanceof` fails.
- Using `targetFn.bind` recursively → infinite loop in your polyfill.
- Forgetting to capture `this` outside the inner function — `this` inside `function Bound()` is different from the outer `this`.
- Using an arrow function for `Bound` → arrow has no `new.target`, so constructor invocations break.

**Related questions**
- Polyfill `call` and `apply` — simpler; uses a symbol-property trick to set `this` temporarily.
- Polyfill the `new` operator — `myNew(Ctor, ...args)` = `Object.create(Ctor.prototype)` + `Ctor.apply(obj, args)` + return-handling.
- `Reflect.construct(target, args, newTarget)` — modern equivalent of bind+new.

## Variants

1. **Polyfill `call`** — `Function.prototype.myCall = function(thisArg, ...args) { const sym = Symbol(); thisArg[sym] = this; const result = thisArg[sym](...args); delete thisArg[sym]; return result; }`. Be ready.

2. **Polyfill `apply`** — same as `call` but takes an array. One-line difference.

3. **Polyfill `new`** — `function myNew(Ctor, ...args) { const obj = Object.create(Ctor.prototype); const res = Ctor.apply(obj, args); return (typeof res === 'object' && res !== null) ? res : obj; }`. The `return` handling is the gotcha — constructors that return an object override the new instance.

4. **`bind` chain immutability** — once bound, the `this` can't be changed even by `call`/`apply`. Polyfill above naturally has this property because the inner `Bound` always uses captured `thisArg`.

5. **Strict / sloppy mode differences** — `bind(null)` in strict gives `this === null` inside fn; in sloppy it becomes `globalThis`. Out of scope for the polyfill (engine handles it).

## Revision notes

> **bind polyfill — 60 second recap**
> - `Function.prototype.myBind = function(thisArg, ...boundArgs) { ... }`
> - Inner `Bound`: `const ctx = new.target ? this : thisArg;`
> - `Bound.prototype = Object.create(targetFn.prototype)` for `instanceof`.
> - Partial app: `[...boundArgs, ...callArgs]`.
> - **THE test:** `new (foo.bind(ctx))()` — `this` must be the new instance, NOT ctx. `new.target` detects.
> - Sibling polyfills: `call` (symbol trick), `apply` (array variant), `new` (Object.create + apply + return handling).
> - **Trap:** arrow for `Bound` — no `new.target`, breaks constructor calls.
