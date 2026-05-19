# `process.nextTick` vs `setImmediate` vs `setTimeout(0)`

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md), [microtask-macrotask-order.md](./microtask-macrotask-order.md)
>
> **Source:** Canonical Node interview question.

---

## 1. Problem statement

Three Node APIs that all "run later" but live in three different places in the loop.

**Verification examples**

| API                           | Where it runs                                  | Priority                |
|--------------------------------|------------------------------------------------|--------------------------|
| `process.nextTick(fn)`        | Its own queue (NOT a phase)                    | Highest deferred         |
| `queueMicrotask` / `.then`    | Microtask queue                                | After nextTick           |
| `setImmediate(fn)`            | libuv check phase                              | Macrotask, post-poll     |
| `setTimeout(fn, 0)`           | libuv timers phase                             | Macrotask, top of loop   |

**Ordering rules**

| Context                            | `setImmediate` vs `setTimeout(0)`              |
|-------------------------------------|-------------------------------------------------|
| From main module                    | Non-deterministic (timer-arming race)          |
| From inside an I/O callback         | `setImmediate` ALWAYS wins (check follows poll)|
| From inside `setImmediate`          | `setTimeout(0)` next iteration (timers first)  |

**Constraints**
- `process.nextTick` runs between every callback (NOT a phase).
- Recursive nextTick STARVES all I/O.
- Browsers have no `nextTick`/`setImmediate`.

---

## 2. Plain-English restatement

Three names that look interchangeable but aren't. **`nextTick`** is Node-specific, drained between every callback, highest priority. **`setImmediate`** runs in libuv's check phase, after I/O. **`setTimeout(0)`** runs in libuv's timers phase. The misleading names: `setImmediate` is NOT immediate; `nextTick` does NOT run on the next loop tick.

---

## 3. Why this matters in interviews

Backend interviewer's go-to test. Misuse of `nextTick` is one of the top three causes of event-loop starvation in production Node. Knowing the I/O-callback determinism rule is the senior follow-up.

---

## 4. Mental model

```
   ┌───────────────────────────────────────┐
   │ Current callback (sync work)           │
   └───────────────────────────────────────┘
        ▼ after every callback returns
   ┌───────────────────────────────────────┐
   │ 1. process.nextTick queue   ← drain    │
   │ 2. Microtask queue           ← drain   │
   └───────────────────────────────────────┘
        ▼
   ┌───────────────────────────────────────┐
   │ Next libuv phase                       │
   │   - timers    ← setTimeout/setInterval │
   │   - poll      ← I/O callbacks          │
   │   - check     ← setImmediate           │
   │   - close     ← 'close' events         │
   └───────────────────────────────────────┘

   Memorize: nextTick > microtasks > everything else.

   Names are historically backwards:
   - setImmediate is NOT immediate (runs in check phase)
   - nextTick does NOT run on next tick (runs BEFORE next phase)
     → nextTick is more immediate than setImmediate.

   Inside an I/O callback (poll phase):
     next phase is check → setImmediate beats setTimeout(0) deterministically.
   From main module:
     loop entry timing is racy → order unpredictable.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. From main: which runs first, `setImmediate` or `setTimeout(0)`?
> 2. Inside `fs.readFile` callback: which runs first?
> 3. What does `process.nextTick(loop)` (recursive) do?

---

## 6. Brute force — walked through

### Wrong attempt 1: "they all defer work"
Not enough — name the queue/phase each uses.

### Wrong attempt 2: "nextTick is a microtask"
No — separate higher-priority Node-specific queue.

### Wrong attempt 3: "setImmediate runs immediately"
No — runs in check phase, after poll.

---

## 7. The unlocking insight

> **Hierarchy: sync → `process.nextTick` → microtasks → libuv phase (timers/poll/check/close). Inside I/O callback, `setImmediate` deterministically beats `setTimeout(0)`. Recursive `nextTick` starves I/O.**

Three properties:

1. **`nextTick` is not a phase, not a microtask** — its own queue.
2. **Inside I/O cb:** `setImmediate` wins (poll → check is fixed order).
3. **Recursive nextTick** starves the entire loop.

---

## 8. Solution (annotated)

```js
console.log('sync start');

setTimeout(() => console.log('setTimeout(0)'), 0);                   // step 1: timers phase
setImmediate(() => console.log('setImmediate'));                      // step 2: check phase
process.nextTick(() => console.log('process.nextTick'));              // step 3: NT queue
Promise.resolve().then(() => console.log('promise.then'));            // step 4: microtask
queueMicrotask(() => console.log('queueMicrotask'));                  // step 5: microtask

console.log('sync end');

// Output (deterministic part):
// sync start
// sync end
// process.nextTick              ← drained first
// promise.then                  ← MQ drain
// queueMicrotask                ← MQ drain (same priority, FIFO)
// setTimeout(0) and setImmediate ← order racy from main module
```

**Inside an I/O callback — deterministic ordering:**

```js
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
// inner immediate          ← DETERMINISTIC: check follows poll
// inner timeout(0)         ← runs in NEXT iteration's timers phase
```

**Try it yourself — DANGER: nextTick starvation**

```js
function starve() { process.nextTick(starve); }
setTimeout(() => console.log('I NEVER print'), 100);
starve();
// Process burns 100% CPU; setTimeout callback never fires.
```

---

## 9. Step-by-step dry run

```
fs.readFile callback example:

t=0    fs.readFile dispatched to libuv pool. sync done.
t=0    loop iteration: timers (empty), pending (empty), poll → waits for fs.

t=N    poll fires: fs cb runs. Inside it:
        setTimeout(cb_T, 0)              timers=[cb_T]
        setImmediate(cb_I)                check=[cb_I]
        process.nextTick(cb_N)            NT=[cb_N]
        Promise.resolve().then(cb_M)      MQ=[cb_M]
       fs cb returns → drain NT (cb_N → log 'inner nextTick')
                       drain MQ (cb_M → log 'inner microtask')
       poll empty → check phase → run cb_I → log 'inner immediate'
       drain NT, MQ (empty)
       close phase: nothing
       next iteration: timers → cb_T's deadline passed → run cb_T → log 'inner timeout(0)'

Output: nextTick, microtask, immediate, timeout(0).

Recursive nextTick:
  call starve() → enqueue starve in NT.
  drain NT → run starve → re-enqueue starve in NT.
  drain NT → infinite loop. Never advance to timers/poll/check.
  CPU 100%, timers never fire.
```

---

## 10. Common confusion + traps

1. **nextTick is a microtask** — no, separate higher-priority queue.
2. **setImmediate "runs immediately"** — no, check phase.
3. **From main: deterministic order between setImmediate/setTimeout(0)** — non-deterministic.
4. **Recursive nextTick to "batch" work** — STARVES I/O.
5. **Promise.resolve() runs on nextTick** — no, microtask.
6. **Browsers have setImmediate** — no (except IE).
7. **`setImmediate` vs `setTimeout(0)` for yielding CPU** — both yield; `setImmediate` is cheaper (no timer heap).

---

## 11. Senior follow-ups & variants

### Variant 1 — "How yield CPU to let I/O run?"
`setImmediate`. Demonstrate chunking a big array reduce.

### Variant 2 — "Build a CPU-yielding worker"
`setImmediate` between batches; check `signal.aborted` for cancellation.

### Variant 3 — "Cost of nextTick vs setImmediate"
nextTick is cheaper (no libuv handle), but priority cost is high. Don't optimize prematurely.

### Variant 4 — `process.nextTick` in old libraries
Express middleware once used it heavily. Modern code uses microtasks or `setImmediate`.

### Variant 5 — Node 11+ behavior
Microtasks drain between every callback (was every phase before).

---

## 12. How to think aloud

> "Three APIs, three places. `process.nextTick` is Node-only, its own queue, drained between every callback — highest deferred priority. `setImmediate` runs in libuv's check phase (after poll). `setTimeout(0)` runs in libuv's timers phase. Names are misleading: `setImmediate` is NOT immediate; `nextTick` does NOT run on next tick. From main module: `setImmediate` vs `setTimeout(0)` is RACY. From inside an I/O callback: `setImmediate` deterministically wins (check follows poll). Recursive nextTick STARVES all I/O — top-3 production Node bug. Modern advice: prefer `queueMicrotask` over `nextTick`; prefer `setImmediate` over `setTimeout(0)`."

---

## 13. 60-second revision

> - **Hierarchy:** sync > nextTick > microtasks > libuv phase (timers/poll/check/close).
> - **`nextTick`** is NOT a microtask, NOT a libuv phase — own queue, highest deferred.
> - **`setImmediate`** = check phase. **`setTimeout(0)`** = timers phase.
> - **From main:** setImmediate vs setTimeout(0) RACY.
> - **From inside I/O cb:** setImmediate deterministically wins.
> - **Recursive nextTick STARVES** all I/O.
> - **Browsers have neither** — use `queueMicrotask`/`setTimeout(0)`.
> - **Modern advice:** prefer `queueMicrotask` to `nextTick`; prefer `setImmediate` to `setTimeout(0)`.

---

**Related:** [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md) · [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [predict-mixed-async-output.md](./predict-mixed-async-output.md) · [nexttick-starvation.md](./nexttick-starvation.md) · [setimmediate-vs-settimeout-in-io.md](./setimmediate-vs-settimeout-in-io.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
