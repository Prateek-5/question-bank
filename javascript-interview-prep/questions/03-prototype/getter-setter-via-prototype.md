# Getter / setter via prototype

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [defineproperty-vs-assignment.md](./defineproperty-vs-assignment.md), [prototype-chain-inheritance.md](./prototype-chain-inheritance.md)
>
> **Source:** ES5 accessor properties; ES2015 class syntax. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Accessor properties (getters/setters) look like data but run code. Where do they live? How do they interact with the prototype chain?

**Verification examples**

```js
class Temperature {
  constructor(celsius) { this._c = celsius; }
  get celsius() { return this._c; }
  set celsius(v) { if (v < -273.15) throw new RangeError(); this._c = v; }
  get fahrenheit() { return this._c * 9/5 + 32; }
  set fahrenheit(f) { this._c = (f - 32) * 5/9; }
}

const t = new Temperature(20);
t.celsius;                                                                // 20 (getter runs)
t.fahrenheit;                                                             // 68
t.fahrenheit = 100;                                                       // setter runs
t.celsius;                                                                // ~37.78
```

**Constraints**
- Getters/setters live on `prototype` (not instance).
- Accessor descriptor has `get`/`set`, NOT `value`/`writable`.
- `instance.hasOwnProperty('celsius')` is `false`.
- Shadowing trap: `instance.celsius = 50` sets data property (overrides accessor).

---

## 2. Plain-English restatement

`get foo() {...}` and `set foo(v) {...}` define a computed property — looks like data on read/write but runs your function. Lives on prototype. `JSON.stringify` runs the getter. `Object.assign` calls the getter and stores its return as a data property (loses the accessor).

---

## 3. Why this matters in interviews

Property-descriptor literacy + lookup mechanics + practical patterns (validation, derived values, lazy init).

---

## 4. Mental model

```
   class Temperature {
     get fahrenheit() { ... }
     set fahrenheit(f) { ... }
   }
   
   Lives on Temperature.prototype as accessor descriptor:
     { get: <fn>, set: <fn>, enumerable: false, configurable: true }
   
   Property lookup on instance:
     instance.fahrenheit:
       1. own property? no.
       2. walk to prototype → find accessor → INVOKE getter with this=instance.
   
   instance.fahrenheit = 100:
       walk to prototype → find accessor with setter → INVOKE setter.
   
   Shadowing trap:
     instance.fahrenheit = 50 normally calls setter, BUT if you do
     Object.defineProperty(instance, 'fahrenheit', {value: 50}), it
     creates a DATA property on instance, shadowing the accessor.
   
   JSON.stringify runs getters (treats as data).
   Object.assign reads getter, stores as data property.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Where does a class getter live — instance or prototype?
> 2. Does `instance.hasOwnProperty('getterName')` return `true`?
> 3. What does `JSON.stringify(t)` do with the getter?

---

## 6. Brute force — walked through

### Wrong attempt 1: getter on instance
Wastes memory (per-instance copy); class puts on prototype.

### Wrong attempt 2: `value` + `writable` for accessor
Mutually exclusive with `get`/`set`.

### Wrong attempt 3: `Object.assign` preserves accessor
Calls getter, stores result as data property; loses accessor.

---

## 7. The unlocking insight

> **Getters/setters live on prototype as accessor descriptors (`{get, set}`). Lookup walks chain; finds accessor; INVOKES function with `this=instance`. `JSON.stringify` runs getters. `Object.assign` reads then stores as data.**

Three properties:

1. **Accessor on prototype** — not instance.
2. **`{get, set}`** descriptor — mutually exclusive with `value/writable`.
3. **Shadowing** via instance data property kills accessor.

---

## 8. Solution (annotated)

```js
class Temperature {
  constructor(celsius) { this._c = celsius; }
  get celsius() { return this._c; }                                      // step 1: accessor on proto
  set celsius(v) {
    if (v < -273.15) throw new RangeError('Below absolute zero');         // step 2: validation
    this._c = v;
  }
  get fahrenheit() { return this._c * 9 / 5 + 32; }                       // step 3: derived value
  set fahrenheit(f) { this._c = (f - 32) * 5 / 9; }
}

const t = new Temperature(20);
t.celsius;                                                                // 20
t.fahrenheit;                                                             // 68 (derived)
t.fahrenheit = 100;                                                       // setter sets _c
t.celsius;                                                                // ~37.78

// Where it lives
Object.getOwnPropertyDescriptor(Temperature.prototype, 'celsius');
// { get: fn, set: fn, enumerable: false, configurable: true }
t.hasOwnProperty('celsius');                                              // false
Object.getPrototypeOf(t).hasOwnProperty('celsius');                       // true

// Lazy initialization pattern
class Cache {
  get value() {
    const v = expensiveCompute();
    Object.defineProperty(this, 'value', { value: v });                   // step 4: replace with data
    return v;
  }
}
```

**Try it yourself**

```js
// JSON.stringify runs getters
JSON.stringify(t);                                                        // {"_c":37.78}
// Note: fahrenheit/celsius getters not enumerable → not in JSON.
// To include: explicitly add to toJSON or set enumerable.

// Object.assign reads getter
const copy = Object.assign({}, { get x() { return 42; } });
copy.x;                                                                   // 42 (data property now)
Object.getOwnPropertyDescriptor(copy, 'x');
// { value: 42, writable: true, enumerable: true, configurable: true }
// Accessor LOST.

// Shadowing trap
const obj = Object.create({
  get foo() { return 'proto-getter'; },
});
obj.foo;                                                                  // 'proto-getter'
obj.foo = 'shadow';                                                       // calls setter? NO setter → silent fail in strict... wait
// Actually: no setter defined → strict mode throws "cannot set without setter"
```

---

## 9. Step-by-step dry run

```
const t = new Temperature(20):
  obj.[[Proto]] = Temperature.prototype
  Temperature.apply(obj, [20]):
    obj._c = 20.
  return obj.

t.celsius:
  Lookup celsius on t:
    own? no.
    walk to Temperature.prototype.
    found celsius accessor: {get, set}.
    INVOKE get with this=t → return t._c → 20.

t.fahrenheit:
  Walk to proto → accessor → invoke getter → t._c * 9/5 + 32 → 68.

t.fahrenheit = 100:
  Walk to proto → accessor → invoke SETTER with this=t, args=[100]:
    this._c = (100 - 32) * 5/9 = 37.78.
  No return.

JSON.stringify(t):
  Iterate own ENUMERABLE properties.
  Own: { _c: 37.78 }.
  Accessors on proto: NOT included (not own).
  Result: '{"_c":37.78}'.
```

---

## 10. Common confusion + traps

1. **Accessor on instance** — class puts on prototype.
2. **`hasOwnProperty(getter)`** false on instance.
3. **`Object.assign` preserves accessor** — no, stores result as data.
4. **`JSON.stringify` ignores getters** — calls them (if enumerable).
5. **No setter → assignment** — strict TypeError; sloppy silent.
6. **Computed property keys for getter** — `get [name]() {}` works.
7. **Symbol-keyed accessor** — works, not in `for...in`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Lazy initialization
Getter computes on first access, replaces itself with `defineProperty` data property.

### Variant 2 — Validation in setter
Setter throws on invalid input; getter just returns.

### Variant 3 — `Object.assign` quirk
Reads getter, stores as data — loses accessor.

### Variant 4 — Computed key accessor
`get [Symbol.toPrimitive]() {}` for custom coercion.

### Variant 5 — Proxy `get`/`set` traps
Intercept all property access, including accessors.

---

## 12. How to think aloud

> "Getters/setters are ACCESSOR properties — `get foo() {}` and `set foo(v) {}`. They live on the PROTOTYPE (when defined in a class), not the instance. Descriptor has `{get, set, enumerable, configurable}` — NO value/writable (mutually exclusive). Property lookup on instance walks to prototype, finds the accessor, and INVOKES the getter with `this=instance`. Similarly for assignment: walks to prototype, finds accessor, invokes setter. Use cases: validation in setter, derived values in getter (e.g., `fahrenheit` from `_c`), lazy init (getter computes once, replaces self via `defineProperty`), instrumentation. Gotchas: `instance.hasOwnProperty(getter)` is false; `Object.assign` reads getter then stores as data property (LOSES accessor); `JSON.stringify` runs getters (if enumerable). Trap: putting accessor on instance (per-instance memory); mixing get/set with value/writable; expecting Object.assign to preserve."

---

## 13. 60-second revision

> - **Accessor on PROTOTYPE** (when defined in class).
> - **Descriptor:** `{get, set, enumerable, configurable}` — NO value/writable.
> - **Lookup:** walk chain → find accessor → INVOKE function with `this=instance`.
> - **Uses:** validation (setter), derived value (getter), lazy init, instrumentation.
> - **`instance.hasOwnProperty(accessor)`** false.
> - **`JSON.stringify`** runs getter (if enumerable).
> - **`Object.assign`** reads getter, stores as DATA property (loses accessor).
> - **Trap:** instance vs proto location; mixing get/set + value/writable; Object.assign preservation.

---

**Related:** [defineproperty-vs-assignment.md](./defineproperty-vs-assignment.md) · [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [class-to-prototype-desugar.md](./class-to-prototype-desugar.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
