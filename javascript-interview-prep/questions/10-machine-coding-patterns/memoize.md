# Implement `memoize(fn)`

## Source
- Canonical machine-coding interview problem (LeetCode #2623 "Memoize", BFE.dev, Frontend Masters).
- LeetCode reference: https://leetcode.com/problems/memoize/

## Why this question matters in interviews
Memoize is the classic 10-minute warm-up that tests **closures + Map + cache-key design** in one shot. Interviewers love it because the naive solution looks fine but breaks the moment the args contain objects — which leads naturally into the follow-up "Memoize II" (object-keyed memoize). As a backend engineer you've already memoized things — Redis-backed function results, in-process LRUs for hot paths, batched DataLoader-style joins. This question forces you to articulate **what makes a good cache key** and **when memoization is safe** (pure functions only). A senior answer pre-empts the "what about objects?" question by saying "this version assumes primitive args; for object-identity keys, you'd use a Map trie — happy to extend if useful."

## Concepts involved

### Syntax to lock in
```js
const memo = memoize(fn);
memo(1, 2);   // computes fn(1,2), caches result
memo(1, 2);   // returns from cache

function memoize(fn) {
  const cache = new Map();
  return function (...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  };
}
```

### Runtime / engine behavior
- `Map` is preferred over a plain object because:
  - Keys are not stringified (well, we stringify ourselves, but `Map` keeps the original type if we wanted to use object refs).
  - `Map.has` / `Map.get` are O(1), with no `Object.prototype` collision risk (`"constructor"`, `"__proto__"`).
  - Iteration order is guaranteed insertion order — useful for LRU-style eviction (see lru-cache.md).
- `JSON.stringify(args)` is the cheap-and-cheerful key strategy. It works for primitives, primitive arrays, and plain-old-data objects. It's **wrong** for:
  - Objects with circular refs (throws).
  - Objects where you want **identity** equality (two `{a:1}` literals stringify the same but are distinct refs).
  - `undefined` (becomes `null` in arrays, vanishes in object props).
  - Functions, Symbols, BigInt, Date, RegExp, Map, Set.
- Closure mechanics: the `cache` lives in the outer scope and is shared across all calls to the returned wrapper. Each call to `memoize(fn)` gets its own private cache.

### Edge cases (these are the interview traps)
1. **Primitive vs object args** — `JSON.stringify` is fine for `memoize((a, b) => a + b)`. It's catastrophically wrong for `memoize((user) => user.id)` where two users with identical shape but different identities should be cached separately (or, depending on semantics, **together** — that's the design question).
2. **Argument order** — `memo(1, 2)` and `memo(2, 1)` get different keys. Don't sort args unless the function is symmetric.
3. **`this` binding** — `fn.apply(this, args)` preserves method-style usage. Skipping this breaks `obj.compute = memoize(obj.compute)`.
4. **Cache growth unbounded** — memoize has no eviction. For long-running processes this leaks memory. Mention bounded variants (LRU memoize) for senior cred.
5. **Side effects** — memoizing a function with side effects is a bug. The interviewer may bait you with `memoize(console.log)` — flag it.
6. **`fn.length` test cases** — LeetCode's test rig calls memoize with specific functions (sum / fib / factorial) and counts call counts. The wrapper must **not** invoke `fn` more than once per unique arg set.
7. **Recursive memoization** — for `fib`, you only get the benefit if `fib` itself calls the memoized version. The test rig usually arranges this; mention it for bonus.
8. **`NaN` keys** — `JSON.stringify([NaN])` becomes `[null]`. Edge case worth flagging.

## Brute force approach
Use a plain object: `if (key in cache) return cache[key]`. Works, but has the `Object.prototype` collision risk (`memo("toString")` returns the inherited method). And you still need to stringify the args. Skip the plain object; go straight to `Map`.

## Optimal approach
`Map` keyed by `JSON.stringify(args)`. O(1) average lookup, O(K) for the stringify itself where K is the arg payload size. State: one `Map` per memoized function. Per-call: one stringify + one map lookup.

For object-identity-keyed memoization (where two refs with the same shape should NOT collide), see **memoize-ii.md** — that's a different data structure (nested Map trie).

## Solution (JavaScript)

```js
/**
 * Returns a memoized version of `fn`. Keys args via JSON.stringify.
 * Suitable for fn taking primitive args (numbers, strings, booleans, null).
 * @param {Function} fn  must be pure for correctness
 * @returns {Function & { cache: Map, clear: () => void }}
 */
function memoize(fn) {
  const cache = new Map();

  function memoized(...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    return result;
  }

  memoized.cache = cache;            // expose for tests / debugging
  memoized.clear = () => cache.clear();
  return memoized;
}
```

## Step-by-step dry run

Input:
```js
let calls = 0;
const slowSum = (a, b) => { calls++; return a + b; };
const sum = memoize(slowSum);

sum(1, 2);   // (1)
sum(1, 2);   // (2)
sum(2, 1);   // (3)
sum(1, 2);   // (4)
```

Trace:
- Call (1): `args = [1, 2]`. `key = "[1,2]"`. `cache.has(key)` → false. Invoke `slowSum(1,2)` → `3`, `calls=1`. `cache.set("[1,2]", 3)`. Return `3`.
- Call (2): `args = [1, 2]`. `key = "[1,2]"`. Cache **hit**. Return `3`. `calls` unchanged.
- Call (3): `args = [2, 1]`. `key = "[2,1]"`. Cache miss (different key). Invoke → `3`, `calls=2`. `cache.set("[2,1]", 3)`. Return `3`.
- Call (4): `args = [1, 2]`. Cache hit. Return `3`. `calls` unchanged.

After all 4 calls: `calls === 2`. Memoization saved 2 invocations.

Cache state:
```
{
  "[1,2]": 3,
  "[2,1]": 3
}
```

If we tried `sum({id:1}, {id:1})` twice — both stringify to `"[{\"id\":1},{\"id\":1}]"`, so they'd share a cache entry. **That's a bug** if you wanted identity-based memoization. Flag it; this is what Memoize II solves.

## Important takeaways

**Syntax to memorize**
- `const cache = new Map()` in outer scope.
- `JSON.stringify(args)` for primitive-keyed memoize.
- `cache.has(key)` then `cache.get(key)` — avoid double-lookup if you care (`const v = cache.get(key); if (v !== undefined) ...` — but watch out for cached `undefined` results).
- `fn.apply(this, args)` for `this` forwarding.

**Patterns to reuse**
- "Wrap a pure function in a closure-scoped cache" is the same pattern as: TTL cache (add expiry), LRU memoize (add eviction), promise memoize (cache the in-flight promise, not the result — deduplicates concurrent requests).
- Exposing `.cache` and `.clear()` on the returned function is the decorated-function pattern (see debounce's `.cancel` / `.flush`).

**Common mistakes**
- Using a plain object instead of Map → prototype-pollution risk (`memo("hasOwnProperty")`).
- Forgetting `this` forwarding → breaks method-style use.
- Using `JSON.stringify` and being surprised when object-identity-keyed cases collide → that's literally the next question, Memoize II.
- Caching the result of a function that returns `undefined` and then using `cache.get(key) ?? compute()` — re-invokes every time. Use `cache.has(key)`.
- Caching the result of a function with side effects → invisible bug.

**Related questions**
- **Memoize II** — object-identity-keyed memoize using nested Map / WeakMap trie.
- `once(fn)` — memoize where only one cache slot exists.
- `Promise` memoization — cache the in-flight promise to dedupe concurrent fetches.
- LRU cache — bounded memoization.

## Variants

1. **Custom key resolver** — accept a second arg: `memoize(fn, resolver = (...args) => JSON.stringify(args))`. Lodash does this. Lets the caller hash by `args[0].id` only, for example.

2. **TTL memoize** — cache entries expire after N ms. Combine a `Map<key, {value, expiry}>` with a lazy-eviction-on-read.

3. **Async / promise memoize** — `fn` returns a promise. Cache the **promise** (not the resolved value) so concurrent calls reuse the in-flight request. On rejection, evict the entry so the next caller can retry.

4. **Bounded memoize (LRU)** — wrap the cache in an LRU container so the memoized function doesn't leak unbounded memory. See lru-cache.md.

5. **Memoize II** — object-identity-keyed via nested Map trie. Separate file.

## Revision notes

> **memoize — 60 second recap**
> - Closure over a `Map`. Key = `JSON.stringify(args)`.
> - Hit → return cached. Miss → invoke `fn.apply(this, args)`, store, return.
> - **Pure functions only** — memoizing side effects is a bug.
> - **Object args** → stringify-keyed memoize is wrong; use the trie variant (Memoize II).
> - Cache grows unbounded; for production use LRU memoize.
> - **Trap:** plain object cache → prototype pollution. **Trap 2:** `cache.get(key) ?? compute()` re-invokes when cached value is `undefined`.
