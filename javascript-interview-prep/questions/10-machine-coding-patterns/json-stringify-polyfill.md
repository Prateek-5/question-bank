# Implement `JSON.stringify` polyfill

## Source
- Classic machine-coding deep-dive (BFE.dev, codedamn, GreatFrontEnd polyfill series).
- ECMA-262 §25.5.2 / §24.5.2 — the spec definition is precise and worth a skim.

## Why this question matters in interviews
JSON.stringify polyfill is the **recursive-descent serializer** of JS interviews. The naive approach (`'"' + obj + '"'` for strings) gets you a third of the way; the real interview begins at edge cases: cycles, undefined-in-arrays-vs-objects, special numbers (NaN/Infinity), the replacer parameter, indentation, surrogate pairs, custom `toJSON` methods. It tests **type dispatch via `typeof`**, **recursive traversal**, **cycle detection with `WeakSet`**, **escape-sequence handling**, and the kind of attention-to-spec-detail interviewers want to see in someone who'll write production data serializers (logging, audit trails, HTTP body encoding).

## Concepts involved

### Syntax to lock in
```js
function stringify(value) {
  if (value === null) return 'null';
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : 'null';
  if (typeof value === 'boolean') return String(value);
  if (typeof value === 'string') return `"${escape(value)}"`;
  if (typeof value === 'undefined' || typeof value === 'function' || typeof value === 'symbol') return undefined;
  if (Array.isArray(value)) {
    const items = value.map((v) => stringify(v) ?? 'null'); // undefined/fn/symbol → null in arrays
    return `[${items.join(',')}]`;
  }
  if (typeof value === 'object') {
    const pairs = [];
    for (const k of Object.keys(value)) {
      const v = stringify(value[k]);
      if (v !== undefined) pairs.push(`${stringify(k)}:${v}`);  // skip in objects
    }
    return `{${pairs.join(',')}}`;
  }
}
```

### Runtime / engine behavior
- The spec walks the value with **type-based dispatch** (`typeof`, `Array.isArray`, `value === null`). There's no single API to ask "what kind of thing is this"; you assemble it.
- **Asymmetric undefined handling**: in arrays, `undefined`/function/symbol becomes `null` in the output (positional integrity). In objects, the **whole key** is omitted. `JSON.stringify([1, undefined, 3])` → `"[1,null,3]"`; `JSON.stringify({a: undefined})` → `"{}"`.
- **Number specials**: `NaN`, `Infinity`, `-Infinity` are not representable in JSON. The spec serializes them as `"null"`. `-0` becomes `"0"`.
- **String escaping**: must escape `"`, `\`, control chars (`\b`, `\f`, `\n`, `\r`, `\t`), and any other ASCII < 0x20 via `\u00XX`. Lone surrogates produce invalid JSON in JSON.stringify (though some engines emit them anyway). Standard says: keep them, but emit `\uXXXX` for control chars.
- **Cycles** throw `TypeError: Converting circular structure to JSON`. Detection requires tracking "what we've already entered" — a `WeakSet` of visited objects, push on enter, delete on exit (or check before recursing).
- **`toJSON`**: if the value has a `toJSON()` method, the spec calls it first and serializes the return value. `Date.prototype.toJSON` returns ISO string — that's why Dates become `"2026-05-14T...Z"`.
- The optional **replacer** can be either a function (called for each key/value pair) or an array (whitelist of keys for objects). The **space** parameter inserts indentation.

### Edge cases (these are the interview traps)
1. **Cycles** — must throw. The canonical detection is a WeakSet of currently-entered objects, pushed on enter, deleted on exit. Don't use Set — non-object keys can't be tracked; non-object values can't be cyclical anyway.
2. **`undefined` asymmetry** — array slot becomes `null`; object key is omitted entirely. Many candidates write the array case wrong.
3. **`NaN`/`Infinity`** — serialize as `null`, not as the string `"NaN"`. Use `Number.isFinite`.
4. **Strings** — escape `"`, `\`, `\n`, `\r`, `\t`, `\b`, `\f`, and all C0 control chars (0x00–0x1F) via `\u00XX`. Don't forget ` ` / ` ` if you care about JSONP-safe output (not strictly required by JSON.stringify; nice-to-have).
5. **`toJSON()`** — check it on every value before type-dispatching. Dates, Mongo ObjectIds, and many custom classes rely on it.
6. **Symbol keys** — `Object.keys` excludes them, which is correct. `JSON.stringify` ignores symbol keys silently.
7. **`function`, `undefined`, `symbol`** as top-level argument → return `undefined` (not the string `"undefined"`). This trips up many.
8. **Number-like classes** — `new Number(5)` is an object, not a primitive. The spec unwraps via `toJSON` or `valueOf`. Subtle; safe to skip in an interview unless asked.
9. **Replacer + space** — full spec includes both. Most interviews only require the core; mention these as "easy add."
10. **Object key order** — spec says iterate own enumerable string keys in their property-creation order. `Object.keys` already does this. Don't sort.

## Brute force approach
"Just call `String(value)`." Works for primitives, totally wrong for objects (becomes `"[object Object]"`). Drop.

A more reasonable starter: handle primitives directly, recurse on arrays/objects, ignore everything else. This is essentially the correct approach — the work is in the details.

## Optimal approach
Recursive descent with `typeof`-based dispatch, WeakSet for cycle detection, and a small escape function for strings. O(n) in total bytes of input. Memory: O(depth) for the call stack plus the WeakSet for visited objects.

## Solution (JavaScript)

```js
/**
 * Polyfill of JSON.stringify (core, no replacer / space — see Variants).
 * @param {*} value
 * @returns {string | undefined}  undefined when top-level value is non-serializable
 */
function stringify(value) {
  const seen = new WeakSet();

  function escapeString(s) {
    let out = '"';
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      const ch = s[i];
      if (ch === '"') out += '\\"';
      else if (ch === '\\') out += '\\\\';
      else if (c === 0x08) out += '\\b';
      else if (c === 0x09) out += '\\t';
      else if (c === 0x0a) out += '\\n';
      else if (c === 0x0c) out += '\\f';
      else if (c === 0x0d) out += '\\r';
      else if (c < 0x20) out += '\\u' + c.toString(16).padStart(4, '0');
      else out += ch;
    }
    return out + '"';
  }

  function walk(val) {
    // toJSON hook (Date, custom classes, ObjectId, etc.)
    if (val !== null && typeof val === 'object' && typeof val.toJSON === 'function') {
      val = val.toJSON();
    }

    if (val === null) return 'null';
    const t = typeof val;
    if (t === 'boolean') return val ? 'true' : 'false';
    if (t === 'number') return Number.isFinite(val) ? String(val) : 'null';
    if (t === 'string') return escapeString(val);
    if (t === 'undefined' || t === 'function' || t === 'symbol') return undefined;

    // From here, val is an object.
    if (seen.has(val)) throw new TypeError('Converting circular structure to JSON');
    seen.add(val);

    let out;
    if (Array.isArray(val)) {
      const items = val.map((v) => walk(v) ?? 'null');     // undefined/fn/symbol → null
      out = `[${items.join(',')}]`;
    } else {
      const pairs = [];
      for (const k of Object.keys(val)) {
        const v = walk(val[k]);
        if (v !== undefined) pairs.push(`${escapeString(k)}:${v}`);  // skip omitted keys
      }
      out = `{${pairs.join(',')}}`;
    }

    seen.delete(val);  // allow same object via different branches (not a cycle)
    return out;
  }

  return walk(value);
}
```

## Step-by-step dry run

Input:
```js
const obj = {
  a: 1,
  b: 'hi\n"x"',
  c: [1, undefined, NaN, () => {}],
  d: { nested: true, drop: undefined },
  e: new Date('2026-05-14T00:00:00Z')
};

stringify(obj);
```

Trace:
- Enter `obj` (object, not seen). Add to WeakSet. Object branch.
- `a`: walk(1) → `"1"`. Pair: `"a":1`.
- `b`: walk('hi\n"x"') → escapeString → `"hi\n\"x\""` (with actual `\n` escaped as `\\n`).
- `c`: walk([1, undef, NaN, fn]). Array branch. Map each:
  - walk(1) → `"1"`
  - walk(undefined) → `undefined` → coerce to `'null'`
  - walk(NaN) → not finite → `'null'`
  - walk(fn) → `undefined` → coerce to `'null'`
  - join: `[1,null,null,null]`
- `d`: walk({nested:true, drop:undefined}). Object branch.
  - `nested`: walk(true) → `"true"`. Pair: `"nested":true`.
  - `drop`: walk(undefined) → `undefined`. **Skip the key entirely.**
  - Out: `{"nested":true}`.
- `e`: Date instance has `toJSON` → call it → `"2026-05-14T00:00:00.000Z"` (string). walk(that string) → escaped JSON string.
- Combine: `{"a":1,"b":"hi\n\"x\"","c":[1,null,null,null],"d":{"nested":true},"e":"2026-05-14T00:00:00.000Z"}`.

Cycle test:
```js
const a = {}; a.self = a;
stringify(a); // throws TypeError: Converting circular structure to JSON
```
- Enter `a`, add to seen. Iterate keys.
- `self` → walk(`a`) → `seen.has(a)` is true → throw.

## Important takeaways

**Syntax to memorize**
- `typeof`-based dispatch order: null → number → boolean → string → unserializable (undef/fn/symbol) → array → object.
- WeakSet for cycle detection, add on enter, delete on exit.
- Array: undefined/fn/symbol → `null`. Object: skip the whole key.
- NaN/Infinity → `null`. Use `Number.isFinite`.

**Patterns to reuse**
- Recursive-descent with type dispatch is the same shape as: deep-clone, deep-equal, schema validators (Joi/Zod walker), and AST printers.
- WeakSet for "what have I entered" generalizes to any graph traversal that might cycle.

**Common mistakes**
- Skipping the `toJSON` hook → Dates serialize as `{}` (no own enumerable string keys).
- Writing `JSON.stringify(undefined)` as `'undefined'` (wrong — should be `undefined`).
- Treating the array `undefined`-slot the same as the object `undefined`-value. They differ.
- Using `Set` instead of `WeakSet` for `seen`. Works but doesn't release references — for huge trees it can matter. WeakSet is correct.
- Forgetting control-char escape (raw `\n` in the output is invalid JSON).
- Not escaping the **key** when emitting `"key":value` — keys are strings and must go through the same escaper.

**Related questions**
- `JSON.parse` polyfill (recursive-descent parser, the inverse).
- Deep clone (same walker, different leaves).
- Deep equal (two walkers in lockstep).
- Schema validator / serializer.

## Variants

1. **With `replacer`** — if function: call `replacer.call(holder, key, value)` for each entry and serialize the returned value. If array: only emit object keys whose name appears in the array.

2. **With `space` indentation** — track a current indent string. Emit `\n` + indent before each item; close with `\n` + parent indent + `]`/`}`. Skip indentation entirely if `space` is omitted or `0`.

3. **Streaming / chunked stringify** — for huge objects, yield chunks via a generator instead of building one giant string. Used by `JSONStream` and similar. Avoids OOM on large arrays.

4. **Strict mode** — instead of dropping undefined/function/symbol silently, throw. Useful for HTTP body serializers where silent loss is dangerous.

## Revision notes

> **JSON.stringify polyfill — 90 second recap**
> - Recursive walker with `typeof` dispatch.
> - WeakSet for cycle detection — add on enter, delete on exit, throw if seen.
> - `toJSON` hook called before type dispatch (Dates etc).
> - Array: undefined/fn/symbol → `null`. Object: skip the key entirely. Asymmetric.
> - NaN/Infinity → `null`. -0 → `"0"`.
> - String escape: `"`, `\`, `\b\t\n\f\r`, and any ASCII < 0x20 → `\u00XX`.
> - Top-level non-serializable → return `undefined`.
> - Trap: Date without toJSON serializes as `{}`. Cycle without WeakSet stack-overflows.
> - Same shape as deep-clone, deep-equal, schema walker.
