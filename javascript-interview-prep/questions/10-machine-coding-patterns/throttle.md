# Implement `throttle(fn, wait, options?)` — at most once per window

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [debounce.md](./debounce.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** <a href="https://leetcode.com/problems/throttle/" target="_blank" rel="noopener noreferrer">LeetCode 2676 — Throttle</a>. The immediate follow-up to debounce.

---

## 1. Problem statement

**Signature**
```ts
function throttle<F extends (...args: any[]) => any>(
  fn: F,
  wait: number,
  options?: { leading?: boolean; trailing?: boolean }
): F & { cancel(): void };
```

**Input / Output examples**

| Setup                                                            | Behaviour                                              |
|-------------------------------------------------------------------|---------------------------------------------------------|
| 4 rapid calls within 100ms window                                 | 1 leading + 1 trailing = **2 invocations**             |
| Scroll handler throttled at 100ms                                 | fires regularly during continuous scroll               |
| `{ leading: false, trailing: true }`                              | suppresses first, fires once at end of window          |
| `{ leading: true, trailing: false }`                              | fires first, swallows rest, no trailing fire           |
| Continuous calls every 50ms with `wait=100`                       | fires every 100ms with latest args                     |

**Constraints**
- At most one invocation per `wait` ms.
- Default: both leading and trailing.
- Tracks `lastInvokeTime` + `timerId` (for trailing).
- Last-args-win: between window boundaries, intermediate calls are dropped.

---

## 2. Plain-English restatement

`throttle(fn, 100)` ensures `fn` runs **at most once every 100ms** — regardless of how often you call it. Where debounce *resets* the timer on every call (waits for silence), throttle *enforces a minimum spacing* between invocations. Use throttle for scroll/resize handlers, log shippers, analytics flushes — anywhere you want a steady stream of invocations during a continuous burst.

---

## 3. Why this matters in interviews

Throttle is the immediate follow-up to debounce. The interviewer's real test is whether you can articulate **the difference vs debounce**: debounce *resets* the timer on every call (fires once after silence); throttle *enforces a minimum spacing* between invocations (fires at most once per window). Getting that contrast crisp in one sentence is what separates a senior answer from a junior one. The implementation also forces you to handle the `leading` / `trailing` matrix.

---

## 4. Mental model

A **drip irrigation valve** — opens at most once per `wait` ms, regardless of how much pressure builds up.

```
   t=0   t('a'): no last invoke → fire immediately. lastInvokeTime=0.
   t=30  t('b'): remaining=70, schedule trailing T1 (t=100). lastArgs='b'
   t=60  t('c'): remaining=40, timer already set → overwrite lastArgs='c'
   t=100 T1 fires → fn('c'). lastInvokeTime=100.
   t=250 t('d'): remaining=-150 → fire immediately. lastInvokeTime=250.

   4 calls → 3 invocations
```

**vs debounce:**
- Debounce = wait for silence. Each call **resets** the timer. Fires once per burst, after burst ends.
- Throttle = rate-limit. Each call **respects** a minimum spacing. Fires regularly during a continuous burst, at most once per window.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With 5 calls every 20ms and `wait=100`, how many times does `fn` fire?
> 2. Why does throttle NOT call `clearTimeout` on every call (unlike debounce)?
> 3. Between window boundaries, which args reach `fn` — first or last?

---

## 6. Brute force — walked through

### Wrong attempt 1: track time, drop calls
```js
function throttle(fn, wait) {
  let lastInvokeTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastInvokeTime >= wait) {
      lastInvokeTime = now;
      fn.apply(this, args);
    }
    // else: drop
  };
}
```
Works for **leading-only** throttle but drops trailing args. If burst ends mid-window, last args lost. Add trailing timer.

### Wrong attempt 2: clearTimeout on every call
That's debounce, not throttle. Throttle lets in-flight timer **complete**.

### Wrong attempt 3: use `setInterval`
Drifts; double-fires on the boundary. Use `setTimeout` + recompute.

---

## 7. The unlocking insight

> **Two pieces of state: `lastInvokeTime` (timestamp) + `timerId` (trailing fire handle). On each call: compute `remaining = wait - (now - lastInvokeTime)`. If `<=0`, fire now and stamp. Else if no trailing timer scheduled, schedule one with latest args.**

Last-args-win: subsequent calls in the same window just overwrite `lastArgs`/`lastThis`. Only the latest reach `fn`.

Don't `clearTimeout` on every call — the timer must complete to enforce the spacing. That's the key difference from debounce.

---

## 8. Solution (annotated)

```js
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
    if (lastInvokeTime === 0 && !leading) lastInvokeTime = now;  // suppress leading

    const remaining = wait - (now - lastInvokeTime);
    lastArgs = args;
    lastThis = this;

    if (remaining <= 0 || remaining > wait) {                    // step 1: fire now
      if (timerId !== null) { clearTimeout(timerId); timerId = null; }
      invoke(now);
    } else if (timerId === null && trailing) {                    // step 2: schedule trailing once
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

**Try it yourself**

```js
const log = (msg) => console.log('fired:', msg, Date.now() % 1000);
const t = throttle(log, 100);

t('a');                                   // t=0  → fires immediately
setTimeout(() => t('b'), 30);             // t=30 → schedule trailing
setTimeout(() => t('c'), 60);             // t=60 → overwrite args
// t=100: trailing fires with 'c'
setTimeout(() => t('d'), 250);            // t=250 → fires immediately
```

---

## 9. Step-by-step dry run

```
t=0   t('a'): lastInvokeTime=0, leading=true. remaining=wait-(0-0)=100 but it's
              first call so we special-case: fire. lastInvokeTime=0. Output: a.
t=30  t('b'): remaining=100-30=70. No timer. trailing=true → schedule T1 (t=100).
              lastArgs=['b']
t=60  t('c'): remaining=100-60=40. Timer set → overwrite lastArgs=['c']
t=100 T1 fires → invoke(100) → fn('c'). lastInvokeTime=100. Output: c.
t=250 t('d'): remaining=100-(250-100)=-50. Fire immediately. lastInvokeTime=250.
              Output: d.
```

4 calls → 3 invocations. Trailing-edge call used **latest** args (`'c'`), not `'b'`.

With `{leading: false, trailing: true}`: t=0 suppressed → schedule T1 (t=100) → fires with `'c'`. Then t=250 → schedule T2 (t=350). Total: 2 invocations.

---

## 10. Common confusion + traps

1. **Confuse with debounce** — debounce clears timer every call; throttle does not.
2. **Forget trailing** — drops latest args at end of burst.
3. **Use `setInterval`** — drifts, double-fires.
4. **No first-call handling** — fires after `wait` instead of immediately.
5. **`Date.now()` vs `performance.now()`** — `Date.now()` is fine; `performance.now()` only for sub-ms precision.
6. **Reset `lastInvokeTime` in `cancel`** — otherwise next call sees stale stamp.
7. **last-args-win surprise** — middle calls' args are dropped.

---

## 11. Senior follow-ups & variants

### Variant 1 — `requestAnimationFrame` throttle
Browser-only; use `rAF` instead of `setTimeout(16)` for scroll/resize. Aligns with paint cycles; no drift.

### Variant 2 — Promise-returning throttle
Throttled function returns a Promise resolving to the eventual `fn` result. Closes over a `resolve` for the trailing call.

### Variant 3 — Sliding-window throttle
Count invocations in the last `wait` ms via a deque of timestamps. More accurate; O(N) memory per window. Bridge into rate-limiting.

### Variant 4 — `.cancel()` + `.flush()`
Symmetric with debounce — expose methods to clear pending trailing call or fire it immediately.

---

## 12. How to think aloud

> "Two pieces of state: `lastInvokeTime` + `timerId`. On each call: `remaining = wait - (now - lastInvokeTime)`. If `remaining <= 0` → fire and stamp. Else if no trailing timer set → schedule one. Don't `clearTimeout` on every call — that's debounce. Throttle enforces *spacing*; debounce waits for *silence*. Last-args-win: middle calls in a window overwrite `lastArgs`. For scroll handlers I'd use rAF throttle in browser — aligns with paint cycles."

---

## 13. 60-second revision

> - **At most one invocation per `wait` ms.**
> - **State:** `lastInvokeTime` + `timerId` + `lastArgs` + `lastThis`.
> - **`remaining = wait - (now - lastInvokeTime)`** — the core arithmetic.
> - **`remaining <= 0`** → fire + stamp; **else** schedule trailing (once).
> - **vs debounce:** throttle = *spacing*; debounce = *silence*.
> - **NEVER `clearTimeout` on every call** — that's debounce.
> - **Last-args-win** between window boundaries.
> - **Defaults:** leading + trailing both true.
> - **Trap:** writing debounce by accident; dropping trailing args; using setInterval.

---

**Related:** [debounce.md](./debounce.md) · [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md) · [batched-request-coalescer.md](./batched-request-coalescer.md) · [`04-promises/retry-with-backoff.md`](../04-promises/retry-with-backoff.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
