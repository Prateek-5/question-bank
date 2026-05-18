# Closure as a Finite State Machine

## Source / Origin
- Classic "rolling your own FSM" pattern; xstate's mental model.
- Asked at: Stripe, Razorpay, Atlassian (state-heavy UIs / order flows).
- Concept reference: `concepts/closures.md`, sibling `10-machine-coding-patterns/mini-state-machine.md`.

## Why this question matters in interviews
Lots of business logic *is* a state machine: order status (placed → paid → shipped → delivered), file-upload phases, auth flows. Closure-based FSMs are tiny, dependency-free, and force you to enumerate transitions explicitly. Senior bar: you handle invalid transitions cleanly, support entry/exit hooks, and articulate when to graduate to xstate.

## Concepts involved

### Syntax to lock in
```js
function createMachine({ initial, states }) {
  let current = initial;
  const listeners = new Set();

  return {
    get state() { return current; },
    send(event) {
      const def = states[current];
      const next = def?.on?.[event];
      if (!next) throw new Error(`Invalid transition: ${current} -[${event}]→ ?`);
      if (def.exit) def.exit();
      current = next;
      if (states[next].entry) states[next].entry();
      listeners.forEach(fn => fn(current));
    },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}

const traffic = createMachine({
  initial: 'red',
  states: {
    red:    { on: { TIMER: 'green' }, entry: () => console.log('stop')},
    green:  { on: { TIMER: 'yellow' }, entry: () => console.log('go')},
    yellow: { on: { TIMER: 'red' }, entry: () => console.log('slow')},
  },
});
traffic.send('TIMER');   // green; logs 'go'
```

### Edge cases / traps
1. **Invalid transition.** Throw vs silently ignore — pick a policy. Throwing surfaces bugs early.
2. **Entry/exit ordering** — exit current → set state → entry next. Otherwise `state` is inconsistent during hooks.
3. **Re-entrant transitions** — same state to itself (`send TIMER` in red goes to red). Decide if entry hook re-fires.
4. **Async transitions** — `entry` may be async; await before calling listeners or let it run in background.
5. **Guards (conditional transitions)** — extend `on[event]` to `{ target, cond }` or array.
6. **State data** — pure FSM has no payload; "extended state machine" has a context object updated on transition.
7. **Snapshot/restore** — persist `current` and rehydrate; useful for resumable flows.

## Mental Model

```
   ┌──── red ────┐ TIMER  ┌──── green ────┐ TIMER  ┌──── yellow ────┐
   │ entry:stop  │ ────▶  │ entry:go      │ ────▶  │ entry:slow      │ TIMER
   └─────────────┘        └───────────────┘        └────────────────┘ ─┐
        ▲                                                             │
        └─────────────────────────────────────────────────────────────┘

   closure state: { current, listeners }
   send(event): exit current → set current=next → entry next → notify
```

## Why interviewers care

- **State-modeling discipline** — explicit transitions kill "impossible state" bugs.
- **Hook ordering** — exit/enter sequencing.
- **Closure encapsulation.**

## Common confusion

- **"Use boolean flags instead."** A boolean for each state explodes combinatorially; you get `isLoading && isError && isSuccess` confusion. FSM is mutually exclusive.
- **"Use a switch statement."** Same effect but transition rules are scattered through code.
- **"Async transitions are fine to fire-and-forget."** They can race; listeners may see old `current`.

## Brute force

```js
let status = 'pending';
function approve() { status = 'approved'; }
function reject()  { status = 'rejected'; }
function ship()    { if (status !== 'approved') throw; status = 'shipped'; }
// transitions scattered, error-prone, no observability
```

## Optimal approach

Single source of truth: a transitions table. `send(event)` looks up and applies; impossible transitions throw.

## Solution

```js
function createMachine({ initial, states, context = {} }) {
  let current = initial;
  let ctx = { ...context };
  const listeners = new Set();

  function set(state) {
    const cur = states[current];
    if (cur?.exit) cur.exit(ctx);
    current = state;
    if (states[state].entry) states[state].entry(ctx);
    listeners.forEach(fn => fn({ state: current, context: ctx }));
  }

  return {
    get state() { return current; },
    get context() { return ctx; },
    send(event, payload) {
      const def = states[current];
      const trans = def?.on?.[event];
      if (!trans) {
        if (def?.on?.['*']) return; // catch-all
        throw new Error(`No transition from ${current} on ${event}`);
      }
      const next = typeof trans === 'string' ? trans : trans.target;
      if (typeof trans === 'object' && trans.cond && !trans.cond(ctx, payload)) {
        throw new Error(`Guard failed: ${current} -[${event}]→ ${next}`);
      }
      if (typeof trans === 'object' && trans.actions) trans.actions(ctx, payload);
      set(next);
    },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    serialize() { return { state: current, context: ctx }; },
    restore(snap) { current = snap.state; ctx = { ...snap.context }; },
  };
}

// Order flow
const order = createMachine({
  initial: 'placed',
  context: { paid: 0 },
  states: {
    placed: {
      on: {
        PAY: { target: 'paid', actions: (ctx, p) => { ctx.paid = p.amount; }, cond: (ctx, p) => p.amount > 0 },
        CANCEL: 'cancelled',
      },
    },
    paid:      { on: { SHIP: 'shipped', REFUND: 'refunded' } },
    shipped:   { on: { DELIVER: 'delivered' } },
    delivered: { entry: () => console.log('done') },
    cancelled: {}, refunded: {},
  },
});

order.send('PAY', { amount: 100 });
order.send('SHIP');
order.send('DELIVER');
```

## Dry run

```
state=placed, ctx={paid:0}
send('PAY', {amount:100})
  trans = {target:'paid', actions, cond}
  cond(ctx, {amount:100}) → 100 > 0 → true
  actions(ctx, {amount:100}) → ctx.paid=100
  set('paid'):
    exit placed (none)
    current = 'paid'
    entry paid (none)
    notify listeners
state=paid, ctx={paid:100}
```

Invalid:

```
send('DELIVER') from 'placed'
  states['placed'].on['DELIVER'] → undefined → throw
```

## How to think aloud

> "Closure-encapsulated FSM: enclose `current` and `context`. `send(event)` looks up the transition in a table; impossible transitions throw to catch bugs. Hooks: exit current → set new → entry next, then notify. Guards (`cond`) gate; actions mutate context. Subscribe for reactive UIs. For complex graphs I'd reach for xstate — visualizer, statecharts, hierarchical states. For 80% of business state, this hand-rolled is enough."

## Important takeaways

- **Transitions in a TABLE**, not scattered.
- **Throw on invalid transition** to surface bugs.
- **Exit → set → entry → notify** ordering.
- **Guards + actions** extend to "extended FSM."
- **Closure hides state**; only `send`/`subscribe`/`state` exposed.
- **Graduate to xstate** for hierarchical/parallel states.

## Variants

- **Hierarchical (statecharts)** — nested states; xstate territory.
- **Parallel states** — multiple regions active simultaneously.
- **Async actions** — `actions: async (ctx) => {}`.
- **Persistence** — `serialize`/`restore` for resumable flows.
- **History states** — return to last sub-state on re-entry.

## Revision notes

```
createMachine({initial, states, context}):
  closure: current, ctx, listeners
  send(event, payload):
    lookup transition; check guard; run actions; transition
    exit-current → set → entry-next → notify
  subscribe(fn); serialize(); restore(snap)

PATTERN:
  states: { name: { on: { EVENT: 'target' | { target, cond, actions } }, entry, exit } }

USES: order flows, auth, upload phases, mode toggles
GRADUATE: xstate for hierarchical/parallel/visualizer
```
