# First non-repeating character

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [multiset-counter.md](./multiset-counter.md)
>
> **Source:** LeetCode #387. Cracking the Coding Interview Ch. 1.

---

## 1. Problem statement

Return the first char in string `s` that appears exactly once. `null` if none.

**Verification examples**

```js
firstNonRepeating('leetcode');          // 'l'
firstNonRepeating('loveleetcode');      // 'v'
firstNonRepeating('aabb');               // null
firstNonRepeating('');                   // null
firstNonRepeating('a😀b😀');             // 'a' (or correct Unicode handling)
```

**Constraints**
- Two passes O(n).
- First: count via Map.
- Second: scan string for count===1.
- Unicode: use `for..of` or `[...s]` for code-point iteration.

---

## 2. Plain-English restatement

Count each char's occurrences; then scan in order and return the first with count 1.

---

## 3. Why this matters in interviews

Two-pass-with-counter-Map archetype. Tests: Map literacy, insertion-order, `?? 0` idiom, Unicode awareness.

---

## 4. Mental model

```
   Two-pass O(n):
     pass 1: count = Map<char, int>
       for ch of s: count.set(ch, (count.get(ch) ?? 0) + 1)
     pass 2: scan in order
       for i in 0..s.length-1:
         if count.get(s[i]) === 1: return s[i]
       return null
   
   Single-pass via insertion order:
     Use Map<char, {count, firstIdx}> or just count.
     Iterate map in insertion order; return first with count 1.
     Same O(n) — different shape.
   
   Unicode:
     for (const ch of s) iterates CODE POINTS (handles surrogate pairs).
     s[i] indexing iterates CODE UNITS (splits surrogate pairs).
     For ASCII: same; for emoji: use for..of.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why two passes?
> 2. `s[i]` vs `for..of` for Unicode?
> 3. Empty string return?

---

## 6. Brute force — walked through

```js
function brute(s) {
  for (let i = 0; i < s.length; i++) {
    let dup = false;
    for (let j = 0; j < s.length; j++) {
      if (i !== j && s[i] === s[j]) { dup = true; break; }
    }
    if (!dup) return s[i];
  }
  return null;
}
```

O(n²). Dies on n > 10⁴.

---

## 7. The unlocking insight

> **Count first (Map), then scan in order. Use `for..of` for Unicode. `?? 0` for default count.**

Three properties:

1. **Two-pass** — count then scan.
2. **`?? 0` idiom** — clean increment.
3. **`for..of`** for Unicode safety.

---

## 8. Solution (annotated)

```js
function firstNonRepeating(s) {
  const count = new Map();
  for (const ch of s) {                                                    // step 1: count (code-point safe)
    count.set(ch, (count.get(ch) ?? 0) + 1);
  }
  for (const ch of s) {                                                    // step 2: scan in order
    if (count.get(ch) === 1) return ch;
  }
  return null;                                                              // step 3: none found
}

// Single-pass via insertion order
function firstNonRepeatingSinglePass(s) {
  const count = new Map();
  for (const ch of s) count.set(ch, (count.get(ch) ?? 0) + 1);
  for (const [ch, c] of count) if (c === 1) return ch;                     // step 4: Map insertion order
  return null;
}

// LeetCode #387 wants the INDEX
function firstUniqueIndex(s) {
  const count = new Map();
  for (const ch of s) count.set(ch, (count.get(ch) ?? 0) + 1);
  for (let i = 0; i < s.length; i++) {
    if (count.get(s[i]) === 1) return i;
  }
  return -1;
}

// ASCII-only fastest: fixed array
function firstNonRepeatingAscii(s) {
  const count = new Array(128).fill(0);
  for (let i = 0; i < s.length; i++) count[s.charCodeAt(i)]++;
  for (let i = 0; i < s.length; i++) {
    if (count[s.charCodeAt(i)] === 1) return s[i];
  }
  return null;
}
```

**Try it yourself**

```js
firstNonRepeating('leetcode');                                // 'l'
firstNonRepeating('loveleetcode');                            // 'v'
firstNonRepeating('aabb');                                    // null
firstNonRepeating('');                                         // null

// Unicode test
firstNonRepeating('a😀b😀');                                  // 'a'  (😀 is surrogate pair)
firstNonRepeating('a😀b😀c');                                 // 'a'

// Wrong with s[i] indexing — splits emoji
function wrong(s) {
  const count = new Map();
  for (let i = 0; i < s.length; i++) {                         // iterates UTF-16 units
    count.set(s[i], (count.get(s[i]) ?? 0) + 1);
    // For '😀': s[0]='\uD83D' (high surrogate), s[1]='\uDE00' (low).
    // Both counted separately. Often wrong.
  }
  // ...
}

// Real-time stream: maintain insertion order + remove on duplicate
class StreamUnique {
  constructor() { this.q = new Map(); this.dup = new Set(); }
  add(ch) {
    if (this.dup.has(ch)) return;
    if (this.q.has(ch)) { this.q.delete(ch); this.dup.add(ch); }
    else this.q.set(ch, true);
  }
  first() { return this.q.keys().next().value ?? null; }
}
```

---

## 9. Step-by-step dry run

```
firstNonRepeating('loveleetcode'):
  Pass 1 (count):
    l:2, o:1, v:1, e:4, t:1, c:1, d:1.
  
  Pass 2 (scan):
    'l' count 2 → skip.
    'o' count 1 → return 'o'.
    
  Wait — return is 'v' on LeetCode. Let me re-check.
  
  Actually: l-o-v-e-l-e-e-t-c-o-d-e
            1 1 1 1 1 1 1 1 1 1 1 1
  Count: l=2, o=2, v=1, e=4, t=1, c=1, d=1.
  Scan: l(2)skip, o(2)skip, v(1) → return 'v'. ✓

firstNonRepeating('aabb'):
  count: a=2, b=2.
  scan: a skip, a skip, b skip, b skip.
  return null.

Unicode 'a😀b😀':
  for..of yields: 'a', '😀', 'b', '😀'.
  count: a=1, 😀=2, b=1.
  scan: 'a' count 1 → return 'a'. ✓
  
  Wrong with s[i]:
  s.length = 6 (4 code points but '😀' = 2 units).
  s[0]='a', s[1]='\uD83D', s[2]='\uDE00', s[3]='b', s[4]='\uD83D', s[5]='\uDE00'.
  count: a=1, '\uD83D'=2, '\uDE00'=2, b=1.
  scan: 'a' count 1 → return 'a'. (Accidentally correct here.)
  
  But: '😀' alone — wrong returns the surrogate string, not the emoji.
```

---

## 10. Common confusion + traps

1. **`s[i]` indexing for Unicode** — splits surrogate pairs.
2. **`|| 0`** — treats legit 0 as missing.
3. **Object instead of Map** — numeric coercion (`obj['1']`).
4. **Index vs char** — different problem variants.
5. **Return value vs index** — re-read prompt.
6. **All chars repeat** — return null/-1.
7. **Single-pass with `count`-Map insertion order** is valid.

---

## 11. Senior follow-ups & variants

### Variant 1 — Return index
LeetCode #387.

### Variant 2 — Online / streaming
Maintain a queue + duplicates set.

### Variant 3 — Case-insensitive
Lowercase first.

### Variant 4 — First repeating
Inverse — first char that appears twice.

### Variant 5 — N-th unique
Generalize beyond first.

---

## 12. How to think aloud

> "Two-pass with a counter Map: pass 1 counts each char via `count.set(ch, (count.get(ch) ?? 0) + 1)`; pass 2 scans the string in order, returns the first char with count exactly 1. O(n) time, O(k) space where k = distinct chars. Use `?? 0` not `|| 0` — `||` treats legit 0 as missing (matters here less, but use ?? for habit). Map preserves insertion order, so a single-pass variant works: count first, then iterate Map entries in insertion order, return first with count 1 — equivalent O(n). Unicode: use `for..of` or `[...s]` which iterate code points; `s[i]` indexes code units and splits surrogate pairs (`'😀'` is two code units). LeetCode #387 wants index; some variants want char — re-read prompt. ASCII-only fastest: fixed `Array(128)` indexed by `charCodeAt`. Real-time streaming variant: maintain Map of candidates + Set of duplicates; first() returns first key of Map. Trap: `s[i]` Unicode; `|| 0`; Object instead of Map (numeric coercion); confusing index vs char return."

---

## 13. 60-second revision

> - **Two passes:** count, then scan.
> - **`(count.get(ch) ?? 0) + 1`** idiom.
> - **`for..of`** for Unicode (code points).
> - **`s[i]`** splits surrogate pairs.
> - **Map insertion order** — single-pass variant.
> - **LeetCode #387 wants index.**
> - **ASCII fast path:** `Array(128) + charCodeAt`.
> - **Streaming:** Map + Set of dups.
> - **Trap:** Unicode indexing; `|| 0`; Object key coercion.

---

**Related:** [multiset-counter.md](./multiset-counter.md) · [group-anagrams.md](./group-anagrams.md) · [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [two-sum-map.md](./two-sum-map.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
