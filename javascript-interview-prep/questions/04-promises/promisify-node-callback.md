# Implement `promisify(fn)` — convert callback-style to promise-returning

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [build-promise-from-scratch.md](./build-promise-from-scratch.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** Node `util.promisify`. Canonical interview question. BFE.dev #21.

---

## 1. Problem statement

**Signature**
```ts
function promisify<R>(fn: (...args: any[], cb: (err: any, value: R) => void) => void):
  (...args: any[]) => Promise<R>;
```

**Input / Output examples**

| Setup                                                          | Behaviour                                              |
|----------------------------------------------------------------|---------------------------------------------------------|
| `promisify(fs.readFile)('/etc/hosts', 'utf8')`                | resolves with file content; rejects on error            |
| `promisify(fn)` where `fn` calls `cb(null, value)`             | resolves with `value`                                   |
| `promisify(fn)` where `fn` calls `cb(err)`                     | rejects with `err`                                      |
| `promisify(obj.method).call(obj, ...)`                         | preserves `this` so methods work                        |
| `promisify(fn)` where `fn` throws synchronously                | rejected promise (not crashed wrapper)                  |
| Multi-arg cb: `(err, a, b)`                                    | resolves with `a` (drop `b`) — Node convention          |

**Constraints**
- Node convention: callback is the **last** arg, signature is `(err, value)`.
- `this` must be preserved — `promisify(obj.method).call(obj, ...)` works.
- Sync throws in `fn` become promise rejections.

---

## 2. Plain-English restatement

Wrap a callback-style function so it returns a Promise instead. The wrapper takes the same arguments as the original (without the callback), and the callback you'd have passed is now an internal `(err, value)` handler that calls `resolve(value)` on success or `reject(err)` on error.

The Node convention is "error-first callback": the last arg is `cb(err, value)`, where `err` is `null` on success and an Error on failure. `promisify` mechanically adapts this shape into Promises.

---

## 3. Why this matters in interviews

Backend JavaScript is full of callback-style APIs — `fs`, `dns`, legacy SDKs, anything written before 2017. Knowing `promisify` (and being able to implement it in 10 lines) is table stakes. The question also tests **rest args**, **`this` preservation**, **error-first conventions**, and how to expose a clean wrapper. Senior interviewers tack on twists: "what if the callback doesn't follow `(err, value)`?", "handle multi-arg callbacks", "preserve `this`."

---

## 4. Mental model

```
   Original (callback-style):
   fs.readFile(path, opts, (err, data) => {
     if (err) handleError(err);
     else useData(data);
   });

   After promisify:
   const readFile = promisify(fs.readFile);
   readFile(path, opts).then(useData).catch(handleError);
                          │
                          └── internally:
                              new Promise((resolve, reject) => {
                                fs.readFile.call(this, path, opts, (err, data) => {
                                  if (err) reject(err);
                                  else resolve(data);
                                });
                              });
```

The wrapper:
1. Captures user args.
2. Constructs a Promise.
3. Inside the executor, calls `fn.call(this, ...args, injectedCb)` where `injectedCb` is `(err, value) => err ? reject(err) : resolve(value)`.
4. Returns the Promise.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why must the wrapper be `function (...args)` and not `(...args) =>`?
> 2. If you use `fn(...args, cb)` instead of `fn.call(this, ...args, cb)`, what breaks?
> 3. `dns.lookup(host, (err, address, family) => ...)` has TWO success args. What does `promisify(dns.lookup)('example.com')` resolve with?

---

## 6. Brute force — walked through

### Wrong attempt 1: arrow function wrapper

```js
const promisify = (fn) => (...args) =>
  new Promise((res, rej) =>
    fn(...args, (err, v) => err ? rej(err) : res(v))
  );
```

**Looks fine** — but kills `this` binding. Arrow functions don't have their own `this`; `promisify(obj.method).call(obj, ...)` won't forward `obj` to `fn`. Use `function (...args)` so `this` from the caller is reachable, then `fn.call(this, ...)`.

### Wrong attempt 2: don't preserve `this`

```js
function promisify(fn) {
  return function (...args) {
    return new Promise((res, rej) =>
      fn(...args, (err, v) => err ? rej(err) : res(v))   // BUG: no this binding
    );
  };
}

class Store { fetch(key, cb) { /* uses this.cache */ } }
const store = new Store();
store.fetchAsync = promisify(store.fetch);
store.fetchAsync('user:1');   // BUG: this.cache is undefined inside store.fetch
```

When `store.fetchAsync('user:1')` is invoked, `this` inside the wrapper is `store`. But we call `fn(...args, cb)` without forwarding `this` — `fn` runs with `this === undefined` (strict) or `globalThis` (sloppy). Use `fn.call(this, ...args, cb)`.

### Wrong attempt 3: forget to handle sync throws

```js
function promisify(fn) {
  return function (...args) {
    return new Promise((res, rej) => {
      fn.call(this, ...args, (err, v) => err ? rej(err) : res(v));
      // BUG: if fn throws synchronously (e.g., bad input), wrapper itself throws
    });
  };
}
```

A `fn` that throws before invoking its callback (e.g., validation error) crashes the wrapper synchronously instead of returning a rejected promise. Wrap in try/catch.

### Wrong attempt 4: swap err and value

```js
fn(...args, (value, err) => err ? rej(err) : res(value));   // BUG: wrong arg order
```

Node convention is **err first, value second**. Don't swap. Some libraries use the reverse — those need a custom adapter.

---

## 7. The unlocking insight

> **Return a `function` (not arrow) so the wrapper has its own `this`. Use `fn.call(this, ...args, injectedCb)` to forward both args and `this`. Wrap in try/catch to convert sync throws into rejections.**

The four pieces:

1. **`function (...args)` wrapper** — has its own `this` bound by the caller. Arrow functions don't.
2. **`fn.call(this, ...args, cb)`** — explicit forwarding. `call` (or `apply`) is the only way to pass both `this` and a rest-args list to the underlying function.
3. **`(err, value) => err ? reject(err) : resolve(value)`** — the canonical injected callback. Node convention.
4. **`try/catch` around `fn.call(...)`** — converts sync throws (bad input, type errors) into rejected promises for uniform error handling.

**Edge cases worth knowing**: multi-arg callbacks (Node resolves with first by default; `util.promisify.custom` lets you override), `util.promisify.custom` symbol for explicit overrides, `.name` preservation for debugging. Most of these are senior-bonus mentions.

---

## 8. Solution (annotated)

```js
function promisify(fn) {
  return function (...args) {                            // step 1: function, not arrow
    return new Promise((resolve, reject) => {
      try {
        fn.call(this, ...args, (err, value) => {          // step 2: forward this + args + injected cb
          if (err) return reject(err);                     // step 3: error-first; check err
          resolve(value);                                  // step 4: resolve with value
        });
      } catch (syncErr) {                                  // step 5: convert sync throws to rejections
        reject(syncErr);
      }
    });
  };
}

// Variant: multi-arg callback support
function promisifyMultiArg(fn) {
  return function (...args) {
    return new Promise((resolve, reject) => {
      try {
        fn.call(this, ...args, (err, ...values) => {
          if (err) return reject(err);
          resolve(values);                                 // array of all success args
        });
      } catch (syncErr) {
        reject(syncErr);
      }
    });
  };
}
```

**Try it yourself**

```js
// Basic Node fs
const fs = require('fs');
const readFile = promisify(fs.readFile);

readFile('/etc/hosts', 'utf8')
  .then((text) => console.log(text.length))
  .catch((err) => console.error('failed:', err.code));

// Preserves `this` — method-style works
class Store {
  constructor() { this.cache = new Map(); }
  fetch(key, cb) {
    if (this.cache.has(key)) return cb(null, this.cache.get(key));
    setTimeout(() => cb(null, `value-of-${key}`), 50);
  }
}
const store = new Store();
store.fetchAsync = promisify(store.fetch);
store.fetchAsync('user:1').then(console.log);   // 'value-of-user:1'

// Sync throw is rejection, not crash
function brokenFn(badArg, cb) {
  if (typeof badArg !== 'string') throw new TypeError('bad arg');
  cb(null, 'ok');
}
const wrapped = promisify(brokenFn);
wrapped(42).catch((e) => console.log(e.name));   // 'TypeError'
```

---

## 9. Step-by-step dry run

Input:

```js
function loadConfig(path, cb) {
  setTimeout(() => {
    if (path === '/bad') return cb(new Error('not found'));
    cb(null, { from: path });
  }, 30);
}

const loadConfigAsync = promisify(loadConfig);
loadConfigAsync('/good').then((v) => console.log('ok:', v));
loadConfigAsync('/bad').catch((e) => console.log('err:', e.message));
```

Values-first trace:

| Time (ms) | Event                                                  | Output                |
|-----------|--------------------------------------------------------|-----------------------|
| 0         | `loadConfigAsync('/good')` runs; creates Promise; calls `loadConfig('/good', injectedCb)`; timer scheduled | — |
| 0         | `loadConfigAsync('/bad')` runs; same shape; separate timer | —                |
| 30        | First timer fires; `loadConfig` calls `cb(null, {from:'/good'})`; injectedCb sees `err=null` → resolves with object | — |
| 30+µ      | first `.then` handler runs                             | `ok: { from: '/good' }` |
| 30        | Second timer fires; `loadConfig` calls `cb(new Error('not found'))`; injectedCb sees truthy err → rejects | — |
| 30+µ      | second `.catch` handler runs                           | `err: not found`      |

---

## 10. Common confusion + traps

1. **Arrow function wrapper.** Kills `this` binding. Use `function (...args) { ... }`.

2. **`fn(...args, cb)` instead of `fn.call(this, ...args, cb)`.** Breaks method-style usage.

3. **Forgetting to reject on truthy `err`.** Promise hangs (or worse, resolves with `undefined`).

4. **Not handling sync throws.** Wrapper crashes instead of returning a rejected promise.

5. **Resolving with `[value1, value2]` for multi-arg callbacks.** Node's built-in resolves with just the first; if you change this, document it.

6. **Swapping err and value.** Node convention is err first. Don't break it without an explicit option.

7. **`util.promisify.custom`** — if `fn[util.promisify.custom]` exists, Node's built-in returns that directly. Real-world detail; mention for senior signal.

8. **Calling cb multiple times.** Defensive promisify could guard with a "settled" flag; Node's built-in does not — the Promise state machine handles second-settle as a no-op anyway.

9. **`.name` preservation.** Node's built-in copies `fn.name` onto the wrapper. Nice touch for debugging; most candidates skip.

---

## 11. Senior follow-ups & variants

### Variant 1 — Custom callback signature

```js
function promisifyCustom(fn, options = {}) {
  const { multiArgs = false, errFirst = true } = options;
  return function (...args) {
    return new Promise((resolve, reject) => {
      const cb = errFirst
        ? (err, ...vs) => err ? reject(err) : resolve(multiArgs ? vs : vs[0])
        : (...vs) => {                                  // some libs use (value, ..., err)
            const err = vs[vs.length - 1];
            const values = vs.slice(0, -1);
            err ? reject(err) : resolve(multiArgs ? values : values[0]);
          };
      try { fn.call(this, ...args, cb); }
      catch (e) { reject(e); }
    });
  };
}
```

### Variant 2 — `promisifyAll(obj)` — walk methods, attach Async versions

Bluebird-style. Promisify every own method on an object:

```js
function promisifyAll(obj, suffix = 'Async') {
  for (const key of Object.getOwnPropertyNames(obj)) {
    if (typeof obj[key] === 'function' && !key.endsWith(suffix)) {
      obj[key + suffix] = promisify(obj[key]);
    }
  }
  return obj;
}

const fs = require('fs');
promisifyAll(fs);
fs.readFileAsync('/etc/hosts').then(/* ... */);
```

### Variant 3 — `callbackify` (reverse direction)

```js
function callbackify(asyncFn) {
  return function (...args) {
    const cb = args[args.length - 1];
    asyncFn.apply(this, args.slice(0, -1))
      .then((value) => cb(null, value))
      .catch((err) => cb(err));
  };
}
```

Useful when handing a promise-returning function to a callback-only API.

### Variant 4 — Support `util.promisify.custom`

```js
function promisify(fn) {
  if (fn[promisify.custom]) return fn[promisify.custom];
  // ... standard impl ...
}
promisify.custom = Symbol('util.promisify.custom');
```

Mirror Node's behavior — if `fn` defines its own promisified version via the symbol, return that.

### Variant 5 — Preserve `.name` and `.length`

```js
function promisify(fn) {
  function wrapper(...args) { /* ... */ }
  Object.defineProperty(wrapper, 'name', { value: fn.name });
  Object.defineProperty(wrapper, 'length', { value: Math.max(fn.length - 1, 0) });
  return wrapper;
}
```

Better debugging output and introspection.

---

## 12. How to think aloud in the interview

> "Wrap the callback-style function in a Promise. Return a `function` not an arrow so `this` is bound by the caller. Inside the executor, `fn.call(this, ...args, injectedCb)` forwards `this` and args. The injected callback is `(err, value) => err ? reject(err) : resolve(value)` — Node convention is err-first. Wrap the `fn.call` in try/catch to convert sync throws into rejections. Multi-arg callbacks resolve with the first by default; Node has `util.promisify.custom` for overrides. For walking an entire object, `promisifyAll` from Bluebird-style. Reverse direction: `callbackify`. The Promise state machine ensures double-callback calls are no-ops, so no defensive flag needed."

---

## 13. 60-second revision

> - **Pattern:** `function (...args) { return new Promise((res, rej) => { try { fn.call(this, ...args, (err, v) => err ? rej(err) : res(v)); } catch (e) { rej(e); } }); }`.
> - **`function` not arrow** — preserve `this`.
> - **`fn.call(this, ...args, cb)`** — forward this + args.
> - **Try/catch** for sync-throw safety.
> - **Err first**, value second (Node convention).
> - **Multi-arg cb:** resolve with first by default; `util.promisify.custom` for overrides.
> - **Family:** `promisifyAll` (object-walk), `callbackify` (reverse), `util.promisify.custom`.
> - **Trap:** arrow function killing `this`; forgetting `fn.call(this, ...)`; not handling sync throws; swapping err/value.

---

**Related:** [build-promise-from-scratch.md](./build-promise-from-scratch.md) · [fetch-with-abort.md](./fetch-with-abort.md) · [deferred-with-resolvers.md](./deferred-with-resolvers.md) · [sleep.md](./sleep.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
