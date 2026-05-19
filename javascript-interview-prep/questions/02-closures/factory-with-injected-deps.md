# Build a `createService({ deps })` factory — functional dependency injection

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [counter-ii.md](./counter-ii.md), [module-pattern-iife.md](./module-pattern-iife.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Mark Seemann's *Functional Architecture*; ubiquitous in modern Node services. Asked at Stripe, Atlassian, Razorpay.

---

## 1. Problem statement

**Signature**
```ts
function createService(deps: { dep1: T1; dep2: T2; ... }): {
  method1(...): ...;
  method2(...): ...;
};
```

**Input / Output examples**

| Setup                                                                                | Production / test         | Behaviour                              |
|--------------------------------------------------------------------------------------|---------------------------|----------------------------------------|
| `createUserService({ fetch, logger, db, cache })`                                    | real deps in prod         | calls real fetch / db / cache          |
| `createUserService({ fetch: fakeFetch, logger: noOp, db: {}, cache: fakeCache })`   | fakes in tests            | no network, no DB; deterministic       |
| `createUserService({ fetch, logger: requestScopedLogger })` per middleware           | per-request scope         | request-scoped logger; shared db/cache |

**Constraints**
- Every dependency is in the factory **signature** — no hidden globals, no `require` inside the service body.
- Factory returns a service object whose methods close over the injected deps.
- Production wires real deps at the **composition root** (typically `index.ts`).
- Tests wire fakes — no mocking framework required.

---

## 2. Plain-English restatement

The interviewer says: "How would you make this code that calls `fetch` testable?" The textbook answer is "use a mocking library." The senior answer is: **accept `fetch` as a dependency**. Write your service as a factory that takes a `deps` object and returns the service. Production code wires the real `fetch`, the real logger, the real database. Test code wires fakes. The service itself doesn't know — and doesn't care — which it got.

This is **functional dependency injection** — the smallest, framework-free form of DI. No containers, no decorators, no metadata. Just closures.

---

## 3. Why this matters in interviews

Senior interviewers ask this to test three things at once. **(1)** Testability discipline — can you make your code unit-testable without relying on `jest.mock` patching the require cache? **(2)** Encapsulation — can you use closures to keep dependencies private to the service? **(3)** Anti-pattern detection — do you flinch when code reaches for module-level singletons, hidden globals, or `Date.now()` called inside business logic? Functional DI is the cleanest answer to all three.

---

## 4. Mental model

A factory is **a function that takes deps and returns a service**. The service's methods close over the deps; the deps are invisible from outside.

```
   createUserService({ fetch, logger, db, cache })
            │
            ▼
   ┌───────────────────────────────────────────┐
   │ closure scope:                            │
   │   fetch, logger, db, cache  ← captured    │
   │                                            │
   │   getUser(id) { uses fetch, logger, ... } │
   │   updateUser(id, data) { uses db, logger }│
   └───────────────────────────────────────────┘
            │
            ▼
   service = { getUser, updateUser }

   PRODUCTION:        TEST:
   ──────────────     ──────────────
   pass real deps     pass fake deps
   service runs       service runs
   real network       no network
```

The service has no awareness of *which* deps it got. That's the whole point — behavior is **entirely** determined by inputs.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `const logger = require('./logger')` inside a service file harder to test than `function createService({ logger })`?
> 2. If your factory's signature has 12 deps, what does that tell you about the service?
> 3. How would you do **per-request scope** — a logger that includes the request ID, but a database connection pool that's shared across requests?

---

## 6. Brute force — walked through

### Wrong attempt 1: module-level singletons

```js
// userService.js
const fetch = require('node-fetch');
const logger = require('./logger');
const db = require('./db');

async function getUser(id) {
  logger.info('fetch user', { id });
  const r = await fetch(`/api/users/${id}`);
  return r.json();
}
module.exports = { getUser };
```

How do you test this? You'd have to either:
- Use `jest.mock('node-fetch')` — patches the require cache, fragile across test suites, doesn't compose.
- Run a real network — slow, flaky.

Either way, you've baked the dependencies into the module. The service is a singleton with hidden global state.

### Wrong attempt 2: pass deps as scattered args

```js
async function getUser(id, fetch, logger, db) {
  logger.info('fetch user', { id });
  ...
}
```

Works mechanically but the signature is bad. Every caller has to pass all 3 deps. The deps leak into every call site instead of being captured once.

### Wrong attempt 3: dependency container with strings

```js
const container = new Container();
container.register('fetch', fetch);
container.register('logger', logger);
async function getUser(id) {
  const fetch = container.resolve('fetch');
  ...
}
```

Now you've got a container. Closure-based DI doesn't need it — you've added ceremony without reducing coupling. The container itself becomes the hidden global.

---

## 7. The unlocking insight

> **A factory function that takes a single `deps` object and returns a service is the simplest, framework-free form of dependency injection. Closures capture the deps; the service methods read them; tests pass fakes; production passes real implementations.**

The pattern has three rules:

1. **Single deps object** as the factory parameter — destructured for clarity. Adding a dep is a one-line change (add to signature; capture in closure).
2. **All side effects** (network, time, randomness, DB) come through deps — never `import { fetch }` inside the service body, never `Date.now()` inside business logic, never `Math.random()` deep in the call tree.
3. **Composition root** wires the real graph in one place (typically `index.ts`). The graph is fully explicit there.

**When to call the factory:**

- **Once per process** (app-level deps) — call at module init, export the singleton.
- **Once per request** (request-scoped deps like a logger with `requestId`) — call inside middleware.
- **Once per task** (rare; usually only for long-running background work with its own context).

**When to break a service into smaller ones:**

If the deps signature has more than ~6 entries, the service is doing too much. Split it.

**Comparison with class-based DI:**

```js
// Class with constructor injection — same pattern, different syntax
class UserService {
  constructor({ fetch, logger, db, cache }) { /* assign to this */ }
  async getUser(id) { /* use this.fetch, this.logger ... */ }
}
```

Equivalent. Closure version is destructure-safe (no `this`); class version is more familiar to OOP-trained engineers. Pick by team culture.

---

## 8. Solution (annotated)

```js
// ── service.js ──────────────────────────────────────────────────
export function createUserService({                        // step 1: factory takes deps object
  fetch,                                                    // step 2: each dep is captured in closure
  logger,
  db,
  cache,
}) {
  return {                                                  // step 3: return the service object
    async getUser(id) {                                     // step 4: methods close over deps
      const cached = await cache.get(`user:${id}`);
      if (cached) return cached;
      logger.info('cache miss', { id });
      const res = await fetch(`/api/users/${id}`);
      const data = await res.json();
      await cache.set(`user:${id}`, data, { ttl: 300 });
      return data;
    },
    async updateUser(id, patch) {
      await db.users.update(id, patch);
      await cache.del(`user:${id}`);
      logger.info('updated', { id });
    },
  };
}

// ── index.js (composition root) ─────────────────────────────────
import { createUserService } from './service.js';
import { fetch } from 'undici';
import { realLogger } from './logger.js';
import { db } from './db.js';
import { redisCache } from './cache.js';

export const userService = createUserService({              // step 5: production wiring
  fetch,
  logger: realLogger,
  db,
  cache: redisCache,
});

// ── service.test.js ─────────────────────────────────────────────
import { createUserService } from './service.js';

test('getUser returns cached value without calling fetch or db', async () => {
  const svc = createUserService({                            // step 6: test wiring with fakes
    fetch: () => { throw new Error('should not be called'); },
    logger: { info() {}, error() {} },
    db: {},
    cache: {
      get: async (k) => k === 'user:1' ? { id: 1, name: 'A' } : null,
      set: async () => {},
      del: async () => {},
    },
  });
  expect(await svc.getUser(1)).toEqual({ id: 1, name: 'A' });
});
```

**Try it yourself**

```js
// Per-request DI with middleware
app.use((req, res, next) => {
  req.services = createUserService({
    fetch,
    logger: realLogger.child({ requestId: req.id }),   // per-request scoped logger
    db,                                                 // shared
    cache: redisCache,                                  // shared
  });
  next();
});

app.get('/users/:id', async (req, res) => {
  res.json(await req.services.getUser(req.params.id));
});
```

---

## 9. Step-by-step dry run

Test scenario (cache hit path):

```js
const svc = createUserService({
  fetch: fakeFetch,
  logger: fakeLogger,
  db: {},
  cache: { get: async () => ({ id: 1, name: 'A' }), set: async () => {}, del: async () => {} },
});
await svc.getUser(1);
```

Values-first trace:

| Step | Call                       | Captured deps used | Outcome                            |
|------|----------------------------|---------------------|-------------------------------------|
| 1    | `createUserService({...})` | (capture all 4)     | returns service object              |
| 2    | `svc.getUser(1)`           | `cache.get('user:1')` | resolves to `{id:1, name:'A'}` (not null) |
| 3    | (cache hit branch)         | (skip logger, fetch) | returns `{id:1, name:'A'}`          |

`fakeFetch` was never called. `fakeLogger.info` was never called. No network, no DB. The test is deterministic and fast.

Production scenario (cache miss path):

| Step | Call                  | Captured deps used                       | Outcome                              |
|------|------------------------|-------------------------------------------|---------------------------------------|
| 1    | `svc.getUser(1)`      | `realCache.get('user:1')`                | resolves to `null` (miss)             |
| 2    | (miss branch)         | `realLogger.info('cache miss', {id:1})`  | logged                                |
| 3    |                        | `fetch('/api/users/1')`                  | resolves with HTTP response           |
| 4    |                        | `res.json()`                              | resolves with `{id:1, name:'A'}`      |
| 5    |                        | `realCache.set('user:1', data, {ttl})`   | cached for next call                  |
| 6    |                        |                                           | returns data                          |

---

## 10. Common confusion + traps

1. **"That's just dependency inversion."**
   It is. Functional DI is the simplest form. The principle is the same as Mark Seemann's *Dependency Injection in .NET*; the implementation is 10 lines of JS.

2. **"This means I need a container."**
   No. `createService({ a, b, c })` is the entire framework. Containers help at scale (auto-resolution of deep graphs) but most services don't need them.

3. **"Mocking with `jest.mock` is the same."**
   Mocking patches the module system **after the fact**. Factory DI makes deps **explicit in the signature** and harder to forget. Mocking is a workaround for code that didn't accept deps; DI is the prevention.

4. **"Factory must be a class."**
   No. Plain function returning an object is fine. Classes work too — same pattern with constructor injection.

5. **"Too many deps in the signature."**
   That's a signal the service does too much. Split. A `UserService` with 12 deps is probably hiding a `UserService` + a `UserBillingService` + a `UserNotificationService`.

6. **"Production wires deps in every file."**
   No — only at the **composition root** (typically `index.ts` or a `compose.ts`). Everywhere else just imports and uses the assembled services.

7. **Hidden `Date.now()` / `Math.random()` / process.env access.**
   These are deps too. Inject them as `now: () => Date.now()` or `rand: () => Math.random()`. Tests that depend on time become trivial.

8. **Circular deps (A needs B, B needs A).**
   Resolve via lazy getters: pass `getB` instead of `b`, call it inside the method. Or restructure to remove the cycle.

---

## 11. Senior follow-ups & variants

### Variant 1 — Layered composition (`createApp`)

For larger systems, layer factories:

```js
function createApp({ db, cache, fetch, logger }) {
  const userService = createUserService({ db, cache, fetch, logger });
  const orderService = createOrderService({ db, cache, userService, logger });
  const paymentService = createPaymentService({ db, fetch, logger, orderService });
  return { userService, orderService, paymentService };
}

// composition root
const app = createApp({ db, cache, fetch: undici.fetch, logger: realLogger });
```

The graph is wired in one place. Each service still has its own narrow deps signature.

### Variant 2 — Class-based DI

```ts
class UserService {
  constructor(private deps: { fetch: Fetch; logger: Logger; db: Db; cache: Cache }) {}
  async getUser(id) { /* this.deps.fetch(...) */ }
}
```

Same shape with constructor injection. Closure version is destructure-safe; class version is more familiar to OOP teams.

### Variant 3 — Async factory

When a dep needs async init (DB connection, secret fetch):

```js
async function createUserService({ fetch, logger, getDb, cache }) {
  const db = await getDb();        // resolve at factory time, once
  return {
    async getUser(id) { /* uses db directly */ },
  };
}
```

Composition root awaits all factories. Slightly more ceremony at boot.

### Variant 4 — Hexagonal-style port adapters

For testing complex flows, separate the *port* (interface) from the *adapter* (implementation):

```js
// port (the interface the service knows about)
type UserStore = {
  getById(id): Promise<User | null>;
  put(user): Promise<void>;
};

// adapter (production implementation)
const postgresUserStore: UserStore = { /* uses pg */ };

// adapter (in-memory implementation for tests)
const fakeUserStore: UserStore = {
  data: new Map(),
  async getById(id) { return this.data.get(id) || null; },
  async put(user) { this.data.set(user.id, user); },
};

const svc = createUserService({ userStore: postgresUserStore });   // prod
const test = createUserService({ userStore: fakeUserStore });      // test
```

The service depends on the port; adapters are swappable. Pure functional architecture.

### Variant 5 — `InversifyJS` / NestJS DI

For very large apps with deep dep graphs, decorators + container resolution can help — annotate classes/factories, the container resolves dependencies automatically by type. Mention it as a tool you'd reach for at scale, not as a default.

---

## 12. How to think aloud in the interview

> "Functional DI: factory function takes a single `deps` object, destructures the deps in the signature, captures them in closure, returns a service whose methods use them. No globals, no containers, no decorators. Production wires real deps at the composition root — `index.js`. Tests wire fakes — no mocking framework needed. Each method has access to everything it needs via the captured scope. Per-request scope: call the factory inside middleware; per-app scope: call once at module init. Trade-off: if the signature has more than ~6 deps, the service is doing too much — split. Hidden deps like `Date.now()` and `Math.random()` should also be injected; tests that depend on time become trivial. For large graphs, layer factories: `createApp({ db, cache })` returns `{ userService, orderService }` each wired."

---

## 13. 60-second revision

> - **Pattern:** `function createService({ dep1, dep2, ... }) { return { method() { /* uses dep1, dep2 */ } }; }`
> - **No hidden globals** — every dep in the factory signature.
> - **Composition root** wires production deps in one place.
> - **Tests wire fakes** — no mocking framework.
> - **Per-request or per-app scope** — call the factory at the right boundary.
> - **Inject side effects** (fetch, time, randomness, env) — tests become deterministic.
> - **Many deps = split the service.**
> - **Circular deps** → lazy getter or restructure.
> - **Family:** module pattern, ports-and-adapters, hexagonal architecture, class constructor injection.
> - **Trap:** `jest.mock` after-the-fact patching; module-level `require` of side-effect deps.

---

**Related:** [module-pattern-iife.md](./module-pattern-iife.md) · [counter-ii.md](./counter-ii.md) · [closure-vs-private-class-field-comparison.md](./closure-vs-private-class-field-comparison.md) · [`10-machine-coding-patterns/dependency-injection-container.md`](../10-machine-coding-patterns/dependency-injection-container.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
