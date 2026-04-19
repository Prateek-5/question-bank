# Linked List — Concepts Guide

----------------------------------------

## 1. Introduction

Linked lists are deceptively simple — a chain of nodes with pointers — but their problems are beloved by interviewers because they demand precise pointer handling without the safety net of random access. Master them and you've mastered pointer thinking.

----------------------------------------

## 2. Real-Life Analogy

Imagine a treasure hunt where each clue points to the next location. You can only find the 5th clue by reading the first four in sequence — no shortcut. That's a linked list: each node holds a piece of data and a pointer to the next, and you always start from the head.

----------------------------------------

## 3. Core Idea

A linked list is a sequence of nodes, each holding a value and a pointer to the next. Operations are O(n) for random access but O(1) for insertion and deletion at a known position. Most linked-list problems revolve around pointer manipulation: reversing, merging, finding middle/end, detecting cycles. A **dummy head node** is a common technique to simplify edge cases.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Reach for linked-list thinking when:

- **Dynamic sizing is needed** with frequent inserts/deletes.
- **Random access isn't required.**
- **The problem explicitly gives a linked list.**
- **Memory fragmentation is a concern** (though rare in interviews).

----------------------------------------

## 5. Types / Variations

- **Singly linked list:** one `next` pointer per node.
- **Doubly linked list:** `next` and `prev` pointers, enabling backward traversal.
- **Circular linked list:** tail links back to head.
- **Skip list:** hierarchical linked list with O(log n) search, used by Redis.

----------------------------------------

## 6. Step-by-Step Working

**Reverse a singly linked list:**
1. prev = null, cur = head.
2. While cur:
   - Save `next = cur.next`.
   - `cur.next = prev`.
   - `prev = cur; cur = next`.
3. Return `prev` as the new head.

**Find the middle (Floyd):**
1. slow = fast = head.
2. While fast and fast.next: slow = slow.next; fast = fast.next.next.
3. Return slow.

**Detect cycle (Floyd):**
1. Same as middle-finding.
2. If slow == fast at any point, cycle exists.

----------------------------------------

## 7. Visual Explanation

**Reversing `1 → 2 → 3 → null`:**

```
Start:  prev=null,  cur=1,  [1 → 2 → 3]
Step 1: prev=1,     cur=2,  [1] [2 → 3]   (1 now points to null)
Step 2: prev=2,     cur=3,  [2 → 1] [3]
Step 3: prev=3,     cur=null, [3 → 2 → 1]
Return prev → head of reversed list = 3
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x): val(x), next(nullptr) {}
};

// Reverse
ListNode* reverse(ListNode* head) {
    ListNode* prev = nullptr;
    while (head) {
        auto* next = head->next;
        head->next = prev;
        prev = head;
        head = next;
    }
    return prev;
}

// Middle (Floyd)
ListNode* middle(ListNode* head) {
    auto s = head, f = head;
    while (f && f->next) {
        s = s->next;
        f = f->next->next;
    }
    return s;
}

// Merge two sorted lists (dummy-head pattern)
ListNode* merge(ListNode* a, ListNode* b) {
    ListNode dummy(0);
    auto* t = &dummy;
    while (a && b) {
        if (a->val <= b->val) { t->next = a; a = a->next; }
        else { t->next = b; b = b->next; }
        t = t->next;
    }
    t->next = a ? a : b;
    return dummy.next;
}
```

----------------------------------------

## 9. Common Mistakes

- **Losing the head pointer** by overwriting it.
- **Null dereference** — always null-check before `.next`.
- **Missing the dummy head trick** — it simplifies insert/delete at the head.
- **Forgetting to null-terminate** after rewiring — leads to cycles.
- **Stack overflow on recursive solutions** — use iterative when lists are long.

----------------------------------------

## 10. Interview Insights

Linked-list questions test pointer precision. Interviewers want to see:

1. **Clean use of a dummy head** when appropriate.
2. **Careful pointer rewiring** without cycles or lost nodes.
3. **Slow/fast pointer recognition** for cycle and middle problems.
4. **Edge cases:** empty list, single node, exactly two nodes.

Draw the pointer diagram before coding. It's the single best way to avoid bugs.
