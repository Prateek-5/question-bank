# Closure vs `#`-private class field — when to pick which

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [private-data-counter.md](./private-data-counter.md), [counter-ii.md](./counter-ii.md), [`concepts/closures.md`](../../concepts/closures.md), [`concepts/prototype.md`](../../concepts/prototype.md)
>
> **Source:** ES2022 `#private` fields; lifelong closure-based privacy. Output-prediction + "design choice" questions at Stripe, Atlassian, Razorpay.

---

## 1. Problem statement

**The question**: "Make this counter private. Then rewrite it the other way and compare."

**Two correct answers**

```js
// (A) Closure factory
function createCounter() {
  let n = 0;
  return { inc: () => ++n, peek: () => n };
}

// (B) Class with #private field
class Counter {
  #n = 0;
  inc() { return ++this.#n; }
  peek() { return this.#n; }
}
```

**Input / Output examples**

| Setup                                                 | Behaviour                                       |
|-------------------------------------------------------|--------------------------------------------------|
| `(A): const c = createCounter(); c.n;`                | `undefined` — closure literally unreachable     |
| `(B): const c = new Counter(); c.#n;`                 | SyntaxError outside class body — private slot   |
| `(A): const {inc} = createCounter(); inc();`          | works — no `this` involved                       |
| `(B): const {inc} = new Counter(); inc();`            | `TypeError: Cannot read private field '#n' on undefined` |
| 1000 instances                                        | (A) ~4000 fn objects; (B) ~3 prototype methods   |
| `Counter` extends another class                       | (A) awkward; (B) standard `extends`              |

**Constraints (for the discussion)**
- List at least **6 axes** of difference.
- Recommend a choice with justification per use case.

---

## 2. Plain-English restatement

There are two ways to keep a piece of state genuinely private in modern JavaScript: hide it in a closure (the historical way), or hide it as a `#`-prefixed class field (the ES2022 way). Both give true privacy — no reflection escape, no property descriptor, no enumeration. They differ in everything else: how methods are shared across instances, whether `this` is involved, how they interact with inheritance, memory cost, debuggability, and idiomatic fit (functional vs OOP).

The interviewer wants you to articulate the differences and pick the right one for a given scenario.

---

## 3. Why this matters in interviews

This is a **tradeoff-fluency** question. Multiple right answers exist; choosing well — and naming the tradeoffs aloud — is what separates senior from mid. Modern-JS literacy is also tested: `#fields` are ES2022, recent enough that some candidates haven't seen them. The third signal is style: do you reach for functional (closure) or OOP (class) by default, and can you switch idioms when the context calls for it?

---

## 4. Mental model

Two different mechanisms with the same privacy guarantee but different physics:

```
   Closure factory                    Class with #private field
   ───────────────                    ─────────────────────────
   one closure per instance           one prototype, many instances
   each instance owns its methods     methods shared on prototype
   methods see state via [[Env]]      methods see #fields via slot table
   no `this`; methods are bound       `this` binds to instance
   memory: O(instances × methods)     memory: O(instances × fields)
   created with a factory call        created with `new`
   compatible with all engines        ES2022+ only

   privacy guarantee:                 privacy guarantee:
     closure variables are            #fields are syntactically
     unreachable from outside         restricted; runtime-enforced
                                       slot lookup checks ownership
```

**Six axes of difference** to keep in your pocket:

| Axis | Closure | Class `#field` |
|---|---|---|
| Available since | Always | ES2022 |
| Methods location | Per-instance | Prototype (shared) |
| `this` semantics | Not used | Standard `this` |
| Destructure-safe | Yes (`const {inc} = ...; inc();` works) | No (loses `this`) |
| `instanceof` checks | Doesn't apply | Standard |
| Inheritance | Awkward | Native `extends` |
| Memory per instance | LE + N function objects | Slot table + shared prototype |
| Reflection visibility | Invisible | Invisible (`#x` syntactically gated) |

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With 100k counter instances, which uses less memory — closure or class? Why?
> 2. `const {inc} = createCounter(); inc(); inc();` works. `const {inc} = new Counter(); inc(); inc();` throws. Why does the closure survive destructuring?
> 3. If your boss says "we want a counter that extends a `Logger` base class," which approach fits more naturally and why?

---

## 6. Brute force — walked through

### Wrong attempt 1: `class { _n = 0 }` (underscore convention)

```js
class Counter {
  _n = 0;
  inc() { return ++this._n; }
}
const c = new Counter();
c._n = 999;   // public; convention violated
```

`_n` is publicly readable and writable. The leading underscore is a convention only — no enforcement. Soft privacy = no privacy in adversarial contexts. Reject as "not actually private."

### Wrong attempt 2: TypeScript's `private` keyword

```ts
class Counter {
  private n = 0;
  inc() { return ++this.n; }
}
const c = new Counter();
(c as any).n = 999;   // TypeScript can't stop this at runtime
```

TypeScript's `private` is **compile-time only**. The emitted JavaScript has no protection — anyone can access `.n` at runtime via type-erasure. Don't rely on it for actual privacy. Mention it as a non-answer.

### Wrong attempt 3: `Symbol`-keyed properties

```js
const _n = Symbol('n');
class Counter {
  [_n] = 0;
  inc() { return ++this[_n]; }
}
const c = new Counter();
Object.getOwnPropertySymbols(c);   // [Symbol(n)] — visible
```

`Symbol`s are discoverable via `Object.getOwnPropertySymbols` and `Reflect.ownKeys`. Not truly private. Useful for "namespaced public" — not for hiding.

---

## 7. The unlocking insight

> **Both closure and `#field` give *true* privacy. The choice is about everything else: methods location (per-instance vs prototype), `this` semantics, inheritance support, and idiomatic fit.**

**Closure** gives you per-instance methods. Each `createCounter()` call allocates fresh function objects for every method, each carrying `[[Environment]]` pointing at that call's LE. Methods don't use `this` — they reach state through the scope chain. This makes destructuring safe (`const {inc} = createCounter(); inc();` works) but costs `O(instances × methods)` function objects in memory.

**Class `#field`** uses prototype-shared methods. One prototype object holds all methods; instances hold just the `#field` slots. Methods use `this` to find the instance, then look up the private slot via the engine's runtime check (the lookup throws `TypeError` if `this` isn't an instance of the class that declared the field). This makes memory `O(instances × fields + 1 × methods)` — much better at scale — but destructuring breaks because `inc` without `this` has no way to find `#n`.

**Privacy mechanism**:

- **Closure**: there's literally no name accessible from outside that points at `n`. `c.n` is `undefined`; `Object.keys(c)` shows methods; `Reflect.ownKeys` doesn't expose `n`.
- **`#field`**: `obj['#n']` looks for a property named `#n` (no such property); the actual slot is in a side-table the runtime checks against the receiving class. The `#` syntax is the **only way to address it** — and only from within the declaring class.

Both are reflection-proof. Both survive `JSON.stringify` (entries skipped). Both invisible to `Object.getOwnPropertyNames` and `Reflect.ownKeys`.

**The decision tree**:

```
   Need inheritance / extends?                → class with #
   Need many instances (memory matters)?      → class with # (prototype share)
   Need `instanceof` checks?                  → class with #
   Need destructure-safe methods?             → closure
   No `this`, functional style?               → closure
   Module-pattern singleton or factory?       → closure
   Pre-ES2022 browser/runtime?                → closure
   Building reactive primitives?              → either; closure feels more natural
```

---

## 8. Solution (annotated)

```js
// ── (A) Closure factory ──────────────────────────────────────────
export function createTodoStore() {                  // step 1: factory; each call = independent store
  let items = [];                                     // step 2: private state in closure
  const listeners = new Set();
  function emit() { listeners.forEach((fn) => fn()); }

  return {                                            // step 3: public API
    add(t)        { items = [...items, t]; emit(); }, // step 4: methods close over `items`, `listeners`
    remove(id)    { items = items.filter((i) => i.id !== id); emit(); },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    snapshot()    { return items.slice(); },
  };
}

// ── (B) Class with # private fields ──────────────────────────────
export class TodoStore {
  #items = [];                                        // step 1: private slot per instance
  #listeners = new Set();
  #emit() { this.#listeners.forEach((fn) => fn()); }  // step 2: private method

  add(t)        { this.#items.push(t); this.#emit(); }
  remove(id)    { this.#items = this.#items.filter((i) => i.id !== id); this.#emit(); }
  subscribe(fn) { this.#listeners.add(fn); return () => this.#listeners.delete(fn); }
  snapshot()    { return this.#items.slice(); }
}
```

**Try it yourself — memory comparison**

```js
// 1000 stores via closure: 1000 LEs × 4 methods = 4000 function objects
// 1000 stores via class:   1000 instances × 0 own methods + 4 prototype methods = 4 fn objects
//                          (plus 1000 slot tables for #items, #listeners)

// At small N (< 100), no measurable difference.
// At large N (10k+), the class version saves significant memory.
```

**Try it yourself — destructure safety**

```js
// (A) destructuring safe
const { add, snapshot } = createTodoStore();
add({ id: 1, text: 'go' });
console.log(snapshot());   // [{id:1,text:'go'}]

// (B) destructuring breaks
const store = new TodoStore();
const { add: addB } = store;
addB({ id: 1, text: 'go' });   // TypeError: Cannot read private field '#items' on undefined
// (You'd need to bind: const addB = store.add.bind(store);)
```

---

## 9. Step-by-step dry run

Memory and behavior trace for 3 instances each:

| Step       | Closure version                                            | Class version                                  |
|------------|------------------------------------------------------------|------------------------------------------------|
| Create x 3 | 3 LEs + 12 fn objects (3 × 4 methods)                      | 3 instances + 1 shared prototype (4 methods)  |
| Call inc   | Look up `inc` on instance → call → reads `n` via scope chain | Look up `inc` on prototype → call → reads `this.#n` via slot table |
| Memory     | Each instance owns its method copies                       | Methods shared across instances                |
| Destructure | `const {inc} = ...; inc();` → works (no `this`)            | `const {inc} = ...; inc();` → TypeError (no `this`) |
| Reflect    | `Object.keys(c)` → method names; no `n`                    | `Object.keys(c)` → `[]`; no `#n`               |

For the closure version, V8 sometimes optimizes by sharing the inner function code while still allocating per-instance closures. The class version benefits more consistently from V8's hidden-class + inline-cache optimizations because of its predictable shape.

---

## 10. Common confusion + traps

1. **`#fields` are public if accessed via brackets.**
   They're not. `obj['#n']` looks for a property literally named `'#n'` (no such property). The slot is in a runtime-checked side-table — the `#` syntax is the only way to address it.

2. **Closures are slow.**
   Negligibly for normal use. Per-instance method allocation costs memory at scale but doesn't affect per-call latency in any measurable way. Benchmark before optimizing.

3. **Classes always need a constructor.**
   Not with field initializers. `class C { #n = 0 }` works without an explicit `constructor`.

4. **`#fields` work in TypeScript via `private`.**
   `private` and `#` are different. `private` is compile-time only; `#` is runtime-enforced. Use `#` when you want actual privacy.

5. **Destructuring works the same for both.**
   It doesn't. Closure methods don't need `this`; class methods do. Class methods lose `this` on destructure unless you bind them.

6. **`#fields` can be accessed from subclasses.**
   They can't. A `#n` declared in `Base` is not accessible from `Sub extends Base`. Each class declares its own `#fields`. This is a *feature* — true hard privacy.

7. **Symbol-keyed properties are private.**
   They're discoverable via `Object.getOwnPropertySymbols` and `Reflect.ownKeys`. Not private.

8. **`WeakMap`-keyed privacy as an alternative.**
   ```js
   const _state = new WeakMap();
   class C {
     constructor() { _state.set(this, { n: 0 }); }
     inc() { return ++_state.get(this).n; }
   }
   ```
   Module-scoped `_state` is invisible outside the file (with ESM). Pre-ES2022 alternative to `#`. Slightly slower than `#` (Map lookup vs slot lookup).

---

## 11. Senior follow-ups & variants

### Variant 1 — Hybrid: closure factory returning a class instance

For complex cases, return a class instance from a factory that captured deps:

```js
export function createStoreFactory({ db, logger }) {
  return class Store {
    #db = db;            // captured via factory closure
    #logger = logger;
    add(item) { /* uses this.#db, this.#logger */ }
  };
}
const Store = createStoreFactory({ db, logger });
const s = new Store();
```

Closure handles dependency injection; class handles instance method sharing. Best of both for some scenarios.

### Variant 2 — `Object.freeze` to lock the public API

The closure version is mutable from outside (`c.inc = () => 999`). Freeze the returned object to prevent monkey-patching:

```js
function createCounter() {
  let n = 0;
  return Object.freeze({
    inc: () => ++n,
    peek: () => n,
  });
}
```

The closure protects `n`; freeze protects the API surface. Class with `#` is already partially protected (methods on prototype can be patched only on the prototype, not per-instance).

### Variant 3 — `WeakMap`-based private state for classes (pre-ES2022)

```js
const _state = new WeakMap();
class Counter {
  constructor() { _state.set(this, { n: 0 }); }
  inc() { return ++_state.get(this).n; }
}
```

Module-scoped `_state` is invisible outside the module. Slower than `#` but works in old engines. Useful for libraries targeting Node 10+ or older browsers.

### Variant 4 — `Symbol` for "private-ish" (not actually private)

For namespacing or framework-internal "extension points" where the property *could* be discoverable but shouldn't be touched casually:

```js
const _internal = Symbol('internal');
class C {
  [_internal] = { /* framework state */ };
}
```

Discoverable via reflection but invisible in normal property access. Used by some libraries (e.g., React's `Symbol.for('react.element')`).

### Variant 5 — Decorator-based privacy (Stage 3 proposal)

```js
class C {
  @private n = 0;          // hypothetical decorator
  inc() { return ++this.n; }
}
```

The decorator proposal is still moving; current state: Stage 3 with some changes. `#` is the production-ready answer.

---

## 12. How to think aloud in the interview

> "Both give true privacy. Closure factories are functional-style: per-instance methods, no `this`, simpler mental model for one-off factories, destructure-safe. Class `#fields` share methods on the prototype: less memory at scale, supports inheritance via `extends`, gets `instanceof`, but requires `this` and breaks under destructuring. I'd pick closure for module-pattern singletons, small factories, dependency-injection patterns, and pre-ES2022 environments. Class for libraries that consumers extend, OOP-style codebases, or scenarios with many instances where memory matters. TypeScript `private` is compile-time only — not real privacy; `#` is the only runtime guarantee in modern JS. `WeakMap`-keyed state is the pre-2022 alternative; still works, slightly slower."

---

## 13. 60-second revision

> - **Both give true privacy.** No reflection escape.
> - **Closure**: per-instance methods, no `this`, functional style, destructure-safe.
> - **Class `#`**: prototype-shared methods, supports inheritance, `instanceof`-able, requires `this`.
> - **Memory**: closure `O(instances × methods)`; class `O(instances × fields + 1 × methods)`.
> - **TS `private` ≠ runtime privacy** — `#` or closure are the only real options.
> - **Symbol-keyed is not private** — `Object.getOwnPropertySymbols` exposes them.
> - **`WeakMap`-keyed** is the pre-2022 class alternative.
> - **Pick closure** for: factory / module pattern, destructure safety, DI.
> - **Pick class `#`** for: inheritance, many instances, `instanceof`, OOP team style.
> - **Trap:** assuming `_field` convention is privacy; trusting TS `private` at runtime.

---

**Related:** [private-data-counter.md](./private-data-counter.md) · [counter-ii.md](./counter-ii.md) · [module-pattern-iife.md](./module-pattern-iife.md) · [factory-with-injected-deps.md](./factory-with-injected-deps.md) · [`03-prototype/private-static-fields.md`](../03-prototype/private-static-fields.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md), [`concepts/prototype.md`](../../concepts/prototype.md)
