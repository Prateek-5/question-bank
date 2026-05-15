# Implement `JSON.parse` — recursive-descent parser (simplified)

## Source
- Compiler-style machine-coding problem (FAANG senior rounds, BFE.dev #21, Frontend Masters parser series).
- Pairs with the JSON.stringify polyfill — interviewers love asking both back-to-back.

## Why this question matters in interviews
JSON.parse is the smallest **real parser** you can implement under interview pressure. It tests **tokenization vs parsing**, **recursive descent**, **lookahead-by-one**, **error recovery**, and the ability to think about a string as a stream with a cursor. You don't need shift/reduce machinery — JSON is unambiguous LL(1), so a 60-80 line hand-rolled parser is the canonical answer. Backend engineers see this skill applied in CSV/TSV parsers, log-line parsers, environment-variable expanders, template languages, mini-DSLs for config files. Once you've written one recursive-descent parser, the rest are easy.

## Concepts involved

### Syntax to lock in
```js
function parse(s) {
  let i = 0;
  const skipWs = () => { while (' \n\r\t'.includes(s[i])) i++; };

  const value = () => {
    skipWs();
    const c = s[i];
    if (c === '{') return object();
    if (c === '[') return array();
    if (c === '"') return string();
    if (c === 't' || c === 'f') return bool();
    if (c === 'n') return nullLit();
    if (c === '-' || (c >= '0' && c <= '9')) return number();
    throw new SyntaxError(`Unexpected ${c} at ${i}`);
  };

  const object = () => {
    i++; skipWs();
    const o = {};
    if (s[i] === '}') { i++; return o; }
    while (true) {
      skipWs();
      const k = string();
      skipWs();
      if (s[i++] !== ':') throw new SyntaxError(`Expected : at ${i}`);
      o[k] = value();
      skipWs();
      if (s[i] === ',') { i++; continue; }
      if (s[i] === '}') { i++; return o; }
      throw new SyntaxError(`Expected , or } at ${i}`);
    }
  };

  // similar for array(), string(), number(), bool(), nullLit()...
  const result = value();
  skipWs();
  if (i !== s.length) throw new SyntaxError(`Unexpected trailing content at ${i}`);
  return result;
}
```

### Runtime / engine behavior
- The parser maintains a **single cursor `i`** into the source string. All sub-parsers consume from `s[i]` and advance `i`. This is the canonical recursive-descent pattern — no explicit token stream needed because JSON's lexemes are short.
- Each parser function (`object`, `array`, `string`, `number`, `bool`, `nullLit`) corresponds to a **grammar production**. The dispatch in `value()` is the single-character lookahead that makes this LL(1).
- Numbers in JSON are stricter than JS: no leading `+`, no leading zeros (except `0` and `0.x`), no hex, no `Infinity`. Real parsers enforce this; interview parsers usually skip the validation and rely on `Number(str)`.
- Strings need **escape handling**: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\uXXXX`. Surrogate pairs in `\uXXXX\uXXXX` form must be combined into a single code point.
- Whitespace per spec: space, tab, LF, CR. Nothing else (no Unicode whitespace).

### Edge cases (these are the interview traps)
1. **Trailing comma** — JSON does not allow `[1, 2,]` or `{"a":1,}`. After consuming `,`, expect another value. Many candidates accidentally allow trailing commas.
2. **Trailing content** — `parse("{} junk")` should throw. After parsing the top-level value, skip whitespace and assert `i === s.length`.
3. **Empty containers** — `[]` and `{}` are the base cases. Check immediately after consuming the opening bracket.
4. **String escapes** — `\u00XX`, `\n`, `\\`, `\"` minimum. Don't forget `\/` (valid in JSON, optional). For `\uXXXX`, parse 4 hex digits, build the code unit via `String.fromCharCode`.
5. **Number edge cases** — `-0`, `1e10`, `1.5e-3`, `0.1`. Easiest path: regex-match the number lexeme, then `Number(matched)`. Don't reinvent IEEE 754 parsing.
6. **Number followed by garbage** — `parse("1abc")`. The number lexeme is `"1"`; after parsing, `i` points at `a`; the top-level "no trailing content" check catches it.
7. **Unterminated string / unclosed bracket** — must throw with a useful position. Cursor-past-end on `s[i]` returns `undefined`, which all the comparisons fail on; turn that into an explicit error.
8. **Whitespace policy** — only space/tab/CR/LF per RFC 8259. Don't accept `\v` or non-breaking space.
9. **Duplicate keys** — spec is silent; most parsers (and the native one) take the last value. Don't error.
10. **Maximum depth** — recursive descent stack-overflows on deeply nested input (e.g., `[[[...]]]` with 10k levels). The native parser has a depth limit; interview parsers usually don't.

## Brute force approach
Two passes: tokenize the entire string into an array of tokens, then build the parser over that token stream. Cleaner mental model but more allocations. For an interview the single-cursor recursive descent is preferred — less code, easier to talk through. Mention the tokens approach if asked about compiler-style parsing for larger languages.

Worst non-starter: `Function('return ' + s)()` or `eval(s)`. Mention as a non-answer — interviewer wants the parser.

## Optimal approach
Single-pass, single-cursor recursive descent. One function per grammar production. ~80 lines. O(n) time and O(depth) memory.

## Solution (JavaScript)

```js
/**
 * Recursive-descent JSON parser (subset, no surrogate-pair combining, no
 * strict number validation — interview shape).
 * @param {string} src
 * @returns {*}
 */
function jsonParse(src) {
  let i = 0;

  const error = (msg) => { throw new SyntaxError(`${msg} at position ${i}`); };
  const skipWs = () => { while (i < src.length && ' \n\r\t'.includes(src[i])) i++; };

  const parseValue = () => {
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
    i++; // consume '{'
    skipWs();
    const obj = {};
    if (src[i] === '}') { i++; return obj; }
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
    i++; // consume '['
    skipWs();
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
    i++; // consume opening '"'
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
  if (i !== src.length) error('Unexpected trailing content');
  return result;
}
```

## Step-by-step dry run

Input: `'{"a":1,"b":[true,"x\\n"]}'`

Trace:
- `parseValue` at i=0: sees `{` → `parseObject`. i=1.
- skipWs (none). src[1] is `"`, not `}`. Loop enter.
  - `parseString` at i=1: i=2 reading content. `a` appended. i=3 sees `"` → close. i=4. Return `"a"`.
  - skipWs. src[4]=`:`. i=5.
  - `parseValue` at i=5: `1` is digit → `parseNumber`. i=6 (one digit). Return `1`. `obj.a = 1`.
  - skipWs. src[6]=`,`. i=7. continue.
  - `parseString` at i=7: → `"b"`. i=10.
  - skipWs. src[10]=`:`. i=11.
  - `parseValue` at i=11: `[` → `parseArray`. i=12.
    - skipWs. src[12]=`t` ≠ `]`. Loop enter.
      - `parseValue` at i=12: `t` → `parseBool`. `true`. i=16.
      - skipWs. src[16]=`,`. i=17. continue.
      - `parseValue` at i=17: `"` → `parseString`. content `x`, then escape `\n` → newline char appended. i=22 sees `"`. i=23. Return `"x\n"`.
      - skipWs. src[23]=`]`. i=24. Return `[true, "x\n"]`.
  - `obj.b = [true, "x\n"]`.
  - skipWs. src[24]=`}`. i=25. Return obj.
- skipWs. i === src.length. Return.

Result: `{ a: 1, b: [true, 'x\n'] }`.

Error case: `'{"a":1,}'` — after consuming `,` at the trailing-comma position, loop expects a string key next, sees `}`, throws.

## Important takeaways

**Syntax to memorize**
- Single cursor `i` shared across all sub-parsers.
- `parseValue` dispatches on `s[i]` — single-char lookahead.
- `skipWs` before every dispatch.
- Open-bracket-then-empty fast-path: check for closing bracket immediately after opening.
- Final check: `skipWs(); if (i !== src.length) throw` — rejects trailing junk.

**Patterns to reuse**
- Recursive descent generalizes to **any LL(1) grammar**: simple expression parsers, query DSLs, template engines, cron expression parsers.
- Single-cursor + helper functions is the simplest implementation. For larger grammars, switch to a token stream with a `peek`/`advance` API.

**Common mistakes**
- Allowing trailing commas (`[1,]`) — fails spec.
- Forgetting the "no trailing content" check — `parse("1abc")` silently returns `1`.
- Off-by-one in number parsing — leaving `i` past the last digit vs at the last digit. Pick a convention (advance past) and stick to it.
- Not handling `\uXXXX` escapes — strings with Unicode escapes parse as literal `\u...`.
- Not throwing on unterminated string (infinite loop or `undefined` arithmetic).
- Confusing `src.startsWith('true', i)` with `src.slice(i, i+4) === 'true'` (both work; pick one).

**Related questions**
- JSON.stringify polyfill (inverse).
- CSV parser (different separators, optional quoting).
- Expression parser (arithmetic + precedence — Pratt parser).
- URL query string parser.

## Variants

1. **With reviver** (matches native API) — after parsing, walk the result tree calling `reviver(key, value)` on each node bottom-up. Replace nodes with the reviver's return value; `undefined` deletes.

2. **Streaming parser** — for huge JSON inputs (multi-GB log dumps), parse one token at a time and emit events (SAX-style). Libraries like `clarinet` or `JSONStream` do this. Out of interview scope but worth name-dropping.

3. **Lenient JSON5** — allow comments, trailing commas, single-quoted strings, unquoted keys. Useful for config files. Each leniency is a small tweak to the same parser.

4. **Position tracking for errors** — augment with line/column numbers updated in `skipWs`/`parseString`. Worth mentioning if interviewer asks about real-world error UX.

## Revision notes

> **JSON.parse polyfill — 90 second recap**
> - Recursive descent, single cursor `i`.
> - `parseValue` dispatches on `s[i]` (LL(1) single-char lookahead).
> - Productions: object, array, string, number, bool, null.
> - Always `skipWs` before dispatch; check fast-path empty container right after opening bracket.
> - String escapes: `"`, `\`, `/`, `b f n r t`, `\uXXXX`. Throw on bad escape.
> - Final guard: `skipWs(); if (i !== src.length) throw`.
> - Spec-strict: no trailing commas, no leading zeros, only space/tab/CR/LF whitespace.
> - Trap: trailing comma, trailing content, unterminated string, unhandled `\u` escapes.
> - Same shape as any LL(1) recursive-descent parser.
