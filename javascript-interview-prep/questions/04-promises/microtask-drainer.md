# Microtask Drainer / Manual Microtask Flush

## Source / Origin
- Comes from `queueMicrotask`, `Promise.resolve().then`; the V8 microtask queue.
- Asked at: Razorpay, Stripe, Atlassian, anywhere with output-prediction puzzles.
- Concept reference: `concepts/event-loop.md`, `concepts/promises.md`.

## Why this question matters in interviews
"Predict the output" or "schedule N tasks but flush all microtasks before any macrotask" is a recurring puzzle. The microtask queue drains *to completion* between every macrotask and after every top-level script. Senior bar: you can explain why `setTimeout(0)` runs *after* a chained `.then`, why excessive microtasks cause UI freeze (microtask starvation), and how to implement a "wait for everything queued right now" primitive.

## Concepts involved

### Syntax to lock in
```js
// 1. Trigger a microtask
queueMicrotask(() => console.log('microtask'));
Promise.resolve().then(() => console.log('also microtask'));

// 2. Drain all currently-queued microtasks before the next macrotask
function drainMicrotasks() {
  return new Promise(res => setImmediate(res));   // Node: setImmediate is a macrotask
  // browser: return new Promise(res => setTimeout(res, 0))
}

// 3. Microtask order vs macrotask order
console.log('1');
setTimeout(() => console.log('4 (macrotask)'), 0);
Promise.resolve().then(() => console.log('2 (microtask)'));
queueMicrotask(() => console.log('3 (microtask)'));
console.log('1.5');
// Order: 1, 1.5, 2, 3, 4
```

### Edge cases / interview traps
1. **Microtasks chain into more microtasks.** A `.then` inside a `.then` adds another microtask that runs in the *same* drain. The queue drains until empty, not just length-at-start.
2. **`process.nextTick` (Node) is its own queue,** drained even *before* the microtask queue. Recursive `nextTick` starves microtasks AND macrotasks (= "I/O starvation").
3. **`queueMicrotask` vs `.then`** — same queue; `.then` allocates a promise.
4. **`await` of a non-Promise** still schedules a microtask.
5. **`await` of a synchronous value** — still defers to the next microtask. `async function() { return 1 }` then `.then` runs one microtask later.
6. **Microtask starvation** — a long chain of `.then.then.then...` blocks the macrotask queue (timers, I/O callbacks) and freezes the UI.
7. **"Drain microtasks" isn't a real API** — you simulate it by scheduling a macrotask (`setImmediate` / `setTimeout(0)`) and awaiting it.
8. **`Promise.resolve(p)` where p is already a Promise** — short-circuits (returns p). Doesn't add an extra microtask.

## Mental Model

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

So after each macrotask: drain all microtasks. After the top-level script: drain all microtasks before the first timer fires.

```
   sync prints "1"
   schedule setTimeout(t1)        macroQ = [t1]
   schedule .then(m1)             microQ = [m1]
   schedule queueMicrotask(m2)    microQ = [m1, m2]
   sync prints "1.5"
   script ends → drain micro queue → m1 runs → m2 runs
   loop picks next macrotask → t1 runs
```

## Why interviewers care

- **Foundational event-loop knowledge.** Either you know it cold or you don't.
- **Output-prediction puzzles** are filtering tools at top firms.
- **Production bug pattern** — microtask starvation is a real outage cause (long Promise chains in HTTP handlers blocking timers).

## Common beginner confusion

- **"setTimeout(0) runs immediately."** No — it runs after the current macrotask + microtask drain.
- **"Microtasks and macrotasks alternate one-by-one."** No — *all* microtasks drain before *any* macrotask.
- **"`process.nextTick` is faster than queueMicrotask."** Faster in latency, but it's a separate queue that drains *before* microtasks, and can starve everything if recursive.
- **"`await` is just sleep."** It's a microtask suspension.
- **"async function returns synchronously if no await."** It still wraps the value in a promise; subsequent `.then` is a microtask away.

## Brute force approach

```js
// "wait for everything pending" via repeated setTimeout
for (let i = 0; i < 10; i++) await new Promise(r => setTimeout(r, 0));
// fragile — depends on how many macrotasks the runtime has queued
```

## Optimal approach

For "drain microtasks" use one macrotask boundary: `await new Promise(res => setImmediate(res))` (Node) or `await new Promise(res => setTimeout(res, 0))` (browser). Microtasks fully drained before that callback fires.

## Solution (JavaScript)

```js
// Drain microtasks: wait until the next macrotask runs (microtask queue is empty by then)
function drainMicrotasks() {
  return new Promise(resolve => {
    if (typeof setImmediate === 'function') setImmediate(resolve);
    else setTimeout(resolve, 0);
  });
}

// Example: ensure all pending Promise.then's run before continuing
let log = [];
log.push('A');
Promise.resolve().then(() => log.push('B'));
queueMicrotask(() => log.push('C'));
await drainMicrotasks();
// log === ['A', 'B', 'C']

// Counter-example: microtask starvation
async function starve() {
  while (true) await Promise.resolve();     // never yields to macrotasks
}
// timers and I/O callbacks never fire while this loop runs
```

## Step-by-step dry run

```js
console.log('s1');
setTimeout(() => console.log('t1'), 0);
Promise.resolve()
  .then(() => { console.log('m1'); return Promise.resolve(); })
  .then(() => console.log('m2'));
queueMicrotask(() => console.log('m3'));
console.log('s2');
```

```
Step 1: top-level script runs synchronously
        macroQ: [t1]
        microQ: [m1-handler, m3]
        prints: s1, s2

Step 2: script ends → drain microQ
        run m1-handler → prints 'm1' → returns Promise.resolve()
                       → schedules m2-handler (waits one microtask for chained promise resolution)
                       → microQ: [m3, m2-handler]
        run m3 → prints 'm3' → microQ: [m2-handler]
        run m2-handler → prints 'm2' → microQ: []

Step 3: microQ empty → next macrotask t1
        prints 't1'

Output: s1, s2, m1, m3, m2, t1
```

The "m1 → m3 → m2" order (not m1→m2→m3) trips up most candidates. Reason: chaining `.then(Promise.resolve())` adds an extra microtask hop.

## How to think aloud in the interview

> "Two queues. Microtask queue drains to completion between macrotasks. queueMicrotask and Promise.then enqueue microtasks; setTimeout enqueues macrotasks. process.nextTick (Node) is even higher priority — drains before microtasks. To 'drain microtasks' I schedule a macrotask (setImmediate or setTimeout(0)) and await it; by the time it runs, microtask queue is empty. Watch for chained promises that add extra microtask hops — that's the m1 m3 m2 trap. Beware microtask starvation: an infinite `await Promise.resolve()` blocks timers and I/O."

## Important takeaways

- **Microtasks drain to completion** between macrotasks.
- **Order**: sync → microtasks (incl. process.nextTick first) → next macrotask.
- **`Promise.resolve(promise)` short-circuits** but chained `.then(() => Promise.resolve())` does add a hop.
- **Drain primitive**: `await setImmediate` (Node) or `await setTimeout(0)` (browser).
- **Microtask starvation** = real outage cause.

## Variants

- **Async drain** — `while (microtaskCount > 0) await microtask`. Doesn't exist in JS API; simulated via macrotask boundary.
- **Test utilities** — testing libraries (RTL, jest) expose `flushPromises()` which is just `await new Promise(r => setTimeout(r))`.
- **`Promise.resolve().then` vs `queueMicrotask`** — identical scheduling cost; latter allocates no promise.
- **`process.nextTick` recursion** — Node's "starvation" gotcha; use `setImmediate` to break the loop.

## Revision notes

```
event loop turn:
  run 1 macrotask
  drain microtask queue to EMPTY (microtasks can enqueue microtasks)
  repeat

priority:
  Node: process.nextTick > microtask (.then, queueMicrotask) > macrotask (setTimeout, setImmediate, I/O)
  browser: microtask > macrotask

drain primitive: await new Promise(r => setImmediate(r))  // Node
                 await new Promise(r => setTimeout(r, 0)) // browser

traps:
  - .then(() => Promise.resolve()) adds extra microtask hop
  - process.nextTick recursion starves I/O
  - while(true) await Promise.resolve() starves timers
```
