# Binary Tree Level Order Traversal — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Level_Order_Traversal.md`](../Binary_Tree_Level_Order_Traversal.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/binary-tree-level-order-traversal/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The introduction to BFS on trees.** The lesson: **use a QUEUE for level-by-level traversal. The "snapshot queue size at the start of each level" trick lets you group nodes by level cleanly.** Same template solves Right Side View, Zigzag Traversal, and many other level-grouped problems. **Read [`Binary_Tree_Preorder_Traversal.md`](./Binary_Tree_Preorder_Traversal.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. Why a queue (BFS)?
3. The level-snapshot trick
4. The algorithm
5. Code
6. Trace it
7. The DFS alternative
8. Common pitfalls
9. The shape — BFS template

---

## 1. Read the problem

Given the root of a binary tree, return the **LEVEL ORDER TRAVERSAL** of its nodes' values — i.e., values grouped by depth.

**Example:** for tree
```
    3
   / \
  9   20
      / \
     15  7
```

Output: `[[3], [9, 20], [15, 7]]`.

Level 0: `[3]`. Level 1: `[9, 20]`. Level 2: `[15, 7]`.

---

## 2. Why a queue (BFS)?

> **Mini-refresher: DFS vs BFS.**
>
> - **DFS** (depth-first search): goes DEEP first, using a STACK (or recursion).
> - **BFS** (breadth-first search): goes WIDE first, using a QUEUE.
>
> For "process all nodes at depth d before depth d+1," BFS is natural. The queue's FIFO order ensures: we dequeue all level-d nodes before any level-(d+1) ones (because the d+1 nodes were enqueued AFTER all level-d nodes).

For level order:
- Start: queue contains just `[root]` (level 0).
- Each "pass": dequeue everything currently in the queue (these are this level's nodes), enqueue their children (next level).

But we need to KNOW where each level ends — when to start a new group.

---

## 3. The level-snapshot trick

> **Mini-refresher: snapshot the queue size before processing.**
>
> Before starting a level, RECORD the current queue size:
>
> ```
> size = len(queue)
> ```
>
> This `size` is the number of nodes in the CURRENT LEVEL. Process exactly `size` nodes:
>
> ```
> for _ in range(size):
>     node = queue.popleft()
>     # process node
>     enqueue children
> ```
>
> After this inner loop, the queue contains exactly the NEXT LEVEL's nodes (children of the level we just processed). Ready for the next outer iteration.

This snapshot ensures levels are CLEANLY SEPARATED, without sentinels or extra queues.

---

## 4. The algorithm

```
if root is null: return []
queue = [root]
result = []
while queue:
    size = len(queue)
    level = []
    for _ in range(size):
        node = queue.popleft()
        level.append(node.val)
        if node.left:  queue.append(node.left)
        if node.right: queue.append(node.right)
    result.append(level)
return result
```

**Pattern:**
- Outer `while`: each iteration processes ONE LEVEL.
- Snapshot `size` = number of nodes at this level.
- Inner `for`: process exactly `size` nodes, collecting values and enqueuing children.

---

## 5. Code

**C++:**

```cpp
vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        vector<int> level;
        for (int i = 0; i < sz; ++i) {
            TreeNode* n = q.front(); q.pop();
            level.push_back(n->val);
            if (n->left)  q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(std::move(level));
    }
    return res;
}
```

**Python:**

```python
from collections import deque

def levelOrder(root):
    if not root: return []
    q = deque([root])
    res = []
    while q:
        size = len(q)
        level = []
        for _ in range(size):
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        res.append(level)
    return res
```

**JavaScript:**

```javascript
function levelOrder(root) {
    if (!root) return [];
    const q = [root];
    const res = [];
    while (q.length) {
        const size = q.length;
        const level = [];
        for (let i = 0; i < size; i++) {
            const node = q.shift();
            level.push(node.val);
            if (node.left)  q.push(node.left);
            if (node.right) q.push(node.right);
        }
        res.push(level);
    }
    return res;
}
```

Complexity: **O(n) time, O(w) space** where w is the max width (≤ n/2 for balanced trees, but O(n) worst case).

(JS `shift()` is O(n); for very large inputs, use a real deque or maintain a head index.)

---

## 6. Trace it

**Tree:**
```
    3
   / \
  9   20
      / \
     15  7
```

```
q = [3]. res = [].

Iter 1: size = 1. level = [].
  Process 3: level = [3]. Enqueue 9, 20. q = [9, 20].
  res = [[3]].

Iter 2: size = 2. level = [].
  Process 9: level = [9]. No children.
  Process 20: level = [9, 20]. Enqueue 15, 7. q = [15, 7].
  res = [[3], [9, 20]].

Iter 3: size = 2. level = [].
  Process 15: level = [15]. No children.
  Process 7: level = [15, 7]. No children. q = [].
  res = [[3], [9, 20], [15, 7]].

Iter 4: q is empty. EXIT.

Return [[3], [9, 20], [15, 7]].  ✓
```

The snapshot trick CLEANLY SEPARATES the levels. Each outer iteration produces one level's array.

---

## 7. The DFS alternative

You CAN do level order with DFS by passing a `depth` argument:

```python
def levelOrder(root):
    res = []
    def dfs(node, depth):
        if not node: return
        if len(res) == depth:
            res.append([])           # new level
        res[depth].append(node.val)
        dfs(node.left, depth + 1)
        dfs(node.right, depth + 1)
    dfs(root, 0)
    return res
```

Works, but BFS feels more natural for "by level."

DFS variant is useful when:
- Tree is very wide (BFS queue would be huge).
- You need to process levels lazily.

For most cases, BFS is the idiomatic answer.

---

## 8. Common pitfalls

1. **Forgetting to snapshot `size`.** If you don't, the inner loop runs forever (the queue keeps growing).

2. **Using a recursive DFS but not passing `depth`.** Then you don't know which level a node belongs to.

3. **Forgetting `if not root: return []`.** Some inputs are empty trees.

4. **JS `.shift()` performance.** O(n) for arrays. For large trees, use a real deque or two-stack queue.

5. **Pushing the entire result into a single flat list.** This problem asks for a LIST OF LISTS (per level). Don't flatten.

6. **Confusing with preorder.** Preorder visits depth-first; level order visits breadth-first.

---

## 9. The shape — BFS template

The pattern:

> **BFS with level snapshot = clean per-level processing on trees (and graphs).**

```
queue = [start]
while queue:
    size = len(queue)
    for _ in range(size):
        node = queue.popleft()
        # process node at current level
        for child in children(node):
            queue.append(child)
```

Where this applies:

| Problem | Variant |
|---|---|
| **This problem** | collect each level's values |
| Right Side View | record the LAST value of each level |
| Zigzag Level Order | reverse alternate levels |
| Level Averages | sum each level, divide by size |
| Minimum Depth | return depth when you find a leaf |
| Binary Tree from Level Order Serialization | inverse |
| Word Ladder | states = words, levels = transformation count |
| Shortest Path in Grid | BFS on grid cells |

**Pattern to internalize:**

> "When you need LEVEL-BY-LEVEL processing of a tree (or hop-count on a graph), use BFS with the queue-size snapshot trick."

---

> **Self-check — the question to ask next time.**
>
> When you face a tree problem asking for "by level," "by depth," or "shortest path in nodes," ask:
>
> > **"Can I use BFS with a queue? Snapshot `queue.size()` before each level to group nodes cleanly."**
>
> If yes, you've got the BFS template.

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Level_Order_Traversal.md`](../Binary_Tree_Level_Order_Traversal.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Inorder_Traversal_Iterative.md`](./Binary_Tree_Inorder_Traversal_Iterative.md) (DFS with stack).
  - Coming next: [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md), [`Balanced_Binary_Tree.md`](./Balanced_Binary_Tree.md).
