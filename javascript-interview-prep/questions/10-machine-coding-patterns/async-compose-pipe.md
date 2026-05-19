# Async `compose` / `pipe` — chain async functions

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [function-composition.md](./function-composition.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** Ramda `R.pipeP`, Koa/Express middleware patterns. Frequent at staff-level Node interviews.

---

## 1. Problem statement

**Signature**
```ts
function pipeAsync<T>(...fns: Array<(x: T) => T | Promise<T>>): (x: T) => Promise<T>;
function composeAsync<T>(...fns: Array<(x: T) => T | Promise<T>>): (x: T) => Promise<T>;
```

**Input / Output examples**

| Setup                                                            | Behaviour                                              |
|-------------------------------------------------------------------|---------------------------------------------------------|
| `pipeAsync(parse, enrich, persist)(input)`                        | sequential `.then` chain; awaits each                  |
| Any step throws                                                   | rejection short-circuits remaining steps              |
| Mixed sync + async fns                                            | both work; `.then` autoboxes                          |
| `pipeAsync()(x)`                                                  | identity → `Promise.resolve(x)`                       |
| Input is already a Promise                                        | `Promise.resolve(x)` unwraps it                       |

**Constraints**
- Each step unary; returns either value or thenable.
- `reduce` for pipe (L→R), `reduceRight` for compose (R→L).
- Seed: `Promise.resolve(x)` — handles "x might be a thenable" for free.
- Errors short-circuit via standard Promise rejection.

---

## 2. Plain-English restatement

Same idea as sync `pipe`/`compose` but each step may return a Promise. Strung together via `.then`, so the next step waits for the previous step's promise to resolve. Mixed sync/async fns just work because `.then(fn)` auto-wraps a sync return in `Promise.resolve`. If any step rejects, the rest are skipped and the failure surfaces at the final `await`.

---

## 3. Why this matters in interviews

The sync version is a one-liner; the async variant forces you to combine **`Array.prototype.reduce`**, **promise chaining**, the **`Promise.resolve` seed trick**, and an understanding of why direction matters. It shows up everywhere in real Node code: Koa middleware, Apollo request transforms, ETL pipelines, retry-then-timeout-then-circuit-breaker decorator stacks. Senior bar: explain the laziness — `acc.then(fn)` (returned eagerly) vs `await acc; await fn(...)` (forces serial execution at compose-time).

---

## 4. Mental model

A **promise conveyor belt**:

```
   pipeAsync(parse, enrich, validate, persist)(input):

     Promise.resolve(input)
            │
            ▼
       .then(parse)         resolves to {id:42}
            │
            ▼
       .then(enrich)        resolves to {id:42, ts:...}
            │
            ▼
       .then(validate)      sync; returns object as-is
            │
            ▼
       .then(persist)       resolves to {id:42, ts:..., saved:true}
            │
            ▼
       await → final value
```

Each `.then(fn)` is a microtask hop. Sync fns slot in naturally because `.then` autoboxes their return.

**On reject:**
```
.then(parse) → ok
.then(enrich) → REJECT (throws / returns rejected)
.then(validate) ⇢ skipped
.then(persist)  ⇢ skipped
.catch / await throws
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `pipeAsync()(42)` return — `42` or `Promise.resolve(42)`?
> 2. If step 2 throws synchronously, do steps 3 and 4 run?
> 3. Why use `Promise.resolve(x)` as the seed instead of just `x`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `for-of` with `await`
```js
async function pipe(...fns) {
  return async (x) => {
    for (const fn of fns) x = await fn(x);
    return x;
  };
}
```
Works and is arguably clearer. Downside: the inner function is now `async`, which always adds a microtask hop even for sync-only chains. Interviewers accept this, but the `reduce` version earns FP-flavour points.

### Wrong attempt 2: forget the seed value
```js
fns.reduce((acc, fn) => acc.then(fn), Promise.resolve())  // BUG
```
First `fn` receives `undefined`, not `x`. Pass `x` to `Promise.resolve(x)`.

### Wrong attempt 3: `await` inside reducer body
```js
fns.reduce(async (acc, fn) => (await acc, fn(await acc)), Promise.resolve(x))
```
Forces every reducer step to be async-evaluated at compose-time and breaks laziness. Use `acc.then(fn)` — pure promise composition.

---

## 7. The unlocking insight

> **`reduce` with `Promise.resolve(x)` as seed and `acc.then(fn)` as combiner. Mixed sync/async works because `.then` autoboxes. `reduceRight` for compose.**

Three properties:

1. **`Promise.resolve(x)`** as the seed — unwraps if `x` is already a thenable.
2. **`acc.then(fn)`** is lazy — builds a single chain that resolves end-to-end.
3. **Errors short-circuit** via standard Promise rejection — no special handling needed.

The whole implementation is two lines.

---

## 8. Solution (annotated)

```js
function pipeAsync(...fns) {
  return function (x) {
    return fns.reduce(                                          // step 1: L→R reduce
      (acc, fn) => acc.then((v) => fn.call(this, v)),           // step 2: chain via .then
      Promise.resolve(x),                                        // step 3: seed wraps x
    );
  };
}

function composeAsync(...fns) {
  return function (x) {
    return fns.reduceRight(                                      // R→L reduce
      (acc, fn) => acc.then((v) => fn.call(this, v)),
      Promise.resolve(x),
    );
  };
}

// Error-recovering variant: each fn is [transform, errorHandler] pair
function pipeAsyncWithRecovery(...steps) {
  return (x) =>
    steps.reduce(
      (acc, [fn, errFn]) => acc.then(fn, errFn),                // step 4: catch per step
      Promise.resolve(x),
    );
}
```

**Try it yourself**

```js
const parse    = (s) => JSON.parse(s);
const enrich   = async (obj) => ({ ...obj, ts: Date.now() });
const validate = (obj) => { if (!obj.id) throw new Error('no id'); return obj; };
const persist  = async (obj) => ({ ...obj, saved: true });

const handler = pipeAsync(parse, enrich, validate, persist);

const out = await handler('{"id":42,"name":"x"}');
// { id: 42, name: 'x', ts: 1234567890, saved: true }

// Reject case
const bad = pipeAsync(parse, enrich, validate, persist);
try { await bad('{"name":"no-id"}'); } catch (e) { console.error(e.message); }  // "no id"
```

---

## 9. Step-by-step dry run

```
handler('{"id":42}') called:

t=0    seed = Promise.resolve('{"id":42}')
       reduce step 1: seed.then(parse)
                       → microtask hop, parse('{"id":42}') = {id:42}
                       → resolves to {id:42}

       reduce step 2: prev.then(enrich)
                       → microtask hop, enrich({id:42}) returns Promise
                       → unwraps to {id:42, ts:1234}

       reduce step 3: prev.then(validate)
                       → microtask hop, validate sync
                       → returns {id:42, ts:1234}

       reduce step 4: prev.then(persist)
                       → microtask hop, persist returns Promise
                       → unwraps to {id:42, ts:1234, saved:true}

       await → final value
```

If `validate` throws `Error('no id')`:

```
       reduce step 3: prev.then(validate)
                       → throws synchronously inside .then handler
                       → resulting promise REJECTS with Error('no id')

       reduce step 4: prev.then(persist)
                       → rejected promise.then(persist) → skip handler
                       → propagate rejection

       await → throws
```

---

## 10. Common confusion + traps

1. **`Promise.resolve()` (no arg)** — first fn gets `undefined`.
2. **`await` inside reducer body** — forces async wrapping, kills laziness.
3. **Confusing pipe vs compose direction** — always state explicitly.
4. **Multi-arg first fn** — `pipeAsync` is point-free. Pass objects/tuples if you need multi-args.
5. **`this` lost in chain** — bind methods first or use arrow functions for steps.
6. **Mixed sync/async**: NOT a problem (`.then` autoboxes). Don't manually wrap sync fns.
7. **Errors are values** — every step propagates rejection; only `.catch` or pair handlers can recover.

---

## 11. Senior follow-ups & variants

### Variant 1 — Per-step error recovery
```js
pipeAsyncWithRecovery(
  [parse, (e) => ({ raw: '' })],
  [enrich, null],
  ...
)
```
Allows one step to both transform and handle errors from above.

### Variant 2 — Cancellable pipeline
Pass `AbortSignal`; each step checks `signal.aborted`. Or wrap with `Promise.race([chain, abortPromise])`.

### Variant 3 — Branching Either/Result
Each step returns `{ok: true, value} | {ok: false, error}`. Pipe short-circuits on error without throwing.

### Variant 4 — Parallel fan-out
`fanOut(a, b, c)(x) === Promise.all([a(x), b(x), c(x)])`. Different semantics — clarify which.

### Variant 5 — Middleware-style (Koa)
Each fn `(ctx, next)`; chooses when to call next. Allows pre- and post-processing around inner fns.

---

## 12. How to think aloud

> "`fns.reduce((acc, fn) => acc.then(fn), Promise.resolve(x))`. Drill this. `Promise.resolve(x)` as seed handles 'x might be a thenable' for free. Mixed sync/async fns work because `.then` autoboxes both. Empty `pipe()` returns identity. Errors short-circuit via promise rejection — no special handling. `reduceRight` for compose. Trap: `Promise.resolve()` with no arg → first fn gets undefined. Trap: `await` inside reducer body forces eager async and kills laziness. Senior bonus: per-step error handlers via `[fn, errFn]` pairs, or Either/Result for exception-free pipelines."

---

## 13. 60-second revision

> - **`pipeAsync(...fns)(x) = fns.reduce((acc, fn) => acc.then(fn), Promise.resolve(x))`**.
> - **`composeAsync`** = same with `reduceRight`.
> - **Seed** is `Promise.resolve(x)` — unwraps if `x` is thenable.
> - **Mixed sync/async** just works — `.then` autoboxes returns.
> - **Empty** = identity (Promise.resolve(x)).
> - **Reject short-circuits**; surfaces at final await.
> - **Each fn unary** — state pipe vs compose direction.
> - **Trap:** `Promise.resolve()` (no arg); `await` inside reducer; losing `this`.

---

**Related:** [function-composition.md](./function-composition.md) · [`04-promises/async-reduce.md`](../04-promises/async-reduce.md) · [`04-promises/sequential-vs-parallel-async-map.md`](../04-promises/sequential-vs-parallel-async-map.md) · [retry-with-jitter-and-budget.md](./retry-with-jitter-and-budget.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
