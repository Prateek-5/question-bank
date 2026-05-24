# Paths from Root with a Specified Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Paths_from_root_with_a_specified_sum.md`](../Paths_from_root_with_a_specified_sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/problems/paths-from-root-with-a-specified-sum/1

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **Companion to Path Sum II — paths don't need to end at LEAVES.** The lesson: **emit a path WHENEVER the running sum hits the target, regardless of whether you're at a leaf. Keep descending after a match.** Same backtracking pattern, different emit condition. **Read [`Path_Sum_II.md`](./Path_Sum_II.md) first.**

**Map of this file (7 short sections):**

1. Read the problem
2. Difference from Path Sum II
3. The algorithm
4. Code
5. Trace it
6. Why "don't stop after a match"
7. Common pitfalls

---

## 1. Read the problem

Given a binary tree and a target integer `k`, find **ALL root-to-NODE paths** (the path ends at any node, NOT necessarily a leaf) whose values sum to `k`.

Return each as a list of values.

**Example:**

```
       1
      / \
     3  -1
    / \
   2   1
```
`k = 4`. Root-to-any-node paths summing to 4:
- `[1, 3]` (sum 4) ✓

Return `[[1, 3]]`.

> **Mini-refresher: "root-to-node" vs "root-to-leaf."**
>
> Path Sum II uses ROOT-TO-LEAF (must end at a leaf). This problem uses ROOT-TO-ANY-NODE (can end anywhere).
>
> Implication: emit when sum matches, EVEN IF the current node has children — they might form OTHER matching paths.

---

## 2. Difference from Path Sum II

| Aspect | Path Sum II | This problem |
|---|---|---|
| Where path ends | LEAF only | ANY node |
| Emit condition | leaf AND sum matches | sum matches (any node) |
| After emit | continue (siblings) | continue (recurse into children) |

The CRUCIAL difference: emit at INTERNAL nodes too. And after emitting, KEEP DESCENDING (children might also have matching paths via subsequent additions).

---

## 3. The algorithm

```
result = []
path = []

def dfs(node, current_sum):
    if node is null: return
    path.append(node.val)
    current_sum += node.val
    
    if current_sum == k:
        result.append(path.copy())          # emit (don't stop)
    
    dfs(node.left, current_sum)
    dfs(node.right, current_sum)
    
    path.pop()
```

Note: emit and CONTINUE — descend into children too. Don't return early.

---

## 4. Code

**C++:**

```cpp
class Solution {
    vector<vector<int>> result;
    vector<int> path;

    void dfs(Node* node, int target, int currentSum) {
        if (!node) return;
        path.push_back(node->data);
        currentSum += node->data;

        if (currentSum == target) {
            result.push_back(path);
        }

        dfs(node->left, target, currentSum);
        dfs(node->right, target, currentSum);
        path.pop_back();
    }

public:
    vector<vector<int>> printPaths(Node* root, int k) {
        dfs(root, k, 0);
        return result;
    }
};
```

**Python:**

```python
def printPaths(root, k):
    result = []
    path = []
    def dfs(node, current):
        if not node: return
        path.append(node.data)
        current += node.data
        if current == k:
            result.append(path[:])
        dfs(node.left, current)
        dfs(node.right, current)
        path.pop()
    dfs(root, 0)
    return result
```

Complexity: **O(n) time + O(output size), O(h) space.**

---

## 5. Trace it

Tree:
```
       1
      / \
     3  -1
    / \
   2   1
```
`k = 4`.

```
dfs(1, 0): path=[1], sum=1. 1!=4.
  dfs(3, 1): path=[1,3], sum=4. 4==4 → EMIT [1, 3].
    dfs(2, 4): path=[1,3,2], sum=6. 6!=4. POP.
    dfs(1, 4): path=[1,3,1], sum=5. 5!=4. POP.
    POP path=[1].
  dfs(-1, 1): path=[1,-1], sum=0. 0!=4.
    (no children)
    POP path=[1].
  POP.

Result: [[1, 3]]. ✓
```

---

## 6. Why "don't stop after a match"

A LONGER path through a child could ALSO sum to k (if subsequent additions cancel out, e.g., +5 then -5 keeps sum unchanged).

Example: tree `1 → 4 → 2 → -2`. Paths from root:
- `[1, 4]` sums to 5.
- `[1, 4, 2]` sums to 7.
- `[1, 4, 2, -2]` sums back to 5.

For target 5, BOTH `[1, 4]` AND `[1, 4, 2, -2]` qualify. If we stopped after the first match, we'd miss the second.

**Always continue the recursion after emitting.**

---

## 7. Common pitfalls

1. **Early return after a match.** Misses longer paths through children.

2. **Only emitting at leaves** (copying Path Sum II behavior). This problem allows paths ending anywhere — emit at every match.

3. **Forgetting to copy path.** Reference would corrupt as path mutates.

4. **Forgetting to backtrack (pop).** Path accumulates across siblings.

5. **Confusing "root-to-any" with "any-to-any."** This problem still requires the path to START AT THE ROOT. For "any-to-any" paths, see Path Sum III's prefix-sum technique.

---

## Cross-references

- **Reference card (post-mastery):** [`../Paths_from_root_with_a_specified_sum.md`](../Paths_from_root_with_a_specified_sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Path_Sum_II.md`](./Path_Sum_II.md) — root-to-LEAF version.
  - [`Path_Sum_III.md`](./Path_Sum_III.md) — any-start to any-end.
