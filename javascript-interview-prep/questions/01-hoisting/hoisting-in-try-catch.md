# Hoisting and scope inside `try`/`catch`

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md), [let-vs-var-differences.md](./let-vs-var-differences.md)
>
> **Source:** BFE.dev, "You Don't Know JS". Node error-handling deep dives.

---

## 1. Problem statement

`try { ... } catch (err) { ... }` has THREE layered scopes: the try block, the catch parameter's own scope, and the catch body.

**Verification examples**

```js
function f() {
  try {
    var a = 1;                                                          // var → escapes try, lives in f's VE
    let b = 2;                                                          // let → block-scoped to try
  } catch (err) {                                                        // err has its OWN scope
    var c = 3;                                                           // var → escapes catch-body, into f's VE
    let d = 4;                                                           // let → block-scoped to catch body
  }
  console.log(a);                                                        // 1 (or undefined if try threw)
  console.log(c);                                                        // 3 (only if catch ran) else undefined
  // console.log(b);   // ReferenceError — block-scoped to try
  // console.log(d);   // ReferenceError — block-scoped to catch
  // console.log(err); // ReferenceError — bound in catch param scope only
}
```

| Scope                            | Holds                                                |
|----------------------------------|-------------------------------------------------------|
| Function VE                      | `var a, var c` (escaped from blocks)                 |
| `try` block LE                   | `let b`                                               |
| `catch` param scope (its own LE) | `err`                                                 |
| `catch` body LE                  | `let d`                                               |

**Constraints**
- `var` ignores `try`/`catch` block boundaries.
- `let`/`const` are block-scoped to their respective block.
- `catch (err)` parameter has its OWN scope; not in function VE.
- Optional catch binding `catch {}` (ES2019) — no `err` param.

---

## 2. Plain-English restatement

`try`/`catch` looks like one block but has three scope layers. `var` leaks across all three to the function scope. `let`/`const` stay in their own block. The `catch (err)` parameter has its own scope between the catch body and the function — `err` is invisible outside the catch.

---

## 3. Why this matters in interviews

Tests scope-chain precision. Subtle bug source — `var result` inside `try` survives the block on purpose; `let result` doesn't.

---

## 4. Mental model

```
   function f() {                              ← function-scope (VE)
     try {                                     ← try block LE
       var a;                                  ← LIFTED to f's VE
       let b;                                  ← stays in try LE
     } catch (err) {                           ← catch PARAM scope (LE)
       var c;                                  ← LIFTED to f's VE
       let d;                                  ← stays in catch BODY LE
     }                                            (yes, catch body is yet another LE
                                                   inside the param scope)
   }
   
   Three scopes for try/catch:
     1. try block LE          → let b
     2. catch param scope LE  → err
        catch body LE         → let d (block inside param scope)
   
   var ignores ALL three; lives in f's VE.

   Optional catch binding (ES2019):
     try { ... } catch { /* no err */ }
     - no parameter scope needed.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `try { var a = 1; } catch {}`, is `a` accessible outside?
> 2. After `try { } catch (err) { var b = err.message; }`, is `b` accessible outside?
> 3. Is `err` accessible outside the catch block?

---

## 6. Brute force — walked through

### Wrong attempt 1: "try/catch is one block"
Three layered scopes.

### Wrong attempt 2: "var in catch is scoped to catch"
Function-scoped — leaks out.

### Wrong attempt 3: "err is in function scope"
Has its own param scope.

---

## 7. The unlocking insight

> **Three layered scopes: try LE, catch param LE, catch body LE. `var` ignores all three (escapes to function VE). `let`/`const` stay in their immediate block. `err` is in catch param LE — invisible outside.**

Three properties:

1. **Three layered scopes** — try, catch param, catch body.
2. **`var` leaks** through all three.
3. **`err` lives in param scope** — distinct from body.

---

## 8. Solution (annotated)

```js
function processData(input) {
  let result;                                                          // step 1: function-scope let

  try {
    var x = parseInt(input);                                            // step 2: var leaks to function scope
    let y = x * 2;                                                      // step 3: try-block let, dies at } 
    result = y;
  } catch (err) {                                                       // step 4: err in param scope
    var fallback = 0;                                                   // step 5: var leaks to function scope
    let logged = err.message;                                           // step 6: catch-body let, dies at }
    result = fallback;
    console.log(logged);
  }

  console.log(x, fallback);                                              // accessible (var leaked)
  // console.log(y, logged, err);   // ReferenceError each
  return result;
}
```

**Try it yourself**

```js
// var captures error info beyond block
function safeParse(s) {
  try {
    return { ok: true, value: JSON.parse(s) };
  } catch (err) {
    var msg = err.message;                                              // var captured to function scope
    return { ok: false, error: msg };
  }
}

// Optional catch binding (ES2019)
try {
  doRiskyThing();
} catch {                                                                // no err param
  console.log('failed');
}

// Catch param vs body scope
function demo() {
  try { throw new Error('x'); }
  catch (e) {
    let e2 = 'shadow';                                                   // e is in PARAM scope; let e2 in BODY scope
    console.log(e, e2);                                                   // Error: x, shadow
  }
  // console.log(e);   // ReferenceError
}
```

---

## 9. Step-by-step dry run

```
function f() {
  try {
    var a = 1;
    let b = 2;
  } catch (err) {
    var c = 3;
    let d = 4;
  }
  console.log(a, c);
}

CREATION phase (function f):
  VE: { a: undefined, c: undefined }            (var hoisted past blocks)
  LE: {}

EXECUTION phase:
  try {
    enter try block (LE_try: { b: <uninitialized> })
    var a = 1   → f.VE.a = 1
    let b = 2   → LE_try.b = 2
  } exit try block (LE_try popped; b gone)
  
  (no exception, so catch never runs)
  
  console.log(a, c)   → f.VE.a = 1, f.VE.c = undefined (catch never ran)

Now imagine try threw:
  try { throw new Error('boom'); }
  catch { enter catch param LE (LE_cparm: { err: <error obj> })
          enter catch body LE (LE_cbody: { d: <uninit> })
          var c = 3 → f.VE.c = 3
          let d = 4 → LE_cbody.d = 4
          exit body (LE_cbody popped)
          exit param scope (LE_cparm popped; err gone)
  }
  
  console.log(a, c) → undefined (var a was hoisted but never assigned because throw happened), 3
```

---

## 10. Common confusion + traps

1. **One block** — three scopes.
2. **`var` block-scoped here** — function-scoped (leaks).
3. **`err` in function scope** — param scope only.
4. **`var` and `let` of same name in try and catch** — `let` in one block doesn't collide with var in function.
5. **Optional catch binding** — ES2019; no param needed.
6. **`finally` is its own block too** — fourth scope layer.
7. **Re-declaring `err` in catch body** — separate scope; allowed.

---

## 11. Senior follow-ups & variants

### Variant 1 — `finally` scope
Yet another block LE.

### Variant 2 — Optional catch binding
`try {} catch {}` — no err param scope.

### Variant 3 — Re-throw pattern
`catch (err) { throw err }` — re-uses param.

### Variant 4 — Error subclassing
Custom errors propagate through catch like any object.

### Variant 5 — Async / await + try/catch
Wrap awaits in try/catch; same scope rules apply.

---

## 12. How to think aloud

> "try/catch has THREE layered scopes — the try block LE, the catch parameter scope LE (where `err` lives), and the catch body LE (a separate block inside param scope). `var` ignores ALL three and leaks to the function VE — that's why `var x = 1` inside `try` is accessible outside. `let`/`const` are block-scoped to their immediate block — `let b` inside try dies at `}`. The catch parameter `err` is in its own param scope, distinct from both function and catch body — invisible outside the catch. Optional catch binding (ES2019) `catch {}` removes the param. `finally` is yet another block. Trap: thinking try/catch is one block; assuming var is block-scoped; thinking err is function-scoped."

---

## 13. 60-second revision

> - **Three layered scopes:** try LE, catch param LE, catch body LE.
> - **`var` leaks** through all three to function VE.
> - **`let`/`const`** stay in their immediate block.
> - **`err` in catch param scope** — invisible outside.
> - **Optional catch binding** (ES2019): `catch {}` — no param.
> - **`finally`** is fourth block layer.
> - **Use `var` deliberately** to capture error info beyond block.
> - **Trap:** "try/catch is one block"; var block-scoped; err in function scope.

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [var-in-block.md](./var-in-block.md) · [let-vs-var-differences.md](./let-vs-var-differences.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
