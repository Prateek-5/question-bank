# Implement a Tiny DI Container

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [mini-state-machine.md](./mini-state-machine.md), [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)
>
> **Source:** NestJS, InversifyJS, Awilix, tsyringe. Staff-level Node interview classic.

---

## 1. Problem statement

**Signature**
```ts
function createContainer(parent?: Container): {
  register(token: any, factory: (c: Container) => any, opts?: { singleton?: boolean }): Container;
  resolve(token: any): any;
  child(): Container;
  reset(): void;
};
```

**Input / Output examples**

| Setup                                                  | Behaviour                                              |
|--------------------------------------------------------|---------------------------------------------------------|
| `register('db', factory, { singleton: true })`         | factory not called yet (lazy)                          |
| `resolve('db')` (1st call)                              | factory runs; instance cached                          |
| `resolve('db')` (2nd call, singleton)                   | cached instance returned                               |
| `resolve('userSvc')` chained deps                       | recursively resolves graph; lazy                       |
| Two services depend on each other circularly           | throws `Circular dependency: a -> b -> a`              |
| `resolve('unknown')`                                    | throws "Not registered"                                |
| `child().resolve('app-scope-token')`                    | falls through to parent if not registered locally     |

**Constraints**
- Lazy resolution — no construction at registration.
- Singleton (cached) vs transient (new each time) lifetimes.
- Cycle detection via in-progress Set + try/finally.
- Factory receives container, pulls own deps via `container.resolve`.

---

## 2. Plain-English restatement

A registry where you map a name (token) to a factory function. Resolving a token calls its factory, which can ask the container for other tokens. The container caches singletons, builds transients fresh each time, and detects circular dependencies. Lets you swap implementations at the seams (mock DB in tests, real DB in prod).

---

## 3. Why this matters in interviews

DI is the **invisible scaffolding** of every non-trivial backend. Probes: `Map<token, factory>`, lazy resolution, singleton vs transient lifetimes, circular-dependency detection, the architectural taste to separate **construction** from **use**. Tests whether you've moved past "instantiate everything in main.ts."

---

## 4. Mental model

```
   Container:
   ┌──────────────────────────────────────────────────────────────┐
   │ registry:    Map<token, {factory, singleton}>                 │
   │ singletons:  Map<token, instance>                             │
   │ resolving:   Set<token>          ← currently being built     │
   │ parent:      Container | null    ← scope fall-through        │
   └──────────────────────────────────────────────────────────────┘

   resolve('userSvc'):
     singletons.has('userSvc')? no
     entry = registry.get('userSvc')
     resolving.add('userSvc')
     try:
       instance = entry.factory(container)
                    ↳ inside: container.resolve('repo')
                              singletons.has? no
                              resolving.add('repo')
                              instance = factory(container)
                                ↳ container.resolve('db')
                                  singletons.has? no
                                  resolving.add('db')
                                  instance = factory(container)
                                  resolving.delete('db'); cache singleton
                                ↳ returns cached 'log' (singleton)
                              resolving.delete('repo')
     finally: resolving.delete('userSvc')

   Cycle detection:
     resolve('a') → resolving={a} → factory calls resolve('b')
     → resolving={a, b} → factory calls resolve('a')
     → resolving.has('a') → THROW with path
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `db` is singleton but `userSvc` is transient, do two `resolve('userSvc')` calls share the same `db` instance?
> 2. Why use try/finally around `resolving.delete(token)`?
> 3. What's the difference between manual wiring in `main.ts` and using a DI container — when does DI start paying off?

---

## 6. Brute force — walked through

### Wrong attempt 1: instantiate everything eagerly in main.ts
For tiny apps, fine. Stops scaling at ~20 services; tests become painful (have to mock the whole world); startup is slow.

### Wrong attempt 2: global service locator
```js
globalThis.services.db
```
"DI with a global" — sacrifices testability, the very property DI is supposed to give. Anti-pattern.

### Wrong attempt 3: no cycle detection
Infinite recursion → cryptic stack overflow. Detect cycles and throw a helpful "a → b → a" error.

---

## 7. The unlocking insight

> **Two Maps (`registry`, `singletons`) + one Set (`resolving`). `resolve(token)` is recursive: cache check → registry lookup → cycle check → call factory(container) → cache if singleton → return. Try/finally around cycle Set so a throwing factory doesn't leave the token "stuck resolving."**

Three properties:

1. **Lazy resolution** — nothing constructed until `resolve`.
2. **Factory takes container** — pulls deps via `container.resolve(...)`.
3. **Cycle detection** with try/finally — robust against throwing factories.

---

## 8. Solution (annotated)

```js
function createContainer(parent = null) {
  const registry = new Map();                                       // step 1: token → {factory, singleton}
  const singletons = new Map();                                      // step 2: cached instances
  const resolving = new Set();                                       // step 3: cycle detection

  function register(token, factory, { singleton = false } = {}) {
    if (registry.has(token)) {
      throw new Error(`Token already registered: ${String(token)}`);
    }
    registry.set(token, { factory, singleton });
    return container;
  }

  function resolve(token) {
    if (singletons.has(token)) return singletons.get(token);          // step 4: fast path

    const entry = registry.get(token);
    if (!entry) {
      if (parent) return parent.resolve(token);                       // step 5: scope fall-through
      throw new Error(`Not registered: ${String(token)}`);
    }

    if (resolving.has(token)) {                                       // step 6: cycle
      const path = [...resolving, token].map(String).join(' -> ');
      throw new Error(`Circular dependency: ${path}`);
    }
    resolving.add(token);

    let instance;
    try {
      instance = entry.factory(container);                            // step 7: factory pulls deps
    } finally {
      resolving.delete(token);                                        // step 8: cleanup on throw too
    }

    if (entry.singleton) singletons.set(token, instance);
    return instance;
  }

  function child() { return createContainer(container); }
  function reset() { singletons.clear(); }

  const container = { register, resolve, child, reset };
  return container;
}
```

**Try it yourself**

```js
class Logger      { log(m) { console.log(m); } }
class Db          { constructor(log) { this.log = log; log.log('db init'); } }
class UserRepo    { constructor(db, log) { this.db = db; this.log = log; } }
class UserService { constructor(repo) { this.repo = repo; } }

const c = createContainer();
c.register('log',     () => new Logger(),                                    { singleton: true });
c.register('db',      (c) => new Db(c.resolve('log')),                       { singleton: true });
c.register('repo',    (c) => new UserRepo(c.resolve('db'), c.resolve('log')));
c.register('userSvc', (c) => new UserService(c.resolve('repo')));

const svc1 = c.resolve('userSvc');
const svc2 = c.resolve('userSvc');
svc1 === svc2;                  // false — transient
svc1.repo.db === svc2.repo.db;  // true — singleton

// Cycle
c.register('a', (c) => c.resolve('b'));
c.register('b', (c) => c.resolve('a'));
c.resolve('a');   // throws: Circular dependency: a -> b -> a
```

---

## 9. Step-by-step dry run

```
resolve('userSvc'):
  singletons.has? no. entry=transient. resolving={userSvc}.
  factory(c) → new UserService(c.resolve('repo')):
    resolve('repo'):
      singletons.has? no. transient. resolving={userSvc, repo}.
      factory → new UserRepo(c.resolve('db'), c.resolve('log')):
        resolve('db'):
          no cache. singleton. resolving={userSvc, repo, db}.
          factory → new Db(c.resolve('log')):
            resolve('log'):
              no cache. singleton. resolving adds 'log'.
              factory → new Logger().
              resolving.delete('log'). singletons.set('log', logger). return logger.
            new Db(logger) constructed. Logs 'db init'.
          resolving.delete('db'). singletons.set('db', db). return db.
        resolve('log'): cached → return logger (same ref).
      new UserRepo(db, logger). resolving.delete('repo'). transient → no cache. return.
  new UserService(repo). resolving.delete('userSvc'). transient → no cache. return.

resolve('userSvc') again:
  no cache (transient). Re-runs factory → new UserService(new UserRepo(cached db, cached log)).
  New svc instance, same db, same log.

Cycle dry run:
resolve('a'):
  resolving.add('a') → {a}.
  factory → c.resolve('b'):
    resolving.add('b') → {a, b}.
    factory → c.resolve('a'):
      resolving.has('a') → TRUE → throw "Circular dependency: a -> b -> a".
    finally: resolving.delete('b').
  finally: resolving.delete('a').
  rethrown to caller.
```

---

## 10. Common confusion + traps

1. **No cycle detection** — stack overflow with cryptic trace.
2. **Cleanup without try/finally** — a throwing factory leaves token stuck in `resolving`.
3. **Strings as tokens, typo'd** — TS symbols-as-tokens or class-as-token catches at compile time.
4. **Singleton cache leaking across tests** — provide `reset()` or fresh containers per test.
5. **Eager resolution at registration** — the whole point is laziness.
6. **Forgetting `child` falls through to parent** — break request-scoped isolation.
7. **Order of registration matters** — it doesn't (resolution is lazy); state this.

---

## 11. Senior follow-ups & variants

### Variant 1 — Auto-wiring via decorators / metadata
NestJS / InversifyJS use TypeScript decorators + `reflect-metadata`. Saves boilerplate but adds compilation step.

### Variant 2 — Async resolution
Factories return Promises; `resolve` becomes async. Whole graph builds asynchronously. Needed for DB connections, KMS clients.

### Variant 3 — Scoped lifetimes
Three lifetimes: singleton (app), scoped (request/child container), transient. Child containers fall through to parent.

### Variant 4 — Disposal hooks
Register `onDispose` per token. Shutdown walks singletons in reverse-creation-order and disposes. Critical for graceful shutdown.

### Variant 5 — Provider pattern for cycle break
Inject `getB: () => container.resolve('B')` instead of `b`. Cycle exists at call time, not construction — breaks the trap.

### Variant 6 — Module system
Group registrations into modules; resolve a module to register all its services at once. NestJS works this way.

---

## 12. How to think aloud

> "Two Maps + one Set. `registry: Map<token, {factory, singleton}>`, `singletons: Map<token, instance>`, `resolving: Set<token>` for cycle detection. `resolve(token)`: cache check first (fast path) → registry lookup (fall through to parent if missing) → cycle check → factory(container) → cache if singleton → return. Use try/finally around the resolving Set so a throwing factory still cleans up. Factory signature `(c) => new Foo(c.resolve('bar'))` lets each factory pull its own deps. Lazy — nothing constructed until first resolve. Order of registration doesn't matter. Pays off past ~20 services. Below that, manual wiring is fine. Trap: no cycle detection → stack overflow. Trap: cleanup without try/finally → stuck token. Trap: singleton state leaks across tests."

---

## 13. 60-second revision

> - **`Map<token, {factory, singleton}>` + `Map<token, instance>` cache + `Set<token>` for cycles.**
> - **Lazy resolve:** nothing built until first `resolve`.
> - **Factory signature:** `(c) => ...`. Pulls own deps via `c.resolve`.
> - **Singleton lifetime:** cache. **Transient:** new each time. **Scoped:** per-child container.
> - **Cycle detection:** in-progress Set; **try/finally** around delete.
> - **Pays off past ~20 services.** Below that, manual wiring is fine.
> - **Family:** NestJS, Inversify, Awilix, tsyringe.
> - **Trap:** no cycle detection; no try/finally; singleton leak across tests.

---

**Related:** [mini-state-machine.md](./mini-state-machine.md) · [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) · [event-emitter.md](./event-emitter.md) · [memoize-ii.md](./memoize-ii.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
