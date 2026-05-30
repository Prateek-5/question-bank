# Deferred pattern — `Promise.withResolvers()`

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [build-promise-from-scratch.md](./build-promise-from-scratch.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** TC39 ES2024; popularized by jQuery's `$.Deferred` (2009). <a href="https://github.com/tc39/proposal-promise-with-resolvers" target="_blank" rel="noopener noreferrer">Proposal</a>.

---

## 1. Problem statement

**Signature**
```ts
function deferred<T>(): { promise: Promise<T>; resolve(v: T): void; reject(e: any): void };
// Or use ES2024 native: Promise.withResolvers()
```

**Input / Output examples**

| Code                                                                  | Behaviour                                       |
|-----------------------------------------------------------------------|--------------------------------------------------|
| `const { promise, resolve } = deferred(); setTimeout(() => resolve('done'), 100); await promise;` | yields `'done'` at t=100 |
| Settle from inside an event handler (`emitter.once('event', resolve)`) | wraps an event-emitter into a promise         |
| Call `resolve(...)` twice                                              | second call no-op (Promise locks on first settle) |
| Call `reject(...)` after `resolve(...)`                                | no-op                                            |
| Never settle the deferred                                              | promise pending forever (memory leak if retained) |

**Constraints**
- Hands you `{ promise, resolve, reject }` so you can settle from **outside** the executor.
- ES2024 native: `Promise.withResolvers()` (Node 22+, Chrome 119+, Firefox 121+, Safari 17.4+).
- Polyfill is 4 lines.
- Used when settlement happens in a different code path from the call site (callbacks, socket replies, queue dispatchers).

---

## 2. Plain-English restatement

Sometimes you need to create a Promise *and* hold onto its `resolve` and `reject` so you can settle it from elsewhere — an event listener, an incoming socket message, a job queue handler. The Deferred pattern hands you a tuple of `{ promise, resolve, reject }`. ES2024 ships this as `Promise.withResolvers()`. Before ES2024, you write the same thing in 4 lines.

---

## 3. Why this matters in interviews

Most code uses `new Promise((resolve, reject) => ...)` where the executor *is* the place that settles. But sometimes you need to **resolve from outside** the constructor — event handlers, message-bus replies, async queues, deferred-event waits. The Deferred pattern handles this. Interviewers probe it when discussing **promise pools**, **request/reply correlation**, **WebSocket request matching**, and **why senior code suddenly stops using `new Promise` in some places**. ES2024 made it a one-liner — knowing the native form is "I'm current."

---

## 4. Mental model

`new Promise((res, rej) => ...)` keeps `res` and `rej` local to the executor. The deferred pattern leaks them deliberately by writing to outer variables, so external code can settle later.

```
   Standard Promise:
   ┌─────────────────────────────────────┐
   │ new Promise((resolve, reject) => {  │
   │   // resolve/reject are LOCAL       │
   │   doWork().then(resolve, reject);   │
   │ })                                  │
   └─────────────────────────────────────┘

   Deferred pattern:
   ┌─────────────────────────────────────────┐
   │ let resolve, reject;                    │
   │ const promise = new Promise((res, rej) =>│
   │ {                                       │
   │   resolve = res;  reject = rej;         │ ← leak to outer scope
   │ });                                     │
   │ return { promise, resolve, reject };    │
   └─────────────────────────────────────────┘

   Now external code can call resolve(x) when the right event happens.
```

**Use case: request/reply correlation.** Send a request with an ID; store `{ resolve, reject }` keyed by ID; when a reply comes in, look up the deferred and settle it. This is **impossible** with raw `new Promise` because the promise has to be returned synchronously while the settlement happens later.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Without the Deferred pattern, how would you wrap `emitter.once('data', cb)` into a promise?
> 2. If you call `resolve('a')` then `resolve('b')` on the same deferred, what does the promise resolve to?
> 3. If you store a deferred in a Map keyed by request ID, but never receive a matching reply, what happens to that promise?

---

## 6. Brute force — walked through

### Wrong attempt 1: nest everything inside the executor

```js
function rpcCall(id, socket) {
  return new Promise((resolve, reject) => {
    socket.on('message', (msg) => {
      if (msg.id === id) resolve(msg.result);
    });
    socket.send({ id, method: 'getUser' });
  });
}
```

**Works** for one call. But registering a listener per call leaks — the listener fires for every message, not just the matching ID. Multiple in-flight calls collide. The clean version uses a deferred + a shared Map (see Variant 1).

### Wrong attempt 2: add a `settled` flag

```js
function deferred() {
  let resolve, reject;
  let settled = false;
  const promise = new Promise((res, rej) => {
    resolve = (v) => { if (!settled) { settled = true; res(v); } };
    reject  = (e) => { if (!settled) { settled = true; rej(e); } };
  });
  return { promise, resolve, reject };
}
```

Works, but the `settled` guard is **redundant**. Promises already lock on first settle — subsequent `res`/`rej` calls are silent no-ops by spec. Belt-and-suspenders code is noise.

### Wrong attempt 3: return the resolvers directly

```js
function deferred() {
  const promise = new Promise((res, rej) => { /* ... */ });
  return [promise, res, rej];  // BUG: variables don't escape the executor scope
}
```

`res` and `rej` are *inside* the executor; you can't reach them from outside the function. Must assign to outer-scoped `let` variables before the executor returns.

---

## 7. The unlocking insight

> **The Promise executor runs synchronously — so by the time `new Promise(...)` returns, you've already had a chance to capture `resolve` and `reject` into outer-scope variables.**

The four-line polyfill:

```js
function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}
```

Three properties:

1. **The executor is synchronous.** It runs *during* `new Promise(...)`. By the time the constructor returns, `resolve` and `reject` are already assigned in the outer scope.
2. **Order is guaranteed.** No race: the executor *must* finish before `new Promise` returns. So `resolve` and `reject` are always set before you return the deferred tuple.
3. **State-once-locked.** The promise can only settle once. Calling `resolve` again or `reject` after `resolve` is a silent no-op. No defensive flag needed.

ES2024's `Promise.withResolvers()` is exactly this — sugar with the same semantics. Use it where available; polyfill otherwise.

**The canonical use case** is the **request/reply correlation Map** — keyed by request ID, each entry stores a deferred. Incoming messages look up the matching deferred and settle it. Without the pattern, this requires nesting every callback inside the constructor, which doesn't compose.

---

## 8. Solution (annotated)

```js
// Polyfill (works on every runtime that has Promise)
if (!Promise.withResolvers) {
  Promise.withResolvers = function () {
    let resolve, reject;
    const promise = new this((res, rej) => {              // step 1: executor runs synchronously
      resolve = res;                                       // step 2: capture into outer scope
      reject = rej;
    });
    return { promise, resolve, reject };                  // step 3: return the tuple
  };
}

// Use it
const { promise, resolve, reject } = Promise.withResolvers();
```

**Canonical use case — request/reply over a message bus**

```js
class RequestReply {
  constructor(socket) {
    this.socket = socket;
    this.pending = new Map();                              // id → { resolve, reject }
    socket.on('message', (raw) => this._onMessage(raw));
  }

  send(method, params) {
    const id = crypto.randomUUID();
    const { promise, resolve, reject } = Promise.withResolvers();
    this.pending.set(id, { resolve, reject });
    this.socket.send(JSON.stringify({ id, method, params }));
    return promise;
  }

  _onMessage(raw) {
    const { id, result, error } = JSON.parse(raw);
    const entry = this.pending.get(id);
    if (!entry) return;                                    // unknown id — ignore
    this.pending.delete(id);
    if (error) entry.reject(new Error(error));
    else entry.resolve(result);
  }
}
```

The promise is returned synchronously, but its resolver is held in the Map for later use when the matching reply arrives. **This is impossible to write cleanly with raw `new Promise`.**

---

## 9. Step-by-step dry run

Input:

```js
const rpc = new RequestReply(fakeSocket);
const p1 = rpc.send('getUser', { id: 1 });        // returns deferred's promise
const p2 = rpc.send('getOrder', { id: 99 });

// Later, replies arrive
fakeSocket.emit('message', JSON.stringify({ id: 'abc', result: { name: 'Ava' } }));
fakeSocket.emit('message', JSON.stringify({ id: 'def', error: 'Not found' }));
```

Values-first trace:

| Time | Event                                                              | `pending` Map                                | State        |
|------|---------------------------------------------------------------------|----------------------------------------------|---------------|
| 0    | `rpc.send('getUser', ...)`: generate id='abc'; deferred returns `{P1, r1, rj1}` | `{ 'abc': {r1, rj1} }`                  | P1 pending   |
| 0    | `rpc.send('getOrder', ...)`: id='def'; deferred returns `{P2, r2, rj2}` | `{ 'abc': ..., 'def': {r2, rj2} }`       | P2 pending   |
| 10   | socket emits reply id='abc'; `_onMessage`: `r1({name:'Ava'})`        | `{ 'def': {r2, rj2} }`                      | P1 fulfilled |
| 20   | socket emits reply id='def'; `_onMessage`: `rj1(Error('Not found'))` | `{}`                                         | P2 rejected  |

`await p1` → `{ name: 'Ava' }`. `await p2` throws `'Not found'`. Both run in parallel; settlement is correlated by ID.

---

## 10. Common confusion + traps

1. **Adding a `settled` guard.**
   Redundant. The Promise spec already locks on first settle. Don't write defensive flags.

2. **Holding the deferred forever.**
   Long-lived deferreds with no settle path leak memory — and any resources reachable from the resolver. Always have a settle or a timeout.

3. **Exposing the resolvers publicly.**
   Anyone can settle the promise from outside. Encapsulate. Don't return them from your library API.

4. **Using deferred when the executor would do.**
   Code smell. Use `new Promise((res, rej) => ...)` when settlement happens *inside* the executor's natural scope. Use deferred only when settlement is in a different code path.

5. **Race: external `reject` after async `resolve` already queued.**
   First wins. If `resolve(x)` was already called (state locked), subsequent `reject` is a no-op.

6. **Error in `then` chain doesn't reject the deferred.**
   `deferred.promise.then(...).catch(...)` only affects the chain. The original promise stays in its settled state.

7. **`Promise.withResolvers` polyfill** is a one-liner — safe to add globally if the runtime is too old.

---

## 11. Senior follow-ups & variants

### Variant 1 — Deferred with timeout

```js
function deferredWithTimeout(ms) {
  const { promise, resolve, reject } = Promise.withResolvers();
  const timer = setTimeout(() => reject(new Error('timeout')), ms);
  const wrap = (fn) => (v) => { clearTimeout(timer); fn(v); };
  return { promise, resolve: wrap(resolve), reject: wrap(reject) };
}
```

Self-cleaning timer; safe against double-settle.

### Variant 2 — One-shot event-to-promise

```js
function eventToPromise(emitter, eventName, errorEventName = 'error') {
  const { promise, resolve, reject } = Promise.withResolvers();
  emitter.once(eventName, resolve);
  if (errorEventName) emitter.once(errorEventName, reject);
  return promise;
}
```

Common helper for wrapping EventEmitters.

### Variant 3 — Pipe one promise to another

```js
function pipe(source, deferred) {
  source.then(deferred.resolve, deferred.reject);
}
```

Useful when routing the result of one promise into a deferred owned elsewhere — e.g., in middleware chains.

### Variant 4 — Multi-resolve "Subject" (relaxes single-settle)

The Deferred is single-shot by Promise spec. If you want many values over time (event stream), use an Observable / Subject instead. See [`10-machine-coding-patterns/observable-subject.md`](../10-machine-coding-patterns/observable-subject.md).

### Variant 5 — `AsyncIterator` from a deferred queue

A push-into / pull-out queue where pushes resolve the next pending pull's deferred:

```js
function asyncQueue() {
  const buf = [];
  const waiters = [];
  return {
    push(v) {
      if (waiters.length) waiters.shift().resolve(v);
      else buf.push(v);
    },
    [Symbol.asyncIterator]() {
      return {
        next: () => {
          if (buf.length) return Promise.resolve({ value: buf.shift(), done: false });
          const { promise, resolve } = Promise.withResolvers();
          waiters.push({ resolve });
          return promise.then((value) => ({ value, done: false }));
        },
      };
    },
  };
}
```

Used internally by Node's `stream.Readable` async iterator and many event-driven async libraries.

---

## 12. How to think aloud in the interview

> "Deferred is `{ promise, resolve, reject }` — hands the resolvers out to outer scope so I can settle the promise from somewhere else. Four-line polyfill: `let resolve, reject; const promise = new Promise((res, rej) => { resolve = res; reject = rej; });`. ES2024 ships it as `Promise.withResolvers()`. The Promise executor runs synchronously, so by the time `new Promise` returns, the resolvers are already captured. Canonical use: request/reply correlation — Map keyed by request ID, each entry stores a deferred; incoming replies look up the matching one and settle it. Don't add a `settled` flag — Promises already lock on first settle. Always have a settle path or a timeout; orphaned deferreds leak memory."

---

## 13. 60-second revision

> - **Pattern:** `let resolve, reject; const promise = new Promise((res, rej) => { resolve = res; reject = rej; });`
> - **Native (ES2024):** `Promise.withResolvers()`.
> - **Use when** settlement happens in a different code path than the call site (callbacks, socket replies, queue dispatchers).
> - **Don't add `settled` flag** — Promise spec locks on first settle.
> - **Always have a settle path** — orphaned deferreds leak memory.
> - **Foundation of:** request/reply RPC, priority queues, async-memoize (cache in-flight), event-to-promise, AsyncIterator queues.
> - **Trap:** holding a deferred forever; exposing resolvers publicly; using deferred when raw `new Promise` would do.

---

**Related:** [build-promise-from-scratch.md](./build-promise-from-scratch.md) · [priority-async-queue.md](./priority-async-queue.md) · [async-memoize.md](./async-memoize.md) · [async-mutex.md](./async-mutex.md) · [`10-machine-coding-patterns/cancellable-promise-wrapper.md`](../10-machine-coding-patterns/cancellable-promise-wrapper.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
