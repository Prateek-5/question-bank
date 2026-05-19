# `queueMicrotask` — when and why over `Promise.resolve().then`

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [microtask-macrotask-order.md](./microtask-macrotask-order.md)
>
> **Source:** WHATWG HTML spec, MDN, Node.js docs. React/Vue/MobX schedulers use it.

---

## 1. Problem statement

When should you reach for `queueMicrotask(fn)` instead of `Promise.resolve().then(fn)`? Both schedule on the same microtask queue, but they differ in three ways.

**Verification examples**

| Case                                              | `queueMicrotask`                       | `Promise.resolve().then`                |
|---------------------------------------------------|----------------------------------------|-----------------------------------------|
| Allocation cost                                   | one microtask record                   | Promise + reactions + microtask + closure |
| Exception path                                    | `uncaughtException` (process-level)    | `unhandledRejection` (swallowed)         |
| Return value                                      | `undefined`                            | a Promise (chainable, awaitable)         |
| Scheduling priority                               | microtask                               | microtask (same)                         |
| Order between them                                 | FIFO (registration order)              | FIFO                                     |

**Constraints**
- Same scheduling tier — both microtasks.
- `queueMicrotask` is cheaper (less GC pressure).
- Exception semantics differ — pick the right one.
- Microtasks queued during a flush drain in the SAME flush.

---

## 2. Plain-English restatement

Both schedule a callback to run before the next macrotask. `queueMicrotask` is the lower-level primitive — no Promise allocation, exceptions bubble up like sync code. `Promise.resolve().then` is what you reach for when you actually want a Promise to chain or await. Default to `queueMicrotask` for fire-and-forget; use the Promise version when you need a Promise.

---

## 3. Why this matters in interviews

Mid-level says "they're the same." Senior knows the three differences (allocation, exception, intent). React/Vue schedulers use `queueMicrotask` for batched flushes — fewer allocations in hot paths.

---

## 4. Mental model

```
   queueMicrotask(fn):              Promise.resolve().then(fn):
   ┌─────────────────────────┐      ┌─────────────────────────────┐
   │ 1 microtask record       │     │ Promise object               │
   │                          │     │ + reactions array            │
   │                          │     │ + microtask record           │
   │                          │     │ + continuation closure       │
   └─────────────────────────┘      └─────────────────────────────┘
            │                                  │
            ▼                                  ▼
   Schedules cb on microtask queue.   Schedules cb on microtask queue.

   On exception:
   queueMicrotask:           Promise.resolve().then:
   throw → uncaughtException  throw → unhandledRejection
   (process supervisor       (Node 16+ exits, but
    sees process-level fail) older versions don't)

   Default rule: if you don't use the returned Promise → use queueMicrotask.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `queueMicrotask(() => { throw new Error() })` do? `Promise.resolve().then(() => { throw new Error() })`?
> 2. Are `queueMicrotask` and `Promise.resolve().then` the same FIFO?
> 3. Why is `queueMicrotask` cheaper for a scheduler firing 10k times/sec?

---

## 6. Brute force — walked through

### Wrong attempt 1: "they're identical"
Miss the exception semantics, miss the GC cost.

### Wrong attempt 2: "use Promise.resolve().then everywhere"
Allocates Promise per call; in hot paths, GC pressure hurts.

### Wrong attempt 3: "queueMicrotask is for browsers only"
No — Node has it too (Node 11+). Cross-platform.

---

## 7. The unlocking insight

> **Same priority tier; different cost + exception semantics + intent. `queueMicrotask`: 1 allocation, exception → uncaughtException, no return value. `Promise.resolve().then`: Promise allocation, exception → unhandledRejection, returns Promise. Rule: if you don't use the returned Promise, use `queueMicrotask`.**

Three properties:

1. **Allocation cost** — `queueMicrotask` is lighter.
2. **Exception path** — `uncaughtException` vs `unhandledRejection`.
3. **Intent** — `queueMicrotask` says "defer this," not "compute a value."

---

## 8. Solution (annotated)

```js
// React-style batcher using queueMicrotask
function createBatcher(flushFn) {
  let scheduled = false;
  const queue = [];

  return function enqueue(item) {
    queue.push(item);
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(() => {                                            // step 1: cheap defer
      scheduled = false;
      const batch = queue.splice(0);
      flushFn(batch);                                                  // step 2: if this throws → uncaughtException
    });
  };
}

const batcher = createBatcher((items) => console.log('flush', items));

batcher('a'); batcher('b'); batcher('c');
// After current sync work: 'flush ["a","b","c"]'  — one microtask, three items batched.

// Exception semantics
queueMicrotask(() => { throw new Error('a'); });          // → uncaughtException
Promise.resolve().then(() => { throw new Error('b'); });  // → unhandledRejection
```

**Try it yourself**

```js
// Microtasks queued during a microtask drain SAME flush
console.log('1');
queueMicrotask(() => {
  console.log('2');
  queueMicrotask(() => console.log('3'));        // joins same flush
  Promise.resolve().then(() => console.log('4')); // also same flush, after 3
});
queueMicrotask(() => console.log('5'));
console.log('6');

// Output: 1, 6, 2, 5, 3, 4
//
// 1, 6     — sync.
// 2, 5     — initial microtasks in registration order.
// 3, 4     — microtasks queued from inside 2; drain after 5.
```

---

## 9. Step-by-step dry run

```
Trace the "queued during flush" example:

Sync:
  log '1'                                     output: 1
  queueMicrotask(mt_A)                         MQ=[mt_A]
  queueMicrotask(mt_B)                         MQ=[mt_A, mt_B]
  log '6'                                       output: 1, 6

Drain MQ:
  pop mt_A → log '2'
    inside mt_A:
      queueMicrotask(mt_C)                    MQ=[mt_B, mt_C]
      Promise.resolve().then(mt_D)            MQ=[mt_B, mt_C, mt_D]
  pop mt_B → log '5'
  pop mt_C → log '3'
  pop mt_D → log '4'
  MQ=[].

Output: 1, 6, 2, 5, 3, 4.

Microtasks queued during the same flush drain in the SAME flush.
```

---

## 10. Common confusion + traps

1. **"Identical to `.then`"** — different exception path, different allocation cost.
2. **Use in hot loops** — GC pressure if you reach for Promise version.
3. **Expect "next macrotask"** — no, fires BEFORE next macrotask at next microtask checkpoint.
4. **Infinite microtask recursion** — `queueMicrotask` can starve I/O like `nextTick`.
5. **`MessageChannel` is a microtask** — no, MACROTASK; used to yield.
6. **Polyfill via `.then`** — works but exception semantics don't match.
7. **`nextTick` outranks `queueMicrotask`** — yes (Node).

---

## 11. Senior follow-ups & variants

### Variant 1 — Polyfill `queueMicrotask`
`const queueMicrotask = (fn) => Promise.resolve().then(fn).catch(/* re-throw */)`. Exception path can't be fully matched.

### Variant 2 — `MessageChannel` for cross-realm task scheduling
Macrotask, not microtask. Used by React Scheduler for time-slicing.

### Variant 3 — `process.nextTick` vs microtask
nextTick outranks microtask in Node. Use nextTick for "before any I/O." Otherwise microtask.

### Variant 4 — Node 11 microtask behavior change
Pre-11, microtasks drained between phases only; post-11, after every individual callback within a phase (aligns with browser).

### Variant 5 — Hot-path benchmark
React Scheduler benchmarks: `queueMicrotask` < `Promise.then` < `setTimeout(0)`.

---

## 12. How to think aloud

> "Same scheduling tier (microtask queue, FIFO). Three differences: (1) allocation — `queueMicrotask` is one record vs Promise + reactions + closure; matters in hot paths; (2) exceptions — `queueMicrotask` throw → `uncaughtException` (sync-like); `Promise.then` throw → `unhandledRejection` (swallowed/wrapped); (3) intent — `queueMicrotask` says 'defer'; Promise.then says 'compute a value.' Rule: if you don't use the returned Promise, use `queueMicrotask`. React/Vue/MobX schedulers prefer it. Trap: 'identical' is wrong on exception path; using Promise version in hot loops creates GC pressure."

---

## 13. 60-second revision

> - **Same scheduling tier** (microtask queue, FIFO).
> - **`queueMicrotask`:** 1 allocation; throw → `uncaughtException`; no return.
> - **`Promise.resolve().then`:** Promise + reactions allocated; throw → `unhandledRejection`; returns Promise.
> - **Rule:** if you don't use the returned Promise → `queueMicrotask`.
> - **React/Vue/MobX schedulers** use it for batched flushes.
> - **Microtasks queued during a flush** drain in SAME flush (can starve I/O).
> - **Trap:** "identical" (no — exception path differs); using Promise version in hot loops.

---

**Related:** [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [microtask-starvation-recipes.md](./microtask-starvation-recipes.md) · [messagechannel-microtask.md](./messagechannel-microtask.md) · [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md)
