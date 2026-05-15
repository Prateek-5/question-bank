# Polyfill `Function.prototype.bind`

## Source
- Canonical machine-coding interview problem — asked at Razorpay, Atlassian, PhonePe, Meta, Amazon.
- Reference spec: https://tc39.es/ecma262/#sec-function.prototype.bind

## Why this question matters in interviews
`myBind` is the **single most-asked polyfill in JS interviews**, period. It is the meeting point of every fundamental: `this` binding (rule 3), partial application (closures), `new` semantics (rule 4 — and how it must *override* the bound `this`), prototype chain (the bound function's `prototype` must let `new` produce the right instance), and rest/spread. Senior backend engineers are expected to write the full production-grade version in ~20 lines, *including the `new` handling*. A candidate who only writes the 4-line "happy path" version signals junior-level depth.

## Concepts involved

### Spec contract of `bind`
```js
const bound = fn.bind(thisArg, ...presetArgs);
bound(...laterArgs);          // === fn.call(thisArg, ...presetArgs, ...laterArgs)
new bound(...laterArgs);      // creates an instance of fn — thisArg is IGNORED;
                              //   args are still concatenated.
bound.name === 'bound ' + fn.name;
bound.prototype === undefined; // bound functions do NOT have their own `prototype`
```

### Syntax to lock in
```js
Function.prototype.myBind = function (ctx, ...preset) {
  const fn = this;                  // the original function
  function bound(...later) {
    const calledAsNew = this instanceof bound;
    // If called with `new`, ignore `ctx`; the `new` machinery already gave
    // us a fresh `this` whose prototype is bound.prototype === fn.prototype.
    return fn.apply(calledAsNew ? this : ctx, [...preset, ...later]);
  }
  // So `new bound()` produces an instance of `fn`.
  if (fn.prototype) bound.prototype = Object.create(fn.prototype);
  return bound;
};
```

### Runtime / engine behavior
- `bind` returns an **exotic** function object whose `[[BoundTargetFunction]]`, `[[BoundThis]]`, `[[BoundArguments]]` are baked in.
- Native `bind` makes the result have **no `prototype` property** of its own; instead, `new boundFn` walks the chain to `fn.prototype` (the engine does this via `[[Construct]]`). We can't replicate exotic objects from JS, so in a polyfill we *give* the returned function a prototype that *chains to* `fn.prototype` — which is the next best thing.
- `new bound(...)` triggers `[[Construct]]`. The newly created object's prototype is `bound.prototype`. Because we set `bound.prototype = Object.create(fn.prototype)`, the new instance is `instanceof fn` ✓.
- The spec also says: bound functions don't have `arguments` / `caller` (poison pills). Real interview rounds rarely test this.

### Edge cases (interview traps)
1. **`new boundFn()` must IGNORE the bound `this`.** This is the #1 trap. Detect via `this instanceof bound` inside the wrapper.
2. **Partial application must concatenate**, not replace: `[...preset, ...later]`.
3. **Calling `myBind` on a non-function** should throw `TypeError`. Native does.
4. **Arrow functions** — calling `bind` on an arrow does nothing to its `this` (rule 5). Your polyfill will mirror this if `fn` is an arrow because `apply` is also a no-op on arrows for `this`. Mention it.
5. **`bound.prototype === undefined` in native** vs your polyfill exposes a `prototype`. Real-world impact: `Object.getPrototypeOf(new bound())` chains correctly either way. Most interviewers accept the close-enough form.
6. **Chained binds** — `fn.bind(A).bind(B)` → `this === A`. Your polyfill should naturally preserve this because the second bind wraps the first, which already has `ctx = A` baked in, and the new `apply(B, ...)` is overridden internally.
7. **Length** — native `bound.length === Math.max(0, fn.length - preset.length)`. Skip unless asked.
8. **`name`** — native sets `name = 'bound ' + fn.name`. One-liner addition if asked.

## Brute force approach
The naive 4-line version:
```js
Function.prototype.myBind = function (ctx, ...preset) {
  const fn = this;
  return (...later) => fn.apply(ctx, [...preset, ...later]);
};
```
Works for `bound()` calls. Breaks for `new bound()` — arrows can't be constructed, and even with a `function` wrapper, the `new` machinery cannot override `ctx`. This is the version juniors stop at; you must go further.

## Optimal approach
A `function` wrapper (not arrow — we need our own `this`), plus `this instanceof wrapper` to detect construction. Chain `wrapper.prototype` to `fn.prototype` so `new bound()` produces an instance that satisfies `instanceof fn`. One closure over `(fn, ctx, preset)`. O(1) per call.

## Solution (JavaScript)

```js
/**
 * Production-grade Function.prototype.bind polyfill.
 *
 * Contract:
 *   const bound = fn.myBind(ctx, ...preset);
 *   bound(...later)        ≡  fn.call(ctx, ...preset, ...later)
 *   new bound(...later)    ≡  new fn(...preset, ...later)   // ctx IGNORED
 *   new bound() instanceof fn   →  true
 */
Function.prototype.myBind = function (ctx, ...preset) {
  if (typeof this !== 'function') {
    throw new TypeError('myBind must be called on a function');
  }
  const fn = this;

  function bound(...later) {
    // RULE 4 precedence: when invoked with `new`, the `new` machinery
    // already created a fresh `this` whose prototype is `bound.prototype`.
    // We must honor that, NOT the bound ctx.
    const calledAsNew = this instanceof bound;
    return fn.apply(calledAsNew ? this : ctx, [...preset, ...later]);
  }

  // Wire `new bound()` so that instance.__proto__ chains to fn.prototype.
  // (Arrow functions have no .prototype; skip the wiring for them — they
  //  can't be constructed anyway, so `new bound()` would throw downstream.)
  if (fn.prototype) {
    bound.prototype = Object.create(fn.prototype);
  }

  // Optional cosmetic touches that mirror the spec:
  Object.defineProperty(bound, 'name', { value: 'bound ' + (fn.name || ''), configurable: true });

  return bound;
};
```

## Step-by-step dry run

### Case 1 — plain call with partial application
```js
function greet(greeting, punct, name) { return `${greeting}, ${name}${punct} (${this.title})`; }
const hi = greet.myBind({ title: 'Dr.' }, 'Hello', '!');
hi('Ada');   // → ?
```
1. `myBind` is invoked with `this = greet`, `ctx = {title:'Dr.'}`, `preset = ['Hello', '!']`. Returns `bound`.
2. `hi('Ada')` → call `bound` *bare*. Inside, `this` is `undefined` (strict) / `globalThis` (sloppy). `this instanceof bound` → `false` (undefined isn't an instance of anything).
3. `calledAsNew = false`. Call `greet.apply({title:'Dr.'}, ['Hello', '!', 'Ada'])`.
4. Inside `greet`: `this.title = 'Dr.'`, args fill positionally. Returns `'Hello, Ada! (Dr.)'`.

### Case 2 — `new` with a bound function (the crown jewel)
```js
function Person(first, last) {
  this.first = first;
  this.last = last;
}
Person.prototype.full = function () { return this.first + ' ' + this.last; };

const Bound = Person.myBind({ /* ignored */ }, 'Ada');
const p = new Bound('Lovelace');
p.full();             // 'Ada Lovelace'
p instanceof Person;  // true
p instanceof Bound;   // true
```
1. `new Bound('Lovelace')` triggers `[[Construct]]`. JS creates a new object `o` with `Object.getPrototypeOf(o) = Bound.prototype = Object.create(Person.prototype)`.
2. `Bound` is called with `this = o`, `later = ['Lovelace']`.
3. Inside, `this instanceof bound` → `true` (`o`'s proto chain includes `Bound.prototype` which we just set). So `calledAsNew = true`.
4. Call `Person.apply(o, ['Ada', 'Lovelace'])`. Sets `o.first='Ada'`, `o.last='Lovelace'`.
5. `[[Construct]]` returns `o` (since `Person` did not return an object explicitly).
6. `p.full()` walks `p → Bound.prototype → Person.prototype → full found`. Returns `'Ada Lovelace'`.
7. `p instanceof Person` walks `p`'s chain looking for `Person.prototype` — found one hop in. ✓.

If we had naively returned `fn.apply(ctx, [...preset, ...later])` regardless of `new`, `o` would never receive the assignments, and `p.first` would be `undefined`. That's why detecting `new` is mandatory.

## Important takeaways

**Syntax to memorize**
- `this instanceof bound` inside a *named* wrapper — detects `new`.
- `Object.create(fn.prototype)` — chains the wrapper's prototype to the original's, so `instanceof` and inherited methods work after `new`.
- Concatenate args: `[...preset, ...later]`. Don't replace.

**Patterns to reuse**
- Same skeleton works for `Function.prototype.partial(fn, ...args)`, currying utilities, decorator factories — anything that returns a wrapped function preserving identity.

**Common mistakes**
- Returning an arrow function from `myBind`. Arrows can't be `new`-ed and have no `this`, so the `new`-detection trick fails.
- Forgetting `bound.prototype = Object.create(fn.prototype)` → `new bound()` produces objects that fail `instanceof fn`.
- Replacing `[...preset, ...later]` with just `later` (drops partial args) or just `preset` (drops the new call args).
- Using `fn.bind(ctx)` inside `myBind` (recursive — works in v8 but defeats the point).

**Why interviewers ask this**
- It's the *only* polyfill that simultaneously requires: closures, `this`, `apply`, partial application, prototype chain, `new` semantics. One question, six concepts.

## Variants

1. **`partial(fn, ...args)`** — same as bind but doesn't lock `this`. Drop the `ctx` parameter.
2. **`curry(fn)`** — returns until arity is met; can be implemented atop bind. Used in functional libraries (Ramda, Lodash).
3. **`Function.prototype.myCall(ctx, ...args)`** — see polyfill-call-apply.md.
4. **Why does `new Bound()` ignore `ctx`?** — Explain the spec: `[[Construct]]` creates `this`; the wrapper sees it via `this instanceof bound` and must forward it, not the bound `ctx`. Senior follow-up question.
5. **`bound.length`** — set `length` to `Math.max(0, fn.length - preset.length)` using `Object.defineProperty` for spec compliance.

## Revision notes

> **myBind — 60 second recap**
> - Returns a new function that closes over `(fn, ctx, ...preset)`.
> - On call: if invoked with `new`, IGNORE `ctx` (use the fresh `this`); else use `ctx`.
> - Detect `new` via `this instanceof bound` inside a *named function* wrapper (not arrow).
> - Concatenate args: `[...preset, ...later]`.
> - Wire `bound.prototype = Object.create(fn.prototype)` so `new bound()` chains correctly and `instanceof fn` holds.
> - Use `fn.apply` (or `Reflect.apply`) — never `fn.bind` (recursion).
> - Native bound fns have no own `.prototype`; polyfills compromise — fine for interviews.
> - Optional polish: spec-compliant `name = 'bound ' + fn.name`, `length = max(0, fn.length - preset.length)`.
> - **Trap #1:** using an arrow wrapper → `new` breaks, `this`-detection breaks.
> - **Trap #2:** forgetting to override `ctx` when called with `new` → instances come back blank.
