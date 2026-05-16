# Closures

## Intuition first: what even is a closure?

> **Mental Model:** A closure is a function that "remembers" the room it was born in. Even after the room is locked and everyone leaves, the function still has the key, and any variable that was in that room is still alive for it — and only for it.

Imagine you walk into your manager's office to grab a sticky note off her desk. You take the sticky note out into the hallway. You can still read what's written on it because *you carried it with you*. A closure is JavaScript doing the same thing: a function "carries" the variables that surrounded it at the moment it was created.

**Why does this concept exist?** Because JavaScript needs a way to keep state *private*. Other languages have keywords like `private` baked into classes; JavaScript, in its early days, didn't. So instead, the language gave you a trick: hide a variable inside a function, and let a smaller "inner" function be the only door through which it can be touched. That trick *is* the closure. Decades later, every counter, every memoized function, every middleware-builder, every "module" in Node is still riding on this same idea.

### First-principles definition

> A **closure** is the pair `(function, environment)`. When you create a function, JS attaches a hidden pointer to the variable environment where the function was defined. That pointer outlives the function call that created it, as long as the function itself is reachable.

The fancy textbook way to say this is "lexical scoping with first-class functions." The plain-English way to say it is: *functions remember where they came from, not where they're called from.*

### Progressive examples — start tiny, end realistic

```js
// 1) Tiniest possible closure — does NOTHING fancy
function outer() {
  const greeting = "hello";
  function inner() { return greeting; }  // inner "sees" greeting
  return inner;
}
const fn = outer();    // outer() has returned, its frame "should" be gone
fn();                  // → "hello"   ← but greeting is still alive!

// 2) Intermediate — closure that remembers AND mutates
function counter() {
  let n = 0;
  return () => ++n;    // returned arrow shares n with counter()'s frame
}
const next = counter();
next(); next(); next(); // 1, 2, 3

// 3) Advanced edge case — multiple closures over the SAME frame
function pair() {
  let v = 0;
  return [() => v, (x) => { v = x; }];   // getter and setter on one v
}
const [get, set] = pair();
set(42); get();        // → 42

// 4) Interview expectation — closure leak in a long-running server
function attach(bigBuffer) {
  return () => bigBuffer.id;   // entire bigBuffer is pinned in memory!
}
```

By the time you can explain example 4 in 30 seconds — including *why* `bigBuffer` is pinned — you're at interview-ready depth.

## Mental Model

> Picture a function as a backpack. When JS creates the function, it stuffs into the backpack a reference to **the room it was born in** (its lexical environment). Wherever that function travels — into a callback, into another module, into `setTimeout` — it carries the backpack. When it finally runs and asks "where's `x`?", it doesn't look around the room it's *currently* in. It reaches into the backpack and looks in the room it came from.

This is the entire mental model. Memorize it. Every interview question on closures collapses to: "what's in the backpack, and is the room still alive?"

## Why interviewers care

Interviewers reach for closures because *one concept tests three skills at once*:

1. **Scope reasoning** — do you know which variables are visible from where?
2. **Lifetime / memory reasoning** — do you know when GC can/can't reclaim?
3. **Idiom fluency** — do you reach for closures naturally for private state, memoization, currying, middleware?

If you stumble on closures, the interviewer has a cheap signal that you'll also stumble on `this`, async timing, module loading, and memory leaks. That's why it's the first question in 70% of JS interviews.

## Common beginner confusion

- "But the outer function already returned — how can its variables still exist?" → They exist because the inner function still references them; JS keeps the environment alive as long as *anyone* points into it.
- "Are closures a special syntax?" → No. Every function in JS is technically a closure; we just only use the word when the captured environment matters.
- "Does the closure capture *values* or *variables*?" → Variables (bindings). If the outer code changes the variable later, the closure sees the new value.
- "Does `this` get captured?" → No, not by `function` declarations. Yes, by arrow functions. This trips up beginners constantly.
- "Why do all my `setTimeout`s in a `for (var i...)` loop print the same number?" → Because all three callbacks share *one* `i` binding. There is only one room, with one variable, and by the time the timers fire it holds the final value.

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

> **Bridge:** Now that you can picture the "backpack of variables," let's see how the engine actually implements it. The backpack is not magic — it's a real object on the heap called a *Context*.

Every function literal in JS captures a `[[Environment]]` slot pointing to the lexical environment at its *creation site*. When the function runs, identifier lookup walks that chain — not the call site's chain. This is **lexical scoping** (vs dynamic scoping in some Lisps).

### Visualizing the scope chain

```
   Global Env
   ┌────────────────────────┐
   │ makeCounter: <fn>      │
   │ c: <fn>                │
   └─────────┬──────────────┘
             │  (outer ref)
             ▼
   makeCounter's Env (still alive!)
   ┌────────────────────────┐
   │ n: 2                   │  ← lives here, mutated by c()
   └─────────┬──────────────┘
             │  (outer ref / [[Environment]])
             ▼
   inner fn's local Env (created on each call to c())
   ┌────────────────────────┐
   │ (no locals)            │
   └────────────────────────┘
```

When `c()` does `++n`, it walks: local env → makeCounter's env → finds `n` → increments it.

```js
function makeCounter() {
  let n = 0;                        // lives in makeCounter's environment
  return () => ++n;                 // captures that environment
}
const c = makeCounter();
c(); // 1
c(); // 2
```

#### Line-by-line walkthrough

1. `function makeCounter() { ... }` — defines a function in the global env. Nothing else happens yet.
2. `const c = makeCounter();` — call begins. JS creates a new environment for this call. Inside it: `n = 0`. Then `return () => ++n;` constructs a new function object whose `[[Environment]]` points at *this* env. That function object is returned and stored in `c`.
3. Normally, after a call returns, its environment is garbage. **But** `c` holds a reference to a function whose `[[Environment]]` still points to that env. The GC sees the env is reachable. It stays.
4. `c();` — executes the arrow. It looks up `n` via the captured env, increments it (the env now holds `n = 1`), and returns 1.
5. `c();` — same env, `n` becomes 2, returns 2.

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

#### Walkthrough of the shared-context idea

Imagine `vault()` is called. Inside it, one environment is created with `secret = 0`. Two arrow functions are then built, both pointing to **the same** environment. They're not copies — they're two doors into one room.

```
   vault()'s Env
   ┌───────────────┐
   │ secret: 0     │
   └──┬──────────┬─┘
      │          │
      ▼          ▼
   set arrow   get arrow
```

When `set(42)` runs, it mutates `secret` in the shared room. When `get()` runs *after* that, it sees `42`. This is exactly the mechanism behind the module pattern and every "private field via closure" technique.

## Syntax cheat sheet

> **Bridge:** Now that you understand WHY closures work, the syntax below should feel like seven flavors of the same idea — each captures a different shape of environment.

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

### Reading the loop bug visually

```
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0);

Timeline:
  t=0  i=0  schedule cb1   ──┐
  t=0  i=1  schedule cb2     │  all three closures share ONE i
  t=0  i=2  schedule cb3   ──┘
  t=0  i=3  loop ends, i=3 (final value)
  t≈0  cb1 runs → looks up i → sees 3
  t≈0  cb2 runs → same
  t≈0  cb3 runs → same                  → prints 3, 3, 3
```

Now with `let`:

```
for (let i = 0; i < 3; i++) setTimeout(() => console.log(i), 0);

Spec rule: each iteration of a let-headed for-loop creates a FRESH binding.

  iter 0: env_0 { i: 0 }  ── cb1 captures env_0
  iter 1: env_1 { i: 1 }  ── cb2 captures env_1
  iter 2: env_2 { i: 2 }  ── cb3 captures env_2
  ──────────────────────────────────────────  → prints 0, 1, 2
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

> **How to use this section:** For each example, first try to predict the output yourself. Then read "I'd say" as the actual script you'd speak aloud to the interviewer. The "common candidate mistake" notes are the traps most people fall into — knowing them is half the battle.

### Example 1 — Counter factory
**Asked as:** "Implement `makeCounter()` so that each call returns an independent incrementing function."

**How to think aloud:** "OK — they want INDEPENDENT counters. That word 'independent' is the hint: each call to the factory must produce its own private `n`. So I'll declare `n` *inside* the factory, not outside. Each invocation gets a fresh env."

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

**Common candidate mistake:** declaring `let n = 0` *outside* `makeCounter`, which makes all counters share one variable. The interviewer will smile and ask "now make two of them" — and you'll see the bug.

**What the interviewer is testing:** Lexical environment isolation per outer-function call.
**Sharp follow-up they often ask:** "Add a reset method." → return `{ inc, reset: () => { n = start; } }`, both closing over the same `n`.

### Example 2 — The loop-closure bug (and `let` fix)
**Asked as:** "Why does this print 3 three times, and how do you fix it without `let`?"

**How to think aloud:** "There are two questions here: WHY does it print 3 three times, and HOW do I fix it. For 'why', I trace timing: timers fire after the loop is done, and by then `i` is 3. For the fix without `let`, I need to create a fresh binding per iteration — the IIFE trick captures the *value* of `i` at that moment as a new parameter."

I'd say: "With `var`, the three setTimeout callbacks share ONE `i` binding that becomes 3 by the time the timers fire. The fix is to create a per-iteration binding — either by using `let` (which gives a fresh `i` each iteration) or by wrapping in an IIFE that captures the current value as an argument."

```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0); // 3 3 3

// fix with IIFE (no let)
for (var i = 0; i < 3; i++) {
  (function (j) { setTimeout(() => console.log(j), 0); })(i);     // 0 1 2
}
```

**Common candidate mistake:** Saying "JS is async so the values get mixed up." That's wrong — the cause is *binding sharing*, not async-ness. Even a synchronous loop that stores the callbacks in an array and runs them later would show the same bug.

**What the interviewer is testing:** Closures capture bindings, not values; per-iteration scope concept.
**Sharp follow-up they often ask:** "What if the inner code does `await`?" → Same rule applies — `let` gives per-iteration capture across awaits too.

### Example 3 — Private bank account
**Asked as:** "Build an account with `deposit`, `withdraw`, `balance` where balance can't be tampered with from outside."

**How to think aloud:** "The keyword is 'can't be tampered with from outside.' That means `balance` must NOT be on the returned object. So I declare it as a local variable inside the factory and only expose *methods* that read/write it. Closure handles the rest."

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

**Common candidate mistake:** Returning `balance` as a number on the object (`return { balance, deposit, ... }`). That snapshots the number at creation — `acc.balance` would always read `100` even after deposits, because primitives don't auto-update like that. You need it to be a *function* that reads the live variable.

**What the interviewer is testing:** Shared-closure pattern for encapsulation (pre-`#private`).
**Sharp follow-up they often ask:** "Now write it with ES2022 `#private` fields — when would you prefer one over the other?"

### Example 4 — `once()` wrapper
**Asked as:** "Write a function `once(fn)` that calls `fn` only the first time; subsequent calls return the cached result."

**How to think aloud:** "I need a flag that survives across calls — that's a job for closure state. Two variables: `called` (bool) and `value` (cached result). Each call: check the flag, short-circuit if set."

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

**Common candidate mistake:** Setting `called = true` *after* calling `fn(...args)`. If `fn` throws, the flag never flips, so the next call retries — which may or may not be what you want. Be deliberate.

**What the interviewer is testing:** Stateful closure with a latch flag.
**Sharp follow-up they often ask:** "What if the first call throws?" → Decide: should retries be allowed? Either reset `called = false` in catch, or cache the rejection.

### Example 5 — `setInterval` stale closure leak
**Asked as:** "Spot the bug: a per-request interval that logs request data after the request is done."

**How to think aloud:** "Every per-request thing that survives the request is suspicious. `setInterval` keeps firing forever unless you clear it. Its callback closes over `req`. So even after the response is sent, the interval keeps `req` alive — GC can't free it. Multiply by N requests/sec, and the heap balloons."

I'd say: "The interval callback closes over `req`, keeping the entire request object alive for the process lifetime. Even if the handler returns, the interval keeps firing and holding GC roots. You must `clearInterval` on teardown."

```js
function handler(req, res) {
  const id = setInterval(() => console.log(req.id), 1000); // LEAK
  res.on("close", () => clearInterval(id));                // FIX
  res.end("ok");
}
```

**Common candidate mistake:** Saying "Node will GC the interval when no one references it." Wrong — `setInterval` itself is a GC root in libuv; the timer queue references the callback, which references the closure, which references `req`. Only `clearInterval` (or process death) frees it.

**What the interviewer is testing:** Closure lifetime + memory leak intuition for long-running Node.
**Sharp follow-up they often ask:** "Same bug with `setTimeout`?" → No — setTimeout fires once and releases. The danger is `setInterval` and event listeners.

### Example 6 — Module pattern (IIFE-revealed)
**Asked as:** "Build a counter module that exposes only `inc` and `get` — no way to set the count directly."

**How to think aloud:** "Same pattern as the bank account, but at module level. IIFE runs once on load, creates the private state, returns just the public methods. The closure handles privacy."

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

**Common candidate mistake:** Forgetting the trailing `()` on the IIFE. Without invocation, you get a function, not the returned object — and `Counter.inc` is undefined.

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
