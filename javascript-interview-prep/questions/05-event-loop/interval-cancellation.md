# Interval Cancellation

## Source
- LeetCode #2725 "Interval Cancellation": https://leetcode.com/problems/interval-cancellation/
- Canonical: the periodic-task primitive used by polling loops, heartbeats, metric emitters, watchdogs.

## Why this question matters in interviews
On the surface it's `setInterval` / `clearInterval`. But every senior interviewer follows up with: "Why is `setInterval` usually the wrong tool? When does the period drift? What if `fn` is async and overruns?". A backend engineer who can articulate the **re-arming `setTimeout` pattern** and explain **why `setInterval` ticks can stack up under load** has demonstrated real event-loop understanding. The first call running at `t=0` (not `t=t`) is also a classic trap.

## Concepts involved

### Syntax to lock in
```js
function cancellable(fn, args, t) {
  fn(...args);                                  // first call immediately
  const id = setInterval(() => fn(...args), t); // then every t ms
  return () => clearInterval(id);
}
```

### Runtime / engine behavior
- `setInterval(cb, t)` schedules `cb` to fire repeatedly in the **timers phase** of libuv. Each tick adds a new entry to the timers heap with a target time of `prev + t` (not `lastFired + t`).
- If a tick's callback runs longer than `t`, libuv will **not double-fire** — it skips overlapping ticks and resumes on the next aligned slot. Browsers behave similarly.
- `clearInterval(id)` removes the recurring entry. Like `clearTimeout`, calling it after the most recent tick already moved to the stack does not unwind that tick.
- The interval object in Node is a `Timeout` instance; `id.unref()` lets the event loop exit while it's still scheduled (useful for background heartbeats).

### Edge cases (interview traps)
1. **First call at t=0 vs t=t** — `setInterval(fn, t)` fires its FIRST tick at `t`, not at `0`. Most LeetCode-style prompts want the first call immediately; do it manually before scheduling.
2. **Long-running `fn`** — if `fn` is sync and takes longer than `t`, subsequent ticks queue up but Node coalesces; if `fn` is async (returns a Promise), there's **no overlap protection** — overlapping invocations can run concurrently.
3. **Drift** — `setInterval` does not guarantee exact `t` spacing under load. For accurate scheduling, use `setTimeout` re-armed manually (the "self-rescheduling" pattern).
4. **Cancel mid-tick** — calling cancel from inside `fn` itself is safe; the current invocation completes, no further ticks.
5. **`unref` / `ref`** — Node-only. An unref'd interval won't keep the process alive.
6. **Microtask starvation inside `fn`** — if `fn` schedules `process.nextTick` recursively, the next interval tick is delayed until nextTick queue drains.

## Brute force approach
"I'll use `setInterval` only and accept that the first tick happens at `t`." This fails the typical test case that asserts an immediate first invocation. Always call `fn(...args)` once before scheduling.

## Optimal approach
Invoke `fn` once synchronously, then `setInterval` for periodic firing, then return a closure over the id that calls `clearInterval`. O(1) per tick, O(1) cancel.

For drift-sensitive use cases, the alternative is a **self-rescheduling `setTimeout`** where each callback ends with `setTimeout(self, t)` — drift is bounded per-tick and async overruns naturally serialize.

## Solution (JavaScript)

```js
/**
 * Invokes fn(...args) immediately, then every t ms, until the
 * returned canceller is called.
 *
 * @param {(...args: any[]) => any} fn
 * @param {any[]} args
 * @param {number} t  period in ms
 * @returns {() => void}  cancellation function
 */
function cancellable(fn, args, t) {
  fn(...args);                                     // tick 0
  const id = setInterval(() => fn(...args), t);    // ticks 1..n
  return () => clearInterval(id);
}

// --- Drift-aware variant (preferred in production) ---
function cancellableDriftAware(fn, args, t) {
  let stopped = false;
  const tick = async () => {
    if (stopped) return;
    try { await fn(...args); } finally {
      if (!stopped) setTimeout(tick, t);
    }
  };
  tick();
  return () => { stopped = true; };
}
```

## Step-by-step dry run

Input:
```js
const result = [];
const fn = (x) => result.push(x);
const cancel = cancellable(fn, [7], 100);
setTimeout(cancel, 250);
```

Trace (timers heap shown as `[id@deadline]`):

| Time (ms) | Phase | Action | result |
|-----------|-------|--------|--------|
| 0 | sync | `cancellable` called → `fn(7)` runs immediately | `[7]` |
| 0 | sync | `setInterval` → schedules tick at 100 | `[7]` |
| 0 | sync | outer `setTimeout(cancel, 250)` scheduled | `[7]` |
| 100 | timers | interval tick → `fn(7)` | `[7,7]` |
| 100 | timers | next tick re-armed for 200 | `[7,7]` |
| 200 | timers | tick → `fn(7)` | `[7,7,7]` |
| 200 | timers | next tick re-armed for 300 | `[7,7,7]` |
| 250 | timers | `cancel` runs → `clearInterval(id)` | `[7,7,7]` |
| 300 | timers | heap empty for this id, no tick | `[7,7,7]` |

Now imagine `fn` is async and takes 150 ms:

| Time | Event |
|------|-------|
| 0 | `fn(7)` invoked, returns pending Promise. Sync stack unwinds. |
| 100 | interval tick fires → `fn(7)` invoked AGAIN. Now two are in flight. |
| 150 | first `fn` settles its promise. |
| 200 | another tick fires → `fn(7)` invoked. Three concurrent. |

This is why the drift-aware variant `await`s before re-arming.

## Important takeaways

**Syntax to memorize**
- `fn(...args)` then `setInterval(() => fn(...args), t)` then `return () => clearInterval(id)`.
- The arrow inside `setInterval` is what lets us forward `args` cleanly.

**Patterns to reuse**
- "Self-rescheduling setTimeout" is the prod pattern for: polling APIs, heartbeats, watchdogs, retry loops with stable spacing.
- Combine with `AbortSignal` for modern cancellation.

**Common mistakes**
- Returning the interval `id` directly instead of a closure → forces caller to call `clearInterval` themselves.
- Forgetting the immediate-first-tick. The LeetCode tests assert this.
- Assuming `setInterval` won't overlap async callbacks — it absolutely will.
- Recursively scheduling `process.nextTick` inside `fn` and starving subsequent ticks (and I/O).

**Where it sits in the event loop**
- Both the initial sync call and each periodic tick fire in libuv's **timers phase**.
- Microtasks and `process.nextTick` drain between ticks, just like any other macrotask boundary.

## Variants

1. **`setTimeout`-based polling** — write the same API but reschedule with `setTimeout` after each call settles. Eliminates async overlap, bounds drift per-tick.

2. **Exponential-backoff poller** — `period` grows on each empty result (e.g., long-polling). Same skeleton, dynamic `t`.

3. **Heartbeat with timeout watchdog** — combine `setInterval` for heartbeat emission with a parallel `setTimeout` watchdog that fires if no ack arrives.

4. **`AbortSignal`-driven** — accept a signal instead of returning a canceller. `signal.addEventListener('abort', () => clearInterval(id))`.

## Revision notes

> **interval-cancellation — 60 second recap**
> - First call must be **manual** — `setInterval` fires first tick at `t`, not `0`.
> - Period is **best-effort**; libuv timers can drift under load.
> - `setInterval` does NOT serialize async overruns — concurrent invocations possible.
> - Preferred prod pattern: self-rescheduling `setTimeout` with `await`.
> - `clearInterval(id)` removes the recurring entry; safe after cancel.
> - Same `Timeout` object as `setTimeout`; `id.unref()` lets process exit.
> - **Trap:** recursive `process.nextTick` inside `fn` starves the next interval tick AND all I/O.
> - **Trap:** assuming spacing is exact — never use `setInterval` for billing windows or rate limiting.
