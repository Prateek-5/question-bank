# Circuit Breaker — three-state failure-isolation primitive

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [mini-state-machine.md](./mini-state-machine.md), [retry-with-jitter-and-budget.md](./retry-with-jitter-and-budget.md)
>
> **Source:** Michael Nygard's "Release It!" (2007); Netflix Hystrix, resilience4j, Polly, opossum. Asked at Razorpay, Stripe, Uber, Atlassian.

---

## 1. Problem statement

**Signature**
```ts
class CircuitBreaker {
  constructor(opts?: { threshold?: number; windowMs?: number; cooldownMs?: number; halfOpenMax?: number; isFailure?(err): boolean });
  exec<T>(fn: () => Promise<T>): Promise<T>;
  reset(): void;
  snapshot: { state: 'CLOSED'|'OPEN'|'HALF_OPEN'; failures: number; openedAt: number };
}
```

**Input / Output examples**

| Setup (threshold=3, window=10s, cooldown=5s)          | Behaviour                                              |
|--------------------------------------------------------|---------------------------------------------------------|
| 3 failures within 10s                                  | state → OPEN                                            |
| Call while OPEN                                        | throws `CircuitOpen` immediately, no downstream call   |
| Cooldown elapsed                                       | state → HALF_OPEN; one probe allowed                    |
| HALF_OPEN probe succeeds                               | state → CLOSED, failures cleared                       |
| HALF_OPEN probe fails                                  | state → OPEN, openedAt reset                            |
| 4xx error                                              | with injected `isFailure`, does NOT trip                |

**Constraints**
- Three states: CLOSED, OPEN, HALF_OPEN.
- Sliding-window failure count (default 10s).
- Bounded probes in HALF_OPEN (default 1).
- `isFailure(err)` injectable — distinguish caller (4xx) from server (5xx/timeout) errors.

---

## 2. Plain-English restatement

When a downstream service starts failing repeatedly, stop calling it for a while. Three states: **CLOSED** (normal, count failures), **OPEN** (short-circuit, reject without calling), **HALF_OPEN** (after cooldown, allow a few probes — success closes, failure re-opens). Prevents cascading failure: A's threads don't pile up waiting for B; instead A fails fast and falls back.

---

## 3. Why this matters in interviews

Cascading failure is the canonical distributed-systems incident. The circuit breaker is the protocol that says "stop calling B for 30 seconds; let it recover." Probes the three-state machine, knobs (threshold, window, cooldown, halfOpenMax), and operational instincts (per-key, alert on OPEN).

---

## 4. Mental model

```
                ┌──────────┐  failures < threshold   ┌──────────┐
   normal ───▶  │  CLOSED  │ ──────────────────────▶ │  CLOSED  │
   traffic      └────┬─────┘                         └──────────┘
                     │ failures >= threshold
                     ▼
                ┌──────────┐    cooldown elapsed    ┌─────────────┐
                │   OPEN   │ ─────────────────────▶ │ HALF_OPEN   │
                │ (reject) │                         │ (probe ≤N)  │
                └──────────┘                         └─────┬───────┘
                     ▲                                     │
                     │ probe fails                         │ probes ok
                     └─────────────────────────────────────┘
                                                           ▼
                                                      back to CLOSED
```

**Like an electrical fuse**: trips on overload, cools off, then probes to see if normal flow is back.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why per-downstream breaker, not one global breaker?
> 2. After cooldown, why allow only ONE probe, not full traffic?
> 3. Should 4xx errors trip the breaker?

---

## 6. Brute force — walked through

### Wrong attempt 1: no breaker, retry forever
Retries amplify load on slow downstream. Without a breaker, the slow service gets slower.

### Wrong attempt 2: OPEN forever after first failure
Threshold=1 trips on transient blip. Use 5/10s window default.

### Wrong attempt 3: full traffic in HALF_OPEN
Thundering herd hits the recovering service. Bound probes (default 1).

---

## 7. The unlocking insight

> **Three-state machine + sliding-window failure count + cooldown timer + bounded HALF_OPEN probes. Per-downstream key. `isFailure` injectable so 4xx don't trip.**

Three properties:

1. **CLOSED tallies, OPEN rejects, HALF_OPEN probes.**
2. **Sliding window** of failure timestamps within `windowMs`.
3. **Bounded probe count** prevents thundering herd on recovery.

---

## 8. Solution (annotated)

```js
class CircuitBreaker {
  constructor(opts = {}) {
    this.threshold   = opts.threshold   ?? 5;
    this.windowMs    = opts.windowMs    ?? 10_000;
    this.cooldownMs  = opts.cooldownMs  ?? 30_000;
    this.halfOpenMax = opts.halfOpenMax ?? 1;
    this.isFailure   = opts.isFailure   ?? (() => true);
    this.state = 'CLOSED';
    this.failures = [];
    this.openedAt = 0;
    this.halfOpenInFlight = 0;
  }

  _gate() {                                                          // step 1: state check
    if (this.state === 'OPEN') {
      if (Date.now() - this.openedAt >= this.cooldownMs) {
        this.state = 'HALF_OPEN';
        this.halfOpenInFlight = 0;                                    // promote to HALF_OPEN
      } else {
        const err = new Error('CircuitOpen'); err.code = 'CIRCUIT_OPEN'; throw err;
      }
    }
    if (this.state === 'HALF_OPEN' && this.halfOpenInFlight >= this.halfOpenMax) {
      const err = new Error('CircuitHalfOpenSaturated'); err.code = 'CIRCUIT_SATURATED'; throw err;
    }
  }

  async exec(fn) {
    this._gate();
    const wasHalfOpen = this.state === 'HALF_OPEN';
    if (wasHalfOpen) this.halfOpenInFlight++;
    try {
      const r = await fn();
      this._onSuccess();                                              // step 2: success
      return r;
    } catch (err) {
      if (this.isFailure(err)) this._onFailure();                     // step 3: count failure
      throw err;
    } finally {
      if (wasHalfOpen) this.halfOpenInFlight--;
    }
  }

  _onSuccess() {
    if (this.state === 'HALF_OPEN') { this.state = 'CLOSED'; this.failures = []; }
  }

  _onFailure() {
    const t = Date.now();
    if (this.state === 'HALF_OPEN') { this.state = 'OPEN'; this.openedAt = t; return; }
    this.failures = this.failures.filter((x) => t - x < this.windowMs);  // sliding window
    this.failures.push(t);
    if (this.failures.length >= this.threshold) { this.state = 'OPEN'; this.openedAt = t; }
  }

  reset() { this.state = 'CLOSED'; this.failures = []; this.halfOpenInFlight = 0; }
  get snapshot() { return { state: this.state, failures: this.failures.length, openedAt: this.openedAt }; }
}
```

**Try it yourself**

```js
const cb = new CircuitBreaker({
  threshold: 3, windowMs: 10_000, cooldownMs: 5_000,
  isFailure: (e) => /5\d\d|ETIMEDOUT|ECONNRESET/.test(e.message),    // don't trip on 4xx
});

try {
  const data = await cb.exec(() => fetch('https://api.example.com').then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  }));
} catch (e) {
  if (e.code === 'CIRCUIT_OPEN') console.log('Failing fast — service is down');
  else throw e;
}
```

---

## 9. Step-by-step dry run

```
threshold=3, windowMs=10s, cooldownMs=5s, halfOpenMax=1

t=0  exec(f) → CLOSED. f fails. failures=[0]. state=CLOSED.
t=1  exec(f) → CLOSED. f fails. failures=[0,1].
t=2  exec(f) → CLOSED. f fails. failures=[0,1,2]. >=3 → state=OPEN, openedAt=2.

t=3  exec(f) → _gate: OPEN, now-openedAt=1 < 5 → THROW CircuitOpen (no f call).
t=4  exec(f) → same → THROW.

t=8  exec(f) → _gate: OPEN, now-openedAt=6 >= 5 → state=HALF_OPEN, inflight=0.
              halfOpenInFlight=1. exec f.
              f SUCCEEDS → _onSuccess → state=CLOSED, failures=[].
              halfOpenInFlight-- = 0.

t=9  exec(f) → CLOSED. passes through.

If f had FAILED at t=8:
  _onFailure → HALF_OPEN → state=OPEN, openedAt=8. Full 5s cooldown again.
```

---

## 10. Common confusion + traps

1. **Per-downstream breaker, not global** — sharing flips unrelated calls.
2. **Trip on 4xx** — caller bug, not server failure. Inject `isFailure`.
3. **No probe bound** — thundering herd on recovery.
4. **HALF_OPEN failure → CLOSED** — wrong. Must re-OPEN with fresh cooldown.
5. **Retry without breaker** — amplifies load on slow downstream. Always pair.
6. **Threshold=1** — single transient blip trips. 5/10s sane default.
7. **Forget to reset `failures` on CLOSE** — stale counts trip again on next failure.

---

## 11. Senior follow-ups & variants

### Variant 1 — Rolling-window buckets
Count failures per 1s bucket, sum last N. Better resolution. (resilience4j default.)

### Variant 2 — Error rate, not count
Trip on >50% failures over last 100 calls. Fair under variable traffic.

### Variant 3 — Bulkhead + breaker
Separate connection pools per downstream — one slow dep can't starve another.

### Variant 4 — Distributed circuit breaker
Share state via Redis so all app instances trip together. Adds latency.

### Variant 5 — Fallback on OPEN
Combine with cached/stale-while-revalidate. On OPEN, return last-known-good or degraded UX.

---

## 12. How to think aloud

> "Three states: CLOSED tallies failures in a sliding window; threshold hit → OPEN. OPEN short-circuits; after cooldown → HALF_OPEN. HALF_OPEN allows N probes — success closes, failure re-opens with fresh cooldown. Per-downstream breaker, not global. Inject `isFailure` so 4xx don't trip me. Expose `snapshot.state` as a metric; page on `state=OPEN`. Pair with retry (inside breaker for transient blips) and bulkhead (separate pools per dep). Trap: trip on 4xx; threshold too low; HALF_OPEN unbounded; missing per-key isolation."

---

## 13. 60-second revision

> - **Three states:** CLOSED (tally) → OPEN (reject) → HALF_OPEN (probe).
> - **Sliding window** of failures within `windowMs`.
> - **Bounded probes** in HALF_OPEN (default 1).
> - **`isFailure`** injectable — don't trip on 4xx.
> - **Per-downstream** key, never global.
> - **HALF_OPEN failure → re-OPEN** (fresh cooldown).
> - **Page on OPEN**; expose `reset()` for ops.
> - **Family:** retry + jitter (inside), bulkhead (alongside), distributed (Redis).
> - **Trap:** global breaker; 4xx trip; HALF_OPEN unbounded; missing isFailure injection.

---

**Related:** [mini-state-machine.md](./mini-state-machine.md) · [retry-with-jitter-and-budget.md](./retry-with-jitter-and-budget.md) · [idempotency-wrapper.md](./idempotency-wrapper.md) · [async-semaphore.md](./async-semaphore.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
