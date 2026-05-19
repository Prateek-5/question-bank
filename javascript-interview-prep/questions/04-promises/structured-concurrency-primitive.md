# Implement a `TaskGroup` — structured concurrency primitive

> **Difficulty:** Hard   |   **Time:** ~35 min   |   **Prereqs:** [abortcontroller-fanout.md](./abortcontroller-fanout.md), [promise-all-polyfill.md](./promise-all-polyfill.md), [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md)
>
> **Source:** Nathaniel Smith's "Notes on structured concurrency" (2018); Python `asyncio.TaskGroup`, Kotlin `coroutineScope`, Swift `withTaskGroup`.

---

## 1. Problem statement

**Signature**
```ts
class TaskGroup {
  spawn<T>(fn: (signal: AbortSignal) => Promise<T>): Promise<T>;
  run(body: (spawn: TaskGroup['spawn']) => Promise<void>): Promise<void>;
}
```

**Input / Output examples**

| Setup                                                                   | Behaviour                                              |
|--------------------------------------------------------------------------|---------------------------------------------------------|
| 3 children spawn; all succeed                                           | `run` returns when all 3 done                          |
| Child B throws at t=20                                                  | `ac.abort(B.err)` → A and C receive `AbortError`; `run` rejects with B's error |
| Multiple real errors (not abort)                                        | `run` rejects with `AggregateError`                    |
| Body throws synchronously                                                | siblings still awaited via `Promise.allSettled` in finally |
| Spawn after body returns                                                 | throws `TaskGroupClosed`                              |

**Constraints**
- **Children's lifetime bounded by scope** — `run` returns only after all children settle.
- First real error (not abort) cancels siblings via shared AbortSignal.
- Multiple real errors collected into `AggregateError`.
- `AbortError` filtered from collected errors (cancellation isn't failure).
- `Promise.allSettled` in `finally` so scope can't exit with live children.

---

## 2. Plain-English restatement

`Promise.all` leaks: if one task throws, the others keep running in the background. A `TaskGroup` (also called a "nursery") binds the lifetime of async tasks to a syntactic scope — when the scope exits, every spawned child is guaranteed to be done (resolved, rejected, or cancelled). First error cancels siblings via a shared `AbortController`. Multiple real errors get collected into `AggregateError`.

---

## 3. Why this matters in interviews

JavaScript's stock async tools leak. `Promise.all([a(), b()])` — if `a` throws, `b` continues running in the background, possibly touching state that's already torn down. Errors get swallowed. Cancellation is ad-hoc. Structured concurrency **binds the lifetime of async tasks to a syntactic scope** — when the scope exits, every child task is guaranteed to be done. Senior bar: implement `TaskGroup` in 30 lines and name the principle ("no thread escapes its function").

---

## 4. Mental model

A **rule: no thread escapes its function**:

```
   ┌─ TaskGroup scope ────────────────────────────────┐
   │  spawn(A)  → child A running                     │
   │  spawn(B)  → child B running                     │
   │  spawn(C)  → child C running                     │
   │                                                  │
   │  if A throws:                                    │
   │     ac.abort(err)                                │
   │     B, C receive AbortSignal → reject            │
   │                                                  │
   │  AT scope exit: A, B, C ALL settled              │
   │  (no leaked background tasks)                    │
   └──────────────────────────────────────────────────┘

   vs Promise.all:
     Promise.all([fetchA(), fetchB(), fetchC()])
       fetchA throws at t=5 → Promise.all rejects → caller continues
       fetchB, fetchC STILL RUNNING IN BACKGROUND   ← leak
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `Promise.all([a(), b(), c()])`, if `a` throws at t=5 and `b`, `c` take 60s, when do `b` and `c` actually stop?
> 2. If two siblings throw real errors simultaneously, which error reaches the caller?
> 3. Why filter `AbortError` from collected errors?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Promise.all`
Siblings keep running after first reject. Leak.

### Wrong attempt 2: `Promise.allSettled` only
No cancellation — slow siblings still run to completion. Caller waits longer than needed.

### Wrong attempt 3: forget to wait in `finally`
If body throws before all spawns settle, scope exits with live children. Defeats the entire point.

### Wrong attempt 4: count `AbortError` as failure
Cancellation isn't a "real" error. Filter `err.name === 'AbortError'` from collected errors.

---

## 7. The unlocking insight

> **`TaskGroup` tracks spawned children's promises, gives them a shared `AbortSignal`, and `Promise.allSettled`-waits in `finally`. First real error → `ac.abort(err)` → siblings cancel. Multiple real errors → `AggregateError`. `AbortError` filtered (cancellation ≠ failure).**

Five mechanics:

1. **Shared `AbortController`** — all spawned children receive `ac.signal`.
2. **`spawn(fn)`** registers a child promise and pushes onto `tasks`.
3. **First real error** (not `AbortError`) — call `ac.abort(err)`, collect `err` into errors list.
4. **`run(body)`** awaits `body(spawn)`, then `Promise.allSettled(tasks)` in `finally` — guarantees no child outlives the scope.
5. **Error surfacing:** if 1 real error → throw it; if many → `AggregateError`.

---

## 8. Solution (annotated)

```js
class TaskGroupClosed extends Error {}

class TaskGroup {
  constructor() {
    this.tasks = [];                                       // step 1: track all children
    this.ac = new AbortController();                       // step 2: shared signal
    this.errors = [];
    this.closed = false;
  }

  spawn(fn) {
    if (this.closed) throw new TaskGroupClosed('Cannot spawn after group is closing');
    const p = (async () => {
      try {
        return await fn(this.ac.signal);
      } catch (err) {
        if (err?.name !== 'AbortError') {                  // step 3: filter abort
          this.errors.push(err);
          if (!this.ac.signal.aborted) this.ac.abort(err); // step 4: cancel siblings
        }
        throw err;
      }
    })();
    this.tasks.push(p);
    return p;
  }

  async run(body) {
    let bodyErr;
    try {
      await body((fn) => this.spawn(fn));
    } catch (err) {
      bodyErr = err;
      if (!this.ac.signal.aborted) this.ac.abort(err);
    } finally {
      this.closed = true;
      await Promise.allSettled(this.tasks);                 // step 5: WAIT for all children
    }
    const all = [];
    if (bodyErr && bodyErr.name !== 'AbortError') all.push(bodyErr);
    all.push(...this.errors);
    if (all.length === 1) throw all[0];
    if (all.length > 1) throw new AggregateError(all, 'TaskGroup errors');
  }
}

async function withTaskGroup(body) {
  return new TaskGroup().run(body);
}
```

**Try it yourself**

```js
await withTaskGroup(async (spawn) => {
  spawn((signal) => fetchA(signal));
  spawn((signal) => fetchB(signal));
  spawn((signal) => fetchC(signal));
});
// All three settled by the time this line runs.
// If any throws, the others are aborted via signal.
```

---

## 9. Step-by-step dry run

3 children; B throws at t=20:

```
t=0    run(body)
       body calls spawn(A), spawn(B), spawn(C)
       A, B, C all start with shared signal
       body returns → finally runs
       finally: await allSettled([A, B, C])

t=20   B throws → catch in spawn wrapper
       errors.push(B.err)
       ac.abort(B.err) → A and C receive 'abort'
       A rejects with AbortError, C rejects with AbortError
       allSettled resolves [A:abort, B:err, C:abort]

       collect errors: [B.err] (AbortError filtered)
       throw B.err to caller
```

---

## 10. Common confusion + traps

1. **`Promise.all` is structured concurrency.** It isn't — gives up on first reject but doesn't cancel siblings.
2. **`Promise.allSettled` is enough.** Better — but still doesn't cancel on first error.
3. **Cancellation is impossible in JS.** Wrong — `AbortController` exists for this.
4. **Structured concurrency = no goroutines.** No — children exist; they just can't outlive scope.
5. **Counting `AbortError` as failure.** Filter it — cancellation ≠ failure.
6. **Spawn after body returns** — disallow with `TaskGroupClosed`.
7. **`allSettled` in finally not needed.** Critical — without it scope exits with live children.

---

## 11. Senior follow-ups & variants

### Variant 1 — Race mode (first success cancels siblings)
For "ask all replicas, take fastest answer."

### Variant 2 — Bounded concurrency
Combine with Semaphore: `spawn` awaits a permit before starting.

### Variant 3 — Cancellation propagation upward
Child can signal parent to abort siblings (rare).

### Variant 4 — Timeout-wrapped scope
Pass `AbortSignal.timeout(...)` to bound total scope time.

### Variant 5 — Detached background tasks
Explicit opt-out (`spawn.detached(fn)`). Discouraged; defeats the principle.

---

## 12. How to think aloud

> "Structured concurrency binds task lifetimes to a syntactic scope. `TaskGroup` tracks spawned children, gives each a shared AbortSignal, and on scope exit awaits `allSettled` so no child leaks past. First error → abort siblings via signal. Cancellation rejects with AbortError; filter those out of the surfaced error set since they're not 'real' failures. Multiple real errors → AggregateError. Body-level throws also cancel siblings. The contract is: when `run()` returns, every child is *done*."

---

## 13. 60-second revision

> - **Children's lifetime bounded by `run()` scope.**
> - **Shared `AbortController`** — first error aborts siblings.
> - **`Promise.allSettled` in finally** — guarantees no live children leak.
> - **Filter `AbortError`** from collected errors (cancellation ≠ failure).
> - **Single real error → throw it; many → `AggregateError`.**
> - **vs `Promise.all`:** doesn't cancel or wait for siblings on reject.
> - **Family:** Python `asyncio.TaskGroup`, Kotlin `coroutineScope`, Swift `withTaskGroup`.
> - **Trap:** thinking `Promise.all` = structured concurrency; missing `allSettled` in finally.

---

**Related:** [abortcontroller-fanout.md](./abortcontroller-fanout.md) · [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md) · [retry-with-backoff.md](./retry-with-backoff.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
