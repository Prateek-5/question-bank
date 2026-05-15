# Implement a Tiny DI (Dependency Injection) Container

## Source
- Backend-architecture machine-coding problem (NestJS, InversifyJS, Awilix, tsyringe are the canonical libraries).
- Common at staff-level Node interviews — probes whether you understand the architecture of testable backends.

## Why this question matters in interviews
DI is the **invisible scaffolding** of every non-trivial backend. The container lets you swap implementations at the seams: a real DB connection in prod, a mock in unit tests, a test-containers Postgres in integration tests. Implementing one in ~50 lines tests **`Map<token, factory>`**, **lazy resolution**, **singleton vs transient lifetimes**, **circular-dependency detection**, and the architectural taste to separate **construction** from **use**. Backend interviewers ask this when probing whether you've moved past "instantiate everything in main.ts." It's also the cleanest demonstration of why JS doesn't need decorators or TypeScript metadata to do DI properly — a plain Map is enough.

## Concepts involved

### Syntax to lock in
```js
const container = createContainer();

container.register('db', () => new Database(process.env.DB_URL), { singleton: true });
container.register('userRepo', (c) => new UserRepo(c.resolve('db')));
container.register('userSvc',  (c) => new UserService(c.resolve('userRepo')));

const svc = container.resolve('userSvc');  // builds the whole tree lazily
```

### Runtime / engine behavior
- The container is a `Map<token, { factory, lifetime }>`. Resolution walks the dependency tree by **calling factories with the container itself as an argument**, letting each factory pull its own deps.
- **Lazy resolution** — nothing is constructed until you `resolve(token)`. Registering a Postgres pool doesn't open a connection; resolving the service that needs it does. This makes test setup fast.
- **Singleton lifetime** — first `resolve(token)` calls the factory and caches the instance. Subsequent resolves return the cached one. Implementation: a second Map for resolved singletons.
- **Transient lifetime** — every `resolve(token)` builds a new instance. Useful for stateless utilities, request-scoped objects (if you use a child container per request).
- **Cycle detection** — track tokens currently being resolved in a Set. If `resolve(token)` is called and `token` is already in the in-progress set, throw "circular dependency: a → b → a." Add on enter, delete on exit. Same shape as JSON.stringify cycle detection.

### Edge cases (these are the interview traps)
1. **Cycles** — `A depends on B`, `B depends on A`. Without detection, infinite recursion → stack overflow. With detection, throw a helpful error showing the cycle path.
2. **Lazy injection (`provider` pattern)** — sometimes a cycle is real but can be broken by **deferring resolution**: inject `getB: () => container.resolve('B')` instead of `b`. Cycle still exists in the call graph, but not at construction time. Mention this.
3. **Singleton state leak in tests** — if your test suite shares a container, singleton state leaks across tests. Either reset the container between tests or use a fresh child container per test.
4. **Multiple containers (scopes)** — request-scoped vs app-scoped. A child container can inherit from a parent: `child.resolve('db')` falls through to parent. Common in HTTP frameworks.
5. **Token type** — strings are convenient but typo-prone. Symbols are unique but harder to debug. Classes-as-tokens (`container.resolve(UserService)`) are the TypeScript-y option. Pick one and stay consistent.
6. **Async factories** — `async () => await connectDb()`. Resolution becomes async, the whole graph becomes async. Many DI libs (Awilix) support this; others (InversifyJS) bolt it on awkwardly. Discuss the trade-off.
7. **Missing dependency** — `resolve('userSvc')` but `userSvc` was never registered. Throw with a clear "not registered" error; don't silently return `undefined`.
8. **Order of registration doesn't matter** because resolution is lazy. You can register a dependency after the thing that uses it as long as both are registered before `resolve`. This is the elegance of the pattern.

## Brute force approach
"I'll instantiate everything in `main.ts` and pass deps as constructor args manually." This is the **poor man's DI** — and for tiny apps it's totally fine. The container becomes worthwhile when:
- The graph has >10 nodes.
- You want easy test mocks.
- You want lifetime management (singleton/transient/scoped).
- You want lazy startup (don't connect to DB until something needs it).

Don't shame manual wiring in the interview — say "for a 5-service app I'd wire by hand; the container shines past ~20 services."

Another wrong path: using a service locator (`getService('db')`) as a global singleton. This is "DI with a global," which sacrifices testability — exactly the property DI is supposed to give you. Mention as an anti-pattern.

## Optimal approach
`Map<token, {factory, singleton}>` for registry. `Map<token, instance>` for singleton cache. `Set<token>` for in-progress cycle detection. `resolve(token)` is recursive: lookup → check cycle → call factory(container) → cache if singleton → return.

## Solution (JavaScript)

```js
/**
 * Tiny DI container with singleton/transient lifetimes and cycle detection.
 */
function createContainer(parent = null) {
  const registry = new Map();   // token -> { factory, singleton }
  const singletons = new Map(); // token -> instance
  const resolving = new Set();  // tokens currently being resolved (cycle detection)

  function register(token, factory, { singleton = false } = {}) {
    if (registry.has(token)) {
      throw new Error(`Token already registered: ${String(token)}`);
    }
    registry.set(token, { factory, singleton });
    return container;
  }

  function resolve(token) {
    // Cached singleton?
    if (singletons.has(token)) return singletons.get(token);

    const entry = registry.get(token);
    if (!entry) {
      if (parent) return parent.resolve(token);    // walk up to parent scope
      throw new Error(`Not registered: ${String(token)}`);
    }

    if (resolving.has(token)) {
      const path = [...resolving, token].map(String).join(' -> ');
      throw new Error(`Circular dependency: ${path}`);
    }
    resolving.add(token);

    let instance;
    try {
      instance = entry.factory(container);
    } finally {
      resolving.delete(token);
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

## Step-by-step dry run

Input:
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

const svc = c.resolve('userSvc');
const svc2 = c.resolve('userSvc');
console.log(svc === svc2);  // false — userSvc is transient
console.log(svc.repo.db === svc2.repo.db);  // true — db is singleton
```

Trace:
- `resolve('userSvc')`:
  - Not cached. entry = transient. Add to resolving={userSvc}.
  - factory(c) → `new UserService(c.resolve('repo'))`.
    - `resolve('repo')`:
      - Not cached. transient. resolving={userSvc, repo}.
      - factory → `new UserRepo(c.resolve('db'), c.resolve('log'))`.
        - `resolve('db')`:
          - Not cached. singleton. resolving adds 'db'.
          - factory → `new Db(c.resolve('log'))`:
            - `resolve('log')`: not cached. singleton. factory → `new Logger()`. Cache singletons['log']. resolving removes 'log'. Return logger.
            - `new Db(logger)` constructed. Logs 'db init'.
          - resolving removes 'db'. Cache singletons['db']. Return db.
        - `resolve('log')`: cached → return same logger.
      - `new UserRepo(db, logger)` constructed. resolving removes 'repo'. Return repo.
    - `new UserService(repo)`. resolving removes 'userSvc'. Transient → not cached. Return.
- `resolve('userSvc')` again:
  - Not cached (transient). Re-runs factory → new UserService with `c.resolve('repo')` → new UserRepo with cached db + cached logger. New svc instance, same db, same logger.

Cycle test:
```js
c.register('a', (c) => c.resolve('b'));
c.register('b', (c) => c.resolve('a'));
c.resolve('a');   // throws: Circular dependency: a -> b -> a
```

## Important takeaways

**Syntax to memorize**
- Two Maps + one Set: `registry`, `singletons`, `resolving`.
- Factory signature: `(container) => instance`. Factory pulls its own deps via `container.resolve`.
- Cycle detection via in-progress Set, add on enter, **finally**-delete on exit (so a throw inside the factory still cleans up).
- Singleton cache check is the FIRST thing in `resolve` (before registry lookup) — fast path.

**Patterns to reuse**
- The cycle-detection pattern is the same shape as: JSON.stringify, deep-clone with cycles, topological sort, dependency-graph linkers.
- "Factory takes container as arg" is the **service locator inside a factory** pattern — keeps registration declarative without metadata or reflection.

**Common mistakes**
- Forgetting cycle detection — stack overflow with cryptic stack trace instead of "a → b → a."
- Removing from `resolving` without try/finally — a throw in the factory leaves the token "permanently resolving."
- Using strings as tokens but typo-ing one (`'usrSvc'`). TypeScript symbols-as-tokens or class-as-token catches this at compile time.
- Singleton cache leaking across tests. Always provide a `reset()` or use fresh containers per test.
- Eager resolution at registration time. The whole point is laziness.

**Related questions**
- Lodash's `_.once` (singleton lifetime = once + closure).
- Module bundler dependency graphs (same topology, different goal).
- Express middleware pipeline (similar registration → invocation pattern).
- Factory function vs class — the container doesn't care; both work.

## Variants

1. **Auto-wiring with parameter names / decorators** — read function parameter names (`fn.toString()` parsing) or use TypeScript metadata (`reflect-metadata`) so factories don't have to manually `container.resolve(...)`. NestJS / InversifyJS work this way. Costlier; rely on decorators that compile to runtime metadata.

2. **Async resolution** — factories return Promises; `resolve` becomes async. Whole graph builds asynchronously. Needed for DB connections, KMS clients, anything that can't be constructed synchronously.

3. **Scoped lifetimes** — three lifetimes: singleton (per container), scoped (per child container — typically per HTTP request), transient (always new). Child containers fall through to parent for unregistered tokens.

4. **Disposal** — register an `onDispose` per token. When the container shuts down, walk singletons in reverse-creation-order and call disposal hooks. Critical for graceful shutdown: close DB pools, drain queues, flush logs.

## Revision notes

> **DI container — 75 second recap**
> - `Map<token, {factory, singleton}>` registry + `Map<token, instance>` cache + `Set<token>` for cycle detection.
> - `resolve(token)`: singleton cache hit? → return. Else lookup, check cycle, call `factory(container)`, cache if singleton, return.
> - Factory takes container, pulls its own deps: `(c) => new Foo(c.resolve('bar'))`.
> - **Lazy**: nothing constructed until first `resolve`. Order of registration doesn't matter.
> - Singleton vs transient: cache or don't. Scoped = per-child-container.
> - Cycle detection: in-progress Set, add on enter, finally-delete on exit. Error names the path.
> - Trap: throw without try/finally → token stuck "resolving." Singleton state leaks across tests.
> - Pays off past ~20 services. Below that, manual wiring is fine.
