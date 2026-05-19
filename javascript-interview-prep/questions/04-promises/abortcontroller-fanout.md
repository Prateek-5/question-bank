# `AbortController` fanout — cancel all in-flight work with one signal

> **Difficulty:** Medium-Hard   |   **Time:** ~25 min   |   **Prereqs:** [fetch-with-abort.md](./fetch-with-abort.md), [promise-time-limit.md](./promise-time-limit.md)
>
> **Source:** DOM/Node `AbortController` (Node 15+). Asked at Stripe, Atlassian, Cloudflare, Razorpay.

---

## 1. Problem statement

**Signature**
```ts
function fanoutFetch(urls: string[], opts?: { timeoutMs?: number; userSignal?: AbortSignal }): Promise<{ results: any[]; aborted?: boolean }>;
function abortable<T>(promise: Promise<T>, signal: AbortSignal): Promise<T>;
function combineSignals(...signals: AbortSignal[]): AbortSignal;
```

**Input / Output examples**

| Setup                                                   | Behaviour                                              |
|---------------------------------------------------------|---------------------------------------------------------|
| 5 parallel fetches, one shared signal; caller aborts    | All 5 fetches reject with `AbortError` immediately     |
| `AbortSignal.any([userSignal, AbortSignal.timeout(5000)])` | Either user-cancel OR 5s timeout aborts the work    |
| Custom async work checks `signal.aborted` at each yield | Bails out without finishing                            |
| `Promise.race([fetch(url), timeoutPromise])`           | **doesn't cancel** the fetch — resource leak           |

**Constraints**
- One `AbortController` per top-level request scope; signal threaded into every fetch + custom work.
- Compose signals via `AbortSignal.any([...])` (Node 20+, browsers).
- Detect aborts via `err.name === 'AbortError'`.
- Always cleanup: `{ once: true }` listeners, `clearTimeout`.

---

## 2. Plain-English restatement

`AbortController` is the standard cancellation token. You create one, hand its `signal` to every async operation that supports it, and call `controller.abort()` when you want everything to stop. Unlike `Promise.race` with a timeout, `AbortController` actually **interrupts** the work — fetch closes the socket, timers clear, custom code checks `signal.aborted` and bails. This problem is about wiring one controller's signal to fan out across many concurrent operations.

---

## 3. Why this matters in interviews

"Cancel" used to mean "ignore the result." Native `AbortController` finally lets us cancel *the work itself*. A senior candidate must know: (1) `AbortSignal` is the standard cancellation token, (2) fan-out — when one source cancels, all derived workers cancel, (3) composition — `AbortSignal.any([...])` combines multiple signals, (4) listener hygiene — `{ once: true }` and removeListener on resolve. Production fetch helpers all use this; interviewers want to see you wire it correctly.

---

## 4. Mental model

A **shared kill-switch wired to every worker**:

```
   AbortController (kill-switch)
       │
       │ signal (broadcast wire)
       │
       ├──▶ fetch A   (listens; on abort → throw AbortError)
       ├──▶ fetch B
       ├──▶ fetch C
       ├──▶ setTimeout-based work (listens; on abort → clearTimeout + reject)
       └──▶ user code (checks signal.aborted at boundaries)

   caller: ac.abort() → ALL branches reject simultaneously
```

`AbortSignal.any([s1, s2])` is a **wire-or** of multiple kill-switches — pull either, every consumer aborts. Modern timeout-only shortcut: `AbortSignal.timeout(ms)` returns a signal that aborts itself.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `Promise.race([fetch(url), timeoutPromise])` not actually cancel the fetch's request?
> 2. With `AbortSignal.any([userSignal, AbortSignal.timeout(5000)])`, what aborts the work — only the timeout, or also user cancel?
> 3. Inside custom async code, where should you check `signal.aborted`?

---

## 6. Brute force — walked through

### Wrong attempt 1: ignore result via `Promise.race`

```js
const result = await Promise.race([fetch(url), sleep(5000).then(() => 'timeout')]);
```

Fetch keeps streaming, socket stays open. Connection pool exhausts. Memory leaks. Use `AbortController` to actually stop fetch.

### Wrong attempt 2: forget `{ once: true }`

```js
signal.addEventListener('abort', onAbort);   // BUG: never removed
```

Long-lived signals accumulate stale listeners. Memory leak. Use `{ once: true }` or explicit `removeEventListener`.

### Wrong attempt 3: don't check `signal.aborted` in custom work

```js
async function process(items, { signal }) {
  for (const item of items) {
    await heavyWork(item);   // BUG: doesn't honor signal
  }
}
```

Caller aborts but loop runs to completion. Check `signal.aborted` at every yield boundary.

---

## 7. The unlocking insight

> **One `AbortController` per top-level scope. Its `signal` is threaded into every fetch and custom async API. To compose with a timeout, use `AbortSignal.any([userSignal, AbortSignal.timeout(5000)])`. Every custom API exposes `{ signal }` and listens for `'abort'` to clean up.**

Three threading points:

1. **fetch/built-ins** — accept `{ signal }` natively. Just pass it.
2. **Custom async loops** — check `signal.aborted` at every yield boundary (`await`, `yield`, etc.).
3. **Resource holders** — register `abort` listener with `{ once: true }` to close handles, clear timers.

`err.name === 'AbortError'` is the standard discriminant in catch blocks. Don't check message text — it varies across runtimes.

---

## 8. Solution (annotated)

```js
// Race a promise against a signal
function abortable(promise, signal) {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(signal.reason);
  return new Promise((resolve, reject) => {
    const onAbort = () => reject(signal.reason);
    signal.addEventListener('abort', onAbort, { once: true });
    promise
      .finally(() => signal.removeEventListener('abort', onAbort))
      .then(resolve, reject);
  });
}

// Fan-out fetch with timeout + optional user-signal
async function fanoutFetch(urls, { timeoutMs = 10_000, userSignal } = {}) {
  const timeoutSig = AbortSignal.timeout(timeoutMs);
  const signal = userSignal
    ? AbortSignal.any([userSignal, timeoutSig])
    : timeoutSig;
  try {
    const results = await Promise.all(
      urls.map((u) => fetch(u, { signal }).then((r) => r.json()))
    );
    return { results };
  } catch (err) {
    if (err.name === 'AbortError') return { aborted: true, reason: signal.reason };
    throw err;
  }
}

// Custom long-running work that respects signal
async function chunkyCompute(items, { signal }) {
  for (let i = 0; i < items.length; i++) {
    if (signal?.aborted) throw signal.reason;
    await processChunk(items[i]);
  }
}

// AbortSignal.any polyfill for older Node
function combineSignals(...signals) {
  if ('any' in AbortSignal) return AbortSignal.any(signals);
  const ac = new AbortController();
  for (const s of signals) {
    if (s.aborted) { ac.abort(s.reason); break; }
    s.addEventListener('abort', () => ac.abort(s.reason), { once: true });
  }
  return ac.signal;
}
```

**Try it yourself**

```js
const ac = new AbortController();
setTimeout(() => ac.abort('user cancel'), 100);

try {
  const { results } = await fanoutFetch(
    ['/api/a', '/api/b', '/api/c'],
    { timeoutMs: 5000, userSignal: ac.signal }
  );
} catch (err) {
  if (err.name === 'AbortError') console.log('cancelled:', err.cause);
}
```

---

## 9. Step-by-step dry run

User clicks "Search" → 5 parallel fetches; user clicks "Cancel" at t=100:

```
t=0   ac = new AbortController()
      Promise.all([fetch(A..E), all { signal: ac.signal }])
      5 sockets opened
t=100 user clicks Cancel
      ac.abort(new DOMException('user cancelled', 'AbortError'))
      → fetch(A..E) each reject with AbortError
      → Promise.all rejects with AbortError
      → catch: err.name === 'AbortError' → render "Cancelled"

(alternate: timeout)
With AbortSignal.timeout(5000) wired via AbortSignal.any, same abort path fires at t=5000.
```

---

## 10. Common confusion + traps

1. **`Promise.race` with timeout doesn't cancel** — fetch keeps streaming. Use `AbortController`.
2. **Listener leak** — always `{ once: true }` or `removeEventListener`.
3. **`err.message` for abort detection** — varies across runtimes. Use `err.name === 'AbortError'`.
4. **Reusing controllers** — once aborted, permanently aborted. One per request.
5. **Custom code not checking `signal.aborted`** — loops finish despite abort. Check at every yield.
6. **`AbortSignal.timeout` vs manual setTimeout** — modern shortcut, no cleanup needed.
7. **Abort on already-completed work** — no-op, fine.

---

## 11. Senior follow-ups & variants

### Variant 1 — Parent-child cascade
Outer controller aborts inner controllers; inner abort doesn't affect parent.

```js
function childController(parentSignal) {
  const ac = new AbortController();
  parentSignal.addEventListener('abort', () => ac.abort(parentSignal.reason), { once: true });
  return ac;
}
```

### Variant 2 — AsyncIterator with signal
Producer checks `signal.aborted` between yields; consumer can `for await ... of` and bail.

### Variant 3 — Bidirectional abort
Both caller and worker share one controller; either can abort. Rare; useful for "worker refuses, signals upstream."

### Variant 4 — Compose with structured concurrency
See [structured-concurrency-primitive.md](./structured-concurrency-primitive.md) — TaskGroup uses an internal AbortController to cancel siblings on first error.

---

## 12. How to think aloud

> "`AbortController` is the standard cancellation token. One controller per top-level request scope; the signal threads down into every async API: fetch, custom long-runners, timers. For composition: `AbortSignal.any([userCancel, AbortSignal.timeout(5000)])` for 'cancel on either.' Inside custom code I check `signal.aborted` at every yield point and listen to `'abort'` with `{ once: true }` for cleanup. Catch path: `err.name === 'AbortError'` to distinguish cancel from real failure. `Promise.race` with timeout does NOT cancel — that's the resource-leak bug AbortController exists to fix."

---

## 13. 60-second revision

> - **One controller, many consumers** — fan-out via shared signal.
> - **`AbortSignal.any([...])`** combines signals (timeout + user + parent).
> - **`AbortSignal.timeout(ms)`** for timeout-only (Node 17+).
> - **`{ once: true }`** on abort listeners — avoid leaks.
> - **`err.name === 'AbortError'`** is the standard check.
> - **Custom code:** check `signal.aborted` at every yield.
> - **One controller per request** — once aborted, permanent.
> - **Trap:** `Promise.race` doesn't cancel; listener leaks; checking `err.message`.

---

**Related:** [fetch-with-abort.md](./fetch-with-abort.md) · [structured-concurrency-primitive.md](./structured-concurrency-primitive.md) · [promise-time-limit.md](./promise-time-limit.md) · [retry-with-backoff.md](./retry-with-backoff.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
