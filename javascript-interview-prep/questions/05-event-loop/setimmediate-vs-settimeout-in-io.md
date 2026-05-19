# `setImmediate` vs `setTimeout(0)` — inside an I/O callback

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md), [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md)
>
> **Source:** Node docs (the exact warning); libuv design doc. Classic interview question.

---

## 1. Problem statement

When does `setImmediate` deterministically beat `setTimeout(fn, 0)`, and when is it a race?

**Verification examples**

| Context                                | Order                                                  |
|----------------------------------------|---------------------------------------------------------|
| From main module                       | Non-deterministic (1ms timer-arming race)              |
| Inside an I/O callback (poll phase)    | `setImmediate` ALWAYS first (check follows poll)       |
| Inside a `setImmediate` callback        | `setTimeout(0)` next iter's timers fires before next check |
| Inside a `setTimeout` callback          | Non-deterministic again (back to main-like context)   |

**Constraints**
- `setTimeout(fn, 0)` is coerced to `setTimeout(fn, 1)` (1ms minimum in Node).
- Both lose to `process.nextTick` and microtasks.
- Browsers have no `setImmediate` (use `MessageChannel`).

---

## 2. Plain-English restatement

Both look like "run me after the current work." From the main module, it's a race — `setTimeout(0)` has a 1ms floor and the loop may or may not have reached its expiry by the time it enters the timers phase. From inside an I/O callback, you're in the **poll** phase; libuv's next phase is **check** (where `setImmediate` lives). So `setImmediate` deterministically wins. This is THE follow-up question after the basic ordering.

---

## 3. Why this matters in interviews

Exposes whether you've read the libuv design doc vs skimmed Stack Overflow. Pure-Node question.

---

## 4. Mental model

```
   libuv phase order, per iteration:
     timers → pending → idle/prepare → poll → check → close

   Inside fs.readFile callback (poll phase):
     poll cb returns → drain NT/MQ → move to check → setImmediate fires
                                                   → close → loop back to timers
   
   So inside I/O cb: setImmediate FIRST, setTimeout(0) on NEXT iteration.

   From main module:
     sync done → enter timers phase
     IS 1ms elapsed? RACE.
       yes → setTimeout(0) fires here → setImmediate in next check
       no  → skip timers → poll empty → check → setImmediate fires
                                                → next iteration → setTimeout(0)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. From main: which fires first?
> 2. Inside `fs.readFile`: which fires first? Why deterministic?
> 3. Why is `setTimeout(0)` actually `setTimeout(1)` in Node?

---

## 6. Brute force — walked through

### Wrong attempt 1: "run it 100 times and observe"
Loses interview points — predict, don't measure.

### Wrong attempt 2: "setImmediate is always first"
Wrong from main module.

### Wrong attempt 3: "setTimeout(0) is always first"
Wrong everywhere.

---

## 7. The unlocking insight

> **Inside I/O cb (poll phase): next phase is check → setImmediate deterministically wins. From main: race depends on whether 1ms (Node's minimum) elapsed when timers phase entered.**

Three properties:

1. **Phase order: poll → check → close → timers (next iter).**
2. **Main-module race**: 1ms minimum on `setTimeout(0)`.
3. **I/O-cb determinism** falls out of phase order.

---

## 8. Solution (annotated)

```js
const fs = require('node:fs');

// Inside I/O callback — DETERMINISTIC
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timer (I/O)'), 0);
  setImmediate(() => console.log('immediate (I/O)'));
  process.nextTick(() => console.log('nextTick (I/O)'));
  Promise.resolve().then(() => console.log('microtask (I/O)'));
});

// Output:
// nextTick (I/O)
// microtask (I/O)
// immediate (I/O)    ← DETERMINISTIC (check follows poll)
// timer (I/O)        ← runs in NEXT iteration

// From main module — RACE
setTimeout(() => console.log('timer (main)'), 0);
setImmediate(() => console.log('immediate (main)'));

// Output (varies):
// warm:  immediate (main), timer (main)
// slow:  timer (main), immediate (main)
```

**Try it yourself**

```js
// Force deterministic ordering from main: wrap in setImmediate
setImmediate(() => {
  setTimeout(() => console.log('timer first now'), 0);
  setImmediate(() => console.log('immediate second'));
});
// Output: timer first, immediate second
// (Now you're inside a check callback; next phase is close → timers.)
```

---

## 9. Step-by-step dry run

```
Inside I/O cb:

t=N    poll fires: cb runs.
       inside: register cb_T (timers), cb_I (check), cb_N (NT), cb_M (MQ).
       cb returns.
       Drain NT: cb_N → log 'nextTick (I/O)'.
       Drain MQ: cb_M → log 'microtask (I/O)'.
       Poll empty → move to check phase → run cb_I → log 'immediate (I/O)'.
       Drain NT, MQ (empty).
       close phase: empty.
Iteration 2:
       timers: cb_T deadline passed → run → log 'timer (I/O)'.

DETERMINISTIC ORDER: nextTick, microtask, immediate, timer.

From main:
t=0    register cb_T (timer=[cb_T@1ms]), cb_I (check=[cb_I]). sync done.
       Loop iteration 1: timers phase. IS 1ms passed?
         If YES → cb_T fires → 'timer (main)'. Then check → cb_I → 'immediate (main)'.
         If NO  → skip → poll empty → check → cb_I → 'immediate (main)'. Iter 2 → cb_T → 'timer'.
       RACE.
```

---

## 10. Common confusion + traps

1. **"setImmediate always first"** — wrong from main.
2. **"setTimeout(0) is 0ms"** — no, 1ms minimum.
3. **`process.nextTick` runs after them** — no, before both.
4. **Determinism from `setInterval` callback** — same race as main; only `poll` cb is deterministic.
5. **Inside `setImmediate` cb, scheduling another `setImmediate`** — next iter's check (not same).
6. **Browser equivalent** — no `setImmediate`; use `MessageChannel` or `setTimeout(0)`.
7. **Assuming determinism by running it once** — race may go one way most of the time.

---

## 11. Senior follow-ups & variants

### Variant 1 — Inside `setImmediate`, schedule setImmediate + setTimeout(0)
New `setImmediate` → next iter's check. `setTimeout(0)` → next iter's timers. Timers fires first.

### Variant 2 — Why Node's 1ms minimum?
HTML spec history + hardware-timer resolution + CPU jitter at sub-ms.

### Variant 3 — Force deterministic from main
Wrap in `setImmediate(() => { setTimeout(...); setImmediate(...) })`. Now inside check; timers comes before next check.

### Variant 4 — Browser equivalent
`MessageChannel.postMessage(0)` is the closest analog (faster than `setTimeout(0)` due to no 4ms clamp).

### Variant 5 — Yielding CPU
`setImmediate` is cheaper than `setTimeout(0)` (no timer heap). Use to break up long sync work.

---

## 12. How to think aloud

> "Inside an I/O callback, we're in the poll phase. libuv's next phase is check (where setImmediate lives). So setImmediate fires first deterministically; setTimeout(0) runs in the next iteration's timers phase. From main module, it's a race — Node coerces `setTimeout(0)` to 1ms minimum; whether the loop reaches timers before 1ms elapses depends on machine speed. Both lose to `process.nextTick` and microtasks. Browsers have no setImmediate; use `MessageChannel` for fast macrotask yield. Trap: claiming deterministic ordering from main."

---

## 13. 60-second revision

> - **Inside I/O cb:** setImmediate ALWAYS first (poll → check is fixed).
> - **From main:** race (1ms minimum on setTimeout(0); timer-arming jitter).
> - **`setTimeout(0)` is `setTimeout(1)`** under the hood.
> - **Both lose to** `process.nextTick` and microtasks.
> - **Force deterministic from main:** wrap in `setImmediate`.
> - **`setImmediate` cheaper** than `setTimeout(0)` (no timer heap).
> - **Browsers:** no setImmediate; use `MessageChannel`.
> - **Trap:** "setImmediate always first"; "setTimeout(0) is 0ms".

---

**Related:** [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md) · [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) · [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [`10-machine-coding-patterns/scheduler-idle-callback.md`](../10-machine-coding-patterns/scheduler-idle-callback.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
