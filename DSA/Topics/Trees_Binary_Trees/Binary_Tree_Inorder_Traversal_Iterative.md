# Binary Tree Inorder Traversal (Iterative)

**Problem Link:**
<a href="https://leetcode.com/problems/binary-tree-inorder-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/binary-tree-inorder-traversal/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What's Inorder Traversal?

Given a binary tree, return its in-order traversal: visit the left subtree, then the current node, then the right subtree.

For:
```
    1
     \
      2
     /
    3
```

Inorder:
- Start at 1. Left subtree empty. Visit 1.
- Right subtree: node 2.
  - Left subtree of 2: node 3.
    - Left of 3: empty. Visit 3.
    - Right of 3: empty.
  - Visit 2.
  - Right of 2: empty.

Output: `[1, 3, 2]`.

The **recursive** version is trivial:
```cpp
void inorder(TreeNode* n, vector<int>& out) {
    if (!n) return;
    inorder(n->left, out);
    out.push_back(n->val);
    inorder(n->right, out);
}
```

But the problem asks for an **iterative** version. Why? Iterative avoids the call stack; it's safer for very deep trees (recursion could stack-overflow). And it's a classic interview litmus test for understanding how recursion actually works.

----------------------------------------

## Step 2: What Does Recursion Do Internally?

The recursive function implicitly uses the **call stack** to remember "where to return to." When `inorder(n->left, out)` is called, the function's state (including `n`) is pushed onto the call stack. When it finishes, we return to the line `out.push_back(n->val)`.

To mimic this without actual recursion, we build our own **explicit stack** that tracks pending nodes — nodes we've partially processed (walked into their left subtree) but haven't yet "visited" (printed) or processed their right subtree.

----------------------------------------

## Step 3: Plan the Iterative Version

Here's the insight. At any point in the traversal, we're "in the middle of processing" some sequence of ancestors. Their left subtrees have been fully explored; we're about to visit them (or we've visited them and are heading into their right subtrees).

At each step:
- If there's a node `cur`, go left: push `cur` onto the stack, move to `cur->left`.
- If `cur` is null, we've run out of left-descent. Pop the top of the stack (that's the next node to visit), record its value, and go right.

This matches the recursive pattern:
- "Go left" = recurse into left subtree (simulated by pushing the current node).
- "Visit" = process the popped node.
- "Go right" = recurse into right subtree.

----------------------------------------

## Step 4: The Algorithm

```
stack = []
cur = root
result = []

while cur or stack is not empty:
    # go as far left as possible
    while cur:
        stack.push(cur)
        cur = cur.left
    # cur is null; pop and visit
    cur = stack.pop()
    result.append(cur.val)
    # move to right subtree
    cur = cur.right

return result
```

Two nested loops. The inner loop dives left; the outer "pop and go right" is the visit-and-advance step.

----------------------------------------

## Step 5: Trace on the Example

Tree:
```
    1
     \
      2
     /
    3
```

```
stack = [], cur = 1, result = [].

Outer iter 1:
  Inner: cur=1 non-null. Push. cur = 1.left = null.
         Inner exits (cur null).
  Pop 1. result = [1]. cur = 1.right = 2.

Outer iter 2:
  Inner: cur=2. Push. cur = 2.left = 3.
         cur=3. Push. cur = 3.left = null.
  Pop 3. result = [1, 3]. cur = 3.right = null.

Outer iter 3 (stack has 2):
  Inner: cur null, skip.
  Pop 2. result = [1, 3, 2]. cur = 2.right = null.

Outer iter 4: cur=null, stack empty. Exit.
```

Output: `[1, 3, 2]`. ✓

----------------------------------------

## Step 6: Why the Stack Tracks Exactly What Recursion Does

In the recursive version, when we call `inorder(n->left, out)`, we're pausing at node `n` — we'll come back and execute `out.push_back(n->val)` next. The call stack remembers `n`.

In the iterative version, we explicitly push `n` onto the stack before descending. When the inner loop stops (we've hit a null left child), we pop — that's the node we paused at, time to visit.

The two loops mirror this exactly:
- **Inner loop** = "recurse into left subtree as deep as possible, pushing each node we pass."
- **Pop and visit** = "return from the leftmost-null recursion, visit the paused node."
- **Move to right** = "recurse into right subtree."

----------------------------------------

## Step 7: Alternative — Morris Traversal (O(1) Space)

There's a clever method called **Morris traversal** that does in-order without any stack *or* recursion, using **threaded pointers**: temporarily modify `rightmost.right` of each left subtree to point to the current node, so we can find our way back.

Morris is O(n) time, O(1) space, but mutates the tree during traversal (restoring it at the end). Worth knowing for memory-constrained scenarios; overkill for most interview answers.

Most interviewers prefer the stack-based iterative version for its clarity and general applicability.

----------------------------------------

## Step 8: Name It

This is the classic **stack-based iterative in-order traversal** — a foundational pattern. Once you understand it for in-order, similar ideas apply to:
- **Iterative preorder:** push right then left; pop and visit immediately.
- **Iterative postorder:** two stacks, or one stack with tracking flags.
- **BST iterator:** reuse this exact structure, pausing between `next()` calls.
- **Threaded trees / Morris traversal:** avoids the stack entirely.

----------------------------------------

## Step 9: Complexity

Time: each node is pushed and popped exactly once. **O(n)**.
Space: the stack holds at most `h` nodes, where h is the tree's height. **O(h)**. For balanced trees O(log n); worst case O(n).

----------------------------------------

## Step 10: C++ Implementation

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

The whole thing is 11 lines. The key invariant: between loop iterations, every node in the stack is "waiting to be visited" — its left subtree is done (or currently being explored), and its right subtree hasn't been touched yet.

----------------------------------------

## Step 11: Follow-up Questions

- **Iterative preorder traversal.** Push root; pop, visit, push right then left (so left is popped next).
- **Iterative postorder traversal.** Harder — use two stacks (one builds reverse postorder, the other reverses it), or track "last visited" to decide when to pop a node.
- **Morris in-order (O(1) space).** Temporarily thread right-pointers; un-thread when done.
- **Inorder of a BST with early termination (like "find k-th smallest").** Same structure; break out when a counter reaches k.
- **Concurrent inorder iteration.** Use the BST Iterator pattern with state encapsulated in an object.
- **Why the inner while (go-left) loop?** Because in-order requires visiting left first. "Go all the way left before visiting" mirrors recursion's behavior.
