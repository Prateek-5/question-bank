# MinHeap / Priority Queue — array-backed binary heap

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [`concepts/recursion.md`](../../concepts/recursion.md), [circular-buffer.md](./circular-buffer.md)
>
> **Source:** [LeetCode 703](https://leetcode.com/problems/kth-largest-element-in-a-stream/), [215](https://leetcode.com/problems/kth-largest-element-in-an-array/), [1046](https://leetcode.com/problems/last-stone-weight/). Backbone of Dijkstra, A*, top-K, K-way merge, async schedulers.

---

## 1. Problem statement

**Signature**
```ts
class PriorityQueue<T> {
  constructor(compare?: (a: T, b: T) => number);
  push(item: T): void;
  pop(): T | undefined;
  peek(): T | undefined;
  size: number;
}
```

**Input / Output examples**

| Setup                                            | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| `push(5); push(2); push(8); push(1); push(3)`    | min at root: `1`                                       |
| `pop()` 5 times                                  | `1, 2, 3, 5, 8` (sorted)                               |
| `peek()`                                          | min without removal                                    |
| Custom compare `(a,b) => b - a`                   | max-heap                                               |
| Pop on empty                                      | `undefined`, no throw                                  |
| `heapify(arr)`                                    | O(n) bottom-up build, faster than n pushes (O(n log n))|

**Constraints**
- O(log n) push, O(log n) pop, O(1) peek.
- Array indexing: parent `(i-1) >> 1`, children `2i+1` / `2i+2`.
- Heap invariant: every parent comes before both children per comparator.
- **Not sorted** — only root is guaranteed minimum.

---

## 2. Plain-English restatement

A priority queue: items go in any order, come out in priority order. JS has no built-in, so you build one with an **array used as an implicit binary tree**. The root is the highest-priority item. Push adds at the end and "sifts up" until the heap property is restored. Pop swaps root with last, removes last, then "sifts down" from the root.

---

## 3. Why this matters in interviews

Every "K largest," "top by priority," "soonest deadline," "merge K streams" problem needs one. The 50-line implementation tests **array-as-tree indexing**, **sift up/down**, **the difference between O(log n) heap and O(n log n) sort-based fakes**. Backend uses: async-task schedulers, rate limiters with delayed slots, K-way merge in ETL.

---

## 4. Mental model

```
   Array as implicit binary tree:
   index:  0   1   2   3   4   5   6
   value: [1, 2, 8, 5, 3, _, _]

       1               ← root (index 0): the min
      / \
     2   8             ← indices 1, 2
    / \
   5   3               ← indices 3, 4

   For node i:
     parent = (i - 1) >> 1
     left   = 2i + 1
     right  = 2i + 2

   Heap invariant: parent ≤ both children (min-heap)
   ✗ NOT sorted — only root is guaranteed.

   push(0):
     append → [1, 2, 8, 5, 3, 0]
     sift up from i=5:
       parent=(5-1)>>1=2 → heap[2]=8 > 0 → swap → [1, 2, 0, 5, 3, 8]
       i=2, parent=0 → heap[0]=1 > 0 → swap → [0, 2, 1, 5, 3, 8]

   pop():
     top=0, last=8 → put 8 at root, sift down → [1, 2, 8, 5, 3]
     children of 0: 2, 8. min(0)=2 → swap root with 2 → [1, 8, 2, 5, 3]
     ...
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. After `push(5); push(2); push(8); push(1)`, what is `peek()`?
> 2. Why use `(i - 1) >> 1` instead of `Math.floor((i - 1) / 2)`?
> 3. How is heapify(n elements) O(n) when n pushes is O(n log n)?

---

## 6. Brute force — walked through

### Wrong attempt 1: sorted array
`push` does `splice` at the right position — O(n). `pop` removes first — O(n) due to shift. Baseline; immediately upgrade.

### Wrong attempt 2: push unsorted, sort on pop
O(n log n) per pop. Useless beyond toy workloads.

### Wrong attempt 3: linked list
Same time complexity as sorted array, more allocations. Worse cache behaviour.

---

## 7. The unlocking insight

> **Array-backed binary heap. `push` appends + sifts up; `pop` swaps root with last + sifts down. O(log n) each. Sifting is a single while-loop comparing parent vs child or self vs smaller child.**

Three properties:

1. **Implicit tree in array** — no pointers, cache-friendly.
2. **Sift-up on push** — bubble new item toward root.
3. **Sift-down on pop** — drop replacement toward leaves.

---

## 8. Solution (annotated)

```js
class PriorityQueue {
  constructor(compare = (a, b) => a - b) {                          // step 1: default min-heap
    this.heap = [];
    this.compare = compare;
  }

  get size() { return this.heap.length; }
  peek() { return this.heap[0]; }

  push(item) {
    this.heap.push(item);                                            // step 2: append
    this._siftUp(this.heap.length - 1);
  }

  pop() {
    if (this.heap.length === 0) return undefined;
    const top = this.heap[0];
    const last = this.heap.pop();
    if (this.heap.length > 0) {
      this.heap[0] = last;                                            // step 3: move last to root
      this._siftDown(0);
    }
    return top;
  }

  static heapify(items, compare) {                                    // step 4: O(n) build
    const pq = new PriorityQueue(compare);
    pq.heap = items.slice();
    for (let i = (pq.heap.length >> 1) - 1; i >= 0; i--) pq._siftDown(i);
    return pq;
  }

  _siftUp(i) {
    const h = this.heap, cmp = this.compare;
    while (i > 0) {
      const p = (i - 1) >> 1;                                         // parent index
      if (cmp(h[i], h[p]) >= 0) break;                                // heap restored
      [h[i], h[p]] = [h[p], h[i]];                                    // swap
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
      if (smallest === i) break;                                      // heap restored
      [h[i], h[smallest]] = [h[smallest], h[i]];
      i = smallest;
    }
  }
}

// Tiebreaker for FIFO-among-equals
let seq = 0;
const pq = new PriorityQueue((a, b) => a.priority - b.priority || a.seq - b.seq);
pq.push({ priority: 2, seq: seq++, payload: 'a' });
pq.push({ priority: 1, seq: seq++, payload: 'b' });
pq.push({ priority: 2, seq: seq++, payload: 'c' });
// pop order: b (pri 1), a (pri 2 seq 0), c (pri 2 seq 2)
```

**Try it yourself**

```js
const pq = new PriorityQueue();
[5, 2, 8, 1, 3].forEach(x => pq.push(x));
while (pq.size) console.log(pq.pop());      // 1, 2, 3, 5, 8

// Max-heap
const maxPq = new PriorityQueue((a, b) => b - a);
[5, 2, 8].forEach(x => maxPq.push(x));
maxPq.pop();                                 // 8

// O(n) heapify
const fast = PriorityQueue.heapify([5, 2, 8, 1, 3]);
fast.peek();                                 // 1
```

---

## 9. Step-by-step dry run

```
Push sequence [5, 2, 8, 1, 3]:

push(5): heap=[5]                    siftUp(0): exit
push(2): heap=[5, 2]                 siftUp(1): p=0, 2<5 → swap → [2, 5]
push(8): heap=[2, 5, 8]              siftUp(2): p=0, 8≥2 → break
push(1): heap=[2, 5, 8, 1]           siftUp(3): p=1, 1<5 → swap → [2, 1, 8, 5]
                                                  i=1, p=0, 1<2 → swap → [1, 2, 8, 5]
push(3): heap=[1, 2, 8, 5, 3]        siftUp(4): p=1, 3≥2 → break

State: [1, 2, 8, 5, 3]
   1
  / \
 2   8
/ \
5  3

Pop sequence:

pop(): top=1. last=3 → heap=[3, 2, 8, 5]. siftDown(0):
       l=1(2), r=2(8). smallest=1 (2<3). swap → [2, 3, 8, 5]
       i=1, l=3(5), r=4 oob. smallest=1 (3<5). break.  → returns 1

pop(): top=2. last=5 → heap=[5, 3, 8]. siftDown(0):
       l=1(3), r=2(8). smallest=1 (3<5). swap → [3, 5, 8]
       i=1, l=3 oob. break.  → returns 2

pop(): top=3. last=8 → heap=[8, 5]. siftDown(0):
       l=1(5), r=2 oob. smallest=1 (5<8). swap → [5, 8]
       i=1, l=3 oob. break.  → returns 3

pop(): top=5. last=8 → heap=[8]. heap.length>0 → 8 at root, siftDown(0):
       l=1 oob. break.  → returns 5

pop(): top=8. heap.length===0 after pop → skip siftDown. → returns 8

Order: 1, 2, 3, 5, 8 (sorted output).
```

---

## 10. Common confusion + traps

1. **Confusing min-heap and max-heap** when porting from another language. State the comparator.
2. **Off-by-one in child indices** — `2i+1` / `2i+2` for 0-indexed; `2i` / `2i+1` for CLRS 1-indexed.
3. **No empty-heap guard on pop** — return undefined, don't crash.
4. **n pushes when you have a batch** — use `heapify` (O(n)) instead.
5. **Mutating priority of an item already in heap** — silently breaks invariant. Use decrease-key indexed heap.
6. **NaN comparisons** — `NaN < anything` is false; silently breaks invariant.
7. **Duplicate priorities order undefined** — pair with `seq` counter for FIFO-among-equals.

---

## 11. Senior follow-ups & variants

### Variant 1 — Max-heap
Negate comparator: `(a, b) => b - a`. Same DS, reversed order.

### Variant 2 — Indexed / decrease-key heap
`Map<item, index>`; `update(item, newPriority)` looks up and sifts up or down. O(log n). Used by Dijkstra.

### Variant 3 — K-ary heap
K children per node. K=4 reduces tree height; better for cache. Used in some real-world schedulers.

### Variant 4 — Pairing / Fibonacci heap
O(1) amortized decrease-key — theoretically better for Dijkstra; constants too bad in practice.

### Variant 5 — Bounded heap (top-K)
Fixed max size. On `push` past capacity, compare with root and replace. O(log K) regardless of input.

### Variant 6 — `replace(item)` (pop+push fused)
Replace top in one sift-down. Used in K-way merge.

---

## 12. How to think aloud

> "Array-backed binary heap. Parent `(i-1)>>1`, children `2i+1`, `2i+2`. Heap invariant: parent ≤ children (min-heap). `push`: append, sift up (swap with parent while smaller). `pop`: take root, move last to root, sift down (swap with smaller child). O(log n) each, O(1) peek. Custom comparator for max-heap or object-priority. `heapify(arr)` is O(n) bottom-up sift-down — beats n pushes (O(n log n)). FIFO-among-equals: pair priority with insertion counter. Backbone of: Dijkstra, A*, top-K, K-way merge, scheduler. Trap: mutating priority in place — use decrease-key indexed heap. Trap: empty pop crash. Trap: n pushes when batch."

---

## 13. 60-second revision

> - **Array-backed binary heap.** Parent `(i-1)>>1`, children `2i+1`, `2i+2`.
> - **`push`** = append + sift up. **`pop`** = swap root with last, sift down. O(log n).
> - **`peek`** = O(1) (heap[0]).
> - **Custom comparator** for max-heap, object-priority, ties via insertion counter.
> - **`heapify`** = bottom-up sift-down, O(n).
> - **Decrease-key indexed heap** for Dijkstra.
> - **Family:** top-K, K-way merge, A*, async scheduler, rate-limiter delayed slots.
> - **Trap:** off-by-one children; empty pop; mutate priority in place; NaN.

---

**Related:** [trie.md](./trie.md) · [lru-cache.md](./lru-cache.md) · [`04-promises/priority-async-queue.md`](../04-promises/priority-async-queue.md) · [scheduler-idle-callback.md](./scheduler-idle-callback.md)

**Concept primer:** [`concepts/recursion.md`](../../concepts/recursion.md), [`concepts/arrays.md`](../../concepts/arrays.md)
