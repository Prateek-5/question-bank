# `MessageChannel` for cross-realm task scheduling

## Source
- WHATWG HTML spec: https://html.spec.whatwg.org/multipage/web-messaging.html#message-channels
- MDN: https://developer.mozilla.org/en-US/docs/Web/API/MessageChannel
- React Scheduler source (uses MessageChannel): https://github.com/facebook/react/blob/main/packages/scheduler/src/forks/SchedulerDOM.js
- Vue 3 nextTick implementation (uses microtask fallback chain).

## Why this question matters in interviews
This is a senior-level question because the **right answer involves admitting `MessageChannel` is NOT a microtask** — it's a *macrotask* (or "task" in HTML spec language). Most candidates conflate them. Production schedulers (React's, Vue's, Lit's) use `MessageChannel` specifically to **yield to the browser between batches of work** while staying faster than `setTimeout(0)`. If you can explain why React doesn't just use `queueMicrotask` for everything, you're showing the kind of judgment that gets senior-engineer offers.

## Concepts involved

### What `MessageChannel` actually does
Creates a pair of `MessagePort` objects. Posting a message on one port schedules a `'message'` event on the other port — as a **task** (macrotask), not a microtask.

### Syntax to lock in
```js
const { port1, port2 } = new MessageChannel();

port1.onmessage = (event) => {
  console.log('received:', event.data);
};

port2.postMessage('hello');
// Next macrotask: port1.onmessage fires.
```

In Node, `MessageChannel` is in `node:worker_threads` (also globally available since Node 15). Same scheduling semantics.

### Why React/Vue use it instead of `setTimeout(0)`
- **`setTimeout(fn, 0)` is coerced to 4ms** for nested timers (HTML5 clamping rule).
- **`MessageChannel.postMessage` has no clamping** — it's queued as a task immediately.
- React's scheduler does work in 5ms slices; if it used `setTimeout`, the 4ms clamp would consume most of the budget. With `MessageChannel`, the yield cost is sub-millisecond.

### Why not `queueMicrotask` for scheduling?
- Microtasks drain in the **same** tick. The browser never gets a chance to render between microtasks. If you `queueMicrotask` recursively to "yield," the page is frozen.
- `MessageChannel` posts a *task*, which yields to the rendering pipeline. The browser gets to paint, handle clicks, etc., between tasks.

### Scheduling tier summary
| API | Tier | Min delay | Used for |
|-----|------|-----------|----------|
| `process.nextTick` | nextTick (Node-only) | none | Emit-before-I/O |
| `queueMicrotask` | microtask | none | After current sync, before I/O |
| `Promise.resolve().then` | microtask | none | Same as queueMicrotask + Promise allocation |
| `MessageChannel.postMessage` | task / macrotask | ~0ms (no clamp) | Yield to render, batched scheduler |
| `setTimeout(fn, 0)` | timers phase / task | 1ms (Node) / 4ms (clamped) | Delayed work |
| `setImmediate` | check phase (Node) | none | Yield to poll in Node |
| `requestIdleCallback` | idle | varies | Background work in browser |

### Edge cases
1. **Cross-realm**: `MessageChannel` can post between iframes (in browsers) and across worker threads (in Node). Used to bridge isolated contexts.
2. **Transferable objects**: `port.postMessage(data, [transferList])` — moves ArrayBuffer ownership without copy. Critical for high-perf workers.
3. **Garbage collection of unused ports**: if you don't `.start()` or attach `onmessage`, the port may be GC'd. Always attach a listener before posting.
4. **Closing**: `port1.close()` stops further messages. Important for cleanup in long-running schedulers.
5. **Order**: messages posted in order are delivered in order. FIFO within a single channel.
6. **Node-specific**: `worker_threads.MessageChannel` works between threads, with structured cloning + transferables.

## Brute force approach
"I'd use `setTimeout(0)`." Works, but the 4ms clamp kills perf at scale. Used in pre-2016 schedulers. React migrated away from it for exactly this reason.

## Optimal approach
For "yield to main thread" semantics in browsers:
```js
const { port1, port2 } = new MessageChannel();
const callbacks = new Set();

port1.onmessage = () => {
  for (const cb of callbacks) cb();
  callbacks.clear();
};

function yieldToMainThread(cb) {
  callbacks.add(cb);
  port2.postMessage(0); // wake up port1 next task
}
```

For Node cross-thread communication, use `MessageChannel` from `worker_threads` to exchange data between main thread and a worker.

## Solution (JavaScript)

### A minimal scheduler à la React

```js
/**
 * yieldToMain(): defer fn to the next macrotask (after rendering, after I/O).
 * Uses MessageChannel because:
 *  - setTimeout(0) is clamped to 4ms (nested timers)
 *  - queueMicrotask doesn't yield to rendering
 */
const channel = new MessageChannel();
const queue = [];
let scheduled = false;

channel.port1.onmessage = () => {
  scheduled = false;
  // Snapshot to avoid mutations during iteration.
  const tasks = queue.splice(0);
  for (const task of tasks) {
    try { task(); }
    catch (e) { setTimeout(() => { throw e; }); } // re-throw async, don't kill loop
  }
};

function yieldToMain(fn) {
  queue.push(fn);
  if (scheduled) return;
  scheduled = true;
  channel.port2.postMessage(0);
}

// Demo
console.log('sync 1');
queueMicrotask(() => console.log('microtask'));
yieldToMain(() => console.log('yielded 1'));
yieldToMain(() => console.log('yielded 2'));
setTimeout(() => console.log('timer 4ms'), 0);
console.log('sync 2');
```

### Expected output (browser)
```
sync 1
sync 2
microtask
yielded 1
yielded 2
timer 4ms
```

Why this ordering:
- Sync runs first.
- Microtask drains after current sync.
- MessageChannel task fires as the next task (before the clamped setTimeout).
- setTimeout(0) waits ~4ms.

### React's actual usage (simplified)
```js
function schedulerPostTask(callback) {
  channel.port2.postMessage(null);
  scheduledHostCallback = callback;
}

channel.port1.onmessage = () => {
  const currentTime = performance.now();
  const hasMoreWork = scheduledHostCallback(currentTime);
  if (hasMoreWork) {
    channel.port2.postMessage(null); // schedule next slice
  }
};
```
Each slice does work for ~5ms then yields. Smooth 60fps. With `setTimeout(0)` and its 4ms clamp, you'd waste 80% of the budget.

### Node cross-thread example

```js
const { Worker, MessageChannel } = require('node:worker_threads');

const { port1, port2 } = new MessageChannel();
const worker = new Worker(`
  const { parentPort } = require('node:worker_threads');
  parentPort.once('message', ({ port }) => {
    port.on('message', (msg) => port.postMessage('echo: ' + msg));
  });
`, { eval: true });

worker.postMessage({ port: port2 }, [port2]); // transfer port2 to worker
port1.on('message', (msg) => console.log(msg));
port1.postMessage('hello from main');
// Logs: echo: hello from main
```

## Step-by-step dry run

```js
const ch = new MessageChannel();
ch.port1.onmessage = () => console.log('port1 received');
console.log('A');
ch.port2.postMessage('x');     // queues a task
queueMicrotask(() => console.log('B'));
console.log('C');
```

Trace:
- Sync: log `A`, post message (queues task), queue microtask, log `C`.
- Sync ends.
- Drain microtask: log `B`.
- Browser/runtime pumps next task: fires `port1.onmessage` → log `port1 received`.

Output: `A C B port1 received`.

Note: microtask drains before the MessageChannel task — they're on different tiers.

## Important takeaways

**Syntax to memorize**
- `const { port1, port2 } = new MessageChannel()`.
- `port.onmessage = (e) => ...`; data on `e.data`.
- `port.postMessage(data, [transferList])` — postMessage queues a task.
- `port.close()` for cleanup.

**Patterns to reuse**
- **Browser scheduler**: MessageChannel for sub-4ms yield to main thread. Used by React, Vue, Lit.
- **Cross-thread messaging in Node**: MessageChannel from worker_threads, with transferables for zero-copy.
- **Cross-iframe comms**: MessageChannel for isolated trusted communication channels.

**Common mistakes**
- Calling MessageChannel a "microtask scheduler." It's a **macrotask** scheduler. Microtask = queueMicrotask.
- Forgetting `port.close()` — long-running schedulers leak channels otherwise.
- Forgetting transferList — copying a 100MB ArrayBuffer instead of transferring.
- Believing `setTimeout(0)` and MessageChannel are equivalent. They're not — `setTimeout(0)` has a 1ms (Node) / 4ms-when-nested (browser) clamp.

**Related questions**
- queueMicrotask vs Promise.resolve().then
- setImmediate vs setTimeout(0) in I/O
- worker_threads
- React Scheduler internals

## Variants

1. **"Implement requestIdleCallback polyfill"** — combine MessageChannel for yielding with `performance.now()` for budget tracking. (See the dedicated machine-coding problem on this.)
2. **"Why doesn't browser have setImmediate?"** — IE/Edge legacy had it, others rejected for spec reasons. The standardized replacement is essentially `MessageChannel.postMessage`.
3. **"Implement a backpressured task queue between two iframes"** — port-based comms with explicit ack messages.
4. **"How would you cancel a posted message?"** — you can't. Once queued, the task is scheduled. You can ignore it in the handler by checking a generation counter.

## Revision notes

> **MessageChannel — 60 second recap**
> - Posts a **task (macrotask)**, NOT a microtask.
> - Used by React/Vue schedulers because:
>   - faster than `setTimeout(0)` (no 4ms clamp)
>   - yields to render (unlike `queueMicrotask`)
> - `port1.onmessage = fn; port2.postMessage(0)` is the idiom.
> - In Node: from `worker_threads`; supports cross-thread + transferables (zero-copy).
> - **Trap**: thinking it's a microtask scheduler. It's a task scheduler.
> - Cleanup with `port.close()` for long-running services.
