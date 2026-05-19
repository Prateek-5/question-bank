# 05 — Event Loop

The hierarchy that decides what runs when. Output prediction, starvation diagnosis, worker offload, cooperative scheduling. Files follow the v2 13-section template.

---

## How to study this folder

1. **Foundation:** event-loop-concurrency, microtask-macrotask-order, nodejs-event-loop-phases.
2. **Output prediction:** predict-mixed-async-output, nexttick-vs-setimmediate, setimmediate-vs-settimeout-in-io, queuemicrotask-deep-dive.
3. **Starvation:** nexttick-starvation, microtask-starvation-recipes.
4. **Cancellation:** timeout-cancellation, interval-cancellation, cancellable-function.
5. **Scheduling primitives:** messagechannel-microtask, requestidlecallback-scheduling.
6. **Cross-thread:** worker-threads-vs-event-loop, worker-pool-implementation, postmessage-roundtrip, structured-clone-cost, atomics-wait-notify-intuition, broadcastchannel-fanout.
7. **Modules + context:** top-level-await-modules, async-hooks-basics.

---

## Files (22)

### Foundation
- [event-loop-concurrency.md](./event-loop-concurrency.md) — Four-layer model: stack → nextTick → microtask → phase.
- [microtask-macrotask-order.md](./microtask-macrotask-order.md) — The rule: microtasks drain to empty between macrotasks.
- [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md) — Six libuv phases in order.

### Output prediction
- [predict-mixed-async-output.md](./predict-mixed-async-output.md) — Walk four columns: nextTick / MQ / timer / check.
- [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) — Three deferred APIs, three queues.
- [setimmediate-vs-settimeout-in-io.md](./setimmediate-vs-settimeout-in-io.md) — Deterministic only inside I/O cb.
- [queuemicrotask-deep-dive.md](./queuemicrotask-deep-dive.md) — When over `Promise.then`; exception semantics differ.

### Starvation
- [nexttick-starvation.md](./nexttick-starvation.md) — Recursive nextTick silently hangs the loop.
- [microtask-starvation-recipes.md](./microtask-starvation-recipes.md) — Cure: yield via `setImmediate` periodically.

### Cancellation
- [timeout-cancellation.md](./timeout-cancellation.md) — `setTimeout` + `clearTimeout`; closure-returned canceller.
- [interval-cancellation.md](./interval-cancellation.md) — Immediate-first-tick; drift-aware variant.
- [cancellable-function.md](./cancellable-function.md) — Generator + runner; cooperative cancel via `.throw`.

### Scheduling primitives
- [messagechannel-microtask.md](./messagechannel-microtask.md) — Fast macrotask yield; no 4ms clamp.
- [requestidlecallback-scheduling.md](./requestidlecallback-scheduling.md) — Browser idle-slice scheduler; React Fiber's original.

### Cross-thread
- [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) — Workers for CPU, not I/O.
- [worker-pool-implementation.md](./worker-pool-implementation.md) — Warm pool + taskId correlation + crash recovery.
- [postmessage-roundtrip.md](./postmessage-roundtrip.md) — RPC over one-way messaging via correlation ID.
- [structured-clone-cost.md](./structured-clone-cost.md) — O(n) sync on sender; transferables + SAB.
- [atomics-wait-notify-intuition.md](./atomics-wait-notify-intuition.md) — Block on shared memory; building block for mutex.
- [broadcastchannel-fanout.md](./broadcastchannel-fanout.md) — Same-origin pub/sub across tabs/workers.

### Modules + context
- [top-level-await-modules.md](./top-level-await-modules.md) — ESM only; siblings parallelize; cyclic deadlock.
- [async-hooks-basics.md](./async-hooks-basics.md) — `AsyncLocalStorage` for request-scoped context.

---

## Concept primers

- [`concepts/event-loop.md`](../../concepts/event-loop.md) — Loop mechanics.
- [`concepts/promises.md`](../../concepts/promises.md) — Microtask scheduling.

---

## Companion sections

- `04-promises/` — Promise polyfills, microtask drainer, top-level await.
- `10-machine-coding-patterns/` — debounce, throttle, scheduler-idle-callback, cancellable-promise-wrapper.
