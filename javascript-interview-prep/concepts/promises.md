# Promises & async/await

> **Senior-mentor framing:** A Promise is the cleanest abstraction JavaScript has for saying "this value isn't here yet, but it will be (or it'll fail)." Before promises, async JS was a tangle of nested callbacks ("callback hell"). Promises gave us a *value-like* thing for the future, with a uniform error-propagation channel. `async`/`await` is just nicer syntax on top.

## Why this concept exists (first principles)

Imagine ordering coffee at a busy cafe. You don't stand at the counter blocking everyone behind you while it brews. The barista hands you a **buzzer** — a small, immediate object that represents the *future* coffee. You sit down, do other things, and when the buzzer lights up, you go pick up your drink (or learn that the espresso machine broke and there's no coffee).

That buzzer is a Promise.

- **State:** the buzzer can be **pending** (still brewing), **fulfilled** (coffee ready, here's the cup), or **rejected** (machine broke, here's the reason).
- **Immutable settling:** once it lights up, it never goes back to pending. A buzzer fires exactly once.
- **`.then(cb)`:** "when the buzzer lights up successfully, run `cb` with the drink."
- **`.catch(cb)`:** "if the order failed, run `cb` with the failure reason."

`async`/`await` is the syntactic sugar that lets you write code as if you were waiting at the counter — but under the hood, the function yields control back to the event loop at every `await` and resumes later as a microtask.

> **Mental Model:** A Promise is a **container for a future value** + a **single-shot state machine** + an **error channel that propagates down the chain**. Three things in one. Once you internalize that, every Promise API makes sense.

## Why interviewers care

- Every Node.js I/O is promise-based now (fs/promises, fetch, db drivers). Mishandled rejections kill processes (`--unhandled-rejections=strict`).
- Concurrency control (promise pools), retries with backoff, and timeouts via `AbortController` are bread-and-butter backend work.
- async/await pitfalls (sequential vs parallel, missing `return`) cause the most subtle prod bugs interviewers love to probe.
- Output-prediction questions mixing `Promise.then`, `await`, and `setTimeout` test event-loop literacy *through* the promise lens.

## Common beginner confusion

- "Promises are async, so the executor runs later." — **No.** The executor `(resolve, reject) => { ... }` runs **synchronously** the moment you call `new Promise()`. Only the `then` callbacks are async.
- "I can change a fulfilled promise to rejected later." — **No.** Settled is final, forever.
- "`await` makes my code blocking." — **No.** It blocks *the async function* but yields control to the event loop. Other code keeps running.
- "Promises run in parallel." — Tricky. The underlying *I/O* may run in parallel (network, fs), but Promise state transitions and `.then` callbacks always run on the single JS thread, one at a time.
- "Returning a value from `.then` doesn't matter." — **It absolutely does.** A returned promise is chained-into; a fire-and-forget call is silently dropped.
- "`.catch` catches everything." — Only errors from *before* it in the chain. Errors after the last `.catch` (or inside `.catch` itself) become unhandled.

## Progressive concept building

**Beginner level:** "A Promise is `new Promise((resolve, reject) => ...)`. Call `.then(v => ...)` to get the value, `.catch(e => ...)` for errors."

**Intermediate level:** "`async`/`await` desugars to `.then` chains. Every `await` yields a microtask. `Promise.all` parallelizes, `Promise.race` picks the first to settle, `allSettled` never rejects, `any` returns the first fulfilled."

**Advanced level:** "Executor is sync. `resolve(anotherPromise)` adopts state. Microtask scheduling means `.then` always runs after the current sync block but before macrotasks. Errors propagate through the chain until caught; uncaught rejections crash Node 15+."

**Interview expectation:** You can write a `sleep`, a `retry` with backoff, a `timeout` wrapper, a `promisify`, and a concurrency-limited `pool` — and explain microtask vs macrotask scheduling implications for each.

## Promise state machine — visualized

```
                  ┌─────────────────────┐
                  │                     │
                  │      PENDING        │   ← created, not yet settled
                  │  (initial state)    │
                  │                     │
                  └─────┬───────────┬───┘
                        │           │
                  resolve(v)    reject(e)
                        │           │
                        v           v
            ┌─────────────────┐ ┌─────────────────┐
            │   FULFILLED     │ │    REJECTED     │
            │   (value = v)   │ │   (reason = e)  │
            │   *immutable*   │ │   *immutable*   │
            └─────────────────┘ └─────────────────┘
                  │                       │
                  │ .then(onF, ...)       │ .then(..., onR) / .catch(onR)
                  v                       v
            (new promise,             (new promise,
             settles based on          settles based on
             onF return value)         onR return value)
```

- **Settled** = either FULFILLED or REJECTED. Once settled, the state and value/reason cannot change.
- **`.then`/.catch return a NEW promise** — that's why chaining works.
- **Throwing inside `.then(onF)` → next promise REJECTS** with the thrown error. This is the unified error channel.

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

> **Mental Model — Two-layer thinking:**
> 1. **Value layer:** "What value will eventually be here?"
> 2. **Scheduling layer:** "When does the `.then` callback run on the event loop?"
> Senior devs always think in both layers. Bugs come from forgetting layer 2.

A Promise wraps an asynchronous outcome. Its `then` handlers are scheduled on the **microtask queue**, which runs after the current synchronous task completes and *before* the next macrotask (timers, I/O). This is why `Promise.resolve().then(...)` runs before a `setTimeout(..., 0)`.

> **Step-by-step walkthrough of the code below:**
> 1. `new Promise(...)` runs the executor **synchronously**. The executor calls `setTimeout(...)` — that schedules a macrotask in 100ms.
> 2. `p.then(...)` registers a callback for when p resolves. p is still pending.
> 3. 100ms later, the timer fires → `resolve(42)` runs → p transitions PENDING → FULFILLED.
> 4. The registered `then` callback is queued as a microtask.
> 5. The microtask drains → `console.log(v)` prints `42`.

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

### Visualizing async/await as a state machine

```
async function f() {            ┌──────────────────────────────────┐
  console.log("A");             │  Step 1: run sync until first    │
  await getUser();              │  await. Suspend, schedule resume │
  console.log("B");             │  as microtask when promise       │
  await getOrders();            │  settles.                        │
  console.log("C");             │                                  │
}                               │  Step 2: when getUser() resolves │
                                │  → continuation logs "B", hits   │
              becomes →         │  next await, suspends again.     │
                                │                                  │
                                │  Step 3: when getOrders() resolves│
                                │  → continuation logs "C", returns│
                                │  → wrapping promise fulfills.    │
                                └──────────────────────────────────┘
```

Each `await` is a "save point": save local state, yield, resume later as a microtask.

## Bridge: from theory to syntax

Now that you see Promises as state machines plus a microtask scheduler, the API surface below should feel like a *toolbox* rather than a list of incantations. Tag each API mentally: "creator", "consumer", "combinator", "control-flow".

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

### Combinator decision table (which one to use)

```
┌─────────────────┬──────────────────────────────────────────────────────┐
│ Promise.all     │ Need ALL results; one failure = whole thing fails.   │
│                 │ Use for required parallel I/O (user + orders +       │
│                 │ address all needed).                                 │
├─────────────────┼──────────────────────────────────────────────────────┤
│ Promise.allSettled │ Need every outcome (success or fail) reported.    │
│                 │ Use for "best-effort" fan-out, audit logs, fan-out   │
│                 │ to N services where partials are OK.                 │
├─────────────────┼──────────────────────────────────────────────────────┤
│ Promise.race    │ First to SETTLE wins (success OR failure).           │
│                 │ Use for timeouts, "whichever endpoint replies first".│
├─────────────────┼──────────────────────────────────────────────────────┤
│ Promise.any     │ First to FULFILL wins. Ignore individual rejections. │
│                 │ Use for "try N mirrors, take first success".         │
└─────────────────┴──────────────────────────────────────────────────────┘
```

## Bridge: edge cases reveal the *real* model

The cheat sheet is the happy path. The traps below are where seniors are separated from juniors — they reveal whether you understand the state machine, the microtask scheduling, and the error-propagation rules.

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

## Bridge: from traps to live interview practice

Now we apply this to the actual interview format. Each example shows the question, how to think aloud, and the step-by-step walkthrough. Practice saying the "how to think aloud" sentences out loud — they're the difference between *knowing* the answer and *explaining* it well.

## Interview worked examples

### Example 1 — `sleep` utility
**Asked as:** "Write `sleep(ms)` that returns a Promise resolving after `ms` milliseconds."

> **How to think aloud:**
> "I want a function returning a Promise that resolves after `ms` ms. The Promise constructor's executor is the right place to call `setTimeout` because it's the one place I get a `resolve` handle. The executor runs synchronously, so the timer is scheduled immediately, and `ms` later the timer fires `resolve()`. The returned promise's `then` callback will then run as a microtask. Simple but it's the foundation for delays, retries, and timeouts."

I'd say: "Wrap setTimeout in a new Promise. The executor runs synchronously and schedules the resolve. This is the foundation for delays, retries, and timeouts."

```js
const sleep = (ms) => new Promise(res => setTimeout(res, ms));
await sleep(500); // pauses for 500ms inside an async fn
```

> **Step-by-step walkthrough:**
> 1. Call `sleep(500)` → new Promise created. Executor runs sync, schedules `setTimeout(res, 500)`.
> 2. The returned Promise is pending. `await` suspends the surrounding async function.
> 3. 500ms later, timer fires → `res()` is called → Promise transitions to FULFILLED.
> 4. The async function's continuation is queued as a microtask → resumes.

**What the interviewer is testing:** Comfort wrapping callback APIs as promises.
**Sharp follow-up they often ask:** "Make it cancellable with an AbortSignal." → check `signal.aborted`, attach `signal.addEventListener('abort', () => { clearTimeout(t); reject(new DOMException('aborted', 'AbortError')); })`.

### Example 2 — Parallel fetch with `Promise.all`
**Asked as:** "Fetch user, orders, and address concurrently for a profile page."

> **How to think aloud:**
> "If I write three `await`s in sequence, each request only starts AFTER the previous one resolves. That's wasteful — they're independent. By starting all three (calling the fetch functions before any `await`) and then awaiting `Promise.all`, the total latency becomes `max(t1, t2, t3)` instead of `t1 + t2 + t3`. The catch: `Promise.all` is fail-fast — one rejection rejects the combined promise, even though the others still finish in the background."

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

> **Step-by-step walkthrough:**
> 1. All three `fetch(...)` calls are invoked immediately — three network requests fly in parallel.
> 2. Each `.then(r => r.json())` chain returns a Promise that resolves to the parsed JSON.
> 3. `Promise.all([...])` returns a single Promise that resolves only when ALL three resolve.
> 4. `await` suspends until that combined Promise settles.
> 5. On success: destructure the array of results. On any one's failure: throws at the await.

**What the interviewer is testing:** Knowing when to parallelize vs sequence; awareness of fail-fast.
**Sharp follow-up they often ask:** "Make address optional — don't fail the whole call if it errors." → use `Promise.allSettled`, or wrap address in `.catch(() => null)`.

### Example 3 — Sequential reduce of async tasks
**Asked as:** "Run a list of async functions in order, each receiving the previous result."

> **How to think aloud:**
> "Each task depends on the previous task's output, so I can't parallelize. The cleanest idiom is `reduce` over a Promise accumulator: start with `Promise.resolve(seed)`, then for each task, `.then(task)` — that chains the task's invocation after the previous one's resolution. The whole reduce produces one promise that resolves to the final task's return."

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

> **Step-by-step walkthrough:**
> 1. Initial accumulator: `Promise.resolve(1)`.
> 2. Reduce iter 1: `Promise.resolve(1).then(x => x + 1)` → resolves to `2`.
> 3. Reduce iter 2: previous promise → `.then(x => x * 2)` → resolves to `4`.
> 4. Reduce iter 3: previous → `.then(x => x.toString())` → resolves to `"4"`.
> 5. Final promise resolves to `"4"`.

**What the interviewer is testing:** Sequential vs parallel; reduce-as-promise-chain idiom.
**Sharp follow-up they often ask:** "What if a task throws midway?" → the chain rejects; subsequent tasks don't run. To continue, wrap each task's call in a try/catch inside the reducer.

### Example 4 — Timeout via `Promise.race`
**Asked as:** "Wrap any promise so it rejects after N ms."

> **How to think aloud:**
> "`Promise.race` settles with the first to settle, whichever it is. So I race the input promise against a timer that *rejects* after `ms`. If the input wins, we get its value; if the timer wins, we throw 'timeout'. Important caveat: race doesn't *cancel* the loser — the original work keeps running in the background. For true cancellation we'd combine this with `AbortController`."

I'd say: "Race the input promise against a setTimeout that rejects. Whichever settles first wins. The downside: the original work keeps running in the background — use AbortController if you need true cancellation."

```js
const withTimeout = (p, ms) =>
  Promise.race([
    p,
    new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms)),
  ]);

await withTimeout(fetch(url), 3000);
```

> **Step-by-step walkthrough:**
> 1. Build a timer-promise that schedules a rejection in `ms` ms.
> 2. `Promise.race([fetchPromise, timerPromise])` returns a new Promise.
> 3. If fetch resolves first (< 3000ms): race settles with fetch's value.
> 4. If timer fires first: race settles with rejection "timeout". Fetch continues in the background but its result is ignored.

**What the interviewer is testing:** `Promise.race` semantics + understanding cancellation.
**Sharp follow-up they often ask:** "How would you also abort the in-flight fetch?" → pass `signal` to fetch, call `controller.abort()` from the timeout branch.

### Example 5 — Retry with exponential backoff
**Asked as:** "Implement retry-with-backoff for a flaky HTTP call."

> **How to think aloud:**
> "A loop with try/catch and a backoff sleep between attempts. On the last attempt, re-throw instead of swallowing. Exponential backoff doubles the delay each time (`base * 2^i`) to give a failing service breathing room. In production, add 'jitter' — small randomization — to prevent synchronized retry storms from a thousand clients."

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

> **Step-by-step walkthrough (assume fn fails twice then succeeds):**
> 1. i=0: `await fn()` throws. Not the last attempt → sleep 200ms.
> 2. i=1: `await fn()` throws. Not last → sleep 400ms.
> 3. i=2: `await fn()` resolves → `return` value exits the loop and the function.

**What the interviewer is testing:** Loops with await; control flow around try/catch.
**Sharp follow-up they often ask:** "Make it abortable mid-retry." → check `signal.aborted` at the top of each loop iteration; throw if aborted.

### Example 6 — Promisify a Node-style callback
**Asked as:** "Convert `fs.readFile(path, cb)` to return a Promise without using `util.promisify`."

> **How to think aloud:**
> "Node-style callbacks are `(err, value) => {}` — error-first. To bridge to Promises, wrap the call in `new Promise`: pass our own callback that calls `resolve(value)` on success or `reject(err)` on failure. To make it reusable, curry it — a `promisify(fn)` returns a new function that does the wrapping."

I'd say: "Wrap the call in a new Promise; the callback's error becomes reject, value becomes resolve. This is the bridge between legacy Node APIs and modern async/await. Curry the function so you get a reusable promisified version."

```js
const promisify = (fn) => (...args) =>
  new Promise((res, rej) =>
    fn(...args, (err, value) => (err ? rej(err) : res(value))));

const readFileP = promisify(require("fs").readFile);
const data = await readFileP("/etc/hosts", "utf8");
```

> **Step-by-step walkthrough:**
> 1. `promisify(fs.readFile)` returns a new function. Call it with `("/etc/hosts", "utf8")`.
> 2. Inside, `new Promise(...)` is created. The executor calls `fs.readFile("/etc/hosts", "utf8", customCb)`.
> 3. `fs.readFile` does its async I/O off-thread. When done, it calls `customCb(err, value)`.
> 4. `customCb` checks err: if truthy → `reject(err)`; else → `resolve(value)`.
> 5. The promise settles. `await` resumes with the value (or throws the error).

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
