# `BroadcastChannel` — same-origin pub/sub across tabs and workers

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [postmessage-roundtrip.md](./postmessage-roundtrip.md), [`10-machine-coding-patterns/pub-sub.md`](../10-machine-coding-patterns/pub-sub.md)
>
> **Source:** Web/Node BroadcastChannel API. Razorpay, Atlassian, Cloudflare browser roles.

---

## 1. Problem statement

Multiple tabs of the same origin. User logs out in tab A — tabs B, C, D should reflect immediately. Same for multi-worker Node apps invalidating shared caches.

**Verification examples**

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| 3 tabs subscribe to `'session'` channel             | each receives messages from others                     |
| Sender posts                                        | other tabs/workers get `'message'` event; sender NOT  |
| Different origin                                    | does NOT receive (origin-isolated)                     |
| Posts function                                      | DataCloneError (structured clone)                     |
| `ch.close()`                                        | further messages dropped                              |

**Constraints**
- Same-origin only.
- Sender does NOT receive its own message.
- Structured clone — no functions.
- Must `close()` to release resources.

---

## 2. Plain-English restatement

A named pub/sub bus. Anyone same-origin can `new BroadcastChannel('foo')` and join. Posts on one are received by all OTHERS on the same channel. Simpler than `localStorage` events; no polling. Used for cross-tab logout, cross-worker cache invalidation.

---

## 3. Why this matters in interviews

The right answer for cross-tab sync without rolling your own. Tests origin isolation literacy, structured-clone awareness, the "sender doesn't get its own message" gotcha.

---

## 4. Mental model

```
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ Tab A    │     │ Tab B    │     │ Tab C    │
   │ ch=new   │     │ ch=new   │     │ ch=new   │
   │ BC('s')  │     │ BC('s')  │     │ BC('s')  │
   └─────────┘     └─────────┘     └─────────┘
        │                ▲               ▲
        │ postMessage('logout')            
        └────────────────┴───────────────┘
                       fan-out

   Same origin → same broker → all subscribers receive.
   Sender does NOT receive its own message.
   Cleanup: ch.close() releases the subscription.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does the sender's own `onmessage` fire when it posts?
> 2. Can you `postMessage(fn)` over a BroadcastChannel?
> 3. What happens if you don't `close()`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `localStorage` + `'storage'` event
Works but: sender doesn't get event in own tab (same as BroadcastChannel), older API, requires JSON serialization, single-key contention.

### Wrong attempt 2: WebSocket + server roundtrip
Network roundtrip for same-machine sync — overkill.

### Wrong attempt 3: forget `close()`
Long-running tabs accumulate subscriptions; leak.

---

## 7. The unlocking insight

> **`new BroadcastChannel('name')` joins a same-origin named bus. `postMessage(data)` fans out to OTHERS (not self). Structured clone (no functions). `close()` to release. Modern replacement for `localStorage` `'storage'` events.**

Three properties:

1. **Same-origin pub/sub** — no setup, no server.
2. **Sender excluded** — no echo loop.
3. **Structured clone** — no functions.

---

## 8. Solution (annotated)

```js
// Tab A: emit logout
const ch = new BroadcastChannel('session');                            // step 1: join named bus
ch.postMessage({ type: 'LOGOUT', userId: 42 });                         // step 2: fan out

// Tab B, C, D: receive
const ch = new BroadcastChannel('session');
ch.onmessage = (event) => {                                             // step 3: listener
  if (event.data.type === 'LOGOUT') {
    redirectToLogin();
  }
};

// Cleanup
window.addEventListener('beforeunload', () => ch.close());              // step 4: release
```

**Try it yourself**

```js
// Multi-worker Node cache invalidation
const { BroadcastChannel } = require('node:worker_threads');           // Node 15+

const ch = new BroadcastChannel('cache:invalidate');
ch.onmessage = (event) => {
  cache.delete(event.data.key);
};

// Elsewhere in any worker:
async function updateUser(id, data) {
  await db.update(id, data);
  ch.postMessage({ key: `user:${id}` });                               // invalidate everywhere
}
```

---

## 9. Step-by-step dry run

```
3 tabs open at /app:

Tab A: ch = new BroadcastChannel('session'); subscribes.
Tab B: ch = new BroadcastChannel('session'); subscribes.
Tab C: ch = new BroadcastChannel('session'); subscribes.

Tab A: ch.postMessage({type: 'LOGOUT', userId: 42}).

t=0 (immediate):
  Tab A: ch.onmessage does NOT fire (sender excluded).
  Tab B: ch.onmessage fires → redirectToLogin().
  Tab C: ch.onmessage fires → redirectToLogin().

Different origin? https://other.example.com:
  Has its own BroadcastChannel namespace. No fan-out across origins.

postMessage({fn: () => 42}):
  DataCloneError. Functions don't clone.

ch.close():
  Subscription released. Further posts NOT received.
```

---

## 10. Common confusion + traps

1. **Sender receives own message** — no, excluded.
2. **Cross-origin** — no, same-origin only.
3. **Functions/DOM nodes** — no, structured clone throws.
4. **Forget `close()`** — leak in long-running tabs.
5. **Same as WebSocket** — no server, no network; in-browser only.
6. **Works in service workers** — yes; useful for cross-context coordination.
7. **`localStorage` `'storage'` event** — older alt; same constraints but lossy.

---

## 11. Senior follow-ups & variants

### Variant 1 — Leader election across tabs
Use BroadcastChannel for "I'm leader" heartbeats; lowest unique ID wins.

### Variant 2 — Optimistic UI sync
Tab A applies optimistic update + posts; B and C apply same; server reconciles.

### Variant 3 — Service worker coordination
Service worker uses BroadcastChannel to notify all controlled pages.

### Variant 4 — Encrypted channels
Encrypt payloads if multiple iframes share origin but want isolation.

### Variant 5 — Versioned channels
Include version in channel name (`'session:v2'`) for safe schema upgrades.

---

## 12. How to think aloud

> "`new BroadcastChannel('name')` joins a same-origin named bus. `postMessage(data)` fans out to OTHER tabs/workers on same channel (sender excluded). Structured clone — no functions. Must `close()` to release. Use case: cross-tab logout, cache invalidation across workers, optimistic sync. Compare with `localStorage` `'storage'` event: BroadcastChannel is the modern replacement, cleaner API, supports object payloads natively. With service workers: SW can broadcast to all controlled pages. Trap: thinking sender gets echo; forgetting `close()`; trying to send functions."

---

## 13. 60-second revision

> - **`new BroadcastChannel('name')`** joins same-origin bus.
> - **Fan-out** to others on channel; sender excluded.
> - **Same-origin only**; different origin = separate namespace.
> - **Structured clone** payload — no functions.
> - **`close()`** to release subscription.
> - **Use cases:** cross-tab logout, cache invalidation, leader election, optimistic sync.
> - **vs `localStorage 'storage'` event:** modern API; native object support.
> - **Trap:** sender-echo assumption; cross-origin; functions; no close.

---

**Related:** [postmessage-roundtrip.md](./postmessage-roundtrip.md) · [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) · [`10-machine-coding-patterns/pub-sub.md`](../10-machine-coding-patterns/pub-sub.md) · [`10-machine-coding-patterns/leader-election-toy.md`](../10-machine-coding-patterns/leader-election-toy.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
