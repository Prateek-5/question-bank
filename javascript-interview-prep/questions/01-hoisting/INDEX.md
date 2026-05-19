# 01 — Hoisting

Two-phase execution model, TDZ, scope rules, module hoisting. Files follow the v2 13-section template.

---

## How to study this folder

1. **Foundation:** hoisting-in-javascript, hoisting-and-scoping, tdz-let-const.
2. **`var` mechanics:** var-hoisting-output, var-in-block, let-vs-var-differences.
3. **Function/class:** function-declaration-vs-expression-hoisting, class-hoisting, class-static-block-hoisting, named-fn-expression-binding, func-expr-in-conditional.
4. **TDZ corners:** typeof-on-tdz-variable, tdz-with-default-parameter, let-in-for-loop-binding.
5. **Module/scope:** es-module-live-bindings, import-vs-require-hoisting, circular-import-live-binding-quiz, hoisting-in-try-catch.

---

## Files (18)

### Foundation
- [hoisting-in-javascript.md](./hoisting-in-javascript.md) — Two-phase execution model.
- [hoisting-and-scoping.md](./hoisting-and-scoping.md) — VE + LE + scope chain interaction.
- [tdz-let-const.md](./tdz-let-const.md) — Three states: not-declared / TDZ / initialized.

### `var` mechanics
- [var-hoisting-output.md](./var-hoisting-output.md) — Canonical output prediction.
- [var-in-block.md](./var-in-block.md) — `var` ignores block boundaries.
- [let-vs-var-differences.md](./let-vs-var-differences.md) — Five differences.

### Functions and classes
- [function-declaration-vs-expression-hoisting.md](./function-declaration-vs-expression-hoisting.md) — Statement vs expression.
- [class-hoisting.md](./class-hoisting.md) — TDZ like `let`/`const`, NOT like function.
- [class-static-block-hoisting.md](./class-static-block-hoisting.md) — Run once at class eval; private access.
- [named-fn-expression-binding.md](./named-fn-expression-binding.md) — Inner read-only name.
- [func-expr-in-conditional.md](./func-expr-in-conditional.md) — Function-in-block (Annex B).

### TDZ corners
- [typeof-on-tdz-variable.md](./typeof-on-tdz-variable.md) — `typeof` no longer universally safe.
- [tdz-with-default-parameter.md](./tdz-with-default-parameter.md) — Parameter scope TDZ.
- [let-in-for-loop-binding.md](./let-in-for-loop-binding.md) — Fresh LE per iteration.

### Module + scope
- [es-module-live-bindings.md](./es-module-live-bindings.md) — Hoisted live read-only.
- [import-vs-require-hoisting.md](./import-vs-require-hoisting.md) — Static + hoisted vs runtime.
- [circular-import-live-binding-quiz.md](./circular-import-live-binding-quiz.md) — 2-phase load + cycles.
- [hoisting-in-try-catch.md](./hoisting-in-try-catch.md) — Three layered scopes.

---

## Concept primers

- [`concepts/hoisting.md`](../../concepts/hoisting.md) — Mechanism + states.
- [`concepts/closures.md`](../../concepts/closures.md) — VE/LE; capture semantics.

---

## Companion sections

- `02-closures/` — Loop-closure bug, IIFE pattern.
- `03-prototype/` — Class internals, `this` binding.
- `05-event-loop/` — Top-level await + module evaluation.
