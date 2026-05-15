# Array intersection / union / difference

## Source
- Canonical interview problem at every level (BFE.dev #76, LeetCode #349/#350, GreatFrontEnd).
- Lodash refs: https://lodash.com/docs/4.17.15#intersection, #union, #difference
- ES2025 native Set methods spec: https://tc39.es/proposal-set-methods/

## Why this question matters in interviews
"Find the intersection of two arrays" is the SQL JOIN of JavaScript questions — comes up everywhere from data pipelines to permission systems to feature-flag computation. The bait answer is `arr1.filter(x => arr2.includes(x))`. The interviewer wants to hear: **"Wait, that's O(n × m). Let me convert one to a Set first — O(n + m)."** This is the signature "do you actually think about complexity?" question. Bonus signal: knowing about the ES2025 native `Set.prototype.intersection` / `union` / `difference` / `symmetricDifference` and when polyfills are still needed.

## Concepts involved

### Syntax to lock in
```js
intersection([1, 2, 3], [2, 3, 4]);      // [2, 3]
union([1, 2, 3], [2, 3, 4]);              // [1, 2, 3, 4]
difference([1, 2, 3], [2, 3, 4]);         // [1]   — in a, not in b
symmetricDifference([1, 2, 3], [2, 3, 4]); // [1, 4]   — XOR
```

### Runtime / engine behavior
- The two-array set ops are O(n + m) with one Set lookup pass.
- N-way generalizations exist (intersection of K arrays is O(total length) using a counting Map).
- `Set` uses SameValueZero — `NaN === NaN` in this world.
- Lodash preserves the order of the FIRST input array. Mimic that for "least surprise."
- Sets are hash-table-backed in V8; `has` is O(1) amortized.
- ES2025 added native `Set.prototype.intersection(other)`, `.union(other)`, `.difference(other)`, `.symmetricDifference(other)`, `.isSubsetOf(other)`, `.isSupersetOf(other)`, `.isDisjointFrom(other)`. Node 22+ has them.

### Edge cases (the interview traps)
1. **Duplicates in input** — `intersection([1, 1, 2], [1, 2])`. Should `1` appear once or twice? Lodash dedups → `[1, 2]`. SQL `INTERSECT ALL` keeps multiplicity. Pick one and state the choice.
2. **Order preservation** — lodash preserves first-input order. Pure `Set` ops do not necessarily preserve original order. State which you do.
3. **NaN handling** — `Set` says NaN equals NaN; `[].includes(NaN)` works; `[].indexOf(NaN)` does not. Stick with Set-based to be safe.
4. **N-way intersection** — for K arrays, the elegant approach is a counting Map: count occurrences across DEDUPED inputs; elements with count === K are in the intersection. O(total).
5. **Reference equality on objects** — `intersection([{a:1}], [{a:1}])` is `[]`. Two distinct objects. To match by key, accept a `keyFn`.
6. **Symmetric difference vs difference** — `difference(a, b)` is "in a, not in b" (asymmetric). Symmetric difference is the XOR: "in a or b but not both."
7. **Native ES2025** — `new Set(a).intersection(new Set(b))` returns a Set, not an array. Need to spread back.

### Complexity table
| Op | Naive (filter+includes) | Set-based |
|---|---|---|
| Intersection | O(n × m) | O(n + m) |
| Union | O(n × m) | O(n + m) |
| Difference | O(n × m) | O(n + m) |
| Sym. diff | O(n × m) | O(n + m) |
| N-way intersection | O(n × m × k) | O(total) with counting Map |

## Brute force approach
```js
const intersection = (a, b) => a.filter(x => b.includes(x));
```
O(n × m). For 1000-element arrays that's a million ops. For 10k arrays it's 100 million — visibly slow. Mention it as a baseline, immediately upgrade.

## Optimal approach
Convert the **other** array to a Set, filter the first array against `set.has(x)`. O(n + m). For dedup of the result, wrap in `[...new Set(...)]` or filter while tracking a `seen` Set.

For N-way intersection: dedup each input into a Set, count membership across all sets via a Map. Elements with count K are in the intersection. O(total).

## Solution (JavaScript)

```js
/**
 * Intersection — elements present in BOTH arrays.
 * Preserves first-array order. Dedups output.
 */
function intersection(a, b) {
  const bSet = new Set(b);
  const seen = new Set();
  const result = [];
  for (const x of a) {
    if (bSet.has(x) && !seen.has(x)) {
      seen.add(x);
      result.push(x);
    }
  }
  return result;
}

/**
 * Union — elements in either array (deduped).
 */
function union(a, b) {
  return [...new Set([...a, ...b])];
}

/**
 * Difference — elements in `a` that are NOT in `b`. Asymmetric.
 */
function difference(a, b) {
  const bSet = new Set(b);
  const seen = new Set();
  const result = [];
  for (const x of a) {
    if (!bSet.has(x) && !seen.has(x)) {
      seen.add(x);
      result.push(x);
    }
  }
  return result;
}

/**
 * Symmetric difference — elements in EXACTLY ONE of the arrays (XOR).
 */
function symmetricDifference(a, b) {
  const aSet = new Set(a);
  const bSet = new Set(b);
  return [
    ...[...aSet].filter(x => !bSet.has(x)),
    ...[...bSet].filter(x => !aSet.has(x)),
  ];
}

/**
 * N-way intersection — counting-Map approach.
 * O(total elements across all arrays).
 */
function intersectionN(...arrays) {
  if (arrays.length === 0) return [];
  if (arrays.length === 1) return [...new Set(arrays[0])];

  const counts = new Map();
  for (const arr of arrays) {
    for (const x of new Set(arr)) {   // dedup each input
      counts.set(x, (counts.get(x) ?? 0) + 1);
    }
  }
  const k = arrays.length;
  return [...counts.entries()]
    .filter(([_, c]) => c === k)
    .map(([x]) => x);
}

/**
 * Key-based intersection — for objects.
 */
function intersectionBy(a, b, keyFn) {
  const bKeys = new Set(b.map(keyFn));
  const seenKeys = new Set();
  const result = [];
  for (const item of a) {
    const k = keyFn(item);
    if (bKeys.has(k) && !seenKeys.has(k)) {
      seenKeys.add(k);
      result.push(item);
    }
  }
  return result;
}

// ES2025 native (Node 22+) — for comparison
// new Set([1,2,3]).intersection(new Set([2,3,4]));   // Set{2,3}
// new Set([1,2]).union(new Set([2,3]));               // Set{1,2,3}
// new Set([1,2,3]).difference(new Set([2]));          // Set{1,3}
// new Set([1,2]).symmetricDifference(new Set([2,3])); // Set{1,3}
```

## Step-by-step dry run

Input — intersection of two user-permission lists:
```js
const aliceRoles = ['admin', 'editor', 'viewer', 'editor'];
const bobRoles   = ['editor', 'viewer'];
intersection(aliceRoles, bobRoles);
```

Trace:
- `bSet = Set{'editor', 'viewer'}` (dedups bob's list automatically).
- `seen = Set{}`. `result = []`.
- `x = 'admin'`: bSet doesn't have it. Skip.
- `x = 'editor'`: bSet has it, seen doesn't → push. `seen={editor}`, `result=['editor']`.
- `x = 'viewer'`: bSet has it, seen doesn't → push. `seen={editor,viewer}`, `result=['editor','viewer']`.
- `x = 'editor'`: bSet has it, but seen does too → skip (dedup).
- Final: `['editor', 'viewer']`.

N-way trace:
```js
intersectionN([1, 2, 3], [2, 3, 4], [3, 4, 5]);
// counts after processing dedup'd sets:
//   from [1,2,3]: {1:1, 2:1, 3:1}
//   from [2,3,4]: {1:1, 2:2, 3:2, 4:1}
//   from [3,4,5]: {1:1, 2:2, 3:3, 4:2, 5:1}
// k = 3 → filter count === 3 → 3
// → [3]
```

## Important takeaways

**Syntax to memorize**
- `new Set(b)` for fast `has` lookup. O(1) per check.
- `a.filter(x => bSet.has(x))` is the canonical intersection skeleton.
- `[...new Set([...a, ...b])]` for union (one-liner).
- For dedup-preserving order, track a `seen` Set alongside.

**Patterns to reuse**
- **Counting Map for N-way ops** — same pattern used in "find element appearing in all K lists," "majority vote," and database `GROUP BY ... HAVING COUNT(DISTINCT ...)`.
- **Set as a lookup index** — convert "do I contain X?" from O(n) to O(1). Universal speedup.
- **`keyFn` parameter** — letting callers control equality is the standard pattern for object inputs (also used in lodash, lo-dash style libs).

**Common mistakes**
- `arr1.filter(x => arr2.includes(x))` — O(n × m). Junior tell.
- Forgetting to dedup the result — `intersection([1,1,2],[1,2])` returning `[1,1,2]`. Mention the policy choice.
- Forgetting that `Set` uses reference equality on objects — `intersection([{id:1}], [{id:1}])` is `[]`.
- `union` not deduping — that's actually `concat`. Make the difference explicit.
- Confusing `difference` (asymmetric) with `symmetricDifference` (XOR).

**Related questions**
- `array-dedup` — same Set-based primitive.
- `two-sum-map` — Set/Map as lookup index.
- SQL `INTERSECT` / `UNION` / `EXCEPT` semantics — direct parallels.
- N-way intersection via counting Map.

## Variants

1. **N-way intersection** — counting Map approach. O(total). The interviewer's favorite follow-up.

2. **`intersectionBy(a, b, keyFn)`** — for objects. Same as above with a derived key for `has` checks.

3. **`intersectionWith(a, b, comparator)`** — custom equality (not derivable from a key). Forced back to O(n × m). Mention as the "fallback when key-based isn't possible."

4. **Streaming / chunked diff** — "The arrays don't fit in memory. Sort each on disk, then merge-diff (like Unix `comm`)." External-memory algorithm; pivot to mergesort + linear merge.

5. **ES2025 native Set methods** — show the modern equivalent. `set.intersection(other)`, `set.union(other)`, etc. Available in Node 22+, Chrome 122+.

## Revision notes

> **array set ops — 60 second recap**
> - Intersection: `bSet = new Set(b); a.filter(x => bSet.has(x))`. O(n + m).
> - Union: `[...new Set([...a, ...b])]`.
> - Difference (asymmetric): `a.filter(x => !bSet.has(x))`.
> - Symmetric difference (XOR): two halves of difference concatenated.
> - Dedup output by tracking a `seen` Set if duplicates in input matter.
> - N-way intersection: counting Map, count === K → in result.
> - **Trap:** `a.filter(x => b.includes(x))` is O(n × m). Set the lookup table FIRST.
> - **Family:** SQL set ops, lodash `_.intersection/_.union/_.difference`, ES2025 native `Set` methods.
