# Implement `PriorityAsyncQueue` — concurrency-limited queue with priority scheduling

> **Difficulty:** Medium-Hard   |   **Time:** ~30 min   |   **Prereqs:** [promise-pool.md](./promise-pool.md), [deferred-with-resolvers.md](./deferred-with-resolvers.md), [`10-machine-coding-patterns/min-heap-priority-queue.md`](../10-machine-coding-patterns/min-heap-priority-queue.md)
>
> **Source:** FAANG, fintech, infra-heavy startup machine coding question. Real-world: BullMQ, fetch schedulers, rate-limited API clients.

---

## 1. Problem statement

**Signature**
```ts
class PriorityAsyncQueue {
  constructor(opts?: { concurrency?: number });
  add<T>(task: () => Promise<T>, opts?: { priority?: number }): Promise<T>;
  size(): number;       // pending tasks
  pending(): number;    // currently running
  onIdle(): Promise<void>;
}
```

**Input / Output examples**

| Setup                                                                   | Behaviour                                                |
|--------------------------------------------------------------------------|-----------------------------------------------------------|
| `q = new PriorityAsyncQueue({concurrency: 2})`                          | up to 2 tasks run in parallel                            |
| `q.add(t1, {priority: 1}); q.add(t2, {priority: 5})`                    | t2 runs first (higher priority pops first)               |
| Same priority, added in order                                            | FIFO among ties (insertion-order tie-breaker)            |
| Dynamic additions while running                                          | new high-priority tasks interleave correctly             |
| `q.add(task)` after a long batch                                         | resolves with task's value via deferred pattern          |
| `await q.onIdle()`                                                       | resolves when in-flight === 0 AND heap is empty          |

**Constraints**
- Max `concurrency` tasks in flight at any time.
- Higher priority runs first; same priority falls back to FIFO.
- Each `add()` returns a per-task Promise (deferred pattern).
- Empty heap + idle workers → resolve `onIdle()` waiters.
- Slot must be freed in `finally` so throws don't leak in-flight count.

---

## 2. Plain-English restatement

Build a job queue with three controls: a **concurrency cap** (only N tasks running at once), a **priority order** (higher priority runs next), and a **dynamic admission** model (new jobs can be added mid-flight). When you `add` a task, you get back a Promise that resolves with the task's result once it actually runs.

Internally: a heap of waiting tasks, a counter of running tasks, a dispatcher loop that pops from the heap whenever a slot is free. Each task stores its `resolve`/`reject` so the per-task Promise can be settled from outside the constructor.

---

## 3. Why this matters in interviews

This is the **boss-level** version of `Promise.all` / promise pool. It tests four things at once: (1) **concurrency limiting** via a counter, (2) **priority scheduling** via a min/max-heap, (3) **deferred Promise** pattern (resolving from outside the constructor), and (4) **backpressure design** (what happens when the queue fills up). Backend engineers see this exact shape every time they build a job runner, an outbound webhook dispatcher, or a rate-limited HTTP client. Senior interviewers use it to probe data-structure literacy alongside async fluency.

---

## 4. Mental model

A **call center with priority customers**:

```
   ┌─ heap of waiting tasks (priority desc, then FIFO) ─┐
   │  [P=10 seq=2]  ← runs next when slot opens         │
   │  [P=5  seq=0]                                       │
   │  [P=1  seq=3]                                       │
   └────────────────────────────────────────────────────┘
                       │ pop when inFlight < concurrency
                       ▼
                ┌─ active workers ─┐
                │ task A running    │  inFlight = 2
                │ task B running    │
                └───────────────────┘
                       │ task done → finally → _next()
                       ▼
                  pop next from heap (or resolve onIdle)
```

**Key insight:** priority controls *who runs next*, not *who preempts*. A high-priority task added after low-priority tasks have started will wait for a slot to free. Real OS schedulers behave the same way (cooperative scheduling).

The **deferred pattern** (see [deferred-with-resolvers.md](./deferred-with-resolvers.md)) is the enabling primitive: `add` returns a Promise immediately, but its settlement happens later when the task eventually runs. We store `resolve`/`reject` in the heap entry.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With concurrency=2 and tasks A(p=1), B(p=1), C(p=10) added in that order at t=0, in what order do they finish?
> 2. If two tasks have the same priority, how should ties break? Why does ordering still matter?
> 3. If a task throws synchronously (not via rejected promise), does the slot leak? How do you prevent that?

---

## 6. Brute force — walked through

### Wrong attempt 1: sort then run with `asyncMapBounded`

```js
const sorted = tasks.sort((a, b) => b.priority - a.priority);
await asyncMapBounded(sorted, (t) => t.fn(), concurrency);
```

**Doesn't handle dynamic additions.** New tasks added after the queue starts running need to interleave by priority, not append. This is a static batch processor, not a queue.

### Wrong attempt 2: forget the FIFO tie-breaker

```js
class MinHeap {
  _gt(a, b) { return a.priority > b.priority; }
}
```

When two tasks have the same priority, heap comparison is undefined → order drift (depends on heap internals, may not be stable). For predictable behavior with equal priorities, fall back to insertion order. Use `(priority, seq)` tuple where `seq` is a monotonic counter.

### Wrong attempt 3: no `_next()` in `finally`

```js
async _next() {
  if (this.inFlight >= this.concurrency) return;
  const entry = this.heap.pop();
  if (!entry) return;
  this.inFlight += 1;
  try {
    const v = await entry.task();
    entry.resolve(v);
  } catch (err) {
    entry.reject(err);
  }
  // BUG: no finally → if catch's reject() throws, inFlight is never decremented
  this.inFlight -= 1;
  this._next();
}
```

The decrement-and-recurse must be in `finally`. Otherwise an unexpected throw (from a misbehaving subscriber to the rejection) can leak a slot, eventually deadlocking the queue.

### Wrong attempt 4: synchronous throw not wrapped

```js
const value = await entry.task();
// BUG: entry.task() can throw synchronously before returning a Promise
```

If `task` is `() => { throw new Error('bad'); }`, the throw isn't inside the `try` until *after* `task()` returns. `await` of an already-thrown exception doesn't catch it. Wrap with `await Promise.resolve().then(entry.task)` or always `try { value = await entry.task(); }`.

---

## 7. The unlocking insight

> **Max-heap of `{priority, seq, task, resolve, reject}` entries + in-flight counter + dispatcher loop. `add` pushes to heap and triggers `_next()`. `_next()` pops if `inFlight < concurrency`, runs task, decrements in `finally` and recurses to keep the queue flowing.**

Five mechanics:

1. **Heap with tuple key.** `(priority desc, seq asc)` — higher priority first; FIFO among ties. `seq` is a monotonic counter incremented on each `add`.

2. **In-flight counter.** Simple integer. Increment before running task, decrement in `finally`.

3. **Deferred per task.** `add(task)` returns `new Promise((resolve, reject) => { heap.push({task, resolve, reject, ...}); this._next(); })`. The heap entry carries the resolvers so we can settle the per-task promise once the task actually runs.

4. **`_next()` dispatcher.** Called after every state change (new add, task done). Pops if a slot is free; runs the task; decrements and recurses in `finally`. The `try/catch/finally` makes the recursion safe even on throw.

5. **`onIdle()` via waiters list.** Track callers awaiting "queue empty + no work running"; resolve them when `_next()` finds the heap empty and `inFlight === 0`.

**Senior bonus:** mention that real-world queues (BullMQ, Bull, p-queue, Sidekiq) build on this exact skeleton plus: persistence, retry policies, distributed lock for cross-process scheduling, rate-limit windows.

---

## 8. Solution (annotated)

```js
// Minimal max-heap with (priority, seq) tuple key — FIFO among ties
class MaxHeap {
  constructor() { this.data = []; }
  size() { return this.data.length; }
  push(item) { this.data.push(item); this._siftUp(this.data.length - 1); }
  pop() {
    if (!this.data.length) return undefined;
    const top = this.data[0];
    const last = this.data.pop();
    if (this.data.length) { this.data[0] = last; this._siftDown(0); }
    return top;
  }
  // Higher priority first; equal priority → lower seq first (FIFO)
  _gt(a, b) { return a.priority !== b.priority ? a.priority > b.priority : a.seq < b.seq; }
  _siftUp(i) {
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this._gt(this.data[i], this.data[p])) { [this.data[i], this.data[p]] = [this.data[p], this.data[i]]; i = p; }
      else break;
    }
  }
  _siftDown(i) {
    const n = this.data.length;
    while (true) {
      const l = 2 * i + 1, r = 2 * i + 2;
      let best = i;
      if (l < n && this._gt(this.data[l], this.data[best])) best = l;
      if (r < n && this._gt(this.data[r], this.data[best])) best = r;
      if (best === i) break;
      [this.data[i], this.data[best]] = [this.data[best], this.data[i]]; i = best;
    }
  }
}

class PriorityAsyncQueue {
  constructor({ concurrency = 1 } = {}) {
    this.concurrency = concurrency;
    this.inFlight = 0;
    this.heap = new MaxHeap();
    this.seq = 0;                                              // step 1: FIFO tie-breaker
    this.idleWaiters = [];
  }

  add(task, { priority = 0 } = {}) {
    return new Promise((resolve, reject) => {                  // step 2: deferred pattern
      this.heap.push({                                          //         entry carries resolvers
        priority,
        seq: this.seq++,
        task,
        resolve,
        reject,
      });
      this._next();                                             // step 3: try to dispatch
    });
  }

  async _next() {
    if (this.inFlight >= this.concurrency) return;              // step 4: respect concurrency
    const entry = this.heap.pop();
    if (!entry) {                                               // step 5: heap empty
      if (this.inFlight === 0) {                                //         and no work running → idle
        this.idleWaiters.forEach((r) => r());
        this.idleWaiters = [];
      }
      return;
    }
    this.inFlight += 1;                                         // step 6: take slot
    try {
      const value = await entry.task();                         // step 7: run task
      entry.resolve(value);                                     //         settle per-task promise
    } catch (err) {
      entry.reject(err);
    } finally {
      this.inFlight -= 1;                                       // step 8: free slot in FINALLY
      this._next();                                              //         dispatch next
    }
  }

  size() { return this.heap.size(); }                           // pending in heap
  pending() { return this.inFlight; }                            // currently running
  onIdle() {
    if (this.inFlight === 0 && this.heap.size() === 0) return Promise.resolve();
    return new Promise((resolve) => this.idleWaiters.push(resolve));
  }
}
```

**Try it yourself**

```js
const q = new PriorityAsyncQueue({ concurrency: 2 });
const job = (label, ms) => () =>
  new Promise((r) => setTimeout(() => { console.log('done', label); r(label); }, ms));

q.add(job('A-low', 100), { priority: 1 });
q.add(job('B-low', 100), { priority: 1 });
q.add(job('C-high', 50), { priority: 10 });   // higher priority
q.add(job('D-low', 30), { priority: 1 });

await q.onIdle();
console.log('all done');
```

Output:
```
done A-low      (t=100)
done B-low      (t=100)
done D-low      (t=130)
done C-high     (t=150)
all done
```

**C had highest priority, but only ran after A or B freed a slot.** Priority is not preemption.

---

## 9. Step-by-step dry run

Input:

```js
const q = new PriorityAsyncQueue({ concurrency: 2 });
q.add(job('A-low',  100), { priority: 1 });   // t=0
q.add(job('B-low',  100), { priority: 1 });   // t=0
q.add(job('C-high',  50), { priority: 10 });  // t=0
q.add(job('D-low',   30), { priority: 1 });   // t=0
```

Values-first trace:

| Time | Event                                          | `inFlight` | Heap (priority desc, seq asc) |
|------|------------------------------------------------|-------------|--------------------------------|
| 0    | `add(A, p=1)`: push A(p=1, seq=0); `_next()` → pop A, run | 1 | `[]`                |
| 0    | `add(B, p=1)`: push B(p=1, seq=1); `_next()` → pop B, run | 2 | `[]`                |
| 0    | `add(C, p=10)`: push C(p=10, seq=2); `_next()` → inFlight===2, return | 2 | `[C]`     |
| 0    | `add(D, p=1)`: push D(p=1, seq=3); `_next()` → still 2 in flight, return | 2 | `[C, D]` |
| 100  | A done; `_next()` → pop C (highest pri), run               | 2 | `[D]`                          |
| 100  | B done; `_next()` → pop D, run                              | 2 | `[]`                           |
| 130  | D done (30ms after start at t=100); `_next()` → heap empty, but inFlight>0 | 1 | `[]` |
| 150  | C done (50ms after start at t=100); `_next()` → heap empty, inFlight=0 → resolve idle waiters | 0 | `[]` |

Order of completion: A, B, D, C. Priority influenced who ran *after* slots opened, not who preempted.

---

## 10. Common confusion + traps

1. **No FIFO tie-breaker.** Same priority → undefined order. Use `(priority, seq)` tuple.

2. **No `_next()` in `finally`.** Throws leak a slot. Eventually deadlocks.

3. **Synchronous throw in task.** `entry.task()` may throw before returning. The `try { await entry.task(); }` catches it correctly because `await` of an already-thrown call doesn't bypass the try.

4. **No backpressure.** If `add` is called faster than tasks complete, the heap grows unbounded. Production: expose `maxSize` and reject new adds when full.

5. **Confusing this with `Promise.all`.** `all` is a snapshot of N existing promises; this queue accepts dynamic additions and reorders by priority.

6. **Priority isn't preemption.** A high-priority task added while a low-priority task is running waits for a slot. Real schedulers behave this way too.

7. **Memory leak.** Tasks added but never drained pin their closures. Always have a way to clear the queue or set max size.

8. **`onIdle` race.** If `add` happens between popping the last item and resolving idle waiters, the waiters resolve incorrectly. Check `inFlight === 0 && heap.size() === 0` *after* the task finishes (in `finally`), not before.

---

## 11. Senior follow-ups & variants

### Variant 1 — `pause()` / `resume()`

```js
pause() { this.paused = true; }
resume() { this.paused = false; this._next(); }

async _next() {
  if (this.paused || this.inFlight >= this.concurrency) return;
  // ... rest unchanged ...
}
```

Real-world batch processors need this for graceful shutdown.

### Variant 2 — Cancellation via AbortSignal

```js
add(task, { priority = 0, signal } = {}) {
  return new Promise((resolve, reject) => {
    const entry = { priority, seq: this.seq++, task, resolve, reject, signal };
    if (signal?.aborted) return reject(signal.reason);
    if (signal) signal.addEventListener('abort', () => {
      // remove from heap if not yet started
      const idx = this.heap.data.indexOf(entry);
      if (idx >= 0) {
        this.heap.data.splice(idx, 1);   // O(N); for big queues, mark-and-skip is better
        reject(signal.reason);
      }
      // if already running, signal is passed through to task and it handles abort
    });
    this.heap.push(entry);
    this._next();
  });
}
```

Cancel waiting tasks (remove from heap). Running tasks need to honor the signal themselves.

### Variant 3 — Per-key rate limit

Tag tasks by key; enforce max-N-per-key concurrency on top of global concurrency. Useful for per-customer fairness.

### Variant 4 — Multi-band weighted scheduling

Round-robin across priority bands instead of strict priority. Prevents starvation of low-priority work. Approach: maintain N FIFO queues by priority band; service them in a weighted round-robin schedule.

### Variant 5 — Persistent queue (BullMQ-style)

Back the heap with Redis sorted sets. Tasks survive process restarts. Distributed coordination via Lua scripts. Real production job runners.

### Variant 6 — Retry + priority adjustment

On task failure, re-add with lower priority (so retries don't starve fresh work). Cap retry count.

```js
async _runTask(entry) {
  try { entry.resolve(await entry.task()); }
  catch (err) {
    if (entry.retries < this.maxRetries) {
      entry.retries++;
      this.add(entry.task, { priority: entry.priority - 1 });   // lower priority on retry
    } else {
      entry.reject(err);
    }
  }
}
```

---

## 12. How to think aloud in the interview

> "Max-heap of `{priority, seq, task, resolve, reject}` + in-flight counter + dispatcher loop. `seq` is the FIFO tie-breaker so equal priorities preserve insertion order. `add` uses the deferred pattern: returns a Promise, pushes the entry with its resolvers onto the heap, triggers `_next()`. `_next()` pops if a slot's free, runs the task, decrements in `finally` and recurses. The `finally` is critical — throws can't leak slot count. `try { await entry.task(); }` catches sync throws too. `onIdle()` resolves when heap is empty AND `inFlight === 0`. For backpressure, add `maxSize` to reject `add()` when full. For cancellation, AbortSignal per task — remove from heap if waiting, signal-pass if running. Real-world job queues (BullMQ) extend this with persistence, retry policies, distributed locks."

---

## 13. 60-second revision

> - **Heap of `{priority, seq, task, resolve, reject}` + in-flight counter.**
> - **`seq` for FIFO tie-breaker** among equal priorities.
> - **`add` returns Promise via deferred pattern.** Entry stores its `resolve`/`reject`.
> - **`_next()` dispatcher:** if `inFlight < concurrency` and heap non-empty → pop and run.
> - **`finally` to decrement and recurse.** Throws don't leak slot count.
> - **`onIdle()` waiters resolve when heap empty AND `inFlight === 0`**.
> - **Priority is not preemption** — high-priority task added mid-flight waits for a slot.
> - **Family:** BullMQ, p-queue, Bull, Sidekiq, OS schedulers.
> - **Trap:** no FIFO tie-breaker; no `_next()` in finally; synchronous throw not wrapped; no backpressure.

---

**Related:** [promise-pool.md](./promise-pool.md) · [deferred-with-resolvers.md](./deferred-with-resolvers.md) · [async-mutex.md](./async-mutex.md) · [retry-with-backoff.md](./retry-with-backoff.md) · [`10-machine-coding-patterns/min-heap-priority-queue.md`](../10-machine-coding-patterns/min-heap-priority-queue.md) · [`10-machine-coding-patterns/rate-limiter-token-bucket.md`](../10-machine-coding-patterns/rate-limiter-token-bucket.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
