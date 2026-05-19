# JSON path resolver — `get(obj, path)`

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)
>
> **Source:** lodash `_.get` / `_.set`. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Implement `get(obj, 'a.b.c[0].d')` and `set(obj, path, value)`. Handle dot, bracket, escaped dots.

**Verification examples**

```js
get({a: {b: {c: 1}}}, 'a.b.c');                   // 1
get({a: [1, 2, 3]}, 'a[1]');                      // 2
get({a: {b: 1}}, 'a.x.y');                        // undefined
get({a: 1}, 'a.b.c', 'default');                  // 'default'

set({}, 'a.b.c', 1);                              // {a: {b: {c: 1}}}
set({a: {}}, 'a.b[0]', 'x');                      // {a: {b: ['x']}}
```

**Constraints**
- Parse path: dot for keys, `[n]` for array index.
- Safe traversal: null/undefined at any level → defaultVal.
- `set`: auto-create intermediate object/array based on next path segment.

---

## 2. Plain-English restatement

Parse a string path into tokens (keys + indices). Walk the object; return value or default. For `set`: walk creating missing intermediates inferred by next token type.

---

## 3. Why this matters in interviews

Tests path parsing + safe traversal + edge cases (escaped dots, bracket notation).

---

## 4. Mental model

```
   Path syntax:
     'a.b.c'      = obj.a.b.c
     'a[0]'        = obj.a[0]
     'a.b[0].c'    = obj.a.b[0].c
     'a["x.y"]'    = obj.a['x.y']   (quoted to allow dot in key)
   
   Parse algorithm:
     Tokenize: dot, [, ], ', "
     States: outside/inside-bracket/inside-quoted.
     Output: array of tokens [key, key, index, key, ...].
   
   get:
     curr = obj
     for token of parsed:
       if curr is null/undef: return defaultVal
       curr = curr[token]
     return curr === undefined ? defaultVal : curr
   
   set:
     last = tokens.pop()
     curr = obj
     for token of tokens:
       if curr[token] not exists or wrong type:
         curr[token] = (next token is number) ? [] : {}
       curr = curr[token]
     curr[last] = value
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. How parse `'a["b.c"][0]'`?
> 2. `get({a: {b: 0}}, 'a.b', 99)` — return 0 or 99?
> 3. `set` auto-create policy?

---

## 6. Brute force — walked through

```js
function naive(obj, path) {
  return path.split('.').reduce((acc, k) => acc?.[k], obj);
}
// FAILS: 'a[0]', 'a["x.y"]', escaped dots.
```

---

## 7. The unlocking insight

> **Tokenize path (dot, bracket, quote). Walk with optional chaining. `set` infers type by next token.**

Three properties:

1. **Tokenize** properly.
2. **`get` returns undefined → default**.
3. **`set` infers `[]` vs `{}`** by next token.

---

## 8. Solution (annotated)

```js
function parsePath(path) {
  if (Array.isArray(path)) return path;                                   // step 1: pre-tokenized
  const out = [];
  let i = 0, buf = '';
  while (i < path.length) {
    const c = path[i];
    if (c === '.') {
      if (buf) { out.push(buf); buf = ''; }
      i++;
    } else if (c === '[') {
      if (buf) { out.push(buf); buf = ''; }
      const end = path.indexOf(']', i);                                    // step 2: find ]
      const raw = path.slice(i + 1, end);
      if (raw.startsWith('"') || raw.startsWith("'")) {
        out.push(raw.slice(1, -1));                                        // step 3: quoted
      } else {
        out.push(Number(raw));                                              // step 4: array index
      }
      i = end + 1;
    } else {
      buf += c;
      i++;
    }
  }
  if (buf) out.push(buf);
  return out;
}

function get(obj, path, defaultVal) {
  const parts = parsePath(path);
  let curr = obj;
  for (const p of parts) {
    if (curr == null) return defaultVal;                                   // step 5: safe traverse
    curr = curr[p];
  }
  return curr === undefined ? defaultVal : curr;
}

function set(obj, path, value) {
  const parts = parsePath(path);
  if (parts.length === 0) return obj;
  let curr = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const p = parts[i];
    const nextIsNum = typeof parts[i + 1] === 'number';
    if (curr[p] == null || typeof curr[p] !== 'object') {
      curr[p] = nextIsNum ? [] : {};                                       // step 6: infer type
    }
    curr = curr[p];
  }
  curr[parts[parts.length - 1]] = value;
  return obj;
}
```

**Try it yourself**

```js
get({a: {b: {c: 1}}}, 'a.b.c');                              // 1
get({a: [1, 2, 3]}, 'a[1]');                                 // 2
get({a: {b: {c: 1}}}, 'a.b.x', 'def');                       // 'def'
get({a: {b: 0}}, 'a.b', 99);                                 // 0 (not 99 — only undefined uses default)

get({a: {'b.c': 1}}, 'a["b.c"]');                            // 1 (quoted)

set({}, 'a.b.c', 1);                                          // {a: {b: {c: 1}}}
set({a: {}}, 'a.b[0]', 'x');                                  // {a: {b: ['x']}}
set({a: [1, 2]}, 'a[5]', 'z');                                // {a: [1, 2, , , , 'z']}

// Has check
function has(obj, path) {
  const parts = parsePath(path);
  let curr = obj;
  for (const p of parts) {
    if (curr == null || !(p in curr)) return false;
    curr = curr[p];
  }
  return true;
}
has({a: {b: 1}}, 'a.b');                                      // true
has({a: {b: 1}}, 'a.c');                                      // false

// Unset / delete
function unset(obj, path) {
  const parts = parsePath(path);
  const last = parts.pop();
  let curr = obj;
  for (const p of parts) {
    if (curr == null) return false;
    curr = curr[p];
  }
  if (curr == null) return false;
  return delete curr[last];
}
```

---

## 9. Step-by-step dry run

```
parsePath('a.b[0].c'):
  i=0 'a': buf='a'. i=1.
  i=1 '.': push 'a'. buf=''. i=2.
  i=2 'b': buf='b'.
  i=3 '[': push 'b'. find ']' at i=5. raw='0'. push Number('0')=0. i=6.
  i=6 '.': i=7.
  i=7 'c': buf='c'.
  end: push 'c'.
  Result: ['a', 'b', 0, 'c'].

get({a: {b: [{c: 'x'}]}}, 'a.b[0].c'):
  parts = ['a', 'b', 0, 'c'].
  curr = obj.
  'a': curr = {b: [...]}.
  'b': curr = [...].
  0: curr = {c: 'x'}.
  'c': curr = 'x'.
  Return 'x'.

get({a: null}, 'a.b'):
  curr = obj.
  'a': curr = null.
  'b': curr is null → return defaultVal.

set({}, 'a.b[0]', 'x'):
  parts = ['a', 'b', 0].
  iter 0 (last 'a'): nextIsNum? parts[1]='b' is string → curr.a = {}. curr = {}.
  iter 1 (last 'b'): nextIsNum? parts[2]=0 is number → curr.b = []. curr = [].
  Final: curr[0] = 'x'.
  Result: {a: {b: ['x']}}.

get({a: {b: 0}}, 'a.b', 99):
  curr.b = 0. Loop ends with curr=0.
  curr === undefined? No (0 is defined). Return 0.
  Not 99!  Default only when undefined.
```

---

## 10. Common confusion + traps

1. **Default for any falsy** — should only be for undefined.
2. **`split('.')` only** — breaks on brackets / quoted keys.
3. **`set` overwrite existing wrong type** — policy unclear.
4. **Sparse array indexing** — `set(arr, 'a[5]', v)` creates holes.
5. **Prototype pollution via path** — `set({}, '__proto__.polluted', 1)` — sanitize!
6. **Negative indices** — `arr[-1]` ≠ last in JS.
7. **Path is array shortcut** — `get(obj, ['a', 'b', 0])`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Array path
Skip parsing if `Array.isArray(path)`.

### Variant 2 — `has`, `unset`
Companion ops.

### Variant 3 — Path-typed (TypeScript)
`get<O, P>(o: O, p: P): GetPath<O, P>` — type-level path resolution.

### Variant 4 — Prototype pollution safe
Reject `__proto__`, `constructor`, `prototype`.

### Variant 5 — JSONPath / JMESPath
Full query language.

---

## 12. How to think aloud

> "JSON path resolver: parse path string into tokens (keys for dot-notation, numeric indices for bracket-notation, escape-quoted for keys-with-dots), then walk. Parser handles: dot separator, `[n]` numeric index, `[\"key\"]` quoted key (escapes embedded dots). Tokenize with simple state machine: dot pushes current buffer; `[` finds closing `]`, parses interior as number or stripped-quoted string. `get`: walk tokens; if curr is null/undefined at any step, return defaultVal; final value only uses default if it's `undefined` (NOT for `null`, `0`, `''`, etc. — those are legit values). `set`: walk tokens except last; auto-create intermediate objects/arrays based on the NEXT token's type (numeric → `[]`, string → `{}`); assign final. Helpers: `has(obj, path)` uses `in` check; `unset(obj, path)` uses `delete`. Prototype pollution: reject `__proto__`, `constructor`, `prototype` keys in set/unset. Path can be passed as array `['a', 'b', 0]` for pre-tokenized speed. Lodash `_.get` / `_.set` matches semantics roughly. Trap: default for any falsy (should be undefined only); split('.') breaks brackets; prototype pollution; negative indices ≠ last."

---

## 13. 60-second revision

> - **Parse:** dot, `[n]`, `[\"key\"]`.
> - **`get`:** walk with optional chaining; default only for undefined.
> - **`set`:** auto-create intermediates by next-token type.
> - **`has`** via `in`; **`unset`** via `delete`.
> - **Reject `__proto__`** — pollution safe.
> - **Array path** shortcut for pre-tokenized.
> - **lodash `_.get/set`** parity.
> - **Trap:** falsy default; split('.'); pollution; negative idx.

---

**Related:** [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) · [`08-maps-sets/object-deep-diff.md`](../08-maps-sets/object-deep-diff.md) · [recursive-descent-parser.md](./recursive-descent-parser.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
