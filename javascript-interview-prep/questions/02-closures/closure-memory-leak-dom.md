# Diagnose and fix closure-induced memory leaks in long-lived handlers

> **Difficulty:** Medium-Hard   |   **Time:** ~20 min   |   **Prereqs:** [setinterval-stale-closure.md](./setinterval-stale-closure.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Real production debugging pattern (Node services, browser DOM); senior interview "where does this leak?"

---

## 1. Problem statement

**The leaky code**
```js
const EventEmitter = require('events');
const bus = new EventEmitter();

function handleRequest(req) {
  const huge = new Array(1_000_000).fill(req.id);   // ~8 MB
  bus.on('event', () => console.log(huge[0]));      // listener never removed
}
```

**Input / Output examples**

| Setup                                              | After 1000 requests | Why                                            |
|----------------------------------------------------|---------------------|-------------------------------------------------|
| Run `handleRequest(req)` 1000 times                | ~8 GB RSS, OOM      | each call adds a listener whose closure pins ~8 MB |
| Same, but with Fix A (explicit cleanup)            | Bounded             | listeners removed when requests close            |
| Same, but with Fix B (capture only what you need) | Slightly better     | `huge` is collectable as soon as fn returns      |
| Same, but with Fix C (AbortSignal lifecycle)      | Bounded             | one signal cleans up many listeners              |

**Constraints**
- Identify the leak (closure pins scope; listener never removed).
- Provide **three** fixes (explicit cleanup, capture-minimization, AbortSignal).
- Articulate **why** the scope is pinned even after `handleRequest` returns.

---

## 2. Plain-English restatement

You add an event listener inside a per-request handler. The listener uses a big array from the handler's local scope. The handler returns, but the listener stays registered forever — and because the listener references the big array via closure, the array can't be garbage-collected. Every request piles on another listener and another array. Eventually the server OOMs.

The interviewer wants you to (1) explain why the array survives even though the handler is "done," (2) show three fixes, and (3) discuss how you'd diagnose this in production.

---

## 3. Why this matters in interviews

This question separates engineers who can *write* closures from engineers who understand **why closures are GC anchors**. In any long-running Node service — HTTP servers, WebSocket gateways, message-queue consumers — closures that outlive their useful purpose silently pin entire object graphs. Senior interviewers ask: "you added an EventEmitter listener inside a request handler — what just leaked?" If you can articulate this with a real example (listeners, intervals, sockets), you sound senior. If you can't, you sound like someone who'll page the team at 3 AM with `JavaScript heap out of memory`.

---

## 4. Mental model

A closure is a **GC root anchor**. The garbage collector traces from roots — globals, the call stack, registered listeners, active timers, open sockets — and marks everything reachable. A registered listener is reachable from `bus._events`. The listener references its closure environment. The environment references every variable in scope. As long as the listener is registered, the entire scope tree behind it is alive.

```
   GC roots
     │
     ├── global vars, call stack
     │
     └── bus                 (EventEmitter is reachable)
            │
            └── _events.event = [L1, L2, L3, ...]
                       │
                       L1.[[Environment]] ──▶ closure record for handleRequest call #1
                                                  │
                                                  ├── req (the request object — 100s of KB)
                                                  ├── huge (the array — 8 MB)
                                                  └── ...everything else in scope
```

Each unremoved listener is a chain back to a per-request scope. Three fixes:

1. **Cut the GC anchor** — remove the listener when the request completes.
2. **Minimize what's in scope** — extract the small bits you need into a tighter scope; let the big bits go out of scope before the listener registers.
3. **Bind to a lifecycle** — use `AbortSignal` so one teardown call cleans up many subscriptions.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `handleRequest` returns, `req` and `huge` are "out of scope" — why aren't they garbage-collected?
> 2. Would `bus.once('event', ...)` instead of `bus.on('event', ...)` fix the leak? Why?
> 3. If `bus.off('event', this.handle.bind(this))` doesn't work, what's going on with `bind`?

---

## 6. Brute force — walked through

### Wrong attempt 1: null out the variable after use

```js
function handleRequest(req) {
  let huge = new Array(1_000_000).fill(req.id);
  bus.on('event', () => console.log(huge[0]));
  huge = null;   // BUG: only nulls my reference; listener still holds it
}
```

Nulling `huge` here only releases *your* scope's reference. The listener's closure record has its *own* reference to `huge` (captured at function-definition time). The listener still pins the value the array was at capture time. Wrong fix.

### Wrong attempt 2: trust `Node max-old-space-size`

Bumping the heap limit delays the OOM. It doesn't fix the leak — you'll still hit the new limit. Reject as a workaround, not a fix.

### Wrong attempt 3: `MaxListenersExceededWarning` is the signal

Node warns at 11 listeners on the same emitter. The warning is correlated with the bug (listeners growing unboundedly), but treating "shut up the warning" as the fix is wrong. Address the underlying leak.

---

## 7. The unlocking insight

> **A closure pins its entire scope until the closure itself becomes unreachable from GC roots. To free the scope, the closure must lose all its GC anchors — typically the listener registration.**

When `handleRequest(req)` runs, the engine creates an LE for the call (containing `req`, `huge`, and any other locals). The arrow function `() => console.log(huge[0])` is created with `[[Environment]]` pointing at that LE. When `handleRequest` returns, **its stack frame pops, but the LE survives on the heap** because the listener still references it.

The listener's reachability is the linchpin. It lives in `bus._events.event`, an internal Map/array. As long as `bus` is reachable (typically forever, in a singleton-emitter app) and the listener is in that map, the listener is reachable → its closure is reachable → its entire captured scope is reachable.

**Three fixes target three different parts of the chain:**

- **Fix A — Remove the listener (cut the anchor).** Pair every `bus.on(...)` with a `bus.off(...)` tied to a lifecycle event (`req.close`, `signal.abort`, component unmount).
- **Fix B — Don't capture what you don't need.** Pull `req.id` out as a primitive **before** the listener is registered, and let `huge` go out of scope. The listener's closure pins only the primitive.
- **Fix C — Bind to a lifecycle primitive.** Use `AbortSignal` — Node's modern lifecycle abstraction. One `abort()` call removes everything registered with `{ signal }`.

**The optimizer footnote.** V8 has `ScopeInfo`-based escape analysis that sometimes drops captured variables the inner function doesn't reference. *Don't rely on it.* Engines can't always prove a variable is unused — even small inner-function changes can re-pin everything. Write code that doesn't *need* the optimization to work.

---

## 8. Solution (annotated)

```js
const EventEmitter = require('events');
const bus = new EventEmitter();

// ── The leak ───────────────────────────────────────────────────────
function leaky(req) {
  const huge = new Array(1_000_000).fill(req.id);   // step 1: 8 MB allocated
  bus.on('event', () => console.log(huge[0]));      // step 2: listener pins `huge` forever
  // handleRequest returns; listener stays registered; closure pins huge + req
}

// ── Fix A: explicit cleanup tied to request lifecycle ─────────────
function fixedA(req) {
  const huge = new Array(1_000_000).fill(req.id);
  const onEvent = () => console.log(huge[0]);       // step 1: keep a named reference
  bus.on('event', onEvent);
  req.on('close', () => bus.off('event', onEvent));  // step 2: remove listener when request closes
}

// ── Fix B: capture only what you need ─────────────────────────────
function fixedB(req) {
  const reqId = req.id;                              // step 1: capture only the primitive
  {
    const huge = new Array(1_000_000).fill(reqId);
    processSync(huge);                                // step 2: use huge in a tight scope
  }                                                   // step 3: huge goes out of scope here — GC eligible
  bus.once('event', () => console.log(reqId));       // step 4: closure pins reqId (4 bytes), not huge
}

// ── Fix C: AbortSignal lifecycle ──────────────────────────────────
function fixedC(req, signal) {
  function onEvent() { /* ... */ }
  bus.on('event', onEvent);
  signal.addEventListener('abort', () => bus.off('event', onEvent), { once: true });
}
// Caller: const ac = new AbortController(); fixedC(req, ac.signal); ... ac.abort();
```

**Try it yourself**

```js
// Reproduce the leak
const bus = new EventEmitter();
function leaky(req) {
  const huge = new Array(1_000_000).fill(req.id);
  bus.on('event', () => console.log(huge[0]));
}
for (let i = 0; i < 1000; i++) {
  leaky({ id: i, on: () => {} });
}
console.log('listeners:', bus.listenerCount('event'));   // 1000
console.log('RSS:', process.memoryUsage().rss);          // ~8 GB
// All 1000 closures + huge arrays are pinned forever
```

---

## 9. Step-by-step dry run

Setup (leaky version):

```js
const bus = new EventEmitter();
const handler = leaky;
handler({ id: 1, on: () => {} });
handler({ id: 2, on: () => {} });
handler({ id: 3, on: () => {} });
```

Values-first trace:

| Step | Action            | `bus._events.event` | Closures on heap            | Reachable memory                         |
|------|-------------------|---------------------|------------------------------|-------------------------------------------|
| 1    | `handler(req₁)`   | `[L₁]`              | LE₁ (req₁, huge₁)            | ~8 MB                                    |
| 2    | `handler(req₂)`   | `[L₁, L₂]`          | LE₁ + LE₂                    | ~16 MB                                   |
| 3    | `handler(req₃)`   | `[L₁, L₂, L₃]`      | LE₁ + LE₂ + LE₃              | ~24 MB                                   |
| 4    | GC runs           | (unchanged)         | (unchanged)                  | **All three LEs reachable from `bus`**   |

With Fix A, after each request emits `'close'`:

| Step | Action                | `bus._events.event` | Closures on heap | Reachable memory after GC |
|------|-----------------------|---------------------|-------------------|--------------------------|
| 1+close | `handler(req₁)`; req₁ closes | `[]` | LE₁ unreachable | freed (~0 MB pinned) |

Each request's 8 MB is freed promptly. Steady-state memory is bounded.

---

## 10. Common confusion + traps

1. **"Out of scope" ≠ "garbage-collected."**
   `handleRequest` returning means its **stack frame** pops. But if any closure references the call's LE, the LE survives on the heap. Out-of-scope only releases *that scope's* reference; any other holder still pins.

2. **`bind(this)` makes removal harder.**
   `bus.on('e', this.handle.bind(this))` then `bus.off('e', this.handle.bind(this))` doesn't work — `bind` returns a *new* function each call. Listener identity is the function reference; the second `bind` is a different reference. Save the bound function once:
   ```js
   this.bound = this.handle.bind(this);
   bus.on('e', this.bound);
   // later
   bus.off('e', this.bound);
   ```

3. **Engines aggressively GC closures.**
   They don't. V8's escape analysis is best-effort. Write code that doesn't *need* the optimization.

4. **`once(...)` self-cleans.**
   True — `bus.once('e', fn)` removes itself after firing. Use it whenever you expect exactly one fire. Doesn't help if the event never fires.

5. **Caches that grow then plateau are not leaks.**
   A bounded LRU is fine. A `Map` keyed by request ID without eviction is a leak.

6. **`Map` vs `WeakMap` for object-keyed caches.**
   `Map` pins the key strongly. `WeakMap` lets the key (and its value) be GC'd when nothing else holds the key. Use `WeakMap` for "metadata attached to objects whose lifetime I don't control."

7. **`process.memoryUsage()` is monotonic during steady-state load — leak.**
   Flat (or oscillating around a baseline) = OK. Always growing = investigate.

---

## 11. Senior follow-ups & variants

### Variant 1 — AbortSignal-driven unified cleanup

Node 17.4+ and modern browsers accept `{ signal }` on most lifecycle-bound APIs:

```js
const ac = new AbortController();

bus.on('a', handleA, { signal: ac.signal });   // hypothetical EE signal support
fetch(url, { signal: ac.signal });
process.on('SIGTERM', () => ac.abort());

// One abort() removes/cancels everything
```

For APIs that don't natively support `{ signal }`, register a listener on the signal:

```js
function withSignal(signal, register, unregister) {
  register();
  signal.addEventListener('abort', unregister, { once: true });
}
```

### Variant 2 — `WeakRef` for caches that should auto-evict

`WeakRef` (ES2021) holds a reference that doesn't prevent GC. Useful for caches keyed by objects whose lifetimes you don't control:

```js
const cache = new Map();
function get(key) {
  const ref = cache.get(key);
  const cached = ref?.deref();
  if (cached) return cached;
  const fresh = compute(key);
  cache.set(key, new WeakRef(fresh));
  return fresh;
}
```

The referent can vanish between `deref()` calls. Plan for that.

### Variant 3 — `FinalizationRegistry` for cleanup-on-GC

Run a callback when an object becomes unreachable:

```js
const registry = new FinalizationRegistry((id) => bus.off('event', listeners.get(id)));
registry.register(req, req.id);
```

Use with caution: ordering and timing of finalizers is engine-defined.

### Variant 4 — Debugging with heap snapshots

`node --inspect` → Chrome DevTools → Memory → take two snapshots between calls → compare retainers. Look for `(closure)` entries with growing counts. Tells you exactly which closures are leaking.

```bash
node --inspect myserver.js
# Chrome → chrome://inspect → "Take snapshot"
# Load test the suspected endpoint
# "Take snapshot" again → "Comparison" view → sort by Delta
```

### Variant 5 — `process.memoryUsage()` over time

```js
setInterval(() => console.log(process.memoryUsage()), 60_000);
```

Flat across days = no leak. Monotonic = investigate. The `external` and `arrayBuffers` fields hide Buffer-backed leaks.

---

## 12. How to think aloud in the interview

> "Every per-request call adds a listener whose closure pins the request's local scope — including the 8 MB array. The listener lives in `bus._events`; as long as it's registered, it's reachable from a GC root. The closure pins the entire scope, including unused vars; V8 can sometimes drop unused captures but I wouldn't rely on it. Three fixes. (A) Explicit cleanup tied to lifecycle — `req.on('close', () => bus.off(...))`. (B) Minimize capture — extract only the primitives the listener needs, let heavy locals go out of scope before registration. (C) AbortSignal lifecycle — one `abort()` cleans up many subscriptions. For diagnosis: heap snapshots in DevTools, look for growing `(closure)` retainers; `process.memoryUsage().rss` monotonic over time = leak. Be aware that `bind(this)` returns a new function each call — store the bound reference if you need to `off()` it later."

---

## 13. 60-second revision

> - **Closures pin their scope** until the closure itself becomes unreachable from GC roots.
> - **Three leak vectors:** unremoved listeners, uncleared timers, long-lived socket handlers.
> - **Three fixes:** (A) explicit cleanup tied to lifecycle, (B) minimize what the closure captures, (C) `AbortSignal` for unified teardown.
> - Use `.once(...)` when one fire is enough — auto-removes.
> - `bind` returns a new function each call — save the bound reference if you need to `off()` it.
> - `WeakMap` / `WeakRef` for object-keyed caches that should auto-evict.
> - **Debug:** heap snapshots in Chrome DevTools; look for growing `(closure)` retainers. `process.memoryUsage()` monotonic = leak.
> - **Trap:** assuming "out of scope" = GC'd. It only releases *that scope's* ref — other holders still pin.
> - **Trap:** thinking V8 will GC unused captures — escape analysis is best-effort.

---

**Related:** [setinterval-stale-closure.md](./setinterval-stale-closure.md) · [closure-with-cancel-token.md](./closure-with-cancel-token.md) · [`08-maps-sets/weakmap-memoize.md`](../08-maps-sets/weakmap-memoize.md) · [`08-maps-sets/weakref-finalization-registry.md`](../08-maps-sets/weakref-finalization-registry.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
