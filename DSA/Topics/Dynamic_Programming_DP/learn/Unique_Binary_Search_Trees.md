# Unique Binary Search Trees — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Unique_Binary_Search_Trees.md`](../Unique_Binary_Search_Trees.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/unique-binary-search-trees/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/unique-binary-search-trees/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: condition on the ROOT. With root = k-th smallest, left subtree has k-1 nodes and right has n-k nodes. Shape count depends only on the NUMBER of values (not their identities). C(n) = Σ C(k-1) · C(n-k) — Catalan numbers.**

**Map of this file (8 sections):**

1. Read the problem
2. Hand-count small cases
3. The "root choice" recurrence
4. Why shape count depends only on size
5. Code
6. Trace it
7. Catalan numbers connection
8. The shape — interval DP for counting

---

## 1. Read the problem

Given `n`, return the number of STRUCTURALLY UNIQUE BSTs with n nodes storing values 1..n.

**Examples:** n=1 → 1. n=2 → 2. n=3 → **5**. n=4 → 14. n=5 → 42.

---

## 2. Hand-count small cases

- **n=0:** the empty tree — count = 1 (one valid tree).
- **n=1:** single node, 1 tree.
- **n=2:** {1 root, 2 right} or {2 root, 1 left}. 2 trees.
- **n=3:** 5 trees (root = 1, 2, or 3; subtree shapes combine).

Sequence: 1, 1, 2, 5, 14, 42, ... — Catalan numbers.

---

## 3. The "root choice" recurrence

> **Mini-refresher: condition on the ROOT.**
>
> If the root is the k-th value (1 ≤ k ≤ n), then:
> - Left subtree has values 1..k-1 → k-1 nodes.
> - Right subtree has values k+1..n → n-k nodes.
> - Subtree shapes are INDEPENDENT — multiply.
>
> So `C(n) = Σ over k of C(k-1) · C(n-k)`.

This is the Catalan recurrence.

---

## 4. Why shape count depends only on size

The number of BST SHAPES on `m` consecutive values is the same regardless of which specific values they are. (BST shape is determined by relative order; the values are just labels.)

So `C(m)` only depends on `m`, not on the specific 1..m range. This is what makes the recurrence work.

---

## 5. Code

**C++:**

```cpp
int numTrees(int n) {
    vector<long long> C(n + 1, 0);
    C[0] = 1;
    for (int i = 1; i <= n; ++i) {
        for (int k = 1; k <= i; ++k) {
            C[i] += C[k - 1] * C[i - k];
        }
    }
    return (int)C[n];
}
```

**Python:**

```python
def numTrees(n):
    C = [0] * (n + 1)
    C[0] = 1
    for i in range(1, n + 1):
        for k in range(1, i + 1):
            C[i] += C[k - 1] * C[i - k]
    return C[n]
```

Complexity: **O(n²)** time, **O(n)** space.

---

## 6. Trace it

n = 4:
- C[0] = 1.
- C[1] = C[0]·C[0] = 1.
- C[2] = C[0]·C[1] + C[1]·C[0] = 1 + 1 = 2.
- C[3] = C[0]·C[2] + C[1]·C[1] + C[2]·C[0] = 2 + 1 + 2 = 5.
- C[4] = C[0]·C[3] + C[1]·C[2] + C[2]·C[1] + C[3]·C[0] = 5 + 2 + 2 + 5 = **14**.  ✓

---

## 7. Catalan numbers connection

The sequence 1, 1, 2, 5, 14, 42, 132, ... is the famous Catalan sequence. Other places it appears:

| Setting | What's counted |
|---|---|
| BST shapes | this problem |
| Balanced parens | sequences of n `(` and n `)` |
| Triangulations of polygon | (n+2)-gon |
| Lattice paths | non-crossing |
| Plane trees | n+1 nodes |

Closed form: `C_n = C(2n, n) / (n+1)`. The DP version is friendlier for typical n ≤ 19 (where it fits in int).

---

## 8. The shape — interval DP for counting

The pattern: **count combinatorial structures by SPLITTING on a chosen pivot.**

| Problem | Pivot |
|---|---|
| **This problem** | root value |
| Unique BSTs II (generate all) | same, plus actual tree construction |
| Burst Balloons | last balloon |
| Matrix Chain Multiplication | last multiplication |
| Optimal BST (weighted) | root with weighted depth |
| Stone Game variants | last move |

**Pattern to internalize:**

> "For counting/optimizing over combinatorial structures, fix the LAST/PIVOT decision. Recurse on the resulting sub-structures. Multiply for independent choices, sum across all pivot choices."

---

> **Self-check — the question to ask next time.**
>
> When counting structures parameterized by a size n:
>
> > **"Condition on a pivot (root, last action, split). Recurse on smaller sub-structures. Sum over pivot choices."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Unique_Binary_Search_Trees.md`](../Unique_Binary_Search_Trees.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Matrix_Chain_Multiplication.md`](./Matrix_Chain_Multiplication.md).
  - Coming next: [`Maximal_Rectangle.md`](./Maximal_Rectangle.md), [`Dungeon_Game.md`](./Dungeon_Game.md), [`Numbers_at_Most_N_Given_Digit_Set.md`](./Numbers_at_Most_N_Given_Digit_Set.md).
