# Factory with Injected Dependencies (Functional DI)

## Source / Origin
- Dependency injection without a framework — Mark Seemann; "Functional Architecture" patterns.
- Asked at: Stripe, Atlassian, Razorpay — services-shop interviews.
- Concept reference: `concepts/closures.md`, sibling `10-machine-coding-patterns/dependency-injection-container.md`.

## Why this question matters in interviews
"How do you test this code that calls `fetch`?" The textbook answer is mocking. The senior answer is: don't call `fetch` directly — accept it as a dependency. A factory closure that captures injected deps gives you (1) trivial unit testing by stubbing in fakes, (2) explicit dependency surface (no hidden globals), (3) no DI container, no decorators, no metadata. It's the smallest viable DI pattern.

## Concepts involved

### Syntax to lock in
```js
// Without DI — hard to test
async function getUser(id) {
  const r = await fetch(`/api/users/${id}`);
  return r.json();
}

// With factory DI
function createUserService({ fetch, logger }) {
  return {
    async getUser(id) {
      logger.info('fetch user', { id });
      const r = await fetch(`/api/users/${id}`);
      return r.json();
    },
  };
}

// In production
const userService = createUserService({ fetch: globalThis.fetch, logger: realLogger });

// In tests
const fakeFetch = (url) => Promise.resolve({ json: () => ({ id: 1, name: 'A' }) });
const test = createUserService({ fetch: fakeFetch, logger: noOpLogger });
const u = await test.getUser(1);
```

### Edge cases / interview traps
1. **Each call to `createUserService` creates a fresh closure** with its own captured deps. Useful for per-request scoping.
2. **Singletons** — call once, export the result. Good for shared connection pools.
3. **No hidden globals** — every dep is in the factory signature. The function's behavior is *entirely* determined by inputs.
4. **Stub fidelity** — your test fakes must match the real shape. Use TypeScript interfaces for safety.
5. **Lazy resolution** — sometimes a dep isn't ready at factory call; pass a function: `({ getDb })` instead of `({ db })`.
6. **Circular deps** — A needs B, B needs A. Resolve via lazy getters or restructure.
7. **Per-request vs per-app scope** — bigger apps mix: app-level deps captured in module init; request-level deps re-captured in middleware.
8. **Test isolation** — don't share factory across tests; each test creates a fresh service.

## Mental Model

A factory is a **function that takes deps and returns a service**:

```
   createUserService({ fetch, logger, db, cache })
            │
            ▼
   ┌──────────────────────────────────┐
   │ closure scope:                    │
   │   fetch, logger, db, cache        │  ← captured
   │                                   │
   │   getUser(id):                    │  ← method captures the scope
   │     uses fetch, logger, ...       │
   │                                   │
   │   updateUser(id, data):           │
   │     uses db, logger               │
   └──────────────────────────────────┘
            │
            ▼
   service = { getUser, updateUser }
```

In production: pass real deps. In tests: pass fakes. Service has *no awareness* of which it got.

## Why interviewers care

- **Testability discipline.** Senior signal.
- **Closure-as-encapsulation** — deps are private to the service.
- **Anti-pattern detection** — they want to see you flinch when code reaches for module-level singletons.

## Common beginner confusion

- **"That's just dependency inversion."** It IS dependency inversion. Functional DI is the simplest form.
- **"This means I need a container."** No — `createService({ a, b, c })` is the entire framework.
- **"Mocking with jest is the same."** Mocking patches the module after-the-fact. Factory DI makes deps explicit and is harder to forget. Mocking is a workaround for bad code; DI is the fix.
- **"I have too many deps in the signature."** That's a signal the service does too much. Split.
- **"Factory must be a class."** No — plain function returning an object is fine.

## Brute force approach

```js
// Module-level singleton — hidden global; can't unit-test isolation
const logger = require('./logger');
const db = require('./db');

async function getUser(id) {
  logger.info(...);
  return db.query(...);
}

// Tests must mock requires (jest.mock) — flaky, slow
```

## Optimal approach

A factory that takes deps as a single object and returns the service. Production wires real deps in `index.js`/composition root. Tests wire fakes.

## Solution (JavaScript)

```js
// service.js
export function createUserService({ fetch, logger, db, cache }) {
  return {
    async getUser(id) {
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

// index.js (composition root)
import { createUserService } from './service.js';
import { fetch } from 'undici';
import { realLogger } from './logger.js';
import { db } from './db.js';
import { redisCache } from './cache.js';

const userService = createUserService({ fetch, logger: realLogger, db, cache: redisCache });
export { userService };

// service.test.js
import { createUserService } from './service.js';

test('getUser uses cache when present', async () => {
  const fakeCache = { get: async () => ({ id: 1, name: 'A' }), set: async () => {}, del: async () => {} };
  const fakeFetch = () => { throw new Error('should not be called'); };
  const fakeLogger = { info() {}, error() {} };
  const fakeDb = {};
  const svc = createUserService({ fetch: fakeFetch, logger: fakeLogger, db: fakeDb, cache: fakeCache });
  const u = await svc.getUser(1);
  expect(u).toEqual({ id: 1, name: 'A' });
});
```

Per-request DI with middleware:

```js
// per-request scope: wire deps per request
app.use((req, res, next) => {
  req.services = createUserService({
    fetch,
    logger: realLogger.child({ requestId: req.id }),    // child logger with request ID
    db,
    cache: redisCache,
  });
  next();
});

app.get('/users/:id', async (req, res) => {
  res.json(await req.services.getUser(req.params.id));
});
```

## Step-by-step dry run

```
createUserService({ fetch: F, logger: L, db: D, cache: C })
  → enter factory scope; capture {F, L, D, C}
  → return service object with methods that close over those four
  
test call:
  fakeCache.get returns { id:1, name:'A' }
  svc.getUser(1):
    cache.get('user:1') → { id:1, name:'A' } (not null)
    return { id:1, name:'A' }
    (logger.info not called, fetch not called, db not touched)

prod call:
  realCache.get('user:1') → null (cache miss)
  logger.info('cache miss', { id: 1 })
  fetch('/api/users/1') → response
  res.json() → { id:1, name:'A' }
  cache.set('user:1', data, ttl:300)
  return data
```

## How to think aloud in the interview

> "Functional DI: factory function takes a deps object, captures it in closure, returns a service with methods that use those deps. No globals, no containers, no decorators. Production wires real deps at the composition root; tests wire fakes. Each method has access to everything it needs from the closure. For per-request scope, the factory is called inside middleware. Trade-off: signature gets verbose when deps multiply — usually a signal the service should be split."

## Important takeaways

- **Factory takes deps; closure captures them.**
- **No hidden globals** — every dep in the signature.
- **Composition root** wires production deps in one place.
- **Tests wire fakes** — no mocking framework needed.
- **Per-request or per-app** scope possible.
- **Many deps = split the service.**

## Variants

- **Class-based DI** — same idea, with classes; constructor takes deps.
- **`InversifyJS` / NestJS DI** — full containers; useful at scale.
- **Async factory** — `async function create...` for deps that need async init.
- **Layered factories** — `createApp({ db, cache })` returns `{ userService, orderService }` each wired.
- **Module replacement** (`jest.mock`) — patches at the require layer; alternative to DI but less clean.

## Revision notes

```
function createService({ dep1, dep2, ... }) {
  // closure captures deps
  return {
    method() { ... uses dep1, dep2 ... },
  };
}

// production
const service = createService({ dep1: real1, dep2: real2 });

// test
const test = createService({ dep1: fake1, dep2: fake2 });

BENEFITS:
  - explicit deps (no hidden globals)
  - trivial testing (no mocking framework)
  - per-request scoping possible
  - composition root pattern

WHEN TO SCALE UP:
  - many deps → split service
  - circular deps → lazy getter or restructure
  - shared per-app deps + per-request deps → mix at composition root
```
