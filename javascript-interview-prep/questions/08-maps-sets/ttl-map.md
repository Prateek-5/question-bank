# TTL Map with auto-eviction — setTimeout vs lazy

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [lru-cache-with-map.md](./lru-cache-with-map.md)
>
> **Source:** Redis EXPIRE, node-cache, lru-cache. Session stores, rate limiters, idempotency keys.

---

## 1. Problem statement

Cache with per-entry TTL. Compare active (setTimeout per entry) vs lazy (check on read) eviction.

**Verification examples**

```js
const m = new TTLMap(60_000);
m.set('session-abc', userId);
m.get('session-abc');                    // userId
// 60 seconds later
m.get('session-abc');                    // undefined

m.set('one-shot', value, 5_000);         // explicit 5s TTL
```

**Constraints**
- Per-entry TTL (default + override).
- Active: per-entry setTimeout; need clearTimeout on overwrite/delete.
- Lazy: check `Date.now() >= entry.exp` on access.
- Use `Date.now()` (wall clock), not `performance.now()` (relative).

---

## 2. Plain-English restatement

Either schedule a timer per entry (active) or check timestamp lazily on read. Tradeoffs in timer churn vs memory drift.

---

## 3. Why this matters in interviews

Three senior concerns: timer management, memory pressure, API design (`get` returns undefined when expired). No single right answer — compare.

---

## 4. Mental model

```
   Lazy expiry:
     set(k, v, ttl): store {value, exp: now + ttl}.
     get(k): if exp < now, delete + return undefined.
     No timers. Memory grows until read or sweep.
     Wins: simple, zero timer overhead.
     Loses: stale entries linger; need periodic sweep or size cap.
   
   Active expiry (per-entry setTimeout):
     set(k, v, ttl): clearTimeout(old); store; schedule timeout.
     On timer fire: delete entry.
     Memory always bounded by live entries.
     Wins: bounded memory.
     Loses: timer churn (overwrite-heavy = thrash); each timer holds Map ref; consider .unref().
   
   Hybrid:
     Lazy + periodic sweep (every minute clear expired).
   
   Clocks:
     Date.now() — wall clock, JUMPS on NTP sync. OK for short TTLs.
     performance.now() — high-res monotonic, RELATIVE. Don't use for absolute TTLs.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Lazy vs active — which for high overwrite?
> 2. Why not `performance.now`?
> 3. Where do timers leak if not cleared?

---

## 6. Brute force — walked through

```js
// Active without clearTimeout — leaks phantom deletions
function set(k, v) {
  this.store.set(k, v);
  setTimeout(() => this.store.delete(k), ttl);   // older timer still fires later → drops new entry
}
```

Bug: overwrite leaves old timer, which deletes the new value when it fires.

---

## 7. The unlocking insight

> **Lazy: check exp on read; cheap; sweeps optional. Active: per-entry timer; bounded memory; clearTimeout on overwrite/delete. Trade timer churn vs memory drift.**

Three properties:

1. **`Date.now()`** for absolute TTL.
2. **`clearTimeout`** in active on overwrite.
3. **Lazy needs sweep or cap** to bound memory.

---

## 8. Solution (annotated)

```js
// Lazy
class LazyTTLMap {
  #store = new Map();                                                     // step 1: {value, exp}
  constructor(defaultTtl = 60_000) { this.defaultTtl = defaultTtl; }

  set(key, value, ttl = this.defaultTtl) {
    this.#store.set(key, { value, exp: Date.now() + ttl });
  }
  get(key) {
    const entry = this.#store.get(key);
    if (!entry) return undefined;
    if (Date.now() >= entry.exp) {                                         // step 2: lazy check
      this.#store.delete(key);
      return undefined;
    }
    return entry.value;
  }
  has(key) { return this.get(key) !== undefined; }                         // step 3: side-effect check
  delete(key) { return this.#store.delete(key); }

  sweep() {                                                                  // step 4: optional periodic
    const now = Date.now();
    for (const [k, e] of this.#store) {
      if (now >= e.exp) this.#store.delete(k);
    }
  }
}

// Active (per-entry timeout)
class ActiveTTLMap {
  #store = new Map();                                                     // key → {value, timer}
  constructor(defaultTtl = 60_000) { this.defaultTtl = defaultTtl; }

  set(key, value, ttl = this.defaultTtl) {
    if (this.#store.has(key)) {
      clearTimeout(this.#store.get(key).timer);                            // step 5: clear old
    }
    const timer = setTimeout(() => {
      this.#store.delete(key);
    }, ttl);
    if (typeof timer.unref === 'function') timer.unref();                  // step 6: don't keep process alive
    this.#store.set(key, { value, timer });
  }
  get(key) { return this.#store.get(key)?.value; }
  has(key) { return this.#store.has(key); }
  delete(key) {
    const entry = this.#store.get(key);
    if (!entry) return false;
    clearTimeout(entry.timer);                                              // step 7: clean timer
    return this.#store.delete(key);
  }
  clear() {
    for (const e of this.#store.values()) clearTimeout(e.timer);
    this.#store.clear();
  }
}

// Hybrid: lazy + periodic sweep
class HybridTTLMap extends LazyTTLMap {
  constructor(defaultTtl, sweepIntervalMs = 60_000) {
    super(defaultTtl);
    this.sweepTimer = setInterval(() => this.sweep(), sweepIntervalMs);
    this.sweepTimer.unref?.();
  }
  stop() { clearInterval(this.sweepTimer); }
}
```

**Try it yourself**

```js
const m = new LazyTTLMap(5_000);
m.set('k', 1);
m.get('k');                                                   // 1
// wait 6 sec
m.get('k');                                                   // undefined (deleted on access)

// Active version — bounded memory
const m2 = new ActiveTTLMap(5_000);
m2.set('session', userId);
// 5 sec later, automatically deleted

// Overwrite — active version clears old timer
m2.set('k', 1, 10_000);
m2.set('k', 2, 10_000);    // first timer cleared; only second fires

// Idempotency-key store
class IdempotencyStore extends LazyTTLMap {
  isProcessed(key) { return this.get(key) === true; }
  markProcessed(key, ttl) { this.set(key, true, ttl); }
}
```

---

## 9. Step-by-step dry run

```
LazyTTLMap, ttl=5000:
  t=0:    set('k', 1) → store: {k: {value:1, exp:5000}}.
  t=2000: get('k') → 2000 < 5000 → return 1.
  t=6000: get('k') → 6000 ≥ 5000 → delete, return undefined.

ActiveTTLMap, ttl=5000:
  t=0:    set('k', 1) → setTimeout(5000) → store: {k: {value:1, timer:T1}}.
  t=5000: T1 fires → store.delete('k').
  t=6000: get('k') → undefined.

Overwrite, active:
  t=0:  set('k', 1, 10000) → T1 (10s).
  t=2:  set('k', 2, 10000):
        store.has('k') → clearTimeout(T1). Schedule T2 (10s).
  t=12: T2 fires → delete. (T1 never fires; was cleared.)
  
  Without clearTimeout:
    T1 fires at t=10 (it was set at t=0 for 10s).
    T1 callback: store.delete('k').
    Now value 2 also deleted (set at t=2, intended to live until t=12). PHANTOM DELETION.

Lazy memory drift:
  Set 1M entries with TTL 1s. Never read again. None deleted. Memory grows.
  Mitigate: periodic sweep or size cap.

Active timer churn:
  set('rate-limit-user-42', n) every request, 1000 req/sec.
  Each set: clear + new setTimeout. V8 timer overhead noticeable.
  Lazy avoids this.
```

---

## 10. Common confusion + traps

1. **No clearTimeout** — phantom deletions.
2. **`performance.now()`** for TTL — relative, not absolute.
3. **Lazy without sweep** — memory grows.
4. **Timer pins process** — `.unref()` in Node.
5. **Wall clock jumps** — NTP sync can skip TTLs.
6. **Concurrent set/delete** — JS single-threaded; safe per turn.
7. **`has()` without expiry check** — returns stale true.

---

## 11. Senior follow-ups & variants

### Variant 1 — LRU + TTL
Combine eviction; expire on access.

### Variant 2 — Single coalesced sweep timer
One setInterval; cheaper than N setTimeouts.

### Variant 3 — Monotonic clock for short TTLs
`process.hrtime.bigint()` Node — but tracking across reboot is harder.

### Variant 4 — Distributed (Redis)
EXPIRE / PEXPIRE; PERSIST.

### Variant 5 — Heap-ordered expiry
Min-heap keyed by exp; pop expired on access.

---

## 12. How to think aloud

> "TTL Map has two implementation poles. **Lazy**: check `Date.now() >= entry.exp` on every read; if expired, delete and return undefined. No timers, simple, cheap on overwrite-heavy workloads. Memory drift: entries written and never read linger forever → pair with periodic sweep or size cap. **Active**: per-entry `setTimeout(() => delete, ttl)`; bounded memory; but on overwrite MUST `clearTimeout` the old timer (otherwise the old timer fires and deletes the new value — phantom deletion bug). Timer churn: heavy overwrite (e.g., rate-limit per request) means thousands of timer creates/clears per second — overhead matters. In Node, call `timer.unref()` so timers don't keep the process alive. **Hybrid**: lazy + a single `setInterval` sweep — best of both. **Clock**: use `Date.now()` (wall clock, ms since epoch) for absolute TTL; `performance.now()` is high-res MONOTONIC but RELATIVE — wrong for TTL. Wall clock can jump on NTP sync — minor for short TTLs. Variants: combine with LRU (max-size + TTL); distributed via Redis EXPIRE; min-heap of expiries for O(log n) earliest. Use cases: session stores, idempotency keys, JWT blacklists, rate-limit buckets, OTP caches. Trap: no clearTimeout (phantom delete); lazy without sweep (memory grows); performance.now (relative); not unref'ing timer."

---

## 13. 60-second revision

> - **Lazy:** check on read; sweep optional; no timer churn.
> - **Active:** per-entry setTimeout; bounded memory; clearTimeout on overwrite.
> - **Hybrid:** lazy + periodic sweep.
> - **`Date.now()`** — wall clock; `performance.now()` is relative.
> - **`.unref()`** in Node so timer doesn't pin process.
> - **Combine with LRU** for max-size.
> - **Min-heap** for O(log n) earliest expiry.
> - **Distributed:** Redis EXPIRE.
> - **Trap:** no clearTimeout (phantom); lazy no sweep; performance.now; no unref.

---

**Related:** [lru-cache-with-map.md](./lru-cache-with-map.md) · [cache-invalidate-by-tag.md](./cache-invalidate-by-tag.md) · [weakref-finalization-registry.md](./weakref-finalization-registry.md) · [`05-event-loop/settimeout-vs-setimmediate.md`](../05-event-loop/settimeout-vs-setimmediate.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/event-loop-architecture.md`](../../concepts/event-loop-architecture.md)
