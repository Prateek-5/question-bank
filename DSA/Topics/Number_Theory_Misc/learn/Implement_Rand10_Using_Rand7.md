# Implement Rand10() Using Rand7() — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Implement_Rand10_Using_Rand7.md`](../Implement_Rand10_Using_Rand7.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/implement-rand10-using-rand7/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/implement-rand10-using-rand7/description/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: REJECTION SAMPLING. Two rand7()s give 49 uniform outcomes; accept the first 40, reject the rest, map mod 10. Expected calls: 2.45. Can't simply scale or add — those bias the distribution.**

**Map of this file (8 sections):**

1. Read the problem
2. Why scaling and addition fail
3. The 49-uniform trick
4. Rejection sampling: take first 40
5. Code
6. Trace it
7. Expected number of calls
8. The shape — rejection sampling

---

## 1. Read the problem

You're given `rand7()` returning UNIFORM int in {1..7}. Implement `rand10()` returning UNIFORM int in {1..10}. Minimize expected rand7() calls.

---

## 2. Why scaling and addition fail

> **Mini-refresher: simple arithmetic on uniform RVs DOES NOT preserve uniformity.**
>
> - `rand7() + rand7()` is in {2..14} but PEAKED at 8 (most pairs sum to 8). Not uniform.
> - `(rand7() - 1) * 10 / 7 + 1` doesn't give 10 equally-likely values due to integer division and non-divisibility.
>
> You CAN'T scale a discrete uniform RV into another non-divisor range without bias.

---

## 3. The 49-uniform trick

> **Mini-refresher: two rand7()s = 49 equally-likely pairs.**
>
> Compute `value = (rand7() - 1) * 7 + rand7()` → uniform on {1..49}.
>
> Interpretation: a 2-digit base-7 number plus 1.

Now we have a uniform RV on 49 values. 49 isn't a multiple of 10, but 40 is.

---

## 4. Rejection sampling: take first 40

> **Mini-refresher: REJECT samples in the "extra" range; RESAMPLE.**
>
> - If `value <= 40`: accept. Return `((value - 1) % 10) + 1` — uniform on {1..10} (each output has 4 of the 40 pre-images).
> - If `value > 40`: REJECT. Retry from scratch.
>
> Rejection doesn't BIAS the output — it just extends expected runtime.

Accepted range (1..40) divides evenly by 10 → 4 pre-images per output → uniform.

---

## 5. Code

**C++:**

```cpp
int rand10() {
    while (true) {
        int a = rand7();
        int b = rand7();
        int value = (a - 1) * 7 + b;   // 1..49
        if (value <= 40) {
            return ((value - 1) % 10) + 1;
        }
        // value in {41..49}: reject and retry
    }
}
```

**Python:**

```python
def rand10():
    while True:
        a = rand7()
        b = rand7()
        value = (a - 1) * 7 + b
        if value <= 40:
            return ((value - 1) % 10) + 1
```

---

## 6. Trace it

- rand7() returns 3, 5 → value = 2·7 + 5 = 19. Accept. Result = ((19-1) % 10) + 1 = **9**.
- rand7() returns 6, 5 → value = 40. Accept. Result = **10**.
- rand7() returns 7, 6 → value = 48. Reject. Retry.

---

## 7. Expected number of calls

Each iteration: 2 rand7() calls. Acceptance probability: 40/49.

Expected iterations = 49/40 ≈ 1.225.

Expected rand7() calls = 2 × 1.225 = **~2.45**.

**Optimization:** the rejected 9 values (41..49) carry 9 uniform outcomes. We can map them to 1..9 and combine with another rand7() to extract more samples → reduces calls to ~2.2. Usually overkill in interviews.

---

## 8. The shape — rejection sampling

The pattern: **sample uniformly from a LARGER space, then ACCEPT only a divisor-friendly subset.**

| Problem | Source → Target |
|---|---|
| **This problem** | rand7 → rand10 (49 → 40 → 10) |
| Generate uniform in a disk | rand in unit square, reject outside circle |
| Shuffle a list using biased RNG | rejection on each step |
| Generate uniform on {1..n} from {1..m} (n not dividing m^k) | rejection in m^k space |
| Sampling from arbitrary distributions | importance / rejection sampling |
| Monte Carlo integration | reject samples outside target region |

**Pattern to internalize:**

> "Can't directly sample uniform on N from a different source? Sample uniform on a multiple of N (via combining sources), accept only the first N·k values, map mod N. O(1) expected calls."

---

> **Self-check — the question to ask next time.**
>
> When given a biased uniform RNG and asked for a different uniform:
>
> > **"Combine calls into a larger uniform space. Find the largest multiple of N ≤ that. Accept-or-reject. Map accepted values mod N."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Implement_Rand10_Using_Rand7.md`](../Implement_Rand10_Using_Rand7.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Digit_One.md`](./Number_of_Digit_One.md), [`Divisor_Game.md`](./Divisor_Game.md), [`Memoization_DP_Basics.md`](./Memoization_DP_Basics.md).
  - **Topic complete — DSA v2 migration FINISHED (22/22 topics, all sub-problems migrated).**
