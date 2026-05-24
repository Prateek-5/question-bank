# Number of Good Pairs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Good_Pairs.md`](../Number_of_Good_Pairs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/number-of-good-pairs/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: for each value v appearing c times, the count of pairs is `C(c, 2) = c · (c-1) / 2`. Group by value, sum binomials. Or even slicker: running-count single-pass.**

**Map of this file (8 sections):**

1. Read the problem
2. Brute force
3. Group by value: C(c, 2)
4. Running-count one-pass
5. Code
6. Trace it
7. Common pitfalls
8. The shape — pair counting

---

## 1. Read the problem

Array `nums`. A "good pair" is `(i, j)` with `i < j` AND `nums[i] == nums[j]`. Return the count.

**Example:** `[1, 2, 3, 1, 1, 3]` → good pairs at (0,3), (0,4), (3,4), (2,5) → **4**.

---

## 2. Brute force

Two nested loops, count matches. O(n²). Works for small n.

---

## 3. Group by value: C(c, 2)

> **Mini-refresher: `C(c, 2) = c · (c-1) / 2`.**
>
> If a value appears `c` times, the number of unordered pairs of its occurrences is "choose 2 from c" = c · (c-1) / 2.
>
> Total good pairs = Σ over distinct values v of C(count[v], 2).

For `[1, 2, 3, 1, 1, 3]`: 1 appears 3 times, 3 appears 2 times. C(3, 2) + C(2, 2) = 3 + 1 = **4**.

This is THE combinatorial reflex worth burning in.

---

## 4. Running-count one-pass

> **Mini-refresher: at each element, add the count of PREVIOUS occurrences.**
>
> ```
> count = {}
> total = 0
> for x in nums:
>     total += count.get(x, 0)   # each previous v pairs with this v
>     count[x] = count.get(x, 0) + 1
> ```
>
> When we see the k-th occurrence of v, it forms k-1 new pairs with the previous k-1 occurrences.

Equivalent to `Σ C(c, 2)` (because 0 + 1 + 2 + ... + (c-1) = C(c, 2)).

---

## 5. Code

**C++ — running-count (slickest):**

```cpp
int numIdenticalPairs(vector<int>& nums) {
    unordered_map<int, int> count;
    int total = 0;
    for (int x : nums) {
        total += count[x];
        count[x]++;
    }
    return total;
}
```

**C++ — group then count:**

```cpp
int numIdenticalPairs(vector<int>& nums) {
    unordered_map<int, int> count;
    for (int x : nums) count[x]++;
    int total = 0;
    for (auto& [val, c] : count) total += c * (c - 1) / 2;
    return total;
}
```

Both **O(n)** time, O(distinct values) space.

---

## 6. Trace it

Running-count on `[1, 2, 3, 1, 1, 3]`:

- 1: count[1]=0, total += 0 → 0. count[1]=1.
- 2: total += 0 → 0. count[2]=1.
- 3: total += 0 → 0. count[3]=1.
- 1: count[1]=1, total += 1 → 1. count[1]=2.
- 1: count[1]=2, total += 2 → 3. count[1]=3.
- 3: count[3]=1, total += 1 → 4. count[3]=2.

Return **4**.  ✓

---

## 7. Common pitfalls

1. **Off-by-one with `c * (c - 1) / 2`.** For c = 1, this gives 0 (correct — single occurrence makes 0 pairs).
2. **Forgetting integer division.** In Python, use `//` (or rely on `c * (c-1)` being even — it always is for consecutive integers).
3. **Counting ordered pairs (i, j) instead of unordered.** "Good pair" here requires `i < j` → unordered.
4. **O(n²) brute force on huge arrays.** O(n) is the right tool.
5. **Adding before incrementing.** The running-count formula needs `total += count[x]` BEFORE `count[x]++`.

---

## 8. The shape — pair counting

The pattern: **for each (key, count), the number of pairs is C(count, 2).**

| Problem | Group by |
|---|---|
| **This problem** | equal value |
| Count Pairs Whose XOR is K | xor-key |
| Count Pairs Divisible by K | residue mod K |
| Two Sum (count) | complement value |
| Count Triplets satisfying X | three-tuple keys (C(c, 3)) |
| Equivalent Domino Pairs | sorted-tuple |

**Pattern to internalize:**

> "Counting pairs/triples with property X: group by the relevant invariant; per-group pairs is C(c, 2), triples is C(c, 3). Or running-count for one-pass."

---

> **Self-check — the question to ask next time.**
>
> When counting pairs sharing some property:
>
> > **"Group by the property's invariant. Each group of size c contributes C(c, 2) pairs. Single-pass running count also works."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Good_Pairs.md`](../Number_of_Good_Pairs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Self_Dividing_Numbers.md`](./Self_Dividing_Numbers.md), [`Lucky_Numbers_in_a_Matrix.md`](./Lucky_Numbers_in_a_Matrix.md), [`Subtract_Product_and_Sum_of_Digits.md`](./Subtract_Product_and_Sum_of_Digits.md).
  - Coming next: [`Max_Consecutive_Ones.md`](./Max_Consecutive_Ones.md), [`Number_of_Open_Doors.md`](./Number_of_Open_Doors.md), [`Total_Number_of_Divisors_of_a_Given_Number.md`](./Total_Number_of_Divisors_of_a_Given_Number.md).
