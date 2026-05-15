# Cancellable fetch with AbortController

## Source
- Standard frontend/backend interview question — `AbortController` is mainstream on both since Node 18.
- MDN: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- Real bug source: hanging fetches in serverless functions / closed React components.

## Why this question matters in interviews
Native Promise has **no built-in cancellation**. Pre-2017 this meant a hanging fetch retained the response stream, blocked the connection pool, and leaked memory. `AbortController` finally fixed it — and interviewers want to know whether you (a) know the API exists, (b) can combine it with `setTimeout` for **timeout-aware fetch**, and (c) understand that the underlying request actually stops, not just the promise wrapper. This is also the gateway to discussing cancellation in general — see `cancellable-promise-wrapper.md`.

## Concepts involved

### Syntax to lock in
```js
const controller = new AbortController();
const promise = fetch(url, { signal: controller.signal });
controller.abort(); // request stops; promise rejects with AbortError
```

### Runtime / engine behavior
- An `AbortController` exposes a `signal` (an `AbortSignal`). Pass `signal` into any abortable API (`fetch`, `addEventListener`, Node `fs.readFile`, etc.).
- Calling `controller.abort(reason)` flips `signal.aborted` to `true` and fires the `abort` event on the signal.
- `fetch` listens for `abort`; on fire, it tears down the request, closes the socket, and rejects the returned promise with a `DOMException` of name `'AbortError'` (browser) or `AbortError` (Node).
- The signal can carry a **reason** (any value). `controller.abort(new Error('timeout'))` is common.
- **Signals compose** — `AbortSignal.any([signal1, signal2])` (Node 20+, modern browsers) is a logical OR. Older runtimes need manual listener wiring.

### Edge cases (interview traps)
1. **Already-aborted signal** — pass an aborted signal and `fetch` rejects synchronously (well, microtask-quickly).
2. **Detecting abort vs other errors** — `err.name === 'AbortError'` (don't check the message text).
3. **Timeout = setTimeout + abort()** — wire `setTimeout(() => controller.abort(timeoutErr), ms)` and clear the timer on success.
4. **`AbortSignal.timeout(ms)`** — modern shortcut (Node 17+, browsers): `fetch(url, { signal: AbortSignal.timeout(5000) })`. No manual setTimeout needed.
5. **Leak: not clearing the timeout** — if fetch finishes first, the timer still fires and aborts… nothing (or worse, aborts the next request if you reuse the controller).
6. **Reusing controllers** — once aborted, a controller is permanently aborted. Create a new one per request.
7. **Cleanup of inner streams** — if you're consuming `response.body` as a stream, abort *also* cancels the body read. Make sure your downstream code handles a partial body gracefully.

## Brute force approach
`Promise.race([fetch(url), timeoutPromise])` — works for the *timeout* signal in the user-facing promise, but **does not cancel the underlying fetch**. The connection stays open, response body keeps streaming, memory leaks. Don't ship; this is exactly the bug AbortController exists to fix.

## Optimal approach
Create an `AbortController`, pass `signal` into `fetch`. For timeout, `setTimeout(() => controller.abort(...), ms)` and `clearTimeout` on the success path. Bonus: accept an external signal and combine via `AbortSignal.any` or manual listener wiring.

## Solution (JavaScript)

```js
// Basic: cancellable fetch with .cancel()
function cancellableFetch(url, options = {}) {
  const controller = new AbortController();
  const promise = fetch(url, { ...options, signal: controller.signal });
  promise.cancel = (reason) => controller.abort(reason);
  return promise;
}

// Timeout-aware fetch
async function fetchWithTimeout(url, { timeout = 5000, signal: externalSignal, ...rest } = {}) {
  const controller = new AbortController();

  // If caller provided a signal, forward its abort to ours.
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort(externalSignal.reason);
    else externalSignal.addEventListener('abort', () => controller.abort(externalSignal.reason), { once: true });
  }

  const timer = setTimeout(
    () => controller.abort(new Error(`Request timed out after ${timeout}ms`)),
    timeout,
  );

  try {
    return await fetch(url, { ...rest, signal: controller.signal });
  } finally {
    clearTimeout(timer); // critical — prevents leaking the timer
  }
}

// Usage
try {
  const res = await fetchWithTimeout('https://example.com/api/slow', { timeout: 2000 });
  const data = await res.json();
} catch (err) {
  if (err.name === 'AbortError') console.error('aborted:', err.message);
  else throw err;
}
```

## Step-by-step dry run

**Case 1 — happy path (fetch finishes before timeout):**
```js
fetchWithTimeout('https://fast.example.com', { timeout: 5000 });
```
- **t=0** — controller created. Timer scheduled for t=5000. `fetch` initiated with signal.
- **t=300** — fetch resolves with Response. `finally` runs `clearTimeout(timer)`. Timer never fires. Promise resolves to caller with the Response.

**Case 2 — timeout fires first:**
```js
fetchWithTimeout('https://slow.example.com', { timeout: 200 });
```
- **t=0** — controller created, timer scheduled for t=200, fetch initiated.
- **t=200** — timer fires: `controller.abort(new Error('Request timed out after 200ms'))`. Signal flips. Fetch tears down socket. fetch promise rejects with AbortError whose `.reason` is our Error.
- **t=200** — caller's `await fetch` throws. `finally` runs `clearTimeout` (no-op, timer already fired).
- Caller's `catch` sees `err.name === 'AbortError'` and logs `'aborted: Request timed out after 200ms'`.

**Case 3 — external signal aborts:**
```js
const outer = new AbortController();
fetchWithTimeout('https://example.com', { timeout: 10000, signal: outer.signal });
outer.abort('user navigated away');
```
- **t=0** — fetch starts. Listener on `outer.signal` forwards future aborts to our controller.
- **t=10** — `outer.abort('user navigated away')` fires the abort event. Our listener calls `controller.abort('user navigated away')`. Fetch tears down. Rejects with AbortError whose `.reason === 'user navigated away'`.

## Important takeaways

**Syntax to memorize**
- `const controller = new AbortController(); fetch(url, { signal: controller.signal });`
- `controller.abort(reason)` — reason is preserved on the AbortError.
- `err.name === 'AbortError'` — the standard check.
- `clearTimeout(timer)` in `finally` — non-negotiable.
- Modern shortcut: `AbortSignal.timeout(ms)`.

**Patterns to reuse**
- The "abort signal + cleanup in finally" idiom applies to any abortable API: `fs.readFile`, `setTimeout` (Node 18+), `events.once`, vendor SDKs.
- Forwarding an external signal to an internal controller via listener is the **signal composition** pattern. Same trick for AbortSignal.any polyfill.
- The `cancellable promise + .cancel()` shape is the user-facing decoration pattern — see `cancellable-promise-wrapper.md`.

**Common mistakes**
- `Promise.race` with a timeout promise — doesn't cancel the underlying request. Classic resource-leak bug.
- Not clearing the timer on success — timer eventually fires; if you reuse the controller (don't!), it aborts the next request.
- Checking error type with `err.message` text or `err.code` — only `err.name === 'AbortError'` is portable.
- Reusing a single controller across many requests — once aborted, it's permanently aborted.
- Forgetting that `AbortSignal.timeout` exists — manual timer is fine, but knowing the shortcut is senior signal.

**Related questions**
- `cancellable-promise-wrapper.md` (generalized cancellation, not just fetch)
- `promise-time-limit.md` (timeout without cancel)
- `retry-with-backoff.md` (each retry needs a fresh controller)

## Variants

1. **`Promise.race` with cleanup** — the alternative timeout pattern when you can't pass `signal` to the inner API. Make sure to attach an explicit `.cancel()` or the request still completes in the background.
2. **Retry with timeout per attempt** — each retry needs a fresh `AbortController` and timer.
3. **Compose multiple signals** — implement `AbortSignal.any` polyfill: create a controller, listen on each input signal, forward first abort.
4. **Abort on React unmount** — `useEffect(() => { const c = new AbortController(); fetch(url, { signal: c.signal })...; return () => c.abort(); }, [])`. Classic React pattern.

## Revision notes

> **fetch + AbortController — 60 second recap**
> - `new AbortController()` → `.signal` → pass into fetch's options.
> - `controller.abort(reason)` rejects the fetch with AbortError whose `.reason` is your value.
> - Timeout: `setTimeout(() => controller.abort(), ms)` + **clearTimeout in finally**.
> - Shortcut: `AbortSignal.timeout(ms)` (Node 17+).
> - Check abort errors via `err.name === 'AbortError'`.
> - One controller per request — never reuse.
> - **Trap:** `Promise.race` with timeout does NOT cancel the underlying request — only AbortController does.
