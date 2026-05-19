# Cancellable Function — generator-based cooperative coroutine

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [`04-promises/structured-concurrency-primitive.md`](../04-promises/structured-concurrency-primitive.md), [`10-machine-coding-patterns/cancellable-promise-wrapper.md`](../10-machine-coding-patterns/cancellable-promise-wrapper.md)
>
> **Source:** [LeetCode 2777 — Design Cancellable Function](https://leetcode.com/problems/design-cancellable-function/). The deepest event-loop problem on LeetCode JS.

---

## 1. Problem statement

**Signature**
```ts
function cancellable<T>(generator: Generator<Promise<T>|T, T, T>): [
  cancel: () => void,
  promise: Promise<T>,
];
```

**Input / Output examples**

| Setup                                          | Behaviour                                              |
|------------------------------------------------|---------------------------------------------------------|
| Normal completion                              | promise resolves to `return` value                     |
| Cancel before first step                       | generator gets `.throw('Cancelled')` at first yield    |
| Cancel mid-generator                            | next resumption injects throw; `try/finally` cleanups run |
| Yielded promise rejects                         | runner re-enters via `.throw(error)`                   |
| Generator already done; cancel called          | no-op                                                   |

**Constraints**
- Generator + runner = cooperative coroutine — same shape as transpiled `async/await`.
- Cancellation is **cooperative** at microtask checkpoints, never preemptive.
- `generator.throw('Cancelled')` lets `try/finally` clean up.
- Defer first `step` to microtask so immediate `cancel()` is honored.

---

## 2. Plain-English restatement

A generator (`function*`) is a pause-able function. A "runner" drives it by calling `.next(value)` to resume, treating yielded promises as awaits. To cancel: set a flag; on the next resumption, call `.throw('Cancelled')` instead — raises the error inside the generator at the paused `yield`, so `try/finally` can clean up.

---

## 3. Why this matters in interviews

The deepest event-loop problem on LeetCode JS. Tests generators, microtask scheduling, cooperative cancellation, the realization that there is no `Thread.kill()` in JS.

---

## 4. Mental model

```
   Generator function:
   function* gen() {
     const a = yield Promise.resolve(1);    // suspend; await
     const b = yield Promise.resolve(2);
     return a + b;
   }

   Runner drives it:
   step(input):
     result = generator.next(input)       // resume up to next yield
     if (result.done) resolve(result.value)
     else Promise.resolve(result.value).then(
       v => step(v),                       // re-enter with value
       e => step(e, isError=true)          // re-enter with throw
     )

   Cancellation:
   cancel() { cancelled = true }
   step inspects cancelled BEFORE resuming
     if set, generator.throw('Cancelled') instead of .next()
     → try/finally inside generator runs cleanup

   Cooperative: cancellation observed at microtask checkpoints,
                never inside sync block within a yield's step.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `generator.throw('X')` do?
> 2. Why defer the first `step` to a microtask?
> 3. Can you cancel during a long sync `for` loop inside the generator?

---

## 6. Brute force — walked through

### Wrong attempt 1: generator checks cancellation itself
Forces generator code to be cancellation-aware everywhere. Bad API.

### Wrong attempt 2: race against a cancel-rejected promise
Works for one-shot; can't trigger `try/finally` cleanup.

### Wrong attempt 3: forget the rejected-yield path
`.then(v => step(v))` ignores errors; rejected yielded promises need `.throw`.

---

## 7. The unlocking insight

> **Runner-based scheduler. After each `.next`/`.throw`, inspect result. If done, resolve. Else wrap yielded value in `Promise.resolve`; on settle, re-enter via `.next` (fulfill) or `.throw` (reject). Before every re-entry, check cancellation flag — if set, `.throw('Cancelled')` once.**

Three properties:

1. **Generator + runner** — cooperative coroutine.
2. **Cancellation is microtask-aware** — observed between yields, not within.
3. **`.throw` for cleanup** — enables `try/finally`.

---

## 8. Solution (annotated)

```js
function cancellable(generator) {
  let cancelled = false;
  const cancel = () => { cancelled = true; };

  const promise = new Promise((resolve, reject) => {
    function step(input, isError = false) {
      let result;
      try {
        if (cancelled && !isError) {                                  // step 1: inject cancellation
          result = generator.throw('Cancelled');
        } else {
          result = isError ? generator.throw(input) : generator.next(input);
        }
      } catch (e) {
        return reject(e);
      }

      if (result.done) return resolve(result.value);                  // step 2: done

      Promise.resolve(result.value).then(                              // step 3: re-enter
        (v) => step(v, false),
        (e) => step(e, true),
      );
    }

    Promise.resolve().then(() => step(undefined, false));              // step 4: defer first step
  });

  return [cancel, promise];
}
```

**Try it yourself**

```js
function* gen() {
  try {
    const a = yield Promise.resolve(1);
    const b = yield Promise.resolve(2);
    return a + b;
  } finally {
    console.log('cleanup ran');
  }
}

const [cancel, p] = cancellable(gen());
p.then(console.log, (e) => console.log('rej:', e));

// Without cancel: cleanup ran, then 3.

// With cancel before first step:
const [cancel2, p2] = cancellable(gen());
cancel2();                                       // sync cancel
p2.catch(console.log);
// Output: cleanup ran, rej: Cancelled
```

---

## 9. Step-by-step dry run

```
Normal trace (gen yields P.resolve(1) → P.resolve(2) → return 3):

t=0    cancellable runs; queues kickoff via microtask. Returns [cancel, p].
t=μ1   microtask: step():
         generator.next() → result={value:P1, done:false}
         P1.then(step) queues microtask
t=μ2   step(1): generator.next(1) → {value:P2, done:false}; a=1.
         P2.then(step) queues
t=μ3   step(2): generator.next(2) → {value:3, done:true}; b=2.
         resolve(3).

Cancel-immediately trace:
t=0    cancellable runs; queues kickoff. Returns [cancel, p].
       cancel() sets cancelled=true.
t=μ1   step(): cancelled=true → generator.throw('Cancelled').
       gen has try/finally → finally runs → 'cleanup ran'.
       gen rethrows 'Cancelled' (no catch).
       caught by runner's try → reject('Cancelled').
t=μ2   p.catch handler → 'rej: Cancelled'.

Cancel mid-generator:
  Each yield is a microtask suspend point.
  When you call cancel(), the flag flips.
  Next resumption (via .then) sees flag → injects throw at the yield.
  try/finally runs before exception propagates.
```

---

## 10. Common confusion + traps

1. **Forget `Promise.resolve(...)` around yielded value** — breaks for non-thenable yields.
2. **Forget `isError` path** — rejected yielded promises must enter via `.throw`.
3. **No defer of first step** — immediate cancel can't take effect.
4. **`.throw` on done generator** — throws synchronously; guard.
5. **Long sync block inside yield** — can't be cancelled until between yields.
6. **`await` allowed in generator** — no, generators use `yield`, not `await`. Async generators are different.
7. **Pre-emptive cancellation** — doesn't exist in JS; always cooperative.

---

## 11. Senior follow-ups & variants

### Variant 1 — AbortSignal-driven
Replace flag with `signal.aborted`. Cancel via `controller.abort()`. Idiomatic modern API.

### Variant 2 — Timeout cancellation
`setTimeout(cancel, ms)` for auto-abort after deadline.

### Variant 3 — Parallel `yield [p1, p2]`
Extend runner to handle arrays (like `Promise.all`). Used in redux-saga.

### Variant 4 — Async generator
`async function*` with `for await...of` — built-in. Explicit runner remains best mental model.

### Variant 5 — Cancellation propagation
`generator.throw` lets try/catch inside generator recover. To propagate, re-throw.

---

## 12. How to think aloud

> "Generator + runner = cooperative coroutine. `yield` pauses; `.next(v)` resumes; `.throw(e)` injects exception. Runner wraps yielded value in `Promise.resolve`, attaches `.then` with two handlers: `.next` for fulfill, `.throw` for reject. Cancellation: flag inspected on every re-entry; if set, call `generator.throw('Cancelled')` instead of `.next` — try/finally inside generator runs cleanup. Defer first step to microtask so immediate cancel is honored. Cooperative — never preemptive; long sync inside a yield can't be cancelled. This is exactly how Babel transpiles `async/await`. Modern equivalent: AbortSignal + async/await + early returns on `signal.aborted`."

---

## 13. 60-second revision

> - **Generator + runner** = cooperative coroutine.
> - **`yield`** pauses; **`.next(v)`** resumes; **`.throw(e)`** injects.
> - **Wrap yielded value** with `Promise.resolve`; re-enter via `.next` or `.throw`.
> - **Cancellation cooperative** — observed at microtask checkpoints.
> - **`generator.throw('Cancelled')`** enables `try/finally` cleanup.
> - **Defer first step** to microtask so immediate cancel works.
> - **Modern:** AbortSignal + async/await + early returns.
> - **Trap:** no `Promise.resolve` wrap; missing isError path; sync block inside yield; pre-emptive cancellation expectation.

---

**Related:** [`04-promises/structured-concurrency-primitive.md`](../04-promises/structured-concurrency-primitive.md) · [`10-machine-coding-patterns/cancellable-promise-wrapper.md`](../10-machine-coding-patterns/cancellable-promise-wrapper.md) · [timeout-cancellation.md](./timeout-cancellation.md) · [interval-cancellation.md](./interval-cancellation.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md), [`concepts/event-loop.md`](../../concepts/event-loop.md)
