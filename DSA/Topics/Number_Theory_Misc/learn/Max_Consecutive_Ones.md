# Max Consecutive Ones — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Max_Consecutive_Ones.md`](../Max_Consecutive_Ones.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/max-consecutive-ones/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~8 minutes. **The lesson: one-pass streak counter. Increment on 1, RESET on 0, track running max. O(n) time, O(1) space.**

**Map of this file (6 sections):**

1. Read the problem
2. The streak idea
3. Code
4. Trace it
5. Common pitfalls
6. The shape — single-pass streak counting

---

## 1. Read the problem

Binary array. Return the LENGTH of the LONGEST run of consecutive 1s.

**Examples:**

- `[1, 1, 0, 1, 1, 1]` → runs of 1s have lengths 2 and 3 → **3**.
- `[1, 0, 1, 1, 0, 1]` → **2**.
- `[0, 0, 0]` → **0**.

---

## 2. The streak idea

> **Mini-refresher: track a CURRENT streak and the MAX seen.**
>
> Walk left-to-right:
> - On `1`: extend current streak, update max.
> - On `0`: RESET current streak to 0.
>
> Two counters; one pass.

---

## 3. Code

**C++:**

```cpp
int findMaxConsecutiveOnes(vector<int>& nums) {
    int cur = 0, best = 0;
    for (int x : nums) {
        if (x == 1) {
            cur++;
            best = max(best, cur);
        } else {
            cur = 0;
        }
    }
    return best;
}
```

Complexity: **O(n)** time, **O(1)** space.

---

## 4. Trace it

`[1, 1, 0, 1, 1, 1]`:

```
1: cur=1, best=1.
1: cur=2, best=2.
0: cur=0, best=2.
1: cur=1, best=2.
1: cur=2, best=2.
1: cur=3, best=3.
```

Return **3**.  ✓

---

## 5. Common pitfalls

1. **Decrementing on 0 instead of resetting.** A single 0 ENDS the streak entirely — `cur = 0`, not `cur--`.
2. **Updating `best` only at the end of the array.** Update inside the loop after each increment so transient peaks aren't lost.
3. **Forgetting to handle all-zero arrays.** `best = 0` initialized correctly handles this.
4. **Using sliding window unnecessarily.** No flips allowed here → just a counter.

---

## 6. The shape — single-pass streak counting

The pattern: **scan + running counter + reset on boundary + track max.**

| Problem | Reset condition |
|---|---|
| **This problem** | element is 0 |
| Longest run of any char | element changes |
| Longest increasing run | element ≤ previous |
| Longest valid parentheses (variant) | invalid char |
| Max Consecutive Ones III | sliding window (more state) |

**Pattern to internalize:**

> "Longest valid run = single counter + reset on boundary + track max. O(n), O(1)."

---

> **Self-check — the question to ask next time.**
>
> When asked for the longest run of some condition:
>
> > **"One pass. Increment counter while condition holds, reset on boundary, update max."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Max_Consecutive_Ones.md`](../Max_Consecutive_Ones.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Good_Pairs.md`](./Number_of_Good_Pairs.md).
  - Coming next: [`Number_of_Open_Doors.md`](./Number_of_Open_Doors.md), [`Total_Number_of_Divisors_of_a_Given_Number.md`](./Total_Number_of_Divisors_of_a_Given_Number.md).
