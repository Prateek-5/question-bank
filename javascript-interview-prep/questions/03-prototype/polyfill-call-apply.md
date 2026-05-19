# Polyfill `Function.prototype.call` and `.apply`

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [this-keyword-nodejs.md](./this-keyword-nodejs.md)
>
> **Source:** ECMA-262 §20.2.3.3. Razorpay, Walmart, Atlassian, Microsoft.

---

## 1. Problem statement

Polyfill `call` and `apply` — set `this` and invoke the function.

**Verification examples**

```js
fn.myCall(ctx, ...args);                    // ≡ fn.call(ctx, ...args)
fn.myApply(ctx, [args]);                     // ≡ fn.apply(ctx, [args])
```

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| `fn.myCall(obj, a, b)`                              | invokes fn with `this=obj`, args `(a, b)`               |
| `fn.myCall(null)` (strict)                          | `this = null`                                            |
| `fn.myCall(null)` (sloppy)                          | `this = globalThis`                                      |
| Function throws inside                              | symbol key cleaned up via `try/finally`                |
| Primitive ctx                                       | boxed via `Object(ctx)`                                 |

**Constraints**
- Use Symbol-as-temporary-property trick to leverage implicit binding.
- `try/finally` to clean up on throw.
- Apply delegates to call via spread.

---

## 2. Plain-English restatement

`call(ctx, ...args)` invokes the function with `this = ctx`. Trick: temporarily attach the function as a unique-Symbol property of `ctx`, then call method-style — JS's implicit binding sets `this = ctx` for free. Delete the key after.

---

## 3. Why this matters in interviews

Simplest of the three explicit-binding polyfills. Tests whether you understand implicit binding (rule 2) is the MECHANISM behind explicit binding.

---

## 4. Mental model

```
   The Symbol trick:
   ┌──────────────────────────────────────────────┐
   │ ctx[Symbol()] = fn       (temporary prop)    │
   │ ctx[symbolKey](...args)  (method-style call) │
   │   → JS implicit binding sets this = ctx       │
   │ delete ctx[symbolKey]    (cleanup, in finally)│
   │ return result                                 │
   └──────────────────────────────────────────────┘
   
   Why Symbol (not string)?
   - Unique — can't collide with user keys.
   - Strings like '__tmp__' risk overwriting existing properties.
   
   Why try/finally?
   - If fn throws, must still delete the temp key.
   - Otherwise leaked Symbol pollutes ctx forever.
   
   apply is one-liner over call via spread.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why a Symbol key instead of a string?
> 2. What goes wrong if you skip `try/finally`?
> 3. How does the Symbol trick "set `this`"?

---

## 6. Brute force — walked through

### Wrong attempt 1: string key `'__tmp__'`
Risks collision with user data; `delete` might remove their property.

### Wrong attempt 2: no try/finally
Function throws → temp key stays → ctx polluted.

### Wrong attempt 3: write your own `this` setter
No public API to set `this` from outside; must use callsite shape.

---

## 7. The unlocking insight

> **Stash `this` (the function) on `ctx` under a unique `Symbol()` key. Invoke method-style — JS's implicit binding sets `this = ctx` for free. Delete the key in `finally`. `apply` is a one-liner over `call` via spread.**

Three properties:

1. **Symbol key** for uniqueness (no collision).
2. **Method-style call** triggers implicit binding.
3. **`try/finally`** for cleanup on throw.

---

## 8. Solution (annotated)

```js
Function.prototype.myCall = function (ctx, ...args) {
  if (typeof this !== 'function') {
    throw new TypeError('myCall must be called on a function');
  }
  ctx = (ctx === null || ctx === undefined) ? globalThis : Object(ctx); // step 1: box ctx

  const key = Symbol('fn');                                              // step 2: unique key
  ctx[key] = this;                                                       // step 3: stash function
  try {
    return ctx[key](...args);                                            // step 4: method-style call
  } finally {
    delete ctx[key];                                                     // step 5: cleanup ALWAYS
  }
};

Function.prototype.myApply = function (ctx, args) {
  // Accept array, array-like, iterable, or null/undefined
  if (args !== null && args !== undefined
      && typeof args[Symbol.iterator] !== 'function'
      && typeof args.length !== 'number') {
    throw new TypeError('myApply: second arg must be array-like');
  }
  return this.myCall(ctx, ...(args ? Array.from(args) : []));
};
```

**Try it yourself**

```js
const user = { name: 'Ada' };
function greet(greeting, punct) {
  return `${greeting}, ${this.name}${punct}`;
}

greet.myCall(user, 'Hello', '!');                                       // 'Hello, Ada!'
greet.myApply(user, ['Hi', '?']);                                       // 'Hi, Ada?'

// Throw safety
function boom() { throw new Error('nope'); }
const obj = { x: 1 };
try { boom.myCall(obj); } catch {}
Object.getOwnPropertySymbols(obj);                                       // [] — cleaned up
```

---

## 9. Step-by-step dry run

```
greet.myCall(user, 'Hello', '!'):

  Inside myCall:
    this = greet (the function).
    ctx = user.
    args = ['Hello', '!'].
  
  ctx is not null/undefined → Object(user) = user (no boxing needed).
  key = Symbol('fn')  ← unique.
  user[key] = greet.  user now: { name: 'Ada', [Symbol(fn)]: greet }.
  
  try:
    user[key]('Hello', '!')  ← method-style call.
    JS implicit binding: this = user.
    Body: `Hello, ${user.name}!` = 'Hello, Ada!'.
    Result = 'Hello, Ada!'.
  finally:
    delete user[key]. user back to { name: 'Ada' }.
  
  Return 'Hello, Ada!'.

Throw safety:
  boom.myCall(obj):
    key = Symbol('fn').
    obj[key] = boom.
    try: obj[key]() → throws Error('nope').
    finally: delete obj[key]. obj clean.
    Re-throws Error.
```

---

## 10. Common confusion + traps

1. **String key** — collisions destroy user data.
2. **No try/finally** — symbol leaks on throw.
3. **Forget `return`** — function runs but caller gets undefined.
4. **Implement apply from scratch** — delegate to call via spread.
5. **`null` ctx in strict** — coerce to globalThis or leave null (spec choice).
6. **Frozen ctx** — assignment throws; polyfill limitation.
7. **Primitive ctx not boxed** — assignment fails in strict.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Reflect.apply(fn, thisArg, args)`
Same logic, different namespace. Used in proxy traps.

### Variant 2 — `fn.uncurryThis()`
Turn `Array.prototype.slice` into a free function via bind. Babel/SES pattern.

### Variant 3 — "Why not just spread?"
Modern code: `fn.call(ctx, ...args)` ≡ `fn.apply(ctx, args)` ≡ `Reflect.apply(fn, ctx, args)`.

### Variant 4 — Frozen ctx
Polyfill mutates ctx; native doesn't. Acknowledge limitation.

### Variant 5 — Primitive ctx in strict
`Object(ctx)` boxes to wrapper object.

---

## 12. How to think aloud

> "Use the Symbol-as-temporary-property trick. `const key = Symbol(); ctx[key] = this; try { return ctx[key](...args); } finally { delete ctx[key]; }`. Why Symbol? Strings can collide with user keys; symbols are guaranteed unique. The method-style call `ctx[key](...)` triggers JS's IMPLICIT binding (rule 2) which sets `this = ctx` for free — we piggyback on the language rule we're polyfilling. `try/finally` to clean up on throw — otherwise the symbol pollutes ctx forever. `null`/`undefined` ctx → coerce to `globalThis` (sloppy semantics). Primitive ctx → `Object(ctx)` boxes it. `apply` is one-liner: delegate to call via spread. Trap: string key collisions; no try/finally; forgetting return."

---

## 13. 60-second revision

> - **Symbol trick:** `ctx[Symbol()] = fn; try { return ctx[key](...args) } finally { delete ctx[key] }`.
> - **Symbol** for uniqueness (no string collision).
> - **Method-style call** triggers implicit binding → `this = ctx`.
> - **`try/finally`** to clean up on throw.
> - **`null`/`undefined` ctx** → coerce to `globalThis`.
> - **Primitive ctx** → `Object(ctx)` boxes.
> - **`apply`** = one-liner over `call` via spread.
> - **Trap:** string key (collisions); no try/finally (leak); forget return.

---

**Related:** [polyfill-bind.md](./polyfill-bind.md) · [polyfill-new.md](./polyfill-new.md) · [this-keyword-nodejs.md](./this-keyword-nodejs.md) · [`10-machine-coding-patterns/bind-polyfill.md`](../10-machine-coding-patterns/bind-polyfill.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
