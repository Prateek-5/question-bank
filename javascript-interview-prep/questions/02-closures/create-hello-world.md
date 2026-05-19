# Return a function that returns "Hello World"

> **Difficulty:** Easy   |   **Time:** ~5 min   |   **Prereqs:** none (this *is* the prereq for the closures section)
>
> **Source:** [LeetCode 2667 — Create Hello World Function](https://leetcode.com/problems/create-hello-world-function/)

---

## 1. Problem statement

**Signature**
```ts
function createHelloWorld(): (...args: any[]) => "Hello World";
```

**Input / Output examples**

| Call                                        | Returns                |
|---------------------------------------------|------------------------|
| `const f = createHelloWorld(); f();`        | `"Hello World"`        |
| `f(1, 2, 3, {}, [])`                        | `"Hello World"` (args ignored) |
| `createHelloWorld()();`                     | `"Hello World"`        |
| `createHelloWorld() === createHelloWorld()` | `false` (different function instances each time) |

**Constraints**
- `createHelloWorld` must return a **function**, not a string.
- The returned function accepts any number/type of arguments and ignores them.
- Always returns the literal `"Hello World"`.

---

## 2. Plain-English restatement

The interviewer asks: write a function whose only job is to *return another function*. That inner function, when called, returns the string `"Hello World"` no matter what you pass to it. It's the smallest possible higher-order function exercise — five lines of code that test whether you grasp "a function can return a function."

---

## 3. Why this matters in interviews

This is the universal closure warm-up. In five lines, the interviewer checks three things at once: (1) a function can *return* a function, (2) the inner function captures the surrounding lexical scope, (3) that scope survives after the outer call returns. Every closure-heavy pattern you'll see later — debounce, throttle, memoize, once, currying, private state — is a 5× bigger version of this exact shape. Getting fluent in under 60 seconds gives you a clean runway into the harder closures problems.

---

## 4. Mental model

Think of `createHelloWorld` as a **factory machine** that produces single-use greeting cards. You press the button (call `createHelloWorld()`) and out pops a fresh card-printer. Press the card-printer's button (call the returned function) and out comes the card: `"Hello World"`.

```
   createHelloWorld()
        │
        └──► returns ──► function () { return "Hello World"; }
                              │
                              └──► returns ──► "Hello World"

   Two call sites:
      createHelloWorld()    ← produces the printer
      printer()             ← produces the greeting
```

The captured scope here is *empty* — the inner function doesn't read any variable from the outer. But the **mechanism** (LE → returned function → captured scope) is identical to every other closure problem.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `createHelloWorld()` (just one set of parens) return — a string or a function?
> 2. What does `createHelloWorld()(1, 2, 3)` return?
> 3. If you call `createHelloWorld()` twice and compare the two results with `===`, are they equal?

---

## 6. Brute force — walked through

There isn't a real "brute force vs optimal" split here — the problem *is* the answer. But there are predictable wrong attempts:

### Wrong attempt 1: return the string directly

```js
function createHelloWorld() { return "Hello World"; }
```

What's wrong? `createHelloWorld()` is now a string, not a function. The contract requires a function. Caller would write `createHelloWorld()()` and get a `TypeError: "Hello World" is not a function`.

### Wrong attempt 2: take args at the outer layer

```js
function createHelloWorld(...args) { return "Hello World"; }
```

The prompt says the *returned* function is variadic, not the factory. Read the I/O table carefully — args go to the inner call site, not the outer.

### Wrong attempt 3: stash on a global

```js
globalThis.HELLO = "Hello World";
function createHelloWorld() { return () => globalThis.HELLO; }
```

Works but defeats the closure exercise. Reject — the test is whether you can produce a closure, not whether you can find a globally-scoped string.

---

## 7. The unlocking insight

> **A function literal evaluated inside another function captures the outer scope, even when it doesn't read any variable from it.**

When `createHelloWorld()` is called, JavaScript creates a fresh **lexical environment** (LE) for it. Inside that LE, the engine evaluates the inner `function () { return "Hello World"; }` literal. The resulting function object carries an internal slot, `[[Environment]]`, that points at the outer LE. Returning this function transfers ownership of the captured scope out of the call. Even though the inner function reads no outer variable here, the *closure mechanism* is identical — and that mechanism is what every subsequent closure problem builds on.

Two consequences fall out immediately:

1. **Two factory calls return two different function instances.** Each call creates a fresh LE and a fresh function object with `[[Environment]]` pointing at its own LE. `createHelloWorld() === createHelloWorld()` is `false`.
2. **Args go to the inner function.** The outer just produces the function; the inner is where call-site arguments arrive. The inner uses a rest parameter `(...args)` (or no params at all) and ignores them.

---

## 8. Solution (annotated)

```js
var createHelloWorld = function () {        // step 1: the factory — takes no args
  return function (...args) {                // step 2: returns a function that accepts (and ignores) any args
    return "Hello World";                    // step 3: always returns the literal greeting
  };
};
```

**Try it yourself**

```js
const f = createHelloWorld();
console.log(f());                  // "Hello World"
console.log(f(1, 2, 3, {}, []));   // "Hello World"  (args ignored)
console.log(createHelloWorld()()); // "Hello World"  (call-and-call in one line)

const a = createHelloWorld();
const b = createHelloWorld();
console.log(a === b);              // false  (different function instances)
```

---

## 9. Step-by-step dry run

Input:

```js
const f = createHelloWorld();
console.log(f());
```

Values-first trace:

| Step | Action                          | Captured LE        | Returns           |
|------|---------------------------------|--------------------|-------------------|
| init | `createHelloWorld()`            | (created, empty)   | the inner function |
| 1    | `f()`                           | (read from heap)   | `"Hello World"`   |
| 2    | `console.log` prints            | —                  | logs `Hello World` |

<details>
<summary><b>Engine internals (click to expand)</b></summary>

1. `createHelloWorld()` is called. The engine creates a new LE `LE_outer` (empty — no locals).
2. Inside `LE_outer`, the inner function expression is evaluated. A function object is created with `[[Environment]] = LE_outer`.
3. The function object is returned. `createHelloWorld`'s stack frame is popped. `LE_outer` would be GC'd, except the returned function still references it — so it migrates from stack to heap.
4. `f` now holds the inner function reference.
5. `f()` is invoked. A new LE `LE_inner` is created with parent `LE_outer` (via `[[Environment]]`).
6. The inner body runs: `return "Hello World"`. The literal needs no scope lookup.
7. `LE_inner` is popped. `"Hello World"` is returned.

</details>

---

## 10. Common confusion + traps

1. **Returning the string instead of a function.**
   Easy slip under stress: `function createHelloWorld() { return "Hello World"; }`. The contract demands a function — read it twice.

2. **Args at the wrong layer.**
   The interviewer might say "make it accept arguments." Many candidates pass them to `createHelloWorld` instead of the returned function. The prompt's variadic behavior belongs to the **inner** call site.

3. **`this` semantics.**
   With an arrow function inside (`() => "Hello World"`), `this` is the outer `this`. With a regular `function () {}`, `this` depends on the call site. Trivial here, but the same distinction matters in Counter II and Event Emitter.

4. **Re-entrancy.**
   Calling `createHelloWorld()` twice gives you two independent function instances with two independent (empty) LEs. They share nothing. Some interviewers ask "make them return the same instance" as a follow-up — that requires memoization in module scope.

5. **`createHelloWorld()` vs `createHelloWorld()()`.**
   Single parens → returns a function. Double parens → calls that function → returns the string. Confusing under pressure; practice typing it out.

6. **Over-engineering.**
   A class. `Function.prototype.bind`. Stashing the string in a `Symbol`-keyed slot. Don't — the interviewer marks down candidates who turn a one-liner into a saga.

---

## 11. Senior follow-ups & variants

### Variant 1 — Configurable greeting

The interviewer hands you `createGreeting(greeting)` and asks the returned function to return that greeting. Now the inner *actually* closes over a variable from the outer LE — the smallest non-trivial closure.

```js
function createGreeting(greeting) {
  return function () { return greeting; };
}
const hi = createGreeting("hi");
hi();        // "hi"
```

### Variant 2 — Count the calls

Extend so the returned function also tells you how many times it's been called. Now you need mutable state in the outer LE:

```js
function createHelloWorld() {
  let count = 0;
  return function () {
    count++;
    return `Hello World (call #${count})`;
  };
}
```

This is the bridge to `counter.md` — same skeleton, mutable slot instead of static string.

### Variant 3 — Memoized to return the same instance

"Calling `createHelloWorld()` twice must return the same function reference." Useful for asserting identity in test code.

```js
let cached = null;
function createHelloWorld() {
  if (!cached) cached = function () { return "Hello World"; };
  return cached;
}
createHelloWorld() === createHelloWorld(); // true
```

Trade-off discussion: the cached version pollutes module scope but is sometimes what callers want (e.g., for `addEventListener`/`removeEventListener` pairs that need the same function reference).

---

## 12. How to think aloud in the interview

> "OK — the contract says the *factory* returns a function, and that function returns the literal `"Hello World"`. The args go to the inner, not the outer; the inner uses `...args` and ignores them. Each call to the factory makes a fresh inner function instance. Let me write it... [writes 3 lines]. Even though the inner doesn't read any variable from the outer, this is the canonical closure shape — same skeleton I'll use for counter, once, debounce. If they ask follow-ups: configurable greeting (real closure capture), counting calls (mutable slot), or memoize-the-instance (identity guarantee)."

---

## 13. 60-second revision

> - **Pattern:** `function outer() { return function inner() { ... }; }`
> - Inner function captures `[[Environment]]` = outer's LE at *creation* time.
> - When outer returns, its LE migrates from stack to heap (kept alive by the inner).
> - For this problem the capture is empty — but the mechanism is identical to every later closure problem.
> - **Each `outer()` call** = a fresh LE + a fresh inner function instance. `outer() === outer()` is `false`.
> - **Trap:** putting the return-value logic in the outer instead of the inner.
> - **Trap:** receiving args at the outer instead of the inner.
> - **Family:** counter, once, debounce, throttle, memoize, curry — all variations on this shape.

---

**Related:** [counter.md](./counter.md) · [allow-one-function-call.md](./allow-one-function-call.md) · [curry-via-closures.md](./curry-via-closures.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
