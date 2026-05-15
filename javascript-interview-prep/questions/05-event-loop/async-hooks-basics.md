# `AsyncLocalStorage` / `async_hooks` for request-scoped context

## Source
- Node.js docs: https://nodejs.org/api/async_context.html#class-asynclocalstorage
- async_hooks docs: https://nodejs.org/api/async_hooks.html
- Real-world usage: pino logger, OpenTelemetry, NestJS request-scoped providers, Fastify request context.
- Original RFC for AsyncLocalStorage: nodejs/node#36436.

## Why this question matters in interviews
Backend interviewers (especially at infra-heavy shops — Datadog, Stripe, payment companies) ask this because the alternative (passing `ctx` through every function signature) is a known anti-pattern and `AsyncLocalStorage` is the canonical solution. If you can explain that it's built on `async_hooks`, that it survives `await`/`Promise.then` boundaries, and that it gives you a **trace id / request id / user id** without polluting every signature — you've shown senior judgment. The follow-up is usually a memory-safety question (does it leak? can it grow unbounded?).

## Concepts involved

### The problem it solves
Without `AsyncLocalStorage`, you have two bad options:
1. **Thread the `ctx` through every function** — pollutes every signature, leaks abstractions, doesn't work across library boundaries.
2. **Stash on a module global** — broken under concurrency. Two requests in flight overwrite each other's globals.

`AsyncLocalStorage` gives you a **per-async-context store**. The store automatically follows the async call chain — across `await`, `setTimeout`, `Promise.then`, callback APIs. Two concurrent requests have two separate stores.

### Syntax to lock in
```js
const { AsyncLocalStorage } = require('node:async_hooks');
const als = new AsyncLocalStorage();

// Per-request setup (HTTP middleware)
app.use((req, res, next) => {
  als.run({ requestId: crypto.randomUUID(), userId: req.user?.id }, () => {
    next();
  });
});

// Deep in your code, anywhere — no parameter passing needed
function log(message) {
  const ctx = als.getStore();
  console.log(`[${ctx.requestId}]`, message);
}
```

### How it works (the senior-level explanation)
- Built on `async_hooks` — Node's low-level lifecycle hooks for async resources.
- Every async resource (Promise, Timer, FSReqCallback, etc.) is tracked. When you `await` or pass a callback, Node propagates the **execution context** automatically.
- `als.run(store, fn)` sets `store` as the active context. Any async work spawned inside `fn` inherits it.
- `als.getStore()` reads the currently-active store. Returns `undefined` if none.

### Edge cases
1. **`als.getStore()` returns undefined outside `als.run`** — always guard or default.
2. **Doesn't cross worker_threads** — workers have their own async contexts. Pass via `workerData`.
3. **Old C++ libraries that don't use async_hooks-aware APIs** can break propagation — extremely rare, but native addons (some old DB drivers) may not propagate context across their callbacks.
4. **Performance** — async_hooks has overhead (~5-10% in worst case). `AsyncLocalStorage` specifically was optimized in Node 16+ to be near-zero overhead when not used. Enabling it across the board is fine.
5. **Memory** — the store is held as long as the async call chain is reachable. If you stash a huge object, it stays in memory until the request finishes. Be deliberate about what you store.
6. **Detached promises** — if you `setInterval(fn)` from inside `als.run`, the interval inherits the context **forever** until cleared. Long-lived intervals + ALS = leak.
7. **Nested `als.run`** — replaces the store for the inner scope. Outer scope resumes after. Like a dynamic scope.
8. **Reading is sync, fast** — `als.getStore()` is a single TLS-like lookup. Cheap enough to call thousands of times per request.

## Brute force approach
"Pass `ctx` as the first arg to every function." Works for small codebases. Breaks at scale (typescript signatures balloon, library boundaries leak). Use only if you can't run Node 14+.

## Optimal approach
Wrap each request in `als.run(context, () => next())`. Anywhere downstream, read with `als.getStore()`. Build a tiny accessor:

```js
const als = new AsyncLocalStorage();
const getContext = () => als.getStore() ?? {};
const getRequestId = () => getContext().requestId;
```

For logging: hook into your logger to auto-inject `requestId` from ALS into every log line. For tracing: most OpenTelemetry SDKs use ALS under the hood.

## Solution (JavaScript)

### A minimal request-scoped context

```js
const http = require('node:http');
const crypto = require('node:crypto');
const { AsyncLocalStorage } = require('node:async_hooks');

const als = new AsyncLocalStorage();

// Logger that auto-tags every line with requestId
function log(level, msg, meta = {}) {
  const ctx = als.getStore() ?? {};
  console.log(JSON.stringify({
    level,
    msg,
    requestId: ctx.requestId ?? null,
    userId: ctx.userId ?? null,
    ...meta,
  }));
}

// Simulated DB layer (would normally need ctx for transaction)
async function dbFetchUser(id) {
  log('info', 'querying user', { id });    // logs with requestId automatically
  await new Promise(r => setTimeout(r, 50));
  return { id, name: 'Alice' };
}

// Simulated handler
async function handler(req, res) {
  log('info', 'request started');
  const user = await dbFetchUser(42);
  log('info', 'request done', { user });
  res.end(JSON.stringify(user));
}

// Server: wrap every request in a per-request store
http.createServer((req, res) => {
  const store = {
    requestId: crypto.randomUUID(),
    userId: req.headers['x-user-id'] ?? null,
    startedAt: Date.now(),
  };
  als.run(store, () => handler(req, res));
}).listen(3000);
```

Now hit the server with two concurrent requests:
```
$ curl localhost:3000 & curl localhost:3000 &
```

Logs are interleaved but each line carries the correct `requestId`. No ctx parameter was passed anywhere.

### Demonstrating cross-await propagation

```js
const als = new AsyncLocalStorage();

als.run({ id: 'A' }, async () => {
  console.log('start A:', als.getStore()?.id);    // A
  await new Promise(r => setTimeout(r, 100));
  console.log('after await A:', als.getStore()?.id);  // A — preserved!

  als.run({ id: 'B' }, () => {
    console.log('inside B:', als.getStore()?.id);     // B
  });

  console.log('after inner B, outer:', als.getStore()?.id);  // A
});

als.run({ id: 'C' }, async () => {
  await new Promise(r => setTimeout(r, 50));
  console.log('parallel C:', als.getStore()?.id);  // C — separate!
});
```

Output:
```
start A: A
parallel C: C
after await A: A
inside B: B
after inner B, outer: A
```

Two parallel "requests" (A and C) maintain isolated contexts. Inner `als.run(B)` shadows for its scope.

## Step-by-step dry run

```js
const als = new AsyncLocalStorage();

console.log('1:', als.getStore());              // undefined

als.run({ tag: 'X' }, async () => {
  console.log('2:', als.getStore().tag);        // X
  await Promise.resolve();
  console.log('3:', als.getStore().tag);        // X (preserved across await)
  setImmediate(() => {
    console.log('5:', als.getStore().tag);      // X (preserved into setImmediate)
  });
});

console.log('4:', als.getStore());              // undefined
```

Output order: `1 undefined`, `2 X`, `4 undefined`, `3 X`, `5 X`.

Trace:
- Line 1: not inside any `als.run` → `undefined`.
- `als.run` activates store `{tag:'X'}`. Async function runs sync portion: log `2 X`.
- `await Promise.resolve()` → continuation enqueued as microtask. Store context **captured**.
- After the async function suspends, line 4 runs — outside `als.run`, store is `undefined`.
- Microtask drains: continuation runs with store `{tag:'X'}` restored → log `3 X`.
- `setImmediate` queued with store captured.
- `setImmediate` fires → log `5 X`.

## Important takeaways

**Syntax to memorize**
- `new AsyncLocalStorage()` once at module top.
- `als.run(store, fn)` to set context for a scope.
- `als.getStore()` to read (returns undefined outside any run).
- `als.enterWith(store)` (rarely used) — set without callback; use only in well-defined hook points.
- `als.disable()` to fully turn off (rare).

**Patterns to reuse**
- **Request ID propagation** — set in HTTP middleware, read in logger.
- **User / tenant context** — read deep in business logic without parameter pollution.
- **Distributed tracing** — current span carried via ALS; OTel SDK does this for you.
- **Transaction context** — the DB connection / transaction handle stored in ALS, picked up by repository methods. (Care: this can leak connections if you don't clean up.)

**Common mistakes**
- Forgetting to `als.run(...)` at the top — `getStore()` returns undefined. Always default-handle.
- Storing huge objects in the store — they live until the chain completes.
- Using a global `setInterval` that captures ALS context indefinitely — leak.
- Assuming context propagates to worker_threads — it does not.
- Believing ALS is "free" — it has overhead, just small (~5%). Don't enable for trivial values when you can pass as args.

**Related questions**
- `async_hooks` low-level API
- `unhandledRejection` and request correlation
- Promise context loss in old codebases

## Variants

1. **"How would you implement ALS from scratch?"** — use `async_hooks.createHook` with `init`, `before`, `after`, `destroy` callbacks. Maintain a Map<asyncId, store>. In `init`, copy parent's store to the new resource. In `before`, set as current. In `after`/`destroy`, clean up. (~50 LOC for a basic version.)
2. **"Why doesn't ALS work across worker_threads?"** — workers are separate V8 isolates with their own async_hooks scheduler. Context is process-local.
3. **"How does OpenTelemetry use ALS?"** — every active span is stored in ALS. `tracer.startActiveSpan(name, fn)` wraps `fn` in `als.run(span, fn)`. Nested spans inherit and override.
4. **"Performance impact?"** — Node 16+ benchmarks show <2% on typical HTTP servers. Pre-16, it could hit 10%+. Always benchmark before sweeping changes.

## Revision notes

> **AsyncLocalStorage — 60 second recap**
> - Solves: "I need request-scoped context (requestId, userId, txn) without threading it through every function."
> - Built on async_hooks; survives `await`, `Promise.then`, `setTimeout`, callbacks.
> - `als.run(store, fn)` to enter; `als.getStore()` to read.
> - Per-request isolation: two concurrent requests have two separate stores.
> - **Used by**: pino logger, OpenTelemetry, NestJS scopes, Fastify request context.
> - **Trap**: stashing huge objects → memory bloat. Long-lived intervals inside `als.run` → leak.
> - **Trap**: doesn't cross worker_threads. Pass via `workerData`.
> - Replaces explicit ctx threading and global-state hacks.
