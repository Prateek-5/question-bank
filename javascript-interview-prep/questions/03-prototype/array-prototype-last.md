# Implement `Array.prototype.last`

> **Difficulty:** Easy   |   **Time:** ~5 min   |   **Prereqs:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md)
>
> **Source:** [LeetCode 2619 — Array Prototype Last](https://leetcode.com/problems/array-prototype-last/). Frontend-leaning 10-min warm-up.

---

## 1. Problem statement

Add a `.last()` method to `Array.prototype` that returns the last element or `-1` if empty.

**Verification examples**

```js
Array.prototype.last = function () {
  return this.length === 0 ? -1 : this[this.length - 1];
};

[1, 2, 3].last();    // 3
[].last();           // -1
```

**Constraints**
- Return `-1` for empty array (not `undefined`).
- `this` must be the array — don't use arrow function.
- Safe form uses `Object.defineProperty` with `enumerable: false`.

---

## 2. Plain-English restatement

Add a method to the Array prototype that returns the last element, or `-1` if empty.

---

## 3. Why this matters in interviews

Tests prototype augmentation + `this` binding + awareness that polluting built-ins is a code smell. 10-min warm-up.

---

## 4. Mental model

```
   Array.prototype.last = function() { ... }
   
   [1,2,3].last():
     lookup: [1,2,3] own → no. Array.prototype own → last. Invoke with this=[1,2,3].
     return this[this.length - 1] = 3.
   
   Why function not arrow?
     Arrow has no own `this`; can't access the array.
   
   Why -1 for empty? LeetCode contract.
   
   Code smell:
     Polluting Array.prototype:
     - Enumerable in for...in.
     - Can clash with future ES proposals (Array.prototype.findLast exists now).
     - Other libraries may monkey-patch the same name.
   Safe form:
     Object.defineProperty(Array.prototype, 'last', {
       value: fn, enumerable: false, writable: true, configurable: true,
     });
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does the safe form use `Object.defineProperty`?
> 2. What happens if you use an arrow function instead?
> 3. Why is "augmenting built-ins" a code smell?

---

## 6. Brute force — walked through

### Wrong attempt 1: arrow function
`Array.prototype.last = () => this[this.length - 1]` — arrow has no `this`; broken.

### Wrong attempt 2: return `undefined` for empty
Spec says `-1`.

### Wrong attempt 3: hardcode `arr`
`function() { return arr[arr.length - 1] }` — what `arr`? Use `this`.

---

## 7. The unlocking insight

> **`Array.prototype.last = function() { return this.length === 0 ? -1 : this[this.length - 1]; }`. Use plain function for `this`. Use `Object.defineProperty` with `enumerable: false` for safe form.**

Three properties:

1. **Plain function** (not arrow) for `this`.
2. **`-1` for empty** array.
3. **`enumerable: false`** to not pollute `for...in`.

---

## 8. Solution (annotated)

```js
// Simple form (LeetCode acceptable)
Array.prototype.last = function () {                                    // step 1: plain function for this
  return this.length === 0 ? -1 : this[this.length - 1];                // step 2: -1 sentinel
};

[1, 2, 3].last();                                                       // 3
[].last();                                                              // -1

// Safe form (production-like)
Object.defineProperty(Array.prototype, 'last', {
  value: function () {
    return this.length === 0 ? -1 : this[this.length - 1];
  },
  enumerable: false,                                                     // step 3: not in for...in
  writable: true,
  configurable: true,
});
```

**Try it yourself**

```js
// Code smell demo
Array.prototype.last = function () { return this[this.length - 1]; };
for (const k in [1, 2, 3]) console.log(k);                              // '0', '1', '2', 'last' ← leaked

// Safe form: not in for...in
Object.defineProperty(Array.prototype, 'last2', {
  value: function () { return this[this.length - 1]; },
  enumerable: false,
});
for (const k in [1, 2, 3]) console.log(k);                              // '0', '1', '2' only

// Modern alternative: just use built-in
[1, 2, 3].at(-1);                                                       // 3 — no pollution
[1, 2, 3].findLast((x) => true);                                        // 3 — finds matching
```

---

## 9. Step-by-step dry run

```
[1, 2, 3].last():
  Lookup `last`:
    [1,2,3] own? no.
    Walk to Array.prototype. last? yes.
  Invoke last with this=[1,2,3]:
    this.length === 3 (not 0).
    return this[2] = 3.

[].last():
  Lookup `last` → same way.
  Invoke with this=[]:
    this.length === 0.
    return -1.
```

---

## 10. Common confusion + traps

1. **Arrow function** — no `this`; breaks.
2. **Return `undefined` for empty** — spec says -1.
3. **`Array.prototype.last = ...`** — enumerable by default; leaks in `for...in`.
4. **Sparse arrays** — `[1,,3].last()` is 3 (length 3, last index has value).
5. **`[1,,].last()`** — trailing comma; length 2, last value 1.
6. **Built-in alternatives** — `.at(-1)`, `.findLast`. Use these in production.
7. **Class-by-class augmentation** — `class MyArr extends Array {}` is the modern way.

---

## 11. Senior follow-ups & variants

### Variant 1 — Safe form via defineProperty
`enumerable: false` keeps `for...in` clean.

### Variant 2 — Use `.at(-1)` instead
Modern built-in; no pollution.

### Variant 3 — Subclass Array
`class MyArr extends Array { last() {...} }` — no prototype pollution.

### Variant 4 — Prototype pollution attack
User-controlled keys writing to `__proto__`; CVE-worthy bug.

### Variant 5 — Other LeetCode prototype problems
`Array.prototype.groupBy`, `Function.prototype.memoize`.

---

## 12. How to think aloud

> "`Array.prototype.last = function() { return this.length === 0 ? -1 : this[this.length - 1]; }`. Plain function (not arrow) so `this` refers to the array. Return `-1` for empty per spec. Augmenting built-in prototypes is a code smell because (a) it's enumerable by default — leaks into `for...in`; (b) clashes with future ES proposals (we already have `Array.prototype.findLast`); (c) other libraries may monkey-patch the same name. Safe form: `Object.defineProperty(Array.prototype, 'last', { value: fn, enumerable: false })`. Modern alternative: just use `.at(-1)` or `.findLast` — no pollution needed. For your own class hierarchy, subclass: `class MyArr extends Array { last() {...} }`. Trap: arrow function (no this); -1 vs undefined; enumerable pollution."

---

## 13. 60-second revision

> - **`Array.prototype.last = function() { return this.length === 0 ? -1 : this[this.length-1] }`**.
> - **Plain function** (not arrow) for `this`.
> - **`-1` for empty** (LeetCode spec).
> - **Safe form:** `Object.defineProperty` with `enumerable: false`.
> - **Modern alt:** `.at(-1)`, `.findLast`.
> - **Subclass:** `class MyArr extends Array {}` for own methods.
> - **Trap:** arrow; -1 vs undefined; for...in pollution.

---

**Related:** [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) · [hasownproperty-vs-in.md](./hasownproperty-vs-in.md) · [defineproperty-vs-assignment.md](./defineproperty-vs-assignment.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
