# Promises & async/await

## TL;DR
- A Promise is a state machine: **pending → fulfilled | rejected**. Once settled, immutable.
- `.then(onFulfilled, onRejected)` returns a NEW promise. Throwing in a `.then` callback rejects the returned promise.
- `async` functions always return a Promise. `await x` suspends and resumes on the **microtask queue**.
- **Top-level await** works only in ES modules (and Node.js with `"type": "module"`).
- `Promise.all` fails fast; `allSettled` never rejects; `race` settles on first; `any` resolves on first fulfilled or rejects with `AggregateError`.

## Why backend interviewers care
- Every Node.js I/O is promise-based now (fs/promises, fetch, db drivers). Mishandled rejections kill processes (`--unhandled-rejections=strict`).
- Concurrency control (promise pools), retries with backoff, and timeouts via `AbortController` are bread-and-butter backend work.
- async/await pitfalls (sequential vs parallel, missing `return`) cause the most subtle prod bugs interviewers love to probe.

## Core mental model
A Promise wraps an asynchronous outcome. Its `then` handlers are scheduled on the **microtask queue**, which runs after the current synchronous task completes and *before* the next macrotask (timers, I/O). This is why `Promise.resolve().then(...)` runs before a `setTimeout(..., 0)`.

```js
const p = new Promise((resolve, reject) => {
  // executor runs SYNCHRONOUSLY now
  setTimeout(() => resolve(42), 100);
});
p.then(v => console.log(v));     // microtask after timer fires
```

The promise constructor's executor is synchronous; only `resolve`/`reject` plus `then` callbacks are async. `resolve` "adopts" another thenable — if you `resolve(promise)`, the outer promise mirrors the inner.

`async`/`await` is sugar on top: `await p` is roughly `.then(v => /* resume with v */, e => /* throw e at resume site */)`. Each `await` yields a microtask.

Errors propagate down the chain until caught. An uncaught rejection becomes `unhandledRejection` — in Node 15+, defaults to crashing the process.

## Syntax cheat sheet
```js
// Creation
const p1 = Promise.resolve(1);
const p2 = Promise.reject(new Error("x"));
const p3 = new Promise((res, rej) => res(42));

// then / catch / finally
p1.then(v => v + 1)
  .then(v => console.log(v))     // 2
  .catch(err => console.error(err))
  .finally(() => console.log("done")); // runs regardless; value passes through

// Throw inside then → next catch
Promise.resolve().then(() => { throw new Error("boom"); }).catch(e => e.message); // "boom"

// async/await
async function f() {
  try {
    const v = await fetchSomething();
    return v;
  } catch (e) {
    console.error(e);
    throw e; // re-throw
  }
}
// async fn ALWAYS returns a Promise
const result = f(); // Promise<...>

// Top-level await (ESM only)
// const data = await fetch(url);

// Combinators
Promise.all([p1, p2]);            // resolves with [v1, v2]; rejects on first failure
Promise.allSettled([p1, p2]);     // [{status:"fulfilled",value}|{status:"rejected",reason}]
Promise.race([p1, p2]);           // settles with first to settle (fulfill OR reject)
Promise.any([p1, p2]);            // first fulfilled; AggregateError if all reject

// Parallel
const [a, b] = await Promise.all([loadA(), loadB()]);

// Serial (rare but useful)
const a = await loadA();
const b = await loadB(a);

// for-await-of (async iterable)
for await (const chunk of readable) { process(chunk); }

// AbortController for cancellation
const ac = new AbortController();
fetch(url, { signal: ac.signal }).catch(e => e.name === "AbortError");
setTimeout(() => ac.abort(), 1000);

// Convert callback to promise (legacy node API)
const { promisify } = require("util");
const readFile = promisify(require("fs").readFile);

// Promise as one-shot timer
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
```

## Edge cases & interview traps
1. **`new Promise(executor)` executor runs synchronously** — common gotcha when interviewers ask "what logs first?".
2. **`return` is required inside `.then` to chain** — `then(v => somePromise)` chains; `then(v => { somePromise; })` doesn't (fire-and-forget).
3. **`await` in a `forEach` callback does NOTHING** — `forEach` ignores the returned promise; loop doesn't wait. Use `for...of` instead.
4. **`Promise.all` with mixed values resolves with values** — non-promises are wrapped via `Promise.resolve`.
5. **Rejection without `.catch` → unhandledRejection** — in Node 15+, exits the process by default.
6. **`finally` does NOT swallow errors** but its own thrown error replaces the chain's outcome.
7. **`return await x` vs `return x`** — inside `try/catch`, `return await` lets local catch handle rejection; bare `return` passes the promise out.
8. **Microtask starvation**: recursive `.then` can starve macrotasks (timers, I/O) — also true for Node's `process.nextTick`.
9. **`Promise.race([])` returns a pending promise forever**; same with `all([])` → resolves with `[]`; `any([])` → rejects with empty `AggregateError`.
10. **Async functions catch sync errors too** — `throw` inside async becomes a rejection.
11. **Resolving with another promise adopts its state** — `resolve(p)` → outer mirrors `p`.
12. **`.then(onF, onR)` vs `.then(onF).catch(onR)`** — the latter catches errors thrown *inside* `onF`; the former does not.
13. **Awaiting a non-promise** just resolves immediately on microtask — still costs one tick.
14. **`AbortSignal` errors are DOMException with name "AbortError"** — match by `.name`, not `instanceof`.
15. **Mixing top-level `await` with circular ESM imports can deadlock** the module graph.
16. **`async` arrow without `await` is fine**, but linters flag — function still returns a Promise.
    ```js
    const f = async () => 1;
    f(); // Promise { 1 } — still a Promise
    ```

## Interview worked examples

### Example 1 — `sleep` utility
**Asked as:** "Write `sleep(ms)` that returns a Promise resolving after `ms` milliseconds."

I'd say: "Wrap setTimeout in a new Promise. The executor runs synchronously and schedules the resolve. This is the foundation for delays, retries, and timeouts."

```js
const sleep = (ms) => new Promise(res => setTimeout(res, ms));
await sleep(500); // pauses for 500ms inside an async fn
```

**What the interviewer is testing:** Comfort wrapping callback APIs as promises.
**Sharp follow-up they often ask:** "Make it cancellable with an AbortSignal." → check `signal.aborted`, attach `signal.addEventListener('abort', () => { clearTimeout(t); reject(new DOMException('aborted', 'AbortError')); })`.

### Example 2 — Parallel fetch with `Promise.all`
**Asked as:** "Fetch user, orders, and address concurrently for a profile page."

I'd say: "Start all three requests so they fly in parallel, then await Promise.all — total time is max(latencies), not sum. Critical for backend latency. Note Promise.all fails fast: one rejection kills the others' results."

```js
async function getProfile(userId) {
  const [user, orders, address] = await Promise.all([
    fetch(`/u/${userId}`).then(r => r.json()),
    fetch(`/u/${userId}/orders`).then(r => r.json()),
    fetch(`/u/${userId}/address`).then(r => r.json()),
  ]);
  return { user, orders, address };
}
```

**What the interviewer is testing:** Knowing when to parallelize vs sequence; awareness of fail-fast.
**Sharp follow-up they often ask:** "Make address optional — don't fail the whole call if it errors." → use `Promise.allSettled`, or wrap address in `.catch(() => null)`.

### Example 3 — Sequential reduce of async tasks
**Asked as:** "Run a list of async functions in order, each receiving the previous result."

I'd say: "I'll use `Array.reduce` over an awaited accumulator. Each step waits for the previous Promise before kicking off the next. This is the right pattern when later tasks DEPEND on earlier results — otherwise use `Promise.all`."

```js
const runSerial = (tasks, seed) =>
  tasks.reduce((p, task) => p.then(task), Promise.resolve(seed));

await runSerial([
  async (x) => x + 1,
  async (x) => x * 2,
  async (x) => x.toString(),
], 1); // "4"
```

**What the interviewer is testing:** Sequential vs parallel; reduce-as-promise-chain idiom.
**Sharp follow-up they often ask:** "What if a task throws midway?" → the chain rejects; subsequent tasks don't run. To continue, wrap each task's call in a try/catch inside the reducer.

### Example 4 — Timeout via `Promise.race`
**Asked as:** "Wrap any promise so it rejects after N ms."

I'd say: "Race the input promise against a setTimeout that rejects. Whichever settles first wins. The downside: the original work keeps running in the background — use AbortController if you need true cancellation."

```js
const withTimeout = (p, ms) =>
  Promise.race([
    p,
    new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms)),
  ]);

await withTimeout(fetch(url), 3000);
```

**What the interviewer is testing:** `Promise.race` semantics + understanding cancellation.
**Sharp follow-up they often ask:** "How would you also abort the in-flight fetch?" → pass `signal` to fetch, call `controller.abort()` from the timeout branch.

### Example 5 — Retry with exponential backoff
**Asked as:** "Implement retry-with-backoff for a flaky HTTP call."

I'd say: "Wrap the call in a for-loop that catches, sleeps with exponentially-growing delay, and retries up to N times. Re-throw the last error so callers can react. Add jitter in production to avoid synchronized retry storms."

```js
async function retry(fn, retries = 3, base = 200) {
  for (let i = 0; i <= retries; i++) {
    try { return await fn(); }
    catch (e) {
      if (i === retries) throw e;
      await new Promise(r => setTimeout(r, base * 2 ** i));
    }
  }
}
await retry(() => fetch("/flaky"));
```

**What the interviewer is testing:** Loops with await; control flow around try/catch.
**Sharp follow-up they often ask:** "Make it abortable mid-retry." → check `signal.aborted` at the top of each loop iteration; throw if aborted.

### Example 6 — Promisify a Node-style callback
**Asked as:** "Convert `fs.readFile(path, cb)` to return a Promise without using `util.promisify`."

I'd say: "Wrap the call in a new Promise; the callback's error becomes reject, value becomes resolve. This is the bridge between legacy Node APIs and modern async/await. Curry the function so you get a reusable promisified version."

```js
const promisify = (fn) => (...args) =>
  new Promise((res, rej) =>
    fn(...args, (err, value) => (err ? rej(err) : res(value))));

const readFileP = promisify(require("fs").readFile);
const data = await readFileP("/etc/hosts", "utf8");
```

**What the interviewer is testing:** Bridging callback ↔ promise paradigms.
**Sharp follow-up they often ask:** "What if the callback uses multiple result args (not just `err, value`)?" → resolve with an array of the trailing args.

## Common machine-coding patterns
- **Promisify a callback** — when used: legacy Node APIs. Sketch:
  ```js
  const pify = (fn) => (...args) =>
    new Promise((res, rej) =>
      fn(...args, (err, val) => err ? rej(err) : res(val)));
  ```
- **Promise.all polyfill** — when used: interview classic. Sketch:
  ```js
  function pAll(arr) {
    return new Promise((res, rej) => {
      const out = []; let done = 0;
      if (!arr.length) return res([]);
      arr.forEach((p, i) =>
        Promise.resolve(p).then(v => { out[i] = v; if (++done === arr.length) res(out); }, rej));
    });
  }
  ```
- **Retry with exponential backoff** —
  ```js
  async function retry(fn, n = 3, base = 200) {
    for (let i = 0; i < n; i++) {
      try { return await fn(); }
      catch (e) { if (i === n - 1) throw e; await sleep(base * 2 ** i); }
    }
  }
  ```
- **Promise pool (concurrency limit)** —
  ```js
  async function pool(tasks, limit) {
    const ret = []; const exec = new Set();
    for (const t of tasks) {
      const p = Promise.resolve().then(t);
      ret.push(p);
      exec.add(p);
      p.finally(() => exec.delete(p));
      if (exec.size >= limit) await Promise.race(exec);
    }
    return Promise.all(ret);
  }
  ```
- **Timeout wrapper** —
  ```js
  const withTimeout = (p, ms) =>
    Promise.race([p, new Promise((_, rej) =>
      setTimeout(() => rej(new Error("timeout")), ms))]);
  ```
- **Deferred (resolver-exposed promise)** — when used: bridging events to promises.
  ```js
  function deferred() {
    let res, rej; const p = new Promise((r, j) => { res = r; rej = j; });
    return { promise: p, resolve: res, reject: rej };
  }
  ```

## Backend-specific notes
For HTTP servers, **parallelize independent I/O with `Promise.all`** — a route that does `await db.users.find()` then `await db.orders.find()` doubles latency for no reason. But beware: `Promise.all` fails fast — one fail rejects the whole, leaving other in-flight queries running uselessly. For "best effort", use `Promise.allSettled`.

**Connection pools** must own their concurrency — don't fire 10k `await query()` calls expecting magic; use `pool` size and a queue (most drivers do this internally but verify). For external HTTP, build a promise pool of e.g. 20 to avoid overwhelming the downstream.

**Cancellation**: use `AbortController` everywhere it's accepted (fetch, fs/promises). On HTTP, propagate the request's abort signal to downstream calls so a closed client connection doesn't leave queries running.

**Top-level await in ESM** is great for bootstrapping (load config, connect db) but blocks the module graph — keep it minimal.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ PROMISES — DAY-BEFORE CRAM                               │
├──────────────────────────────────────────────────────────┤
│ • States: pending → fulfilled | rejected (immutable)     │
│ • then handlers run as MICROTASKS (before next macro)    │
│ • Executor runs SYNC; resolve/reject async               │
│ • async fn always → Promise; await yields one microtask  │
│ • forEach + await = silent bug; use for...of             │
│ • Promise.all: fail-fast; allSettled: never rejects      │
│ • race: first to settle; any: first fulfilled            │
│ • return await vs return inside try/catch matters        │
│ • resolve(p) adopts p's state                            │
│ • Unhandled rejection → process crash (Node 15+)         │
│ • AbortController.signal → cancel fetch/fs               │
│ • retry: try/catch + sleep(base*2^i)                     │
│ • pool: Set + race(Set) when size >= limit               │
│ • timeout: race(p, sleep+reject)                         │
│ • Top-level await only in ESM; blocks module graph       │
└──────────────────────────────────────────────────────────┘
```
