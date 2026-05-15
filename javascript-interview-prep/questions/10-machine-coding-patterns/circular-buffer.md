# Implement a Circular Buffer (Fixed-size Ring Queue)

## Source
- Classic data-structures interview problem (LeetCode #622 "Design Circular Queue").
- Used everywhere: audio/video frame buffers, network packet ring buffers (DPDK, io_uring), rolling-window metrics, ring loggers, V8's GC write barriers.

## Why this question matters in interviews
Circular buffer is the **fixed-memory FIFO** every systems-leaning engineer should know. The naive approach (`Array.prototype.shift`) is O(n) per dequeue and reallocates as it grows; the ring buffer is O(1) for both push and shift with **zero allocations after construction**. Implementing one tests **head/tail index arithmetic**, **modulo arithmetic for wrap-around**, **the full vs empty disambiguation**, and **the policy choice** (overwrite oldest vs reject new). Backend interviewers ask this when probing whether you understand bounded-memory data structures — critical for log aggregation, time-series sliding windows, websocket message buffers, retry queues with size limits.

## Concepts involved

### Syntax to lock in
```js
class CircularBuffer {
  constructor(capacity, { overwrite = true } = {}) {
    this.buf = new Array(capacity);
    this.capacity = capacity;
    this.head = 0;          // index of oldest item
    this.tail = 0;          // index where next push lands
    this.size = 0;
    this.overwrite = overwrite;
  }

  push(item) {
    if (this.size === this.capacity) {
      if (!this.overwrite) return false;
      this.head = (this.head + 1) % this.capacity;   // drop oldest
    } else {
      this.size++;
    }
    this.buf[this.tail] = item;
    this.tail = (this.tail + 1) % this.capacity;
    return true;
  }

  shift() {
    if (this.size === 0) return undefined;
    const v = this.buf[this.head];
    this.buf[this.head] = undefined;            // release reference
    this.head = (this.head + 1) % this.capacity;
    this.size--;
    return v;
  }

  peek() { return this.size === 0 ? undefined : this.buf[this.head]; }
  isFull()  { return this.size === this.capacity; }
  isEmpty() { return this.size === 0; }
}
```

### Runtime / engine behavior
- The buffer is a **fixed-length array**; head/tail indices walk around it modulo capacity. After capacity allocations, no further allocations happen — this is the key property.
- **Full vs empty disambiguation** — when `head === tail`, the buffer could be empty OR full. Two solutions: (a) track an explicit `size` field (what we do above), (b) waste one slot so full is `(tail + 1) % cap === head`. The size-field approach is cleaner and lets you query length in O(1).
- Modulo arithmetic: `(i + 1) % capacity` wraps the index back to 0 when it reaches `capacity`. Cheap on modern CPUs; if `capacity` is a power of 2, you can replace with `(i + 1) & (capacity - 1)` for a tiny speedup.
- `overwrite` policy: when full, do we drop the oldest (advance head) or reject the new write? Both are valid; the policy depends on use case. Logs typically overwrite (keep most recent). Backpressure queues typically reject (signal the producer to slow down).
- Setting `buf[head] = undefined` on shift is important — without it, the array still holds a reference to the dequeued item, preventing GC.

### Edge cases (these are the interview traps)
1. **Capacity 0** — degenerate. Reject `push` always, `shift` always returns undefined. Either throw at construction or handle silently.
2. **Capacity 1** — single slot. Every push overwrites if `overwrite=true`. Easy to write a wrong implementation that breaks here; test it.
3. **Full-vs-empty ambiguity** — without an explicit `size` field, `head === tail` is ambiguous. Most interview candidates wing it and produce a buffer that thinks it's empty when full or vice versa.
4. **Overwrite + size update** — when overwriting, you don't increment size (still at capacity). Easy off-by-one bug.
5. **Releasing references** — failing to null out `buf[head]` on shift is a memory leak. Items live forever even after "dequeue."
6. **Iteration** — implementing `[Symbol.iterator]` should yield from head to tail in insertion order, not the underlying array order. Walk via `(head + i) % capacity`.
7. **Concurrent push/shift** — JS is single-threaded so this isn't an issue in user code. In Worker + SharedArrayBuffer scenarios, you need atomics; out of scope unless asked.
8. **Resize / dynamic capacity** — not part of "fixed-size." If interviewer asks, mention that growing a ring buffer requires allocating a new array and copying head→tail-region in order. O(n) operation.

## Brute force approach
"I'll use a regular array and `.push()` / `.shift()`." `push` is amortized O(1), but `shift` is O(n) because it re-indexes the entire array. For a high-throughput buffer (millions of ops/sec) this is fatal. Mention as the baseline; the whole point of circular buffer is replacing O(n) shift with O(1) wrap-around.

Another non-starter: a doubly-linked list. O(1) push and shift, but every node allocates; with 1 million ops/sec you'll spend more time in GC than doing work. Ring buffer's zero-allocation property is what makes it suitable for hot paths.

## Optimal approach
Array of fixed capacity + head/tail indices + size counter. Push at tail, shift from head, wrap modulo capacity. O(1) push, O(1) shift, O(1) peek, O(1) size. Zero allocations after construction.

## Solution (JavaScript)

```js
/**
 * Fixed-capacity ring queue. O(1) push / shift / peek.
 * @template T
 */
class CircularBuffer {
  /**
   * @param {number} capacity
   * @param {{ overwrite?: boolean }} [options]
   *   overwrite=true (default): full push drops the oldest item.
   *   overwrite=false: full push returns false (caller must apply backpressure).
   */
  constructor(capacity, { overwrite = true } = {}) {
    if (!Number.isInteger(capacity) || capacity < 1) {
      throw new RangeError('capacity must be a positive integer');
    }
    this.capacity = capacity;
    this.buf = new Array(capacity);
    this.head = 0;
    this.tail = 0;
    this.size = 0;
    this.overwrite = overwrite;
  }

  push(item) {
    if (this.size === this.capacity) {
      if (!this.overwrite) return false;
      // Drop oldest: advance head; size stays at capacity.
      this.head = (this.head + 1) % this.capacity;
    } else {
      this.size++;
    }
    this.buf[this.tail] = item;
    this.tail = (this.tail + 1) % this.capacity;
    return true;
  }

  shift() {
    if (this.size === 0) return undefined;
    const value = this.buf[this.head];
    this.buf[this.head] = undefined;              // release ref for GC
    this.head = (this.head + 1) % this.capacity;
    this.size--;
    return value;
  }

  peek() { return this.size === 0 ? undefined : this.buf[this.head]; }
  isFull()  { return this.size === this.capacity; }
  isEmpty() { return this.size === 0; }
  clear()   { this.head = 0; this.tail = 0; this.size = 0; this.buf.fill(undefined); }

  /** Iterate from oldest to newest. */
  *[Symbol.iterator]() {
    for (let i = 0; i < this.size; i++) {
      yield this.buf[(this.head + i) % this.capacity];
    }
  }

  toArray() { return [...this]; }
}
```

## Step-by-step dry run

Input (overwrite=true, capacity=3):
```js
const buf = new CircularBuffer(3);
buf.push(1);            // [1, _, _] head=0 tail=1 size=1
buf.push(2);            // [1, 2, _] head=0 tail=2 size=2
buf.push(3);            // [1, 2, 3] head=0 tail=0 size=3 (FULL)
buf.push(4);            // overwrite: drop head=1, store 4 at tail=0 → [4, 2, 3] head=1 tail=1 size=3
buf.shift();            // returns 2. head=2 size=2. buf=[4, undef, 3]
buf.push(5);            // size<cap so size++. tail=1 → buf=[4, 5, 3] head=2 tail=2 size=3
buf.toArray();          // [3, 4, 5] (insertion order: head walk)
```

Trace push(4) (overwrite case):
- size===capacity (3). overwrite=true. head=(0+1)%3=1. (size stays 3.)
- buf[tail=0]=4. tail=(0+1)%3=1.
- Result: buf=[4,2,3], head=1, tail=1, size=3.

Trace shift():
- size!=0. value=buf[head=1]=2. buf[1]=undefined. head=2. size=2.
- Returns 2.

Trace push(5):
- size!=cap. size++=3. buf[tail=1]=5. tail=(1+1)%3=2.
- Result: buf=[4,5,3], head=2, tail=2, size=3.

Trace toArray():
- Yield buf[(2+0)%3=2]=3. Yield buf[(2+1)%3=0]=4. Yield buf[(2+2)%3=1]=5. → [3,4,5].

Rejection mode (overwrite=false):
```js
const buf = new CircularBuffer(2, { overwrite: false });
buf.push(1); buf.push(2);
buf.push(3);   // returns false. buf still [1,2].
buf.shift();   // returns 1. now [2, _].
buf.push(3);   // returns true. buf=[3,2] head=1 tail=1 size=2.
```

## Important takeaways

**Syntax to memorize**
- `head`, `tail`, `size`, fixed `capacity`. Index advance: `(i + 1) % capacity`.
- Three index fields disambiguate full vs empty (don't rely on `head === tail`).
- Push at tail, shift from head. Bookkeeping is the only state.
- Null out `buf[head]` after shift to release the reference.

**Patterns to reuse**
- Modulo wrap-around is the same trick used in hash tables (probing), Bloom filter bit arrays, frame buffers, audio sample queues.
- Power-of-two capacities + bit-and instead of modulo is a micro-optimization used in real-time audio code.
- "Overwrite vs reject" policy choice generalizes to any bounded queue (logs, retry queues, websocket buffers).

**Common mistakes**
- Using `head === tail` as the full/empty check without a size field — ambiguous.
- Forgetting to update `size` correctly in the overwrite case (don't increment).
- Not nulling out shifted slots — memory leak.
- Off-by-one in iteration: walking from `head` to `tail` directly without wrapping.
- Using `Array.prototype.splice` for "remove from middle" — destroys the ring property. Ring buffers don't support arbitrary deletion.

**Related questions**
- Sliding window (rate limiter, moving average) — circular buffer over timestamps.
- Bounded async queue with backpressure.
- ETL log batcher with max-size cap.
- Reservoir sampling (similar bounded random selection).
- Lock-free SPSC queue (extends to Worker + SharedArrayBuffer).

## Variants

1. **Rolling-window statistics** — circular buffer of (timestamp, value) pairs. On read, sum/avg/max only items within the window. Constant memory regardless of input rate.

2. **Bounded async queue** — push returns a Promise that resolves when slot is available (instead of rejecting). Implements backpressure. Used by p-queue, bull, etc.

3. **Multi-producer single-consumer (MPSC)** — multiple writers, one reader. In JS user-land single-threaded code this is a non-issue. With SharedArrayBuffer + Atomics, it's a real thing (lock-free SPSC/MPSC queues are a research topic).

4. **Typed array backing** — use `Int32Array` / `Float32Array` for numeric workloads. Eliminates per-element heap allocation entirely. Used in audio/DSP code.

5. **Resizable** — track high-water mark; if push hits capacity AND overwrite=false, allocate a new array of 2x capacity and copy in head-to-tail order. Amortized O(1).

## Revision notes

> **Circular buffer — 60 second recap**
> - Fixed-cap array + `head`, `tail`, `size`. Advance with `(i + 1) % capacity`.
> - Push at tail, shift from head. O(1) both.
> - `size` field disambiguates full from empty (head==tail is ambiguous otherwise).
> - Policy: overwrite (drop oldest) vs reject (return false). Logs overwrite; backpressure queues reject.
> - Always null out shifted slot for GC.
> - Iterator walks `(head + i) % cap` for i in 0..size.
> - Trap: head==tail ambiguity, missing size update in overwrite path, leaked references on shift, off-by-one in iteration.
> - Use: rolling metrics, packet buffers, audio frames, log ring, retry queue cap.
