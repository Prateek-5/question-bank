# Decorators (Stage 3 / Legacy) — Basics

## Source / Origin
- Legacy decorators (Babel `legacy: true`, TypeScript `experimentalDecorators`).
- New Stage 3 decorators (TC39 proposal, finalizing 2024-2026).
- Asked at: NestJS / Angular shops; Razorpay, Atlassian, anywhere with framework-heavy code.
- Concept reference: `concepts/prototype.md`, sibling `mixin-composition-pattern.md`.

## Why this question matters in interviews
Decorators are the *transparent* alternative to mixins/HOFs. NestJS, Angular, TypeORM, MikroORM all use them. Senior bar: you know the two flavors (legacy vs Stage 3), the four kinds of decorators (class, method, accessor, field), and what they actually *do* — receive descriptor, optionally return modified version.

## Concepts involved

### Syntax to lock in
```js
// Method decorator (Stage 3 style)
function log(originalMethod, context) {
  return function (...args) {
    console.log(`[${context.name}] called with`, args);
    const result = originalMethod.call(this, ...args);
    console.log(`[${context.name}] returned`, result);
    return result;
  };
}

class Service {
  @log
  greet(name) { return `hello ${name}`; }
}

new Service().greet('alice');
// [greet] called with ['alice']
// [greet] returned 'hello alice'
```

### Edge cases / traps
1. **Legacy vs Stage 3 — different signatures.**
   - Legacy: `(target, propertyKey, descriptor)` for methods.
   - Stage 3: `(value, context: {kind, name, addInitializer, ...})`.
2. **Decorator factories** — `@logLevel('info') foo() {}` is a factory `(level) => decorator`.
3. **Decorator order** — bottom-to-top within a single member (innermost runs first); outer wraps inner.
4. **Side effects at class definition time.** Decorators run once when the class is defined.
5. **`this` binding** — return a function that uses `this`, not an arrow that captures outer `this`.
6. **TypeScript metadata** (`emitDecoratorMetadata`) — extra reflection metadata for DI frameworks.
7. **Tree-shaking** — decorators often prevent tree-shaking; bundler concern.
8. **Replacing the method vs decorating** — return new function = replace; mutate `descriptor.value` = wrap (legacy).

## Mental Model

```
   class Service {
     @log
     greet(name) { ... }
   }

   at class definition:
     1. greet method defined
     2. @log invoked with (greet, context) → returns wrapped version
     3. Service.prototype.greet = wrapped

   at call site:
     new Service().greet('alice') → wrapped → logs + invokes original
```

For multiple decorators on one method:

```
   @a
   @b
   @c
   foo() {}
   
   execution order: c → b → a (bottom-up to define)
   call order at runtime: a(b(c(original)))  (outer wraps inner)
```

## Why interviewers care

- **Framework literacy** (NestJS, Angular).
- **AOP awareness** — cross-cutting concerns (logging, caching, validation).
- **Spec currency** — knowing Stage 3 shape matters.

## Common confusion

- **"Decorators run at every call."** They run at class definition; the *returned* function runs at each call.
- **"Multiple decorators run top-to-bottom."** Define order is bottom-up; call wrapping is outer-wraps-inner.
- **"You can decorate plain functions."** Not in either spec — class/member only.
- **"Legacy and Stage 3 are interchangeable."** Different shapes; adapt.

## Brute force

Manual wrapping at the call site — verbose, error-prone, not centralized:

```js
class Service {
  greet(name) {
    console.log('start'); const r = `hello ${name}`; console.log('end'); return r;
  }
}
```

## Optimal approach

Decorator + factory pattern centralizes cross-cutting logic. Apply with `@`.

## Solution

```js
// Method decorator factory (Stage 3)
function memoize() {
  return function (originalMethod, context) {
    const cache = new WeakMap();
    return function (...args) {
      let perThis = cache.get(this);
      if (!perThis) { perThis = new Map(); cache.set(this, perThis); }
      const key = JSON.stringify(args);
      if (perThis.has(key)) return perThis.get(key);
      const r = originalMethod.call(this, ...args);
      perThis.set(key, r);
      return r;
    };
  };
}

class Computer {
  @memoize()
  expensive(x) { /* heavy work */ return x * x; }
}

// Class decorator (Stage 3)
function singleton(Cls, ctx) {
  if (ctx.kind !== 'class') throw new Error('only for classes');
  let inst;
  return new Proxy(Cls, {
    construct(target, args) {
      if (!inst) inst = new target(...args);
      return inst;
    }
  });
}

@singleton
class Logger { constructor(level) { this.level = level; } }
new Logger('info') === new Logger('debug');   // true (same instance)

// Field decorator (Stage 3)
function defaultValue(val) {
  return function (_value, context) {
    return function () { return val; };       // initializer
  };
}

class User {
  @defaultValue('anonymous') name;
}
new User().name;        // 'anonymous'
```

Legacy (TypeScript `experimentalDecorators: true`):

```ts
function legacyLog(target: any, prop: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`call ${prop}`);
    return original.apply(this, args);
  };
}

class Service {
  @legacyLog
  greet(name: string) { return `hello ${name}`; }
}
```

## Dry run

```
class Service {
  @memoize()
  expensive(x) { return x * x; }
}

at class definition:
  define expensive(x) on Service.prototype
  @memoize() runs:
    memoize() called → returns decorator
    decorator(originalExpensive, {kind:'method', name:'expensive', ...}):
      cache = new WeakMap (in closure)
      return wrapped function
  Service.prototype.expensive = wrapped

call: new Service().expensive(5)
  wrapped called with [5], this=instance
  cache.get(this) → undefined → create new Map
  key = '[5]'
  perThis.has → no
  result = originalExpensive.call(this, 5) → 25
  perThis.set('[5]', 25)
  return 25

call again: new Service().expensive(5)   // different instance!
  cache.get(this2) → undefined → fresh Map → recompute
```

(Per-instance memoization due to WeakMap keyed on `this`.)

## How to think aloud

> "Decorator: a function applied at class-definition time. Stage 3 signature: `(value, context)`; legacy: `(target, key, descriptor)`. Returns a replacement value — wrapped method, new initializer, modified class. Factories like `@cache(60)` are functions returning decorators. Cross-cutting logic — logging, caching, validation — lives in decorators instead of polluting every method. Tradeoff: harder to tree-shake, sometimes opaque to debuggers."

## Important takeaways

- **Run at class definition, not call time.**
- **Stage 3 signature: `(value, context)`; legacy: `(target, key, descriptor)`.**
- **Factories**: `@cache(60)` is `(60) => decorator`.
- **Multiple decorators on one member**: outer wraps inner.
- **Used heavily in NestJS, Angular, TypeORM.**
- **Tree-shaking limitations** — bundler concern.

## Variants

- **Class decorator** — wraps the constructor.
- **Method decorator** — wraps the function.
- **Field decorator** — provides initializer.
- **Auto-accessor** (`accessor x = 0`) — Stage 3 special.
- **Composition** — `@cache(60) @log` stacks.

## Revision notes

```
Stage 3 decorator: (value, context) => replacement

context fields (Stage 3):
  kind: 'class' | 'method' | 'getter' | 'setter' | 'field' | 'accessor'
  name: string
  addInitializer(fn): register an initializer
  access: { get, set, has }
  static: boolean
  private: boolean

multiple decorators:
  @a @b @c foo()
  apply order: c (innermost) → b → a (outermost)
  call order: a wraps b wraps c wraps original

factories: @cache(60) means cache(60) returns the decorator

USES: cross-cutting (logging, caching, validation, DI metadata)
FRAMEWORKS: NestJS, Angular, TypeORM, MikroORM
```
