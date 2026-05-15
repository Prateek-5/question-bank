# Predict output: mixed `setTimeout` / `Promise` / `process.nextTick` / `queueMicrotask` / `setImmediate` / `await`

## Source
- The single most-asked senior-level JavaScript interview puzzle — appears verbatim on greatfrontend, codedamn, BFE.dev, and most Node-heavy interviews (Zomato, Razorpay, Atlassian, Uber).
- Node.js docs: https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick
- v8.dev microtask explainer: https://v8.dev/features/top-level-await

## Why this question matters in interviews
This is the **single gotcha** that separates a senior backend engineer from a mid-level one. Anyone who has shipped a Node service will eventually debug a "why is this firing in the wrong order" bug — usually a `process.nextTick` storming I/O, or an `await` running before a `setImmediate`. The interviewer hands you 10 lines of mixed async APIs and asks "what does this log?" If you can walk the queues out loud, you've demonstrated mastery of the runtime. If you guess, you've failed. There is no middle ground.

## Concepts involved

### The five tiers of "later" in Node
In priority order (highest fires first):
1. **Synchronous code** — runs to completion in the current call stack.
2. **`process.nextTick` queue** — drained completely between every operation, before microtasks.
3. **Microtask queue** — `Promise.resolve().then()`, `queueMicrotask()`, `await` continuations, `MutationObserver` (browser). Drained completely between every step of the libuv loop.
4. **`setImmediate`** — runs in the `check` phase of libuv.
5. **`setTimeout(fn, 0)`** — runs in the `timers` phase of libuv (which is *before* `check` on most ticks, but ordering vs. `setImmediate` is **non-deterministic from the main module**).

### The libuv loop has six phases (in order, per tick)
`timers` → `pending callbacks` → `idle/prepare` → `poll` → `check` → `close callbacks`.

Between **every callback** in **every phase**, Node drains:
1. The entire `nextTick` queue.
2. The entire microtask queue.

### `await` is sugar for `.then`
`const x = await p` is equivalent to `p.then(x => /* rest of function */)`. The rest of the function runs as a **microtask**.

### Syntax to lock in
```js
console.log('1: sync');                          // synchronous

process.nextTick(() => console.log('2: nextTick')); // nextTick queue

Promise.resolve().then(() => console.log('3: microtask')); // microtask queue
queueMicrotask(() => console.log('4: microtask'));  // microtask queue

setTimeout(() => console.log('5: timer'), 0);   // timers phase
setImmediate(() => console.log('6: immediate'));// check phase

(async () => {
  await null;                                   // suspends; rest goes to microtask
  console.log('7: after await');
})();
```

### Edge cases (the interview traps)
1. **`nextTick` outruns microtasks**, even though both drain before the next phase. `process.nextTick` queue empties first, *then* the microtask queue.
2. **`await null` / `await undefined` / `await 42`** all enqueue a microtask. You cannot "synchronously fall through" an await even if the awaited value is not a Promise.
3. **An async function up to its first `await` runs synchronously.** Only the part after the await is deferred.
4. **`setTimeout(fn, 0)` vs `setImmediate(fn)`** from the main module is **non-deterministic** — order depends on how fast the runtime entered the timer's "expiry window." Inside an I/O callback, `setImmediate` is guaranteed first.
5. **Microtasks queued from microtasks** are appended and drained in the same flush. Microtasks queued from `nextTick` are drained in the same flush (after nextTick).
6. **`nextTick` queued from a microtask** is *not* drained until the next "step boundary" — but in practice this is still before the next libuv phase, so it still fires before timers.

## Brute force approach
"Just run it and observe." This loses the interview — they want the *prediction*, not the verification. You must walk the queues on the whiteboard.

## Optimal approach
Draw **four columns**: `nextTick`, `microtask`, `timer`, `check`. Walk the code top-down. Every async API → push to the right column. Then drain in priority order: sync → nextTick (fully) → microtask (fully) → next libuv phase callback → drain nextTick + microtask again → repeat.

## Solution (JavaScript)

```js
// The canonical puzzle. Predict the output.
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
```

### Expected output
```
A
J
L
I
G
H
K
B
D
C
E
F
```

(`B` vs `E` ordering from main module: `setTimeout(0)` *usually* fires before `setImmediate`, but this is **not guaranteed** — both Node and V8 docs explicitly warn this is racy. The output above assumes the common case. If you said "B before E or E before B — depends on the loop's entry timing into the timers phase," you've shown senior-level awareness.)

## Step-by-step dry run

Walk it line by line. Maintain four queues.

| Step | Event | nextTick | microtask | timer | check | Output |
|------|-------|----------|-----------|-------|-------|--------|
| 1 | `console.log('A')` | — | — | — | — | `A` |
| 2 | `setTimeout(cb1)` | — | — | [cb1] | — | |
| 3 | `setImmediate(cb2)` | — | — | [cb1] | [cb2] | |
| 4 | `Promise.resolve().then(G)` | — | [G] | [cb1] | [cb2] | |
| 5 | `queueMicrotask(H)` | — | [G, H] | [cb1] | [cb2] | |
| 6 | `process.nextTick(I)` | [I] | [G, H] | [cb1] | [cb2] | |
| 7 | Async IIFE runs sync part: `console.log('J')`, then `await null` suspends | [I] | [G, H, K-cont] | [cb1] | [cb2] | `J` |
| 8 | `console.log('L')` | [I] | [G, H, K-cont] | [cb1] | [cb2] | `L` |
| 9 | **Main script ends.** Drain nextTick queue. | — | [G, H, K-cont] | [cb1] | [cb2] | `I` |
| 10 | Drain microtask queue. | — | — | [cb1] | [cb2] | `G`, `H`, `K` |
| 11 | Enter `timers` phase. Run cb1. Logs `B`. Inside cb1: schedule `C` (microtask) and `D` (nextTick). | [D] | [C] | — | [cb2] | `B` |
| 12 | cb1 returns. Drain nextTick first, then microtask. | — | [C] | — | [cb2] | `D` |
| 13 | Drain microtask. | — | — | — | [cb2] | `C` |
| 14 | Skip empty phases. Enter `check` phase. Run cb2. Logs `E`. Inside cb2: schedule `F` (nextTick). | [F] | — | — | — | `E` |
| 15 | cb2 returns. Drain nextTick. | — | — | — | — | `F` |

Final output: `A J L I G H K B D C E F`. **12 logs**.

### The four mental rules to memorize
1. Sync runs to completion.
2. Between every "thing," drain nextTick **then** microtask, both completely.
3. `await x` is a hidden `.then` — the continuation is a **microtask**.
4. Inside an I/O cb, `setImmediate` beats `setTimeout(0)` deterministically. From main, it's a race.

## Important takeaways

**Syntax to memorize**
- `process.nextTick(fn)` — Node-only, highest async priority.
- `queueMicrotask(fn)` — cross-platform, microtask tier, **does not allocate a Promise**.
- `Promise.resolve().then(fn)` — microtask tier, but allocates a Promise object.
- `setImmediate(fn)` — Node-only, `check` phase.
- `setTimeout(fn, 0)` — `timers` phase. Min delay is actually 1ms on most platforms.

**Patterns to reuse**
- **Yield to I/O without starvation**: use `setImmediate` to break up long CPU work — `setImmediate` lets the poll phase run (so I/O can proceed); `process.nextTick` does *not*.
- **Defer to "end of current sync work"**: use `queueMicrotask`. It's what async/await uses.
- **Debug ordering**: prefix every async API with a number and `console.log` to validate your mental model live.

**Common mistakes**
- Saying "Promise.resolve().then runs before nextTick." **Wrong.** nextTick always wins.
- Forgetting that `await` inserts a microtask **even when awaiting a non-Promise**.
- Assuming `setTimeout(0)` fires before `setImmediate` from main module. **It's a race.** Both Node docs and v8 are explicit.
- Forgetting that nextTick is drained between *every* phase callback, not just at the end of the loop tick. Starvation is real.

**Related questions**
- `process.nextTick` starvation (next question in this bucket)
- `setImmediate` vs `setTimeout(0)` inside I/O
- `queueMicrotask` vs `Promise.resolve().then`
- Top-level await deadlock

## Variants

1. **"Reorder this code to make X log first"** — given the puzzle, swap two lines to change the output. Tests deep mastery, not memorization.
2. **Add `fs.readFile` callback in the middle** — now you have a real I/O step. Inside the readFile callback, `setImmediate` is deterministically before `setTimeout(0)`. This is the classic "main vs I/O" follow-up.
3. **Replace `Promise.resolve().then` with `new Promise(res => res()).then`** — same scheduling, but interviewers test if you know `new Promise(executor)` runs the executor synchronously.
4. **"Why does removing the `await null` change the output?"** — because removing it means the async IIFE runs entirely sync; `K` then logs immediately after `J`, before `L`.

## Revision notes

> **Mixed async output prediction — 60 second recap**
> - **Priority**: sync → nextTick (full drain) → microtask (full drain) → next libuv phase callback.
> - Between **every** phase callback, drain nextTick THEN microtask, fully.
> - `await x` = `.then(x => ...)`; continuation is a microtask. Even `await null` defers.
> - `setImmediate` (check phase) vs `setTimeout(0)` (timers phase): **inside I/O cb → setImmediate first**; from main → race.
> - `process.nextTick` storms can starve I/O. Use `setImmediate` to yield.
> - **Walk the queues out loud** when answering — don't run-and-guess.
> - Trap: forgetting that async IIFE runs sync up to first `await`.
