# Implement a Mini Finite State Machine

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [observable-subject.md](./observable-subject.md), [event-emitter.md](./event-emitter.md)
>
> **Source:** XState (the canonical JS state-machine library), GoF State pattern. Order workflows, retry circuits, connection lifecycles, auth flows.

---

## 1. Problem statement

**Signature**
```ts
function createMachine(config: {
  initial: string;
  states: { [state: string]: { [event: string]: string | { target: string; action?: Function; cond?: Function } } };
}): {
  initial: string;
  transition(state: string, event: string, context?: any): { state: string; changed: boolean; actions: Function[] };
  interpret(context?: any): { state; context; send(event); subscribe(fn): () => void };
};
```

**Input / Output examples**

| Setup                                                                                  | Behaviour                                              |
|-----------------------------------------------------------------------------------------|---------------------------------------------------------|
| order: cart → checkout → paid → shipped                                                | linear workflow                                        |
| `transition('cart', 'CHECKOUT')`                                                       | `{state: 'awaiting_payment', changed: true, actions: []}` |
| `transition('cart', 'ADD_ITEM')` (self)                                                | `{state: 'cart', changed: false, actions: []}`         |
| `transition('shipped', 'PAY')` (no PAY in shipped)                                     | `{state: 'shipped', changed: false, actions: []}`      |
| Transition with `action` → runtime runs the action                                      | side effect dispatched                                 |
| Transition with `cond: (ctx) => boolean` failing                                       | no transition                                          |
| `interpret().subscribe(fn)`                                                            | fn fires on `changed` transitions only                |

**Constraints**
- State is a string; events are strings. Config is plain data.
- `transition` is **pure**: same input → same output, no side effects.
- Runtime (`interpret`) holds state, emits to subscribers, runs actions.
- Subscriber fires only when `changed === true` (not on self/no-op transitions).

---

## 2. Plain-English restatement

A data-driven dispatch table. The machine config describes states and which events transition them to which next states. `transition(state, event)` is an O(1) lookup that returns the next state — purely. The runtime wraps this with current-state storage, side-effect execution, and subscribers. Used to model order workflows, retry circuit breakers, connection lifecycles — anything with a small set of well-defined states.

---

## 3. Why this matters in interviews

The right abstraction for **anything with a small set of well-defined states and transitions**. Probes: object-as-config, lookup dispatch, immutability of transitions, side-effect separation, the discipline to not write spaghetti `if/else` over a `status` field. Backend interviewers ask this when probing workflow modeling.

---

## 4. Mental model

```
   Config:
   ┌──────────────────────────────────────────────────────────────┐
   │ initial: 'cart'                                              │
   │ states:                                                       │
   │   cart:             { CHECKOUT: 'awaiting_payment',           │
   │                       ADD_ITEM: 'cart' }                      │
   │   awaiting_payment: { PAY: {target:'paid', action: charge},  │
   │                       CANCEL: 'cancelled' }                  │
   │   paid:             { SHIP: 'shipped' }                       │
   │   shipped:          {}      ← terminal                        │
   │   cancelled:        {}      ← terminal                        │
   └──────────────────────────────────────────────────────────────┘

   transition(state, event) = config.states[state][event]
   ↓ O(1) lookup ↓

   transition('cart', 'CHECKOUT')      → {state:'awaiting_payment', changed:true}
   transition('cart', 'PAY')           → {state:'cart',             changed:false}
   transition('shipped', 'PAY')        → {state:'shipped',          changed:false}

   interpret wraps:
   send(event):
     {next, changed, actions} = transition(state, event, context)
     state = next
     run actions(context, event)
     if changed: fire subscribers
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why should `transition` be pure (not run actions itself)?
> 2. If the current state has no entry for the event, what should happen?
> 3. Why fire subscribers only on `changed: true` transitions?

---

## 6. Brute force — walked through

### Wrong attempt 1: giant `switch` statement
```js
function transition(state, event) {
  switch (state) {
    case 'cart': switch (event) { case 'CHECKOUT': return 'awaiting_payment'; ... }
    ...
  }
}
```
Works mathematically but doesn't scale; can't lint, can't visualize, every new state means another case. Use data-driven config.

### Wrong attempt 2: events keyed at the top level
```js
events: { PAY: { from: 'awaiting', to: 'paid' } }
```
Works but reads worse. Workflows are designed state-by-state; `states[s][e]` is the canonical shape.

### Wrong attempt 3: actions inside `transition`
Makes it impure → hard to test, no time-travel debugging. Separate decision (pure transition) from execution (runtime).

---

## 7. The unlocking insight

> **Config is plain data. `transition(state, event)` is a pure O(1) lookup. Runtime (`interpret`) is the side-effectful wrapper — holds state, runs actions, notifies subscribers. Separating decision from execution makes the machine testable.**

Three properties:

1. **Data-driven config** — can be serialized, lint-ed, visualized.
2. **Pure `transition`** — same input → same output.
3. **Runtime separates side effects** — actions run by the interpreter, not by transition.

---

## 8. Solution (annotated)

```js
function createMachine(config) {
  if (!(config.initial in config.states)) {
    throw new Error(`Initial state '${config.initial}' not in states`);
  }

  function transition(currentState, event, context = {}) {           // step 1: pure
    const stateConfig = config.states[currentState];
    if (!stateConfig) throw new Error(`Unknown state: ${currentState}`);
    const t = stateConfig[event];
    if (t === undefined) {                                            // step 2: no transition for event
      return { state: currentState, changed: false, actions: [] };
    }
    const t2 = typeof t === 'string' ? { target: t } : t;             // normalize
    if (t2.cond && !t2.cond(context)) {                                // step 3: guards
      return { state: currentState, changed: false, actions: [] };
    }
    if (!(t2.target in config.states)) {
      throw new Error(`Transition target '${t2.target}' is not a state`);
    }
    return {
      state: t2.target,
      changed: t2.target !== currentState,
      actions: t2.action ? [t2.action] : [],
    };
  }

  function interpret(context = {}) {                                  // step 4: runtime wrapper
    let state = config.initial;
    const subs = new Set();
    return {
      get state() { return state; },
      get context() { return context; },
      send(event) {
        const { state: next, changed, actions } = transition(state, event, context);
        state = next;
        for (const action of actions) action(context, event);          // step 5: run side effects
        if (changed) for (const sub of [...subs]) sub(state, event);   // step 6: fire on changed only
        return state;
      },
      subscribe(fn) { subs.add(fn); return () => subs.delete(fn); },
    };
  }

  return { initial: config.initial, transition, interpret };
}
```

**Try it yourself**

```js
const orderMachine = createMachine({
  initial: 'cart',
  states: {
    cart:             { CHECKOUT: 'awaiting_payment', ADD_ITEM: 'cart' },
    awaiting_payment: {
      PAY:    { target: 'paid', action: (ctx) => console.log('charged', ctx.amount) },
      CANCEL: 'cancelled',
    },
    paid:             { SHIP: 'shipped' },
    shipped:          {},
    cancelled:        {},
  },
});

const order = orderMachine.interpret({ amount: 100 });
const unsub = order.subscribe((s, e) => console.log('->', s, 'via', e));

order.send('ADD_ITEM');    // self-transition; subscriber NOT fired
order.send('CHECKOUT');    // -> awaiting_payment via CHECKOUT
order.send('PAY');         // 'charged 100'; -> paid via PAY
order.send('SHIP');        // -> shipped via SHIP
order.send('PAY');         // no-op; subscriber NOT fired (terminal)
unsub();
```

---

## 9. Step-by-step dry run

```
interpret({amount:100}):
  state = 'cart'
  subs = {fn}

send('ADD_ITEM'):
  transition('cart', 'ADD_ITEM'):
    t = 'cart' (string)
    t2 = {target: 'cart'}
    return {state:'cart', changed: false, actions:[]}
  state = 'cart' (no change)
  actions: []
  changed=false → subscribers NOT fired

send('CHECKOUT'):
  transition('cart', 'CHECKOUT'):
    t = 'awaiting_payment'
    return {state:'awaiting_payment', changed:true, actions:[]}
  state = 'awaiting_payment'
  changed=true → fn('awaiting_payment', 'CHECKOUT') → log

send('PAY'):
  transition('awaiting_payment', 'PAY', {amount:100}):
    t = {target:'paid', action: charge}
    cond undefined
    return {state:'paid', changed:true, actions:[charge]}
  state = 'paid'
  run charge({amount:100}, 'PAY') → 'charged 100'
  fn('paid', 'PAY') → log

send('SHIP'):
  transition('paid', 'SHIP'):
    return {state:'shipped', changed:true, actions:[]}
  fn('shipped', 'SHIP')

send('PAY'):
  transition('shipped', 'PAY'):
    stateConfig = {}; t = undefined
    return {state:'shipped', changed:false, actions:[]}
  no-op
```

---

## 10. Common confusion + traps

1. **Actions inside `transition`** — makes it impure; hard to test.
2. **Validating only `initial`** — typo'd transition targets crash at runtime.
3. **Subscribers firing on self-transitions** — gate on `changed`.
4. **Silent transition to undefined** for unknown events — choose: return unchanged OR throw.
5. **Forgetting terminal states** — they're just states with empty event maps; no special syntax.
6. **Mutating `context` instead of returning new one** — XState convention is event-driven assigns; mention.
7. **Shared mutable state across interpreters** — separate `interpret()` calls hold separate state, but if context is a shared ref, mutations leak.

---

## 11. Senior follow-ups & variants

### Variant 1 — Guards (conditional transitions)
`{target, cond: (ctx) => bool}`. Run cond first; if false, treat as no-transition.

### Variant 2 — Entry/exit actions per state
`states[X].entry`, `states[X].exit`. Useful for resource setup/teardown (open socket on `connected`, close on `disconnected`).

### Variant 3 — Persistence
Serialize state + context to JSON; rehydrate by passing back to a fresh interpret. Required for order processing.

### Variant 4 — Hierarchical / parallel states
XState supports nested machines and parallel regions. Out of scope for mini; mention as next level.

### Variant 5 — Visualization
Walk config and emit Graphviz / Mermaid. Two-pager max; great infra-tooling demo.

### Variant 6 — Invoked services
A state spawns an async task (e.g., a fetch); the task's result emits an event that transitions further. XState `invoke`.

---

## 12. How to think aloud

> "Config is plain data: `{initial, states: {[state]: {[event]: target_or_object}}}`. `transition(state, event)` is a pure O(1) lookup that returns `{state, changed, actions}` — no side effects. Runtime (`interpret`) is the wrapper: holds state, runs actions, notifies subscribers on changed transitions only. Self-transitions (target===current) don't fire subscribers. Unknown event from current state: return unchanged, OR throw — pick one. Guards: `{target, cond}` run cond first. Entry/exit actions for resource setup/teardown. Trap: actions inside `transition` make it impure. Trap: missing target validation. Family: order workflows, retry circuits, connection lifecycles, XState."

---

## 13. 60-second revision

> - **Config:** `{initial, states: {[state]: {[event]: target | {target, action?, cond?}}}}`.
> - **`transition(state, event)`** pure; O(1) lookup; returns `{state, changed, actions}`.
> - **Runtime (`interpret`)** holds state, runs actions, fires subscribers on `changed`.
> - **Self-transitions** don't fire subscribers.
> - **Unknown event** → return unchanged (or throw, pick policy).
> - **Guards** `{target, cond}`; **entry/exit** per-state actions.
> - **Persistence:** JSON serialize state + context.
> - **Family:** order workflow, retry circuit, connection FSM, auth flow, XState.
> - **Trap:** impure transition; missing target validation; subscribers firing on no-op.

---

**Related:** [event-emitter.md](./event-emitter.md) · [observable-subject.md](./observable-subject.md) · [circuit-breaker.md](./circuit-breaker.md) · [dependency-injection-container.md](./dependency-injection-container.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
