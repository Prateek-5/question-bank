# Node.js Event Loop Phases (libuv internals)

## Source
- codedamn: https://codedamn.com/news/nodejs/event-loop-role
- Node official docs: https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick

## Why this question matters in interviews
Senior backend roles drill on this directly. The interviewer wants to hear the **six libuv phases by name in order**, what kind of callback each one runs, and where `process.nextTick` and the microtask queue fit *in between* (they're not phases). If you can also explain WHY `setImmediate` beats `setTimeout(0)` inside an I/O callback but is non-deterministic from main, you've signaled deep Node literacy. This shows up in every staff-level system-design discussion when latency budgets and "what blocks the loop" come up.

## Concepts involved

### The 6 libuv phases (in order, each iteration)
```
   ┌───────────────────────────┐
   │   1. timers                │  setTimeout / setInterval callbacks whose
   │                            │  deadline has passed
   ├───────────────────────────┤
   │   2. pending callbacks     │  deferred system-level errors (TCP errors,
   │                            │  some ECONNREFUSED retries)
   ├───────────────────────────┤
   │   3. idle, prepare         │  libuv internal — almost never user-visible
   ├───────────────────────────┤
   │   4. poll                  │  retrieve new I/O events; execute I/O
   │                            │  callbacks; block here when nothing else
   │                            │  is pending (waiting for new events)
   ├───────────────────────────┤
   │   5. check                 │  setImmediate callbacks
   ├───────────────────────────┤
   │   6. close callbacks       │  socket.on('close'), etc.
   └───────────────────────────┘
            │
            ▼  (loop back to phase 1)
```

**Between every single callback in every phase**, Node runs:
- `process.nextTick` queue → drain to empty
- microtask queue (Promise jobs, `queueMicrotask`) → drain to empty

These two queues are **NOT phases**. They're interleaved.

### What each phase actually contains
1. **timers** — only timers whose `target time <= now` are run. The phase runs at most up to a per-iteration limit, then exits. Order is by deadline, ties broken by registration order.
2. **pending callbacks** — rare. libuv uses this for operations that couldn't be queued in `poll` (e.g., a TCP socket reporting `ECONNREFUSED` from a previous tick).
3. **idle, prepare** — internal. You'll never put code here directly.
4. **poll** — **the most important phase**. It:
   - Computes how long to block waiting for new I/O (the "poll timeout").
   - Calls into the kernel (epoll / kqueue / IOCP) to grab ready events.
   - Runs the I/O callbacks until either the queue is empty or a hard limit is reached.
   - If nothing else is pending (no timers due, no immediates, no closes), it BLOCKS here waiting for new events.
5. **check** — runs all queued `setImmediate` callbacks. This phase exists precisely so you can schedule "run me right after I/O" work.
6. **close callbacks** — emits `'close'` events for destroyed handles (sockets, streams).

### Edge cases (interview traps)
1. **`setImmediate` vs `setTimeout(0)` from main module** — non-deterministic. The loop may start in timers (firing the 0ms timer first) or arrive at timers after their deadline hasn't quite hit (firing setImmediate first via check).
2. **`setImmediate` vs `setTimeout(0)` inside an I/O callback** — deterministic. After poll, the loop *always* goes to check before looping back to timers. So `setImmediate` runs first.
3. **Microtasks drain between every callback** — not just at phase boundaries. So `setTimeout(fn1)` and `setTimeout(fn2)` both due in the same timers phase: `fn1` runs, microtasks/nextTicks drain, THEN `fn2` runs.
4. **`process.nextTick` runs before microtasks** — even before `Promise.resolve().then`.
5. **Recursive `process.nextTick` starves I/O** — because nextTick drains to empty before the next phase, an infinite recursive nextTick prevents the loop from ever entering the poll phase. Same risk with microtasks but less severe.
6. **Long sync code in any callback blocks the loop**. Always.
7. **`UV_THREADPOOL_SIZE`** — defaults to 4. fs/dns/crypto use this pool. Tune for CPU-heavy crypto workloads.
8. **`process.exit()` vs natural exit** — natural exit happens when the loop has zero pending handles. `unref`'d timers and sockets don't count.

## Brute force approach
"Node has an event loop." Too vague. You must name phases, explain poll's special role (it's the only phase that blocks), and place nextTick + microtasks in the interleaving model.

## Optimal approach
Memorize the six phase names in order. Memorize what each runs. Memorize that nextTick + microtasks drain between every callback. Be able to draw the diagram from scratch in 30 seconds.

## Solution (JavaScript)

```js
// Demonstration: each phase in action.
const fs = require('node:fs');

// Phase 1: timers
setTimeout(() => console.log('[timers] setTimeout(0)'), 0);

// Phase 5: check
setImmediate(() => console.log('[check] setImmediate'));

// Between-phase: nextTick + microtasks
process.nextTick(() => console.log('[between] process.nextTick'));
Promise.resolve().then(() => console.log('[between] microtask (promise)'));

// Phase 4: poll — this fs callback lands here
fs.readFile(__filename, () => {
  console.log('[poll] fs.readFile callback');

  // From inside an I/O callback, ordering becomes deterministic.
  setTimeout(() => console.log('  [timers]  inner setTimeout(0)'), 0);
  setImmediate(() => console.log('  [check]   inner setImmediate'));
  process.nextTick(() => console.log('  [between] inner nextTick'));
  Promise.resolve().then(() => console.log('  [between] inner microtask'));
});

console.log('sync end');
```

```js
// Expected output (Node, sync part):
// sync end
// [between] process.nextTick
// [between] microtask (promise)
// [timers] setTimeout(0)            ← order with setImmediate may flip
// [check] setImmediate              ← from main module
// [poll] fs.readFile callback
//   [between] inner nextTick
//   [between] inner microtask
//   [check]   inner setImmediate    ← DETERMINISTIC: check follows poll
//   [timers]  inner setTimeout(0)   ← runs on next loop iteration
```

## Step-by-step dry run

Trace the script line by line. State per tick: `CS = call stack`, `NT = nextTick`, `MQ = microtask`, `Timers / Poll / Check` = libuv phase queues.

| Step | CS action | NT | MQ | Timers | Poll | Check |
|------|-----------|----|----|--------|------|-------|
| 1 | register `setTimeout` cb T | — | — | `[T@0]` | — | — |
| 2 | register `setImmediate` cb I | — | — | `[T@0]` | — | `[I]` |
| 3 | `process.nextTick` enqueue N | `[N]` | — | `[T@0]` | — | `[I]` |
| 4 | `.then` enqueue M | `[N]` | `[M]` | `[T@0]` | — | `[I]` |
| 5 | `fs.readFile` dispatches to libuv thread pool; cb F registered for poll | `[N]` | `[M]` | `[T@0]` | (pending) | `[I]` |
| 6 | `console.log('sync end')` runs | `[N]` | `[M]` | `[T@0]` | (pending) | `[I]` |
| 7 | sync stack empty → drain NT → run N → log `nextTick` | — | `[M]` | `[T@0]` | (pending) | `[I]` |
| 8 | drain MQ → run M → log `microtask` | — | — | `[T@0]` | (pending) | `[I]` |
| 9 | enter timers phase → T's deadline (0ms) has passed → run T → log `setTimeout(0)` | — | — | — | (pending) | `[I]` |
| 10 | drain NT (empty), MQ (empty) | — | — | — | (pending) | `[I]` |
| 11 | pending / idle/prepare phases — no work | — | — | — | (pending) | `[I]` |
| 12 | enter poll phase → fs not done yet → block waiting (or skip if timeout) | — | — | — | (pending) | `[I]` |
| 13 | skip poll (immediates pending) → enter check → run I → log `setImmediate` | — | — | — | (pending) | — |
| 14 | drain NT, MQ | — | — | — | (pending) | — |
| 15 | close phase — nothing | — | — | — | (pending) | — |
| 16 | new iteration → timers (nothing) → poll: fs.readFile completes → run F → log `fs.readFile callback` | — | — | — | — | — |
| 17 | F schedules inner T2, I2, N2, M2 | `[N2]` | `[M2]` | `[T2@0]` | — | `[I2]` |
| 18 | F returns → drain NT → log `inner nextTick` | — | `[M2]` | `[T2@0]` | — | `[I2]` |
| 19 | drain MQ → log `inner microtask` | — | — | `[T2@0]` | — | `[I2]` |
| 20 | poll's queue empty → move to check → run I2 → log `inner setImmediate` | — | — | `[T2@0]` | — | — |
| 21 | next iteration → timers → run T2 → log `inner setTimeout(0)` | — | — | — | — | — |

Note step 20 / 21: inside an I/O callback, **check ALWAYS runs before the next timers phase**, so `setImmediate` beats `setTimeout(0)` deterministically.

## Important takeaways

**Memorize this exact order**
> timers → pending callbacks → idle/prepare → poll → check → close

**Memorize what each runs**
- timers: `setTimeout` / `setInterval`
- poll: I/O callbacks (fs, net) + blocks here
- check: `setImmediate`
- close: `'close'` event handlers

**Memorize the interleave rule**
- After EVERY callback: drain `process.nextTick` to empty, then drain microtasks to empty.

**The two priorities you must know**
1. `process.nextTick` > microtasks > any libuv phase callback.
2. Inside an I/O cb: `setImmediate` > `setTimeout(0)` (deterministic). From main: non-deterministic.

**Common mistakes**
- Listing only 3-4 phases. There are six. Idle/prepare is rarely user-visible but exists.
- Saying microtasks drain only "at the end" — they drain between every single callback.
- Treating `process.nextTick` as a microtask — it's not. It's its own queue with higher priority.
- Forgetting that poll blocks. It's the only phase that does.

## Variants

1. **"Why might `setTimeout(fn, 1)` fire later than 1ms?"** — Because the timer phase only runs when the loop reaches it; if poll is blocked waiting on I/O for 50ms, the timer fires at 50ms+.

2. **"How would you measure event loop lag?"** — schedule a `setImmediate`, record `process.hrtime()`, compare to expected. Or use `perf_hooks.monitorEventLoopDelay()`.

3. **"How does `worker_threads` relate to the event loop?"** — each worker has its own V8 isolate AND its own libuv loop. They communicate via `MessageChannel` (which queues messages onto the receiver's loop).

4. **"What if my fs callback runs CPU-heavy work?"** — it blocks the poll phase. Move it to a worker thread or break into chunks with `setImmediate`.

## Revision notes

> **nodejs-event-loop-phases — 60 second recap**
> - **6 phases:** timers → pending → idle/prepare → poll → check → close.
> - Each phase has its own queue; the loop visits in order, iteration after iteration.
> - **Between every callback:** drain `process.nextTick`, then drain microtasks.
> - **poll** is the only blocking phase; it waits for new I/O events.
> - **timers** = `setTimeout/setInterval`. **check** = `setImmediate`. **close** = `'close'` events.
> - From an I/O callback: `setImmediate` > `setTimeout(0)` (deterministic). From main: non-deterministic.
> - libuv's thread pool (default size 4, `UV_THREADPOOL_SIZE`) backs fs/dns/crypto.
> - **Trap:** recursive `process.nextTick` starves the entire loop (including I/O).
> - **Trap:** long sync work in any callback blocks every phase.
