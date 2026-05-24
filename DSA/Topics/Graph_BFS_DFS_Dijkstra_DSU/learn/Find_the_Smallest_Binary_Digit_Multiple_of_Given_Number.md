# Find the Smallest Binary Digit Multiple of Given Number — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md`](../Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/dsa/find-the-smallest-binary-digit-multiple-of-given-number/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: numbers can be huge, but REMAINDERS mod n are bounded by n. BFS over remainder states (transition: append 0 or 1) finds the smallest "binary-digit" multiple in O(n). State space ≤ n; pigeonhole guarantees a solution exists.**

**Map of this file (9 sections):**

1. Read the problem
2. Why a solution always exists
3. The brute-force enumeration
4. The remainder-state BFS
5. Code
6. Trace it
7. Why BFS gives the smallest
8. Common pitfalls
9. The shape — BFS on a state-space modulo

---

## 1. Read the problem

Given positive integer n, return the smallest positive multiple of n whose decimal digits are ONLY 0 and 1.

**Examples:**

- n = 2 → smallest = **10** (digits 1, 0).
- n = 3 → smallest = **111** (3 × 37 = 111).
- n = 7 → smallest = **1001001** (7 × 143).

---

## 2. Why a solution always exists

> **Mini-refresher: Pigeonhole guarantees a binary-digit multiple of any n.**
>
> Consider the repunits 1, 11, 111, ..., 11...1 (n+1 of them). Each has a remainder mod n in {0, 1, ..., n-1}. By pigeonhole, TWO of them share a remainder. Their difference is a binary-digit number (1's followed by 0's) divisible by n.
>
> So a binary-digit multiple always exists for any n.

---

## 3. The brute-force enumeration

Iterate: 1, 10, 11, 100, 101, 110, 111, 1000, ... (binary representations interpreted as decimal). Test each for divisibility by n; return the first that works.

Works in theory, but the numbers grow exponentially — for n=7 the answer has 7 digits, fine, but for larger n we exceed 64-bit quickly.

---

## 4. The remainder-state BFS

> **Mini-refresher: track only the REMAINDER, not the full number.**
>
> Define a state graph where:
> - **Nodes** are remainders 0, 1, ..., n-1.
> - From state r, two transitions: append `'0'` → new remainder `(10r) mod n`; append `'1'` → `(10r + 1) mod n`.
> - **Start:** state `1 mod n` with string `"1"` (every candidate has a leading 1).
> - **Goal:** state `0` (divisible).
>
> BFS finds the shortest path, which gives the FEWEST-DIGIT answer, which is the SMALLEST in magnitude.

Each remainder is visited at most once → O(n) work.

---

## 5. Code

**C++:**

```cpp
string smallestBinaryDigitMultiple(int n) {
    if (n == 1) return "1";

    queue<pair<int, string>> q;
    vector<bool> visited(n, false);
    q.push({1 % n, "1"});
    visited[1 % n] = true;

    while (!q.empty()) {
        auto [r, s] = q.front(); q.pop();
        if (r == 0) return s;
        for (char d : {'0', '1'}) {
            int nr = (r * 10 + (d - '0')) % n;
            if (!visited[nr]) {
                visited[nr] = true;
                q.push({nr, s + d});
            }
        }
    }
    return "";   // unreachable
}
```

**Python:**

```python
from collections import deque

def smallestBinaryDigitMultiple(n):
    if n == 1:
        return "1"
    q = deque([(1 % n, "1")])
    visited = {1 % n}
    while q:
        r, s = q.popleft()
        if r == 0:
            return s
        for d in ('0', '1'):
            nr = (r * 10 + int(d)) % n
            if nr not in visited:
                visited.add(nr)
                q.append((nr, s + d))
    return ""
```

Complexity: **O(n)** time (at most n distinct remainders), **O(n)** space.

For very large n, storing the full string per queue entry can bloat memory; use parent pointers and reconstruct only on goal.

---

## 6. Trace it

**n = 3:**

```
Start: queue = [(1, "1")]. visited = {1}.

Pop (1, "1"). r=1.
  '0': nr = (10 + 0) % 3 = 1. Visited. Skip.
  '1': nr = 11 % 3 = 2. Push (2, "11"). visited = {1, 2}.

Pop (2, "11"). r=2.
  '0': nr = 20 % 3 = 2. Visited. Skip.
  '1': nr = 21 % 3 = 0. Push (0, "111"). visited = {0, 1, 2}.

Pop (0, "111"). r=0. Return "111".  ✓
```

Notice we NEVER computed the number 111 itself — only remainders mod 3.

---

## 7. Why BFS gives the smallest

> **Mini-refresher: BFS minimizes digit count → minimizes magnitude.**
>
> Each transition appends one digit. BFS visits states in order of increasing digit count. The first goal-state pop gives the FEWEST-DIGIT solution.
>
> Among numbers with a leading 1, fewer digits → smaller number. So fewest digits = smallest answer.

If we enqueue `'0'` BEFORE `'1'` at each step, among equal-length candidates BFS finds the lexicographically smallest digit string — also numerically smallest given the leading 1.

---

## 8. Common pitfalls

1. **Computing the actual number, overflowing.** Store the remainder, not the value.
2. **Starting at state 0 with string "".** That returns "" — empty, not a positive multiple. Start at state `1 % n` with string `"1"`.
3. **DFS instead of BFS.** Finds *some* multiple, not the smallest.
4. **Forgetting `visited`.** State space cycles forever without it.
5. **Returning the digit count instead of the string.** Read the problem carefully.
6. **Edge case n=1.** Every number is a multiple of 1. The smallest binary-digit positive integer is 1. Handle separately.

---

## 9. The shape — BFS on a state-space modulo

The pattern: **state = compact invariant (here, remainder); transitions = bounded moves.**

| Problem | State | Transitions |
|---|---|---|
| **This problem** | remainder mod n | append digit |
| Open the Lock | 4-digit code | rotate one wheel ±1 |
| Water Jug Problem | (a, b) volumes | fill, empty, pour |
| Word Ladder | current word | change one letter |
| Minimum Steps to Reach Target Knight | knight position | 8 moves |
| Bus Routes | current stop | take a route |

**Pattern to internalize:**

> "When the actual values can be huge but the relevant state space is bounded, BFS over the state space. Track only the invariant; reconstruct the answer via parent pointers."

---

> **Self-check — the question to ask next time.**
>
> When you need the SMALLEST number satisfying some divisibility/property, ask:
>
> > **"Can I track REMAINDERS (or some compact invariant) instead of full numbers? BFS over the state space, append digits as transitions, parent-pointer reconstruction at the goal."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md`](../Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Open_the_Lock.md`](../../Sorting_Divide_and_Conquer/learn/Open_the_Lock.md), [`Shortest_Path_in_Binary_Matrix.md`](./Shortest_Path_in_Binary_Matrix.md).
  - Coming next: [`Minimum_Weight_Cycle.md`](./Minimum_Weight_Cycle.md).
