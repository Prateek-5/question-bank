# Polyfill `Function.prototype.bind`

> **Difficulty:** Medium-Senior   |   **Time:** ~20 min   |   **Prereqs:** [this-keyword-nodejs.md](./this-keyword-nodejs.md), [polyfill-call-apply.md](./polyfill-call-apply.md)
>
> **Source:** ECMA-262 §20.2.3.2. THE most-asked polyfill in JS interviews. Razorpay, Atlassian, PhonePe, Meta, Amazon.

---

## 1. Problem statement

Polyfill `Function.prototype.bind` including the `new` override (bound ctx IGNORED when called with `new`).

**Verification examples**

```js
const bound = fn.myBind(ctx, ...preset);
bound(...later);                              // fn.call(ctx, ...preset, ...later)
new bound(...later);                          // fresh `this`; ctx IGNORED; args concatenated
new bound() instanceof fn;                    // true
```

| Setup                                                | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| `bound()` plain call                                  | uses bound ctx                                          |
| `new bound()` (constructor)                           | fresh `this` whose proto is `fn.prototype`; ctx IGNORED |
| Partial application                                   | bound args prepend call args                            |
| Chain `fn.bind(A).bind(B)`                           | first bind wins (sticky)                                |
| Arrow as `fn`                                          | ctx ignored (arrows have lexical this)                 |

**Constraints**
- Detect `new` via `this instanceof bound` in a NAMED function wrapper (not arrow — no `[[Construct]]`).
- `Object.create(fn.prototype)` for `instanceof` support.
- Partial app: `[...preset, ...later]`.

---

## 2. Plain-English restatement

`myBind(ctx, ...preset)` returns a new function with `this` permanently set to `ctx` and `preset` args pre-applied. The twist: if someone calls it with `new`, the bound `this` is IGNORED — they get a fresh instance.

---

## 3. Why this matters in interviews

THE most-asked polyfill. Tests `this`, partial application, `new` semantics, prototype chain — all in 20 lines.

---

## 4. Mental model

```
   fn.myBind(ctx, ...preset):
   ┌────────────────────────────────────────────────────┐
   │ Captures fn, ctx, preset in closure.                │
   │ Returns `bound` function.                            │
   │                                                       │
   │ bound(...later):                                     │
   │   if `this instanceof bound`:                        │
   │     // called with new → fresh this; IGNORE ctx       │
   │     return fn.apply(this, [...preset, ...later])     │
   │   else:                                              │
   │     return fn.apply(ctx, [...preset, ...later])       │
   │                                                       │
   │ bound.prototype = Object.create(fn.prototype)        │
   │   so `new bound()` instances satisfy instanceof fn.  │
   └────────────────────────────────────────────────────┘

   Why named function wrapper (not arrow)?
     - Arrows can't be called with `new` (no [[Construct]]).
     - Arrows have no own `this`.
     - We need `this instanceof bound` to work.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why arrow wrapper breaks `new`-detection?
> 2. After `new bound()`, why must `instance instanceof fn` be true?
> 3. What's `fn.bind(A).bind(B)()` — A or B?

---

## 6. Brute force — walked through

### Wrong attempt 1: 4-line happy path
```js
return (...later) => fn.apply(ctx, [...preset, ...later]);
```
Works for plain calls; FAILS `new` test. Arrow has no `[[Construct]]`.

### Wrong attempt 2: function wrapper without new-detect
`new bound()` → calls `fn.apply(ctx, ...)` → fresh `this` IGNORED. Instances come back blank.

### Wrong attempt 3: skip `Object.create(fn.prototype)`
`new bound() instanceof fn` → false. Inherited methods don't resolve.

---

## 7. The unlocking insight

> **Named function wrapper (NOT arrow). Inside: detect `new` via `this instanceof bound`. If `new`, use fresh `this`; else use bound ctx. Wire `bound.prototype = Object.create(fn.prototype)` for `instanceof` support.**

Three properties:

1. **Named function wrapper** — has own `this` + `[[Construct]]`.
2. **`this instanceof bound`** detects `new` invocation.
3. **`bound.prototype = Object.create(fn.prototype)`** for instanceof.

---

## 8. Solution (annotated)

```js
Function.prototype.myBind = function (ctx, ...preset) {
  if (typeof this !== 'function') {
    throw new TypeError('myBind must be called on a function');
  }
  const fn = this;

  function bound(...later) {                                            // step 1: NAMED wrapper
    const calledAsNew = this instanceof bound;                          // step 2: detect new
    return fn.apply(calledAsNew ? this : ctx, [...preset, ...later]);   // step 3: route this + concat args
  }

  if (fn.prototype) {
    bound.prototype = Object.create(fn.prototype);                      // step 4: instanceof support
  }

  Object.defineProperty(bound, 'name', {
    value: 'bound ' + (fn.name || ''),
    configurable: true,
  });

  return bound;
};
```

**Try it yourself**

```js
// Plain call with partial application
function greet(greeting, punct, name) {
  return `${greeting}, ${name}${punct} (${this.title})`;
}
const hi = greet.myBind({ title: 'Dr.' }, 'Hello', '!');
hi('Ada');                                                              // 'Hello, Ada! (Dr.)'

// new with bound function — the crown jewel
function Person(first, last) {
  this.first = first;
  this.last = last;
}
Person.prototype.full = function () { return `${this.first} ${this.last}`; };

const Bound = Person.myBind({}, 'Ada');
const p = new Bound('Lovelace');
p.full();                                                                // 'Ada Lovelace'
p instanceof Person;                                                     // true (chain via Object.create)
p instanceof Bound;                                                      // true

// Chain
const A = greet.bind({ title: 'A' });
const B = A.bind({ title: 'B' });
B('Hi', '!', 'X');                                                       // 'Hi, X! (A)' — first bind wins
```

---

## 9. Step-by-step dry run

```
const Bound = Person.myBind({ignored}, 'Ada')

myBind execution:
  fn = Person (this inside myBind).
  ctx = {ignored}; preset = ['Ada'].
  Define `bound` function (named).
  bound.prototype = Object.create(Person.prototype).
  Return bound.

new Bound('Lovelace'):
  JS [[Construct]] machinery:
    Create obj. obj.[[Prototype]] = Bound.prototype.
    Call bound with this = obj, args = ['Lovelace'].
  
  Inside bound:
    this = obj
    this instanceof bound? Walk obj's chain: Bound.prototype found. YES.
    calledAsNew = true.
    Return fn.apply(this, ['Ada', 'Lovelace']):
      Person.call(obj, 'Ada', 'Lovelace'):
        obj.first = 'Ada'
        obj.last = 'Lovelace'
      returns undefined.
  bound returns undefined.
  
  [[Construct]]: undefined returned → use obj.
  
p = obj = {first: 'Ada', last: 'Lovelace'}.

p.full():
  Walk p's chain:
    p own? no.
    Bound.prototype own (= Object.create(Person.prototype) — empty)? no.
    Person.prototype own? YES → full.
  Invoke with this=p → 'Ada Lovelace'.

p instanceof Person:
  Walk p's chain looking for Person.prototype.
  p.[[Proto]] = Bound.prototype.
  Bound.prototype.[[Proto]] = Person.prototype. MATCH.
  Return true.
```

---

## 10. Common confusion + traps

1. **Arrow wrapper** → no `[[Construct]]`, `this instanceof bound` breaks.
2. **Skip Object.create** → `instanceof fn` fails.
3. **Replace args (not concat)** → loses preset.
4. **Recursive `fn.bind`** inside polyfill — infinite loop.
5. **`bound.prototype` should be `undefined`** — native does, but polyfills compromise.
6. **Chained bind: second wins** — no, first wins (sticky).
7. **Forget `name` property** — spec sets `'bound ' + fn.name`.

---

## 11. Senior follow-ups & variants

### Variant 1 — `partial(fn, ...args)`
Same shape but doesn't lock `this`. Drop `ctx`.

### Variant 2 — `curry(fn)`
Returns until arity met; can be built atop bind.

### Variant 3 — `myCall` / `myApply`
See [polyfill-call-apply.md](./polyfill-call-apply.md).

### Variant 4 — Why `new` ignores bound ctx
Spec: `[[Construct]]` creates `this`; the wrapper sees it via `this instanceof bound` and forwards it.

### Variant 5 — `bound.length`
Native: `Math.max(0, fn.length - preset.length)`. Polish via `Object.defineProperty`.

---

## 12. How to think aloud

> "Named function wrapper, NOT arrow — arrows can't be called with `new`. Inside: `const calledAsNew = this instanceof bound;` detects `new` invocation. If `calledAsNew`, use the fresh `this` (passed by [[Construct]]); else use bound `ctx`. Then `fn.apply(target, [...preset, ...later])` to invoke with concatenated args. Wire `bound.prototype = Object.create(fn.prototype)` so `new bound() instanceof fn` works and inherited methods resolve. Native bound functions have no own `.prototype`; polyfills compromise. Optional: `Object.defineProperty(bound, 'name', { value: 'bound ' + fn.name })`. Trap: arrow wrapper (breaks new + this-detection); skipping Object.create (instanceof fails); replacing args instead of concatenating; expecting chained binds to second-wins (first wins)."

---

## 13. 60-second revision

> - **Named function wrapper** (NOT arrow).
> - **Detect `new`** via `this instanceof bound`.
> - **If new:** use fresh `this`; **else:** use bound `ctx`.
> - **Concat args:** `[...preset, ...later]`.
> - **`bound.prototype = Object.create(fn.prototype)`** for instanceof.
> - **`fn.bind(A).bind(B)`** → A wins (sticky).
> - **Optional:** `name = 'bound ' + fn.name`, `length = max(0, fn.length - preset.length)`.
> - **Trap:** arrow wrapper; skip Object.create; replace not concat args; expect second-bind-wins.

---

**Related:** [this-keyword-nodejs.md](./this-keyword-nodejs.md) · [polyfill-call-apply.md](./polyfill-call-apply.md) · [polyfill-new.md](./polyfill-new.md) · [`10-machine-coding-patterns/bind-polyfill.md`](../10-machine-coding-patterns/bind-polyfill.md) · [`10-machine-coding-patterns/curry.md`](../10-machine-coding-patterns/curry.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
