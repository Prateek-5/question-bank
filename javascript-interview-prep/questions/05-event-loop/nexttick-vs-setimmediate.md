# process.nextTick vs setImmediate vs setTimeout(0)

## Source
- Canonical Node interview question — every senior Node round asks this.
- Node docs: https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick

## Why this question matters in interviews
Three APIs that all look like "run this later" but live in three different places in the loop. The interviewer is checking whether you can place each one on the correct rung:
- **`process.nextTick`** runs in its own queue, drained **between every callback**, before microtasks. NOT a libuv phase.
- **`setImmediate`** runs in libuv's **check** phase.
- **`setTimeout(fn, 0)`** runs in libuv's **timers** phase.

Bonus points for naming the deterministic vs non-deterministic ordering between `setImmediate` and `setTimeout(0)`. Backend engineers care because misuse of `nextTick` is one of the top three causes of event-loop starvation in production Node services.

## Concepts involved

### Where each one lives
```
   ┌──────────────────────────────────────┐
   │ Current callback (sync work)          │
   └──────────────────────────────────────┘
        ▼ after every callback returns
   ┌──────────────────────────────────────┐
   │ 1) process.nextTick queue  ← DRAIN    │
   │ 2) Microtask queue         ← DRAIN    │
   └──────────────────────────────────────┘
        ▼
   ┌──────────────────────────────────────┐
   │ Next libuv phase                      │
   │   - timers     ← setTimeout / setInterval
   │   - poll       ← I/O callbacks
   │   - check      ← setImmediate
   │   - close      ← 'close' events
   └──────────────────────────────────────┘
```

### Naming confusion (deliberate)
The names are historically backwards:
- `setImmediate` is NOT immediate — it runs in the **check** phase, after poll.
- `process.nextTick` does NOT run on the next loop tick — it runs **before** the next phase, at the END of the current operation. So it's more "immediate" than `setImmediate`.

Memorize: **nextTick > microtasks > everything else**.

### `setImmediate` vs `setTimeout(0)` ordering

| Context | Order |
|---------|-------|
| Called from **main module** | Non-deterministic. Depends on whether the 0ms timer deadline has elapsed by the time the loop reaches timers. |
| Called from inside an **I/O callback** (poll phase) | Deterministic: `setImmediate` first. Because after poll comes check, then a new iteration which arrives at timers. |
| Called from inside a `setImmediate` callback | Deterministic: `setImmediate` chained runs on the NEXT iteration's check; `setTimeout(0)` runs on the next iteration's timers (earlier in iteration). So `setTimeout(0)` first. |

This is the most common follow-up question after the basic ordering.

### Edge cases (interview traps)
1. **`process.nextTick` starvation** — recursive `process.nextTick(fn)` where `fn` schedules another nextTick prevents the loop from EVER advancing. No timers fire, no I/O completes. Worst kind of bug.
2. **Microtasks can also starve** — but slightly less likely because Promise chains usually terminate. `nextTick` is more dangerous because it's drained even more aggressively.
3. **Recommendation**: use `queueMicrotask` (or `Promise.resolve().then`) instead of `process.nextTick` for almost everything in user-land code. Reserve `nextTick` for the rare case of "I need to defer until the current operation completes but before any I/O" — historically used inside libraries that need to emit events after the constructor returns.
4. **`setImmediate(fn)` vs `setTimeout(fn, 0)` from main** — flaky tests are usually caused by relying on this ordering. Don't.
5. **`setImmediate` inside a hot loop** — preferred way to yield to the event loop without burning CPU. Better than `setTimeout(0)` because it doesn't go through the timers heap.
6. **`process.nextTick` runs even before queueMicrotask** — both in browser/Node, microtasks queue ≠ nextTick queue (Node only).
7. **Browsers don't have `process.nextTick` or `setImmediate`** (well, IE had setImmediate). Use `queueMicrotask` and `setTimeout(0)` instead.
8. **`Promise.resolve()` does NOT schedule on nextTick** — it's a microtask. They are separate queues.

## Brute force approach
"They all defer work." That's not enough. You must name the queue/phase each one uses and the priority order. The interviewer will then ask "what's the difference?" and you'll be back to square one.

## Optimal approach
Memorize the hierarchy:
1. `process.nextTick` queue — drained first (between every callback).
2. Microtask queue (Promise jobs) — drained next.
3. Macrotask phases — `setTimeout` (timers), I/O (poll), `setImmediate` (check), close callbacks.

Memorize the I/O-callback rule: `setImmediate` always beats `setTimeout(0)` from inside an I/O callback.

## Solution (JavaScript)

```js
// Side-by-side demonstration.
console.log('sync start');

setTimeout(() => console.log('setTimeout(0)'), 0);
setImmediate(() => console.log('setImmediate'));
process.nextTick(() => console.log('process.nextTick'));
Promise.resolve().then(() => console.log('promise.then (microtask)'));
queueMicrotask(() => console.log('queueMicrotask'));

console.log('sync end');

// Deterministic part of the output (Node):
// sync start
// sync end
// process.nextTick                ← drained first
// promise.then (microtask)        ← microtask drain
// queueMicrotask                  ← microtask drain (same priority as .then)
// setTimeout(0) and setImmediate  ← order between these two is non-deterministic
```

```js
// Inside an I/O callback the order between setImmediate and setTimeout(0)
// becomes DETERMINISTIC.
const fs = require('node:fs');

fs.readFile(__filename, () => {
  setTimeout(() => console.log('inner timeout(0)'), 0);
  setImmediate(() => console.log('inner immediate'));
  process.nextTick(() => console.log('inner nextTick'));
  Promise.resolve().then(() => console.log('inner microtask'));
});

// Output:
// inner nextTick
// inner microtask
// inner immediate                 ← DETERMINISTIC: check follows poll
// inner timeout(0)                ← runs in next iteration's timers phase
```

```js
// DANGER: nextTick starvation
function starve() {
  process.nextTick(starve);   // never lets the loop advance
}
setTimeout(() => console.log('I will NEVER print'), 100);
starve();
// The setTimeout callback never fires. The process burns 100% CPU.
```

## Step-by-step dry run

For the I/O-callback snippet:

| Step | Phase | NT | MQ | Timers | Check | Output |
|------|-------|----|----|--------|-------|--------|
| 1 | sync | — | — | — | — | — |
| 2 | sync | `fs.readFile` dispatched to libuv pool | — | — | — | — | — |
| 3 | sync done | — | — | — | — | — |
| 4 | loop iteration: timers (empty), pending (empty), poll → waits for fs | — | — | — | — | — |
| 5 | poll fires: fs cb runs; inside it: register `setTimeout` cbT, `setImmediate` cbI, `nextTick` cbN, `microtask` cbM | `[cbN]` | `[cbM]` | `[cbT@0]` | `[cbI]` | — |
| 6 | fs cb returns → drain NT → run cbN | — | `[cbM]` | `[cbT@0]` | `[cbI]` | `inner nextTick` |
| 7 | drain MQ → run cbM | — | — | `[cbT@0]` | `[cbI]` | `inner microtask` |
| 8 | poll done (no more I/O cbs) → check phase → run cbI | — | — | `[cbT@0]` | — | `inner immediate` |
| 9 | drain NT, MQ (both empty) | — | — | `[cbT@0]` | — | — |
| 10 | close phase: nothing | — | — | `[cbT@0]` | — | — |
| 11 | next iteration: timers → cbT's deadline passed → run cbT | — | — | — | — | `inner timeout(0)` |

Critical observation at step 8: after the I/O callback in poll, the loop moves to **check** before looping back to **timers**. That's why `setImmediate` deterministically wins inside an I/O callback.

For the nextTick starvation snippet:

| Step | Action | NT | Macro |
|------|--------|----|----|
| 1 | register `setTimeout` cbT@100 | — | `[cbT@100]` |
| 2 | call `starve()` → enqueue starve in NT | `[starve]` | `[cbT@100]` |
| 3 | sync done | `[starve]` | `[cbT@100]` |
| 4 | drain NT → run starve → enqueues starve again | `[starve]` | `[cbT@100]` |
| 5 | drain NT (re-enqueued) → run starve → enqueues starve again | `[starve]` | `[cbT@100]` |
| ... | infinite loop in step 5 | `[starve]` | `[cbT@100]` |

The loop never reaches the timers phase. `cbT` never fires.

## Important takeaways

**The hierarchy (memorize)**
1. Sync code (call stack)
2. `process.nextTick` queue
3. Microtask queue (Promise, `queueMicrotask`)
4. libuv phase callbacks (timers, pending, poll, check, close)

Steps 2 + 3 drain between every callback.

**The four "deferred" APIs**
| API | Queue | Order |
|-----|-------|-------|
| `process.nextTick(fn)` | nextTick queue | Before microtasks. Between every callback. |
| `queueMicrotask(fn)` / `Promise.resolve().then(fn)` | microtask queue | After nextTick. Between every callback. |
| `setImmediate(fn)` | check phase | Once per loop iteration, after poll. |
| `setTimeout(fn, 0)` | timers phase | Once per loop iteration, at the top. |

**When to use which**
- `queueMicrotask` — defer to "right after this sync block" without leaving the current macrotask. Modern idiom.
- `process.nextTick` — same as above but Node-only and higher priority. Rarely the right choice today; mostly used by older libraries (e.g., emitting 'error' events after construction).
- `setImmediate` — yield to the event loop, let pending I/O run, then resume. Great for chunking CPU work.
- `setTimeout(0)` — same effect, but goes through the timers heap. Slightly slower than `setImmediate`. Prefer `setImmediate` in Node.

**Common mistakes**
- Using `process.nextTick` thinking it's "the same as setImmediate" — it isn't.
- Relying on `setImmediate` vs `setTimeout(0)` ordering from main module — non-deterministic.
- Recursively scheduling `nextTick` to "batch" work — starves I/O.
- Saying `setImmediate` runs immediately — it doesn't; it runs in the check phase.

**Production lore**
- The `node:process` docs explicitly recommend AGAINST `process.nextTick` in new code. Prefer `queueMicrotask`.
- Express middleware once used `nextTick` heavily; modern code uses microtasks or `setImmediate` for chunking.
- `nextTick` starvation has crashed real services. If you find yourself reaching for it, justify why microtasks aren't enough.

## Variants

1. **"Predict the output"** — interviewer drops a snippet mixing all four. Walk the hierarchy.

2. **"How do you yield CPU to let I/O run?"** — `setImmediate` is the answer. Demonstrate chunking a big array reduce.

3. **"How would you implement an `asyncQueue` that respects backpressure?"** — call `setImmediate` between batches; await drain events.

4. **"What's the cost of `process.nextTick` vs `setImmediate`?"** — nextTick is cheaper (no libuv handle), but the priority cost is high. Don't optimize prematurely.

## Revision notes

> **nexttick-vs-setimmediate — 60 second recap**
> - **Hierarchy:** sync → `process.nextTick` → microtasks → libuv phase (timers/poll/check/close).
> - `process.nextTick` is **NOT** a microtask and **NOT** a libuv phase — it's its own queue with the highest deferred-priority.
> - `setImmediate` runs in the **check** phase (after poll). NOT immediate.
> - `setTimeout(0)` runs in the **timers** phase.
> - **From main module:** `setImmediate` vs `setTimeout(0)` order is non-deterministic.
> - **From inside an I/O callback:** `setImmediate` always wins (check follows poll deterministically).
> - **Trap:** recursive `process.nextTick` starves ALL I/O, timers, and immediates.
> - **Modern advice:** prefer `queueMicrotask` over `process.nextTick`; prefer `setImmediate` over `setTimeout(0)`.
> - Browsers have NO `process.nextTick` and NO `setImmediate` — use `queueMicrotask` and `setTimeout(0)`.
