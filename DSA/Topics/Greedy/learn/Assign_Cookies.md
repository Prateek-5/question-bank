# Assign Cookies — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Assign_Cookies.md`](../Assign_Cookies.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/assign-cookies/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: SORT both sides + TWO POINTERS to match smallest greed with smallest sufficient cookie. The exchange argument proves greedy is optimal.**

**Map of this file (8 sections):**

1. Read the problem
2. The greedy intuition
3. Two-pointer sweep
4. The exchange-argument correctness proof
5. Code
6. Trace it
7. Common pitfalls
8. The shape — sort + two-pointer match

---

## 1. Read the problem

Children with greed factors `g`, cookies with sizes `s`. Each child can receive at most one cookie, each cookie can go to at most one child. Child i is content iff their cookie has size ≥ g[i]. Maximize the number of content children.

**Examples:**

- `g = [1, 2, 3], s = [1, 1]` → can only satisfy child 0 → **1**.
- `g = [1, 2], s = [1, 2, 3]` → satisfy both → **2**.

---

## 2. The greedy intuition

> **Mini-refresher: match SMALLEST greed with SMALLEST sufficient cookie.**
>
> If you have a tiny cookie, give it to the least-greedy child who's still satisfied by it. This preserves bigger cookies for greedier children who might actually NEED them.
>
> The wasteful alternative — giving a big cookie to a low-greed child — leaves no cookie for someone who can't be satisfied by a small one.

---

## 3. Two-pointer sweep

After sorting both arrays ascending:
- `i` iterates over children.
- `j` iterates over cookies.

For each cookie j, if it satisfies child i, MATCH and advance both. Otherwise, the cookie is too small for child i — discard it and try the next bigger one.

```
sort(g); sort(s)
i = 0, j = 0
while i < |g| and j < |s|:
    if s[j] >= g[i]:
        i += 1   # child satisfied
    j += 1       # consume cookie either way
return i
```

---

## 4. The exchange-argument correctness proof

> **Mini-refresher: exchange argument.**
>
> Suppose optimal OPT differs from greedy. Find the first position where they diverge.
>
> - If OPT gave child c a BIGGER cookie than greedy did: swap to use the smaller cookie. The same child is still satisfied; greedy's leftover larger cookie can now help OPT's next child as well.
> - If OPT assigned cookie that greedy reserved for a later child: same kind of swap.
>
> Each swap leaves OPT's content-count ≥ before. Repeating, we transform OPT into greedy without losing children. So greedy ≥ OPT → greedy is optimal.

---

## 5. Code

**C++:**

```cpp
int findContentChildren(vector<int>& g, vector<int>& s) {
    sort(g.begin(), g.end());
    sort(s.begin(), s.end());
    int i = 0, j = 0;
    while (i < (int)g.size() && j < (int)s.size()) {
        if (s[j] >= g[i]) i++;
        j++;
    }
    return i;
}
```

**Python:**

```python
def findContentChildren(g, s):
    g.sort()
    s.sort()
    i = j = 0
    while i < len(g) and j < len(s):
        if s[j] >= g[i]:
            i += 1
        j += 1
    return i
```

Complexity: **O(n log n + m log m)** time (sorts dominate), **O(1)** extra space.

---

## 6. Trace it

**`g = [1, 2, 3], s = [1, 1]`:**

```
Sorted: g = [1, 2, 3], s = [1, 1].

i=0, j=0: s[0]=1 ≥ g[0]=1. Match. i=1, j=1.
i=1, j=1: s[1]=1 ≥ g[1]=2? No. j=2.
j=2: out of bounds. Exit.

Return i = 1.  ✓
```

**`g = [1, 2], s = [1, 2, 3]`:**

```
Sorted: g = [1, 2], s = [1, 2, 3].

i=0, j=0: 1 ≥ 1. Match. i=1, j=1.
i=1, j=1: 2 ≥ 2. Match. i=2, j=2.
i=2: out of bounds.

Return i = 2.  ✓
```

---

## 7. Common pitfalls

1. **Sorting only one side.** Both must be sorted for the two-pointer logic to find the smallest sufficient match.
2. **Advancing `j` only on match.** If you don't advance j on mismatch, infinite loop.
3. **Advancing `i` on mismatch.** Skips children who could be satisfied by a later (bigger) cookie.
4. **Sorting descending.** Either direction can work with adapted code, but match the loop logic to the sort direction.
5. **Comparing `s[j] > g[i]` instead of `>=`.** A cookie of size exactly equal to greed should satisfy the child.

---

## 8. The shape — sort + two-pointer match

The pattern: **sort both sequences; greedy pair from one end.**

| Problem | What's matched |
|---|---|
| **This problem** | children ↔ cookies |
| Boats to Save People | lightest + heaviest fits? |
| Two Sum II (sorted) | move pointers to hit target |
| Container With Most Water | shorter side moves in |
| Minimum Add to Make Parens Valid | match `(` and `)` |
| Merge Sorted Arrays | walk both arrays |

**Pattern to internalize:**

> "When two sorted sequences need matching under some inequality, sort both, walk with two pointers, match smallest to smallest. The exchange argument proves optimality."

---

> **Self-check — the question to ask next time.**
>
> When you need to match items from two sets under an inequality constraint, ask:
>
> > **"Can I sort both, then sweep two pointers? Smallest matches smallest sufficient — exchange argument confirms optimal."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Assign_Cookies.md`](../Assign_Cookies.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Distribute_Candies.md`](./Distribute_Candies.md), [`Maximum_Product_of_Three_Numbers.md`](./Maximum_Product_of_Three_Numbers.md), [`Maximize_Sum_After_K_Negations.md`](./Maximize_Sum_After_K_Negations.md).
