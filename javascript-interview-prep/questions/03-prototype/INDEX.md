# 03 — Prototype

Prototype chain, `this`, polyfills, class internals. Files follow the v2 13-section template.

---

## How to study this folder

1. **Foundation:** prototype-chain-inheritance, this-keyword-nodejs.
2. **Polyfills:** polyfill-new, polyfill-bind, polyfill-call-apply, instanceof-polyfill, object-create-polyfill.
3. **Class internals:** class-to-prototype-desugar, extends-super-implementation, reflect-construct-vs-new.
4. **Property descriptors:** defineproperty-vs-assignment, getter-setter-via-prototype, hasownproperty-vs-in.
5. **Patterns:** mixin-composition-pattern, method-chaining-builder, decorator-basics-legacy.
6. **Modern features:** private-static-fields, symbol-iterator-on-class, tostring-symbol-tag-override.
7. **Perf + traps:** object-setprototypeof-perf-trap, array-prototype-last, differences-between-two-objects.

---

## Files (22)

### Foundation
- [prototype-chain-inheritance.md](./prototype-chain-inheritance.md) — Three names; lookup; chain walk.
- [this-keyword-nodejs.md](./this-keyword-nodejs.md) — 5 rules in precedence.

### Polyfills
- [polyfill-new.md](./polyfill-new.md) — 4-step `[[Construct]]`.
- [polyfill-bind.md](./polyfill-bind.md) — Detect `new` via `this instanceof bound`.
- [polyfill-call-apply.md](./polyfill-call-apply.md) — Symbol-key trick.
- [instanceof-polyfill.md](./instanceof-polyfill.md) — Walk prototype chain.
- [object-create-polyfill.md](./object-create-polyfill.md) — Empty constructor trick.

### Class internals
- [class-to-prototype-desugar.md](./class-to-prototype-desugar.md) — Class is sugar.
- [extends-super-implementation.md](./extends-super-implementation.md) — Two prototype writes.
- [reflect-construct-vs-new.md](./reflect-construct-vs-new.md) — `newTarget` for built-in subclassing.

### Property descriptors
- [defineproperty-vs-assignment.md](./defineproperty-vs-assignment.md) — Default flags differ.
- [getter-setter-via-prototype.md](./getter-setter-via-prototype.md) — Accessor on prototype.
- [hasownproperty-vs-in.md](./hasownproperty-vs-in.md) — Three operators, three questions.

### Patterns
- [mixin-composition-pattern.md](./mixin-composition-pattern.md) — Subclass factory mixin.
- [method-chaining-builder.md](./method-chaining-builder.md) — `return this` pattern.
- [decorator-basics-legacy.md](./decorator-basics-legacy.md) — Legacy + Stage 3.

### Modern features
- [private-static-fields.md](./private-static-fields.md) — `static #x`; subclass cannot access.
- [symbol-iterator-on-class.md](./symbol-iterator-on-class.md) — `for...of` protocol.
- [tostring-symbol-tag-override.md](./tostring-symbol-tag-override.md) — Coercion hooks.

### Perf + traps
- [object-setprototypeof-perf-trap.md](./object-setprototypeof-perf-trap.md) — Hidden-class deopt.
- [array-prototype-last.md](./array-prototype-last.md) — Built-in augmentation; code smell.
- [differences-between-two-objects.md](./differences-between-two-objects.md) — Recursive deep diff.

---

## Concept primers

- [`concepts/prototype.md`](../../concepts/prototype.md) — Chain mechanics; `this` rules.

---

## Companion sections

- `01-hoisting/` — class hoisting; TDZ.
- `02-closures/` — module pattern; private state.
- `10-machine-coding-patterns/` — bind, curry, mixin patterns.
