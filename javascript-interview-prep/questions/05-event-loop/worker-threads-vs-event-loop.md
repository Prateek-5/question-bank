# Worker threads vs the event loop — when single-threaded isn't enough

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [event-loop-concurrency.md](./event-loop-concurrency.md), [microtask-starvation-recipes.md](./microtask-starvation-recipes.md)
>
> **Source:** Node docs, libuv design, Piscina. Senior backend interview.

---

## 1. Problem statement

When does the event loop fall short? When use `worker_threads`? `cluster`? `child_process`?

**Verification examples**

| Workload                                | Right tool                                              |
|-----------------------------------------|---------------------------------------------------------|
| 1000 concurrent HTTP requests           | event loop (I/O concurrent natively)                   |
| `JSON.parse(huge)` on hot path           | `worker_threads`                                       |
| `bcrypt.hashSync(...)`                   | `worker_threads` (CPU-bound)                            |
| Crash isolation, OS load balancing       | `cluster` (separate processes)                          |
| Fork an external CLI                     | `child_process.spawn`                                   |
| Share state between threads              | `SharedArrayBuffer + Atomics` (worker_threads)         |

**Constraints**
- Event loop = I/O concurrency, NOT CPU concurrency.
- Worker startup cost (~20-50ms) → use a pool.
- `postMessage` = structured clone (copies); SAB = zero-copy.
- Workers can't run libraries that need DOM.

---

## 2. Plain-English restatement

Node runs JS on one thread. I/O is offloaded to libuv internally — your JS code doesn't block. But CPU-bound JS (parsing, hashing, image processing) DOES block — every other request waits. `worker_threads` give you a separate V8 isolate with its own event loop for that CPU work.

---

## 3. Why this matters in interviews

Senior backend interviewers verify you know the difference between **I/O concurrency** (event loop's job) and **CPU concurrency** (worker_threads' job). Follow-up: "you have a CPU-heavy endpoint, how do you scale?" — workers with a pool, not "scale horizontally."

---

## 4. Mental model

```
   Single-threaded event loop:
   ┌─────────────────────────────────┐
   │ Main thread — all JS runs here   │
   │                                  │
   │ libuv thread pool (size 4)       │
   │ for fs/dns/crypto C-level work   │
   │ — JS callbacks queue BACK to     │
   │   main thread.                   │
   └─────────────────────────────────┘

   What blocks the loop:
   - JSON.parse / JSON.stringify on large objects
   - crypto.*Sync, bcrypt.hashSync
   - Regex with catastrophic backtracking
   - Tight CPU loops (image, parsing)

   worker_threads:
   ┌──────────────┐  postMessage  ┌──────────────┐
   │ Main V8       │ ←──────────→ │ Worker V8     │
   │ event loop    │  (structured │ event loop    │
   │               │   clone)      │               │
   │               │              │               │
   │   SAB ←─── shared memory ───→ SAB             │
   │             (zero-copy)                       │
   └──────────────┘              └──────────────┘

   Each worker = separate V8 isolate, separate heap, separate event loop.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does the event loop's libuv thread pool run JS in parallel?
> 2. Why use a worker POOL instead of spawning per request?
> 3. What's the difference between `postMessage` and `SharedArrayBuffer`?

---

## 6. Brute force — walked through

### Wrong attempt 1: "scale horizontally" for CPU work
Wastes resources; one process per replica. Workers within a process share OS resources better.

### Wrong attempt 2: spawn worker per request
~20-50ms cold start. Kills perf. Pool warm workers.

### Wrong attempt 3: `postMessage` huge objects
Structured clone copies all bytes. For 100MB → use SAB or transferList.

### Wrong attempt 4: workers for I/O
Pointless — libuv handles I/O without blocking already.

---

## 7. The unlocking insight

> **Workers are for CPU, not I/O. Each worker has its own V8 isolate. Communicate via `postMessage` (structured clone) or `SharedArrayBuffer + Atomics` (zero-copy). Use a pool (Piscina) because cold start is expensive.**

Three properties:

1. **I/O ≠ CPU.** Event loop handles I/O; workers handle CPU.
2. **Pool warm workers** — ~30ms cold start.
3. **SAB for zero-copy state**; `postMessage` for messages.

---

## 8. Solution (annotated)

```js
// Minimal worker pool
const { Worker } = require('node:worker_threads');
const os = require('node:os');

class WorkerPool {
  constructor(workerScript, size = os.cpus().length) {
    this.workers = [];
    this.queue = [];
    this.free = [];
    for (let i = 0; i < size; i++) {
      const w = new Worker(workerScript);                              // step 1: warm pool
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
      w.postMessage(task.input);                                       // step 2: dispatch
    }
  }
  _onResult(w, result) {
    const task = w._task;
    task.resolve(result);
    this.free.push(w);
    this._drain();
  }
  _onError(w, err) {
    if (w._task) w._task.reject(err);
    // production: replace worker
  }
  close() { return Promise.all(this.workers.map((w) => w.terminate())); }
}
```

**Try it yourself**

```js
// hash-worker.js
const { parentPort } = require('node:worker_threads');
const crypto = require('node:crypto');
parentPort.on('message', (password) => {
  const hash = crypto.pbkdf2Sync(password, 'salt', 100_000, 64, 'sha512');
  parentPort.postMessage(hash.toString('hex'));
});

// server.js
const pool = new WorkerPool('./hash-worker.js');
http.createServer(async (req, res) => {
  if (req.url === '/hash') {
    const hash = await pool.run('pa$$w0rd');                          // offload CPU
    res.end(hash);
  } else {
    res.end('hello');                                                  // stays fast
  }
}).listen(3000);

// SharedArrayBuffer for zero-copy counter
const sab = new SharedArrayBuffer(4);
const counter = new Int32Array(sab);
const worker = new Worker('./inc-worker.js', { workerData: { sab } });
Atomics.add(counter, 0, 1);                                            // safe mutate
```

---

## 9. Step-by-step dry run

```
Without worker — CPU-bound endpoint:
t=0    HTTP req for /hash arrives → handler starts.
       bcrypt.hashSync runs synchronously. ~500ms.
       Event loop FROZEN. Other requests wait.
t=10   HTTP req for /healthcheck arrives. Queues. Waits.
t=20   Another /healthcheck. Waits.
t=500  /hash returns. Event loop wakes. All queued requests served LATE.
       p99 latency on /healthcheck: 500ms+.

With worker pool:
t=0    /hash arrives → pool.run(payload).
       Main thread: returns Promise; continues other work.
t=0    pool dispatches to free worker. Worker thread CPU-busy.
       Main thread: free.
t=10   /healthcheck arrives → main thread handles immediately.
t=15   another /healthcheck → handled.
t=500  worker posts result back. Main thread fulfills Promise.
       /hash request returns.
       p99 on /healthcheck: ~1ms (unaffected).
```

---

## 10. Common confusion + traps

1. **"libuv pool runs JS in parallel"** — no, C-level work only; JS callbacks queue back to main.
2. **"Workers help with I/O"** — pointless; libuv already handles I/O.
3. **Spawn per request** — cold start kills perf; use pool.
4. **`postMessage` zero-cost** — structured clone copies; use SAB for big payloads.
5. **`SharedArrayBuffer` without Atomics** — silent corruption.
6. **`cluster` and `worker_threads` interchangeable** — cluster forks processes; workers share process.
7. **`AsyncLocalStorage` propagates to workers** — no, separate isolates.

---

## 11. Senior follow-ups & variants

### Variant 1 — `cluster` vs `worker_threads`
Cluster forks processes (OS isolation, OS load balance); workers share process (cheaper, can share memory).

### Variant 2 — `child_process.spawn` / `fork`
For external CLIs or process-level isolation; heavier than workers.

### Variant 3 — `UV_THREADPOOL_SIZE`
Tune libuv internal pool (default 4) for crypto-heavy workloads.

### Variant 4 — Piscina
Production-grade worker pool. Auto-recycle on crash; backpressure; abort.

### Variant 5 — Pipeline of workers
Chain via `MessageChannel`: Stage 1 (parse) → Stage 2 (transform) → Stage 3 (serialize).

### Variant 6 — Debugging a worker
`node --inspect-brk=0.0.0.0:9230 main.js`; attach via `worker.threadId` in DevTools.

---

## 12. How to think aloud

> "Event loop = I/O concurrency, NOT CPU. Single thread runs all JS. CPU-bound work (JSON.parse big, bcrypt.hashSync, regex, image processing) blocks ALL other requests. Solution: `worker_threads` — each worker is its own V8 isolate, separate heap, separate event loop. Communicate via `postMessage` (structured clone) or `SharedArrayBuffer + Atomics` (zero-copy shared memory). Use a POOL (Piscina) because cold start is ~30ms. `cluster` is process-level (heavier, isolated); `worker_threads` is thread-level (cheaper, shared memory). Workers are for CPU, NOT I/O. Trap: spawning per request; postMessage on huge objects (copy); SAB without Atomics."

---

## 13. 60-second revision

> - **Event loop = I/O concurrency**, NOT CPU.
> - **Workers** = separate V8 isolate, heap, event loop.
> - **`postMessage`** = structured clone (copy); **`SharedArrayBuffer`** = zero-copy.
> - **Use a pool** (Piscina) — cold start ~30ms.
> - **Workers for CPU only;** I/O already doesn't block.
> - **`cluster`** = process-level (OS isolation); **`worker_threads`** = thread-level.
> - **`SharedArrayBuffer + Atomics`** for safe shared mutation.
> - **Trap:** workers help I/O; spawn-per-request; postMessage huge data; SAB without Atomics.

---

**Related:** [worker-pool-implementation.md](./worker-pool-implementation.md) · [microtask-starvation-recipes.md](./microtask-starvation-recipes.md) · [event-loop-concurrency.md](./event-loop-concurrency.md) · [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
