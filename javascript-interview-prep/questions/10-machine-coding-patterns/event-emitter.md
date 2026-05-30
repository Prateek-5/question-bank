# Implement an `EventEmitter`

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** <a href="https://leetcode.com/problems/event-emitter/" target="_blank" rel="noopener noreferrer">LeetCode 2694 — Event Emitter</a>. Node.js `events` module. The #1 most-asked machine-coding problem for backend roles.

---

## 1. Problem statement

**Signature**
```ts
class EventEmitter {
  subscribe(event: string, fn: Function): { unsubscribe(): void };
  on(event: string, fn: Function): { unsubscribe(): void };   // alias
  once(event: string, fn: Function): { unsubscribe(): void };
  off(event: string, fn: Function): void;
  emit(event: string, ...args: any[]): any[];
}
```

**Input / Output examples**

| Setup                                                                                       | Behaviour                                              |
|---------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `sub = e.subscribe('x', fn); e.emit('x', 1); sub.unsubscribe(); e.emit('x', 1)`            | first emit fires fn, second doesn't                    |
| `e.once('boot', fn); e.emit('boot'); e.emit('boot')`                                       | fn fires once; second emit is no-op                    |
| `e.emit('unknown')`                                                                         | returns `[]`; no error                                  |
| Same `fn` subscribed twice via `Set`                                                        | stored once; fires once per emit                       |
| `e.subscribe('x', fn)` inside another `fn` during emit                                     | new fn does NOT fire in current emit                  |
| `sub.unsubscribe()` inside an emit handler                                                  | next handlers in snapshot still fire                  |

**Constraints**
- Map<event, Set<fn>> internal shape.
- Return `{ unsubscribe }` handle from subscribe (better than ID-based).
- Snapshot listeners before iterating in emit (concurrent-modification safety).
- `once` wraps `fn` in a self-removing wrapper.
- Fire handlers synchronously (Node parity).

---

## 2. Plain-English restatement

A topic-keyed callback registry. `subscribe(event, fn)` adds a listener and returns a handle to remove it. `emit(event, ...args)` calls every listener for that event, in registration order, with the args. `once(event, fn)` is `subscribe` + auto-remove after the first fire. The trickiness is letting handlers safely subscribe/unsubscribe **during** an emit — solved by snapshotting the listener set first.

---

## 3. Why this matters in interviews

EventEmitter is the **#1 most-asked machine-coding problem for Node.js / backend roles**. It tests four things at once: (1) Map/Set choice, (2) returning an unsubscribe handle vs ID-based unsubscribe, (3) the `once` decorator with self-removing wrapper, (4) memory-leak awareness. Every Node engineer uses it daily — streams, http, child_process, custom domain events.

---

## 4. Mental model

```
   ┌──────────────────────────────────────────┐
   │ events: Map<string, Set<fn>>             │
   ├──────────────────────────────────────────┤
   │ 'user:login'  → { fnA, fnB }            │
   │ 'order:done'  → { fnC }                  │
   │ 'boot'        → { wrappedOnceFn }        │
   └──────────────────────────────────────────┘

   subscribe('user:login', fnX):
     events.get('user:login').add(fnX)
     return { unsubscribe: () => set.delete(fnX) }

   emit('user:login', payload):
     listeners = [...events.get('user:login')]   ← snapshot
     for fn of listeners: fn.apply(this, payload)

   once('boot', fn):
     wrapper = (...args) => { sub.unsubscribe(); fn(...args) }
     sub = subscribe('boot', wrapper)
     return sub
```

**Snapshot-before-iterate** is the key trick: handlers added or removed during emit don't break iteration.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If handler A unsubscribes itself and subscribes handler C during one emit, does C fire this round?
> 2. Why prefer a returned `{unsubscribe}` over a separate `off(event, fn)` API?
> 3. With `once(event, fn)`, what gets stored in the set — `fn` or a wrapper?

---

## 6. Brute force — walked through

### Wrong attempt 1: plain object as registry
```js
this.events = {};
// events['toString']  ← inherits from Object.prototype
```
Prototype pollution risk + `__proto__` collisions. Use `Map`.

### Wrong attempt 2: iterate the live set
```js
emit(event, ...args) {
  for (const fn of this.events.get(event) || []) fn(...args);
}
```
If `fn` unsubscribes itself, JS `Set` iteration handles it. But if `fn` *subscribes* a new handler, it may or may not fire — engine-dependent. Snapshot first.

### Wrong attempt 3: storing `fn` for `once` instead of wrapper
```js
once(event, fn) {
  fn._wasOnce = true;
  this.subscribe(event, fn);
}
emit() {
  ... if (fn._wasOnce) remove; ...
}
```
Tag-based logic is brittle. Wrap `fn` in a self-removing closure instead.

---

## 7. The unlocking insight

> **`Map<event, Set<fn>>` for O(1) ops + insertion-order iteration. `subscribe` returns `{ unsubscribe }` closing over set+fn. `emit` snapshots the set before iterating. `once` wraps in a self-removing wrapper.**

Three properties:

1. **`Map` of `Set`s** — O(1) add/delete, Set preserves insertion order, no proto pollution.
2. **Return-handle pattern** — `{ unsubscribe }` survives renames and beats string-keyed `off(event, fn)`.
3. **Snapshot in emit** — `[...set]` lets handlers mutate the set during iteration without bugs.

---

## 8. Solution (annotated)

```js
class EventEmitter {
  constructor() {
    this.events = new Map();                                     // step 1: Map<event, Set<fn>>
  }

  subscribe(event, fn) {
    if (!this.events.has(event)) this.events.set(event, new Set());
    const set = this.events.get(event);
    set.add(fn);                                                  // step 2: add listener

    return {
      unsubscribe: () => {                                        // step 3: return handle
        set.delete(fn);
        if (set.size === 0) this.events.delete(event);            // tidy: drop empty bucket
      },
    };
  }

  on(event, fn) { return this.subscribe(event, fn); }

  once(event, fn) {
    const wrapper = (...args) => {                                // step 4: self-removing wrapper
      sub.unsubscribe();
      fn.apply(this, args);
    };
    const sub = this.subscribe(event, wrapper);
    return sub;
  }

  off(event, fn) {                                                // step 5: legacy API
    const set = this.events.get(event);
    if (!set) return;
    set.delete(fn);
    if (set.size === 0) this.events.delete(event);
  }

  emit(event, ...args) {
    const set = this.events.get(event);
    if (!set || set.size === 0) return [];
    const listeners = [...set];                                   // step 6: SNAPSHOT
    return listeners.map((fn) => fn.apply(this, args));
  }
}
```

**Try it yourself**

```js
const e = new EventEmitter();

const s1 = e.subscribe('msg', (x) => console.log('A:', x));
const s2 = e.subscribe('msg', (x) => {
  console.log('B:', x);
  s2.unsubscribe();                                  // unsub self during emit
  e.subscribe('msg', (y) => console.log('C:', y));   // sub during emit
});

e.emit('msg', 1);     // A: 1 / B: 1   (C does NOT fire — added after snapshot)
e.emit('msg', 2);     // A: 2 / C: 2

// once
e.once('boot', () => console.log('boot fired'));
e.emit('boot');       // boot fired
e.emit('boot');       // (nothing)
```

---

## 9. Step-by-step dry run

```
const e = new EventEmitter()
const s1 = e.subscribe('msg', A)
            → events = { msg: Set{A} }
const s2 = e.subscribe('msg', B)
            → events = { msg: Set{A, B} }

e.emit('msg', 1):
  set = Set{A, B}
  snapshot listeners = [A, B]
  iterate snapshot:
    fn=A:  A(1) → log 'A: 1'
    fn=B:  B(1) → log 'B: 1'
                  inside B:
                    s2.unsubscribe() → set.delete(B) → set = Set{A}
                    e.subscribe('msg', C) → set = Set{A, C}
                  ↑ live set mutated; but iteration uses SNAPSHOT [A,B]
                  → C does NOT fire this round
  emit returns [undefined, undefined]

after emit: events = { msg: Set{A, C} }

e.emit('msg', 2):
  snapshot = [A, C]
  A(2) → log 'A: 2'
  C(2) → log 'C: 2'

Output: A:1 / B:1 / A:2 / C:2
```

`once` dry run:

```
e.once('boot', fn):
  wrapper = (...args) => { sub.unsubscribe(); fn(...args) }
  sub = subscribe('boot', wrapper)
  events = { boot: Set{wrapper} }

e.emit('boot'):
  snapshot = [wrapper]
  wrapper() runs:
    sub.unsubscribe() → events = { } (set drained, bucket removed)
    fn() runs → 'boot fired'

e.emit('boot'):
  events.get('boot') = undefined → return []
```

---

## 10. Common confusion + traps

1. **Plain object instead of Map** — proto pollution / collisions.
2. **No snapshot in emit** — subscribe-during-emit fires unexpectedly (engine-dependent).
3. **Storing `fn` instead of wrapper for `once`** — `off(event, fn)` can't find the wrapper.
4. **Forgetting to drop empty buckets** — `events` Map grows monotonically.
5. **Letting handler throw kill emit loop** — Node EventEmitter does NOT catch; failures bubble. Decide policy.
6. **Memory leak from forgotten `unsubscribe`** — closure-retained captures live forever.
7. **Async emit confusion** — Node fires sync; if interviewer wants `emitAsync`, return `Promise.all`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Wildcard topics
`e.on('user.*', fn)` — maintain a separate pattern list; match each `emit('user.x', ...)` against patterns. O(P) overhead per emit.

### Variant 2 — Async emit
```js
async emitAsync(event, ...args) {
  const set = this.events.get(event);
  if (!set) return [];
  const snapshot = [...set];
  return Promise.all(snapshot.map((fn) => fn.apply(this, args)));
}
```
Awaits each listener's return value. Useful for plugin/hook systems.

### Variant 3 — Max listeners limit
Node defaults to 10. Warn when `set.size > maxListeners`. Prevents leak detection.

### Variant 4 — `AbortSignal` integration
`subscribe(event, fn, { signal })` — auto-unsubscribes when `signal.aborted`. Pairs with request-scoped cleanup.

### Variant 5 — `prependListener`
Insert at front of list. Requires `Array` instead of `Set` (or two-list strategy).

---

## 12. How to think aloud

> "`Map<event, Set<fn>>`. `subscribe` adds and returns `{unsubscribe}` closing over set+fn — better than ID-based `off`. `emit` SNAPSHOTS the listeners (`[...set]`) before iterating, so handlers can safely subscribe/unsubscribe mid-emit. `once` wraps `fn` in a self-removing closure stored as the listener. Tidy: drop empty buckets to avoid memory growth. Family: Pub/Sub (topics + wildcards), Observable/RxJS (operators + backpressure), AbortSignal (modern cleanup). Trap: plain object → proto pollution. Trap: iterating live set → subscribe-during-emit fires unexpectedly. Trap: forgotten unsubscribe → closure retention → memory leak."

---

## 13. 60-second revision

> - **`events = Map<string, Set<fn>>`**.
> - **`subscribe` → returns `{ unsubscribe }`** (handle closing over set+fn).
> - **`emit` SNAPSHOTS** listeners (`[...set]`), then iterates.
> - **`once`** = wrap `fn` in a self-removing wrapper.
> - **Drop empty buckets** when `set.size === 0`.
> - **Sync fire** (Node parity); `emitAsync` uses `Promise.all`.
> - **Family:** Pub/Sub, Observable, AbortSignal.
> - **Trap:** plain object; no snapshot; missing unsubscribe → memory leak.

---

**Related:** [pub-sub.md](./pub-sub.md) · [observable-subject.md](./observable-subject.md) · [`04-promises/abortcontroller-fanout.md`](../04-promises/abortcontroller-fanout.md) · [`02-closures/closure-with-cancel-token.md`](../02-closures/closure-with-cancel-token.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/closures.md`](../../concepts/closures.md)
