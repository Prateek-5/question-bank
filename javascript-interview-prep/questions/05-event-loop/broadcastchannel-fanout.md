# BroadcastChannel Fan-Out (Cross-Tab / Cross-Worker Messaging)

## Source / Origin
- Web / Node BroadcastChannel API (standardized 2018 in DOM; Node 15+).
- Asked at: Razorpay, Atlassian, Cloudflare (browser-focused roles).
- Concept reference: `concepts/event-loop.md`, sibling `messagechannel-microtask.md`.

## Why this question matters in interviews
Multiple tabs of the same origin. User logs out in tab A. Tabs B, C, D should immediately reflect the logout. Or: a multi-worker Node app where one worker invalidates a cache and others should know. `BroadcastChannel` is the simplest API: same-origin pub/sub with structured cloning. Senior bar: you know it's same-origin only, that messages are structurally cloned (no functions), that the sender doesn't receive its own message, and that you must `close()` when done.

## Concepts involved

### Syntax to lock in
```js
// Tab A
const ch = new BroadcastChannel('session');
ch.postMessage({ type: 'LOGOUT', userId: 42 });

// Tab B (same origin)
const ch = new BroadcastChannel('session');
ch.onmessage = (event) => {
  if (event.data.type === 'LOGOUT') {
    redirectToLogin();
  }
};

// cleanup
ch.close();
```

### Edge cases / interview traps
1. **Same-origin only.** Two tabs at `https://a.com` see each other's messages; `https://b.com` does not.
2. **Sender doesn't receive its own message.** If tab A posts and listens on the same channel, A's handler is *not* invoked. Use a different channel or a state-broadcast pattern.
3. **Structured clone.** Functions, DOM nodes, Promises cannot be sent. Plain data only. Big payloads = clone cost.
4. **Order is not guaranteed across multiple senders.** Within one sender, posts arrive in order at each receiver. Across senders, interleaving is implementation-dependent.
5. **No persistence.** A new tab won't see past messages. Use `localStorage`'s `storage` event for "broadcast + late-joiner gets it" semantics.
6. **`close()` is mandatory.** Without it the channel and listeners leak.
7. **Service Workers** can also send/receive — useful for "service worker tells all tabs to refresh."
8. **Node `worker_threads`** — BroadcastChannel works across workers in same process; not across processes.

## Mental Model

A **room with a microphone**:

```
                  ┌───────────────────────┐
                  │  channel('session')   │
                  └─────────┬─────────────┘
                            │ all tabs subscribed
        ┌───────────┬───────┴───────┬───────────┐
        │           │               │           │
      Tab A       Tab B           Tab C       Tab D
       posts       hears           hears       hears
                  message         message     message

   A posts → all OTHER tabs receive (A does NOT)
```

For Node worker_threads:

```
   main → spawn worker1, worker2
   main, worker1, worker2 all open BroadcastChannel('cache-invalidate')
   worker1.postMessage({key:'x'})
   main + worker2 receive; worker1 does NOT
```

## Why interviewers care

- **Cross-context messaging fluency** — beyond `postMessage` between iframes.
- **API limit awareness** — same-origin, structured clone, no self-receive.
- **Lifecycle hygiene** — `close()` mandatory.

## Common beginner confusion

- **"BroadcastChannel works across origins."** No — same-origin only.
- **"Sender gets its own message."** It does not.
- **"I can send a Promise."** No — structured clone won't pass it. You can send a `MessagePort` (transferable) for back-channel.
- **"BroadcastChannel is RxJS Subject."** Similar shape; very different scope (cross-tab) and serialization (clone).
- **"It's persistent."** New tab won't see old messages. For persistence: localStorage.

## Brute force approach

```js
// Polling — wasteful, latent
setInterval(() => {
  if (localStorage.getItem('isLoggedOut') === 'true') redirectToLogin();
}, 1000);
```

## Optimal approach

A single `BroadcastChannel` per logical concern (`'session'`, `'cache'`, `'user-prefs'`). Subscribers register handlers; senders post. Close on tab unload.

## Solution (JavaScript)

```js
// shared module: createBus.js
class Bus {
  constructor(name) {
    this.ch = new BroadcastChannel(name);
    this.listeners = new Map();
    this.ch.onmessage = (ev) => {
      const handlers = this.listeners.get(ev.data?.type);
      if (handlers) handlers.forEach(h => h(ev.data));
    };
  }
  on(type, handler) {
    const set = this.listeners.get(type) || new Set();
    set.add(handler);
    this.listeners.set(type, set);
    return () => set.delete(handler);
  }
  emit(type, payload) {
    this.ch.postMessage({ type, ...payload, _ts: Date.now() });
  }
  close() { this.ch.close(); this.listeners.clear(); }
}

// usage
const bus = new Bus('session');
const off = bus.on('LOGOUT', () => redirectToLogin());

bus.emit('LOGOUT', { userId: 42 });
window.addEventListener('beforeunload', () => bus.close());

// Pattern: "broadcast my own action too" — useful when sender also wants its handler invoked
function broadcastAndLocal(type, payload) {
  bus.emit(type, payload);
  bus.listeners.get(type)?.forEach(h => h({ type, ...payload }));  // call locally too
}
```

## Step-by-step dry run

3 tabs open at `https://app.example.com`. User clicks logout in Tab A.

```
Tab A: bus.emit('LOGOUT', { userId: 42 })
       → ch.postMessage({type:'LOGOUT', userId:42, _ts: 1234})

Tab A: does NOT receive its own message
       (but App code typically navigates A directly without waiting)

Tab B: bus.ch.onmessage fires
       → handlers for 'LOGOUT' run
       → redirectToLogin()

Tab C: same as B

(Tab D opens later) → no historical event; current session check
                      via localStorage/cookie tells it the user is logged out
```

## How to think aloud in the interview

> "BroadcastChannel — same-origin pub/sub for tabs and workers. One channel per concern. Subscribers register `onmessage`; senders `postMessage`. Sender doesn't get its own message; if needed, dispatch locally too. Structured clone limits payload to plain data. Always `close()` on tab unload to avoid leaks. For cross-origin: postMessage between explicit windows. For persistent broadcast: localStorage + `storage` event. For service-worker → tabs: SW also can use BroadcastChannel."

## Important takeaways

- **Same-origin only.**
- **Sender doesn't self-receive.**
- **Structured clone — plain data only.**
- **`close()` mandatory** to avoid listener leaks.
- **No persistence** — late joiners don't see past messages.
- **One channel per concern**, not one giant channel.

## Variants

- **`storage` event** — `localStorage.setItem` triggers a `storage` event in other tabs. Lower API quality but persistent.
- **Service Worker as hub** — service worker maintains state and pushes to all clients.
- **WebRTC DataChannel** — for cross-machine pub/sub (different problem, much heavier).
- **SharedArrayBuffer + Atomics** — for high-frequency low-latency cross-worker messaging.
- **`MessageChannel`** — point-to-point with a transferable port; useful when you don't want broadcast.

## Revision notes

```
BroadcastChannel:
  new BroadcastChannel(name) — same-origin pub/sub
  ch.postMessage(data) — structured clone
  ch.onmessage = (event) => ...
  ch.close()
  
  TRAPS:
  - same-origin ONLY
  - sender does NOT receive own message
  - structured clone (no functions/Promises)
  - no persistence
  - close() mandatory
  
  alternatives:
  localStorage 'storage' event — persistent, cross-tab
  ServiceWorker → tabs — central hub
  MessageChannel — point-to-point with transferable
```
