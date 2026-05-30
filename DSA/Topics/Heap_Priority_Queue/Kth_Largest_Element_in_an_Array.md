# Kth Largest Element in an Array

**Problem Link:**
<a href="https://leetcode.com/problems/kth-largest-element-in-an-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/kth-largest-element-in-an-array/</a>

**Topic:**
Heap / Priority Queue

----------------------------------------

## Step 1: What We're Finding

Given an integer array `nums` and an integer k, return the **k-th largest element** (k-th in sorted-descending order — NOT the k-th distinct element).

Example: `nums = [3, 2, 1, 5, 6, 4]`, k = 2. Sorted descending: [6, 5, 4, 3, 2, 1]. 2nd largest = **5**.
Example: `nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]`, k = 4. Sorted descending: [6, 5, 5, 4, 3, 3, 2, 2, 1]. 4th = **4**.

Note duplicates count as separate entries.

----------------------------------------

## Step 2: Baseline — Sort Entire Array

Easiest solution: sort in descending order, return `nums[k - 1]`. O(n log n) time.

For large n, we're paying to sort everything when we only need the top k. Can we avoid that?

----------------------------------------

## Step 3: Min-Heap of Size k

Here's the classic heap idea. Maintain a **min-heap** of the top k largest elements seen so far.

Why min-heap? Because the **smallest** of the top-k is the one we'd kick out when a bigger challenger arrives. A min-heap gives O(log k) access to its minimum.

Algorithm:
1. Push first k elements into the heap.
2. For each remaining element, if it's larger than the heap's minimum (top), pop the min and push the new element.
3. After processing all elements, the heap's minimum is the k-th largest.

```
heap = min-heap
for x in nums:
    heap.push(x)
    if heap.size() > k: heap.pop()
return heap.top()
```

This keeps exactly k elements in the heap at all times (the current top k). The smallest of them is the k-th largest overall.

Time: O(n log k). Space: O(k). Better than full sort when k << n.

----------------------------------------

## Step 4: Quickselect — Average O(n)

Even smarter: **Quickselect**. A partition-based algorithm.

Idea: pick a pivot. Partition the array into "greater than pivot" and "less than pivot" (classic quicksort partition). Now you know where the pivot ranks.
- If its rank is exactly k (counting from largest), return the pivot.
- If k is among the "greater than" side, recurse into that side.
- Else recurse into the "less than" side.

Average: O(n) (each recursion halves the size; linear via master theorem). Worst: O(n²) if pivots are bad — mitigate with random pivot or median-of-three.

For interview purposes, the heap solution is usually accepted. Quickselect is faster but more fiddly.

----------------------------------------

## Step 5: Heap Trace on `[3, 2, 1, 5, 6, 4]`, k = 2

```
heap (min-heap, at most size 2):
push 3: heap = [3]. size 1 ≤ 2.
push 2: heap = [2, 3]. size 2 ≤ 2.
push 1: heap = [1, 3, 2]. size 3 > 2. Pop min → 1. heap = [2, 3].
push 5: heap = [2, 3, 5]. size 3 > 2. Pop min → 2. heap = [3, 5].
push 6: heap = [3, 5, 6]. size 3 > 2. Pop min → 3. heap = [5, 6].
push 4: heap = [4, 6, 5]. size 3 > 2. Pop min → 4. heap = [5, 6].

Heap min (top) = 5.
```

Return **5**. ✓

Through the process, the heap always held the top-2 elements seen so far. At the end, heap = {5, 6}; the min of those is 5 — the 2nd largest.

----------------------------------------

## Step 6: Why Min-Heap (Not Max-Heap)?

Intuition check: why not a max-heap?

If we put all elements in a max-heap and popped k times, we'd find the k-th largest. But that's O(n + k log n) — worse when k is close to n. And it requires storing all n elements, losing the O(k) space advantage.

With min-heap of size k, we store just k elements. When a new one arrives, we need to know "is this bigger than the smallest we've kept?" The min-heap's top gives that instantly. Push and immediately pop if size exceeds k — net size stays k.

----------------------------------------

## Step 7: Name It

**Heap-based selection**, specifically "bounded min-heap of size k" for top-k selection. Universal pattern:
- Top k largest: min-heap of size k.
- Top k smallest: max-heap of size k.
- Streaming median: two heaps (min and max, balanced).

Related problems:
- K closest points to origin.
- Top K frequent elements.
- Kth smallest in sorted matrix.

All use the same size-bounded heap idiom.

**Quickselect** is the alternative when average-case O(n) matters and the data is in memory.

----------------------------------------

## Step 8: Complexity

**Heap approach:** Time O(n log k), Space O(k).
**Quickselect:** Average O(n), Worst O(n²), Space O(log n) for recursion (randomized pivot).
**Full sort:** O(n log n), Space O(1) or O(log n).

For large n and small k, heap wins. For arbitrary k, quickselect wins in practice.

----------------------------------------

## Step 9: C++ Implementation (Heap)

```cpp
int findKthLargest(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> minHeap;
    for (int x : nums) {
        minHeap.push(x);
        if ((int)minHeap.size() > k) minHeap.pop();
    }
    return minHeap.top();
}
```

`priority_queue` with `greater<int>` gives a min-heap. Keep only k elements; the top is the answer.

## Step 10: C++ Implementation (Quickselect)

```cpp
int quickselect(vector<int>& a, int lo, int hi, int k) {
    // k = 0-based index in sorted-descending order we want.
    int pivot = a[lo + rand() % (hi - lo + 1)];
    int i = lo, j = hi;
    // Partition so a[lo..i-1] > pivot, a[j+1..hi] < pivot.
    // (3-way would also work for duplicates.)
    while (i <= j) {
        while (a[i] > pivot) i++;
        while (a[j] < pivot) j--;
        if (i <= j) { swap(a[i], a[j]); i++; j--; }
    }
    // After partition: a[lo..j] has elements >= pivot, a[i..hi] has <= pivot.
    if (k <= j) return quickselect(a, lo, j, k);
    if (k >= i) return quickselect(a, i, hi, k);
    return a[k];
}

int findKthLargest(vector<int>& nums, int k) {
    return quickselect(nums, 0, nums.size() - 1, k - 1);
}
```

Random pivot avoids the adversarial worst case on pre-sorted inputs.

----------------------------------------

## Step 11: Follow-up Questions

- **Kth smallest instead.** Flip: max-heap of size k, or descending quickselect.
- **Find all k largest elements.** The heap's contents at the end are exactly the top k.
- **Streaming: elements arrive one by one.** Perfect for heap approach — O(log k) per element.
- **Memory constraint: can't fit all n elements.** Heap with O(k) space is the right choice.
- **Worst case guarantee.** Use median-of-medians to pick pivots deterministically — Quickselect in worst-case O(n), but constants are high.
- **Why `k - 1` in quickselect?** Because "kth largest" in 1-indexed language is index k-1 in a 0-indexed descending array.
