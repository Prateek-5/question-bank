# Implement a tiny Observable / `Subject` (RxJS-lite)

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [event-emitter.md](./event-emitter.md), [pub-sub.md](./pub-sub.md)
>
> **Source:** RxJS `Subject` source, Angular `EventEmitter`, MobX reactions. Asked at frontend-leaning senior rounds and at backend interviews touching event-driven systems.

---

## 1. Problem statement

**Signature**
```ts
class Subject<T> {
  subscribe(observer: ((v: T) => void) | { next?(v: T); error?(e: any); complete?() }): () => void;
  next(value: T): void;
  error(err: any): void;
  complete(): void;
}
```

**Input / Output examples**

| Setup                                                          | Behaviour                                                |
|-----------------------------------------------------------------|----------------------------------------------------------|
| `s.next(1); s.subscribe(log); s.next(2)`                        | new subscriber misses `1`, sees `2` (hot)                |
| Subscriber unsubscribes inside its own `next` handler           | next call cleanly skips it; other subs unaffected        |
| One subscriber throws inside `next`                             | other subscribers still receive the value                |
| `s.complete(); s.next(x)`                                       | `next` is a no-op; Subject is closed                     |
| `s.error(e)` then `s.complete()`                                | second call ignored; closed latch is one-way             |
| `s.complete(); s.subscribe(log)`                                | returns no-op unsubscribe; subscriber never fires        |

**Constraints**
- `Set<Observer>` — O(1) add/delete + insertion-order iteration.
- Snapshot before iterating in `next`/`error`/`complete`.
- `closed` latch is one-way; terminal `error`/`complete` set it.
- Subject is **hot multicast**: late subscribers miss prior values.

---

## 2. Plain-English restatement

A push-based event source. Subscribers attach handlers (`next`/`error`/`complete`) and receive values whenever `next` is called. After `error` or `complete`, the Subject is dead — no further events fire, new subscribers are no-ops. Difference from EventEmitter: explicit terminal states and the observer-object convention.

---

## 3. Why this matters in interviews

Subject is the bridge between **imperative pub/sub** and **declarative reactive streams**. The implementation is ~30 lines but probes: class state, iteration-over-mutating-Set, teardown via returned unsubscribe, terminal states, hot vs cold distinction. Senior interviewers reach for it to test reactive-systems literacy — change feeds, websocket fan-out, real-time price ticks, log multiplexers.

---

## 4. Mental model

```
   Subject:
   ┌─────────────────────────────────┐
   │ subscribers: Set<Observer>      │
   │ closed: boolean                 │
   └─────────────────────────────────┘

   subscribe(obs):
     if closed → return () => {}
     add obs to Set
     return () => Set.delete(obs)

   next(v):     iterate SNAPSHOT [...subscribers]; call obs.next?.(v)
   error(e):    closed=true; fire obs.error?.(e); clear Set
   complete():  closed=true; fire obs.complete?.(); clear Set

   HOT MULTICAST:
   s.next(1)                  ← nobody home, value drops
   s.subscribe(A)
   s.next(2)                  → A sees 2
   s.subscribe(B)
   s.next(3)                  → A and B both see 3
   s.complete()               → A.complete fires, B.complete fires; closed=true
   s.next(4)                  ← no-op
```

**Hot vs cold:** Subject is hot (push regardless of subscribers). A cold `Observable` re-runs its producer per subscription.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If a subscriber calls `unsub()` inside its `next` handler, do the other subscribers still see this value?
> 2. After `complete()`, what does calling `next(x)` do? What about a new `subscribe(log)`?
> 3. If one subscriber's `next` throws, does the Subject keep firing the other subscribers?

---

## 6. Brute force — walked through

### Wrong attempt 1: Array + splice
```js
this.subs = [];
this.subs.push(obs);
const i = this.subs.indexOf(obs); this.subs.splice(i, 1);
```
Works but `splice` is O(n). For thousands of subscribers (websocket fan-out), real cost. Set is O(1).

### Wrong attempt 2: iterate the live Set
```js
for (const obs of this.subscribers) obs.next?.(v);
```
If an `obs.next` unsubscribes itself or others, iteration is engine-defined. Snapshot first.

### Wrong attempt 3: no closed latch
Without `closed`, `complete()` followed by `next(x)` still fires handlers. Or `complete()` runs twice → handlers fire twice. Latch with one-way boolean.

---

## 7. The unlocking insight

> **`Set<Observer>` for O(1) add/delete and insertion-order iteration. `closed` latch for terminal states. `next` iterates a SNAPSHOT (`[...subscribers]`) so handlers can safely subscribe/unsubscribe mid-emit. Wrap each handler in try/catch so one thrower doesn't stop the rest.**

Three properties:

1. **`Set<Observer>`** — observer is `{next?, error?, complete?}` (or a plain function for `next`).
2. **`closed` one-way latch** — set by `error` or `complete`; gates all further mutation.
3. **Snapshot + per-handler try/catch** — isolation and concurrent-modification safety.

---

## 8. Solution (annotated)

```js
class Subject {
  constructor() {
    this.subscribers = new Set();                                  // step 1: O(1) ops, insertion order
    this.closed = false;                                            // step 2: terminal latch
  }

  subscribe(observerOrNext) {
    if (this.closed) return () => {};                               // step 3: post-terminal no-op
    const observer =
      typeof observerOrNext === 'function'
        ? { next: observerOrNext }
        : observerOrNext;
    this.subscribers.add(observer);
    return () => this.subscribers.delete(observer);                 // step 4: closure-returned cleanup
  }

  next(value) {
    if (this.closed) return;
    for (const obs of [...this.subscribers]) {                       // step 5: SNAPSHOT
      try { obs.next?.(value); }
      catch (err) { queueMicrotask(() => { throw err; }); }          // isolate, re-throw async
    }
  }

  error(err) {
    if (this.closed) return;
    this.closed = true;
    for (const obs of [...this.subscribers]) {
      try { obs.error?.(err); } catch {}
    }
    this.subscribers.clear();
  }

  complete() {
    if (this.closed) return;
    this.closed = true;
    for (const obs of [...this.subscribers]) {
      try { obs.complete?.(); } catch {}
    }
    this.subscribers.clear();
  }
}

// BehaviorSubject — replays the last value to new subscribers
class BehaviorSubject extends Subject {
  constructor(initial) { super(); this.value = initial; }
  subscribe(o) {
    const off = super.subscribe(o);
    if (!this.closed) (typeof o === 'function' ? o : o.next)?.(this.value);
    return off;
  }
  next(v) { this.value = v; super.next(v); }
}
```

**Try it yourself**

```js
const s = new Subject();
const log = (tag) => (v) => console.log(tag, v);

const offA = s.subscribe(log('A'));
s.next(1);                             // A 1

const offB = s.subscribe(log('B'));
s.next(2);                             // A 2, B 2

offA();
s.next(3);                             // B 3

s.complete();
s.next(4);                             // (nothing, closed)
s.subscribe(log('C'));                 // returns no-op; C never fires
```

---

## 9. Step-by-step dry run

```
const s = new Subject()                                    state: subs={}, closed=false
const offA = s.subscribe(log('A'))                         subs={A}
s.next(1)                                                   snapshot=[A]; A.next(1) → 'A 1'
const offB = s.subscribe(log('B'))                         subs={A, B}
s.next(2)                                                   snapshot=[A, B]; A.next(2), B.next(2) → 'A 2', 'B 2'
offA()                                                       subs={B}
s.next(3)                                                   snapshot=[B]; B.next(3) → 'B 3'
s.complete()                                                 closed=true; for [B]: B.complete?.() (noop); subs={}
s.next(4)                                                   closed=true → return; no output
s.subscribe(log('C'))                                       closed=true → return () => {}; C never registered
```

In-handler unsubscribe:
```
sub1 subscribes; sub2 subscribes — subs={sub1, sub2}
sub1.next = (v) => { ...; sub1Unsub(); s.subscribe(sub3) }
s.next('x'):
  snapshot=[sub1, sub2]
  iterate snapshot:
    fn=sub1: handles v. Inside handler: subs={sub2}, then subs={sub2, sub3}
                       ↑ live mutation; snapshot unchanged
    fn=sub2: still in snapshot → fires.
  sub3 NOT fired this round.
After next: subs={sub2, sub3}.
```

---

## 10. Common confusion + traps

1. **Iterating the live Set** — reentrant subscribe/unsubscribe causes inconsistent fan-out.
2. **No `closed` latch** — `complete()` twice fires handlers twice; `next` after `complete` still dispatches.
3. **Letting one thrower kill the loop** — wrap each `obs.next?.(v)` in try/catch.
4. **Confusing Subject (hot multicast) with Observable (cold unicast)** — Subject pushes regardless; Observable re-runs producer per subscription.
5. **Async `next` handlers** — `obs.next?.(v)` is called sync; returned promise is ignored.
6. **Memory leak via long-lived subscribers** — closures retain everything. Always pair `subscribe` with cleanup.
7. **BehaviorSubject replay timing** — replay happens during subscribe, before subsequent `next` calls.

---

## 11. Senior follow-ups & variants

### Variant 1 — `BehaviorSubject`
Holds a "current value." New subscribers immediately receive it. State-bearing streams (MobX, Angular services).

### Variant 2 — `ReplaySubject(n)`
Buffers last `n` values. New subscribers receive the buffer on subscribe.

### Variant 3 — `AsyncSubject`
Only emits to subscribers when `complete()` is called — the **last** value before completion.

### Variant 4 — Backpressure-aware Subject
If `next` returns a Promise, await before next subscriber. Sync fan-out → serial-async fan-out. Slow subscribers block fast ones — trade-off.

### Variant 5 — Cold Observable
```js
new Observable((subscriber) => {
  const producer = ...;
  return () => producer.cancel();   // teardown
});
```
Each `subscribe` re-runs the producer. Subject is hot; Observable is cold.

---

## 12. How to think aloud

> "`Set<Observer>` for O(1) add/delete and insertion-order iteration. `closed` boolean as a one-way latch — set by `error` or `complete`. `next` iterates a SNAPSHOT (`[...subscribers]`) so handlers can subscribe/unsubscribe mid-emit. Each handler call wrapped in try/catch — one thrower must not break the loop; rethrow async via `queueMicrotask` so test runners and global error handlers still see it. Subject is hot multicast — late subscribers miss prior values. BehaviorSubject replays last value to new subscribers. Cold Observable re-runs producer per subscription. Trap: iterating live Set without snapshot. Trap: no `closed` latch."

---

## 13. 60-second revision

> - **`Set<Observer>` + `closed` latch.**
> - **`subscribe`** returns closure that deletes from Set; no-op if already closed.
> - **`next`** iterates SNAPSHOT (`[...subscribers]`), try/catch per handler.
> - **`error` / `complete`** set `closed=true`, fire matching handler, clear Set.
> - **Hot multicast** — late subscribers miss prior values.
> - **`BehaviorSubject`** = replays last value; **`ReplaySubject(n)`** = buffers N.
> - **vs cold Observable** — cold re-runs producer per subscription.
> - **Trap:** iterate live Set; no `closed` latch; one thrower breaking loop.

---

**Related:** [event-emitter.md](./event-emitter.md) · [pub-sub.md](./pub-sub.md) · [`04-promises/async-generator-producer.md`](../04-promises/async-generator-producer.md) · [`06-streams/backpressure-and-highwater.md`](../06-streams/backpressure-and-highwater.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
