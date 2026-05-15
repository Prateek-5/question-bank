# Implement a MinHeap / Priority Queue

## Source
- Canonical data-structures interview problem (LeetCode #703, #215, #1046; Hackerrank "Priority Queue").
- Backbone of many practical algorithms: Dijkstra, A*, K-way merge, top-K, async task schedulers, rate limiters.

## Why this question matters in interviews
JS doesn't ship a priority queue. Every time you see "process tasks in priority order," "find the K largest," "schedule the soonest deadline," "merge K sorted streams" — you need one. The 50-line array-backed binary heap is the canonical answer. Implementing it tests **array-as-tree indexing math** (`parent = (i-1)>>1`, `children = 2i+1, 2i+2`), **sift up / sift down**, **the difference between O(log n) push/pop and O(n log n) sort-based fakes**, and the realization that "priority queue" is just an interface — the heap is one implementation. Backend interviewers reach for this when probing whether you can build the engine room of an async queue, a rate limiter with delayed slots, or a real scheduler.

## Concepts involved

### Syntax to lock in
```js
class MinHeap {
  constructor() { this.heap = []; }

  push(item) {
    this.heap.push(item);
    this._siftUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 0) return undefined;
    const top = this.heap[0];
    const last = this.heap.pop();
    if (this.heap.length) {
      this.heap[0] = last;
      this._siftDown(0);
    }
    return top;
  }

  peek() { return this.heap[0]; }
  get size() { return this.heap.length; }

  _siftUp(i) {
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (this.heap[p] <= this.heap[i]) break;
      [this.heap[p], this.heap[i]] = [this.heap[i], this.heap[p]];
      i = p;
    }
  }

  _siftDown(i) {
    const n = this.heap.length;
    while (true) {
      const l = 2 * i + 1, r = 2 * i + 2;
      let smallest = i;
      if (l < n && this.heap[l] < this.heap[smallest]) smallest = l;
      if (r < n && this.heap[r] < this.heap[smallest]) smallest = r;
      if (smallest === i) break;
      [this.heap[i], this.heap[smallest]] = [this.heap[smallest], this.heap[i]];
      i = smallest;
    }
  }
}
```

### Runtime / engine behavior
- A binary heap is an **array** with implicit tree structure. For node at index `i`: parent is `(i-1) >> 1`, left child is `2i+1`, right child is `2i+2`. No pointers, no allocations per node — just an array.
- **Heap invariant** (min-heap): every parent ≤ both children. The root is the minimum. The heap is **not sorted** — only the root is guaranteed minimum.
- `push` appends at the end (O(1)) then sifts up (O(log n)). `pop` removes root, moves last element to root (O(1)), then sifts down (O(log n)).
- `peek` is O(1) — just `heap[0]`.
- Sifting is bitwise-fast: `(i - 1) >> 1` is integer division by 2. Faster and clearer than `Math.floor((i-1)/2)`.
- Heap construction from an array (heapify) is O(n) using bottom-up sift-down — better than n push calls (O(n log n)). Worth mentioning.

### Edge cases (these are the interview traps)
1. **Empty heap pop** — return `undefined`, don't throw (unless interviewer specifies). The `peek()` of an empty heap is also undefined.
2. **Single element** — `pop()` of a 1-element heap should return that element and leave the heap empty. The "move last to root, sift down" path doesn't apply — check `if (heap.length)` after the pop.
3. **Duplicate priorities** — heap doesn't guarantee order among equals. If you need FIFO among same-priority items, store an insertion counter as a tiebreaker (e.g., `[priority, seq, item]`).
4. **Object items with separate priority** — store `{priority, item}` pairs. Compare on `.priority` (custom comparator).
5. **Custom comparator** — generalize to a max-heap or sort by an arbitrary key. Pass a `compare(a, b)` function: negative if a should come first. This is the production-shape API.
6. **Mutation during iteration** — if you push/pop while iterating, you corrupt the structure. Treat the heap as opaque; don't expose `.heap` for direct manipulation.
7. **`pop` then `push` (replace top)** — common in K-way merge. Doing it as one operation saves one sift (replace + single sift down). Real libs expose `replace(item)`.
8. **Numeric NaN comparison** — `NaN < anything` is `false`. NaN in the heap breaks the invariant silently. Reject NaN or validate in `push`.
9. **`Math.floor((i-1)/2)` vs `(i-1) >> 1`** — both work for non-negative indices. Bitshift is idiomatic and faster.

## Brute force approach
"I'll keep a sorted array; `push` does `splice` at the right position (O(n)), `pop` removes the first (O(n) due to shift)." Correct but slow. For an interview, mention this as the baseline and reach for the heap.

Or: "I'll push without sorting and re-sort on every pop." That's O(n log n) per pop. Useless for any non-trivial workload. The whole point of the heap is amortized O(log n) per op.

Don't try to be clever with a sorted linked list — same time complexity, more allocations.

## Optimal approach
Array-backed binary heap with sift-up on push and sift-down on pop. O(log n) per op, O(1) peek. Single array, no pointer chasing — cache-friendly and GC-friendly.

## Solution (JavaScript)

```js
/**
 * Binary heap-backed priority queue. Custom comparator for min/max/object-keyed.
 * @template T
 */
class PriorityQueue {
  /**
   * @param {(a: T, b: T) => number} [compare]  negative => a precedes b
   */
  constructor(compare = (a, b) => a - b) {
    this.heap = [];
    this.compare = compare;
  }

  get size() { return this.heap.length; }
  peek() { return this.heap[0]; }

  push(item) {
    this.heap.push(item);
    this._siftUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 0) return undefined;
    const top = this.heap[0];
    const last = this.heap.pop();
    if (this.heap.length > 0) {
      this.heap[0] = last;
      this._siftDown(0);
    }
    return top;
  }

  /** O(n) heapify from an array — faster than n pushes. */
  static heapify(items, compare) {
    const pq = new PriorityQueue(compare);
    pq.heap = items.slice();
    for (let i = (pq.heap.length >> 1) - 1; i >= 0; i--) pq._siftDown(i);
    return pq;
  }

  _siftUp(i) {
    const h = this.heap, cmp = this.compare;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (cmp(h[i], h[p]) >= 0) break;
      [h[i], h[p]] = [h[p], h[i]];
      i = p;
    }
  }

  _siftDown(i) {
    const h = this.heap, n = h.length, cmp = this.compare;
    while (true) {
      const l = 2 * i + 1, r = 2 * i + 2;
      let smallest = i;
      if (l < n && cmp(h[l], h[smallest]) < 0) smallest = l;
      if (r < n && cmp(h[r], h[smallest]) < 0) smallest = r;
      if (smallest === i) break;
      [h[i], h[smallest]] = [h[smallest], h[i]];
      i = smallest;
    }
  }
}

// MinHeap with a `priority` field on items, FIFO tiebreaker:
let seq = 0;
const pq = new PriorityQueue((a, b) => a.priority - b.priority || a.seq - b.seq);
pq.push({ priority: 2, seq: seq++, payload: 'a' });
pq.push({ priority: 1, seq: seq++, payload: 'b' });
pq.push({ priority: 2, seq: seq++, payload: 'c' });
// pop order: b (pri 1), a (pri 2 seq 0), c (pri 2 seq 2)
```

## Step-by-step dry run

Input:
```js
const pq = new PriorityQueue();   // default min-heap on numbers
pq.push(5);
pq.push(2);
pq.push(8);
pq.push(1);
pq.push(3);
```

Heap state evolution:
- push 5: heap=[5]. siftUp(0): i=0, exit.
- push 2: heap=[5,2]. siftUp(1): p=0, cmp(2,5)<0 → swap → heap=[2,5]. i=0, exit.
- push 8: heap=[2,5,8]. siftUp(2): p=0, cmp(8,2)>=0 → break.
- push 1: heap=[2,5,8,1]. siftUp(3): p=1, cmp(1,5)<0 → swap → heap=[2,1,8,5]. i=1, p=0, cmp(1,2)<0 → swap → heap=[1,2,8,5]. i=0, exit.
- push 3: heap=[1,2,8,5,3]. siftUp(4): p=1, cmp(3,2)>=0 → break.

`pop()` sequence:
- pop: top=1. last=3 (heap.pop). heap=[3,2,8,5] (length 4). siftDown(0): l=1(2), r=2(8). smallest=1. swap heap[0]/heap[1] → [2,3,8,5]. i=1, l=3(5), r=4(oob). smallest=1 still (3 < 5). break. Returns 1.
- pop: top=2. last=5. heap=[5,3,8] (3 elems). siftDown(0): l=1(3), r=2(8). smallest=1. swap → [3,5,8]. i=1, l=3 oob. break. Returns 2.
- pop: top=3. last=8. heap=[8,5]. siftDown(0): l=1(5), r=2(oob). smallest=1 (5<8). swap → [5,8]. i=1, l=3 oob. break. Returns 3.
- pop: top=5. last=8. heap=[]. push 8 back as root? No — `heap.pop` returned 8 (the last), and after that `heap.length === 0` so we skip the sift step entirely. Returns 5.

Wait — recheck the last pop: heap=[5,8]. top=5. last=heap.pop() → last=8, heap=[5]. heap.length=1>0, so heap[0]=8, siftDown(0). l=1 oob. break. Returns 5. Then pop again: top=8. last=heap.pop()=8, heap=[]. heap.length=0 → skip. Returns 8.

Final pop order: 1, 2, 3, 5, 8 — sorted, as expected.

## Important takeaways

**Syntax to memorize**
- Array indexing: parent `(i-1)>>1`, children `2i+1`, `2i+2`.
- `push` = append + sift up. `pop` = swap root with last, pop last, sift down.
- Sift up: while parent > self, swap and move up.
- Sift down: while smaller child exists, swap with smaller child and move down.
- Custom comparator: negative if `a` should come out first.

**Patterns to reuse**
- Array-as-implicit-tree generalizes to: segment trees, Fenwick trees (BIT), k-ary heaps.
- "Pop is swap-and-sift-down" pattern is the heart of `heapify` and heapsort.
- Pair-with-tiebreaker (sequence counter) is the FIFO-among-equals trick — same idea is used in lodash, Linux kernel run-queues, etc.

**Common mistakes**
- Confusing min-heap and max-heap when copying from another language's docs. Pick a direction and stay consistent.
- Off-by-one in children: `2i+1`, `2i+2`, not `2i` and `2i+1`. (The latter is correct for 1-indexed arrays — used in CLRS textbook; JS is 0-indexed.)
- Not handling empty heap on pop. Don't crash; return undefined.
- Pushing one-at-a-time when you have a batch — use `heapify` (O(n)) instead of n pushes (O(n log n)).
- Mutating items inside the heap (e.g., changing `.priority` of an item in place). Heap invariant breaks silently. To "decrease key," remove and re-insert, or use a position map.

**Related questions**
- Heapsort (heapify + n pops).
- Top-K elements (heap of size K, evict min, keep K largest).
- K-way merge (heap of one element per stream).
- Dijkstra / A* (priority queue keyed by tentative distance).
- AsyncQueue with priority (this heap is the engine).
- Rate limiter with delayed slot release.

## Variants

1. **Max-heap** — negate the comparator: `(a, b) => b - a`. Same data structure, reverse order.

2. **Indexed / decrease-key heap** — maintain a Map<item, index>. On `update(item, newPriority)`, look up the index and sift up or down depending on direction. O(log n). Used by Dijkstra to avoid re-inserting nodes.

3. **K-ary heap** — each node has K children instead of 2. Sift down does K comparisons per level but fewer levels. Faster for `push`-heavy workloads when K is tuned to cache line size.

4. **Pairing heap / Fibonacci heap** — O(1) amortized `decrease-key`. Theoretically better for Dijkstra, but constants are awful — binary heap wins in practice.

5. **Bounded heap (top-K)** — fixed max size. On `push` past capacity, compare with root (min in max-heap) and replace. O(log K) per op regardless of input size.

## Revision notes

> **MinHeap / PQ — 90 second recap**
> - Array-backed binary tree. Parent `(i-1)>>1`, children `2i+1`, `2i+2`.
> - `push`: append, sift up. `pop`: take root, move last to root, sift down. O(log n).
> - `peek`: O(1).
> - Custom comparator: `(a, b) => negative if a precedes b`.
> - `heapify(arr)`: bottom-up sift-down, O(n). Faster than n pushes.
> - FIFO-among-equals: pair with insertion counter as tiebreaker.
> - Trap: empty-heap pop (return undefined), off-by-one in child indices, mutating priorities in place (use decrease-key indexed heap).
> - Backbone of: top-K, K-way merge, Dijkstra/A*, rate limiter delayed slots, async queue priorities, scheduler.
