# Group anagrams via Map with canonical key

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [group-by.md](./group-by.md), [multiset-counter.md](./multiset-counter.md)
>
> **Source:** LeetCode #49. Cracking the Coding Interview Ch. 11. Blind 75.

---

## 1. Problem statement

Group words that are anagrams of each other. Each group is an array.

**Verification examples**

```js
groupAnagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat']);
// [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]

groupAnagrams([]);                       // []
groupAnagrams(['']);                     // [['']]
```

**Constraints**
- Canonical key per word (anagrams collide).
- Map<key, bucket> + push.
- Sorted-key: O(k log k) per word.
- Char-count key: O(k) per word.

---

## 2. Plain-English restatement

For each word, derive a canonical key shared by all its anagrams. Bucket via Map. Output values.

---

## 3. Why this matters in interviews

Textbook "groupBy with canonical key." Tests: Map<key, bucket>, key choice, Big-O over both `n` (words) and `k` (length).

---

## 4. Mental model

```
   Sorted-key:
     key(w) = [...w].sort().join('')
     'eat' → 'aet', 'tea' → 'aet', 'ate' → 'aet'.
     O(k log k) per word.
   
   Char-count key (faster for long words):
     count[26] = zeros
     for ch of w: count[ch.codeAt - 97]++
     key = count.join(',')      ← '1,0,0,...,1,0,1' etc.
     O(k) per word.
   
   Total:
     n words, avg k chars.
     Sorted: O(n × k log k).
     Counts: O(n × k).
   
   Group container:
     Map<key, string[]>.
     (groups.get(key) ?? push pattern.)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Sorted-key vs char-count tradeoff?
> 2. Unicode handling?
> 3. Empty string in input?

---

## 6. Brute force — walked through

```js
// Pairwise comparison
function brute(words) {
  const groups = [];
  for (const w of words) {
    let placed = false;
    for (const g of groups) {
      if (isAnagram(g[0], w)) { g.push(w); placed = true; break; }
    }
    if (!placed) groups.push([w]);
  }
  return groups;
}
```

O(n² × k) for pairwise comparison.

---

## 7. The unlocking insight

> **Canonical key (sorted chars or char counts). Map<key, bucket>; push into bucket. Single pass.**

Three properties:

1. **Canonical key** — anagrams collide.
2. **Map<key, bucket>** init + push.
3. **Sorted vs counts** by `k` size.

---

## 8. Solution (annotated)

```js
function groupAnagrams(words) {
  const groups = new Map();
  for (const w of words) {
    const key = [...w].sort().join('');                                    // step 1: canonical key
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(w);                                                // step 2: mutate bucket
  }
  return [...groups.values()];                                              // step 3: insertion order
}

// Char-count key for long strings (lowercase a-z)
function groupAnagramsCount(words) {
  const groups = new Map();
  for (const w of words) {
    const count = new Array(26).fill(0);
    for (let i = 0; i < w.length; i++) {
      count[w.charCodeAt(i) - 97]++;
    }
    const key = count.join(',');                                            // step 4: O(k) key
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(w);
  }
  return [...groups.values()];
}

// Generic groupBy abstraction
function groupBy(items, keyFn) {
  const groups = new Map();
  for (const x of items) {
    const k = keyFn(x);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(x);
  }
  return [...groups.values()];
}
const groupAnagramsGeneric = (words) =>
  groupBy(words, w => [...w].sort().join(''));
```

**Try it yourself**

```js
groupAnagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat']);
// [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]

groupAnagrams(['']);                                          // [['']]
groupAnagrams([]);                                            // []
groupAnagrams(['abc']);                                       // [['abc']]

// Case-insensitive
function groupAnagramsCI(words) {
  return groupBy(words, w => [...w.toLowerCase()].sort().join(''));
}

// Unicode-safe key
function groupAnagramsUnicode(words) {
  return groupBy(words, w => [...w].sort().join(''));
}

// Anagram check via Counter
function isAnagram(a, b) {
  if (a.length !== b.length) return false;
  const c = new Map();
  for (const ch of a) c.set(ch, (c.get(ch) ?? 0) + 1);
  for (const ch of b) {
    if (!c.has(ch)) return false;
    c.set(ch, c.get(ch) - 1);
    if (c.get(ch) === 0) c.delete(ch);
  }
  return c.size === 0;
}
```

---

## 9. Step-by-step dry run

```
groupAnagrams(['eat', 'tea', 'tan', 'ate']):
  groups = {}.
  
  'eat': key = 'aet'. !has → []. push 'eat'. groups: {'aet': ['eat']}.
  'tea': key = 'aet'. has → push. groups: {'aet': ['eat', 'tea']}.
  'tan': key = 'ant'. !has → push. groups: {'aet': [...], 'ant': ['tan']}.
  'ate': key = 'aet'. has → push. groups: {'aet': ['eat', 'tea', 'ate'], 'ant': ['tan']}.
  
  Return [...values] = [['eat','tea','ate'], ['tan']].

Char-count key for 'eat':
  count = [0]*26. 
  e (4): count[4]++.
  a (0): count[0]++.
  t (19): count[19]++.
  key = '1,0,0,0,1,0,0,...,1,0,0,0,0,0,0' (with 1s at 0, 4, 19).

Sorted vs count tradeoff:
  k=10: sort ≈ 33 ops vs count ≈ 10 ops. Count wins.
  k=3: sort ≈ 5 ops vs count ≈ 30 ops (incl. key.join). Sort wins.
  Crossover around k=20-50.
```

---

## 10. Common confusion + traps

1. **Object as map** — `'__proto__'` or 'constructor' as input → bug.
2. **`split('')` on Unicode** — splits surrogate pairs.
3. **Mutate bucket via `set(key, [...old, w])`** — O(n) per insert; quadratic overall.
4. **Sorted key for long strings** — char-count faster.
5. **Case sensitivity** — clarify.
6. **Empty string** — valid; key is `''`.
7. **Char-count assumes a-z** — broaden alphabet if needed.

---

## 11. Senior follow-ups & variants

### Variant 1 — Char-count key (O(k))
For long strings.

### Variant 2 — Unicode key
`[...w].sort().join('')`.

### Variant 3 — Case-insensitive
`.toLowerCase()` first.

### Variant 4 — Group by signature (sorted char counts)
Same idea different domain (e.g., DB column signature).

### Variant 5 — Streaming
Group anagrams from a stream; emit groups as full.

---

## 12. How to think aloud

> "Group anagrams: pick a canonical key shared by all anagrams of the same word; bucket via Map<key, bucket>. Two key strategies: (1) sorted-string `[...w].sort().join('')` — O(k log k) per word; clean to read; OK for short words. (2) char-count tuple `count[26]` of letter frequencies, joined into a string — O(k) per word; faster for long words; assumes alphabet (lowercase a-z by default). Crossover ~k=20-50. Total: O(n × k log k) or O(n × k). Use Map (not Object) to avoid `'__proto__'`/'constructor' collisions if input contains those words. Mutate bucket via `groups.get(key).push(w)` — NOT `set(key, [...old, w])` which is O(n) per insert (quadratic overall). Unicode: `[...w]` for code-point iteration; `w.split('')` splits surrogates. Variants: case-insensitive (toLowerCase first); Unicode-safe key with separator. Trap: Object map collisions; surrogate splitting; quadratic 'set(key, [...spread, x])' anti-pattern."

---

## 13. 60-second revision

> - **Canonical key:** sorted string or char counts.
> - **Map<key, bucket>**, mutate via `push`.
> - **Sorted:** O(k log k); counts: O(k).
> - **Crossover ~k=20-50.**
> - **`[...w]`** for Unicode (code points).
> - **`groups.get(key).push(w)`** — NOT spread.
> - **Map over Object** — avoids name collisions.
> - **Case-insensitive variant** — toLowerCase first.
> - **Trap:** Object map; surrogates; spread-set.

---

**Related:** [group-by.md](./group-by.md) · [multiset-counter.md](./multiset-counter.md) · [first-non-repeating-char.md](./first-non-repeating-char.md) · [composite-key-strategies.md](./composite-key-strategies.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
