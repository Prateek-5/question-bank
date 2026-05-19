# 04 — Promises

> 26 question files. Promises + async/await dominate senior backend interviews — both as "implement this polyfill" tests and as "design this async flow" discussions. Master these and you've covered ~30% of the interview surface area on their own.

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md) — read this first if you haven't built a Promise polyfill from scratch.

---

## Suggested reading order

### Tier 1 — Foundations (the warmups)

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 1 | [sleep.md](./sleep.md) | Easy | 5 min | The simplest promise wrapper. `new Promise(r => setTimeout(r, ms))`. |
| 2 | [add-two-promises.md](./add-two-promises.md) | Easy | 10 min | Composing two promises with `Promise.all`. |
| 3 | [build-promise-from-scratch.md](./build-promise-from-scratch.md) | Medium-Hard | 45 min | The whole Promise state machine. The single most foundational. |
| 4 | [deferred-with-resolvers.md](./deferred-with-resolvers.md) | Easy-Medium | 10 min | `{promise, resolve, reject}` factory; foundation for many later patterns. |
| 5 | [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md) | Easy-Medium | 10 min | `for/await` vs `Promise.all(arr.map(async))` — when each. |

### Tier 2 — The polyfill quartet (most-asked)

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 6 | [promise-all-polyfill.md](./promise-all-polyfill.md) | Medium | 20 min | The canonical polyfill. Fail-fast, input-order preservation, empty-input edge. |
| 7 | [promise-race-polyfill.md](./promise-race-polyfill.md) | Easy-Medium | 15 min | First-settled wins (resolve OR reject). |
| 8 | [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md) | Medium | 20 min | All settled; per-entry `{status, value/reason}`. |
| 9 | [promise-any-polyfill.md](./promise-any-polyfill.md) | Medium | 20 min | First fulfillment; `AggregateError` on all-reject. |
| 10 | [promise-finally-polyfill.md](./promise-finally-polyfill.md) | Easy-Medium | 15 min | Run cleanup regardless of settle; preserve resolve/reject. |

### Tier 3 — Real-world async patterns

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 11 | [retry-with-backoff.md](./retry-with-backoff.md) | Medium | 25 min | Exponential backoff + jitter; idempotency awareness. |
| 12 | [promise-pool.md](./promise-pool.md) | Medium | 30 min | Bounded concurrency over N tasks. |
| 13 | [promise-time-limit.md](./promise-time-limit.md) | Easy-Medium | 15 min | `Promise.race` + `setTimeout` timeout wrapper. |
| 14 | [promisify-node-callback.md](./promisify-node-callback.md) | Easy-Medium | 15 min | Node-callback → Promise. |
| 15 | [fetch-with-abort.md](./fetch-with-abort.md) | Medium | 20 min | `AbortController` integration with fetch. |
| 16 | [cache-with-time-limit.md](./cache-with-time-limit.md) | Medium | 25 min | Async memoize with TTL. |
| 17 | [priority-async-queue.md](./priority-async-queue.md) | Medium-Hard | 30 min | Priority queue over async tasks. |

### Tier 4 — Iterables + advanced

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 18 | [async-filter.md](./async-filter.md) | Medium | 20 min | `filter` over async predicates. |
| 19 | [async-reduce.md](./async-reduce.md) | Medium | 20 min | `reduce` over async accumulator. |
| 20 | [async-memoize.md](./async-memoize.md) | Medium | 25 min | Cache the **promise**, not the value (in-flight dedupe). |

### Tier 5 — Senior-grade primitives (the gap-fills)

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 21 | [async-mutex.md](./async-mutex.md) | Medium-Hard | 25 min | Mutex via Promise-queue. Foundation for in-process serialization. |
| 22 | [abortcontroller-fanout.md](./abortcontroller-fanout.md) | Medium-Hard | 25 min | Standard cancellation; combine signals. |
| 23 | [structured-concurrency-primitive.md](./structured-concurrency-primitive.md) | Hard | 35 min | TaskGroup / nursery — children can't outlive scope. |
| 24 | [async-generator-producer.md](./async-generator-producer.md) | Medium-Hard | 30 min | Pull-based streaming with built-in backpressure. |
| 25 | [microtask-drainer.md](./microtask-drainer.md) | Medium | 20 min | Force a microtask flush; understanding the queue. |
| 26 | [top-level-await-deadlock-quiz.md](./top-level-await-deadlock-quiz.md) | Medium | 20 min | TLA semantics + circular-import deadlock. |

---

## If you only have 60 minutes

Read these 6:
1. [build-promise-from-scratch.md](./build-promise-from-scratch.md) — internalize the state machine
2. [promise-all-polyfill.md](./promise-all-polyfill.md) — the canonical polyfill
3. [retry-with-backoff.md](./retry-with-backoff.md) — backoff + jitter (asked everywhere)
4. [promise-pool.md](./promise-pool.md) — bounded concurrency
5. [abortcontroller-fanout.md](./abortcontroller-fanout.md) — cancellation modern style
6. [async-memoize.md](./async-memoize.md) — in-flight dedupe

---

## How to use this folder

For each file:
1. Read **section 1 (problem statement)** — confirm you understand the contract.
2. Try **section 5 (try yourself)** before scrolling.
3. Read sections 4 and 7 (mental model + unlocking insight) first if you're stuck.
4. Write the solution from scratch *without looking* at section 8. Then compare.
5. Revisit **section 10 (common confusion)** the night before the interview.
6. Memorize **section 13 (60-second revision)** the morning of.

**The promise state machine is the substrate.** Almost every later question (event-loop, machine-coding patterns, system design async flows) builds on what you learn here.
