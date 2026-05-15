# Customize `toString` and `Symbol.toPrimitive` on a class

## Source
- Common "what happens when JS coerces your object?" interview question (You Don't Know JS: Types & Grammar, BFE.dev #38).
- MDN references:
  - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/toPrimitive
  - https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/toStringTag

## Why this question matters in interviews
Every JS object has a default `toString` that yields `'[object Object]'` and a default `valueOf` that yields the object itself. Both are inherited from `Object.prototype`. When an object lands in a string context (`` `${obj}` ``), number context (`+obj`), or comparison (`obj == 5`), JS calls these methods through a well-defined coercion protocol: `Symbol.toPrimitive` first, then `valueOf`/`toString` depending on the **hint** (`'string'`, `'number'`, `'default'`). Senior interviews probe this because (a) it tests whether you understand the prototype chain (you're overriding inherited methods), (b) it tests `Symbol.*` well-known symbols, and (c) it surfaces classic gotchas like `Date` returning `'string'` hint for `+`. Backend engineers see this when building Money / Decimal / Duration classes that need to print and arithmetic-coerce sensibly.

## Concepts involved

### Syntax to lock in
```js
class Money {
  constructor(amount, currency) {
    this.amount = amount;
    this.currency = currency;
  }
  toString() {
    return `${this.amount.toFixed(2)} ${this.currency}`;
  }
  valueOf() {
    return this.amount;
  }
  [Symbol.toPrimitive](hint) {
    if (hint === 'string')  return this.toString();
    if (hint === 'number')  return this.valueOf();
    return this.toString(); // 'default' hint — for == and string concat with `+`
  }
  get [Symbol.toStringTag]() {
    return 'Money';
  }
}

const m = new Money(99.5, 'INR');
String(m);                     // '99.50 INR'   (hint 'string')
+m;                            // 99.5          (hint 'number')
`${m}`;                        // '99.50 INR'   (hint 'string')
m + 1;                         // '99.50 INR1'  (hint 'default' → toString)
Object.prototype.toString.call(m); // '[object Money]'
```

### Runtime / engine behavior
- Coercion calls **`ToPrimitive(obj, hint)`** internally:
  1. If `obj[Symbol.toPrimitive]` exists, call it with the hint. Whatever it returns is the result (must be a primitive).
  2. Else, the hint determines ordering:
     - `'number'` or `'default'` → try `valueOf()`, then `toString()`.
     - `'string'` → try `toString()`, then `valueOf()`.
  - Whichever returns a primitive first wins.
- Hint sources:
  - `String(obj)`, template literals, `${}` → `'string'`.
  - `+obj`, `obj * 1`, `Math.abs(obj)`, bitwise → `'number'`.
  - `obj + x`, `obj == x` (with non-objects) → `'default'`.
- `Date` is the exception: `Date.prototype[Symbol.toPrimitive]` treats `'default'` as `'string'` — that's why `new Date() + ''` produces the date string, not a number.
- `Symbol.toStringTag` only affects `Object.prototype.toString.call(obj)` — the legacy `'[object Tag]'` style. Doesn't affect template literals.

### Edge cases (these are the interview traps)
1. **`==` coercion order** — `m == '99.50 INR'` → `Symbol.toPrimitive('default')` on `m` → `'99.50 INR'` → string compare → true. But `m == 99.5` → primitive on `m` is `'99.50 INR'`, not `99.5`, so equality is FALSE unless `Symbol.toPrimitive('default')` returns the number.
2. **`valueOf` returning an object** — JS silently falls through to `toString`. Must return a primitive.
3. **`Symbol.toPrimitive` precedence** — if defined, it short-circuits `valueOf`/`toString` entirely. One source of truth.
4. **Default `Object.prototype.toString`** — returns `'[object Object]'` unless `Symbol.toStringTag` is set. Setting it changes the tag everywhere (`Object.prototype.toString.call(map)` → `'[object Map]'`).
5. **Inheritance** — overriding `toString` on a subclass is just prototype shadowing. Same chain-walk rules.
6. **`JSON.stringify` doesn't call `toString`** — it calls `toJSON()` instead. Different protocol. Worth mentioning if asked about serialization.
7. **`Array.prototype.toString`** joins with commas — `[1, 2].toString() === '1,2'`. That's why `[1,2] + ''` is `'1,2'`. The inherited default.
8. **`null` returns from primitive hooks** — `null` IS a primitive, so coercion stops there. Returns `null` to the caller.

## Brute force approach
"Just override `toString`." Works for string contexts but fails for `+obj` (number context falls back to `valueOf`, which is the default object identity — returns `NaN` when coerced). Half-solutions like this are the most common interview answer; the full coercion protocol is what separates seniors.

## Optimal approach
- Implement `Symbol.toPrimitive(hint)` as the **single source of truth** for coercion. Handle all three hints explicitly.
- Implement `toString()` for explicit `String(obj)` and for legacy callers.
- Implement `valueOf()` if numeric arithmetic is meaningful (Money, Duration, etc.).
- Set `Symbol.toStringTag` if you want a nicer default tag.

## Solution (JavaScript)

```js
class Duration {
  constructor(ms) {
    this.ms = ms;
  }

  toString() {
    const sec = Math.floor(this.ms / 1000);
    const min = Math.floor(sec / 60);
    const hr  = Math.floor(min / 60);
    if (hr)  return `${hr}h ${min % 60}m`;
    if (min) return `${min}m ${sec % 60}s`;
    return `${sec}s`;
  }

  valueOf() {
    return this.ms; // numeric coercion → milliseconds
  }

  [Symbol.toPrimitive](hint) {
    switch (hint) {
      case 'string':  return this.toString();
      case 'number':  return this.valueOf();
      case 'default': return this.valueOf(); // arithmetic-friendly default
      default:        return this.toString();
    }
  }

  get [Symbol.toStringTag]() {
    return 'Duration';
  }

  toJSON() {
    // JSON serialization uses its own protocol
    return { ms: this.ms, label: this.toString() };
  }
}

const d = new Duration(125_000); // 2 minutes 5 seconds
```

## Step-by-step dry run

Input:
```js
const d = new Duration(125_000);

`${d}`;                              // (1)
+d;                                  // (2)
d + 1000;                            // (3)
d * 2;                               // (4)
d == 125000;                         // (5)
Object.prototype.toString.call(d);   // (6)
JSON.stringify(d);                   // (7)
```

Trace:
- (1) Template literal → hint `'string'` → `Symbol.toPrimitive('string')` → `toString()` → `'2m 5s'`.
- (2) Unary `+` → hint `'number'` → `Symbol.toPrimitive('number')` → `valueOf()` → `125000`.
- (3) Binary `+` between object and non-string → hint `'default'` → `Symbol.toPrimitive('default')` → `valueOf()` → `125000`. Then `125000 + 1000` = `126000`.
- (4) `*` always hints `'number'` → `valueOf()` → `125000`. Then `125000 * 2` = `250000`.
- (5) Loose equality `obj == primitive` → hint `'default'` → `valueOf()` → `125000`. Then `125000 == 125000` → `true`.
- (6) Default `Object.prototype.toString` checks `Symbol.toStringTag` → `'Duration'` → returns `'[object Duration]'`.
- (7) `JSON.stringify` calls `toJSON()` first if present → `{ ms: 125000, label: '2m 5s' }` → serialized as `'{"ms":125000,"label":"2m 5s"}'`.

Each coercion exercises a different rung of the protocol.

## Important takeaways

**Syntax to memorize**
- Three hint values: `'string'`, `'number'`, `'default'`. Handle all three.
- `Symbol.toPrimitive` short-circuits `valueOf`/`toString` when present.
- Default coercion order: `'string'` hint → toString → valueOf; everything else → valueOf → toString.
- `Symbol.toStringTag` only affects `Object.prototype.toString.call(...)`.

**Patterns to reuse**
- "Define `Symbol.toPrimitive` as the source of truth" is the canonical pattern for value-like classes (Money, Decimal, Duration, BigDecimal). Don't rely on coercion ordering — make it explicit.
- `toJSON()` is the separate protocol for `JSON.stringify`. Not affected by `Symbol.toPrimitive`.

**Common mistakes**
- Overriding only `toString` and being surprised that `+obj` returns `NaN`.
- Forgetting the `'default'` hint — it's used by `+` and `==`, which are the most common coercion sites.
- Returning a non-primitive from `Symbol.toPrimitive` — silently invalid; engine throws `TypeError` in modern engines.
- Confusing `Object.prototype.toString.call(obj)` (legacy tag-extraction trick) with `obj.toString()` (instance method). They're not interchangeable.
- Assuming `JSON.stringify(obj)` calls `toString` — it doesn't. Implement `toJSON()` for serialization control.

**Related questions**
- "How does loose equality (`==`) work?" — same `ToPrimitive` algorithm under the hood.
- "Implement a BigDecimal class" — exact same protocol, plus arithmetic methods.
- "Why does `[] + []` produce `''`?" — both arrays toString to `''`, then string concat. Coercion in action.

## Variants

1. **`Money` with currency-aware comparison** — "How would you make `usd100 == eur100` return `false` even though both have `valueOf() === 100`?" Answer: override `Symbol.toPrimitive('default')` to throw or return an object-unique tagged string; document that loose equality across currencies is forbidden.

2. **`Date.prototype[Symbol.toPrimitive]`** — "Why does `new Date() + 0` produce a string?" Because `Date` overrides the protocol: `'default'` hint is treated as `'string'`. Demonstrates that built-ins use the same hook.

3. **Custom `Object.prototype.toString` tag** — "Make a class whose `Object.prototype.toString.call(x)` returns `'[object Currency]'`." Just `get [Symbol.toStringTag]() { return 'Currency'; }`.

## Revision notes

> **toString / Symbol.toPrimitive — 60 second recap**
> - Coercion calls `ToPrimitive(obj, hint)` where `hint ∈ {'string','number','default'}`.
> - `Symbol.toPrimitive(hint)` is the single source of truth — short-circuits valueOf/toString.
> - Hint sources: `String()`/`${}` → `'string'`; `+obj`/`*` → `'number'`; `obj + x` / `obj == prim` → `'default'`.
> - Default order: `'string'` → toString→valueOf; else → valueOf→toString.
> - `Symbol.toStringTag` only affects `Object.prototype.toString.call(obj)` → `'[object Tag]'`.
> - `JSON.stringify` calls `toJSON()`, NOT `toString`.
> - **Trap:** overriding only `toString` → `+obj` is NaN.
> - **Trap:** `Symbol.toPrimitive` must return a primitive; returning an object throws.
> - `Date` quirk: `'default'` hint treated as `'string'`.
