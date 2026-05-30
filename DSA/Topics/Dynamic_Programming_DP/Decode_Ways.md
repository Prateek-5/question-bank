# Decode Ways

**Problem Link:**
<a href="https://leetcode.com/problems/decode-ways/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/decode-ways/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Understand the Mapping

Letters are encoded as `A=1, B=2, ..., Z=26`. Given a string of digits, count **how many distinct ways** it can be decoded back into letters.

`"12"` could mean:
- `"AB"` (1 then 2)
- `"L"` (12 — which is L)

That's 2 ways.

`"226"`:
- `"BBF"` (2, 2, 6)
- `"BZ"` (2, 26)
- `"VF"` (22, 6)

That's 3 ways.

And an annoying edge case: `"06"`. Leading zero? `0` doesn't map to anything (letters start at 1). And `06` isn't a valid two-digit decode either. So this decodes 0 ways.

----------------------------------------

## Step 2: Try to Enumerate by Hand

**s = "1":** One digit, maps to `A`. 1 way.

**s = "11":** `"AA"` or `"K"` (since 11 = K). 2 ways.

**s = "12":** `"AB"` or `"L"`. 2 ways.

**s = "27":** `"BG"` (2, 7). Can I read "27" as a two-digit? 27 > 26, no. So just 1 way.

**s = "10":** `"J"` (since 10 = J). Can I split as "1" then "0"? No — "0" has no decode. So only the two-digit split works. 1 way.

**s = "100":** let's see. `"1" + "00"` fails (no decode for "00" or "0"). `"10" + "0"` fails (standalone "0" has no decode). `"100"` isn't a single-letter decode (letters go 1-26). So 0 ways.

**s = "226":** already did — 3 ways.

Patterns appearing:
- A leading `0` or an isolated `0` kills a branch entirely.
- Each position, we look at either the current digit alone or the current digit paired with the previous one.

----------------------------------------

## Step 3: What Happens at Each Position?

Let me think recursively. Suppose I've got the string `s` and I want to count decodings. At the very beginning:

- If `s[0] != '0'`, I can consume `s[0]` alone as a letter (1 through 9) and then decode the rest.
- If `s[0..1]` forms a valid two-digit number between 10 and 26, I can consume two digits as one letter, and decode the rest.

Each choice is independent (after the choice, the rest of the string is smaller). The total is the sum over all valid starting choices.

So the recurrence is:

```
decode(s, i) = 
    (1 if s[i] != '0' else 0) * decode(s, i+1)
  + (1 if 10 <= s[i..i+1] as int <= 26 else 0) * decode(s, i+2)
```

Base case: `decode(s, len(s)) = 1` (empty suffix = one valid decoding, the empty one — think of it as "all characters consumed successfully").

Why does the empty suffix count as 1 and not 0? Because reaching the end successfully represents one completed decoding. If we said 0, we'd never accumulate a count. Think of it as "there's exactly one way to decode nothing: do nothing."

----------------------------------------

## Step 4: Does the Recurrence Revisit Subproblems?

For `s = "226"`:

- decode(0) = decode(1) + decode(2) (both splits valid at position 0)
- decode(1) = decode(2) + decode(3)
- decode(2) = decode(3) + 0 (no two-digit starting at index 2; the string ends)

decode(2) gets called from both decode(0)-via-two-digit and decode(1)-via-one-digit. And decode(3) is called from both decode(1) and decode(2). Classic overlap.

For a longer string, this overlap grows exponentially — every split creates branches that reconverge. So we'd benefit from remembering each `decode(i)` the first time we compute it. That turns the exponential recursion into linear by eliminating re-work.

----------------------------------------

## Step 5: Bottom-Up Table

Let `dp[i]` = number of ways to decode the suffix `s[i..]`. We compute from right to left.

- `dp[n] = 1` (empty suffix).
- For `i` from `n-1` down to `0`:
  - If `s[i] != '0'`, `dp[i] += dp[i+1]`.
  - If the two-digit number `s[i..i+1]` is in `[10, 26]`, `dp[i] += dp[i+2]`.

Return `dp[0]`.

Notice we only ever need `dp[i+1]` and `dp[i+2]` to compute `dp[i]`. So we can keep just two variables.

----------------------------------------

## Step 6: Trace on "226"

We go right-to-left. n = 3.

```
dp[3] = 1 (empty suffix)

dp[2]: s[2] = '6'. Single-digit works → dp[2] += dp[3] = 1.
       Two-digit s[2..3] doesn't exist (i+1 = 3 = n).
       dp[2] = 1.

dp[1]: s[1] = '2'. Single-digit works → dp[1] += dp[2] = 1.
       Two-digit s[1..2] = "26", in [10, 26] → dp[1] += dp[3] = 1.
       dp[1] = 2.

dp[0]: s[0] = '2'. Single-digit works → dp[0] += dp[1] = 2.
       Two-digit s[0..1] = "22", in [10, 26] → dp[0] += dp[2] = 1.
       dp[0] = 3.
```

Answer: **3**. ✓

Trace on "06":

```
dp[2] = 1
dp[1]: s[1]='6'. dp[1] += dp[2] = 1. No two-digit (end). dp[1] = 1.
dp[0]: s[0]='0'. Single-digit fails (zero has no decode). 
       Two-digit s[0..1]="06", 6 < 10 → not valid. No addition.
       dp[0] = 0.
```

Answer: 0. ✓

----------------------------------------

## Step 7: Name the Pattern Now

This is a textbook **linear DP on index**, with two branches per state (take 1 digit or take 2). The recurrence `dp[i] = dp[i+1] + dp[i+2]` (when both branches are valid) looks suspiciously like Fibonacci — and it is, but with conditions that can zero out either branch when digits don't form valid letters.

The teaching lesson: whenever you have a sequence where each position has a small number of "commit k characters" choices, an index-based DP of this shape is often the answer.

----------------------------------------

## Step 8: Complexity

Time: one pass over the string, O(1) work per position. **O(n)**.
Space: two rolling variables. **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int numDecodings(string s) {
    int n = s.size();
    if (n == 0 || s[0] == '0') return 0;   // empty or leading zero — no decoding

    int two_ahead = 1;    // dp[i+2]
    int one_ahead = 1;    // dp[i+1] — starts as "dp[n]"

    // Iterate from n-1 down to 0
    for (int i = n - 1; i >= 0; --i) {
        int cur = 0;
        if (s[i] != '0') cur += one_ahead;                     // take one digit
        if (i + 1 < n) {
            int pair = (s[i] - '0') * 10 + (s[i+1] - '0');
            if (pair >= 10 && pair <= 26) cur += two_ahead;    // take two digits
        }
        two_ahead = one_ahead;
        one_ahead = cur;
    }

    return one_ahead;
}
```

The two rolling vars mirror `dp[i+1]` and `dp[i+2]` as we sweep from right to left. The `pair >= 10` check is crucial: it rejects "06" (invalid because of the leading zero) and anything under 10 that would only be a one-digit code.

----------------------------------------

## Step 10: Follow-up Questions

- **Decode Ways II (the input contains `*`, which represents any digit 1-9).** Messier case analysis — `*` can be any of 9 digits for the one-digit branch, and can pair with the next/previous to form various two-digit numbers. More cases, same structure.
- **Print all decodings, not just count.** Switch from DP counting to backtracking; at each index, branch on the valid choices and record the full letter sequence.
- **Count modulo M.** Wrap each addition in `% M` to avoid overflow.
- **Input might contain non-digits — return -1.** Add validation; zero out the count on invalid characters.
- **Streaming version — count decodings so far after each digit arrives.** Same recurrence, but read left to right: `dp[i] = (one-digit contribution) * dp[i-1] + (two-digit contribution) * dp[i-2]`.
