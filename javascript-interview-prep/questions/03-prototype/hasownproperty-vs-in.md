# `hasOwnProperty` vs `in` vs `Object.hasOwn`

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md)
>
> **Source:** Every JS fundamentals round. ESLint `no-prototype-builtins`.

---

## 1. Problem statement

Three operators that traverse different slices of the property space. When to use which?

**Verification examples**

```js
const proto = { a: 1 };
const child = Object.create(proto);
child.b = 2;

'a' in child;                       // true  (chain walk)
'b' in child;                       // true  (own)
'toString' in child;                // true  (inherited from Object.prototype)

child.hasOwnProperty('a');          // false (inherited)
child.hasOwnProperty('b');          // true  (own)

Object.hasOwn(child, 'a');          // false (own only)
Object.hasOwn(child, 'b');          // true

// Dictionary trap
const dict = Object.create(null);
dict.x = 1;
dict.hasOwnProperty;                 // undefined (no chain to Object.prototype!)
Object.hasOwn(dict, 'x');           // true (static method works)
'x' in dict;                         // true (operator, not method)
```

**Constraints**
- `in` walks chain (includes inherited + non-enumerable).
- `hasOwnProperty` = own properties (susceptible to shadowing + missing on `Object.create(null)`).
- `Object.hasOwn` (ES2022) = own only, immune to shadowing.

---

## 2. Plain-English restatement

`in` asks "is this key anywhere on the chain?" (true for `'toString' in {}`). `hasOwnProperty` and `Object.hasOwn` ask "is this an OWN property?" Difference: `hasOwnProperty` is a method on `Object.prototype` (can be shadowed/missing); `Object.hasOwn` is a static method (immune).

---

## 3. Why this matters in interviews

Tests chain vs own understanding. Killer follow-up: `Object.create(null)` breaks `hasOwnProperty`.

---

## 4. Mental model

```
   `'key' in obj`      — operator. WALKS chain. Includes non-enumerable inherited.
   obj.hasOwnProperty('k') — method. OWN ONLY. Susceptible to shadow/missing.
   Object.hasOwn(obj, 'k') — static. OWN ONLY. SAFE against shadow/missing.
   
   Chain example:
   child = Object.create({a:1});
   child.b = 2;
   
   'a' in child       → true (proto has a)
   'b' in child       → true (own)
   'toString' in child → true (Object.prototype has it)
   child.hasOwnProperty('a') → false (inherited)
   child.hasOwnProperty('b') → true
   
   Dictionary trap:
   dict = Object.create(null);  // no chain to Object.prototype!
   dict.hasOwnProperty           → undefined
   dict.hasOwnProperty('x')      → TypeError
   Object.hasOwn(dict, 'x')      → works
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `'toString' in {}` return `true` or `false`?
> 2. What happens with `Object.create(null).hasOwnProperty('x')`?
> 3. Why is `Object.hasOwn` safer than `obj.hasOwnProperty`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `obj[key] !== undefined`
Walks chain, doesn't distinguish explicit `undefined`, broken for falsy values.

### Wrong attempt 2: always use `hasOwnProperty`
Breaks on `Object.create(null)` and shadowed names.

### Wrong attempt 3: only `in`
Includes inherited; not always what you want.

---

## 7. The unlocking insight

> **`in` for "anywhere on chain". `Object.hasOwn(obj, key)` for "own only" (safe). `obj.hasOwnProperty(key)` is legacy — fails on null-proto dicts and shadowed names. Three operators, three different questions.**

Three properties:

1. **`in`** = chain walk.
2. **`hasOwn`** = own (modern, safe).
3. **`hasOwnProperty`** = own (legacy, fragile).

---

## 8. Solution (annotated)

```js
const obj = { a: 1 };
const child = Object.create(obj);
child.b = 2;

// CHAIN walk
'a' in child;                                                            // true (inherited)
'b' in child;                                                            // true (own)
'toString' in child;                                                     // true (Object.prototype)

// OWN only — legacy method
child.hasOwnProperty('a');                                               // false
child.hasOwnProperty('b');                                               // true

// OWN only — modern, safe static
Object.hasOwn(child, 'a');                                               // false
Object.hasOwn(child, 'b');                                               // true

// Dictionary trap
const dict = Object.create(null);
dict.x = 1;
try { dict.hasOwnProperty('x'); } catch (e) { console.log(e.message); }  // TypeError
Object.hasOwn(dict, 'x');                                                 // true (safe)
'x' in dict;                                                              // true (operator)

// Shadowing trap
const bad = { hasOwnProperty: false };
try { bad.hasOwnProperty('x'); } catch (e) { console.log(e.message); }   // TypeError
Object.hasOwn(bad, 'x');                                                  // false (safe)
```

**Try it yourself**

```js
// Distinguish missing from undefined
const obj = { foo: undefined };
obj.foo === undefined;                                                    // true
'foo' in obj;                                                             // true (key exists)
Object.hasOwn(obj, 'foo');                                                 // true

// Sparse array
const arr = [,,];
0 in arr;                                                                  // false (hole)
arr.hasOwnProperty(0);                                                     // false

// Safe dictionary iteration
for (const key of Object.keys(dict)) {
  console.log(key, dict[key]);
}
// Object.keys is safe — own enumerable only, doesn't walk chain
```

---

## 9. Step-by-step dry run

```
'a' in child:
  Walk child's chain: child own? no. proto own? YES. Return true.

child.hasOwnProperty('a'):
  Method on Object.prototype.
  Walk: child own? no. proto own? no. Object.prototype own? YES → hasOwnProperty.
  Invoke with this=child, args=['a']:
    Check if child has own 'a' → no.
    Return false.

dict.hasOwnProperty('x') where dict = Object.create(null):
  Walk: dict own? no. dict.__proto__ === null → end of chain.
  Property hasOwnProperty undefined.
  dict.hasOwnProperty is undefined.
  undefined('x') → TypeError.

Object.hasOwn(dict, 'x'):
  Static method on Object. Always available.
  Check if dict has own 'x' → yes.
  Return true.
```

---

## 10. Common confusion + traps

1. **`obj[key] !== undefined`** — broken for explicit undefined + falsy.
2. **Shadowed `hasOwnProperty`** — `{ hasOwnProperty: false }.hasOwnProperty('x')` throws.
3. **`Object.create(null)` + hasOwnProperty** — missing method.
4. **`'toString' in {}`** — true (inherited, non-enumerable).
5. **`in` for arrays** — index check; `0 in [1,2]` is true, holes are false.
6. **`for...in` walks chain** — includes inherited enumerable; use `Object.keys`.
7. **Proxy `has` trap** — intercepts `in`.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Object.prototype.hasOwnProperty.call(dict, k)`
Works on null-proto dicts; verbose.

### Variant 2 — ESLint `no-prototype-builtins`
Recommends `Object.hasOwn` over `obj.hasOwnProperty`.

### Variant 3 — Sparse array detection
`1 in [1,,3]` → false; perfect for hole detection.

### Variant 4 — `Object.keys` / `Object.entries`
Own enumerable; doesn't walk chain.

### Variant 5 — Proxy `has` trap
Can intercept `in` operator for meta-programming.

---

## 12. How to think aloud

> "Three operators, three different questions. `'key' in obj` is an OPERATOR that walks the entire prototype chain — includes inherited and non-enumerable. So `'toString' in {}` is true. `obj.hasOwnProperty(key)` is a METHOD inherited from `Object.prototype` — checks OWN properties only, but susceptible to two problems: (1) can be shadowed by a property of the same name, (2) missing entirely on `Object.create(null)` dictionaries. `Object.hasOwn(obj, key)` is the ES2022 STATIC method — same own-only semantics but safe against shadowing and unreachable chains. ESLint's `no-prototype-builtins` rule recommends `Object.hasOwn` over `obj.hasOwnProperty`. Use `in` for 'is this key anywhere?'. Use `Object.hasOwn` for 'is this an own property?'. Distinguish missing from undefined via `in` or `hasOwn` (not `obj[key] !== undefined`). Trap: shadowed hasOwnProperty; null-proto dict; for...in walking chain."

---

## 13. 60-second revision

> - **`'key' in obj`** = chain walk (includes inherited + non-enumerable).
> - **`Object.hasOwn(obj, key)`** = own only (modern, safe).
> - **`obj.hasOwnProperty(key)`** = own only (legacy, can shadow/missing).
> - **`Object.create(null).hasOwnProperty`** = undefined → TypeError.
> - **`in` for arrays:** index check; `1 in [1,,3]` is false (hole).
> - **`for...in`** walks chain; use `Object.keys` for own enumerable.
> - **`obj[key] !== undefined`** — broken for explicit undefined.
> - **ESLint `no-prototype-builtins`** recommends Object.hasOwn.
> - **Trap:** shadowed; null-proto dict; for...in chain walk.

---

**Related:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [defineproperty-vs-assignment.md](./defineproperty-vs-assignment.md) · [object-create-polyfill.md](./object-create-polyfill.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
