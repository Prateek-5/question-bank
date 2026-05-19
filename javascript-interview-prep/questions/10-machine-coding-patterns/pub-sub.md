# Implement a Pub/Sub bus with wildcards

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [event-emitter.md](./event-emitter.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** GoF Observer, RxJS `Subject`, Redis pub/sub, MQTT topic broker.

---

## 1. Problem statement

**Signature**
```ts
class PubSub {
  subscribe(topic: string, fn: (payload: any, topic: string) => void): () => void;
  publish(topic: string, payload: any): void;
  clear(topic?: string): void;
}
```

**Input / Output examples**

| Setup                                                                 | Behaviour                                            |
|-----------------------------------------------------------------------|------------------------------------------------------|
| `subscribe('user.login', fn); publish('user.login', x)`               | fn fires with `x`                                    |
| `subscribe('user.*', fn); publish('user.login', x)`                   | fn fires (wildcard, one segment)                     |
| `subscribe('user.**', fn); publish('user.profile.update', x)`         | fn fires (deep wildcard)                             |
| `subscribe('user.*', fn); publish('user.profile.update', x)`          | fn does NOT fire (one-segment limit)                 |
| `unsub = subscribe(...); unsub()`                                     | removes fn                                           |
| `publish('unknown', x)`                                               | no error, no-op                                      |

**Constraints**
- `Map<topic, Set<fn>>` for exact match; separate list for wildcard patterns.
- `subscribe` returns an unsubscribe function (closes over set + fn).
- `publish` snapshots subscribers before iterating.
- `*` = exactly one segment; `**` = one or more.

---

## 2. Plain-English restatement

A topic-string-keyed event bus. Anyone can subscribe to a topic (literal or wildcard pattern) and receive payloads published to matching topics. Decoupled from any source object — publishers and subscribers don't know each other. Used for Redis pub/sub, RabbitMQ topics, MQTT, GraphQL subscriptions, internal monorepo buses.

---

## 3. Why this matters in interviews

Pub/Sub is the **conceptual sibling** of EventEmitter, but interviewers ask it for a different reason: it tests whether you understand **decoupled communication**, **topic-based dispatch**, and the **unsubscribe-handle pattern**. Senior bonus: wildcards (`*` and `**`), async dispatch, last-value cache (BehaviorSubject), distributed-pub/sub trade-offs.

---

## 4. Mental model

```
   ┌────────────────────────────────────────────────┐
   │ subscribers: Map<topic, Set<fn>>              │
   ├────────────────────────────────────────────────┤
   │ 'user.login'  → { fnA, fnB }                  │
   │ 'order.done'  → { fnC }                        │
   └────────────────────────────────────────────────┘

   ┌────────────────────────────────────────────────┐
   │ patternSubs: [{ pattern: RegExp, fn }]         │
   ├────────────────────────────────────────────────┤
   │ /^user\.[^.]+$/   → wildFn   (single segment)  │
   │ /^user\..+$/      → deepFn   (any depth)       │
   └────────────────────────────────────────────────┘

   publish('user.login', payload):
     exact: snapshot Set{fnA, fnB} → fire both
     patterns: regex.test('user.login') → fire matches
```

**`*` vs `**`:**
- `user.*` matches `user.login`, `user.logout` — **exactly one segment after `user`**.
- `user.**` matches `user.login`, `user.profile.update`, `user.x.y.z` — **one or more segments**.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `subscribe('user.*', fn)`, does `publish('user.profile.update', x)` fire `fn`?
> 2. If three subscribers exist and one unsubscribes itself during publish, do the other two still fire?
> 3. Why return an unsubscribe function instead of an ID + `unsubscribe(id)`?

---

## 6. Brute force — walked through

### Wrong attempt 1: plain object registry
Proto pollution / collisions on keys like `'toString'`. Use `Map`.

### Wrong attempt 2: linear scan all topic names on publish
On every `publish`, walk every key in `subscribers` to find matches. O(N) per publish where N = unique topics. Use exact-match Map + separate pattern list instead — O(1) + O(P).

### Wrong attempt 3: no snapshot in publish
If a subscriber subscribes/unsubscribes during dispatch, iteration breaks or fires unexpected handlers. Always `[...set]` first.

---

## 7. The unlocking insight

> **Two structures: `Map<topic, Set<fn>>` for exact match, `Array<{pattern, fn}>` for wildcards. Compile patterns to regex once. `subscribe` returns a closure that captures set+fn. `publish` snapshots, iterates exact subs, then regex-tests patterns.**

Three properties:

1. **Two-tier registry** — Map for O(1) exact match, list for O(P) wildcard.
2. **Pre-compiled regex** — pattern compiled once at subscribe time, not per publish.
3. **Snapshot-before-iterate** — concurrent-modification safety.

---

## 8. Solution (annotated)

```js
class PubSub {
  constructor() {
    this.subscribers = new Map();                                // step 1: exact match
    this.patternSubs = [];                                        // step 2: wildcard entries
  }

  subscribe(topic, fn) {
    if (topic.includes('*')) {                                    // step 3: pattern branch
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
    return () => {                                                // step 4: unsubscribe handle
      set.delete(fn);
      if (set.size === 0) this.subscribers.delete(topic);
    };
  }

  publish(topic, payload) {
    const exact = this.subscribers.get(topic);
    const listeners = exact ? [...exact] : [];                    // step 5: snapshot
    for (const fn of listeners) {
      try { fn(payload, topic); } catch {}
    }
    for (const { pattern, fn } of [...this.patternSubs]) {        // step 6: wildcard fan-out
      if (pattern.test(topic)) {
        try { fn(payload, topic); } catch {}
      }
    }
  }

  clear(topic) {
    if (topic === undefined) {
      this.subscribers.clear();
      this.patternSubs = [];
    } else {
      this.subscribers.delete(topic);
    }
  }

  _compilePattern(topic) {                                        // 'user.*' → /^user\.[^.]+$/
    const escaped = topic
      .split('.')
      .map((seg) =>
        seg === '**' ? '.+' :
        seg === '*'  ? '[^.]+' :
        seg.replace(/[.+?^${}()|[\]\\]/g, '\\$&'),
      )
      .join('\\.');
    return new RegExp(`^${escaped}$`);
  }
}
```

**Try it yourself**

```js
const bus = new PubSub();
const u1 = bus.subscribe('user.login',  (p)    => console.log('exact:', p));
const u2 = bus.subscribe('user.*',      (p, t) => console.log('wild:',  t, p));
const u3 = bus.subscribe('user.**',     (p, t) => console.log('deep:',  t, p));

bus.publish('user.login', { id: 1 });
// exact: { id: 1 } / wild: user.login { id: 1 } / deep: user.login { id: 1 }

bus.publish('user.profile.update', { id: 1 });
// deep: user.profile.update { id: 1 }   ← only ** matches

u1();
bus.publish('user.login', { id: 2 });
// wild: user.login { id: 2 } / deep: user.login { id: 2 }
```

---

## 9. Step-by-step dry run

```
Setup:
  subscribers = { 'user.login' → Set{exactFn} }
  patternSubs = [
    { /^user\.[^.]+$/, wildFn },
    { /^user\..+$/,    deepFn }
  ]

publish('user.login', {id:1}):
  exact = subscribers.get('user.login') = Set{exactFn}
  snapshot listeners = [exactFn]
  fire: exactFn({id:1}, 'user.login') → log 'exact: {id:1}'
  for each pattern entry:
    /^user\.[^.]+$/.test('user.login') → true → wildFn → log 'wild: user.login {id:1}'
    /^user\..+$/.test('user.login')    → true → deepFn → log 'deep: user.login {id:1}'

publish('user.profile.update', {id:1, name:'P'}):
  exact = subscribers.get('user.profile.update') = undefined → []
  patterns:
    /^user\.[^.]+$/.test('user.profile.update') → false ([^.]+ won't match 'profile.update')
    /^user\..+$/.test('user.profile.update')    → true → deepFn fires

u1():
  set.delete(exactFn) → set = {}
  size === 0 → subscribers.delete('user.login')

publish('user.login', {id:2}):
  exact = undefined → []
  patterns still match → wildFn and deepFn fire
```

---

## 10. Common confusion + traps

1. **ID-based unsubscribe** — outdated; the handle pattern is cleaner.
2. **No snapshot in publish** — subscribe-during-publish bugs.
3. **Plain object registry** — proto pollution.
4. **Walking all topic names** for wildcard matching — O(N) per publish. Use separate pattern list with pre-compiled regex.
5. **Letting one bad subscriber kill publish** — wrap each call in try/catch (pub/sub usually isolates failures).
6. **Forgetting to drop empty topic Sets** — Map grows monotonically.
7. **`*` vs `**` confusion** — clarify single-segment vs any-depth.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async dispatch
`queueMicrotask(() => fn(payload, topic))`. Publish never blocks; ordering shifts to microtask scheduling.

### Variant 2 — BehaviorSubject (last-value cache)
Stash last published value per topic; new subscribers receive it immediately on subscribe.

### Variant 3 — ReplaySubject(n)
Buffer last `n` values per topic; replay buffer on subscribe.

### Variant 4 — Filtered subscribe
`subscribe(topic, fn, { filter: p => p.userId === me })` — subscriber-side predicate.

### Variant 5 — Distributed pub/sub
Redis `PUBLISH/SUBSCRIBE` (at-most-once); Kafka consumer groups (at-least-once + replay); NATS. Bring up delivery-guarantee trade-offs.

---

## 12. How to think aloud

> "`Map<topic, Set<fn>>` for exact match, plus a separate array for wildcard patterns (compiled to regex once). `subscribe` returns an unsubscribe function — closes over set+fn, much cleaner than ID-based. `publish` snapshots subscribers before iterating to survive in-handler mutation. Wildcards: `*` = one segment, `**` = any depth. EventEmitter and Pub/Sub have the same data structure; the conceptual difference is that EventEmitter is an object emitting its own events, while Pub/Sub is a decoupled global bus. Trap: ID-based unsubscribe. Trap: no snapshot. Trap: linear scan over all topic names for wildcard matching — use the separate pattern list with regex pre-compilation."

---

## 13. 60-second revision

> - **`Map<topic, Set<fn>>` + `Array<{pattern, fn}>`**.
> - **`subscribe` returns unsubscribe handle** (closure over set+fn).
> - **`publish` snapshots** subs, fires exact, then regex-tests patterns.
> - **`*`** = one segment; **`**`** = any depth.
> - **Drop empty topic Sets** to avoid Map growth.
> - **Family:** EventEmitter, Subject (BehaviorSubject, ReplaySubject), Redis/Kafka.
> - **Trap:** ID-based unsubscribe; no snapshot; linear scan for wildcards.

---

**Related:** [event-emitter.md](./event-emitter.md) · [observable-subject.md](./observable-subject.md) · [`04-promises/abortcontroller-fanout.md`](../04-promises/abortcontroller-fanout.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
