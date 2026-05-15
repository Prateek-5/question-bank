# Implement `compose` / `pipe` for async functions

## Source
- Canonical FP machine-coding question (Ramda `R.pipeP`, Redux middleware composition, Express middleware chains).
- Common at staff-level Node interviews — middleware pipelines, request transformers.

## Why this question matters in interviews
`pipe`/`compose` is the FP litmus test. The sync version is a one-liner; the async version forces you to combine **`Array.prototype.reduce`**, **promise chaining**, **the `Promise.resolve` seed trick**, and an understanding of why `reduceRight` exists. It also probes whether you understand the **direction** distinction: `pipe(a, b, c)(x) === c(b(a(x)))` (left-to-right reading order) while `compose(a, b, c)(x) === a(b(c(x)))` (math convention). This shows up everywhere in real Node backends: Koa middleware, Apollo `applyMiddleware`, RxJS `pipe`, Express request transforms, ETL pipelines, retry-then-timeout-then-circuit-breaker decorator stacks.

## Concepts involved

### Syntax to lock in
```js
const pipe = (...fns) => (x) =>
  fns.reduce((acc, fn) => acc.then(fn), Promise.resolve(x));

const compose = (...fns) => (x) =>
  fns.reduceRight((acc, fn) => acc.then(fn), Promise.resolve(x));

// usage
const pipeline = pipe(parse, validate, persist, log);
const result = await pipeline(rawInput);
```

### Runtime / engine behavior
- `Promise.resolve(x)` is the **seed**: turns the input into a Promise so the chain starts with a thenable. If `x` is already a Promise, `Promise.resolve` is a no-op (it unwraps).
- Each `.then(fn)` returns a **new Promise**. Synchronous `fn`s work transparently because `.then` boxes their return value into a fulfilled Promise. Async `fn`s work because `.then` unwraps any returned thenable.
- `reduce` walks left-to-right: `pipe(a, b)(x)` becomes `Promise.resolve(x).then(a).then(b)`. `reduceRight` walks right-to-left: `compose(a, b)(x)` becomes `Promise.resolve(x).then(b).then(a)`.
- Error propagation: if any `fn` throws or returns a rejected Promise, the chain short-circuits to the first rejection handler. With no `.catch`, it surfaces as an unhandled rejection at the await site.

### Edge cases (these are the interview traps)
1. **Empty pipeline** — `pipe()` must return an identity function: `x => Promise.resolve(x)`. With no `fns`, `reduce` returns the seed unchanged. Good — works for free.
2. **Synchronous functions mixed with async** — works without special-casing because `.then(fn)` accepts both. Don't wrap sync fns in `Promise.resolve` manually.
3. **Each `fn` is unary** — `pipe`/`compose` is point-free composition. Each step takes exactly one arg. Multi-arg pipelines need partial application or destructuring at each stage.
4. **`this` binding** — composed functions lose `this`. If a step is a method, bind it first: `pipe(obj.method.bind(obj), ...)`.
5. **Error short-circuit** — once a step rejects, all downstream `.then(fn)` are skipped. Add a `.catch` at the end or in the middle for recovery steps.
6. **Order of reading** — `pipe(a, b, c)` reads naturally L→R ("first a, then b, then c"). `compose(a, b, c)` reads R→L (math: `a ∘ b ∘ c`). State which one when answering — interviewers ask both names.
7. **Don't use `await` in the reducer body** — `acc.then(fn)` is correct and lazy; `await acc` would force serial execution at compose-time and break the laziness that lets you `pipe(...)` once and call repeatedly.
8. **Single-arg, single-return rule** — if you need multiple values flowing, pass an object/tuple. This is where pipelines get awkward; many candidates abandon and reach for raw `async/await`. State the trade-off.

## Brute force approach
"I'll `await` each function manually in a loop." Like:
```js
async function pipe(...fns) {
  return async (x) => {
    for (const fn of fns) x = await fn(x);
    return x;
  };
}
```
This actually works and is **arguably clearer for async-only pipelines** — interviewers will accept it. The downside is the inner function is now `async`, which adds a microtask hop even when all `fns` are sync. The `reduce` version is the FP-flavored answer and gives you nice points for "I know this is `Array.prototype.reduce` with `Promise.resolve` as the seed." Mention both.

## Optimal approach
`reduce` with `Promise.resolve(x)` as the seed and `.then(fn)` as the combiner. O(n) in number of steps. O(1) extra memory (no intermediate array). Each step is a single microtask hop, which is the price of asynchrony.

## Solution (JavaScript)

```js
/**
 * Left-to-right async pipe: pipe(a, b, c)(x) === c(b(a(x))) with promises unwrapped.
 * @param  {...Function} fns  unary functions; each may be sync or return a thenable
 * @returns {(x: any) => Promise<any>}
 */
function pipeAsync(...fns) {
  return function (x) {
    return fns.reduce((acc, fn) => acc.then((v) => fn.call(this, v)), Promise.resolve(x));
  };
}

/**
 * Right-to-left async compose: compose(a, b, c)(x) === a(b(c(x))).
 */
function composeAsync(...fns) {
  return function (x) {
    return fns.reduceRight((acc, fn) => acc.then((v) => fn.call(this, v)), Promise.resolve(x));
  };
}
```

For a version that preserves `this` binding through a method chain on a host object:
```js
const pipeBound = (host, ...fns) => (x) =>
  fns.reduce((acc, fn) => acc.then(fn.bind(host)), Promise.resolve(x));
```

## Step-by-step dry run

Input:
```js
const parse    = (s) => JSON.parse(s);
const enrich   = async (obj) => ({ ...obj, ts: Date.now() });
const validate = (obj) => { if (!obj.id) throw new Error('no id'); return obj; };
const persist  = async (obj) => { /* db.save */ return { ...obj, saved: true }; };

const handler = pipeAsync(parse, enrich, validate, persist);
const out = await handler('{"id":42,"name":"x"}');
```

Trace:
- `handler('{"id":42,"name":"x"}')` starts: seed = `Promise.resolve('{"id":42,"name":"x"}')`.
- `reduce` step 1: `seed.then(parse)` → Promise that resolves to `{id:42, name:'x'}`.
- step 2: `.then(enrich)` → enrich is async, returns Promise → unwrapped to `{id:42, name:'x', ts: 17... }`.
- step 3: `.then(validate)` → sync, `id` is truthy, returns object as-is.
- step 4: `.then(persist)` → returns Promise that resolves to `{id:42, name:'x', ts:..., saved:true}`.
- `await handler(...)` resolves to the final object.

If step 3 throws (`id` missing): the rejection propagates past `persist` (its `.then` handler is skipped) and surfaces at `await`.

## Important takeaways

**Syntax to memorize**
- `fns.reduce((acc, fn) => acc.then(fn), Promise.resolve(x))` — drill this until you can write it cold.
- `reduceRight` for `compose`. `reduce` for `pipe`.
- `Promise.resolve(x)` is the seed — handles "x might already be a promise" for free.

**Patterns to reuse**
- Reduce-over-promises is the same shape as **`asyncReduce`** (a separate problem) and as Redux's `applyMiddleware` (which composes higher-order functions, not values).
- "Sync interface, async-capable internals" — `pipe` accepts mixed sync/async fns without branching. This is the elegance of `.then` autoboxing.

**Common mistakes**
- Starting with `Promise.resolve()` (no arg) instead of `Promise.resolve(x)` — first `fn` gets `undefined`.
- Using `await` inside `reduce`'s reducer instead of returning `acc.then(fn)` — works but forces the outer to be `async` and adds a microtask per iteration.
- Confusing `pipe`/`compose` direction — always state which one you're naming.
- Forgetting that each `fn` must be unary. Composing `fn(a, b)` doesn't work without partial application.

**Related questions**
- Synchronous `pipe`/`compose` (same shape, no `.then`).
- `asyncReduce(arr, fn, init)` — different (reduce over a data array, not a function array).
- Koa/Express middleware composition (functions are `(ctx, next) => ...` — different signature).
- Redux `compose` for store enhancers.

## Variants

1. **Error-recovering pipeline** — each step is `[fn, errHandler]`. Build with `.then(fn, errHandler)`. Lets a single step both transform and handle errors from above.

2. **Cancellable pipeline** — pass an `AbortSignal`; each step checks `signal.aborted` and short-circuits. Or wrap the chain so the seed promise can reject externally.

3. **Branching pipe (Either/Result)** — each step returns `{ok: true, value} | {ok: false, error}` and downstream steps short-circuit on error. Avoids exception-based control flow; common in TypeScript-heavy codebases.

4. **Parallel fan-out** — `parallelPipe(a, b, c)(x)` runs all three on the same input concurrently and returns `[ra, rb, rc]`. Different semantics — clarify which the interviewer wants.

## Revision notes

> **async pipe/compose — 45 second recap**
> - `pipe(...fns)(x) = fns.reduce((acc, fn) => acc.then(fn), Promise.resolve(x))`.
> - `compose` is the same with `reduceRight`.
> - `Promise.resolve(x)` seed handles "x might be a thenable" for free.
> - Mixed sync/async fns just work — `.then(fn)` autoboxes both.
> - Empty `pipe()` = identity (`Promise.resolve(x)`). Errors short-circuit to the next `.catch`.
> - Each fn must be unary. State `pipe` vs `compose` direction explicitly.
> - Trap: `Promise.resolve()` with no arg; using `await` inside reducer body; losing `this`.
