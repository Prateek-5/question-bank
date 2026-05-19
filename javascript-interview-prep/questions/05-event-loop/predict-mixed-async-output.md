# Predict mixed async output — the canonical puzzle

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [microtask-macrotask-order.md](./microtask-macrotask-order.md), [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md)
>
> **Source:** The single most-asked senior JS interview puzzle. Zomato, Razorpay, Atlassian, Uber.

---

## 1. Problem statement

10-line snippet mixing `setTimeout`, `setImmediate`, `Promise.then`, `queueMicrotask`, `await`, and `process.nextTick`. Predict exact log order on Node.

**Verification example**

```js
console.log('A');
setTimeout(() => {
  console.log('B');
  Promise.resolve().then(() => console.log('C'));
  process.nextTick(() => console.log('D'));
}, 0);
setImmediate(() => {
  console.log('E');
  process.nextTick(() => console.log('F'));
});
Promise.resolve().then(() => console.log('G'));
queueMicrotask(() => console.log('H'));
process.nextTick(() => console.log('I'));
(async () => {
  console.log('J');
  await null;
  console.log('K');
})();
console.log('L');

// Output: A, J, L, I, G, H, K, B, D, C, E, F
// (B vs E from main module is racy; this assumes setTimeout-first common case)
```

**Constraints**
- 5-tier priority: sync > nextTick > microtask > setImmediate (check) > setTimeout (timers).
- Between every callback in every phase: drain nextTick → drain microtask.
- `await x` enqueues a microtask continuation even for non-Promise `x`.
- From main module: `setImmediate` vs `setTimeout(0)` is non-deterministic; from inside an I/O callback: deterministic (`setImmediate` wins).

---

## 2. Plain-English restatement

The interviewer dumps a snippet. Walk the queues out loud. Maintain four columns: **nextTick**, **microtask**, **timer**, **check**. Print sync logs as you go. After sync: drain nextTick → drain microtask → process one macrotask → re-drain. Repeat until all queues empty.

---

## 3. Why this matters in interviews

The single gotcha that separates senior backend from mid-level. Tests deep mastery of the runtime — walking queues correctly is mechanical once you know the rules. Guessing = no-hire.

---

## 4. Mental model

```
   5 priority tiers in Node:
   1. Synchronous code (call stack)
   2. process.nextTick queue           ← drain between every callback
   3. Microtask queue                   ← drain between every callback
   4. setImmediate (libuv check phase)  ← once per iteration
   5. setTimeout(fn, 0) (libuv timers)  ← once per iteration, top of loop

   libuv phases in order:
     timers → pending → idle/prepare → poll → check → close → repeat

   Special rule: from inside an I/O callback, setImmediate runs BEFORE
                 setTimeout(0) deterministically (poll→check is fixed order).

   await x equivalent:
     await null    →  Promise.resolve(null).then(v => /* rest */);
   The "rest" of the async function runs as a MICROTASK.

   The 4-column technique:
   nextTick │ microtask │ timer │ check
   ────────┼───────────┼───────┼──────
            │           │       │
   Walk the code; push each async API to its column.
   After sync: drain nextTick → drain microtask → pick from timer (or check)
   → drain again → repeat.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Without running, predict the canonical snippet's output. Then verify by walking columns.
> 2. Why is `I` before `G` (both deferred)?
> 3. Inside the setTimeout callback, why does `D` come before `C` even though `D` was scheduled AFTER `C`?

---

## 6. Brute force — walked through

### Wrong attempt 1: "just run it"
Loses interview points — they want the prediction.

### Wrong attempt 2: read top to bottom
Wrong for any async.

### Wrong attempt 3: predict by intuition
Get nextTick vs microtask priority wrong, or `setImmediate` vs `setTimeout(0)` wrong.

---

## 7. The unlocking insight

> **Four columns method: maintain `nextTick`, `microtask`, `timer`, `check` as separate FIFO queues. Walk code top-down. After sync: drain NT → drain MQ → pick one macrotask → re-drain NT+MQ → next macrotask. Inside a macrotask callback, scheduled NT/MQ items drain BEFORE the next macrotask.**

Three properties:

1. **Four columns** — mechanical, not creative.
2. **NT + MQ drain between every callback** (not just at end of sync).
3. **I/O-callback determinism** — `setImmediate` beats `setTimeout(0)` inside I/O.

---

## 8. Solution (annotated)

```js
console.log('A');                                                    // sync → A

setTimeout(() => {                                                    // T1
  console.log('B');
  Promise.resolve().then(() => console.log('C'));
  process.nextTick(() => console.log('D'));
}, 0);

setImmediate(() => {                                                   // I1
  console.log('E');
  process.nextTick(() => console.log('F'));
});

Promise.resolve().then(() => console.log('G'));                        // microtask MG
queueMicrotask(() => console.log('H'));                                 // microtask MH
process.nextTick(() => console.log('I'));                               // nextTick NI

(async () => {
  console.log('J');                                                     // sync (inside IIFE) → J
  await null;                                                            // suspend; cont = MK
  console.log('K');
})();

console.log('L');                                                       // sync → L

// Output (Node, main module):
// A, J, L          ← sync
// I                ← nextTick drains first
// G, H, K          ← microtask FIFO
// B                ← timers phase fires T1
//   D              ← nextTick scheduled inside T1, drains before next callback
//   C              ← microtask scheduled inside T1
// E                ← check phase fires I1
//   F              ← nextTick scheduled inside I1
```

**Try it yourself**

```js
// Inside I/O callback — deterministic ordering
fs.readFile(__filename, () => {
  setTimeout(() => console.log('inner T'), 0);
  setImmediate(() => console.log('inner I'));
  process.nextTick(() => console.log('inner N'));
  Promise.resolve().then(() => console.log('inner M'));
});

// Output: inner N, inner M, inner I, inner T
// (check follows poll within same iteration; timers waits for next iteration)
```

---

## 9. Step-by-step dry run

```
Walk canonical snippet:

Sync:
  log 'A'                                output: A
  schedule T1                            timer=[T1]
  schedule I1                            check=[I1]
  schedule MG                            MQ=[MG]
  schedule MH                            MQ=[MG, MH]
  schedule NI                            NT=[NI]
  IIFE: log 'J'                          output: A, J
        await null → MK                  MQ=[MG, MH, MK]
  log 'L'                                output: A, J, L

Sync done. Drain NT:
  pop NI → log 'I'                       output: A, J, L, I. NT=[].

Drain MQ:
  pop MG → log 'G'                       output: ..., G
  pop MH → log 'H'                       output: ..., H
  pop MK → log 'K'                       output: ..., K. MQ=[].

Timers phase: run T1:
  log 'B'                                output: ..., B
  inside T1:
    schedule promise.then(cb_C)          MQ=[cb_C]
    schedule nextTick(cb_D)              NT=[cb_D]
  T1 returns; drain NT (cb_D → log 'D'), then MQ (cb_C → log 'C').
  output: ..., B, D, C.

Check phase: run I1:
  log 'E'                                output: ..., E
  schedule nextTick(cb_F)                NT=[cb_F]
  I1 returns; drain NT (cb_F → log 'F').
  output: ..., E, F.

Final: A, J, L, I, G, H, K, B, D, C, E, F.

Note: B vs E from main is racy; from inside an I/O cb it's deterministic.
```

---

## 10. Common confusion + traps

1. **nextTick is microtask** — separate higher-priority queue.
2. **`await null` no-op** — still enqueues microtask continuation.
3. **`setImmediate` vs `setTimeout(0)` from main is deterministic** — non-deterministic.
4. **Chained `.then`s all enqueued at once** — each waits.
5. **Microtasks queued mid-macrotask wait until end of macrotask** — no, drain right after the current callback.
6. **NT scheduled inside a microtask drains in next phase** — no, drains immediately after current callback.
7. **`Promise.resolve(thenable)`** can add extra microtask hops vs `Promise.resolve(value)`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Add `fs.readFile` callback
Now you have a real I/O step. Inside it, `setImmediate` deterministically beats `setTimeout(0)`.

### Variant 2 — Reorder to make X log first
Swap two lines; explain what changes.

### Variant 3 — Remove the `await null`
Now async IIFE runs entirely sync; `K` logs immediately after `J`, before `L`.

### Variant 4 — Replace `Promise.resolve().then` with `new Promise(res => res()).then`
Same scheduling; tests that you know `new Promise(exec)` runs `exec` synchronously.

### Variant 5 — Browser vs Node differences
Browser has no `process.nextTick`, no `setImmediate`. `MutationObserver` is microtask.

---

## 12. How to think aloud

> "Four columns: nextTick, microtask, timer, check. Walk top-down. Print sync logs (A, J, L). After sync: drain nextTick (I), then drain microtask (G, H, K — K is the await continuation). Next iteration: timers phase fires T1 → log B → inside T1 schedule new NT and MT entries → T1 returns → drain NT first (D), then MQ (C). Check phase fires I1 → log E → schedule NT (F) → drain (F). Output: A, J, L, I, G, H, K, B, D, C, E, F. Trap: nextTick is NOT a microtask; await even on null suspends; setImmediate vs setTimeout(0) from main is RACY."

---

## 13. 60-second revision

> - **5 tiers:** sync > nextTick > microtask > setImmediate (check) > setTimeout(0) (timers).
> - **Drain NT + MQ between every callback.**
> - **`await x`** enqueues microtask continuation even for non-Promise.
> - **Inside I/O cb:** `setImmediate` > `setTimeout(0)` deterministic.
> - **From main:** `setImmediate` vs `setTimeout(0)` racy.
> - **Four-column walk** to predict mechanically.
> - **Trap:** nextTick as microtask; await null as no-op; chained then co-enqueue; main-module determinism assumption.

---

**Related:** [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) · [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md) · [event-loop-concurrency.md](./event-loop-concurrency.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
