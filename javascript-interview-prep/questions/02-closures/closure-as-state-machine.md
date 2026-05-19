# Build a finite state machine — `createMachine({ states, initial })`

> **Difficulty:** Medium-Hard   |   **Time:** ~30 min   |   **Prereqs:** [counter-ii.md](./counter-ii.md), [module-pattern-iife.md](./module-pattern-iife.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Classic "rolling your own FSM" pattern; xstate's mental model. Asked at Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

**Signature**
```ts
function createMachine<S extends string, E extends string>(config: {
  initial: S;
  states: Record<S, {
    on?: Partial<Record<E, S | { target: S; cond?: (ctx, payload) => boolean; actions?: (ctx, payload) => void }>>;
    entry?: (ctx) => void;
    exit?: (ctx) => void;
  }>;
  context?: object;
}): {
  readonly state: S;
  readonly context: object;
  send(event: E, payload?: any): void;
  subscribe(fn: (snapshot) => void): () => void;
  serialize(): { state: S; context: object };
  restore(snap: { state: S; context: object }): void;
};
```

**Input / Output examples**

| Setup                                                                         | Sequence                                  | Outcome                                |
|-------------------------------------------------------------------------------|--------------------------------------------|----------------------------------------|
| Traffic light: red → green → yellow → red                                    | `send('TIMER')` × 3                       | `red → green → yellow → red`           |
| Order machine with guard: `PAY` only if `amount > 0`                          | `send('PAY', {amount: 100})`              | transitions to `paid`; sets `ctx.paid` |
| Invalid event from current state                                              | `send('DELIVER')` from `placed`           | throws `"No transition from placed on DELIVER"` |
| Persistence                                                                   | `serialize() → JSON → restore()`         | resumable workflow                    |

**Constraints**
- All state, transitions, and context are private to the closure.
- Transitions defined declaratively in a `states` table.
- Invalid transitions **throw** (surface bugs).
- Hooks: `entry` and `exit` fire on every state change. Order: exit current → set new state → entry next → notify subscribers.
- Optional: guards (`cond`), actions (mutate `ctx`), serialize/restore.

---

## 2. Plain-English restatement

Many business workflows are state machines: an order moves through `placed → paid → shipped → delivered`; a file upload moves through `idle → uploading → done | failed`; a user session moves through `anonymous → authenticating → authenticated → expired`. A finite state machine (FSM) makes the legal transitions **explicit** — you declare a table mapping `(current_state, event) → next_state`, and the machine refuses anything not in the table.

Build one as a closure: the current state and a context object live inside the factory's lexical scope; the only doors in are `send(event)` to fire a transition and `subscribe(fn)` to observe changes.

---

## 3. Why this matters in interviews

State-modeling discipline is a senior signal. Engineers who don't reach for FSMs end up with combinatorial boolean flags — `isLoading && !isError && isStale` — that explode into "impossible state" bugs. A senior interviewer asks for an FSM (or describes a workflow that's obviously an FSM) to see whether you (1) propose the right shape, (2) handle invalid transitions cleanly, (3) get the exit/entry ordering right, and (4) know when to graduate to xstate (hierarchical states, parallel regions, visualizer, statecharts). For most business state, a hand-rolled FSM in ~40 lines is the right answer.

---

## 4. Mental model

A **traffic light** with three states and one event:

```
   ┌──── red ────┐ TIMER  ┌──── green ────┐ TIMER  ┌──── yellow ────┐ TIMER
   │ entry:stop  │ ─────▶ │ entry:go      │ ─────▶ │ entry:slow      │ ───┐
   └─────────────┘        └───────────────┘        └────────────────┘    │
        ▲                                                                 │
        └─────────────────────────────────────────────────────────────────┘
                                                                  back to red

   closure state:  { current, context, listeners }
   send(event):    exit current → set current=next → entry next → notify
```

The transitions table is the **source of truth**. Code that mutates state directly (`current = 'paid'`) violates the model and re-introduces "impossible state" bugs. Funnel every change through `send`.

For richer flows, extend transitions to `{ target, cond, actions }`:

- **`cond(ctx, payload)`** — guard. If false, the transition is rejected.
- **`actions(ctx, payload)`** — mutates `context` before the state change. Used for "amount paid," "retries remaining," etc.
- **`entry(ctx)`** / **`exit(ctx)`** — side effects per state.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If you fire `send('DELIVER')` from a `placed` state where the table has no `DELIVER` mapping, should the machine throw, ignore silently, or log a warning? What's the trade-off?
> 2. In what order should `exit`, the state assignment, `entry`, and the subscriber notification fire? What goes wrong if you do them in the wrong order?
> 3. If you want subscribers to receive the **new** state (not the old one), where does the notification go in the lifecycle?

---

## 6. Brute force — walked through

### Wrong attempt 1: boolean flags

```js
let isPending = true, isApproved = false, isShipped = false;
function approve() { isApproved = true; isPending = false; }
function ship() { isShipped = true; }
```

Two problems. **Combinatorial explosion**: three booleans = eight possible states, but only four are valid (`pending`, `approved`, `approved+shipped`, `pending+shipped`?). Code has to check every illegal combo. **Scattered transitions**: rules live in each method, not in a table — hard to audit, easy to miss.

### Wrong attempt 2: enum + switch

```js
let status = 'pending';
function approve() {
  if (status !== 'pending') throw;
  status = 'approved';
}
function ship() {
  if (status !== 'approved') throw;
  status = 'shipped';
}
```

Better — one variable, mutually exclusive states. But transitions are still scattered across methods. Adding a new event means hunting through code. Hard to visualize. No hooks for entry/exit.

### Wrong attempt 3: table without exit/entry ordering

```js
function send(event) {
  const next = states[current].on[event];
  if (!next) throw;
  states[next].entry?.();   // BUG: entry fires before current is set
  states[current].exit?.();  // BUG: exit fires AFTER entry — wrong order
  current = next;
}
```

Hook ordering is wrong. Subscribers reading `state` during `entry` see the old state because the assignment hasn't happened yet. The correct sequence: **exit current → set current = next → entry next → notify subscribers**.

---

## 7. The unlocking insight

> **A finite state machine is a closure over `(current, context)` whose only entry point is `send(event)` — which looks up the transition in a declarative table, runs guards/actions, and applies the exit/set/entry/notify lifecycle in that exact order.**

The pattern enforces three invariants:

1. **All transitions in the table** — no method mutates `current` directly. Want to add a new event? Edit the table. Want to audit legal transitions? Read the table. The table is the single source of truth.

2. **Throw on invalid transitions** — silently ignoring "no transition from X on Y" hides bugs (callers think their event landed when it didn't). Throwing forces the caller to handle the error or fix the call site. Optionally add a catch-all `'*'` for "ignore unknown events" if your domain genuinely allows it.

3. **Lifecycle order: exit → set → entry → notify** — exit fires while `current` is still the old state (so the hook sees the state it's leaving); then `current = next`; then entry fires with the new state visible; then subscribers are notified. Reversing any pair breaks observability.

**Guards and actions** extend the model from "pure FSM" to "extended FSM" (also called a state-transducer). The guard `cond(ctx, payload)` returns true/false; false rejects the transition. The action `actions(ctx, payload)` mutates `context` *before* the state change — so `entry(ctx)` sees the updated context.

**Persistence** is free: serialize `{ current, context }` to JSON; restore by setting both. The transitions table is part of the code, not the state — it doesn't need persisting.

**When to graduate to xstate**: hierarchical states (state inside a state), parallel regions (orthogonal sub-machines), history states (return to last-active-substate), visualizer support, and statechart formalism. For most business flows, a hand-rolled FSM in ~40 lines beats the dependency.

---

## 8. Solution (annotated)

```js
function createMachine({ initial, states, context = {} }) {
  let current = initial;                                         // step 1: private state
  let ctx = { ...context };                                       //          (shallow copy)
  const listeners = new Set();                                    // step 2: pub/sub

  function set(next) {                                            // step 3: the lifecycle
    const cur = states[current];
    if (cur?.exit) cur.exit(ctx);                                   //          exit current
    current = next;                                                 //          set new state
    if (states[next].entry) states[next].entry(ctx);                //          entry next
    listeners.forEach((fn) => fn({ state: current, context: ctx }));// notify subscribers
  }

  return {
    get state() { return current; },
    get context() { return ctx; },

    send(event, payload) {
      const def = states[current];
      const trans = def?.on?.[event];

      if (!trans) {                                                  // step 4: invalid event
        if (def?.on?.['*']) return;                                   //          optional catch-all
        throw new Error(`No transition from ${current} on ${event}`);
      }

      const next = typeof trans === 'string' ? trans : trans.target;

      if (typeof trans === 'object' && trans.cond) {                 // step 5: guard
        if (!trans.cond(ctx, payload)) {
          throw new Error(`Guard failed: ${current} -[${event}]→ ${next}`);
        }
      }
      if (typeof trans === 'object' && trans.actions) {              // step 6: action (mutates ctx)
        trans.actions(ctx, payload);
      }
      set(next);                                                      // step 7: transition
    },

    subscribe(fn) {                                                  // step 8: observation
      listeners.add(fn);
      return () => listeners.delete(fn);
    },

    serialize() { return { state: current, context: { ...ctx } }; }, // step 9: persistence
    restore(snap) { current = snap.state; ctx = { ...snap.context }; },
  };
}
```

**Try it yourself**

```js
// Traffic light
const traffic = createMachine({
  initial: 'red',
  states: {
    red:    { on: { TIMER: 'green' },  entry: () => console.log('STOP') },
    green:  { on: { TIMER: 'yellow' }, entry: () => console.log('GO') },
    yellow: { on: { TIMER: 'red' },    entry: () => console.log('SLOW') },
  },
});
traffic.send('TIMER');   // logs "GO"; state: 'green'
traffic.send('TIMER');   // logs "SLOW"; state: 'yellow'
traffic.send('TIMER');   // logs "STOP"; state: 'red'

// Order workflow with guard, action, and context
const order = createMachine({
  initial: 'placed',
  context: { paid: 0, shippedAt: null },
  states: {
    placed: {
      on: {
        PAY: {
          target: 'paid',
          cond: (ctx, p) => p.amount > 0,
          actions: (ctx, p) => { ctx.paid = p.amount; },
        },
        CANCEL: 'cancelled',
      },
    },
    paid:      { on: { SHIP: { target: 'shipped', actions: (ctx) => { ctx.shippedAt = Date.now(); } }, REFUND: 'refunded' } },
    shipped:   { on: { DELIVER: 'delivered' } },
    delivered: { entry: () => console.log('order complete') },
    cancelled: {}, refunded: {},
  },
});

const unsub = order.subscribe(({ state, context }) =>
  console.log('order →', state, context)
);

order.send('PAY', { amount: 100 });    // → 'paid'   ctx.paid = 100
order.send('SHIP');                     // → 'shipped' ctx.shippedAt set
order.send('DELIVER');                  // → 'delivered' logs "order complete"

// Persistence
const snap = order.serialize();          // { state: 'delivered', context: {...} }
const restored = createMachine({ initial: 'placed', states: order.states });
restored.restore(snap);
```

---

## 9. Step-by-step dry run

Input:

```js
const m = createMachine({
  initial: 'idle',
  context: { count: 0 },
  states: {
    idle:    { on: { START: { target: 'running', actions: (ctx) => { ctx.count++; } } } },
    running: { on: { STOP: 'idle' }, entry: () => console.log('started') },
  },
});
m.send('START');
m.send('STOP');
m.send('STOP');   // illegal from 'idle' → throws
```

Values-first trace:

| Step      | Action          | `current`       | `ctx`             | Output / Throw           |
|-----------|-----------------|-----------------|--------------------|---------------------------|
| init      | `createMachine` | `'idle'`        | `{count: 0}`       | —                         |
| 1         | `send('START')` | `'idle' → 'running'` | `{count: 1}` | logs `"started"` (entry)  |
| 2         | `send('STOP')`  | `'running' → 'idle'` | `{count: 1}` | —                         |
| 3         | `send('STOP')`  | (unchanged)     | (unchanged)        | throws `"No transition from idle on STOP"` |

Lifecycle of step 1:

1. Look up `states.idle.on.START` → `{target: 'running', actions}`.
2. No `cond` to check.
3. Run `actions(ctx, undefined)` → `ctx.count = 1`.
4. `set('running')`:
   - `states.idle.exit` — none, skip.
   - `current = 'running'`.
   - `states.running.entry()` → logs `"started"`.
   - Notify subscribers with `{ state: 'running', context: {count: 1} }`.

---

## 10. Common confusion + traps

1. **Boolean flags instead of states.**
   Three booleans = eight combinations, four invalid. Use a single state variable with mutually-exclusive values.

2. **Scattered transitions in methods.**
   A switch in each handler works but loses the audit trail. The table is the single source of truth.

3. **Async transitions fire-and-forget.**
   If `entry` is async and you don't await it, listeners may fire with `state` pointing to "after entry" while entry is still running. Decide: synchronous entry only, or `await` inside set.

4. **Wrong lifecycle order.**
   Must be **exit → set → entry → notify**. Reversing exit and set means exit sees the new state (wrong); reversing entry and notify means subscribers see no entry side effects yet.

5. **Silently ignoring invalid transitions.**
   Throws are better — they surface bugs in the caller. Add a `'*'` catch-all only when your domain genuinely allows ignoring unknown events.

6. **Mutating `current` from outside the machine.**
   Use only `send()`. The getter `state` is read-only by design.

7. **Pure FSM has no context.**
   If you need data alongside state (counters, amounts, retries), you're in **extended FSM** territory. The `ctx` object holds the data; actions mutate it on transition.

8. **Re-entrant transitions (self → self).**
   `send('TIMER')` on `red` going to `red` — should `entry` fire again? Decide per use case. Default: yes (re-firing entry is sometimes desirable, e.g., for re-arming a timer).

---

## 11. Senior follow-ups & variants

### Variant 1 — Hierarchical states (statecharts)

Nested states. `green` has substates `solid`, `flashing`. Transitions at the parent level apply to all children unless overridden. This is **xstate** territory — hand-rolling gets verbose quickly. Mention you'd reach for xstate.

```js
// Sketch: states have their own substate machine
const player = createMachine({
  initial: 'stopped',
  states: {
    stopped: { on: { PLAY: 'playing.normal' } },
    playing: {
      initial: 'normal',
      states: {
        normal: { on: { FAST_FORWARD: 'fast' } },
        fast:   { on: { NORMAL: 'normal' } },
      },
      on: { STOP: 'stopped' },   // applies to all substates
    },
  },
});
```

### Variant 2 — Parallel regions

Two orthogonal sub-machines running simultaneously. Example: a media player has `playback` state (`playing`/`paused`) AND `audio` state (`muted`/`unmuted`). Independent transitions; combined snapshot. Again, xstate.

### Variant 3 — Async actions / effects

```js
states: {
  uploading: {
    entry: async (ctx) => {
      try { await uploadFile(ctx.file); send('DONE'); }
      catch (e) { ctx.error = e; send('FAIL'); }
    },
    on: { DONE: 'completed', FAIL: 'errored' },
  },
}
```

xstate calls these "invoked services." For hand-rolled, be careful: synchronously trigger `send()` from within `entry` can cause re-entrant transitions. Defer with `queueMicrotask` if needed.

### Variant 4 — Persistence with workflow engines

For long-running flows (hours, days), persist `{ state, context, history }` to a database. Recover on process restart. This is what Temporal, AWS Step Functions, and Cadence do at scale.

### Variant 5 — Time-based transitions

```js
states: {
  pending: {
    on: { CONFIRM: 'confirmed' },
    after: { 60_000: 'expired' },   // auto-transition after 60s
  },
}
```

xstate has built-in `after`. Hand-rolled: `setTimeout` inside `entry`, clear in `exit`.

### Variant 6 — Catch-all wildcard `*`

```js
states: {
  any: { on: { '*': 'any' } },   // ignore unknown events
}
```

Useful when the machine should silently absorb out-of-band events (e.g., spurious pings).

---

## 12. How to think aloud in the interview

> "I'd model this as a finite state machine. Closure over `current` and `context`. The transitions table is the source of truth: `states[name].on[event]` maps to either a target string or `{target, cond, actions}`. `send(event)` looks up, runs the guard, runs the action, then applies the lifecycle: exit current → set new → entry next → notify subscribers. Invalid transitions throw (surfaces bugs). `cond` rejects without changing state; `actions` mutate `context` before the state change. Subscribers see the new state. Serialize/restore is just `{ state, context }` — the table is code. For complex flows — hierarchical states, parallel regions, async services — I'd reach for xstate. Most business state fits in a 40-line hand-rolled FSM."

---

## 13. 60-second revision

> - **Pattern:** closure over `current`, `context`, `listeners`. Transitions in a declarative table.
> - **`send(event, payload)`** = lookup → guard (`cond`) → action (mutate ctx) → exit current → set new → entry next → notify.
> - **Order matters:** exit → set → entry → notify.
> - **Invalid transitions throw** — surfaces bugs. Optional `'*'` catch-all.
> - **Guards reject** without state change; **actions mutate `context`** before transition.
> - **Subscribers** see `{ state, context }` snapshots.
> - **Persistence** = serialize `{ state, context }`; restore by setting both.
> - **Graduate to xstate** for hierarchical, parallel, visualizer, time-based.
> - **Family:** order flows, auth, upload phases, mode toggles, request-state machines.
> - **Trap:** boolean flags (combinatorial explosion); scattered transitions; wrong lifecycle order; async entry without await.

---

**Related:** [counter-ii.md](./counter-ii.md) · [factory-with-injected-deps.md](./factory-with-injected-deps.md) · [`10-machine-coding-patterns/mini-state-machine.md`](../10-machine-coding-patterns/mini-state-machine.md) · [`10-machine-coding-patterns/observable-subject.md`](../10-machine-coding-patterns/observable-subject.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
