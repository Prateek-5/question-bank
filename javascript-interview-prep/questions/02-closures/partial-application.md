# Partial application — `partial(fn, ...presetArgs)`

## Source
- Classic FP problem (lodash `_.partial`, Ramda `R.partial`).
- Distinct from currying — interviewers ask both together to check you can tell them apart.

## Why this question matters in interviews
Partial application is the **one-shot cousin of curry**. Where curry is "collect args call-by-call until arity is reached," partial is "fix some args **now**, return a function that takes the rest." Senior backend interviewers ask it to test whether you can articulate the *semantic* difference (not just write similar-looking code) and whether you understand the **placeholder pattern** for non-prefix presets. In practice you use partial application everywhere: pre-binding a logger's component label, fixing the first arg of a generic dispatcher, building request handlers from a generic helper. It's the second-shortest closure problem after `once`.

## Concepts involved

### Syntax to lock in
```js
function partial(fn, ...presetArgs) {
  return function (...laterArgs) {
    return fn.apply(this, [...presetArgs, ...laterArgs]);
  };
}

const greet = (greeting, name) => `${greeting}, ${name}!`;
const hi = partial(greet, 'Hi');
hi('Maya');        // "Hi, Maya!"
hi('Sam');         // "Hi, Sam!"
```

### Runtime / engine behavior
- `presetArgs` is captured in the wrapper's closure. The array is shared across all later invocations — never mutate it.
- Each wrapper call concatenates `[...presetArgs, ...laterArgs]` into a fresh array — O(N+M) per call, M = number of late args. Fine for typical use.
- Unlike curry, partial **does not return another function** if you under-supply args — it calls `fn` immediately with whatever you gave. If `fn` expects more, you'll get `undefined` for the missing slots.
- `this` is forwarded via `.apply(this, ...)`. Critical for method-style use: `obj.handler = partial(genericHandler, 'route-a')`.

### Curry vs partial — the senior distinction

| Feature | Curry | Partial |
|---|---|---|
| Returns function until arity met | Yes | No — returns one wrapper |
| Knows about arity | Yes (`fn.length` or explicit) | No |
| Per-call accumulation | Yes | No |
| Placeholder support | Usually no (lodash extension) | Yes (lodash `_`) |
| Use case | FP composition pipelines | Pre-binding args for a callback |

Curry generalizes partial: `curry(fn)(a)` is `partial(fn, a)`, but `curry` keeps returning wrappers. Partial returns a wrapper that fires `fn` on the *next* call no matter how many args you give it.

### Edge cases (interview traps)
1. **Placeholders (`_`)** — `partial(fn, _, 'B', _)('A', 'C')` should call `fn('A', 'B', 'C')`. Requires walking the preset array and filling `_` slots from later args.
2. **Right-partial** — fix args from the right: `partialRight(divide, 2)` → `divide(x, 2)`. Swap concat order.
3. **`this` binding** — preserve method-style. Use `.apply(this, ...)`.
4. **Over-supplying args** — pass them all through (default) or truncate. Match `fn`'s behaviour.
5. **Mutating `presetArgs`** — never. Always concat into a new array.
6. **Argument shape after preset** — `fn.length` of the returned wrapper is `0` (it's variadic). Don't rely on it.

## Brute force approach
Hardcode positional pre-binding: `const hi = (name) => greet('Hi', name)`. Works for one case, doesn't generalize. The interview tests whether you can write the **generic** form.

## Optimal approach
Closure over `presetArgs`. Return a wrapper that concatenates with later args and invokes `fn`. O(1) state. Add placeholder support for the senior version.

## Solution (JavaScript)

```js
/**
 * Partial application — fix some args of `fn`.
 * @param {Function} fn
 * @param  {...any} presetArgs
 * @returns {Function}
 */
function partial(fn, ...presetArgs) {
  return function (...laterArgs) {
    return fn.apply(this, [...presetArgs, ...laterArgs]);
  };
}

/* ---- Senior version: placeholders ---- */
const _ = Symbol('partial.placeholder');

function partialP(fn, ...presetArgs) {
  return function (...laterArgs) {
    let i = 0;
    const finalArgs = presetArgs.map((a) =>
      a === _ && i < laterArgs.length ? laterArgs[i++] : a
    );
    // Append any leftover later args
    while (i < laterArgs.length) finalArgs.push(laterArgs[i++]);
    return fn.apply(this, finalArgs);
  };
}

partial._ = _;

// Usage
const subtract = (a, b) => a - b;
const subFrom10 = partial(subtract, 10);     // 10 - x
subFrom10(3);                                // 7

const subtractFrom = partialP(subtract, _, 3);   // x - 3
subtractFrom(10);                                // 7
```

## Step-by-step dry run

Input:
```js
const fetchUser = (baseUrl, headers, id) => `${baseUrl}/users/${id} [${headers.auth}]`;

const apiCall = partial(fetchUser, 'https://api.example.com', { auth: 'Bearer abc' });
apiCall(42);    // "https://api.example.com/users/42 [Bearer abc]"
apiCall(43);    // "https://api.example.com/users/43 [Bearer abc]"
```

Trace:
- `partial(fetchUser, 'https://api.example.com', { auth: 'Bearer abc' })`:
  - `presetArgs = ['https://api.example.com', { auth: 'Bearer abc' }]`.
  - Returns a wrapper closure capturing `presetArgs` + `fn`.
- `apiCall(42)`:
  - `laterArgs = [42]`.
  - Concat: `['https://api.example.com', { auth: 'Bearer abc' }, 42]`.
  - `fetchUser.apply(this, [...])` → returns `"https://api.example.com/users/42 [Bearer abc]"`.
- `apiCall(43)`:
  - Same closure, same `presetArgs`. New `laterArgs = [43]`.
  - Returns `"https://api.example.com/users/43 [Bearer abc]"`.

Heap snapshot: one closure record holds the (large-ish) `presetArgs` array forever. The `headers` object inside it is also pinned — if you partial-applied a 10MB config object, that 10MB lives until `apiCall` is GC'd.

## Important takeaways

**Syntax to memorize**
- `function partial(fn, ...preset)` captures preset args in closure.
- Returned wrapper: `function (...later) { return fn.apply(this, [...preset, ...later]); }`.
- For placeholder support, swap `map` over preset args, consuming later args in order.

**Patterns to reuse**
- "Closure over preset args" is the foundation of: bound methods (`fn.bind(thisArg, ...args)` is partial application + `this` binding), Express middleware factories, Redux action creators, retry-with-fixed-options.
- `Function.prototype.bind` is literally `partial` with a `this` binding. `fn.bind(null, ...presetArgs)` ≡ `partial(fn, ...presetArgs)`.

**Common mistakes**
- Confusing partial with curry — the question often asks "implement BOTH and explain the difference."
- Mutating `presetArgs` — closure is shared across all wrapper calls; mutation poisons later calls.
- Forgetting `this` forwarding — `obj.handler = partial(genericHandler, 'route')` then `obj.handler()` loses `this`.
- Believing `fn.bind(null, x)` is "the same as currying" — it isn't; bind fires `fn` on the first call to the bound function, like partial.

**Related questions**
- `curry(fn)` — the call-by-call cousin
- `Function.prototype.bind` polyfill
- `pipe(...fns)` / `compose(...fns)`
- Method binding for `setTimeout(obj.method.bind(obj), 100)`

## Variants

1. **`partialRight(fn, ...presetArgs)`** — fix args from the **right**. `partialRight(divide, 2)` → `(x) => divide(x, 2)`. Implementation: concat as `[...laterArgs, ...presetArgs]`.

2. **Placeholder-aware partial (`partial._`)** — let callers leave gaps: `partial(fn, _, 'B')('A')` → `fn('A', 'B')`. Tests array walking + index bookkeeping.

3. **`bind` polyfill** — `Function.prototype.bind = function (thisArg, ...preset) { ... }`. Same closure shape but adds `this` binding. Often a follow-up question.

## Revision notes

> **partial-application — 60 second recap**
> - Closure over a `presetArgs` array; wrapper concats `[...preset, ...later]` and calls `fn`.
> - Returns **one** wrapper that fires `fn` on the next call — does NOT keep returning wrappers like curry.
> - `Function.prototype.bind(null, ...args)` ≡ `partial(fn, ...args)`.
> - Placeholders (`_`) fill the gaps for non-prefix presets — walk preset array, consume later args in order.
> - Forward `this` via `.apply(this, ...)`.
> - Never mutate the preset array — closure shared across calls.
> - Heap: preset args pinned for wrapper lifetime — big args = retained memory.
> - **Trap:** confusing with curry. Curry waits for arity, partial fires immediately on the next call.
