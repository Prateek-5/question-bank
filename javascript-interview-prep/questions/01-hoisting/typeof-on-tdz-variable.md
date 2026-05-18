# `typeof` on a TDZ Variable

## Source / Origin
- Subtle ES2015 spec change: `typeof undeclared` was traditionally safe; `typeof tdz-variable` now throws.
- Asked at: Razorpay, Atlassian, Cloudflare — favorite output-prediction trap.
- Concept reference: `concepts/hoisting.md`.

## Why this question matters in interviews
Pre-ES2015, `typeof someName` was the *one* "safe" reference — it returned `'undefined'` even if the name didn't exist. That's why old code used `typeof window !== 'undefined'` for feature detection. ES2015 broke this for TDZ-bound names: `typeof letDeclaredLater` *throws*. Senior bar: you can name this exception, predict it, and explain why the spec did it (TDZ is supposed to catch real "use before declared" bugs).

## Concepts involved

### Syntax to lock in
```js
// Pre-ES2015 behavior — safe for undeclared
typeof undeclaredName;     // 'undefined' — does NOT throw

// var hoists — typeof is safe BEFORE assignment
typeof v;                  // 'undefined'
var v = 1;
typeof v;                  // 'number'

// let / const in TDZ — typeof THROWS
typeof l;                  // ReferenceError — Cannot access 'l' before initialization
let l = 1;

// class in TDZ — typeof THROWS
typeof C;                  // ReferenceError
class C {}

// Function declaration — fully hoisted
typeof f;                  // 'function'
function f() {}
```

### Edge cases / interview traps
1. **`typeof` is no longer universally safe.** Only safe for genuinely undeclared identifiers; throws for TDZ-bound.
2. **`var` survives** — variable is hoisted and bound to `undefined`; `typeof` returns `'undefined'`.
3. **`let` / `const` / `class`** — TDZ. `typeof` throws.
4. **Function declaration** — fully hoisted including body; `typeof` returns `'function'`.
5. **Function expression** — only the variable hoists (as `undefined` for `var`, TDZ for `let`/`const`).
6. **`typeof` of an undeclared property** — `typeof obj.foo` is fine (returns `'undefined'`).
7. **Conditional `typeof` for feature detection** — broken pattern post-ES2015 for things declared by `let`/`const`. Use `typeof` on `globalThis.X` instead: `typeof globalThis.WebSocket !== 'undefined'`.

## Mental Model

Pre-ES2015:

```
   typeof was a "soft" reference: didn't trigger ReferenceError
   for unbound names
   → returned 'undefined' for both undeclared and var-undefined
```

ES2015 introduced TDZ — a *third* state:

```
                  ┌──────────────────┐
                  │ binding states   │
                  ├──────────────────┤
                  │ undeclared       │ ← typeof safe → 'undefined'
                  │ TDZ (let/const)  │ ← typeof THROWS
                  │ undefined (var)  │ ← typeof safe → 'undefined'
                  │ initialized      │ ← typeof returns the type
                  └──────────────────┘

   The bind has happened (let/const exists in this scope), it just isn't initialized.
   Spec: any reference at all during TDZ throws. `typeof` is a reference. Throws.
```

## Why interviewers care

- **Spec corner-case awareness.**
- **Hoisting nuance** — distinguishing var, let, const, class, function-decl, function-expr.
- **Feature-detection idiom literacy** — knowing `typeof window` is *still* fine but `typeof someLet` isn't.

## Common beginner confusion

- **"`typeof` never throws."** It does for TDZ-bound names.
- **"`let` hoists like `var`, just to `undefined`."** It hoists to TDZ — strictly different.
- **"`typeof` works on classes."** Only after the class declaration.
- **"`typeof` is the only safe access."** Was true pre-2015 for genuinely undeclared names. Still true *only* for undeclared, not for declared-but-TDZ.

## Brute force approach

```js
// Feature detection that BREAKS in ESM modules where someLib is let/const
if (typeof someLib !== 'undefined') someLib.init();
// → ReferenceError if `someLib` is declared via let/const later
```

## Optimal approach

For feature detection, query `globalThis`:

```js
if (typeof globalThis.someLib !== 'undefined') globalThis.someLib.init();
// Property access on globalThis never throws; returns undefined for missing
```

Or `in` operator:

```js
if ('someLib' in globalThis) globalThis.someLib.init();
```

## Solution (JavaScript)

```js
// Live demo of the 4 cases
function demo() {
  try { console.log(typeof a); } catch (e) { console.log('a:', e.message); }
  try { console.log(typeof b); } catch (e) { console.log('b:', e.message); }
  try { console.log(typeof c); } catch (e) { console.log('c:', e.message); }
  try { console.log(typeof d); } catch (e) { console.log('d:', e.message); }
  console.log(typeof e);                 // 'function'

  var a = 1;
  let b = 2;
  const c = 3;
  class d {}
  function e() {}
}
demo();
// Output:
//   a: undefined            ← var-hoisted, undefined slot
//   b: Cannot access 'b'... ← TDZ
//   c: Cannot access 'c'... ← TDZ
//   d: Cannot access 'd'... ← TDZ
//   function                ← fully hoisted
```

## Step-by-step dry run

```js
console.log(typeof x);   // 'undefined'  (truly undeclared — global x doesn't exist)
console.log(typeof y);   // ReferenceError — y is let-declared below; in TDZ
let y = 1;
```

```
phase 1 (parse): collect lexical bindings
  scope has `y` as let, TDZ until line `let y = 1`

phase 2 (run):
  line 1: typeof x  → x is not declared in any scope → returns 'undefined' (no throw)
  line 2: typeof y  → y is declared, in TDZ → REFERENCE ERROR
  (line 3 never reached)
```

Feature-detection fix:

```js
// BAD (post-2015):
if (typeof SomeLib !== 'undefined') ...
let SomeLib;                              // wherever — still TDZ at the if

// GOOD:
if (typeof globalThis.SomeLib !== 'undefined') ...
```

## How to think aloud in the interview

> "`typeof undeclared` is `'undefined'` and doesn't throw — that's the pre-ES2015 'one safe reference' property. ES2015 added TDZ for `let`/`const`/`class`; `typeof` on a TDZ-bound name *does* throw, because any reference during TDZ is illegal. So `typeof someLet` is no longer a safe feature-detection. For globals, use `typeof globalThis.X !== 'undefined'` or `'X' in globalThis`. `var`, function decl, and undeclared names are still safe."

## Important takeaways

- **`typeof` of TDZ-bound name THROWS.**
- **`typeof` of truly undeclared name is `'undefined'`** (and doesn't throw).
- **`var` hoists to `undefined` slot** — typeof safe.
- **Function declaration fully hoists** — typeof `'function'`.
- **Feature detection**: use `globalThis.X` or `'X' in globalThis`.

## Variants

- **Module-scope vs global** — both have TDZ for `let`/`const`.
- **`typeof` of property** — `typeof obj.foo` is fine even if `foo` not present (returns `'undefined'`).
- **`typeof` in strict mode** — same behavior; TDZ throws.
- **Dead-code elimination** — bundlers may strip `typeof someLet === 'undefined'` checks; result depends on tooling.
- **`window` vs `globalThis`** — `window` only in browsers; `globalThis` works everywhere.

## Revision notes

```
typeof rules:
  typeof undeclared           → 'undefined'   (no throw)
  typeof var-before-assign    → 'undefined'   (var hoists, slot = undefined)
  typeof let-before-init      → THROWS        (TDZ)
  typeof const-before-init    → THROWS        (TDZ)
  typeof class-before-decl    → THROWS        (TDZ)
  typeof function-decl        → 'function'    (fully hoisted)
  
Feature detection idiom:
  pre-2015:  typeof X !== 'undefined'   (worked for any case)
  post-2015: if X might be let/const, use:
             typeof globalThis.X !== 'undefined'
             or 'X' in globalThis
```
