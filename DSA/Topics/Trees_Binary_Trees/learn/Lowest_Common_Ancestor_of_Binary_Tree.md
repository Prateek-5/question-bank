# Lowest Common Ancestor of Binary Tree — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Lowest_Common_Ancestor_of_Binary_Tree.md`](../Lowest_Common_Ancestor_of_Binary_Tree.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **One of the most elegant tree recursions.** The lesson: **post-order DFS — if BOTH children's recursions return something, the current node IS the LCA. Otherwise pass UP whichever child returned something.** Six-line solution with deep correctness magic. **Read [`Path_Sum.md`](./Path_Sum.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. The brute force
3. The recursive insight
4. The three cases
5. Why early-return at p or q works
6. Code
7. Trace it
8. Why the algorithm is correct
9. Common pitfalls
10. The shape — DFS with "found" propagation

---

## 1. Read the problem

Given a binary tree and two of its nodes `p` and `q`, return their **LOWEST COMMON ANCESTOR (LCA)** — the DEEPEST node that has both `p` and `q` as DESCENDANTS (where a node IS considered a descendant of itself).

**Example:**
```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4
```

- `LCA(5, 1) = 3` (only common ancestor).
- `LCA(5, 4) = 5` (5 is its own ancestor and 4's ancestor).
- `LCA(7, 4) = 2`.

**Guarantees:** both `p` and `q` exist in the tree. Values are unique.

---

## 2. The brute force

Find the path from root to p, and from root to q. Walk both paths simultaneously. The LAST common node is the LCA.

```
path_p = root_to_p_path
path_q = root_to_q_path
i = 0
while i < min(len(path_p), len(path_q)) and path_p[i] == path_q[i]:
    i += 1
return path_p[i - 1]
```

O(n) for each path-finding + O(h) comparison = O(n) total, but uses O(h) auxiliary storage and feels heavyweight.

The recursive single-pass approach is more elegant.

---

## 3. The recursive insight

At ANY node in the tree, one of three things is true about the pair (p, q):

1. Both p and q are in this node's subtree.
2. ONLY ONE of them is in this subtree.
3. NEITHER is in this subtree.

**LCA happens in case 1, specifically the DEEPEST such node.**

Use post-order DFS. Define `find(node)` to return:
- `node` if `node == p` or `node == q` (we've found a target).
- The LCA if both p and q are in the subtree.
- The found target (p or q) if only one is in the subtree.
- `null` if neither is in the subtree.

**Recurrence:**
- `l = find(node.left)` — recurse into left subtree.
- `r = find(node.right)` — recurse into right.
- If both `l` and `r` are non-null: p is in one side, q in the other (or one is the LCA itself) — CURRENT NODE is the LCA. Return `node`.
- If only one is non-null: pass it up (we haven't found both yet).
- If neither: return null.

> **Mini-refresher: the genius of dual-purpose return.**
>
> The return value of `find` does DOUBLE DUTY:
> - Sometimes it means "this is a target I found below."
> - Sometimes it means "this is the LCA I already determined."
>
> The "if both children returned something" check is what distinguishes the two cases.

---

## 4. The three cases

**Case A: `node == p` or `node == q`.**

Return `node` immediately. We've found a target. If the OTHER target is in the subtree below, our ancestor will see "left returned p, right returned q" and declare itself the LCA. If the other isn't in the subtree, we're just bubbling up "I found one."

**Case B: `node.left` returned something AND `node.right` returned something.**

p and q are in DIFFERENT subtrees of `node`. `node` is the LCA. Return `node`.

**Case C: only one side returned something.**

Either:
- It's p or q (still looking for the other).
- It's an LCA discovered deeper (already determined).

Either way, propagate it up.

---

## 5. Why early-return at p or q works

You might worry: "If I return `p` at node p without exploring p's subtree, what if the LCA was INSIDE p's subtree?"

> **Mini-refresher: LCA can't be a strict descendant of p or q.**
>
> The LCA must be an ANCESTOR of both p and q. If the LCA were a descendant of p, it wouldn't be p's ancestor. Contradiction.
>
> So when we hit p, we don't need to explore its subtree — the LCA is at p OR ABOVE.

If the other target IS in p's subtree, then p ITSELF is the LCA (p is the deepest node containing both — including itself and a descendant).

In that case, our code: `find(p)` returns p. The other side returns null. Combined at p's ancestor: only one side returned non-null (p from one, null from the other if other target was in p's subtree). The ancestor returns p, propagates up. Eventually p is the LCA returned at the top level.

Actually wait — let me re-examine. If `q` is in p's subtree:
- `find(p)` returns p (early return at p).
- p's parent recurses: one child returns p, the OTHER child returns null.
- Parent passes UP p.
- ... etc. Final return: p.

p IS the LCA in this case (it's an ancestor of both p and q). ✓

---

## 6. Code

**C++:**

```cpp
TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (!root || root == p || root == q) return root;
    TreeNode* l = lowestCommonAncestor(root->left, p, q);
    TreeNode* r = lowestCommonAncestor(root->right, p, q);
    if (l && r) return root;
    return l ? l : r;
}
```

**Six lines.** That's the entire solution.

**Python:**

```python
def lowestCommonAncestor(root, p, q):
    if not root or root == p or root == q:
        return root
    l = lowestCommonAncestor(root.left, p, q)
    r = lowestCommonAncestor(root.right, p, q)
    if l and r:
        return root
    return l if l else r
```

Complexity: **O(n) time, O(h) space.**

---

## 7. Trace it

**Tree:**
```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4
```

**`LCA(7, 4)`:**

```
lca(3, 7, 4):
  not p, not q.
  lca(5, 7, 4):
    not p, not q.
    lca(6, 7, 4):
      not p, not q. children null. l = null, r = null. return null.
    lca(2, 7, 4):
      not p, not q.
      lca(7, 7, 4):
        is p (7). RETURN 7.
      lca(4, 7, 4):
        is q (4). RETURN 4.
      l = 7, r = 4. BOTH NON-NULL. RETURN 2.
    l = null, r = 2. l-null, return r = 2.
  lca(1, 7, 4):
    not p, not q. Children 0, 8. Neither contains 7 or 4. → null.
  l = 2, r = null. Return l = 2.

Final: 2.  ✓
```

The LCA bubbles up: discovered at node 2 (both 7 and 4 in different subtrees), then propagated through the recursion.

**`LCA(5, 4)`:**

```
lca(3, 5, 4):
  lca(5, ...): is p. RETURN 5 (early).
  lca(1, ...): subtree has neither. RETURN null.
  l = 5, r = null. Return 5.

Final: 5.  ✓ (5 is its own ancestor and 4's ancestor.)
```

The early-return at p didn't break correctness; the algorithm is robust.

---

## 8. Why the algorithm is correct

> **Mini-refresher: proof sketch.**
>
> **Invariant:** `find(node)` returns:
> - `null` if neither p nor q is in node's subtree.
> - `p` (or `q`) if only that target is in the subtree.
> - The LCA (some ancestor of p and q) if both are in the subtree.
>
> **By induction on subtree size:**
>
> - Base: null subtree → returns null. ✓
> - Base: node IS p or q → returns node. Subtree may contain only p (or q), or both. The early return correctly handles "node is the LCA" case.
> - Recursive: l = find(left), r = find(right). By induction, l and r satisfy the invariant for their subtrees.
>   - If l != null AND r != null: targets are in BOTH subtrees → current node is the LCA. Return current.
>   - If only l != null: only one target in either subtree (in left). Propagate l up.
>   - Similarly for r.
>   - If both null and current isn't p or q: no targets in this subtree. Return null.
>
> Invariant preserved at every node. At the root, we get the LCA.

---

## 9. Common pitfalls

1. **Missing the `root == p or root == q` check.** Then we'd recurse INTO p's or q's subtree unnecessarily and possibly return the wrong node.

2. **Wrong "if both non-null" branch.** Must return `current node` (the LCA), not `l` or `r`.

3. **Recursing into BOTH subtrees even after finding LCA.** Inefficient but correct. (Could optimize by early-return but adds complexity.)

4. **Trying to use BST property.** This is a GENERAL binary tree — no ordering. The BST version is easier (uses the value comparisons). Different problem.

5. **Returning the wrong thing for "single found."** Just return the non-null child's result.

6. **Assuming p and q exist.** Problem guarantees they do. If they MIGHT not, you'd need a post-check.

---

## 10. The shape — DFS with "found" propagation

The pattern this problem teaches:

> **"DFS where each subtree's return value carries INFORMATION up. The combination of children's returns determines the current node's action."**

| Problem | Subtree returns | Current node decides |
|---|---|---|
| **This problem** | p, q, LCA, or null | if both non-null: LCA = self |
| Diameter | height | max via reference |
| Balanced check | height or -1 | propagate height or -1 |
| Max Path Sum | best path-through | update global max |
| Universal Tree Sum | subtree sum | combine |
| House Robber III | (rob, no-rob) tuple | combine via DP |

**Pattern to internalize:**

> "Tree problems that need to COMBINE LEFT AND RIGHT subtree info follow this template: recurse, get l and r, combine. The return type carries the 'partial answer' from each subtree."

---

> **Self-check — the question to ask next time.**
>
> When you face "find a node satisfying a property in a tree," ask:
>
> > **"Can I recursively ask each subtree 'did you find something?', then combine? Return the COMBINED ANSWER from the current node."**
>
> If yes, you've got six-line LCA-style elegance.

---

## Cross-references

- **Reference card (post-mastery):** [`../Lowest_Common_Ancestor_of_Binary_Tree.md`](../Lowest_Common_Ancestor_of_Binary_Tree.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Balanced_Binary_Tree.md`](./Balanced_Binary_Tree.md), [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md) — post-order returns.
  - Coming next: [`Construct_Binary_Tree_from_Inorder_and_Postorder.md`](./Construct_Binary_Tree_from_Inorder_and_Postorder.md).
  - Coming later: BST topic's LCA — simpler thanks to BST ordering.
