# Merge K Sorted Lists — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Merge_K_Sorted_Lists.md`](../Merge_K_Sorted_Lists.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/merge-k-sorted-lists/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **THE canonical K-way merge problem.** The lesson: **MIN-HEAP of K heads. Pop the smallest, append to output, push its next.** O(N log K) — beats the O(NK) naive scan-all-heads approach. **Read [`Merge_Two_Sorted_Lists.md`](../../Linked_List/learn/Merge_Two_Sorted_Lists.md) first.**

**Map of this file (8 sections):**

1. Read the problem
2. Two-list merge (the warm-up)
3. The O(NK) naive: scan all heads
4. The O(N log K) heap approach
5. Code
6. Trace it
7. The divide-and-conquer alternative
8. The shape — K-way merge

---

## 1. Read the problem

Given an array of K sorted linked lists, merge them into one sorted linked list and return its head.

**Example:** lists = `[[1, 4, 5], [1, 3, 4], [2, 6]]`.

Merged: `1 → 1 → 2 → 3 → 4 → 4 → 5 → 6`.

---

## 2. Two-list merge (the warm-up)

Merging TWO sorted lists is classic: walk both with pointers, pick the smaller head, advance.

```python
def merge_two(a, b):
    dummy = Node(0)
    tail = dummy
    while a and b:
        if a.val <= b.val:
            tail.next = a; a = a.next
        else:
            tail.next = b; b = b.next
        tail = tail.next
    tail.next = a if a else b
    return dummy.next
```

O(n + m). The natural starting point.

Now extend to K lists.

---

## 3. The O(NK) naive: scan all heads

Repeatedly: find the SMALLEST among all K current heads. Append it. Advance that list's pointer.

```
while any list non-empty:
    smallest = list with the smallest current head
    append smallest.head to output
    advance smallest's pointer
```

Per "step" (one node output): O(K) to find the smallest. Total nodes N → **O(NK)**.

For K = 10⁴, N = 10⁶: 10¹⁰ ops. TLE.

---

## 4. The O(N log K) heap approach

> **Mini-refresher: replace "linear scan of K heads" with a HEAP.**
>
> Maintain a min-heap of the K current heads (one per non-empty list). Pop the smallest in O(log K); push the popped node's `.next` (if any) back in O(log K).
>
> Total: N pops × O(log K) = O(N log K).

```
heap = min-heap of list heads
for head in lists: if head: heap.push(head)

dummy = Node(0)
tail = dummy
while heap:
    smallest = heap.pop()
    tail.next = smallest
    tail = smallest
    if smallest.next: heap.push(smallest.next)
return dummy.next
```

Compare to the naive: we replaced an O(K) operation with O(log K). Massive speedup.

---

## 5. Code

**C++:**

```cpp
struct ListNode {
    int val;
    ListNode* next;
};

ListNode* mergeKLists(vector<ListNode*>& lists) {
    auto cmp = [](ListNode* a, ListNode* b) { return a->val > b->val; };
    priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
    for (auto* h : lists) if (h) pq.push(h);

    ListNode dummy(0);
    ListNode* tail = &dummy;
    while (!pq.empty()) {
        auto* n = pq.top(); pq.pop();
        tail->next = n;
        tail = n;
        if (n->next) pq.push(n->next);
    }
    return dummy.next;
}
```

**Python:**

```python
import heapq

# Python's heapq requires comparable items. ListNode usually isn't.
# Use (val, index, node) tuples to break ties on index.

def mergeKLists(lists):
    heap = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, i, head))
    
    dummy = ListNode(0)
    tail = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
```

Complexity: **O(N log K) time, O(K) space.**

---

## 6. Trace it

`lists = [[1, 4, 5], [1, 3, 4], [2, 6]]` (3 lists).

```
Initial heap (showing values; node identity matters but elided): [1A, 1B, 2C].
(A, B, C label which list; the heap may order ties arbitrarily.)

Pop 1A. Append to output. Push A.next = 4A. Heap = [1B, 2C, 4A].
Pop 1B. Output: 1A→1B. Push B.next = 3B. Heap = [2C, 4A, 3B].
Pop 2C. Output: 1A→1B→2C. Push C.next = 6C. Heap = [3B, 4A, 6C].
Pop 3B. Output: 1A→1B→2C→3B. Push B.next = 4B. Heap = [4A, 4B, 6C].
Pop 4A. Output: ...→4A. Push A.next = 5A. Heap = [4B, 5A, 6C].
Pop 4B. Output: ...→4B. B has no next. Heap = [5A, 6C].
Pop 5A. Output: ...→5A. A done. Heap = [6C].
Pop 6C. Output: ...→6C. C done. Heap empty.

Final: 1A → 1B → 2C → 3B → 4A → 4B → 5A → 6C.
```

Values: `1, 1, 2, 3, 4, 4, 5, 6`. ✓

The heap never held more than 3 nodes (one per list).

---

## 7. The divide-and-conquer alternative

Alternative: pair up lists, merge each pair, then merge the merged pairs. Repeat until ONE list remains.

```
while len(lists) > 1:
    new_lists = []
    for i in range(0, len(lists), 2):
        a = lists[i]
        b = lists[i+1] if i+1 < len(lists) else None
        new_lists.append(merge_two(a, b))
    lists = new_lists
return lists[0]
```

Each round halves K. Log K rounds. Each round processes N nodes (total across all merges). Total: **O(N log K)** — same complexity as the heap.

Both approaches reach the same complexity. Heap is more streaming-friendly; divide-and-conquer is more parallelizable.

---

## 8. The shape — K-way merge

The pattern:

> **"K SORTED STREAMS merged into ONE sorted stream via a MIN-HEAP of K heads."**

| Problem | What's being merged |
|---|---|
| **This problem** | K linked lists |
| K sorted arrays | K arrays |
| Kth Smallest in Sorted Matrix | K matrix rows |
| External Merge Sort | K sorted runs on disk |
| Find K Pairs Smallest Sums | conceptual K rows of pair grid |
| Smallest Range Covering K Lists | K lists with multi-element window |

**Pattern to internalize:**

> "K-way merge = MIN-HEAP of K candidate heads. Pop smallest, push its next. O(N log K) total."

---

## Cross-references

- **Reference card (post-mastery):** [`../Merge_K_Sorted_Lists.md`](../Merge_K_Sorted_Lists.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Merge_Two_Sorted_Lists.md`](../../Linked_List/learn/Merge_Two_Sorted_Lists.md), [`Find_K_Pairs_with_Smallest_Sums.md`](./Find_K_Pairs_with_Smallest_Sums.md), [`Kth_Smallest_Element_in_Sorted_Matrix.md`](./Kth_Smallest_Element_in_Sorted_Matrix.md).
  - Coming next: [`Find_Median_from_Data_Stream.md`](./Find_Median_from_Data_Stream.md) — the senior-bar two-heap technique.
