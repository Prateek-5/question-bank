# Implement `Promise.any` (first fulfilled wins; AggregateError)

## Source
- Canonical polyfill interview question post-ES2021 (Promise.any landed).
- LeetCode #2637 "Promise Time Limit" family; BFE.dev #45 "implement Promise.any".
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/any

## Why this question matters in interviews
`Promise.any` completes the trio after `all` and `race`. It's the **failure-tolerant racer** — useful when you have N redundant data sources (CDN mirrors, fallback APIs, replica DBs) and you want the first one that succeeds. Interviewers ask it to test (1) whether you know it exists at all (juniors don't), (2) `AggregateError` handling, and (3) whether you correctly invert `all`'s logic — reject-on-all instead of fulfill-on-all. The classic mistake is using `race` semantics, which fail too fast.

## Concepts involved

### Syntax to lock in
```js
const winner = await Promise.any([fetchA(), fetchB(), fetchC()]);
// winner is the first value any of them fulfills with.
// If ALL reject → throws AggregateError with .errors = [errA, errB, errC].
```

### Runtime / engine behavior
- **`Promise.any` resolves on first FULFILLED**, ignoring intermediate rejections.
- It rejects **only when every input rejects**, with an `AggregateError` whose `.errors` array preserves input order.
- Empty array → rejects immediately with `AggregateError([])`. (Mirror image of `Promise.all([])` which resolves with `[]`.)
- Inputs are processed in iteration order; non-thenables are wrapped via `Promise.resolve()`.

### Edge cases (interview traps)
1. **Empty iterable** → reject with `new AggregateError([], 'All promises were rejected')`. Many candidates forget this and resolve with `undefined`.
2. **Mixed thenables / values** — `Promise.any([1, p, Promise.reject(e)])` should resolve with `1` (the non-promise is wrapped, resolves immediately).
3. **Order of `errors` array** — must match input index, not settlement order.
4. **Counting rejections** — track a counter, reject only when counter === total.
5. **Already-settled inputs** — first iteration may settle synchronously via microtask; counter logic must be robust.
6. **Don't leak unhandled rejections** — every input's rejection is "handled" by your `.then(_, onReject)`, so no warnings should fire.
7. **`AggregateError` availability** — Node 15+ / modern browsers. For older runtimes, polyfill it (extend `Error` with `.errors`).

## Brute force approach
"Loop, await each, return first success, collect errors otherwise" — but `await` in a loop is **sequential**, killing the whole point of `any` (parallel race). The correct path is fire all at once and track via callbacks. Drop the sequential approach immediately.

## Optimal approach
Iterate inputs, wrap each in `Promise.resolve()`, attach a `.then(onFulfill, onReject)`. First `onFulfill` resolves the outer promise. Each `onReject` writes into `errors[i]` and increments a counter; when counter equals total, reject with `AggregateError(errors)`. O(n) time, O(n) memory for errors array.

## Solution (JavaScript)

```js
function promiseAny(iterable) {
  return new Promise((resolve, reject) => {
    const promises = Array.from(iterable);

    if (promises.length === 0) {
      return reject(new AggregateError([], 'All promises were rejected'));
    }

    const errors = new Array(promises.length);
    let rejectedCount = 0;

    promises.forEach((p, i) => {
      Promise.resolve(p).then(
        (value) => resolve(value),
        (err) => {
          errors[i] = err;
          rejectedCount += 1;
          if (rejectedCount === promises.length) {
            reject(new AggregateError(errors, 'All promises were rejected'));
          }
        },
      );
    });
  });
}
```

## Step-by-step dry run

Input:
```js
const p1 = new Promise((_, rej) => setTimeout(() => rej('A failed'), 50));
const p2 = new Promise((_, rej) => setTimeout(() => rej('B failed'), 30));
const p3 = new Promise((res) => setTimeout(() => res('C wins'), 100));

promiseAny([p1, p2, p3]).then(v => console.log(v)).catch(e => console.log(e.errors));
```

Trace:
- **t=0** — outer promise built. Iterate `[p1, p2, p3]`. Each `Promise.resolve(p).then(...)` registers handlers. `errors = [empty, empty, empty]`, `rejectedCount = 0`.
- **t=30** — p2 rejects with `'B failed'`. `errors[1] = 'B failed'`, `rejectedCount = 1`. Not equal to 3, so outer stays pending.
- **t=50** — p1 rejects with `'A failed'`. `errors[0] = 'A failed'`, `rejectedCount = 2`. Still pending.
- **t=100** — p3 fulfills with `'C wins'`. Outer resolves with `'C wins'`. **Subsequent rejections (none here) would be ignored** because state is locked.

Output: `C wins`.

If we replace p3 with `Promise.reject('C failed')`:
- All three reject in order p2 → p1 → p3.
- On the third rejection, `rejectedCount === 3`, reject outer with `AggregateError(['A failed', 'B failed', 'C failed'])`. `.errors` array is in **input** order, not settlement order.

## Important takeaways

**Syntax to memorize**
- `new AggregateError(errors, 'message')` — first arg is an iterable of errors, second is an optional message.
- `errors[i] = err` (positional write), not `errors.push(err)` — preserves input order.
- `Promise.resolve(p)` to coerce non-thenables uniformly.

**Patterns to reuse**
- **Counter + total** is the universal pattern for "wait for all of X" — used in `Promise.all`, `Promise.allSettled`, and any custom barrier sync.
- **Positional write into pre-allocated array** is the order-preservation idiom; same trick is needed in `Promise.all`.

**Common mistakes**
- Using `errors.push(err)` — breaks order under non-deterministic settlement.
- Resolving on the first settlement (mimicking `race`) — wrong; `any` ignores rejections.
- Forgetting empty-iterable case — must reject with empty `AggregateError`, not resolve.
- Using `for await...of` — that's sequential. Defeats parallel racing.
- Not wrapping non-thenables with `Promise.resolve()` — `[1, 2]` should resolve with 1 immediately.

**Related questions**
- `Promise.all` polyfill (mirror image — fulfill-on-all)
- `Promise.race` (first settled, regardless of state)
- `Promise.allSettled` (waits for all, never rejects)

## Variants

1. **`Promise.firstSuccessful`** — same semantics, custom name. Some companies (Amazon was one) have an in-house variant before ES2021 landed.
2. **`anyWithLimit(promises, k)`** — resolve when ANY `k` of them fulfill. Generalization; nice follow-up.
3. **Cancel losing requests** — combine with AbortController so the slower CDN fetches get aborted when one wins. Real-world use case.
4. **Tolerate N failures, then reject** — instead of waiting for all to reject, configure threshold.

## Revision notes

> **Promise.any — 60 second recap**
> - First **fulfilled** wins. Rejections are accumulated but ignored.
> - Rejects only when **all** inputs reject, with `AggregateError(errors)`.
> - Empty array → reject immediately with empty `AggregateError`.
> - Pattern: positional `errors[i] = err` + `rejectedCount` counter.
> - Mirror image of `Promise.all` (which uses `values[i]` + `fulfilledCount`).
> - **Trap:** confusing it with `Promise.race` (which fails fast). `any` is the survivor.
