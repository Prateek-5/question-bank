# Structured Concurrency Primitive (`TaskGroup` / nursery)

## Source / Origin
- Concept: Nathaniel J. Smith's "Notes on structured concurrency" (2018); Python's `asyncio.TaskGroup`; Kotlin's `coroutineScope`; Swift's `withTaskGroup`.
- Asked at: Stripe, Atlassian, Razorpay, Cloudflare.
- Concept reference: `concepts/promises.md`, sibling `abortcontroller-fanout.md`.

## Why this question matters in interviews
JavaScript's stock async tools leak. `Promise.all([a(), b()])` — if `a` throws, `b` continues running in the background, sometimes touching state that's already torn down. Errors get swallowed. Cancellation is ad-hoc. Structured concurrency *binds the lifetime of async tasks to a syntactic scope* — when the scope exits, every child task is guaranteed to be done (resolved, rejected, or cancelled). Senior bar: you can implement a `TaskGroup` in 30 lines and name the principle ("the lifetime of a task is bounded by its parent").

## Concepts involved

### Syntax to lock in
```js
class TaskGroup {
  constructor() {
    this.tasks = [];                 // promises of children
    this.ac = new AbortController(); // shared signal
    this.errors = [];
  }
  spawn(fn) {
    const p = (async () => {
      try { return await fn(this.ac.signal); }
      catch (err) {
        if (err.name !== 'AbortError') {
          this.errors.push(err);
          this.ac.abort(err);         // cancel siblings on first error
        }
        throw err;
      }
    })();
    this.tasks.push(p);
    return p;
  }
  async run(body) {
    try {
      await body((fn) => this.spawn(fn));     // body uses spawn(fn) to add children
    } finally {
      // wait for all children regardless of body outcome
      await Promise.allSettled(this.tasks);
    }
    if (this.errors.length > 0) {
      const err = this.errors.length === 1 ? this.errors[0] : new AggregateError(this.errors, 'TaskGroup errors');
      throw err;
    }
  }
}

// Usage
await new TaskGroup().run(async (spawn) => {
  spawn((signal) => fetchA(signal));
  spawn((signal) => fetchB(signal));
  spawn((signal) => fetchC(signal));
});
// All three are done by the time this line runs.
// If any throws, the others are aborted via signal.
```

### Edge cases / interview traps
1. **`Promise.all` reject lets siblings run.** That's leak #1. TaskGroup waits via `Promise.allSettled` so the scope never exits with running children.
2. **First-error cancellation.** TaskGroup aborts siblings on first error so they don't continue computing dead work.
3. **`AbortSignal` plumbing.** Children must accept the signal and respect it. Stock `fetch(url, {signal})` works; custom long-runners must check `signal.aborted` at boundaries.
4. **Multiple errors.** Use `AggregateError` to preserve them all instead of dropping all but the first.
5. **Body throws.** Even if `body` throws synchronously, the finally must still wait for already-spawned children to settle.
6. **Spawn after body returns.** Disallow; once body returned, `run` is in the finally. Throw `TaskGroupClosed`.
7. **Cancellation semantics.** Aborted children should reject with the abort reason; TaskGroup ignores abort errors when collecting `this.errors` (only real failures count).
8. **Nesting.** TaskGroups compose; an inner group has its own scope; outer abort cascades via its signal.

## Mental Model

A **rule: no thread escapes its function**.

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
   │  AT scope exit: A, B, C are ALL settled          │
   │  (no leaked background tasks)                    │
   └──────────────────────────────────────────────────┘
```

Vs unstructured `Promise.all`:

```
   Promise.all([fetchA(), fetchB(), fetchC()])
     ├── fetchA throws at t=5
     ├── Promise.all rejects → caller continues
     └── fetchB, fetchC STILL RUNNING IN BACKGROUND   ← leak
        (they may write to state the caller cleaned up)
```

## Why interviewers care

- **Discipline over async lifecycles.** A senior signal.
- **AbortController fluency.** You can compose signals correctly.
- **Error semantics.** AggregateError, cancellation-reason distinction.

## Common beginner confusion

- **"`Promise.all` is structured concurrency."** It isn't — it gives up on first reject but doesn't cancel siblings or wait for them.
- **"Just `await Promise.allSettled` instead."** Better — but still doesn't cancel on first error or surface errors in a usable shape.
- **"Cancellation is impossible in JS."** Wrong — `AbortController` was specifically built for this.
- **"Structured concurrency = no goroutines."** No — it's about *lifetime*, not absence. Children exist; they just can't outlive the scope.

## Brute force approach

```js
// Leak on error:
await Promise.all([
  longTaskA(),
  longTaskB(),    // if A throws at t=10, B keeps running until t=60
]);
```

## Optimal approach

`TaskGroup` with `spawn(fn)` that registers a child promise; shared `AbortController` cancels siblings on first error; `Promise.allSettled` in `finally` ensures we never exit the scope with live children; collect all errors into `AggregateError`.

## Solution (JavaScript)

```js
class TaskGroupClosed extends Error {}

class TaskGroup {
  constructor() {
    this.tasks = [];
    this.ac = new AbortController();
    this.errors = [];
    this.closed = false;
  }
  spawn(fn) {
    if (this.closed) throw new TaskGroupClosed('Cannot spawn after group is closing');
    const p = (async () => {
      try {
        return await fn(this.ac.signal);
      } catch (err) {
        if (err?.name !== 'AbortError') {
          this.errors.push(err);
          if (!this.ac.signal.aborted) this.ac.abort(err);  // first-error cancels siblings
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
      await Promise.allSettled(this.tasks);
    }
    const all = [];
    if (bodyErr && bodyErr.name !== 'AbortError') all.push(bodyErr);
    all.push(...this.errors);
    if (all.length === 1) throw all[0];
    if (all.length > 1) throw new AggregateError(all, 'TaskGroup errors');
  }
}

// Helper sugar
async function withTaskGroup(body) {
  return new TaskGroup().run(body);
}
```

## Step-by-step dry run

Three children; B throws at t=20.

```
t=0   group.run(body)
      body calls spawn(A), spawn(B), spawn(C)
      A starts, B starts, C starts; all receive same signal
      body awaits something (or returns) → falls to finally
      finally: await allSettled([A, B, C])

t=20  B throws → catch → errors.push(B.err) → ac.abort(B.err)
                       → A receives 'abort' → rejects with AbortError
                       → C receives 'abort' → rejects with AbortError
                       → allSettled resolves with [A:abort, B:err, C:abort]

      collect errors: errors=[B.err]; AbortError filtered out
      throw single error (B.err) to caller
```

## How to think aloud in the interview

> "Structured concurrency binds task lifetimes to a syntactic scope. `TaskGroup` tracks spawned children, gives each a shared AbortSignal, and on scope exit awaits `allSettled` so no child leaks past. First error → abort siblings via signal. Cancellation rejects with AbortError; I filter those out of the surfaced error set since they're not 'real' failures. Multiple real errors → AggregateError. Body-level throws also cancel siblings. The contract is: when `run()` returns, every child is *done*."

## Important takeaways

- **Lifetimes bounded by scope.** No child outlives `run()`.
- **First error → abort siblings via shared signal.**
- **`Promise.allSettled` in `finally`** so the scope can't exit with live children.
- **`AggregateError`** for multiple real failures.
- **Filter `AbortError`** from collected errors — abortion is cancellation, not failure.

## Variants

- **Race mode** — first success cancels siblings (instead of first error). Useful for "ask all replicas, take fastest answer."
- **Bounded concurrency** — combine with `Semaphore` so spawn awaits a permit before starting.
- **Detached background tasks** — explicit opt-out (`spawn.detached(fn)`); rare and discouraged.
- **Cancellation propagation upward** — child can signal parent to abort siblings (rare).
- **Timeout-wrapped scope** — pass an outer `AbortSignal.timeout(...)` to bound total scope time.

## Revision notes

```
TaskGroup:
  spawn(fn): start child with shared signal; on error → ac.abort, push to errors
  run(body):
    try body(spawn) catch bodyErr
    finally: closed=true; await allSettled(children)
    surface errors: AggregateError if multiple, single if one
  
  KEY: children NEVER outlive run()
  first-error cancels siblings via signal
  filter AbortError (not a real failure)
  alternative: `await Promise.all` LEAKS siblings on reject
  Python: asyncio.TaskGroup; Kotlin: coroutineScope; Swift: withTaskGroup
```
