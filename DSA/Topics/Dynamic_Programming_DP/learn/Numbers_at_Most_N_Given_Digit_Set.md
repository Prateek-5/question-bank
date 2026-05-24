# Numbers At Most N Given Digit Set — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Numbers_at_Most_N_Given_Digit_Set.md`](../Numbers_at_Most_N_Given_Digit_Set.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/numbers-at-most-n-given-digit-set/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: DIGIT DP. Split by length L = digits-in-N. Numbers with FEWER digits are unconstrained (d^k each). Numbers with EQUAL digits need digit-by-digit comparison — track "still tied with N." O(L) work for n up to 10^L.**

**Map of this file (9 sections):**

1. Read the problem
2. Split by length
3. Case 1 — fewer digits
4. Case 2 — same length (digit by digit)
5. The tie-tracking algorithm
6. Code
7. Trace it
8. Common pitfalls
9. The shape — digit DP

---

## 1. Read the problem

Given a SORTED array `digits` (each a single digit string from '1' to '9', no '0'), and integer `n`, count POSITIVE INTEGERS formable from those digits (with REPETITION allowed) that are ≤ n.

**Example:** `digits = ["1","3","5","7"], n = 100` → **20**.

---

## 2. Split by length

Let L = number of digits in n. Any valid number has:

- **Fewer digits (< L):** automatically < n.
- **Same digits (= L):** may or may not be ≤ n; check carefully.
- **More digits (> L):** > n. Skip.

---

## 3. Case 1 — fewer digits

For length k < L, every position has `d = |digits|` choices → `d^k` numbers.

Total: `d + d² + ... + d^(L-1)`.

For the example: d = 4, L = 3 → 4 + 16 = **20**.

---

## 4. Case 2 — same length (digit by digit)

For exactly L digits, walk through n's digits left-to-right. At each position i:

- Digits in our set STRICTLY LESS than n's i-th digit: each commits the number to "< n from now on." Remaining `L-i-1` positions are unconstrained → `d^(L-i-1)` each. Add (count of smaller digits) × d^(L-i-1).
- Digit in our set EQUAL to n's i-th digit: maintain the tie; continue to position i+1.
- No digit equal to n's i-th digit: STOP (tie broken, no contribution from positions i+1..L-1 in the tied branch).

If the tie survives ALL positions, then n ITSELF is representable by our digit set → add 1.

---

## 5. The tie-tracking algorithm

```
L = number of digits in n
d = |digits|
count = 0

# Case 1
for k in 1..L-1: count += d^k

# Case 2
tie = true
for i in 0..L-1, while tie:
    ch = n's i-th digit
    lesser = number of digits in set < ch
    count += lesser * d^(L-i-1)
    if ch in digits: continue   # tie persists
    else: tie = false

if tie: count += 1   # n itself representable

return count
```

O(L · d) work (or O(L) with binary search on the sorted set). For n ≤ 10^9, L ≤ 10 — practically O(1).

---

## 6. Code

**C++:**

```cpp
int atMostNGivenDigitSet(vector<string>& digits, int n) {
    string N = to_string(n);
    int L = N.size();
    int d = digits.size();
    int count = 0;

    // Case 1: shorter numbers
    int power = 1;
    for (int k = 1; k < L; ++k) {
        power *= d;
        count += power;
    }

    // Case 2: same length, possibly tied
    bool tie = true;
    for (int i = 0; i < L && tie; ++i) {
        char ch = N[i];
        int lesser = 0;
        bool match = false;
        for (const string& dgt : digits) {
            if (dgt[0] < ch) lesser++;
            else if (dgt[0] == ch) match = true;
            else break;   // sorted, can stop
        }
        // Compute d^(L-i-1)
        int p = 1;
        for (int x = 0; x < L - i - 1; ++x) p *= d;
        count += lesser * p;
        if (!match) tie = false;
    }

    if (tie) count += 1;
    return count;
}
```

Complexity: **O(L · d)** time, **O(1)** space.

---

## 7. Trace it

**`digits = ["1","3","5","7"], n = 100`:** L = 3, d = 4.

Case 1: `4 + 16 = 20`.

Case 2:
- i=0, ch='1'. lesser = 0 (no digit < 1). match = "1" matches. count += 0 · 16 = 0. tie continues.
- i=1, ch='0'. lesser = 0. match = none. count += 0 · 4 = 0. tie BREAKS.

Total = 20 + 0 = **20**.  ✓

**`digits = ["1","3","5","7"], n = 555`:** L = 3.

Case 1: 4 + 16 = 20.

Case 2:
- i=0, ch='5'. lesser = 2 ('1', '3'). match = "5". count += 2 · 16 = 32. tie continues.
- i=1, ch='5'. lesser = 2. match = "5". count += 2 · 4 = 8. tie continues.
- i=2, ch='5'. lesser = 2. match = "5". count += 2 · 1 = 2. tie continues.
- End. tie survived → count += 1 (n=555 is "555", representable).

Case 2 total: 32 + 8 + 2 + 1 = 43.

Grand total: 20 + 43 = **63**.

---

## 8. Common pitfalls

1. **Forgetting the "+1 for n itself."** If the tie survives all positions, n IS representable → add 1.
2. **Counting digits "<= n[i]" instead of "< n[i]" for the lesser branch.** The EQUAL case maintains the tie, so it's not counted as lesser.
3. **Reading n's digits from least to most significant.** Walk from MOST significant (left).
4. **Allowing '0' in the digit set.** The problem typically excludes '0' (numbers can't have leading zeros).
5. **Computing `d^(L-i-1)` redundantly.** Cache powers, or note that as i increases, divide by d.
6. **Off-by-one on the for-else (Python).** In C++, use a `tie` boolean.

---

## 9. The shape — digit DP

The pattern: **count numbers up to N with digit constraints by iterating positions and tracking "tied with N."**

| Problem | Constraint |
|---|---|
| **This problem** | digits from a fixed set |
| Number of Digit One | count occurrences of digit 1 |
| Count Numbers with Unique Digits | no repeated digits |
| Confusing Number II | rotation-invariant digits |
| Nth Magical Number | divisible by a or b |
| Beautiful Arrangement | digit-constraint counting |

**Pattern to internalize:**

> "Digit DP: state = (position, tight_to_N, started_yet, ...). Iterate digit positions. For each, sum 'this digit < N's digit' branches (free for the rest) and continue in the 'tight' branch."

The variant here is a SIMPLIFIED digit DP because there's no "free zeros allowed" and no complex per-digit state.

---

> **Self-check — the question to ask next time.**
>
> When counting numbers in `[1, N]` with digit-property constraints:
>
> > **"Digit DP: split by digit length. For shorter lengths, count freely. For same length, walk N's digits left to right, splitting 'lesser' (free for the rest) vs 'tied' (continue)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Numbers_at_Most_N_Given_Digit_Set.md`](../Numbers_at_Most_N_Given_Digit_Set.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Decode_Ways.md`](./Decode_Ways.md), [`Climbing_Stairs.md`](./Climbing_Stairs.md).
  - **Topic complete — next: Segment Tree / Range Queries.**
