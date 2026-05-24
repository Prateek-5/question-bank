# Binary Tree Inorder Traversal (Iterative) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Inorder_Traversal_Iterative.md`](../Binary_Tree_Inorder_Traversal_Iterative.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/binary-tree-inorder-traversal/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: ITERATIVE inorder uses an EXPLICIT STACK with the "go-left-as-far-as-possible, then pop and go right" pattern. The stack holds nodes whose LEFT subtree has been (or is being) explored, but who haven't been visited yet.** **Read [`Binary_Tree_Inorder_Traversal.md`](./Binary_Tree_Inorder_Traversal.md) first.**

**Map of this file (9 short sections):**

1. Read the problem (recap)
2. Why iterative?
3. The recursion-to-stack mapping
4. The two-loop structure
5. Code
6. Trace it
7. The stack invariant
8. Common pitfalls
9. The shape — explicit stack for DFS

---

## 1. Read the problem (recap)

Same as Inorder Traversal: return values in **Left → Root → Right** order. But now WITHOUT using recursion.

**Example:** tree `1 → right 2 → left 3`. Inorder: `[1, 3, 2]`.

---

## 2. Why iterative?

> **Mini-refresher: when recursion fails.**
>
> Recursion uses the CALL STACK. Each recursive call adds a frame. For VERY DEEP trees (think: 10⁵ nodes in a left-skewed tree), the call stack overflows.
>
> Iterative versions use an EXPLICIT STACK on the heap. The heap has much more room than the call stack.
>
> Also: iterative versions are often required by:
> - Interviewers testing your understanding of how recursion works internally.
> - Languages with limited recursion depth (Python defaults to ~1000).
> - Environments where you need to pause/resume traversal (BST iterator).

---

## 3. The recursion-to-stack mapping

> **Mini-refresher: what the call stack does during recursion.**
>
> When `inorder(node)` calls `inorder(node.left)`, the function PAUSES at the recursive call. Its STATE (the `node` variable, the position in the function) is saved on the call stack. After `inorder(node.left)` returns, we resume — visit `node`, then recurse into right.
>
> An explicit stack PLAYS THE SAME ROLE. We push `node` onto a stack BEFORE descending into `node.left`. When we've finished `node.left` (hit a null), we pop `node` and continue (visit it, then go right).

So the explicit stack contains: **nodes we've descended INTO (going left), but haven't yet VISITED.**

---

## 4. The two-loop structure

```
stack = []
cur = root
result = []
while cur or stack not empty:
    # PHASE 1: Walk LEFT, pushing along the way
    while cur is not null:
        stack.push(cur)
        cur = cur.left
    # Now cur is null — we've reached a "left edge"
    # PHASE 2: Pop and visit; then move to RIGHT
    cur = stack.pop()
    result.append(cur.val)
    cur = cur.right
return result
```

**Outer loop:** while there's still work to do (either we have a current node to explore OR there are paused nodes on the stack).

**Inner while (Phase 1):** walk LEFT as far as possible, pushing each node we pass. This is "going left in the recursion."

**Phase 2 (after inner loop):** pop the top (it's the deepest left-descendant of where we paused). Visit it. Then move to its RIGHT child — which becomes the new `cur` for the next outer iteration.

---

## 5. Code

**C++:**

```cpp
vector<int> inorderTraversal(TreeNode* root) {
    vector<int> result;
    stack<TreeNode*> st;
    TreeNode* cur = root;
    while (cur || !st.empty()) {
        while (cur) {
            st.push(cur);
            cur = cur->left;
        }
        cur = st.top(); st.pop();
        result.push_back(cur->val);
        cur = cur->right;
    }
    return result;
}
```

**Python:**

```python
def inorderTraversal(root):
    result = []
    stack = []
    cur = root
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        result.append(cur.val)
        cur = cur.right
    return result
```

**JavaScript:**

```javascript
function inorderTraversal(root) {
    const result = [];
    const stack = [];
    let cur = root;
    while (cur || stack.length) {
        while (cur) {
            stack.push(cur);
            cur = cur.left;
        }
        cur = stack.pop();
        result.push(cur.val);
        cur = cur.right;
    }
    return result;
}
```

Complexity: **O(n) time, O(h) space.**

---

## 6. Trace it

**Tree:** root=1, root.right=2, 2.left=3.

```
stack = [], cur = 1, result = [].

Outer iter 1:
  Inner: cur=1 → push, cur=1.left=null. EXIT inner.
  Pop 1. result = [1]. cur = 1.right = 2.

Outer iter 2:
  Inner: cur=2 → push, cur=2.left=3. cur=3 → push, cur=3.left=null. EXIT.
  Pop 3. result = [1, 3]. cur = 3.right = null.

Outer iter 3:
  Inner: cur=null → skip.
  Pop 2. result = [1, 3, 2]. cur = 2.right = null.

Outer iter 4: cur=null, stack=[]. EXIT outer.

Return [1, 3, 2].  ✓
```

The stack peaked at 2 elements (`[1, 2, 3]` was never simultaneously held). Inner loop dives left; pop-and-go-right is one step at a time.

---

## 7. The stack invariant

> **Mini-refresher: what the stack holds.**
>
> AT ANY POINT between outer-loop iterations, the stack holds nodes such that:
>
> 1. They were encountered during a LEFT-descent.
> 2. Their LEFT subtree has been (or is being) fully explored.
> 3. They have NOT YET been VISITED.
> 4. Their RIGHT subtree has NOT YET been explored.
>
> The TOP of the stack is the deepest such node — the next one to be visited.

When we pop:
- Visit it (its left is done).
- Then descend into its right (next subtree to explore).

This invariant exactly mirrors the recursive function's behavior.

---

## 8. Common pitfalls

1. **Visiting nodes during the LEFT descent.** That would be preorder, not inorder. Visit AFTER popping.

2. **Forgetting the `or stack` part of the outer loop condition.** Need `cur != null OR stack not empty`. Without the second part, we'd exit while there are still paused nodes.

3. **Pushing the right child instead of leaving it for the outer loop.** Don't push `cur.right` — set `cur = cur.right` so the OUTER iteration handles it.

4. **Confusing the two while loops.** Inner = left descent. Outer = "one more pop-and-go-right step."

5. **Trying to combine the loops.** They have different roles. Keep them separated.

6. **Stack of integers instead of node pointers.** You need POINTERS to navigate; integers lose tree structure.

---

## 9. The shape — explicit stack for DFS

The pattern this problem teaches:

> **"Recursion can be transformed to iteration via an EXPLICIT STACK that holds the state of paused calls. The stack mirrors the call stack."**

Where this applies:

| Use case | Stack content |
|---|---|
| **This problem** (Inorder iterative) | nodes paused mid-traversal |
| Preorder iterative | nodes to visit (yet to push children) |
| Postorder iterative (one-stack) | nodes + "last visited" marker |
| BST Iterator class | same as this problem, pause between `next()` calls |
| Iterative DFS on a graph | nodes to explore |
| Function call simulation | function arguments + return addresses |
| Expression parsing | operator + operand stack |

**Pattern to internalize:**

> "Any recursive traversal can become iterative with an explicit stack. The stack holds 'frames' = pending work. The algorithm explicitly does what recursion does implicitly."

---

> **Self-check — the question to ask next time.**
>
> When you need to convert recursion to iteration (for deep trees or to support pause/resume), ask:
>
> > **"What does each recursive call's STATE look like? Push that state onto an explicit stack. Pop when done with the sub-call."**
>
> If yes, you've converted recursion to iteration.

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Inorder_Traversal_Iterative.md`](../Binary_Tree_Inorder_Traversal_Iterative.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Inorder_Traversal.md`](./Binary_Tree_Inorder_Traversal.md), [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md).
  - Coming next: [`Binary_Tree_Level_Order_Traversal.md`](./Binary_Tree_Level_Order_Traversal.md) — BFS, not DFS.
