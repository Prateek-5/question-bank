# Implement a Mini Finite State Machine

## Source
- Classic computer-science machine-coding question (XState is the canonical JS library; FAANG senior interviews often ask the mini-version).
- Adapted from BFE.dev / GreatFrontEnd state-machine problems.

## Why this question matters in interviews
State machines are the right abstraction for **anything with a small set of well-defined states and transitions**: order workflows (cart → checkout → paid → shipped), retry circuits (closed → open → half-open), connection lifecycles (idle → connecting → connected → reconnecting), authentication flows, feature flags with gradual rollout. Implementing one in 30-50 lines tests **object-as-config**, **lookup-based dispatch**, **immutability of transitions**, **event emission for side effects**, and shows the interviewer you've seen the "spaghetti `if/else` over a `status` field" antipattern and know the cure. Backend interviewers ask this when probing whether you can model business workflows cleanly.

## Concepts involved

### Syntax to lock in
```js
const orderMachine = createMachine({
  initial: 'cart',
  states: {
    cart:       { ADD_ITEM: 'cart', CHECKOUT: 'awaiting_payment' },
    awaiting_payment: { PAY: 'paid', CANCEL: 'cancelled' },
    paid:       { SHIP: 'shipped' },
    shipped:    { /* terminal */ },
    cancelled:  { /* terminal */ },
  },
});

let state = orderMachine.initial;          // 'cart'
state = orderMachine.transition(state, 'CHECKOUT');  // 'awaiting_payment'
state = orderMachine.transition(state, 'PAY');       // 'paid'
state = orderMachine.transition(state, 'INVALID');   // throws or returns same
```

### Runtime / engine behavior
- State is just a **string** (or symbol). Events are strings. The machine config is a plain object — totally serializable, which means you can persist a machine definition to disk / DB / version control.
- `transition(state, event)` is a **pure function**: same input → same output, no side effects. This is what makes state machines composable and testable.
- The lookup `config.states[state][event]` is O(1). The whole machine is a 2D map.
- Side effects (actions) are decoupled: when transitioning, emit an event or return an `{nextState, action}` tuple. The caller runs the action — the machine just decides. This is the XState pattern.
- Subscribers: similar to Observable / Subject, you can `subscribe(state => ...)` to react to state changes. Useful for UI rerendering and logging.

### Edge cases (these are the interview traps)
1. **Invalid event from current state** — two policies: (a) throw to surface bugs, or (b) return current state unchanged ("ignore unknown events"). Pick one and state it; XState ignores by default.
2. **Self-transitions** — `cart -> ADD_ITEM -> cart`. The state name didn't change but it's still a transition. Should the action fire? Yes — that's the point. Some libs distinguish "internal" (no exit/entry) vs "external" (re-entry) transitions.
3. **Terminal states** — states with no outgoing transitions. Once you enter, you stay. Don't crash on lookup of `config.states[terminal][anyEvent]` — handle undefined.
4. **Guards (conditional transitions)** — sometimes the same event from the same state goes to different next states depending on context. Extend the transition definition: `{ target: 'x', cond: (ctx) => ctx.amount > 0 }`. Common in real workflows.
5. **Context** — XState has a separate "extended state" (a JSON object alongside the named state). The state is "paid," the context is `{ amount: 100, currency: 'USD' }`. Mention this as an extension.
6. **Action side effects** — running an action inside `transition` makes it impure. Better: `transition` returns `{ nextState, actions: [...] }` and the runtime runs the actions. Keeps `transition` testable.
7. **Hierarchical / parallel states** — XState supports nested machines and parallel regions. Out of scope for the mini version; mention as the next level.
8. **Initial state must be a valid state name** — validate this in `createMachine`. Otherwise the first transition crashes.

## Brute force approach
"I'll write a giant switch statement on `state` with nested switches on `event`." Works, but doesn't scale — every new state means another case, every new event another sub-case, and you can't introspect or visualize the machine. The data-driven object-config approach is the canonical alternative: same expressiveness, but the machine is **data**, not code, so you can lint it, visualize it (XState's inspector tool), and even synthesize tests from it.

Another wrong path: putting transitions on the **events** instead of the **states** (`events: { PAY: { from: 'awaiting', to: 'paid' } }`). Works mathematically but reads worse; `states[s][e]` is the canonical shape because real workflows are designed state-by-state, not event-by-event.

## Optimal approach
Plain-object config: `{ initial, states: { [stateName]: { [eventName]: target } } }`. `transition(state, event)` is an O(1) lookup. Build a subscriber list for state-change events. Add action support via `{ target, action }` tuple.

## Solution (JavaScript)

```js
/**
 * Mini finite state machine.
 *
 * @param {object} config
 * @param {string} config.initial
 * @param {Object<string, Object<string, string | { target: string, action?: Function, cond?: Function }>>} config.states
 */
function createMachine(config) {
  if (!(config.initial in config.states)) {
    throw new Error(`Initial state '${config.initial}' not in states`);
  }

  function transition(currentState, event, context = {}) {
    const stateConfig = config.states[currentState];
    if (!stateConfig) throw new Error(`Unknown state: ${currentState}`);
    const t = stateConfig[event];
    if (t === undefined) return { state: currentState, changed: false, actions: [] };

    // Normalize to {target, action, cond}
    const t2 = typeof t === 'string' ? { target: t } : t;
    if (t2.cond && !t2.cond(context)) {
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

  // Runtime wrapper — holds state, emits to subscribers, runs actions.
  function interpret(context = {}) {
    let state = config.initial;
    const subs = new Set();

    return {
      get state() { return state; },
      get context() { return context; },
      send(event) {
        const { state: next, changed, actions } = transition(state, event, context);
        state = next;
        for (const action of actions) action(context, event);
        if (changed) for (const sub of [...subs]) sub(state, event);
        return state;
      },
      subscribe(fn) { subs.add(fn); return () => subs.delete(fn); },
    };
  }

  return { initial: config.initial, transition, interpret };
}
```

## Step-by-step dry run

Input:
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

order.send('ADD_ITEM');   // cart -> cart (self-transition; subscriber NOT fired because changed=false)
order.send('CHECKOUT');   // cart -> awaiting_payment. logs '-> awaiting_payment via CHECKOUT'.
order.send('PAY');        // awaiting_payment -> paid. action logs 'charged 100'. subscriber logs '-> paid via PAY'.
order.send('SHIP');       // paid -> shipped.
order.send('PAY');        // shipped[PAY] undefined → no-op, state stays 'shipped'.
unsub();
```

Trace:
- `interpret({amount:100})`: state='cart', subs=∅, context={amount:100}.
- `subscribe(fn)`: subs={fn}.
- `send('ADD_ITEM')`: `transition('cart', 'ADD_ITEM')` → target='cart', changed=false. State stays 'cart'. No subscribers fired.
- `send('CHECKOUT')`: target='awaiting_payment', changed=true. State='awaiting_payment'. Subscriber logs.
- `send('PAY')`: t = `{target:'paid', action}`. cond undefined (skip). Run action(context, 'PAY') → 'charged 100'. State='paid'. Subscriber logs.
- `send('SHIP')`: target='shipped'. State='shipped'. Subscriber logs.
- `send('PAY')`: state='shipped' has no PAY in config. Return state unchanged. No subscriber fire.

## Important takeaways

**Syntax to memorize**
- Config: `{ initial, states: { [state]: { [event]: target_or_object } } }`.
- `transition(state, event)` is **pure** — returns the next state. Action execution is the runtime's job.
- O(1) lookup: `config.states[state][event]`.
- Subscribe = Set of callbacks; return unsubscribe closure (same pattern as Observable/Subject).

**Patterns to reuse**
- The "data-driven object dispatch" pattern: same shape as reducers (Redux), route tables (Express), parser action tables (compiler).
- Pure `transition` + runtime `interpret` separation: makes the machine testable in isolation. Same idea as functional core + imperative shell.

**Common mistakes**
- Mixing actions into `transition` — makes it impure, hard to test, hard to time-travel-debug.
- Validating only `initial` in the state set, not transition targets. A typo'd `target: 'paif'` silently crashes at runtime.
- Always firing subscribers (even on self-transitions or invalid events). Gate on `changed`.
- Not handling unknown event from current state — throwing is OK, returning unchanged is OK, **silently transitioning to undefined** is not.
- Forgetting that terminal states are just states with empty transition maps. No special syntax needed.

**Related questions**
- Observable/Subject (the subscribe API is identical).
- Reducer pattern (Redux) — state + action → new state.
- XState (next-level: hierarchy, parallel states, history, invoked services).
- Retry circuit breaker (closed/open/half-open is a 3-state machine).

## Variants

1. **Guards / conditions** — transition is `{ target, cond: (ctx) => bool }`. Run cond first; if false, treat as no-transition.

2. **Actions on entry / exit** — separate from transition actions. When entering state X, run `states[X].entry`. When leaving, `states[X].exit`. Useful for resource setup/teardown (open socket on connected, close on disconnected).

3. **Persistence** — since state is just a string, serialize to disk: `JSON.stringify({state, context})`. Rehydrate by passing the string back to a fresh interpret. Real workflows (order processing) need this.

4. **Visualization** — given the config object, walk it and emit a Graphviz / Mermaid diagram. Two-pager max; great talking point for "I write infra tooling."

## Revision notes

> **Mini state machine — 60 second recap**
> - Config: `{ initial, states: { [state]: { [event]: target } } }`. State + event are strings.
> - `transition(state, event)` is pure: O(1) lookup, returns next state.
> - Runtime (`interpret`) holds the state, emits subscribers, runs actions.
> - Self-transitions (target === current) don't fire subscribers (gate on `changed`).
> - Invalid event → return current state (no-op) OR throw. Pick a policy.
> - Guards: `{target, cond}`. Actions: `{target, action}`. Entry/exit on the state itself.
> - Trap: actions inside `transition` make it impure. Subscribers firing on self-transitions. Missing target validation.
> - Reuse: order workflows, retry circuits, connection lifecycles, auth flows, feature rollouts.
