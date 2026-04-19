# Maximum Number of Words Found in Sentences

**Problem Link:**
https://leetcode.com/problems/maximum-number-of-words-found-in-sentences/

**Topic:**
Arrays and Matrices

----------------------------------------

## Step 1: The Setup

You're given an array of strings `sentences`. Each string is a **sentence** — one or more words separated by single spaces, with no leading or trailing whitespace. Return the **maximum number of words** in any one sentence.

Example: `["alice and bob love leetcode", "i think so too", "this is great thanks very much"]`.
- First: 5 words.
- Second: 4 words.
- Third: 6 words.
- Answer: **6**.

----------------------------------------

## Step 2: How to Count Words?

The obvious approach: split each sentence on spaces and count the pieces. Works, but creates throwaway arrays of strings.

Is there a cheaper way? Yes — exploit the structure the problem guarantees.

Since words are separated by **single spaces**, with no doubles, no leading/trailing spaces, the relationship between **spaces** and **words** is tight:

```
number of words = number of spaces + 1
```

A sentence with k spaces has k+1 words. "hello world" → 1 space, 2 words. "a" → 0 spaces, 1 word.

So we just **count spaces** in each string — no splitting, no allocations.

----------------------------------------

## Step 3: Algorithm

```
best = 0
for s in sentences:
    spaces = count of ' ' in s
    best = max(best, spaces + 1)
return best
```

Linear in the total length of all sentences. Can't do better — we must at least look at each character to know whether it's a space.

----------------------------------------

## Step 4: Trace

`sentences = ["please wait", "continue to fight", "continue to win"]`.

- "please wait": 1 space → 2 words.
- "continue to fight": 2 spaces → 3 words.
- "continue to win": 2 spaces → 3 words.

Best = **3**. ✓

----------------------------------------

## Step 5: Why Not Split?

`split(" ")` would also give the right answer. For each sentence of length L, it allocates an array of O(L / avg_word_length) strings. For large inputs, that's a lot of memory pressure and GC (in languages with it) or extra string objects (in C++).

Counting spaces is O(L) time and O(1) extra space per sentence — the minimal work.

For this problem size (≤100 sentences, ≤100 chars each), either approach is fine. But the space-count idiom is a useful habit for string problems.

----------------------------------------

## Step 6: Name It

This isn't really a named algorithm — it's a **structural invariant**: *delimiter count + 1 = token count*, valid when delimiters are single and no leading/trailing ones exist.

Relatives:
- Count CSV fields by counting commas.
- Count lines by counting `\n`.
- Count path components by counting `/` (with care around root/trailing slashes).

Whenever the delimiter structure is rigidly specified, counting delimiters beats tokenizing.

----------------------------------------

## Step 7: Complexity

Time: **O(total characters across all sentences)**.
Space: **O(1)** extra.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int mostWordsFound(vector<string>& sentences) {
    int best = 0;
    for (const string& s : sentences) {
        int spaces = 0;
        for (char c : s) if (c == ' ') spaces++;
        best = max(best, spaces + 1);
    }
    return best;
}
```

A single pass per sentence; no extra allocations. One could also use `count(s.begin(), s.end(), ' ')` from `<algorithm>` for conciseness.

----------------------------------------

## Step 9: Follow-up Questions

- **Multiple spaces between words.** Split on whitespace runs, or count transitions (space → non-space) — each transition begins a new word.
- **Leading/trailing spaces.** Trim first, or count transitions.
- **Unicode whitespace (tabs, non-breaking spaces).** Use a whitespace predicate, not a literal space comparison.
- **Return the longest sentence itself, not just its word count.** Track the argmax.
- **Average word count across sentences.** Sum and divide.
- **Why is `spaces + 1` valid even if a sentence is a single word (no spaces)?** Because 0 spaces → 1 word, and the formula handles it naturally.
