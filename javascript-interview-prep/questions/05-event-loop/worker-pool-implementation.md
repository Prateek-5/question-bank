# Worker Pool — reusable threads with task queue

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md), [`10-machine-coding-patterns/async-pool.md`](../10-machine-coding-patterns/async-pool.md)
>
> **Source:** Node `worker_threads`, browser `Worker`, Piscina library. Cloudflare, Stripe, Atlassian.

---

## 1. Problem statement

**Signature**
```ts
class WorkerPool {
  constructor(workerScript: string, size?: number);
  run<T>(input: any): Promise<T>;
  close(): Promise<void>;
}
```

**Verification examples**

| Setup                                            | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| 100 tasks → pool of 8 workers                    | 8 in flight; queue 92; drain as workers free          |
| Task throws                                       | task Promise rejects; worker reused (or replaced)     |
| Worker crashes mid-task                            | replace worker; reject task; resume drain             |
| `close()` during work                             | wait for in-flight; reject queued                      |
| Cancellation                                       | post abort message to worker (cooperative)             |

**Constraints**
- Spawn workers UP FRONT (warm pool); cold start ~30ms.
- Map `taskId → {resolve, reject}` for correlation.
- Replace crashed workers; track free list.
- Workers are for CPU; light I/O = use event loop directly.

---

## 2. Plain-English restatement

Pre-spawn N worker threads. Each task is enqueued; a free worker picks it up. Each task has an ID; results route back via map. On crash, replace worker, reject pending. The whole point: avoid the ~30ms cold start per task.

---

## 3. Why this matters in interviews

The follow-up to "use `worker_threads`." Tests pool design, task correlation, crash recovery, when NOT to use workers (light I/O is fine on event loop).

---

## 4. Mental model

```
   ┌──────────────────────────────────────┐
   │ workers: [W1, W2, ..., WN]            │  pre-spawned, warm
   │ idle: [W1, W3, W5]                     │  free workers
   │ queue: [{task, resolve, reject}]      │  pending tasks
   │ pending: Map<taskId, {resolve, reject}>│  in-flight tasks
   └──────────────────────────────────────┘

   run(input):
     id = nextId++
     return Promise → pending.set(id, {resolve, reject})
     if idle.length: dispatch immediately
     else queue.push

   _drain():
     while idle.length && queue.length:
       w = idle.pop()
       task = queue.shift()
       w._taskId = task.id
       w.postMessage({id: task.id, input})

   onMessage(w, {id, result, error}):
     pending.get(id) → resolve/reject
     pending.delete(id)
     idle.push(w)
     _drain()

   onCrash(w):
     replace worker; reject any in-flight task on it.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why spawn workers up-front instead of on first request?
> 2. What happens if a worker crashes mid-task?
> 3. When is the event loop ALONE better than a worker pool?

---

## 6. Brute force — walked through

### Wrong attempt 1: spawn per task
~30ms cold start × N = wasted time.

### Wrong attempt 2: no taskId correlation
Worker A's result delivered to Worker B's caller.

### Wrong attempt 3: no crash recovery
Crashed worker leaves task hanging forever.

---

## 7. The unlocking insight

> **Pre-spawn warm workers + idle list + queue + taskId map. On each `run`: assign ID, push to queue, drain. On `onMessage`: look up pending by ID, resolve, free worker, drain. On crash: replace worker, reject in-flight.**

Three properties:

1. **Warm pool** — eliminates cold start.
2. **TaskId correlation** — `pending: Map<id, callbacks>`.
3. **Crash recovery** — replace + reject in-flight.

---

## 8. Solution (annotated)

```js
const { Worker } = require('node:worker_threads');
const os = require('node:os');

class WorkerPool {
  constructor(workerScript, size = os.cpus().length) {
    this.workerScript = workerScript;
    this.workers = [];
    this.idle = [];
    this.queue = [];
    this.pending = new Map();
    this.nextId = 1;
    for (let i = 0; i < size; i++) this._spawn();                     // step 1: warm pool
  }

  _spawn() {
    const w = new Worker(this.workerScript);
    w.on('message', ({ id, result, error }) => this._onResult(w, id, result, error));
    w.on('error', (err) => this._onCrash(w, err));
    w.on('exit', (code) => { if (code !== 0) this._onCrash(w, new Error(`exit ${code}`)); });
    this.workers.push(w);
    this.idle.push(w);
  }

  run(input) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      this.pending.set(id, { resolve, reject });                       // step 2: correlation
      this.queue.push({ id, input });
      this._drain();
    });
  }

  _drain() {
    while (this.idle.length && this.queue.length) {
      const w = this.idle.pop();
      const task = this.queue.shift();
      w._taskId = task.id;
      w.postMessage({ id: task.id, input: task.input });                // step 3: dispatch
    }
  }

  _onResult(w, id, result, error) {
    const pending = this.pending.get(id);
    if (pending) {
      this.pending.delete(id);
      error ? pending.reject(error) : pending.resolve(result);
    }
    w._taskId = null;
    this.idle.push(w);
    this._drain();
  }

  _onCrash(w, err) {                                                   // step 4: crash recovery
    const idx = this.workers.indexOf(w);
    if (idx >= 0) this.workers.splice(idx, 1);
    if (w._taskId != null) {
      const pending = this.pending.get(w._taskId);
      if (pending) { this.pending.delete(w._taskId); pending.reject(err); }
    }
    this._spawn();                                                      // replace
  }

  async close() {
    await Promise.all(this.workers.map((w) => w.terminate()));
  }
}
```

**Try it yourself**

```js
// worker.js
const { parentPort } = require('node:worker_threads');
parentPort.on('message', ({ id, input }) => {
  try {
    const result = expensiveCompute(input);
    parentPort.postMessage({ id, result });
  } catch (error) {
    parentPort.postMessage({ id, error: error.message });
  }
});

// main.js
const pool = new WorkerPool('./worker.js', 4);
const results = await Promise.all(items.map((i) => pool.run(i)));
await pool.close();
```

---

## 9. Step-by-step dry run

```
4 workers, 10 tasks:

t=0    constructor: spawn 4 workers (each ~20ms cold start, parallel)
       idle=[W1, W2, W3, W4]; queue=[]
t=20   warm pool ready.
       run × 10 → queue=[T1..T10]; pending size 10
       _drain: idle.pop() × 4 → dispatch T1..T4. idle=[].
       queue=[T5..T10].
t=80   W1 done → onResult → pending.delete(T1.id); idle=[W1].
       _drain → dispatch T5 to W1. idle=[].
       queue=[T6..T10].
...
t=180  all 10 done. idle=[W1,W2,W3,W4]; queue=[]; pending=size 0.

Crash scenario:
W2 mid-T2 crashes → onCrash(W2):
  workers.splice(W2 out).
  W2._taskId = T2.id → reject T2's Promise.
  _spawn() new worker W5; idle.push(W5).
  _drain → dispatch next queued task.
```

---

## 10. Common confusion + traps

1. **Spawn per request** — kills perf.
2. **No taskId correlation** — results delivered to wrong caller.
3. **No crash recovery** — task hangs forever.
4. **`postMessage` huge data** — copies; use transferList or SAB.
5. **Workers for I/O** — pointless; event loop handles I/O natively.
6. **Forgetting to terminate on close** — process hangs at exit.
7. **No idle list** — must scan workers to find free.

---

## 11. Senior follow-ups & variants

### Variant 1 — Piscina
Production: auto-recycle on crash, backpressure, abort signal, worker reuse limits.

### Variant 2 — AbortSignal cancellation
Post `{ type: 'abort', id }` to worker; worker checks periodically and exits early.

### Variant 3 — Backpressure
Bound `queue.length`; reject `run` when full.

### Variant 4 — Priority queue input
Sort by priority; high-priority tasks jump the queue.

### Variant 5 — `SharedArrayBuffer` for in-out
Avoid `postMessage` overhead; share memory directly.

### Variant 6 — Cluster vs worker_threads
Cluster forks processes (OS isolation); workers share process (cheaper, shared memory).

---

## 12. How to think aloud

> "Pre-spawn N workers at construction — eliminates ~30ms cold start. `run(input)` assigns taskId, pushes to queue, drains. Dispatch posts `{id, input}` to a free worker; result `onMessage` looks up taskId in pending map, resolves Promise, frees worker, re-drains. Crash recovery: replace worker, reject in-flight task. Production: Piscina has all this plus backpressure, abort, recycle limits. When NOT to pool: light I/O — event loop alone handles thousands of concurrent fetches better than 8 workers each waiting on one. Trap: spawn-per-request; no taskId correlation; no crash recovery; postMessage huge data."

---

## 13. 60-second revision

> - **Warm pool** of N pre-spawned workers.
> - **Idle list** + **queue** + **pending Map<id, {resolve, reject}>**.
> - **`run(input)`** queues with new id; `_drain` dispatches to free worker.
> - **`onMessage`** looks up id, resolves, frees worker, re-drains.
> - **Crash recovery:** replace worker, reject in-flight task.
> - **`close()`** terminates all workers.
> - **Production:** Piscina (recycling, backpressure, abort).
> - **Trap:** spawn-per-request; missing correlation; no crash recovery; pool for I/O.

---

**Related:** [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) · [`10-machine-coding-patterns/async-pool.md`](../10-machine-coding-patterns/async-pool.md) · [`10-machine-coding-patterns/async-semaphore.md`](../10-machine-coding-patterns/async-semaphore.md) · [postmessage-roundtrip.md](./postmessage-roundtrip.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
