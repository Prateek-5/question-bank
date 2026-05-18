# WeakRef + FinalizationRegistry

## Source / Origin
- ES2021.
- Asked at: Razorpay, Cloudflare, Atlassian — modern-JS depth questions.
- Concept reference: `concepts/maps-sets.md`.

## Why this question matters in interviews
`WeakRef` lets you hold a reference that *doesn't* prevent GC. `FinalizationRegistry` lets you run cleanup when an object is collected. Both are advanced and rarely needed — but knowing them signals depth. Senior bar: you know they're discouraged for normal code, can describe valid use cases (caches that don't pin objects, resource cleanup), and the non-determinism caveat.

## Concepts involved

```js
let target = { big: new Array(1e6) };
const ref = new WeakRef(target);

ref.deref();         // returns target (still alive)
target = null;
// some time later, GC collects target
ref.deref();         // returns undefined

const reg = new FinalizationRegistry(heldValue => {
  console.log('collected:', heldValue);
});
let obj = {};
reg.register(obj, 'obj-key');
obj = null;
// eventually: console.log fires with 'obj-key'
```

### Edge cases / traps
1. **GC timing is unspecified.** You can't rely on *when* a finalizer runs; only that it *may*.
2. **Don't use for critical cleanup.** Use try/finally for that.
3. **`WeakRef` can re-promote.** If you `deref()` and assign somewhere, the object stays alive.
4. **`registry.unregister(token)`** to deregister a watch.
5. **`heldValue` mustn't reference the target** — would prevent collection.
6. **Closures inside finalizers** that capture the target also prevent collection.
7. **Iteration**: WeakRef/Registry are not iterable.
8. **Best practice (TC39 note)**: "avoid these unless you have a clear use case."

## Mental Model

```
   Normal reference:   strong; prevents GC
   WeakRef:            weak; doesn't prevent GC; deref() returns obj or undefined
   FinalizationRegistry: register(obj, heldValue); when obj is GC'd, call cleanup(heldValue)
```

## Why interviewers care

- **Modern-JS literacy.**
- **GC understanding.**
- **Non-determinism awareness.**

## Common confusion

- **"WeakRef is like WeakMap value."** Conceptually related; WeakRef is per-object reference, WeakMap is key→value with weak keys.
- **"Finalizer always runs."** Not guaranteed; engine may skip on shutdown.
- **"Use for resource cleanup like file handles."** No — use try/finally or explicit close. Finalizer is best-effort.
- **"WeakRef prevents memory leaks."** Doesn't help unless the rest of the graph also weakens.

## Solution

```js
// 1. GC-friendly memoize — cached values can be collected if memory tight
class WeakRefMemo {
  cache = new Map();
  get(key, compute) {
    const ref = this.cache.get(key);
    const cached = ref?.deref();
    if (cached) return cached;
    const fresh = compute();
    this.cache.set(key, new WeakRef(fresh));
    return fresh;
  }
}

// 2. Resource cleanup notification
const fileHandles = new FinalizationRegistry((fd) => {
  console.warn(`File ${fd} was not closed before GC — bug!`);
});

class File {
  constructor(path) {
    this.fd = openSync(path);
    fileHandles.register(this, this.fd, this);
  }
  close() {
    if (this.fd != null) { closeSync(this.fd); fileHandles.unregister(this); this.fd = null; }
  }
}

// 3. Subscriber pattern that doesn't pin subscribers
class Topic {
  subs = new Set();
  subscribe(fn) { this.subs.add(new WeakRef(fn)); }
  emit(value) {
    for (const ref of this.subs) {
      const fn = ref.deref();
      if (fn) fn(value);
      else this.subs.delete(ref);
    }
  }
}

// 4. Cleanup with held value avoiding target capture
const reg = new FinalizationRegistry(({ id }) => {
  // do NOT reference the target here
  console.log('release lease', id);
});
function lease(target, leaseId) {
  reg.register(target, { id: leaseId });
}
```

## Dry run

```
let obj = { data: ... };
const ref = new WeakRef(obj);
ref.deref();   // → obj

obj = null;     // sole strong ref dropped
// GC may run; obj becomes unreachable
// ref.deref() now → undefined (after collection)

// FinalizationRegistry:
const r = new FinalizationRegistry(v => console.log('gone:', v));
let target = {}; r.register(target, 'mykey');
target = null;
// eventually: "gone: mykey" (when GC happens)
```

## How to think aloud

> "WeakRef holds a weak pointer — deref returns the object or undefined if collected. FinalizationRegistry runs a callback when the registered object is collected; the held value must not reference the target. Both are non-deterministic — don't use for critical cleanup. Valid uses: GC-friendly caches, leak-detection in dev (warn when a resource wasn't explicitly closed), unbinding observer patterns. For real cleanup, use try/finally or explicit dispose."

## Important takeaways

- **`WeakRef.deref()`** returns target or undefined.
- **`FinalizationRegistry.register(target, heldValue, token?)`** runs callback on GC.
- **Don't reference target in heldValue** — would prevent GC.
- **GC timing not guaranteed.** Best-effort.
- **Use cases**: GC-friendly cache, leak warnings, weak observers.
- **Not for critical cleanup** — use try/finally or `Symbol.dispose`.

## Variants

- **`Symbol.dispose` / `using` declaration** (ES2023+) — deterministic resource cleanup; *preferred* for files/locks.
- **WeakMap/WeakSet** — weak keys; related but different.
- **Per-realm registries** — each realm has its own.

## Revision notes

```
WeakRef(target):
  .deref() → target or undefined (after GC)
  doesn't prevent collection

FinalizationRegistry(callback):
  .register(target, heldValue, unregisterToken?)
  callback(heldValue) — eventually, when target collected
  .unregister(token)
  
RULES:
  - GC timing NOT guaranteed
  - heldValue must NOT reference target
  - don't rely on for critical cleanup
  - prefer try/finally or Symbol.dispose

USES:
  - GC-friendly caches (cache.set(key, new WeakRef(value)))
  - leak warnings (dev: register fd; if finalizer fires before close → bug)
  - weak observers
```
