# All Elements in Two BSTs

**Problem Link:**
<a href="https://leetcode.com/problems/all-elements-in-two-binary-search-trees/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/all-elements-in-two-binary-search-trees/</a>

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Read the Problem

Given two BSTs, return a sorted list containing **all** elements from both trees combined.

Example:
```
Tree 1:        Tree 2:
  2              1
 / \            / \
1   4          0   3
```

Elements: 2, 1, 4 and 1, 0, 3. Combined and sorted: `[0, 1, 1, 2, 3, 4]`. Duplicates are preserved.

----------------------------------------

## Step 2: The Obvious Approach

Dump every value from both trees into an array, sort it, done.

```cpp
vector<int> all;
collect(tree1, all);
collect(tree2, all);
sort(all.begin(), all.end());
return all;
```

The `collect` function does any tree traversal (in-order, preorder, doesn't matter for now). Then one O(N log N) sort.

N = total number of nodes (both trees combined). Time: O(N log N). Works. But let me think about whether we can do better.

----------------------------------------

## Step 3: Leverage the BST Property

Each BST, traversed **in-order**, gives a sorted list of its elements. That's the defining gift of a BST.

So we can:
1. In-order traverse tree 1 → sorted list L1.
2. In-order traverse tree 2 → sorted list L2.
3. Merge two sorted lists.

This takes O(N) total: O(|L1| + |L2|) for traversals, O(|L1| + |L2|) for the merge. No sorting needed — we never throw away the BST's built-in order.

Going from O(N log N) to O(N) just by reading the problem structurally.

----------------------------------------

## Step 4: Merge Two Sorted Lists

The merge step is a classic two-pointer operation:

```
i = j = 0
result = []
while i < len(L1) and j < len(L2):
    if L1[i] <= L2[j]:
        result.append(L1[i]); i++
    else:
        result.append(L2[j]); j++
# append remaining
while i < len(L1): result.append(L1[i++])
while j < len(L2): result.append(L2[j++])
```

Linear in the combined size. This is the merge step from merge-sort.

----------------------------------------

## Step 5: Trace on the Example

Tree 1 in-order: 1, 2, 4.
Tree 2 in-order: 0, 1, 3.

Merge:
```
i=0, j=0: L1[0]=1, L2[0]=0. 0 smaller. Append 0. j=1. result=[0].
i=0, j=1: L1[0]=1, L2[1]=1. 1 <= 1, append L1. i=1. result=[0, 1].
i=1, j=1: L1[1]=2, L2[1]=1. 1 smaller. Append 1. j=2. result=[0, 1, 1].
i=1, j=2: L1[1]=2, L2[2]=3. 2 smaller. Append 2. i=2. result=[0, 1, 1, 2].
i=2, j=2: L1[2]=4, L2[2]=3. 3 smaller. Append 3. j=3. result=[0, 1, 1, 2, 3].
j=3, L2 exhausted. Append rest of L1: 4. result=[0, 1, 1, 2, 3, 4].
```

Final: `[0, 1, 1, 2, 3, 4]`. ✓

----------------------------------------

## Step 6: Extra-Sharp Version — Interleaved Traversal

The two-step approach (traverse each tree fully, then merge) uses O(N) auxiliary memory for the two lists. For O(h1 + h2) memory, we can interleave: use two BST iterators, comparing their "next" values and emitting whichever is smaller.

This is the **BST iterator merge**:
```
it1 = BSTIterator(tree1)
it2 = BSTIterator(tree2)
result = []
while it1.hasNext() and it2.hasNext():
    if it1.peek() <= it2.peek():
        result.append(it1.next())
    else:
        result.append(it2.next())
# drain whichever is left
while it1.hasNext(): result.append(it1.next())
while it2.hasNext(): result.append(it2.next())
```

This needs a `peek()` method on the iterator (look without advancing). Each iterator holds its pending stack of ancestors — O(h) memory each.

For small trees or simple implementations, the two-list approach is fine. The interleaved version shines when memory is tight and trees are balanced.

----------------------------------------

## Step 7: Name the Pattern

This is a classic **two-sorted-lists merge**, the same operation that powers merge-sort's merge step. The twist is that the "sorted lists" here are the in-order traversals of BSTs — which we get for free from the BST structure.

When you see "combine two BSTs" or "combine two sorted streams," merge step is the answer.

----------------------------------------

## Step 8: Complexity

Time: **O(N)** where N = n1 + n2. Each node visited once for traversal, and the merge is linear.

Space: **O(N)** for the two in-order lists and the output. O(h1 + h2) with the iterator approach.

----------------------------------------

## Step 9: C++ Implementation

```cpp
void inorder(TreeNode* node, vector<int>& out) {
    if (!node) return;
    inorder(node->left, out);
    out.push_back(node->val);
    inorder(node->right, out);
}

vector<int> getAllElements(TreeNode* root1, TreeNode* root2) {
    vector<int> L1, L2;
    inorder(root1, L1);
    inorder(root2, L2);

    vector<int> result;
    result.reserve(L1.size() + L2.size());
    int i = 0, j = 0;
    while (i < (int)L1.size() && j < (int)L2.size()) {
        if (L1[i] <= L2[j]) result.push_back(L1[i++]);
        else result.push_back(L2[j++]);
    }
    while (i < (int)L1.size()) result.push_back(L1[i++]);
    while (j < (int)L2.size()) result.push_back(L2[j++]);

    return result;
}
```

Reading the code:
- `inorder` does a standard recursive in-order traversal.
- `reserve` pre-allocates for `L1.size() + L2.size()` to avoid reallocations.
- The merge step handles the case where one list exhausts before the other.

----------------------------------------

## Step 10: Follow-up Questions

- **Merge K BSTs.** Use a min-heap of iterators (similar to Merge K Sorted Lists).
- **Handle unbalanced BSTs (recursion might stack-overflow).** Switch to iterative in-order using explicit stacks.
- **O(1) extra memory** (not counting output). Morris traversal on each tree, interleaved — very fiddly.
- **Intersection of two BSTs (only values in both).** Similar merge, but only emit values equal in both.
- **Symmetric difference (values in exactly one).** Similar merge, emit values from one side but skip if equal.
- **Return sorted unique values.** Skip duplicates during the merge.
