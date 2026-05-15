# Worker threads — when the event loop isn't enough

## Source
- Node.js docs: https://nodejs.org/api/worker_threads.html
- libuv design: http://docs.libuv.org/en/v1.x/design.html
- Piscina (production-grade worker pool): https://github.com/piscinajs/piscina
- "Don't block the event loop" — Node official guide.

## Why this question matters in interviews
The event loop assumes **all callbacks are short**. As soon as you do `JSON.parse(huge)` or `bcrypt.hashSync(...)` or any CPU-bound computation, you block I/O. Senior backend interviewers ask this question to verify you know the difference between **I/O concurrency** (event loop's job) and **CPU concurrency** (worker_threads' job). The follow-up is almost always: "you have a CPU-heavy endpoint, how do you scale it?" — and the answer is worker threads with a pool, not "scale horizontally."

## Concepts involved

### Single-threaded model recap
Node runs JavaScript on **one** thread. All `setTimeout`, `Promise.then`, async I/O callbacks share that thread. libuv has a thread pool (default 4 threads) — but it's used internally for filesystem ops and DNS lookups, not for your JS code.

### What blocks the loop
- `JSON.parse` / `JSON.stringify` on large objects.
- `crypto.pbkdf2Sync`, `bcrypt.hashSync`, any `*Sync` API.
- Regex with catastrophic backtracking.
- Tight CPU loops (image processing, parsing, compilation).
- Synchronous compression / decompression.

When you block the loop, **every other request waits**. HTTP latency p99 spikes. Health probes fail.

### What worker_threads gives you
- Each worker has its **own V8 isolate, its own event loop, its own heap**.
- Communication via `postMessage` (structured clone) or `SharedArrayBuffer + Atomics` (zero-copy shared memory).
- Spawning is **expensive** (~20-50ms cold start) — use a **pool**.

### Syntax to lock in
```js
// main.js
const { Worker } = require('node:worker_threads');

const worker = new Worker('./worker.js', {
  workerData: { input: [1, 2, 3] }
});

worker.on('message', (result) => console.log('result:', result));
worker.on('error', (err) => console.error('worker error:', err));
worker.on('exit', (code) => console.log('worker exited:', code));
```

```js
// worker.js
const { parentPort, workerData } = require('node:worker_threads');

const result = workerData.input.reduce((a, b) => a + b, 0);
parentPort.postMessage(result);
```

### SharedArrayBuffer + Atomics
```js
const sab = new SharedArrayBuffer(8); // 8 bytes
const arr = new Int32Array(sab);       // typed view
// Pass `sab` to a worker; both threads see the same bytes.
// Use Atomics.add, Atomics.load, Atomics.wait/notify for safe access.
```

### Edge cases
1. **Worker startup cost is real** — ~20-50ms for first message. Use `piscina` to maintain a warm pool.
2. **Workers can't share regular objects** — `postMessage` does a structured clone (deep copy). Large objects = expensive.
3. **SharedArrayBuffer + Atomics is the only way to share state without copying.** It's also error-prone (memory model bugs). Use lock-free libs (`@kbrw/atomics-mutex`, etc.) or avoid.
4. **No DOM access** — workers in Node have no `document` (also true in browsers).
5. **Cluster vs worker_threads** — `cluster` forks processes, each with its own V8 + event loop. Heavier than threads but isolated (one OOM doesn't kill all). `worker_threads` share the process; cheaper but a bug in one can corrupt shared memory.
6. **Worker exit on uncaughtException** — the worker exits; main thread sees `'exit'` event with non-zero code. Handle it; restart.
7. **`postMessage` queues to the worker's message queue** — drained between event loop phases on the worker side. The worker can be busy in JS and not receive messages until it yields.

## Brute force approach
"Just use `child_process.fork`." Works but slower (separate processes, no shared memory). Use `cluster` for HTTP scaling, worker_threads for CPU offload.

## Optimal approach
Use a **worker pool** (piscina or hand-rolled). Pool workers stay warm; queued tasks are dispatched to whichever worker is idle. For zero-copy data sharing, use `SharedArrayBuffer + Atomics`.

## Solution (JavaScript)

### A minimal worker pool

```js
// pool.js
const { Worker } = require('node:worker_threads');
const path = require('node:path');
const os = require('node:os');

class WorkerPool {
  constructor(workerScript, size = os.cpus().length) {
    this.workers = [];
    this.queue = [];        // pending tasks
    this.free = [];         // idle workers
    for (let i = 0; i < size; i++) {
      const w = new Worker(workerScript);
      w.on('message', (result) => this._onResult(w, result));
      w.on('error', (err) => this._onError(w, err));
      this.workers.push(w);
      this.free.push(w);
    }
  }

  run(input) {
    return new Promise((resolve, reject) => {
      this.queue.push({ input, resolve, reject });
      this._drain();
    });
  }

  _drain() {
    while (this.free.length && this.queue.length) {
      const w = this.free.pop();
      const task = this.queue.shift();
      w._task = task;
      w.postMessage(task.input);
    }
  }

  _onResult(w, result) {
    const task = w._task;
    w._task = null;
    task.resolve(result);
    this.free.push(w);
    this._drain();
  }

  _onError(w, err) {
    const task = w._task;
    if (task) task.reject(err);
    // worker died → replace it (production logic omitted)
  }

  async close() {
    await Promise.all(this.workers.map(w => w.terminate()));
  }
}

module.exports = WorkerPool;
```

```js
// hash-worker.js
const { parentPort } = require('node:worker_threads');
const crypto = require('node:crypto');

parentPort.on('message', (password) => {
  // CPU-bound: would block the main loop for 200ms
  const hash = crypto.pbkdf2Sync(password, 'salt', 100_000, 64, 'sha512');
  parentPort.postMessage(hash.toString('hex'));
});
```

```js
// server.js
const http = require('node:http');
const WorkerPool = require('./pool');
const pool = new WorkerPool('./hash-worker.js');

http.createServer(async (req, res) => {
  if (req.url === '/hash') {
    const hash = await pool.run('pa$$w0rd');
    res.end(hash);
  } else {
    res.end('hello');
  }
}).listen(3000);
// /hello stays fast (no blocking) while /hash is offloaded.
```

### SharedArrayBuffer example (zero-copy counter)

```js
// Main thread
const sab = new SharedArrayBuffer(4);
const counter = new Int32Array(sab);
const worker = new Worker('./inc-worker.js', { workerData: { sab } });

setTimeout(() => {
  console.log('counter after 1s:', Atomics.load(counter, 0));
}, 1000);

// inc-worker.js
const { workerData } = require('node:worker_threads');
const counter = new Int32Array(workerData.sab);
for (let i = 0; i < 1_000_000; i++) {
  Atomics.add(counter, 0, 1);    // atomic +1
}
```

Both threads see the same memory. `Atomics.add` is the safe way to mutate.

## Step-by-step dry run

```js
const { Worker } = require('node:worker_threads');

console.log('main: start');
const w = new Worker(`
  const { parentPort } = require('node:worker_threads');
  let sum = 0;
  for (let i = 0; i < 1e8; i++) sum += i;  // CPU heavy, ~500ms
  parentPort.postMessage(sum);
`, { eval: true });

w.on('message', (sum) => console.log('main: got', sum));
console.log('main: continuing');
setInterval(() => console.log('main: tick'), 100).unref();
```

Trace:
- `main: start` logs.
- Worker spawned (~30ms cold start). Worker thread begins the 1e8 loop.
- `main: continuing` logs.
- Main thread is **unblocked**. Every 100ms: `main: tick`.
- After ~500ms, worker finishes its loop, posts message.
- Main thread's next event loop iteration picks up the message: `main: got 4999999950000000`.

Without the worker (sync loop on main): you'd see `main: start`, then a 500ms freeze, no ticks, then `main: continuing`. The interval would be queued but starved.

## Important takeaways

**Syntax to memorize**
- `new Worker(scriptPath, { workerData })`.
- `worker.on('message' | 'error' | 'exit', cb)`.
- `parentPort.postMessage(value)` from inside worker.
- `new SharedArrayBuffer(bytes)` + typed array view + Atomics.

**Patterns to reuse**
- **Worker pool**: keep workers warm. Library: `piscina`.
- **Pipeline of workers**: chain workers via MessageChannel — Stage 1 (parse) → Stage 2 (transform) → Stage 3 (serialize).
- **SharedArrayBuffer**: for high-frequency state between workers; for typed binary data (image pixels, audio buffers).

**Common mistakes**
- Spawning a new worker per request — kills perf (cold start cost). Pool.
- Passing large objects via `postMessage` — structured clone copies them. Use SharedArrayBuffer for zero-copy.
- Forgetting `Atomics.*` for shared state — race conditions silently corrupt data.
- Using workers for I/O — pointless. Workers are for **CPU**. I/O already doesn't block (libuv handles it).
- Not handling worker death — a worker can crash; pool must replace.

**Related questions**
- libuv thread pool (UV_THREADPOOL_SIZE)
- cluster vs worker_threads vs child_process
- AsyncLocalStorage in worker context (no, it doesn't propagate)
- MessageChannel cross-thread

## Variants

1. **"When would you choose `cluster` over `worker_threads`?"** — when you need OS-level isolation (memory leak in one process doesn't affect others), when you want OS-level load balancing across HTTP listeners, or when forking external CLI tools.
2. **"How do you debug a worker?"** — `node --inspect-brk=0.0.0.0:9230 main.js`; attach to worker via `worker.threadId` in DevTools.
3. **"What about libuv's thread pool — isn't that already 'workers'?"** — libuv's pool is for **C-level I/O** (filesystem, DNS, some crypto). You can't run JS on it. `UV_THREADPOOL_SIZE=N` env var controls its size (default 4).
4. **"How do you implement piscina from scratch?"** — pool of workers, FIFO queue, round-robin dispatch, idle-replace on crash, terminate-on-shutdown. The pool above is ~80% of the implementation.

## Revision notes

> **worker_threads — 60 second recap**
> - Event loop = single-threaded for JS. CPU-heavy work blocks I/O.
> - **worker_threads**: each worker has its own V8 isolate, heap, event loop.
> - Communication: `postMessage` (structured clone, copy) or `SharedArrayBuffer + Atomics` (zero-copy).
> - **Use a pool** (piscina) — cold start ~30ms makes per-request workers pointless.
> - Workers are for **CPU** (parsing, hashing, image processing). I/O already doesn't block.
> - `cluster` = process-level (heavier, isolated). `worker_threads` = thread-level (cheaper, shared memory).
> - **Trap**: thinking workers help I/O. They don't. Use them only when JS is CPU-bound.
