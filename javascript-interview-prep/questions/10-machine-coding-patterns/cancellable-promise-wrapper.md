# Make a Promise Cancellable (token / signal pattern)

## Source
- Famous in the JS community since 2014 (Domenic Denicola's TC39 cancellation proposals; bluebird's `Promise.cancel`).
- Modern answer: `AbortController` (Node 15+, all evergreen browsers).
- Common at senior frontend / backend interviews to probe understanding of why native Promise doesn't have cancel.

## Why this question matters in interviews
This is a **conceptual trap question**. Many candidates start writing `promise.cancel()` and get derailed. The correct first answer is "native Promises are intentionally not cancellable — once started, a Promise's settlement is determined by its executor. You can build a wrapper that **ignores** the result, or use **AbortController** to cancel the underlying operation." That distinction — between cancelling **the work** vs cancelling **the awaiter** — is the senior insight. Then you implement the wrapper. It tests **closures over a flag**, **Promise constructor**, **understanding of microtask scheduling**, and the discipline to say "this is a wrapper, the underlying fetch/timer is still running."

## Concepts involved

### Syntax to lock in
```js
// "Cancel" by ignoring future settlement
function makeCancellable(promise) {
  let cancelled = false;
  const wrapped = new Promise((resolve, reject) => {
    promise.then(
      (v) => cancelled ? reject({ cancelled: true }) : resolve(v),
      (e) => cancelled ? reject({ cancelled: true }) : reject(e),
    );
  });
  return { promise: wrapped, cancel: () => { cancelled = true; } };
}

// Native cancel — cancels the actual underlying work (fetch, timer)
const controller = new AbortController();
const res = await fetch(url, { signal: controller.signal });
controller.abort();   // request actually stops
```

### Runtime / engine behavior
- A Promise's settlement is decided by its **executor function**, which runs synchronously inside `new Promise(...)`. Once the executor calls `resolve` or `reject`, the Promise is locked. **There is no API to undo this from outside.** That's why "cancel a Promise" isn't a real thing.
- What you can cancel: the **consumer's interest** in the result. The wrapper ignores the eventual settlement and rejects with a `cancelled` flag instead. The underlying work still runs to completion — it just publishes to a black hole.
- `AbortController` is different: it's a **signal** the underlying operation listens to. `fetch(url, {signal})` polls `signal.aborted` and tears down the HTTP request. `setTimeout` has a wrapper version that does the same. This is **real** cancellation because the work itself stops.
- Microtask scheduling: the wrapper's `.then` callbacks run on the microtask queue, so the cancellation check sits inside the microtask. Calling `cancel()` synchronously before the original settles guarantees the wrapper rejects.
- Why TC39 declined cancellable Promises: it would break the **invariant** that a Promise's settlement state is monotonic. Plus, chaining (`p.then(a).then(b)`) would need to define cancellation propagation, which gets ugly fast (does cancelling `b` cancel `a`?). The community settled on `AbortController` as the right separation: signal the work, not the Promise.

### Edge cases (these are the interview traps)
1. **Already-settled promise** — calling `cancel()` after the promise has resolved is a no-op (the wrapper already settled). State this; don't pretend cancel always works.
2. **Multiple cancels** — second call should be a no-op, not a double-reject. The wrapper's outer Promise can only settle once anyway, so it's safe; but flip a flag to avoid extra work.
3. **Cleanup side effects** — if you opened a socket, started a timer, or held a lock, cancelling the wrapper doesn't release them. Need a separate `cleanup` callback or use AbortSignal.
4. **Error in original** — should a rejected original after cancel still reject the wrapper? With the cancellation flag, no — wrapper rejects with `{cancelled:true}`. Some implementations preserve the original error.
5. **Chaining cancelled Promises** — `.then(handler)` on the cancelled wrapper still runs `handler` if you return a fulfilled value. The "cancelled" status doesn't propagate through `.then` unless `handler` is explicitly checking.
6. **AbortController is the modern answer** — for fetch, fs streams (Node 16+), and any opt-in API, `signal` is the right cancellation mechanism. Most interviewers will accept "use AbortController" as a full answer if you explain why native Promise.cancel doesn't exist.
7. **Combining AbortController with the wrapper** — sometimes you have a Promise that doesn't accept a signal (third-party lib). Wrap it AND wire the signal: `signal.addEventListener('abort', () => cancel())`. Two-layer pattern.
8. **`Promise.withResolvers`** (ES2024) — externalizes resolve/reject without the constructor callback dance. Cleaner for advanced cancellation control. Mention if asked.

## Brute force approach
"Just have the consumer not call `.then`." Doesn't work — the underlying work still runs and any side effects in `then` chains down the line will still fire if reachable. You need to break the chain explicitly.

Another non-starter: "I'll mutate the Promise's internal state." There's no API. Promise state is private to the engine.

A subtle wrong answer: "I'll use `Promise.race` against a `cancel()`-rejected promise." This works for the consumer (`.race` settles first), but the original is still running and its `.then` handlers (if any) will still fire when it settles. Use only if you don't care about side effects in the original chain.

## Optimal approach
- For **real cancellation** (stopping the work): use `AbortController`. The work itself listens and tears down.
- For **wrapper cancellation** (ignoring the result): closure over a `cancelled` flag, override settlement in the wrapper.
- For **both**: combine — the wrapper listens to a signal and flips the flag.

## Solution (JavaScript)

```js
class CancelError extends Error {
  constructor() { super('Cancelled'); this.name = 'CancelError'; }
}

/**
 * Wrap a Promise so the caller can "cancel" — meaning, the wrapper will
 * reject with CancelError and never resolve/reject from the original.
 *
 * NOTE: this does NOT stop the underlying work. For that, use AbortController.
 *
 * @param {Promise<T>} promise
 * @returns {{ promise: Promise<T>, cancel: () => void, isCancelled: () => boolean }}
 * @template T
 */
function makeCancellable(promise) {
  let cancelled = false;

  const wrapped = new Promise((resolve, reject) => {
    promise.then(
      (value) => cancelled ? reject(new CancelError()) : resolve(value),
      (error) => cancelled ? reject(new CancelError()) : reject(error),
    );
  });

  return {
    promise: wrapped,
    cancel: () => { cancelled = true; },
    isCancelled: () => cancelled,
  };
}

/**
 * Modern version: bridge an AbortSignal to a cancel-on-abort wrapper.
 * Use this when wrapping APIs that don't natively accept a signal.
 */
function fromSignal(promise, signal) {
  const c = makeCancellable(promise);
  if (signal.aborted) c.cancel();
  else signal.addEventListener('abort', () => c.cancel(), { once: true });
  return c.promise;
}

/** Cancellable setTimeout via AbortController — real cancellation. */
function delay(ms, { signal } = {}) {
  return new Promise((resolve, reject) => {
    const onAbort = () => { clearTimeout(t); reject(new CancelError()); };
    const t = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    if (signal?.aborted) onAbort();
    else signal?.addEventListener('abort', onAbort, { once: true });
  });
}
```

## Step-by-step dry run

Input (wrapper approach):
```js
const slow = new Promise((resolve) => setTimeout(() => resolve('done'), 1000));
const { promise, cancel } = makeCancellable(slow);

promise.then(v => console.log('got', v), e => console.log('rej', e.name));

setTimeout(cancel, 100);   // cancel before slow resolves
```

Trace:
- `slow` is created; its 1000ms timer is started immediately.
- `makeCancellable(slow)`: creates `wrapped`. Inside `wrapped`'s executor, attaches `.then` to `slow`. Returns `{promise: wrapped, cancel}`.
- `promise.then(...)` attaches the user's handlers to `wrapped`.
- At t=100ms: `cancel()` runs. Sets `cancelled=true`.
- At t=1000ms: `slow` resolves with 'done'. The `.then` handler in `wrapped`'s executor fires: `cancelled` is true → reject(new CancelError()).
- `wrapped` rejects. User's `.then`'s rejection handler runs: prints `rej CancelError`.

The 1000ms timer **still fired**. The Promise resolved. Only the wrapper ignored it.

Input (AbortController approach — real cancellation):
```js
const ctrl = new AbortController();
delay(1000, { signal: ctrl.signal }).then(() => console.log('done'), e => console.log('rej', e.name));
setTimeout(() => ctrl.abort(), 100);
```

Trace:
- `delay(1000, {signal})` schedules a timer for 1000ms, attaches an abort listener.
- At t=100ms: `ctrl.abort()` fires the abort event. Listener calls `clearTimeout(t)` (actually cancels the timer) and rejects.
- The 1000ms timer **never fires**. The reject happens at t=100ms. Real cancellation.

## Important takeaways

**Syntax to memorize**
- Wrapper: closure over `cancelled` flag + override settlement in the wrapper's executor.
- Real cancellation: `AbortController` + `signal` + the underlying API listening.
- `signal.addEventListener('abort', fn, { once: true })` for one-shot listeners.
- `Promise.withResolvers()` (ES2024) gives you `{promise, resolve, reject}` without the constructor — cleaner for some cancellation patterns.

**Patterns to reuse**
- "Wrap and ignore" is the same pattern as: race-against-timeout, debounce-of-async (the abandoned call still settles but the wrapper ignores).
- AbortSignal is the canonical async-cancellation primitive — `fetch`, `fs.readFile`, `stream.pipeline`, `EventEmitter.once` all accept it. Reuse everywhere instead of inventing new cancellation APIs.

**Common mistakes**
- Claiming you've "cancelled the Promise" when really the work is still running.
- Not handling the "cancelled after settled" case — second-cancel should be no-op.
- Using `Promise.race` with a manually-rejected promise as a "cancel" — works for the consumer but doesn't reflect that the original is still doing work.
- Forgetting to remove the abort listener after settlement — memory leak in long-lived signals.
- Re-using a single `AbortController` for multiple operations and then can't cancel one without cancelling all.

**Related questions**
- `fetch` with timeout + abort (combine AbortController with setTimeout).
- `Promise.withResolvers` / Deferred pattern (ES2024).
- `Promise.race` for timeout enforcement.
- Cancellation in async generators (`return()` cleanup).
- Why TC39 dropped cancellable Promises (worth a 30-second narrative).

## Variants

1. **Promise + AbortSignal combination** — accept a signal in the API; on abort, both the wrapper rejects AND the underlying work is signalled to stop. Composes naturally with fetch / streams.

2. **Cancel with cleanup** — accept a `cleanup` function: `makeCancellable(promise, { onCancel: () => closeSocket() })`. On cancel, run cleanup before rejecting. Bridges to resource management.

3. **Hierarchical cancellation** — parent signal cancels all child signals. Built on `AbortSignal.any([...signals])` (ES2024). Useful for "cancel all in-flight requests for this user logout."

4. **Race with timeout** — `Promise.race([promise, delay(ms).then(() => { throw new TimeoutError(); })])`. Combine with cancellation so a timeout also cancels the underlying work.

5. **Async iterator cancellation** — `for await (const x of iter)` supports `iter.return()` to clean up. The async iterator protocol has explicit cancellation built in, unlike single Promises.

## Revision notes

> **Cancellable Promise — 75 second recap**
> - Native Promises are intentionally NOT cancellable — settlement is monotonic, executor is in charge.
> - Two flavors: (1) wrapper that **ignores** settlement (work still runs, consumer rejects). (2) AbortController — work itself listens and stops.
> - Wrapper: closure over `cancelled` flag; in the wrapper's executor, attach `.then` to original and override settlement based on flag.
> - Real answer in 2026: AbortController + signal. Pass signal into fetch / setTimeout (wrapped) / streams / etc.
> - `AbortSignal.any([...signals])` (ES2024) for hierarchical cancellation.
> - Trap: claiming you cancelled when work is still running. Not removing abort listeners (leak). Reusing one controller for multiple ops.
> - Mention: TC39 dropped Promise.cancel because chaining cancellation propagation is unsolvable cleanly. AbortController is the agreed answer.
