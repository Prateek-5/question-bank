# DataLoader — Per-Request Batch + Cache

## Source / Origin
- Facebook's `dataloader` (Lee Byron, 2015) — the canonical Node implementation underpinning GraphQL resolvers.
- Asked at: anywhere with GraphQL (Shopify, Stripe, GitHub, Atlassian, Razorpay).
- Concept reference: `concepts/promises.md`; sibling `batched-request-coalescer.md`.

## Why this question matters in interviews
DataLoader solves the **N+1 problem** at the *application* layer: a GraphQL resolver naively calls `getUser(id)` 100 times across a single request; without batching that's 100 DB hits. DataLoader collects those calls within a single event-loop tick, dispatches one batch `getUsers([id1..id100])`, and resolves each individual promise. It's also a *per-request cache*: identical keys collapse to one fetch. Interviewers love this because it forces you to understand microtask scheduling, promise lifecycle, and cache scope all in 30 lines.

## Concepts involved

### Syntax to lock in
```js
class DataLoader {
  constructor(batchFn, { maxBatchSize = Infinity, cache = true } = {}) {
    this.batchFn = batchFn;           // async (keys: K[]) => V[]  (output array length === input length)
    this.maxBatchSize = maxBatchSize;
    this.cache = cache ? new Map() : null;
    this.queue = [];                  // [{key, resolve, reject}]
    this.scheduled = false;
  }

  load(key) {
    if (this.cache?.has(key)) return this.cache.get(key);
    const p = new Promise((resolve, reject) => this.queue.push({ key, resolve, reject }));
    if (this.cache) this.cache.set(key, p);          // cache the *promise*, not the value
    if (!this.scheduled) {
      this.scheduled = true;
      queueMicrotask(() => this._dispatch());        // drain at end of tick
    }
    return p;
  }

  async _dispatch() {
    this.scheduled = false;
    const batch = this.queue.splice(0, this.queue.length);
    for (let i = 0; i < batch.length; i += this.maxBatchSize) {
      const slice = batch.slice(i, i + this.maxBatchSize);
      try {
        const values = await this.batchFn(slice.map(b => b.key));
        if (values.length !== slice.length) throw new Error('batchFn must return array of same length as keys');
        slice.forEach((b, idx) => values[idx] instanceof Error ? b.reject(values[idx]) : b.resolve(values[idx]));
      } catch (err) {
        slice.forEach(b => b.reject(err));
      }
    }
  }
}
```

### Edge cases / interview traps
1. **Output array must align with input order and length.** This is the contract clients depend on. Throw loudly if violated.
2. **Cache the promise, not the value.** If two callers `load(42)` before the batch dispatches, they should share the same in-flight promise. Caching the value (after resolution) is the same effect, but caching the promise covers the in-flight window too.
3. **`queueMicrotask` vs `setImmediate` vs `Promise.resolve().then`.** Microtask = same tick = same render frame; that's the standard choice. `setTimeout(0)` would batch across the macrotask boundary — too late.
4. **Per-request cache, not global.** A new loader per HTTP request. Otherwise user A's stale `getUser(42)` leaks to user B.
5. **Error per key vs error per batch.** If the batch function returns `[user1, Error, user3]`, each promise resolves/rejects individually. If `batchFn` throws, all in the batch reject.
6. **Cache invalidation.** Provide `clear(key)` and `clearAll()` for write-paths that mutate the data mid-request.
7. **`maxBatchSize`.** Prevent megabatches from breaking DB query limits (e.g., Postgres parameter limit).
8. **Sync `batchFn` is fine.** `await` of a non-Promise is no-op.

## Mental Model

DataLoader is a **rideshare carpool**:

```
   load(1) ────▶ [_, _, _]              ┐
   load(2) ────▶ [1, _, _]              │ within
   load(3) ────▶ [1, 2, _]              │ one tick
   load(1) ────▶ shared with first      │ (microtask)
                                        ┘
   end of tick:  dispatch batchFn([1,2,3])  → values = [u1, u2, u3]
                 resolve load(1) → u1
                 resolve load(2) → u2
                 resolve load(3) → u3
                 (the second load(1) shares the same promise → also u1)
```

The two key properties:

1. **Batching**: keys collected synchronously through promise resolution, dispatched at end of tick.
2. **Per-request cache**: identical keys map to a single in-flight promise.

## Why interviewers care

- **Microtask understanding** — they want to see you reach for `queueMicrotask` and explain why.
- **N+1 awareness** — anyone who's debugged a GraphQL endpoint knows this pattern.
- **API contract design** — output ordering, error semantics, cache scope.

## Common beginner confusion

- **"Just memoize."** Memoization handles identical-key dedup but doesn't batch *different* keys.
- **"Use `setTimeout(0)`."** That's macrotask — collects too late, and microtasks (other Promise chains) might starve.
- **"Make it a singleton."** Global cache → cross-request leaks. New loader per request.
- **"`batchFn` can return values in any order."** No — the contract is `values[i]` corresponds to `keys[i]`. Some implementations support a map-style return, but ordered array is the default.
- **"Cache the value."** Then in-flight duplicates miss. Cache the *promise*.

## Brute force approach

```js
// GraphQL resolver naively
async function user(parent) { return getUser(parent.userId); }
// 100 posts → 100 getUser calls → 100 DB hits
```

## Optimal approach

`load(key)` returns a promise, enqueues `{key, resolve, reject}`, schedules a microtask if not already scheduled. The microtask drains the queue and calls `batchFn(keys)` once. The result array is sliced back to per-key resolvers. Promise caching covers in-flight duplicates.

## Solution (JavaScript)

See "Syntax to lock in" above for the full implementation. Below is the canonical user-facing usage:

```js
// per-request setup (e.g., in Apollo context function)
const userLoader = new DataLoader(async (ids) => {
  const rows = await db.query('SELECT * FROM users WHERE id = ANY($1)', [ids]);
  // align output to input
  const byId = new Map(rows.map(r => [r.id, r]));
  return ids.map(id => byId.get(id) ?? new Error(`User ${id} not found`));
});

// in resolvers
const u1 = userLoader.load(1);
const u2 = userLoader.load(2);
const u1Again = userLoader.load(1);   // shares with first
// → end of tick → batchFn([1, 2]) → one DB query
const [r1, r2, r3] = await Promise.all([u1, u2, u1Again]);
```

## Step-by-step dry run

```
t=0  resolver A: loader.load(1)
       cache.get(1) miss → push {key:1, resolve_A, reject_A}
       scheduled=false → queueMicrotask(_dispatch); scheduled=true
       return promise_1
     resolver B: loader.load(2)
       cache.get(2) miss → push {key:2, resolve_B, reject_B}
       scheduled=true → don't schedule again
       return promise_2
     resolver C: loader.load(1)
       cache.get(1) HIT → return same promise_1

t=microtask:   _dispatch()
       batch = [{key:1,...}, {key:2,...}]
       batchFn([1, 2]) → DB query → [u1, u2]
       resolve_A(u1); resolve_B(u2)
       resolver C's promise (== promise_1) → also u1
```

One DB query for three `.load()` calls.

## How to think aloud in the interview

> "Per-request loader. `load(key)` returns a promise and enqueues the resolver. End of tick — `queueMicrotask` — I dispatch one batch. `batchFn` returns values in input-key order; I resolve each promise. I cache the *promise*, not the value, so in-flight duplicates share. New loader per HTTP request to avoid cross-request leakage. For mutations I expose `clear(key)`. For DB safety, `maxBatchSize` caps per-batch keys."

## Important takeaways

- **One loader per request, never global.**
- **Cache the promise.** Covers in-flight duplicates.
- **`queueMicrotask` (or `Promise.resolve().then`).** Not `setTimeout`.
- **`batchFn` contract**: output array same length and order as input keys; per-key errors are returned as `Error` instances.
- **Pair with GraphQL** but works anywhere with N+1 risk.

## Variants

- **Custom cacheKeyFn** — for object keys, supply a string serializer.
- **`prime(key, value)`** — preload the cache (e.g., after a `WHERE id IN (...)` query, prime each id).
- **Returning a Map** — some implementations let `batchFn` return `Map<key, value>` instead of ordered array; the loader handles re-ordering.
- **Streaming results** — Async iterator variant; rarely needed in practice.
- **Bounded loader** — combine with a Semaphore to limit batch dispatch concurrency on slow databases.

## Revision notes

```
DataLoader(batchFn):
  load(key):
    if cache.has → return cached promise
    push {key,res,rej} to queue
    cache.set(key, promise)
    if !scheduled: queueMicrotask(_dispatch); scheduled=true
    return promise
  _dispatch():
    batch = queue.splice(0)
    values = await batchFn(keys)       # contract: same length/order
    map each value → resolve/reject
  
  per-request (not global)
  cache the promise (covers in-flight)
  queueMicrotask, not setTimeout
  maxBatchSize for DB limits
  clear(key) on mutation
```
