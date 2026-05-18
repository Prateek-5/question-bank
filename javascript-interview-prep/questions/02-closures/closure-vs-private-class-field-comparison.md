# Closure vs `#`-Private Class Field — Comparison

## Source / Origin
- ES2022 `#private` fields; lifelong closure-based privacy.
- Asked at: Stripe, Atlassian, Razorpay — output-prediction and "design choice" questions.
- Concept reference: `concepts/closures.md`, `concepts/prototype.md`.

## Why this question matters in interviews
"Make this counter private." Two right answers — closure factory or `#field` in a class. Senior bar: you can list 6+ axes of difference (inheritance, performance, syntax, debuggability, memory, when to pick which) and reason about each.

## Concepts involved

### Syntax to lock in
```js
// Closure
function createCounter() {
  let n = 0;
  return { inc: () => ++n, peek: () => n };
}
const c = createCounter();
c.n;            // undefined (truly private)

// #private class field
class Counter {
  #n = 0;
  inc() { return ++this.#n; }
  peek() { return this.#n; }
}
const c2 = new Counter();
c2.#n;          // SyntaxError outside class body
```

### Comparison axes
1. **Visibility**: both invisible from outside (closure literally unreachable; #field syntax-checked).
2. **Inheritance**: `#` fields are *not inherited* by subclasses' code. Subclass methods can't read parent's `#x`. Closure naturally isolates.
3. **Methods sharing**: class methods live on the prototype (one copy); closure methods are per-instance (more memory).
4. **Performance**: # fields are slot-based in V8 — fast property access. Closures have slightly more overhead per call.
5. **`this`**: closure has no `this` confusion; class methods need binding when passed around.
6. **Debuggability**: # fields visible in DevTools (with the `#` prefix); closure variables visible only when scope is paused.
7. **JSON/structured clone**: # fields are not serialized; neither are closure vars. Both opaque.
8. **Reflection**: `Object.keys`, `Reflect.ownKeys` don't see # fields nor closure vars.

## Mental Model

```
   Closure factory                Class with #private
   ─────────────────              ───────────────────
   one closure per instance       one prototype, many instances
   each instance owns methods     methods shared on prototype
   methods see env via [[Env]]    methods see #fields via slot table
   no `this`; methods bound       `this` binds to instance
   memory: O(instances * methods) memory: O(instances * fields)
```

## Why interviewers care

- **Tradeoff fluency.** Multiple right answers; choosing well is senior.
- **Modern JS literacy** — # fields are recent (2022).
- **OOP vs functional preference** — closures = functional style; classes = OOP.

## Common confusion

- **"# fields are public if accessed via brackets."** They're not. `obj['#x']` looks for a property named `#x`; the private slot is invisible.
- **"Closures are slower."** Negligibly for normal use; per-instance methods add memory.
- **"Classes always need a constructor."** Not with field initializers — `class C { #n = 0 }` works.
- **"# fields work in TypeScript."** Yes, but TS also has `private` keyword which is *compile-time only* (no runtime privacy).

## Brute force / typical answers

Either works. Pick by use case.

## Optimal — the decision tree

```
Need inheritance / prototype methods / many instances → class with #
Need a one-shot factory / no `this` / module-pattern → closure
Need compatibility with old environments (pre-2022) → closure
Need to share methods across instances cheaply → class (prototype)
Need true privacy in tests too (no reflection) → both work
Building reactive primitives → either; closure feels more natural
```

## Solution

```js
// Closure factory — module pattern
export function createTodoStore() {
  let items = [];
  let listeners = new Set();
  return {
    add(t) { items = [...items, t]; emit(); },
    remove(id) { items = items.filter(i => i.id !== id); emit(); },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    snapshot() { return items.slice(); },
  };
  function emit() { listeners.forEach(fn => fn()); }
}

// Class with # — many instances
class TodoStore {
  #items = [];
  #listeners = new Set();
  add(t) { this.#items.push(t); this.#emit(); }
  remove(id) { this.#items = this.#items.filter(i => i.id !== id); this.#emit(); }
  subscribe(fn) { this.#listeners.add(fn); return () => this.#listeners.delete(fn); }
  snapshot() { return this.#items.slice(); }
  #emit() { this.#listeners.forEach(fn => fn()); }
}

// 1000 stores
// Closure: 1000 closures + 4 methods each = 4000 function objects
// Class:   1000 instances + 4 prototype methods shared = 4 function objects
```

## Dry run

```
class Counter { #n=0; inc(){return ++this.#n} }
new Counter() → instance with slot #n=0
inst.inc() → looks up Counter.prototype.inc → method finds #n in slot table → increments → returns 1

createCounter() → returns object with inc/peek closures over local n
counter.inc() → reads its private `n` slot in closure env → increments → returns 1

Compare allocation:
  100 new Counter() instances: each has 1 slot for #n; 1 shared prototype with inc/peek
  100 createCounter() instances: each has its own inc + peek closure objects
  → closure variant uses ~2x function-object memory
```

## How to think aloud

> "Both achieve true privacy. Closure factories are functional-style: per-instance methods, no `this`, simpler mental model for one-off factories. # class fields share methods on the prototype: less memory for many instances, inheritance support, but introduce `this`. I'd pick closure for module-pattern singletons and small factories; class for libraries that consumers extend or instantiate many times. TS `private` keyword is compile-time only — not real privacy."

## Important takeaways

- **Both give true privacy.**
- **Closure**: per-instance methods, no `this`, functional.
- **Class `#`**: prototype-shared methods, supports inheritance.
- **Memory**: closure is `O(instances × methods)`; class is `O(instances × fields)`.
- **TS `private` ≠ runtime privacy** — `#` is the only runtime guarantee.
- **No reflection** sees either.

## Variants

- **WeakMap-based privacy** (pre-2022 alternative) — `_privates.get(this).x`.
- **Symbol-keyed properties** — discoverable via `Object.getOwnPropertySymbols`; not truly private.
- **Module-scoped state + factory functions** — closure-equivalent, often used in libraries.

## Revision notes

```
Closure                       # Private Class Field
───────                       ─────────────────────
factory: createX()            class X { #x = 0 }
methods per instance           methods on prototype (shared)
no `this`                      requires `this`
memory: instances × methods    memory: instances × fields
not inherited (natural)        not inherited by subclass (by design)
debuggable when paused         visible in DevTools as `#x`
older browsers                 ES2022+ only

PICK:
  closure → module-pattern, one-off factory, functional style
  # field → many instances, inheritance, OOP style
  TS `private` = compile-time only; not runtime privacy
```
