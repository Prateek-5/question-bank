# postMessage Round-Trip (Worker / iframe Bidirectional)

## Source / Origin
- DOM/Node MessageChannel + `worker.postMessage`; `window.postMessage` for iframes.
- Asked at: Cloudflare, Stripe, Razorpay, Atlassian (browser-heavy roles).
- Concept reference: `concepts/event-loop.md`, sibling `messagechannel-microtask.md`, `worker-threads-vs-event-loop.md`.

## Why this question matters in interviews
`worker.postMessage(x)` is fire-and-forget. To get a *reply*, you need a correlation ID and a pending-promise map — request/response semantics on top of one-way messaging. This question filters candidates who only know `worker.postMessage('go')` from those who can build an RPC abstraction over it. Senior bar: you handle (1) message-ID correlation, (2) error replies, (3) transferables for zero-copy, (4) timeout + cancel.

## Concepts involved

### Syntax to lock in
```js
// main.js — RPC client
class WorkerRpc {
  constructor(worker) {
    this.worker = worker;
    this.pending = new Map();           // id → {resolve, reject, timer}
    this.nextId = 1;
    worker.addEventListener('message', (e) => this._onMessage(e.data));
  }
  call(method, args, { timeoutMs = 30_000, transfer = [] } = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`RPC ${method} timed out after ${timeoutMs}ms`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.worker.postMessage({ id, method, args }, transfer);
    });
  }
  _onMessage(msg) {
    const slot = this.pending.get(msg.id);
    if (!slot) return;                  // unsolicited or after-timeout
    clearTimeout(slot.timer);
    this.pending.delete(msg.id);
    if (msg.error) slot.reject(Object.assign(new Error(msg.error.message), msg.error));
    else slot.resolve(msg.result);
  }
}

// worker.js — RPC server
const handlers = {
  square: ({ x }) => x * x,
  fetchJson: async ({ url }) => (await fetch(url)).json(),
};
self.onmessage = async (e) => {
  const { id, method, args } = e.data;
  try {
    const result = await handlers[method](args);
    self.postMessage({ id, result });
  } catch (err) {
    self.postMessage({ id, error: { message: err.message, code: err.code } });
  }
};
```

### Edge cases / interview traps
1. **No correlation = no replies.** Without an `id`, you can't tell which postMessage reply belongs to which call.
2. **Unsolicited messages** — handler should ignore unknown IDs (worker might broadcast events without a corresponding call).
3. **Transferable objects** — `ArrayBuffer`, `MessagePort`, `ImageBitmap` can be *transferred* (zero-copy) instead of cloned. Caller loses access after transfer.
4. **Structured clone cost** — sending a 10MB object incurs serialization on send + deserialization on receive. Use transferables.
5. **Timeout cleanup** — clear timer and remove pending entry on either resolution or reject.
6. **Worker crash** — pending calls hang forever unless you listen to `error`/`messageerror` and reject all pending.
7. **Bidirectional RPC** — both sides have client and server roles. Useful for "main asks worker to render; worker asks main to log."
8. **Cross-origin iframes** — `event.origin` check is mandatory; never trust senders.

## Mental Model

A **letter-and-reply protocol** with envelopes labeled by ID:

```
   main ─────────postMessage({id:1, method:'square', args:{x:5}})────────▶ worker
                                                                              │ runs handler
   main ◀────────postMessage({id:1, result:25}) ─────────────────────────────┘

   main keeps a "pending" map: { 1: { resolve, reject, timer } }
   on reply with id=1, resolve/reject and clear the slot
```

For iframes the picture is the same, except `event.origin` adds an authentication step:

```
   parent ─── postMessage({id:1, ...}, 'https://child.example') ───▶ child iframe
   parent ◀── postMessage({id:1, ...}, 'https://parent.example') ─── child
                  ^ child must specify parent origin
```

## Why interviewers care

- **API design** — building request/response over fire-and-forget.
- **Lifecycle hygiene** — timeouts, cleanup, worker-crash recovery.
- **Performance awareness** — transferables vs cloning.

## Common beginner confusion

- **"postMessage is synchronous."** It's async (microtask boundary on same realm; macrotask across realms).
- **"I can send a function."** No — structured clone won't pass functions, DOM nodes, classes with methods (unless serialized).
- **"Transferable means copy."** No — *zero-copy transfer*. The sender loses access. Different semantics.
- **"Workers can't access main memory."** They can via `SharedArrayBuffer` (with `Atomics`).
- **"`event.origin` is always trustworthy."** It is set by the browser, but checking it is on you. Skipping the check = XSS-style cross-window attack vector.

## Brute force approach

```js
// Fire-and-forget — no result
worker.postMessage({ method: 'square', x: 5 });
worker.onmessage = (e) => console.log(e.data);   // global handler; how to map to request?
```

## Optimal approach

A client-side `WorkerRpc` class with a `call(method, args)` method returning a Promise. Each call gets a unique ID; worker echoes it back. Server-side `worker.js` dispatches by method name and replies. Transferables for big payloads. Timeout + error wiring.

## Solution (JavaScript)

```js
// main.js
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
const rpc = new WorkerRpc(worker);

// Easy calls
const sq = await rpc.call('square', { x: 5 });            // 25
const json = await rpc.call('fetchJson', { url: '/api/users' });

// Transferable: send a 10MB buffer zero-copy
const buf = new ArrayBuffer(10 * 1024 * 1024);
await rpc.call('processBuffer', { buf }, { transfer: [buf] });
// buf is now neutered in main; cannot be read.

// Crash recovery
worker.addEventListener('error', (e) => {
  for (const slot of rpc.pending.values()) slot.reject(new Error('Worker crashed: ' + e.message));
  rpc.pending.clear();
});

// worker.js
const handlers = {
  square: ({ x }) => x * x,
  fetchJson: async ({ url }) => (await fetch(url)).json(),
  processBuffer: ({ buf }) => {
    const view = new Uint8Array(buf);
    // ... process in place ...
    return { processedBytes: view.length };
  },
};
self.onmessage = async (e) => {
  const { id, method, args } = e.data;
  try {
    if (!handlers[method]) throw new Error(`Unknown method ${method}`);
    const result = await handlers[method](args);
    self.postMessage({ id, result });
  } catch (err) {
    self.postMessage({ id, error: { message: err.message, code: err.code } });
  }
};
```

For iframe cross-origin:

```js
// parent
const iframe = document.querySelector('iframe');
const childOrigin = 'https://child.example.com';
iframe.contentWindow.postMessage({ id: 1, method: 'ping' }, childOrigin);

window.addEventListener('message', (e) => {
  if (e.origin !== childOrigin) return;        // SECURITY
  // ... handle reply with e.data.id ...
});
```

## Step-by-step dry run

```
t=0   main: rpc.call('square', {x:5})
       → id=1, pending.set(1, {resolve, reject, timer=30s})
       → worker.postMessage({id:1, method:'square', args:{x:5}})

t=1ms worker: onmessage runs
       → handlers.square({x:5}) → 25
       → self.postMessage({id:1, result:25})

t=2ms main: worker.onmessage with {id:1, result:25}
       → pending.get(1) → resolve(25); clearTimeout
       → Promise resolves with 25
```

Error path:

```
t=0   rpc.call('boom', ...) → handler throws "kaboom"
t=1ms worker: self.postMessage({id:2, error:{message:'kaboom'}})
t=2ms main: rejects with Error('kaboom')
```

## How to think aloud in the interview

> "I'll build RPC on top of postMessage. Client side: monotonic ID, pending Map of `id → {resolve, reject, timer}`. `call(method, args)` posts `{id, method, args}` and stores the slot. Worker side: switch on method, reply with `{id, result}` or `{id, error}`. Big payloads via transferables (ArrayBuffer, MessagePort) — zero-copy, sender loses access. Crash handler rejects all pending. Cross-origin iframe — always check `event.origin`. Timeouts clean up the slot."

## Important takeaways

- **Correlation ID** — without it, no replies.
- **Pending Map** — `id → {resolve, reject, timer}`.
- **Transferables** for big payloads (zero-copy).
- **`event.origin` check** for cross-origin.
- **Worker-crash handler** — reject all pending.
- **Bidirectional RPC** = both sides have client+server roles.

## Variants

- **Comlink** (Google's library) — wraps this RPC in a Proxy so you write `await worker.square(5)`.
- **MessageChannel direct pipe** — pass a `MessagePort` as transferable so two sub-components communicate without going through main.
- **Streaming RPC** — server emits multiple `{id, chunk, done}` messages; client assembles.
- **AbortSignal across worker boundary** — send `{id, type:'abort'}`; server checks a cancellation table.
- **Service worker as RPC** — same pattern; service worker is the worker.

## Revision notes

```
postMessage RPC:
  client: id-keyed pending Map; call() → postMessage({id, method, args}) + add slot + timer
  server: dispatch by method; reply { id, result } or { id, error }
  
  transferable (ArrayBuffer, MessagePort) — zero-copy; sender loses access
  structured clone (default) — deep copy; no functions
  
  cross-origin iframe: ALWAYS check event.origin
  worker.onerror: reject all pending
  
  Comlink: Proxy wrapper for ergonomic RPC
```
