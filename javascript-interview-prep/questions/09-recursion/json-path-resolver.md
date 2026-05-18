# JSON Path Resolver

## Source / Origin
- `lodash.get` / `lodash.set`; common utility.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/recursion.md`.

## Why this question matters in interviews
"Implement `get(obj, 'a.b.c[0].d')`." Tests path parsing + safe traversal + edge cases. Senior bar: handle bracket notation, array indexing, escaped dots, and `set` with auto-creation of intermediate objects/arrays.

## Concepts involved

```js
function get(obj, path, defaultVal) {
  const parts = parsePath(path);
  let curr = obj;
  for (const p of parts) {
    if (curr == null) return defaultVal;
    curr = curr[p];
  }
  return curr === undefined ? defaultVal : curr;
}

function parsePath(path) {
  if (Array.isArray(path)) return path;
  const out = [];
  let i = 0, buf = '';
  while (i < path.length) {
    const c = path[i];
    if (c === '.') { if (buf) { out.push(buf); buf = ''; } i++; }
    else if (c === '[') {
      if (buf) { out.push(buf); buf = ''; }
      const end = path.indexOf(']', i);
      const idx = path.slice(i + 1, end);
      out.push(idx.startsWith('"') || idx.startsWith("'") ? idx.slice(1, -1) : Number(idx));
      i = end + 1;
    } else { buf += c; i++; }
  }
  if (buf) out.push(buf);
  return out;
}
```

### Edge cases / traps
1. **Bracket vs dot** — `a.b` and `a[b]` and `a["b"]` all valid.
2. **Numeric vs string indices** — `arr[0]` is index 0; `obj['0']` is key `"0"`.
3. **Escaped delimiters** — `a\.b` for literal dot. Rarely supported; document it.
4. **Missing intermediate** — return `defaultVal`, don't throw.
5. **`set` with missing intermediate** — auto-create: object if next key is non-numeric, array if numeric.
6. **`__proto__` / `constructor`** — prototype pollution risk; reject these keys in `set`.
7. **Wildcard `*`** or filter `[?(@.foo)]` — that's JSONPath proper; usually scope creep.
8. **Symbol keys** — paths can't represent them directly.

## Mental Model

```
   'a.b[0].c'  → parse → ['a', 'b', 0, 'c']
   walk: obj.a.b[0].c
   null-check at each step; default on miss
   set: auto-create intermediates based on next part's type
```

## Solution

```js
const PROTO_KEYS = new Set(['__proto__', 'prototype', 'constructor']);

function parsePath(path) {
  if (Array.isArray(path)) return path;
  const out = [];
  let i = 0, buf = '';
  while (i < path.length) {
    const c = path[i];
    if (c === '\\' && i + 1 < path.length) { buf += path[i + 1]; i += 2; }
    else if (c === '.') { if (buf) { out.push(buf); buf = ''; } i++; }
    else if (c === '[') {
      if (buf) { out.push(buf); buf = ''; }
      const end = path.indexOf(']', i);
      const idx = path.slice(i + 1, end).trim();
      if (idx.startsWith('"') || idx.startsWith("'")) out.push(idx.slice(1, -1));
      else if (/^\d+$/.test(idx)) out.push(Number(idx));
      else out.push(idx);
      i = end + 1;
    } else { buf += c; i++; }
  }
  if (buf) out.push(buf);
  return out;
}

function get(obj, path, defaultVal) {
  const parts = parsePath(path);
  let curr = obj;
  for (const p of parts) {
    if (curr == null) return defaultVal;
    curr = curr[p];
  }
  return curr === undefined ? defaultVal : curr;
}

function set(obj, path, value) {
  const parts = parsePath(path);
  let curr = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    if (PROTO_KEYS.has(k)) throw new Error('prototype pollution refused');
    if (curr[k] == null || typeof curr[k] !== 'object') {
      const nextKey = parts[i + 1];
      curr[k] = typeof nextKey === 'number' ? [] : {};
    }
    curr = curr[k];
  }
  const last = parts[parts.length - 1];
  if (PROTO_KEYS.has(last)) throw new Error('prototype pollution refused');
  curr[last] = value;
  return obj;
}

function has(obj, path) {
  const parts = parsePath(path);
  let curr = obj;
  for (const p of parts) {
    if (curr == null || !(p in curr)) return false;
    curr = curr[p];
  }
  return true;
}

function del(obj, path) {
  const parts = parsePath(path);
  let curr = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (curr == null) return false;
    curr = curr[parts[i]];
  }
  if (curr == null) return false;
  return delete curr[parts[parts.length - 1]];
}
```

## Dry run

```js
const obj = { a: { b: [{ c: 1 }, { c: 2 }] } };
get(obj, 'a.b[0].c');           // 1
get(obj, 'a.b[1].c');           // 2
get(obj, 'a.x.y', 'default');   // 'default'
set(obj, 'a.b[2].d', 'new');
// obj.a.b[2] auto-created as object (because next key 'd' is non-numeric)
// obj.a.b is array, has length 3
```

## How to think aloud

> "Parse path into parts: split on `.`, handle bracket notation, escape backslash. Walk: null-check at each step, return default on miss. Set: auto-create intermediate — object if next part is string, array if number. Reject `__proto__` / `prototype` / `constructor` to prevent prototype pollution. For has, check `in`; for del, `delete` last part."

## Important takeaways

- **Parse path → array of parts.**
- **Null-check at every step** in get.
- **Auto-create intermediates** in set (object vs array by next-part type).
- **Reject prototype-keys** in set (`__proto__`, `prototype`, `constructor`).
- **Numeric vs string indices**: distinct.

## Variants

- **JSONPath** (`$.a.b[*].c`) — full spec with wildcards/filters.
- **JMESPath** — used by AWS CLI.
- **Wildcard match** — return all matches as array.
- **Immutable set** — return new object, structurally shared.

## Revision notes

```
parsePath('a.b[0]["c"]'):
  ['a', 'b', 0, 'c']

get(obj, path, default):
  walk parts; null-check at each step; default on miss

set(obj, path, value):
  walk; if intermediate missing, create {} or [] by next part's type
  REJECT prototype keys (security)

has(obj, path): walk; check `in` at last step
del(obj, path): walk to parent; delete last

SECURITY: __proto__, prototype, constructor — always reject in set
ESCAPE: \. for literal dot (custom convention)
```
