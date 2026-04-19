# Kth Smallest Element in BST

**Problem Link:**
https://leetcode.com/problems/kth-smallest-element-in-a-bst/

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Read the Problem, Check Assumptions

Given the root of a **Binary Search Tree** and an integer `k`, return the k-th smallest value. It's 1-indexed — `k = 1` means the smallest, `k = 2` means the second smallest, and so on.

Example:
```
     5
    / \
   3   6
  / \
 2   4
/
1
```

Sorted values in this tree: 1, 2, 3, 4, 5, 6. So for `k = 3`, the answer is **3**.

The key word is **BST**. Without that property, we'd need to collect everything and sort. With it, we can do better.

----------------------------------------

## Step 2: The Defining BST Property

For any BST node, all values in its left subtree are smaller, and all values in its right subtree are larger. This has a wonderful consequence:

> **An in-order traversal of a BST visits nodes in sorted order.**

In-order means: visit the entire left subtree, then the current node, then the entire right subtree. Because of the BST property, everything in the left subtree is < current, and everything in the right subtree is > current — so the visits are sorted.

Let me verify on the example.

In-order of our tree:
- Recurse into 3's subtree → recurse into 2's subtree → recurse into 1. Visit 1.
- Back to 2. Visit 2.
- Right subtree of 2 is null.
- Back to 3. Visit 3.
- Recurse into 4. Visit 4.
- Back to 5. Visit 5.
- Recurse into 6. Visit 6.

Order: 1, 2, 3, 4, 5, 6. ✓

----------------------------------------

## Step 3: Using In-Order to Find the k-th

If in-order visits nodes in sorted order, then the k-th visited node is the k-th smallest. We just need to count.

Naïve version: do a full in-order traversal, collect into an array, return `array[k-1]`.

```cpp
void inorder(TreeNode* n, vector<int>& vals) {
    if (!n) return;
    inorder(n->left, vals);
    vals.push_back(n->val);
    inorder(n->right, vals);
}

int kthSmallest(TreeNode* root, int k) {
    vector<int> vals;
    inorder(root, vals);
    return vals[k - 1];
}
```

Works, but visits every node (O(n)) even though we only need the first k. Can we stop early?

----------------------------------------

## Step 4: Stopping Early

Yes — just maintain a counter that decrements with each in-order visit. When the counter hits zero, that's the k-th smallest. Stop there.

```
kthSmallest(node, k):
    use a stack for iterative in-order
    while cur or stack not empty:
        push left spine of cur
        pop; decrement k
        if k == 0: return that node's value
        cur = popped.right
```

Iterative in-order requires a stack. Let me make sure I remember it exactly.

**Iterative in-order pattern:**

```
cur = root
stack = []
while cur or stack:
    while cur:           # push entire left spine
        stack.push(cur)
        cur = cur.left
    cur = stack.pop()    # now visit
    visit(cur)
    cur = cur.right      # move to right subtree
```

Each `pop` is a "visit". So we can intercept there to apply the counter logic.

```
while cur or stack:
    while cur:
        stack.push(cur); cur = cur.left
    cur = stack.pop()
    k--
    if k == 0: return cur.val
    cur = cur.right
```

----------------------------------------

## Step 5: Trace for k = 3 on Our Example

```
     5
    / \
   3   6
  / \
 2   4
/
1
```

```
Start: cur = 5, stack = []

Push left spine of 5:
  push 5, cur = 3.
  push 3, cur = 2.
  push 2, cur = 1.
  push 1, cur = null.
Stack: [5, 3, 2, 1].

Pop 1. k=3→2. cur = null (1 has no right).
Visit: 1.

Pop 2. k=2→1. cur = null.
Visit: 2.

Pop 3. k=1→0. Return 3.
```

Answer: **3**. ✓

We stopped after visiting exactly three nodes instead of traversing the whole tree.

----------------------------------------

## Step 6: The Recursive Version (Also Fine)

```cpp
int count = 0;
int ans = -1;

void inorder(TreeNode* n, int k) {
    if (!n || ans != -1) return;
    inorder(n->left, k);
    if (++count == k) { ans = n->val; return; }
    inorder(n->right, k);
}
```

Recursive in-order, using `ans != -1` as an early-exit flag. Some interviewers prefer iterative for this problem because it doesn't need the shared-state flag.

----------------------------------------

## Step 7: What If the Tree Is Modified Frequently?

The problem's follow-up asks: if we're doing many insertions, deletions, and k-th-smallest queries, can we do better than O(k) per query?

Yes — **augment each node** with the size of its subtree. Then k-th smallest is a walk:

- Let `left_size` = size of left subtree.
- If `k == left_size + 1`: current node is the answer.
- If `k <= left_size`: recurse left.
- Else: recurse right with `k -= left_size + 1`.

Each step descends one level, so the query is O(h). Inserts and deletes update the stored sizes along the path — also O(h).

For a balanced BST, that's O(log n) per operation. A significant win when queries are frequent.

----------------------------------------

## Step 8: Complexity

Time: at most k visits before we stop. In the worst case (k = n), that's **O(h + k)** — we walk the left spine to find the smallest, then visit k nodes in order. For a balanced tree this is essentially O(h + k), which is better than the O(n) full-traversal baseline when k is small.

Space: **O(h)** for the iterative stack (or recursion depth).

With augmentation: **O(h)** per query, O(h) per update.

----------------------------------------

## Step 9: C++ Implementation

Iterative, with early termination:

```cpp
int kthSmallest(TreeNode* root, int k) {
    stack<TreeNode*> st;
    auto* cur = root;
    while (cur || !st.empty()) {
        while (cur) {
            st.push(cur);
            cur = cur->left;
        }
        cur = st.top(); st.pop();
        if (--k == 0) return cur->val;
        cur = cur->right;
    }
    return -1;  // unreachable given valid k
}
```

----------------------------------------

## Step 10: Follow-up Questions

- **Kth largest in a BST.** Do a reverse in-order (right, root, left) with the same counter trick.
- **Find the median of a BST.** If you know the size, the median is the (n/2)-th or (n/2 + 1)-th smallest.
- **Frequent insert/delete and kth queries.** Augment nodes with subtree sizes as described.
- **Morris traversal.** In-order in O(1) extra space (no stack or recursion) by temporarily rewiring pointers. Works but is subtle.
- **Kth smallest in an unsorted tree (generic binary tree).** No BST property — fallback is collecting all and using a heap or quickselect.
