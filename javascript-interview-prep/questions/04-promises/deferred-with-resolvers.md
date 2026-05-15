# Deferred pattern / `Promise.withResolvers` (ES2024)

## Source
- Classic JS pattern, popularized in jQuery's `$.Deferred` (2009) — still widely used in libraries.
- Standardized as `Promise.withResolvers()` in ES2024 (Node 22+, Chrome 119+, Firefox 121+, Safari 17.4+).
- TC39 proposal: https://github.com/tc39/proposal-promise-with-resolvers

## Why this question matters in interviews
Most code uses the Promise constructor's executor (`new Promise((resolve, reject) => ...)`) — but sometimes you need to **resolve from outside** the constructor (event handlers, message-bus replies, async queues, deferred-event waits). The Deferred pattern hands you a tuple of `{ promise, resolve, reject }` so you can store the resolvers on `this` and settle later. Interviewers probe this when discussing: **promise pools**, **request/reply correlation**, **WebSocket request matching**, and **why senior code suddenly stops using `new Promise` in some places**. ES2024 made it a one-liner — knowing the native form is "I'm current."

## Concepts involved

### Syntax to lock in
```js
// Manual implementation (works everywhere)
function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

// ES2024 native
const { promise, resolve, reject } = Promise.withResolvers();
```

### Runtime / engine behavior
- Inside the executor, `resolve` and `reject` are local — they don't leak. The deferred pattern leaks them deliberately by writing to outer variables.
- The Promise is created synchronously; the resolvers are extracted synchronously. **Order is guaranteed** because the executor runs immediately during `new Promise(...)`.
- `Promise.withResolvers()` is sugar — the runtime returns a `{ promise, resolve, reject }` plain object. No deeper semantics.
- Storing resolvers in an outer scope creates a closure-style retention — be aware of memory implications for long-lived deferreds.

### Edge cases (interview traps)
1. **Double-settling** — calling `resolve` after `reject` (or twice) is a no-op (state-locked). Mention this; don't add a defensive flag yourself.
2. **Never settling** — the promise stays pending forever. Memory leak if the deferred is retained anywhere.
3. **`Promise.withResolvers` polyfill** — one-liner; trivial to add for older runtimes.
4. **Returning the resolvers directly** — exposes mutation power. Don't accidentally hand them to untrusted code.
5. **Error in `then` chain doesn't reject the deferred** — `deferred.promise.then(...).catch(...)` only affects the chain, not the original promise.
6. **Race: external `reject` after async `resolve` already queued** — first wins. Counter-intuitive at first.

## Brute force approach
"Just use `new Promise((res, rej) => ...)` everywhere." Fine for self-contained async ops, but **breaks down** when the settlement event is on a different code path (a callback from an external API, an incoming socket message). Without the deferred pattern, you'd have to nest everything inside the executor.

## Optimal approach
Use the deferred pattern when settlement happens outside the constructor's natural lexical scope. Prefer `Promise.withResolvers()` if the runtime supports it. Otherwise, the 4-line manual version is portable forever.

## Solution (JavaScript)

```js
// Polyfill — works on every runtime that has Promise
if (!Promise.withResolvers) {
  Promise.withResolvers = function () {
    let resolve, reject;
    const promise = new this((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve, reject };
  };
}

// --- Practical use: request/reply over a message bus ---
class RequestReply {
  constructor(socket) {
    this.socket = socket;
    this.pending = new Map(); // id -> { resolve, reject }
    socket.on('message', (msg) => this._onMessage(msg));
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
    if (!entry) return; // unknown id (timeout/duplicate) — ignore
    this.pending.delete(id);
    if (error) entry.reject(new Error(error));
    else entry.resolve(result);
  }
}
```

The `RequestReply` class is the canonical use case: when a reply arrives, we have an `id` in hand, look up the matching deferred, and settle it. There's **no way** to do this cleanly with raw `new Promise`.

## Step-by-step dry run

Input:
```js
const rpc = new RequestReply(fakeSocket);
const p1 = rpc.send('getUser', { id: 1 });
const p2 = rpc.send('getOrder', { id: 99 });
// fakeSocket later emits messages
fakeSocket.emit('message', JSON.stringify({ id: 'abc', result: { name: 'Ava' } }));    // matches p1
fakeSocket.emit('message', JSON.stringify({ id: 'def', error: 'Not found' }));         // matches p2
```

Trace:
- **t=0** — `rpc.send('getUser', ...)` generates id='abc'. `Promise.withResolvers()` returns `{ promise: P1, resolve: r1, reject: rj1 }`. `pending.set('abc', {resolve: r1, reject: rj1})`. Send over socket. Return P1.
- **t=0** — `rpc.send('getOrder', ...)` generates id='def'. Same flow, returns P2. `pending` has two entries.
- **t=10** — socket emits the first reply (id='abc'). `_onMessage` parses, looks up `pending.get('abc')`, calls `r1({ name: 'Ava' })`. P1 settles. Removed from `pending`.
- **t=20** — socket emits second reply (id='def', error). `_onMessage` calls `rj1(new Error('Not found'))`. P2 rejects. Removed.

Output: `await p1 === { name: 'Ava' }`, `await p2` throws `'Not found'`. **Without `Promise.withResolvers`, this is impossible to write cleanly** because P1 must be returned synchronously, but its resolver must be reachable from `_onMessage` later.

## Important takeaways

**Syntax to memorize**
- `let resolve, reject; const promise = new Promise((res, rej) => { resolve = res; reject = rej; });` — the manual 4-liner.
- `const { promise, resolve, reject } = Promise.withResolvers();` — native.
- Polyfill is one method definition; safe to add globally.

**Patterns to reuse**
- The deferred pattern is the **enabling primitive** for: priority queues (see `priority-async-queue.md`), promise pools, request/reply over message buses, debounce-that-returns-a-promise, `async-memoize.md` (cache the in-flight deferred).
- "Map<id, deferred>" is the universal **request/reply correlation** structure — used in JSON-RPC, WebSocket protocols, gRPC clients.

**Common mistakes**
- Adding a "settled" guard yourself — Promise already locks on first settle. Belt-and-suspenders code is noise.
- Holding the deferred forever — long-lived deferreds with no settle path leak memory; clear them on timeout/disconnect.
- Exposing the resolvers publicly — anyone can settle the promise from outside. Encapsulate.
- Using deferred when the executor would do — code smell. Use `new Promise` if settlement happens inside its lexical scope.

**Related questions**
- `priority-async-queue.md` (uses deferred per task)
- `async-memoize.md` (caches an in-flight deferred)
- `cancellable-promise-wrapper.md` (deferred + cancel token)
- JSON-RPC client implementation

## Variants

1. **Deferred with timeout** — wrap settlement with a `setTimeout` that calls `reject(timeoutErr)`. Make sure to `clearTimeout` on settle.
2. **One-shot event-to-promise** — `eventToPromise(emitter, eventName)`: deferred + once-listener. Common helper.
3. **Pipe one promise to another** — `pipe(source, deferred)`: `source.then(deferred.resolve, deferred.reject)`. Useful in routers.
4. **Multi-resolve deferred (observable-lite)** — relaxes the "settle once" rule. Not a Promise; it's a Subject. See `observable-subject.md`.

## Revision notes

> **Deferred / Promise.withResolvers — 60 second recap**
> - Hands you `{ promise, resolve, reject }` so you can settle from outside the executor.
> - Native in ES2024: `Promise.withResolvers()`. 4-line manual polyfill otherwise.
> - **Use it when** settlement happens in a different code path than the call site (callbacks, socket replies, queue dispatchers).
> - Foundation of: priority queues, async-memoize, RPC clients, request/reply matching.
> - **Trap:** holding a deferred with no settle path → memory leak. Always have a settle or timeout.
