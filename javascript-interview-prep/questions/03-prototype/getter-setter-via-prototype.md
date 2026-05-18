# Getter / Setter via Prototype

## Source / Origin
- ES5 accessor properties (`Object.defineProperty`); ES2015 class syntax.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/prototype.md`.

## Why this question matters in interviews
Properties that "look like data but run code." Used for derived values, validation, lazy init, instrumentation. Senior bar: you know they live on the prototype (not the instance), how to define them via `Object.defineProperty`, and the performance trap (they can prevent V8's hidden-class optimizations if abused).

## Concepts involved

### Syntax to lock in
```js
class Temperature {
  constructor(celsius) { this._c = celsius; }
  get celsius() { return this._c; }
  set celsius(v) { if (v < -273.15) throw new RangeError(); this._c = v; }
  get fahrenheit() { return this._c * 9/5 + 32; }
  set fahrenheit(f) { this._c = (f - 32) * 5/9; }
}

const t = new Temperature(20);
t.celsius;          // 20
t.fahrenheit;       // 68
t.fahrenheit = 100; // setter runs
t.celsius;          // ~37.78
```

### Edge cases / traps
1. **Getters/setters live on prototype**, not instance. `Object.getOwnPropertyDescriptor(Temperature.prototype, 'celsius')` returns the accessor.
2. **No corresponding `value`** — descriptor has `get`/`set`, not `value`.
3. **No `writable`** field — `writable` is only for data descriptors.
4. **Shadowing trap** — `instance.celsius = 50` doesn't call the setter if the instance has its own `celsius` data property (which would have to be set explicitly via `defineProperty`).
5. **`hasOwnProperty` is false** for accessor on prototype — `instance.hasOwnProperty('celsius')` is `false`; `'celsius' in instance` is `true`.
6. **`Object.assign` reads but doesn't copy accessors** — copies the *value* from getter as a data property.
7. **JSON.stringify** runs getters (treats them as data).
8. **Lazy initialization** pattern — getter computes on first access, replaces self with data property.

## Mental Model

```
   class Temperature {
     get fahrenheit() { ... }
   }

   prototype chain:
     instance → Temperature.prototype  ──┐
                                          ├──► fahrenheit accessor descriptor: {get, set}
     instance does NOT have its own 'fahrenheit' property

   instance.fahrenheit:
     property lookup: not on instance → look on prototype → find accessor → invoke getter
     getter runs with `this` = instance
```

## Why interviewers care

- **Property descriptor knowledge** — accessor vs data.
- **Lookup mechanics** — prototype chain walk.
- **API design** — getters can simplify or obscure (debate-worthy).

## Common confusion

- **"Setter call is `obj.x(value)`."** It's `obj.x = value`.
- **"Getters cost the same as fields."** They cost more — V8 sometimes deopts.
- **"Defining `obj.x = ...` after a setter on prototype overrides it."** It does — creates an instance data property, shadows the accessor. Use `Object.defineProperty(obj, 'x', { value: ..., writable, ... })` carefully.
- **"`for...in` skips accessors."** No — enumerable accessors show up; non-enumerable don't.

## Brute force

Plain method `get_x() / set_x(v)` — no syntactic sugar. Loses the data-like access.

## Optimal approach

Class `get`/`set` syntax — defines accessors on the prototype. For runtime definition, `Object.defineProperty`.

## Solution

```js
// Validating setter
class User {
  #email;
  get email() { return this.#email; }
  set email(v) {
    if (!/.+@.+/.test(v)) throw new TypeError('invalid email');
    this.#email = v;
  }
}

// Lazy initialization — common pattern
class Config {
  get schema() {
    const computed = expensive();
    Object.defineProperty(this, 'schema', {
      value: computed, writable: false, configurable: false, enumerable: true,
    });
    return computed;
  }
}
const c = new Config();
c.schema;   // runs expensive(); replaces with data property
c.schema;   // hits data property directly (no recompute)

// Object.defineProperty for plain objects
const obj = {};
Object.defineProperty(obj, 'fullName', {
  get() { return `${this.first} ${this.last}`; },
  set(v) { [this.first, this.last] = v.split(' '); },
  enumerable: true, configurable: true,
});
obj.fullName = 'jane doe';
obj.first;   // 'jane'

// Reactive accessor (toy)
function reactive(obj) {
  const listeners = new Map();
  const proxy = {};
  for (const key of Object.keys(obj)) {
    let v = obj[key];
    Object.defineProperty(proxy, key, {
      get() { return v; },
      set(nv) { v = nv; (listeners.get(key) || []).forEach(fn => fn(nv)); },
      enumerable: true,
    });
  }
  proxy.on = (key, fn) => {
    if (!listeners.has(key)) listeners.set(key, []);
    listeners.get(key).push(fn);
  };
  return proxy;
}
```

## Dry run

```
class T { get x() { return 42 } }
const t = new T();

t.x:
  lookup t.x → no own property
  walk prototype → T.prototype has 'x' as accessor descriptor
  invoke descriptor.get with this=t → 42

Object.getOwnPropertyDescriptor(T.prototype, 'x')
  → { get: [Function], set: undefined, enumerable: false, configurable: true }
```

Shadowing:

```
t.x = 99;          // assignment with no setter → strict: TypeError; sloppy: silently fails
                    // BUT if T.prototype.x has both get and set, runs setter
                    // If only get, no set: strict-throws, sloppy-ignores
```

If you forcibly set:

```
Object.defineProperty(t, 'x', { value: 99, writable: true });
t.x;   // 99 — instance data property shadows prototype accessor
```

## How to think aloud

> "Getter/setter — accessor property on the prototype. `instance.x` looks up the chain, finds the accessor, invokes the getter with `this` = instance. They're great for derived values, validation, lazy init. Pitfalls: shadowing via plain assignment can fail silently in sloppy mode; `Object.assign` flattens them to values; V8 sometimes deopts. For one-time lazy compute, the 'replace self with data property' pattern is gold."

## Important takeaways

- **Accessors live on prototype.**
- **`get x()/set x(v)`** in class; `Object.defineProperty` for plain objects.
- **`'x' in instance`** is true; `hasOwnProperty` is false.
- **Shadowing**: explicit `defineProperty` on instance overrides.
- **Lazy init**: getter replaces self with data property on first access.
- **`Object.assign` doesn't copy accessors** (reads value as data).

## Variants

- **Private + getter** — `#field` + `get x() { return this.#field; }` is the canonical encapsulation.
- **`Proxy`** for catch-all reactivity (instead of per-field accessors).
- **`Object.defineProperties`** for batch.
- **Static accessors** — `static get version() { return '1.0' }`.

## Revision notes

```
class C {
  get x() { return ... }      // accessor on prototype
  set x(v) { ... }
}

Object.defineProperty(obj, 'x', { get, set, enumerable, configurable })

descriptor flavors:
  data: {value, writable, enumerable, configurable}
  accessor: {get, set, enumerable, configurable}
  (cannot mix value+get)

USES:
  - derived values: get fullName()
  - validation in setter
  - lazy init: replace self with data property
  - reactive primitives (toy; usually Proxy for breadth)

TRAPS:
  - Object.assign flattens accessors to values
  - shadow by instance data property (defineProperty)
  - V8 deopt for hot accessors
```
