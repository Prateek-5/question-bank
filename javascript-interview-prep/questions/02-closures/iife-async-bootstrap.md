# Bootstrap a script with `(async () => { ... })()` — async IIFE

> **Difficulty:** Easy-Medium   |   **Time:** ~10 min   |   **Prereqs:** [module-pattern-iife.md](./module-pattern-iife.md), [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** Pre-TLA module bootstrap idiom; Node CLI scripts.

---

## 1. Problem statement

**Signature**
```js
(async () => {
  // top-level async region
})().catch(handleBoot);
```

**Input / Output examples**

| Code                                                                   | Outcome                                            |
|------------------------------------------------------------------------|-----------------------------------------------------|
| `(async () => { await loadConfig(); startServer(); })().catch(exit1);` | Loads config, starts server. On error: exits 1.    |
| Same without `.catch(...)`                                              | Unhandled rejection — Node 15+ exits with non-zero. |
| `(async () => { return 42; })()`                                       | Returns a Promise; the resolved 42 is usually discarded. |
| `await (async () => { ... })()` (ESM top-level)                        | Equivalent to TLA; in ESM, just use TLA directly.   |

**Constraints**
- For CJS scripts where `await` at top level isn't allowed, wrap async work in an IIFE.
- **Always** attach `.catch(...)` — boot errors are not caught by `uncaughtException`.
- Prefer top-level await (TLA) in ESM where it's available.

---

## 2. Plain-English restatement

In CommonJS scripts, you can't use `await` at the top level. The workaround is to wrap the async work in an immediately-invoked async arrow function — `(async () => { ... })()`. It returns a Promise. You attach `.catch` to handle boot failures (otherwise the process dies via "unhandled rejection"). In ESM, you can use top-level await directly, but the IIFE pattern is still common in CJS and in code that has to support both.

---

## 3. Why this matters in interviews

The async IIFE is a small but telling test. **CJS literacy** — does the candidate know `await` doesn't work at top level there? **Error-handling discipline** — do they remember the `.catch`, knowing that `process.on('uncaughtException')` doesn't catch promise rejections? **Modern awareness** — do they know TLA is the better answer in ESM but the IIFE still has a place? Senior bar: you can articulate all three plus the gotchas (unhandled rejection killing Node 15+, scope isolation, the IIFE doesn't block the rest of the script).

---

## 4. Mental model

A **one-shot async region** carved out inside synchronous code. The IIFE returns a Promise; the script keeps moving while the async work runs in the background.

```
   sync script
     │
     │   (async () => {                          ← carve out async region
     │     await loadConfig();
     │     startServer();
     │   })()                                    ← returns Promise immediately
     │   .catch(handleBoot);                     ← attach error handler
     │
     ▼
   sync script continues (typically just exits to event loop)
   
   async work proceeds in background
     ├── success → IIFE Promise resolves (caller may not care)
     └── failure → IIFE Promise rejects → handleBoot fires
```

The IIFE doesn't block the rest of the sync script. If you want sequential bootstrap, put it all inside the IIFE.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why can't you write `await loadConfig()` at the top of a `.cjs` file?
> 2. If you omit `.catch(...)` and the IIFE rejects, what happens in Node 15+ vs Node 12?
> 3. Why is `(async () => { ... })().then(...)` rare in bootstrap code?

---

## 6. Brute force — walked through

### Wrong attempt 1: top-level `await` in CJS

```js
// boot.cjs
const cfg = await loadConfig();    // SyntaxError: await is only valid in async functions
startServer(cfg);
```

CJS doesn't support top-level `await`. You'd need to either convert to ESM or use the IIFE wrapper.

### Wrong attempt 2: omit `.catch`

```js
(async () => {
  await loadConfig();
  startServer();
})();
```

If `loadConfig()` rejects, the IIFE rejects. There's no `.catch` attached. In Node 15+, an unhandled promise rejection terminates the process with a non-zero exit code (with a noisy `UnhandledPromiseRejection` warning). In older Node, it warns but doesn't exit — leading to zombie processes serving in a half-booted state.

### Wrong attempt 3: rely on `process.on('uncaughtException')`

```js
process.on('uncaughtException', (err) => {
  console.error('boot failed', err);
  process.exit(1);
});

(async () => {
  await loadConfig();
  startServer();
})();
```

`uncaughtException` catches *synchronous* throws and rare async edge cases — but **not** promise rejections in modern Node. For Promise rejections, you need `unhandledRejection` (or attach a `.catch` directly, which is the correct pattern).

---

## 7. The unlocking insight

> **An async IIFE wraps an async region inside synchronous code; it returns a Promise; you must attach `.catch` to handle rejections. In ESM, prefer top-level await — same effect, cleaner syntax.**

The shape is `(async () => { ... })().catch(handler)`. Three properties make it useful:

1. **Scope isolation.** The IIFE creates its own closure. `var`s and locals inside don't leak. Same property as a sync IIFE.
2. **Error containment.** The `.catch` consolidates failure handling in one place. Without it, `unhandledRejection` is your only safety net — and it's a hammer.
3. **Sequential-then-async.** Anything *after* the IIFE in the sync script runs immediately (doesn't wait for the IIFE). Anything *inside* the IIFE runs sequentially (awaited one by one). This lets you mix "bootstrap is async" with "the rest of the script (e.g., signal handlers) is sync."

**When to use:**

- CJS bootstraps (`node script.cjs`).
- ESM where you need to contain errors inside a region (rare).
- Quick one-shot scripts where you want `await` without converting to ESM.

**When to skip:**

- ESM with top-level await available — TLA is cleaner and gives better stack traces.
- Inside larger code — just use `async function main() { ... } main().catch(...)` for clarity.

---

## 8. Solution (annotated)

```js
// Classic CJS bootstrap
(async () => {                                         // step 1: open async IIFE
  const db = await connectDb(process.env.DB_URL);       // step 2: sequential awaits inside
  const cache = await connectRedis(process.env.REDIS_URL);
  const app = createApp({ db, cache });
  app.listen(3000);
  console.log('listening on 3000');
})()                                                    // step 3: invoke immediately
  .catch((err) => {                                     // step 4: ALWAYS attach .catch
    console.error('Boot failed:', err);
    process.exit(1);
  });
```

**Parallel waits**

```js
(async () => {
  const [a, b, c] = await Promise.all([loadA(), loadB(), loadC()]);
  start(a, b, c);
})().catch((err) => { console.error(err); process.exit(1); });
```

**With graceful shutdown**

```js
(async () => {
  const services = await bootServices();
  process.on('SIGTERM', async () => {
    console.log('shutting down');
    await services.close();
    process.exit(0);
  });
})().catch((err) => { console.error(err); process.exit(1); });
```

**Named alternative (preferred for clarity in longer scripts)**

```js
async function main() {
  const db = await connectDb(process.env.DB_URL);
  // ...
}
main().catch((err) => { console.error(err); process.exit(1); });
```

Same shape; the IIFE is just syntactic sugar over this.

---

## 9. Step-by-step dry run

Input:

```js
(async () => {
  await loadConfig();
  startServer();
})().catch(handleBoot);

console.log('script tail');
```

Values-first trace:

| Step | Action                          | Async state                       | Output         |
|------|---------------------------------|------------------------------------|----------------|
| 1    | `(async () => { ... })()`       | Promise created, pending           | —              |
| 2    | `.catch(handleBoot)`            | error handler attached             | —              |
| 3    | `console.log('script tail')`    | (IIFE still pending)               | `script tail`  |
| 4    | (event loop tick)               | `loadConfig()` awaited             | —              |
| 5    | `loadConfig()` resolves         | execution resumes inside IIFE      | —              |
| 6    | `startServer()` runs            | IIFE Promise resolves              | —              |

On rejection:

| Step | Action                | Outcome                              |
|------|------------------------|---------------------------------------|
| 5'   | `loadConfig()` rejects | IIFE Promise rejects                  |
| 6'   | `.catch(handleBoot)`   | handler runs → logs + `process.exit(1)` |

The `console.log('script tail')` ran *before* the IIFE finished — the IIFE doesn't block sync code.

---

## 10. Common confusion + traps

1. **`await` at top level "works" in older Node.**
   It doesn't. CJS has never supported it. The IIFE is the workaround. ESM (Node 14+) added top-level await proper.

2. **`unhandledException` catches promise rejections.**
   It doesn't. Use `unhandledRejection` (or, properly, attach `.catch` to every top-level promise chain).

3. **IIFE blocks the script.**
   It doesn't. It returns a Promise; the rest of the synchronous script continues. If you want sequential bootstrap *plus* sync work afterwards, put the sync work inside the IIFE too.

4. **Returned value matters.**
   It rarely does. The IIFE's resolved value is usually discarded — the side effects (`startServer`) are the point.

5. **`.then(...)` for handling success is overkill.**
   You're not chaining anything. If you need post-boot work, just put it after the last `await` inside the IIFE.

6. **TLA vs IIFE confusion.**
   TLA (ESM `await loadConfig()` at top level) is cleaner. Use it when available. The IIFE is a CJS-era workaround that still has a place in tooling, scripts, and dual-build code.

7. **`void (async () => ...)()`.**
   Common in code that uses `void` to signal "I don't care about the Promise." But you've also lost any error handling — `void` doesn't attach a `.catch`. Avoid unless you've thought it through.

---

## 11. Senior follow-ups & variants

### Variant 1 — TLA equivalent (ESM)

```js
// boot.mjs (or any .js in a "type": "module" package)
const db = await connectDb(process.env.DB_URL);
const cache = await connectRedis(process.env.REDIS_URL);
const app = createApp({ db, cache });
app.listen(3000);
```

Same effect, no IIFE wrapper. Errors propagate as the module's evaluation rejecting, which Node turns into a non-zero exit. Preferred in modern ESM code.

See [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md) for TLA gotchas (circular import deadlock).

### Variant 2 — Named `main()` with `if (require.main === module)`

```js
async function main() {
  const cfg = await loadConfig();
  startServer(cfg);
}
if (require.main === module) {
  main().catch((err) => { console.error(err); process.exit(1); });
}
module.exports = { main };
```

Lets the same file be `require()`d as a library *and* run as a script. Common in CJS CLI tools.

### Variant 3 — Process-level handlers for safety

```js
process.on('unhandledRejection', (reason) => {
  console.error('UNHANDLED REJECTION:', reason);
  process.exit(1);
});

process.on('uncaughtException', (err) => {
  console.error('UNCAUGHT EXCEPTION:', err);
  process.exit(1);
});

(async () => {
  // ... boot ...
})().catch((err) => { /* ... */ });
```

Belt-and-suspenders. The IIFE's `.catch` is the primary; the process-level handlers catch anything that slips past.

### Variant 4 — Parallel boot

```js
(async () => {
  const [db, cache, secrets] = await Promise.all([
    connectDb(),
    connectRedis(),
    fetchSecrets(),
  ]);
  startServer({ db, cache, secrets });
})().catch(/* ... */);
```

Don't await sequentially when the work is independent. Cuts boot time substantially.

### Variant 5 — `Promise.allSettled` for partial-boot tolerance

```js
(async () => {
  const results = await Promise.allSettled([
    connectDb(),
    connectRedis(),
    connectTelemetry(),    // optional — start without it if it fails
  ]);
  const [db, cache, telemetry] = results.map((r) => r.status === 'fulfilled' ? r.value : null);
  if (!db) throw new Error('Cannot boot without database');
  startServer({ db, cache, telemetry });
})().catch(/* ... */);
```

Useful when some boot dependencies are optional. Decide per-dep what to do on failure.

---

## 12. How to think aloud in the interview

> "In CJS scripts you can't `await` at top level, so wrap async work in an immediately-invoked async function: `(async () => { ... })().catch(handler)`. The `.catch` is mandatory — without it, Node 15+ exits on unhandled rejection. `uncaughtException` doesn't catch promise rejections. In ESM I'd use top-level await directly — cleaner, better stack traces. For boot scripts, I also typically add `unhandledRejection` and `uncaughtException` handlers as belt-and-suspenders. Use `Promise.all` inside the IIFE to parallelize independent waits. For named clarity in longer scripts, `async function main() { ... }; main().catch(...)` is equivalent and a bit more readable."

---

## 13. 60-second revision

> - **Pattern:** `(async () => { ... })().catch(handler)` — async IIFE for CJS top-level await.
> - **`.catch` is mandatory** — unhandled rejection exits Node 15+.
> - **ESM:** prefer top-level await (TLA) — cleaner, better stack traces.
> - **Scope isolation** — IIFE's `var`s don't leak.
> - **Doesn't block** the rest of the sync script (returns a Promise).
> - **Parallelize inside** with `Promise.all` for independent waits.
> - **Belt-and-suspenders:** add `process.on('unhandledRejection')` and `('uncaughtException')` handlers.
> - **Named alternative:** `async function main() {} main().catch(...)` — same shape, more readable.
> - **Trap:** trusting `uncaughtException` to catch promise rejections (it doesn't).

---

**Related:** [module-pattern-iife.md](./module-pattern-iife.md) · [`04-promises/top-level-await-deadlock-quiz.md`](../04-promises/top-level-await-deadlock-quiz.md) · [`04-promises/structured-concurrency-primitive.md`](../04-promises/structured-concurrency-primitive.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md), [`concepts/closures.md`](../../concepts/closures.md)
