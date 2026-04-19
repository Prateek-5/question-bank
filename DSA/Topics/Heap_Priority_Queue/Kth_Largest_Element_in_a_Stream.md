# Kth Largest Element in a Stream

**Problem Link:**
https://leetcode.com/problems/kth-largest-element-in-a-stream/

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: Understand the Setup

Design a class `KthLargest`:
- Constructor: takes `k` and an initial array of integers.
- `add(val)`: adds a new value to the stream. Returns the **k-th largest** element seen so far.

The stream grows over time. Each `add` returns a fresh "k-th largest" that reflects everything added so far.

Example: k = 3, initial = `[4, 5, 8, 2]`.
- After init, sorted values: [2, 4, 5, 8]. The 3rd largest is 4.
- add(3): stream is now [4, 5, 8, 2, 3]. Sorted: [2, 3, 4, 5, 8]. 3rd largest = 4. Return 4.
- add(5): stream [4, 5, 8, 2, 3, 5]. Sorted: [2, 3, 4, 5, 5, 8]. 3rd largest = 5. Return 5.
- add(10): stream adds 10. 3rd largest now 5. Return 5.
- add(9): 3rd largest now 8. Return 8.
- add(4): 3rd largest still 8. Return 8.

Notice: "3rd largest" means third when sorted descending. Not unique — duplicate values count separately.

----------------------------------------

## Step 2: What Data Would We Naïvely Track?

Keep a growing list of all values. On every `add`, sort (or partial sort) to find the k-th largest.

- Each `add` runs in O(n log n) or O(n) with partial sort.
- Total cost across m adds: O(m · n log n) or O(m · n).

For long streams this is wasteful. We're re-sorting almost the same data over and over.

Can we maintain just the "top k" values as we go?

----------------------------------------

## Step 3: A Sharper Observation

We don't need all values — we need the k-th largest. At any moment, the only values that could be the "k-th largest" are the **k largest values** seen so far. Everything smaller than that is irrelevant to the answer.

So: maintain a collection of the k largest values. When a new value arrives:
- If the new value is larger than the smallest in our top-k, include it and kick out the old smallest.
- Otherwise, ignore it — it can't affect the answer.

Either way, after processing, the **smallest in our top-k** is the k-th largest overall (because the top-k has exactly k elements, and its minimum is the k-th when sorted descending).

What structure gives us "quick access to the smallest, and quick insert/remove"? A **min-heap of size k**.

----------------------------------------

## Step 4: Why a Min-Heap, Specifically?

We want to maintain the **k largest values**. The "weakest link" in this collection — the one most likely to be kicked out by a new arrival — is the smallest one. So the heap is organized with the minimum at the top.

Operations:
- `push(x)`: O(log k).
- `top()`: O(1) — gives us the smallest of the top-k, which **is** the k-th largest overall.
- `pop()`: O(log k).

Insert-and-maybe-kick pattern:
```
heap.push(x)
if heap.size() > k:
    heap.pop()    # kicks out the smallest
return heap.top()
```

After the operation, the heap still has exactly k elements (the k largest seen), and its top is the answer.

One edge case to think about: during the first few adds (before the stream has k elements), the heap size is less than k. We don't pop yet; we just accumulate.

----------------------------------------

## Step 5: Trace on the Example

k = 3, initial = [4, 5, 8, 2].

Initialize by adding each in sequence:

```
heap = []
add(4): push. heap = [4]. size < 3, no pop. (returns 4 since only 1 element, but we don't query).
add(5): push. heap = [4, 5]. size < 3.
add(8): push. heap = [4, 5, 8]. size == 3. Top = 4.
add(2): push. heap = [2, 5, 8, 4]. size > 3, pop 2. heap = [4, 5, 8]. Top = 4.
```

Constructor returns; `.add` queries will run from here.

```
add(3): push. heap = [3, 4, 8, 5]. Pop 3. heap = [4, 5, 8]. Top = 4. Return 4. ✓
add(5): push. heap = [4, 5, 8, 5]. Pop 4. heap = [5, 5, 8]. Top = 5. Return 5. ✓
add(10): push. heap = [5, 5, 8, 10]. Pop 5. heap = [5, 8, 10]. Top = 5. Return 5. ✓
add(9): push. heap = [5, 8, 9, 10]. Pop 5. heap = [8, 9, 10]. Top = 8. Return 8. ✓
add(4): push. heap = [4, 8, 9, 10]. Pop 4. heap = [8, 9, 10]. Top = 8. Return 8. ✓
```

Matches expected. ✓

Notice at add(4): the new value is smaller than the smallest in the heap (8). So pushing and popping is a no-op — we pop the same value we just pushed. Still correct, just slightly wasteful.

We could optimize: only push if `x > heap.top()`. But the simpler "always push-then-pop-if-oversize" is fine and avoids edge-case bugs.

----------------------------------------

## Step 6: Why This Is the Right Data Structure for the Job

The key insight is that we're maintaining a **rolling set of the k largest values**, and the one most vulnerable to eviction is the smallest of them. A min-heap specifically gives us O(1) access to that vulnerable element and O(log k) to swap it out.

If we tried to use a max-heap instead, finding the "k-th largest" would require O(k) time (pop-then-restore) — much slower.

If we tried a sorted array, insertions would be O(k) (shifting elements).

The min-heap-of-size-k is the minimal structure that supports exactly what we need.

----------------------------------------

## Step 7: Name It

This is the classic **"bounded heap" pattern** — maintain a heap of size exactly k as a filter. The polarity (min-heap vs max-heap) is opposite to what you'd naïvely expect:
- To track top-k largest: use min-heap (smallest is vulnerable).
- To track top-k smallest: use max-heap (largest is vulnerable).

Same structure, opposite polarity. Mixing these up is a classic interview bug.

----------------------------------------

## Step 8: Complexity

- Constructor: O(n log k) where n = size of initial array.
- `add`: O(log k) per call.
- Space: O(k) for the heap.

Elegant and fast.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class KthLargest {
    priority_queue<int, vector<int>, greater<int>> heap;   // min-heap
    int k;
public:
    KthLargest(int k, vector<int>& nums) : k(k) {
        for (int x : nums) add(x);
    }

    int add(int val) {
        heap.push(val);
        if ((int)heap.size() > k) heap.pop();
        return heap.top();
    }
};
```

Compact. The constructor just calls `add` on each initial element — reuses the same logic for initialization as for streaming updates.

One subtle point: the return of `add` from the constructor's loop is discarded (we just care about the side effect of growing the heap). Some implementations skip returning from the init-phase adds, but calling `add(val)` and ignoring the return is cleaner.

----------------------------------------

## Step 10: Follow-up Questions

- **Kth smallest in a stream.** Swap polarity: use a max-heap of size k. Smallest stays inside; top (largest of the smallest-k) is the answer.
- **Median in a stream.** Two heaps (low half max-heap, high half min-heap), balanced. See "Find Median from Data Stream."
- **Kth largest over a sliding window (not everything seen).** Requires lazy deletion or a multiset with an "erase by value" operation.
- **Top k largest at each step (return the full list).** Heap structure works, but extracting the full heap is O(k log k).
- **Kth largest with updates to past values.** Much harder; use segment trees or order-statistic trees.
- **Why not use sort on every add?** O(n log n) per add vs O(log k). Heap wins for large n.
