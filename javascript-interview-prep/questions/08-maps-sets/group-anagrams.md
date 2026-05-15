# Group anagrams via Map keyed by sorted string

## Source
- LeetCode #49 "Group Anagrams": https://leetcode.com/problems/group-anagrams/
- Cracking the Coding Interview Ch. 11 (Sorting & Searching), Blind 75, NeetCode 150.

## Why this question matters in interviews
Group-anagrams is the textbook **"groupBy with a canonical key"** problem — interviewers use it to test whether you can (1) reach for a `Map<key, bucket>` reduce pattern instantly, (2) design a good canonical key (and articulate the tradeoff between sorted-string and char-count keys), and (3) reason about Big-O when both `n` (number of strings) and `k` (string length) matter. Backend versions of this problem are everywhere: grouping events by canonical user-agent, batching DB writes by table+columns signature, deduplicating webhook payloads by content hash. Master this and you've internalized the "reduce-into-Map" idiom that powers half of all data-shaping interview questions.

## Concepts involved

### Syntax to lock in
```js
function groupAnagrams(words) {
  const groups = new Map();
  for (const w of words) {
    const key = [...w].sort().join('');     // canonical key
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(w);
  }
  return [...groups.values()];
}
```

### Runtime / engine behavior
- `[...w].sort().join('')` is the canonical-key trick: anagrams produce identical sorted strings. `'eat'` → `'aet'`, `'tea'` → `'aet'`, `'ate'` → `'aet'` — all collide on the same Map key.
- `Array.prototype.sort` is **TimSort in V8** (since V8 7.0, ES2019 mandates stable sort) — sorting `k` chars is **O(k log k)**.
- `Map.get(key).push(...)` mutates the bucket in place — no need to `set` again. Same trick as `dict[key].append(x)` in Python.
- Spreading `groups.values()` returns the buckets in **Map insertion order** (the order each unique key was first seen). LeetCode accepts any order but real systems often need this guarantee.

### Edge cases (these are the interview traps)
1. **Empty input** — `[]` → `[]`. Don't crash.
2. **Empty string in input** — `['']` → `[['']]`. Sorted empty string is `''`, a valid Map key.
3. **Single-char strings** — `['a', 'b', 'a']` → `[['a','a'], ['b']]`. Works trivially.
4. **Unicode / case sensitivity** — `'Eat'` vs `'eat'` are not anagrams by default sort (uppercase code points < lowercase). Clarify; lowercase the key if needed.
5. **Long strings** — sorted-string key costs O(k log k) per word. For long words, switch to **char-count key** (26-tuple, O(k)) — see Variants.
6. **Non-ASCII** — `'😀a'` sort over code units splits surrogates; use `[...w]` (code-point iteration) not `w.split('')`.
7. **Mutation safety** — pushing into the bucket via `groups.get(key).push(w)` is fine, but be careful not to reassign the bucket array (`groups.set(key, [...groups.get(key), w])` is O(n²) overall — don't).
8. **`Object` vs `Map`** — both work here since keys are strings, but `Map` is preferred: cleaner API, no prototype-chain accidents (`words = ['hasOwnProperty']` would collide with a plain-object method).

## Brute force approach
For every pair `(i, j)`, check if `words[i]` and `words[j]` are anagrams (by sorting both, or by comparing character counts). Build groups via union-find or by marking visited. **O(n² · k log k) time** — fails on n ≥ 10⁴. Mention it, then pivot to the Map-based approach.

## Optimal approach
**Reduce-into-Map with a canonical key.** For each word, compute a key that is identical for all anagrams of that word, then push the word into `Map<key, string[]>` under that key. Two natural choices for the key:

- **Sorted-string key:** `[...w].sort().join('')`. Simple, one-liner. Cost: **O(k log k)** per word.
- **Char-count tuple key:** for lowercase ASCII, build a 26-element count array, then stringify it (e.g. `'1#0#2#...'`). Cost: **O(k)** per word — wins when k is large.

Total cost with sorted-string key: **O(n · k log k)**. With char-count key: **O(n · k)**. Space: **O(n · k)** for the output. Both are acceptable; sorted-string wins on simplicity, char-count wins on asymptotic.

## Solution (JavaScript)

```js
/**
 * Group strings that are anagrams of each other.
 * @param {string[]} words
 * @returns {string[][]}
 */
function groupAnagrams(words) {
  const groups = new Map();

  for (const w of words) {
    const key = anagramKey(w);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(w);
  }

  return [...groups.values()];
}

/** Canonical key: sorted characters. O(k log k). */
function anagramKey(w) {
  return [...w].sort().join('');
}

/**
 * Faster key for lowercase ASCII strings.
 * Builds a 26-bucket char-count fingerprint. O(k).
 */
function anagramKeyCount(w) {
  const counts = new Array(26).fill(0);
  const aCode = 'a'.charCodeAt(0);
  for (let i = 0; i < w.length; i++) {
    counts[w.charCodeAt(i) - aCode]++;
  }
  return counts.join('#');               // '#' separator avoids '1,11' === '11,1' collisions
}
```

## Step-by-step dry run

Input: `words = ['eat', 'tea', 'tan', 'ate', 'nat', 'bat']`

| word | key (sorted) | groups after action          |
|------|--------------|------------------------------|
| eat  | `'aet'`      | `{ 'aet': ['eat'] }`         |
| tea  | `'aet'`      | `{ 'aet': ['eat','tea'] }`   |
| tan  | `'ant'`      | `+ 'ant': ['tan']`           |
| ate  | `'aet'`      | `'aet': ['eat','tea','ate']` |
| nat  | `'ant'`      | `'ant': ['tan','nat']`       |
| bat  | `'abt'`      | `+ 'abt': ['bat']`           |

Final Map (insertion order): `'aet' → ['eat','tea','ate']`, `'ant' → ['tan','nat']`, `'abt' → ['bat']`.

Output: `[['eat','tea','ate'], ['tan','nat'], ['bat']]`.

With the char-count key, `'eat'` → counts `[1,0,0,0,1,0,...,1,...]` (a=1, e=1, t=1) → key `'1#0#0#0#1#...#1#...'`. All anagrams of `'eat'` produce the identical 26-tuple, so the grouping is the same.

## Important takeaways

**Syntax to memorize**
- `[...w].sort().join('')` — sorted-string canonical key (code-point safe).
- `if (!map.has(k)) map.set(k, []); map.get(k).push(v)` — "get-or-init-then-push" idiom. Memorize this; you'll use it constantly.
- `[...map.values()]` — extract groups as array.

**Patterns to reuse**
- **GroupBy via Map** is the universal data-shaping primitive. Same skeleton groups: orders by customer, events by hour, requests by route, log lines by error code.
- **Canonical-key design** is the more interesting half: anagrams → sort, "same multiset" → frequency tuple, "same shape" → key on `Object.keys(o).sort().join(',')`, geographic clustering → key on `[Math.floor(lat * 100), Math.floor(lon * 100)]`.
- **`Map.get(key).push(...)` mutation** beats `Map.set(key, [...prev, v])` — O(1) vs O(n) per insert.

**Common mistakes**
- Using `w.split('').sort().join('')` instead of `[...w].sort().join('')`. `.split('')` splits surrogate pairs (`'😀'.split('')` returns two broken halves); `[...w]` iterates code points. For ASCII it doesn't matter; for Unicode it bites.
- Reassigning the bucket: `groups.set(key, [...(groups.get(key) ?? []), w])` — quadratic.
- Char-count key without a separator: `counts.join('')` makes `'1,11'` and `'11,1'` indistinguishable. Always use a delimiter like `'#'` (or pad counts to a fixed width).
- Using `{}` and forgetting that `'constructor'`, `'__proto__'`, etc. are inherited. `Map` sidesteps this.
- Sorting in place: `w.split('').sort()` allocates anyway; no win.

**Sorted-key vs count-key tradeoff**
| Aspect          | Sorted string         | Char-count 26-tuple    |
|-----------------|-----------------------|------------------------|
| Per-word time   | O(k log k)            | O(k)                   |
| Key length      | k                     | constant (~26 chars)   |
| Code complexity | 1 line                | 5–6 lines              |
| Unicode-safe    | Yes (`[...w]`)        | No (alphabet-bounded)  |
| Best when       | Short words, any chars| Long words, ASCII only |

State the tradeoff to the interviewer — that's the senior signal.

**Related questions**
- LeetCode #242 Valid Anagram — pair check, same canonical-key idea
- LeetCode #438 Find All Anagrams in a String — sliding window over counts
- LeetCode #383 Ransom Note — count subtraction
- "Group by shape" / "deduplicate by content hash" — same pattern, different key

## Variants

1. **Char-count key for large k** — when words can be 10⁵ chars long, sorted-string becomes the bottleneck. Switch to the 26-tuple key (or 128-tuple for ASCII). Shown above.

2. **Anagrams of a query string within a corpus** — given target `t` and array `words`, return all words that are anagrams of `t`. Compute `anagramKey(t)` once, filter words by matching key. O(n·k log k) or O(n·k).

3. **Streaming / online** — words arrive one at a time. Maintain `groups` Map across the stream; emit each word's group ID (the key) as it arrives. Constant memory per unique anagram class.

4. **Group by frequency multiset (numbers, not chars)** — `[[1,2,2], [2,1,2], [3]]` → group `[1,2,2]` with `[2,1,2]`. Key = sorted JSON or sorted tuple.

5. **Anagram-key for unicode** — for arbitrary unicode, use `[...w].sort().join(' ')` — sort code points, join with a delimiter that can't appear in valid input. Char-count tuple doesn't generalize without a hash map of counts (which is the next variant).

6. **Generic-key Map<Map<char, count>, string[]>** — if you want to skip the stringification, use a serialized-canonical-form key. Adds code; rarely worth it.

## Revision notes

> **group-anagrams — 60 second recap**
> - **Reduce-into-Map with canonical key.** Key = sorted-string OR 26-tuple of counts.
> - Idiom: `if (!groups.has(key)) groups.set(key, []); groups.get(key).push(w)`.
> - **O(n·k log k)** with sorted-string key; **O(n·k)** with count-tuple key.
> - Use `[...w]` not `w.split('')` — Unicode-safe code-point iteration.
> - Count-tuple needs a **delimiter** in the key — `'#'`-join, never bare `join('')`.
> - `Map > {}` for grouping — no prototype-chain collisions.
> - Pattern generalizes: groupBy-by-canonical-form. Anagram is the test case; the skeleton is reusable.
