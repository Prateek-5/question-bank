# Polyfill `Function.prototype.bind`

> **Difficulty:** Medium-Senior   |   **Time:** ~25 min   |   **Prereqs:** [`concepts/prototype.md`](../../concepts/prototype.md), [`03-prototype/this-binding-rules.md`](../03-prototype/this-binding-rules.md)
>
> **Source:** ECMA-262 §20.2.3.2. BFE.dev, Frontend Masters classic. The polyfill that everyone gets wrong on the first try.

---

## 1. Problem statement

**Signature**
```ts
Function.prototype.myBind: (this: Function, thisArg: any, ...boundArgs: any[]) => Function;
```

**Input / Output examples**

| Setup                                                    | Behaviour                                              |
|-----------------------------------------------------------|---------------------------------------------------------|
| `f.myBind(ctx)(a, b)` (normal call)                       | `f.apply(ctx, [a, b])`                                 |
| `f.myBind(ctx, 1, 2)(3)` (partial app)                   | `f.apply(ctx, [1, 2, 3])`                              |
| `new (Foo.myBind(ctx))()` (constructor)                   | `this` is the new instance, **NOT** ctx                |
| `new (Foo.myBind(ctx))() instanceof Foo`                  | `true`                                                  |
| `arrowFn.myBind(ctx)()`                                   | ctx ignored — arrows have lexical `this`               |
| `f.myBind(a).myBind(b)`                                   | `b` ignored — first bind wins                          |

**Constraints**
- Normal call → `this = thisArg`.
- `new` call → `this = new instance` (ignore thisArg, but boundArgs still apply).
- Partial application: boundArgs prepend callArgs.
- `instanceof` preserved via prototype chain.

---

## 2. Plain-English restatement

Make a copy of a function whose `this` is permanently set to `thisArg` and whose first few args are pre-filled. The one twist: if someone calls the result with `new`, the bound `this` is ignored — JS gives the function a fresh instance, and the bound args still prefix the call args. The polyfill detects `new` via `new.target`.

---

## 3. Why this matters in interviews

The classic prototype-chain interview problem. Looks like "just `fn.apply(thisArg, ...args)` inside a wrapper" — but the *real* test is one follow-up: **"What happens if I do `new (foo.bind(obj))()`?"** A correct answer detects constructor calls (`new.target`) and **ignores** the bound `this`, using the new instance instead. This catches ~80% of candidates. Backend interviewers love it because Node code is full of `bind` usage — callback wiring, event handlers, class methods passed to async libraries.

---

## 4. Mental model

The bound function as a **decorator that re-routes `this`**:

```
   normal call:                    new call:
   ────────────                    ──────────
   fn.myBind(ctx)(a, b)            new (fn.myBind(ctx))(c)
       │                                │
       ▼                                ▼
   Bound(a, b):                    Bound(c):
     new.target = undefined          new.target = Bound   (truthy)
     ctx = thisArg                   ctx = `this`         (fresh instance)
     fn.apply(thisArg, [a, b])       fn.apply(newInstance, [c])
                                     // boundArgs still prefix
                                     // newInstance.[[Proto]] === Bound.prototype
                                     //                       === Object.create(fn.prototype)
                                     // so `new Bound() instanceof fn` → true
```

The `new.target` is the magic line. Without it, `new (foo.bind(ctx))()` sends `this` to ctx — wrong.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What is `new.target` inside a function called normally vs called with `new`?
> 2. Why does `new (foo.bind(ctx))() instanceof foo` need to be `true`?
> 3. If you `bind` an arrow function with a `thisArg`, does the arrow's `this` change?

---

## 6. Brute force — walked through

### Wrong attempt 1: just `apply`
```js
Function.prototype.myBind = function (thisArg, ...boundArgs) {
  const targetFn = this;
  return function (...callArgs) {
    return targetFn.apply(thisArg, [...boundArgs, ...callArgs]);   // BUG: ignores `new`
  };
};
```
Normal calls work. But `new (foo.myBind(ctx))()` → `foo.apply(ctx, ...)`, so `this` inside `foo` is `ctx`, NOT a new instance. Interviewer pounces.

### Wrong attempt 2: arrow for `Bound`
```js
return (...callArgs) => targetFn.apply(thisArg, [...boundArgs, ...callArgs]);   // BUG
```
Arrow has no `new.target` and can't be called with `new`. Constructor invocations throw "is not a constructor."

### Wrong attempt 3: no prototype chain
Forget `Bound.prototype = Object.create(targetFn.prototype)` → `new Bound() instanceof targetFn === false`. Bound class loses its identity.

---

## 7. The unlocking insight

> **`new.target` flips the `this` source. Inside `Bound`: `const ctx = new.target ? this : thisArg`. Set `Bound.prototype = Object.create(targetFn.prototype)` so `instanceof` works.**

Three properties:

1. **`new.target`** is `undefined` for normal calls, set to the constructor for `new` calls — the cleanest detection.
2. **Capture `targetFn = this`** before the inner function so it's accessible in the closure.
3. **Prototype chain via `Object.create(targetFn.prototype)`** so `new Bound() instanceof targetFn`.

---

## 8. Solution (annotated)

```js
Function.prototype.myBind = function (thisArg, ...boundArgs) {
  if (typeof this !== 'function') {
    throw new TypeError('myBind must be called on a function');   // step 1: guard
  }
  const targetFn = this;                                          // step 2: capture fn

  function Bound(...callArgs) {
    const ctx = new.target ? this : thisArg;                      // step 3: THE magic line
    return targetFn.apply(ctx, [...boundArgs, ...callArgs]);      // step 4: partial app
  }

  if (targetFn.prototype) {                                       // step 5: instanceof support
    Bound.prototype = Object.create(targetFn.prototype);
  }

  // Polish: name + length to match native bind output
  Object.defineProperty(Bound, 'name', {
    value: `bound ${targetFn.name || ''}`, configurable: true,
  });
  Object.defineProperty(Bound, 'length', {
    value: Math.max(0, (targetFn.length || 0) - boundArgs.length), configurable: true,
  });

  return Bound;
};
```

**Try it yourself**

```js
function Greeter(greeting, name) {
  this.greeting = greeting;
  this.name = name;
}
Greeter.prototype.say = function () { return `${this.greeting}, ${this.name}!`; };

const ctx = { tag: 'wrongCtx' };
const Bound = Greeter.myBind(ctx, 'Hello');

// Normal call → mutates ctx
Bound('Prateek');
console.log(ctx.greeting, ctx.name);          // 'Hello' 'Prateek'

// `new` call → fresh instance; ctx unchanged
const g = new Bound('Anu');
console.log(g.greeting, g.name);              // 'Hello' 'Anu'
console.log(g instanceof Greeter);            // true
console.log(g.say());                         // 'Hello, Anu!'
console.log(ctx.greeting);                    // still 'Hello' (from earlier mutation)
```

---

## 9. Step-by-step dry run

```
const ctx = { tag: 'wrongCtx' }
const Bound = Greeter.myBind(ctx, 'Hello')
  step 2:  targetFn = Greeter
  step 5:  Bound.prototype = Object.create(Greeter.prototype)
           → Bound.prototype.[[Proto]] === Greeter.prototype

Test 1 — normal call:
Bound('Prateek')
  enter Bound(['Prateek'])
  step 3:  new.target = undefined → ctx = thisArg = { tag: 'wrongCtx' }
  step 4:  Greeter.apply({tag:'wrongCtx'}, ['Hello', 'Prateek'])
           inside Greeter: this = ctx
             ctx.greeting = 'Hello'
             ctx.name = 'Prateek'
  return undefined
  // ctx mutated (yikes, but that's the contract)

Test 2 — new call:
const g = new Bound('Anu')
  JS engine: create freshObj with freshObj.[[Proto]] = Bound.prototype
  enter Bound(['Anu']) with this = freshObj, new.target = Bound (truthy)
  step 3:  ctx = this = freshObj
  step 4:  Greeter.apply(freshObj, ['Hello', 'Anu'])
           inside Greeter: this = freshObj
             freshObj.greeting = 'Hello'
             freshObj.name = 'Anu'
  return undefined
  // `new` uses freshObj as the result since Bound returned undefined
  
g instanceof Greeter:
  walk g's prototype chain
  g.[[Proto]] === Bound.prototype === Object.create(Greeter.prototype)
  Bound.prototype.[[Proto]] === Greeter.prototype
  → match → true

g.say():
  property lookup on g → not own → walk chain
  g.[[Proto]] (Bound.prototype) → no 'say' → walk further
  Bound.prototype.[[Proto]] (Greeter.prototype) → has 'say' ✓
  invoke say() with this=g → `${g.greeting}, ${g.name}!` = 'Hello, Anu!'
```

---

## 10. Common confusion + traps

1. **Forgetting `new.target`** — bound constructors send `this` to ctx instead of new instance.
2. **Arrow for `Bound`** — no `new.target`; cannot be called with `new`.
3. **Skipping `Object.create(targetFn.prototype)`** — `instanceof` fails.
4. **Capturing `this` inside `function Bound()`** — the inner `this` is different from the outer; capture `targetFn` outside.
5. **`fn.bind(a).bind(b)`** — `b` is silently ignored; native and polyfill both behave this way.
6. **Arrow function as `targetFn`** — `thisArg` is ignored; arrow `this` is lexical. Polyfill silently no-ops correctly.
7. **Strict vs sloppy `bind(null)`** — strict gives `this === null`; sloppy gives `globalThis`. Engine handles.

---

## 11. Senior follow-ups & variants

### Variant 1 — Polyfill `call`
```js
Function.prototype.myCall = function (thisArg, ...args) {
  thisArg = thisArg ?? globalThis;
  const sym = Symbol();
  thisArg[sym] = this;
  try { return thisArg[sym](...args); }
  finally { delete thisArg[sym]; }
};
```
Temporarily attaches the function as a property of `thisArg`, calls, removes.

### Variant 2 — Polyfill `apply`
Same as `call` but takes an array.

### Variant 3 — Polyfill `new`
```js
function myNew(Ctor, ...args) {
  const obj = Object.create(Ctor.prototype);
  const res = Ctor.apply(obj, args);
  return (res !== null && typeof res === 'object') ? res : obj;
}
```
The return-handling line is the gotcha — constructors that return an object override the new instance.

### Variant 4 — `Reflect.construct`
Modern equivalent of `bind` + `new`: `Reflect.construct(Foo, args, NewTarget)`.

### Variant 5 — Immutability of bound `this`
Once bound, `this` can't be changed even by `call`/`apply` on the bound fn. Native and polyfill both have this.

---

## 12. How to think aloud

> "Capture `targetFn = this`. Return a `Bound` function (NOT an arrow — arrows can't be called with `new`). Inside `Bound`: `const ctx = new.target ? this : thisArg` — the magic line. Then `targetFn.apply(ctx, [...boundArgs, ...callArgs])`. For `instanceof` to work, `Bound.prototype = Object.create(targetFn.prototype)`. Trap: forgetting `new.target` → constructor calls send `this` to ctx. Trap: arrow for `Bound` → no `new.target`. Sibling polyfills: `call` (symbol-property trick), `apply` (array variant), `new` (Object.create + apply + return-handling)."

---

## 13. 60-second revision

> - **Polyfill: capture `targetFn`, return `Bound` (NOT arrow).**
> - **`const ctx = new.target ? this : thisArg`** — the magic line.
> - **`Bound.prototype = Object.create(targetFn.prototype)`** for `instanceof`.
> - **Partial app:** `[...boundArgs, ...callArgs]`.
> - **THE test:** `new (foo.bind(ctx))()` — `this` must be the new instance, NOT ctx.
> - **Sibling polyfills:** `call` (symbol trick), `apply` (array variant), `new` (create + apply + return-handling).
> - **Trap:** arrow `Bound`; missing prototype chain; capturing `this` inside `Bound`.

---

**Related:** [`03-prototype/this-binding-rules.md`](../03-prototype/this-binding-rules.md) · [`03-prototype/call-apply-bind-differences.md`](../03-prototype/call-apply-bind-differences.md) · [function-composition.md](./function-composition.md) · [curry.md](./curry.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
