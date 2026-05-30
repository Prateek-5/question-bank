# Last Stone Weight

**Problem Link:**
<a href="https://leetcode.com/problems/last-stone-weight/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/last-stone-weight/</a>

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Read the Problem

You have stones with positive integer weights. Each round:
- Pick the two heaviest stones, `x` and `y` (with `x ≤ y`).
- If `x == y`, both shatter to nothing.
- If `x < y`, `x` vanishes and `y` becomes `y - x`.

Repeat until at most one stone is left. Return the remaining stone's weight (or 0 if none).

Example: `stones = [2, 7, 4, 1, 8, 1]`.
- Round 1: pick 7 and 8. 7 < 8, so 7 gone, 8 → 1. Stones: [2, 4, 1, 1, 1].
- Round 2: pick 4 and 2. 4 > 2, so 2 gone, 4 → 2. Stones: [2, 1, 1, 1].
- Round 3: pick 2 and 1. 1 gone, 2 → 1. Stones: [1, 1, 1].
- Round 4: pick 1 and 1. Both gone. Stones: [1].
- Loop ends.

Answer: **1**.

----------------------------------------

## Step 2: Spot the Key Operation

Each round, we need the **two largest stones**. Everything else just updates the list.

If I kept stones in a plain array, finding "the two largest" would take O(n) per round. Over many rounds, O(n²) total. For small n (say n ≤ 30), that's fine. But we should think about what structure gives us the two largest quickly.

A **sorted list** gives us the two largest at the end (O(1)), but inserting the new result takes O(n) shifting. Net: O(n) per round.

A **max-heap** gives us the top in O(log n), removes in O(log n), inserts in O(log n). Much better — and crucially, two pops and potentially one push per round is all we need.

----------------------------------------

## Step 3: Translate to Heap Operations

Each round:
1. `y = heap.pop()` (largest).
2. `x = heap.pop()` (second largest).
3. If `x != y`: `heap.push(y - x)`.
4. If `x == y`: do nothing.

Loop while the heap has ≥ 2 stones. At the end:
- If heap is empty: return 0.
- Else: return `heap.top()`.

Each round does O(log n) work. Total rounds ≤ n-1 (each round reduces the stone count by 1 or 2). Total time: O(n log n).

----------------------------------------

## Step 4: Trace on the Example

`stones = [2, 7, 4, 1, 8, 1]`. Build max-heap.

```
heap (top-to-bottom by weight): [8, 7, 4, 2, 1, 1]

Round 1: y=8, x=7. Different. Push 1. heap = [4, 2, 1, 1, 1].
Round 2: y=4, x=2. Different. Push 2. heap = [2, 1, 1, 1, 1].
Round 3: y=2, x=1. Different. Push 1. heap = [1, 1, 1, 1].
Round 4: y=1, x=1. Equal. (Nothing pushed.) heap = [1, 1].
Round 5: y=1, x=1. Equal. heap = [].
Loop ends.

heap is empty → return 0.
```

Wait, I got 0 but earlier by hand I got 1. Let me re-trace more carefully.

Round 1: pop 8 and 7 (the two largest). 7 ≠ 8, push 8-7=1. Stones: the original minus 7 and 8 plus 1 = [2, 4, 1, 1, 1]. Heap has these 5 elements. Let me check my above trace.

I think I made a mistake saying "heap = [4, 2, 1, 1, 1]" after round 1. Let me redo.

Original stones: [2, 7, 4, 1, 8, 1]. Heap holds {2, 7, 4, 1, 8, 1}, with 8 at top.

Round 1: pop 8, pop 7. Push 1 (= 8-7). Heap now holds {2, 4, 1, 1, 1}. Top is 4.
Round 2: pop 4, pop 2. Push 2 (= 4-2). Heap now holds {1, 1, 1, 2}. Wait but we popped 4 and 2, then pushed 2. The original had 1, 1, 1 (three 1's). Plus the new 2. Heap size 4. Top is 2.
Round 3: pop 2, pop 1. Push 1. Heap now {1, 1, 1}. Top 1.
Round 4: pop 1, pop 1. Equal, no push. Heap {1}. Size 1 — can't do another round (need ≥ 2).

Answer: 1. ✓

My earlier trace had an error — I pushed 1 in round 3 instead of 1, meant the heap went to [1, 1, 1] not [1, 1, 1, 1]. Let me re-fix: at round 3 pop 2, pop 1, push 1. Heap originally had {1, 1, 1, 2}. After pop 2 and pop 1: {1, 1}. After push 1: {1, 1, 1}. Correct.

Round 4: pop 1, pop 1, equal, no push. Heap: {1}. Loop ends.

Return 1. ✓

(My first trace had an arithmetic slip — let me flag that as a lesson to trace carefully.)

----------------------------------------

## Step 5: Why a Max-Heap Is the Right Tool

The rules demand "two heaviest stones each round," which is exactly what a max-heap's `top()` repeatedly gives us. Any alternative (sorted list, sorted set) does the same abstract thing but with different performance tradeoffs.

In C++, `priority_queue<int>` is a max-heap by default — no comparator needed. That's the sweet convenience for this problem.

----------------------------------------

## Step 6: Could We Solve Without a Heap?

For small inputs, yes — bubble-sort-style repeated scans work. But a heap is the standard answer.

A sorted container like `multiset<int>` also works: `*rbegin()` gives max, `erase(prev(end()))` removes it, `insert` adds. Each op O(log n). Multiset is more general (allows deleting arbitrary elements), but for this problem a heap is lighter-weight.

----------------------------------------

## Step 7: Name It

**Max-heap with repeated extract-top**. The structure is perfect for "repeatedly combine the two largest" problems. Similar pattern:
- Last Stone Weight (this).
- Minimum Cost to Connect Ropes (but min-heap).
- Reorganize String (frequency-based reordering).

Whenever a problem repeatedly asks for "the current max" (or min), reach for a heap.

----------------------------------------

## Step 8: Complexity

Time: **O(n log n)**. Initial heap build O(n). At most n-1 rounds, each O(log n).
Space: **O(n)** for the heap.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int lastStoneWeight(vector<int>& stones) {
    priority_queue<int> pq(stones.begin(), stones.end());  // max-heap
    while (pq.size() >= 2) {
        int y = pq.top(); pq.pop();
        int x = pq.top(); pq.pop();
        if (y > x) pq.push(y - x);
        // if y == x, both destroyed (push nothing)
    }
    return pq.empty() ? 0 : pq.top();
}
```

Reading the code:
- Construct the heap directly from the array — O(n) thanks to heapify.
- Loop while at least 2 stones remain.
- Pop the two largest, push the difference if nonzero.
- At the end, return whatever's left (or 0).

----------------------------------------

## Step 10: Follow-up Questions

- **Last Stone Weight II.** Different problem: we don't have to pick the two largest; we can pick *any* two and subtract. Much trickier — becomes a subset-sum DP (partition into two groups with minimum difference).
- **What if stones can be positive or negative?** Flip signs as needed, but the problem's semantics would shift.
- **Break ties differently** (say, when `x == y`, only one is destroyed). Adapt the rule; same heap skeleton.
- **What if there are millions of stones?** O(n log n) scales fine. For streaming input, use a self-balancing BST to allow deletion during rounds.
- **Can we be smarter about "the two largest" by tracking state?** Not really — removing and re-inserting is the cheapest correct path.
