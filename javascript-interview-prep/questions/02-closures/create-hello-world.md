# Create Hello World Function

## Source
- https://leetcode.com/problems/create-hello-world-function/

## Why this question matters in interviews
This is the universal closure warm-up. Five lines of code, but in those five lines the interviewer is checking whether you understand: **a function can return a function**, the inner function **captures the surrounding lexical scope**, and that captured scope survives even after the outer call returns. Every closure-heavy pattern you'll see later (debounce, throttle, memoize, once, currying, private state) is a 5x-bigger version of this. As a backend engineer dusting off JS, getting this fluent in <60 seconds gives you a clean runway into the harder problems.

## Concepts involved

### Syntax to lock in
```js
function createHelloWorld() {
  return function () {
    return "Hello World";
  };
}
```
- Outer function returns an **anonymous function expression** — not invoked, just defined and returned.
- Caller does `const f = createHelloWorld(); f();` — two distinct call sites.

### Lexical environment + scope chain
- When `createHelloWorld` is called, a new **Lexical Environment** (LE) is created on the call stack with its own `VariableEnvironment` slot.
- The inner function literal captures a reference to that LE in its `[[Environment]]` internal slot at the moment it's **created** (not when it's called).
- When `createHelloWorld` returns, its activation record is popped from the call stack — **but** the LE is not garbage-collected because the returned function holds a live reference to it. The LE migrates from stack to heap. This is the heart of "what is a closure."
- For this specific problem, the inner function captures *nothing meaningful* from the outer scope (no variables), so the closure is degenerate — but the mechanism is identical.

### Edge cases / interview traps
1. **Arguments at the wrong layer** — interviewer says "make it also accept arguments." Many candidates pass args to `createHelloWorld` instead of to the returned function. Read the prompt: it's the *returned* function that's variadic.
2. **`this` semantics** — if you use an arrow function for the inner, `this` is the outer `this`. With `function () {}`, `this` is determined by the call site. Trivial here, important for Counter II.
3. **Re-entrancy** — calling `createHelloWorld()` twice gives you two independent functions, each with its own captured LE. They share nothing.
4. **Return value vs function reference** — `createHelloWorld()` returns a function; `createHelloWorld()()` returns the string. Common slip when stressed.

## Brute force approach
There is no brute-force-vs-optimal distinction here — the problem is a closure primer. The only "wrong" path is overthinking: trying to use a class, `bind`, or storing the string on `globalThis`. Don't. The literal answer is the optimal one.

## Optimal approach
Return a function literal that returns the string. Zero state. O(1) memory, O(1) per call.

## Solution (JavaScript)

```js
/**
 * @return {Function}
 */
var createHelloWorld = function () {
  return function (...args) {
    return "Hello World";
  };
};

// Usage
const f = createHelloWorld();
f();                 // "Hello World"
f(1, 2, 3, {}, []);  // "Hello World" — args are ignored
```

## Step-by-step dry run

Input:
```js
const f = createHelloWorld();
console.log(f());
```

Trace:
1. `createHelloWorld()` is called → a new LE `LE_outer` is created.
2. Inside `LE_outer`, the inner function expression is evaluated. A function object is created with `[[Environment]] = LE_outer`.
3. The function object is returned. `createHelloWorld`'s frame is popped from the call stack, but `LE_outer` is kept alive on the heap because the returned function references it.
4. `f` now points to the inner function object.
5. `f()` is invoked. A new LE `LE_inner` is created with parent = `LE_outer` (via `[[Environment]]`).
6. The inner function body executes: `return "Hello World"`. Resolution of the literal needs no scope lookup.
7. `LE_inner` is popped. `"Hello World"` is returned.
8. `console.log` prints `Hello World`.

## Important takeaways

**Syntax to memorize**
- `function outer() { return function inner() { ... } }` — the canonical closure skeleton.
- Caller pattern: `const fn = outer(); fn();`.

**Patterns to reuse**
- This is the **factory function** pattern. Every "make a configured function" problem (debounce, throttle, curry, memoize, once) starts from this exact shape.
- Even when the inner function captures no variables, the *shape* of the answer signals you understand higher-order functions.

**Common mistakes**
- Writing `return "Hello World"` directly inside `createHelloWorld` (returns a string instead of a function).
- Passing args to the outer instead of the inner.
- Adding unnecessary state — interviewer will subtract points for over-engineering a warm-up.

**Related questions**
- Counter (closure over mutable state)
- Allow One Function Call (closure over a boolean flag)
- Currying (nested closures)

## Variants

1. **Configurable greeting** — "Make `createHelloWorld(greeting)` so the returned function returns whatever string you passed in." Now the inner function actually captures `greeting` from the outer LE. This is the smallest non-trivial closure.

2. **Counting calls** — "Also return how many times the inner function has been called so far." Now you need a `let count = 0` in the outer scope; the inner function increments and returns it. Same skeleton as `Counter`.

3. **Returning the same instance** — "Calling `createHelloWorld()` twice must return the same function reference." Tests whether you know functions are objects. Solution: memoize the inner inside the module scope.

## Revision notes

> **createHelloWorld — 60 second recap**
> - Pattern: `function outer() { return function inner() {...} }`.
> - Returned function is created with `[[Environment]] = outer's LE`.
> - When outer returns, its LE migrates from stack to heap (kept alive by the returned function).
> - Each call to `outer` makes a **fresh** LE — multiple inner functions don't share state.
> - For this problem the captured scope is empty, but the mechanism is identical to debounce, counter, once.
> - **Trap:** putting the return-value logic in the outer instead of the inner.
> - Family: every "factory of a function" problem — debounce, throttle, memoize, curry, once.
