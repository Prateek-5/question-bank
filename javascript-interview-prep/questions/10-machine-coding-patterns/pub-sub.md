# Implement a Pub/Sub (Observer pattern)

## Source
- Canonical machine-coding / design-patterns interview problem (Gang of Four "Observer", Node.js EventEmitter, RxJS Subject, Redis pub/sub).
- Reference: GoF Design Patterns, RxJS `Subject` source.

## Why this question matters in interviews
Pub/Sub is the **conceptual sibling** of EventEmitter (see event-emitter.md), but interviewers ask it for a different reason: it tests whether you understand **decoupled communication**, **topic-based dispatch**, and the **unsubscribe-handle pattern**. As a backend engineer you've used pub/sub everywhere: Redis pub/sub, RabbitMQ topics, Kafka consumer groups, GraphQL subscriptions, internal event buses in modular monoliths. The interview implementation is small but the design choices are senior-level: **does `subscribe` return an unsubscribe handle (cleaner) or an ID (older)?**, **how do you support wildcards (`user.*`)?**, **is dispatch sync or async?**. A senior answer states the choices upfront and implements the clean version.

## Concepts involved

### Syntax to lock in
```js
const pubsub = new PubSub();

const unsub = pubsub.subscribe('user:login', (payload) => console.log(payload));
pubsub.publish('user:login', { id: 1 });   // logs { id: 1 }
unsub();
pubsub.publish('user:login', { id: 1 });   // nothing — unsubscribed
```

Internal shape:
```js
class PubSub {
  constructor() { this.subscribers = new Map(); /* Map<topic, Set<fn>> */ }
}
```

### Runtime / engine behavior
- Topic strings are the routing key. Some implementations support **namespacing** (`user.profile.update`) and **wildcards** (`user.*`, `user.**`).
- `Map<topic, Set<fn>>` is the textbook shape — same as EventEmitter — but pub/sub usually has additional features like wildcards, async dispatch, and last-value caching.
- Returning an **unsubscribe function** from `subscribe` is the idiomatic modern API. Beats ID-based `unsubscribe(id)` because the handle closes over the right set + fn, no lookup needed.
- Dispatch can be sync (cheap, deterministic order) or async (`queueMicrotask` / `setImmediate`) (callers don't block; harder to reason about). State which.

### Edge cases (these are the interview traps)
1. **Pub/Sub vs EventEmitter** — practically the same data structure. Conceptually: EventEmitter is OO (instance has events of itself), Pub/Sub is a **global bus** (topics are decoupled from objects). Interviewers use the terms interchangeably; ask which they mean.
2. **Wildcards** — `subscribe('user.*', fn)` should fire on `'user.login'`, `'user.logout'`, but not `'user.profile.update'`. `**` is "any depth." Implement separately from exact-match subscribers.
3. **Unsubscribe during dispatch** — if a callback unsubscribes itself or others mid-publish, the iteration must not break. **Snapshot subscribers** before iterating (same as EventEmitter).
4. **Same fn subscribed twice** — Set: stored once. Array: twice. Choose Set unless interviewer wants duplicates.
5. **Memory leaks** — subscribers retained by closures forever if `unsubscribe` is never called. The single most common pub/sub bug in long-running services. Always pair with lifecycle teardown.
6. **Publishing with no subscribers** — must be no-op, never throw.
7. **Last-value cache (Subject behavior)** — RxJS `BehaviorSubject` replays the last published value to new subscribers. Worth implementing as a variant.
8. **Cross-topic broadcasting** — `publish('*', payload)` to all subscribers regardless of topic. Avoid; usually a code smell.

## Brute force approach
Plain object keyed by topic. Same plain-object prototype-pollution risk. Skip; use Map.

## Optimal approach
`Map<topic, Set<fn>>` for exact-match subscribers. `subscribe` returns an `unsubscribe` function that closes over the set + fn. `publish` snapshots and iterates.

For wildcards, maintain a separate list of `{pattern, fn}` and match patterns on publish — O(P) overhead where P = pattern count. Compile patterns to regexes once for speed.

## Solution (JavaScript)

```js
/**
 * Topic-keyed Pub/Sub with sync dispatch and unsubscribe-handle pattern.
 */
class PubSub {
  constructor() {
    /** @type {Map<string, Set<Function>>} */
    this.subscribers = new Map();
    /** @type {Array<{ pattern: RegExp, fn: Function }>} */
    this.patternSubs = [];
  }

  /**
   * Subscribe to a topic.
   * Pattern subs: 'user.*' (single segment) or 'user.**' (any depth).
   * @returns {() => void} unsubscribe function
   */
  subscribe(topic, fn) {
    if (topic.includes('*')) {
      const pattern = this._compilePattern(topic);
      const entry = { pattern, fn };
      this.patternSubs.push(entry);
      return () => {
        this.patternSubs = this.patternSubs.filter((e) => e !== entry);
      };
    }

    if (!this.subscribers.has(topic)) this.subscribers.set(topic, new Set());
    const set = this.subscribers.get(topic);
    set.add(fn);
    return () => {
      set.delete(fn);
      if (set.size === 0) this.subscribers.delete(topic);
    };
  }

  /**
   * Publish a payload to a topic. Sync dispatch. Returns nothing.
   */
  publish(topic, payload) {
    const exact = this.subscribers.get(topic);
    const listeners = exact ? [...exact] : [];   // snapshot
    for (const fn of listeners) {
      try { fn(payload, topic); } catch (e) { /* isolate; pub/sub typically swallows */ }
    }
    // Wildcard dispatch
    for (const { pattern, fn } of [...this.patternSubs]) {
      if (pattern.test(topic)) {
        try { fn(payload, topic); } catch (e) {}
      }
    }
  }

  /**
   * Remove ALL subscribers for a topic (or globally if topic is omitted).
   */
  clear(topic) {
    if (topic === undefined) {
      this.subscribers.clear();
      this.patternSubs = [];
    } else {
      this.subscribers.delete(topic);
    }
  }

  _compilePattern(topic) {
    // 'user.**' → '^user\.(.+)$';  'user.*' → '^user\.([^.]+)$'
    const escaped = topic
      .split('.')
      .map((seg) => seg === '**' ? '.+' : seg === '*' ? '[^.]+' : seg.replace(/[.+?^${}()|[\]\\]/g, '\\$&'))
      .join('\\.');
    return new RegExp(`^${escaped}$`);
  }
}
```

## Step-by-step dry run

Input:
```js
const bus = new PubSub();

const u1 = bus.subscribe('user.login',    (p) => console.log('exact:', p));
const u2 = bus.subscribe('user.*',        (p, t) => console.log('wild:', t, p));
const u3 = bus.subscribe('user.**',       (p, t) => console.log('deep:', t, p));

bus.publish('user.login', { id: 1 });
bus.publish('user.profile.update', { id: 1, name: 'P' });
u1();
bus.publish('user.login', { id: 2 });
```

Trace:

- After 3 subscribes:
  - `subscribers = { 'user.login' → Set{ exactFn } }`
  - `patternSubs = [{ /^user\.[^.]+$/, wildFn }, { /^user\..+$/, deepFn }]`

- `publish('user.login', {id:1})`:
  - Exact: `[exactFn]` snapshot. Call → `exact: {id:1}`.
  - Patterns: `/^user\.[^.]+$/` matches → `wild: user.login {id:1}`. `/^user\..+$/` matches → `deep: user.login {id:1}`.
  - Output:
    ```
    exact: {id:1}
    wild: user.login {id:1}
    deep: user.login {id:1}
    ```

- `publish('user.profile.update', {id:1, name:'P'})`:
  - Exact: no `'user.profile.update'` topic → empty snapshot.
  - Patterns: `/^user\.[^.]+$/` → `user.profile.update` has two dots after user, segment `[^.]+` won't match → **no match**. `/^user\..+$/` → matches.
  - Output:
    ```
    deep: user.profile.update {id:1, name:'P'}
    ```

- `u1()` — unsubscribes `exactFn`. Now `subscribers.get('user.login')` is empty → topic is deleted.

- `publish('user.login', {id:2})`:
  - No exact subscribers.
  - Both wildcard patterns still match `user.login`.
  - Output:
    ```
    wild: user.login {id:2}
    deep: user.login {id:2}
    ```

Note how single-star and double-star differ on depth. `*` = exactly one segment. `**` = one or more.

## Important takeaways

**Pub/Sub vs EventEmitter**
- **Data structure**: identical (`Map<topic/event, Set<fn>>`).
- **Mental model**: EventEmitter is an object emitting its own events. Pub/Sub is a **global bus** decoupled from any source object.
- **Typical features**: Pub/Sub more often adds wildcards, last-value caching (BehaviorSubject), async dispatch. EventEmitter is usually plainer.

**Syntax to memorize**
- `Map<topic, Set<fn>>` + separate list for pattern subs.
- `subscribe(topic, fn)` returns an **unsubscribe function** (closes over set + fn). Always prefer this over ID-based unsubscribe.
- `publish(topic, payload)` snapshots subscribers before iterating.

**Patterns to reuse**
- Unsubscribe-handle: identical to `useEffect` cleanup, RxJS `Subscription`, DOM `AbortSignal`. Universal modern pattern.
- Map-of-Set: shows up in EventEmitter, room-based websockets, topic-based broker.
- Wildcard matching via compiled regex: used by router libraries (Express, Koa-route), MQTT brokers, Redis pub/sub.

**Common mistakes**
- ID-based unsubscribe (`const id = sub.subscribe(...); sub.unsubscribe(id)`) — outdated, ergonomic loss, no real upside.
- Iterating subscribers without snapshotting → subscribe-during-publish causes inconsistent fan-out.
- Letting one bad subscriber's exception kill the publish loop — wrap each call in try/catch (pub/sub typically isolates).
- Forgetting to clean up empty topic sets → growing Map of empty Sets.
- Implementing wildcards by linear scan of all topic names every publish — O(N*P). Compile patterns to regex once, match each pub against P patterns instead.

**Related questions**
- EventEmitter — see event-emitter.md. Same DS, slightly different framing.
- Redis pub/sub — distributed equivalent; topic-fanned, sync semantics, no persistence.
- Kafka consumer groups — persistent log + ordered consumption + replay. Different beast.
- RxJS `Subject` / `BehaviorSubject` / `ReplaySubject` — superset of pub/sub with operators.
- GraphQL subscriptions — pub/sub over WebSocket.

## Variants

1. **Wildcard topics** — `'user.*'` (one segment) and `'user.**'` (any depth). Shown above.

2. **Async dispatch** — `queueMicrotask(() => fn(payload))` so publish never blocks. Useful in hot paths but reorders semantics; state clearly.

3. **Last-value cache (BehaviorSubject)** — `publish` stashes the last value per topic; new subscribers immediately receive the cached value.

4. **Replay buffer (ReplaySubject)** — buffer last N values per topic; new subscribers get the buffer on subscribe.

5. **Filtered subscribe** — `subscribe(topic, fn, { filter: p => p.userId === me })`. Lets one subscriber receive only events it cares about.

6. **Distributed pub/sub** — Redis `PUBLISH` / `SUBSCRIBE`, NATS, RabbitMQ topics. System-design follow-up: how do you handle delivery guarantees? (Redis: at-most-once; Kafka: at-least-once with offsets.)

## Revision notes

> **Pub/Sub — 60 second recap**
> - `Map<topic, Set<fn>>` for exact match + list of `{pattern, fn}` for wildcards.
> - `subscribe(topic, fn)` returns an **unsubscribe function**, not an ID.
> - `publish(topic, payload)`: snapshot exact subs, iterate; then iterate patterns, regex-test each.
> - Sync dispatch by default; async (queueMicrotask) as variant.
> - vs EventEmitter: same DS, conceptually a global bus.
> - **Trap:** ID-based unsubscribe — outdated; always return a handle.
> - **Trap 2:** no snapshot before iteration → subscribe-during-publish bugs.
> - Family: RxJS Subject (BehaviorSubject, ReplaySubject), Redis pub/sub, Kafka.
