# Numbers At Most N Given Digit Set

**Problem Link:**
<a href="https://leetcode.com/problems/numbers-at-most-n-given-digit-set/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/numbers-at-most-n-given-digit-set/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Parse the Problem

Given a sorted array of digits (strings, each a single digit '1'-'9', no '0'), and an integer `n`, count how many positive integers can be formed using those digits (with unlimited reuse) that are **less than or equal to n**.

Example: `digits = ["1", "3", "5", "7"]`, n = 100.

Count of valid numbers ≤ 100:
- 1-digit: 1, 3, 5, 7. That's 4.
- 2-digit: can use any digit for each of 2 positions → 4 × 4 = 16. All these (11 through 77) are ≤ 100.
- 3-digit: smallest would be 111, already > 100. Zero.

Total: 4 + 16 + 0 = **20**.

----------------------------------------

## Step 2: Split by Length

Any valid number has fewer, equal, or more digits than n. Let `L = number of digits in n`.

- Numbers with **fewer** digits (< L) are always < n. Count per length.
- Numbers with **equal** digits (= L) may be ≤ n or > n. Careful digit-by-digit count.
- Numbers with **more** digits (> L) are > n. Skip.

Let me separate these cases.

----------------------------------------

## Step 3: Case 1 — Fewer Digits

For a length `k` with k < L: every digit position has `d = len(digits)` choices. So there are `d^k` numbers of length k.

Total across k = 1 to L-1: `d + d² + ... + d^(L-1)`.

For the example: digits = ["1","3","5","7"] (d=4), n=100 (L=3).

Sum for k < L (= for k=1, 2): 4 + 16 = 20. ✓ matches.

----------------------------------------

## Step 4: Case 2 — Equal Digits, Digit by Digit

For exactly L digits, we have to compare against n digit-by-digit.

Let n have digits `n[0], n[1], ..., n[L-1]` from most significant to least.

Consider position i. Two sub-cases:
- **A digit d in our set is strictly less than n[i]:** then placing it here commits us to "less than n" from this position onward. The remaining L-i-1 positions can be any of the `d` digits freely. Count: (number of digits in set < n[i]) × `d^(L-i-1)`.
- **A digit d in our set equals n[i]:** placing it keeps us "tied" with n. We continue to position i+1 to decide.

If at any position, no digit in our set equals n[i], we stop (can't continue the tie).

After processing all L positions, if we reached the end with a valid tie, then n itself is representable by our digit set — add 1 (n itself is a valid number).

----------------------------------------

## Step 5: Trace Case 2 for digits = ["1","3","5","7"], n = 100

L = 3. Digits of n = [1, 0, 0].

**Position 0 (n[0] = 1):**
- Digits in set < 1: none.
- Digits equal to 1: "1". Tie continues.

Count so far: 0 × 4^2 = 0.

**Position 1 (n[1] = 0):**
- Digits in set < 0: none (our digits are 1, 3, 5, 7).
- Digits equal to 0: none.
- No tie possible. STOP.

So for L=3, no numbers equal to or less than n starting with '1' then reaching down. 0 contribution.

Wait — but my earlier count said 20 total and the case-1 already gave 20. So case 2 should give 0. ✓ Matches.

Let me try a case where case 2 matters: n = 555, digits = ["1", "3", "5", "7"].

L = 3. n digits: [5, 5, 5].

**Position 0 (n[0] = 5):**
- Digits < 5: "1" and "3". That's 2.
- Contribution: 2 × 4² = 32.
- Digits == 5: "5". Tie continues.

**Position 1 (n[1] = 5):**
- Digits < 5: 2. Contribution: 2 × 4¹ = 8.
- Digits == 5: 1. Tie continues.

**Position 2 (n[2] = 5):**
- Digits < 5: 2. Contribution: 2 × 4⁰ = 2.
- Digits == 5: 1. Tie continues.

End of digits. Tie survived, so n itself (555) is valid. Add 1.

Case 2 total: 32 + 8 + 2 + 1 = 43.

Case 1 (L < 3): 4 + 16 = 20.

Grand total: 20 + 43 = 63.

Let me sanity check: for n = 555 and digits {1, 3, 5, 7}:
- 1-digit: 4.
- 2-digit: 16.
- 3-digit ≤ 555: first digit 1, 3 (anything after), or 5 with constraints.
  - Starts with 1: 16 numbers (1**).
  - Starts with 3: 16.
  - Starts with 5: the "5**" combinations. 
    - 1-digit after 5: if second digit < 5 (so 51*, 53*), each has 4 options for last = 8.
    - Second digit = 5 (so 55*): third < 5 gives "551", "553" → 2. Third = 5 gives "555" → 1. So 3.
  - Total 5*** = 11.
- 3-digit total: 16 + 16 + 11 = 43. ✓

Grand total: 4 + 16 + 43 = 63. Matches.

----------------------------------------

## Step 6: The Algorithm

```
L = len(str(n))
d = len(digits)
count = 0

# Case 1: fewer digits
for k in 1..L-1:
    count += d^k

# Case 2: exactly L digits
N_str = str(n)
for i in 0..L-1:
    ch = N_str[i]
    lesser_count = count of digits in set strictly less than ch
    count += lesser_count * d^(L - i - 1)
    
    if ch is in digits:
        continue tie
    else:
        break
else:
    # tie survived all positions: n itself is representable
    count += 1

return count
```

The for-else construct (Python-esque): the `else` runs if the for loop completes without breaking, meaning the tie lasted all L positions.

O(L) work. Since L ≤ 10 for typical n ≤ 10^9, this is basically O(1).

----------------------------------------

## Step 7: Name It

**Digit DP / digit-position counting**. The pattern: count numbers up to N by iterating through digit positions, accumulating counts for "strictly less at this position" and recursing into "tied" cases.

Classic digit-DP problem. Same structure applies to:
- Count of numbers with specific digit properties up to N.
- Number of Digit One.
- Nth Digit.
- Confusing Number II.

The power of digit DP: exponentially-large ranges collapsed to O(L) work where L = digit count.

----------------------------------------

## Step 8: Complexity

Time: **O(L)** where L = digit count of n. For n ≤ 10^9, L ≤ 10.
Space: **O(1)** extra.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int atMostNGivenDigitSet(vector<string>& digits, int n) {
    string N_str = to_string(n);
    int L = N_str.size();
    int d = digits.size();
    int count = 0;

    // Case 1: numbers with fewer digits than n.
    int power = 1;
    for (int k = 1; k < L; ++k) {
        power *= d;
        count += power;
    }

    // Case 2: numbers with exactly L digits, possibly tied with n.
    bool tie = true;
    for (int i = 0; i < L && tie; ++i) {
        char ch = N_str[i];
        int lesser = 0;
        bool match = false;
        for (const string& dgt : digits) {
            if (dgt[0] < ch) lesser++;
            else if (dgt[0] == ch) match = true;
            else break;   // digits are sorted; can stop
        }
        count += lesser * pow(d, L - i - 1);
        if (!match) tie = false;
    }

    if (tie) count += 1;   // n itself is representable

    return count;
}
```

The outer loop walks through n's digits. For each, we count how many of our digits are strictly smaller, and check if any matches to continue the tie.

Careful: `pow(d, ...)` should use integer arithmetic; here `pow` returns double, so we could cast or compute manually. For L ≤ 10 and d ≤ 9, `pow(d, L)` fits in an int safely after casting.

----------------------------------------

## Step 10: Follow-up Questions

- **Count numbers in a range [L, R].** Compute `f(R) - f(L - 1)` where f is our function.
- **Count numbers with specific digit constraints** (no consecutive equal digits, etc.). More elaborate digit DP — add state for "last digit" or similar.
- **Very large n (bigint).** Same algorithm; just use string representation.
- **Allow '0' in the digit set.** Handle leading zeros carefully (shorter numbers can't start with 0).
- **Memoization version for more general digit DP.** Recurse on (position, tight, ...) state; memo on (position, tight) or similar.
- **Count rather than upper-bound (exactly k valid numbers).** Needs different DP.
