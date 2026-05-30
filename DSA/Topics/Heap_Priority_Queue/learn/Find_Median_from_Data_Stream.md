# Find Median from Data Stream — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_Median_from_Data_Stream.md`](../Find_Median_from_Data_Stream.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/find-median-from-data-stream/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-median-from-data-stream/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~24 minutes. **The senior-bar TWO-HEAP technique.** The lesson: **maintain a MAX-HEAP of the LOWER half and a MIN-HEAP of the UPPER half. The median is from the tops. O(log n) per add, O(1) per query.** This pattern is used in many "online statistics" problems. **Read [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. The naive O(n log n)/add approach
3. The two-heap insight
4. The balance invariants
5. The add operation
6. Code
7. Trace it
8. Why the two-step dance
9. Common pitfalls
10. The shape — two-heap for streaming statistics

---

## 1. Read the problem

Design a class supporting:
- `addNum(int x)`: add `x` to the stream.
- `double findMedian()`: return the median of all numbers added so far.

The median:
- If odd count: middle value.
- If even count: average of the two middle values.

**Example:**
- `add(1), add(2)`. Median = (1+2)/2 = **1.5**.
- `add(3)`. Median = **2**.
- `add(4)`. Median = (2+3)/2 = **2.5**.

Both operations should be EFFICIENT (better than re-sorting every time).

---

## 2. The naive O(n log n)/add approach

Keep all numbers in a list; sort on every `findMedian`.

```
data = []
def addNum(x): data.append(x)
def findMedian():
    data.sort()
    n = len(data)
    return data[n//2] if n%2 else (data[n//2-1] + data[n//2]) / 2
```

`findMedian`: O(n log n). For frequent queries: TLE.

Alternative: keep `data` sorted by inserting in O(n) (binary-search insertion). Then `findMedian` is O(1). Still O(n²) total for n adds.

We want BOTH operations in O(log n).

---

## 3. The two-heap insight

> **Mini-refresher: split the data into halves.**
>
> The median is the BOUNDARY between the LOWER HALF and the UPPER HALF of the sorted data.
>
> Maintain:
> - **`lo`**: a MAX-HEAP holding the LOWER half. Top = LARGEST of the lower half.
> - **`hi`**: a MIN-HEAP holding the UPPER half. Top = SMALLEST of the upper half.
>
> The median:
> - If odd total: `lo.top()` (where `lo` has one more element).
> - If even total: `(lo.top() + hi.top()) / 2`.
>
> Each insert: O(log n). Median query: O(1).

The two heaps together = a "sorted set" but optimized for ONLY accessing the middle boundaries.

---

## 4. The balance invariants

> **Mini-refresher: TWO invariants.**
>
> 1. **Ordering:** every element in `lo` ≤ every element in `hi`.
> 2. **Size:** `lo.size()` is equal to or exactly ONE MORE THAN `hi.size()`.
>
> If we always maintain these, the median is trivial:
> - Odd total → `lo.size() = hi.size() + 1`. Median = `lo.top()`.
> - Even total → `lo.size() = hi.size()`. Median = `(lo.top() + hi.top()) / 2`.

---

## 5. The add operation

The CLEANEST add operation uses a TWO-STEP DANCE:

```
def addNum(x):
    lo.push(x)                  # tentatively put in lower half
    hi.push(lo.pop())           # transfer the max of lower to upper
    if hi.size() > lo.size():
        lo.push(hi.pop())       # rebalance: ensure lo.size >= hi.size
```

Steps:
1. **Push `x` to `lo`.** Lo's top is updated.
2. **Move lo's top to hi.** This ensures the ordering invariant: whatever was the max of lo is now in hi, so future lo values stay ≤ future hi values.
3. **If hi is bigger, move hi's top back to lo.** Maintains the size invariant `lo.size() >= hi.size()`.

> **Mini-refresher: why the dance works even if x belongs in hi.**
>
> If x is "large" (belongs in hi), the dance still places it correctly:
> 1. Push x to lo. Lo's top might now be x.
> 2. Pop lo's top → push to hi. So x might end up in hi naturally.
> 3. Rebalance ensures sizes are right.
>
> The dance handles BOTH "x belongs in lo" and "x belongs in hi" UNIFORMLY. No branching needed.

---

## 6. Code

**C++:**

```cpp
class MedianFinder {
    priority_queue<int> lo;                                  // max-heap
    priority_queue<int, vector<int>, greater<int>> hi;       // min-heap

public:
    void addNum(int x) {
        lo.push(x);
        hi.push(lo.top()); lo.pop();
        if (hi.size() > lo.size()) {
            lo.push(hi.top()); hi.pop();
        }
    }

    double findMedian() {
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + hi.top()) / 2.0;
    }
};
```

**Python:**

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []   # max-heap (negate values)
        self.hi = []   # min-heap
    
    def addNum(self, x):
        heapq.heappush(self.lo, -x)
        heapq.heappush(self.hi, -heapq.heappop(self.lo))
        if len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))
    
    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2.0
```

Complexity:
- `addNum`: **O(log n)**.
- `findMedian`: **O(1)**.

---

## 7. Trace it

Stream: `1, 2, 3, 4`. Expected medians after each add: 1, 1.5, 2, 2.5.

```
add(1):
  lo.push(1). lo=[1], hi=[].
  hi.push(lo.pop()=1). lo=[], hi=[1].
  hi.size 1 > lo.size 0. lo.push(hi.pop()=1). lo=[1], hi=[].
  Median: lo.size > hi.size → lo.top()=1. ✓

add(2):
  lo.push(2). lo=[2, 1], hi=[].
  hi.push(lo.pop()=2). lo=[1], hi=[2].
  hi.size 1 = lo.size 1, no rebalance. lo=[1], hi=[2].
  Median: lo.size == hi.size → (1+2)/2 = 1.5. ✓

add(3):
  lo.push(3). lo=[3, 1], hi=[2].
  hi.push(lo.pop()=3). lo=[1], hi=[2, 3].
  hi.size 2 > lo.size 1. lo.push(hi.pop()=2). lo=[2, 1], hi=[3].
  Median: lo.size > hi.size → lo.top()=2. ✓

add(4):
  lo.push(4). lo=[4, 2, 1], hi=[3].
  hi.push(lo.pop()=4). lo=[2, 1], hi=[3, 4].
  hi.size 2 = lo.size 2, no rebalance. lo=[2, 1], hi=[3, 4].
  Median: (2+3)/2 = 2.5. ✓
```

All four medians correct.

---

## 8. Why the two-step dance

Alternative formulation without the dance:

```python
def addNum(x):
    if not lo or x <= -lo[0]:
        heapq.heappush(lo, -x)
    else:
        heapq.heappush(hi, x)
    # rebalance...
```

Requires explicit comparison. The two-step dance avoids this:

> **Mini-refresher: the dance unifies cases.**
>
> The "push to lo, transfer to hi" sequence handles BOTH "x ≤ all lo elements" and "x > all lo elements" uniformly. The "if hi too big, transfer back" handles size invariant.
>
> Three lines, no branches. Beautiful.

---

## 9. Common pitfalls

1. **Pushing directly to lo or hi based on comparison, but forgetting to rebalance.** Easy to leave one heap too big.

2. **Wrong heap polarity.** Lo is MAX-heap (we want max of lower half). Hi is MIN-heap (we want min of upper half).

3. **Median formula for odd total.** When `lo.size() > hi.size()` (one extra in lo), median = `lo.top()`. NOT `hi.top()`.

4. **Integer division for median.** Use `2.0` to force floating-point. Otherwise `(lo + hi) / 2` is integer division (loses .5).

5. **Forgetting Python's heapq is min-heap only.** Negate values to simulate max-heap.

6. **For very large sums (lo.top() + hi.top()), overflow.** Use 64-bit if needed: `(long long)lo.top() + hi.top()` in C++.

---

## 10. The shape — two-heap for streaming statistics

The pattern:

> **"For streaming statistics that depend on the MIDDLE of sorted data, maintain TWO HEAPS — one for each side of the median. The median is computable from the heap tops."**

| Problem | What two heaps track |
|---|---|
| **This problem** | median of all numbers |
| Sliding Window Median | median of last K (with lazy deletion) |
| IPO (LC #502) | profits + capital constraints |
| Smallest Range Covering K Lists | window across K sorted lists |
| Single Number with Streaming Frequencies | similar variations |

**Pattern to internalize:**

> "Two-heap technique = OPTIMAL data structure for median in a stream. Max-heap for LOWER half, min-heap for UPPER half. Balance after each insert."

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_Median_from_Data_Stream.md`](../Find_Median_from_Data_Stream.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Kth_Largest_Element_in_a_Stream.md`](./Kth_Largest_Element_in_a_Stream.md), [`Last_Stone_Weight.md`](./Last_Stone_Weight.md).
  - Heap topic complete!
