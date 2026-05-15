# `setImmediate` vs `setTimeout(fn, 0)` — ordering inside an I/O callback

## Source
- Node.js docs (the exact warning): https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick#setimmediate-vs-settimeout
- libuv design doc: http://docs.libuv.org/en/v1.x/design.html
- Classic interview question — appears in every Node interview cheat sheet.

## Why this question matters in interviews
The "trick" answer is: **inside an I/O callback, `setImmediate` always fires first; from the main module, it's non-deterministic.** Candidates who only memorize "setImmediate is the check phase" miss the *why* — and miss the followup about how the loop actually entered the timers phase. This is the question that exposes whether you've read the libuv design doc or just skimmed Stack Overflow. It's a pure-Node question; the browser has no `setImmediate` (it's non-standard, removed from MS Edge).

## Concepts involved

### The libuv phase order (every loop iteration)
1. `timers` — runs callbacks scheduled by `setTimeout` / `setInterval` whose expiry has elapsed.
2. `pending callbacks` — handful of system-level I/O callbacks.
3. `idle, prepare` — internal.
4. `poll` — fetches new I/O events; runs I/O callbacks here. Blocks if nothing to do (with a calculated timeout).
5. `check` — runs `setImmediate` callbacks.
6. `close callbacks` — `'close'` events.

### Why inside an I/O callback ordering is deterministic
You're in the **poll** phase. The phase right after poll is **check**. So if you schedule both:
```js
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});
```
After the readFile callback returns, libuv moves to **check** — fires `immediate`. Then continues to close, then loops back to timers — fires `timeout`. **`immediate` always first.**

### Why from the main module ordering is non-deterministic
```js
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
```
- The main script runs.
- `setTimeout(fn, 0)` is actually coerced to `setTimeout(fn, 1)` (min 1ms).
- Sync code ends.
- The loop enters the **timers** phase.
- **Question:** has 1ms elapsed?
  - If yes (process is slow / loaded) → timer cb fires → `timeout` logs. Then check runs → `immediate`.
  - If no (process is fast) → timer skipped → loop advances → poll (empty) → check fires → `immediate` logs. Next iteration → timers fires → `timeout`.
- **Race condition**. The result depends on how fast the runtime made it from main-script completion to the timers-phase entry.

### Syntax to lock in
```js
const fs = require('node:fs');

// Deterministic: immediate before timeout
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});

// Non-deterministic: race
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
```

### Edge cases
1. **`setImmediate(fn)` vs `setImmediate(fn)` x N**: all queued go into the same `check` phase. They drain in FIFO order.
2. **`setTimeout(fn, 0)` is `setTimeout(fn, 1)` under the hood** — Node coerces. This is the source of the race.
3. **`process.nextTick`** wins over both, always — it runs *before* any libuv phase advances.
4. **Inside `setImmediate`, calling `setImmediate` again** schedules into the *next* iteration's check phase. Not the same one.
5. **`setTimeout(fn, 0)` inside `setImmediate`** → next timers phase fires it. Order: this immediate → close → timers (timeout fires) → poll → check (next immediate).
6. **CPU-bound work in main script** can shift the race outcome — slower main = timer fires first more often.
7. **Worker thread**: each worker has its own loop. Ordering rules apply per-loop.

## Brute force approach
"Run it 100 times and observe." This is the wrong answer in an interview. The whole point is to **predict** based on phase order. If your answer is "it depends" without explaining *why*, you've failed.

## Optimal approach
Two clean sentences:
- "Inside an I/O callback, we're in the poll phase. The next phase is check, where setImmediate lives. So setImmediate fires first, deterministically."
- "From the main module, the race is between timer-expiry detection and entering the check phase. Node coerces `setTimeout(fn, 0)` to a 1ms minimum, so the outcome depends on whether 1ms has elapsed when the timers phase is entered. Both orderings are valid."

## Solution (JavaScript)

```js
const fs = require('node:fs');

// ----------------------------
// Case 1: Inside I/O callback
// ----------------------------
console.log('--- inside I/O ---');
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer (I/O)'), 0);
  setImmediate(() => console.log('immediate (I/O)'));
  process.nextTick(() => console.log('nextTick (I/O)'));
  Promise.resolve().then(() => console.log('microtask (I/O)'));
});

// Output (deterministic):
// nextTick (I/O)
// microtask (I/O)
// immediate (I/O)
// timer (I/O)

// ----------------------------
// Case 2: From main module
// ----------------------------
setTimeout(() => console.log('timer (main)'), 0);
setImmediate(() => console.log('immediate (main)'));

// Output (NON-deterministic):
//   On a "warm" machine:  immediate (main), timer (main)
//   On a "slow" machine:  timer (main), immediate (main)
//   Run 100 times → you'll see both orderings.
```

### Why the I/O case is interview gold
Inside `readFile`'s cb:
- We're in **poll phase**.
- `process.nextTick` queue drained first → logs `nextTick (I/O)`.
- Microtask queue drained → logs `microtask (I/O)`.
- Poll cb returns. Loop continues to **check** → fires immediate → logs `immediate (I/O)`.
- Drain nextTick + microtask (empty).
- Loop continues to **close**, then loops back to **timers** → fires timeout → logs `timer (I/O)`.

## Step-by-step dry run

Walk through Case 1 (inside I/O) explicitly:

| Step | Loop state | Action | Output |
|------|------------|--------|--------|
| 1 | poll phase, in readFile cb | log nothing yet, schedule timer/immediate/nextTick/microtask | — |
| 2 | poll phase, cb returns | drain nextTick queue | `nextTick (I/O)` |
| 3 | poll phase | drain microtask queue | `microtask (I/O)` |
| 4 | move to check phase | run setImmediate cb | `immediate (I/O)` |
| 5 | check phase, cb returns | drain nextTick + microtask (empty) | — |
| 6 | close phase | nothing | — |
| 7 | next iteration: timers phase | timer is ready (1ms elapsed by now) | `timer (I/O)` |

Order: `nextTick → microtask → immediate → timer`. Deterministic.

## Important takeaways

**Syntax to memorize**
- `setImmediate(fn)` — Node-only, `check` phase. Use when "give I/O a chance, then run me."
- `setTimeout(fn, 0)` — `timers` phase. Coerced to `setTimeout(fn, 1)` (min 1ms).
- `process.nextTick(fn)` — beats both. Drained before any phase advance.

**Patterns to reuse**
- **Inside a libraray callback, you don't always know if you're in I/O or main**. If determinism matters, document the assumption (e.g., "this is always called after I/O").
- **Breaking up long sync work**: `setImmediate(continueLoop)` is the canonical pattern. It guarantees poll runs each iteration.
- **Cooperative multitasking in Node** is built on this: heavy CPU → break into `setImmediate` chunks.

**Common mistakes**
- Saying "setImmediate is always first." Wrong from main module.
- Saying "setTimeout(0) is always first." Wrong from anywhere.
- Forgetting that `process.nextTick` and microtasks fire *between* phases — both fire before `setImmediate` *and* before `setTimeout(0)`.
- Believing `setTimeout(fn, 0)` is really 0ms. Node enforces a 1ms minimum.

**Related questions**
- libuv 6-phase loop
- `process.nextTick` priority
- `process.nextTick` starvation

## Variants

1. **"Inside a `setImmediate`, you schedule another `setImmediate` and a `setTimeout(0)`. Which fires first?"** — The new immediate goes to *next* iteration's check phase. The timer goes to next iteration's timers phase. Timer fires first (timers comes before check in phase order).
2. **"Why does Node enforce a 1ms minimum on `setTimeout(fn, 0)`?"** — Historical: matches HTML spec's 4ms minimum for nested timers but with looser 1ms for top-level. Also: hardware timer resolution and CPU jitter at sub-ms is unreliable.
3. **"How would you guarantee `setTimeout(0)` runs before `setImmediate` from main module?"** — You can't, deterministically. Best you can do is wrap in `setImmediate(() => setTimeout(0, fn))` — now you're inside check, so the next timers phase fires before the next check.
4. **"What's the equivalent in the browser?"** — Browsers don't have `setImmediate`. Closest is `MessageChannel` (next macrotask) or `queueMicrotask` (microtask). `setTimeout(fn, 0)` is `setTimeout(fn, 4)` for nested timers (HTML5 spec).

## Revision notes

> **setImmediate vs setTimeout(0) — 60 second recap**
> - **Inside I/O cb**: setImmediate **always** fires before setTimeout(0). Deterministic. We're in poll → check comes next.
> - **From main module**: race. Depends on whether the 1ms min-delay has elapsed when timers phase is entered.
> - `setTimeout(fn, 0)` is coerced to 1ms in Node.
> - Both lose to `process.nextTick` and microtasks (queueMicrotask / Promise.then).
> - Use `setImmediate` to break up long CPU work — yields to poll each iteration.
> - **Trap**: claiming deterministic ordering from main script. It's not.
