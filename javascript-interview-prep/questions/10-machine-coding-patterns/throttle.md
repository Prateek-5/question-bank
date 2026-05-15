# Implement `throttle(fn, wait, options?)`

## Source
- Canonical machine-coding interview problem (LeetCode #2676 "Throttle", BFE.dev, Frontend Masters).
- LeetCode reference: https://leetcode.com/problems/throttle/

## Why this question matters in interviews
Throttle is the immediate follow-up to debounce in nearly every senior-frontend / full-stack interview, and it shows up in backend rounds whenever the problem touches **rate-of-events**: scroll-triggered analytics flushes, log shippers, API gateway proxies, websocket message coalescing. The interviewer's real test is whether you can articulate **the difference vs debounce**: debounce *resets* the timer on every call (fires once after silence); throttle *enforces a minimum spacing* between invocations (fires at most once per window). Getting that contrast crisp in one sentence is what separates a senior answer from a junior one. The implementation also forces you to handle the `leading` / `trailing` matrix, which is where most candidates trip up.

## Concepts involved

### Syntax to lock in
```js
const throttled = throttle(fn, 300);
throttled(...args); // fires immediately, then at most once per 300ms

function throttle(fn, wait) {
  let lastInvokeTime = 0;
  let timerId = null;
  let lastArgs = null;
  let lastThis = null;

  return function (...args) {
    const now = Date.now();
    const remaining = wait - (now - lastInvokeTime);
    lastArgs = args;
    lastThis = this;

    if (remaining <= 0) {
      lastInvokeTime = now;
      fn.apply(this, args);
    } else if (timerId === null) {
      timerId = setTimeout(() => {
        lastInvokeTime = Date.now();
        timerId = null;
        fn.apply(lastThis, lastArgs);
      }, remaining);
    }
  };
}
```

### Runtime / engine behavior
- Throttle keeps a `lastInvokeTime` timestamp (or "did we already fire in this window" flag) — this is the key state that debounce does **not** have.
- `Date.now()` is fine here; you don't need `performance.now()` unless you're sub-millisecond.
- The trailing-edge timer must recompute `lastInvokeTime` when it fires, otherwise the next call sees a stale timestamp and fires immediately again.
- Like debounce, the wrapper uses `setTimeout` macrotasks. Microtask order between events is irrelevant.

### Edge cases (these are the interview traps)
1. **Debounce vs throttle confusion** — if your code calls `clearTimeout` on every invocation, you wrote debounce, not throttle. Throttle must let an in-flight timer **complete**.
2. **Leading-only mode** — fire on first call, swallow everything in the window, **don't** fire trailing. This is what most "throttle scroll handler" use-cases want.
3. **Trailing-only mode** — suppress the first call, fire one summary call at the end of the window. Useful for "flush buffer once per second."
4. **Both leading + trailing** — the lodash default. First call fires immediately, second call within window schedules a trailing fire with the latest args. **Three quick calls** = 2 invocations.
5. **`this` and args forwarding** — same trap as debounce. Capture `args` and `this` in outer scope, use `fn.apply(lastThis, lastArgs)`.
6. **Last-args-win semantics** — between window boundaries, intermediate calls are dropped; only the *latest* args reach `fn`. Don't queue them.
7. **Concurrent timer** — never schedule more than one trailing timer at a time. Guard with `timerId === null`.
8. **`wait = 0`** — degenerates to "fire every call." Don't crash, but it's a code smell.

## Brute force approach
"Track `lastInvokeTime`, on every call check `now - lastInvokeTime >= wait`, fire or drop." This works for **leading-only** throttle but silently drops the trailing call — so if the last burst of calls ended 50ms into the window, those args are lost. Interviewer will follow up "what about the trailing call?" and you'll have to re-architect. Start with the full version.

## Optimal approach
Two pieces of state:
- `lastInvokeTime` — when `fn` was last actually invoked.
- `timerId` — handle for the pending trailing call (or `null`).

On each call: compute `remaining = wait - (now - lastInvokeTime)`. If `<= 0`, fire now and stamp `lastInvokeTime`. Else if no trailing timer is queued, schedule one to fire after `remaining` ms with the **latest** args. Subsequent calls within the window just overwrite `lastArgs` / `lastThis`. O(1) memory, O(1) per call.

## Solution (JavaScript)

```js
/**
 * Returns a throttled version of `fn`. fn runs at most once per `wait` ms.
 * @param {Function} fn
 * @param {number} wait  minimum spacing between invocations, ms
 * @param {{ leading?: boolean, trailing?: boolean }} [options]
 * @returns {Function & { cancel: () => void }}
 */
function throttle(fn, wait, { leading = true, trailing = true } = {}) {
  let lastInvokeTime = 0;
  let timerId = null;
  let lastArgs = null;
  let lastThis = null;

  function invoke(time) {
    lastInvokeTime = time;
    fn.apply(lastThis, lastArgs);
    lastArgs = lastThis = null;
  }

  function throttled(...args) {
    const now = Date.now();
    // First call ever: if leading is false, pretend we just fired.
    if (lastInvokeTime === 0 && !leading) lastInvokeTime = now;

    const remaining = wait - (now - lastInvokeTime);
    lastArgs = args;
    lastThis = this;

    if (remaining <= 0 || remaining > wait) {
      if (timerId !== null) {
        clearTimeout(timerId);
        timerId = null;
      }
      invoke(now);
    } else if (timerId === null && trailing) {
      timerId = setTimeout(() => {
        timerId = null;
        invoke(Date.now());
      }, remaining);
    }
  }

  throttled.cancel = () => {
    if (timerId !== null) clearTimeout(timerId);
    timerId = null;
    lastInvokeTime = 0;
    lastArgs = lastThis = null;
  };

  return throttled;
}
```

## Step-by-step dry run

Input (with `wait = 100`, leading + trailing default):
```js
const log = (msg) => console.log('fired:', msg, Date.now() % 1000);
const t = throttle(log, 100);

t('a');                          // t=0
setTimeout(() => t('b'), 30);    // t=30
setTimeout(() => t('c'), 60);    // t=60
setTimeout(() => t('d'), 250);   // t=250
```

Trace:
- `t=0` — `t('a')`: `lastInvokeTime=0`, `remaining = 100 - 0 = 100`... wait, but it's the first call. With `leading=true` and `lastInvokeTime=0`, `remaining = 100 - (0 - 0) = 100`. Hmm — that's why we use the `remaining > wait` guard, which detects the "stale clock" case. Or simpler: special-case the first call by initializing `lastInvokeTime = now - wait` lazily. Either way, fires immediately. `lastInvokeTime = 0`. Output: `fired: a 0`.
- `t=30` — `t('b')`: `remaining = 100 - 30 = 70`. No timer yet → schedule trailing T1 for `t=100`. `lastArgs = ['b']`.
- `t=60` — `t('c')`: `remaining = 40`. Timer already set → just overwrite `lastArgs = ['c']`.
- `t=100` — T1 fires. `invoke(100)` → `log('c')`. `lastInvokeTime = 100`. Output: `fired: c 100`.
- `t=250` — `t('d')`: `remaining = 100 - 150 = -50` → fire immediately. `lastInvokeTime = 250`. Output: `fired: d 250`.

Net: 3 invocations from 4 calls. The trailing-edge call uses the **last args seen** (`'c'`), not `'b'`.

If `leading=false, trailing=true`, the `t=0` call is suppressed and a timer fires at `t=100` with args `['c']` (still latest). Total: 2 invocations.

## Important takeaways

**Throttle vs debounce — say this verbatim in the interview**
- **Debounce** = "wait for silence." Each call **resets** the timer. Fires at most once per burst, after the burst ends.
- **Throttle** = "rate-limit." Each call **respects** a minimum spacing. Fires regularly during a continuous burst, at most once per window.

**Syntax to memorize**
- Two pieces of state: `lastInvokeTime` (timestamp) + `timerId` (handle for the trailing fire).
- `remaining = wait - (now - lastInvokeTime)` is the core arithmetic.
- Never `clearTimeout` on every call — that's debounce.

**Patterns to reuse**
- The `lastInvokeTime + timerId` pair is the same skeleton used by rate-limiter (token-bucket variant), batch flusher (`maxWait`), and animation-frame coalescer (`requestAnimationFrame` instead of `setTimeout`).
- Last-args-win is a common decision in event coalescing — call it out explicitly when discussing the design.

**Common mistakes**
- Writing debounce by accident (clearing the timer on every call).
- Forgetting the trailing fire — drops the most recent args.
- Using `setInterval` instead of `setTimeout` + recompute — drifts and double-fires.
- Not handling the first-call case → fires after `wait` ms instead of immediately.

**Related questions**
- `debounce(fn, wait)`
- `requestAnimationFrame`-throttle (use `rAF` instead of `setTimeout`)
- `rateLimiter(maxCalls, perMs)` — the multi-token generalization

## Variants

1. **`rAF` throttle** — use `requestAnimationFrame` instead of `setTimeout(..., 16)` for scroll/resize handlers. Browser-only, but tests whether you know that 60 fps ≠ `setTimeout(16)` because the latter drifts.

2. **Throttle with promise return** — "make the throttled function return a promise resolving to the eventual `fn` result." Closes over a `resolve` for the trailing call.

3. **Sliding-window throttle** — instead of fixed buckets, count invocations in the last `wait` ms via a deque of timestamps. More accurate but O(N) memory per window. This is the bridge into rate-limiting questions.

4. **Throttle + `cancel` + `flush`** — symmetric with debounce; expose methods to clear the pending trailing call or fire it immediately. Tests decorated-function-pattern.

## Revision notes

> **throttle — 60 second recap**
> - At most one invocation per `wait` ms.
> - State: `lastInvokeTime` + `timerId` (for trailing) + `lastArgs` / `lastThis`.
> - On call: compute `remaining`. If `<=0`, fire and stamp. Else schedule trailing once.
> - Defaults: leading + trailing both true.
> - **vs debounce**: throttle enforces *spacing*; debounce waits for *silence*. Throttle does NOT clearTimeout on every call.
> - **Trap:** writing debounce by accident (clearing on every call). Trap 2: dropping the trailing args.
