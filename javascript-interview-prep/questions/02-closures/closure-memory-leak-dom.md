# Closure-induced memory leaks in long-lived handlers

## Source
- Production debugging pattern in Node services (EventEmitter, long-lived sockets, intervals) and browsers (DOM event listeners).
- Classic senior interview question — "where does this leak and why?"

## Why this question matters in interviews
This question separates engineers who can write closures from engineers who understand **why closures are GC anchors**. In any long-running Node service — HTTP servers, WebSocket gateways, message queue consumers — closures that outlive their useful purpose silently pin entire object graphs in memory. Senior interviewers ask: "you added an EventEmitter listener inside a request handler — what just leaked?" The answer requires understanding (1) what variables a closure captures, (2) when the closure becomes unreachable, and (3) how to **break the chain**. If you can articulate this with a real example (sockets, EventEmitters, setInterval), you sound senior. If you can't, you sound like someone who'll page the team at 3am with `heap OOM`.

## Concepts involved

### The canonical leak
```js
const EventEmitter = require('events');
const bus = new EventEmitter();

function handleRequest(req) {
  const huge = new Array(1_000_000).fill(req.id);   // 8MB-ish
  bus.on('event', () => console.log(huge[0]));      // closure captures `huge`
  // handler is never removed → `huge` is retained forever
}
```
Every request adds a listener whose closure pins an 8MB array. Listeners never get removed. After 1000 requests: 8GB resident, OOM.

### Why the closure pins the scope
- A closure captures the **entire variable environment** of its lexical scope. V8 does some `ScopeInfo`-based optimization to drop variables the inner function doesn't reference, but you cannot rely on it in general — assume the **whole scope** is pinned.
- The listener function lives in the EventEmitter's internal `_events` map. As long as the emitter is alive AND the listener is registered, the listener (and its closure) is reachable.
- When the closure is reachable, every variable in its scope is reachable. The mark-and-sweep GC starts from roots (global, stack frames, registered listeners) and traces — it cannot collect anything reachable.

### Common leak shapes (memorize the categories)

1. **EventEmitter / DOM listener never removed** — registered handler closes over request-scoped data.
2. **`setInterval` never cleared** — handler closes over outer scope; outer scope (and the timer) live forever.
3. **Long-lived socket with per-message handler** — `socket.on('data', () => ctx.something)` — each handler pins `ctx`.
4. **Cached function values** — `Map<key, fn>` where `fn` closes over a big object.
5. **Promise that never settles** — `then`/`finally` callbacks pin the chain's scope until resolved.
6. **Circular closures via React refs / Node EventEmitters** — handler A closes over B, B's handler closes over A. The cycle is collectible *if* both become unreachable from roots; not collectible if even one is a root.

### How to break the chain (the senior fixes)

**Fix A — Always remove listeners explicitly**
```js
function handleRequest(req) {
  const huge = new Array(1_000_000).fill(req.id);
  const onEvent = () => console.log(huge[0]);
  bus.on('event', onEvent);
  req.on('close', () => bus.off('event', onEvent));   // cleanup
}
```

**Fix B — Avoid capturing what you don't need**
```js
function handleRequest(req) {
  const reqId = req.id;                                // capture only the primitive
  const huge = new Array(1_000_000).fill(reqId);
  bus.once('event', () => console.log(reqId));         // closure pins reqId, not `huge`
  // huge is GC'd as soon as handleRequest returns (no closure refs)
}
```
The key insight: closures pin **what's reachable from the inner function's free-variable list**, not literally the whole scope on most engines — but cautious code structures *help the optimizer* by not putting heavy vars in scope at all.

**Fix C — Use `once` semantics or AbortSignal**
```js
function handleRequest(req, signal) {
  bus.addListener('event', handler);
  signal.addEventListener('abort', () => bus.removeListener('event', handler));
}
```
`AbortSignal` is the modern Node + browser way to clean up everything tied to a lifecycle.

**Fix D — Use `WeakRef` / `WeakMap` for unowned references**
A `WeakMap<obj, metadata>` lets metadata be collected when the key object becomes unreachable. Doesn't help in handler patterns (the handler itself is a strong root), but helps for caches keyed by objects.

### Edge cases / interview discussion
1. **`MaxListenersExceededWarning`** — Node warns at 11 listeners. Not the leak, but a symptom — if a per-request handler is being added repeatedly, this fires.
2. **Heap snapshots are how you find these** — `node --inspect` → Chrome DevTools → Memory tab → take two snapshots, compare retainers. Mention this for senior bonus.
3. **`--max-old-space-size`** doesn't fix leaks — it delays the OOM.
4. **Closures vs prototypes** — a method on a prototype doesn't capture any free variables, so it doesn't have a closure-scope retention problem. Closures are the leak vector, not prototype methods.
5. **Engine-specific behaviour** — V8 may inline functions and drop unused captures (escape analysis). Don't rely on it; write code that doesn't need the optimization.
6. **React analog** — `useEffect` callbacks that don't return cleanup leak the same way for component lifetimes.

## Brute force approach
"Set the variable to `null` after using it" — works for hard refs in your own scope, doesn't help when the variable is captured by someone else's listener. The listener still pins `huge` because it references `huge` from its closure record, not via your scope.

## Optimal approach
Break the closure's reachability. Either (a) remove the listener (cut the GC root), (b) avoid capturing the heavy var by extracting only what you need, or (c) restructure so the handler is short-lived (e.g., `.once` instead of `.on`, `AbortSignal` for lifecycle binding).

## Solution (JavaScript)

```js
const EventEmitter = require('events');

/* ---- Leak ---- */
function leaky(bus) {
  return function handleRequest(req) {
    const huge = new Array(1_000_000).fill(req.id);
    bus.on('event', () => console.log(huge[0]));     // pinned forever
  };
}

/* ---- Fix A: explicit cleanup tied to request lifecycle ---- */
function fixed(bus) {
  return function handleRequest(req) {
    const huge = new Array(1_000_000).fill(req.id);
    const onEvent = () => console.log(huge[0]);
    bus.on('event', onEvent);
    req.on('close', () => bus.off('event', onEvent));   // ← cuts the GC anchor
  };
}

/* ---- Fix B: minimize capture ---- */
function minimal(bus) {
  return function handleRequest(req) {
    const reqId = req.id;                              // primitive — tiny
    {
      const huge = new Array(1_000_000).fill(reqId);
      processSync(huge);
    }   // `huge` goes out of scope here — eligible for GC
    bus.once('event', () => console.log(reqId));       // closure pins reqId only
  };
}

/* ---- Fix C: AbortSignal lifecycle ---- */
function withSignal(bus, signal) {
  function onEvent() { /* ... */ }
  bus.on('event', onEvent);
  signal.addEventListener('abort', () => bus.off('event', onEvent), { once: true });
}
```

## Step-by-step dry run

Setup (leaky version):
```js
const bus = new EventEmitter();
const handler = leaky(bus);

handler({ id: 1, on: () => {} });
handler({ id: 2, on: () => {} });
handler({ id: 3, on: () => {} });

// Now: bus._events.event === [fn1, fn2, fn3]
// Each fn closes over its own `huge` (8MB each)
// Total retained: ~24MB even though all requests are "done"
```

Trace:
- Call 1: `huge1` allocated (8MB). Listener `L1` added to `bus`. `handler` returns. Locals (`huge`, `req`) go out of scope in `handleRequest`, BUT `L1` references them → still reachable from `bus._events`.
- Call 2: same, `huge2` (another 8MB), `L2` added.
- Call 3: same, `huge3` (another 8MB), `L3` added.
- GC runs. Roots: globals, stack, `bus`. From `bus` it reaches `_events.event = [L1, L2, L3]`. Each `Li` has a closure record pointing to its `huge_i`. **All three `huge` arrays are reachable and survive GC.**

Trace (fix A):
- Call 1: `huge1` allocated, `L1` added. `req.on('close', cleanup1)` registers an unbind.
- Request 1 closes → `cleanup1` runs → `bus.off('event', L1)`. `L1` is removed from `bus._events`. Now `L1`'s only references are local in the closed cleanup — gone after the scope ends.
- GC: `L1` unreachable → its closure record unreachable → `huge1` unreachable → freed.

Net: with fix A, after each request closes, that request's 8MB is freed promptly. Steady-state memory is bounded.

## Important takeaways

**Syntax to memorize**
- Pair every `on(...)` with an `off(...)` or use `.once(...)`.
- Pair every `setInterval` with a `clearInterval`, every `setTimeout` with `clearTimeout` if it might be cancelled.
- `AbortSignal` is the modern lifecycle primitive — every Node API that schedules work accepts one in recent versions.

**Patterns to reuse**
- "Closure as GC anchor" — every closure pins its scope. The leak fix is to **shorten the closure's life**.
- Tie cleanup to a known lifecycle event (`req.close`, `signal.abort`, component unmount).
- For caches keyed by objects, use `WeakMap` so the cache entry GCs when the key dies.
- For uncertain object references (e.g., DOM nodes in a long-running script), use `WeakRef` (ES2021) — but most code shouldn't need it.

**Common mistakes**
- Registering a fresh listener inside a request handler without removal — the classic leak.
- Closing over the entire `req` or `res` object when you only need `req.id`.
- Trusting that "out of scope" means "GC'd" — it only means *that scope* no longer has a ref; any other holder still pins it.
- Confusing memory growth with a leak — caches that grow then plateau are bounded; closures that pin per-request data are unbounded.

**How to debug**
- `node --inspect` → Chrome DevTools → Memory → take two heap snapshots between calls → compare retainers. Look for "(closure)" entries with growing counts.
- `process.memoryUsage()` over time — flat = OK, monotonic up = leak.
- `node --trace-gc` to see GC pauses; long old-gen pauses often correlate with closure-retained graphs.

**Related questions**
- `setinterval-stale-closure` — same closure mechanics, different bug
- Why `bind(this)` inside `addEventListener` makes removal harder (different listener identity)
- `WeakMap` vs `Map` for caches
- React `useEffect` cleanup

## Variants

1. **Listener removal with `bind`** — `bus.on('e', this.handle.bind(this))` then `bus.off('e', this.handle.bind(this))` doesn't work, because `bind` returns a new function each call. Tests whether you know listener identity.

2. **AbortSignal-driven cleanup** — register multiple listeners with a single `{ signal }` option (Node 17.4+, browsers); call `controller.abort()` once to remove all. Tests whether you know modern lifecycle APIs.

3. **`WeakRef` for "cache without retaining"** — store a `WeakRef` to a heavy object; entry is auto-evictable. Tests whether you know ES2021 weak references and their limitations (the referent can vanish between checks).

## Revision notes

> **closure-memory-leak — 60 second recap**
> - Closures pin their scope. As long as the closure is reachable from a GC root (EventEmitter, timer, socket, global), nothing in its scope can be collected.
> - **Three leak vectors:** unremoved listeners, uncleared timers, long-lived socket handlers.
> - **Three fixes:** (A) explicit cleanup tied to lifecycle, (B) minimise what the closure captures, (C) `AbortSignal` for unified teardown.
> - Use `.once(...)` when you only need one fire — auto-removes.
> - `bind` returns a new function each call — store the bound ref if you need to `off()` it later.
> - `WeakMap` / `WeakRef` for object-keyed caches that should auto-evict.
> - Debug with heap snapshots in Chrome DevTools; look for growing `(closure)` retainers.
> - **Trap:** assuming "out of scope" = GC'd. It only releases *that scope's* ref — other holders still pin.
