# Largest Multiple of Three

**Problem Link:**
<a href="https://leetcode.com/problems/largest-multiple-of-three/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/largest-multiple-of-three/</a>

**Topic:**
Number Theory / Misc (also greedy)

----------------------------------------

## Step 1: The Goal

Given an array of digits (each 0..9), choose a subset of them (using each digit at most as many times as it appears) and concatenate them in any order to form the **largest number divisible by 3**.

Return this number as a string. If no multiple of 3 can be formed, return `""`. Avoid leading zeros (except the case where the answer is just "0").

Example: `digits = [8, 1, 9]`. Total sum = 18 (divisible by 3). Use all. Largest arrangement: "981". Return **"981"**.

Example: `digits = [8, 6, 7, 1, 0]`. Sum = 22. Not divisible by 3. Remove one digit to make sum divisible by 3: 22 mod 3 = 1. Need to remove a digit ≡ 1 (mod 3). Candidates: 7 or 1. Remove 1 (the smaller) → remaining {8, 6, 7, 0}. Sum = 21. Arrange: "8760". Return **"8760"**.

----------------------------------------

## Step 2: The Rule for Divisibility by 3

**A number is divisible by 3 iff the sum of its digits is divisible by 3.**

So we want to choose a subset of digits whose sum is ≡ 0 (mod 3), then arrange them largest-first.

----------------------------------------

## Step 3: Strategy

1. **Use as many digits as possible** (larger number = more digits used, when leading zeros aren't an issue).
2. If total sum is divisible by 3, use all digits.
3. Otherwise, **remove the minimum number of digits** to fix the sum's mod-3 residue, while keeping the remaining sum as large as possible (i.e., remove **small** digits).

Say total_sum mod 3 = 1. We need to drop digits summing to ≡ 1 (mod 3). Options:
- Drop 1 digit with residue 1 (digits 1, 4, 7).
- Drop 2 digits with residue 2 each (2, 5, 8). Because 2 + 2 = 4 ≡ 1 (mod 3).

Prefer dropping **fewer digits** when possible. So try option 1 first; if no residue-1 digit exists, try option 2.

For residue 2: drop 1 digit with residue 2, or drop 2 digits with residue 1.

----------------------------------------

## Step 4: Algorithm

1. Compute total_sum of all digits.
2. Let r = total_sum mod 3.
3. If r == 0: use all digits.
4. Else: group digits by residue (mod 3). Try to remove:
   - If r == 1: remove smallest digit with residue 1. If none, remove two smallest with residue 2.
   - If r == 2: remove smallest digit with residue 2. If none, remove two smallest with residue 1.
5. Sort remaining digits descending; concatenate.
6. Strip leading zeros (keep one if all zeros remain).

----------------------------------------

## Step 5: Trace on `[8, 6, 7, 1, 0]`

Digits sorted: [8, 7, 6, 1, 0]. Sum = 22. r = 22 mod 3 = 1.

Group by residue:
- r=0: {6, 0}.
- r=1: {7, 1}.
- r=2: {8}.

Remove smallest r=1 digit: 1. Remaining: [8, 7, 6, 0]. Sum = 21. Arrange descending: "8760".

Return **"8760"**. ✓

Try `[1, 1, 1, 1]`. Sum = 4. r = 1.

Groups: r=0: {}. r=1: {1, 1, 1, 1}. r=2: {}.

Remove smallest r=1: one 1. Remaining: [1, 1, 1]. Sum = 3 ✓. Arrange: "111".

Return "111".

Try `[0, 0, 0, 0, 0]`. Sum = 0. r = 0. Use all. But they're all zeros → return "0" (strip leading zeros to one).

----------------------------------------

## Step 6: Why Fewer Removals Is Better

Larger number = more digits, assuming no leading zeros ruin things. So we always prefer removing **fewer digits**.

When r = 1 and no r=1 digit exists, we must remove two r=2 digits (since two r=2's sum to r=4 ≡ 1 mod 3). Losing 2 digits is worse than 1, but necessary.

Among candidates within a category, prefer removing **smaller** values — larger digits contribute more to the final number's magnitude.

----------------------------------------

## Step 7: Why Sort Descending After Selection?

To maximize the concatenated number, arrange digits from largest to smallest (leftmost is most significant).

Exception: if all chosen digits are 0, return "0" (not "000...0").

----------------------------------------

## Step 8: Name It

**Greedy digit selection by modular arithmetic**. A number-theoretic approach: the divisibility rule for 3 is a linear function of digit values (their sum mod 3), so we can remove minimal "mass" with respect to the sum to fix the residue.

Related problems:
- Largest Multiple of Two (last digit must be even).
- Largest Multiple of Five (last digit 0 or 5).
- Largest Number using given digits.

The modular-sum trick generalizes to 9 (digit sum mod 9) and 11 (alternating digit sum mod 11).

----------------------------------------

## Step 9: Complexity

Time: **O(n log n)** (dominated by sorting).
Space: **O(n)** for the digit groups.

----------------------------------------

## Step 10: C++ Implementation

```cpp
string largestMultipleOfThree(vector<int>& digits) {
    int sum = 0;
    for (int d : digits) sum += d;

    // Group digits by residue mod 3
    vector<int> r1, r2;
    for (int d : digits) {
        if (d % 3 == 1) r1.push_back(d);
        else if (d % 3 == 2) r2.push_back(d);
    }

    // Sort each group ascending (to find smallest to remove)
    sort(r1.begin(), r1.end());
    sort(r2.begin(), r2.end());

    auto remove_k = [&](vector<int>& grp, int k) {
        for (int i = 0; i < k; ++i) {
            grp.erase(grp.begin());   // remove smallest
        }
    };

    int rem = sum % 3;
    if (rem == 1) {
        if (!r1.empty()) remove_k(r1, 1);
        else if (r2.size() >= 2) remove_k(r2, 2);
        else return "";
    } else if (rem == 2) {
        if (!r2.empty()) remove_k(r2, 1);
        else if (r1.size() >= 2) remove_k(r1, 2);
        else return "";
    }

    // Collect remaining digits, sort descending
    vector<int> all_digits;
    for (int d : digits) {
        // subtract from group if still present; complex. Simpler: rebuild from r0, r1, r2.
    }

    // Simpler: rebuild from groups
    vector<int> r0;
    for (int d : digits) if (d % 3 == 0) r0.push_back(d);

    all_digits.clear();
    all_digits.insert(all_digits.end(), r0.begin(), r0.end());
    all_digits.insert(all_digits.end(), r1.begin(), r1.end());
    all_digits.insert(all_digits.end(), r2.begin(), r2.end());

    sort(all_digits.rbegin(), all_digits.rend());

    if (all_digits.empty()) return "";
    if (all_digits[0] == 0) return "0";   // all zeros

    string result;
    for (int d : all_digits) result += char('0' + d);
    return result;
}
```

The code has some rough edges (using `erase(begin())` is O(n)); a tighter version would pop from the back after sorting descending. But the structure is clear.

----------------------------------------

## Step 11: Follow-up Questions

- **Largest multiple of 9.** Same trick (digit sum mod 9). Analogous analysis.
- **Largest multiple of 11.** More complex; uses alternating-sum divisibility rule.
- **Smallest multiple instead.** Same approach, ascending sort.
- **Digits must stay in original order.** Different — needs DP.
- **Why 3 and not other divisors?** Because 3 (and 9) have the remarkable property that digit sums mirror divisibility. 7 doesn't; testing divisibility by 7 requires evaluating the number itself.
- **Why prefer small digit removal?** Larger digits contribute more to the number's value; keep them.
