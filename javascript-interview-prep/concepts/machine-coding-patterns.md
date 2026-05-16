# Machine-Coding Patterns (Meta Primer)

## Intuitive primer (read this first)

Machine-coding rounds are a **performance** as much as a code test. The interviewer wants to see *how you think*, *how you build incrementally*, and *how you handle the inevitable "now add this" twist*. Every pattern in this file is a tiny machine that controls **time, frequency, or memory**. Carry that one sentence with you.

### Real-world analogies for the headline patterns

- **Debounce = elevator doors.** People keep walking in; the doors keep resetting their "close timer." Doors close only after `wait` ms of *stillness* (no new arrivals). One action at the end.
- **Throttle = a faucet limiter / shower mixer with a flow regulator.** The faucet is open continuously, but it physically can't deliver more than X liters per minute. Calls during the wait window are silently dropped (or coalesced into one trailing call).
- **Retry with backoff = polite knocking.** Knock once, no answer — wait, knock louder. Still no answer — wait longer (with random jitter so we and other knockers don't all knock in unison and overwhelm the door).
- **Promise pool = parking lot with K spaces.** Cars (tasks) queue at the entrance; only K can be inside at once; as soon as one leaves, the next pulls in.
- **EventEmitter / Pub-Sub = a radio station + listeners.** Station broadcasts on a channel (event/topic); whoever tuned in (subscribed) hears it. Adding/removing listeners doesn't affect the broadcast.
- **LRU = a desk with limited paper space.** Most-recently-handled paper goes on top; when the desk overflows, the bottom paper (oldest, untouched) is binned.
- **Token bucket = a refilling water bucket.** Bucket holds up to K tokens, refills at rate R. Each request scoops 1 token; if dry, request is denied (or queued).
- **Leaky bucket = a bucket with a hole.** You pour requests in at any rate; they drip out at fixed rate R. Overflow on the input side is rejected.
- **Memoize = a notepad of past answers.** Same question asked twice? Read the notepad, don't recompute.
- **Compose/Pipe = an assembly line.** Each station transforms the part and hands it to the next.

### Why machine-coding patterns exist (first principles)

Real systems have three perennial scarcities:
1. **Time** — you can't make all calls instantly; you must throttle, debounce, batch, retry.
2. **Memory** — caches grow without bounds; LRU/TTL/WeakMap exist to bound them.
3. **Failure** — networks blink; retries, circuit breakers, queues paper over it.

Every pattern in this file is a *small, composable answer* to one of those scarcities. Interviewers ask them because real backend code is *full* of them — and getting the edges wrong (clock drift, error poisoning, listener leaks) is exactly the bug class that takes a senior to debug.

### Progression (simplest → interview-grade)
1. **Simplest:** "write a debounce." (5 lines, no leading/trailing options).
2. **Intermediate:** "now add cancel/flush." (real-world API surface).
3. **Advanced:** "now add maxWait so it fires at least every N ms even with continuous input."
4. **Interview-grade:** "now make it work with async fns and propagate AbortSignal."

The promotion from one rung to the next is *always* a new edge case. Practice reaching to the next rung *before* the interviewer asks; that's how you signal seniority.

## How to read this file
Sections 1–20 are the **catalogue of patterns**. Each pattern below now has four blocks added:
- **Mental Model** — the analogy & internal state map.
- **Why interviewers care** — what's actually being tested.
- **Common confusion** — the misread that trips beginners.
- **Walkthrough** — step-by-step trace of the code as if executing in your head.

The earlier sections (Core mental model, Edge cases, Interview worked examples) frame the *meta-skill*. The catalogue is the muscle memory.

## TL;DR
- This is the **interview hit-list**: ~20 patterns that show up across 90% of JS machine-coding rounds.
- Memorize the **shape and intent** of each — not byte-perfect code. Interviewers care about correctness on edge cases, not LOC count.
- Common axes that vary in the prompt: leading/trailing for throttle, cancel/flush for debounce, sync/async, with/without args, bound concurrency.
- Always ask: *"do calls during the wait period reset the timer, get queued, or get dropped?"*
- Have a mental rubric: signature → state → edge cases → cleanup.

## Why backend interviewers care
- These primitives compose into production code: rate limiters, retries, batching, in-memory caches, pub-sub.
- A senior candidate is expected to write a correct LRU or promise pool in ~10 minutes — not just describe it.
- Errors in these patterns (concurrency bugs, missed errors, leaks) leak straight into prod, so getting them right signals seniority.

### What's actually being measured
Most interviewers grade machine-coding rounds on five axes that have nothing to do with whether your code compiles:
1. **Clarification before coding** — do you ask "leading or trailing?" before writing debounce?
2. **State design** — can you name the minimum state needed and why?
3. **Edge-case anticipation** — do you bring up cancellation, errors, empty input *before* the follow-up forces you to?
4. **Incremental thinking** — can you start simple and bolt on features without rewriting?
5. **Cleanup hygiene** — timers cleared, listeners unsubscribed, promises not poisoning the chain.

A candidate who writes the perfect debounce in silence scores *worse* than one who writes a slightly buggy debounce while narrating those five axes.

## Core mental model
For any of these patterns, structure your answer:
1. **Signature** — what goes in, what comes out (function vs object vs class).
2. **Internal state** — timers, caches, counters, queues.
3. **Semantics** — leading/trailing, fail-fast/best-effort, eager/lazy.
4. **Cleanup** — cancel hooks, abort signals, timer clearing.
5. **Edge cases** — empty input, zero limit, cancellation mid-flight, errors.

State the assumptions out loud before coding; that alone moves you from mid to senior in the interviewer's notes.

---

## Edge cases & interview traps
1. **Debounce vs throttle confusion** — calling debounce "with leading=true, trailing=false, maxWait=wait" is roughly throttle. Be explicit about semantics.
   ```js
   // Debounce: fire once, wait elapsed since LAST call.
   // Throttle: fire at most once per wait window.
   ```
2. **Forgetting `cancel`/`flush` on debounce** breaks teardown for SPAs / long-lived processes.
   ```js
   const save = debounce(persist, 500);
   onUnmount(() => save.cancel()); // else save fires after teardown
   ```
3. **Retry without jitter** synchronises clients into a thundering herd.
   ```js
   await sleep(base * 2 ** i * (0.5 + Math.random())); // add jitter
   ```
4. **`Promise.all` inside pool** still fails fast on first reject — sometimes you want allSettled wrapping each task.
5. **EventEmitter `emit` while listeners mutate the list** — always copy `[...arr].forEach(...)` to prevent skip/double-fire.
6. **LRU evicting from `m.keys().next().value`** assumes Map insertion order; never re-sort the map.
7. **Token bucket using `Date.now()`** drifts on system clock changes — use `performance.now()` for monotonic time.
   ```js
   this.last = performance.now(); // monotonic; immune to clock jumps
   ```
8. **AbortController not propagated** through retry/pool/batch → cancelled requests still run; cancellation must be threaded through every layer.
9. **deepClone with functions / Symbols / DOM nodes** — undefined behavior; document what you don't clone.
10. **Memoize cache key via `JSON.stringify`** breaks on circular args, functions, or non-determined key order. Use a deterministic serializer or per-arg-type strategy.
11. **Async queue `tail = result`** without catching → an error poisons the chain forever.
    ```js
    this.tail = result.catch(() => {}); // critical
    ```
12. **Batcher race**: `add` called concurrently while flush is in-flight — accumulate into a fresh buffer first, then call `flush` with the captured snapshot.
13. **Compose argument order is right-to-left**, pipe is left-to-right — trip-up in interviews.
    ```js
    compose(f, g, h)(x) === f(g(h(x)));
    pipe(f, g, h)(x)    === h(g(f(x)));
    ```
14. **`once` returning cached value is correct, but caching a rejected Promise locks failure forever** — decide whether to reset on error.

### Bridge: from rules-of-thumb to applied examples
The traps above are *general* — they apply across patterns. The worked examples below show the *meta-skill* of these traps in action: how to talk through a problem, propose a structure, then refine under follow-ups. Treat the "I'd say" blocks as scripts to memorize verbatim for the day.

## Interview worked examples

### Example 1 — Debounce vs throttle in one breath
**Asked as:** "I'll give you a search input; would you debounce or throttle? Why?"

I'd say: "Debounce — I want exactly one request after the user stops typing, not one every 200ms during typing. Throttle is for streams of events where you DO want periodic firing, like scroll-position tracking or metric emissions. Mental rule: 'wait for silence' → debounce; 'sample at most once per window' → throttle."

```js
const onSearch = debounce(q => fetch(`/api?q=${q}`), 300);  // search
const onScroll = throttle(() => updateScrollPos(), 100);    // scroll
```

**What the interviewer is testing:** Mental model, not code — when to pick which.
**Sharp follow-up they often ask:** "User types 'react', pauses 100ms, then types ' hooks'. With debounce 200ms, how many requests fire?" → One: for "react hooks", 200ms after the last keystroke.

### Example 2 — EventEmitter with `once` semantics
**Asked as:** "Build a tiny EventEmitter supporting `on`, `off`, `once`, `emit`."

I'd say: "Keep a Map of event → array of listeners. `once` wraps the listener so it removes itself on first fire. In `emit`, copy the listener array before iterating — otherwise an `off` during emit can skip the next listener."

```js
class EventEmitter {
  #l = new Map();
  on(e, fn)   { (this.#l.get(e) ?? this.#l.set(e, []).get(e)).push(fn); return this; }
  off(e, fn)  { const a = this.#l.get(e); if (a) a.splice(a.indexOf(fn) >>> 0, 1); return this; }
  once(e, fn) { const w = (...a) => { this.off(e, w); fn(...a); }; return this.on(e, w); }
  emit(e, ...a) { [...(this.#l.get(e) ?? [])].forEach(fn => fn(...a)); }
}
```

**What the interviewer is testing:** Pub-sub structure + the listener-mutation-during-emit trap.
**Sharp follow-up they often ask:** "What about error events?" → Node's convention: if 'error' is emitted with no listener, throw. Add that handling.

### Example 3 — LRU vs TTL cache
**Asked as:** "Build a cache. Now make it bounded. Now make entries expire after N seconds."

I'd say: "LRU evicts least-recently-used when full; TTL evicts based on insertion timestamp. They solve different problems — LRU bounds memory; TTL bounds staleness. Combine them: TTL check on `get`, LRU eviction on `set`."

```js
class TTLCache {
  constructor(ttl) { this.ttl = ttl; this.m = new Map(); }
  set(k, v) { this.m.set(k, { v, exp: Date.now() + this.ttl }); }
  get(k) {
    const e = this.m.get(k);
    if (!e) return;
    if (Date.now() > e.exp) { this.m.delete(k); return; }
    return e.v;
  }
}
```

**What the interviewer is testing:** Choosing the right eviction policy for the problem.
**Sharp follow-up they often ask:** "How do you evict expired entries proactively to free memory?" → Periodic sweep with setInterval (and `.unref()`), or evict-on-set during eviction passes.

### Example 4 — Retry with `AbortSignal`
**Asked as:** "Make retry-with-backoff respect a cancellation signal."

I'd say: "Check `signal.aborted` before each attempt and during the backoff sleep. Throw an AbortError to short-circuit. The sleep itself must be cancellable — listen for `abort` to clear the timer."

```js
function abortableSleep(ms, signal) {
  return new Promise((res, rej) => {
    if (signal?.aborted) return rej(new DOMException("aborted", "AbortError"));
    const t = setTimeout(res, ms);
    signal?.addEventListener("abort",
      () => { clearTimeout(t); rej(new DOMException("aborted", "AbortError")); },
      { once: true });
  });
}

async function retry(fn, { retries = 3, base = 200, signal } = {}) {
  for (let i = 0; i <= retries; i++) {
    if (signal?.aborted) throw new DOMException("aborted", "AbortError");
    try { return await fn({ signal }); }
    catch (e) {
      if (i === retries || e.name === "AbortError") throw e;
      await abortableSleep(base * 2 ** i, signal);
    }
  }
}
```

**What the interviewer is testing:** Threading cancellation through a control-flow primitive.
**Sharp follow-up they often ask:** "What if the underlying fetch doesn't accept signal?" → wrap it in Promise.race with an abort-rejection promise.

### Example 5 — Rate-limiter per API key (token bucket)
**Asked as:** "Implement a per-API-key rate limiter for an Express middleware: 100 req/min, burstable to 20."

I'd say: "One TokenBucket per API key, stored in a Map. Refill at 100/60 tokens/sec, capacity 20. On request, look up or create the bucket; if `take(1)` returns false, respond 429. For multi-process, back this with Redis instead."

```js
class TokenBucket {
  constructor(cap, ratePerSec) {
    this.cap = cap; this.rate = ratePerSec;
    this.tokens = cap; this.last = Date.now();
  }
  take(n = 1) {
    const now = Date.now();
    this.tokens = Math.min(this.cap, this.tokens + (now - this.last) / 1000 * this.rate);
    this.last = now;
    if (this.tokens >= n) { this.tokens -= n; return true; }
    return false;
  }
}

const buckets = new Map();
function rateLimit(req, res, next) {
  const key = req.headers["x-api-key"];
  let b = buckets.get(key);
  if (!b) buckets.set(key, b = new TokenBucket(20, 100 / 60));
  if (!b.take(1)) return res.status(429).end("Too Many Requests");
  next();
}
```

**What the interviewer is testing:** Per-tenant state isolation; lazy bucket allocation; rate vs burst.
**Sharp follow-up they often ask:** "How would you garbage-collect inactive keys' buckets?" → periodic sweep removing buckets whose `last` is older than threshold, or use an LRU map.

### Example 6 — Compose vs pipe
**Asked as:** "Implement `compose` and `pipe`. What's the difference?"

I'd say: "`compose(f, g, h)(x)` is `f(g(h(x)))` — right-to-left, mirroring math notation. `pipe(f, g, h)(x)` is `h(g(f(x)))` — left-to-right, mirroring how you'd read a data flow. Same machinery, different reduce direction."

```js
const compose = (...fns) => x => fns.reduceRight((v, f) => f(v), x);
const pipe    = (...fns) => x => fns.reduce      ((v, f) => f(v), x);

const trim   = s => s.trim();
const upper  = s => s.toUpperCase();
const exclaim= s => s + "!";
pipe(trim, upper, exclaim)("  hi  ");    // "HI!"
compose(exclaim, upper, trim)("  hi  "); // "HI!"
```

**What the interviewer is testing:** Reduce direction; readability trade-offs.
**Sharp follow-up they often ask:** "Make it async — each fn can return a Promise." → `pipeAsync = (...fns) => x => fns.reduce((p, f) => p.then(f), Promise.resolve(x));`

---

### Bridge: from worked examples to the catalogue
You've seen the *meta-skill* (clarify → structure → code → narrate). Now we drill the actual patterns. Each numbered section is a self-contained reference: read the Mental Model + Why interviewers care first, then the code, then the Walkthrough where present. The day-before cram at the bottom is the 60-second refresher.

## 1. Debounce
**Intent**: collapse rapid calls; fire only after `wait` ms of silence. Common: search-as-you-type, autosave.

### Mental Model
```
Elevator door analogy:
Each call() is a new person walking up to the elevator.
The doors START a 'close in WAIT ms' timer.
Each new arrival CANCELS the existing timer and starts a fresh one.
The elevator only closes when WAIT ms pass with no new arrivals.

Timeline (wait = 300ms):
call────call──call──────call───────────────► time
  └reset └reset └reset    └──300ms─►FIRE
```
State you must track:
- `timer` — the pending setTimeout id (or null).
- `lastArgs` / `lastThis` — so the deferred call uses the *latest* arguments, not the first.

### Why interviewers care
They're testing three things at once:
- **Timer lifecycle**: can you correctly clearTimeout + reassign without leaks?
- **Closures**: the inner function must close over the outer state (`timer`, `lastArgs`).
- **API design**: do you volunteer `cancel`/`flush` without being asked?

### Common beginner confusion: debounce vs throttle
> "I want my expensive function to run *at most* every 200ms."

That's throttle, not debounce. Debounce will *never* fire while calls keep coming faster than wait. Throttle guarantees a steady drip.

> "I want it to fire immediately on the first call and then wait."

That's `leading: true`. The default in most libraries is trailing-only.

```js
function debounce(fn, wait, { leading = false, trailing = true } = {}) {
  let timer, lastArgs, lastThis, result;
  const invoke = () => { result = fn.apply(lastThis, lastArgs); };
  const debounced = function (...args) {
    lastArgs = args; lastThis = this;
    const callNow = leading && !timer;
    clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      if (trailing) invoke();
    }, wait);
    if (callNow) invoke();
    return result;
  };
  debounced.cancel = () => { clearTimeout(timer); timer = null; };
  debounced.flush = () => { if (timer) { clearTimeout(timer); timer = null; invoke(); } };
  return debounced;
}
```
**Tweaks**: leading edge, flush/cancel API, maxWait.

### Step-by-step walkthrough
Trace `const d = debounce(fn, 300)`, then `d("a")`, then 100ms later `d("b")`, then 350ms of silence:

```
t=0     d("a") called
        lastArgs=["a"], lastThis=this
        callNow = leading(false) && !timer  → false
        clearTimeout(timer=undefined) → no-op
        timer = setTimeout(..., 300)  // scheduled at t=300

t=100   d("b") called
        lastArgs=["b"]  ← UPDATED to latest args
        callNow = leading(false) && !timer(truthy) → false
        clearTimeout(timer)  ← old timer cancelled
        timer = setTimeout(..., 300)  // re-scheduled at t=400

t=400   timer fires
        timer = null
        trailing(true) → invoke() runs fn.apply(this, ["b"])
        Result: fn called ONCE with "b". "a" was discarded.
```

The single most important insight: **`lastArgs` is overwritten on every call**, so the eventual fire uses only the last seen arguments. That's *exactly* what a search box wants.

### Interview storytelling
"I'll start with the simplest trailing-only debounce, then layer in leading edge as an option, then expose cancel/flush. Cancel is essential for component teardown — without it, the timer fires after the component is gone and references stale closures." Then write the code. Expected follow-ups:
- "Add `maxWait`." → track a separate `maxTimer` that fires regardless of new calls.
- "Make it work with async functions returning the eventual result." → store and return a Promise; resolve it when the trailing fire happens.
- "How do you test this?" → fake timers (`jest.useFakeTimers()`); assert call count after `advance(wait)`.

---

## 2. Throttle
**Intent**: at most one call per `interval`. Common: scroll, resize, metric emit.

### Mental Model
```
Faucet limiter analogy:
The water (events) is flowing continuously, but the regulator delivers
at most ONE drop per WAIT ms.

Timeline (wait = 100ms, leading=true, trailing=true):
calls:    | | | |  | | |     | |
          ▼ ▼ ▼ ▼  ▼ ▼ ▼     ▼ ▼
fired:    █────────█─────────█──────█
          0       100        200    300
          ↑                         ↑
          leading edge              trailing edge
          (first call fires now)    (one queued call after silence)
```
State to track:
- `last` — timestamp of the most recent fire.
- `timer` — pending trailing-edge fire (if any).
- `lastArgs` — for the trailing fire.

### Why interviewers care
- **Time arithmetic**: `wait - (now - last)` is the kind of expression where off-by-one is common.
- **Leading vs trailing semantics**: do you know that with both true, you can get *two* fires for one burst (one at the start, one at the end)?
- **The Date.now / performance.now choice** — see edge case #7 above. Bringing it up unprompted is a senior signal.

### Common beginner confusion: throttle vs debounce
- Throttle **always** fires at regular intervals during a continuous stream of calls.
- Debounce **never** fires during a continuous stream — only after silence.
- If your interview prompt says "fire at most once per N ms", that's throttle.
- If it says "fire after the user stops doing X for N ms", that's debounce.

Another trap: `leading=true, trailing=false` throttle = "fire the first call in each window, drop the rest." That's the "fire-and-forget" flavor used for scroll-position sampling.

```js
function throttle(fn, wait, { leading = true, trailing = true } = {}) {
  let last = 0, timer, lastArgs, lastThis;
  return function (...args) {
    const now = Date.now();
    if (!last && !leading) last = now;
    const remain = wait - (now - last);
    lastArgs = args; lastThis = this;
    if (remain <= 0) {
      clearTimeout(timer); timer = null;
      last = now;
      fn.apply(lastThis, lastArgs);
    } else if (!timer && trailing) {
      timer = setTimeout(() => {
        last = leading ? Date.now() : 0;
        timer = null;
        fn.apply(lastThis, lastArgs);
      }, remain);
    }
  };
}
```
**Tweaks**: leading-only, trailing-only, both.

### Step-by-step walkthrough
Trace `const t = throttle(fn, 100)` (leading & trailing true), then `t("a")` at t=0, `t("b")` at t=50, `t("c")` at t=80, then silence:

```
t=0    t("a"): now=0, last=0 → remain = 100 - (0-0) = 100
       leading=true, last stays 0 logically; the branch reads
       'if (!last && !leading) last = now' — last IS 0 but leading is true,
       so we DON'T reset last. remain<=0? No (remain=100).
       !timer && trailing → schedule trailing fire in 100ms. lastArgs=["a"]
       (Note: this minimal impl fires only on trailing; libraries differ.
        Read the code carefully — interviewers will dissect every branch.)

t=50   t("b"): now=50, last=0 → remain = 100 - 50 = 50
       timer is already set; !timer is false → do nothing.
       lastArgs=["b"]  ← overwritten

t=80   t("c"): same logic; lastArgs=["c"]

t=100  Trailing timer fires:
       last = leading ? Date.now() : 0  → last = 100
       timer = null
       fn.apply(this, ["c"])  ← only "c" runs, "a" and "b" coalesced.
```

The structural insight: **throttle keeps state across calls (`last` timestamp)**; debounce keeps state across calls within a *single window* (`timer`). Throttle is "have I fired recently?", debounce is "has the storm settled?".

### Interview storytelling
"Throttle has two firing edges — leading (immediate) and trailing (window's-end coalesced call). I'll write the both-true version since it's the most common; the option flags let me degrade to either pure form. Like debounce, I'd add a cancel hook for teardown."
Expected follow-ups:
- "Switch to performance.now for monotonicity." → trivial substitution; emphasize clock-jump immunity.
- "Make it work across worker threads." → can't share JS timers; share state via SharedArrayBuffer or an external store.

---

## 3. Retry with exponential backoff
**Intent**: retry transient failures (HTTP 5xx, ECONNRESET) with growing delays + jitter.

### Mental Model
```
Polite-knocking analogy:
  attempt 0  → knock                ✗  fail
  attempt 1  → wait 200ms           ✗  fail
  attempt 2  → wait 400ms           ✗  fail
  attempt 3  → wait 800ms           ✓  ok

Without jitter, every client in the world retries at the SAME instant
after an outage — the recovery moment becomes a self-DDoS ("thundering herd").
Jitter randomizes each client's retry time so the recovery is spread out.
```

### Why interviewers care
- **Loop control flow**: `while(true)` with try/catch is the cleanest shape; many candidates over-engineer with recursion.
- **Termination correctness**: do you re-throw on the LAST attempt? Off-by-one here means infinite retries or one-attempt-too-few.
- **Distributed-systems awareness**: jitter & idempotency. If they mention "what if the request was actually processed but you got a timeout?", they're testing if you know that retries assume idempotent operations.

### Common beginner confusion
- "Retry on any error" is wrong — some errors (400, 401, business validation) are *deterministic* and won't change on retry. Add a `shouldRetry(err)` predicate.
- "Linear delay is fine" — for transient overload, exponential is essential; linear keeps hitting the downstream at the same cadence that just overwhelmed it.

```js
async function retry(fn, { retries = 3, base = 200, factor = 2, jitter = true } = {}) {
  let attempt = 0;
  while (true) {
    try { return await fn(attempt); }
    catch (e) {
      if (attempt >= retries) throw e;
      const delay = base * factor ** attempt * (jitter ? 0.5 + Math.random() : 1);
      await new Promise(r => setTimeout(r, delay));
      attempt++;
    }
  }
}
```
**Tweaks**: retryable-error predicate, AbortSignal, max total time, full vs equal jitter.

### Step-by-step walkthrough
Trace `retry(fn, { retries: 2, base: 100 })` where fn fails twice then succeeds:

```
attempt=0  fn(0) throws  → caught
           0 >= 2? no    → delay = 100 * 2^0 * jitter(~0.5..1.5) ≈ 50..150ms
           sleep, attempt=1

attempt=1  fn(1) throws  → caught
           1 >= 2? no    → delay = 100 * 2^1 * jitter ≈ 100..300ms
           sleep, attempt=2

attempt=2  fn(2) resolves → return value. Loop exits.
```

If attempt=2 had thrown: `2 >= 2` → re-throw. Total attempts = retries+1 (3 here). Common off-by-one: people write `if (attempt > retries)` and get one extra try.

---

## 4. Promise pool / concurrency limiter
**Intent**: run N tasks at most K in parallel.

### Mental Model
```
Parking lot with K spaces:
                 ┌───────────────────────┐
queue: [t4 t5 t6]│ [t1] [t2] [t3]        │  ← capacity K=3 running
                 └───────────────────────┘
                          │
            Promise.race picks the FIRST car to leave;
            then t4 pulls in.
```
Key trick: `Promise.race(executingSet)` resolves as soon as *any* task finishes, letting us un-block and admit the next.

### Why interviewers care
- **Concurrency primitive composition** — pool is the building block for crawlers, fan-out fetchers, bulk DB writers.
- **Order vs throughput trade-off** — do you preserve input order in results? (Yes if you `results.push(p)` and `Promise.all(results)` at the end — output order matches input order even if completion order differs.)
- **Error handling** — if one task rejects, `Promise.all` fails fast. Senior candidates note this and offer an `allSettled` variant.

### Common beginner confusion
- "Just slice the array into K-sized chunks." — wrong; that's *batched parallel*, not bounded concurrency. If chunk #1 has one slow task, the whole batch stalls. True pool keeps K in flight at all times.
- Forgetting `.finally(() => executing.delete(p))` → the set never shrinks, race always picks the original task. Classic bug.

```js
async function pool(tasks, limit) {
  const results = [];
  const executing = new Set();
  for (const task of tasks) {
    const p = Promise.resolve().then(() => task());
    results.push(p);
    executing.add(p);
    p.finally(() => executing.delete(p));
    if (executing.size >= limit) await Promise.race(executing);
  }
  return Promise.all(results);
}
```
**Tweaks**: streaming (yield results as they finish), fail-fast vs allSettled.

---

## 5. EventEmitter from scratch
**Intent**: Node's core pub-sub primitive.

### Mental Model
```
Radio station with channels:
  on(event, fn)   = tune fn into channel `event`
  off(event, fn)  = unsubscribe fn from channel `event`
  once(event, fn) = subscribe-then-self-unsubscribe
  emit(event, …) = broadcast on channel

Internal: Map<eventName, Array<listenerFn>>
   "click"  → [fn1, fn2, fn3]
   "submit" → [fn4]
```

### Why interviewers care
- **Pub-sub structure** (Map of arrays) is foundational; many real Node APIs inherit from EventEmitter.
- **The listener-mutation-during-emit trap**: if a listener calls `off` for the next listener, the next listener gets *skipped* because the array shifted under iteration. The fix `[...arr].forEach(...)` is the senior-level detail.
- **once correctness** — implemented via a wrapper that removes itself; checking that you handle this without leaking the wrapper is a common ask.

### Common beginner confusion
- "Why a wrapper for `once`? Just remove `fn` on first call." — but if the user called `off(event, fn)` later, they'd pass the *original* fn, and you stored the *wrapper*. You need a stable wrapper that the `off` path can find via the user's `fn`. (Production EventEmitter exposes `originalListener` or does linear scan checking `listener.listener === fn`.)
- Forgetting to return `this` from `on/off/once` → breaks chaining: `emitter.on('a', f).on('b', g)`.

```js
class EventEmitter {
  #listeners = new Map();
  on(event, fn) {
    if (!this.#listeners.has(event)) this.#listeners.set(event, []);
    this.#listeners.get(event).push(fn);
    return this;
  }
  once(event, fn) {
    const wrapper = (...a) => { this.off(event, wrapper); fn(...a); };
    return this.on(event, wrapper);
  }
  off(event, fn) {
    const arr = this.#listeners.get(event);
    if (!arr) return this;
    const i = arr.indexOf(fn);
    if (i >= 0) arr.splice(i, 1);
    return this;
  }
  emit(event, ...args) {
    const arr = this.#listeners.get(event);
    if (!arr) return false;
    [...arr].forEach(fn => fn(...args));   // copy to allow off during emit
    return true;
  }
}
```
**Tweaks**: maxListeners warning, error event special handling, async listeners.

### Step-by-step walkthrough — the copy-before-iterate trick
```js
emitter.on("x", function a() {
  emitter.off("x", b);   // <-- a removes b mid-emit
});
emitter.on("x", function b() { console.log("b fires"); });
emitter.on("x", function c() { console.log("c fires"); });
emitter.emit("x");
```
Without the spread copy: iteration uses the live array. After `a` runs, `b` is removed; the loop index advances; `c` becomes index 1 — but the loop already moved past index 1 to look at index 2 (out of bounds). Net effect: **c is silently skipped**.
With `[...arr].forEach`: the array is a snapshot; all original listeners run; `off` only affects the *next* `emit`.

---

## 6. Pub-Sub
**Intent**: decoupled message bus, often topic-based. Differs from EventEmitter by usage shape — typically a singleton.

### Mental Model
EventEmitter and Pub-Sub are *almost* the same data structure (Map of topic → listeners). The difference is contract:
- **EventEmitter**: typically *attached to one object* — "this stream emits 'data' and 'end' events."
- **Pub-Sub**: typically a *global bus* — "anyone in the app can subscribe to 'user.signup'."

The subtle API difference: pub-sub's `subscribe` usually returns an **unsubscribe function**, so callers don't need to keep their `fn` around or remember the topic name to clean up.

### Why interviewers care
- **Contract design** — returning the unsubscribe handle is a deliberate API choice; explain *why* (callers shouldn't have to retain fn + topic to clean up; it composes with `useEffect` and signal patterns).
- **Set vs Array** for listeners — Set gives O(1) delete; Array gives ordered traversal. The example uses Set, which is fine when order doesn't matter.

### Common beginner confusion
- "Pub-Sub and Observer are the same." — Loosely yes; precisely no. Observer (GoF pattern) typically has the *subject* directly know its observers. Pub-Sub inserts a *broker* (the bus) between publisher and subscriber, so they don't know each other exist.
- Forgetting to clean empty topics — over time `topics.get('rare.event')` keeps an empty Set; for very dynamic topic spaces, delete the topic when its Set becomes empty.

```js
function createPubSub() {
  const topics = new Map();
  return {
    subscribe(topic, fn) {
      if (!topics.has(topic)) topics.set(topic, new Set());
      topics.get(topic).add(fn);
      return () => topics.get(topic).delete(fn);   // unsubscribe
    },
    publish(topic, data) {
      topics.get(topic)?.forEach(fn => fn(data));
    },
  };
}
```
**Tweaks**: wildcards, async handlers, dead-letter for errors.

---

## 7. Observable (mini-RxJS)
**Intent**: lazy stream of values with subscribe/unsubscribe semantics.

### Mental Model
A Promise is "one value, eventually." An Observable is "zero-or-more values, lazily, over time." Think of it as a **function that hasn't been called yet** — calling `subscribe` is what *starts* the producer.

```
Promise:    [───────────────────►●]    (one value or error)
Observable: [───●───●───●───●───●─...] (stream, may complete)
              ▲
              subscribe() turns on the spigot.
```

### Why interviewers care
- **Lazy evaluation** — producers only fire when subscribed. Many candidates forget and create eager streams.
- **Teardown discipline** — every subscription must return a way to stop the producer. Memory leak otherwise.
- **Operator chaining** — `map`/`filter`/etc each return a *new* Observable wrapping the source.

### Common beginner confusion
- Confusing Observable with Promise — Observables can emit multiple values; Promises resolve once.
- Hot vs cold: a *cold* Observable runs its producer per subscriber (independent streams); a *hot* one shares one producer across subscribers (like an event listener). The minimal impl above is cold.

```js
class Observable {
  constructor(producer) { this._producer = producer; }
  subscribe(observer) {
    const obs = typeof observer === "function" ? { next: observer } : observer;
    const teardown = this._producer(obs);
    return { unsubscribe: () => teardown?.() };
  }
  map(fn) {
    return new Observable(obs =>
      this.subscribe({ next: v => obs.next(fn(v)), error: obs.error, complete: obs.complete }).unsubscribe);
  }
}
```
**Tweaks**: error/complete callbacks, operators (filter, take), hot vs cold.

---

## 8. Currying
**Intent**: convert `f(a, b, c)` into `f(a)(b)(c)` (or partial: `f(a, b)(c)`).

### Mental Model
```
Original:   add(a, b, c)
Curried:    add(a)(b)(c)      OR  add(a, b)(c)  OR  add(a)(b, c)

Internal:   keep a running args list; each call appends;
            when args.length reaches the original arity (fn.length),
            invoke the underlying fn.
```

### Why interviewers care
- **Closures** — each partial call returns a new closure capturing accumulated args. Classic test of closure mastery.
- **`fn.length`** — knowing this property holds the parameter count (not counting defaults/rest) is a JS-trivia test.
- **Recursion structure** — the recursive `curried` call is elegant; a candidate who writes a sprawling state machine instead has missed the point.

### Common beginner confusion
- "Why does `fn.length` give the arity?" — it's the count of formal parameters *before* the first default or rest. So `function f(a, b = 1, c)` has `f.length === 1`. Currying breaks on default params unless you pass arity explicitly.
- Confusing curry with partial application — curry insists on one-arg-per-call (strict curry) or any-arg-per-call until arity reached (relaxed curry, common JS flavor); partial just bakes in some args ahead of time without changing the call shape.

```js
function curry(fn) {
  return function curried(...args) {
    return args.length >= fn.length
      ? fn.apply(this, args)
      : (...more) => curried.apply(this, [...args, ...more]);
  };
}
```
**Tweaks**: variadic, placeholder support (`_`).

---

## 9. Compose / Pipe
**Intent**: function composition. `compose(f,g,h)(x) === f(g(h(x)))`. `pipe` is left-to-right.

### Mental Model
```
Assembly line:
                  pipe(f, g, h)(x)
   x → [ f ] → [ g ] → [ h ] → result
        left ───────────── right

                  compose(f, g, h)(x)
   x → [ h ] → [ g ] → [ f ] → result
        right ────────────── left
```
Same machine, opposite reduce direction. Pipe reads naturally as "do X, then Y, then Z." Compose reads as math (f∘g∘h).

### Why interviewers care
- **Reduce mastery** — `reduce` for pipe, `reduceRight` for compose. Demonstrates fluency with array methods.
- **Higher-order function pattern** — both return a function that returns a value. Two layers of closure.
- **Async extension** — once you grasp the sync version, the async version (`p.then(f)` instead of `f(v)`) is a one-liner. Interviewers like to see you make that leap.

### Common beginner confusion
- Compose argument order — *new* developers expect left-to-right (because we read left-to-right). It's right-to-left because of the mathematical f∘g convention. Pipe was invented precisely because compose's order felt unnatural for data pipelines.
- "Why two functions, not one with a flag?" — convention. Pipe and compose are recognizable names in functional libraries; an `order: 'ltr'` param would be more confusing.

```js
const compose = (...fns) => x => fns.reduceRight((v, f) => f(v), x);
const pipe    = (...fns) => x => fns.reduce((v, f) => f(v), x);

// Async pipe
const pipeAsync = (...fns) => x => fns.reduce((p, f) => p.then(f), Promise.resolve(x));
```
**Tweaks**: async, multi-arg first fn.

---

## 10. Deep clone (with cycles)
**Intent**: structural copy. Modern: `structuredClone(x)` — but interviewers want the impl.

### Mental Model
```
Recursion + a WeakMap memo:

  clone(node):
    if node is primitive → return as-is
    if node already in `seen` → return seen.get(node)   ← cycle break
    create a fresh container of the same shape
    register seen.set(node, container)  ← register BEFORE recursing
    for each child key: container[key] = clone(child)
    return container
```
The "register before recursing" step is what makes cycles work. If A points to B and B points back to A, the recursion into B sees A already in `seen` and returns the in-progress clone without infinite descent.

### Why interviewers care
- **Recursion with memo** — classic dynamic-programming flavor applied to data structures.
- **Type discrimination** — Date, RegExp, Map, Set, Array, plain object all need different handling. Reveals breadth of JS knowledge.
- **Prototype preservation** — copying via `Object.create(Object.getPrototypeOf(x))` keeps the class. Many candidates use `{}` and silently break instanceof.

### Common beginner confusion
- Using JSON.parse(JSON.stringify(x)) — fast, but breaks on cycles (throws), Dates (becomes string), Maps/Sets (becomes {}), undefined (omitted), functions (omitted), Symbols (omitted). Fine for plain JSON-shaped data only.
- Forgetting to register *before* recursing → infinite recursion on cycles.
- Cloning a class instance into a plain object — instanceof fails afterward. Use the prototype-preserving form.

```js
function deepClone(x, seen = new WeakMap()) {
  if (x === null || typeof x !== "object") return x;
  if (seen.has(x)) return seen.get(x);
  if (x instanceof Date) return new Date(x);
  if (x instanceof RegExp) return new RegExp(x.source, x.flags);
  if (x instanceof Map) {
    const m = new Map(); seen.set(x, m);
    for (const [k, v] of x) m.set(deepClone(k, seen), deepClone(v, seen));
    return m;
  }
  if (x instanceof Set) {
    const s = new Set(); seen.set(x, s);
    for (const v of x) s.add(deepClone(v, seen));
    return s;
  }
  const out = Array.isArray(x) ? [] : Object.create(Object.getPrototypeOf(x));
  seen.set(x, out);
  for (const k of Reflect.ownKeys(x)) out[k] = deepClone(x[k], seen);
  return out;
}
```
**Tweaks**: handle Buffer, TypedArray; functions usually not cloned.

---

## 11. Memoize (with eviction)
**Intent**: cache pure function results. Variants: unbounded Map, LRU, TTL.

### Mental Model
```
Notepad analogy:
  call fn(args):
    key = serialize(args)
    if key in cache → return cache[key]      ← cache hit
    val = fn(args)
    cache[key] = val                          ← store
    return val
```
The harder part isn't the cache — it's the **key function**. Two calls are "the same" only if their key strings are equal.

### Why interviewers care
- **Key-derivation strategy** — `JSON.stringify` is the default; they'll push you on why it's bad for objects with different key orders, functions, circular refs.
- **Eviction policy** — unbounded memoize *is* a memory leak in disguise; LRU is the senior answer.
- **Async memoize gotcha** — you must cache the *Promise*, not the awaited value, otherwise concurrent callers each kick off a fresh fn call before the first resolves (cache stampede).

### Common beginner confusion: cache keys
- `memoize(JSON.stringify)` on `{a:1, b:2}` and `{b:2, a:1}` produces *different* keys despite being logically equal. Stable serializer or sorted keys solve this.
- Using object identity (Map keyed by the args object) breaks across calls — every fresh call site passes a new object.
- Cache key for primitives: usually safe (`String(arg)` or just `arg`). For objects: WeakMap if you want GC-friendly, JSON.stringify if you accept the limitations, custom hash if you control the schema.

```js
function memoize(fn, { key = (...a) => JSON.stringify(a), max = Infinity } = {}) {
  const cache = new Map();
  return function (...args) {
    const k = key(...args);
    if (cache.has(k)) { const v = cache.get(k); cache.delete(k); cache.set(k, v); return v; }
    const v = fn.apply(this, args);
    cache.set(k, v);
    if (cache.size > max) cache.delete(cache.keys().next().value);
    return v;
  };
}
```
**Tweaks**: WeakMap for object arg, async (cache Promise, not awaited value).

---

## 12. LRU Cache
**Intent**: bounded cache, evict least-recently-used. `Map` insertion order makes this clean.

### Mental Model
```
Classic LRU = HashMap + Doubly-Linked List

   HashMap (key → node)                 Doubly-Linked List (recency)
   ┌─────────────────┐                  HEAD ↔ N1 ↔ N2 ↔ N3 ↔ TAIL
   │ "a" → N3        │                  ↑                      ↑
   │ "b" → N1        │                  LRU                   MRU
   │ "c" → N2        │
   └─────────────────┘

   get("a"): hashmap → N3 → unlink, append to tail (now MRU)
   set("d") when full: drop HEAD (LRU), insert at TAIL.

In JavaScript, Map ALREADY is HashMap + insertion-order list!
   m.delete(k); m.set(k, v) = "unlink + re-append" in O(1)
   m.keys().next().value     = "the head node"      in O(1)
So the Map-based LRU is a 10-line equivalent of the classic textbook impl.
```

### Why interviewers care
- **Data structure composition** — they want you to recognize that LRU is fundamentally two structures glued. If you write the Map version, expect "now do it without Map" → you must implement HashMap + Doubly Linked List manually (the textbook LeetCode 146).
- **O(1) on both ops** — they'll ask "why is this O(1)?" and want you to point to (a) hash lookup O(1), (b) linked-list splice O(1), (c) `keys().next()` is a single-node read.

### Common beginner confusion
- "delete + set is just two operations, must be O(2)." → O(1) and O(2) are the same complexity class. Constant work per op.
- Confusing LRU with LFU (least *frequently* used). LFU tracks counts; LRU tracks recency. Different policies, different code.
- For Map-based LRU, mutating values without re-setting → recency NOT updated. Always `delete` then `set` even on update.

```js
class LRU {
  constructor(capacity) { this.cap = capacity; this.m = new Map(); }
  get(k) {
    if (!this.m.has(k)) return undefined;
    const v = this.m.get(k);
    this.m.delete(k); this.m.set(k, v);          // move to end
    return v;
  }
  set(k, v) {
    if (this.m.has(k)) this.m.delete(k);
    this.m.set(k, v);
    if (this.m.size > this.cap) this.m.delete(this.m.keys().next().value);
  }
}
```
**Tweaks**: TTL per entry, peek (no LRU bump), size as bytes not count.

---

## 13. Rate Limiter — Token Bucket
**Intent**: allow bursts up to bucket size, refill at constant rate.

### Mental Model
```
Refilling water bucket:
   capacity = 20 tokens
   refill rate = 100/60 tokens/sec  (≈ 1.67/sec → ≈ 100 per minute)

   bucket level over time (no requests):
   0 ──── 5s ──── 10s ──── 12s (full at 20)
   ↑                       ↑
   start                   capped at capacity (no overflow)

   on take(1):
     refill based on elapsed time  (lazy refill — no setInterval)
     if level >= 1: level -= 1, return true (allow)
     else: return false (reject / 429)
```
Beauty: **lazy refill**. No timer, no setInterval. Each `take` updates the bucket level based on time elapsed since last touch.

### Why interviewers care
- **Math correctness** — the refill formula `tokens += dt * rate` capped at `cap` is one line; off-by-one or unit mistakes (ms vs sec) are common.
- **Per-tenant isolation** — they often follow up "now make it per-API-key" → `Map<key, bucket>`.
- **Multi-process awareness** — single-process bucket is in-memory; senior candidates note that prod needs Redis (with Lua script for atomicity).

### Common beginner confusion
- "Use setInterval to refill." — works but wastes CPU and timer slots; lazy refill is strictly better.
- Forgetting to cap at `cap` → bucket grows unboundedly, defeating the burst limit.
- Date.now vs performance.now — use `performance.now()` to be immune to wall-clock adjustments (NTP, manual clock changes, DST). Bring this up unprompted.

```js
class TokenBucket {
  constructor(capacity, refillPerSec) {
    this.cap = capacity; this.rate = refillPerSec;
    this.tokens = capacity; this.last = Date.now();
  }
  take(n = 1) {
    const now = Date.now();
    this.tokens = Math.min(this.cap, this.tokens + (now - this.last) / 1000 * this.rate);
    this.last = now;
    if (this.tokens >= n) { this.tokens -= n; return true; }
    return false;
  }
}
```
**Tweaks**: async `await take()` that waits until tokens available.

---

## 14. Rate Limiter — Leaky Bucket
**Intent**: smooth out bursts; output at constant rate regardless of input.

### Mental Model
```
Bucket with a hole:
   ┌──────┐  ← pour requests in (any rate)
   │ ████ │
   │ ██   │
   │      │
   └──┬───┘
      ↓ leak at fixed rate
   output (steady drip)

If bucket OVERFLOWS on input → reject the request.
If bucket has room → accept; it will be processed at the leak rate.
```

### Token vs leaky — when to pick which
- **Token bucket** allows **bursts** up to capacity, then throttles to refill rate. Good for APIs where occasional spikes are fine.
- **Leaky bucket** *smooths* output to a constant rate regardless of input shape. Good for downstream protection where the consumer can only handle X/sec.

### Why interviewers care
- **Differentiating the two** — many candidates conflate them. Spelling out the burst vs smoothing distinction is the senior signal.
- **Math symmetry** — leaky uses `level -= dt*rate, max 0`; token uses `tokens += dt*rate, min cap`. Mirror images.

### Common beginner confusion
- "Aren't they the same?" — Same complexity, opposite metaphor. Token measures *available credit*; leaky measures *pending load*.
- Forgetting `Math.max(0, ...)` — level can go negative if you don't clamp, producing nonsense allowances.

```js
class LeakyBucket {
  constructor(capacity, leakPerSec) {
    this.cap = capacity; this.rate = leakPerSec;
    this.level = 0; this.last = Date.now();
  }
  add(n = 1) {
    const now = Date.now();
    this.level = Math.max(0, this.level - (now - this.last) / 1000 * this.rate);
    this.last = now;
    if (this.level + n > this.cap) return false;
    this.level += n; return true;
  }
}
```

---

## 15. Polyfills — `bind`, `call`, `apply`

### Mental Model
```
call(ctx, a, b)   → "invoke this function with `ctx` as `this`, args a,b"
apply(ctx, [a,b]) → same, but args as an array
bind(ctx, a)      → "give me back a NEW function permanently glued to `ctx` with `a` pre-supplied"
```

### Why interviewers care
- **`this` binding rules** — the whole polyfill exists because `this` is dynamic. Implementing it forces you to articulate exactly how `this` works.
- **The Symbol trick for `call`** — assigning `this` (the original fn) to a unique Symbol property on `ctx`, calling it, then deleting. Cleaner than older-style `ctx.__fn__` because Symbol won't clash with existing keys.
- **`bind` + `new`** — when the bound function is called with `new`, the bound `this` is *ignored* and `new`'s freshly-created object wins. Senior candidates handle this with `new.target`.

### Common beginner confusion
- "Just use arrow functions to avoid `this` issues." — true in many cases, but interview prompt asks you to *implement bind*, so you must reason about dynamic `this`.
- Forgetting prototype chain on bind — calling `new boundFn()` should make `instanceof OriginalFn` true. That's what `bound2.prototype = Object.create(fn.prototype || null)` ensures.

```js
Function.prototype.myCall = function (ctx, ...args) {
  ctx = ctx ?? globalThis;
  const sym = Symbol();
  ctx[sym] = this;
  const r = ctx[sym](...args);
  delete ctx[sym];
  return r;
};
Function.prototype.myApply = function (ctx, args = []) { return this.myCall(ctx, ...args); };
Function.prototype.myBind = function (ctx, ...bound) {
  const fn = this;
  function bound2(...args) {
    return fn.apply(new.target ? this : ctx, [...bound, ...args]);
  }
  bound2.prototype = Object.create(fn.prototype || null);
  return bound2;
};
```

---

## 16. Polyfill — `Promise.all`

### Mental Model
```
INPUT:    [p1, p2, p3, p4]
OUTPUT:   Promise<[v1, v2, v3, v4]> — resolves when ALL resolve
                 OR
          rejection — fails when ANY rejects (fail-fast)

Internal counter `done` ticks up on each fulfillment;
when done === arr.length → resolve with collected results in INPUT order.
```
Critical detail: results array is indexed by *input position*, not completion order. p3 may resolve first; `out[2]` is still its slot.

### Why interviewers care
- **The empty-array edge** — `Promise.all([])` resolves immediately with `[]`. Many candidates miss this; their polyfill hangs forever.
- **Wrapping non-promises** — `arr` may contain non-thenables; `Promise.resolve(p)` normalizes them.
- **Order vs completion-time** — testing whether you understand the resolved array shape.

### Common beginner confusion
- Forgetting `arr.length === 0` early-resolve → infinite-pending Promise.
- Resolving with `out` before all done — relying on `out.length` or `out.every(v => v !== undefined)` is wrong because `undefined` is a valid resolved value.
- Mutating shared state in then-callback without realizing settlements may be reordered.

```js
function promiseAll(arr) {
  return new Promise((resolve, reject) => {
    const out = []; let done = 0;
    if (arr.length === 0) return resolve([]);
    arr.forEach((p, i) =>
      Promise.resolve(p).then(
        v => { out[i] = v; if (++done === arr.length) resolve(out); },
        reject
      )
    );
  });
}
```
**Tweaks**: `allSettled` (never reject), `race` (first), `any` (first fulfilled, AggregateError otherwise).

---

## 17. Polyfills — `map` / `filter` / `reduce`

### Mental Model
```
map:     new array, same length, every element transformed by fn
filter:  new array, possibly shorter, only elements where fn(x) is truthy
reduce:  collapse the array to a single value via an accumulator

`i in this` check = "is this index ACTUALLY set?"
   const a = [];           a.length = 3;        // a is a "sparse" array: [, , ,]
   a[1] = 'x';
   0 in a  → false   (hole)
   1 in a  → true
   for-loop with `i in this` skips holes → matches native map/filter/reduce behavior.
```

### Why interviewers care
- **Spec-fidelity awareness** — many candidates forget that native `map` skips holes in sparse arrays.
- **Reduce's two forms** — with and without initial value. Without init, the first element becomes the accumulator and iteration starts at index 1. Catching this is a senior signal.
- **`thisArg` honoring** — accepting a thisArg means using `fn.call(thisArg, …)`. Easy to forget.

### Common beginner confusion
- Treating sparse arrays as if they were dense — `[1,,3].map(x => x*2)` returns `[2, <empty>, 6]`, NOT `[2, NaN, 6]`. The hole stays a hole.
- `reduce` with empty array & no init → must throw `TypeError`. Many polyfills silently return `undefined`.

```js
Array.prototype.myMap = function (fn, thisArg) {
  const out = new Array(this.length);
  for (let i = 0; i < this.length; i++)
    if (i in this) out[i] = fn.call(thisArg, this[i], i, this);
  return out;
};
Array.prototype.myFilter = function (fn, thisArg) {
  const out = [];
  for (let i = 0; i < this.length; i++)
    if (i in this && fn.call(thisArg, this[i], i, this)) out.push(this[i]);
  return out;
};
Array.prototype.myReduce = function (fn, init) {
  let i = 0, acc = init;
  if (arguments.length < 2) {
    while (i < this.length && !(i in this)) i++;
    if (i === this.length) throw new TypeError("Reduce of empty");
    acc = this[i++];
  }
  for (; i < this.length; i++) if (i in this) acc = fn(acc, this[i], i, this);
  return acc;
};
```
Note: `i in this` skips holes — same as native.

---

## 18. `once` (call only first time)

### Mental Model
```
First call:  → run fn, latch the flag, store value.
Later calls: → ignore args, return stored value.

It's a tiny finite state machine with two states: NOT_CALLED → CALLED.
```

### Why interviewers care
- **Closure-as-state** — the flag and cached value live in the closure. Demonstrates that closures are state machines.
- **Idempotency in user-facing APIs** — initializers, one-time event handlers, "show this modal only once."

### Common beginner confusion
- **Caching a rejected promise locks failure forever**. If fn returns a Promise and it rejects, the cached failure is what every future call returns. Decide: reset-on-failure? Or accept that failure is sticky? Either is valid, but you must choose.
- Treating once as "throttle of 1" — they're different; once never re-arms.

```js
function once(fn) {
  let called = false, value;
  return function (...args) {
    if (called) return value;
    called = true;
    return (value = fn.apply(this, args));
  };
}
```

---

## 19. Async queue (serial processor)
**Intent**: process tasks one at a time in order.

### Mental Model
```
A chain of promises:

   tail₀ = Promise.resolve()
   enqueue(t1): tail₁ = tail₀.then(t1)
   enqueue(t2): tail₂ = tail₁.then(t2)   ← waits for t1 to finish
   enqueue(t3): tail₃ = tail₂.then(t3)

Each enqueue extends the chain. Tasks run strictly in order.

Critical: this.tail = result.catch(()=>{}) — without it, ONE rejection
poisons the whole chain (every subsequent .then is skipped). With it,
errors are reported to the caller via `result` but the chain stays alive.
```

### Why interviewers care
- **Promise chaining as a queue** — elegant; no explicit array of pending tasks.
- **The poisoning trap** — without `.catch(()=>{})`, after one task errors, all subsequent enqueued tasks silently never run. The fact that you have to "branch" the chain (return one promise to caller, store another to the queue) is the senior insight.

### Common beginner confusion
- "Just push tasks into an array and `await` them in a loop." — works for batch processing, but doesn't dynamically accept new tasks while running.
- Returning `this.tail` to the caller — then the caller sees `undefined` (because of the .catch swallow). You must return `result`, store `result.catch(...)`.

```js
class AsyncQueue {
  constructor() { this.tail = Promise.resolve(); }
  enqueue(task) {
    const result = this.tail.then(task);
    this.tail = result.catch(() => {});       // don't poison chain
    return result;
  }
}
```
**Tweaks**: concurrency > 1 (becomes promise pool), pause/resume.

---

## 20. Batch processor
**Intent**: accumulate items, flush when batch size or timeout reached. Common for DB writes, metrics, logs.

### Mental Model
```
add(item)
   ↓
push to buffer
   ├── if buffer ≥ maxSize → flush NOW
   ├── else if no timer → start a maxWait timer that will flush
   └── else (timer running) → wait

flush:
   clear timer
   take a SNAPSHOT of buffer (set buffer = [])
   pass snapshot to user's flush callback
```

This is the **DataLoader pattern** under the hood — coalescing many small calls into one bulk operation.

### Why interviewers care
- **Race-condition awareness** — if `add` is called *during* an async flush, the new item must NOT be lost. Capturing the snapshot before resetting `this.buf = []` ensures the new item lands in the fresh buffer.
- **Two trigger conditions** — size AND time. Forgetting either is a partial solution.
- **Composable building block** — they may follow up with "make it return a Promise per add, resolved when that batch completes." Classic DataLoader API.

### Common beginner confusion
- Flushing the *reference* to `this.buf` and then clearing — the async flush may run concurrently with new `add` calls into the same reference. Always snapshot-then-reset.
- Forgetting to clear the timer on size-triggered flush → the timer fires later with an empty buffer (wasted work) or a now-stale batch.

```js
class Batcher {
  constructor({ maxSize = 100, maxWait = 1000, flush }) {
    this.maxSize = maxSize; this.maxWait = maxWait; this.flush = flush;
    this.buf = []; this.timer = null;
  }
  add(item) {
    this.buf.push(item);
    if (this.buf.length >= this.maxSize) return this._flush();
    if (!this.timer) this.timer = setTimeout(() => this._flush(), this.maxWait);
  }
  _flush() {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    const items = this.buf; this.buf = [];
    return this.flush(items);
  }
}
```

---

## Backend-specific notes
- **Debounce/throttle in backend**: rate-limiting metric pushes, log shipping intervals, cache-invalidation coalescing.
- **Retry**: HTTP clients to flaky downstreams (Stripe, S3); always combine with circuit breaker for cascading-failure resistance.
- **Promise pool**: outbound HTTP fan-out, parallel DB queries with bounded connection pool, batch fetches.
- **EventEmitter**: foundational — Streams, HTTP, child_process all inherit from it. Memory leaks if you `.on` without `.off` for transient instances.
- **LRU cache**: in-process caches for hot reads (config, parsed permissions, JWT decode). Always size-bound.
- **Token bucket**: API rate-limit middleware (per-user, per-IP). Backed by Redis for multi-process.
- **Batch processor**: bulk inserts (DB, ES, Kafka), DataLoader pattern for N+1 GraphQL queries.
- **AbortController**: thread through all retry/pool/batch APIs so request cancellations propagate.

## Debounce vs Throttle — side-by-side reference

This is the single most-asked comparison question. Internalize this table:

| Aspect | Debounce | Throttle |
|---|---|---|
| **Analogy** | Elevator doors waiting for stillness | Faucet limiter dripping at fixed rate |
| **Fires** | Once, after `wait` ms of silence | At most once per `interval` |
| **Continuous stream** | NEVER fires | Fires at regular intervals |
| **Use case** | Search input, autosave, validate-on-pause | Scroll, resize, mousemove, metrics |
| **Mental rule** | "Wait until quiet" | "Sample at most once per window" |
| **State** | `timer` (the pending fire) | `last` (when we last fired) + maybe `timer` for trailing |
| **Edge variants** | leading / trailing / maxWait | leading / trailing |
| **Cancel API** | Yes (clear pending timer) | Yes (clear trailing timer) |
| **Flush API** | Yes (fire pending immediately) | Less common |

Timeline contrast (calls = bursts every 50ms, wait/interval = 200ms):
```
calls:    ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ (continuous)
debounce: ─────────────────────────────────  (never fires — stream is continuous)
throttle: █───────█───────█───────█───────█   (every 200ms — steady drip)

calls:    ▼▼▼▼▼   (silence)   ▼▼▼▼▼   (silence)
debounce: ────────█────────────────────█──    (fires after each silence)
throttle: █───────█───────────────█───────█    (steady sampling within each burst)
```

## Patterns at a glance — what each owns
A senior-grade mental index. When you hear a problem, this should be your first scan:

| Pattern | Owns | Reach for when |
|---|---|---|
| Debounce | "settle after silence" | search-as-you-type, autosave, validate-on-blur |
| Throttle | "sample per window" | scroll, resize, mousemove, metric emit |
| Retry | "transient failure tolerance" | flaky HTTP, S3, DB connection drop |
| Promise pool | "bounded parallelism" | crawler, bulk import, fan-out fetch |
| EventEmitter / Pub-Sub | "decoupled broadcast" | streams, lifecycle events, cross-component messaging |
| Observable | "lazy stream of values" | reactive UIs, WebSocket data, sensor input |
| Compose / Pipe | "transformation pipeline" | data normalization, middleware chains |
| Deep clone | "structural copy" | undo/redo state, fixture cloning, props isolation |
| Memoize | "cache pure results" | recursive math, repeated expensive lookups |
| LRU cache | "bounded recency cache" | hot reads in-process, config caching, JWT decode |
| Token bucket | "burst-tolerant rate limit" | API gateway, per-user throttling |
| Leaky bucket | "smooth output rate" | downstream protection, traffic shaping |
| once | "idempotent initializer" | bootstrap fn, single-fire callbacks |
| Async queue | "serial async processing" | DB migrations, ordered writes, single-resource access |
| Batcher | "coalesce small ops into bulk" | DB batch inserts, DataLoader, log shipping |

## Senior storytelling: building a "live coding" answer
For any machine-coding prompt, follow this 6-beat script:

1. **Clarify** — "Before I code, can I confirm: leading or trailing? Sync or async fn? Should cancel be a feature?"
2. **Sketch the signature** — write the function signature and JSDoc-comment what each param means. This buys thinking time and prevents API rework.
3. **Name the state** — say out loud "I'll need a timer, lastArgs, and maybe a cancel handle."
4. **Write the minimum viable version** — leading-only or trailing-only first; pass a smoke test.
5. **Layer in features** — add cancel, then flush, then maxWait. State each layer's purpose before adding it.
6. **Edge-case audit** — close with "Things I'd add for production: AbortSignal support, monotonic clock, test coverage with fake timers."

If you do nothing else differently, doing this 6-beat script turns a "mid" coder into a "senior" coder in the interviewer's notes.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ MACHINE CODING — DAY-BEFORE CRAM                         │
├──────────────────────────────────────────────────────────┤
│ • debounce: timer reset on each call; cancel/flush API   │
│ • throttle: last + remain; leading/trailing variants     │
│ • retry: try/catch in loop, sleep(base*factor^n) +jitter │
│ • pool: Set + race when size>=limit                      │
│ • EventEmitter: Map<event, fn[]>; copy arr in emit       │
│ • pub-sub: Map<topic, Set<fn>>; sub returns unsub fn     │
│ • Observable: lazy subscribe → teardown                  │
│ • curry: args.length >= fn.length ? call : recurse       │
│ • compose=reduceRight, pipe=reduce                       │
│ • deepClone: WeakMap for cycles; handle Date/Map/Set     │
│ • memoize: Map + JSON.stringify key + LRU evict          │
│ • LRU: Map.delete-then-set on access; evict keys().next()│
│ • token bucket: tokens += dt*rate, cap; spend on take    │
│ • leaky bucket: level -= dt*rate, max 0; reject if full  │
│ • once: latch flag, return cached value                  │
│ • bind: new.target ? this : ctx; copy proto              │
│ • Promise.all: resolve at done===n; reject on first fail │
│ • myMap/filter/reduce: respect holes via `i in this`     │
│ • batcher: maxSize OR maxWait timeout → flush            │
│ • async queue: tail = tail.then(task); .catch(()=>{}) chain│
└──────────────────────────────────────────────────────────┘
```
