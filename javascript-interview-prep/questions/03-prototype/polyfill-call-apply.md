# Polyfill `Function.prototype.call` and `Function.prototype.apply`

## Source
- Canonical machine-coding interview problem — asked at Razorpay, Walmart, Atlassian, Microsoft.
- Reference spec: https://tc39.es/ecma262/#sec-function.prototype.call

## Why this question matters in interviews
`call` and `apply` are the **simplest of the three explicit-binding polyfills (call / apply / bind)** — and precisely because they're simple, interviewers use them to test whether you understand *how `this` is set without engine magic*. The clever bit is the "symbol-as-temporary-property" trick: you stash the function on the context object under a unique key, invoke it method-style (`ctx[key](...)`) so JS's implicit binding does the `this` setup for free, then delete the key. Demonstrates that you understand rule 2 (implicit binding) is the **mechanism** behind rule 3, not a separate thing. Backend engineers see this in callsite wrappers, mock-injection utilities, and code that does dynamic dispatch.

## Concepts involved

### Spec contract
```js
fn.call(thisArg, ...args)    // pass args one by one
fn.apply(thisArg, argsArray) // pass args as an array (or iterable)

// In sloppy mode, thisArg=null/undefined is coerced to globalThis.
// In strict mode, thisArg=null/undefined stays as-is.
// Primitive thisArg in sloppy mode is boxed (e.g. 'x' → new String('x')).
```

### Syntax to lock in
```js
Function.prototype.myCall = function (ctx, ...args) {
  ctx = ctx ?? globalThis;            // null/undefined → global (sloppy semantics)
  const key = Symbol();               // unique key, won't collide with anything
  ctx[key] = this;                    // 'this' here = the function myCall was called on
  try { return ctx[key](...args); }   // method-style call → implicit binding sets `this = ctx`
  finally { delete ctx[key]; }        // always clean up
};

Function.prototype.myApply = function (ctx, args = []) {
  return this.myCall(ctx, ...args);   // delegate
};
```

### Runtime / engine behavior
- **Why the Symbol trick works:** `ctx[key]()` is a *method-style* call. JS's implicit-binding rule (rule 2 of `this`) automatically sets `this = ctx` inside the invoked function. We are *literally piggybacking on the binding rule we are trying to polyfill.* This is the right level of abstraction.
- **Why `Symbol()`, not a string like `'__tmp__'`:** strings can collide with existing keys on `ctx`. Symbols are guaranteed unique — `Symbol() !== Symbol()` even with the same description.
- **`finally` cleanup:** if `fn` throws, we still need to `delete ctx[key]`, otherwise we've permanently polluted the caller's object. Don't skip the try/finally.
- **`ctx ?? globalThis`:** in sloppy mode, native `call(null)` makes `this === globalThis`. In strict, it stays `null`. The polyfill above mimics sloppy; document the trade-off if asked.
- **Primitive `ctx` boxing** — `(function(){return this}).call('x')` returns a `String` object wrapper in sloppy, `'x'` itself in strict. Setting `'x'[Symbol()] = fn` throws in strict on a frozen primitive — handle with `Object(ctx)` if you need full spec fidelity.

### Edge cases (interview traps)
1. **Existing key clash** — without `Symbol()` you'd risk overwriting `ctx.foo` and then `delete` it (losing user data). Symbols sidestep this.
2. **Throwing function** — `try/finally` is mandatory to clean up.
3. **`null` / `undefined` ctx** — coerce to `globalThis` (sloppy) or leave alone and accept TypeError on property set (strict). Choose your spec and document it.
4. **Primitive ctx** — `Object(ctx)` boxes it. Mention but only implement if asked.
5. **`apply` with iterable, not array** — native `apply` requires `argsArray` to be array-like (has `length`). `myCall(ctx, ...args)` accepts any iterable since spread does the work. Good enough.
6. **Frozen ctx** — `Object.freeze({})`. Setting a key throws. Native `call` doesn't have this problem because it doesn't mutate `ctx`. Acknowledge as a limitation of the polyfill; full-spec fidelity would use a `Reflect.apply`-style approach.
7. **Returning the function's return value** — many candidates forget. The whole `ctx[key](...)` expression must be **returned**, not just called.
8. **`apply` vs spread** — `fn.apply(ctx, args)` predates `...` spread. In modern code you'd just write `fn.call(ctx, ...args)`. But the polyfill is still asked.

## Brute force approach
"I'll save `this = ctx` somewhere and read it." There's no way to manually set the engine-level `this` of a function from outside — you can only do it via the call site shape (method-style, `new`, or explicit binding). So if you can't use the very `call`/`apply`/`bind` you're polyfilling, you must engineer a method-style callsite. That's exactly what the Symbol trick does.

A worse alternative — wrap `fn` in `new Function('ctx', 'args', ...)` and stringify — is a security/perf disaster. Don't go there.

## Optimal approach
Symbol-key trick: stash the function on `ctx` under a unique symbol → invoke method-style → delete the key in `finally`. Return the call's result. O(1) overhead. `apply` is a one-line wrapper around `call`.

## Solution (JavaScript)

```js
/**
 * Polyfill Function.prototype.call.
 *
 * Strategy: stash the function on `ctx` under a UNIQUE Symbol key, invoke
 * method-style so the engine's implicit-binding rule sets `this = ctx`
 * for free, then delete the key (always, even on throw).
 */
Function.prototype.myCall = function (ctx, ...args) {
  if (typeof this !== 'function') {
    throw new TypeError('myCall must be called on a function');
  }
  // null/undefined → globalThis (sloppy-mode semantics).
  // Primitive ctx is boxed via Object(...) so we can set a property on it.
  ctx = (ctx === null || ctx === undefined) ? globalThis : Object(ctx);

  const key = Symbol('fn');     // unique — cannot collide with any existing key
  ctx[key] = this;              // `this` here = the function being myCall'd
  try {
    return ctx[key](...args);   // method-style call → JS sets this = ctx for us
  } finally {
    delete ctx[key];            // clean up even if the function threw
  }
};

/**
 * Polyfill Function.prototype.apply — same as call, but takes an array.
 */
Function.prototype.myApply = function (ctx, args) {
  // Spec: if argsArray is null/undefined, treat as empty.
  // We accept any iterable (arrays + array-likes via Array.from).
  if (args !== null && args !== undefined && typeof args[Symbol.iterator] !== 'function' && typeof args.length !== 'number') {
    throw new TypeError('myApply: second arg must be array-like or iterable');
  }
  return this.myCall(ctx, ...(args ? Array.from(args) : []));
};
```

## Step-by-step dry run

```js
const user = { name: 'Ada' };
function greet(greeting, punct) { return `${greeting}, ${this.name}${punct}`; }

greet.myCall(user, 'Hello', '!');           // → ?
greet.myApply(user, ['Hi', '?']);           // → ?
```

### Trace `myCall(user, 'Hello', '!')`
1. `this` inside `myCall` is `greet` (because `greet.myCall(...)` is itself a method-style call — irony intended).
2. `ctx = user` (not null/undefined → kept as-is by `Object(...)`).
3. `key = Symbol('fn')` — say it prints as `Symbol(fn)#a1b2c3` internally.
4. `user[key] = greet`. Now `user` looks like `{ name: 'Ada', [Symbol(fn)#a1b2c3]: greet }`.
5. `user[key]('Hello', '!')` — this is the **method-style** call. JS's implicit binding (rule 2) sets `this = user` inside `greet`. The args fill `greeting='Hello', punct='!'`.
6. Body executes: `` `Hello, Ada!` ``. Stored as the return value.
7. `finally` block runs: `delete user[key]`. `user` is back to `{name:'Ada'}`.
8. Return `'Hello, Ada!'`.

### Trace `myApply(user, ['Hi', '?'])`
1. `myApply` delegates → `this.myCall(user, 'Hi', '?')`.
2. Same path as above. Returns `'Hi, Ada?'`.

### Throw safety
```js
function boom() { throw new Error('nope'); }
const obj = { x: 1 };
try { boom.myCall(obj); } catch {}
console.log(Object.getOwnPropertySymbols(obj));  // [] — key was cleaned up
```
The `finally` block deleted the symbol even though `boom` threw. Without `try/finally`, `obj` would carry an orphan symbol key forever (memory + correctness leak).

## Important takeaways

**Syntax to memorize**
- `const key = Symbol(); ctx[key] = this; try { return ctx[key](...args); } finally { delete ctx[key]; }` — the four lines that *are* the polyfill.
- `Object(ctx)` for primitive boxing.
- `ctx ?? globalThis` for null/undefined defaulting (sloppy semantics).

**Patterns to reuse**
- "Use a Symbol as a temporary property key to avoid collisions" is a reusable trick: mutex flags on objects, request-scoped metadata, framework internals (React fibers, etc.).
- `try/finally` for cleanup of any temporary state — closes file handles, releases locks, removes event listeners.

**Common mistakes**
- Using a string key like `'__tmp__'` — collides with user data; `delete` removes the user's property.
- Forgetting `return` — function executes but caller gets `undefined`.
- Skipping `try/finally` — exceptions leave the symbol stuck on `ctx`.
- Implementing `apply` from scratch instead of delegating to `call`. Redundant and error-prone.
- Forgetting to handle `null`/`undefined` ctx — `Object(null)` returns a new empty object, not `globalThis`. Test it.

**Why interviewers ask this**
- It tests whether you can use language rules **as tools**. The Symbol trick is the canonical "build complex semantics out of simple ones" exercise.

## Variants

1. **Implement `Reflect.apply(fn, thisArg, args)`** — same logic, different namespace. Used internally in proxy traps.
2. **Implement `Function.prototype.toString.call(fn)`** — actually a usage question, not a polyfill: shows you know `toString` is a method that walks the chain.
3. **`fn.uncurryThis()`** — turn `Array.prototype.slice` into a free function `slice(arr, ...)` by binding `this`. Common in Babel/SES code.
4. **"Why not just use spread?"** — `fn.apply(ctx, args)` ≡ `fn.call(ctx, ...args)` ≡ `Reflect.apply(fn, ctx, args)`. Modern code uses spread; the polyfill is still asked because it tests fundamentals.
5. **What goes wrong with frozen ctx?** — Mutating frozen objects throws in strict mode. Polyfill limitation. Native `call` doesn't mutate.

## Revision notes

> **myCall / myApply — 60 second recap**
> - Trick: stash `this` (the function) on `ctx` under a unique `Symbol()` key, invoke method-style, delete the key in `finally`.
> - Method-style call triggers implicit binding (rule 2) → `this = ctx` automatically.
> - `Symbol()` avoids clashing with existing keys; strings would risk overwriting user data.
> - `try/finally` is mandatory — exceptions must not leak the temp key.
> - `null` / `undefined` ctx → coerce to `globalThis` (sloppy semantics).
> - Primitive ctx → `Object(ctx)` to box it so property assignment works.
> - **Return** `ctx[key](...args)` — the return value matters.
> - `myApply` is a one-line wrapper around `myCall` via spread.
> - Modern equivalent in user code: `fn.call(ctx, ...args)` over `fn.apply(ctx, args)`.
> - **Trap:** using a string key — collisions destroy user data.
> - **Trap:** no `try/finally` — symbol leaks on throw.
