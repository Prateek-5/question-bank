# Worker Pool — Reusable Worker Threads with Task Queue

## Source / Origin
- Node `worker_threads`; browser `Worker`; libraries like `piscina`, `workerpool`.
- Asked at: Cloudflare, Stripe, Atlassian, AWS.
- Concept reference: `concepts/event-loop.md`, sibling `postmessage-roundtrip.md`, `10-machine-coding-patterns/async-pool.md`.

## Why this question matters in interviews
Spinning up a Worker per task is expensive — boot time, memory, V8 init. A pool of N workers servicing a shared queue is the canonical solution. Senior bar: (1) you understand task → worker assignment, (2) you handle worker crashes (replace and replay), (3) you support task cancellation, (4) you can articulate when *not* to use workers (light I/O — the event loop alone handles thousands of concurrent fetches better than 8 workers each waiting on one).

## Concepts involved

### Syntax to lock in
```js
// Node: pool.js
import { Worker } from 'worker_threads';
import { fileURLToPath } from 'url';

class WorkerPool {
  constructor(workerScript, size = navigator.hardwareConcurrency || 4) {
    this.workerScript = workerScript;
    this.size = size;
    this.workers = [];
    this.idle = [];
    this.queue = [];
    this.nextId = 1;
    this.pending = new Map();   // taskId → {resolve, reject}
    for (let i = 0; i < size; i++) this._spawn();
  }

  _spawn() {
    const w = new Worker(this.workerScript);
    w.on('message', ({ id, result, error }) => {
      const slot = this.pending.get(id);
      if (!slot) return;
      this.pending.delete(id);
      if (error) slot.reject(Object.assign(new Error(error.message), error));
      else slot.resolve(result);
      this.idle.push(w);
      this._drain();
    });
    w.on('error', (err) => this._replace(w, err));
    w.on('exit', (code) => { if (code !== 0) this._replace(w, new Error('Worker exited ' + code)); });
    this.workers.push(w);
    this.idle.push(w);
  }

  _replace(deadWorker, err) {
    // reject any pending tasks assigned to this worker
    for (const [id, slot] of this.pending.entries()) {
      if (slot.worker === deadWorker) { slot.reject(err); this.pending.delete(id); }
    }
    this.workers = this.workers.filter(w => w !== deadWorker);
    this.idle = this.idle.filter(w => w !== deadWorker);
    this._spawn();
  }

  run(method, args, { transfer = [] } = {}) {
    return new Promise((resolve, reject) => {
      this.queue.push({ method, args, transfer, resolve, reject });
      this._drain();
    });
  }

  _drain() {
    while (this.idle.length && this.queue.length) {
      const w = this.idle.shift();
      const t = this.queue.shift();
      const id = this.nextId++;
      this.pending.set(id, { resolve: t.resolve, reject: t.reject, worker: w });
      w.postMessage({ id, method: t.method, args: t.args }, t.transfer);
    }
  }

  async terminate() {
    await Promise.all(this.workers.map(w => w.terminate()));
  }
}
```

```js
// worker.js — RPC server (see postmessage-roundtrip.md for full version)
const handlers = {
  hashPassword: ({ password, salt }) => bcrypt.hashSync(password, salt),
  resizeImage: async ({ buf, width }) => sharp(buf).resize(width).toBuffer(),
};
parentPort.on('message', async ({ id, method, args }) => {
  try { parentPort.postMessage({ id, result: await handlers[method](args) }); }
  catch (err) { parentPort.postMessage({ id, error: { message: err.message } }); }
});
```

### Edge cases / interview traps
1. **Workers should not be CPU-idle but I/O-bound.** If your tasks are fetch-only, the main event loop handles thousands more efficiently than 8 workers blocking on I/O.
2. **Worker crash** — pending tasks on that worker leak unless you reject them in the `exit`/`error` handler.
3. **Replay** — should a crashed task auto-retry on a new worker? Sometimes yes (idempotent), sometimes no.
4. **Backpressure** — unbounded queue grows forever under heavy load. Bound queue size and either drop or reject `run()` when full.
5. **Cancellation** — pre-dispatch: splice from queue. Mid-dispatch: send abort message; worker checks; honors if possible.
6. **Worker boot time.** ~20-100ms in Node. Don't spawn-per-task.
7. **Transferables for big payloads** — `ArrayBuffer` zero-copy across thread.
8. **Pool sizing** — `hardwareConcurrency` for CPU work; can be higher for I/O-heavy tasks within the worker.

## Mental Model

A **call center** with N agents:

```
   tasks → queue   ▶  agent1 ▶ result
                    ▶  agent2 ▶ result
                    ▶  agent3 ▶ result
                    ▶  agent4 ▶ result
                          ↓
                   when free, agent picks next from queue
                          ↓
                   if agent has a heart attack (crash) → replace with new agent
                   reject any pending call assigned to dead agent
```

Pool keeps `idle` (free agents) and `queue` (waiting tasks). `_drain` runs whenever either changes — match free agent to head of queue.

## Why interviewers care

- **CPU-bound vs I/O-bound** distinction — senior intuition.
- **Failure-handling discipline** — crashes, replays, leak prevention.
- **Production patterns** — every Node service with image processing, password hashing, or compression uses this.

## Common beginner confusion

- **"Use workers for everything async."** No — JS already handles I/O concurrency on one thread. Workers are for **CPU-bound** work (encryption, image resize, parsing).
- **"More workers = faster."** Beyond `hardwareConcurrency`, you context-switch more than you compute. Some workloads (I/O inside worker) benefit from oversubscription.
- **"Pool restart is automatic."** No — you write the replace logic.
- **"Transferables are slower than clone."** Faster — they're zero-copy; the original is neutered.
- **"Pool tasks share memory."** They don't, unless you use `SharedArrayBuffer` + Atomics (separate question).

## Brute force approach

```js
// Spawn per task — boot overhead dwarfs work
async function hash(password) {
  const w = new Worker('./worker.js');
  return new Promise((res, rej) => {
    w.on('message', (r) => { res(r); w.terminate(); });
    w.postMessage({ method: 'hashPassword', args: { password } });
  });
}
```

20-100ms boot for a 30ms hash = 70ms overhead per call.

## Optimal approach

`WorkerPool` of N workers servicing a shared queue. `run(method, args)` returns a promise. Pool handles task dispatch, worker lifecycle, and crash recovery.

## Solution (JavaScript)

See "Syntax to lock in" above. Usage:

```js
import { WorkerPool } from './worker-pool.js';
import { fileURLToPath } from 'url';

const pool = new WorkerPool(fileURLToPath(new URL('./worker.js', import.meta.url)), 8);

// CPU-bound API endpoint
app.post('/hash', async (req, res) => {
  const hashed = await pool.run('hashPassword', { password: req.body.password, salt: 10 });
  res.json({ hashed });
});

// Backpressure: bound queue
class BoundedPool extends WorkerPool {
  constructor(script, size, maxQueue) { super(script, size); this.maxQueue = maxQueue; }
  run(...args) {
    if (this.queue.length >= this.maxQueue) return Promise.reject(new Error('Pool overloaded'));
    return super.run(...args);
  }
}

// Cancellation
const ac = new AbortController();
const promise = pool.run('resizeImage', { buf, width: 100 });
ac.signal.addEventListener('abort', () => {
  // ... pool needs to know taskId to send abort to worker
  pool.cancel(taskId);
});
```

## Step-by-step dry run

`size=2`, 5 tasks submitted at t=0:

```
t=0    pool: idle=[W1, W2], queue=[]
       run(t1) → queue=[t1]; _drain → W1 picks t1; idle=[W2], queue=[]
       run(t2) → queue=[t2]; _drain → W2 picks t2; idle=[], queue=[]
       run(t3) → queue=[t3]; _drain (idle empty) → no-op
       run(t4) → queue=[t3,t4]
       run(t5) → queue=[t3,t4,t5]

t=100  W1 done with t1 → onMessage → resolve t1 promise; W1 → idle
       _drain → W1 picks t3; idle=[], queue=[t4,t5]

t=150  W2 done with t2 → resolve; W2 → idle
       _drain → W2 picks t4; queue=[t5]

t=200  W1 done with t3 → resolve; idle=[W1]; pick t5; queue=[]
t=250  W2 done with t4 → resolve
t=300  W1 done with t5 → resolve

(if W1 crashes at t=200: exit handler → reject t3's promise; _replace spawns W1'; idle=[W1', W2])
```

## How to think aloud in the interview

> "Pool of N workers (typically `os.cpus().length`). Idle list + task queue + pending Map. On submit, push to queue + `_drain`. `_drain` matches idle to queue. Each task is a `postMessage({id, method, args})`; reply matches by id. Worker crash handler: reject pending tasks for that worker, respawn, refill idle. Use only for CPU-bound work — I/O is already concurrent on one thread. Backpressure: bounded queue. Transferables for big payloads. Cancellation by ID — pre-dispatch splice or post-dispatch abort message."

## Important takeaways

- **CPU-bound only.** I/O doesn't need workers.
- **`hardwareConcurrency`** as default size.
- **Idle list + queue + pending Map** is the pattern.
- **Crash recovery** — reject pending, respawn.
- **Backpressure** — bound the queue.
- **Transferables** for big payloads.
- **Boot time matters** — never spawn-per-task.

## Variants

- **`piscina`** (Node) — production-grade worker pool with abort, queue limits, idle timeout.
- **Shared queue via SharedArrayBuffer** — high-throughput lock-free queue.
- **Dedicated worker per route** — when a worker holds expensive state (ML model in memory).
- **Worker scaling** — grow/shrink pool based on queue length.
- **Browser-side pool** — same pattern; `new Worker(url)`; `navigator.hardwareConcurrency`.

## Revision notes

```
WorkerPool:
  workers + idle + queue + pending Map(id → {resolve,reject,worker})
  run(method, args):
    queue.push; _drain()
  _drain():
    while (idle.length && queue.length):
      w = idle.shift(); t = queue.shift()
      id = next; pending.set; w.postMessage({id, method, args}, transfer)
  worker.on('message', {id, result|error}):
    resolve/reject pending[id]; idle.push(worker); _drain()
  worker.on('error'|'exit'):
    reject pending tasks for that worker; respawn; idle.push(new worker)
  
  CPU-BOUND only
  size = hardwareConcurrency
  boot ~20-100ms — pool, don't spawn-per-task
  backpressure: bounded queue
  transferables for big payloads
```
