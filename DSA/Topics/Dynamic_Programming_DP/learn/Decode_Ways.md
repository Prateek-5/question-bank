# Decode Ways — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Decode_Ways.md`](../Decode_Ways.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/decode-ways/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/decode-ways/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: at each position, you EITHER take 1 digit (if non-zero) OR take 2 digits (if in [10, 26]). Sum the two branches. Fibonacci-shaped DP with VALIDITY GUARDS for zeros and out-of-range pairs.**

**Map of this file (9 sections):**

1. Read the problem
2. The 1-or-2 split
3. The zero trap
4. Recurrence
5. Code
6. Trace it
7. Common pitfalls
8. The shape — split-position DP
9. Self-check

---

## 1. Read the problem

Letters encode as `A=1, B=2, ..., Z=26`. Given a digit string, count the number of distinct decodings.

**Examples:**

- `"12"` → "AB" or "L" → **2**.
- `"226"` → "BBF", "BZ", "VF" → **3**.
- `"06"` → invalid (leading zero, no decode) → **0**.

---

## 2. The 1-or-2 split

> **Mini-refresher: at each position, decide how many digits to consume.**
>
> Either:
> - Take 1 digit (valid if it's 1..9), then recurse on the rest.
> - Take 2 digits (valid if pair ∈ [10, 26]), then recurse on the rest.
>
> SUM both contributions.

This is structurally identical to Climbing Stairs (1 or 2 steps), but with VALIDITY GUARDS.

---

## 3. The zero trap

> **Mini-refresher: zeros are special.**
>
> - `'0'` standalone has NO decode (no letter maps to 0). One-digit branch INVALID.
> - Two-digit pair like `"06"`: 6 < 10, so this 2-digit isn't a letter either. INVALID.
> - Valid 2-digit pairs: `"10".."26"`.

So a `'0'` is only valid as the SECOND digit of a pair `[10, 20]` (i.e., paired with a leading 1 or 2). Otherwise it kills the decoding.

---

## 4. Recurrence

`dp[i]` = number of decodings of suffix `s[i..]`.

- `dp[n] = 1` (empty suffix has exactly one decoding — the empty one).
- For i from n-1 down to 0:
  - If `s[i] != '0'`: `dp[i] += dp[i+1]` (take 1 digit).
  - If `i+1 < n` and pair `s[i..i+1] ∈ [10, 26]`: `dp[i] += dp[i+2]` (take 2 digits).

Answer: `dp[0]`.

Only `dp[i+1]` and `dp[i+2]` are ever read → use two rolling variables.

---

## 5. Code

**C++:**

```cpp
int numDecodings(string s) {
    int n = s.size();
    if (n == 0 || s[0] == '0') return 0;

    int two_ahead = 1;    // dp[n]
    int one_ahead = 1;    // dp[n] (initialized for i = n - 1)

    for (int i = n - 1; i >= 0; --i) {
        int cur = 0;
        if (s[i] != '0') cur += one_ahead;
        if (i + 1 < n) {
            int pair = (s[i] - '0') * 10 + (s[i+1] - '0');
            if (pair >= 10 && pair <= 26) cur += two_ahead;
        }
        two_ahead = one_ahead;
        one_ahead = cur;
    }
    return one_ahead;
}
```

**Python:**

```python
def numDecodings(s):
    n = len(s)
    if not s or s[0] == '0':
        return 0
    two_ahead = 1
    one_ahead = 1
    for i in range(n - 1, -1, -1):
        cur = 0
        if s[i] != '0':
            cur += one_ahead
        if i + 1 < n:
            pair = int(s[i:i+2])
            if 10 <= pair <= 26:
                cur += two_ahead
        two_ahead, one_ahead = one_ahead, cur
    return one_ahead
```

Complexity: **O(n)** time, **O(1)** space.

---

## 6. Trace it

`s = "226"`. n = 3.

```
two_ahead = 1, one_ahead = 1.   (dp[3] = 1)

i=2 (s[2]='6'): 
  '6' != '0' → cur += one_ahead = 1.
  i+1 = 3 = n → no pair.
  cur = 1.
  shift: two_ahead = 1, one_ahead = 1.   (dp[2] = 1)

i=1 (s[1]='2'):
  '2' != '0' → cur += 1.
  pair = 26 ∈ [10, 26] → cur += two_ahead = 1.
  cur = 2.
  shift: two_ahead = 1, one_ahead = 2.   (dp[1] = 2)

i=0 (s[0]='2'):
  '2' != '0' → cur += 2.
  pair = 22 ∈ [10, 26] → cur += two_ahead = 1.
  cur = 3.
  shift: one_ahead = 3.

Return 3.  ✓
```

`s = "06"`: handled by the early return (s[0] = '0').

`s = "10"`: 
- i=1 (s[1]='0'): s[1]='0' → skip 1-digit. No pair (i+1=n). cur=0. dp[1]=0.
- i=0 (s[0]='1'): 1-digit → cur += dp[1] = 0. pair=10 ∈ [10, 26] → cur += dp[2] = 1. cur = 1.
- Return 1.  ✓ (only "J")

---

## 7. Common pitfalls

1. **Forgetting the `s[0] == '0'` early return.** If the string starts with 0, no decoding exists.
2. **Allowing pair < 10.** `"06"` has pair = 6, which is NOT a valid two-digit code.
3. **Allowing pair > 26.** Letters go up to Z = 26.
4. **Off-by-one on `dp[n]`.** The base case is `dp[n] = 1`, not 0.
5. **Adding both branches WITHOUT validity checks.** Each branch is conditional; if both fail, `dp[i] = 0` (kills the decoding).
6. **Mixing forward and backward DP.** Either iterate right-to-left with `dp[i] = dp[i+1] + maybe dp[i+2]`, OR left-to-right with `dp[i] = dp[i-1] + maybe dp[i-2]`. Pick one and stay consistent.

---

## 8. The shape — split-position DP

The pattern: **at each position, choose how many units to consume; sum contributions.**

| Problem | Choices per step |
|---|---|
| Climbing Stairs | 1 or 2 (unconditional) |
| **This problem** | 1 (if valid digit) or 2 (if valid pair) |
| Decode Ways II (with `*`) | same, but `*` can be many digits |
| Word Break | every prefix that's a dictionary word |
| Concatenated Words | every dictionary split point |
| Perfect Squares | every square root ≤ remaining |

**Pattern to internalize:**

> "At each position, sum contributions from VALID split choices (1, 2, k digits/words/units). Validity guards drop invalid branches to 0. Fibonacci-shape when choices are 1 or 2."

---

## 9. Self-check

> **The question to ask next time:**
>
> > **"At each position, what are the valid 'commit k units' choices? Sum dp[i+k] for each valid k. Watch for zeros / out-of-range pairs killing branches."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Decode_Ways.md`](../Decode_Ways.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Climbing_Stairs.md`](./Climbing_Stairs.md), [`Distinct_Subsequences.md`](./Distinct_Subsequences.md).
  - Coming next: [`Interleaving_String.md`](./Interleaving_String.md), [`Regular_Expression_Matching.md`](./Regular_Expression_Matching.md), [`Frog_Jump.md`](./Frog_Jump.md).
