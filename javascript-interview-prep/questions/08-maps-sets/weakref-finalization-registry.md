# `WeakRef` + `FinalizationRegistry`

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [weakmap-memoize.md](./weakmap-memoize.md)
>
> **Source:** ES2021. Razorpay, Cloudflare, Atlassian — depth questions.

---

## 1. Problem statement

`WeakRef` holds a ref that doesn't prevent GC. `FinalizationRegistry` runs a cleanup when object is collected. Both are advanced and discouraged for normal code.

**Verification examples**

```js
let target = { big: new Array(1e6) };
const ref = new WeakRef(target);

ref.deref();                             // → target (alive)
target = null;
// some time later, GC...
ref.deref();                             // → undefined

const reg = new FinalizationRegistry((heldValue) => {
  console.log('collected:', heldValue);
});
let obj = {};
reg.register(obj, 'token-1');
obj = null;
// eventually: console.log fires with 'token-1'
```

**Constraints**
- GC timing UNSPECIFIED — never rely on when.
- `heldValue` mustn't reference the target.
- Best practice (TC39): avoid unless clear need.

---

## 2. Plain-English restatement

`WeakRef` is a non-pinning reference. `FinalizationRegistry` runs a callback when an object is GC'd. Use sparingly; not deterministic.

---

## 3. Why this matters in interviews

Advanced/rarely needed; knowing them = depth signal. Senior bar: know they're discouraged, valid use cases, non-determinism caveat.

---

## 4. Mental model

```
   WeakRef:
     new WeakRef(target) holds a weak reference.
     ref.deref() returns target OR undefined (if collected).
     If you deref() and store the result, that's a strong ref again — "re-promotes."
   
   FinalizationRegistry:
     reg = new FinalizationRegistry(cb)
     reg.register(target, heldValue, [unregisterToken])
     When target is GC'd, cb(heldValue) MAY fire.
     "MAY" — implementations can defer or skip.
     reg.unregister(token) cancels.
   
   Critical caveats:
     - Timing is unspecified — milliseconds or never.
     - DON'T use for required cleanup (use try/finally or close).
     - DON'T capture target in heldValue/callback — pins it alive.
     - DON'T rely on order; multiple finalizers fire arbitrary order.
     - Microtasks scheduled by finalizer run on host task queue.
   
   Use cases (rare):
     - Caches that don't pin objects (combine WeakMap + WeakRef).
     - Resource cleanup logging (best-effort).
     - Detecting reference-leaks in tests (development only).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can you rely on a finalizer firing?
> 2. What does `deref()` do?
> 3. What's the "re-promotion" risk?

---

## 6. Brute force — walked through

```js
// Wrong: relying on finalizer for cleanup
class FileHandle {
  constructor(path) {
    this.fd = open(path);
    reg.register(this, this.fd);
  }
}
// "fd will be closed when GC reclaims" — NO. May never run.
// Use try/finally + explicit close().
```

---

## 7. The unlocking insight

> **WeakRef = non-pinning ref. FinalizationRegistry = best-effort cleanup callback. Both non-deterministic. Don't rely on either for required cleanup.**

Three properties:

1. **`WeakRef.deref()`** returns target or undefined.
2. **FinalizationRegistry callback** is best-effort.
3. **Both discouraged** for normal flow.

---

## 8. Solution (annotated)

```js
// Cache that doesn't pin values
class WeakValueCache {
  #refs = new Map();                                                      // key → WeakRef
  set(key, obj) {
    this.#refs.set(key, new WeakRef(obj));                                // step 1: weak ref
  }
  get(key) {
    const r = this.#refs.get(key);
    if (!r) return undefined;
    const val = r.deref();                                                 // step 2: maybe alive
    if (val === undefined) {
      this.#refs.delete(key);                                              // step 3: clean stale
      return undefined;
    }
    return val;
  }
}

// FinalizationRegistry for connection cleanup (best-effort logging)
const connReg = new FinalizationRegistry((heldId) => {
  console.warn('Connection leaked:', heldId);
});

class Connection {
  constructor(id) {
    this.id = id;
    this.fd = openSocket();
    connReg.register(this, this.id, this);                                 // step 4: register
  }
  close() {
    closeSocket(this.fd);
    connReg.unregister(this);                                              // step 5: deregister
  }
}
// If Connection is GC'd without close(), finalizer logs.
// MUST still call close() in normal flow — finalizer is just a safety net.

// Multi-resource cleanup with token
const reg = new FinalizationRegistry((heldValue) => {
  if (heldValue.type === 'buffer') releaseBuffer(heldValue.id);
});
function trackedBuffer() {
  const buf = createBuffer();
  reg.register(buf, { type: 'buffer', id: buf.id });
  return buf;
}
```

**Try it yourself**

```js
// Demonstrating non-determinism
let target = { data: 'test' };
const ref = new WeakRef(target);

console.log(ref.deref());                                     // {data:'test'}
target = null;
// In Node: --expose-gc + global.gc() forces GC
if (global.gc) global.gc();
setTimeout(() => {
  console.log(ref.deref());                                   // undefined (after GC)
}, 100);

// Re-promotion risk
let r = null;
{
  let local = { a: 1 };
  const w = new WeakRef(local);
  r = w.deref();    // r is now a STRONG ref to local
  local = null;     // local dropped, but r holds it
}
// local survives because r holds it. Defeats WeakRef's purpose.

// FinalizationRegistry — typical use
const cleanup = new FinalizationRegistry((heldValue) => {
  console.log('GC reclaimed:', heldValue);
});

(function () {
  let obj = { name: 'temp' };
  cleanup.register(obj, 'temp-1');
})();   // obj out of scope
// Eventually (maybe seconds, maybe never): logs 'GC reclaimed: temp-1'

// Don't capture target in heldValue
const wrongReg = new FinalizationRegistry((held) => {
  console.log(held.target.name);   // held.target prevents target from GC!
});
const target2 = { name: 'foo' };
wrongReg.register(target2, { target: target2 });   // ← BAD: cycle
// target2 never GC'd.
```

---

## 9. Step-by-step dry run

```
let t = { big: 1 };
const ref = new WeakRef(t);
ref.deref();    // {big:1} (alive).

t = null;       // last user-side strong ref dropped.

GC: t now only weakly referenced by ref. Eligible for collection.
GC timing: unspecified — could be next major collection, could be never.

Eventually GC runs:
  t reclaimed.
  ref.deref() now returns undefined.

Re-promotion:
  let saved = ref.deref();   // if not yet collected, saved holds strong ref.
  saved keeps target alive even though `ref` is weak.

FinalizationRegistry:
  let obj = {};
  reg.register(obj, 'token').
  obj = null;
  GC eventually:
    Registry callback queued.
    Runs on host task: cb('token').
    Note: NOT a microtask; on a task (setTimeout-like).
  
  Capture risk:
    reg.register(target, target) → cb(target).
    cb closure captures target → if cb is held, target held → no GC.
    Always: don't pass target as heldValue.
```

---

## 10. Common confusion + traps

1. **Rely on finalizer for required cleanup** — wrong; not guaranteed.
2. **`deref()` and store** — re-promotes.
3. **Capture target in heldValue** — pins alive.
4. **Closure in finalizer captures target** — same.
5. **Iterate / size** — not iterable.
6. **GC observable** — non-deterministic, test-unfriendly.
7. **Cross-realm refs** — undefined behavior.

---

## 11. Senior follow-ups & variants

### Variant 1 — WeakValueCache
Cache with weak values; auto-clean on stale.

### Variant 2 — Leak detector (test only)
Register objects; log if collected.

### Variant 3 — Generational cache
Promote hot entries; weak refs for cold.

### Variant 4 — WeakMap vs WeakRef
WeakMap key weakly held; WeakRef explicit weak ref.

### Variant 5 — Node `v8.setFlagsFromString('--expose-gc')`
Force GC for testing.

---

## 12. How to think aloud

> "`WeakRef` and `FinalizationRegistry` are ES2021 advanced GC primitives. WeakRef is a non-pinning reference: `new WeakRef(obj)`, `ref.deref()` returns obj or undefined if collected. FinalizationRegistry: callback runs when an object is GC'd — `reg.register(target, heldValue)`; later `cb(heldValue)` MAY fire. Both are discouraged for normal use: GC timing is unspecified — finalizer may run milliseconds later, may never run. Don't rely on either for required cleanup (use try/finally or explicit close()). Pitfalls: 'Re-promotion' — `deref()` returns a strong reference; if you store it, you've pinned the object alive. 'heldValue capturing target' — if your `heldValue` or callback closure holds target, target can't be GC'd → finalizer never fires. Valid use cases (rare): WeakValueCache (cache with weak values; clean stale on access); best-effort resource leak logging (still call close() in normal flow); test-only leak detection. Node testing: `--expose-gc` + `global.gc()` forces collection. TC39 explicit advice: avoid unless clear need. Trap: rely on finalizer; deref re-promote; capture target; assume order."

---

## 13. 60-second revision

> - **`WeakRef.deref()`** → target or undefined.
> - **FinalizationRegistry callback** — best-effort.
> - **GC timing unspecified.**
> - **Don't rely on for required cleanup** — use try/finally.
> - **Re-promotion** — storing deref() pins.
> - **Capture target in heldValue** → pins alive.
> - **WeakValueCache** — valid use case.
> - **`--expose-gc` + `global.gc()`** for tests.
> - **Trap:** rely on finalizer; capture target; re-promote.

---

**Related:** [weakmap-memoize.md](./weakmap-memoize.md) · [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [ttl-map.md](./ttl-map.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
