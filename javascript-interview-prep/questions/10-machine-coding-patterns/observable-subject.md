# Implement a Tiny Observable / Subject (RxJS-lite)

## Source
- Canonical reactive-programming machine-coding problem (RxJS `Subject`, Angular EventEmitter, MobX reactions).
- Asked at frontend-leaning senior rounds and at backend interviews that touch event-driven systems (SSE, WebSockets, change streams).

## Why this question matters in interviews
Subject is the bridge between **imperative pub/sub** (Node's `EventEmitter`) and **declarative reactive streams** (RxJS Observables). Implementing one in ~30 lines tests **class state**, **iteration over a `Set` while it mutates**, **teardown via returned unsubscribe**, **error/completion as terminal states**, and the **hot vs cold** distinction. Interviewers reach for it when they want to probe whether you understand reactive systems beyond surface-level — change feeds, websocket fan-out, real-time price ticks, log multiplexers, server-sent events. The implementation is small; the conceptual surface (multicasting, replay, backpressure) is enormous.

## Concepts involved

### Syntax to lock in
```js
class Subject {
  constructor() {
    this.subscribers = new Set();
    this.closed = false;
  }

  subscribe(observer) {
    if (this.closed) return () => {};
    const obs = typeof observer === 'function' ? { next: observer } : observer;
    this.subscribers.add(obs);
    return () => this.subscribers.delete(obs);   // teardown
  }

  next(value) {
    if (this.closed) return;
    for (const obs of [...this.subscribers]) obs.next?.(value);
  }

  error(err) {
    if (this.closed) return;
    this.closed = true;
    for (const obs of [...this.subscribers]) obs.error?.(err);
    this.subscribers.clear();
  }

  complete() {
    if (this.closed) return;
    this.closed = true;
    for (const obs of [...this.subscribers]) obs.complete?.();
    this.subscribers.clear();
  }
}
```

### Runtime / engine behavior
- `subscribers` is a `Set` for O(1) add/delete. The `Set` preserves insertion order — observers fire in subscription order.
- The `[...this.subscribers]` copy before iterating is **load-bearing**. If a subscriber calls `unsubscribe()` (or another `subscribe`) inside its `next` handler, mutating the Set mid-iteration would either skip a subscriber or invoke the new one in the same tick. Snapshotting fixes both.
- `closed = true` is a one-way latch. After `error` or `complete`, all further `next`/`error`/`complete` calls are silently dropped. New subscribers after termination get an immediate no-op teardown.
- The returned unsubscribe function captures `obs` in its closure. This is a textbook closure-as-handle pattern.
- Subjects are **hot**: values are pushed regardless of subscribers. A subscriber that joins after `next(1)` never sees that `1`. Compare with cold Observables that re-run a producer per subscription.

### Edge cases (these are the interview traps)
1. **Re-entrancy** — handler calls `subject.next(x)` again. Without iteration-snapshot, you'd recurse over a mutating Set. With snapshot, the nested `next` enqueues its own loop and runs after the current one returns (or synchronously, but over its own snapshot).
2. **Subscribing inside a handler** — the new subscriber should NOT receive the value currently being delivered (it joined mid-delivery). Snapshot-before-iteration gives this for free.
3. **Unsubscribing inside a handler** — same observer can `unsubscribe` itself in `next`. Snapshot makes the current pass complete cleanly; future `next` calls skip the removed observer.
4. **`error` and `complete` are terminal** — both set `closed=true`. After either, the Subject is dead. Don't conflate `error` with a transient "error event."
5. **Multicast vs unicast** — Subject is multicast (one push, all subscribers see it). A plain Observable in RxJS is unicast (each subscriber gets its own producer). Subject = hot multicast.
6. **Memory leak via long-lived subscribers** — a subscriber holds references to whatever its callbacks close over. If you never unsubscribe (e.g., long-running websocket fan-out), those references accumulate. Always return the unsubscribe and call it on cleanup.
7. **Async observer methods** — `obs.next?.(v)` is called synchronously. If `next` is async, the returned promise is ignored. That's intentional for Subject. If you need to wait, you need a different abstraction (a backpressured stream).
8. **Cold Observable** — would be: `new Observable(subscriber => { /* producer code */ return teardown; })`. Each `subscribe` re-runs the producer. Subject is the explicit hot version.

## Brute force approach
"I'll use an array and `.push`/`.indexOf`/`.splice`." Works but `splice` is O(n). For a small number of subscribers it's fine; for thousands (a websocket fan-out server) it's a real cost. State the trade-off and reach for `Set`.

Another non-starter: storing callbacks as plain functions and returning their index as a "token." Forces lookup math on unsubscribe and breaks if you reorder. Stick with Set + closure-captured reference.

## Optimal approach
`Set` of observer objects (`{next, error, complete}`). `subscribe` adds and returns a closure that deletes. `next`/`error`/`complete` iterate a **snapshot** of the Set, calling the matching handler. Terminal latch via `closed` boolean. O(1) subscribe/unsubscribe, O(n) per `next`.

## Solution (JavaScript)

```js
/**
 * Minimal hot multicast Subject — RxJS-lite.
 * Observer shape: { next?, error?, complete? } or a plain `next` function.
 */
class Subject {
  constructor() {
    this.subscribers = new Set();
    this.closed = false;
  }

  subscribe(observerOrNext) {
    if (this.closed) return () => {};
    const observer =
      typeof observerOrNext === 'function'
        ? { next: observerOrNext }
        : observerOrNext;
    this.subscribers.add(observer);
    return () => this.subscribers.delete(observer);
  }

  next(value) {
    if (this.closed) return;
    // Snapshot to survive in-handler subscribe/unsubscribe.
    for (const obs of [...this.subscribers]) {
      try { obs.next?.(value); }
      catch (err) { queueMicrotask(() => { throw err; }); } // don't break the loop
    }
  }

  error(err) {
    if (this.closed) return;
    this.closed = true;
    for (const obs of [...this.subscribers]) {
      try { obs.error?.(err); } catch { /* swallow during teardown */ }
    }
    this.subscribers.clear();
  }

  complete() {
    if (this.closed) return;
    this.closed = true;
    for (const obs of [...this.subscribers]) {
      try { obs.complete?.(); } catch { /* swallow */ }
    }
    this.subscribers.clear();
  }
}
```

A `BehaviorSubject` variant (replays the last value to new subscribers):
```js
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

## Step-by-step dry run

Input:
```js
const s = new Subject();
const log = (tag) => (v) => console.log(tag, v);

const offA = s.subscribe(log('A'));
s.next(1);                          // A 1

const offB = s.subscribe(log('B'));
s.next(2);                          // A 2, then B 2

offA();
s.next(3);                          // B 3

s.complete();
s.next(4);                          // nothing — Subject is closed
s.subscribe(log('C'));              // returns no-op; C never fires
```

Trace:
- `subscribe(log('A'))`: add `{next: log('A')}` to Set. Return unsubscribe closure.
- `next(1)`: snapshot=`[A]`. Call `A.next(1)` → `A 1`.
- `subscribe(log('B'))`: add B.
- `next(2)`: snapshot=`[A, B]`. Fire `A 2`, then `B 2`. Insertion order preserved.
- `offA()`: delete A from Set.
- `next(3)`: snapshot=`[B]`. Fire `B 3`.
- `complete()`: closed=true. Fire `B.complete?.()` (no handler given → noop). Clear set.
- `next(4)`: closed → return. No output.
- `subscribe(log('C'))`: closed → return no-op teardown. C never registered.

## Important takeaways

**Syntax to memorize**
- `Set` of observers; closure-returned unsubscribe.
- **Snapshot before iterating** (`[...this.subscribers]`). This is the bug that catches everyone.
- `closed` latch for terminal states (`error` and `complete` both set it).
- Observer shape: `{next?, error?, complete?}`. Use `?.` to skip missing methods.

**Patterns to reuse**
- "Set + closure-returned cleanup" is the canonical event-subscription pattern. Same shape as DOM `addEventListener` (where the cleanup returns nothing and you must remember the listener), `setInterval` (returns a handle), `MutationObserver` (returns `disconnect()`).
- Hot vs cold distinction generalizes: `EventEmitter` is hot, `function*` generators are cold, async iterators can be either.

**Common mistakes**
- Iterating `this.subscribers` directly without snapshot → reentrant `unsubscribe` skips a subscriber or visits a new one.
- Not latching `closed` → calling `complete()` twice fires `complete` handlers twice.
- Letting one thrown handler crash the whole `next` loop. Wrap in try/catch and rethrow async (`queueMicrotask`) so other subscribers still get the value.
- Confusing Subject (hot, multicast, state-bearing) with Observable (cold, unicast, lazy).

**Related questions**
- Node `EventEmitter` polyfill — same idea, different API (string event names).
- `BehaviorSubject` (replay-last-value), `ReplaySubject` (replay-N), `AsyncSubject` (emit-only-on-complete).
- Cold Observable: `new Observable(subscriber => { producer; return teardown; })`.

## Variants

1. **`BehaviorSubject`** — holds a "current value." New subscribers immediately receive it. Used everywhere in MobX/Angular for state-bearing streams.

2. **`ReplaySubject(n)`** — buffers the last `n` values. New subscribers receive the buffer on subscribe. Useful for late-joiners to a feed.

3. **Backpressure-aware Subject** — if `next` returns a Promise, the Subject `await`s before delivering to the next subscriber. Converts the API from sync fan-out to serial-async fan-out. Trade-off: slow subscribers block fast ones.

4. **Typed Subject (TypeScript)** — `class Subject<T> { ... next(v: T) ... }`. Forces the value type at the boundary. Trivial syntax change, big DX win in real codebases.

## Revision notes

> **Subject — 60 second recap**
> - `Set<Observer>`, `closed` latch.
> - `subscribe(obs) → add to Set, return () => Set.delete(obs)`.
> - `next(v)`: iterate **snapshot** of Set, call `obs.next?.(v)` on each.
> - `error(e)`/`complete()`: set `closed=true`, fire matching handler, clear Set.
> - Subject is **hot multicast**. Late subscribers miss prior values (unless BehaviorSubject/ReplaySubject).
> - Trap: iterating Set without snapshot → reentrancy bugs. One throwing handler must not break the loop.
> - Same shape as `EventEmitter`; reactive cousin of `Promise` (multi-value vs single-value).
