# DataLoader — per-request batch + cache for N+1 problem

> **Difficulty:** Medium-Senior   |   **Time:** ~25 min   |   **Prereqs:** [batched-request-coalescer.md](./batched-request-coalescer.md), [`04-promises/microtask-drainer.md`](../04-promises/microtask-drainer.md)
>
> **Source:** Facebook's `dataloader` (Lee Byron, 2015). Asked at Shopify, Stripe, GitHub, Atlassian, Razorpay — anywhere with GraphQL.

---

## 1. Problem statement

**Signature**
```ts
class DataLoader<K, V> {
  constructor(batchFn: (keys: K[]) => Promise<(V | Error)[]>, opts?: { maxBatchSize?: number; cache?: boolean });
  load(key: K): Promise<V>;
  clear(key: K): this;
  clearAll(): this;
  prime(key: K, value: V): this;
}
```

**Input / Output examples**

| Setup                                                | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| 100 resolvers call `loader.load(id)` in one tick     | one `batchFn([100 ids])` call; 100 promises resolved   |
| Two `load(42)` in same tick                           | shared promise — one entry in batch                    |
| `load(42)` then later `load(42)`                      | cache hit — returns same promise                       |
| `batchFn` returns `[v1, Error, v3]`                  | promise 2 rejects with that Error                      |
| `batchFn` throws                                      | all promises in batch reject                            |
| Per-HTTP-request loader vs global                     | per-request — avoid cross-user leak                    |

**Constraints**
- Batch within a single microtask (`queueMicrotask`).
- `batchFn` output array: same length AND ORDER as input keys.
- Cache the **Promise** (not the value) — covers in-flight duplicates.
- One loader per request, NEVER global.

---

## 2. Plain-English restatement

A GraphQL resolver naively calls `getUser(id)` 100 times across a request — 100 DB hits (N+1). DataLoader collects those `.load(id)` calls within one event-loop tick, dispatches one `batchFn([id1..id100])`, then resolves each promise. Also caches by key per-request: repeated `.load(42)` shares the same promise.

---

## 3. Why this matters in interviews

Solves the **N+1 problem** at the *application* layer. Tests microtask scheduling, promise lifecycle, cache scope. Underpins every GraphQL Node backend.

---

## 4. Mental model

```
   Within one event-loop tick:
   resolver A: loader.load(1) ──┐
   resolver B: loader.load(2) ──┤  push into queue + cache
   resolver C: loader.load(1) ──┤  cache hit on (1) → shared promise
   resolver D: loader.load(3) ──┘  queueMicrotask scheduled (deduped)

   End of tick: _dispatch()
     batch = [{key:1}, {key:2}, {key:3}]
     batchFn([1, 2, 3]) → [v1, v2, v3]   ← one DB query
     resolve each promise

   3 distinct keys → 1 DB call → 4 satisfied callers
```

**Key insight:** `queueMicrotask` defers to end of tick but BEFORE next macrotask. `setTimeout(0)` would batch too late (across macrotask boundary).

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why cache the Promise, not the value?
> 2. What's wrong with `setTimeout(0)` instead of `queueMicrotask`?
> 3. Why "one loader per request, never global"?

---

## 6. Brute force — walked through

### Wrong attempt 1: naive resolver
```js
async function user(post) { return getUser(post.userId); }
```
100 posts → 100 DB hits. N+1.

### Wrong attempt 2: `setTimeout(0)` for batching
Macrotask — batches AFTER microtask queue drains. Other Promise chains might starve.

### Wrong attempt 3: cache value (not promise)
Two concurrent `load(42)` callers before resolution → both miss → both push → batch contains `42` twice → wasted work or wrong contract.

### Wrong attempt 4: global loader
Cross-request leakage. User A's stale data leaks to user B.

---

## 7. The unlocking insight

> **Per-request loader. `load(key)` pushes `{key, resolve, reject}` to queue and caches the Promise. Schedule one `queueMicrotask` (deduped). Microtask drains: `batchFn(keys)` once; map output array (same length+order) back to promises.**

Three properties:

1. **`queueMicrotask`** = same-tick batching.
2. **Cache the Promise** — covers in-flight duplicates.
3. **Per-request scope** — avoid cross-user leakage.

---

## 8. Solution (annotated)

```js
class DataLoader {
  constructor(batchFn, { maxBatchSize = Infinity, cache = true } = {}) {
    this.batchFn = batchFn;                                          // step 1: async batch
    this.maxBatchSize = maxBatchSize;
    this.cache = cache ? new Map() : null;
    this.queue = [];
    this.scheduled = false;
  }

  load(key) {
    if (this.cache?.has(key)) return this.cache.get(key);            // step 2: cache hit
    const p = new Promise((resolve, reject) => {
      this.queue.push({ key, resolve, reject });
    });
    if (this.cache) this.cache.set(key, p);                          // step 3: cache the PROMISE
    if (!this.scheduled) {
      this.scheduled = true;
      queueMicrotask(() => this._dispatch());                         // step 4: end-of-tick drain
    }
    return p;
  }

  async _dispatch() {
    this.scheduled = false;
    const batch = this.queue.splice(0, this.queue.length);
    for (let i = 0; i < batch.length; i += this.maxBatchSize) {
      const slice = batch.slice(i, i + this.maxBatchSize);
      try {
        const values = await this.batchFn(slice.map((b) => b.key));
        if (values.length !== slice.length) {
          throw new Error('batchFn must return array same length as keys');
        }
        slice.forEach((b, idx) =>
          values[idx] instanceof Error ? b.reject(values[idx]) : b.resolve(values[idx]),
        );
      } catch (err) {
        slice.forEach((b) => b.reject(err));
      }
    }
  }

  clear(key)   { this.cache?.delete(key); return this; }
  clearAll()   { this.cache?.clear(); return this; }
  prime(key, value) {
    if (this.cache && !this.cache.has(key)) this.cache.set(key, Promise.resolve(value));
    return this;
  }
}
```

**Try it yourself**

```js
// Per-request setup (e.g., in Apollo context function)
const userLoader = new DataLoader(async (ids) => {
  const rows = await db.query('SELECT * FROM users WHERE id = ANY($1)', [ids]);
  const byId = new Map(rows.map((r) => [r.id, r]));
  return ids.map((id) => byId.get(id) ?? new Error(`User ${id} not found`));
});

// In resolvers
const u1      = userLoader.load(1);
const u2      = userLoader.load(2);
const u1Again = userLoader.load(1);   // shares promise with first
const [r1, r2, r3] = await Promise.all([u1, u2, u1Again]);
// One DB query: SELECT ... WHERE id IN (1, 2)
```

---

## 9. Step-by-step dry run

```
t=0  resolver A: loader.load(1)
       cache.get(1) miss → push {key:1, resA, rejA}
       scheduled=false → queueMicrotask(_dispatch); scheduled=true
       cache.set(1, promise_1)
       return promise_1
     resolver B: loader.load(2)
       cache.get(2) miss → push {key:2, resB, rejB}
       scheduled=true → DON'T schedule again
       cache.set(2, promise_2)
       return promise_2
     resolver C: loader.load(1)
       cache.get(1) HIT → return promise_1   ← shared

t=microtask:   _dispatch()
       scheduled=false
       batch = [{key:1, resA}, {key:2, resB}]
       batchFn([1, 2]) → DB → [u1, u2]
       resA(u1)
       resB(u2)
     promise_1 fulfilled with u1; resolver C sees u1 too (same promise)

Final: ONE DB query for THREE .load() calls.
```

---

## 10. Common confusion + traps

1. **`setTimeout(0)`** — macrotask, batches too late.
2. **Cache value not promise** — in-flight duplicates miss.
3. **Global loader** — cross-request leak.
4. **`batchFn` returns wrong-length array** — caller's mapping breaks; throw loudly.
5. **`batchFn` reorders output** — output[i] must correspond to keys[i].
6. **Forget `clear(key)` on mutation** — stale read after update.
7. **Object keys without `cacheKeyFn`** — Map uses reference equality; identical-shape objects miss.

---

## 11. Senior follow-ups & variants

### Variant 1 — `cacheKeyFn` for object keys
Serializer turns object keys into stable strings for hashing.

### Variant 2 — Map-returning batchFn
Return `Map<key, value>`; loader handles re-ordering. Avoids order-coupling.

### Variant 3 — `prime(key, value)`
Preload cache (e.g., after `WHERE id IN (...)` query, prime each).

### Variant 4 — Bounded loader
Pair with semaphore to cap batch concurrency on slow databases.

### Variant 5 — Streaming results
Async iterator variant for huge result sets. Rare in practice.

### Variant 6 — Cross-request shared cache layer
Separate concern from per-request loader: e.g., Redis + DataLoader on top.

---

## 12. How to think aloud

> "Per-request loader. `load(key)` returns a Promise, enqueues `{key, resolve, reject}`, caches the promise (NOT the value — covers in-flight duplicates). Schedule `queueMicrotask` (deduped); microtask drains the queue, calls `batchFn(keys)` once. Output array contract: same length and order as input keys (or return a Map for safer reordering). Per-error: `Error` instance in output array rejects that one. Per-batch: thrown `batchFn` rejects all in batch. `queueMicrotask` is end-of-tick — `setTimeout(0)` would batch too late. One loader per HTTP request — global causes cross-user leaks. Trap: cache value (in-flight miss); setTimeout(0); wrong-length output."

---

## 13. 60-second revision

> - **Per-request loader; cache the PROMISE (not value).**
> - **`queueMicrotask`** for end-of-tick batching (NOT `setTimeout(0)`).
> - **`batchFn` contract:** output array same length AND ORDER as keys.
> - **Per-key error:** `Error` instance in slot. **Per-batch error:** all reject.
> - **`maxBatchSize`** caps DB parameter limits.
> - **`clear(key)`/`clearAll()`** on mutations.
> - **`prime(key, value)`** to preload after batch queries.
> - **Trap:** global loader (cross-user leak); cache value; setTimeout(0); wrong-length output.

---

**Related:** [batched-request-coalescer.md](./batched-request-coalescer.md) · [memoize.md](./memoize.md) · [memoize-ii.md](./memoize-ii.md) · [cache-stampede-single-flight.md](./cache-stampede-single-flight.md) · [`04-promises/microtask-drainer.md`](../04-promises/microtask-drainer.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md)
