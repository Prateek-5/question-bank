# Cancellable `fetch` with `AbortController` — proper request cancellation

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [promise-time-limit.md](./promise-time-limit.md), [abortcontroller-fanout.md](./abortcontroller-fanout.md)
>
> **Source:** Standard frontend/backend interview question. MDN: <a href="https://developer.mozilla.org/en-US/docs/Web/API/AbortController" target="_blank" rel="noopener noreferrer">AbortController</a>.

---

## 1. Problem statement

**Signature**
```ts
function fetchWithTimeout(url: string, opts?: RequestInit & {
  timeout?: number;
  signal?: AbortSignal;
}): Promise<Response>;
```

**Input / Output examples**

| Setup                                                          | Behaviour                                              |
|----------------------------------------------------------------|---------------------------------------------------------|
| `fetchWithTimeout('https://fast.api/x', { timeout: 5000 })`   | resolves at ~200ms with Response                       |
| `fetchWithTimeout('https://slow.api/x', { timeout: 200 })`    | rejects at t=200 with AbortError; **underlying TCP socket actually closes** |
| `fetchWithTimeout(url, { timeout: 200, signal: outerSignal })`| forwards `outerSignal.abort()` to the inner controller |
| `controller.abort('user cancelled')`                           | rejects with AbortError whose `.reason === 'user cancelled'` |
| `Promise.race([fetch(url), sleep(5000).then(reject)])`         | "times out" but **request keeps streaming** — bug      |

**Constraints**
- `AbortController` actually cancels the underlying request (socket closes).
- `Promise.race` with a timeout promise does NOT — it just discards the result. Resource leak.
- Always `clearTimeout` in `finally` so the timer doesn't keep the event loop alive.
- Detect aborts via `err.name === 'AbortError'`.

---

## 2. Plain-English restatement

Wrap `fetch` so it gets cancelled — for real, not just discarded — when a timeout fires or when the caller bails out. Pass an `AbortController.signal` to `fetch`; when the signal aborts, fetch tears down the connection, closes the socket, and rejects with an AbortError. For timeouts, wire `setTimeout` to call `controller.abort()`. Optionally forward an external caller's signal so they can also cancel.

The senior point is that **`Promise.race` alone leaks resources** — the network request keeps streaming bytes into a dead-on-arrival promise. `AbortController` is the only way to actually stop a fetch.

---

## 3. Why this matters in interviews

Native Promise has **no built-in cancellation**. Pre-2017 this meant a hanging fetch retained the response stream, blocked the connection pool, and leaked memory. `AbortController` fixed it — and interviewers want to know whether you (a) know the API exists, (b) can combine it with `setTimeout` for **timeout-aware fetch**, and (c) understand that the underlying request actually stops, not just the promise wrapper. This is also the gateway to discussing cancellation in general.

---

## 4. Mental model

```
   AbortController
   ├── signal      ← read-only AbortSignal
   ├── abort()     ← flips signal.aborted; fires 'abort' event

   fetch(url, { signal }):
     listens on signal's 'abort' event
     on fire: tear down socket, close stream, reject promise with AbortError

   Timeout pattern:
     1. const ctrl = new AbortController()
     2. const timer = setTimeout(() => ctrl.abort(timeoutErr), ms)
     3. await fetch(url, { signal: ctrl.signal })
     4. clearTimeout(timer) in finally
```

Compare with the broken `Promise.race` approach:

```
   Promise.race([
     fetch(url),                          ← keeps running after race settles
     sleep(5000).then(() => { throw err })
   ])
   
   On timeout: race rejects but fetch keeps streaming.
   Connection pool stays exhausted. Response body buffers in memory.
   This is the resource-leak bug AbortController fixes.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `Promise.race([fetch(url), timeoutPromise])`, what happens to the fetch's socket after the timeout fires?
> 2. If you call `controller.abort()` after fetch has already finished, does anything happen?
> 3. How would you forward an external `AbortSignal` from the caller through to fetch?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Promise.race` with timeout promise

```js
async function fetchWithTimeout(url, ms) {
  return Promise.race([
    fetch(url),
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms)),
  ]);
}
```

**Resource leak.** The fetch's underlying request continues — TCP socket open, response body buffering, connection pool exhausted. On a high-traffic server, this gradually starves the connection pool until everything times out. This is the classic "my server is up but `curl /healthcheck` hangs" outage.

### Wrong attempt 2: forget to clear the timer

```js
async function fetchWithTimeout(url, ms) {
  const ctrl = new AbortController();
  setTimeout(() => ctrl.abort(), ms);   // BUG: timer not stored, can't clear
  return fetch(url, { signal: ctrl.signal });
}
```

On success, the timer still fires later. With a permanently-aborted controller, the abort is a no-op — but the timer kept the event loop alive. Long-running servers accumulate these. Always `clearTimeout` in `finally`.

### Wrong attempt 3: reuse one controller

```js
const sharedController = new AbortController();
async function fetchWithTimeout(url, ms) {
  setTimeout(() => sharedController.abort(), ms);
  return fetch(url, { signal: sharedController.signal });
}
```

Once aborted, an AbortController is **permanently aborted**. The next call sees `signal.aborted === true` and rejects immediately. **One controller per request** — never reuse.

### Wrong attempt 4: check `err.message` instead of `err.name`

```js
catch (err) {
  if (err.message.includes('aborted')) { /* ... */ }   // BUG: not portable
}
```

The message text varies by browser and Node version. `err.name === 'AbortError'` is the portable check.

---

## 7. The unlocking insight

> **`AbortController` actually cancels the underlying request — TCP socket closes, response stream tears down. Pass `controller.signal` to `fetch`. For timeout, `setTimeout(() => controller.abort(reason), ms)` and `clearTimeout` in `finally`. To compose multiple signals, forward an external one to your internal controller via `addEventListener('abort')`.**

Four properties to internalize:

1. **One controller per request.** Once aborted, controllers are permanently aborted. Never reuse.

2. **`clearTimeout` in `finally`.** If fetch succeeds first, clear the timer. Otherwise it stays alive until it naturally fires, holding the event loop open and (worse) aborting a controller that's already done.

3. **Error detection via `err.name === 'AbortError'`.** Standard across browsers and Node. Don't check `err.message`.

4. **Signal composition.** Modern: `AbortSignal.any([sig1, sig2])` (Node 20+, modern browsers). Older runtimes: manually wire `outer.signal.addEventListener('abort', () => inner.abort(outer.signal.reason))`.

The shortcut for the timeout-only case: `AbortSignal.timeout(ms)` (Node 17+, modern browsers). One-liner that creates a signal which aborts itself after `ms`. No manual `setTimeout`/`clearTimeout` needed.

---

## 8. Solution (annotated)

```js
async function fetchWithTimeout(url, {
  timeout = 5000,
  signal: externalSignal,
  ...rest
} = {}) {
  const controller = new AbortController();                            // step 1: fresh controller per call

  // Forward external signal to our controller
  if (externalSignal) {                                                 // step 2: composition
    if (externalSignal.aborted) {
      controller.abort(externalSignal.reason);
    } else {
      externalSignal.addEventListener(
        'abort',
        () => controller.abort(externalSignal.reason),
        { once: true }
      );
    }
  }

  const timer = setTimeout(                                             // step 3: timeout wiring
    () => controller.abort(new Error(`Request timed out after ${timeout}ms`)),
    timeout
  );

  try {
    return await fetch(url, { ...rest, signal: controller.signal });    // step 4: pass signal to fetch
  } finally {
    clearTimeout(timer);                                                // step 5: ALWAYS clean up
  }
}

// Basic version (no external signal forwarding)
function cancellableFetch(url, opts = {}) {
  const controller = new AbortController();
  const promise = fetch(url, { ...opts, signal: controller.signal });
  promise.cancel = (reason) => controller.abort(reason);
  return promise;
}
```

**Try it yourself**

```js
// Timeout-aware
try {
  const res = await fetchWithTimeout('https://example.com/api', { timeout: 2000 });
  const data = await res.json();
} catch (err) {
  if (err.name === 'AbortError') console.error('aborted:', err.message);
  else throw err;
}

// User-cancellable (e.g., React unmount)
const ctrl = new AbortController();
const promise = fetchWithTimeout('/api/data', { timeout: 10_000, signal: ctrl.signal });
// On unmount:
ctrl.abort('component unmounted');

// Modern shortcut: AbortSignal.timeout (no manual setTimeout)
const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
```

---

## 9. Step-by-step dry run

**Case 1 — fetch finishes before timeout:**

```js
fetchWithTimeout('https://fast.example.com', { timeout: 5000 });
```

| Time (ms) | Event                                                       | Outcome             |
|-----------|--------------------------------------------------------------|----------------------|
| 0         | controller created, timer scheduled for t=5000, fetch initiated | pending            |
| 300       | fetch resolves with Response                                  | `finally` clears timer |
| 300       | `await fetch` returns Response                                | promise resolves    |
| 5000      | timer would have fired, but was cleared                       | no-op               |

**Case 2 — timeout fires first:**

```js
fetchWithTimeout('https://slow.example.com', { timeout: 200 });
```

| Time | Event                                                                                              | Outcome                   |
|------|----------------------------------------------------------------------------------------------------|----------------------------|
| 0    | controller created, timer at t=200, fetch initiated                                                | pending                    |
| 200  | timer fires: `controller.abort(Error('timed out 200ms'))`. Signal flips. Fetch tears down socket. | fetch rejects with AbortError whose `.reason === Error('timed out')` |
| 200+µ| caller's `await` throws AbortError; `finally` clears timer (no-op, already fired)                  | caller sees AbortError      |

The underlying TCP socket actually closes — the response body's stream is destroyed. No leak.

**Case 3 — external signal aborts:**

```js
const outer = new AbortController();
const p = fetchWithTimeout('https://example.com', { timeout: 10000, signal: outer.signal });
setTimeout(() => outer.abort('user navigated away'), 10);
```

| Time | Event                                                                              | Outcome                          |
|------|------------------------------------------------------------------------------------|-----------------------------------|
| 0    | controller created; listener wires `outer.signal` → `controller.abort`            | pending                          |
| 10   | `outer.abort('user navigated away')` fires; listener calls `controller.abort(...)` | fetch aborts                     |
| 10+µ | `await fetch` throws AbortError; `.reason === 'user navigated away'`              | caller sees AbortError with reason|

---

## 10. Common confusion + traps

1. **`Promise.race` with timeout doesn't cancel the request.** Just discards the promise. Socket stays open, body keeps streaming. Resource leak.

2. **Not clearing the timer on success.** Timer fires later, aborts an already-completed controller (no-op), but keeps the event loop alive. In long-running servers, this accumulates.

3. **Checking `err.message` text or `err.code`.** Only `err.name === 'AbortError'` is portable across browsers and Node.

4. **Reusing a single controller across many requests.** Once aborted, it's permanently aborted. One controller per request.

5. **Forgetting `AbortSignal.timeout(ms)`.** Modern shortcut for the timeout case. No manual setTimeout. Senior signal.

6. **Cleanup of inner streams.** If you're consuming `response.body` as a stream, abort *also* cancels the body read. Make sure your downstream code handles a partial body gracefully (catch the read error).

7. **Forgetting `{ once: true }` on listeners.** Without it, you leak listeners on long-lived signals.

8. **`controller.abort()` after fetch already finished.** No-op — fetch settled, controller flips state but nothing happens. Don't worry about it.

---

## 11. Senior follow-ups & variants

### Variant 1 — Modern timeout shortcut (Node 17+, modern browsers)

```js
const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
```

`AbortSignal.timeout(ms)` returns a signal that aborts itself after `ms`. No manual timer/cleanup. Use this when timeout is the only cancellation case.

### Variant 2 — Compose multiple signals

```js
// Node 20+, modern browsers
const combined = AbortSignal.any([userSignal, AbortSignal.timeout(5000)]);
await fetch(url, { signal: combined });

// Manual polyfill for older runtimes
function anySignal(signals) {
  const ctrl = new AbortController();
  for (const s of signals) {
    if (s.aborted) { ctrl.abort(s.reason); break; }
    s.addEventListener('abort', () => ctrl.abort(s.reason), { once: true });
  }
  return ctrl.signal;
}
```

### Variant 3 — Retry with timeout per attempt

```js
async function fetchWithRetry(url, opts = {}) {
  const { retries = 3, timeout = 5000, ...rest } = opts;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fetchWithTimeout(url, { timeout, ...rest });
    } catch (err) {
      if (err.name === 'AbortError' && i === retries) throw err;
      await sleep(100 * 2 ** i);   // exponential backoff
    }
  }
}
```

Each retry gets a fresh controller and timer.

### Variant 4 — React `useEffect` abort on unmount

```jsx
function useUser(id) {
  const [user, setUser] = useState(null);
  useEffect(() => {
    const ctrl = new AbortController();
    fetch(`/api/users/${id}`, { signal: ctrl.signal })
      .then(r => r.json())
      .then(setUser)
      .catch(err => { if (err.name !== 'AbortError') console.error(err); });
    return () => ctrl.abort();   // unmount → cancel inflight
  }, [id]);
  return user;
}
```

Canonical React pattern — cancel inflight on unmount or dependency change.

### Variant 5 — Stream-aware: cancel mid-body-read

```js
async function fetchWithStreamTimeout(url, { timeout = 5000 } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, { signal: ctrl.signal });
    // The signal also cancels the body stream — bytes stop arriving when aborted
    const text = await res.text();   // throws if aborted mid-read
    return text;
  } finally {
    clearTimeout(timer);
  }
}
```

Abort during body streaming is a real scenario for large downloads. The Response body's stream is also tied to the signal.

---

## 12. How to think aloud in the interview

> "`AbortController` is the way. Create a fresh controller per request; pass `controller.signal` to fetch. For timeout, `setTimeout(() => controller.abort(reason), ms)` and clear the timer in `finally`. Detect aborts via `err.name === 'AbortError'`. Forward an external caller's signal to our internal controller via `addEventListener('abort', forward, { once: true })`. Modern shortcut for timeout-only: `AbortSignal.timeout(ms)`. Compose multiple: `AbortSignal.any([sig1, sig2])` (Node 20+). The critical contrast: `Promise.race` with a timeout promise does NOT cancel the underlying fetch — socket stays open, body keeps streaming, connection pool exhausts. That's the bug AbortController exists to fix."

---

## 13. 60-second revision

> - **`new AbortController()`** → pass `.signal` to fetch.
> - **`controller.abort(reason)`** rejects fetch with AbortError; `.reason` preserved.
> - **Timeout:** `setTimeout(() => controller.abort(), ms)` + **clearTimeout in finally**.
> - **Modern shortcut:** `AbortSignal.timeout(ms)` (Node 17+).
> - **Compose:** `AbortSignal.any([sig1, sig2])` (Node 20+).
> - **Detect via `err.name === 'AbortError'`** — portable.
> - **One controller per request** — never reuse.
> - **Forward external signal** via `addEventListener('abort', forward, { once: true })`.
> - **React pattern:** `useEffect` returns cleanup that calls `controller.abort()`.
> - **Trap:** `Promise.race` with timeout DOES NOT cancel the underlying request — resource leak. Only `AbortController` actually stops fetch.

---

**Related:** [abortcontroller-fanout.md](./abortcontroller-fanout.md) · [promise-time-limit.md](./promise-time-limit.md) · [retry-with-backoff.md](./retry-with-backoff.md) · [`10-machine-coding-patterns/cancellable-promise-wrapper.md`](../10-machine-coding-patterns/cancellable-promise-wrapper.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
