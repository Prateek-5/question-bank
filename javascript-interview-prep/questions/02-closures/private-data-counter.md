# Encapsulating Private Data via Closures (`createCounter` module pattern)

## Source
- https://codedamn.com/news/nodejs/encapsulating-private-data-closures

## Why this question matters in interviews
This is the conceptual sibling of Counter II, but framed as an **encapsulation / OOP** question rather than a coding puzzle. Interviewers ask this when they want to test whether you understand **why** closures matter at the architecture level: how do you build a stateful object whose internals are truly unreachable from outside? Pre-ES6, this was the *only* way to get private fields in JavaScript — the "revealing module pattern" powered jQuery, Backbone, RequireJS, and 90% of npm modules before classes. Even today, in Node.js codebases, you'll see closure-based modules for: connection-pool handles, rate-limiter state, session stores, cache layers, plugin sandboxes. As a backend engineer, knowing when to reach for a closure vs a class vs a `#field` signals seniority.

## Concepts involved

### Syntax to lock in
```js
function createCounter() {
  let count = 0; // PRIVATE — accessible only via the returned methods
  return {
    increment() { count += 1; },
    decrement() { count -= 1; },
    getValue()  { return count; },
  };
}

const c = createCounter();
c.increment();
c.increment();
c.getValue();    // 2
c.count;         // undefined — no public field, no way in
```

### Lexical environment / why this is private
- `createCounter()` allocates LE_outer = `{ count: 0 }` on the call stack, then heap-promotes it because the returned methods reference it.
- The three methods are independent function objects whose `[[Environment]]` slot points at LE_outer.
- `count` exists **only** as a binding in LE_outer. There is no `this.count`, no property descriptor, no proxy hook, no `Object.getOwnPropertyNames` entry, no Reflect-readable handle. The variable is **literally unreachable** without going through one of the three returned methods.
- This is stronger than `class { _count }` (convention, not enforcement), as strong as `class { #count }` (true private fields, ES2022+), and works in any JS environment older than 2022.

### Closure vs class field comparison

| Aspect | Closure | `class { #field }` | `class { _field }` |
|---|---|---|---|
| Privacy | Hard (no reflective access) | Hard (no reflective access) | Soft (convention only) |
| Available since | Always | ES2022 | Always |
| Memory per instance | One LE + 3 fn objects | Shared prototype + per-instance fields | Shared prototype + per-instance fields |
| `this` semantics | Not used | Standard | Standard |
| Destructure-safe | Yes | No (loses `this`) | No |
| `instanceof` checks | No | Yes | Yes |
| Inheritance | Awkward | Standard `extends` | Standard `extends` |
| Serialization to JSON | Methods skipped, `count` invisible | `#count` invisible | `_count` serialized |

When to pick closure: small handle-style objects, no inheritance, you want destructuring to be safe.
When to pick `#field` class: hierarchies, `instanceof` checks, large method sets, IDE/type-system support.

### Memory: the closure leak risk
- The returned methods *retain* LE_outer, which holds `count` **and** any other locals you declared in `createCounter` even if those locals aren't read by the methods. V8 is smart enough to drop *truly* unreferenced bindings via escape analysis, but it's not always perfect — sometimes a giant local stays alive because *some* nested function lexically references it.
- Worst case: you create a closure that captures a 50MB array "for now" and stash the returned methods in a long-lived `EventEmitter`. The 50MB array can't be GC'd until every listener is removed.
- Mitigations: keep closure scopes minimal, null out heavy locals before returning, prefer `WeakMap`-keyed state for objects that may outlive their referent.

### Edge cases / interview traps
1. **`this` doesn't appear** — methods don't use `this`, so destructuring (`const { increment } = createCounter(); increment();`) is safe. Compare to class methods, where destructuring breaks `this`.
2. **Can I expose `count` via a getter?** — Sure: `return { get value() { return count; }, ... }`. Still read-only from outside. Don't accidentally expose a setter.
3. **`JSON.stringify(c)`** — returns `"{}"` because methods are skipped and `count` is invisible. If serialization matters, add a `toJSON()` method.
4. **Hot path performance** — each `createCounter()` call allocates fresh function objects (one per method). With a class, methods live on the prototype and are shared. If you make a million counters, the class wins on memory; for ≤1000 instances, no measurable difference.
5. **`instanceof` doesn't work** — closures aren't constructors. If callers need `instanceof Counter`, you need a class (or a tag-on-the-object workaround).

## Brute force approach
Public field on a plain object:
```js
function createCounter() {
  const obj = { count: 0 };
  obj.increment = () => obj.count++;
  return obj;
}
```
`count` is now mutable from outside — `c.count = 999`. No encapsulation. **This is what the question is explicitly asking you not to do.**

## Optimal approach
Outer function declares a local `count`. Returns an object literal with method shorthands; each method closes over `count`. No `this`. State is unreachable from outside; methods are destructure-safe.

## Solution (JavaScript)

```js
function createCounter() {
  let count = 0;
  return {
    increment() { count += 1; },
    decrement() { count -= 1; },
    getValue()  { return count; },
    reset()     { count = 0; },
  };
}

// Usage
const c = createCounter();
c.increment();
c.increment();
c.increment();
console.log(c.getValue()); // 3
c.decrement();
console.log(c.getValue()); // 2
c.reset();
console.log(c.getValue()); // 0

// Privacy proof:
console.log(c.count);                       // undefined
console.log(Object.keys(c));                // ["increment","decrement","getValue","reset"]
console.log(Object.getOwnPropertyNames(c)); // same — no "count"
```

## Step-by-step dry run

Input:
```js
const a = createCounter();
const b = createCounter();
a.increment();
a.increment();
b.increment();
console.log(a.getValue(), b.getValue()); // expect 2 1
```

Trace:
1. `createCounter()` call #1.
   - LE_A created on heap: `{ count: 0 }`. Methods bind to LE_A.
   - Returned object → `a`.
2. `createCounter()` call #2.
   - LE_B created on heap: `{ count: 0 }`. New independent LE. New method function objects bind to LE_B.
   - Returned object → `b`. **`a` and `b` share nothing.**
3. `a.increment()` → looks up `count` via scope chain in `LE_A` → `0 → 1`.
4. `a.increment()` → LE_A.count: `1 → 2`.
5. `b.increment()` → LE_B.count: `0 → 1`.
6. `a.getValue()` reads LE_A.count → `2`. `b.getValue()` reads LE_B.count → `1`. Logged: `2 1`.

Two LEs, two `count` slots, zero cross-contamination. Each closure is its own isolated mini-module.

## Important takeaways

**Syntax to memorize**
- `function createX() { let state = ...; return { methodA(){}, methodB(){} }; }`.
- This is the **revealing module pattern** — name it explicitly in the interview.

**Patterns to reuse**
- Anywhere you'd reach for `class { #field }` but want pre-ES2022 compatibility or destructure-safe methods.
- Microservices "handle" objects: DB pool wrappers, redis client wrappers, feature-flag clients.
- Plugin sandboxes — give plugins a closure-scoped API surface they can't bypass.
- Singletons where you want a clear "module returned a configured handle" feel.

**Common mistakes**
- Declaring `count` as a property of the returned object (`return { count: 0, ... }`) — destroys privacy.
- Putting `let count` *inside* one of the methods — each method gets its own counter; mutations don't share.
- Adding a setter on `value` "for convenience" — you've just leaked the private.
- Holding the closure forever inside a long-lived event listener — memory leak.

**Related questions**
- Counter II (same pattern, leetcode framing)
- Event Emitter (closure over `listeners` map)
- LRU Cache (closure over `Map`)
- Pub/Sub (closure over subscriber list)

## Variants

1. **Add subscriptions / observers** — `subscribe(fn)` registers a listener, every mutation fires all listeners. Closure now captures `count` *and* a `listeners` array. Pure module pattern at full size.

2. **Closure vs `class { #count }` rewrite** — interviewer asks "now rewrite with ES2022 private fields." Be ready to write both and compare: privacy is identical, but the closure version is destructure-safe; the class version is `instanceof`-able and inheritance-friendly.

3. **`WeakMap`-backed privacy** — alternative to closures for class-like patterns: `const _state = new WeakMap();` keyed by `this`. Useful when you want class ergonomics + true privacy without `#fields`. Mention it for senior-engineer signal.

## Revision notes

> **private state via closure — 60 second recap**
> - **Pattern:** outer function declares `let state = ...`; returns object of methods; all methods close over the same LE.
> - **Privacy:** `state` is unreachable from outside — no reflection, no enumeration, no property descriptor. As strong as `#field`, predates it by 20 years.
> - **No `this`:** methods read state via scope chain, so destructuring is safe.
> - **Two factory calls = two LEs = two independent instances.**
> - **Memory:** closures retain everything in their LE; long-lived closures over heavy data = leak risk. Keep scopes lean.
> - **vs class `#field`:** closure is destructure-safe, `#field` is `instanceof`-able and inheritance-friendly.
> - **Trap:** putting state as a property of the returned object leaks it.
> - Family: Counter II, Event Emitter, LRU Cache, plugin sandboxes — all revealing-module pattern.
