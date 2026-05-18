# Async IIFE Bootstrap

## Source / Origin
- Pre-TLA module bootstrap idiom; Node CLI scripts; classic "await at top of script."
- Asked at: Razorpay, Atlassian, Cloudflare.
- Concept reference: `concepts/closures.md`, `04-promises/top-level-await-deadlock-quiz.md`.

## Why this question matters in interviews
Pre-ES2022 (and still in CJS), you couldn't `await` at top-level. The idiom is `(async () => { ... })()` — an immediately-invoked async function expression. Senior bar: you know it predates TLA, when to still use it (CJS, error containment), and the gotchas (unhandled rejection on top-level errors).

## Concepts involved

### Syntax to lock in
```js
// Classic async IIFE
(async () => {
  const cfg = await loadConfig();
  startServer(cfg);
})().catch(err => {
  console.error('boot failed', err);
  process.exit(1);
});
```

### Edge cases / traps
1. **Unhandled rejection.** Without `.catch` the IIFE rejects silently — Node 15+ exits, older versions warn only.
2. **Sequential await in IIFE** is fine; parallelize with `Promise.all`.
3. **Scope isolation** — the IIFE creates its own closure, so `var`s inside don't leak.
4. **Top-level await preferred in ESM** for cleaner stack traces; IIFE for CJS or when ESM isn't available.
5. **Returning a value from IIFE** is rarely useful — value is discarded.
6. **IIFE around code that throws synchronously** still gets wrapped — `(async () => { throw new Error() })()` returns a rejected Promise.

## Mental Model

The async IIFE is **a one-shot async region** with its own scope:

```
   ┌─ outer (sync) script ──────────────┐
   │                                    │
   │   (async () => {                   │
   │     // async territory             │
   │     await foo()                    │
   │   })()                             │
   │   .catch(handleBoot)               │
   │                                    │
   │   // back to sync; doesn't wait    │
   └────────────────────────────────────┘
```

## Why interviewers care

- **CJS literacy** — TLA doesn't exist there.
- **Error handling discipline** — boot errors must be caught.
- **Scope isolation** patterns.

## Common confusion

- **"`await` works without async."** Only at module top-level in ESM, not in CJS scripts.
- **"Boot errors are caught by `process.on('uncaughtException')`."** Only sync exceptions; promise rejections need `unhandledRejection` listener or `.catch`.
- **"IIFE blocks the script."** It returns a Promise; the rest of the script continues unless you await it (you can't, in CJS top-level).

## Brute force

`async function main() {} main()` — same idea, named. Fine, but IIFE is one-liner.

## Optimal approach

`(async () => { ... })().catch(handleBoot)` — concise, contained, error-safe.

## Solution

```js
// CJS bootstrap (Node script.cjs)
(async () => {
  const db = await connectDb(process.env.DB_URL);
  const cache = await connectRedis(process.env.REDIS_URL);
  const app = createApp({ db, cache });
  app.listen(3000);
  console.log('listening on 3000');
})().catch(err => {
  console.error('Boot failed:', err);
  process.exit(1);
});

// With graceful shutdown
(async () => {
  const services = await bootServices();
  process.on('SIGTERM', async () => {
    console.log('shutting down');
    await services.close();
    process.exit(0);
  });
})().catch(err => { console.error(err); process.exit(1); });

// Parallel waits inside IIFE
(async () => {
  const [a, b, c] = await Promise.all([loadA(), loadB(), loadC()]);
  start(a, b, c);
})();
```

## Dry run

```
(async () => {
  await loadConfig();    // suspended
  startServer();
})().catch(handler);

  evaluation:
    create async function
    call it → returns Promise (in pending state)
    promise.catch(handler) registered
    sync script continues (typically just exits to event loop)

  async work proceeds; on success, IIFE's Promise resolves
  on failure, IIFE's Promise rejects → handler runs
```

## How to think aloud

> "Async IIFE: wrap your top-level await needs in `(async () => { ... })()` and always attach a `.catch`. In ESM you can use top-level await directly; CJS doesn't allow it. The IIFE returns a Promise; un-caught rejection terminates the process on Node 15+. I'd parallelize inside with Promise.all, and add a SIGTERM handler outside for graceful shutdown."

## Important takeaways

- **`.catch` mandatory** to avoid unhandled rejection.
- **ESM: prefer TLA.** CJS: IIFE.
- **Scope isolation** — `var`s in IIFE don't leak.
- **Parallelize with `Promise.all`** inside.
- **Returned value usually discarded.**

## Variants

- **Named async function call** — `async function main() {}; main().catch(...)`. Equivalent.
- **`void (async () => ...)()`** — communicates "I don't care about the Promise" but loses error handling.
- **Top-level await (ESM)** — preferred where available.

## Revision notes

```
(async () => { ... })().catch(handler)

USES:
  - CJS scripts (no TLA)
  - one-shot bootstrap
  - error containment with .catch

TRAPS:
  - missing .catch → unhandled rejection
  - thinking IIFE blocks script (it doesn't)

PREFER TLA in ESM
```
