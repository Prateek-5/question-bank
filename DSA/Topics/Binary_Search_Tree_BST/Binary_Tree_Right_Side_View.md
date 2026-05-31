# Binary Tree Right Side View

**Problem Link:**
<a href="https://leetcode.com/problems/binary-tree-right-side-view/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/binary-tree-right-side-view/</a>

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Visualize the Problem

Imagine standing to the **right** of a binary tree and looking at it. What do you see?

At each "height level" (depth), you see the **rightmost** node. Every other node at that level is blocked by the rightmost one.

Return the list of visible node values, top to bottom.

Example:
```
     1
    / \
   2   3
    \   \
     5   4
```

Standing on the right:
- Level 0: only node 1. See 1.
- Level 1: nodes 2 and 3. Rightmost is 3. See 3.
- Level 2: nodes 5 and 4. Rightmost is 4. See 4.

Result: `[1, 3, 4]`.

Another example:
```
     1
    /
   2
  /
 3
```

- Level 0: 1.
- Level 1: 2 (only node).
- Level 2: 3 (only node).

Result: `[1, 2, 3]`.

"Rightmost" really means the last node encountered at each level in left-to-right order — not just right children.

----------------------------------------

## Step 2: Natural Fit — BFS by Level

For "last at each level," BFS level-order traversal is the canonical tool.

```
queue = [root]
result = []
while queue is non-empty:
    level_size = len(queue)
    for i in 0..level_size - 1:
        node = queue.pop_front()
        if i == level_size - 1:
            result.append(node.val)   # the last in this level
        if node.left:  queue.push_back(node.left)
        if node.right: queue.push_back(node.right)
return result
```

Each iteration of the outer while processes one level. We remember how many nodes are in this level (via `level_size`), iterate through them, and the last one we process is the rightmost.

----------------------------------------

## Step 3: Trace on Example 1

Tree:
```
     1
    / \
   2   3
    \   \
     5   4
```

```
queue: [1]. result: [].

Level 0: size=1.
  i=0: pop 1. It's the last (i == size-1). Append to result. result=[1].
  Push 2 and 3.
queue: [2, 3].

Level 1: size=2.
  i=0: pop 2. Not last. Push 5 (only right child).
  i=1: pop 3. Last. Append. result=[1, 3]. Push 4.
queue: [5, 4].

Level 2: size=2.
  i=0: pop 5. Not last.
  i=1: pop 4. Last. Append. result=[1, 3, 4].
queue: [].

Done.
```

Output: `[1, 3, 4]`. ✓

----------------------------------------

## Step 4: DFS Alternative — Right-First Preorder

There's another approach that feels different but produces the same output.

Do a preorder DFS, but recurse on the **right** child **first**. At each node, if we're seeing a deeper level than recorded so far, this node is the first to visit at its level — which, because we recursed right-first, is the rightmost node at that level.

```
def dfs(node, depth):
    if node is null: return
    if depth == len(result):   # first node at this depth
        result.append(node.val)
    dfs(node.right, depth + 1)
    dfs(node.left, depth + 1)

dfs(root, 0)
return result
```

This works because DFS going right-first reaches each level's rightmost node before any other. So the first node we see at any given depth is that depth's rightmost.

Trace on example 1:
```
dfs(1, 0): len(result)=0. Append 1. result=[1].
  dfs(3, 1): len=1. Append 3. result=[1, 3].
    dfs(4, 2): len=2. Append 4. result=[1, 3, 4].
    dfs(null, 3).
  dfs(null, 2).
  dfs(2, 1): len=3, depth=1. len != 1, don't append.
    dfs(5, 2): len=3, depth=2. Don't append.
    dfs(null, 3).
  dfs(null, 2).
```

Output: `[1, 3, 4]`. ✓

Shorter code but less intuitive than BFS. Both are valid.

----------------------------------------

## Step 5: Which Approach Is "Better"?

BFS is more direct (literally "traverse by levels, emit the last per level"). DFS with right-first recursion is a bit more elegant in code but requires the subtle "first-at-depth" insight.

Complexity is the same: O(n) time, O(h) or O(n) space depending on tree shape.

For interviews, BFS is usually the clearer answer. DFS with right-first is a nice alternative that shows conceptual flexibility.

----------------------------------------

## Step 6: Edge Cases

- **Empty tree:** queue never fills. Result is `[]`.
- **Single node:** Level 0 has one node, which is trivially rightmost. Result is `[root.val]`.
- **Single-child chain (all lefts):** each level has one node — seen from the right, that one node is what's visible. Result: all values in order.

----------------------------------------

## Step 7: Name It

**Level-order (BFS) traversal with per-level last-element collection**. Same template solves:
- Left side view: pick the **first** node per level.
- Binary Tree Level Averages: collect the average per level.
- Largest Value in Each Tree Row: track the max per level.

Whenever the problem is "something per level," BFS with level-size snapshot is the go-to pattern.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** — each node visited once.
Space: **O(n)** for the queue in the worst case (complete binary tree has ~n/2 at the bottom level).

For DFS: O(h) recursion depth.

----------------------------------------

## Step 9: C++ Implementation

**BFS version:**

```cpp
vector<int> rightSideView(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    queue<TreeNode*> q;
    q.push(root);

    while (!q.empty()) {
        int levelSize = q.size();
        for (int i = 0; i < levelSize; ++i) {
            TreeNode* node = q.front(); q.pop();
            if (i == levelSize - 1) {
                result.push_back(node->val);
            }
            if (node->left) q.push(node->left);
            if (node->right) q.push(node->right);
        }
    }
    return result;
}
```

**DFS version (right-first preorder):**

```cpp
class Solution {
    vector<int> result;
    void dfs(TreeNode* node, int depth) {
        if (!node) return;
        if ((int)result.size() == depth) result.push_back(node->val);
        dfs(node->right, depth + 1);
        dfs(node->left, depth + 1);
    }

public:
    vector<int> rightSideView(TreeNode* root) {
        dfs(root, 0);
        return result;
    }
};
```

Both are ~10 lines. Pick the one that feels clearer to you.

----------------------------------------

## Step 10: Follow-up Questions

- **Left side view.** Symmetric — BFS picks first per level, or DFS with left-first recursion.
- **Top view / bottom view.** Track by horizontal distance from root, not level.
- **Boundary traversal of a binary tree.** Combines left view, leaves, and right view.
- **Right view with N-ary tree.** Rightmost means the last child in each level's list.
- **Return the visible node objects (not just values).** Same algorithm, append the node instead.
- **Tree that's been serialized — compute right view without reconstructing.** Can be done directly on the serialized form if it's level-order.


---

## Interview Signals (from LeetLens)

This problem (or close variants) was reported in **1 real interview(s)** in the LeetLens dataset (snapshot 2026-05-31). Pay attention to the company context when practicing.

| Company | Difficulty | LeetLens ID | Match | Variant note |
|---|---|---|---|---|
| Meta | Medium | `4c260e13` | 1.00 (exact-title) | Binary Tree Right Side View |

_Source: LeetLens DB. Match methods: `substring` = direct hit; `token-coverage` = ≥70% of this card's filename tokens appear in the question; `jaccard`/`ratio` = fuzzy title similarity._
_See the parent folder's `EXTRACTED_QUESTIONS.md` §2 for the full list of incorporated questions._
