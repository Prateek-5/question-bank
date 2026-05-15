# Implement `util.promisify`

## Source
- Canonical Node.js machine-coding question — every backend role asks it.
- Node docs: https://nodejs.org/api/util.html#utilpromisifyoriginal
- Variants on BFE.dev (#21 "implement promisify").

## Why this question matters in interviews
Backend JavaScript is full of callback-style APIs — `fs`, `dns`, legacy SDKs, and any vendor library written before 2017. Knowing `promisify` (and being able to implement it in 10 lines) is table stakes. The question also tests **rest args**, **`this` preservation**, **error-first conventions**, and how to expose a clean wrapper. Senior interviewers tack on twists: "what if the callback doesn't follow `(err, value)`?", "handle multi-arg callbacks", "preserve `this`."

## Concepts involved

### Syntax to lock in
```js
const fs = require('fs');
const readFile = promisify(fs.readFile);
const content = await readFile('/etc/hosts', 'utf8');
// fs.readFile(path, opts, cb) → readFile(path, opts) returns Promise.
```

### Runtime / engine behavior
- Node convention: callback is always the **last** arg, signature is `(err, value)`. Err comes first so you don't forget to check it.
- `promisify(fn)` returns a function that, when called, forwards `...args` plus an injected callback, and resolves/rejects the returned promise based on the callback's outcome.
- `this` must be preserved — `promisify(obj.method).call(obj, ...args)` should work. Implementation: use `fn.call(this, ...args, cb)`, not `fn(...args, cb)`.

### Edge cases (interview traps)
1. **Error-first cb** — if `err` is truthy, reject. Otherwise resolve with `value`. Don't swap.
2. **Multi-arg callbacks** — `dns.lookup(host, (err, address, family) => ...)` has TWO success args. Standard `promisify` resolves with only the first. Node provides `util.promisify.custom` symbol for overrides — mention this for senior points.
3. **`this` binding** — must use `fn.apply(this, ...)` or `fn.call(this, ...)` so methods work when promisified.
4. **Calling cb multiple times** — defensive promisify could guard with a "settled" flag; Node's built-in does not.
5. **Synchronous throw in fn** — should be caught and rejected. Optional but bonus-worthy.
6. **`util.promisify.custom`** — if `fn[util.promisify.custom]` is defined, return that instead. (Real Node behavior; rare in interviews but mentionable.)
7. **Length / name preservation** — Node's built-in copies `.name`. Most candidates skip; it's a nice touch.

## Brute force approach
"Return a promise that calls `fn(...args, cb)`." Works on the happy path but breaks `this`, ignores multi-arg, and doesn't guard against `fn` throwing synchronously. Tighten it for senior interviews.

## Optimal approach
Return a closure that captures `fn` and, when invoked, returns a `new Promise((resolve, reject) => fn.call(this, ...args, (err, value) => err ? reject(err) : resolve(value)))`. Wrap the `fn.call` in a `try/catch` to convert sync throws into rejections.

## Solution (JavaScript)

```js
function promisify(fn) {
  return function (...args) {
    return new Promise((resolve, reject) => {
      try {
        fn.call(this, ...args, (err, value) => {
          if (err) return reject(err);
          resolve(value);
        });
      } catch (syncErr) {
        reject(syncErr);
      }
    });
  };
}

// --- usage ---
const fs = require('fs');
const readFile = promisify(fs.readFile);

readFile('/etc/hosts', 'utf8')
  .then(text => console.log(text.length))
  .catch(err => console.error('failed:', err.code));

// Preserves `this` — method-style works:
class Store {
  fetch(key, cb) { setTimeout(() => cb(null, `value-of-${key}`), 50); }
}
const store = new Store();
store.fetchAsync = promisify(store.fetch);
store.fetchAsync('user:1').then(console.log); // 'value-of-user:1'
```

## Step-by-step dry run

Input:
```js
function loadConfig(path, cb) {
  setTimeout(() => {
    if (path === '/bad') return cb(new Error('not found'));
    cb(null, { from: path });
  }, 30);
}

const loadConfigAsync = promisify(loadConfig);
loadConfigAsync('/good').then(v => console.log('ok:', v));
loadConfigAsync('/bad').catch(e => console.log('err:', e.message));
```

Trace:
- **t=0** — `loadConfigAsync('/good')` runs. Enters the wrapper, creates a new Promise. Inside the executor, calls `loadConfig.call(this, '/good', injectedCb)`. `loadConfig` schedules a 30ms timer.
- **t=0** — `loadConfigAsync('/bad')` runs. Same thing, separate timer.
- **t=30** — first timer fires. `loadConfig` calls `cb(null, { from: '/good' })`. Inside `injectedCb`, `err` is null → `resolve({ from: '/good' })`. Then-handler logs `ok: { from: '/good' }`.
- **t=30** — second timer fires. `loadConfig` calls `cb(new Error('not found'))`. `injectedCb` sees truthy `err` → `reject(err)`. Catch-handler logs `err: not found`.

Output:
```
ok: { from: '/good' }
err: not found
```

## Important takeaways

**Syntax to memorize**
- `function (...args) { ... }` — **not** arrow, because we need `this` binding from the caller.
- `fn.call(this, ...args, cb)` — `call` (or `apply`) to forward `this`.
- `(err, value) => err ? reject(err) : resolve(value)` — the canonical injected callback.
- `try/catch` around the `fn.call` so sync throws become rejections.

**Patterns to reuse**
- "Wrap a callback API in a Promise" is the universal **adapter pattern** for legacy code. Same shape used for: wrapping `XMLHttpRequest`, wrapping `IndexedDB` request objects, adapting AWS SDK v2.
- The same trick generalizes to wrapping any continuation-passing function — even non-Node-style — with a small tweak.

**Common mistakes**
- Arrow function instead of `function` — kills `this` binding.
- `fn(...args, cb)` instead of `fn.call(this, ...args, cb)` — breaks method-style usage.
- Forgetting to reject on truthy `err` — promise hangs forever (or worse, resolves with `undefined`).
- Not handling sync throws — wrapper returns rejecting promise on async errors but throws synchronously on bad inputs. Inconsistent.
- Resolving with `[value1, value2]` for multi-arg callbacks — Node's built-in resolves with just the first; if you change this, document it.

**Related questions**
- `promisifyAll(obj)` — promisify every method on an object (Bluebird-style).
- Convert Promise → callback (`callbackify` — Node has this too).
- AsyncLocalStorage usage with promisified APIs (context preservation).

## Variants

1. **`promisify` with custom callback signature** — what if cb is `(value, err)` instead of `(err, value)`? Take a `multiArgs` or `errFirst` option.
2. **`promisifyAll(obj)`** — walk all own methods, attach `<name>Async` versions. Bluebird's API. Memoize so you don't re-promisify on every call.
3. **`callbackify(asyncFn)`** — reverse direction. Inverts the wrapping; useful when handing a promise-returning function to a callback-only API.
4. **`util.promisify.custom` support** — if `fn[util.promisify.custom]` exists, return it directly. Real Node behavior.

## Revision notes

> **promisify — 60 second recap**
> - Wraps `(err, value)` callback-style fn into a promise-returning fn.
> - Return a `function` (not arrow) to preserve `this`.
> - `fn.call(this, ...args, injectedCb)` — forward args AND `this`.
> - Injected cb: `(err, value) => err ? reject(err) : resolve(value)`.
> - Wrap in `try/catch` to convert sync throws to rejections.
> - Multi-arg callbacks: resolve with first by default; use `util.promisify.custom` for overrides.
> - **Trap:** arrow function breaks method-style use; forgetting err check leaves promise hanging.
