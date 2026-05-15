# Deduplicate an array — Set vs Map vs filter+indexOf

## Source
- Canonical interview warm-up across all levels (BFE.dev, LeetCode #26 variant, codedamn).
- MDN: [Set](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set), [Map](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map).

## Why this question matters in interviews
Dedup looks like a one-liner (`[...new Set(arr)]`), and that's why it's diagnostic. Interviewers ask follow-ups: "now dedup an array of objects by `id`", "what's the time complexity of `filter + indexOf`?", "what happens with NaN?", "what about reference equality?". The candidate who blurts the one-liner and stops gets a polite "thanks." The candidate who sketches **three approaches with their Big-O** and chooses between them based on input type gets the senior nod. Backend engineers also need this for deduping DB results, idempotency keys, batch-processing events, etc.

## Concepts involved

### Syntax to lock in
```js
// Primitives — Set is canonical
[...new Set([1, 2, 2, 3, 3, 3])];        // [1, 2, 3]

// Objects by key — Map with first-write-wins
const dedupByKey = (arr, keyFn) =>
  [...new Map(arr.map(x => [keyFn(x), x])).values()];

dedupByKey(users, u => u.id);
```

### Runtime / engine behavior
- **Set** uses **SameValueZero** equality (same as `Map.prototype.has`). This means: `NaN` is equal to `NaN` (unlike `===`), but `+0` and `-0` are equal (unlike `Object.is`).
- Sets and Maps maintain **insertion order** — iteration order is deterministic and matches insertion. Critical for dedup-by-key where you want "first occurrence wins."
- Set/Map use hash tables internally (V8 uses a chained hash table called `OrderedHashSet`/`OrderedHashTable`). `add`, `has`, `delete` are amortized O(1).
- Spreading `[...new Set(arr)]` is O(n) — single pass into the set, single pass out.
- `Array.prototype.indexOf` uses **strict equality (`===`)** — so `NaN` won't dedup with indexOf-based approaches.
- `Array.prototype.includes` uses **SameValueZero** — finds NaN, unlike indexOf.

### Edge cases (the interview traps)
1. **NaN** — `new Set([NaN, NaN]).size` is `1`. `[NaN, NaN].filter((v, i, a) => a.indexOf(v) === i)` returns `[]` (indexOf can't find NaN). Massive footgun.
2. **Reference equality** — `new Set([{}, {}]).size` is `2` — two distinct objects. To dedup by content, use a key function.
3. **-0 vs +0** — `new Set([0, -0]).size` is `1` (SameValueZero treats them equal). Rarely matters but interviewers love it.
4. **Order preservation** — when deduping, do you keep the first occurrence or the last? `Set` keeps first; `Map.set` overwrites, so dedup-by-key with `Map` ALSO keeps first if you use `if (!map.has(k))` — but `new Map(arr.map(...))` actually keeps the **last** because Map constructor overwrites. Worth knowing.
5. **Type coercion** — `'1'` and `1` are distinct in a Set (no coercion).
6. **Deep dedup** — `{a: 1}` and `{a: 1}` are distinct references. Use `JSON.stringify` as key (with caveats — key order, undefined values, circular refs).

### Time / space complexity
| Method | Time | Space | Handles NaN | Handles objects |
|---|---|---|---|---|
| `[...new Set(arr)]` | O(n) | O(n) | Yes | Reference-only |
| `arr.filter((v, i, a) => a.indexOf(v) === i)` | O(n²) | O(n) | **No** | Reference-only |
| `Map`-based dedup-by-key | O(n) | O(n) | Yes (in key) | Yes (by key) |
| `reduce` + `seen` object | O(n) | O(n) | Yes if `seen` is `Set` | Depends |

## Brute force approach
Two nested loops, push if not seen:
```js
function dedupBrute(arr) {
  const result = [];
  for (const x of arr) {
    let seen = false;
    for (const y of result) if (x === y) { seen = true; break; }
    if (!seen) result.push(x);
  }
  return result;
}
```
O(n²) time. Also fails on NaN (`===`). Mention as a strawman, then immediately move to Set.

The slightly-better-but-still-bad version is `filter + indexOf`:
```js
arr.filter((v, i) => arr.indexOf(v) === i);
```
Still O(n²), still NaN-broken. Looks clever, isn't.

## Optimal approach
- **Primitives**: `[...new Set(arr)]`. O(n) time, O(n) space. Done.
- **Objects by key**: `[...new Map(arr.map(o => [keyFn(o), o])).values()]`. O(n) time.
- **Deep dedup of plain objects**: serialize to a stable key (sorted-keys JSON), use Set/Map on the serialized form. O(n × k) where k is object size.

The choice depends on element type. Always state your assumption first.

## Solution (JavaScript)

```js
// 1. Primitives — canonical
const dedup = (arr) => [...new Set(arr)];

// 2. Objects by single key (first-occurrence-wins variant)
function dedupByKey(arr, keyFn) {
  const seen = new Set();
  const result = [];
  for (const item of arr) {
    const k = keyFn(item);
    if (!seen.has(k)) {
      seen.add(k);
      result.push(item);
    }
  }
  return result;
}

// 2b. Map-based one-liner (last-occurrence-wins because Map.set overwrites)
const dedupByKeyLastWins = (arr, keyFn) =>
  [...new Map(arr.map(o => [keyFn(o), o])).values()];

// 3. Deep dedup using stable JSON key
function dedupDeep(arr) {
  const stableStringify = (v) => {
    if (v === null || typeof v !== 'object') return JSON.stringify(v);
    if (Array.isArray(v)) return '[' + v.map(stableStringify).join(',') + ']';
    return '{' + Object.keys(v).sort()
      .map(k => JSON.stringify(k) + ':' + stableStringify(v[k]))
      .join(',') + '}';
  };
  const seen = new Set();
  return arr.filter(item => {
    const k = stableStringify(item);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

// 4. Slow but historical — filter + indexOf
const dedupSlow = (arr) => arr.filter((v, i) => arr.indexOf(v) === i);
// O(n²), broken on NaN
```

## Step-by-step dry run

Input 1 — primitives:
```js
[...new Set([1, 2, 2, NaN, NaN, 3])];
// Set internals (insertion order):
//   add(1) → {1}
//   add(2) → {1, 2}
//   add(2) → no-op (SameValueZero hit)
//   add(NaN) → {1, 2, NaN}
//   add(NaN) → no-op (NaN === NaN under SameValueZero)
//   add(3) → {1, 2, NaN, 3}
// Spread → [1, 2, NaN, 3]
```

Input 2 — objects by id (first wins):
```js
const users = [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
  { id: 1, name: 'Alice-dup' },
];
dedupByKey(users, u => u.id);
// seen = {}
// item={id:1,...Alice} → k=1, !seen → push, seen={1}
// item={id:2,...Bob}   → k=2, !seen → push, seen={1,2}
// item={id:1,...Alice-dup} → k=1, seen has it → skip
// → [{id:1,Alice}, {id:2,Bob}]
```

Input 3 — last-wins via Map constructor:
```js
dedupByKeyLastWins(users, u => u.id);
// Map entries built:
//   [1, Alice] → Map{1→Alice}
//   [2, Bob]   → Map{1→Alice, 2→Bob}
//   [1, Alice-dup] → Map{1→Alice-dup, 2→Bob}  // overwrite
// values() → [Alice-dup, Bob]
```

This is the "trap": `new Map(entries)` is **last-wins**, not first-wins. Many candidates write the one-liner expecting first-wins. Use the explicit loop if you need first-wins guarantee.

## Important takeaways

**Syntax to memorize**
- `[...new Set(arr)]` — primitives, first-wins, O(n).
- `[...new Map(arr.map(o => [keyFn(o), o])).values()]` — objects by key, **last-wins**.
- For first-wins on objects, use an explicit loop with `seen.has(k)`.
- `Set` uses **SameValueZero** — NaN-friendly.
- `Array.prototype.includes` uses SameValueZero too; `indexOf` uses `===`.

**Patterns to reuse**
- **Set as a seen-cache** — single-pass dedup is the same pattern as cycle detection, visited-nodes in graph traversal, request idempotency.
- **Map for keyed collections** — `Map<key, value>` is the canonical "I want a JS object but with order + non-string keys" pattern.
- **Stable JSON key** — sorted-keys serialization is the dedup-by-content idiom; same trick used in cache keys, content-addressed storage.

**Common mistakes**
- Using `filter + indexOf` and not noticing it's O(n²). Junior tell.
- Using `JSON.stringify` for deep dedup without sorting keys — `{a:1,b:2}` and `{b:2,a:1}` produce different strings.
- Expecting `new Map(arr.map(...))` to keep the **first** occurrence (it keeps the last).
- Using `===` for NaN dedup — NaN never equals NaN under `===`.
- Forgetting Set's reference equality on objects — `new Set([{}, {}]).size` is `2`.

**Related questions**
- `array-set-ops` — intersection / union / difference via Set.
- `polyfill-includes` vs `polyfill-indexOf` (SameValueZero vs `===`).
- `two-sum-map` — Map as complement-cache.
- LRU cache (uses Map's insertion-order property).

## Variants

1. **Dedup keeping last occurrence** — easy with the `new Map(arr.map(...))` trick, or explicit "iterate reverse, dedup, reverse back."

2. **Dedup with merge** — "When duplicates exist, merge their fields." Use `Map.set` with `{...existing, ...incoming}`. Common in event-source replay.

3. **Dedup streaming / cardinality estimation** — "The array is too big to fit in memory." Pivot to HyperLogLog or Count-Min Sketch — sublinear space, approximate counts. Senior follow-up.

4. **Dedup with a custom equality function** — "Two items are equal if their lowercased names match." General-purpose: O(n²) with the predicate, OR O(n) by deriving a canonical key.

## Revision notes

> **array dedup — 60 second recap**
> - Primitives: `[...new Set(arr)]`. O(n). NaN-safe.
> - Objects by key: `[...new Map(arr.map(o => [keyFn(o), o])).values()]` — **last-wins**.
> - First-wins: explicit loop with `seen.has(k)`.
> - `Set` uses SameValueZero — `NaN === NaN` here (unlike `===`).
> - `filter + indexOf` is O(n²) AND fails on NaN. Never ship it.
> - **Trap:** `new Map(entries)` keeps the last value on duplicate keys.
> - **Family:** dedup, intersection, union, difference — all Set-based, O(n+m).
