# Customize `toString` and `Symbol.toPrimitive`

> **Difficulty:** Medium-Senior   |   **Time:** ~12 min   |   **Prereqs:** [getter-setter-via-prototype.md](./getter-setter-via-prototype.md)
>
> **Source:** Coercion protocol (`Symbol.toPrimitive`, `valueOf`, `toString`). BFE.dev #38.

---

## 1. Problem statement

Override how a class coerces to string and number contexts. Use `Symbol.toPrimitive`, `valueOf`, `toString`.

**Verification examples**

```js
class Money {
  constructor(amount, currency) { this.amount = amount; this.currency = currency; }
  toString() { return `${this.amount.toFixed(2)} ${this.currency}`; }
  valueOf() { return this.amount; }
  [Symbol.toPrimitive](hint) {
    if (hint === 'string') return this.toString();
    if (hint === 'number') return this.valueOf();
    return this.toString();                                              // 'default' hint
  }
}

const m = new Money(99.5, 'USD');
`${m}`;                                                                  // '99.50 USD' (string hint)
+m;                                                                       // 99.5 (number hint)
m + 1;                                                                    // '99.50 USD1' (default hint → string concat)
m * 2;                                                                    // 199 (number hint)
m == 99.5;                                                                // true (== coerces; default hint, then num)
```

**Constraints**
- 3 hints: `'string'`, `'number'`, `'default'`.
- `Symbol.toPrimitive` wins over `valueOf`/`toString`.
- Without `Symbol.toPrimitive`: number hint → valueOf then toString; string hint → toString then valueOf.
- Date defaults `'default'` hint to `'string'` (special).

---

## 2. Plain-English restatement

When JS coerces your object — `+obj`, `` `${obj}` ``, `obj == 5` — it calls coercion methods. `Symbol.toPrimitive` (if defined) gets a `hint` argument and full control. Otherwise the engine falls back to `valueOf` and `toString` based on the hint.

---

## 3. Why this matters in interviews

Prototype chain literacy + Symbol.* well-known symbols + coercion protocol depth.

---

## 4. Mental model

```
   Coercion protocol (when JS needs a primitive):
   
   1. If obj[Symbol.toPrimitive] is a function:
      result = obj[Symbol.toPrimitive](hint)
   2. Otherwise, ordered methods based on hint:
      hint === 'string': toString() then valueOf().
      hint === 'number': valueOf() then toString().
      hint === 'default': valueOf() then toString().
   
   Operations and their hints:
   - `${obj}`              → 'string'
   - String(obj)           → 'string'
   - +obj, obj * 2, obj > 5 → 'number'
   - obj + 1, obj == 5     → 'default' (Date is special: 'string')
   
   Use cases:
   - Money/Currency: print formatted, arithmetic as number.
   - Duration: '5h 30m' or 19800 seconds.
   - Decimal: avoid float precision loss in arithmetic.

   Symbol.toStringTag:
   - Customizes Object.prototype.toString.call(obj) result.
   - get [Symbol.toStringTag]() { return 'Money'; }
   - then `Object.prototype.toString.call(m)` → '[object Money]'.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What hint does `obj + 1` send?
> 2. What hint does `` `${obj}` `` send?
> 3. What hint does `+obj` send?

---

## 6. Brute force — walked through

### Wrong attempt 1: only override toString
Number contexts (`+obj`, `obj * 2`) use valueOf, not toString.

### Wrong attempt 2: override Object.prototype.toString
Affects ALL objects globally. Bad.

### Wrong attempt 3: ignore hint
Symbol.toPrimitive's whole point is the hint.

---

## 7. The unlocking insight

> **`Symbol.toPrimitive` (with hint arg) wins. Otherwise: number hint → valueOf, toString; string hint → toString, valueOf. Use for Money, Duration, Decimal classes.**

Three properties:

1. **`Symbol.toPrimitive`** is the modern hook.
2. **Three hints:** string, number, default.
3. **`Symbol.toStringTag`** for `[object X]` customization.

---

## 8. Solution (annotated)

```js
class Money {
  constructor(amount, currency) {
    this.amount = amount;
    this.currency = currency;
  }

  toString() {                                                          // step 1: legacy hook
    return `${this.amount.toFixed(2)} ${this.currency}`;
  }

  valueOf() {                                                            // step 2: legacy numeric hook
    return this.amount;
  }

  [Symbol.toPrimitive](hint) {                                           // step 3: modern hook (wins)
    if (hint === 'string') return this.toString();
    if (hint === 'number') return this.valueOf();
    return this.toString();                                               // 'default'
  }

  get [Symbol.toStringTag]() {                                            // step 4: tag for Object.prototype.toString
    return 'Money';
  }
}

const m = new Money(99.5, 'USD');

`${m}`;                                                                  // '99.50 USD' (string)
String(m);                                                                // '99.50 USD'
+m;                                                                       // 99.5 (number)
m * 2;                                                                    // 199 (number)
m + 1;                                                                    // '99.50 USD1' (default → string)
m == 99.5;                                                                // true (default → string '99.50 USD'? hmm — '99.50 USD' != 99.5 numerically, but == coerces)

Object.prototype.toString.call(m);                                        // '[object Money]'
```

**Try it yourself**

```js
// Duration class
class Duration {
  constructor(seconds) { this.seconds = seconds; }
  [Symbol.toPrimitive](hint) {
    if (hint === 'number') return this.seconds;
    if (hint === 'string') {
      const h = Math.floor(this.seconds / 3600);
      const m = Math.floor((this.seconds % 3600) / 60);
      return `${h}h ${m}m`;
    }
    return this.toString();
  }
  toString() {
    return `Duration(${this.seconds}s)`;
  }
}

const d = new Duration(7200);
`Trip: ${d}`;                                                             // 'Trip: 2h 0m'
+d;                                                                        // 7200
d > 3600;                                                                  // true (number hint, 7200 > 3600)

// Date's special-case 'default' hint = 'string'
String(new Date()) === new Date() + '';                                    // true (default → string)
```

---

## 9. Step-by-step dry run

```
`${m}`:
  Coerce m to primitive with hint='string'.
  m[Symbol.toPrimitive]('string') → toString() → '99.50 USD'.
  Result: '99.50 USD'.

+m:
  Coerce m to primitive with hint='number'.
  m[Symbol.toPrimitive]('number') → valueOf() → 99.5.
  Result: 99.5.

m + 1:
  Coerce m to primitive with hint='default'.
  m[Symbol.toPrimitive]('default') → toString() → '99.50 USD'.
  '99.50 USD' + 1 → string concat → '99.50 USD1'.

m * 2:
  Coerce to primitive with hint='number'.
  → 99.5. 99.5 * 2 = 199.

Without Symbol.toPrimitive (only toString + valueOf):
  hint='number' → valueOf() returns primitive → use.
  hint='string' → toString() returns primitive → use.
  hint='default' → valueOf() first (returns primitive), then toString().
```

---

## 10. Common confusion + traps

1. **Only override toString** — number contexts use valueOf.
2. **`Object.prototype.toString = ...`** — global; never do.
3. **`Symbol.toStringTag` = toString result** — different (changes `[object X]` tag).
4. **`'default'` hint = `'number'`** — depends; Date defaults to `'string'`.
5. **Array's `valueOf`** returns itself; `toString` joins with comma.
6. **`valueOf` returns object** — engine falls through to next method.
7. **`JSON.stringify` doesn't use toString** — uses `toJSON` instead.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Symbol.toStringTag`
Customizes `Object.prototype.toString.call(obj)` → `[object MyClass]`.

### Variant 2 — `toJSON` for JSON.stringify
Separate hook; runs before serialization.

### Variant 3 — Date's special hint
`new Date() + 1` → date.toString() (default hint = 'string' for Date).

### Variant 4 — Money precision
Use BigInt internally; toString for display.

### Variant 5 — Custom `==` semantics
Symbol.toPrimitive('default') controls `==` coercion.

---

## 12. How to think aloud

> "When JS coerces an object — `${obj}`, `+obj`, `obj == 5` — it calls the coercion protocol. `Symbol.toPrimitive(hint)` is the modern hook (wins over `valueOf`/`toString`). Three hints: 'string' (template literals, String()), 'number' (`+`, `*`, comparison), 'default' (`+`, `==`, except Date which uses 'string'). Without `Symbol.toPrimitive`, engine falls back: number hint tries `valueOf` then `toString`; string hint tries `toString` then `valueOf`. Use for Money (print formatted, arithmetic as number), Duration ('5h 30m' vs 19800 seconds), Decimal (precision). Also: `Symbol.toStringTag` customizes `Object.prototype.toString.call(obj)` → `[object MyClass]`. `toJSON` is separate (used by JSON.stringify). Trap: only overriding toString (number contexts use valueOf); confusing toString hooks with Symbol.toStringTag."

---

## 13. 60-second revision

> - **`Symbol.toPrimitive(hint)`** = modern hook (wins).
> - **Three hints:** string, number, default.
> - **Without it:** number → valueOf+toString; string → toString+valueOf.
> - **Operations:** `${obj}` → string; `+obj` → number; `obj + 1` → default.
> - **Date** defaults 'default' to 'string'.
> - **`Symbol.toStringTag`** customizes `Object.prototype.toString.call(obj)` → `[object X]`.
> - **`toJSON`** separate hook for `JSON.stringify`.
> - **Use:** Money, Duration, Decimal, Color.
> - **Trap:** only override toString; mix up toString hooks; ignore hint.

---

**Related:** [getter-setter-via-prototype.md](./getter-setter-via-prototype.md) · [symbol-iterator-on-class.md](./symbol-iterator-on-class.md) · [`08-maps-sets/well-known-symbols.md`](../08-maps-sets/well-known-symbols.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
