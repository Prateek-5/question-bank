# First non-repeating character in a string

## Source
- LeetCode #387 "First Unique Character in a String": https://leetcode.com/problems/first-unique-character-in-a-string/
- Cracking the Coding Interview Ch. 1 (Strings), Frontend Masters JS Hard Parts, GeeksforGeeks classic.

## Why this question matters in interviews
This is the **two-pass-with-a-counter-Map** archetype — interviewers love it because it tests three things at once: (1) do you reach for a hash map immediately? (2) do you know `Map` preserves insertion order while plain objects historically don't (and still have key-type quirks)? (3) can you walk the string a second time without rebuilding state? It comes up in real backend work too: finding the first uncorrelated log line, the first non-duplicate request in a batch, the first unique session token. The "build counts then scan in order" idiom shows up everywhere from rate-limit detection to deduplication pipelines.

## Concepts involved

### Syntax to lock in
```js
function firstNonRepeating(s) {
  const count = new Map();
  for (const ch of s) count.set(ch, (count.get(ch) ?? 0) + 1);
  for (let i = 0; i < s.length; i++) if (count.get(s[i]) === 1) return s[i];
  return null;
}
```

### Runtime / engine behavior
- Iterating a `Map` (`for (const [k, v] of map)`) yields entries **in insertion order** — guaranteed by spec since ES2015. Plain object key order is mostly insertion order for string keys since ES2019, but integer-like keys (`"1"`, `"2"`) get sorted numerically first, which silently breaks order-sensitive code. **Map wins here.**
- `count.get(ch) ?? 0` is the idiomatic "default to 0" — uses nullish coalescing so it doesn't trip on legit `0` values (vs `||` which would).
- Two passes over `s` = **O(n) time**, where n is `s.length`. Map size is bounded by the **alphabet size** (26 for lowercase ASCII, 128 for full ASCII, ~1.1M for full Unicode), so for ASCII inputs space is effectively **O(1)**; for arbitrary Unicode it's O(k) where k is unique chars.

### Edge cases (these are the interview traps)
1. **Empty string** — return `null` (or `-1` if returning indices). Don't crash.
2. **All characters repeat** — `"aabbcc"` → no non-repeating char → return `null` / `-1`.
3. **First char is the answer** — `"abcdab"` → `'c'`. Two-pass scan handles this naturally.
4. **Unicode / emoji** — `"a😀b😀"`. `for...of` over a string iterates **code points** correctly; `s[i]` indexing iterates **code units** and splits surrogate pairs. If the interviewer mentions Unicode, switch your second pass to `[...s]` or `Array.from(s)`.
5. **Case sensitivity** — `"Aa"`: is `'A'` non-repeating or does it match `'a'`? Clarify. Default is case-sensitive.
6. **Return index vs char** — LeetCode #387 wants the **index**, GeeksforGeeks wants the **char**. Re-read the prompt.
7. **`Map` vs `Object`** — for ASCII-only input, a fixed `Array(26)` of counts is fastest (no hashing). Mention it as an optimization.
8. **`Map` vs `Set` for "seen vs duplicate" tracking** — a `Set` only tracks presence; you'd need a *second* Set for "seen twice." A `Map` of counts is cleaner.

## Brute force approach
For every character, scan the rest of the string to check for a duplicate. **O(n²) time, O(1) space.** Works on n ≤ 100; dies on n ≥ 10⁴. Mention it, then move on.

## Optimal approach
**Two-pass with a Map of counts.**
- **Pass 1:** walk the string, increment `count.get(ch)` for each char. Build the full frequency table.
- **Pass 2:** walk the string again in order; the first char with `count === 1` is the answer.

The key insight: Pass 2 walks the **string**, not the Map. We need the *original* order of characters in the input, not the order we encountered them in (which a Map would also give us, but walking the string is identical and more intuitive). **O(n) time, O(k) space** where k = alphabet size.

For ASCII you can swap the Map for `new Int32Array(128)` — same algorithm, faster constant factor.

## Solution (JavaScript)

```js
/**
 * Return the first non-repeating character in `s`, or null if none.
 * @param {string} s
 * @returns {string | null}
 */
function firstNonRepeating(s) {
  if (!s) return null;

  // Pass 1: count occurrences.
  const count = new Map();
  for (const ch of s) {
    count.set(ch, (count.get(ch) ?? 0) + 1);
  }

  // Pass 2: scan original string in order; return first char with count 1.
  for (const ch of s) {
    if (count.get(ch) === 1) return ch;
  }

  return null;
}

/**
 * Index-returning variant — matches LeetCode #387.
 * @param {string} s
 * @returns {number}
 */
function firstUniqueIndex(s) {
  const count = new Map();
  for (const ch of s) count.set(ch, (count.get(ch) ?? 0) + 1);
  for (let i = 0; i < s.length; i++) {
    if (count.get(s[i]) === 1) return i;
  }
  return -1;
}
```

## Step-by-step dry run

Input: `s = "leetcode"`

**Pass 1 — build count Map:**
| step | ch | count after          |
|------|----|----------------------|
| 1    | l  | `{l:1}`              |
| 2    | e  | `{l:1, e:1}`         |
| 3    | e  | `{l:1, e:2}`         |
| 4    | t  | `{l:1, e:2, t:1}`    |
| 5    | c  | `{l:1, e:2, t:1, c:1}` |
| 6    | o  | `+ o:1`              |
| 7    | d  | `+ d:1`              |
| 8    | e  | `e:3`                |

Final: `{l:1, e:3, t:1, c:1, o:1, d:1}`.

**Pass 2 — scan string:**
- `i=0` `'l'` → count is 1 → **return `'l'`**.

Output: `'l'`. (Index variant returns `0`.)

Input: `s = "aabb"`. Pass 1 yields `{a:2, b:2}`. Pass 2 finds no count-1 char. Output: `null` (or `-1`).

## Important takeaways

**Syntax to memorize**
- `count.set(ch, (count.get(ch) ?? 0) + 1)` — the canonical "increment-or-init" Map idiom.
- `for (const ch of s)` iterates code points (Unicode-safe); `s[i]` iterates code units (surrogate-pair-splitting).
- Two passes: first builds the Map, second walks the string in input order.

**Patterns to reuse**
- **"Build frequency Map, then scan"** generalizes to: anagram detection (compare two count Maps), majority element (count > n/2), most-frequent-element, character-replacement problems, and sliding-window frequency tracking.
- **Map preserves insertion order** is the property to cite when an interviewer asks "why not a plain object?" Plain objects sort integer-like string keys numerically, which is a silent footgun.

**Common mistakes**
- Using a `Set` to track "seen" — works for *detecting* repeats but doesn't tell you which were seen exactly once. Wrong tool.
- Single-pass attempts with "remove from Map when seen twice" — looks clever but breaks order: if `'a'` appears at indices 0 and 5, you remove it at 5, but a later char at index 2 might wrongly become "first unique." You'd need an ordered structure of currently-unique chars; over-engineered.
- Using `count.get(ch) || 0` instead of `?? 0` — fine for counts (never 0 here) but a habit-bug that bites elsewhere.
- Indexing with `s[i]` on a Unicode string — `"😀a"[0]` is half a surrogate, not `'😀'`.
- Returning the index when the prompt asks for the char (or vice versa).

**Map vs Object vs Array — when to pick which**
| Structure       | Pros                                                  | Cons                                          |
|-----------------|-------------------------------------------------------|-----------------------------------------------|
| `new Map()`     | Any key, insertion order guaranteed, `.size`, fast    | Slightly more memory than `Object.create(null)` |
| `{}` / `Object` | Familiar, fast, JSON-serializable                     | Stringified keys, prototype chain, integer-key reorder |
| `Int32Array(k)` | Fastest, zero hashing, fixed memory                   | Only works for known small alphabets (ASCII)  |

For interview answers: default to `Map`. Mention `Int32Array` as an optimization when the input is ASCII.

**Related questions**
- LeetCode #387 First Unique Character — index variant
- LeetCode #383 Ransom Note — count subtraction
- LeetCode #242 Valid Anagram — compare two frequency Maps
- LeetCode #438 Find All Anagrams in a String — sliding window of counts

## Variants

1. **Index-returning version** — LeetCode #387 wants the index. Trivial change: replace `for (const ch of s)` with `for (let i; ...)` in Pass 2 and return `i`. (Shown above.)

2. **Stream variant** — characters arrive one at a time; report the current first-non-repeating after each. Maintain a Map of counts **plus** a linked list of currently-unique chars (insert on first sight, remove on second). Head of list = current answer. O(1) per char.

3. **Case-insensitive** — lowercase the string first (`s.toLowerCase()`) or normalize each char in Pass 1. Beware Unicode-aware lowercase (`'İ'.toLowerCase()` → `'i̇'` is two code points).

4. **Most frequent / least frequent char** — same Pass 1, then iterate Map entries tracking min/max count. Demonstrates that the frequency-Map skeleton is the same for many related problems.

5. **Generalize beyond chars** — first unique element in an array of anything. Replace `string` with `array`, `for (const ch of s)` with `for (const x of arr)`. Same algorithm; Map keys can be any value type.

## Revision notes

> **first-non-repeating-char — 60 second recap**
> - **Two passes, one Map.** Pass 1: count chars. Pass 2: scan string in order, return first with count 1.
> - Idiom: `count.set(ch, (count.get(ch) ?? 0) + 1)`.
> - **O(n) time, O(k) space** (k = alphabet size; O(1) for ASCII).
> - **Map > Object** here: insertion order guaranteed, no integer-key reordering, no prototype chain.
> - **`for (const ch of s)` for Unicode safety**; `s[i]` splits surrogate pairs.
> - Single-pass Set tricks tend to break order — stick with two passes.
> - Family: anagram, majority-element, sliding-window frequency.
