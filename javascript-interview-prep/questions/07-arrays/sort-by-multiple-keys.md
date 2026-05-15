# Sort an array of objects by multiple keys (asc/desc mix)

## Source
- Canonical "lodash `_.orderBy`" interview problem (BFE.dev #168, GreatFrontEnd, codedamn).
- Lodash reference: https://lodash.com/docs/4.17.15#orderBy
- MDN: [Array.prototype.sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)

## Why this question matters in interviews
Multi-key sort is the #1 array question at backend interviews after polyfills. Every dashboard, report, table view, and admin UI needs "sort by status, then by createdAt desc, then by name." Candidates who write `arr.sort((a, b) => a.name - b.name)` and call it a day get filtered out. The interviewer wants to see: (1) a clean **comparator factory** that composes multiple field comparisons, (2) awareness of the **ES2019 stable-sort guarantee**, (3) handling of **mixed asc/desc directions**, and (4) sensible **type-aware comparisons** (strings via `localeCompare`, numbers via subtract, dates via valueOf). It's the "can you build a small DSL?" question.

## Concepts involved

### Syntax to lock in
```js
const users = [
  { name: 'Alice', age: 30, role: 'admin' },
  { name: 'Bob',   age: 25, role: 'user' },
  { name: 'Alice', age: 25, role: 'user' },
];

sortBy(users, [
  { key: 'name', dir: 'asc' },
  { key: 'age',  dir: 'desc' },
]);
// → Alice/30, Alice/25, Bob/25
```

### Runtime / engine behavior
- `Array.prototype.sort` is **stable** as of ES2019 (V8, Spidermonkey, JavaScriptCore all aligned). This means: equal-keyed items preserve their original input order. Before 2019, V8 used quicksort for `n > 10` (unstable) and insertion sort below — a portability landmine.
- The comparator must return a **number**: negative (a before b), positive (b before a), zero (equal). Returning `true`/`false` is a classic bug — gets coerced to 1/0 and breaks sort order.
- `sort` mutates in place AND returns the same array. If immutability matters, `[...arr].sort(...)` or ES2023's `arr.toSorted(...)`.
- Comparator should be **total** (transitive, anti-symmetric, reflexive). Non-deterministic comparators produce engine-defined results — never randomize inside a comparator.
- Engine calls comparator O(n log n) times. Keep it cheap. Pre-compute heavy keys (`map` to sortKey arrays, sort indices, then materialize — Schwartzian transform).

### Edge cases (the interview traps)
1. **Mixed types** — `{age: 25}` vs `{age: '30'}`. Subtract coerces, but `'abc' - 1` is `NaN`. Decide policy: throw, coerce, or use type-aware compare.
2. **Nulls / undefineds** — should nulls sort first, last, or throw? Lodash sorts undefineds last. Decide and document.
3. **Strings with diacritics / casing** — `'a'.localeCompare('B')` honors locale; raw `<` doesn't. Choose intentionally.
4. **Numeric strings** — `'10' < '2'` is `true` (lexicographic). Use `localeCompare(b, undefined, {numeric: true})` for natural order.
5. **Dates** — `new Date('2024')` instances compare via `valueOf()` (returns ms), so `dateA - dateB` works. Strings like `'2024-01-01'` happen to compare correctly lexicographically — but that's coincidence, not a rule.
6. **Stability assumption** — if you target Node 10 or below, you can't rely on stability. Add an "original index" tiebreaker. Always.
7. **Deep keys** — `'address.city'` requires path parsing. Lodash does this; decide if your scope includes it.
8. **Direction param** — accept `'asc'` / `'desc'` AND `1` / `-1`. Or accept a custom `compare` fn per field.

## Brute force approach
The naive multi-key sort: sort by the **least significant** key first, then by the next, relying on stability. Works (post-ES2019) but is `O(k n log n)` and reads weird. Worse: every key requires a separate `arr.sort()` call. Memory: low. Code clarity: terrible. Doesn't extend to "sort by custom compare per field."

Drop it for the composed-comparator approach.

## Optimal approach
Build a **single comparator** that runs through the field list and returns the first non-zero result. Each field has a `key` and `dir`. Multiply the per-field result by `dir === 'desc' ? -1 : 1`. Short-circuit with `||` since `0` is falsy.

```js
const cmp = (a, b) =>
  fields.reduce((acc, { key, dir }) => {
    if (acc !== 0) return acc;
    const av = a[key], bv = b[key];
    const r = av < bv ? -1 : av > bv ? 1 : 0;
    return r * (dir === 'desc' ? -1 : 1);
  }, 0);
```

O(n log n × k) total time where k is field count. Stable by virtue of native `sort`. Easy to extend per-field with custom comparators.

## Solution (JavaScript)

```js
/**
 * Sort an array of objects by multiple keys with mixed asc/desc directions.
 *
 * @param {Array<object>} arr
 * @param {Array<{ key: string, dir?: 'asc'|'desc', compare?: (a, b) => number }>} fields
 * @returns {Array<object>}  new sorted array (does not mutate input)
 */
function sortBy(arr, fields) {
  // Schwartzian-style pre-extract not needed for shallow keys, but
  // keep the comparator pure & total.
  const compareFields = (a, b) => {
    for (const { key, dir = 'asc', compare } of fields) {
      const av = a?.[key];
      const bv = b?.[key];

      let r;
      if (compare) {
        r = compare(av, bv);
      } else if (av == null && bv == null) {
        r = 0;
      } else if (av == null) {
        r = 1;            // nulls last
      } else if (bv == null) {
        r = -1;
      } else if (typeof av === 'string' && typeof bv === 'string') {
        r = av.localeCompare(bv);
      } else {
        r = av < bv ? -1 : av > bv ? 1 : 0;
      }

      if (r !== 0) return r * (dir === 'desc' ? -1 : 1);
    }
    return 0;             // all keys equal — stable sort preserves input order
  };

  return [...arr].sort(compareFields);
}
```

## Step-by-step dry run

Input:
```js
const users = [
  { name: 'Alice', age: 30 },     // u0
  { name: 'Bob',   age: 25 },     // u1
  { name: 'Alice', age: 25 },     // u2
];

sortBy(users, [
  { key: 'name', dir: 'asc' },
  { key: 'age',  dir: 'desc' },
]);
```

Comparator calls (sample subset — V8 uses TimSort internally):

- `cmp(u0, u1)` → name: `'Alice'.localeCompare('Bob')` → `-1`. Return `-1`. (u0 before u1.)
- `cmp(u0, u2)` → name: equal (`0`). Continue to age: `30 > 25` → `1`. Multiply by `-1` (desc) → `-1`. Return `-1`. (u0 before u2.)
- `cmp(u1, u2)` → name: `'Bob'.localeCompare('Alice')` → `1`. Return `1`. (u2 before u1.)

Final order: `[u0, u2, u1]` = `[{Alice,30}, {Alice,25}, {Bob,25}]`. Correct.

## Important takeaways

**Syntax to memorize**
- Comparator returns a **number**, never a boolean.
- `dir === 'desc' ? -1 : 1` is the multiplier trick.
- Use `localeCompare` for strings, subtraction or `<`/`>` for numbers/dates.
- `[...arr].sort()` for immutability; `arr.toSorted()` in ES2023+.

**Patterns to reuse**
- **Comparator factory**: returning a comparator from a config is the same pattern as in DB ORDER BY clauses, lodash `_.orderBy`, and SQL window functions.
- **`||` short-circuit on integer zero**: `cmpA(a,b) || cmpB(a,b) || cmpC(a,b)` is the idiomatic one-liner for multi-key compare (equivalent to the reduce, smaller).
- **Schwartzian transform** for expensive keys: `arr.map(x => [keyFn(x), x]).sort(byFirst).map(([_, x]) => x)`. Computes the key once per element rather than O(n log n) times.

**Common mistakes**
- Returning boolean from comparator (`a.name > b.name`) — sort works on small arrays by accident, breaks on larger ones.
- Using `a.name - b.name` on string fields — `NaN`, undefined order.
- Forgetting null handling — `null < 5` is `true`, `null > 5` is `false`, `null == 5` is `false`. Nulls become "less than everything" silently.
- Relying on V8 stability when supporting older Node — add an original-index tiebreaker.
- Mutating `arr` instead of cloning — surprises the caller.

**Related questions**
- Stable sort discussion (what changed in ES2019).
- Sort by computed key (Schwartzian transform).
- Top-K via min-heap instead of full sort.
- SQL ORDER BY mental model alignment.

## Variants

1. **Sort by computed function** — "Allow `key` to be a function `(item) => sortValue`." Trivial extension: `const av = typeof key === 'function' ? key(a) : a[key];`. Lodash's `_.sortBy` does this.

2. **Nested key paths** — "Support `'address.city.zip'`." Adds a path-parser: `path.split('.').reduce((o, p) => o?.[p], obj)`. Tests gotcha-awareness for missing intermediates.

3. **Locale-aware sort with options** — "Group by first letter, case-insensitive, ignore diacritics." Use `localeCompare(b, locale, { sensitivity: 'base', numeric: true })`.

4. **Top-K instead of full sort** — "I only want the top 10 by score." Min-heap of size K, O(n log k). When N is huge and K is small, this destroys `sort().slice(0, k)` in benchmarks.

## Revision notes

> **sort-by-multiple-keys — 60 second recap**
> - Build one comparator that loops fields, returns first non-zero result.
> - Multiply per-field result by `dir === 'desc' ? -1 : 1`.
> - Use `localeCompare` for strings, subtract for numbers/dates.
> - Sort is stable since ES2019 — equal-keyed items preserve input order.
> - Don't mutate: `[...arr].sort()` or `arr.toSorted()`.
> - **Trap:** boolean from comparator (coerced 1/0), missing null policy, lexicographic string compare on numeric strings.
> - **Family:** lodash `_.orderBy`, SQL `ORDER BY`, Schwartzian transform.
