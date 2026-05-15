# Machine-Coding Patterns (Meta Primer)

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

## 1. Debounce
**Intent**: collapse rapid calls; fire only after `wait` ms of silence. Common: search-as-you-type, autosave.

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

---

## 2. Throttle
**Intent**: at most one call per `interval`. Common: scroll, resize, metric emit.

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

---

## 3. Retry with exponential backoff
**Intent**: retry transient failures (HTTP 5xx, ECONNRESET) with growing delays + jitter.

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

---

## 4. Promise pool / concurrency limiter
**Intent**: run N tasks at most K in parallel.

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

---

## 6. Pub-Sub
**Intent**: decoupled message bus, often topic-based. Differs from EventEmitter by usage shape — typically a singleton.

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
