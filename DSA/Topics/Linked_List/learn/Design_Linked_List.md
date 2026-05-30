# Design Linked List — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Design_Linked_List.md`](../Design_Linked_List.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/design-linked-list/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/design-linked-list/</a>

---

## How to use this file

Paced for someone seeing linked lists for the first time. Reading time: ~25 minutes. **This is THE introduction to linked-list primitives.** Every subsequent problem (reverse, merge, cycle detection, palindrome) assumes you can manipulate nodes confidently — pull out a node, splice in a new one, walk to a position. The lesson: **two design moves — dummy head + walk-to-predecessor helper — collapse most edge cases.**

**Map of this file (11 short sections):**

1. What's a linked list?
2. Singly vs doubly — and what we'll use
3. Read the problem
4. The dummy head trick — why it exists
5. The walk-to-predecessor helper
6. Each operation, mapped to the helper
7. Code
8. Trace it
9. Memory in C++ — a note
10. Common pitfalls
11. The shape — primitives you'll reuse forever

---

## 1. What's a linked list?

> **Mini-refresher: linked list vs array.**
>
> **Array** (e.g., `int[]`, `std::vector`, Python `list`): contiguous block of memory. Random access is O(1) (jump to `address + index × size`). But INSERTING or DELETING in the middle is O(n) (must shift everything after).
>
> **Linked list**: a chain of NODES, each holding (1) a value and (2) a pointer to the next node. NO contiguous memory. Random access is O(n) (must walk from the start). But INSERTING or DELETING in the middle is O(1) GIVEN A POINTER to the predecessor.
>
> Picture:
>
> ```
> [val=4 | next] → [val=5 | next] → [val=1 | next] → null
>     head           second           tail
> ```
>
> The `head` pointer is your only handle. You can ONLY walk forward (in a SINGLY linked list).
>
> Compare:
>
> | Operation | Array | Linked list |
> |---|---|---|
> | Access index i | O(1) | O(n) |
> | Insert at front | O(n) (shift) | O(1) |
> | Insert at back (with tail ptr) | O(1) amortized | O(1) |
> | Insert at index | O(n) | O(n) walk + O(1) splice |
> | Delete at index | O(n) | O(n) walk + O(1) splice |

---

## 2. Singly vs doubly — and what we'll use

- **Singly linked**: each node has ONE pointer, `next`. Can only walk forward. Cheap memory.
- **Doubly linked**: each node has TWO pointers, `next` and `prev`. Can walk in both directions. Lets you delete a given node in O(1) without needing the predecessor. Double memory cost per node.

We'll build a **singly linked list**. Add a dummy head for clean edge cases. Most interview problems assume singly linked.

---

## 3. Read the problem

Design `MyLinkedList` with these operations:

| Operation | What it does |
|---|---|
| `get(index)` | Return the value at the given index. Return `-1` if `index` is out of range. |
| `addAtHead(val)` | Insert a new node with value `val` at the FRONT. |
| `addAtTail(val)` | Insert a new node with value `val` at the END. |
| `addAtIndex(index, val)` | Insert before the node at `index`. If `index == size`, becomes addAtTail. If `index > size`, do nothing. |
| `deleteAtIndex(index)` | Delete the node at `index`, if `index` is valid. |

Index is 0-based. The class should track its own size.

**Example sequence:**

```
addAtHead(1);             → [1]
addAtTail(3);             → [1, 3]
addAtIndex(1, 2);          → [1, 2, 3]
get(1);                    → 2
deleteAtIndex(1);         → [1, 3]
get(1);                    → 3
```

---

## 4. The dummy head trick — why it exists

Consider this scenario WITHOUT a dummy head: you want to delete the node at index 0. You must:
- Update the external `head` pointer to point to the new first node.
- Free the old head.

Every operation that affects index 0 (insert, delete) is a SPECIAL CASE — does it modify `head` itself, or does it modify some node's `next`? Without the dummy, you write two pieces of logic.

**With a dummy head:** prepend a sentinel node `dummy` whose `next` points to the real first node. Now `dummy.next` IS the head. Operations on "index 0" become operations on "dummy's next pointer" — exactly like operations on any other position.

> **Mini-refresher: dummy head = sentinel = no-special-case node.**
>
> A **sentinel** is a non-content node added to simplify boundary logic. The dummy head holds no real value (set it to anything, like `-1`). Its only purpose: provide a "predecessor" for the real head, so head operations look like any other operation.
>
> Many real-world implementations use dummy heads AND dummy tails (in doubly linked). `std::list` in C++ does this.
>
> Cost: one extra node. Benefit: no `if (index == 0)` special cases anywhere.

```
Without dummy:                With dummy:
head → A → B → C → null      dummy → A → B → C → null
^                              ^
external pointer               external pointer; dummy.next = first real node
```

---

## 5. The walk-to-predecessor helper

Every operation that inserts at or deletes at index `i` needs access to the node at position `i - 1` (the node WHOSE NEXT POINTER WILL CHANGE).

- For insert at `i`: we set `prev.next = newNode; newNode.next = (old prev.next)`.
- For delete at `i`: we set `prev.next = prev.next.next`.

So a helper `nodeBefore(i)` that returns "the node just BEFORE position i" is the right primitive.

- `nodeBefore(0)` returns `dummy` (nothing is before position 0 except the dummy).
- `nodeBefore(i)` for `i > 0` returns the node at logical position `i - 1`.

```
nodeBefore(i):
    cur = dummy
    for k in 0..i-1:
        cur = cur.next
    return cur
```

**Important:** for this helper to work, the caller must ensure `0 <= i <= size`. If `i > size`, walking would dereference null. Validate `i` BEFORE calling.

> **Mini-refresher: 0-based indexing and "node before position i".**
>
> "Position 0" is the first real node, "position 1" is the second, etc. So `nodeBefore(0)` is the dummy itself (no position -1), and `nodeBefore(size)` is the last real node (the one whose next would be null).
>
> Walking `i` steps from `dummy` lands you at the node before position `i`.

---

## 6. Each operation, mapped to the helper

**`get(index)`:**

```
if index < 0 or index >= size: return -1
prev = nodeBefore(index)
return prev.next.val
```

**`addAtHead(val)`:** delegates to `addAtIndex(0, val)`.

**`addAtTail(val)`:** delegates to `addAtIndex(size, val)`.

**`addAtIndex(index, val)`:**

```
if index < 0 or index > size: return     # NOTE: > size, not >= size (insertion at "end" is valid)
prev = nodeBefore(index)
newNode = Node(val)
newNode.next = prev.next                  # link new node to what came after
prev.next = newNode                       # link prev to new node
size += 1
```

> **Mini-refresher: the order of pointer assignments is CRITICAL.**
>
> Two pointer updates: `newNode.next = prev.next` THEN `prev.next = newNode`.
>
> If you reverse the order:
> ```
> prev.next = newNode      # ← prev.next now points to newNode, OVERWRITING the path to the rest
> newNode.next = prev.next # ← now newNode.next = newNode (self-loop!)
> ```
>
> You've created a cycle. Always update `newNode`'s outgoing pointer FIRST, then redirect `prev`'s pointer.

**`deleteAtIndex(index)`:**

```
if index < 0 or index >= size: return
prev = nodeBefore(index)
target = prev.next
prev.next = target.next
delete target    # C++ only
size -= 1
```

The `target` is the node BEING removed. `prev.next` now skips it.

---

## 7. Code

**C++:**

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
        return nodeBefore(index)->next->val;
    }

    void addAtHead(int val) { addAtIndex(0, val); }
    void addAtTail(int val) { addAtIndex(size, val); }

    void addAtIndex(int index, int val) {
        if (index < 0 || index > size) return;
        Node* prev = nodeBefore(index);
        Node* newNode = new Node(val);
        newNode->next = prev->next;
        prev->next = newNode;
        size++;
    }

    void deleteAtIndex(int index) {
        if (index < 0 || index >= size) return;
        Node* prev = nodeBefore(index);
        Node* target = prev->next;
        prev->next = target->next;
        delete target;
        size--;
    }
};
```

**Python:**

```python
class Node:
    def __init__(self, v):
        self.val = v
        self.next = None

class MyLinkedList:
    def __init__(self):
        self.dummy = Node(-1)
        self.size = 0

    def _nodeBefore(self, i):
        cur = self.dummy
        for _ in range(i):
            cur = cur.next
        return cur

    def get(self, index):
        if index < 0 or index >= self.size:
            return -1
        return self._nodeBefore(index).next.val

    def addAtHead(self, val):
        self.addAtIndex(0, val)

    def addAtTail(self, val):
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index, val):
        if index < 0 or index > self.size:
            return
        prev = self._nodeBefore(index)
        new_node = Node(val)
        new_node.next = prev.next
        prev.next = new_node
        self.size += 1

    def deleteAtIndex(self, index):
        if index < 0 or index >= self.size:
            return
        prev = self._nodeBefore(index)
        prev.next = prev.next.next
        self.size -= 1
```

**Complexity (per operation):**

| Op | Time |
|---|---|
| `get` | O(n) |
| `addAtHead` | O(1) |
| `addAtTail` | O(n) |
| `addAtIndex` | O(n) |
| `deleteAtIndex` | O(n) |

`addAtHead` is O(1) because `nodeBefore(0)` walks 0 steps (returns dummy immediately). `addAtTail` is O(n) because we walk to the end. With a tail pointer, `addAtTail` becomes O(1) too.

---

## 8. Trace it

Sequence: `addAtHead(1); addAtTail(3); addAtIndex(1, 2); get(1); deleteAtIndex(1); get(1)`.

```
Initial: dummy → null. size = 0.

addAtHead(1) = addAtIndex(0, 1):
  prev = nodeBefore(0) = dummy.
  newNode = Node(1).
  newNode.next = prev.next = null.
  prev.next = newNode.
  dummy → 1 → null. size = 1.

addAtTail(3) = addAtIndex(1, 3):
  prev = nodeBefore(1):
    cur = dummy. k=0: cur = dummy.next = Node(1). Return Node(1).
  newNode = Node(3).
  newNode.next = Node(1).next = null.
  Node(1).next = newNode.
  dummy → 1 → 3 → null. size = 2.

addAtIndex(1, 2):
  prev = nodeBefore(1) = Node(1).
  newNode = Node(2).
  newNode.next = Node(1).next = Node(3).
  Node(1).next = newNode.
  dummy → 1 → 2 → 3 → null. size = 3.

get(1):
  prev = nodeBefore(1) = Node(1).
  return Node(1).next.val = Node(2).val = 2.  ✓

deleteAtIndex(1):
  prev = nodeBefore(1) = Node(1).
  target = Node(2).
  Node(1).next = Node(2).next = Node(3).
  dummy → 1 → 3 → null. size = 2.

get(1):
  prev = nodeBefore(1) = Node(1).
  return Node(1).next.val = Node(3).val = 3.  ✓
```

Notice: the dummy head is invisible to the outside world. Every operation goes through it cleanly.

---

## 9. Memory in C++ — a note

C++ does NOT garbage collect. When you `delete` a node, you free its memory. If you `new` a node and never `delete` it, you leak.

In `deleteAtIndex`, we `delete target` after rewiring. Without that, the node sits in memory forever.

The class destructor (not shown above for brevity) should walk the list and `delete` every node, including the dummy. In production code, prefer `std::unique_ptr<Node>` for automatic cleanup.

In garbage-collected languages (Java, Python, JS), you don't need to `delete` — once no pointer references the node, the GC reclaims it.

---

## 10. Common pitfalls

1. **Forgetting the dummy head.** Then `addAtIndex(0, ...)` needs a special case to update the external head pointer. Doubles your bug surface.

2. **Wrong pointer-update order.** Always assign `newNode.next` BEFORE redirecting `prev.next`. Reversing creates self-loops or loses the rest of the list.

3. **Off-by-one in `nodeBefore`.** Walking `i` steps from dummy lands you at the node BEFORE position `i`. Walking `i + 1` steps would land AT position `i`. Pick one and stay consistent.

4. **`addAtIndex` bound check uses `>= size`.** Wrong. `index == size` is valid (insert at end). Use `> size`.

5. **`deleteAtIndex` and `get` bound check uses `> size - 1`.** Use `>= size` for clarity. Or `>= size` directly.

6. **Walking past `null` in `nodeBefore`.** If `i > size`, the helper dereferences `null`. The caller MUST validate before calling.

7. **Forgetting `size` updates.** Every add increments; every delete decrements. Skip and `get` lies.

8. **Returning the dummy's value on out-of-range `get`.** Should return -1. Bounds check FIRST.

9. **In C++, the dummy is stack-allocated but holds heap nodes.** OK as long as the class isn't destroyed mid-use. The destructor should walk and delete heap nodes.

10. **Not testing the all-empty edge cases.** `get(0)` on empty list should return -1. `deleteAtIndex(0)` on empty list should be no-op. Test these.

---

## 11. The shape — primitives you'll reuse forever

The two ideas in this problem — **dummy head** and **walk-to-predecessor** — appear in nearly every linked list problem:

| Pattern | Why dummy head + walk help |
|---|---|
| **This problem** | direct application |
| Remove Linked List Elements | dummy head so head-removal looks like any other removal |
| Reverse Linked List II (reverse a sublist) | dummy head for clean boundary handling |
| Merge Two Sorted Lists | dummy head to build the merged list |
| Remove Duplicates from Sorted List II | dummy head + walk |
| Partition List | dummy heads (two of them) |
| Add Two Numbers | dummy head for the result list |
| Odd Even Linked List | dummy-style sentinels |

**Pattern to internalize:**

> "For any linked-list problem where modifications at the head are possible, prepend a dummy. For any operation that needs to splice in/out at position i, walk to the node BEFORE i (the one whose pointer changes)."

These two ideas are scaffolding for almost every linked-list algorithm. Master them here; reuse them everywhere.

---

> **Self-check — the question to ask next time.**
>
> When you face a linked-list problem with insertions or deletions, ask:
>
> > **"Would a dummy head make head modifications look like any other? And do I really want a pointer to the NODE BEFORE the one I'm modifying?"**
>
> Almost always: yes to both.

---

## Cross-references

- **Reference card (post-mastery):** [`../Design_Linked_List.md`](../Design_Linked_List.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Delete_Node_in_a_Linked_List.md`](./Delete_Node_in_a_Linked_List.md), [`Remove_Linked_List_Elements.md`](./Remove_Linked_List_Elements.md).
  - Coming after: [`Reverse_Linked_List.md`](./Reverse_Linked_List.md) — THE foundational pointer-manipulation pattern.
