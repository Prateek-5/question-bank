# Design Cancellable Function

## Source
- LeetCode #2776 "Convert Callback Based Function To A Promise Based Function" / #2777 "Design Cancellable Function": https://leetcode.com/problems/design-cancellable-function/
- Canonical: a generator-based cooperative scheduler — the JS analogue of Python's `asyncio.Task.cancel()`.

## Why this question matters in interviews
This is the **deepest event-loop problem** in the LeetCode JS set. To solve it you must explain three things at once: (1) generators (`function*`, `yield`) are cooperative coroutines, (2) a **runner** drives them by repeatedly calling `.next(value)`, and (3) `Promise` integration lets `yield somePromise` look like `await`. The cancellation token is the punchline — it shows you understand that **cancellation in JS is cooperative**, never preemptive. There is no `Thread.kill()`. Senior backend engineers hit this when implementing request cancellation, saga rollbacks, and `AbortSignal`-aware libraries.

## Concepts involved

### Syntax to lock in
```js
function cancellable(generator) {
  let cancelled = false;
  const cancel = () => { cancelled = true; };

  const promise = new Promise((resolve, reject) => {
    const step = (input, isError = false) => {
      if (cancelled) {
        try { generator.throw('Cancelled'); } catch (e) { return reject(e); }
        return;
      }
      let result;
      try {
        result = isError ? generator.throw(input) : generator.next(input);
      } catch (e) { return reject(e); }

      if (result.done) return resolve(result.value);

      Promise.resolve(result.value).then(
        (v) => step(v),
        (e) => step(e, true)
      );
    };
    step();
  });

  return [cancel, promise];
}
```

### Runtime / engine behavior
- A **generator function** (`function*`) returns an iterator. Each `.next()` runs the body up to the next `yield` and returns `{ value, done }`. The generator is paused — not blocked, not on a separate stack.
- The **runner** loop awaits whatever the generator yielded (treating non-promises as already resolved via `Promise.resolve`), then resumes by calling `.next(value)` with the resolved value. This is exactly how `async/await` is implemented under the hood (regenerator/Babel transpiles `await` into this pattern).
- **Cancellation is cooperative** — the runner inspects a flag on every resumption and, instead of calling `.next`, calls `.throw('Cancelled')`. This raises the error *inside* the generator at the paused `yield`, letting `try/finally` run cleanups.
- Each `.then` enqueues a **microtask** — so cancellation takes effect at the next microtask checkpoint, not synchronously.

### Edge cases (interview traps)
1. **Cancel before first step** — if `cancel()` runs synchronously after `cancellable(...)`, the first `step()` already ran sync. Some implementations defer the first `step` to a microtask (`Promise.resolve().then(step)`) so cancel always works.
2. **Cancel during a long-running sync block in the generator** — useless. The runner can only check the flag between yields. No preemption.
3. **Generator's `try/finally`** — when you `generator.throw`, the generator can `catch` and recover. Make sure cancellation is propagated by re-throwing or by surfacing the original `'Cancelled'` reason.
4. **Yielding a rejected promise** — must re-enter the generator via `.throw`, not `.next`. That's the `isError` branch.
5. **Generator already done** — calling `.throw` on a finished iterator throws synchronously. Guard before `step`.
6. **Microtask ordering** — every `.then` schedules a microtask. A chain of `yield Promise.resolve()` advances one step per microtask, which means the generator drains in the **microtask queue**, not across macrotasks.
7. **No `await` allowed in generators** — must use `yield` instead. `function*` and `async function*` are different beasts.
8. **Return value vs throw value** — `done: true` resolves the outer promise; uncaught throw rejects it.

## Brute force approach
"I'll just set a flag and have the generator check it itself." This forces the *caller's generator code* to be cancellation-aware everywhere — terrible API. The whole point is that the runner handles cancellation transparently.

Another brute force: race the promise against a "cancel" promise that rejects on cancel. This works for one-shot cancellation but doesn't let `try/finally` inside the generator run cleanups. The `.throw` approach is strictly more powerful.

## Optimal approach
Runner-based scheduler with three rules:
1. After each `.next` / `.throw`, inspect the result. If `done`, resolve the outer promise.
2. Otherwise, wrap the yielded value in `Promise.resolve`, and on settlement re-enter the generator (`.next` on fulfill, `.throw` on reject).
3. Before every re-entry, check the cancellation flag. If set, `.throw('Cancelled')` once.

O(1) memory beyond the generator's own frame; one microtask per `yield`.

## Solution (JavaScript)

```js
/**
 * @param {Generator} generator
 * @returns {[cancelFn: () => void, promise: Promise<any>]}
 */
function cancellable(generator) {
  let cancelled = false;
  const cancel = () => { cancelled = true; };

  const promise = new Promise((resolve, reject) => {
    function step(input, isError = false) {
      let result;
      try {
        if (cancelled && !isError) {
          // Inject cancellation into the generator so try/finally can run.
          result = generator.throw('Cancelled');
        } else {
          result = isError ? generator.throw(input) : generator.next(input);
        }
      } catch (e) {
        return reject(e);
      }

      if (result.done) return resolve(result.value);

      Promise.resolve(result.value).then(
        (v) => step(v, false),
        (e) => step(e, true)
      );
    }

    // Kick off via a microtask so cancel() called immediately after still
    // takes effect on the very first step.
    Promise.resolve().then(() => step(undefined, false));
  });

  return [cancel, promise];
}
```

## Step-by-step dry run

Input:
```js
function* gen() {
  const a = yield Promise.resolve(1);   // (A)
  const b = yield Promise.resolve(2);   // (B)
  return a + b;                          // (C)
}
const [cancel, p] = cancellable(gen());
p.then(console.log);                     // expect 3
```

Trace (CS = call stack, NT = nextTick queue, MQ = microtask queue):

| Step | CS | NT | MQ | Notes |
|------|----|----|----|-------|
| 1 | `cancellable` runs → returns `[cancel,p]` | — | `[kickoff]` | First step queued via `.then` |
| 2 | (empty) | — | `[kickoff]` | Sync done; drain microtasks |
| 3 | `kickoff` → `step()` → `.next()` runs until yield (A); `result={value:P1,done:false}` | — | — | P1 already resolved |
| 4 | `P1.then(v→step(v))` schedules microtask | — | `[stepA]` | — |
| 5 | drain MQ → `stepA(1)` → `.next(1)` runs until yield (B); `a=1`; `result={value:P2,done:false}` | — | — | — |
| 6 | `P2.then(...)` | — | `[stepB]` | — |
| 7 | drain MQ → `stepB(2)` → `.next(2)` → `b=2`, hits `return 3`; `result={value:3,done:true}` | — | — | — |
| 8 | `resolve(3)` → enqueues `.then(console.log)` | — | `[print]` | — |
| 9 | drain MQ → `console.log(3)` | — | — | Output: `3` |

Now trace with `cancel()` called immediately:

```js
const [cancel, p] = cancellable(gen());
cancel();                       // sync, before first step
p.catch(console.log);
```

| Step | Notes |
|------|-------|
| 1 | `cancellable` runs, queues `kickoff` microtask, returns `[cancel,p]`. |
| 2 | `cancel()` sets `cancelled = true`. |
| 3 | `p.catch(...)` chains a handler. |
| 4 | Sync stack unwinds. Microtask queue: `[kickoff, catch-pending]`. |
| 5 | `kickoff` runs `step()`. `cancelled === true` → `generator.throw('Cancelled')`. Generator has no try/catch → rethrows out. |
| 6 | Caught by runner's `try`, calls `reject('Cancelled')`. |
| 7 | `console.log('Cancelled')` runs in the next microtask. Output: `Cancelled`. |

If the generator had a `try/finally`, that `finally` block runs between steps 5 and 6 — guaranteed cleanup.

## Important takeaways

**Syntax to memorize**
- `function*` returns an iterator. `gen.next(v)` resumes; `gen.throw(e)` injects an exception.
- Wrap yielded values in `Promise.resolve(...)` so a yielded plain value still works.
- Two re-entry paths: `.next` for fulfillment, `.throw` for rejection.

**Patterns to reuse**
- The same runner pattern powers transpiled `async/await`. Reading Babel's regenerator output makes it click.
- The same `[cancel, promise]` tuple is the shape of `AbortController.signal` + a wrapped operation.
- Pair with `AbortSignal` instead of a custom flag to integrate with `fetch`, timers, etc.

**Common mistakes**
- Forgetting `Promise.resolve(...)` around yielded value — breaks when the generator yields a non-thenable.
- Not handling the `isError` path — a rejected yielded promise must enter via `.throw`.
- Not deferring the first `step` to a microtask — cancel called immediately can't take effect.
- Calling `.throw` on a generator that already returned — throws synchronously.

**Where it sits in the event loop**
- Each `yield <promise>` parks the generator. Resumption happens via `.then`, which is a **microtask**.
- A chain of `yield Promise.resolve()` thus runs entirely in the microtask queue, **before** the next `setTimeout` ever fires.
- Cancellation is observed **at the next microtask checkpoint** — never inside a sync block.

## Variants

1. **AbortSignal-driven cancellable** — replace the boolean flag with `signal.aborted`. Generator can also be cancelled by `controller.abort()` from anywhere. This is the modern idiomatic API.

2. **Timeout cancellation** — wrap `cancellable(gen)` with `setTimeout(cancel, ms)` to auto-abort after a deadline.

3. **Race / parallel runner** — extend the runner so `yield [p1, p2, p3]` behaves like `Promise.all`. Common in saga libraries (redux-saga's `all` / `race` effects).

4. **Async generator equivalent** — once `async function*` is available, the same pattern is built-in via `for await...of`. But the explicit runner remains the best mental model for understanding what `await` actually does.

## Revision notes

> **cancellable-function — 60 second recap**
> - Generator + runner = cooperative coroutine. `yield` = pause; `.next(v)` = resume.
> - Wrap yielded value with `Promise.resolve(...)`; re-enter via `.next` (fulfill) or `.throw` (reject).
> - Cancellation is **cooperative**, observed at microtask checkpoints — never preemptive.
> - `generator.throw('Cancelled')` lets `try/finally` clean up. Plain rejection doesn't.
> - Defer the first `step` to a microtask so immediate `cancel()` is honored.
> - This is exactly how `async/await` is transpiled by Babel/regenerator.
> - Modern equivalent: `AbortSignal` + `async/await` + early returns on `signal.aborted`.
> - **Trap:** long sync block inside a `yield` step cannot be cancelled — only between yields.
> - **Trap:** forgetting the `isError` re-entry path — rejected yielded promises must use `.throw`.
