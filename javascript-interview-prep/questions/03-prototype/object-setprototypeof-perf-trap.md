# `Object.setPrototypeOf` — The Performance Trap

## Source / Origin
- V8 perf engineering notes; "tips for high-perf JS."
- Asked at: Razorpay, Cloudflare, Atlassian.
- Concept reference: `concepts/prototype.md`.

## Why this question matters in interviews
Changing an object's prototype at runtime *invalidates V8's hidden-class optimizations* for that object — sometimes catastrophically. The MDN docs literally say "consider this a slow operation." Senior bar: you know why (inline caches), when it's still fine (init time, low-frequency), and the alternatives (`Object.create`, `Reflect.construct`).

## Concepts involved

### Syntax to lock in
```js
const proto = { greet() { return 'hi'; } };
const obj = {};

Object.setPrototypeOf(obj, proto);      // change [[Prototype]] at runtime
obj.greet();                            // 'hi'

// Preferred at create time
const fast = Object.create(proto);
fast.greet();                           // 'hi'
```

### Edge cases / traps
1. **Hidden class invalidation.** V8 tracks objects by shape (hidden class). Changing the prototype mutates the shape; every previously-compiled inline cache becomes stale.
2. **`__proto__` setter** — `obj.__proto__ = proto` does the same thing (and is deprecated for the same reason).
3. **`Object.create(proto)` is fast.** It allocates with the correct prototype, no shape change.
4. **Reflect.setPrototypeOf** — same as `Object.setPrototypeOf`, with a Boolean return.
5. **Frozen objects** — `Object.setPrototypeOf` on a frozen object throws (or returns false in non-strict).
6. **Cycles** — JS catches them: `Object.setPrototypeOf(a, b); Object.setPrototypeOf(b, a)` throws.
7. **`null` prototype** — `Object.setPrototypeOf(obj, null)` makes it dictionary-like (no Object.prototype methods).
8. **Edge case mentioned in V8 blogs**: changing prototype of an array can demote it to dictionary mode.

## Mental Model

```
   V8 hidden classes:
     obj1: shape A → optimized accesses based on shape A
     obj2: shape A → shares inline caches with obj1

   setPrototypeOf(obj1, newProto):
     obj1: new shape A' (different prototype)
     V8 invalidates all previously-compiled inline caches that assumed shape A
     obj1's accesses now slow until V8 re-optimizes
     other shape-A objects are also affected if shapes are tracked transitively
```

```
   Object.create(proto):                  Object.setPrototypeOf(obj, proto):
   ┌────────────────────┐                  ┌─────────────────────────────┐
   │ alloc new obj      │                  │ allocate new shape          │
   │ shape pre-set      │                  │ migrate obj                 │
   │ inline caches OK   │                  │ invalidate caches           │
   │ fast path          │                  │ subsequent access slow      │
   └────────────────────┘                  └─────────────────────────────┘
```

## Why interviewers care

- **Perf intuition** — knowing the hidden-class concept signals depth.
- **Modern-engine awareness.**
- **API alternatives** — `Object.create` for the same effect, fast.

## Common confusion

- **"`__proto__ =` is fine."** Same perf hit, just deprecated syntax.
- **"It's only theoretical."** Measurable in microbenchmarks; rare in real apps unless used in a hot loop.
- **"All shape changes are bad."** Only structural ones; adding properties is also a shape change but is amortized (V8 transitions).
- **"Frozen prototype isn't allowed."** Frozen *object* can't have prototype changed; frozen *prototype* is fine.

## Brute force

Just `Object.setPrototypeOf(obj, proto)` in every hot path. Hopefully the GC or JIT keeps up. (It won't.)

## Optimal approach

Create objects with the right prototype from the start: `Object.create(proto)` or `class extends`.

## Solution

```js
// SLOW pattern — avoid in hot path
function makeUser(name) {
  const obj = {};
  Object.setPrototypeOf(obj, UserProto);   // hidden-class deopt
  obj.name = name;
  return obj;
}

// FAST equivalent
function makeUser(name) {
  const obj = Object.create(UserProto);    // correct prototype at allocation
  obj.name = name;
  return obj;
}

// FASTEST equivalent — V8 loves classes
class User { constructor(name) { this.name = name; } }
function makeUser(name) { return new User(name); }

// Legitimate setPrototypeOf — one-shot at init
class MyError extends Error {
  constructor(msg) {
    super(msg);
    Object.setPrototypeOf(this, new.target.prototype);   // fix transpiled-Babel chain
    this.name = new.target.name;
  }
}
// Happens once per Error instantiation; perf hit acceptable.

// Microbench (illustrative)
function bench(fn, iters = 1e6) {
  const start = performance.now();
  for (let i = 0; i < iters; i++) fn(i);
  return performance.now() - start;
}
bench(i => Object.create({})) ;          // fast
bench(i => Object.setPrototypeOf({}, {})); // slow
```

## Dry run

V8's perspective:

```
shape A: {} with [[Prototype]] = Object.prototype
obj = {}; obj has shape A

setPrototypeOf(obj, newProto):
  V8 must create shape A' for obj (new prototype slot)
  obj transitions A → A'
  inline caches for "obj.method()" that assumed shape A → now stale
  next call to obj.method() recompiles
```

In a hot loop with 1M iterations, this means the inline cache thrashes — orders of magnitude slower than steady-state.

## How to think aloud

> "Changing an object's prototype at runtime invalidates V8 hidden classes — slow. Object.create(proto) gives the right prototype at allocation: fast. Classes are fastest. The one legit use of setPrototypeOf is at init time — once per object — like fixing Error subclasses in transpiled code. In a hot path: never. Either build with the right shape from the start or restructure."

## Important takeaways

- **`Object.setPrototypeOf` invalidates hidden classes** — slow.
- **`Object.create(proto)`** for the same effect at allocation — fast.
- **Classes (`new C()`) are fastest** — V8 optimizes them aggressively.
- **`__proto__ =` is the same trap.**
- **One-shot init is OK** (Error subclass fix); hot path is not.

## Variants

- **`Object.create(null)`** — null-prototype objects, useful as maps.
- **`Reflect.setPrototypeOf`** — same op, Boolean return.
- **`Reflect.construct(C, args, NT)`** — sets prototype at construction.
- **Class-extends rewrite** — eliminate dynamic prototype change.

## Revision notes

```
Object.setPrototypeOf(obj, newProto)
  invalidates V8 hidden class for obj
  slow in hot path

Object.create(proto)
  allocates with correct prototype
  fast

new C() / class extends
  fastest

RULE OF THUMB:
  set prototype at creation, never after
  exception: one-shot init (Error subclass fix in transpiled code)
  __proto__ = is the same trap (deprecated)

MEASURE if in doubt — V8 perf is empirical
```
