# `hasOwnProperty` vs `in` vs `Object.hasOwn`

## Source
- Canonical "do you understand chain vs own?" question (every JS fundamentals round, MDN docs, ESLint `no-prototype-builtins` rule).
- MDN references:
  - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/hasOwn
  - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/in

## Why this question matters in interviews
Three operators that look interchangeable but each traverse a different slice of the property space. Junior candidates use them at random; seniors know exactly when each one matters. The killer follow-up — "what happens with `Object.create(null)`?" — exposes whether the candidate understands that `hasOwnProperty` lives on `Object.prototype` and is therefore unreachable when the chain doesn't include `Object.prototype`. Backend engineers hit this every time they build a dictionary-style cache, parse untrusted JSON, or handle `__proto__` keys safely.

## Concepts involved

### Syntax to lock in
```js
const obj = { a: 1 };
const child = Object.create(obj);
child.b = 2;

'a' in child;                          // true  — chain walk
'b' in child;                          // true  — own
'toString' in child;                   // true  — inherited from Object.prototype

child.hasOwnProperty('a');             // false — inherited, not own
child.hasOwnProperty('b');             // true
child.hasOwnProperty('toString');      // false — own only

Object.hasOwn(child, 'a');             // false — own only (modern, ES2022)
Object.hasOwn(child, 'b');             // true

// Dictionary object — chain is null
const dict = Object.create(null);
dict.x = 1;
dict.hasOwnProperty;                   // undefined — no chain to Object.prototype!
dict.hasOwnProperty('x');              // TypeError: dict.hasOwnProperty is not a function
Object.hasOwn(dict, 'x');              // true — works because it's a static method
'x' in dict;                           // true — operator, not method
```

### Runtime / engine behavior
- **`'key' in obj`** — operator. Walks the **entire prototype chain**. Returns `true` if the key exists anywhere. Includes non-enumerable properties (`'toString' in {}` → true).
- **`obj.hasOwnProperty(key)`** — method inherited from `Object.prototype`. Checks **own properties only** (no chain walk). Susceptible to being shadowed (`{ hasOwnProperty: 'oops' }.hasOwnProperty('x')` throws). Susceptible to being unreachable (`Object.create(null)` doesn't inherit it).
- **`Object.hasOwn(obj, key)`** — ES2022 static method. Same semantics as `hasOwnProperty` but **immune to shadowing and unreachable chains** because it doesn't go through the instance. The modern replacement; ESLint's `no-prototype-builtins` rule recommends it.
- All three include both enumerable and non-enumerable own properties. None of them check inherited non-enumerables for `Object.hasOwn` / `hasOwnProperty`.

### Edge cases (these are the interview traps)
1. **`Object.create(null)` breaks `hasOwnProperty.call`** — workaround: `Object.prototype.hasOwnProperty.call(dict, 'x')`. Or just `Object.hasOwn(dict, 'x')`.
2. **Shadowed `hasOwnProperty`** — `const obj = { hasOwnProperty: false }; obj.hasOwnProperty('x')` throws because `false` isn't a function. ESLint's `no-prototype-builtins` catches this; use `Object.hasOwn` to avoid it entirely.
3. **`in` catches inherited symbols too** — `'toString' in {}` is `true` because `toString` lives on `Object.prototype`.
4. **`in` works on arrays for indices** — `0 in [1,2,3]` is `true`; `5 in [1,2,3]` is `false`. Useful for detecting holes: `1 in [1, , 3]` is `false`.
5. **`undefined` values vs missing keys** — `obj.foo === undefined` doesn't distinguish "key is `undefined`" from "key doesn't exist." `'foo' in obj` does.
6. **Array sparse holes** — `[,,].hasOwnProperty(0)` is `false`; `0 in [,,]` is `false`. Both correctly identify sparseness. `for...in` skips them. `array.forEach` skips them. `array.map` preserves them (returns sparse array).
7. **Inherited getters** — `'length' in fn` is `true` even though `length` is inherited from `Function.prototype` (a non-enumerable getter). `in` doesn't care about enumerability.
8. **Proxy traps** — a `Proxy` can intercept `in` via the `has` trap and `hasOwn` queries via `getOwnPropertyDescriptor` trap. Worth mentioning if asked about meta-programming.

## Brute force approach
"Use `obj[key] !== undefined`." Three bugs at once: (a) doesn't distinguish missing from explicit `undefined`, (b) walks the chain (so `obj.toString !== undefined` is `true`), (c) returns `false` for keys with falsy values that you actually want. Drop it.

## Optimal approach
- **Want "is this key anywhere, including inherited and non-enumerable?"** → `'key' in obj`.
- **Want "is this key an own property, safely?"** → `Object.hasOwn(obj, key)` (ES2022) or `Object.prototype.hasOwnProperty.call(obj, key)` (older).
- **Avoid** `obj.hasOwnProperty(key)` — fragile across shadowing and dictionary objects.

## Solution (JavaScript)

```js
/**
 * Demonstrate the three operators and their differences.
 * Plus a safe "is own property?" helper.
 */

function isOwn(obj, key) {
  // The bulletproof version — ES2022 static method, no shadowing risk.
  if (typeof Object.hasOwn === 'function') return Object.hasOwn(obj, key);
  return Object.prototype.hasOwnProperty.call(obj, key);
}

// ---- Demonstration ----

const animal = { eats: true };
const rabbit = Object.create(animal);
rabbit.jumps = true;

console.log('jumps' in rabbit);                       // true (own)
console.log('eats' in rabbit);                        // true (inherited)
console.log('toString' in rabbit);                    // true (Object.prototype)

console.log(isOwn(rabbit, 'jumps'));                  // true
console.log(isOwn(rabbit, 'eats'));                   // false (inherited)
console.log(isOwn(rabbit, 'toString'));               // false

// Dictionary safety
const dict = Object.create(null);
dict['__proto__'] = 'safe';   // not a getter trap on a null-proto object
console.log(isOwn(dict, '__proto__'));                // true
console.log('__proto__' in dict);                     // true

// Sparse array detection
const sparse = [1, , 3];
console.log(1 in sparse);                             // false (hole)
console.log(0 in sparse);                             // true
console.log(isOwn(sparse, 'length'));                 // true (length is own)
```

## Step-by-step dry run

Input:
```js
const parent = { p: 1 };
const child  = Object.create(parent);
child.c = 2;

const dict = Object.create(null);
dict.d = 3;

'p' in child;                                   // (1)
child.hasOwnProperty('p');                      // (2)
Object.hasOwn(child, 'p');                      // (3)
'toString' in child;                            // (4)
child.hasOwnProperty('toString');               // (5)
dict.hasOwnProperty('d');                       // (6)
Object.hasOwn(dict, 'd');                       // (7)
```

Trace:
- (1) `'p' in child` — walks chain: `child` own keys → no `p` → climb → `parent` own → has `p` → returns `true`.
- (2) `child.hasOwnProperty('p')` — looks up `hasOwnProperty` (inherited from `Object.prototype`), then calls it with `this = child`. Checks `child`'s OWN keys for `'p'` → not found → returns `false`.
- (3) `Object.hasOwn(child, 'p')` — same as (2) but called as a static. Returns `false`.
- (4) `'toString' in child` — walks chain → child → parent → `Object.prototype` → has `toString` → returns `true`.
- (5) `child.hasOwnProperty('toString')` — checks child's OWN keys → not found → returns `false`. Correctly reports "inherited, not own."
- (6) `dict.hasOwnProperty('d')` — lookup `dict.hasOwnProperty` walks dict's chain → `null` immediately → not found → returns `undefined` → `undefined('d')` → **TypeError**: not a function. This is the headline gotcha.
- (7) `Object.hasOwn(dict, 'd')` — static method, doesn't touch `dict`'s chain to find itself. Checks `dict`'s own keys → has `'d'` → `true`. Works perfectly.

The dict examples are why `Object.hasOwn` exists.

## Important takeaways

**Syntax to memorize**
- `'key' in obj` — chain walk, includes non-enumerable. Operator, not method.
- `Object.hasOwn(obj, key)` — own only, immune to shadowing. ES2022+.
- `Object.prototype.hasOwnProperty.call(obj, key)` — own only, pre-ES2022 safe form.
- Plain `obj.hasOwnProperty(key)` — fragile. Avoid (ESLint `no-prototype-builtins`).

**Patterns to reuse**
- **`Object.create(null)` for safe dictionaries** — no prototype pollution risk, no `__proto__` setter trap. Pair with `Object.hasOwn` for lookups.
- **`'key' in obj` for hole detection** in sparse arrays — `for (let i = 0; i < arr.length; i++) if (!(i in arr)) skipHole();`.
- **Distinguishing missing vs explicit-undefined**: `'key' in obj` is the only correct test.

**Common mistakes**
- Using `obj[key] !== undefined` to check existence — fails for keys with `undefined` values, walks the chain.
- Calling `dict.hasOwnProperty(...)` on a `Object.create(null)` dict — TypeError.
- Trusting `obj.hasOwnProperty(...)` when `obj` came from untrusted input — `{ hasOwnProperty: 'evil' }` breaks it.
- Forgetting that `in` includes inherited and non-enumerable — `'toString' in {}` surprises candidates who thought `in` was "own only."

**Related questions**
- "What does `for...in` iterate?" → own + inherited **enumerable** keys. Pair with `Object.hasOwn` to filter to own.
- "How do you safely access properties on parsed JSON?" → `Object.hasOwn(parsed, key)` plus guard against `__proto__` keys (older Node versions interpret `__proto__` in JSON specially in some contexts).
- "What's the safest way to clone a plain object?" → `structuredClone` or `Object.assign(Object.create(null), src)` for safe-dict shape.

## Variants

1. **`__proto__` pollution defense** — "Walk a JSON-parsed object and reject any keys named `__proto__`, `constructor`, or `prototype`." Use `Object.hasOwn` to enumerate own keys safely.

2. **`for...in` vs `Object.keys`** — "Why does `for...in` show inherited keys but `Object.keys` doesn't?" Because `Object.keys` is "own + enumerable"; `for...in` is "own + inherited + enumerable." Filter via `if (Object.hasOwn(obj, key))`.

3. **Property descriptor inspection** — "How would you list ALL own properties, including non-enumerable and symbols?" `Reflect.ownKeys(obj)` (returns string + symbol keys, enumerable + non-enumerable). Strictly own — no chain walk.

## Revision notes

> **hasOwnProperty / in / Object.hasOwn — 60 second recap**
> - `'k' in obj` — chain walk, includes non-enumerable. Operator.
> - `Object.hasOwn(obj, k)` — own only, safe. ES2022. **Use this.**
> - `obj.hasOwnProperty(k)` — own only but fragile (shadowable, breaks on `Object.create(null)`).
> - `Object.prototype.hasOwnProperty.call(obj, k)` — older safe form.
> - **Trap:** `Object.create(null)` has no chain to `Object.prototype` → `dict.hasOwnProperty` is `undefined` → TypeError.
> - **Trap:** `{ hasOwnProperty: 'x' }.hasOwnProperty('y')` throws (shadowed by non-function).
> - **Trap:** `obj[key] !== undefined` doesn't distinguish missing from explicit-undefined and walks the chain.
> - `'i' in arr` correctly detects sparse-array holes; `forEach`/`map` skip holes.
> - ESLint rule: `no-prototype-builtins` enforces `Object.hasOwn` over the instance method.
