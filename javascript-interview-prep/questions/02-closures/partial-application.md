# Build `partial(fn, ...presetArgs)` — pre-bind arguments via closure

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [counter.md](./counter.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Classic FP problem (lodash `_.partial`, Ramda `R.partial`).

---

## 1. Problem statement

**Signature**
```ts
function partial<F extends (...args: any[]) => any>(
  fn: F,
  ...presetArgs: any[]
): (...laterArgs: any[]) => ReturnType<F>;
```

**Input / Output examples**

| Setup                                                          | Sequence of calls     | Output             |
|----------------------------------------------------------------|------------------------|--------------------|
| `const greet = (g, n) => \`${g}, ${n}!\``; `const hi = partial(greet, 'Hi')` | `hi('Maya'); hi('Sam')` | `"Hi, Maya!"`, `"Hi, Sam!"` |
| `const subtract = (a, b) => a - b`; `const from10 = partial(subtract, 10)` | `from10(3)` | `7`                |
| `partial(fn, _, 'B')('A')` (with placeholder)                  | one call               | `fn('A', 'B')`     |
| Multiple wrappers from one preset                             | `apiCall(42); apiCall(43);` | each fresh `laterArgs`, shared `presetArgs` |

**Constraints**
- Return a wrapper that, when called, invokes `fn` with `[...presetArgs, ...laterArgs]`.
- Forward `this`.
- Don't mutate `presetArgs` — multiple wrapper calls share it.
- (Senior) Support placeholders (`_` symbol) for non-prefix presets.

---

## 2. Plain-English restatement

Take a function `fn` and some arguments you want to fix *now*. Return a new function that, when eventually called, calls `fn` with all the preset arguments followed by whatever extra arguments you pass at call time. It's "freeze some args, plug in the rest later."

This is the **one-shot cousin of curry**: curry collects args call-by-call until arity is reached; partial fixes some args once and fires on the next call regardless of how many you give it.

---

## 3. Why this matters in interviews

Senior backend interviewers ask `partial` for two reasons. First, to test whether you can articulate the **semantic difference from curry** (not just write similar-looking code). Second, to see whether you understand the **placeholder pattern** for non-prefix presets. In practice, partial application is everywhere: pre-binding a logger's component label, fixing the first arg of a generic dispatcher, building specialized request handlers from a generic helper. `Function.prototype.bind(thisArg, ...args)` is literally partial application + `this` binding.

---

## 4. Mental model

A **template machine with some slots pre-filled**. You hand over a recipe (`fn`) and pre-fill a few of the slots (`presetArgs`); the machine hands you back a partially-prepared template. To run the recipe, you fill in the remaining slots (`laterArgs`) and turn the crank.

```
   partial(greet, 'Hi')
     │
     ├── frozen slots: [presetArgs = ['Hi']]
     │
     └── returns ──► wrapper(...laterArgs)
                       │
                       └── fn.apply(this, [...preset, ...later])

   hi('Maya')   →   greet('Hi', 'Maya')   →   "Hi, Maya!"
   hi('Sam')    →   greet('Hi', 'Sam')    →   "Hi, Sam!"
```

The closure holds **one** preset array. Every wrapper call concatenates fresh `laterArgs` onto it, calls `fn`, returns. No state is mutated.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's the difference between `curry(fn)(1)(2)` and `partial(fn, 1)(2)` — when do each call `fn`?
> 2. Why is `Function.prototype.bind(null, ...args)` essentially the same thing as partial?
> 3. If you needed `partial(fn, _, 'B')('A')` to call `fn('A', 'B')`, how would you implement the placeholder?

---

## 6. Brute force — walked through

### Wrong attempt 1: hardcode the binding

```js
const hi = (name) => greet('Hi', name);
```

Works for this one case. Doesn't generalize. The interview is testing the **generic factory**, not a one-off.

### Wrong attempt 2: mutate the preset array

```js
function partial(fn, ...preset) {
  return function (...later) {
    preset.push(...later);          // BUG: mutates the shared closure
    return fn.apply(this, preset);
  };
}
const hi = partial(greet, 'Hi');
hi('Maya');   // "Hi, Maya!"
hi('Sam');    // "Hi, Maya, Sam!"  ← preset has grown
```

Closure-captured arrays are shared across all wrapper invocations. Mutating poisons future calls. Always concat into a *new* array.

### Wrong attempt 3: forget `this`

```js
return function (...later) {
  return fn(...preset, ...later);   // BUG: doesn't forward `this`
};
```

Works for plain function calls. Breaks for method-style use: `obj.handler = partial(genericHandler, 'route-a'); obj.handler();` — `genericHandler` runs with `this === undefined`. Use `fn.apply(this, ...)`.

---

## 7. The unlocking insight

> **One closure-captured preset array; every call concatenates fresh later-args onto it without mutating. Forward `this` so method-style use stays intact.**

The factory closure holds the `presetArgs` array. The wrapper, on every invocation, builds a new combined args array via `[...presetArgs, ...laterArgs]` and calls `fn` through `apply` for `this`-correctness. The preset array is **read-only** from the wrapper's perspective — it's shared across all calls to the same wrapper, so mutating it would leak.

The senior twist: **placeholder support**. To allow `partial(fn, _, 'B', _)('A', 'C')` to call `fn('A', 'B', 'C')`, the wrapper has to walk the preset array, fill each `_` slot from the next available `laterArg`, and append any leftover `laterArgs` at the end. The placeholder is just a unique `Symbol` value compared with `===`.

The curry vs partial distinction is worth memorizing:

| Feature | Curry | Partial |
|---|---|---|
| Returns function until arity met | Yes | No — single wrapper |
| Knows about arity | Yes (`fn.length` or explicit) | No |
| Per-call accumulation | Yes | No |
| Placeholder support | Usually no (lodash extension) | Common |
| Use case | FP composition pipelines | Pre-binding callback args |

Curry generalizes partial: `curry(fn)(a)` ≈ `partial(fn, a)`, but `curry` keeps returning wrappers; `partial` fires `fn` on the next call no matter how many args you supply.

---

## 8. Solution (annotated)

```js
function partial(fn, ...presetArgs) {           // step 1: capture preset in closure
  return function (...laterArgs) {              // step 2: returned wrapper accepts later args
    return fn.apply(                              // step 3: forward `this` to fn
      this,
      [...presetArgs, ...laterArgs]               // step 4: NEW array; never mutate preset
    );
  };
}
```

**Placeholder-aware version**

```js
const _ = Symbol('partial.placeholder');

function partialP(fn, ...presetArgs) {           // step 1: same capture
  return function (...laterArgs) {
    let i = 0;                                    // step 2: index into laterArgs
    const finalArgs = presetArgs.map((a) =>       // step 3: fill placeholders left-to-right
      a === _ && i < laterArgs.length ? laterArgs[i++] : a
    );
    while (i < laterArgs.length) {                // step 4: append remaining laterArgs at the end
      finalArgs.push(laterArgs[i++]);
    }
    return fn.apply(this, finalArgs);
  };
}

partial._ = _;                                    // expose the placeholder symbol on the API
```

**Try it yourself**

```js
const subtract = (a, b) => a - b;

const subFrom10 = partial(subtract, 10);
console.log(subFrom10(3));                  // 7  (10 - 3)

const subtractFrom = partialP(subtract, _, 3);
console.log(subtractFrom(10));              // 7  (10 - 3)

// Method-style: `this` is forwarded
const obj = {
  prefix: 'log:',
  log(label, msg) { return `${this.prefix} ${label} ${msg}`; },
};
obj.error = partial(obj.log, 'ERROR');
console.log(obj.error('disk full'));        // "log: ERROR disk full"  (this preserved)
```

---

## 9. Step-by-step dry run

Input:

```js
const fetchUser = (baseUrl, headers, id) =>
  `${baseUrl}/users/${id} [${headers.auth}]`;

const apiCall = partial(fetchUser, 'https://api.example.com', { auth: 'Bearer abc' });
apiCall(42);
apiCall(43);
```

Values-first trace:

| Step | Action       | Captured `presetArgs`                                | `laterArgs` | Final args to `fn`                                | Returns                                            |
|------|--------------|------------------------------------------------------|-------------|---------------------------------------------------|----------------------------------------------------|
| init | `partial(...)` | `['https://api.example.com', {auth:'Bearer abc'}]` | —           | —                                                 | wrapper                                            |
| 1    | `apiCall(42)`  | (same)                                              | `[42]`      | `['https://api.example.com', {auth:'...'}, 42]`   | `"https://api.example.com/users/42 [Bearer abc]"` |
| 2    | `apiCall(43)`  | (same)                                              | `[43]`      | `['https://api.example.com', {auth:'...'}, 43]`   | `"https://api.example.com/users/43 [Bearer abc]"` |

The closure holds the preset array once; every call concatenates fresh `laterArgs` without disturbing it.

---

## 10. Common confusion + traps

1. **Confusing partial with curry.**
   Curry waits for arity to be reached, returning wrappers until then. Partial fires `fn` on the next call regardless. Interviewers love to ask "implement both, explain the difference."

2. **Mutating `presetArgs`.**
   The preset array is closure-shared across all wrapper invocations. `preset.push(...later)` poisons every subsequent call. Always concat into a new array via spread.

3. **Forgetting `this` forwarding.**
   `fn(...preset, ...later)` doesn't pass `this`. `fn.apply(this, [...preset, ...later])` does. Critical for method-style assignments.

4. **Believing `bind(null, x)` is currying.**
   It's partial application + `this` binding. `bind` fires `fn` on the first call to the bound function — same as partial, not curry.

5. **Memory pinning.**
   The preset args (especially objects) are pinned for the wrapper's lifetime. A 10 MB config object passed as a preset lives as long as `apiCall` does.

6. **Over- or under-supply.**
   `partial(fn, 1, 2)(3, 4)` passes `[1, 2, 3, 4]` to `fn`. Whether `fn` uses all four is `fn`'s business. `partial(fn, 1)()` passes `[1]` to `fn` — missing args are `undefined`.

7. **Placeholder collision with real values.**
   Using a string like `'_'` as a placeholder lets a caller accidentally pass that string. Use a unique `Symbol` so equality with `===` is unambiguous.

---

## 11. Senior follow-ups & variants

### Variant 1 — `partialRight(fn, ...presetArgs)`

Fix args from the **right** instead of the left. Useful for `divide`-shaped functions:

```js
function partialRight(fn, ...presetArgs) {
  return function (...laterArgs) {
    return fn.apply(this, [...laterArgs, ...presetArgs]);
  };
}
const halve = partialRight(divide, 2);    // x => divide(x, 2)
halve(10);   // 5
```

### Variant 2 — `Function.prototype.bind` polyfill

`bind` is partial application + `this` binding. Implementing it tests both at once:

```js
Function.prototype.myBind = function (thisArg, ...presetArgs) {
  const fn = this;
  return function (...laterArgs) {
    return fn.apply(thisArg, [...presetArgs, ...laterArgs]);
  };
};
```

Production `bind` has additional nuances around `new` (the bound function should be callable as a constructor). See [`10-machine-coding-patterns/bind-polyfill.md`](../10-machine-coding-patterns/bind-polyfill.md).

### Variant 3 — Express middleware factory

Real-world partial. A generic auth middleware that accepts a role; partial-apply per route:

```js
const requireRole = (role, req, res, next) => {
  if (req.user?.role !== role) return res.status(403).end();
  next();
};
app.get('/admin', partial(requireRole, 'admin'), handler);
app.get('/owner', partial(requireRole, 'owner'), handler);
```

Same skeleton, but the practical impact lands: one helper, many specialized middlewares without copy-paste.

### Variant 4 — Curried compose with partial

Partial is the building block for `compose` and `pipe`. Each step is a partial wait for the next value:

```js
const pipe = (...fns) => (x) => fns.reduce((v, f) => f(v), x);
const transform = pipe(
  partial(map, double),
  partial(filter, isEven),
  partial(reduce, sum, 0),
);
```

---

## 12. How to think aloud in the interview

> "Partial application: capture some args at definition time, return a wrapper that takes the rest and calls `fn`. Closure holds `presetArgs`; wrapper does `fn.apply(this, [...preset, ...later])`. Never mutate the preset array — it's shared across calls. For `this`-correctness use `apply`, so method-style usage works. The key distinction from curry: curry keeps returning wrappers until arity is met; partial fires `fn` on the next call regardless. `Function.prototype.bind(null, ...args)` is the same thing plus `this` binding. For non-prefix presets, support a placeholder via a unique Symbol: walk the preset array, fill `_` slots from `laterArgs` in order, append leftovers."

---

## 13. 60-second revision

> - **Pattern:** capture `presetArgs` in closure; wrapper does `fn.apply(this, [...preset, ...later])`.
> - Single wrapper that fires `fn` on the next call. **Not** curry.
> - **Never mutate** the preset array.
> - **Forward `this`** via `.apply(this, ...)`.
> - `Function.prototype.bind(null, ...args)` ≡ `partial(fn, ...args)`.
> - **Placeholder** (`_`) is a unique `Symbol`. Walk preset, fill `_` slots from later args, append leftovers.
> - **Family:** `bind`, `curry`, middleware factories, action creators.
> - **Trap:** confusing with curry; mutating preset; forgetting `this`.

---

**Related:** [curry-via-closures.md](./curry-via-closures.md) · [counter.md](./counter.md) · [`10-machine-coding-patterns/bind-polyfill.md`](../10-machine-coding-patterns/bind-polyfill.md) · [`10-machine-coding-patterns/function-composition.md`](../10-machine-coding-patterns/function-composition.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
