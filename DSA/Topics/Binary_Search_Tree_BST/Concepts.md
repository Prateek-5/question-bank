# Binary Search Tree (BST) — Concepts

## Core Theory
A BST maintains the invariant that for every node, left subtree keys < node < right subtree keys. In-order traversal yields keys in sorted order. Balanced BSTs (red-black, AVL) guarantee O(log n) operations; unbalanced may degrade to O(n).

## Common Patterns
- **In-order traversal** for sorted operations.
- **Divide-and-conquer via median** for converting sorted arrays to balanced BSTs.
- **BST property pruning** when searching a range or finding LCA.
- **Iterator via stack** for O(1) amortized `next()`.

## When to Use
When ordered operations and dynamic inserts/deletes are both required. Use heaps if order-statistics are less important.

## Template
```cpp
struct Node { int val; Node *l, *r; };
Node* insert(Node* r, int v) {
    if (!r) return new Node{v, nullptr, nullptr};
    if (v < r->val) r->l = insert(r->l, v);
    else r->r = insert(r->r, v);
    return r;
}
```

## Common Mistakes
- Assuming tree is balanced — worst-case O(n) if not.
- Duplicate-key policies (left vs right vs ignore).
- Not restoring BST invariants after deletion.
