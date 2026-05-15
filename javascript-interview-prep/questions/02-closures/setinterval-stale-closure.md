# Stale closure bug in `setInterval` — reading the latest state

## Source
- Real bug pattern from Node services and React components (`useEffect` + `setInterval`).
- Frequent senior interview "find the bug in this code" question.

## Why this question matters in interviews
The stale-closure-in-`setInterval` bug is the canonical "closures bite you in production" problem. Every Node backend engineer eventually writes a poll loop, a heartbeat, or a stats flusher that captures stale state — and gets paged at 3am. Senior interviewers love this question because it tests three things at once: (1) you understand that closures capture **variable references, not values**, (2) you know **when** that ref gets re-read (every time the inner function is called), and (3) you can articulate **three** different fixes, each with different trade-offs. Fumbling this signals junior; nailing it with all three fixes signals senior.

## Concepts involved

### The buggy code
```js
function startPoller(getConfig) {
  let config = getConfig();                     // captured ONCE
  setInterval(() => {
    console.log('polling with', config.url);    // ← stale forever
  }, 1000);
}
```
The interval handler closes over `config`. The handler reads `config` every tick, but `config` is **never reassigned** in the outer scope, so it stays the original snapshot forever. If `getConfig()` is fresh data (e.g., from a config service that gets hot-reloaded), the poller will never see updates.

### Why this happens (engine-level)
- Closures capture **bindings**, not values. The interval callback has a reference to the *variable* `config`, not to the object it pointed at when captured.
- The variable lives in the outer function's lexical environment record. As long as the interval is alive, that environment record is alive — including the (stale) value `config` points to.
- If you reassign `config = getConfig()` inside the interval, future ticks see the new value. The problem is that nothing in the original code does that.

### The three fixes (you MUST know all three)

**Fix 1 — Re-read latest state via ref/getter on every tick**
```js
function startPoller(getConfig) {
  setInterval(() => {
    const config = getConfig();          // fresh on every tick
    console.log('polling with', config.url);
  }, 1000);
}
```
Best when `getConfig` is cheap. The closure now captures the **getter**, which is itself fresh on every call.

**Fix 2 — Restart the interval when state changes**
```js
function startPoller(getConfig, onChange) {
  let id;
  function arm() {
    const config = getConfig();
    clearInterval(id);
    id = setInterval(() => console.log('polling with', config.url), 1000);
  }
  arm();
  onChange(arm);                         // call arm() on config change
}
```
Best when `getConfig` is expensive or you only want to react to known events. The interval body has a fresh `config` binding each time `arm()` runs.

**Fix 3 — Generation counter / ref object**
```js
function startPoller(configRef) {        // configRef.current updated externally
  setInterval(() => {
    console.log('polling with', configRef.current.url);
  }, 1000);
}
```
The closure captures `configRef` (the object). The *object* is the same; its `.current` property is what gets reassigned. This is the React `useRef` pattern and the most ergonomic at scale.

### Edge cases / discussion points
1. **`useEffect` + `setInterval` in React** — the canonical front-end version. Closure captures the state value from the render where the effect ran. Fixes: functional setState, ref, restart on dep change.
2. **Memory** — every closure pins the outer environment until the interval is cleared. If you forget `clearInterval`, the closure + its captured vars leak forever.
3. **Pause/resume semantics** — fix 2 (restart) is the only fix that loses no scheduled ticks; fix 1 and fix 3 keep ticking through "changes."
4. **Async work inside the tick** — if the tick `await`s, by the time it resumes `config` may have changed again. You want **request-scoped** captures (deref at the top of the tick).
5. **EventEmitter handlers** — same bug class. A `socket.on('data', ...)` handler closes over outer vars; if the outer scope updates them, the handler sees the updates (because it re-reads); but if you bound *values* (e.g., destructured), you're stale.
6. **`setImmediate` chains** — similar bug if you recursively schedule and capture state at the top.

### Memory leak corollary (closure + long-lived timer)
```js
function startSession(user) {
  const cache = new Map();               // big — held forever
  setInterval(() => sendHeartbeat(user.id), 30_000);   // pins `user` + `cache`
}
```
The interval handler only uses `user.id`, but its closure record retains everything in scope — including `cache`. Engines do some "closure variable analysis" (V8's `ScopeInfo`) but in the general case you must assume the **entire scope is pinned**. Move the heavy `cache` out of scope, or `clearInterval` when the session ends.

## Brute force approach
"Just declare `config` with `var` and reassign it." Doesn't fix anything — the binding semantics are identical. Or "use `let` inside the interval" — also doesn't fix it; you'd be redeclaring per tick but reading from the same outer source. The real fix is to **re-read fresh state**, by one of the three patterns above.

## Optimal approach
Pick **fix 1** (re-read via getter) for simplicity, **fix 2** (restart) if state changes are event-driven, **fix 3** (ref object) for React or when state changes frequently and you don't want to rebuild the interval. State the choice and the trade-off explicitly.

## Solution (JavaScript)

```js
/* ---- Buggy ---- */
function startPollerBuggy(getConfig) {
  const config = getConfig();
  setInterval(() => console.log('poll:', config.url), 1000);
}

/* ---- Fix 1: re-read via getter ---- */
function startPollerFix1(getConfig) {
  const id = setInterval(() => {
    const config = getConfig();
    console.log('poll:', config.url);
  }, 1000);
  return () => clearInterval(id);            // always return a cleanup
}

/* ---- Fix 2: restart on change ---- */
function startPollerFix2(getConfig, onChange) {
  let id;
  function arm() {
    clearInterval(id);
    const config = getConfig();
    id = setInterval(() => console.log('poll:', config.url), 1000);
  }
  arm();
  const unsub = onChange(arm);
  return () => { clearInterval(id); unsub?.(); };
}

/* ---- Fix 3: ref object (generation counter pattern) ---- */
function startPollerFix3(configRef) {
  const id = setInterval(() => console.log('poll:', configRef.current.url), 1000);
  return () => clearInterval(id);
}
// caller does: const ref = { current: getConfig() };  ref.current = newConfig;
```

## Step-by-step dry run

Setup:
```js
let url = 'https://v1';
const getConfig = () => ({ url });

const stop = startPollerFix1(getConfig);

setTimeout(() => { url = 'https://v2'; }, 2_500);
setTimeout(() => stop(), 4_500);
```

Trace (fix 1):
- `t=0` — interval armed.
- `t=1000` — tick: `getConfig()` returns `{url: 'https://v1'}`. Logs `poll: https://v1`.
- `t=2000` — tick: same. Logs `poll: https://v1`.
- `t=2500` — outer reassigns `url = 'https://v2'`.
- `t=3000` — tick: `getConfig()` re-reads the outer `url`, returns `{url: 'https://v2'}`. Logs `poll: https://v2`.
- `t=4000` — tick: `poll: https://v2`.
- `t=4500` — `stop()` → `clearInterval(id)`. Closure record can now be GC'd (assuming no other refs).

With the **buggy** version: every tick would log `poll: https://v1` because `config` was captured once. Even after `t=2500`, the captured object is the same `{url: 'https://v1'}`.

What's on the heap (fix 1): the interval handler closure pins `getConfig`. `getConfig` itself closes over the outer `url`. Each tick reads `url` via the chain. Total retention: the handler + `getConfig` + the outer scope's `url` binding.

## Important takeaways

**Syntax to memorize**
- Always **return a cleanup function** from any function that calls `setInterval`. Otherwise you've made it impossible to stop and easy to leak.
- Capture **getters** or **ref objects**, not raw values, when the value changes over time.
- Reach for `for...of` + `let` (or fresh `const` inside the loop body) instead of `var` to avoid the same bug class in loop-with-setTimeout.

**Patterns to reuse**
- Ref-object pattern (`{ current: X }`) is the JS idiom for "shared mutable cell visible from multiple closures." Same as React's `useRef`. Use it for event emitters, sockets, long-lived timers.
- "Restart on change" mirrors React's `useEffect` with a dep array.
- Generation counter (`let gen = 0; const myGen = ++gen;`) lets old async work check `if (myGen !== gen) return;` and bail out. Used for race-condition-free async refresh.

**Common mistakes**
- Capturing destructured values (`const { url } = config`) inside long-lived handlers — you've snapshot the primitive, not the live ref.
- Trusting that engines GC closures aggressively — they don't. The whole scope is pinned.
- Forgetting `clearInterval` on shutdown — leaks the closure + everything it captures, often a huge graph.
- Using `setInterval` for self-rescheduling tick work — prefer `setTimeout` chain so each tick gets a fresh closure naturally.

**Related questions**
- React's `useEffect` + `setInterval` stale-state bug (same problem class)
- `setTimeout` in a `for` loop with `var` (sibling bug)
- Generation-counter pattern for race-free async refresh
- Memory leak via EventEmitter listeners

## Variants

1. **Stale closure with EventEmitter** — `emitter.on('data', () => useStaleVar)` — same fix family. Often paired with "and why isn't the listener GC'd?"

2. **Stale closure in `Promise.then` chain** — `then(() => doSomething(staleVar))` after a state change. Fix: re-fetch state at the top of `then`, or use a ref.

3. **Stale closure with React's `useEffect`** — captured `state` from a render is stale on the next tick. Fix: functional `setState`, `useRef`, or deps array including the value.

## Revision notes

> **setinterval-stale-closure — 60 second recap**
> - Closures capture **bindings**, not values. Captured-once values stay stale forever.
> - **Three fixes:** (1) re-read via getter on every tick, (2) restart interval on change, (3) ref object (`{ current }`).
> - React analog: `useEffect` + `setInterval` reads stale state — same problem.
> - Always **return a cleanup** from functions that start intervals — leaking timers leaks the whole scope.
> - Heap: the interval pins the entire outer scope, including unused vars.
> - Memory leak corollary: heavy unused locals in scope get pinned alongside the timer. Move them out or `clearInterval` on shutdown.
> - Self-rescheduling `setTimeout` chains avoid the bug naturally (fresh closure per tick).
> - **Trap:** destructured snapshots (`const {url} = config`) inside the handler — you've snapshot the primitive, not the live ref.
