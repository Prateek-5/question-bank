# Build `createRingBuffer(capacity)` — fixed-size O(1) FIFO

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [counter-ii.md](./counter-ii.md), [private-data-counter.md](./private-data-counter.md), [`concepts/closures.md`](../../concepts/closures.md)
>
> **Source:** Classic data structure (metrics, logging buffers, audio streaming). Asked at Razorpay, Atlassian, Cloudflare.

---

## 1. Problem statement

**Signature**
```ts
function createRingBuffer<T>(capacity: number): {
  push(v: T): void;           // overwrite oldest if full
  shift(): T | undefined;     // FIFO read
  peek(): T | undefined;
  toArray(): T[];
  readonly length: number;
  readonly capacity: number;
};
```

**Input / Output examples**

| Setup                  | Sequence of calls                              | State / Output                          |
|------------------------|------------------------------------------------|------------------------------------------|
| `cap=3`               | `push(a); push(b); push(c);`                  | `length=3` (full); `toArray() = [a,b,c]` |
| `cap=3` (full)        | `push(d)`                                      | overwrites oldest; `toArray() = [b,c,d]` |
| `cap=3`               | `shift(); shift();`                            | returns `a, b`; `length=1`               |
| `cap=3` (empty)       | `shift()`                                      | `undefined`                              |
| Wraparound            | `cap=3`; alternating push/shift over many ops  | O(1) per op; no array reindexing         |

**Constraints**
- `push` and `shift` must be **O(1)** — no `Array.prototype.shift` reindexing.
- When full, `push` **overwrites the oldest** (default policy; document if changed).
- Distinguish empty from full when `head === tail` — use an explicit `count`.
- Closure hides internal state; only methods are exposed.

---

## 2. Plain-English restatement

Build a fixed-capacity FIFO queue where pushing past the limit silently drops the oldest entry. The internal storage is a fixed-size array; `head` is where the next push goes; `tail` is where the next shift comes from; both wrap around the array via modulo arithmetic. An explicit `count` distinguishes empty (`count=0`) from full (`count=capacity`) — without it, `head === tail` is ambiguous.

Real-world uses: rolling log buffer ("last 1000 messages"), audio sample window ("last 1 second @ 48 kHz"), metrics sliding window, replay buffer for crash diagnostics.

---

## 3. Why this matters in interviews

Three things tested at once. **Closure encapsulation** — the internal state (`buf`, `head`, `tail`, `count`) must be hidden; only methods are exposed. **Modular arithmetic** — wraparound via `(idx + 1) % capacity` is a classic gotcha (forgetting the modulo, off-by-one). **Policy thinking** — overflow behavior is a design choice the candidate must own: overwrite oldest, reject new, or throw. Pick one explicitly and justify.

---

## 4. Mental model

A **fixed circular track** with two pointers chasing each other. The `tail` is where the next read happens; the `head` is where the next write goes. When `head` catches up to `tail` from behind, the buffer is full — the next push has to advance both pointers (overwrite the oldest).

```
   capacity = 5
   ┌────────────────────────────┐
   │  [_]  [_]  [_]  [_]  [_]   │   empty
   │   t,h                       │
   └────────────────────────────┘
   
   push(a), push(b), push(c)
   ┌────────────────────────────┐
   │  [a]  [b]  [c]  [_]  [_]   │   count=3
   │   t            h            │
   └────────────────────────────┘
   
   push(d), push(e)
   ┌────────────────────────────┐
   │  [a]  [b]  [c]  [d]  [e]   │   count=5 (FULL)
   │   t,h                       │   head wrapped to 0; equals tail
   └────────────────────────────┘
   
   push(f)
   ┌────────────────────────────┐
   │  [f]  [b]  [c]  [d]  [e]   │   count stays 5
   │   h    t                    │   head advanced past tail; tail moves too (overwrite)
   └────────────────────────────┘
   
   shift() → b
   ┌────────────────────────────┐
   │  [f]  [_]  [c]  [d]  [e]   │   count=4
   │   h         t               │   tail advanced; slot nulled
   └────────────────────────────┘
```

The pointers chase around the ring; the `count` is the source of truth for "how full am I."

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `capacity=5`, after `push(a..e)` the buffer is full. After `push(f)`, what does `toArray()` return — `[a,b,c,d,e,f]` (six items) or `[b,c,d,e,f]` (five)?
> 2. Why is `head === tail` ambiguous? What's the +1-trick alternative to using an explicit `count`?
> 3. Why is `Array.prototype.shift()` an O(N) operation, and how does the ring buffer beat it?

---

## 6. Brute force — walked through

### Wrong attempt 1: `Array.shift` on overflow

```js
class Naive {
  buf = [];
  capacity;
  constructor(cap) { this.capacity = cap; }
  push(v) {
    this.buf.push(v);
    if (this.buf.length > this.capacity) this.buf.shift();   // BUG: O(N)
  }
  shift() { return this.buf.shift(); }                        // also O(N)
}
```

`Array.shift()` shifts every element down by one — O(N). On a 10k-element buffer, each push triggers a 10k-element copy. The whole point of a ring buffer is O(1) ops; you've reinvented an inefficient queue.

### Wrong attempt 2: `head === tail` as empty/full discriminator

```js
function createRingBuffer(capacity) {
  const buf = new Array(capacity);
  let head = 0, tail = 0;
  return {
    push(v) { buf[head] = v; head = (head + 1) % capacity; },   // BUG: no overflow check
    shift() {
      if (head === tail) return undefined;    // BUG: same condition for full AND empty
      const v = buf[tail];
      tail = (tail + 1) % capacity;
      return v;
    },
  };
}
```

`head === tail` is true both when empty (nothing pushed yet) and when wrapped fully around. Without a `count` or a "leave one slot empty" trick, you can't tell which.

### Wrong attempt 3: forget the modulo on wraparound

```js
push(v) {
  buf[head] = v;
  head++;                       // BUG: head grows past capacity
  if (head >= capacity) head = 0;
}
```

Works mechanically — but you might write `head++` and forget the bounds check, or do it inconsistently between `push` and `shift`. The cleaner form is `head = (head + 1) % capacity` everywhere. Pick the idiom and stick with it.

---

## 7. The unlocking insight

> **Two pointers on a fixed array, with an explicit `count` to disambiguate full from empty. Modulo arithmetic wraps both pointers around the array boundary. Closure hides the four state slots; only methods are exposed.**

The recipe has four pieces:

1. **Fixed array** of size `capacity`, allocated once at construction.
2. **`head` pointer** — index of the next *write*. Advances on push.
3. **`tail` pointer** — index of the next *read*. Advances on shift.
4. **`count`** — current number of items. Distinguishes empty from full.

The operations:

- **`push(v)`**: write to `buf[head]`; advance `head` modulo capacity; if `count === capacity` (already full), also advance `tail` (overwrite oldest); else `count++`.
- **`shift()`**: if `count === 0`, return `undefined`; else read from `buf[tail]`, null the slot (GC hint), advance `tail` modulo capacity, `count--`.
- **`peek()`**: return `buf[tail]` if `count > 0`, else `undefined`.
- **`toArray()`**: walk from `tail` for `count` steps, modulo capacity.

**Why null the slot on shift?** The array holds a reference; without nulling, the popped object stays reachable via the slot — leaks memory if you store large objects. For primitives, doesn't matter.

**Why modulo and not `if (head >= cap) head = 0`?** The modulo form is idiomatic, hard to get wrong, and the engine optimizes it well. Conditional bounds checks invite off-by-one bugs.

**Alternative "+1 trick" for empty/full disambiguation**: reserve one slot — when `(head + 1) % cap === tail`, you're full. Saves the `count` variable at the cost of one unusable slot. Not worth it in JS; just keep `count`.

---

## 8. Solution (annotated)

```js
function createRingBuffer(capacity) {
  if (!Number.isInteger(capacity) || capacity <= 0) {            // step 1: validate
    throw new RangeError('capacity must be a positive integer');
  }
  const buf = new Array(capacity);                                // step 2: fixed-size storage
  let head = 0;                                                   // step 3: next write index
  let tail = 0;                                                   // step 4: next read index
  let count = 0;                                                  // step 5: live element count

  return {
    push(v) {
      buf[head] = v;                                              // step 6: write
      head = (head + 1) % capacity;                                // step 7: advance head with wrap
      if (count === capacity) {                                    // step 8: full?
        tail = (tail + 1) % capacity;                              //         overwrite oldest
      } else {
        count++;
      }
    },
    shift() {
      if (count === 0) return undefined;                           // step 9: empty
      const v = buf[tail];
      buf[tail] = undefined;                                       // step 10: null slot (GC hint)
      tail = (tail + 1) % capacity;
      count--;
      return v;
    },
    peek() {
      return count === 0 ? undefined : buf[tail];
    },
    get length() { return count; },
    get capacity() { return capacity; },
    toArray() {
      const out = [];
      for (let i = 0, t = tail; i < count; i++, t = (t + 1) % capacity) {
        out.push(buf[t]);                                          // step 11: walk from tail
      }
      return out;
    },
  };
}
```

**Try it yourself**

```js
const recentLogs = createRingBuffer(1000);
function log(msg) { recentLogs.push({ ts: Date.now(), msg }); }

// Audio sample window
const samples = createRingBuffer(48000);   // 1 second @ 48 kHz
function onAudioSample(s) { samples.push(s); }
function getLatest1s() { return samples.toArray(); }

// Roll over a small buffer
const buf = createRingBuffer(3);
buf.push('a'); buf.push('b'); buf.push('c');
console.log(buf.toArray());   // ['a', 'b', 'c']
buf.push('d');                  // overwrites 'a'
console.log(buf.toArray());   // ['b', 'c', 'd']
buf.shift();                    // 'b'
console.log(buf.length);       // 2
```

---

## 9. Step-by-step dry run

Input: `capacity=3`, push `a, b, c, d`, then shift twice.

Values-first trace:

| Step       | Action      | `head` | `tail` | `count` | `buf`         | Returns      |
|------------|-------------|--------|--------|---------|----------------|---------------|
| init       | —           | 0      | 0      | 0       | `[_,_,_]`      | (buffer)      |
| `push(a)`  | write+wrap  | 1      | 0      | 1       | `[a,_,_]`      | —             |
| `push(b)`  |             | 2      | 0      | 2       | `[a,b,_]`      | —             |
| `push(c)`  | full        | 0 (wrap) | 0    | 3       | `[a,b,c]`      | —             |
| `push(d)`  | overwrite   | 1      | 1      | 3       | `[d,b,c]`      | (a evicted)   |
| `shift()`  | read tail=1 | 1      | 2      | 2       | `[d,_,c]`      | `b`           |
| `shift()`  | read tail=2 | 1      | 0      | 1       | `[d,_,_]`      | `c`           |
| `shift()`  |             | 1      | 1      | 0       | `[_,_,_]`      | `d`           |
| `shift()`  | empty       | 1      | 1      | 0       | (same)         | `undefined`   |

Pointers wrap around the array; `count` is the unambiguous indicator. After eviction, `'a'` is no longer reachable from any slot.

---

## 10. Common confusion + traps

1. **`Array.prototype.shift` is O(N).**
   Don't use it. The whole point of a ring buffer is O(1) ops. Use head/tail/count with modulo.

2. **`head === tail` is ambiguous.**
   Could mean empty or full. Use an explicit `count`. The "+1 trick" (reserve one slot) is the alternative but loses capacity-1 usable storage.

3. **Forgetting the modulo on wraparound.**
   `head = (head + 1) % capacity` is the idiom. Inconsistent wrap handling between push and shift is a classic off-by-one source.

4. **GC leak via stale slot references.**
   When you shift, set `buf[tail] = undefined` before advancing. Otherwise the array holds the reference and prevents GC for big payloads.

5. **Iteration starting at index 0.**
   `toArray` must walk from `tail`, not from `0`. The physical order in `buf` is rotated against the logical FIFO order.

6. **Capacity 0 or negative.**
   Throw at construction. Trying to handle it leads to division-by-zero or weird states.

7. **Overflow policy.**
   Default is overwrite-oldest. Alternatives: reject-new (`push` returns `false`), throw, or auto-grow (defeats the "fixed memory" guarantee). Document and pick one.

8. **Concurrent access.**
   In Node single-threaded JS, no concurrency issue. For cross-Worker via `SharedArrayBuffer`, use `Atomics.add`/`compareExchange` on a typed-array-backed buffer.

---

## 11. Senior follow-ups & variants

### Variant 1 — Drop-newest on overflow

```js
push(v) {
  if (count === capacity) return false;    // drop the new value; report failure
  buf[head] = v;
  head = (head + 1) % capacity;
  count++;
  return true;
}
```

For input rate limiters or admission control where you want to **reject** new work rather than drop old.

### Variant 2 — Auto-grow

```js
push(v) {
  if (count === capacity) {
    const next = new Array(capacity * 2);
    for (let i = 0; i < count; i++) next[i] = buf[(tail + i) % capacity];
    buf = next; tail = 0; head = count; capacity = next.length;
  }
  buf[head] = v;
  head = (head + 1) % capacity;
  count++;
}
```

Defeats the "fixed memory" guarantee — your monitoring won't see a bound. Use only when the upstream rate is genuinely unbounded but rare.

### Variant 3 — Typed-array backed (numeric streams)

```js
function createNumericRingBuffer(capacity) {
  const buf = new Float64Array(capacity);    // contiguous; cache-friendly
  // ... same pointer logic ...
}
```

For audio, metrics, or any numeric workload. Avoids V8 polymorphic-array hits; 8 bytes per entry instead of pointer + boxing.

### Variant 4 — Lock-free SAB version

```js
const sab = new SharedArrayBuffer(capacity * 8 + 24);
const view = new Int32Array(sab);
// view[0] = head, view[1] = tail, view[2] = count, view[3..] = data
// Use Atomics.add / compareExchange for pointer updates
```

Cross-Worker safe. Used for high-throughput producer/consumer pipelines (audio threads, worker pools).

### Variant 5 — Iterator support

```js
return {
  // ... existing ...
  [Symbol.iterator]() {
    let i = 0;
    return {
      next: () => i < count
        ? { value: buf[(tail + i++) % capacity], done: false }
        : { value: undefined, done: true },
    };
  },
};
```

Enables `for (const item of ringBuf) ...` and spread `[...ringBuf]`. Idiomatic in modern JS.

---

## 12. How to think aloud in the interview

> "Ring buffer: fixed array, head pointer (next write), tail pointer (next read), explicit count (distinguishes full from empty). Modulo arithmetic wraps both pointers. Push writes at head, advances head modulo capacity; if full, also advances tail to overwrite the oldest. Shift reads at tail, advances tail. Always null the popped slot for GC. Iteration starts at tail, walks count steps. Overflow policy is a design choice — default overwrite-oldest, but reject-new or auto-grow are valid for different use cases. For numeric streams, typed-array backing is faster and more memory-efficient. For cross-Worker, SharedArrayBuffer + Atomics. The closure version hides the four state slots; only methods are exposed."

---

## 13. 60-second revision

> - **Recipe:** fixed array + `head` + `tail` + `count` + modulo wraparound.
> - **Operations:** push at head; shift at tail; both advance with `% capacity`.
> - **Overflow:** advance `tail` to overwrite oldest (default policy).
> - **Empty vs full:** `count === 0` vs `count === capacity`. `head === tail` is ambiguous.
> - **GC:** null slot on shift.
> - **Iteration:** walk from `tail` for `count` steps.
> - **O(1) per op** — much faster than `Array.shift` (O(N)).
> - **Variants:** drop-newest, auto-grow, typed-array-backed, SAB+Atomics.
> - **Family:** circular-buffer (in machine-coding), LRU cache, sliding window, log replay.

---

**Related:** [counter-ii.md](./counter-ii.md) · [private-data-counter.md](./private-data-counter.md) · [`10-machine-coding-patterns/circular-buffer.md`](../10-machine-coding-patterns/circular-buffer.md) · [`07-arrays/sliding-window-helper.md`](../07-arrays/sliding-window-helper.md)

**Concept primer:** [`concepts/closures.md`](../../concepts/closures.md)
