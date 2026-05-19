# Microtask drainer — flush all queued microtasks before continuing

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md), [build-promise-from-scratch.md](./build-promise-from-scratch.md)
>
> **Source:** `queueMicrotask`, `Promise.resolve().then`; the V8 microtask queue. Output-prediction puzzles at Razorpay, Stripe, Atlassian.

---

## 1. Problem statement

**Signature**
```ts
function drainMicrotasks(): Promise<void>;
```

**Input / Output examples**

| Setup                                                  | Output order              |
|--------------------------------------------------------|---------------------------|
| `console.log(1); setTimeout(log(4)); Promise.resolve().then(log(2)); queueMicrotask(log(3)); log(1.5);` | `1, 1.5, 2, 3, 4` |
| `await drainMicrotasks();`                             | all queued microtasks done before next line |
| Chained `.then(() => Promise.resolve())`              | adds extra microtask hop |
| `while (true) await Promise.resolve()`                 | microtask starvation — timers never fire |

**Constraints**
- Microtask queue drains **to completion** between every macrotask.
- `process.nextTick` (Node) drains **before** microtasks.
- "Drain microtasks" isn't a real API — simulate via macrotask boundary.
- Don't starve macrotasks with infinite microtask chains.

---

## 2. Plain-English restatement

Two queues run the event loop: macrotasks (timers, I/O, `setImmediate`) and microtasks (`.then` callbacks, `queueMicrotask`). After each macrotask, ALL microtasks drain to empty before the next macrotask starts. To "wait until all currently-queued microtasks are done" you schedule a macrotask (via `setImmediate` or `setTimeout(0)`) and await it — by the time it runs, the microtask queue is empty.

---

## 3. Why this matters in interviews

"Predict the output" or "schedule N tasks but flush all microtasks before any macrotask" is a recurring puzzle. The microtask queue drains *to completion* between every macrotask and after every top-level script. Senior bar: you can explain why `setTimeout(0)` runs *after* a chained `.then`, why excessive microtasks cause UI freeze (microtask starvation), and how to implement a "wait for everything queued right now" primitive.

---

## 4. Mental model

Two queues per event-loop turn:

```
   ┌─────────────────────────────────────────────────────┐
   │ macrotask queue (timers, I/O, setImmediate)         │
   │   [t1, t2, t3, ...]                                 │
   └─────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────┐
   │ microtask queue (Promise callbacks, queueMicrotask) │
   │   [m1, m2, m3, ...]                                 │
   └─────────────────────────────────────────────────────┘

   loop():
     run next macrotask t_i  (run script if top-level)
     DRAIN microtask queue to EMPTY (m's can enqueue m's)
     repeat
```

Microtasks drain after each macrotask. So `setTimeout(fn, 0)` runs AFTER chained `.then`s.

**Drain primitive:** schedule a macrotask, await it. By the time it runs, microtasks have all drained.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's the output of `setTimeout(() => log(4), 0); Promise.resolve().then(() => log(2)); queueMicrotask(() => log(3)); log(1);`?
> 2. Why does `await Promise.resolve()` in an infinite loop starve `setTimeout` callbacks?
> 3. Does `Promise.resolve(promise)` add a microtask hop, or short-circuit?

---

## 6. Brute force — walked through

### Wrong attempt 1: repeated `setTimeout`
```js
for (let i = 0; i < 10; i++) await new Promise(r => setTimeout(r, 0));
```
Fragile — depends on how many macrotasks the runtime has queued.

### Wrong attempt 2: just `await Promise.resolve()`
Adds one microtask hop — doesn't drain chained `.then`s.

### Wrong attempt 3: busy-loop on `queueMicrotask`
```js
while (microQ.length > 0) await new Promise(queueMicrotask);
```
No public API for queue length; microtasks can enqueue more microtasks → never empties.

---

## 7. The unlocking insight

> **Schedule a macrotask and await it. By the time the macrotask callback runs, the microtask queue has already drained to empty.**

The primitive:

```js
function drainMicrotasks() {
  return new Promise((resolve) => {
    if (typeof setImmediate === 'function') setImmediate(resolve);  // Node
    else setTimeout(resolve, 0);                                     // browser
  });
}
```

Because `setImmediate` / `setTimeout(0)` are macrotasks, the runtime fully drains the microtask queue **before** running them. So `await drainMicrotasks()` resumes only after all queued microtasks have finished.

**Microtask starvation:** an infinite chain of `.then`s blocks the macrotask queue indefinitely. Timers and I/O callbacks never fire while the chain runs. This is a real production outage cause.

---

## 8. Solution (annotated)

```js
function drainMicrotasks() {
  return new Promise((resolve) => {
    if (typeof setImmediate === 'function') setImmediate(resolve);   // Node: setImmediate is macrotask
    else setTimeout(resolve, 0);                                       // browser fallback
  });
}

// Example usage
let log = [];
log.push('A');
Promise.resolve().then(() => log.push('B'));
queueMicrotask(() => log.push('C'));
await drainMicrotasks();
// log === ['A', 'B', 'C']  ← all microtasks drained

// Counter-example: microtask starvation
async function starve() {
  while (true) await Promise.resolve();   // blocks macrotasks forever
}
// timers, I/O never fire while this runs
```

**Try it yourself**

```js
console.log('s1');
setTimeout(() => console.log('t1'), 0);
Promise.resolve()
  .then(() => { console.log('m1'); return Promise.resolve(); })
  .then(() => console.log('m2'));
queueMicrotask(() => console.log('m3'));
console.log('s2');

// Output: s1, s2, m1, m3, m2, t1
```

Note the `m1 → m3 → m2` order — chained `.then(() => Promise.resolve())` adds an extra microtask hop.

---

## 9. Step-by-step dry run

```js
console.log('s1');
setTimeout(() => console.log('t1'), 0);
Promise.resolve().then(() => { console.log('m1'); return Promise.resolve(); }).then(() => console.log('m2'));
queueMicrotask(() => console.log('m3'));
console.log('s2');
```

| Phase | Action | Output | macroQ | microQ |
|-------|--------|--------|--------|--------|
| sync | log s1, schedule t1, register m1-handler, schedule m3, log s2 | `s1, s2` | `[t1]` | `[m1, m3]` |
| µ-drain | run m1 → log, return Promise.resolve() → schedules m2-handler | `m1` | `[t1]` | `[m3, m2]` |
| µ-drain | run m3 → log | `m3` | `[t1]` | `[m2]` |
| µ-drain | run m2 → log | `m2` | `[t1]` | `[]` |
| next macro | run t1 → log | `t1` | `[]` | `[]` |

Final: `s1, s2, m1, m3, m2, t1`.

---

## 10. Common confusion + traps

1. **"setTimeout(0) runs immediately"** — no, after current macrotask + microtask drain.
2. **"Microtasks alternate with macrotasks"** — no, ALL microtasks drain before ANY macrotask.
3. **"`process.nextTick` is faster"** — same speed; different queue (drains BEFORE microtasks).
4. **"`await` is sleep"** — it's a microtask suspension.
5. **"async returns sync without await"** — still wraps in Promise; subsequent `.then` is one microtask away.
6. **Chained `.then(() => Promise.resolve())`** adds an extra microtask hop.
7. **Microtask starvation** — infinite `await Promise.resolve()` blocks timers/I/O.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async drain helper
`while (microtaskCount > 0) await microtask` — no public API; simulated via macrotask boundary.

### Variant 2 — Test utilities
RTL, jest expose `flushPromises()` = `await new Promise(r => setTimeout(r))`.

### Variant 3 — `queueMicrotask` vs `.then`
Identical scheduling priority; `queueMicrotask` allocates no Promise.

### Variant 4 — `process.nextTick` recursion
Node's "starvation" gotcha — recursive `nextTick` blocks even microtasks. Use `setImmediate` to break the loop.

---

## 12. How to think aloud

> "Two queues. Microtask queue drains to completion between macrotasks. queueMicrotask and Promise.then enqueue microtasks; setTimeout enqueues macrotasks. process.nextTick (Node) is even higher priority — drains before microtasks. To 'drain microtasks' I schedule a macrotask (setImmediate or setTimeout(0)) and await it; by the time it runs, microtask queue is empty. Watch for chained promises that add extra microtask hops — that's the m1 m3 m2 trap. Beware microtask starvation: infinite `await Promise.resolve()` blocks timers and I/O."

---

## 13. 60-second revision

> - **Microtasks drain to completion** between macrotasks.
> - **Priority (Node):** `process.nextTick` > microtask (`.then`, `queueMicrotask`) > macrotask (timers, I/O).
> - **Drain primitive:** `await new Promise(r => setImmediate(r))` (Node) or `setTimeout(r, 0)` (browser).
> - **`Promise.resolve(p)`** short-circuits but `.then(() => Promise.resolve())` adds a hop.
> - **Microtask starvation** = real outage cause.
> - **Family:** `flushPromises` test utility; React batched updates.
> - **Trap:** `setTimeout(0)` runs after chained `.then`s; infinite microtask chain starves I/O.

---

**Related:** [build-promise-from-scratch.md](./build-promise-from-scratch.md) · [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md) · [`05-event-loop/microtask-starvation-recipes.md`](../05-event-loop/microtask-starvation-recipes.md) · [`05-event-loop/queuemicrotask-deep-dive.md`](../05-event-loop/queuemicrotask-deep-dive.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md)
