# Design Linked List

**Problem Link:**
https://leetcode.com/problems/design-linked-list/

**Topic:**
Linked List

----------------------------------------

## Step 1: Read the Spec

Design a class `MyLinkedList` (singly or doubly) that supports:
- `get(index)`: return the value at the given index. -1 if out of bounds.
- `addAtHead(val)`: insert at the beginning.
- `addAtTail(val)`: insert at the end.
- `addAtIndex(index, val)`: insert at the given index. If index == size, insert at tail. If index > size, do nothing.
- `deleteAtIndex(index)`: delete the node at the given index if valid.

Design choices:
- **Singly vs doubly linked.** Doubly enables backward traversal but costs more memory.
- **With or without sentinel nodes** (dummy head/tail). Sentinels simplify edge cases.

I'll go with a **singly linked list with a dummy head**. The dummy head eliminates special cases for head operations.

----------------------------------------

## Step 2: Why a Dummy Head Helps

Every operation that involves insertion or deletion at the head has special cases in a raw singly linked list: updating the head pointer itself. With a dummy head:

- `addAtHead` becomes just "insert after dummy."
- `deleteAtIndex(0)` becomes "delete after dummy."
- No null checks for "is this the head?"

The tradeoff: one extra node always exists. Worth it.

----------------------------------------

## Step 3: Data Members

```cpp
class MyLinkedList {
    struct Node {
        int val;
        Node* next;
        Node(int v) : val(v), next(nullptr) {}
    };
    Node* dummy;   // always present; dummy->next is the real head
    int size;
public:
    MyLinkedList() : dummy(new Node(-1)), size(0) {}
    // ...
};
```

`dummy->next` points to the actual first real node. `size` tracks the count of real nodes (excluding dummy).

----------------------------------------

## Step 4: Implement Each Operation

**get(index):**
- If index out of range, return -1.
- Walk from dummy, step `index + 1` times (past dummy, then `index` more).
- Return that node's value.

**addAtHead(val):**
- Insert after dummy. Equivalent to `addAtIndex(0, val)`.

**addAtTail(val):**
- Walk to the last node (dummy + size steps), then insert after.
- Equivalent to `addAtIndex(size, val)`.

**addAtIndex(index, val):**
- If index < 0 or index > size, do nothing.
- Walk to the node at position `index - 1` (the one before where we want to insert). For index = 0, that's dummy.
- Insert new node between that node and its current next.

**deleteAtIndex(index):**
- If index out of range, do nothing.
- Walk to position `index - 1`. Splice out the node at index.

In all cases, the "walking" is done from the dummy head.

----------------------------------------

## Step 5: The Walk Helper

A common helper `nodeBefore(i)` returns a pointer to the node just before position i. That's the node we modify for insertion/deletion at position i.

```cpp
Node* nodeBefore(int i) {
    // Precondition: 0 <= i <= size
    Node* cur = dummy;
    for (int k = 0; k < i; ++k) cur = cur->next;
    return cur;
}
```

If `i == 0`, returns `dummy` (nothing before position 0 except the dummy). If `i == size`, returns the last real node.

With this helper, the operations become almost trivial.

----------------------------------------

## Step 6: Putting It All Together

```cpp
class MyLinkedList {
    struct Node {
        int val;
        Node* next;
        Node(int v) : val(v), next(nullptr) {}
    };
    Node* dummy;
    int size;

    Node* nodeBefore(int i) {
        Node* cur = dummy;
        for (int k = 0; k < i; ++k) cur = cur->next;
        return cur;
    }

public:
    MyLinkedList() : dummy(new Node(-1)), size(0) {}

    int get(int index) {
        if (index < 0 || index >= size) return -1;
        Node* before = nodeBefore(index);
        return before->next->val;
    }

    void addAtHead(int val) { addAtIndex(0, val); }
    void addAtTail(int val) { addAtIndex(size, val); }

    void addAtIndex(int index, int val) {
        if (index < 0 || index > size) return;
        Node* before = nodeBefore(index);
        Node* newNode = new Node(val);
        newNode->next = before->next;
        before->next = newNode;
        size++;
    }

    void deleteAtIndex(int index) {
        if (index < 0 || index >= size) return;
        Node* before = nodeBefore(index);
        Node* target = before->next;
        before->next = target->next;
        delete target;
        size--;
    }
};
```

Each operation:
- Bounds check the index.
- Walk to the "node before" the target position.
- Splice in/out.

----------------------------------------

## Step 7: Trace a Quick Example

Operations:
1. `addAtHead(1)`: list becomes `[1]`.
2. `addAtTail(3)`: `[1, 3]`.
3. `addAtIndex(1, 2)`: `[1, 2, 3]`.
4. `get(1)`: returns 2.
5. `deleteAtIndex(1)`: `[1, 3]`.
6. `get(1)`: returns 3.

Let me trace step 3 in detail. Current list: dummy → 1 → 3, size=2.

`addAtIndex(1, 2)`:
- Index 1 in range [0, 2], OK.
- `nodeBefore(1)` walks: cur=dummy, k=0: cur = dummy->next = Node(1). Return Node(1).
- `newNode = Node(2)`.
- `newNode->next = cur->next = Node(3)`.
- `cur->next = newNode`.
- size = 3.

List: dummy → 1 → 2 → 3.

Step 5, `deleteAtIndex(1)`:
- `nodeBefore(1)` returns Node(1).
- target = Node(1)->next = Node(2).
- Node(1)->next = Node(2)->next = Node(3).
- Delete Node(2). size = 2.

List: dummy → 1 → 3.

----------------------------------------

## Step 8: Complexity

Each operation: **O(n)** worst case (walking to the right index). The "walk" dominates.

Space: O(n) for n nodes.

Note: `addAtHead` is O(1) (index 0, walk just to dummy). `addAtTail` is O(n) because we must walk to the end. A **tail pointer** would make `addAtTail` O(1) too, at the cost of more code.

----------------------------------------

## Step 9: Name It

This is a **standard linked-list data structure**, implemented from scratch. Design techniques at play:
- **Sentinel / dummy head** to eliminate edge cases.
- **Explicit size** to enable O(1) bounds checks and `addAtTail` parameterization.
- **Generic "walk-to-position" helper** to deduplicate index arithmetic.

Real-world C++ `std::list` is doubly-linked with sentinels for O(1) tail access. For interview, this simpler version is fine.

----------------------------------------

## Step 10: Complexity Summary

| Operation | Time |
|---|---|
| get | O(n) |
| addAtHead | O(1) |
| addAtTail | O(n) |
| addAtIndex | O(n) |
| deleteAtIndex | O(n) |

----------------------------------------

## Step 11: Follow-up Questions

- **Doubly-linked version.** Each node has a `prev` pointer. Enables O(1) deletion given a node, and O(1) tail access (with tail pointer).
- **Add a tail pointer to make addAtTail O(1).** Update tail on every modification.
- **Thread-safe version.** Add locks or use lock-free concurrent linked lists.
- **Handle memory carefully.** Delete nodes on `deleteAtIndex`. In the destructor, delete all remaining.
- **Generic templated version (any value type).** Templatize `Node` and the class.
- **Skip list variant.** O(log n) operations on average with probabilistic structure.
