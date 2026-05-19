# `postMessage` round-trip — RPC over one-way messaging

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md), [structured-clone-cost.md](./structured-clone-cost.md)
>
> **Source:** DOM/Node `worker.postMessage`, `window.postMessage`. Cloudflare, Stripe, Razorpay browser-heavy roles.

---

## 1. Problem statement

Build an RPC client over `worker.postMessage` — request/response with correlation IDs, error handling, timeout, transferables.

**Verification examples**

| Setup                                            | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| `rpc.call('hash', 'pw')`                          | Promise resolves to worker's result                    |
| Concurrent `rpc.call(...)` × 100                  | each routes to right caller via id                     |
| Worker throws                                      | Promise rejects with worker's error                    |
| Worker timeout                                     | reject after `timeoutMs`; pending entry cleaned       |
| `transfer` list for ArrayBuffer                   | zero-copy send                                          |
| Worker crashes                                     | reject all pending                                      |

**Constraints**
- `postMessage` is fire-and-forget — need correlation ID for replies.
- Map `id → {resolve, reject, timer}`.
- Errors marshalled (Error → {message, stack}).
- Timeout cleans pending entry to avoid leak.

---

## 2. Plain-English restatement

`worker.postMessage(x)` is fire-and-forget. To get a reply, add a `requestId` to each message; worker echoes it with the result. Maintain a `Map<id, {resolve, reject, timer}>` on the main thread to route the reply back to the correct Promise.

---

## 3. Why this matters in interviews

Tests whether you can build RPC abstractions over one-way messaging — same shape as WebSocket protocols, WebWorker RPC libs (Comlink), service worker postMessage.

---

## 4. Mental model

```
   Main thread:                          Worker thread:
   nextId = 1
   pending: Map<id, callbacks>

   rpc.call('hash', 'pw'):
     id = nextId++
     pending.set(id, {resolve, reject, timer})
     timer = setTimeout(timeoutReject, 30s)
     postMessage({id, method, args, ...})  ─────┐
                                                ▼
                                       parentPort.on('message', ({id, method, args}) => {
                                         try {
                                           result = handlers[method](args);
                                           postMessage({id, result});  ◀──┐
                                         } catch (e) {                       │
                                           postMessage({id, error: e.message}); ◀──
                                         }
                                       });
                                                ▼
   onMessage(({id, result, error})):  ◀────────┘
     pending.get(id) → {resolve, reject, timer}
     clearTimeout(timer); pending.delete(id)
     error ? reject(error) : resolve(result)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why need a correlation ID?
> 2. What happens to `pending` if a request times out — leak?
> 3. How to send a 10MB `ArrayBuffer` without copying?

---

## 6. Brute force — walked through

### Wrong attempt 1: no correlation ID
Reply routes to wrong caller under concurrency.

### Wrong attempt 2: no timeout
Hanging worker leaks pending entries forever.

### Wrong attempt 3: postMessage huge data
Structured clone copies; use transferList.

### Wrong attempt 4: send Error directly
Error objects don't fully clone (lose stack); marshal to `{message, name, stack}`.

---

## 7. The unlocking insight

> **Each call: `id = nextId++; pending.set(id, callbacks); postMessage({id, method, args})`. Worker echoes id with result/error. `onMessage` looks up pending by id, clears timer, resolves. Cleanup on timeout to avoid leak.**

Three properties:

1. **Correlation ID** — routes reply to right caller.
2. **Timer per call** — bound waiting; clean pending on timeout.
3. **Transferables** — zero-copy for large binaries.

---

## 8. Solution (annotated)

```js
class WorkerRpc {
  constructor(worker) {
    this.worker = worker;
    this.pending = new Map();                                          // step 1: id → callbacks
    this.nextId = 1;
    worker.addEventListener('message', (e) => this._onMessage(e.data));
    worker.addEventListener('error', (err) => this._onCrash(err));
  }

  call(method, args, { timeoutMs = 30_000, transfer = [] } = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {                                  // step 2: timeout cleanup
        this.pending.delete(id);
        reject(new Error(`RPC ${method} timed out after ${timeoutMs}ms`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.worker.postMessage({ id, method, args }, transfer);          // step 3: send with transferList
    });
  }

  _onMessage({ id, result, error }) {
    const entry = this.pending.get(id);
    if (!entry) return;
    clearTimeout(entry.timer);
    this.pending.delete(id);
    if (error) entry.reject(new Error(error));                          // step 4: route reply
    else entry.resolve(result);
  }

  _onCrash(err) {
    for (const [id, entry] of this.pending) {                           // step 5: reject all pending
      clearTimeout(entry.timer);
      entry.reject(err);
    }
    this.pending.clear();
  }
}
```

**Worker side:**

```js
// worker.js
const { parentPort } = require('node:worker_threads');
const handlers = {
  hash: async (pw) => crypto.pbkdf2Sync(pw, 'salt', 100_000, 64, 'sha512').toString('hex'),
};
parentPort.on('message', async ({ id, method, args }) => {
  try {
    const result = await handlers[method](args);
    parentPort.postMessage({ id, result });
  } catch (e) {
    parentPort.postMessage({ id, error: e.message });
  }
});
```

**Try it yourself**

```js
const worker = new Worker('./worker.js');
const rpc = new WorkerRpc(worker);

const hash = await rpc.call('hash', 'pa$$w0rd');                       // RPC
const buf = new ArrayBuffer(10_000_000);
const result = await rpc.call('process', { buf }, { transfer: [buf] }); // zero-copy
buf.byteLength;                                                         // 0 — detached
```

---

## 9. Step-by-step dry run

```
Concurrent calls:
t=0    rpc.call('hash', 'a') → id=1; pending={1: cbA}; postMessage({id:1, ...})
       rpc.call('hash', 'b') → id=2; pending={1:cbA, 2:cbB}; postMessage({id:2, ...})

Worker processes both (async, concurrent):
t=200  worker returns result for id=2 → postMessage({id:2, result: 'hashB'})
       main: onMessage → pending.get(2) → resolve cbB('hashB'); pending.delete(2)
t=250  worker returns result for id=1 → postMessage({id:1, result: 'hashA'})
       main: onMessage → pending.get(1) → resolve cbA('hashA'); pending.delete(1)

Note: replies came back OUT OF ORDER. Correlation ID routes correctly.

Timeout case:
t=0    rpc.call('hash', 'c', {timeoutMs: 100}) → id=3; setTimeout(reject, 100)
       pending={3: cbC}
t=100  timer fires → pending.delete(3); reject('timeout')
t=200  worker finally returns id=3 → main onMessage → pending.get(3) → undefined → ignored

Crash case:
t=0    rpc.call(...) × 5 → pending={1..5}
t=50   worker crashes → onCrash
       for each pending: clearTimeout, reject(crashErr)
       pending.clear()
```

---

## 10. Common confusion + traps

1. **No correlation ID** — concurrent calls route incorrectly.
2. **No timeout cleanup** — hanging worker leaks Map entries.
3. **Send Error directly** — stack lost; marshal to `{message, name, stack}`.
4. **Forget transferList** — copies large binaries.
5. **No crash handler** — pending leaks indefinitely.
6. **postMessage from worker echoes** — `worker.postMessage` is one-way; worker uses `parentPort.postMessage`.
7. **Method registry on worker side** — switch on `method` to dispatch.

---

## 11. Senior follow-ups & variants

### Variant 1 — Comlink library
Wraps worker objects as Proxies; calls feel like normal function invocations.

### Variant 2 — Stream large results
Worker chunks; main reassembles. Used for streaming JSON parse.

### Variant 3 — `MessageChannel` for cross-worker RPC
Dedicated lane between workers (not main).

### Variant 4 — Cancellation
Post `{type: 'cancel', id}`; worker checks periodically; rejects with AbortError.

### Variant 5 — `SharedArrayBuffer` for hot loops
Skip RPC overhead; both threads read/write shared memory directly.

### Variant 6 — `window.postMessage` for iframes
Same RPC pattern; check `event.origin` for security.

---

## 12. How to think aloud

> "`postMessage` is fire-and-forget; build RPC on top via correlation ID. Main: `nextId++` per call; `pending: Map<id, {resolve, reject, timer}>`. Send `{id, method, args}`; worker echoes `{id, result, error}`. Main `onMessage` looks up id, clears timer, resolves/rejects. Timeout: setTimeout per call, cleans pending entry on fire. Worker crash: reject all pending. For zero-copy on big binaries: `postMessage(data, [transferList])`. For continuous sharing: `SharedArrayBuffer + Atomics`. Trap: no correlation ID (mis-routed replies); no timeout cleanup (leak); raw Error (stack lost); postMessage huge data (copy)."

---

## 13. 60-second revision

> - **Correlation ID per call** — `pending: Map<id, {resolve, reject, timer}>`.
> - **Send `{id, method, args}`; worker echoes `{id, result, error}`.**
> - **Per-call timer** with cleanup on settle/timeout.
> - **Crash handler** rejects all pending.
> - **Marshal errors** to `{message, name, stack}` — don't send Error directly.
> - **Transferables** for large binaries: `postMessage(data, [transferList])`.
> - **Family:** Comlink, BroadcastChannel, `window.postMessage` for iframes.
> - **Trap:** no id; no timeout; raw Error; huge-data copy.

---

**Related:** [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) · [worker-pool-implementation.md](./worker-pool-implementation.md) · [structured-clone-cost.md](./structured-clone-cost.md) · [messagechannel-microtask.md](./messagechannel-microtask.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
