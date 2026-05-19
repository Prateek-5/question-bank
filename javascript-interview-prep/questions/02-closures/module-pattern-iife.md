# Revealing Module Pattern (IIFE) — closure-based private state for browser-era JS

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [counter-ii.md](./counter-ii.md), [private-data-counter.md](./private-data-counter.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Douglas Crockford (2003); Christian Heilmann's "Revealing Module Pattern" (2007).

---

## 1. Problem statement

**Signature**
```ts
// The pattern, not a function:
const Module = (function () {
  // private state via closure
  // private helpers
  return { /* public API */ };
})();
```

**Input / Output examples**

| Code                                                         | Behaviour                                  |
|--------------------------------------------------------------|---------------------------------------------|
| `const C = (function(){ let n=0; return { inc(){n++}, get(){return n;} }; })();` | `C.inc(); C.get()` → `1`           |
| `C.n`                                                        | `undefined` (truly inaccessible)            |
| `Object.keys(C)`                                             | `['inc', 'get']` (only public methods)      |
| `JSON.stringify(C)`                                          | `"{}"` (methods skipped, `n` invisible)     |

**Constraints**
- The IIFE runs **once** — produces a singleton.
- Private state is reachable only via the returned methods.
- For per-instance state, replace the IIFE with a **factory function** (call it per instance).

---

## 2. Plain-English restatement

Wrap a chunk of code in a function and call it immediately. Whatever you declare inside is *private to that function*; whatever the function returns is the *public API*. The returned methods close over the private state and can read/mutate it; nothing else in the world can.

This is the closure-based answer to "how do you build a module with private state in a language that has no native modules and no private fields?" — the pre-ES6 idiom that powered jQuery, Backbone, RequireJS, and 90% of npm packages before classes.

---

## 3. Why this matters in interviews

Interviewers ask for two reasons. First, to test whether you understand closure-based encapsulation at the *architecture* level — not just on a counter, but on whole modules. Second, to see whether you know its modern replacements (ES6 modules + class `#private` fields) and can articulate *when to use which*. A senior candidate doesn't just write the IIFE — they explain when to still reach for it (legacy bundlers, browser globals, plugin-style APIs) and when not to (modern Node, TypeScript, ESM). It's the single best example of "closure as a privacy mechanism."

---

## 4. Mental model

A **vending machine bolted to the floor**. Inside, there's a stockroom (private state) and a couple of operators (private helpers). The customer-facing slot exposes only a few buttons (public methods). The IIFE is the act of bolting it to the floor — it runs once at install time and the stockroom is permanently sealed.

```
   (function () {
     // ─────────────────── private state
     let buckets = new Map();
     const CAPACITY = 10;

     // ─────────────────── private helpers
     function refill(b) { ... }

     // ─────────────────── public API (revealed at the end)
     return {
       tryConsume(key) { ... uses buckets, refill ... },
       reset(key) { buckets.delete(key); },
     };
   })();
   ↑↑
   immediately invoked; result is captured in `RateLimiter`
   private state lives in the IIFE's LE on the heap
```

The closure record holding `buckets`, `CAPACITY`, `refill` is referenced by `tryConsume` and `reset`. As long as `RateLimiter` is reachable, the private state lives. Nothing outside can name `buckets` — it's invisible to reflection, to enumeration, to JSON serialization.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If you remove the trailing `()` from `(function () { ... })`, what does the assignment produce?
> 2. Inside an IIFE without `'use strict'`, what is `this`?
> 3. Why might you still reach for the module pattern in modern Node — or wouldn't you?

---

## 6. Brute force — walked through

### Wrong attempt 1: leading-underscore convention

```js
const Counter = {
  _count: 0,
  inc() { this._count++; },
  get() { return this._count; },
};
Counter._count = 999;     // anyone can rewrite
```

Convention, not enforcement. Anyone can read or overwrite `_count`. Fails the privacy test.

### Wrong attempt 2: forget the `()`

```js
const Counter = (function () {
  let count = 0;
  return { inc() { count++; } };
});
Counter.inc;                // undefined — Counter is the *function*, not the IIFE result
```

Without the trailing `()`, you've assigned a function expression, not invoked it. `Counter()` would work but defeats the "module runs once" intent. Add the parens.

### Wrong attempt 3: declare private state outside the IIFE

```js
let count = 0;
const Counter = (function () {
  return { inc() { count++; } };
})();
```

`count` is now a module-scope (or global) variable, accessible from outside the closure. Private only inside the file; not private from the rest of the file. Closure must own the state.

### Wrong attempt 4: use the IIFE singleton when you need instances

```js
const RateLimiter = (function () { /* shared buckets */ })();
RateLimiter.tryConsume('user-1');
RateLimiter.tryConsume('user-2');   // shares state across all users
```

If different consumers should have independent state, drop the IIFE and use a **factory function** that you call per instance. The IIFE shape is a singleton by construction.

---

## 7. The unlocking insight

> **Run the function once, return only the methods you want public. The function's local scope becomes the closure record for those methods — and that record is unreachable from outside.**

The IIFE creates a one-shot execution context. During that execution, you declare private state with `let`/`const`, define private helper functions, and finally return an object exposing only the parts of the API you want consumers to touch. The returned object's methods all carry `[[Environment]]` pointing at the IIFE's LE — so they can read and mutate the private state forever, but no external reference exists to that LE.

**Why this is "hard" privacy:**

- No syntactic way to reach `buckets` from outside — the binding name is invisible.
- `Object.keys(Module)` returns only the explicitly-revealed methods.
- `Reflect.ownKeys`, `Object.getOwnPropertyNames`, `for...in` — all blind.
- Even a `Proxy` wrapping `Module` can't intercept access to closure variables.
- Stronger than `Symbol`-keyed properties (which show up in `Reflect.ownKeys`).

The pattern's main downsides today: it's a singleton by construction (use a factory for per-instance), and modern ES modules give you file-level private scope for free without any IIFE.

---

## 8. Solution (annotated)

```js
// Singleton — IIFE runs once and exposes a fixed handle
const RateLimiter = (function () {        // step 1: open IIFE
  'use strict';                            // step 2: prevent `this === globalThis` leaks

  // ── private state in closure ──
  const buckets = new Map();               // step 3: private — can't be read from outside
  const CAPACITY = 10;
  const REFILL_PER_MS = 0.01;

  // ── private helper ──
  function refill(b) {                     // step 4: not part of public API
    const now = Date.now();
    b.tokens = Math.min(CAPACITY, b.tokens + (now - b.lastRefill) * REFILL_PER_MS);
    b.lastRefill = now;
  }

  // ── public API ──
  function tryConsume(key) {               // step 5: defined inside; closes over buckets + refill
    if (!buckets.has(key)) buckets.set(key, { tokens: CAPACITY, lastRefill: Date.now() });
    const b = buckets.get(key);
    refill(b);
    if (b.tokens < 1) return false;
    b.tokens -= 1;
    return true;
  }

  function reset(key) { buckets.delete(key); }

  return { tryConsume, reset };            // step 6: reveal only what should be public
})();                                       // step 7: IMMEDIATELY invoke — note the trailing ()

// Factory variant — one independent instance per call
function createRateLimiter(capacity = 10, refillPerMs = 0.01) {
  const buckets = new Map();
  function refill(b) { /* ... same body ... */ }
  return {
    tryConsume(key) { /* ... */ },
    reset(key) { buckets.delete(key); },
  };
}
```

**Try it yourself**

```js
console.log(RateLimiter.tryConsume('user-1'));   // true
console.log(RateLimiter.tryConsume('user-1'));   // true
console.log(RateLimiter.buckets);                // undefined — truly private
console.log(Object.keys(RateLimiter));           // ['tryConsume', 'reset']
console.log(JSON.stringify(RateLimiter));        // '{}'  — methods skipped, state invisible

// Factory: independent instances
const tenantA = createRateLimiter();
const tenantB = createRateLimiter();
tenantA.tryConsume('x');           // doesn't affect tenantB
```

---

## 9. Step-by-step dry run

Input:

```js
RateLimiter.tryConsume('user-1');
RateLimiter.tryConsume('user-1');
RateLimiter.buckets;
Object.keys(RateLimiter);
```

Values-first trace:

| Step | Call                          | `buckets` state                         | Returns                  |
|------|-------------------------------|------------------------------------------|--------------------------|
| init | IIFE runs                     | `buckets = new Map()`                   | `{tryConsume, reset}`     |
| 1    | `tryConsume('user-1')`        | adds `{user-1: {tokens:9, ...}}`        | `true`                    |
| 2    | `tryConsume('user-1')`        | `{user-1: {tokens:8, ...}}`             | `true`                    |
| 3    | `RateLimiter.buckets`         | (unchanged)                              | `undefined` (no such property) |
| 4    | `Object.keys(RateLimiter)`    | (unchanged)                              | `['tryConsume', 'reset']` |

`buckets` lived in the IIFE's LE throughout; the only way to touch it was through the two public methods.

---

## 10. Common confusion + traps

1. **Forgetting the trailing `()`.**
   Without invocation, you've assigned the function, not its return value. `Module.method` is `undefined`.

2. **`this === globalThis` in the IIFE body.**
   Without `'use strict'`, top-level `this` inside the IIFE is the global object. Adding strict mode at the top of the IIFE makes `this` `undefined` — usually what you want.

3. **Singleton vs factory confusion.**
   IIFE pattern produces a singleton. If you need independent instances, drop the IIFE and use a factory function (call it per instance).

4. **Declaring private state outside the IIFE.**
   Defeats the privacy. Keep all state inside the function body.

5. **Symbol-keyed properties as "privacy."**
   `Symbol`s show up in `Reflect.ownKeys`. Not actually private. Closures and `#fields` are the real options.

6. **`this`-loss on method return.**
   If a returned method uses `this`, destructuring it (`const { method } = Module; method();`) loses `this`. Closures-based methods that use `count` (via scope chain) don't have this issue; closure-based methods that use `this` do.

7. **Memory pinning.**
   The IIFE's full LE is kept alive for the module's lifetime. If you accidentally captured a 50 MB blob during init, that blob stays in memory until the module reference is dropped (rarely happens for module singletons).

---

## 11. Senior follow-ups & variants

### Variant 1 — Factory module pattern (per-instance state)

```js
function createRateLimiter(capacity, refillPerMs) {
  const buckets = new Map();
  function refill(b) { /* ... */ }
  return {
    tryConsume(key) { /* ... uses buckets, refill ... */ },
    reset(key) { buckets.delete(key); },
  };
}

const tenantA = createRateLimiter(10, 0.01);
const tenantB = createRateLimiter(100, 0.1);
// tenantA and tenantB share nothing
```

Same closure shape, but invocation per instance. Use whenever you need independent state.

### Variant 2 — Augmenting module pattern (extending in another file)

Pre-bundler way of adding methods to an existing module across files:

```js
// file1.js
window.MyMod = (function () {
  return { foo() {} };
})();

// file2.js
window.MyMod = (function (mod) {
  mod.bar = function () { /* ... */ };
  return mod;
})(window.MyMod || {});
```

Now `MyMod` has both `foo` and `bar`. Today you'd just use ES modules and re-export.

### Variant 3 — IIFE with injected dependencies

Makes dependencies explicit and minifies well (the IIFE param names can be mangled):

```js
const App = (function ($, win, doc) {
  // use $, win, doc internally
  return { /* api */ };
})(jQuery, window, document);
```

This pattern is everywhere in pre-bundler jQuery code.

### Variant 4 — Modern replacements (mention unprompted for senior signal)

- **ES modules** (`import`/`export`) — every file has private top-level scope by default. The "module pattern" is a free side effect of writing modular code.
- **Class `#private` fields (ES2022)** — true syntactic privacy for class instances. Faster than closures (V8 optimizes hidden classes); supports `extends`.
- **TypeScript `private`** — compile-time only. Runtime is still public. Don't rely on it for actual privacy.

When to still use IIFE in 2025+:

- Plain `<script>` tags in old-school HTML, no bundler.
- Plugins that must register on a global namespace without polluting it.
- Quick one-file demos.
- Codebases that haven't migrated to ESM yet.

---

## 12. How to think aloud in the interview

> "Module pattern: wrap state and helpers in an IIFE, return only the public API. The IIFE runs once and its scope becomes the closure for the returned methods — they can read and mutate private state forever, but no external reference exists to that scope. Singleton by construction; for per-instance state, drop the IIFE and use a factory function. Add `'use strict'` to avoid `this === globalThis`. Modern replacements: ES modules give you file-scope privacy for free; class `#fields` give true syntactic privacy with `instanceof` and inheritance. I'd reach for the IIFE only for plain-script-tag environments or plugin-on-global-namespace patterns; everywhere else, ESM + class is cleaner."

---

## 13. 60-second revision

> - **Pattern:** `const M = (function () { let priv; ... return { publicMethod }; })();`
> - IIFE runs **once**; its LE becomes the closure for returned methods.
> - **Privacy:** binding name is invisible from outside — stronger than `_`-convention, equivalent to `#fields`.
> - **Singleton** by construction. For per-instance state, use a **factory function** (no immediate invocation).
> - **`'use strict'`** inside to avoid `this === globalThis`.
> - **Modern replacements:** ES modules (file-scope private), class `#fields` (instance-scope private).
> - **Symbol-keyed properties are not private** — `Reflect.ownKeys` sees them.
> - **Family:** factory functions, jQuery internals, plugin patterns, Counter II, Pub/Sub.
> - **Trap:** missing `()`, declaring state outside the IIFE, using singleton when you need instances.

---

**Related:** [counter-ii.md](./counter-ii.md) · [private-data-counter.md](./private-data-counter.md) · [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md) · [factory-with-injected-deps.md](./factory-with-injected-deps.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
