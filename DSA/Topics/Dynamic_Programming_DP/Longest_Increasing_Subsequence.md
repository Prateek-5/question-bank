# Longest Increasing Subsequence

**Problem Link:**
<a href="https://leetcode.com/problems/longest-increasing-subsequence/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-increasing-subsequence/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: What Are We Asked

Given an integer array, find the length of the longest **strictly increasing** subsequence. A subsequence keeps original order but skips elements — it doesn't have to be contiguous.

Example: `[10, 9, 2, 5, 3, 7, 101, 18]`. A valid increasing subsequence is `[2, 3, 7, 101]` (length 4) or `[2, 5, 7, 18]` (length 4). No length-5 option exists. Answer: **4**.

----------------------------------------

## Step 2: Start With Small Cases

**n = 1, `[5]`:** trivially length 1.

**n = 2, `[3, 5]`:** strictly increasing, length 2. `[5, 3]`: best is length 1.

**n = 3, `[2, 5, 3]`:** `[2, 5]` or `[2, 3]` — both length 2.

**n = 4, `[1, 2, 3, 4]`:** all increasing, length 4.

**n = 4, `[4, 3, 2, 1]`:** best length is 1.

No obvious pattern, so let's think systematically.

----------------------------------------

## Step 3: The First Formulation

Let `f(i)` = length of the longest increasing subsequence that **ends exactly at index i**.

Then `f(i)` = 1 + max over `j < i` with `a[j] < a[i]` of `f(j)`. If no such `j` exists, `f(i) = 1` (just the element itself).

Final answer = max of `f(i)` over all `i`.

Let's try this on `[10, 9, 2, 5, 3, 7, 101, 18]`:

```
i=0 (10):  no j to look at.             f(0) = 1
i=1 (9):   only j=0, a[0]=10 > 9. no.   f(1) = 1
i=2 (2):   no j where a[j] < 2.         f(2) = 1
i=3 (5):   j=2 works (a[2]=2 < 5).      f(3) = f(2) + 1 = 2
i=4 (3):   j=2 works.                   f(4) = f(2) + 1 = 2
i=5 (7):   j=2,3,4 work. max f = 2.     f(5) = 3
i=6 (101): j=0..5 all work. max f = 3.  f(6) = 4
i=7 (18):  j=0..5 with a[j]<18. max f = 3 (from j=5). f(7) = 4
```

Max of f: **4**. ✓

This gives an O(n²) algorithm — one loop for `i`, one for `j`. For `n = 2500` it's fine; for `n = 10^5` it's too slow. Can we do better?

----------------------------------------

## Step 4: Why O(n²) Feels Wasteful

At each `i`, we scan all previous indices. That's a lot of work. Most of it doesn't help — we're just searching for "what's the best LIS length whose last element is less than `a[i]`?"

That reformulation — "best length for some *condition*" — is a clue. If we could organize previous results *sorted by their last element*, we could answer the query faster.

But there's a cleaner and more surprising way. Let me walk through it.

----------------------------------------

## Step 5: A Different Mental Model — Piles of Cards

Here's a puzzle. Imagine you're dealt cards one at a time, and you place each card on one of several piles with this rule:

- You can place a card on any pile whose top card is **greater than or equal to** the new card (so piles look decreasing top-down? wait, we want strictly increasing LIS — let me be careful).

Actually for *strictly* increasing LIS, the rule is: place the card on the leftmost pile whose top is **greater than or equal to** the new card (so the pile's top is replaced downward). If no pile qualifies, start a new pile to the right.

Claim: at the end, the **number of piles** equals the LIS length.

It's the exact mechanic of a patience-sort game. Why on earth is the number of piles equal to the LIS length?

----------------------------------------

## Step 6: Why Pile-Count = LIS Length

**Claim 1:** We can always construct an increasing subsequence of length equal to the number of piles.

*Sketch:* Each pile grows downward when a smaller card arrives. The top of pile `k+1` was placed after some card on pile `k`'s top at that time. By tracing back pile-top relationships, we can find one card from each pile in order, strictly increasing. Hence LIS ≥ piles.

**Claim 2:** No increasing subsequence can exceed the number of piles.

*Sketch:* Two cards from the same pile are placed one on top of the other, meaning the later one is ≤ the earlier. So any strictly increasing sequence picks at most one card per pile. Hence LIS ≤ piles.

Together: **LIS length = number of piles**.

So if we simulate this card game efficiently, we get the LIS length.

----------------------------------------

## Step 7: Simulating Efficiently

We don't actually need to track full piles — just each pile's **top card** (the smallest value currently on top). Let `tails[k]` = top card of pile `k+1`.

Key observation: `tails` is always sorted ascending. (If pile `k+1` has top `t_k` and pile `k+2` has top `t_{k+1}`, then `t_{k+1}` was placed when `t_k` was some earlier pile's top that was < `t_{k+1}` at placement time. The tops maintain a sorted order.)

So for each incoming number `x`, we want:

- The leftmost pile whose top is **>= x** → that's where `x` goes.
- If no such pile exists, `x` starts a new pile.

"Leftmost position in sorted array where element ≥ x" is exactly **binary search for lower_bound**.

Algorithm:
1. Initialize `tails` as empty.
2. For each `x`:
   - Find position `p` via `lower_bound(tails, x)`.
   - If `p == tails.size()`, push `x` at the end (new pile).
   - Else, replace `tails[p] = x` (update the top of that pile to `x`).
3. Answer is `tails.size()`.

This is O(n log n) — one binary search per element.

----------------------------------------

## Step 8: Walk Through the Example

`nums = [10, 9, 2, 5, 3, 7, 101, 18]`.

```
x=10: tails=[], lower_bound no result → push. tails=[10].
x=9: lower_bound(tails, 9) = 0 (10 is >= 9). Replace. tails=[9].
x=2: lower_bound = 0. Replace. tails=[2].
x=5: lower_bound(tails, 5) = 1 (end, since 2 < 5). Push. tails=[2, 5].
x=3: lower_bound(tails, 3) = 1 (5 is >= 3). Replace. tails=[2, 3].
x=7: lower_bound = 2 (end). Push. tails=[2, 3, 7].
x=101: lower_bound = 3 (end). Push. tails=[2, 3, 7, 101].
x=18: lower_bound(tails, 18) = 3 (101 >= 18). Replace. tails=[2, 3, 7, 18].
```

Final size = **4**. ✓

One curiosity: `tails` at the end is `[2, 3, 7, 18]`, which itself *is* a valid LIS, but that's coincidental. In general, the `tails` array is **not** the LIS — it's just a book-keeping structure. To reconstruct the actual LIS you'd need extra parent pointers.

----------------------------------------

## Step 9: Naming What We Did

This is **patience sorting** and the resulting algorithm is the standard O(n log n) LIS algorithm. A beautiful name for a beautiful trick — but again, we derived it, not memorized it.

One subtlety to nail down: we use `lower_bound` (first position with value **≥ x**) because the LIS we want is **strictly** increasing. If the problem were "longest non-decreasing", we'd use `upper_bound` (first position with value **> x**). The distinction matters; get it wrong and your answer is off by the number of duplicates.

----------------------------------------

## Step 10: Complexity

Time: one binary search per element → **O(n log n)**.
Space: `tails` holds at most n elements → **O(n)**.

From O(n²) down to O(n log n) via the patience-sort insight.

----------------------------------------

## Step 11: C++ Implementation

```cpp
int lengthOfLIS(vector<int>& nums) {
    vector<int> tails;
    for (int x : nums) {
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);
        else *it = x;
    }
    return tails.size();
}
```

----------------------------------------

## Step 12: Follow-up Questions

- **Longest *non-decreasing* subsequence.** Swap `lower_bound` for `upper_bound`.
- **Actual LIS sequence, not just the length.** Track parent pointers during the replacement step; walk them backward at the end.
- **Longest decreasing subsequence.** Negate values and solve LIS.
- **Russian Doll Envelopes (2D LIS).** Sort by width ascending, height descending (the desc tie-breaker is the key), then LIS on heights.
- **LIS with frequent updates.** Segment tree indexed by value with range-max queries gives O(log n) per update/query.
- **K-th longest increasing subsequence.** Much harder — count LIS and use DP with ordered structures.


---

## Interview Signals (from LeetLens)

This problem (or close variants) was reported in **1 real interview(s)** in the LeetLens dataset (snapshot 2026-05-31). Pay attention to the company context when practicing.

| Company | Difficulty | LeetLens ID | Match | Variant note |
|---|---|---|---|---|
| — | Easy | `51c1cc90` | 1.00 (exact-title) | Longest Increasing Subsequence (LIS) |

_Source: LeetLens DB. Match methods: `substring` = direct hit; `token-coverage` = ≥70% of this card's filename tokens appear in the question; `jaccard`/`ratio` = fuzzy title similarity._
_See the parent folder's `EXTRACTED_QUESTIONS.md` §2 for the full list of incorporated questions._
