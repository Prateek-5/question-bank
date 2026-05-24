# Maximum Number of Words Found in Sentences — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Number_of_Words_Found_in_Sentences.md`](../Maximum_Number_of_Words_Found_in_Sentences.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/maximum-number-of-words-found-in-sentences/

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~8 minutes. The problem itself is trivial — but it teaches one genuinely useful idea: **the "delimiters + 1 = tokens" structural invariant**. This idiom skips the cost of allocating arrays of substrings when you only need a count. Once you see it, you'll use it for CSV parsing, log line counting, URL path components, and more.

**Map of this file (8 short sections):**

1. Read the problem
2. The obvious approach (split & count)
3. Why "split" is wasteful when you only want the count
4. The structural invariant — count delimiters instead
5. Code
6. Trace it
7. Common pitfalls
8. The shape — where "delimiters + 1" applies later

---

## 1. Read the problem

You're given an array `sentences`. Each element is a string holding one **sentence** — meaning **one or more words separated by single spaces**, with **no leading or trailing whitespace**. Find and return the maximum number of words across all the sentences.

Example:

```
sentences = [
    "alice and bob love leetcode",     # 5 words
    "i think so too",                   # 4 words
    "this is great thanks very much"    # 6 words
]
```

Return **6**.

> **Mini-refresher: what counts as a "word" here?**
>
> The problem guarantees a clean format:
> - Words are non-empty.
> - Single space between consecutive words (never two in a row, never tabs).
> - No space before the first word or after the last word.
>
> So `"hello world"` has 2 words. `"a"` has 1 word. `"a b c d e"` has 5 words. The structure is rigid, which we'll exploit in section 4.

---

## 2. The obvious approach (split & count)

The most natural code:

```
best = 0
for s in sentences:
    words = s.split(" ")           # break into an array on spaces
    best = max(best, len(words))
return best
```

Trace on the example:

- `"alice and bob love leetcode".split(" ")` → `["alice", "and", "bob", "love", "leetcode"]`, length 5.
- `"i think so too".split(" ")` → length 4.
- `"this is great thanks very much".split(" ")` → length 6.

Max = 6. ✓ Correct.

This works. It's O(L) per sentence (where L is the sentence length) and clear to read. **Why look for anything better?**

---

## 3. Why "split" is wasteful when you only want the count

Look at what `split` actually does. It walks the string character by character, and every time it hits a space, it:

1. Marks the end of the current word.
2. **Allocates a new substring** for the word.
3. Stores it in a result array.

That allocation step is meaningful work. For a 100-character sentence with 20 words, you're allocating 20 substrings — each one a memory allocation, a copy of the bytes, and an entry in the array.

**And we throw all of that away.** We never use the words themselves; we only use the count.

For this problem the data is small (`sentences.length ≤ 100`, each sentence ≤ 100 chars), so the waste is tolerable. But the **idiom of "count the structure, don't extract it"** is genuinely useful when sentences get large, when you're in a hot loop, or in a language with expensive string allocation (C++).

So: is there a way to know the word count **without** allocating the words?

---

## 4. The structural invariant — count delimiters instead

Here's the key observation. Look at how single-space-separated tokens line up with their delimiters:

```
"alice and bob love leetcode"
       ^   ^   ^    ^
       │   │   │    │
       └───┴───┴────┴── 4 spaces
       
  alice  and  bob  love  leetcode  ←  5 words
       
                4 spaces and 5 words.
```

Let me try another:

```
"a"            →  0 spaces, 1 word.
"a b"          →  1 space,  2 words.
"a b c"        →  2 spaces, 3 words.
"a b c d e"    →  4 spaces, 5 words.
```

The pattern is unmistakable:

> **`number of words = number of spaces + 1`**

Why? Because in a sentence with `k` words and the spec's guarantees, the spaces sit between words — one between each pair of consecutive words. Between `k` words there are `k - 1` "gaps," and each gap holds exactly one space. So `spaces = words - 1`, which rearranges to `words = spaces + 1`.

The reason this works ONLY because of the spec's promises:
- Single spaces (not doubles) → no extra delimiters.
- No leading/trailing space → no phantom delimiter at the edges.

If either of those broke, the formula would need adjustment. But for this problem, the guarantees hold.

**So our algorithm becomes:** count the spaces in each sentence, add 1, track the max. No allocations.

```
best = 0
for s in sentences:
    spaces = count of ' ' in s
    best = max(best, spaces + 1)
return best
```

---

## 5. Code

C++:

```cpp
int mostWordsFound(vector<string>& sentences) {
    int best = 0;
    for (const string& s : sentences) {
        int spaces = 0;
        for (char c : s) {
            if (c == ' ') spaces++;
        }
        best = max(best, spaces + 1);
    }
    return best;
}
```

Or using the STL one-liner:

```cpp
int mostWordsFound(vector<string>& sentences) {
    int best = 0;
    for (const string& s : sentences) {
        int spaces = count(s.begin(), s.end(), ' ');
        best = max(best, spaces + 1);
    }
    return best;
}
```

Python:

```python
def mostWordsFound(sentences):
    return max(s.count(" ") + 1 for s in sentences)
```

JavaScript:

```javascript
function mostWordsFound(sentences) {
    return Math.max(...sentences.map(s => (s.match(/ /g) || []).length + 1));
}
```

All are O(total characters), O(1) extra space (no per-sentence allocations).

---

## 6. Trace it

`sentences = ["please wait", "continue to fight", "continue to win"]`.

Walking the C++ code:

```
best = 0

s = "please wait":
    spaces = 0
    p → no
    l → no
    e → no
    a → no
    s → no
    e → no
    ' ' → YES, spaces = 1
    w → no
    a → no
    i → no
    t → no
    spaces + 1 = 2.   best = max(0, 2) = 2.

s = "continue to fight":
    spaces = 0
    after walking: 'continue' (8 chars) → space → 'to' (2 chars) → space → 'fight' (5 chars)
    Total spaces = 2.
    spaces + 1 = 3.   best = max(2, 3) = 3.

s = "continue to win":
    similar — 2 spaces.
    spaces + 1 = 3.   best = max(3, 3) = 3.

Return 3.  ✓
```

---

## 7. Common pitfalls

1. **Counting words by trying to manually parse them.** Some candidates write a state machine ("am I inside a word right now? did the character just change from letter to space?"). For this problem, that's needlessly complex. The structure is rigid; count spaces.

2. **Using `split` and then complaining about performance.** It's fine for this problem size, but if the interviewer pushes "can you avoid the allocation?" — that's where the count-delimiters idiom earns its keep.

3. **Forgetting the `+ 1`.** Counting spaces alone gives one less than the answer. Test on a single-word sentence (`"hello"`): 0 spaces → 1 word, not 0.

4. **Edge case — empty sentences array.** The problem guarantees `sentences.length ≥ 1`, so this shouldn't happen, but if your initial `best = 0` and there's a sentence with 0 words, you'd return 0 incorrectly. (The spec says each sentence has ≥ 1 word, so this is also impossible. Read the spec.)

5. **Applying the `delimiters + 1` formula when the data doesn't match the spec.** If sentences could have multiple spaces, leading/trailing spaces, or be empty, you'd need a different approach (count "transitions from space to non-space," for example).

---

## 8. The shape — where "delimiters + 1" applies later

The pattern is bigger than this problem. Anywhere data is **rigidly delimited**, you can count the delimiter instead of tokenizing:

| Situation | Delimiter | Formula |
|---|---|---|
| **This problem** (words in sentence) | space | `spaces + 1 = words` |
| CSV row | comma | `commas + 1 = fields` |
| File path components | `/` | `(slashes + 1) - (leading slash ? 1 : 0)` |
| Lines in a text file | `\n` | `newlines + (file ends with content ? 1 : 0)` |
| Function args in `(a, b, c)` | comma | `commas + 1 = arg count` (if at least one arg) |
| URL query parameters `a=1&b=2&c=3` | `&` | `ampersands + 1 = param count` |

The technique works **only when delimiters are guaranteed single, with no leading or trailing ones, and the content between delimiters is non-empty.** When those assumptions break, you typically need a slightly more careful "transition counter" (count moments when you go from delimiter to non-delimiter), but the spirit is the same: don't tokenize when you only need the count.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem that asks for **"how many `X` are in this delimited string?"**, before reaching for `split()`, ask:
>
> > **"Is the delimiter structure rigid? Can I just count the delimiters and adjust by a constant?"**
>
> If yes, you've avoided O(n) allocations for tokens you don't need.

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Number_of_Words_Found_in_Sentences.md`](../Maximum_Number_of_Words_Found_in_Sentences.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`Fizz_Buzz.md`](./Fizz_Buzz.md) (other trivial warm-up with a hidden idiom)
