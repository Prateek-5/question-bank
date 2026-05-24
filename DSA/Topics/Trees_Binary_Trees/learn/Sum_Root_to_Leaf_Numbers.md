# Sum Root to Leaf Numbers — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Sum_Root_to_Leaf_Numbers.md`](../Sum_Root_to_Leaf_Numbers.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/sum-root-to-leaf-numbers/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: DFS with an ACCUMULATOR — each new digit DOUBLES (×10) the running number and adds the digit. Horner's method on a tree.** **Read [`Path_Sum.md`](./Path_Sum.md) first** for the accumulator pattern.

**Map of this file (7 short sections):**

1. Read the problem
2. How concatenation becomes arithmetic
3. The DFS recurrence
4. Code
5. Trace it
6. Common pitfalls
7. The shape — Horner's on a tree

---

## 1. Read the problem

Given a binary tree where each node holds a digit `0-9`, each root-to-leaf path forms a number by concatenating digits. Return the **TOTAL SUM** of all such numbers.

**Example:**
```
    4
   / \
  9   0
 / \
5   1
```

Paths:
- `4 → 9 → 5` = 495
- `4 → 9 → 1` = 491
- `4 → 0` = 40

Sum = 495 + 491 + 40 = **1026**.

---

## 2. How concatenation becomes arithmetic

> **Mini-refresher: digit concatenation via Horner's method.**
>
> To build the number 495 from digits 4, 9, 5:
> - Start at 0.
> - See 4: `0 * 10 + 4 = 4`.
> - See 9: `4 * 10 + 9 = 49`.
> - See 5: `49 * 10 + 5 = 495`.
>
> Each digit DOUBLES (×10) the running value, then ADDS the new digit.
>
> Formal: `current = current * 10 + digit`. This is HORNER'S METHOD for polynomial evaluation at x=10.

As we walk the tree top-down, we ACCUMULATE the number by applying this formula at each step.

---

## 3. The DFS recurrence

```
def dfs(node, current):
    if node is null: return 0
    current = current * 10 + node.val
    if node is leaf: return current     # path complete; contribute
    return dfs(node.left, current) + dfs(node.right, current)
```

Initial: `dfs(root, 0)`.

**Reading the recurrence:**
- At null: return 0 (no path; don't contribute).
- At a leaf: the accumulated number IS a complete root-to-leaf number — return it.
- At internal: continue to children with the updated `current`; sum their contributions.

The OUTER `dfs(root, 0)` returns the total sum across all root-to-leaf paths.

---

## 4. Code

**C++:**

```cpp
int sumNumbers(TreeNode* root, int cur = 0) {
    if (!root) return 0;
    cur = cur * 10 + root->val;
    if (!root->left && !root->right) return cur;
    return sumNumbers(root->left, cur) + sumNumbers(root->right, cur);
}
```

Six lines. The default arg `cur = 0` handles the initial call.

**Python:**

```python
def sumNumbers(root):
    def dfs(node, current):
        if not node: return 0
        current = current * 10 + node.val
        if not node.left and not node.right:
            return current
        return dfs(node.left, current) + dfs(node.right, current)
    return dfs(root, 0)
```

**JavaScript:**

```javascript
function sumNumbers(root, cur = 0) {
    if (!root) return 0;
    cur = cur * 10 + root.val;
    if (!root.left && !root.right) return cur;
    return sumNumbers(root.left, cur) + sumNumbers(root.right, cur);
}
```

Complexity: **O(n) time, O(h) space.**

---

## 5. Trace it

**Tree:**
```
    4
   / \
  9   0
 / \
5   1
```

```
dfs(4, 0):
  cur = 4. Not leaf.
  dfs(9, 4):
    cur = 49. Not leaf.
    dfs(5, 49):
      cur = 495. LEAF. Return 495.
    dfs(1, 49):
      cur = 491. LEAF. Return 491.
    Return 495 + 491 = 986.
  dfs(0, 4):
    cur = 40. LEAF. Return 40.
  Return 986 + 40 = 1026.
```

Total: **1026**. ✓

The accumulator `cur` carries the partial number; each leaf "commits" it to the sum.

---

## 6. Common pitfalls

1. **Building digits as a STRING then converting.** Works but wasteful — use the arithmetic accumulation.

2. **Forgetting the leaf check.** Internal-node contributions would double-count.

3. **Using `+=` on a global** instead of returning values up. Cleaner to return.

4. **Integer overflow.** For very deep trees with maxed-out digits, the number could exceed 32-bit. Use `long long` if depth could exceed ~9-10 (since 10⁹ > INT_MAX).

5. **Confusing `cur` semantics: is it the number BEFORE or INCLUDING the current node?** Convention: at function entry, `cur` doesn't yet include `node`. After `cur = cur * 10 + node.val`, it DOES.

---

## 7. The shape — Horner's on a tree

The pattern:

> **"Accumulate a value along a path using a position-dependent formula. Pass the accumulator into recursive calls; commit at leaves."**

| Problem | Formula |
|---|---|
| **This problem** | `current = current * 10 + node.val` (concatenation) |
| Path Sum | `remaining -= node.val` (subtract) |
| Convert Binary Number in Linked List | `current = current * 2 + node.val` (binary base) |
| Path encoding by direction | `current * 4 + direction` (4-ary) |
| Polynomial evaluation | Horner's: `current * x + coefficient` |
| Rolling hash for substrings | `current * base + char` |

**Pattern to internalize:**

> "Whenever you 'build a value' as you walk a sequence (or path), use ACCUMULATOR-based recursion: `current = update(current, element)`."

---

## Cross-references

- **Reference card (post-mastery):** [`../Sum_Root_to_Leaf_Numbers.md`](../Sum_Root_to_Leaf_Numbers.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Path_Sum.md`](./Path_Sum.md), [`Path_Sum_II.md`](./Path_Sum_II.md).
  - [`../../Linked_List/learn/Convert_Binary_Number_in_a_Linked_List_to_Integer.md`](../../Linked_List/learn/Convert_Binary_Number_in_a_Linked_List_to_Integer.md) — Horner's on a list.
