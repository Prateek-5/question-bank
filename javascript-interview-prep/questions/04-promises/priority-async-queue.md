# Concurrency-limited queue with priority

## Source
- Senior backend system design / machine coding question — appears at FAANG, fintech, infra-heavy startups.
- Real-world: job queues (Bull, BullMQ), background processors, fetch schedulers, rate-limited API clients.
- Generalizes `promise-pool` (no priority) by adding ordering.

## Why this question matters in interviews
This is the **boss-level** version of `Promise.all` / promise pool. It tests four things at once: (1) **concurrency limiting** via a counter, (2) **priority scheduling** via a min/max-heap, (3) **deferred Promise** pattern (resolving from outside the constructor), and (4) **backpressure design** (what happens when the queue fills up). Backend engineers see this exact shape every time they build a job runner, an outbound webhook dispatcher, or a rate-limited HTTP client. Senior interviewers use it to probe data-structure literacy alongside async fluency.

## Concepts involved

### Syntax to lock in
```js
const queue = new PriorityQueue({ concurrency: 3 });
const result = await queue.add(() => fetch('/api/...'), { priority: 5 });
// Higher priority runs first; max `concurrency` tasks run in parallel.
```

### Runtime / engine behavior
- **Min-heap** (or max-heap) of waiting tasks. Each task stores: `{ priority, task, resolve, reject }`. Higher priority pops first (max-heap) — you can also use a min-heap with negated priority.
- **In-flight counter** tracks running tasks. When `< concurrency` AND heap non-empty → pop and run.
- Each `add` returns a Promise. We store its `resolve`/`reject` so we can settle from outside the constructor when the task eventually completes — this is the **deferred** pattern.
- On task completion (success or failure), decrement counter and pull next from heap.

### Edge cases (interview traps)
1. **Task throws synchronously** — wrap `task()` in `Promise.resolve().then(task)` or `try { await task() }` to convert sync throws to rejections.
2. **Empty queue, idle workers** — when heap is empty and a new `add` comes in, immediately try to schedule.
3. **All tasks at same priority** — should fall back to FIFO. Heap with `(priority, insertionOrder)` tuple as key preserves FIFO among ties.
4. **`drain()` / `idle()` API** — common follow-up: "let me await the queue going idle." Track waiters and resolve them when in-flight=0 AND heap is empty.
5. **`size` / `pending` API** — return heap size and in-flight count separately.
6. **Cancellation** — adding a cancel token per task is a senior follow-up. Tasks not yet started can be evicted from the heap.
7. **Memory leak** — if a task is added and the queue is never drained, the closure retains task references forever.

## Brute force approach
"Sort the array of tasks by priority and run with `asyncMapBounded`." Doesn't handle **dynamic** additions — new tasks added later need to interleave by priority, not append to the end. Drop this; you need an actual priority queue.

## Optimal approach
Min/max-heap for tasks, integer counter for in-flight. `add(task, { priority })` pushes a `{ priority, task, resolve, reject }` entry onto the heap and triggers `_next()`. `_next()` pops if `inFlight < concurrency` and the heap is non-empty, runs the task, attaches `.then`/`.catch` to settle the per-task promise, and on completion calls `_next()` again. Use a tie-breaker (insertion counter) for FIFO among same priorities.

## Solution (JavaScript)

```js
// Minimal binary max-heap (priority descending)
class MaxHeap {
  constructor() { this.data = []; }
  size() { return this.data.length; }
  push(item) {
    this.data.push(item);
    this._siftUp(this.data.length - 1);
  }
  pop() {
    if (this.data.length === 0) return undefined;
    const top = this.data[0];
    const last = this.data.pop();
    if (this.data.length) {
      this.data[0] = last;
      this._siftDown(0);
    }
    return top;
  }
  // Tuple compare: priority desc, then insertion order asc (FIFO among ties)
  _gt(a, b) {
    return a.priority !== b.priority ? a.priority > b.priority : a.seq < b.seq;
  }
  _siftUp(i) {
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this._gt(this.data[i], this.data[parent])) {
        [this.data[i], this.data[parent]] = [this.data[parent], this.data[i]];
        i = parent;
      } else break;
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
      [this.data[i], this.data[best]] = [this.data[best], this.data[i]];
      i = best;
    }
  }
}

class PriorityAsyncQueue {
  constructor({ concurrency = 1 } = {}) {
    this.concurrency = concurrency;
    this.inFlight = 0;
    this.heap = new MaxHeap();
    this.seq = 0;
    this.idleWaiters = [];
  }

  add(task, { priority = 0 } = {}) {
    return new Promise((resolve, reject) => {
      this.heap.push({ priority, seq: this.seq++, task, resolve, reject });
      this._next();
    });
  }

  async _next() {
    if (this.inFlight >= this.concurrency) return;
    const entry = this.heap.pop();
    if (!entry) {
      if (this.inFlight === 0) {
        this.idleWaiters.forEach((r) => r());
        this.idleWaiters = [];
      }
      return;
    }
    this.inFlight += 1;
    try {
      const value = await entry.task();
      entry.resolve(value);
    } catch (err) {
      entry.reject(err);
    } finally {
      this.inFlight -= 1;
      this._next();
    }
  }

  size() { return this.heap.size(); }
  pending() { return this.inFlight; }
  onIdle() {
    if (this.inFlight === 0 && this.heap.size() === 0) return Promise.resolve();
    return new Promise((resolve) => this.idleWaiters.push(resolve));
  }
}
```

## Step-by-step dry run

Input:
```js
const q = new PriorityAsyncQueue({ concurrency: 2 });
const job = (label, ms) => () => new Promise(r => setTimeout(() => { console.log('done', label); r(label); }, ms));

q.add(job('A-low', 100), { priority: 1 });
q.add(job('B-low', 100), { priority: 1 });
q.add(job('C-high', 50), { priority: 10 });   // arrives 3rd but priority 10
q.add(job('D-low', 30), { priority: 1 });
```

Trace:
- **t=0** — `add(A-low)`: heap=[A(p=1,seq=0)]. `_next()` → inFlight=0<2, pop A, inFlight=1, start A.
- **t=0** — `add(B-low)`: heap=[B(p=1,seq=1)]. `_next()` → inFlight=1<2, pop B, inFlight=2, start B.
- **t=0** — `add(C-high)`: heap=[C(p=10,seq=2)]. `_next()` → inFlight=2, NOT < concurrency, return.
- **t=0** — `add(D-low)`: heap pushes D(p=1,seq=3). Heap now [C, D] (C has higher priority). `_next()` → still 2 in flight, return.
- **t=100** — A finishes (`done A-low`), resolves with 'A-low'. inFlight=1. `_next()` pops C (highest priority), inFlight=2, start C.
- **t=100** — B finishes (`done B-low`). inFlight=1. `_next()` pops D, inFlight=2, start D.
- **t=130** — D finishes (`done D-low`). inFlight=1. `_next()` heap empty, no idle waiters.
- **t=150** — C finishes (`done C-high`). inFlight=0. `_next()` heap empty → resolve idle waiters (none) and return.

Output:
```
done A-low
done B-low
done D-low
done C-high
```

Even though C had highest priority, it only ran after A or B freed a slot. **Priority controls who runs next, not preemption.** Real schedulers behave this way too.

## Important takeaways

**Syntax to memorize**
- `{ priority, seq, task, resolve, reject }` is the canonical heap-entry shape.
- The **deferred pattern**: `new Promise((resolve, reject) => { /* store both, settle later */ })`.
- `try/await/catch/finally` around the task with `_next()` in `finally` — guarantees the slot is freed even on throw.

**Patterns to reuse**
- "Heap of pending work + counter of in-flight + dispatcher loop" is the **scheduler pattern** — same shape used in OS process schedulers, browser rendering pipelines, BullMQ workers.
- The deferred pattern is foundational; see `deferred-with-resolvers.md`.

**Common mistakes**
- Forgetting tie-breaker → tasks at same priority drift to unpredictable order. Use `seq`.
- Forgetting to call `_next()` in `finally` → on throw, a slot is forever consumed (deadlock).
- Synchronous throw not caught — `task()` might throw before returning a promise. Wrap accordingly.
- No backpressure — if `add()` is called faster than tasks complete, the heap grows unbounded. Production version exposes `maxSize` or returns a rejected promise when full.
- Confusing this with `Promise.all` — `all` is a *snapshot* of N existing promises; this queue accepts **dynamic** additions.

**Related questions**
- `min-heap-priority-queue.md` (the heap data structure standalone)
- `promise-pool.md` (FIFO concurrency-limited queue)
- `retry-with-backoff.md` (often combined with this queue for job retries)
- `deferred-with-resolvers.md` (the underlying primitive)

## Variants

1. **`onIdle()` / `drain()` API** — already shown above. Common follow-up.
2. **`pause()` / `resume()`** — set a flag that prevents `_next()` from popping. Real-world batch processors need this.
3. **Cancellation** — accept an AbortSignal per task; remove from heap if not yet started, abort if running.
4. **Per-key rate limit** — extension: tasks tagged by key, enforce max-N-per-key concurrency. Useful for per-customer fairness.
5. **Multi-queue weighted scheduling** — round-robin across priority bands instead of strict priority. Prevents starvation of low-priority work.

## Revision notes

> **PriorityAsyncQueue — 60 second recap**
> - Max-heap of `{ priority, seq, task, resolve, reject }`. `seq` ties → FIFO.
> - `inFlight < concurrency` AND heap non-empty → pop + run.
> - Each `add()` returns a Promise via the **deferred pattern**.
> - Settle per-task in `try/catch`; decrement `inFlight` and call `_next()` in `finally`.
> - Expose `size`, `pending`, `onIdle`.
> - **Trap:** no `_next()` in finally on throw → permanent slot loss → eventual deadlock.
