# 10 — Machine Coding Patterns

The most-asked machine-coding problems for senior JS/Node interviews. Each file follows the v2 13-section learner-first template: problem statement → plain English → mental model → try-yourself → brute force → unlocking insight → annotated solution → dry run → traps → variants → think-aloud → revision.

---

## How to study this folder

1. **Start with the rate-limiting trio** — debounce, throttle, memoize. These are the 15-minute warm-ups that every other machine-coding round opens with.
2. **Then the FP basics** — curry, function-composition, bind-polyfill, once. Higher-order function fluency.
3. **Then the registry/topic family** — event-emitter, pub-sub, observable-subject. Same DS, different APIs.
4. **Then the bounded-concurrency family** — async-semaphore, async-pool, rate-limiter-token-bucket. The production primitives.
5. **Then the resilience family** — circuit-breaker, retry-with-jitter-and-budget, idempotency-wrapper. The trio that makes any external call safe.
6. **Then the caching family** — lru-cache, memoize-ii, cache-stampede-single-flight, dataloader-batch-cache, request-deduplication, batched-request-coalescer.
7. **Then the data structures** — circular-buffer, min-heap-priority-queue, trie, bloom-filter.
8. **Then the JSON polyfills** — json-parse-recursive-descent, json-stringify-polyfill.
9. **Then the distributed-systems toys** — saga-orchestration-toy, leader-election-toy, bfs-with-concurrency.
10. **Then the rest** — deep-clone-with-cycles, set-polyfill, mini-state-machine, dependency-injection-container, scheduler-idle-callback, cancellable-promise-wrapper.

---

## Files (38)

### Rate-limiting trio (most-asked warm-ups)
- [debounce.md](./debounce.md) — Defer until silence; closure over `timerId`.
- [throttle.md](./throttle.md) — At most once per window; differs from debounce by *spacing* vs *silence*.
- [memoize.md](./memoize.md) — Cache function results; closure + Map keyed by `JSON.stringify(args)`.

### Higher-order functions
- [function-composition.md](./function-composition.md) — `compose` / `pipe`; `reduceRight` vs `reduce`.
- [async-compose-pipe.md](./async-compose-pipe.md) — Promise-chained pipe via `reduce` + `Promise.resolve`.
- [curry.md](./curry.md) — Accumulate args until arity; placeholder + infinite-curry variants.
- [bind-polyfill.md](./bind-polyfill.md) — `new.target` detection + prototype chain.
- [once.md](./once.md) — At most once + cached result; flag-gated closure.

### Event/topic registries
- [event-emitter.md](./event-emitter.md) — `Map<event, Set<fn>>` with snapshot-before-iterate.
- [pub-sub.md](./pub-sub.md) — EventEmitter + wildcard pattern subs.
- [observable-subject.md](./observable-subject.md) — RxJS-lite Subject; hot multicast with terminal latch.

### Bounded concurrency
- [async-semaphore.md](./async-semaphore.md) — Permits + FIFO queue; mutex = `Semaphore(1)`.
- [async-pool.md](./async-pool.md) — N runners + shared cursor; order-preserving output.
- [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md) — Lazy refill; per-key bucket.

### Resilience trio
- [circuit-breaker.md](./circuit-breaker.md) — Three-state machine; bounded HALF_OPEN probes.
- [retry-with-jitter-and-budget.md](./retry-with-jitter-and-budget.md) — Full jitter; shared budget; AWS default.
- [idempotency-wrapper.md](./idempotency-wrapper.md) — Atomic `SETNX` acquire; in-flight dedup.

### Caching family
- [lru-cache.md](./lru-cache.md) — Map + delete-then-reinsert for MRU bump.
- [memoize-ii.md](./memoize-ii.md) — Nested Map trie; identity-keyed cache.
- [cache-stampede-single-flight.md](./cache-stampede-single-flight.md) — Coalesce in-flight misses.
- [dataloader-batch-cache.md](./dataloader-batch-cache.md) — Per-request batch + per-key promise cache.
- [request-deduplication.md](./request-deduplication.md) — Two-layer (in-flight + recent) dedup.
- [batched-request-coalescer.md](./batched-request-coalescer.md) — Time-window or size-trigger flush.

### Core data structures
- [circular-buffer.md](./circular-buffer.md) — Fixed-size ring queue.
- [min-heap-priority-queue.md](./min-heap-priority-queue.md) — Array-backed binary heap.
- [trie.md](./trie.md) — Prefix tree with `isEnd` flag.
- [bloom-filter.md](./bloom-filter.md) — Probabilistic Set; no false negatives.

### Parsers / serializers
- [json-parse-recursive-descent.md](./json-parse-recursive-descent.md) — LL(1) single-cursor parser.
- [json-stringify-polyfill.md](./json-stringify-polyfill.md) — Recursive walker with `WeakSet` cycle guard.

### Distributed-systems toys
- [saga-orchestration-toy.md](./saga-orchestration-toy.md) — Forward + compensation in reverse.
- [leader-election-toy.md](./leader-election-toy.md) — Redis SETNX + lease + fencing token.
- [bfs-with-concurrency.md](./bfs-with-concurrency.md) — Graph walk with bounded concurrency.

### Misc
- [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) — `WeakMap<original, clone>`; register-before-recurse.
- [set-polyfill.md](./set-polyfill.md) — Map-backed; SameValueZero for free.
- [mini-state-machine.md](./mini-state-machine.md) — Data-driven dispatch table.
- [dependency-injection-container.md](./dependency-injection-container.md) — Lazy resolution; cycle detection.
- [scheduler-idle-callback.md](./scheduler-idle-callback.md) — Cooperative time-slicing via `MessageChannel`.
- [cancellable-promise-wrapper.md](./cancellable-promise-wrapper.md) — Wrapper vs `AbortController`.

---

## Concept primers

- [`concepts/closures.md`](../../concepts/closures.md) — closure over timer/flag/state.
- [`concepts/promises.md`](../../concepts/promises.md) — microtask scheduling.
- [`concepts/event-loop.md`](../../concepts/event-loop.md) — macrotask vs microtask.
- [`concepts/maps-sets.md`](../../concepts/maps-sets.md) — Map insertion order, WeakMap, SameValueZero.
- [`concepts/recursion.md`](../../concepts/recursion.md) — recursion-with-seen-set pattern.
- [`concepts/prototype.md`](../../concepts/prototype.md) — `this` binding, prototype chain.

---

## Companion sections

- `02-closures/` — counter/memoize/once foundations.
- `04-promises/` — Promise polyfills, retry, pool, mutex.
- `05-event-loop/` — microtask/macrotask scheduling deep-dives.
- `08-maps-sets/` — Set/Map operations.
- `09-recursion/` — BFS/DFS, tree traversal.
