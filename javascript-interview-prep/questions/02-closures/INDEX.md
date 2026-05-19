# 02 — Closures

> 22 question files. Closures are the single most-asked JavaScript topic for senior backend interviews. Get through these and you're 70% of the way there.

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md) — read this **first** if you've never written a closure pattern by hand.

---

## Suggested reading order

### Tier 1 — Warmups (read these first, in order)

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 1 | [create-hello-world.md](./create-hello-world.md) | Easy | 5 min | The universal closure warmup — a function returns a function. |
| 2 | [counter.md](./counter.md) | Easy | 10 min | The smallest closure with mutable state. The pattern most others build on. |
| 3 | [counter-ii.md](./counter-ii.md) | Easy-Medium | 12 min | Multiple methods sharing one LE — the revealing-module pattern. |
| 4 | [create-incrementer.md](./create-incrementer.md) | Easy | 5 min | Counter variant; parameterized step. |
| 5 | [allow-one-function-call.md](./allow-one-function-call.md) | Easy | 10 min | Closure over a boolean — the `once` pattern. |
| 6 | [once-with-cached-return.md](./once-with-cached-return.md) | Easy-Medium | 15 min | `once` + cached return value. |

### Tier 2 — Core patterns (the bread and butter)

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 7 | [partial-application.md](./partial-application.md) | Medium | 15 min | Foundation for currying. Pre-bound arguments via closure. |
| 8 | [curry-via-closures.md](./curry-via-closures.md) | Medium | 25 min | Nested closures. Variadic + fixed-arity. |
| 9 | [private-data-counter.md](./private-data-counter.md) | Medium | 15 min | Comparing closure vs `Symbol` vs `WeakMap` for privacy. |
| 10 | [module-pattern-iife.md](./module-pattern-iife.md) | Medium | 20 min | The pre-ES6 module idiom in 12 lines. |
| 11 | [memoize-with-ttl.md](./memoize-with-ttl.md) | Medium | 25 min | Memoize + time-based eviction. |
| 12 | [to-be-or-not-to-be.md](./to-be-or-not-to-be.md) | Medium | 15 min | Returning `{ toBe, notToBe }` — assertion-library shape. |

### Tier 3 — Traps & memory

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 13 | [loop-closure-var-let.md](./loop-closure-var-let.md) | Medium | 15 min | The canonical `var`-in-loop bug, fixed with `let` or IIFE. |
| 14 | [setinterval-stale-closure.md](./setinterval-stale-closure.md) | Medium | 15 min | Stale captures inside intervals — same family as the React `useEffect` pitfall. |
| 15 | [closure-memory-leak-dom.md](./closure-memory-leak-dom.md) | Medium-Hard | 20 min | DOM + closure → leak pattern. Less common in pure Node but real in Electron/SSR. |

### Tier 4 — Senior-grade patterns

| # | File | Difficulty | Time | Why this one |
|---|------|------------|------|--------------|
| 16 | [closure-with-cancel-token.md](./closure-with-cancel-token.md) | Medium-Hard | 25 min | Cancellation via captured flag — bridges to AbortController. |
| 17 | [memoize-with-deep-equality.md](./memoize-with-deep-equality.md) | Medium-Hard | 30 min | Canonical-key memoize + LRU + WeakMap tradeoffs. |
| 18 | [factory-with-injected-deps.md](./factory-with-injected-deps.md) | Medium | 25 min | Functional dependency injection. Senior architectural pattern. |
| 19 | [iife-async-bootstrap.md](./iife-async-bootstrap.md) | Easy-Medium | 10 min | `(async () => {})()` — top-of-script async pattern. |
| 20 | [ring-buffer-via-closure.md](./ring-buffer-via-closure.md) | Medium | 25 min | Closure-encapsulated bounded FIFO with O(1) push/shift. |
| 21 | [closure-as-state-machine.md](./closure-as-state-machine.md) | Medium-Hard | 30 min | FSM as closure — the simplest xstate-equivalent. |
| 22 | [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md) | Medium | 15 min | When to use closures, when to use `#fields`. Six-axis comparison. |

---

## If you only have 30 minutes

Read these 5:
1. [counter.md](./counter.md) — the core pattern
2. [allow-one-function-call.md](./allow-one-function-call.md) — boolean variant
3. [curry-via-closures.md](./curry-via-closures.md) — nested closures
4. [loop-closure-var-let.md](./loop-closure-var-let.md) — the trap
5. [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md) — modern context

---

## How to use this folder

For each file:
1. Read **section 1 (problem statement)** — confirm you understand the contract.
2. Try **section 5 (try it yourself)** before scrolling.
3. Read sections 4 and 7 (mental model + unlocking insight) first if you're stuck.
4. Write the solution from scratch *without looking* at section 8. Then compare.
5. Revisit **section 10 (common confusion)** the night before the interview.
6. Memorize **section 13 (60-second revision)** the morning of.

Aim for **fluency**, not memorization. The pattern reappears in promises, machine-coding, and DOM/React code — closures are the substrate.
