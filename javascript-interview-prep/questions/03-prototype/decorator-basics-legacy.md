# Decorators — legacy + Stage 3 basics

> **Difficulty:** Medium-Senior   |   **Time:** ~12 min   |   **Prereqs:** [class-to-prototype-desugar.md](./class-to-prototype-desugar.md), [mixin-composition-pattern.md](./mixin-composition-pattern.md)
>
> **Source:** Legacy decorators (Babel/TS), Stage 3 TC39 proposal. NestJS, Angular, TypeORM.

---

## 1. Problem statement

Decorators wrap class members. Two flavors: legacy (`experimentalDecorators`) and Stage 3 (TC39, finalizing 2024-2026). Four kinds: class, method, accessor, field.

**Verification examples**

```js
// Stage 3 style method decorator
function log(originalMethod, context) {
  return function (...args) {
    console.log(`[${context.name}]`, args);
    return originalMethod.call(this, ...args);
  };
}

class Service {
  @log
  greet(name) { return `hello ${name}`; }
}

new Service().greet('world');
// [greet] ['world']
// 'hello world'
```

**Constraints**
- Decorator receives target + context (Stage 3) or target+key+descriptor (legacy).
- Class decorator: wraps class itself.
- Method decorator: wraps function.
- Accessor decorator: wraps getter/setter.
- Field decorator: wraps initializer.

---

## 2. Plain-English restatement

A decorator is a function that modifies what comes after `@decorator`. Used in NestJS (`@Controller`), Angular (`@Component`), TypeORM (`@Entity`). Replace mixins/HOFs with a more declarative syntax.

---

## 3. Why this matters in interviews

Framework code uses them heavily. Senior bar: know the two flavors + four kinds + roughly what each receives.

---

## 4. Mental model

```
   @decorator
   class Foo { ... }
   ≡
   Foo = decorator(Foo);
   
   @decorator
   method() {}
   ≡
   Foo.prototype.method = decorator(Foo.prototype.method, {...context});
   
   Four kinds (Stage 3):
   - class:    (Cls, ctx) => Cls'                  Cls' replaces Cls
   - method:   (fn, ctx) => fn'                    fn' replaces method
   - accessor: ({get,set}, ctx) => {get,set}'      replaces both
   - field:    (initializer, ctx) => initializer'  controls field init
   
   ctx (Stage 3) has:
   - kind: 'class'|'method'|'getter'|'setter'|'field'
   - name: 'methodName'
   - addInitializer(fn): run fn at class init
   - private: boolean (is #private?)
   - static: boolean
   - access: { get, set } (for accessing the member)
   
   Legacy form (TypeScript experimentalDecorators):
   - method: (target, key, descriptor) => descriptor
   - Mutates the descriptor in place.
   - Different signature than Stage 3!
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Where does `@decorator` execute?
> 2. What's the difference between legacy and Stage 3 decorators?
> 3. Can you stack decorators?

---

## 6. Brute force — walked through

### Wrong attempt 1: ignore signature differences
Legacy and Stage 3 have different shapes; can't share code.

### Wrong attempt 2: mutate target directly
Stage 3 expects you to RETURN a new value, not mutate.

### Wrong attempt 3: stateful decorators on prototype
Shared across instances; bug.

---

## 7. The unlocking insight

> **Stage 3 decorator: `(target, context) => replacement`. Four kinds: class, method, accessor, field. Replaces (not mutates). Used by NestJS/Angular/TypeORM for declarative metadata.**

Three properties:

1. **Function over target + context.**
2. **Returns replacement** (not mutates).
3. **Four kinds** + class.

---

## 8. Solution (annotated)

```js
// Stage 3 method decorator (logging)
function log(originalMethod, context) {                                 // step 1: stage 3 signature
  if (context.kind !== 'method') throw new Error('@log on method only');
  return function (...args) {
    console.log(`[${context.name}]`, args);
    const result = originalMethod.call(this, ...args);
    console.log(`[${context.name}] returned`, result);
    return result;
  };
}

class Service {
  @log
  greet(name) { return `hello ${name}`; }
}

new Service().greet('world');
// [greet] ['world']
// [greet] returned hello world

// Class decorator
function singleton(Cls, context) {                                       // step 2: class decorator
  let instance;
  return class extends Cls {
    constructor(...args) {
      if (instance) return instance;
      super(...args);
      instance = this;
    }
  };
}

@singleton
class Config {
  constructor(env) { this.env = env; }
}

new Config('dev') === new Config('prod');                               // true (same instance)

// Stack decorators (bottom-up)
function uppercase(method, ctx) {
  return function (...args) { return method.call(this, ...args).toUpperCase(); };
}
function exclaim(method, ctx) {
  return function (...args) { return method.call(this, ...args) + '!'; };
}

class Greeter {
  @uppercase                                                              // applied LAST
  @exclaim                                                                // applied FIRST (closer to method)
  greet(name) { return `hello ${name}`; }
}
new Greeter().greet('x');                                                // 'HELLO X!'
```

**Try it yourself**

```js
// Legacy form (TypeScript experimentalDecorators)
function logLegacy(target, key, descriptor) {                            // step 3: legacy signature
  const original = descriptor.value;
  descriptor.value = function (...args) {
    console.log(`[${key}]`, args);
    return original.call(this, ...args);
  };
  return descriptor;
}

// In TypeScript:
// class Foo { @logLegacy bar() {} }

// Common decorator uses
// @Component({...}) — Angular
// @Controller() @Get('/path') — NestJS
// @Entity() @Column() — TypeORM
// @Memoize() — caching
// @Throttle(100) — rate limit
```

---

## 9. Step-by-step dry run

```
class Service {
  @log
  greet(name) { return `hello ${name}`; }
}

At class evaluation:
  1. Define greet on Service.prototype (the method).
  2. context = { kind: 'method', name: 'greet', static: false, private: false, ... }.
  3. Call log(greet, context) → returns wrapped function.
  4. Replace Service.prototype.greet with wrapped function.

new Service().greet('world'):
  Lookup greet → wrapped function.
  Invoke:
    console.log('[greet]', ['world']) → '[greet] [\'world\']'.
    originalMethod.call(this, 'world') → 'hello world'.
    console.log('[greet] returned', 'hello world') → '[greet] returned hello world'.
    return 'hello world'.

Stacked decorators (bottom-up):
  @uppercase
  @exclaim
  greet
  
  Order of application:
  1. greet wrapped by exclaim → greet'.
  2. greet' wrapped by uppercase → greet''.
  
  Service.prototype.greet = greet''.
  
  When called: uppercase wrapper runs first → calls exclaim wrapper → calls original greet.
  Result: 'hello x' → 'hello x!' (exclaim) → 'HELLO X!' (uppercase).
```

---

## 10. Common confusion + traps

1. **Legacy vs Stage 3** signatures differ.
2. **Mutate target** — Stage 3 expects replacement returned.
3. **Decorator order** — bottom-up application; top-down call.
4. **`this` inside decorator** — at definition; in wrapper use `.call(this, ...)`.
5. **Field decorator** receives initializer, not the field itself.
6. **Class decorator** can return new class (replace).
7. **Native support** in V8 is recent; transpiler choice matters.

---

## 11. Senior follow-ups & variants

### Variant 1 — Memoization decorator
Cache method results per arguments.

### Variant 2 — Validation decorator
`@positive` ensures parameter > 0.

### Variant 3 — `addInitializer` (Stage 3)
Run code at class init time from a decorator.

### Variant 4 — Framework metadata
Decorators write metadata (via `reflect-metadata`); framework reads at runtime.

### Variant 5 — Babel/TypeScript flags
`legacy: true`, `useDefineForClassFields: false` — configuration matters.

---

## 12. How to think aloud

> "Decorators are functions that wrap class members. Two flavors with DIFFERENT signatures: legacy (Babel/TypeScript `experimentalDecorators`) — `(target, key, descriptor) => descriptor` — mutates descriptor in place. Stage 3 (TC39, finalizing) — `(target, context) => replacement` — returns new value. Four kinds: class (wraps class itself), method (wraps function on prototype), accessor (wraps getter/setter), field (wraps initializer). Decorators stack bottom-up at application; the OUTER decorator wraps the result of the INNER. Used heavily by NestJS (`@Controller`, `@Get`), Angular (`@Component`), TypeORM (`@Entity`, `@Column`) — declarative metadata + behavior modification. Senior follow-ups: `addInitializer` for class init hooks; `reflect-metadata` for framework metadata; memoization, validation, throttle/debounce decorators. Trap: confusing legacy and Stage 3 signatures; mutating instead of returning; decorator order."

---

## 13. 60-second revision

> - **Decorator = function wrapping member.**
> - **Stage 3:** `(target, context) => replacement`.
> - **Legacy:** `(target, key, descriptor) => descriptor` (mutates).
> - **Four kinds:** class, method, accessor, field.
> - **Stack bottom-up;** outer wraps inner result.
> - **Used by:** NestJS, Angular, TypeORM, MikroORM.
> - **`addInitializer`** for class-init hooks (Stage 3).
> - **Trap:** signature differences; mutate vs return; stacking order.

---

**Related:** [class-to-prototype-desugar.md](./class-to-prototype-desugar.md) · [mixin-composition-pattern.md](./mixin-composition-pattern.md) · [`10-machine-coding-patterns/memoize.md`](../10-machine-coding-patterns/memoize.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
