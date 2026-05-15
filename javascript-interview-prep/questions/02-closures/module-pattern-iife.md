# Revealing Module Pattern (IIFE) for private state

## Source
- Pre-ES6 JS pattern formalized by Douglas Crockford (2003) and Christian Heilmann (2007 "Revealing Module Pattern").
- Still asked in senior interviews to test closure depth and encapsulation history.

## Why this question matters in interviews
The Module Pattern is the **historical answer** to "JavaScript has no private fields." Interviewers ask it for two reasons: (1) to test whether you really understand closure-based encapsulation, and (2) to see if you know its modern replacements — ES6 `import`/`export` modules and class `#private` fields. A senior candidate doesn't just write the IIFE — they explain when to still use it (legacy bundlers, browser globals, plugin-style APIs) and when not to (modern Node, ES modules, TypeScript). It's the single best example of "closure as a privacy mechanism."

## Concepts involved

### Syntax to lock in
```js
const Counter = (function () {
  let count = 0;                     // PRIVATE — only the IIFE's closure sees it
  function increment() { count++; }
  function decrement() { count--; }
  function get() { return count; }
  return { increment, decrement, get };   // PUBLIC API
})();

Counter.increment();
Counter.get();        // 1
Counter.count;        // undefined — truly inaccessible
```

### Runtime / engine behavior
- The IIFE (Immediately-Invoked Function Expression) executes once. Its local scope becomes the closure record for the returned object's methods.
- `count` is on the heap, kept alive because `increment`/`decrement`/`get` reference it. There is no syntactic way to reach `count` from outside — no parent reference, no symbol table access.
- The **revealing** twist: define all functions inside the IIFE, then expose them via the returned object. The functions internally call by name (`count++`), not via the public object — so even if the consumer monkey-patches the public method, the private state still works correctly.
- Pre-ES6: this was the only way to get private state. Post-ES6: ES modules + `#private` fields cover 99% of the use cases.

### Edge cases / discussion points
1. **Singleton by construction** — IIFE runs once → one shared `count` for every consumer. For per-instance privacy, return a **factory** (no IIFE) and call it per instance.
2. **`this` is `globalThis`** inside a non-strict IIFE. Use `'use strict'` at the top of the IIFE body.
3. **Memory** — the closure pins `count` forever. The IIFE result lives as long as the module reference does (usually forever).
4. **Imports/exports replace it** — ES modules give you per-file private scope for free; `export` is the new "return the public API."
5. **`#private` class fields (ES2022)** — true hard privacy for classes; no closure tricks needed. Use these in modern code.
6. **Symbol "privacy" is fake** — `Symbol`-keyed properties show up in `Reflect.ownKeys`. Not actually private. Closures and `#fields` are the real options.
7. **Testability** — fully private state means you can't poke it from tests. Sometimes intentional, sometimes a pain. Discuss.

## Brute force approach
"Use a leading-underscore convention like `_count`" — purely a naming convention, anyone can read or write it. Fails the privacy test. Closures (IIFE) or `#private` fields are the only real answers.

## Optimal approach
Wrap state and operations in an IIFE; return only the methods you want public. The state never escapes — closures provide hard encapsulation. For modern JS, prefer ES modules + class `#fields`, and mention this in your answer to show you know the history.

## Solution (JavaScript)

```js
// Singleton — IIFE creates one shared instance
const RateLimiter = (function () {
  'use strict';

  // ----- PRIVATE STATE (in closure) -----
  const buckets = new Map();          // key -> { tokens, lastRefill }
  const CAPACITY = 10;
  const REFILL_PER_MS = 0.01;

  function refill(bucket) {
    const now = Date.now();
    const elapsed = now - bucket.lastRefill;
    bucket.tokens = Math.min(CAPACITY, bucket.tokens + elapsed * REFILL_PER_MS);
    bucket.lastRefill = now;
  }

  // ----- PUBLIC API -----
  function tryConsume(key) {
    if (!buckets.has(key)) buckets.set(key, { tokens: CAPACITY, lastRefill: Date.now() });
    const bucket = buckets.get(key);
    refill(bucket);
    if (bucket.tokens < 1) return false;
    bucket.tokens -= 1;
    return true;
  }

  function reset(key) { buckets.delete(key); }

  // Reveal only what callers should see
  return { tryConsume, reset };
})();

// Factory variant — one instance per call (per-tenant rate-limiter)
function createRateLimiter(capacity = 10, refillPerMs = 0.01) {
  const buckets = new Map();
  // ... same body, parameterized ...
  return {
    tryConsume(key) { /* ... */ },
    reset(key) { /* ... */ },
  };
}
```

## Step-by-step dry run

Input:
```js
console.log(RateLimiter.tryConsume('user-1'));  // true (10 tokens → 9)
console.log(RateLimiter.tryConsume('user-1'));  // true (9 → 8)
console.log(RateLimiter.buckets);               // undefined — truly private
console.log(Object.keys(RateLimiter));          // ['tryConsume', 'reset']
```

Trace:
- IIFE runs **once** at definition. `buckets`, `CAPACITY`, `REFILL_PER_MS`, `refill` all become heap-resident closure variables. The returned object `{tryConsume, reset}` is what's bound to `RateLimiter`.
- `RateLimiter.tryConsume('user-1')`: the inner function looks up `buckets` via its closure scope chain — finds the IIFE's variable record. Adds `'user-1' -> { tokens: 10, ... }`. Refills (no-op, just created). Tokens become 9. Returns `true`.
- `RateLimiter.tryConsume('user-1')`: same closure, same `buckets`. Tokens go 9 → 8. Returns `true`.
- `RateLimiter.buckets`: there's no such property on the returned object — only `tryConsume` and `reset` are exposed. `undefined`.
- `Object.keys(RateLimiter)`: `['tryConsume', 'reset']`. The closure is genuinely opaque to reflection.

What's on the heap: the IIFE's variable environment (`buckets`, `CAPACITY`, `refill`, ...) is kept alive because the returned methods reference it. As long as `RateLimiter` is reachable, all private state lives.

## Important takeaways

**Syntax to memorize**
- Wrap in `(function () { ... })()` to invoke immediately.
- Declare private state with `let`/`const` **inside** the IIFE.
- `return { method1, method2, ... }` — only what you want public.
- Start with `'use strict'` to avoid `globalThis` `this` leaks.

**Patterns to reuse**
- Module pattern = closure-based privacy. Use it for browser globals (no bundler), plugin APIs, jQuery-style libraries.
- Factory function = per-instance module pattern. Drop the IIFE, just call the function multiple times.
- The "reveal" idiom (define then return an object) makes the public API a one-glance read at the bottom of the file.

**Modern replacements** (mention these unprompted to score senior points)
- **ES modules** — every `import`/`export` file is already a module with private top-level scope. No IIFE needed.
- **Class `#private` fields (ES2022)** — true syntactic privacy; faster than closures (engines can optimize hidden classes). Use for OO-shaped data.
- **TypeScript `private`** — compile-time only; runtime is still public. Mention as a *non*-answer for true privacy.

**Common mistakes**
- Forgetting the trailing `()` — you've assigned a function, not its result.
- Returning a method that closes over `this` from inside the IIFE — `this` is `globalThis` (sloppy) or `undefined` (strict).
- Using the module pattern in modern Node code — code-review smell; use ES modules.
- Confusing **singleton IIFE** with **factory function** — they look similar but produce different sharing semantics.

**Related questions**
- Class `#private` fields — when to use which
- Factory functions vs constructors vs classes
- `once(fn)` — single-slot privacy
- Counter with private state (closure-based)

## Variants

1. **Factory module pattern** — drop the immediate invocation, return the factory. Each call creates an independent instance with its own private state. Useful for per-request scoped state.

2. **Augmenting module pattern** — pass the existing module into a new IIFE and add methods: `MyMod = (function (mod) { mod.extra = ...; return mod; })(MyMod || {})`. Pre-bundler way of doing namespace extension across files.

3. **Module pattern with imports** — pass dependencies (`window`, `jQuery`, etc.) as IIFE arguments. Makes dependencies explicit and minifies well: `(function ($, win) { ... })(jQuery, window)`.

## Revision notes

> **module-pattern-iife — 60 second recap**
> - IIFE = `(function () { ... })()`. Runs once; its scope becomes the closure for the returned methods.
> - **Private state** lives in the IIFE; **public API** is the returned object.
> - Closure-based privacy is hard privacy — no reflection escape.
> - Singleton by default. For per-instance state, use a **factory function** (no IIFE).
> - Modern replacements: ES modules (file-scope privacy) + class `#private` fields (instance privacy).
> - Symbol-keyed properties are NOT private (`Reflect.ownKeys` sees them).
> - Use `'use strict'` inside the IIFE to avoid `this === globalThis`.
> - Heap: closure record is pinned for the lifetime of the returned object.
> - **Trap:** forgetting `()` invocation; using IIFE in modern Node where ES modules already give file-scoped privacy.
