# Fix the stale-closure bug in `setInterval` — read latest state on every tick

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [loop-closure-var-let.md](./loop-closure-var-let.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Real Node + React production bug; canonical senior interview "find the bug" question.

---

## 1. Problem statement

**The buggy code**
```js
function startPoller(getConfig) {
  let config = getConfig();
  setInterval(() => {
    console.log('polling with', config.url);
  }, 1000);
}
```

**Input / Output examples**

| Setup                                                              | What happens                                                |
|--------------------------------------------------------------------|-------------------------------------------------------------|
| `getConfig()` returns `{url: 'v1'}`, then later `{url: 'v2'}`     | Every tick logs `v1` — never sees `v2`                      |
| Replace with the fix (re-read via getter on each tick)            | Ticks reflect latest `getConfig()` returns                  |
| Replace with the fix (restart on change)                          | Ticks reflect latest config; current tick may skip          |
| Replace with the fix (ref object — `configRef.current`)            | Ticks reflect latest `.current` — same closure              |

**Constraints**
- Diagnose why the original is stale.
- Provide **three** fixes with different trade-offs (re-read, restart, ref).
- Always return a cleanup function from any code that starts an interval.

---

## 2. Plain-English restatement

You write a function that starts a poller. Inside, you read some config once and capture it. The polling callback uses the captured config every tick. Later, the *source* of that config changes — but your poller never sees the change. It's reading a snapshot from when the poller started.

The interviewer wants you to (1) explain why the closure is stuck on the old value, (2) propose at least three fixes, and (3) discuss the trade-offs.

---

## 3. Why this matters in interviews

The stale-closure-in-`setInterval` bug is the canonical "closures bite you in production" problem. Every Node backend engineer eventually writes a poll loop, a heartbeat, or a stats flusher that captures stale state — and gets paged at 3 AM. Senior interviewers love it because it tests three things at once: (1) you understand that closures capture **variable references, not values**, (2) you know **when** that reference gets re-read (every time the inner function runs), and (3) you can articulate **three** different fixes with different trade-offs. Fumbling this signals junior; nailing it with all three fixes signals senior.

---

## 4. Mental model

The closure is a **pointer to a labeled box**. The box's *label* never changes (`config`); the *contents* of the box are what gets read. If the box's contents are never reassigned, every tick reads the same contents — that's "stale." The three fixes are three different ways to make sure the contents stay fresh.

```
   closure inside setInterval
     │
     ├── ref to box labelled "config"
     │
     ▼
   ┌─────────────────────┐
   │ box: config         │
   │ contents: {url:v1}  │   ← set once; never reassigned
   └─────────────────────┘
   
   tick 1 reads contents → v1
   tick 2 reads contents → v1   (stale forever)
   tick N reads contents → v1
```

The three fix shapes:

```
   Fix 1 — re-read on every tick
     box contents: (fresh from getConfig())   ← refreshed inside the tick
   
   Fix 2 — restart the interval when state changes
     clearInterval(); fresh closure captures fresh contents.
   
   Fix 3 — ref object
     box.contents = { current: {url} }
     box.contents stays the same OBJECT; .current gets reassigned externally
     closure reads box.contents.current — picks up the latest
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If the outer scope reassigns `config = getConfig()` once after starting the poller, does the interval see it? Why or why not?
> 2. What's the difference between capturing the value vs capturing a *getter*? Which one stays fresh?
> 3. Why is the ref-object pattern (`configRef.current`) preferred in React?

---

## 6. Brute force — walked through

### Wrong attempt 1: `var` instead of `let`

```js
function startPoller(getConfig) {
  var config = getConfig();
  setInterval(() => console.log(config.url), 1000);
}
```

`var` doesn't change anything — closures capture bindings regardless of declaration keyword. Same stale `config`.

### Wrong attempt 2: redeclare `config` inside the interval body

```js
setInterval(() => {
  let config;   // BUG: shadows the outer var with undefined
  console.log(config?.url);
}, 1000);
```

Each tick declares a fresh inner `config = undefined`. Logs `undefined`. Doesn't fix the original problem.

### Wrong attempt 3: destructure at the top

```js
function startPoller(getConfig) {
  const { url } = getConfig();
  setInterval(() => console.log('polling', url), 1000);
}
```

Now you've captured a **primitive snapshot** of `url`. Even if the outer scope held a getter, you've copied out the string. Strictly worse — the bug is now baked into a primitive instead of an object ref.

---

## 7. The unlocking insight

> **Closures capture bindings, not values. If the binding is never reassigned, every tick reads the same value. The fix is to capture something that *is* refreshable — a getter, a ref object, or to rebuild the closure entirely.**

The interval callback has a reference to the *binding* `config` in the outer LE. That binding holds an object reference set once. Every tick, the callback dereferences the binding and reads `config.url`. Since `config` never gets reassigned, the value never changes.

Three patterns make the value refreshable:

**Pattern 1 — capture a *getter*.** The callback calls `getConfig()` every tick. The getter encloses (or accesses) the up-to-date source of truth. The closure binding doesn't change; the result of calling the getter does.

**Pattern 2 — capture a *ref object*.** Store config as `configRef = { current: getConfig() }`. The callback reads `configRef.current`. External code can mutate `configRef.current = newConfig` — the closure binding (`configRef`) stays the same object; its `.current` property changes. This is React's `useRef` pattern.

**Pattern 3 — restart the interval.** When state changes, clear the interval and start a new one. The new closure captures a fresh `config`. No stale read because no continuous interval — each interval is short-lived against a fixed snapshot.

Pattern 1 is the cheapest if `getConfig()` is fast. Pattern 3 is the cleanest if state changes are event-driven (you know when to restart). Pattern 2 is the most ergonomic at scale and is the React idiom.

---

## 8. Solution (annotated)

```js
// ── The bug ───────────────────────────────────────────────────────
function startPollerBuggy(getConfig) {
  const config = getConfig();                       // step 1: captured ONCE; never refreshed
  setInterval(() => console.log('poll:', config.url), 1000);
  // closure reads `config.url` every tick, but `config` itself never changes
}

// ── Fix 1: re-read via getter on every tick ───────────────────────
function startPollerFix1(getConfig) {
  const id = setInterval(() => {                    // step 1: callback closes over getConfig (a function)
    const config = getConfig();                      // step 2: fresh value on every tick
    console.log('poll:', config.url);
  }, 1000);
  return () => clearInterval(id);                    // step 3: ALWAYS return cleanup
}

// ── Fix 2: restart on change ──────────────────────────────────────
function startPollerFix2(getConfig, onChange) {
  let id;
  function arm() {                                   // step 1: arm() builds a new interval with fresh config
    clearInterval(id);
    const config = getConfig();
    id = setInterval(() => console.log('poll:', config.url), 1000);
  }
  arm();
  const unsub = onChange(arm);                       // step 2: external signal re-arms the interval
  return () => { clearInterval(id); unsub?.(); };
}

// ── Fix 3: ref object (React-style) ───────────────────────────────
function startPollerFix3(configRef) {                // configRef = { current: getConfig() }
  const id = setInterval(() => {
    console.log('poll:', configRef.current.url);     // step 1: reads .current — caller can update externally
  }, 1000);
  return () => clearInterval(id);
}
```

**Try it yourself**

```js
let url = 'v1';
const getConfig = () => ({ url });

// Fix 1
const stop1 = startPollerFix1(getConfig);
setTimeout(() => { url = 'v2'; }, 2500);
// t=1000 → poll: v1
// t=2000 → poll: v1
// t=2500 → url changes
// t=3000 → poll: v2   ← latest
// t=4000 → poll: v2
// stop1() cleans up

// Fix 3 — ref object
const ref = { current: getConfig() };
const stop3 = startPollerFix3(ref);
setTimeout(() => { ref.current = { url: 'v2' }; }, 2500);
// same behaviour: ticks 1-2 see v1, ticks 3+ see v2
```

---

## 9. Step-by-step dry run

Setup:

```js
let url = 'v1';
const getConfig = () => ({ url });
const stop = startPollerFix1(getConfig);
setTimeout(() => { url = 'v2'; }, 2500);
setTimeout(() => stop(), 4500);
```

Values-first trace (Fix 1):

| Time (ms) | Action                | Outer `url` | What the tick sees | Log         |
|-----------|------------------------|-------------|---------------------|-------------|
| 0         | interval armed        | `'v1'`      | —                   | —           |
| 1000      | tick                  | `'v1'`      | `getConfig()` → `{url:'v1'}` | `poll: v1` |
| 2000      | tick                  | `'v1'`      | `{url:'v1'}`        | `poll: v1`  |
| 2500      | outer reassigns `url` | `'v2'`      | —                   | —           |
| 3000      | tick                  | `'v2'`      | `{url:'v2'}`        | `poll: v2`  |
| 4000      | tick                  | `'v2'`      | `{url:'v2'}`        | `poll: v2`  |
| 4500      | `stop()` cleans up    | `'v2'`      | —                   | —           |

With the **buggy** version, every tick would log `poll: v1` because `config` was captured once and never reassigned.

---

## 10. Common confusion + traps

1. **Destructuring at capture time bakes in a primitive snapshot.**
   `const { url } = config` copies the string. The closure now closes over a primitive that can never update. Worse than capturing the object.

2. **`var` doesn't help.**
   Same binding semantics. The bug isn't about `var` vs `let` — it's about whether the binding gets reassigned.

3. **Trusting that engines GC closures aggressively.**
   They don't. The entire scope is pinned until the interval is cleared. Always return a cleanup function.

4. **`bind(this)` inside `addEventListener` makes removal harder.**
   `bind` returns a new function each call. `emitter.off('e', this.handle.bind(this))` removes a *different* function reference. Store the bound function once if you need to off-it later.

5. **`setInterval` for self-rescheduling work.**
   Prefer a `setTimeout` chain so each tick gets a fresh closure naturally:
   ```js
   function tick() {
     doWork();
     setTimeout(tick, 1000);
   }
   tick();
   ```
   This sidesteps the stale-closure bug because each scheduled tick reads its own fresh environment.

6. **Memory leak corollary.**
   The interval pins the entire outer scope, including unused heavy locals. If your factory function allocated a 50 MB cache "just for now," it's pinned alongside the small `config`. Move heavy locals out of scope.

7. **React `useEffect` + `setInterval`.**
   Same bug. The effect captures `state` from the render where it ran. Fixes: functional `setState((s) => ...)`, `useRef`, or dependency array including the value.

---

## 11. Senior follow-ups & variants

### Variant 1 — Self-rescheduling `setTimeout` chain (no stale-closure problem)

```js
function startPoller(getConfig) {
  let stopped = false;
  function tick() {
    if (stopped) return;
    const config = getConfig();                    // fresh per tick
    console.log('poll:', config.url);
    setTimeout(tick, 1000);                         // re-arm
  }
  tick();
  return () => { stopped = true; };
}
```

Each `tick` schedules the next one fresh. The closure-shape problem doesn't arise because each scheduled call re-enters `tick` cleanly. Also gives you natural backpressure if `getConfig` is async.

### Variant 2 — Generation counter for race-free async refresh

```js
let gen = 0;
function reload() {
  const myGen = ++gen;
  return asyncFetch().then((data) => {
    if (myGen !== gen) return;   // stale — newer reload has started
    apply(data);
  });
}
```

Two reloads firing in overlap: the older one checks `myGen !== gen` after its await and exits, leaving the newer one to apply. Same family of "snapshot at start, check at end" pattern.

### Variant 3 — `AbortController` for unified teardown

```js
function startPoller(getConfig, signal) {
  const id = setInterval(() => {
    if (signal.aborted) return;
    const config = getConfig();
    console.log('poll:', config.url);
  }, 1000);
  signal.addEventListener('abort', () => clearInterval(id), { once: true });
}
```

One `AbortController` cleans up multiple things — listeners, fetches, intervals — when its signal aborts. Modern Node and browsers all support this.

### Variant 4 — React `useEffect` stale-state

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1);   // BUG: count is stale (captured at render time)
    }, 1000);
    return () => clearInterval(id);
  }, []);   // empty deps → effect only runs once → closure captures count=0 forever
}
```

Fixes: functional `setCount((c) => c + 1)` (closure doesn't need `count`), or use `useRef` for the latest value, or add `count` to deps (rebuilds the interval each render — usually wrong).

---

## 12. How to think aloud in the interview

> "Stale closure: the interval handler captured `config` once at start. Every tick reads the same binding, which is never reassigned. Three fixes. (1) Re-read via getter inside the tick — cheap if `getConfig` is fast. (2) Restart the interval when state changes — clean if state changes are event-driven, but tick timing is disrupted. (3) Ref object — `configRef.current` — closure binding stays the same; `.current` gets externally reassigned. React's `useRef` is this. Trade-offs: fix 1 wastes a getter call per tick; fix 2 loses the current tick; fix 3 is most ergonomic but requires the caller to manage the ref. I'd also always return a cleanup function; otherwise the interval pins the entire outer scope forever — closure-as-GC-anchor leak. For self-rescheduling work, prefer `setTimeout` chains — each tick gets a fresh closure naturally."

---

## 13. 60-second revision

> - **Bug:** closure captures `config` once; binding never reassigned; every tick reads the stale value.
> - **Root cause:** closures capture **bindings**, not values. The binding here is never refreshed.
> - **Three fixes**: (1) re-read via getter inside the tick; (2) restart interval on change; (3) ref object (`{ current }`).
> - **React analog:** `useEffect` + `setInterval` reads stale state — same problem class.
> - **Always return a cleanup** from functions that start intervals — leaking timers leaks the whole scope.
> - **Memory corollary:** heavy unused locals in the factory scope get pinned alongside the timer. Move them out.
> - **Self-rescheduling `setTimeout` chains** avoid the bug naturally (fresh closure per tick).
> - **Trap:** destructured snapshots (`const {url} = config`) bake in a primitive — strictly worse than capturing the object.

---

**Related:** [loop-closure-var-let.md](./loop-closure-var-let.md) · [closure-memory-leak-dom.md](./closure-memory-leak-dom.md) · [closure-with-cancel-token.md](./closure-with-cancel-token.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
