# Implement a Circular Buffer (fixed-size ring queue)

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`02-closures/ring-buffer-via-closure.md`](../02-closures/ring-buffer-via-closure.md), [`concepts/arrays.md`](../../concepts/arrays.md)
>
> **Source:** <a href="https://leetcode.com/problems/design-circular-queue/" target="_blank" rel="noopener noreferrer">LeetCode 622 — Design Circular Queue</a>. Used in audio/video frame buffers, packet rings (DPDK, io_uring), rolling-window metrics, ring loggers.

---

## 1. Problem statement

**Signature**
```ts
class CircularBuffer<T> {
  constructor(capacity: number, options?: { overwrite?: boolean });
  push(item: T): boolean;       // false if full and overwrite=false
  shift(): T | undefined;
  peek(): T | undefined;
  isFull(): boolean;
  isEmpty(): boolean;
  size: number;
  [Symbol.iterator](): Iterator<T>;
}
```

**Input / Output examples**

| Setup (cap=3, overwrite=true)       | Buffer state          | Result |
|-------------------------------------|-----------------------|--------|
| `push(1); push(2); push(3)`         | `[1, 2, 3]` full      |        |
| `push(4)` (overwrite)               | `[4, 2, 3]` head=1    | true   |
| `shift()`                           | `[4, _, 3]` head=2    | `2`    |
| `push(5)`                           | `[4, 5, 3]` head=2    | true   |
| `toArray()`                          | head-to-tail order    | `[3, 4, 5]` |

With `overwrite=false`: `push` when full returns `false` (backpressure signal).

**Constraints**
- Fixed-length array; zero allocations after construction.
- O(1) push, shift, peek.
- Track `head`, `tail`, `size` (size disambiguates full vs empty).
- Choose overwrite (drop oldest) or reject (return false) policy upfront.

---

## 2. Plain-English restatement

A queue with a fixed maximum size. Insertions go in at the tail; removals come out at the head. When the buffer wraps around the end of the underlying array, indices use modulo arithmetic. Two policies when full: **overwrite** the oldest (logs, ring loggers) or **reject** the new write (backpressure queues).

---

## 3. Why this matters in interviews

The **fixed-memory FIFO** every systems-leaning engineer should know. Naive `Array.prototype.shift` is O(n) per dequeue and reallocates. The ring buffer is O(1) for both push and shift with **zero allocations after construction**. Probes: head/tail arithmetic, wrap-around modulo, full-vs-empty disambiguation, and the policy choice. Backend uses: log aggregation, sliding-window metrics, websocket message buffers, retry queues with size limits.

---

## 4. Mental model

```
   capacity = 5, head=0, tail=0, size=0
   [ _, _, _, _, _ ]

   push(A): tail=1, size=1
   [ A, _, _, _, _ ]
     ↑head ↑tail

   push(B), push(C), push(D), push(E):  full
   [ A, B, C, D, E ]
     ↑head           ↑tail (wrapped to 0)
   size=5

   push(F) with overwrite=true:
   advance head: head=1; write at tail=0; tail=1
   [ F, B, C, D, E ]
        ↑head ↑tail
   size=5 (still)

   shift():
   read buf[head=1]=B; buf[1]=undefined; head=2; size=4
   [ F, _, C, D, E ]
            ↑head ↑tail (=0... not shown)
```

**Why `size` field:** without it, `head === tail` is ambiguous (could be empty OR full). Explicit `size` field disambiguates in O(1).

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With capacity=3 and three pushes, what are `head`, `tail`, and `size`?
> 2. Why is `[].shift()` on a 1-million-element array O(n)?
> 3. If `head === tail`, is the buffer empty or full? How do you tell?

---

## 6. Brute force — walked through

### Wrong attempt 1: array + `push`/`shift`
`.shift()` is O(n) — re-indexes the entire array. Fine at small N, fatal at scale.

### Wrong attempt 2: doubly-linked list
O(1) push/shift but every node allocates. GC churn at 1M ops/sec. Ring buffer's zero-allocation property is its edge.

### Wrong attempt 3: rely on `head === tail` for full/empty
Ambiguous. Either waste one slot (full = `(tail+1) % cap === head`) or track explicit `size`. Size is cleaner.

---

## 7. The unlocking insight

> **Fixed array + `head` + `tail` + `size`. Push at tail, shift from head. Wrap with `(i + 1) % capacity`. Size disambiguates full from empty. Null out shifted slot for GC.**

Three properties:

1. **Modulo wrap** — `(i + 1) % capacity` keeps indices in range.
2. **`size` field** — full/empty disambiguation in O(1).
3. **Null shifted slot** — release reference for GC.

---

## 8. Solution (annotated)

```js
class CircularBuffer {
  constructor(capacity, { overwrite = true } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be a positive integer');
    }
    this.capacity = capacity;
    this.buf = new Array(capacity);                                 // step 1: fixed alloc
    this.head = 0;
    this.tail = 0;
    this.size = 0;
    this.overwrite = overwrite;
  }

  push(item) {
    if (this.size === this.capacity) {                              // step 2: full path
      if (!this.overwrite) return false;
      this.head = (this.head + 1) % this.capacity;                  // drop oldest
    } else {
      this.size++;
    }
    this.buf[this.tail] = item;                                      // step 3: write at tail
    this.tail = (this.tail + 1) % this.capacity;
    return true;
  }

  shift() {
    if (this.size === 0) return undefined;
    const value = this.buf[this.head];
    this.buf[this.head] = undefined;                                 // step 4: release ref
    this.head = (this.head + 1) % this.capacity;
    this.size--;
    return value;
  }

  peek()    { return this.size === 0 ? undefined : this.buf[this.head]; }
  isFull()  { return this.size === this.capacity; }
  isEmpty() { return this.size === 0; }
  clear()   { this.head = 0; this.tail = 0; this.size = 0; this.buf.fill(undefined); }

  *[Symbol.iterator]() {                                              // step 5: head→tail walk
    for (let i = 0; i < this.size; i++) {
      yield this.buf[(this.head + i) % this.capacity];
    }
  }
  toArray() { return [...this]; }
}
```

**Try it yourself**

```js
const buf = new CircularBuffer(3);
buf.push(1); buf.push(2); buf.push(3);     // [1,2,3] full
buf.push(4);                                // overwrite → [4,2,3], head=1
buf.shift();                                // returns 2; [4,_,3], head=2
buf.push(5);                                // [4,5,3], head=2, tail=2
buf.toArray();                              // [3,4,5]

// Rejection mode
const q = new CircularBuffer(2, { overwrite: false });
q.push(1); q.push(2);
q.push(3);                                  // false (backpressure signal)
```

---

## 9. Step-by-step dry run

```
capacity=3, overwrite=true

push(1):  size 0→1, buf[tail=0]=1, tail=1. state: [1,_,_] h=0 t=1 size=1
push(2):  size 1→2, buf[1]=2, tail=2. state: [1,2,_] h=0 t=2 size=2
push(3):  size 2→3, buf[2]=3, tail=0. state: [1,2,3] h=0 t=0 size=3 (FULL)
push(4):  size===cap. overwrite. head=(0+1)%3=1. buf[tail=0]=4. tail=1.
          state: [4,2,3] h=1 t=1 size=3
shift():  v=buf[head=1]=2. buf[1]=undefined. head=2. size=2.
          state: [4,_,3] h=2 t=1 size=2. returns 2.
push(5):  size<cap. size 2→3. buf[tail=1]=5. tail=2.
          state: [4,5,3] h=2 t=2 size=3

toArray():
  walk i=0..2:
    i=0: buf[(2+0)%3=2] = 3
    i=1: buf[(2+1)%3=0] = 4
    i=2: buf[(2+2)%3=1] = 5
  → [3, 4, 5]
```

---

## 10. Common confusion + traps

1. **`head === tail` for full/empty** — ambiguous. Use explicit `size`.
2. **Forget size update in overwrite path** — `size` stays at capacity; don't increment.
3. **Not nulling shifted slot** — memory leak.
4. **Off-by-one in iteration** — walk via `(head + i) % capacity`, don't go directly head→tail.
5. **`splice` for "remove from middle"** — destroys ring property. Ring buffers don't support arbitrary deletion.
6. **Capacity 0 or 1** — degenerate; handle or reject in constructor.
7. **Confusing with `Array.shift`** — array shift is O(n); ring buffer shift is O(1).

---

## 11. Senior follow-ups & variants

### Variant 1 — Rolling-window stats
Circular buffer of `(timestamp, value)` pairs. On read, sum/avg/max only items within the window. Constant memory regardless of input rate.

### Variant 2 — Bounded async queue with backpressure
`push` returns a Promise that resolves when slot is available (instead of rejecting). Used by p-queue, bull.

### Variant 3 — Typed-array backing
`Int32Array` / `Float32Array` for numeric workloads. Eliminates per-element heap allocation. Audio/DSP.

### Variant 4 — Power-of-2 capacity
Replace `% capacity` with `& (capacity - 1)`. Tiny speedup, common in real-time code.

### Variant 5 — Resizable
Allocate new array of 2× capacity, copy head→tail in order. Amortized O(1).

### Variant 6 — SPSC/MPSC lock-free (`SharedArrayBuffer` + `Atomics`)
Multi-thread (Worker) variant. Research topic.

---

## 12. How to think aloud

> "Fixed array + `head`, `tail`, `size`. Push at tail, shift from head, wrap with `(i+1) % capacity`. Size disambiguates full from empty (head==tail alone is ambiguous). Null shifted slot for GC. Policy: overwrite (drop oldest — logs) vs reject (return false — backpressure queues). Iterator walks `(head + i) % capacity` for i in 0..size, so consumers see head-to-tail insertion order. Trap: ambiguous full/empty without size field. Trap: leaked references on shift. Variants: rolling-window stats, bounded async queue with backpressure, power-of-2 + bit-and, typed-array backing."

---

## 13. 60-second revision

> - **Fixed array** + `head` + `tail` + `size`.
> - **Advance** with `(i + 1) % capacity`.
> - **Size disambiguates** full from empty.
> - **Policy:** overwrite (drop oldest) vs reject (return false).
> - **Null shifted slot** for GC.
> - **Iterator:** `(head + i) % cap` for `i in [0, size)`.
> - **Family:** rolling-window stats, bounded async queue, audio frame buffer, log ring.
> - **Trap:** head==tail ambiguity; missed size update in overwrite; leaked refs; off-by-one iteration.

---

**Related:** [`02-closures/ring-buffer-via-closure.md`](../02-closures/ring-buffer-via-closure.md) · [lru-cache.md](./lru-cache.md) · [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md) · [`06-streams/backpressure-and-highwater.md`](../06-streams/backpressure-and-highwater.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
