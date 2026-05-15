# The `this` Keyword in JavaScript (and Node.js)

## Source
- codedamn "Exploring `this` keyword in Node.js": https://codedamn.com/news/nodejs/javascript-this-keyword
- Universal first-round interview question. Asked verbatim at Atlassian, Stripe, Razorpay, Microsoft, and any callback-heavy Node codebase.

## Why this question matters in interviews
`this` is the **most error-prone primitive in JavaScript**, and interviewers know it. You will be handed a snippet, asked "what does this print?", and the wrong answer ends the round. Worse, Node has its own quirks that desktop-JS tutorials skip: `this` at the top level of a CommonJS module is `module.exports`, not `globalThis`; ESM modules make it `undefined`; arrow functions inside `EventEmitter` handlers behave totally differently from `function` handlers. As a backend engineer you'll lose hours to this on real bugs — express middleware, mongoose hooks, EventEmitter listeners, class-based services with passed-as-callback methods. Mastery here pays back forever.

## Concepts involved

### The 5 rules of `this` (memorize in this order — interviewers ask in this order)
1. **Default binding** — bare function call. `this` = `globalThis` in sloppy mode, `undefined` in strict mode and inside ES modules.
2. **Implicit binding** — method-style call `obj.fn()`. `this` = `obj` (the receiver immediately left of the dot).
3. **Explicit binding** — `fn.call(ctx, ...)`, `fn.apply(ctx, args)`, `fn.bind(ctx)(...)`. `this` = `ctx`. **Strongest** of the three so far.
4. **`new` binding** — `new Fn()`. `this` = a brand-new object whose prototype is `Fn.prototype`. Even **beats** `bind`'s `this` (a bound function called with `new` ignores the bound `this`).
5. **Arrow functions** — no `this` of their own. They **inherit `this` lexically** from the enclosing function/scope at *definition* time. `call`/`apply`/`bind` cannot change it.

Precedence (highest → lowest): **arrow's lexical `this` > new > bind > call/apply > implicit > default.**

### Syntax to lock in
```js
'use strict';
function show() { console.log(this); }

show();                       // undefined  (strict default)
const obj = { show };
obj.show();                   // obj         (implicit)
show.call({ x: 1 });          // { x: 1 }    (explicit)
new show();                   // a fresh {}  (new wins)

const arrow = () => console.log(this);
arrow();                      // whatever `this` was in the enclosing scope
```

### Runtime / engine behavior — Node-specific gotchas
- **CommonJS module top-level** (`.js` file required via `require`):
  - `this` at the top scope **`===` `module.exports`**, NOT `globalThis`. Each module is wrapped in `(function (exports, require, module, __filename, __dirname) { ... })`. The wrapper is called with `this = module.exports`.
- **ES Module top-level** (`.mjs` or `"type":"module"`):
  - `this` is `undefined` at the top level. Different from CommonJS.
- **Inside a regular function declared at the top of a CJS module**, calling it bare: `this === globalThis` in sloppy mode, `undefined` in strict. (Even though the *module top* `this` was `module.exports`.)
- **`setTimeout` / `setInterval` callbacks** — Node passes `Timeout` object or `undefined` as `this` depending on strictness. Use arrow functions or `bind` to fix.
- **EventEmitter listeners** — `emitter.on('x', function(){ /* this === emitter */ })`. With an arrow listener, `this` is whatever surrounded the arrow's *definition*, often not the emitter.
- **Class methods passed as callbacks lose `this`** — `app.get('/x', svc.handler)` — inside `handler`, `this` is `undefined`. Pass `svc.handler.bind(svc)` or `(req,res)=>svc.handler(req,res)`.

### Edge cases (interview traps)
1. **Method ripped off the object** — `const f = obj.method; f();` → default binding, NOT `obj`. The receiver-on-the-dot is what counts; assignment discards it.
2. **Chained property access** — `a.b.c()` → `this === a.b`, not `a`. Only the last receiver counts.
3. **`forEach`'s second arg** — `[1].forEach(fn, ctx)` → `this` inside `fn` is `ctx` (rule: many higher-order methods accept a `thisArg`). Arrow functions ignore it.
4. **`bind` is permanent and stacked** — `f.bind(A).bind(B)` → `this === A`. First `bind` wins; subsequent binds on already-bound functions don't override.
5. **`new` with a bound function** — bound `this` is **ignored**; the freshly created object is `this`. (See polyfill-bind problem.)
6. **Strict vs sloppy** — sloppy default binding gives `globalThis`; strict gives `undefined`. ES modules are strict by default.
7. **Object literal shorthand methods vs arrow properties** — `{ fn() {} }` is a normal method (gets its own `this`); `{ fn: () => {} }` is an arrow (lexical `this` from outside the object literal — usually `globalThis` or `undefined`).
8. **Class field arrow** — `class A { f = () => this }` — `this` is the *instance*, locked at construction. This is the modern "auto-bind" pattern for React/express handlers.

## Brute force approach
"I'll just assign `const self = this;` everywhere." This works but signals you don't know the modern alternatives. In 2026 the answer is: **arrow functions for callbacks** (rule 5), **explicit `.bind`** when you need a callable, **class fields with arrows** when you pass methods as handlers.

## Optimal approach
Match the situation to one of the 5 rules:
- Need `this` to flow from the calling site? Use `function`.
- Need `this` to be captured from the *enclosing* scope? Use arrow.
- Passing a method as a callback? Use `.bind(this)` or wrap in arrow `() => obj.method()` or use class-field-arrow syntax.
- Implementing a class? Use `class`, and never assume external callers will preserve `this`.

## Solution (JavaScript)

A single annotated example covering all 5 rules:

```js
'use strict';

// ── RULE 5: lexical (arrow) — `this` from definition site ──────────────
const lexical = () => this;

// ── RULE 1: default ────────────────────────────────────────────────────
function defaultThis() { return this; }
defaultThis();                              // undefined  (strict)

// ── RULE 2: implicit ───────────────────────────────────────────────────
const obj = {
  name: 'obj',
  who() { return this; },                   // method shorthand → own `this`
  whoArrow: () => this,                      // arrow → lexical (outer scope)
};
obj.who();                                  // obj
obj.whoArrow();                             // outer-scope this (likely module.exports in CJS, undefined in ESM)

// ── method ripped off, default kicks in ────────────────────────────────
const ripped = obj.who;
ripped();                                   // undefined — receiver lost

// ── RULE 3: explicit ───────────────────────────────────────────────────
obj.who.call({ name: 'explicit' });         // { name: 'explicit' }
const bound = obj.who.bind({ name: 'bound' });
bound();                                    // { name: 'bound' }
bound.call({ name: 'tryAgain' });           // STILL { name: 'bound' } — bind is sticky

// ── RULE 4: new beats bind ─────────────────────────────────────────────
function Person(name) { this.name = name; }
const BoundPerson = Person.bind({ name: 'ignored' });
const p = new BoundPerson('Alice');
p.name;                                     // 'Alice' — `new` ignored the bound `this`

// ── class field arrow — modern auto-bind pattern ───────────────────────
class Service {
  prefix = '[svc]';
  handle = (msg) => `${this.prefix} ${msg}`;  // `this` locked to instance
}
const s = new Service();
const detached = s.handle;                  // no .bind needed
detached('hello');                          // '[svc] hello'
```

## Step-by-step dry run

The classic interview snippet:

```js
'use strict';
const user = {
  name: 'Ada',
  greetSync()  { return this.name; },
  greetArrow:  () => this?.name,
  greetTimer() { setTimeout(function () { console.log(this); }, 0); },
  greetTimerArrow() { setTimeout(() => console.log(this.name), 0); },
};

user.greetSync();                       // ?
user.greetArrow();                      // ?
const f = user.greetSync; f();          // ?
user.greetTimer();                      // (after 0ms) ?
user.greetTimerArrow();                 // (after 0ms) ?
```

Trace:

1. **`user.greetSync()`** — implicit binding. `this === user`. Returns `'Ada'`.
2. **`user.greetArrow()`** — arrow, lexical `this`. The arrow was defined at the top level of an ES-module-ish strict context → `this` is `undefined`. `undefined?.name` short-circuits → `undefined`.
3. **`const f = user.greetSync; f();`** — receiver lost on assignment. Bare call → default binding → strict → `this === undefined`. Accessing `.name` throws `TypeError: Cannot read properties of undefined`.
4. **`user.greetTimer()`** — inside, `setTimeout` is given a *regular* `function`. The timer system calls it bare → strict default → `this === undefined`. Prints `undefined`.
5. **`user.greetTimerArrow()`** — inner arrow's `this` is locked to *the surrounding method's* `this`, which (because we called `user.greetTimerArrow()`) is `user`. Prints `'Ada'`.

Rule 5 is what makes arrows so popular inside `setTimeout`, promise `.then`, and event handlers: they pick up the surrounding method's `this` for free.

## Important takeaways

**Syntax to memorize**
- Default (strict) → `undefined`; (sloppy) → `globalThis`.
- Implicit → the receiver on the dot.
- Explicit → `call`/`apply`/`bind`.
- `new` → fresh object, wins over `bind`.
- Arrow → lexical, immutable, ignores all three explicit setters.

**Patterns to reuse**
- Class fields with arrow methods → auto-bound handlers, drop the `.bind(this)` in constructors. Modern preferred form.
- Arrow inside `setTimeout` / `.then` / event handlers → captures the outer method's `this` without effort.
- Save `const self = this` only in legacy callbacks that *must* be `function` declarations.

**Common mistakes**
- Passing `obj.method` directly to `app.get`, `array.map`, `emitter.on`, `setTimeout` and expecting `this === obj`. It won't be. Use `bind`, arrow wrapper, or class-field arrow.
- Putting an arrow inside an object literal expecting `this` to be the object. Arrows ignore implicit binding — `this` will be the *outer* scope of the literal.
- Forgetting CJS top-level `this === module.exports` quirk; trying to "patch" `globalThis` and watching it go nowhere.
- Believing `bind` can be overridden by a second `bind` or by `call`. It can't.

**Why interviewers ask this**
- Predict-the-output snippets are the cheapest filter for "do you actually know JS or just enough to copy-paste from Stack Overflow?"

## Variants

1. **What does `this` print at the top level of a Node CJS file vs a Node ESM file vs a browser script vs a browser module?**
   - CJS: `module.exports`. ESM: `undefined`. Browser script: `window`. Browser module: `undefined`.
2. **`new` with a bound function** — show that `Person.bind({}).call({}); new (Person.bind({}))` produces different `this`. Tests rule precedence directly.
3. **`Array.prototype.forEach(fn, thisArg)`** — implement the second argument; show how it interacts with arrow callbacks (they ignore it).
4. **Class method autobinding** — convert a "broken" `class Svc { handle(req) { return this.cfg; } }` (passed as `app.get('/', svc.handle)`) into a working version via `bind`, arrow class field, or wrapper.
5. **Implement `bind` / `call` / `new`** — see the dedicated polyfill problems in this folder.

## Revision notes

> **`this` — 60 second recap**
> - 5 rules, in precedence order: arrow (lexical, immutable) > new > bind > call/apply > implicit (`obj.fn()`) > default (`undefined` strict / global sloppy).
> - "Receiver on the dot" wins: `a.b.c()` → `this = a.b`.
> - Detaching a method (`const f = obj.fn`) **loses** the receiver → default binding.
> - `bind` is sticky: second `bind` and later `call`s can't override.
> - `new BoundFn()` **ignores** the bound `this` — fresh instance is `this`.
> - Arrow functions: zero own `this`; they snapshot the surrounding scope at definition time.
> - Node CJS module top-level: `this === module.exports`. ESM top-level: `undefined`.
> - Use arrow callbacks inside methods to keep `this` flowing through `setTimeout`/`.then`.
> - Class-field arrow (`handle = () => this.x`) is the modern auto-bind pattern.
> - **Trap:** `setTimeout(function() { this.foo })` — `this` is `undefined`/global, not the enclosing object.
> - **Trap:** `{ name: 'x', greet: () => this.name }` — arrow grabs outer `this`, not the literal.
