# Binary Search Tree Iterator — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Search_Tree_Iterator.md`](../Binary_Search_Tree_Iterator.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/binary-search-tree-iterator/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/binary-search-tree-iterator/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: encapsulate ITERATIVE INORDER traversal as a class with `next()` and `hasNext()`. The stack stores the LEFT SPINE of "yet-to-visit" nodes. O(1) amortized per call, O(h) space.** **Read [`Binary_Tree_Inorder_Traversal_Iterative.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal_Iterative.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The naive O(n) approach
3. The lazy iterator idea
4. The state — left-spine stack
5. The next() operation
6. Code
7. Trace it
8. Why O(1) amortized
9. The shape — pause/resume iteration

---

## 1. Read the problem

Design a class `BSTIterator` that produces a BST's values **in sorted (inorder) order**, one at a time.

API:
- `BSTIterator(root)`: constructor.
- `int next()`: return the next smallest value (1-indexed by call).
- `boolean hasNext()`: is there another value?

**Constraints:** `next()` and `hasNext()` should be **O(1) amortized** time. Memory should be **O(h)** (tree height), NOT O(n).

**Example:**
```
    7
   / \
  3   15
      / \
     9   20
```
Inorder: `3, 7, 9, 15, 20`. Calls `next()` should return these in order.

---

## 2. The naive O(n) approach

Build the inorder list in the constructor; index into it.

```python
class BSTIterator:
    def __init__(self, root):
        self.values = []
        self.idx = 0
        def inorder(node):
            if not node: return
            inorder(node.left)
            self.values.append(node.val)
            inorder(node.right)
        inorder(root)
    def next(self): self.idx += 1; return self.values[self.idx - 1]
    def hasNext(self): return self.idx < len(self.values)
```

O(1) next/hasNext, but **O(n) MEMORY** — fails the O(h) requirement.

We want LAZY traversal — compute each next value on demand.

---

## 3. The lazy iterator idea

> **Mini-refresher: how can iterative inorder pause?**
>
> Iterative inorder uses an EXPLICIT STACK (see Inorder Iterative walkthrough). At any point, the stack holds nodes whose left subtree has been pushed but whose value hasn't been visited yet.
>
> The CLOSEST-TO-TOP node is the NEXT to visit.
>
> If we ENCAPSULATE this stack state in an OBJECT, we can pause and resume — exactly what an iterator does.

So: store the stack inside the class. On `next()`, perform ONE inorder step.

---

## 4. The state — left-spine stack

The stack invariant:

> **At any moment, the stack contains the LEFT SPINE of the current "next to visit" node — its ancestors plus itself, with the TOP being the next to visit.**

**Initialization (constructor):**

Push the root, then walk left, pushing every left child encountered. After this, the LEFTMOST NODE is on top of the stack.

```
def push_left_spine(node):
    while node:
        stack.push(node)
        node = node.left
```

This pre-loads the "first batch" of next visits.

---

## 5. The next() operation

**`next()`:**

1. **Pop** the top of the stack — that's the next inorder node. Save its value.
2. **Pre-load** for the future: push the LEFT SPINE of the popped node's RIGHT CHILD (if any). After visiting a node, the next inorder step is into its right subtree (and recursively the leftmost there).
3. **Return** the saved value.

```
def next():
    node = stack.pop()
    push_left_spine(node.right)
    return node.val
```

**`hasNext()`:**

The iterator is exhausted exactly when the stack is empty.

```
def hasNext():
    return len(stack) > 0
```

---

## 6. Code

**C++:**

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
        pushLeft(node->right);
        return node->val;
    }

    bool hasNext() {
        return !st.empty();
    }
};
```

**Python:**

```python
class BSTIterator:
    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node:
            self.stack.append(node)
            node = node.left

    def next(self):
        node = self.stack.pop()
        self._push_left(node.right)
        return node.val

    def hasNext(self):
        return len(self.stack) > 0
```

Complexity: `next()` O(1) amortized; `hasNext()` O(1); memory O(h).

---

## 7. Trace it

**Tree:**
```
    7
   / \
  3   15
      / \
     9   20
```

**Constructor:** push_left(7) → push 7, walk to 3, push 3, walk to null. Stack = `[7, 3]` (3 on top).

```
next() #1:
  Pop 3. Stack = [7].
  push_left(3.right = null) → no-op.
  Return 3.  ✓

next() #2:
  Pop 7. Stack = [].
  push_left(7.right = 15) → push 15, walk to 9, push 9, walk to null. Stack = [15, 9].
  Return 7.  ✓

next() #3:
  Pop 9. Stack = [15].
  push_left(9.right = null) → no-op.
  Return 9.  ✓

next() #4:
  Pop 15. Stack = [].
  push_left(15.right = 20) → push 20, walk to null. Stack = [20].
  Return 15.  ✓

next() #5:
  Pop 20. Stack = [].
  push_left(20.right = null) → no-op.
  Return 20.  ✓

hasNext() → false.
```

Sequence: 3, 7, 9, 15, 20. ✓

---

## 8. Why O(1) amortized

Each tree node is PUSHED onto the stack ONCE (across the entire iterator's lifetime) and POPPED ONCE.

Total push + pop operations: `2n`. Spread across `n` calls to `next()`: **O(1) amortized per call.**

A SINGLE `next()` might take O(h) (when push_left walks a long left spine). But across many calls, the average is O(1).

This is the SAME amortized analysis as the two-stack-queue (Implement Queue using Stacks). Expensive operations are RARE and compensate for cheap ones.

---

## 9. The shape — pause/resume iteration

The pattern this problem teaches:

> **"To EXPOSE an iterative algorithm as an iterator object (next/hasNext), encapsulate the algorithm's state (stack, counters, pointers) in the object. Each call does ONE step of the algorithm."**

Where this applies:

| Iterator | Underlying algorithm | State |
|---|---|---|
| **This problem** (BST Iterator) | iterative inorder | left-spine stack |
| Peeking Iterator | wrap another iterator | next-value cache |
| Range iterator | sequential walk | current index |
| Linked List Iterator | traversal | current pointer |
| Generator (Python `yield`) | any iterative algorithm | suspended execution state |

**Pattern to internalize:**

> "Iterators encapsulate ITERATIVE ALGORITHMS as objects. Replace recursion (which requires the full computation to run) with an explicit stack + step-at-a-time interface."

---

> **Self-check — the question to ask next time.**
>
> When asked to design an iterator over a tree (or any recursive structure), ask:
>
> > **"Can I encapsulate ITERATIVE inorder (or whatever traversal) in a class? The stack holds the resumption state."**
>
> If yes, you've got an O(1)-amortized lazy iterator.

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Search_Tree_Iterator.md`](../Binary_Search_Tree_Iterator.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Smallest_Element_in_BST.md`](./Kth_Smallest_Element_in_BST.md), [`Range_Sum_of_BST.md`](./Range_Sum_of_BST.md).
  - [`../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal_Iterative.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Inorder_Traversal_Iterative.md).
