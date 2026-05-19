# `AsyncLocalStorage` — request-scoped context

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [event-loop-concurrency.md](./event-loop-concurrency.md), [microtask-macrotask-order.md](./microtask-macrotask-order.md)
>
> **Source:** Node `node:async_hooks`. pino, OpenTelemetry, NestJS, Fastify use it. Datadog, Stripe, payment companies.

---

## 1. Problem statement

How do you propagate request-scoped state (request ID, user ID, trace ID) through async call chains without threading `ctx` through every function signature?

**Verification examples**

| Setup                                                | Behaviour                                              |
|------------------------------------------------------|---------------------------------------------------------|
| `als.run({reqId: 'abc'}, () => handler())`           | inside handler + nested awaits, `als.getStore()` returns `{reqId:'abc'}` |
| Two concurrent requests                              | each sees own store (per-async-context)                |
| Survives `await`, `Promise.then`, `setTimeout`        | context propagates through callback chain              |
| `worker_threads`                                     | NOT propagated to worker (separate isolate)           |
| Store mutated                                         | sees same store object across chain                    |

**Constraints**
- Per-async-context store; survives async boundaries.
- Built on `async_hooks` (Node internal API).
- Doesn't propagate to worker threads.
- Some overhead (~5-10% on hot paths).

---

## 2. Plain-English restatement

A "thread-local-like" store that follows the async call chain. Set up in a middleware (`als.run(store, callback)`); inside `callback` and any awaits/Promises spawned by it, `als.getStore()` returns the same store. Two concurrent requests have two separate stores. No more threading `ctx` through every function.

---

## 3. Why this matters in interviews

Backend infra question. Alternatives are anti-patterns: thread ctx everywhere (pollutes signatures) or stash on global (broken under concurrency). Tests `async_hooks` literacy + production observability awareness.

---

## 4. Mental model

```
   Without ALS:
   handler(req, ctx) → db.query(sql, ctx) → log.info('done', ctx) → ...
   ctx threads through EVERY signature; library boundaries leak ctx.

   With ALS:
   middleware: als.run({reqId, userId}, () => handler(req))
                ↓ async chain
   handler() — calls als.getStore() to read context
     ↓ await db.query(sql)
   db.query() — calls als.getStore() — same context!
     ↓ await pool.connect()
   logger — calls als.getStore() — same context!

   Two concurrent requests:
   req1: als.run({reqId: 1}, handler) ──▶ all awaits see {reqId: 1}
   req2: als.run({reqId: 2}, handler) ──▶ all awaits see {reqId: 2}

   Built on async_hooks: every async resource (Promise, Timeout, ...) tracks
   parent context. Store follows.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does the store survive `await`?
> 2. Does the store propagate to a `worker_threads.Worker`?
> 3. What's the cost — free or measurable?

---

## 6. Brute force — walked through

### Wrong attempt 1: thread ctx through every function
Pollutes signatures; library boundaries leak ctx; refactor pain.

### Wrong attempt 2: module-level global
Race: two concurrent requests overwrite each other's globals.

### Wrong attempt 3: store on `Request` object
Have to pass `req` everywhere → same as threading ctx.

---

## 7. The unlocking insight

> **`als.run(store, callback)` sets store for the entire async chain spawned from callback. `als.getStore()` reads from within. Built on `async_hooks` so it survives `await`, `Promise.then`, `setTimeout`, callback APIs. Two concurrent requests have two separate stores.**

Three properties:

1. **Per-async-context store** — survives async boundaries.
2. **`async_hooks` plumbing** — tracks parent context across resources.
3. **Doesn't cross workers** — separate V8 isolate.

---

## 8. Solution (annotated)

```js
const { AsyncLocalStorage } = require('node:async_hooks');
const als = new AsyncLocalStorage();

// Express middleware
app.use((req, res, next) => {
  const store = { requestId: crypto.randomUUID(), userId: req.user?.id };
  als.run(store, () => {                                              // step 1: scope creation
    next();
  });
});

// In any deep function — pino logger reads context automatically
const logger = pino({
  mixin() {
    return als.getStore() ?? {};                                       // step 2: read context
  },
});

// Or manually
async function deepFunction() {
  const ctx = als.getStore();
  logger.info({ ...ctx, event: 'something' });
  await db.query('...');
  // ctx still accessible after await
  console.log(als.getStore().requestId);                              // same store
}
```

**Try it yourself**

```js
// Concurrent requests don't pollute each other
async function handler(reqId) {
  await new Promise((r) => setTimeout(r, Math.random() * 100));
  console.log('req', reqId, 'sees', als.getStore().requestId);
}

als.run({ requestId: 1 }, () => handler(1));
als.run({ requestId: 2 }, () => handler(2));
// Output:
// req 1 sees 1
// req 2 sees 2
// (separate stores even though setTimeout interleaves)

// Worker_threads — does NOT propagate
const worker = new Worker('./worker.js');
worker.postMessage({});
// Inside worker: als.getStore() → undefined (separate V8 isolate)
```

---

## 9. Step-by-step dry run

```
Request 1 arrives:
  middleware: als.run({reqId: 'a'}, () => next())
  → enters async context A
  
  handler runs in context A:
    als.getStore() → {reqId: 'a'} ✓
    await db.query(...)        ← async_hooks tracks parent context A
    (microtask continuation also in context A)
    als.getStore() → {reqId: 'a'} ✓
    
  Request 2 arrives during request 1's await:
    als.run({reqId: 'b'}, () => next())
    → enters async context B
    handler runs in context B:
      als.getStore() → {reqId: 'b'} ✓
    
  Both run concurrently with separate stores.

Test: worker thread
  als.run({reqId: 'c'}, () => {
    const worker = new Worker('./worker.js');
    // inside worker.js: als is a different instance; getStore() → undefined
  });
```

---

## 10. Common confusion + traps

1. **`getStore` outside `run`** — returns `undefined`.
2. **Propagates to workers** — no, separate isolate.
3. **Free runtime cost** — measurable ~5-10% on hot paths.
4. **Mutating the store** — visible to all in chain.
5. **`als.exit(callback)`** — runs callback OUTSIDE the current context.
6. **Multiple `als` instances** — independent; each tracks own store.
7. **Old `domain` API** — deprecated; ALS is the modern replacement.

---

## 11. Senior follow-ups & variants

### Variant 1 — OpenTelemetry integration
Span context propagated automatically via ALS; trace ID survives async boundaries.

### Variant 2 — pino logger mixin
`mixin: () => als.getStore()` injects requestId into every log line.

### Variant 3 — NestJS request-scoped providers
Backed by ALS under the hood.

### Variant 4 — Manual `async_hooks`
Lower-level API; track every async resource (`init`, `before`, `after`, `destroy`). ALS sits on top.

### Variant 5 — Browser equivalent
None standard; React's Context API for component tree; AsyncContext proposal at TC39.

### Variant 6 — Memory leaks
Stores held until async chain completes; long-lived chains (open WebSockets) hold stores forever.

---

## 12. How to think aloud

> "`AsyncLocalStorage` gives you a per-async-context store that follows the async call chain — across `await`, `Promise.then`, `setTimeout`, callback APIs. Set in HTTP middleware via `als.run(store, callback)`; read anywhere via `als.getStore()`. Two concurrent requests have two separate stores. Built on `async_hooks` — Node tracks parent context for every async resource. Doesn't propagate to `worker_threads` (separate V8 isolate). ~5-10% overhead on hot paths. Modern replacement for the deprecated `domain` API. Used by pino, OpenTelemetry, NestJS, Fastify. Trap: getStore outside run; assumption of worker propagation; memory leaks via long-lived chains."

---

## 13. 60-second revision

> - **`als.run(store, callback)`** sets store for async chain spawned from callback.
> - **`als.getStore()`** reads current context — survives `await`, `Promise.then`, timers, callbacks.
> - **Concurrent requests** have separate stores (per-async-context).
> - **`async_hooks`** tracks parent context for every async resource.
> - **Does NOT propagate to workers** (separate V8 isolate).
> - **~5-10% overhead** on hot paths.
> - **Used by:** pino, OpenTelemetry, NestJS, Fastify.
> - **Replaces** deprecated `domain` API.
> - **Trap:** getStore outside run; worker propagation; long-lived chain leaks.

---

**Related:** [event-loop-concurrency.md](./event-loop-concurrency.md) · [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) · [`10-machine-coding-patterns/dependency-injection-container.md`](../10-machine-coding-patterns/dependency-injection-container.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md)
