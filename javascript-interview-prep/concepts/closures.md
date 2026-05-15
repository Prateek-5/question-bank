# Closures

## TL;DR
- **A closure = a function + the lexical environment it was *defined* in.** The inner function keeps a reference to outer scope variables even after the outer function returns.
- Closures are how JS does **private state, currying, memoization, factories, and module pattern**.
- The classic loop-bug is closure-over-`var`: all callbacks share the SAME binding. `let` creates per-iteration bindings.
- Closures pin memory: if a long-lived callback closes over a big object, V8 keeps it alive (memory leak).
- V8 optimizes closures via "context" objects; only variables actually used by inner functions are retained (modern V8 is smart, but assume "all used vars" for safety).

## Why backend interviewers care
- Express/Koa middleware, per-request scoping, and connection pooling lean heavily on closures.
- Closure-based memory leaks are a top cause of Node.js heap growth in production.
- Factory patterns (logger, db client) and dependency injection in plain JS are pure closure usage.

## Core mental model
Every function literal in JS captures a `[[Environment]]` slot pointing to the lexical environment at its *creation site*. When the function runs, identifier lookup walks that chain — not the call site's chain. This is **lexical scoping** (vs dynamic scoping in some Lisps).

```js
function makeCounter() {
  let n = 0;                        // lives in makeCounter's environment
  return () => ++n;                 // captures that environment
}
const c = makeCounter();
c(); // 1
c(); // 2
```

After `makeCounter` returns, its activation would normally be garbage-collected — but `c` holds a reference into its environment, so V8 keeps the environment alive. This is the *only* way JS exposes private state pre-ES2022 (now there's also `#privateField` on classes).

V8 represents the captured environment as a "Context" object on the heap. Crucially, **multiple closures sharing the same outer scope share the SAME context** — they see each other's mutations. This is the engine of the module pattern.

```js
function vault() {
  let secret = 0;
  return {
    set: (v) => { secret = v; },
    get: () => secret,
  };
}
```

`set` and `get` close over the same `secret`.

## Syntax cheat sheet
```js
// Basic closure
function outer() {
  const x = 10;
  return function inner() { return x; };
}

// Arrow closure (same semantics)
const adder = (a) => (b) => a + b;
adder(2)(3); // 5

// IIFE for one-off encapsulation
const counter = (() => {
  let n = 0;
  return () => ++n;
})();

// Loop with var: shared binding
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0); // 3 3 3

// Loop with let: per-iteration binding
for (let i = 0; i < 3; i++) setTimeout(() => console.log(i), 0); // 0 1 2

// Loop with var fixed via IIFE (legacy)
for (var i = 0; i < 3; i++) {
  (function (j) { setTimeout(() => console.log(j), 0); })(i);
}

// Closure for private state (module pattern)
const cache = (() => {
  const store = new Map();
  return {
    get: (k) => store.get(k),
    set: (k, v) => store.set(k, v),
  };
})();

// Once: closure that fires only once
const once = (fn) => {
  let called = false, value;
  return (...a) => {
    if (called) return value;
    called = true;
    return (value = fn(...a));
  };
};

// Memoize
const memo = (fn) => {
  const cache = new Map();
  return (x) => cache.has(x) ? cache.get(x) : (cache.set(x, fn(x)), cache.get(x));
};

// Currying
const curry = (fn) => {
  return function curried(...args) {
    return args.length >= fn.length
      ? fn(...args)
      : (...more) => curried(...args, ...more);
  };
};

// Closure leak risk
function attach(big) {
  // even if we only use big.id, ALL of big may be retained
  return () => big.id;
}
```

## Edge cases & interview traps
1. **`for (var i ...)` + async callback** — all callbacks log the final value of `i` because they share one binding.
2. **`for (let i ...)` creates a fresh binding per iteration** — but only the binding *inside* the for-header is per-iter; vars declared in the body still share if `var`.
3. **Closures see live values, not snapshots** — if outer code mutates `x` after closure creation, the closure sees the new value.
4. **A closure CAN extend the lifetime of the outer activation indefinitely** — common leak source (event listeners, intervals).
5. **`setInterval` callbacks closing over request-scoped objects** keep them alive forever — clear the interval on teardown.
6. **Returning closures from request handlers** that hold the whole `req`/`res` causes per-request memory bloat under load.
7. **V8 may optimize away unused capture vars** — but only when it's *certain*; using `eval` or `with` disables this.
8. **`this` is NOT captured by regular function closures** — it's bound at call time. Arrows DO capture `this` lexically.
9. **Shared closure mutation race** — multiple async callbacks closing over the same `let` see and mutate concurrently (no JS thread race, but logical races still happen).
10. **Function created inside a hot loop allocates a new closure per call** — V8 may inline, but if you cache the function outside, you avoid allocation.
11. **Closure over loop iterator + early return** — the returned function still holds the entire enclosing scope, not just `i`.
12. **`bind` creates a new function** but does NOT close over the original's free vars directly — it stores them on the function object.
13. **`debugger` keyword forces full closure retention** for inspection — perf impact in prod.
14. **`function.name` is set from the declaration, not the closure** — useful for stack traces.
    ```js
    const make = () => function inner() {};
    make().name; // "inner"
    ```

## Interview worked examples

### Example 1 — Counter factory
**Asked as:** "Implement `makeCounter()` so that each call returns an independent incrementing function."

I'd say: "Each call to makeCounter creates a fresh lexical environment containing `n`. The returned function closes over that environment, so two counters don't share state."

```js
function makeCounter(start = 0) {
  let n = start;
  return () => ++n;
}
const a = makeCounter();
const b = makeCounter();
a(); a(); a(); // 1, 2, 3
b();           // 1 — independent
```

**What the interviewer is testing:** Lexical environment isolation per outer-function call.
**Sharp follow-up they often ask:** "Add a reset method." → return `{ inc, reset: () => { n = start; } }`, both closing over the same `n`.

### Example 2 — The loop-closure bug (and `let` fix)
**Asked as:** "Why does this print 3 three times, and how do you fix it without `let`?"

I'd say: "With `var`, the three setTimeout callbacks share ONE `i` binding that becomes 3 by the time the timers fire. The fix is to create a per-iteration binding — either by using `let` (which gives a fresh `i` each iteration) or by wrapping in an IIFE that captures the current value as an argument."

```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0); // 3 3 3

// fix with IIFE (no let)
for (var i = 0; i < 3; i++) {
  (function (j) { setTimeout(() => console.log(j), 0); })(i);     // 0 1 2
}
```

**What the interviewer is testing:** Closures capture bindings, not values; per-iteration scope concept.
**Sharp follow-up they often ask:** "What if the inner code does `await`?" → Same rule applies — `let` gives per-iteration capture across awaits too.

### Example 3 — Private bank account
**Asked as:** "Build an account with `deposit`, `withdraw`, `balance` where balance can't be tampered with from outside."

I'd say: "I'll use an IIFE-returned closure. Both methods share the same `balance` variable, but it's not exposed on the returned object — no way to mutate it directly."

```js
function makeAccount(initial = 0) {
  let balance = initial;
  return {
    deposit: (n) => { balance += n; },
    withdraw: (n) => {
      if (n > balance) throw new Error("insufficient");
      balance -= n;
    },
    balance: () => balance,
  };
}
const acc = makeAccount(100);
acc.deposit(50); acc.balance(); // 150
```

**What the interviewer is testing:** Shared-closure pattern for encapsulation (pre-`#private`).
**Sharp follow-up they often ask:** "Now write it with ES2022 `#private` fields — when would you prefer one over the other?"

### Example 4 — `once()` wrapper
**Asked as:** "Write a function `once(fn)` that calls `fn` only the first time; subsequent calls return the cached result."

I'd say: "Latch a boolean in the closure; on first call, run fn and cache the result; on subsequent calls, short-circuit and return the cached value. Useful for idempotent init like DB connect."

```js
const once = (fn) => {
  let called = false, value;
  return (...args) => {
    if (called) return value;
    called = true;
    return (value = fn(...args));
  };
};
const connect = once(() => Date.now());
connect(); connect(); // same timestamp
```

**What the interviewer is testing:** Stateful closure with a latch flag.
**Sharp follow-up they often ask:** "What if the first call throws?" → Decide: should retries be allowed? Either reset `called = false` in catch, or cache the rejection.

### Example 5 — `setInterval` stale closure leak
**Asked as:** "Spot the bug: a per-request interval that logs request data after the request is done."

I'd say: "The interval callback closes over `req`, keeping the entire request object alive for the process lifetime. Even if the handler returns, the interval keeps firing and holding GC roots. You must `clearInterval` on teardown."

```js
function handler(req, res) {
  const id = setInterval(() => console.log(req.id), 1000); // LEAK
  res.on("close", () => clearInterval(id));                // FIX
  res.end("ok");
}
```

**What the interviewer is testing:** Closure lifetime + memory leak intuition for long-running Node.
**Sharp follow-up they often ask:** "Same bug with `setTimeout`?" → No — setTimeout fires once and releases. The danger is `setInterval` and event listeners.

### Example 6 — Module pattern (IIFE-revealed)
**Asked as:** "Build a counter module that exposes only `inc` and `get` — no way to set the count directly."

I'd say: "Run an IIFE that creates the private state and returns just the public API. Multiple methods share one lexical environment, so they all see the same `count` — but external code never gets a reference to `count` itself."

```js
const Counter = (() => {
  let count = 0;
  return {
    inc: () => ++count,
    get: () => count,
  };
})();
Counter.inc(); Counter.get(); // 1
// Counter.count → undefined
```

**What the interviewer is testing:** Pre-class encapsulation idiom; foundation of every Node.js singleton pattern.
**Sharp follow-up they often ask:** "Now make it a factory that returns multiple independent counters." → Wrap the IIFE body in a named function returning the object.

## Common machine-coding patterns
- **Counter factory** — when used: rate-limit counters, request IDs. Sketch:
  ```js
  const makeCounter = (start = 0) => () => ++start;
  ```
- **Once** — when used: idempotent init (db connect, config load). Sketch above.
- **Memoize** — when used: pure expensive fn (parsing, regex compile). Sketch above; add WeakMap for object keys.
- **Currying / partial application** — when used: building configurable middleware. Sketch:
  ```js
  const logger = (level) => (msg) => console.log(`[${level}]`, msg);
  ```
- **Module pattern (private state)** — when used: singletons (db pool, in-memory cache). IIFE returning an object of methods.
- **Debounce/throttle** — closure over `timeoutId` + `lastCall`. (Full impls in machine-coding-patterns.md.)

## Backend-specific notes
In Express/Koa/Fastify, every route handler is a closure that often captures the `app`-level config and per-request middleware results via `req`. **Request-scoped state lives on `req` or via `AsyncLocalStorage`**, not in module-level closures, because module-level closures are shared across all requests in the same process — leaking data between users is a classic auth bug. Connection pools, on the other hand, *should* live in module-level closures (singleton via IIFE or top-level `const pool = mysql.createPool(...)`).

Memory-leak hunting in Node: if heap snapshots show growing retention through a closure, look for long-lived listeners (`EventEmitter.on` without `off`), intervals not cleared, or caches without eviction (use `WeakMap` or `lru-cache`).

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ CLOSURES — DAY-BEFORE CRAM                               │
├──────────────────────────────────────────────────────────┤
│ • closure = fn + lexical env at DEFINITION site          │
│ • multiple closures share one outer env (private state)  │
│ • for(var) → shared binding; for(let) → per-iter binding │
│ • closures see LIVE values, not snapshots                │
│ • arrow captures this/arguments lexically; fn does not   │
│ • use cases: factory, once, memoize, curry, module       │
│ • risks: interval/listener leaks, request data bleed     │
│ • module-level closure = shared across requests          │
│ • V8 may DCE unused captures unless eval/with present    │
│ • bind stores args on fn obj — not the same as closure   │
│ • AsyncLocalStorage for per-request scope, not closures  │
│ • once: latch flag in closure → return cached value      │
│ • memoize objects → use WeakMap to allow GC              │
└──────────────────────────────────────────────────────────┘
```
