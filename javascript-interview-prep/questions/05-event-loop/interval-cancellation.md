# Interval Cancellation — `setInterval` + `clearInterval`

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [timeout-cancellation.md](./timeout-cancellation.md)
>
> **Source:** [LeetCode 2725 — Interval Cancellation](https://leetcode.com/problems/interval-cancellation/).

---

## 1. Problem statement

**Signature**
```ts
function cancellable(fn: (...args: any[]) => any, args: any[], t: number): () => void;
```

**Input / Output examples**

| Setup                                            | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| `cancel = cancellable(fn, [7], 100)`              | `fn(7)` runs at t=0, t=100, t=200, ...                  |
| Call `cancel()` at t=250                          | t=0, 100, 200 fired; t=300 onwards skipped              |
| Async `fn` taking > t                              | `setInterval` does NOT serialize; overlapping calls possible |
| `setInterval` drift under load                    | best-effort spacing, not guaranteed                    |

**Constraints**
- **First call must be manual** — `setInterval(fn, t)` fires first at `t`, not 0.
- `setInterval` ticks don't serialize async overruns.
- Drift under load — never use for billing windows or rate limiting.
- Drift-aware variant: self-rescheduling `setTimeout` with `await`.

---

## 2. Plain-English restatement

Schedule `fn(...args)` to run NOW, then every `t` ms, until cancelled. Return a closure that calls `clearInterval`. The trick: `setInterval` fires its FIRST tick at `t`, not 0, so call `fn` once manually before scheduling.

---

## 3. Why this matters in interviews

Tests whether you understand `setInterval`'s drift behavior, the immediate-first-tick contract, and async-overrun gotchas. Senior follow-up: self-rescheduling `setTimeout` for production-grade polling.

---

## 4. Mental model

```
   Naive setInterval(fn, t):
   t=0     fn NOT called (setInterval's first tick is at t, not 0)
   t=t     fn fires
   t=2t    fn fires
   ...

   With manual first call:
   t=0     fn(...args) called synchronously
   t=t     interval tick → fn fires
   t=2t    interval tick → fn fires
   ...
   cancel() → clearInterval(id) → no more ticks

   Drift under load:
   t=100   tick scheduled; main thread busy → fires at t=130
   t=200   tick at t=230
   t=300   tick at t=330
   ↑ drift accumulates

   Async overruns:
   t=0     await fn() → still running at t=100
   t=100   setInterval fires → fn() invoked AGAIN. TWO CONCURRENT.
   ↑ setInterval doesn't await your fn
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `setInterval(fn, 100)` call `fn` at t=0?
> 2. If `fn` is async and takes 150ms, what happens with `setInterval(fn, 100)`?
> 3. Why is `setInterval` bad for "exactly every 100ms" billing windows?

---

## 6. Brute force — walked through

### Wrong attempt 1: `setInterval(fn, t)` alone
First tick at `t`, not 0. Fails the "fn(7) at t=0" test.

### Wrong attempt 2: assume async fn serializes
Overlapping invocations under async overruns.

### Wrong attempt 3: rely on exact `t` spacing
Drifts under load; never use for billing.

---

## 7. The unlocking insight

> **Invoke `fn(...args)` once synchronously, then `setInterval` for periodic firing. Return closure over id calling `clearInterval`. For production, prefer self-rescheduling `setTimeout` with `await` — bounds drift per-tick and serializes async overruns.**

Three properties:

1. **Manual first call** for `fn(...args)` at t=0.
2. **`setInterval` drift** under load — never use for exact spacing.
3. **Async overruns** can run concurrently — self-rescheduling `setTimeout` fixes.

---

## 8. Solution (annotated)

```js
function cancellable(fn, args, t) {
  fn(...args);                                                       // step 1: tick 0
  const id = setInterval(() => fn(...args), t);                       // step 2: ticks 1..n
  return () => clearInterval(id);                                     // step 3: closure canceller
}

// Drift-aware production variant
function cancellableDriftAware(fn, args, t) {
  let stopped = false;
  const tick = async () => {
    if (stopped) return;
    try { await fn(...args); } finally {
      if (!stopped) setTimeout(tick, t);                              // step 4: re-schedule after await
    }
  };
  tick();
  return () => { stopped = true; };
}
```

**Try it yourself**

```js
const result = [];
const fn = (x) => result.push(x);
const cancel = cancellable(fn, [7], 100);
setTimeout(cancel, 250);
// At t=300: result === [7, 7, 7]   (ticks at 0, 100, 200; cancel at 250 stops 300)

// Async overrun problem
async function slow() { await new Promise((r) => setTimeout(r, 150)); }
const c = cancellable(slow, [], 100);
// At t=100: slow() at t=0 still running; setInterval fires another slow() → TWO IN FLIGHT.

// Drift-aware fix
const c2 = cancellableDriftAware(slow, [], 100);
// At t=150: first slow() finishes; reschedule setTimeout for t=250.
// No overlap.
```

---

## 9. Step-by-step dry run

```
Naive setInterval, fn sync (1ms), t=100, cancel at 250:

t=0    fn(7) sync → result=[7]
       setInterval → tick scheduled at t=100. heap: [tick@100].
       outer setTimeout(cancel, 250).
t=100  timers phase: tick → fn(7) → result=[7,7]. Re-arms tick@200.
t=200  timers phase: tick → fn(7) → result=[7,7,7]. Re-arms tick@300.
t=250  timers phase: cancel runs → clearInterval. heap: [].
t=300  heap empty for this id → no tick.

result === [7, 7, 7].

Async overrun (fn returns Promise that takes 150ms):
t=0    fn() called; returns pending promise; result.push(initiated)
t=100  setInterval tick: fn() called AGAIN; another pending promise
       2 IN FLIGHT
t=150  first fn settles
t=200  another tick: fn() called; first one settled; second still running
       2 IN FLIGHT still
t=300  ...

Drift-aware variant:
t=0    tick() → await slow() (150ms)
t=150  slow() done; setTimeout(tick, 100)
t=250  tick() → await slow()
t=400  slow() done; setTimeout(tick, 100)
t=500  ...

No overlap. Spacing = 100 + slow_duration, not 100.
```

---

## 10. Common confusion + traps

1. **First tick at t=0** — no, at t=t; call manually.
2. **Async overrun serialization** — no, `setInterval` doesn't await.
3. **Exact spacing** — drifts under load.
4. **`unref` keeps process alive** — `id.unref()` makes interval NOT keep alive.
5. **Cancel from inside fn** — safe; current invocation completes.
6. **Microtask starvation inside fn** — delays next interval tick.
7. **Same as `setTimeout` cancel** — different cancel API (`clearInterval`).

---

## 11. Senior follow-ups & variants

### Variant 1 — Self-rescheduling `setTimeout` (production)
Bounds drift per-tick; serializes async overruns. Above as `cancellableDriftAware`.

### Variant 2 — Exponential-backoff poller
Period grows on empty result (long-polling pattern).

### Variant 3 — Heartbeat + watchdog
`setInterval` heartbeat + parallel `setTimeout` watchdog firing if no ack.

### Variant 4 — `AbortSignal`-driven
`signal.addEventListener('abort', () => clearInterval(id))`.

### Variant 5 — `id.unref()` for background
Process can exit while interval still scheduled (background heartbeats).

---

## 12. How to think aloud

> "`fn(...args)` once synchronously (test asserts immediate first invocation), then `setInterval(() => fn(...args), t)`, return closure over id calling `clearInterval`. Caveats: `setInterval` ticks don't serialize async overruns — concurrent invocations possible. `setInterval` drifts under load — never for exact spacing. Production pattern: self-rescheduling `setTimeout` with `await` — bounds drift per-tick, serializes overruns. Trap: forgetting immediate first call; assuming async serializes; assuming exact spacing."

---

## 13. 60-second revision

> - **First call manual** — `setInterval` first tick at `t`, not 0.
> - **Closure return** `() => clearInterval(id)`, not raw id.
> - **`setInterval` doesn't await** — async overruns can overlap.
> - **Drifts under load** — never for billing/rate-limiting.
> - **Production:** self-rescheduling `setTimeout(tick, t)` with `await`.
> - **`id.unref()`** lets process exit (background heartbeats).
> - **Trap:** first-tick-at-t; async overlap; exact spacing assumption.

---

**Related:** [timeout-cancellation.md](./timeout-cancellation.md) · [cancellable-function.md](./cancellable-function.md) · [`10-machine-coding-patterns/scheduler-idle-callback.md`](../10-machine-coding-patterns/scheduler-idle-callback.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
