# `JSON.parse` polyfill — recursive-descent parser

> **Difficulty:** Senior   |   **Time:** ~30 min   |   **Prereqs:** [`concepts/recursion.md`](../../concepts/recursion.md), [trie.md](./trie.md)
>
> **Source:** [BFE.dev #21](https://bigfrontend.dev/problem/JSON-parse), Frontend Masters parser series. The smallest "real parser" you can write under interview pressure.

---

## 1. Problem statement

**Signature**
```ts
function jsonParse(src: string): any;
```

**Input / Output examples**

| Input                                      | Output                                  |
|--------------------------------------------|------------------------------------------|
| `'1'`                                       | `1`                                      |
| `'"hi\\n"'`                                 | `'hi\n'` (escape decoded)               |
| `'[1, 2, 3]'`                              | `[1, 2, 3]`                              |
| `'{"a": 1, "b": [true, null]}'`            | `{ a: 1, b: [true, null] }`             |
| `'[1, 2,]'`                                | SyntaxError (trailing comma not allowed)|
| `'1abc'`                                   | SyntaxError (trailing content)          |
| `'{"a":1'`                                  | SyntaxError (unterminated)              |

**Constraints**
- Single cursor `i` across the source string.
- One function per grammar production: `parseValue`, `parseObject`, `parseArray`, `parseString`, `parseNumber`, `parseBool`, `parseNull`.
- LL(1): dispatch on `src[i]`.
- Final check: `skipWs(); if (i !== src.length) throw`.

---

## 2. Plain-English restatement

A hand-rolled JSON parser. Walk the source string with a single cursor. Each `parseX()` function consumes characters that match grammar production X and advances the cursor. The top-level `parseValue` dispatches on the next character: `{` → object, `[` → array, `"` → string, etc. After parsing, ensure no trailing content remains.

---

## 3. Why this matters in interviews

The smallest **real parser** you can implement in 30 minutes. Probes tokenization vs parsing, recursive descent, single-character lookahead, escape handling, error reporting with positions. Once you've written one recursive-descent parser, the rest are easy: CSV, log-line, env-var expanders, template languages, mini-DSLs for config.

---

## 4. Mental model

```
   Single cursor i walks the source:

   src: { " a " : 1 , " b " : t r u e }
   i:   0 1 2 3 4 5 6 7 8 9 …

   parseValue() dispatch on src[i]:
     { → parseObject()    [ → parseArray()
     " → parseString()    t/f → parseBool()
     n → parseNull()      digit/- → parseNumber()

   Each parse function:
     1. consume opening char (i++)
     2. recurse / scan into the production
     3. consume closing char (i++)
     4. return parsed value

   At the top level:
     value = parseValue()
     skipWs()
     if i !== src.length → SyntaxError (trailing content)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `jsonParse('1abc')` do?
> 2. How do you handle `"hi\n"` — what does the string parser see as input bytes?
> 3. Why is the final `if (i !== src.length) throw` necessary?

---

## 6. Brute force — walked through

### Wrong attempt 1: `eval(src)` or `new Function('return ' + src)()`
Insecure (RCE), and doesn't enforce JSON's stricter syntax (no leading `+`, no comments, no trailing commas). Mention as non-answer.

### Wrong attempt 2: two-pass tokenize + parse
Cleaner for larger grammars but unnecessary allocations for JSON. Single-pass cursor is canonical.

### Wrong attempt 3: forget the trailing-content check
`jsonParse('1abc')` silently returns `1`. Always assert `i === src.length` after top-level parse.

---

## 7. The unlocking insight

> **Single cursor `i`, one function per grammar production, dispatch on `src[i]` with single-character lookahead. Skip whitespace before every dispatch. Final guard: no trailing content.**

Three properties:

1. **Single cursor** — all sub-parsers consume from and advance `i`.
2. **LL(1) dispatch** — `parseValue` switches on first char.
3. **Trailing-content guard** — `skipWs(); assert i === length`.

---

## 8. Solution (annotated)

```js
function jsonParse(src) {
  let i = 0;

  const error = (msg) => { throw new SyntaxError(`${msg} at position ${i}`); };
  const skipWs = () => { while (i < src.length && ' \n\r\t'.includes(src[i])) i++; };

  const parseValue = () => {                                         // step 1: top dispatch
    skipWs();
    if (i >= src.length) error('Unexpected end of input');
    const c = src[i];
    if (c === '{') return parseObject();
    if (c === '[') return parseArray();
    if (c === '"') return parseString();
    if (c === 't' || c === 'f') return parseBool();
    if (c === 'n') return parseNull();
    if (c === '-' || (c >= '0' && c <= '9')) return parseNumber();
    error(`Unexpected character '${c}'`);
  };

  const parseObject = () => {
    i++;                                                              // step 2: consume '{'
    skipWs();
    const obj = {};
    if (src[i] === '}') { i++; return obj; }                          // empty fast-path
    while (true) {
      skipWs();
      if (src[i] !== '"') error('Expected string key');
      const key = parseString();
      skipWs();
      if (src[i] !== ':') error("Expected ':'");
      i++;
      obj[key] = parseValue();
      skipWs();
      if (src[i] === ',') { i++; continue; }
      if (src[i] === '}') { i++; return obj; }
      error("Expected ',' or '}'");
    }
  };

  const parseArray = () => {
    i++; skipWs();
    const arr = [];
    if (src[i] === ']') { i++; return arr; }
    while (true) {
      arr.push(parseValue());
      skipWs();
      if (src[i] === ',') { i++; continue; }
      if (src[i] === ']') { i++; return arr; }
      error("Expected ',' or ']'");
    }
  };

  const parseString = () => {
    i++;                                                              // step 3: consume opening "
    let out = '';
    while (i < src.length && src[i] !== '"') {
      if (src[i] === '\\') {
        const esc = src[++i];
        if (esc === '"' || esc === '\\' || esc === '/') out += esc;
        else if (esc === 'b') out += '\b';
        else if (esc === 'f') out += '\f';
        else if (esc === 'n') out += '\n';
        else if (esc === 'r') out += '\r';
        else if (esc === 't') out += '\t';
        else if (esc === 'u') {
          const hex = src.slice(i + 1, i + 5);
          if (!/^[0-9a-fA-F]{4}$/.test(hex)) error('Bad \\u escape');
          out += String.fromCharCode(parseInt(hex, 16));
          i += 4;
        } else error(`Bad escape \\${esc}`);
        i++;
      } else {
        out += src[i++];
      }
    }
    if (src[i] !== '"') error('Unterminated string');
    i++;
    return out;
  };

  const parseNumber = () => {
    const start = i;
    if (src[i] === '-') i++;
    while (i < src.length && src[i] >= '0' && src[i] <= '9') i++;
    if (src[i] === '.') { i++; while (src[i] >= '0' && src[i] <= '9') i++; }
    if (src[i] === 'e' || src[i] === 'E') {
      i++;
      if (src[i] === '+' || src[i] === '-') i++;
      while (src[i] >= '0' && src[i] <= '9') i++;
    }
    const n = Number(src.slice(start, i));
    if (Number.isNaN(n)) error('Bad number');
    return n;
  };

  const parseBool = () => {
    if (src.startsWith('true', i))  { i += 4; return true; }
    if (src.startsWith('false', i)) { i += 5; return false; }
    error('Bad bool');
  };

  const parseNull = () => {
    if (src.startsWith('null', i)) { i += 4; return null; }
    error('Bad null');
  };

  const result = parseValue();
  skipWs();
  if (i !== src.length) error('Unexpected trailing content');         // step 4: final guard
  return result;
}
```

**Try it yourself**

```js
jsonParse('{"a":1,"b":[true,"x\\n"]}');
// { a: 1, b: [true, 'x\n'] }

try { jsonParse('[1, 2,]'); } catch (e) { e.message; }
// 'Expected string key at position 5'  (trailing comma → expects key/value next)

try { jsonParse('1abc'); } catch (e) { e.message; }
// 'Unexpected trailing content at position 1'
```

---

## 9. Step-by-step dry run

```
Input: '{"a":1,"b":[true,"x\n"]}'   (note: \n is the 2 chars backslash+n)

i=0   parseValue → '{' → parseObject. i=1.
      skipWs. src[1]='"' ≠ '}'. Loop enter.
        parseString at i=1:
          i=2 reading 'a'. out='a'. i=3 sees '"'. i=4. return 'a'.
        skipWs. src[4]=':'. i=5.
        parseValue at i=5:
          digit → parseNumber. start=5. i=6 (one digit). Number('1')=1. return 1.
        obj.a = 1.
        skipWs. src[6]=','. i=7. continue.
        parseString at i=7: i=8 reading 'b'. i=9 '"'. i=10. return 'b'.
        skipWs. src[10]=':'. i=11.
        parseValue at i=11:
          '[' → parseArray. i=12. skipWs.
          src[12]='t' ≠ ']'. Loop:
            parseValue at i=12: 't' → parseBool. i+=4 → i=16. return true.
            skipWs. src[16]=','. i=17. continue.
            parseValue at i=17: '"' → parseString.
              i=18 sees 'x' → out='x'. i=19 sees '\\' → esc='n' (src[20]) → out+='\n'. i=21.
              src[21]='"' → i=22. return 'x\n'.
            skipWs. src[22]=']'. i=23. return [true, 'x\n'].
        obj.b = [true, 'x\n'].
        skipWs. src[23]='}'. i=24. return obj.
i=24  skipWs. i === src.length. return.

Result: { a: 1, b: [true, 'x\n'] }
```

Trailing-comma test:

```
Input: '{"a":1,}'
After consuming ',' at i=6, loop re-enters at i=7.
  skipWs. src[7]='}'. We check src[i] !== '"' → error "Expected string key at position 7".
```

---

## 10. Common confusion + traps

1. **Allowing trailing commas** — fails spec.
2. **Forgetting trailing-content check** — `parse('1abc')` silently returns `1`.
3. **Off-by-one in number parsing** — pick a convention (advance past) and stick.
4. **Not handling `\uXXXX`** — strings parse literal `\u...`.
5. **Unterminated string** — infinite loop or `undefined` arithmetic. Throw.
6. **`src.startsWith` vs `slice ===`** — both work; pick one.
7. **Maximum depth** — deeply nested JSON (`[[[...]]]`) stack-overflows the parser.

---

## 11. Senior follow-ups & variants

### Variant 1 — Reviver function
After parsing, walk result tree calling `reviver(key, value)` bottom-up. Replace nodes; `undefined` deletes. Matches native API.

### Variant 2 — Streaming parser (SAX-style)
For multi-GB inputs, parse one token at a time and emit events. Libraries: `clarinet`, `JSONStream`.

### Variant 3 — JSON5 lenient mode
Allow comments, trailing commas, single-quoted strings, unquoted keys. Each leniency is a small tweak.

### Variant 4 — Position-aware errors
Augment with line/column updates in `skipWs`/`parseString`. Real-world error UX.

### Variant 5 — Surrogate pair combining
`😀` should produce 😀 (one code point). Combine high+low surrogates in the string parser.

---

## 12. How to think aloud

> "Recursive descent, single cursor `i`. `parseValue` dispatches on `src[i]` — single-char lookahead, LL(1). One function per grammar production: object, array, string, number, bool, null. Always `skipWs` before dispatch. Check empty-container fast-path immediately after opening bracket. String parser handles escapes including `\uXXXX`. Number parser regex-style: optional `-`, digits, optional `.digits`, optional exponent — then `Number(slice)`. Final guard: `skipWs(); assert i === length`. Trap: trailing commas; trailing content; unterminated string; `\u` escapes ignored. Same shape as any LL(1) recursive-descent parser — generalizes to CSV, expression parsers, query DSLs."

---

## 13. 60-second revision

> - **Recursive descent**, single cursor `i`.
> - **`parseValue`** dispatches on `src[i]` (LL(1)).
> - **One function per production:** object, array, string, number, bool, null.
> - **Always `skipWs`** before dispatch.
> - **Fast-path** empty container after opening bracket.
> - **String escapes:** `" \ /`, `\b \f \n \r \t`, `\uXXXX`.
> - **Number:** `-? digits (.digits)? ([eE] [+-]? digits)?`. Then `Number(slice)`.
> - **Final guard:** `if (i !== src.length) throw`.
> - **Trap:** trailing commas; trailing content; unterminated string; `\u` ignored.

---

**Related:** [json-stringify-polyfill.md](./json-stringify-polyfill.md) · [trie.md](./trie.md) · [`09-recursion/recursive-descent.md`](../09-recursion/recursive-descent.md) · [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)

**Concept primer:** [`concepts/recursion.md`](../../concepts/recursion.md)
