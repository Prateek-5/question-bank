# Number of Open Doors — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Open_Doors.md`](../Number_of_Open_Doors.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/problems/number-of-open-doors1552/1

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: door d gets toggled ONCE per divisor of d. It ends OPEN iff toggled odd times iff d is a PERFECT SQUARE. Count of perfect squares ≤ N is `floor(√N)`. Same shape as Bulb Switcher.**

**Map of this file (7 sections):**

1. Read the problem
2. Toggles = divisor count
3. Why perfect squares have ODD divisors
4. The closed form
5. Code
6. Common pitfalls
7. The shape — divisor-parity reasoning

---

## 1. Read the problem

N doors numbered 1..N, all initially CLOSED. Pass i (for i = 1..N): toggle every door divisible by i. Return the number of doors OPEN at the end.

**Examples:** N = 5 → **2** (doors 1, 4). N = 10 → 3. N = 100 → 10.

---

## 2. Toggles = divisor count

Door d is toggled on pass i iff `i divides d`. Number of toggles = number of divisors of d.

Door ends OPEN iff toggled an ODD number of times.

So we need to count integers ≤ N with an odd divisor count.

---

## 3. Why perfect squares have ODD divisors

> **Mini-refresher: divisors pair up via (d, n/d).**
>
> For each divisor x of n, n/x is also a divisor. Pairs are distinct UNLESS x = n/x (i.e., x² = n).
>
> So divisors come in PAIRS, except for the case x = √n (only possible when n is a PERFECT SQUARE).
>
> Result: divisor count is EVEN for non-squares, ODD for perfect squares.

---

## 4. The closed form

Perfect squares ≤ N: 1², 2², ..., k² where k² ≤ N. Count = `floor(√N)`.

So answer = `floor(√N)`.

For N = 100: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100 → 10 perfect squares.

---

## 5. Code

**C++ — robust integer sqrt:**

```cpp
int numberOfOpenDoors(int N) {
    int r = (int)sqrt((double)N);
    while ((long long)(r + 1) * (r + 1) <= N) r++;
    while ((long long)r * r > N) r--;
    return r;
}
```

**Python:**

```python
import math
def numberOfOpenDoors(N):
    return math.isqrt(N)
```

Complexity: **O(1)** time, **O(1)** space.

---

## 6. Common pitfalls

1. **Simulating all N passes.** O(N²) — wasteful when O(1) is possible.
2. **Floating-point sqrt for large N.** Can be off by 1 due to rounding. Use a corrective loop OR Python's `math.isqrt`.
3. **Treating "open" as starting state.** Doors start CLOSED here. Bulb Switcher variants may differ — read the problem carefully.
4. **Forgetting that 1 is a perfect square.** 1² = 1, so door 1 is open.

---

## 7. The shape — divisor-parity reasoning

The pattern: **count integers with odd divisor count = count perfect squares.**

| Problem | Mapping |
|---|---|
| **This problem** | doors → perfect squares ≤ N |
| Bulb Switcher (LC 319) | same |
| Reach a Number (LC 754) | triangular numbers parity |
| Find Smallest Common Element | divisor reasoning |
| Square root computation | integer sqrt |

**Pattern to internalize:**

> "When a problem counts toggles via divisors, the answer often reduces to PERFECT SQUARES — odd-divisor-count integers. Count via floor(√N), O(1)."

---

> **Self-check — the question to ask next time.**
>
> When a problem says "toggle once per multiple/divisor":
>
> > **"Count of toggles = divisor count. ODD divisors ⇔ perfect square. Answer = floor(√N)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Open_Doors.md`](../Number_of_Open_Doors.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Bulb_Switcher.md`](../../Greedy/learn/Bulb_Switcher.md), [`Max_Consecutive_Ones.md`](./Max_Consecutive_Ones.md).
  - Coming next: [`Total_Number_of_Divisors_of_a_Given_Number.md`](./Total_Number_of_Divisors_of_a_Given_Number.md), [`Four_Divisors.md`](./Four_Divisors.md).
