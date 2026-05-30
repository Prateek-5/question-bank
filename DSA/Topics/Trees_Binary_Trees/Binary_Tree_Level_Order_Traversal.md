# Binary Tree Level Order Traversal

**Problem Link:**
<a href="https://leetcode.com/problems/binary-tree-level-order-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/binary-tree-level-order-traversal/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: The Task

Given a binary tree, return its values grouped by **level** — that is, by depth from the root. Level 0 is just the root, level 1 is both children, etc. The output is a list of lists.

Example:
```
        3
       / \
      9   20
          / \
         15  7
```

Levels:
- Level 0: `[3]`
- Level 1: `[9, 20]`
- Level 2: `[15, 7]`

Output: `[[3], [9, 20], [15, 7]]`.

----------------------------------------

## Step 2: Think About Structure

A tree, visited depth-first, gives us a mess of nodes in some order (preorder, inorder, postorder). None of those naturally group by level.

What does group things by level? A **queue**.

Think of it like ripples from a stone dropped in water. The first ripple is the root. The next ripple is its children. The next is their children. Each ripple is a level.

To simulate ripples:
1. Put the root in a queue.
2. Pop the queue; that's the current level.
3. The children of all nodes in the current level form the next level.
4. Repeat.

This is BFS — breadth-first search. But in standard BFS we just emit nodes one at a time; here we need to know **where one level ends and the next begins**. That's the small twist.

----------------------------------------

## Step 3: Separating Levels — Three Techniques

### Technique A — Level size snapshot

Before processing each level, note how many nodes are currently in the queue. That count is exactly the number of nodes in this level. Pop that many, collect them as the level, pushing their children for later.

```
q = [root]
while q not empty:
    size = q.size()
    level = []
    for _ in range(size):
        n = q.pop_front()
        level.append(n.val)
        if n.left:  q.push_back(n.left)
        if n.right: q.push_back(n.right)
    result.append(level)
```

This is the cleanest approach for most cases.

### Technique B — Sentinels

Push a `null` (or sentinel) after each level. When you pop a sentinel, you know the level has ended — start a new list and push another sentinel. Workable but messier.

### Technique C — Two queues

Maintain a current-level queue and a next-level queue. Swap them each round. Clean but slightly more bookkeeping.

Technique A is the idiomatic one. Let's use it.

----------------------------------------

## Step 4: Trace on the Example

Queue and result, step by step.

```
Initial: q = [3], result = [].

Outer iter 1: size = 1.
  level = []
  pop 3: level = [3]. Push 9, 20.
  End of inner: q = [9, 20].
  result = [[3]].

Outer iter 2: size = 2.
  level = []
  pop 9: level = [9]. No children.
  pop 20: level = [9, 20]. Push 15, 7.
  End of inner: q = [15, 7].
  result = [[3], [9, 20]].

Outer iter 3: size = 2.
  level = []
  pop 15: level = [15]. No children.
  pop 7: level = [15, 7]. No children.
  End: q = [].
  result = [[3], [9, 20], [15, 7]].

Outer iter 4: q empty. Stop.
```

Matches expected. The "snapshot size" trick is what cleanly separates the levels.

----------------------------------------

## Step 5: Why This Works — The Invariant

**Invariant:** at the start of each outer iteration, the queue contains exactly the nodes of the next level to process, and nothing else.

- True initially: queue = [root], which is level 0.
- Preserved: during the inner loop, we pop all `size` nodes of the current level and push their children (which are the next level's nodes). After the inner loop finishes, the queue contains only those children.

That invariant is what makes the size-snapshot technique correct.

----------------------------------------

## Step 6: DFS Alternative with Depth Parameter

You can also solve this with depth-first recursion, carrying a depth argument:

```cpp
void dfs(TreeNode* n, int depth, vector<vector<int>>& res) {
    if (!n) return;
    if ((int)res.size() == depth) res.push_back({});
    res[depth].push_back(n->val);
    dfs(n->left, depth + 1, res);
    dfs(n->right, depth + 1, res);
}
```

Start with `dfs(root, 0, res)`. Each time we visit a node at depth d, we add it to `res[d]` (creating `res[d]` lazily if it doesn't exist yet).

This works, but the output order within a level depends on traversal order. Preorder DFS happens to give left-to-right order at each level because both left and right subtrees get fully explored in that order. Reliable, but less obvious than the BFS version.

----------------------------------------

## Step 7: Complexity

Time: every node is enqueued and dequeued once. **O(n)**.

Space: the queue can hold up to the widest level at a time. For balanced trees, that's `n/2`. For skewed trees, it's O(1). Worst-case **O(n)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        vector<int> level;
        while (sz--) {
            auto* n = q.front(); q.pop();
            level.push_back(n->val);
            if (n->left)  q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(move(level));
    }
    return res;
}
```

The `sz--` in the inner while does two things: it controls loop iterations and decrements after the check, so the loop runs exactly `sz` times. Clear and idiomatic.

----------------------------------------

## Step 9: Follow-up Questions

- **Zigzag level order.** Alternate left-to-right and right-to-left per level. Same BFS; just reverse every other level before pushing to `res`.
- **Level order from bottom up (deepest level first).** Collect the levels normally, then reverse `res` at the end.
- **Average value of each level.** Accumulate a sum during the inner loop; divide at the end.
- **Find the right-most node at each level (Right Side View).** During the inner loop, emit only the last node.
- **Serialize a tree using level order.** Include null markers to represent missing children, so deserialization works.
