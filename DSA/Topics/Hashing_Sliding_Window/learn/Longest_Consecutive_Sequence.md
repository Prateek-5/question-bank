# Longest Consecutive Sequence — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Consecutive_Sequence.md`](../Longest_Consecutive_Sequence.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/longest-consecutive-sequence/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-consecutive-sequence/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. This problem teaches **a beautiful amortization trick**. The naive O(n) approach turns out to be secretly O(n²); the fix is a single "start only from streak beginnings" guard. The amortization analysis is the lesson — once you see it, you'll spot similar patterns in graph traversal, union-find, and many other "each item processed once across multiple loops" arguments.

**Map of this file (10 short sections):**

1. Read the problem
2. Why we can't just sort
3. The hashset insight — O(1) "is this number present?"
4. The naive set-based approach (and why it's secretly O(n²))
5. The fix — only start walking from STREAK BEGINNINGS
6. The amortization proof
7. Code
8. Trace it
9. Common pitfalls
10. The shape — amortized linear-time patterns

---

## 1. Read the problem

You're given an unsorted array of integers `nums`. Find the **length of the longest sequence of CONSECUTIVE INTEGERS** present in the array (consecutive in VALUE, not necessarily contiguous in the array).

You must do this in **O(n) time**.

**Example 1:** `nums = [100, 4, 200, 1, 3, 2]`. Sequences of consecutive integers present:

- `[1, 2, 3, 4]` — all four present. Length 4.
- `[100]` — by itself.
- `[200]` — by itself.

Longest: **4**.

**Example 2:** `nums = [0, 3, 7, 2, 5, 8, 4, 6, 0, 1]`. Sequences:

- `[0, 1, 2, 3, 4, 5, 6, 7, 8]` — all 9 distinct values present.

Longest: **9**. (Duplicate `0` doesn't extend the sequence.)

**Example 3:** `nums = [1, 2, 0, 1]`. Sequences:

- `[0, 1, 2]` — present.

Longest: **3**.

---

## 2. Why we can't just sort

Sorting feels natural: sort the array, then scan, tracking the current consecutive streak.

```python
sorted_nums = sorted(set(nums))
best = 0
current = 0
prev = None
for x in sorted_nums:
    if prev is None or x == prev + 1:
        current += 1
    else:
        current = 1
    best = max(best, current)
    prev = x
return best
```

Works. But sorting is **O(n log n)**. The problem **requires O(n)**.

So we need to exploit something other than sort order. The hint is in the phrase "is this number present?" — that's an **O(1) hash lookup**.

---

## 3. The hashset insight — O(1) "is this number present?"

> **Mini-refresher: hashset and O(1) lookup.**
>
> A hashset stores values without duplicates. `unordered_set<int>` in C++, `set` in Python, `Set` in JS. Key operations:
>
> - `insert(x)` — add x to the set. O(1) amortized.
> - `count(x)` (C++) / `x in s` (Python) / `s.has(x)` (JS) — check if x is in the set. O(1) amortized.
> - `size()` — number of unique elements. O(1).
>
> The "amortized O(1)" means individual operations might be slower if there's a hash collision, but on average across many operations, the cost works out to a constant per call.

So **putting all of `nums` into a hashset gives us O(1) "is value v in the set?" queries.** From there, we can build "is `x + 1` in the set?" and walk consecutive values forward.

---

## 4. The naive set-based approach (and why it's secretly O(n²))

Here's the obvious set-based attempt:

```
s = hashset of all values in nums
best = 0
for each x in s:
    current = 1
    next_val = x + 1
    while next_val in s:
        current += 1
        next_val += 1
    best = max(best, current)
return best
```

For each value `x` in the set, walk forward `x, x+1, x+2, ...` as long as the next value is in the set. Record the streak length.

This **looks** O(n). One iteration per element, hashset lookups are O(1). Surely linear?

**No.** Consider `nums = [1, 2, 3, ..., n]`. Sorted, consecutive, no gaps. The set has `n` elements.

- Starting from 1: we walk `1, 2, 3, ..., n` — `n` steps.
- Starting from 2: we walk `2, 3, ..., n` — `n − 1` steps.
- Starting from 3: we walk `3, ..., n` — `n − 2` steps.
- ...

Total work: `n + (n − 1) + (n − 2) + ... + 1 = O(n²)`.

For `n = 10⁴`, that's `5 × 10⁷` — fine. For `n = 10⁵`, that's `5 × 10⁹` — TLE.

**The wasted work:** when we start from value `2`, we re-walk the entire `[2..n]` portion of the streak that we ALREADY walked when starting from `1`. The streak is the same; we just enter it at different points.

---

## 5. The fix — only start walking from STREAK BEGINNINGS

**Observation:** any consecutive streak has a unique **starting** value — the value `x` such that `x − 1` is NOT in the set. Every value INSIDE the streak (after the start) would have its `x − 1` IN the set.

So: **only walk forward from values that are streak starts.** Skip everything else.

```
s = hashset of all values in nums
best = 0
for each x in s:
    if (x - 1) in s:
        continue                              # x is mid-streak, not a start; skip
    # x is the start of a streak — walk it
    current = 1
    next_val = x + 1
    while next_val in s:
        current += 1
        next_val += 1
    best = max(best, current)
return best
```

The added line `if (x - 1) in s: continue` is the entire trick.

**Why this is O(n):** see the next section's analysis.

---

## 6. The amortization proof

> **Claim:** the total work in the algorithm is O(n).

**Proof:**

Two parts of the work:

1. **Outer loop overhead:** iterate over `n` items in the set; for each, check `(x - 1) in s` — O(1). Total: O(n).

2. **Inner-loop walks:** the inner `while` only executes when `x` is a streak start. Each streak start triggers ONE walk that touches each element of that streak exactly ONCE.

The streaks partition the set (every element belongs to exactly one streak). So the total number of inner-loop iterations across ALL outer iterations equals the sum of streak lengths, which equals the size of the set — at most `n`.

**Total work: O(n) for outer + O(n) for all inner walks combined = O(n).** ✓

> **Mini-refresher: amortized analysis.**
>
> When analyzing an algorithm with nested loops, sometimes the worst-case work per outer iteration looks bad (e.g., the inner loop can run `n` times), BUT the TOTAL work across all outer iterations is bounded.
>
> The amortized argument: instead of "worst case per iteration × number of iterations," we sum the actual total work and show it's small.
>
> Classic examples:
> - **This problem:** outer loop is `n`; inner can run `n` times in the worst case (one streak of length n), but only ONCE (the streak is walked once total). Total: O(n).
> - **DFS on a graph:** outer loop is `n` nodes; inner iterates neighbors. Total work = sum of degrees = O(E) edges.
> - **Two-pointer scans:** both pointers move forward, each at most `n` times. Total: O(n).
>
> The trick is to ask "how much total work is done, summed over all loop iterations?" rather than "how much does each iteration do in isolation?"

---

## 7. Code

**C++:**

```cpp
int longestConsecutive(vector<int>& nums) {
    unordered_set<int> s(nums.begin(), nums.end());
    int best = 0;

    for (int x : s) {
        if (s.count(x - 1)) continue;             // not a streak start; skip

        int cur = x, len = 1;
        while (s.count(cur + 1)) {
            cur++;
            len++;
        }
        if (len > best) best = len;
    }

    return best;
}
```

Ten lines.

**Python:**

```python
def longestConsecutive(nums):
    s = set(nums)
    best = 0
    for x in s:
        if (x - 1) in s:
            continue
        cur, length = x, 1
        while (cur + 1) in s:
            cur += 1
            length += 1
        if length > best:
            best = length
    return best
```

**JavaScript:**

```javascript
function longestConsecutive(nums) {
    const s = new Set(nums);
    let best = 0;
    for (const x of s) {
        if (s.has(x - 1)) continue;
        let cur = x, len = 1;
        while (s.has(cur + 1)) {
            cur++;
            len++;
        }
        if (len > best) best = len;
    }
    return best;
}
```

All amortized O(n) time, O(n) space.

---

## 8. Trace it

**`nums = [100, 4, 200, 1, 3, 2]`:**

```
s = {100, 4, 200, 1, 3, 2}.  best = 0.

(Iteration order is implementation-dependent; I'll go in insertion order for clarity.)

x = 100:
    is (100 - 1) = 99 in s?  No.  Walk forward.
    cur = 100, len = 1.
    is 101 in s?  No.  Stop.
    best = 1.

x = 4:
    is (4 - 1) = 3 in s?  Yes.  4 is mid-streak. Skip.

x = 200:
    is 199 in s?  No.  Walk.
    cur = 200, len = 1.  201 not in s.  Stop.
    best = 1.

x = 1:
    is 0 in s?  No.  Walk.
    cur = 1, len = 1.
    is 2 in s?  Yes.  cur = 2, len = 2.
    is 3 in s?  Yes.  cur = 3, len = 3.
    is 4 in s?  Yes.  cur = 4, len = 4.
    is 5 in s?  No.  Stop.
    best = 4.

x = 3:
    is 2 in s?  Yes.  Skip.

x = 2:
    is 1 in s?  Yes.  Skip.

Return best = 4.  ✓
```

Total inner-loop steps: `1 + 1 + 4 = 6`. Plus outer-loop checks for all 6 elements. ~12 ops total. Compare to brute force O(n²) which would do ~30 ops. Wide difference grows fast as n increases.

---

## 9. Common pitfalls

1. **Forgetting the "streak start" filter.** Walking from every value gives O(n²) on adversarial inputs. The single `if (s.count(x - 1)) continue;` line is critical.

2. **Not deduplicating with a set.** If you walk from each `x` in the original array (which may have duplicates), you'd repeat work. The hashset deduplicates and lets you iterate UNIQUE values.

3. **Iterating the original array instead of the set.** Same issue as #2 — duplicates cause redundant walks. Iterate `s`, not `nums`.

4. **Initializing `best = 1` when `nums` is empty.** Edge case: empty array, no consecutive sequence. Return 0. Initialize `best = 0` and the loop handles emptiness naturally.

5. **Trying to extend the streak BACKWARD too.** Once you've identified `x` as a streak start, you only need to walk forward — `x - 1` is guaranteed NOT in the set by your check.

6. **Using a sorted set (TreeSet / std::set)** instead of `unordered_set`. Sorted sets have O(log n) lookups, making the total O(n log n). The problem demands O(n) — use the hashset.

7. **Worrying about hashset's O(n) worst case.** With adversarial inputs and a bad hash function, hashset operations can degrade. In practice with default hash, lookups are O(1) amortized. Don't optimize for paranoid cases unless you have evidence.

---

## 10. The shape — amortized linear-time patterns

The amortization trick — "each element is processed at most once across all loops, total work is O(n)" — appears in many places:

| Algorithm / Problem | The amortization |
|---|---|
| **This problem** | each element is in one streak; walked once total |
| Two pointers (sliding window, scan inward) | both pointers move forward at most n times |
| Monotonic stack (largest rectangle, daily temperatures) | each index pushed once and popped once |
| Union-Find (with path compression) | nearly O(1) per op amortized |
| Dynamic array resize (e.g., vector push_back) | doubling makes append amortized O(1) |
| DFS / BFS on a graph | each node visited once; total edge traversals = O(V + E) |
| Linear-time selection (quickselect average) | partition shrinks problem; expected work O(n) total |

**Pattern to internalize:**

> "When a nested-loop structure 'looks' O(n²) but each ELEMENT is actually processed at most once across all the inner work, the algorithm is amortized O(n). Identify the 'each item processed once' invariant — and arrange the loop's STARTING condition (e.g., 'streak start' here) so only that one trigger fires per item."

The skill is recognizing **what makes the inner loop fire** and ensuring it fires at most a constant number of times total per element.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem with **nested loops that LOOK O(n²)** but where each element seems to be touched only a few times in total, ask:
>
> > **"Is there a guard I can add to the outer loop so the inner loop fires only at specific 'starting' positions — making the total inner work amortized O(n)?"**
>
> If yes, you've turned an O(n²) heuristic into a provably-linear algorithm.

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Consecutive_Sequence.md`](../Longest_Consecutive_Sequence.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Anagram.md`](./Valid_Anagram.md), [`Valid_Sudoku.md`](./Valid_Sudoku.md) — hashset / hashmap warm-ups.
  - Coming next in this topic: Longest_Substring_Without_Repeating_Characters — sliding window (different amortization story).
  - Coming later: graph DFS / BFS topics — amortization argument generalizes there.
