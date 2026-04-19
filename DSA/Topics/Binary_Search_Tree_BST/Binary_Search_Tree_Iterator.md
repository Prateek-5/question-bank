# Binary Search Tree Iterator

**Problem Link:**
https://leetcode.com/problems/binary-search-tree-iterator/

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: What's an "Iterator" for a BST?

Design a class that simulates a **forward iterator** over a BST's values in **sorted order** (equivalent to in-order traversal). The class needs:
- `BSTIterator(root)` — constructor.
- `next()` — return the next (smallest unreturned) value.
- `hasNext()` — is there another value to return?

Key constraint: `next()` and `hasNext()` should run in **O(1) average time**, and total memory should be **O(h)** where h is the tree's height.

Example:
```
    7
   / \
  3   15
      / \
     9   20
```

The sorted (in-order) values are: 3, 7, 9, 15, 20.

```
it = BSTIterator(root)
it.next()     → 3
it.next()     → 7
it.hasNext()  → true
it.next()     → 9
...
```

----------------------------------------

## Step 2: The Naive Approach — Flatten Upfront

Do a full in-order traversal in the constructor, store all values in an array, and use a running index for `next()` and `hasNext()`.

```cpp
class BSTIterator {
    vector<int> values;
    int idx = 0;
public:
    BSTIterator(TreeNode* root) { inorder(root, values); }
    int next() { return values[idx++]; }
    bool hasNext() { return idx < (int)values.size(); }
};
```

Works. `next` and `hasNext` are O(1). But memory is **O(n)** — we store every value. The problem wants O(h), where h can be much smaller than n (for a balanced BST, h = log n).

Can we do the in-order traversal "lazily" — compute each next value on-demand?

----------------------------------------

## Step 3: What Does In-Order "Want" at Each Step?

In-order traversal visits: left subtree, then node, then right subtree. If we were doing it recursively, the call stack implicitly tracks "where we are." Can we make that stack explicit and pause/resume it?

Yes. Here's the pattern:
- To visit a subtree in-order, first walk all the way down its **left spine**, pushing each node onto a stack.
- When we pop a node, we've "visited" it — return its value.
- Then move to its right child and repeat the left-spine walk.

The stack holds nodes whose values are yet to be returned, waiting for us to process their subtrees.

----------------------------------------

## Step 4: The Algorithm

```
constructor(root):
    stack = []
    pushLeftSpine(root)

pushLeftSpine(node):
    while node:
        stack.push(node)
        node = node.left

next():
    node = stack.pop()
    # before returning, prepare stack for the next call
    pushLeftSpine(node.right)
    return node.val

hasNext():
    return not stack.empty()
```

Reading the algorithm:
- After the constructor, the stack holds the left spine starting from the root — these are the smallest values, with the top being the smallest.
- When `next()` is called, the top is the smallest unvisited value. Pop it, return it.
- But before returning, we need to make sure the stack's next top is the next-smallest value. That's done by pushing the left spine of the popped node's right child.

Why does this work? In in-order traversal, after visiting a node, we go into its right subtree. And for the right subtree, the next value to visit is its leftmost — which is what `pushLeftSpine` queues up.

----------------------------------------

## Step 5: Trace Through an Example

Tree:
```
    7
   / \
  3   15
      / \
     9   20
```

Constructor: pushLeftSpine(7). Walk 7 → 3 → null. Stack = [7, 3].

```
next() call 1:
  pop 3. Stack = [7].
  pushLeftSpine(3.right = null). No-op.
  return 3.

next() call 2:
  pop 7. Stack = [].
  pushLeftSpine(7.right = 15). Walk 15 → 9 → null. Stack = [15, 9].
  return 7.

next() call 3:
  pop 9. Stack = [15].
  pushLeftSpine(9.right = null). No-op.
  return 9.

next() call 4:
  pop 15. Stack = [].
  pushLeftSpine(15.right = 20). Walk 20 → null. Stack = [20].
  return 15.

next() call 5:
  pop 20. Stack = [].
  pushLeftSpine(20.right = null). No-op.
  return 20.

hasNext() → false.
```

Sequence: 3, 7, 9, 15, 20. ✓ Matches in-order traversal.

----------------------------------------

## Step 6: Why O(1) Average Per Call?

Each node is pushed onto the stack exactly once (across the entire iteration) and popped exactly once. So the **total** work across n calls to `next()` is O(n). Amortized per call: O(1).

Some individual `next()` calls might be O(h) (if pushing a long left spine), but most are O(1) (empty right subtree). Averaged out, O(1) per call.

This is the amortized-O(1) trade-off: rare expensive operations compensated by many cheap ones.

----------------------------------------

## Step 7: Why O(h) Space?

The stack only holds ancestors of the "current cursor position" — at most h at any moment (where h is the tree height). In a balanced BST, h = log n; in a skewed one, h = n.

For a balanced BST with n = 10^6, that's log 10^6 ≈ 20 stack entries. Much better than 10^6 for the flatten-upfront approach.

----------------------------------------

## Step 8: Name It

This is the classic **lazy in-order traversal** using an explicit stack. The pattern generalizes:
- Iterators over sorted sets / maps (built into most standard libraries).
- "On-demand" traversals where full materialization is too expensive.
- Coroutines / generators in languages that support them (Python's `yield`, JavaScript generators).

The key idea — maintain minimal state to resume traversal — applies anywhere you need lazy evaluation.

----------------------------------------

## Step 9: Complexity

Time: `next()` is **O(1) amortized**. `hasNext()` is **O(1)**. Constructor is **O(h)** (pushing the initial left spine).

Space: **O(h)** for the stack.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class BSTIterator {
    stack<TreeNode*> st;

    void pushLeft(TreeNode* node) {
        while (node) {
            st.push(node);
            node = node->left;
        }
    }

public:
    BSTIterator(TreeNode* root) {
        pushLeft(root);
    }

    int next() {
        TreeNode* node = st.top(); st.pop();
        pushLeft(node->right);     // prepare for next in-order step
        return node->val;
    }

    bool hasNext() {
        return !st.empty();
    }
};
```

Reading the code:
- The stack holds nodes whose values haven't been returned yet, in order (top = next to return).
- `pushLeft` builds up the left spine — all ancestors plus the leftmost path.
- `next()` pops the top, queues up its right subtree's left spine, returns the value.
- The invariant "stack.top() is always the next node in in-order order" is maintained throughout.

----------------------------------------

## Step 11: Follow-up Questions

- **Support `prev()` (backward iteration).** Maintain a second stack of the right spine, or use a doubly-linked traversal — trickier.
- **Support random-access (jump to kth).** Augment BST nodes with subtree sizes; compute k-th in O(log n) per call.
- **Iterator with filtering (only return values in a range [lo, hi]).** Skip nodes outside the range; use BST property to prune.
- **Thread-safe iterator.** Lock during pushes/pops, or use snapshot-based iteration.
- **Why not Morris traversal?** Morris is also O(1) space but modifies the tree during iteration, which is generally unacceptable for a library iterator.
- **What if the tree is modified during iteration?** Standard iterators in most libraries are invalidated. You'd need a version-tagged iterator or copy-on-iterate semantics.
