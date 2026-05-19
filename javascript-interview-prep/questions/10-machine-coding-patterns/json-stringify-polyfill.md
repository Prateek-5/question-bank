# `JSON.stringify` polyfill — recursive-descent serializer

> **Difficulty:** Senior   |   **Time:** ~30 min   |   **Prereqs:** [json-parse-recursive-descent.md](./json-parse-recursive-descent.md), [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)
>
> **Source:** ECMA-262 §25.5.2, BFE.dev polyfill series, GreatFrontEnd.

---

## 1. Problem statement

**Signature**
```ts
function stringify(value: any): string | undefined;
```

**Input / Output examples**

| Input                                      | Output                                  |
|--------------------------------------------|------------------------------------------|
| `1`, `true`, `'hi'`, `null`                 | `"1"`, `"true"`, `'"hi"'`, `"null"`      |
| `undefined`, `(() => {})`, `Symbol()`       | `undefined` (top-level)                  |
| `[1, undefined, NaN, () => {}]`             | `'[1,null,null,null]'` (asymmetric)     |
| `{a: undefined, b: 1}`                     | `'{"b":1}'` (key omitted)               |
| `NaN`, `Infinity`                            | `'null'`                                 |
| `new Date('2026-05-19')`                    | `'"2026-05-19T00:00:00.000Z"'` (via toJSON) |
| `const a={}; a.self=a; stringify(a)`        | `TypeError: Converting circular structure to JSON` |

**Constraints**
- Asymmetric `undefined`: array slot → `null`; object key → omitted entirely.
- `NaN`/`Infinity` → `'null'`.
- Cycles → throw via WeakSet tracking.
- `toJSON()` hook called before type dispatch.
- Strings escape `"`, `\`, control chars (< 0x20).

---

## 2. Plain-English restatement

The inverse of `JSON.parse`: walk a value tree and emit valid JSON text. Type-dispatch on `typeof`/`Array.isArray`/`null`. Special rules: `undefined`/function/symbol disappear (in objects) or become `null` (in arrays). `NaN`/`Infinity` become `null`. Cycles throw. Dates use `toJSON`.

---

## 3. Why this matters in interviews

The **recursive-descent serializer** of JS interviews. Tests `typeof`-dispatch, recursive traversal, cycle detection with `WeakSet`, escape handling, attention to spec details. Backend uses: HTTP body encoders, audit-log serializers, deterministic config snapshots.

---

## 4. Mental model

```
   stringify(value):
   ┌─────────────────────────────────────────────────────┐
   │ if value.toJSON?  → value = value.toJSON()          │
   │                                                      │
   │ typeof-dispatch:                                    │
   │   null            → "null"                          │
   │   boolean         → "true" / "false"                │
   │   number          → finite? String(v) : "null"      │
   │   string          → escape + quote                  │
   │   undefined/fn/sym → undefined (omitted)            │
   │                                                      │
   │ object branch:                                       │
   │   if seen.has(v) → THROW cycle                      │
   │   seen.add(v)                                        │
   │   if Array → [items.map(v=>walk(v) ?? 'null')]     │
   │   else      → {pairs of "key":walk(v) where v≠undef}│
   │   seen.delete(v)  ← allow same obj via different br │
   └─────────────────────────────────────────────────────┘

   Asymmetry:
     [1, undefined, 2]    → "[1,null,2]"  ← positional
     {a: undefined, b: 2} → '{"b":2}'      ← key dropped
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What is `stringify({d: new Date('2026-05-19')})`?
> 2. What is `stringify([1, undefined, 3])` vs `stringify({a: undefined, b: 1})`?
> 3. Why use `WeakSet` instead of `Set` for cycle detection?

---

## 6. Brute force — walked through

### Wrong attempt 1: `String(value)`
Works for primitives. For objects: `"[object Object]"`. Drop.

### Wrong attempt 2: skip `toJSON` hook
`Date` → `{}` (no own enumerable keys). Wrong.

### Wrong attempt 3: treat array undef same as object undef
`[1, undefined, 2]` → `'[1,,2]'`? Wrong — should be `'[1,null,2]'` (positional integrity).

---

## 7. The unlocking insight

> **Recursive walker with `typeof` dispatch. WeakSet tracks entered objects (cycle detection). `toJSON` hook called before type dispatch. Array vs object asymmetry on `undefined`. NaN/Infinity → `null`.**

Three properties:

1. **Type dispatch order matters** — null first, then primitives, then object branch.
2. **`toJSON` is the override hook** — called before dispatch.
3. **WeakSet for cycles** — push on enter, delete on exit (allows DAG sharing).

---

## 8. Solution (annotated)

```js
function stringify(value) {
  const seen = new WeakSet();

  function escapeString(s) {                                          // step 1: string escaper
    let out = '"';
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      const ch = s[i];
      if (ch === '"')      out += '\\"';
      else if (ch === '\\') out += '\\\\';
      else if (c === 0x08) out += '\\b';
      else if (c === 0x09) out += '\\t';
      else if (c === 0x0a) out += '\\n';
      else if (c === 0x0c) out += '\\f';
      else if (c === 0x0d) out += '\\r';
      else if (c < 0x20)   out += '\\u' + c.toString(16).padStart(4, '0');
      else                  out += ch;
    }
    return out + '"';
  }

  function walk(val) {
    if (val !== null && typeof val === 'object' && typeof val.toJSON === 'function') {
      val = val.toJSON();                                              // step 2: toJSON hook
    }

    if (val === null) return 'null';
    const t = typeof val;
    if (t === 'boolean')   return val ? 'true' : 'false';
    if (t === 'number')    return Number.isFinite(val) ? String(val) : 'null';
    if (t === 'string')    return escapeString(val);
    if (t === 'undefined' || t === 'function' || t === 'symbol') return undefined;

    // From here, val is an object.
    if (seen.has(val)) throw new TypeError('Converting circular structure to JSON');
    seen.add(val);                                                     // step 3: cycle guard

    let out;
    if (Array.isArray(val)) {
      const items = val.map((v) => walk(v) ?? 'null');                // step 4: array → null for undef
      out = `[${items.join(',')}]`;
    } else {
      const pairs = [];
      for (const k of Object.keys(val)) {
        const v = walk(val[k]);
        if (v !== undefined) pairs.push(`${escapeString(k)}:${v}`);   // step 5: object → omit key
      }
      out = `{${pairs.join(',')}}`;
    }

    seen.delete(val);                                                  // step 6: allow DAG sharing
    return out;
  }

  return walk(value);
}
```

**Try it yourself**

```js
stringify({a: 1, b: 'hi\n"x"', c: [1, undefined, NaN, () => {}], d: {nested: true, drop: undefined}, e: new Date('2026-05-19')});
// '{"a":1,"b":"hi\\n\\"x\\"","c":[1,null,null,null],"d":{"nested":true},"e":"2026-05-19T00:00:00.000Z"}'

stringify(undefined);                       // undefined
stringify([1, undefined, 3]);               // '[1,null,3]'
stringify({a: undefined});                  // '{}'
stringify(NaN);                              // 'null'

const a = {}; a.self = a;
try { stringify(a); } catch (e) { e.message; }
// 'Converting circular structure to JSON'
```

---

## 9. Step-by-step dry run

```
walk({a:1, b:'hi', c:[1,undef], d:{x:undef}, e:Date}):
  enter object. seen.add. iterate keys.
    a: walk(1) → '1'. pair: '"a":1'.
    b: walk('hi') → escape → '"hi"'. pair: '"b":"hi"'.
    c: walk([1, undef]). enter array. seen.add. map:
         walk(1) → '1'. walk(undef) → undefined → coerce '[null]' via ?? 'null'.
       out = '[1,null]'. seen.delete.
       pair: '"c":[1,null]'.
    d: walk({x:undef}). enter object. seen.add. iterate:
         x: walk(undef) → undefined. SKIP (key omitted).
       out = '{}'. seen.delete.
       pair: '"d":{}'.
    e: walk(Date instance). toJSON exists → val = '2026-05-19T...'.
       walk(string) → escape → '"2026-05-19T..."'.
       pair: '"e":"2026-05-19T..."'.
  out = '{"a":1,"b":"hi","c":[1,null],"d":{},"e":"2026-05-19T..."}'
  seen.delete. return.

Cycle:
  walk({self: self}):
    seen.add(self).
    iterate keys:
      self: walk(self) → seen.has(self) → THROW.
```

---

## 10. Common confusion + traps

1. **Skipping `toJSON`** — Date serializes as `{}`.
2. **`undefined` symmetry** — array slot vs object key differ; pick correct rule per branch.
3. **NaN/Infinity** as `'NaN'`/`'Infinity'` — must be `'null'`.
4. **`Set` for cycles** — works but doesn't release; WeakSet is correct.
5. **Forgetting control-char escape** — raw `\n` in output is invalid JSON.
6. **Not escaping keys** — keys are strings; pass through `escapeString` too.
7. **Top-level non-serializable returns `'undefined'`** (string) — must return `undefined` (actual).

---

## 11. Senior follow-ups & variants

### Variant 1 — Replacer (function or array)
- Function: call `replacer.call(holder, key, value)` before serializing.
- Array: only emit object keys in the whitelist.

### Variant 2 — `space` indentation
Track current indent string. Emit `\n` + indent before each item; close with `\n` + parent indent. Skip if `space` is `0`/omitted.

### Variant 3 — Streaming stringify
Generator yielding chunks. Avoids OOM on huge arrays. Used by `JSONStream`.

### Variant 4 — Strict mode
Throw on undefined/function/symbol instead of dropping silently. Safer for HTTP body serializers.

### Variant 5 — Stable key order
Sort object keys before emitting; produces deterministic output for diffing/hashing.

---

## 12. How to think aloud

> "Recursive walker with `typeof` dispatch. Order: `toJSON` hook → null → boolean → number (finite check) → string (escape) → unserializable → object branch. WeakSet `seen` for cycle detection — add on enter, delete on exit (so DAG sharing isn't false-positive). Array vs object asymmetry: array's `undefined`/fn/symbol slots become `'null'` (positional); object's `undefined`/fn/symbol keys are OMITTED entirely. NaN/Infinity → `'null'`. Trap: skipping `toJSON` — Date serializes as `{}`. Trap: array/object asymmetry. Trap: Set instead of WeakSet (no release on huge trees). Same shape as deep-clone, deep-equal, schema walker."

---

## 13. 60-second revision

> - **`typeof`-dispatch:** null → bool → number → string → unserializable → object.
> - **`toJSON` hook** called before dispatch (Date, ObjectId, custom).
> - **WeakSet `seen`** for cycles; add on enter, delete on exit.
> - **Array:** undef/fn/symbol → `'null'`. **Object:** key omitted entirely.
> - **NaN/Infinity → `'null'`** (use `Number.isFinite`).
> - **String escape:** `"`, `\`, `\b\t\n\f\r`, `< 0x20 → \uXXXX`.
> - **Top-level non-serializable** returns `undefined` (not `'undefined'`).
> - **Trap:** missing toJSON; asymmetric undef rule; Set instead of WeakSet; raw control chars.

---

**Related:** [json-parse-recursive-descent.md](./json-parse-recursive-descent.md) · [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) · [memoize-ii.md](./memoize-ii.md)

**Concept primer:** [`concepts/recursion.md`](../../concepts/recursion.md)
