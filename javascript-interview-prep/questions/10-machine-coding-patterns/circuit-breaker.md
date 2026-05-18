# Circuit Breaker

## Source / Origin
- Pattern named by Michael Nygard in "Release It!" (2007).
- Netflix Hystrix popularized it; modern equivalents: resilience4j (Java), opossum (Node), polly (.NET).
- Asked at: Razorpay, Stripe, Uber, Atlassian — anywhere outbound calls to flaky deps exist.
- Concept reference: backend `interview-scenarios/02-debugging-scenarios.md` (cascading failure section).

## Why this question matters in interviews
Cascading failure is the canonical distributed-systems incident. Service A calls service B. B slows from 50ms to 5s. A's threads block waiting for B. A's queue fills. A starts timing out. Now A's callers see latency. Eventually the whole graph melts. The circuit breaker is the protocol that says "stop calling B for 30 seconds; let it recover." Senior interviewers expect you to know *why* it exists (fail fast under partial failure), the three-state machine (CLOSED → OPEN → HALF_OPEN), and the knobs (threshold, window, timeout, half-open probe count).

## Concepts involved

### Syntax to lock in
```js
class CircuitBreaker {
  constructor({ threshold = 5, windowMs = 10_000, cooldownMs = 30_000, halfOpenMax = 1 } = {}) {
    this.threshold = threshold;
    this.windowMs = windowMs;
    this.cooldownMs = cooldownMs;
    this.halfOpenMax = halfOpenMax;
    this.state = 'CLOSED';
    this.failures = [];           // timestamps of recent failures
    this.openedAt = 0;
    this.halfOpenInFlight = 0;
  }

  async exec(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.openedAt >= this.cooldownMs) this.state = 'HALF_OPEN';
      else throw new Error('CircuitOpen');
    }
    if (this.state === 'HALF_OPEN' && this.halfOpenInFlight >= this.halfOpenMax) {
      throw new Error('CircuitHalfOpenSaturated');
    }
    if (this.state === 'HALF_OPEN') this.halfOpenInFlight++;
    try {
      const r = await fn();
      this.onSuccess();
      return r;
    } catch (e) {
      this.onFailure();
      throw e;
    } finally {
      if (this.state === 'HALF_OPEN') this.halfOpenInFlight = Math.max(0, this.halfOpenInFlight - 1);
    }
  }

  onSuccess() {
    if (this.state === 'HALF_OPEN') { this.state = 'CLOSED'; this.failures = []; }
  }

  onFailure() {
    const now = Date.now();
    this.failures.push(now);
    this.failures = this.failures.filter(t => now - t < this.windowMs);
    if (this.state === 'HALF_OPEN') { this.state = 'OPEN'; this.openedAt = now; return; }
    if (this.failures.length >= this.threshold) { this.state = 'OPEN'; this.openedAt = now; }
  }
}
```

### Edge cases / interview traps
1. **All exceptions count, or only some?** Production: don't trip on `4xx` (caller bug); trip on `5xx`/timeout. Make `isFailure(err)` injectable.
2. **Time-based vs count-based window.** Count of last-N is simpler; sliding-time window is fairer (resilience4j default).
3. **HALF_OPEN concurrency.** Only `halfOpenMax` requests allowed; the rest are short-circuited. Otherwise a thundering herd on the recovering service.
4. **HALF_OPEN failure → re-OPEN, not CLOSED.** Subtle. Reset `openedAt` to now.
5. **Clock skew & monotonic time.** Use `performance.now()` if your scheduler matters; `Date.now()` is fine for human-scale cooldowns.
6. **Per-key breakers.** One breaker per downstream — never share between `userService` and `paymentService`.
7. **Falling-back vs failing-fast.** Some breakers offer `fallback(fn)`; that's an *additional* concern (bulkhead/fallback), not the breaker itself.
8. **Manual reset for ops.** Expose `reset()` so on-call can force-close after fixing the downstream.

## Mental Model

A circuit breaker is the **electrical fuse for service calls**.

```
                ┌──────────┐  failures < threshold  ┌──────────┐
   normal ──▶   │  CLOSED  │ ─────────────────────▶ │  CLOSED  │
   traffic      └────┬─────┘                        └──────────┘
                     │ failures >= threshold
                     ▼
                ┌──────────┐  cooldown elapsed   ┌────────────┐
                │   OPEN   │ ──────────────────▶ │ HALF_OPEN  │
                │ (reject) │                     │ (probe N)  │
                └──────────┘                     └─────┬──────┘
                     ▲                                 │
                     │ probe fails                     │ probes ok
                     └─────────────────────────────────┘
                                                       │
                                                       ▼
                                                  back to CLOSED
```

**CLOSED**: pass through; tally failures in a sliding window.
**OPEN**: short-circuit; throw immediately so callers can fall back fast.
**HALF_OPEN**: a few probes through; success → CLOSED, failure → OPEN with fresh cooldown.

## Why interviewers care

- **Failure isolation literacy** — you don't melt the system when one dep slows.
- **State-machine discipline** — three states, two timers (window + cooldown), bounded probe count.
- **Operations awareness** — manual reset, per-key keys, what to alert on (`state=OPEN` is a page).

## Common beginner confusion

- **"Just retry on failure."** Retries amplify load; without a breaker, retries on a slow downstream make it slower. Always pair retry with breaker.
- **"OPEN means broken — never close again."** Wrong. After cooldown, probe HALF_OPEN.
- **"HALF_OPEN allows full traffic."** No — *bounded* probes. A single probe is common.
- **"Set threshold=1 for safety."** Then a single transient blip trips you. 5/10s window is a sane default.
- **"Same breaker for all calls."** No. Per-downstream keying; otherwise B's failure flips A's calls open.

## Brute force approach

```js
// no breaker — every call hits the downstream
try { return await call(); } catch (e) { return fallback; }
```

Cascading failure happens because all callers keep hammering the slow service.

## Optimal approach

A three-state breaker with sliding-window failure counting, cooldown timer, and bounded probes in HALF_OPEN. Inject `isFailure(err)` to distinguish caller errors from server errors.

## Solution (JavaScript) — production-shape

```js
class CircuitBreaker {
  constructor(opts = {}) {
    this.threshold   = opts.threshold   ?? 5;
    this.windowMs    = opts.windowMs    ?? 10_000;
    this.cooldownMs  = opts.cooldownMs  ?? 30_000;
    this.halfOpenMax = opts.halfOpenMax ?? 1;
    this.isFailure   = opts.isFailure   ?? ((err) => true);
    this.state = 'CLOSED'; this.failures = []; this.openedAt = 0; this.halfOpenInFlight = 0;
  }
  _now() { return Date.now(); }
  _gate() {
    if (this.state === 'OPEN') {
      if (this._now() - this.openedAt >= this.cooldownMs) {
        this.state = 'HALF_OPEN'; this.halfOpenInFlight = 0;
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
      this._onSuccess();
      return r;
    } catch (err) {
      if (this.isFailure(err)) this._onFailure();
      throw err;
    } finally {
      if (wasHalfOpen) this.halfOpenInFlight--;
    }
  }
  _onSuccess() { if (this.state === 'HALF_OPEN') { this.state = 'CLOSED'; this.failures = []; } }
  _onFailure() {
    const t = this._now();
    if (this.state === 'HALF_OPEN') { this.state = 'OPEN'; this.openedAt = t; return; }
    this.failures = this.failures.filter(x => t - x < this.windowMs);
    this.failures.push(t);
    if (this.failures.length >= this.threshold) { this.state = 'OPEN'; this.openedAt = t; }
  }
  reset() { this.state = 'CLOSED'; this.failures = []; this.halfOpenInFlight = 0; }
  get snapshot() { return { state: this.state, failures: this.failures.length, openedAt: this.openedAt }; }
}
```

## Step-by-step dry run

`threshold=3, windowMs=10s, cooldownMs=5s, halfOpenMax=1`. Calls f1..f5 all fail; cooldown elapses; probe succeeds.

```
t=0   f1 fail → failures=[0], state=CLOSED
t=1   f2 fail → failures=[0,1]
t=2   f3 fail → failures=[0,1,2] → threshold hit → state=OPEN, openedAt=2
t=3   f4 → _gate sees OPEN, cooldown not elapsed → throw CircuitOpen (no downstream call)
t=4   f5 → throw CircuitOpen
t=8   f6 → _gate sees OPEN, cooldown elapsed (8-2=6 ≥ 5) → state=HALF_OPEN, inflight=1
       call succeeds → _onSuccess → state=CLOSED, failures=[]
t=9   f7 → CLOSED, passes through → success
```

If `f6` had failed: state→OPEN, openedAt=8, full cooldown again before next probe.

## How to think aloud in the interview

> "Three states: CLOSED tallies failures in a sliding window. Threshold trips to OPEN. OPEN short-circuits and starts a cooldown. After cooldown, the next call promotes to HALF_OPEN; we allow up to N probes — success closes, failure re-opens. The breaker is per-downstream, not global. I'd inject `isFailure(err)` so 4xx don't trip me. I'd expose `state` as a metric and page on `state=OPEN`."

## Important takeaways

- **Per-downstream** breakers, never shared.
- **isFailure(err)** is injectable — 4xx vs 5xx vs timeout matter.
- **HALF_OPEN is bounded** — single probe is the safe default.
- **Pair with retry** — retry inside the breaker for transient blips; the breaker contains amplification.
- **Observable**: emit state changes; alert on OPEN.

## Variants

- **Rolling window with buckets** (resilience4j) — count failures per 1s bucket, sum last N buckets. Better resolution.
- **Error rate, not count** — trip on >50% failures over last 100 calls. More fair under variable traffic.
- **Bulkhead + breaker** — separate thread/connection pools per downstream so one slow dep can't starve another.
- **Distributed circuit breaker** — share state via Redis so all app instances trip together. Adds latency; uncommon.

## Revision notes

```
CircuitBreaker(threshold, windowMs, cooldownMs, halfOpenMax):
  CLOSED → tally fails in window; threshold hit → OPEN
  OPEN → reject; after cooldown, allow HALF_OPEN
  HALF_OPEN → bounded probes; success → CLOSED, fail → OPEN
  per-downstream key
  inject isFailure (don't trip on 4xx)
  reset() for ops
  pair with retry+jitter
  page on state=OPEN
```
