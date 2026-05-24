# Largest Multiple of Three — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Largest_Multiple_of_Three.md`](../Largest_Multiple_of_Three.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/largest-multiple-of-three/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: divisibility by 3 = DIGIT SUM divisible by 3. Group digits by residue mod 3; if total sum has residue r, REMOVE the FEWEST digits with appropriate residues to fix it. Then sort descending.**

**Map of this file (9 sections):**

1. Read the problem
2. The mod-3 digit sum rule
3. Strategy: remove fewest digits
4. The two residue cases
5. Code
6. Trace it
7. Leading zeros edge case
8. Common pitfalls
9. The shape — greedy modular adjustment

---

## 1. Read the problem

Array of digits (0..9). Pick a subset and arrange them into the LARGEST possible number divisible by 3. Return as a string. Empty string if impossible. Special case: all-zero answer returns "0".

**Example:** `digits = [8, 6, 7, 1, 0]` → sum=22 (residue 1). Remove smallest residue-1 digit (1) → {8, 7, 6, 0} → arrange descending → **"8760"**.

---

## 2. The mod-3 digit sum rule

> **Mini-refresher: a number is divisible by 3 ⇔ the sum of its digits is divisible by 3.**
>
> So pick a subset of digits whose SUM is divisible by 3, then arrange them largest-first.

This reduces the problem to "subset sum modulo 3" + sorting.

---

## 3. Strategy: remove fewest digits

To maximize the number, USE AS MANY DIGITS AS POSSIBLE. So:

1. If total sum is divisible by 3: use ALL digits.
2. Else, remove the FEWEST and SMALLEST digits to fix the residue.

---

## 4. The two residue cases

Group digits by residue mod 3:
- residue 0: {0, 3, 6, 9}.
- residue 1: {1, 4, 7}.
- residue 2: {2, 5, 8}.

Let `r = total_sum mod 3`.

> **Mini-refresher: removal options by residue.**
>
> - **r = 1:** remove ONE digit with residue 1. If none: remove TWO digits with residue 2 (since 2+2 ≡ 4 ≡ 1 mod 3).
> - **r = 2:** remove ONE digit with residue 2. If none: remove TWO digits with residue 1.

ALWAYS prefer the 1-digit removal over the 2-digit removal. Within a residue group, remove the SMALLEST values.

---

## 5. Code

**C++:**

```cpp
string largestMultipleOfThree(vector<int>& digits) {
    int sum = 0;
    for (int d : digits) sum += d;

    vector<int> g0, g1, g2;
    for (int d : digits) {
        if (d % 3 == 0) g0.push_back(d);
        else if (d % 3 == 1) g1.push_back(d);
        else g2.push_back(d);
    }
    sort(g1.begin(), g1.end());   // ascending: smallest first
    sort(g2.begin(), g2.end());

    int r = sum % 3;
    auto pop_smallest = [&](vector<int>& g, int k) {
        for (int i = 0; i < k && !g.empty(); ++i) g.erase(g.begin());
    };

    if (r == 1) {
        if (!g1.empty()) pop_smallest(g1, 1);
        else pop_smallest(g2, 2);
    } else if (r == 2) {
        if (!g2.empty()) pop_smallest(g2, 1);
        else pop_smallest(g1, 2);
    }

    vector<int> all;
    all.insert(all.end(), g0.begin(), g0.end());
    all.insert(all.end(), g1.begin(), g1.end());
    all.insert(all.end(), g2.begin(), g2.end());
    sort(all.rbegin(), all.rend());

    if (all.empty()) return "";
    if (all[0] == 0) return "0";   // all zeros

    string result;
    for (int d : all) result += char('0' + d);
    return result;
}
```

Complexity: **O(n log n)** time (sort dominates), **O(n)** space.

---

## 6. Trace it

`digits = [8, 6, 7, 1, 0]`. sum = 22, r = 1.

- g0 = {6, 0}, g1 = {1, 7} (sorted: {1, 7}), g2 = {8}.
- r=1, g1 non-empty → pop smallest (1). g1 = {7}.
- Combine: {6, 0, 7, 8}. Sort descending: [8, 7, 6, 0].
- Return **"8760"**.  ✓

`[1, 1, 1, 1]`: sum=4, r=1. g1 = {1,1,1,1}. Pop one. g1 = {1,1,1}. Combine = [1,1,1]. Return "111".

`[0,0,0,0]`: sum=0, r=0. All zeros → return "0".

---

## 7. Leading zeros edge case

If all remaining digits are 0, the answer is `"0"` not `"0000"`. Check `all[0] == 0` after sorting descending — if true, all are zero.

---

## 8. Common pitfalls

1. **Removing the BIGGEST digit by residue.** We want to KEEP big digits — remove SMALLEST in each residue group.
2. **Greedily removing one digit per pass.** Sometimes 2 same-residue removals are required (when no opposite-residue exists). Plan accordingly.
3. **Returning "0000" for all-zero input.** Strip leading zeros to a single "0".
4. **Trying to enumerate subsets.** Exponential. The greedy mod-3 logic gives O(n log n).
5. **Sorting digits all the way before residue-removal.** Sort each residue group ascending (for smallest-first removal), then sort the FINAL combined list descending.

---

## 9. The shape — greedy modular adjustment

The pattern: **divisibility-by-k problem → group elements by residue mod k → remove or pick the FEWEST to fix the residue.**

| Problem | Modulus |
|---|---|
| **This problem** | 3 (digit sum rule) |
| Largest Multiple of 9 | 9 (digit sum rule, same trick) |
| Sum Divisible by P (LC 1590) | p (remove smallest subarray with target residue) |
| Last Stone Weight II | sum residues for partition |
| Make Sum Divisible by P | modular running sums |

**Pattern to internalize:**

> "Divisibility-by-k problem? Group by residue mod k. To fix a residue, remove the FEWEST and SMALLEST elements that sum to the offending residue."

---

> **Self-check — the question to ask next time.**
>
> When the problem asks for the largest number with a divisibility property:
>
> > **"Use the divisibility rule (digit sum for 3, 9). Group by residue. Remove FEWEST smallest to fix. Sort remaining descending."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Largest_Multiple_of_Three.md`](../Largest_Multiple_of_Three.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Four_Divisors.md`](./Four_Divisors.md), [`Total_Number_of_Divisors_of_a_Given_Number.md`](./Total_Number_of_Divisors_of_a_Given_Number.md).
  - Coming next: [`Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md`](./Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md), [`Pow_x_n.md`](./Pow_x_n.md).
