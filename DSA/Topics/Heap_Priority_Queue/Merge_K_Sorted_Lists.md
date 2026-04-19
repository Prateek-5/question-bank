# Merge K Sorted Lists

**Problem Link:**
https://leetcode.com/problems/merge-k-sorted-lists/

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Read the Problem

You have `k` linked lists, each already sorted in non-decreasing order. Merge them into a single sorted linked list and return its head.

Example: three lists `[1→4→5]`, `[1→3→4]`, `[2→6]`. Merged: `1→1→2→3→4→4→5→6`.

----------------------------------------

## Step 2: Warm-Up — What If k = 2?

A much simpler problem. You have two sorted lists. Walk both with pointers and at each step pick the smaller head.

```cpp
ListNode* mergeTwo(ListNode* a, ListNode* b) {
    ListNode dummy(0), *tail = &dummy;
    while (a && b) {
        if (a->val <= b->val) { tail->next = a; a = a->next; }
        else { tail->next = b; b = b->next; }
        tail = tail->next;
    }
    tail->next = a ? a : b;
    return dummy.next;
}
```

That's O(n + m). Simple and optimal for k = 2.

Now — can we extend this to k lists?

----------------------------------------

## Step 3: The First Idea — Scan All Heads Each Time

At any moment, the next node in the merged output is the smallest among all current list heads. So a direct approach:

```
while any list is non-empty:
    find the list with the smallest head value
    append that node to output; advance its pointer
```

"Find the smallest head" among k candidates is an O(k) operation (linear scan). We repeat this for every node in the combined output — total `N` nodes across all lists. So overall: **O(N · k)**.

For small `k` this is fine. For `k = 10^4` and `N = 10^6`, it's 10^10 — too slow. So we ask: can we find the minimum-valued head faster than O(k)?

----------------------------------------

## Step 4: A Data Structure That Gives Min in O(log k)

We need a structure that:
- Holds all the current heads (up to `k` of them).
- Returns the smallest in O(log k).
- Lets us replace the smallest with a new value (the next node from the same list) also in O(log k).

That's exactly what a **min-heap** (priority queue) does. Its `top()` is the smallest; `pop()` removes it; `push()` inserts and rebalances. All in O(log size).

So:

1. Put the first node of each list into a min-heap keyed by `.val`.
2. Pop the smallest. Append it to the output. If it has a `next`, push that next node into the heap.
3. Repeat until the heap is empty.

Each node is pushed once and popped once over the whole run. The heap never holds more than `k` nodes at a time. Total: O(N log k).

That's the insight. No template, just "we need fast min → heap".

----------------------------------------

## Step 5: Trace on the Example

Lists:
```
A: 1 → 4 → 5
B: 1 → 3 → 4
C: 2 → 6
```

Initialize heap with heads: `[A(1), B(1), C(2)]`. The heap orders by value; internally it might look like `[1A, 1B, 2C]` or `[1B, 1A, 2C]` depending on insertion; either is fine. Let me show the pops.

```
Output: (empty)

Pop smallest (1 from either A or B, say A). Output: 1. A.next = 4, push 4A.
Heap: [1B, 2C, 4A]

Pop 1B. Output: 1→1. B.next = 3, push 3B.
Heap: [2C, 4A, 3B]

Pop 2C. Output: 1→1→2. C.next = 6, push 6C.
Heap: [3B, 4A, 6C]

Pop 3B. Output: 1→1→2→3. B.next = 4, push 4B.
Heap: [4A, 4B, 6C]

Pop 4 (A or B, say A). Output: 1→1→2→3→4. A.next = 5, push 5A.
Heap: [4B, 5A, 6C]

Pop 4B. Output: 1→1→2→3→4→4. B.next = null, nothing to push.
Heap: [5A, 6C]

Pop 5A. Output: 1→1→2→3→4→4→5. A.next = null.
Heap: [6C]

Pop 6C. Output: 1→1→2→3→4→4→5→6. Heap empty.
```

Done. The output matches the expected merged list.

Notice the heap never held more than 3 nodes at a time — one per list. That's the key efficiency.

----------------------------------------

## Step 6: Implementation Details

In C++ we use `priority_queue` with a comparator that orders by `.val` ascending.

```cpp
auto cmp = [](ListNode* a, ListNode* b) { return a->val > b->val; };
priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
```

The comparator returns `true` when `a` should come *after* `b` — for a min-heap, we want smaller first, so we say "a is after b when a's val is greater".

The merged list is built using a dummy head. We keep a `tail` pointer to append in O(1).

----------------------------------------

## Step 7: An Alternate Path — Divide and Conquer

There's a completely different approach that reaches the same complexity. Pair up the lists: merge 1 with 2, 3 with 4, etc. Then merge those results pairwise again. Continue until one list remains.

This is a tournament. Each round halves the number of lists. We do log(k) rounds, and each round processes every node once across all pairwise merges. Total: O(N log k) — same as the heap.

Both approaches are valid; the heap version tends to be easier to implement cleanly in one pass.

----------------------------------------

## Step 8: Complexity

Time: each of the `N` total nodes is pushed once and popped once. Each heap op is O(log k). **O(N log k).**

Space: the heap holds at most `k` nodes at any moment. **O(k).**

----------------------------------------

## Step 9: C++ Implementation

```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x): val(x), next(nullptr) {}
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

Key details:
- Only push non-null heads initially (`if (h) pq.push(h);`).
- After popping, only push `n->next` if it exists.
- The dummy head means we don't special-case the first node.

----------------------------------------

## Step 10: Follow-up Questions

- **Merge k sorted arrays (not linked lists).** Same idea — push `(value, arrayIndex, elementIndex)` tuples into the heap.
- **Merge k sorted streams of arbitrary size stored on disk.** This is the classic external merge-sort step. The heap version works because we only hold k items in memory at once, regardless of stream size.
- **k is very large (10^6) and N is huge.** Even O(N log k) can be too slow. If the sources are from few underlying files, consider cascading merges (divide and conquer).
- **Find the k-th smallest element across k sorted lists without merging them.** The same heap approach but stop after k pops. Reduces time to O(k log k).
- **What if lists aren't sorted?** Sort each first, then merge. Or just concatenate and sort the whole thing — which might actually be faster depending on sizes.
