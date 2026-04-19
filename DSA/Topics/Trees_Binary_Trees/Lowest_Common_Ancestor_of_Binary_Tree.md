# Lowest Common Ancestor of Binary Tree

**Problem Link:**
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: Define LCA Precisely

Given a binary tree and two nodes `p` and `q`, the **lowest common ancestor (LCA)** is the deepest node that has both `p` and `q` as descendants (where a node is allowed to be a descendant of itself).

Example:
```
        3
       / \
      5   1
     / \ / \
    6  2 0  8
      / \
     7   4
```

- LCA of 5 and 1 → 3 (the only ancestor common to both).
- LCA of 5 and 4 → 5 (5 is an ancestor of itself and of 4).
- LCA of 7 and 4 → 2.

So LCA is about ancestors, and "lowest" means deepest / closest to the nodes rather than the root.

----------------------------------------

## Step 2: First Instinct — Find the Paths and Compare

One approach: find the root-to-p path and the root-to-q path, then walk both simultaneously. The last node where the paths agree is the LCA.

```
path_to_5 = [3, 5]
path_to_4 = [3, 5, 2, 4]
Compare: index 0 → 3 == 3 ✓. index 1 → 5 == 5 ✓. index 2 → p's path ends, q's continues.
LCA = 5 (the last agreement point).
```

That works, but requires two full tree searches (O(n) each) and then storing paths (O(h) space). Clean, but feels heavy.

Can we do it in one DFS pass?

----------------------------------------

## Step 3: What Does a "Common Ancestor" Look Like?

Consider any node `n` in the tree. When we recurse into `n`, one of three things must be true:

1. Both `p` and `q` are in `n`'s subtree.
2. Only one of them is in `n`'s subtree.
3. Neither is in `n`'s subtree.

LCA occurs in case (1) — we want the *deepest* such `n`.

Now here's the magic. If we do a post-order traversal and at each node ask "did I find `p` or `q` in my subtree?", we can identify the LCA exactly.

Define `find(node)` to return:
- `p` if the subtree contains `p` (and not `q` elsewhere below).
- `q` if the subtree contains `q` (and not `p` elsewhere below).
- The LCA if the subtree contains both.
- `null` if it contains neither.

Recurse: `l = find(node.left)`, `r = find(node.right)`.

- If `l` and `r` are both non-null, then `p` was found in one subtree and `q` in the other. Current node is the LCA. Return `node`.
- If only one is non-null, pass that up (it might be `p`, `q`, or an already-identified LCA).
- If both are null, check if current node itself is `p` or `q`. If so, return it (the "target found here" signal). Else return null.

And one small shortcut: if `node == p` or `node == q`, we can return it immediately without recursing. If the other target is in our subtree, the recursion from our ancestor will find it, and the ancestor will be declared the LCA. If the other target isn't in our subtree, we're just passing the single-found signal upward.

----------------------------------------

## Step 4: Let Me Walk Through the Algorithm Slowly

```
function lca(node, p, q):
    if node is null: return null
    if node == p or node == q: return node
    l = lca(node.left, p, q)
    r = lca(node.right, p, q)
    if l and r: return node        # p and q found in different subtrees
    return l if l else r            # one side has a found target (or null); bubble up
```

Why does this compute LCA correctly?

- If both `l` and `r` are non-null, each side "found" one of the targets. The only node where both subtrees contain targets is their LCA. ✓
- If only one is non-null, we haven't seen both yet. We pass the found one upward.
- If both are null, no targets in this subtree. Pass null up.

The crucial subtlety: when `l != null`, we don't know if `l` literally is `p` or `q`, or whether it's an LCA discovered deeper. Either way, it's the "relevant" result from the left subtree, so we return it. This works because the moment both sides report something, the current node *is* the LCA — and that current node gets returned and propagated untouched.

----------------------------------------

## Step 5: Trace on `LCA(5, 1)` in the Example

```
lca(3, 5, 1):
  not null, not p or q.
  lca(5, 5, 1):
    is p (5). return 5.
  lca(1, 5, 1):
    is q (1). return 1.
  l = 5, r = 1, both non-null → return 3.

Answer: 3. ✓
```

And `LCA(5, 4)`:

```
lca(3, 5, 4):
  not p or q.
  lca(5, 5, 4):
    is p. return 5.
  lca(1, 5, 4):
    not p or q.
    lca(0, ...): null, null → null.
    lca(8, ...): null, null → null.
    return null.
  l = 5, r = null → return 5.

Answer: 5. ✓
```

The early-return when a node matches p or q is what produces the "a node is its own ancestor" semantics. When we hit 5, we don't explore 5's subtree; we return 5 and let the ancestor logic decide.

----------------------------------------

## Step 6: Why the Early-Return Doesn't Miss the Answer

You might worry: "If I return early at 5, what if the LCA was *inside* 5's subtree?" The answer is no. LCA of `p` and `q` can never be a strict descendant of `p` or `q` — because the LCA must be an ancestor of both. So stopping at `p` (or `q`) is fine: either the other is in our subtree (ancestor of 5 will be declared LCA, returning 5 from this branch contributes correctly) or it isn't (we're just propagating "found p here" upward).

----------------------------------------

## Step 7: Complexity

Time: one post-order visit per node, constant work per node. **O(n)**.
Space: recursion stack depth. **O(h)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (!root || root == p || root == q) return root;
    TreeNode* l = lowestCommonAncestor(root->left, p, q);
    TreeNode* r = lowestCommonAncestor(root->right, p, q);
    if (l && r) return root;
    return l ? l : r;
}
```

The elegance here comes from the dual use of the return value: sometimes it's "the target I found", sometimes it's "the LCA I already determined". The "if both children returned something" check distinguishes them.

----------------------------------------

## Step 9: Follow-up Questions

- **LCA in a BST** (much simpler thanks to the ordering property). If both `p.val < root.val`, go left. If both `>`, go right. Else current is LCA.
- **What if either `p` or `q` might not be in the tree?** The algorithm above would return the found one if the other is absent — that's technically wrong. Fix: post-check by verifying both are descendants of the returned node.
- **LCA with parent pointers.** Build the set of ancestors of `p` by walking up; then walk up from `q` until hitting a node in that set.
- **Tarjan's offline LCA algorithm.** When we have many LCA queries on the same tree, preprocessing with union-find gives near-linear total time.
- **LCA via Euler tour + RMQ.** Flatten the tree into an Euler tour, then LCA(p, q) is the minimum-depth node in the tour segment between p's and q's first appearances. O(n log n) preprocessing, O(1) per query.
