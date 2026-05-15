# Implement an `EventEmitter`

## Source
- Canonical machine-coding interview problem (LeetCode #2694 "Event Emitter", Node.js source: `events` module, BFE.dev).
- LeetCode reference: https://leetcode.com/problems/event-emitter/

## Why this question matters in interviews
EventEmitter is the **#1 most-asked machine-coding problem for Node.js / backend roles**. It tests four things at once: (1) Map/Set data structure choice, (2) returning an unsubscribe handle vs ID-based unsubscribe, (3) the **once** decorator and its self-removing wrapper, (4) memory-leak awareness. Every Node engineer uses EventEmitter daily — streams, http, child_process, custom domain events — so interviewers expect a clean, idiomatic implementation in under 10 minutes. The senior-level differentiators are: returning a `subscription` object with `.unsubscribe()` (vs the older `off(event, fn)` API), handling listener-during-emit safely (callbacks added in a handler shouldn't fire in the current emit), and discussing wildcards / once / max-listeners.

## Concepts involved

### Syntax to lock in
```js
const emitter = new EventEmitter();
const sub = emitter.subscribe('user:login', (user) => console.log(user));
emitter.emit('user:login', { id: 1 });   // logs { id: 1 }
sub.unsubscribe();
emitter.emit('user:login', { id: 1 });   // nothing

emitter.once('boot', () => console.log('booted'));
emitter.emit('boot');   // logs
emitter.emit('boot');   // nothing
```

Internal shape:
```js
class EventEmitter {
  constructor() { this.events = new Map(); /* Map<eventName, Set<fn>> */ }
}
```

### Runtime / engine behavior
- `Map<string, Set<fn>>` is the textbook choice. `Set` gives O(1) add/remove and de-dupes (same `fn` registered twice is stored once).
- **Order matters** in some semantics — Node's `EventEmitter` fires handlers in **registration order**. `Set` preserves insertion order in JS, so it works. If interviewer insists on duplicates allowed (rare), switch to `Array`.
- **Snapshot on emit**: when iterating handlers to fire them, take a snapshot (`[...set]`) so that handlers added or removed during emit don't break iteration. This is a classic concurrent-modification bug.
- **`once`**: wrap the handler in a function that calls the real one and then unsubscribes itself. Store the wrapper, not the original — so the wrapper is what `off` removes.
- Callbacks fire **synchronously** in Node's EventEmitter (unlike Promise.then). Mention this — many candidates assume async.

### Edge cases (these are the interview traps)
1. **Unsubscribe during emit** — if a handler calls `sub.unsubscribe()` during the emit loop, the next handlers must still fire. Snapshot the listeners first.
2. **Subscribe during emit** — newly added handlers should **not** fire in the current emit. Snapshot handles this for free.
3. **Same fn subscribed twice** — Set: stored once. Array: stored twice and fires twice. Node's default is "twice." Decide and state it.
4. **`once` + `off`** — calling `off(event, fn)` where `fn` is the original (not the wrapper) — does it remove? In Node, `removeListener` walks both. Implement by storing a `wrapped → original` map, or by exposing `sub.unsubscribe()` so the caller doesn't need to track the wrapper.
5. **Emit with no handlers** — should be a no-op, never throw. Special exception: Node throws on `'error'` event with no listeners. Mention but don't implement unless asked.
6. **Max listeners warning** — Node warns at 10 listeners. Skip unless asked.
7. **Wildcard / namespacing** — `emitter.on('user.*', fn)`. Not standard; advanced variant.
8. **Memory leaks** — forgetting to `off` keeps closures alive. Single most common bug in Node services. Always pair `on` with `off` in lifecycles, or use `AbortSignal` (Node 18+).

## Brute force approach
A plain object keyed by event name, value = array. Works, but suffers from the usual prototype-pollution risk (`emitter.emit('toString')` could trip on inherited stuff). Skip — use `Map`.

## Optimal approach
`Map<eventName, Set<fn>>`. `subscribe(event, fn)` adds, returns `{ unsubscribe }` closing over the set + fn. `emit(event, ...args)` snapshots the set and calls each. `once(event, fn)` wraps `fn` to self-remove, then `subscribe`s the wrapper. O(1) subscribe / unsubscribe, O(N) emit where N = listener count.

## Solution (JavaScript)

```js
class EventEmitter {
  constructor() {
    /** @type {Map<string, Set<Function>>} */
    this.events = new Map();
  }

  /**
   * Subscribe a listener.
   * @param {string} event
   * @param {Function} fn
   * @returns {{ unsubscribe: () => void }}
   */
  subscribe(event, fn) {
    if (!this.events.has(event)) this.events.set(event, new Set());
    const set = this.events.get(event);
    set.add(fn);

    return {
      unsubscribe: () => {
        set.delete(fn);
        if (set.size === 0) this.events.delete(event);
      },
    };
  }

  // Alias for the Node-style API
  on(event, fn) { return this.subscribe(event, fn); }

  /**
   * Subscribe a listener that fires once, then auto-unsubscribes.
   */
  once(event, fn) {
    const wrapper = (...args) => {
      sub.unsubscribe();
      fn.apply(this, args);
    };
    const sub = this.subscribe(event, wrapper);
    return sub;
  }

  /**
   * Remove a specific listener (Node-style API).
   * Less ergonomic than the returned-handle approach — prefer subscribe().
   */
  off(event, fn) {
    const set = this.events.get(event);
    if (!set) return;
    set.delete(fn);
    if (set.size === 0) this.events.delete(event);
  }

  /**
   * Emit synchronously. Returns the array of return values from listeners.
   */
  emit(event, ...args) {
    const set = this.events.get(event);
    if (!set || set.size === 0) return [];
    // Snapshot to allow unsubscribe / subscribe during emit.
    const listeners = [...set];
    return listeners.map((fn) => fn.apply(this, args));
  }
}
```

## Step-by-step dry run

Input:
```js
const e = new EventEmitter();
const s1 = e.subscribe('msg', (x) => console.log('A:', x));
const s2 = e.subscribe('msg', (x) => {
  console.log('B:', x);
  s2.unsubscribe();             // unsub during emit
  e.subscribe('msg', (y) => console.log('C:', y));  // sub during emit
});

e.emit('msg', 1);    // first
e.emit('msg', 2);    // second
```

Trace:
- After both subscribes: `events = { msg: Set{ A, B } }`.
- `emit('msg', 1)`:
  - Snapshot listeners = `[A, B]`.
  - Call `A(1)` → logs `A: 1`.
  - Call `B(1)` → logs `B: 1`. Inside B: `s2.unsubscribe()` → set becomes `{ A }`. Then `subscribe(C)` → set becomes `{ A, C }`. The current iteration uses the snapshot `[A, B]`, so C does NOT fire this round.
  - Iteration ends.
- After first emit: `events = { msg: Set{ A, C } }`.
- `emit('msg', 2)`:
  - Snapshot = `[A, C]`.
  - `A(2)` → logs `A: 2`.
  - `C(2)` → logs `C: 2`.

Final output:
```
A: 1
B: 1
A: 2
C: 2
```

This trace specifically demonstrates the "snapshot during emit" property. Without snapshotting, mutating the set during iteration would either skip C / re-fire B / throw, depending on the data structure.

Now `once`:
```js
e.once('boot', () => console.log('boot fired'));
e.emit('boot');   // logs 'boot fired'
e.emit('boot');   // nothing — wrapper already removed itself
```

## Important takeaways

**Syntax to memorize**
- `events = new Map()` of `event → Set<fn>`.
- `subscribe` returns `{ unsubscribe }` — closure over the set + fn.
- `emit` **snapshots** listeners (`[...set]`) before iterating.
- `once` wraps fn in a self-removing wrapper.

**Patterns to reuse**
- "Return an unsubscribe handle" is universally better than "store an ID and call `off(id)`". Pattern shows up in: RxJS `Subscription`, DOM `AbortSignal`, Firebase `onSnapshot`, React `useEffect` cleanup. Always prefer.
- Map-of-Set for "categories with members" is a recurring shape: pub/sub topics, event listeners, room-based websocket clients.
- Snapshot-before-iterate is the cure for concurrent-modification bugs anywhere you have callbacks that can mutate the listener list.

**Common mistakes**
- Iterating a `Set` while mutating it (e.g., `forEach` + `delete`) — works in JS Sets (`Set.forEach` handles deletion safely), but the **subscribe-during-emit** case is the real risk. Snapshot always.
- Storing only the original `fn` in `once` — then `off(event, fn)` looks for the wrapper and fails. Either store the mapping or return an unsubscribe handle (cleaner).
- Forgetting to clean up empty event sets — leaves a growing `events` map. `set.size === 0 → delete` keeps it tidy.
- Letting subscribers throw kill the emit loop — wrap each `fn.apply` in try/catch if you want isolation (Node's emitter does NOT — failures bubble).

**Related questions**
- Pub/Sub — see pub-sub.md. Similar but topic-string-keyed, often supports wildcards and async dispatch.
- Observable / RxJS — generalizes EventEmitter with backpressure and operators.
- `AbortController` — modern cancellation primitive that pairs with `on(event, fn, { signal })`.

## Variants

1. **Wildcard topics** — `emitter.on('user.*', fn)` fires for any event matching the pattern. Maintain a separate list of pattern listeners and match on emit. O(P) overhead per emit (P = pattern count).

2. **Async emit** — `await emitter.emitAsync(event, ...args)` awaits each listener's return value (or all in parallel via `Promise.all`). Useful for hook systems.

3. **Max listeners limit** — Node's default 10-listener warning. Track per-event size; warn when exceeded.

4. **AbortSignal integration** — `subscribe(event, fn, { signal })` auto-unsubscribes when signal aborts. Pairs nicely with `AbortController` for request-scoped lifecycles.

5. **Prepend** — `prependListener(event, fn)` inserts at the front. Requires `Array` instead of `Set`, or a two-list strategy.

## Revision notes

> **EventEmitter — 60 second recap**
> - `events = Map<string, Set<fn>>`.
> - `subscribe(event, fn)` → returns `{ unsubscribe }` (better than ID-based).
> - `emit(event, ...args)` → **snapshot** listeners first, then iterate.
> - `once(event, fn)` → wrap in a self-removing wrapper.
> - **Trap:** mutating the set during iteration without snapshotting → subscribe-during-emit fires/misses unexpectedly.
> - **Trap 2:** forgetting `off` → memory leak (closure retention).
> - Family: Pub/Sub (topics + wildcards), Observable (RxJS), AbortSignal (modern cleanup).
