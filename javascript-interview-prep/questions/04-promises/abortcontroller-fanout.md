# AbortController Fanout — Cancel All In-Flight Work

## Source / Origin
- DOM/Node AbortController (spec'd 2017; native in Node 15+).
- Asked at: Stripe, Atlassian, Cloudflare, Razorpay — anywhere with fetch().
- Concept reference: `concepts/promises.md`, sibling `fetch-with-abort.md`.

## Why this question matters in interviews
"Cancel" used to mean "ignore the result." Native `AbortController` finally lets us cancel *the work itself* — interrupt the fetch, stop the timer, return early from a long compute. A senior candidate must know: (1) `AbortSignal` is the standard cancellation token; (2) fan-out — when one source cancels, all derived workers cancel; (3) reverse — `AbortSignal.any([...])` combines multiple signals; (4) you can listen to `'abort'` to clean up resources. Production fetch helpers all use this; interviewers want to see you wire it correctly.

## Concepts involved

### Syntax to lock in
```js
// 1. Basic fetch with timeout
const ac = new AbortController();
setTimeout(() => ac.abort(new DOMException('timeout', 'AbortError')), 5000);
const res = await fetch(url, { signal: ac.signal });

// 2. Fan-out one signal to multiple workers
async function fanout(urls, signal) {
  return Promise.all(urls.map(u => fetch(u, { signal })));   // all share same signal
}
// caller calls ac.abort() → every fetch aborts

// 3. Combine multiple signals (any → abort propagates)
function combineSignals(...signals) {
  if ('any' in AbortSignal) return AbortSignal.any(signals);   // Node 20+, modern browsers
  const ac = new AbortController();
  for (const s of signals) {
    if (s.aborted) { ac.abort(s.reason); break; }
    s.addEventListener('abort', () => ac.abort(s.reason), { once: true });
  }
  return ac.signal;
}

// 4. Make any promise abortable
function abortable(promise, signal) {
  if (signal.aborted) return Promise.reject(signal.reason);
  return new Promise((resolve, reject) => {
    const onAbort = () => reject(signal.reason);
    signal.addEventListener('abort', onAbort, { once: true });
    promise.then(
      (v) => { signal.removeEventListener('abort', onAbort); resolve(v); },
      (e) => { signal.removeEventListener('abort', onAbort); reject(e); }
    );
  });
}
```

### Edge cases / interview traps
1. **Abort throws an `AbortError`, not a return value.** Callers must `try/catch` and distinguish via `err.name === 'AbortError'`.
2. **Already aborted at start.** Always check `signal.aborted` *before* doing work; don't initiate then check.
3. **Listener leak.** Adding `'abort'` listeners without `{ once: true }` or without removing them on resolve leaks memory.
4. **`AbortSignal.timeout(ms)`** (Node 17+) — convenient, but consider whether you want to abort the *whole tree* or just one branch.
5. **Network resources don't always honor abort instantly.** Underlying TCP socket may take a few ms to close.
6. **Combining old + new signals.** `AbortSignal.any([...])` is the modern way; polyfill via the manual combine pattern.
7. **AbortController in worker_threads** — message-passes correctly via `transferable`; not the same instance.
8. **Abort reason** — pass an Error as the argument to `abort(reason)`; consumers receive it as `signal.reason`.

## Mental Model

A **shared kill-switch wired to every worker bee**:

```
   AbortController(kill-switch)
       │
       │ signal (broadcast wire)
       │
       ├──▶ fetch A   (listens; on abort → throw AbortError)
       ├──▶ fetch B
       ├──▶ fetch C
       ├──▶ setTimeout-based work (listens; on abort → clearTimeout + reject)
       └──▶ user code (checks signal.aborted at boundaries)

   caller: ac.abort() → all branches reject
```

`AbortSignal.any([s1, s2])` is a **wire-or** of multiple kill-switches — pull either, branch aborts.

## Why interviewers care

- **Cancellation hygiene.** Senior candidates wire AbortSignal through *every* async API they build, including custom ones.
- **Resource cleanup.** Closing timers, sockets, file handles on abort.
- **Composition.** Combining timeouts, user-cancel, parent-cancel.

## Common beginner confusion

- **"Promise.race with a timeout cancels the fetch."** No — it just ignores the result. The fetch still runs. Use `AbortController` to *actually* cancel.
- **"Abort is the same as resolve."** Abort *rejects* with an `AbortError`.
- **"One controller per request."** Wrong — fan out one controller's signal to many requests so a single abort cancels all.
- **"Abort cancels already-completed work."** No — abort is fire-and-forget. If the work resolved before abort fired, you got the value.
- **"Listening to 'abort' forever is fine."** Memory leak. Use `{ once: true }` or remove explicitly.

## Brute force approach

```js
// "Cancel" by ignoring the result — but work continues
let cancelled = false;
const p = fetch(url);
setTimeout(() => { cancelled = true; }, 5000);
const res = await p;
if (cancelled) return;     // wasted bytes; socket still open
```

## Optimal approach

`AbortController` per top-level request scope; the signal is threaded into every fetch and custom async API. To compose with a timeout or parent-cancel, use `AbortSignal.any([userSignal, AbortSignal.timeout(5000)])`. Every custom async API exposes an `{ signal }` option and listens for `'abort'` to clean up.

## Solution (JavaScript)

```js
// Reusable: race a promise against a signal
function abortable(promise, signal) {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(signal.reason);
  return new Promise((resolve, reject) => {
    const onAbort = () => reject(signal.reason);
    signal.addEventListener('abort', onAbort, { once: true });
    promise.finally(() => signal.removeEventListener('abort', onAbort)).then(resolve, reject);
  });
}

// Fan-out: cancel many fetches with one controller
async function fanoutFetch(urls, { timeoutMs = 10_000, userSignal } = {}) {
  const timeoutSig = AbortSignal.timeout(timeoutMs);
  const signal = userSignal ? AbortSignal.any([userSignal, timeoutSig]) : timeoutSig;
  try {
    const results = await Promise.all(urls.map(u => fetch(u, { signal }).then(r => r.json())));
    return { results };
  } catch (err) {
    if (err.name === 'AbortError') return { aborted: true, reason: signal.reason };
    throw err;
  }
}

// Custom long task that respects signal
async function chunkyCompute(items, { signal }) {
  for (let i = 0; i < items.length; i++) {
    if (signal?.aborted) throw signal.reason;
    await processChunk(items[i]);
  }
}
```

## Step-by-step dry run

User clicks "Search" → 5 parallel fetches; either succeed in 200ms or user clicks "Cancel" at 100ms.

```
t=0   ac = new AbortController()
      Promise.all([fetch(A), fetch(B), ..., fetch(E)], all { signal: ac.signal })
      5 sockets opened, requests sent

t=100 user clicks Cancel
      ac.abort(new DOMException('user cancelled', 'AbortError'))
      → fetch(A).reject(AbortError); same for B-E
      Promise.all rejects with AbortError
      caller: catch err → err.name === 'AbortError' → render "Cancelled"

(alternate scenario: no cancel)
t=200 fetch(A) resolves; ...; fetch(E) resolves
      Promise.all resolves with [a, b, c, d, e]
```

If `AbortSignal.timeout(5000)` was also wired via `AbortSignal.any`, then a 5s timeout would also trigger the same abort path.

## How to think aloud in the interview

> "AbortController is the standard cancellation token. One controller per top-level request scope; the signal threads down into every async API: fetch, custom long-runners, timers. Composition: `AbortSignal.any([userCancel, AbortSignal.timeout(5000)])` for 'cancel on either user-action or timeout.' Inside custom code I check `signal.aborted` at every yield point and listen to `'abort'` with `{ once: true }` to clean up handles. Catch path checks `err.name === 'AbortError'` to distinguish cancel from real failure."

## Important takeaways

- **One controller, many consumers.** Fan-out.
- **`AbortSignal.any([...])`** combines signals (timeout + user + parent).
- **Check `signal.aborted`** at boundaries inside custom async code.
- **`{ once: true }`** when listening to `'abort'`.
- **`err.name === 'AbortError'`** is the standard discriminant.
- **Cleanup on abort.** Close sockets, clear timers, unwatch files.

## Variants

- **Timeout-only**: `AbortSignal.timeout(5000)` (Node 17+).
- **Parent-child cascade**: A request controller and a finer-grained per-subtask controller; aborting parent aborts children, but a child abort only kills its subtree.
- **Polyfill `AbortSignal.any`** for Node <20: manual fanout listener.
- **AsyncIterator with signal**: producer checks `signal.aborted` between yields; consumer can `for await ... of` and bail.
- **Bidirectional abort**: rare — caller can abort *and* worker can signal "I refuse, abort upstream too" via a shared controller.

## Revision notes

```
AbortController:
  const ac = new AbortController()
  ac.signal threaded to every async API ({ signal })
  ac.abort(reason)  → all listeners reject
  
  AbortSignal.any([s1, s2]) — combine (Node 20+)
  AbortSignal.timeout(ms)
  err.name === 'AbortError' to distinguish
  listen 'abort' with { once: true } to clean handles
  inside custom async: check signal.aborted at yields
  Promise.race for "ignore result" ≠ real cancel
  fan-out: one controller's signal → many consumers
```
