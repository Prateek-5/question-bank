# `let` per-iteration binding in for-loops

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [let-vs-var-differences.md](./let-vs-var-differences.md), [hoisting-and-scoping.md](./hoisting-and-scoping.md)
>
> **Source:** LeetCode-style closure puzzle. BFE.dev #28. Most-asked closure question in JS interview history.

---

## 1. Problem statement

Why does `for (let i = 0; i < 3; i++) setTimeout(() => log(i))` print `0 1 2` while `for (var i...)` prints `3 3 3`?

**Verification examples**

| Loop                                            | Output                                    |
|-------------------------------------------------|-------------------------------------------|
| `for (var i = 0; i < 3; i++) setTimeout(()=>log(i))`  | `3, 3, 3` (shared `i`)                    |
| `for (let i = 0; i < 3; i++) setTimeout(()=>log(i))`  | `0, 1, 2` (fresh `i` per iter)            |
| `for (const x of arr)` with closure              | works correctly                           |
| IIFE pre-ES6 fix: `(function(j){...})(i)`         | `0, 1, 2`                                  |
| `forEach((x) => ...)`                             | always worked correctly (per-call binding) |

**Constraints**
- Spec creates fresh LE per iteration via `CreatePerIterationEnvironment` (ECMA-262 §14.7.4.4).
- Block-scope alone is NOT enough — it's block-scope + cloned each iteration.
- Each closure stores `[[Environment]]` pointing at its iteration's env.

---

## 2. Plain-English restatement

For `for (let i = 0; ...)`, the spec clones the lexical environment at each iteration. So three iterations create three separate `i` bindings; each closure captures its own. For `var`, there's only one `i` in the function scope — all closures share it. By the time timers fire, the loop is done and `i = 3`.

---

## 3. Why this matters in interviews

The canonical closures puzzle. The senior twist: explain mechanically (spec wording: "per-iteration binding") not just "block-scoped".

---

## 4. Mental model

```
   for (let i = 0; i < 3; i++) { body }
   
   Spec: CreatePerIterationEnvironment
   
   Env0 = new LE with { i: 0 }
   while (cond evaluated in Env_n):
     Env_n+1 = clone(Env_n)              ← fresh LE per iteration
     body runs in Env_n+1
       closures capture Env_n+1
     step expr (i++) runs in Env_n+1
   
   Three iterations → three separate Envs → three separate i bindings.
   Each closure stores [[Environment]] pointing at ITS iteration's env.

   for (var i = 0; ...):
   ONE binding in function's VE.
   Three iterations mutate the SAME i.
   All closures share. By timer fire, i = 3.

   Pre-ES6 fix (IIFE):
   for (var i = 0; ...; ...) (function(j){ setTimeout(()=>log(j)) })(i);
   IIFE creates fresh function scope per iter → fresh j.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Is "let is block-scoped" enough explanation, or do you need more?
> 2. What does `forEach` do that prevents the var-loop bug?
> 3. Does `for (const x of arr)` work? Why doesn't `const` clash with iteration?

---

## 6. Brute force — walked through

### Wrong attempt 1: "closures share scope"
Correct for `var`, wrong for `let`. Incomplete.

### Wrong attempt 2: "let is block-scoped"
Half-answer. Block-scope alone wouldn't fix it (still one `i` per loop). Need per-iteration cloning.

### Wrong attempt 3: assume `forEach` fix
Works but obscures the spec mechanism. Use it in code; explain mechanism in interview.

---

## 7. The unlocking insight

> **`for (let i; ...)` creates a FRESH lexical environment per iteration via spec's `CreatePerIterationEnvironment`. Each closure captures its iteration's env. `var` has one binding in function VE; all closures share final value.**

Three properties:

1. **Fresh LE per iteration** — load-bearing.
2. **Closure captures environment** — that iteration's env.
3. **Block-scope alone insufficient** — need cloning + block-scope.

---

## 8. Solution (annotated)

```js
function scheduleWithLet() {
  for (let i = 0; i < 3; i++) {                                       // step 1: fresh LE per iter
    setTimeout(() => console.log('let:', i), 0);                       // closure captures iter's LE
  }
}

function scheduleWithVar() {
  for (var i = 0; i < 3; i++) {                                       // step 2: shared VE.i
    setTimeout(() => console.log('var:', i), 0);                       // all closures share
  }
}

function scheduleWithIIFE() {
  for (var i = 0; i < 3; i++) {                                       // step 3: pre-ES6 fix
    (function (j) {
      setTimeout(() => console.log('iife:', j), 0);                    // fresh j per call
    })(i);
  }
}

scheduleWithLet();    // let: 0, let: 1, let: 2
scheduleWithVar();    // var: 3, var: 3, var: 3
scheduleWithIIFE();   // iife: 0, iife: 1, iife: 2
```

**Try it yourself**

```js
// for-of and for-in also create fresh bindings
for (const x of [1, 2, 3]) {
  setTimeout(() => console.log(x), 0);
}
// Output: 1, 2, 3

// const in for-let header doesn't work (header reassigns)
// for (const i = 0; i < 3; i++) {}   // TypeError: assign to const (i++)

// Workaround for legacy var
for (var i = 0; i < 3; i++) {
  const j = i;                                                         // fresh body-scope const
  setTimeout(() => console.log(j), 0);
}
// Output: 0, 1, 2  (const j per iter body)
```

---

## 9. Step-by-step dry run

```
scheduleWithLet():

Loop entry:
  Env0 = LE { i: 0 }

Iter 1:
  Env1 = clone(Env0) = { i: 0 }
  Body in Env1:
    setTimeout(() => log(i))    — arrow captures Env1
    T1 scheduled. T1.[[Environment]] = Env1.
  Step: i++ in Env1 → Env1.i = 1
  Clone Env1 → Env2 (for next cond check)

Iter 2:
  Env2 = clone with { i: 1 }
  Body: schedule T2 capturing Env2.
  Step: Env2.i = 2.

Iter 3:
  Env3 = { i: 2 }
  Schedule T3 capturing Env3.
  Step: Env3.i = 3. Cond fails. Exit.

Timers fire:
  T1 reads i from Env1 → 0   → 'let: 0'
  T2 reads i from Env2 → 1   → 'let: 1'
  T3 reads i from Env3 → 2   → 'let: 2'

scheduleWithVar():

VE = { i: 0 }   (function scope; ONE binding)

Iter 1: schedule T1 closing over VE.
Iter 2: schedule T2 closing over VE.
Iter 3: schedule T3 closing over VE.
Step: i goes 0 → 1 → 2 → 3.

Timers fire:
  T1 reads VE.i → 3
  T2 reads VE.i → 3
  T3 reads VE.i → 3
Output: var: 3, 3, 3.
```

---

## 10. Common confusion + traps

1. **"Block scope fixes it"** — incomplete; need per-iteration cloning.
2. **`forEach` has the bug** — no, never did (per-call args).
3. **`for-of` doesn't clone** — it does (per-iteration binding).
4. **`for (const i)` header** — TypeError (i++ rebinds).
5. **Babel transpilation cost** — Babel emits IIFE per iter for ES5 target.
6. **V8 always clones** — elides when no closure captures.
7. **`var` + IIFE for legacy** — was the pre-ES6 fix.

---

## 11. Senior follow-ups & variants

### Variant 1 — Replace `setTimeout` with `Promise.resolve().then`
Same fix applies; bug isn't timer-specific.

### Variant 2 — Body-scope `const`
`for (var i; ...) { const j = i; setTimeout(()=>log(j)) }` — fresh body scope per iter.

### Variant 3 — `for-of` async iter
`for (const chunk of asyncIter) { await process(chunk) }` — each iter's chunk isolated.

### Variant 4 — `forEach` vs for-let
Both work; `forEach` via per-call args, for-let via per-iter LE.

### Variant 5 — Performance
V8 elides per-iter env when body has no closures. Don't prematurely de-`let`.

---

## 12. How to think aloud

> "Spec wording: `for (let i = 0; ...)` invokes `CreatePerIterationEnvironment`. Each iteration creates a FRESH lexical environment cloned from the previous. Closures created in the body capture THAT iteration's env via [[Environment]]. So three iterations → three separate `i` bindings → timers print 0, 1, 2. With `var`, one binding in function VE; all closures share; by timer fire `i = 3`. Block-scope ALONE doesn't fix it — block-scope + cloning does. Pre-ES6 fix was IIFE (creates fresh function scope per iter); Babel emits this when transpiling let to ES5. `forEach`/`map` never had the bug — callback args are fresh per invocation."

---

## 13. 60-second revision

> - **`for (let i; ...)`** → fresh LE per iter via `CreatePerIterationEnvironment`.
> - **`for (var i; ...)`** → ONE binding in function VE; closures share.
> - **Block-scope ALONE insufficient** — need cloning.
> - **Each closure** stores [[Environment]] pointing at its iter's LE.
> - **Pre-ES6 fix:** IIFE (`(function(j){...})(i)`) — Babel emits this.
> - **`forEach`/`for-of`** never had the bug — per-call/per-iter args.
> - **`for (const i;)`** TypeError (i++).
> - **Trap:** "block-scope fixes" (half-answer); `var` + closures in async loops.

---

**Related:** [let-vs-var-differences.md](./let-vs-var-differences.md) · [hoisting-and-scoping.md](./hoisting-and-scoping.md) · [`02-closures/loop-closure-var-let.md`](../02-closures/loop-closure-var-let.md) · [var-in-block.md](./var-in-block.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md), [`concepts/closures.md`](../../concepts/closures.md)
