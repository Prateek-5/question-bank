# The `this` keyword — 5 rules

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md)
>
> **Source:** Universal first-round JS interview question. Atlassian, Stripe, Razorpay, Microsoft.

---

## 1. Problem statement

Predict `this` in any callsite. The five rules in precedence order.

**Verification examples**

| Callsite                                  | `this`                                              |
|-------------------------------------------|------------------------------------------------------|
| `fn()` (bare, strict)                      | `undefined`                                          |
| `fn()` (bare, sloppy)                      | `globalThis`                                          |
| `obj.fn()` (implicit)                      | `obj`                                                |
| `fn.call(ctx)` / `fn.apply(ctx)`           | `ctx`                                                |
| `fn.bind(ctx)()` (then any call)           | `ctx` (sticky)                                       |
| `new fn()`                                 | fresh object whose proto is `fn.prototype`           |
| `new (fn.bind(ctx))()`                     | fresh object — bound `ctx` IGNORED                   |
| Arrow function                              | lexical (captured from enclosing scope)             |

**Constraints**
- Precedence (high → low): **arrow > new > bind > call/apply > implicit > default**.
- Arrows have NO own `this`.
- Bound functions called with `new` use fresh `this`, not bound `ctx`.
- CJS module-top `this === module.exports`; ESM top is `undefined`.

---

## 2. Plain-English restatement

`this` depends on HOW the function is called, not where it's defined — except for arrow functions, which capture `this` lexically and can never be re-bound. Five rules in precedence order: arrow lexical > new > bind > call/apply > implicit (`obj.fn()`) > default (`undefined`/`globalThis`).

---

## 3. Why this matters in interviews

Most error-prone primitive in JS. Predict-the-output puzzles are a fast filter.

---

## 4. Mental model

```
   5 rules in precedence (HIGH → LOW):
   
   1. Arrow function: lexical — captured at definition time. IMMUTABLE.
                      Ignored by bind/call/apply.
   2. `new Fn()`:    fresh object whose [[Prototype]] = Fn.prototype.
                     OVERRIDES bound this.
   3. `fn.bind(ctx)`: sticky — second bind doesn't override; call/apply don't override.
   4. `fn.call(ctx)` / `fn.apply(ctx, args)`: explicit ctx.
   5. `obj.fn()`:   implicit — `this` = obj (receiver immediately left of dot).
   6. `fn()`:       default — strict: undefined; sloppy: globalThis.
   
   "Receiver on the dot" wins:
     a.b.c() → this = a.b (NOT a)
     const f = obj.fn; f() → this = default (receiver lost)

   Node-specific:
   - CJS module top: this === module.exports
   - ESM module top: this === undefined
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `const obj = { fn() { return this } }; const ref = obj.fn; ref()` — what's `this`?
> 2. `new (fn.bind(ctx))()` — what's `this` inside fn?
> 3. `const arrow = () => this; obj.method = arrow; obj.method()` — what's `this`?

---

## 6. Brute force — walked through

### Wrong attempt 1: "this is the object the function is on"
Wrong for arrows, detached methods, callbacks.

### Wrong attempt 2: "always assign `const self = this`"
Works but signals junior. Modern: arrow callbacks, class field arrows, bind.

### Wrong attempt 3: assume `setTimeout(obj.fn)` keeps `this = obj`
No — receiver lost on assignment.

---

## 7. The unlocking insight

> **`this` is set at the CALLSITE, not the definition site (except arrows — they capture lexically at definition). 5 rules in precedence: arrow > new > bind > call/apply > implicit > default. Receiver-on-the-dot determines implicit binding. Detaching loses the receiver.**

Three properties:

1. **Callsite-determined** (except arrows).
2. **Precedence order** — higher rules override lower.
3. **Arrows immutable** — no own `this`.

---

## 8. Solution (annotated)

```js
'use strict';

// Rule 1: default
function defaultThis() { return this; }
defaultThis();                                                          // undefined (strict)

// Rule 2: implicit
const obj = {
  name: 'obj',
  who() { return this; },                                               // own this
  whoArrow: () => this,                                                  // lexical (outer scope)
};
obj.who();                                                              // obj
obj.whoArrow();                                                         // outer-scope this

// Detached → default kicks in
const ripped = obj.who;
ripped();                                                                // undefined (receiver lost)

// Rule 3: explicit
obj.who.call({ name: 'explicit' });                                     // { name: 'explicit' }
const bound = obj.who.bind({ name: 'bound' });
bound();                                                                 // { name: 'bound' }
bound.call({ name: 'tryAgain' });                                       // STILL { name: 'bound' } (sticky)

// Rule 4: new beats bind
function Person(name) { this.name = name; }
const BoundPerson = Person.bind({ name: 'ignored' });
const p = new BoundPerson('Alice');
p.name;                                                                  // 'Alice' (new ignores bound ctx)

// Class field arrow — modern auto-bind
class Service {
  prefix = '[svc]';
  handle = (msg) => `${this.prefix} ${msg}`;                             // step 1: lock to instance
}
const s = new Service();
const detached = s.handle;
detached('hello');                                                       // '[svc] hello' (no .bind needed)
```

**Try it yourself**

```js
'use strict';
const user = {
  name: 'Ada',
  greetSync()       { return this.name; },
  greetArrow:       () => this?.name,                                    // arrow at object-literal level
  greetTimer()      { setTimeout(function () { console.log(this); }, 0); },
  greetTimerArrow() { setTimeout(() => console.log(this.name), 0); },
};

user.greetSync();                                                        // 'Ada' (implicit)
user.greetArrow();                                                       // undefined (lexical, outer = undefined in strict)
const f = user.greetSync; f();                                           // TypeError (this is undefined, .name throws)
user.greetTimer();                                                       // (later) undefined (timer cb bare-called in strict)
user.greetTimerArrow();                                                  // (later) 'Ada' (arrow captures method's this)
```

---

## 9. Step-by-step dry run

```
user.greetSync():
  callsite: obj.fn() → IMPLICIT binding.
  this = user. Return user.name = 'Ada'.

user.greetArrow():
  greetArrow is an arrow defined inside the object literal.
  Arrows capture `this` lexically at definition time.
  Outer scope at that line (module top, strict): this = undefined.
  Return undefined?.name = undefined.

const f = user.greetSync; f():
  Receiver lost on assignment to f.
  f() is bare call → DEFAULT binding.
  Strict mode: this = undefined.
  Return undefined.name → TypeError.

user.greetTimer():
  setTimeout(function() { console.log(this); }, 0):
    timer cb is a function expression.
    setTimeout invokes it bare → DEFAULT.
    Strict: this = undefined.
    Print undefined.

user.greetTimerArrow():
  setTimeout(() => console.log(this.name), 0):
    arrow inside greetTimerArrow.
    Captures greetTimerArrow's this = user.
    Print user.name = 'Ada'.
```

---

## 10. Common confusion + traps

1. **`obj.fn` passed as callback** — receiver lost; `this` is default.
2. **Arrow in object literal** — captures outer scope, NOT the object.
3. **Bind doesn't override** — sticky.
4. **`new` with bound function** — fresh `this`, bound ctx IGNORED.
5. **`setTimeout(function() {...})`** — bare call; `this` is default.
6. **`forEach(fn, thisArg)`** — second arg sets `this` (only for `function`, not arrow).
7. **Class method passed as callback** — loses `this`; use bind, arrow wrapper, or class-field arrow.

---

## 11. Senior follow-ups & variants

### Variant 1 — Module-top `this`
CJS: `this === module.exports`. ESM: `this === undefined`. Browser script: `window`. Browser module: `undefined`.

### Variant 2 — `Array.prototype.forEach(fn, thisArg)`
Second arg sets `this` for function callbacks; arrows ignore.

### Variant 3 — Class autobinding patterns
Class-field arrow > `bind` in constructor > wrapper in callsite.

### Variant 4 — Implement `bind`/`call`/`new`
Polyfills. See [polyfill-bind.md](./polyfill-bind.md), etc.

### Variant 5 — `Function.prototype.bind` precedence
`fn.bind(A).bind(B)` → `this = A`. First bind wins.

---

## 12. How to think aloud

> "5 rules in precedence (high to low): (1) arrow function — lexical capture at definition, IMMUTABLE, ignores bind/call/apply. (2) `new Fn()` — fresh `this` whose `[[Prototype]] = Fn.prototype`; OVERRIDES bound ctx. (3) `fn.bind(ctx)` — sticky, second bind doesn't override, call/apply don't override. (4) `fn.call(ctx)` / `fn.apply(ctx, args)` — explicit. (5) `obj.fn()` — implicit, `this` = receiver on the dot. (6) `fn()` bare — default; strict: undefined, sloppy: globalThis. 'Receiver-on-the-dot' wins for implicit. Detaching (`const f = obj.fn; f()`) LOSES the receiver — bare call, default binding. Arrow in setTimeout/Promise.then/event handlers captures method's `this` for free. Modern auto-bind: class field arrow `handle = () => this.x` locks `this` to instance. Node: CJS module-top `this === module.exports`; ESM is `undefined`. Trap: arrow in object literal grabs outer scope, not object; passing class method as callback loses `this`."

---

## 13. 60-second revision

> - **5 rules:** arrow > new > bind > call/apply > implicit > default.
> - **Arrow:** lexical, immutable. Ignores bind/call/apply.
> - **`new` beats bind:** fresh `this`; bound ctx ignored.
> - **Bind is sticky:** second bind, call, apply can't override.
> - **Implicit:** `obj.fn()` → `this = obj` (receiver on dot).
> - **Detaching loses receiver** → default binding.
> - **Default:** strict `undefined`, sloppy `globalThis`.
> - **Node CJS top:** `this === module.exports`. **ESM top:** `undefined`.
> - **Class field arrow** = modern auto-bind.
> - **Trap:** arrow in object literal; class method passed as callback; chained binds.

---

**Related:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [polyfill-bind.md](./polyfill-bind.md) · [polyfill-call-apply.md](./polyfill-call-apply.md) · [`10-machine-coding-patterns/bind-polyfill.md`](../10-machine-coding-patterns/bind-polyfill.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
