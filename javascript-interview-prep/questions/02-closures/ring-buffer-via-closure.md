# Ring Buffer via Closure

## Source / Origin
- Classic data structure; common in metrics, logging buffers, audio streaming.
- Asked at: Razorpay, Atlassian, Cloudflare.
- Concept reference: `concepts/closures.md`, sibling `10-machine-coding-patterns/circular-buffer.md`.

## Why this question matters in interviews
Fixed-size FIFO with O(1) push and pop. The closure variant tests whether you can encapsulate `{ buffer, head, tail, size }` privately and expose only methods. Senior bar: you handle overflow (overwrite oldest), wraparound math (modulo), and full/empty distinction (the +1 trick or explicit count).

## Concepts involved

### Syntax to lock in
```js
function createRingBuffer(capacity) {
  const buf = new Array(capacity);
  let head = 0;       // next write
  let tail = 0;       // next read
  let count = 0;

  return {
    push(v) {
      buf[head] = v;
      head = (head + 1) % capacity;
      if (count === capacity) tail = (tail + 1) % capacity;   // overwrite oldest
      else count++;
    },
    shift() {
      if (count === 0) return undefined;
      const v = buf[tail];
      buf[tail] = undefined;     // help GC
      tail = (tail + 1) % capacity;
      count--;
      return v;
    },
    peek() { return count === 0 ? undefined : buf[tail]; },
    get length() { return count; },
    get capacity() { return capacity; },
    toArray() {
      const out = [];
      for (let i = 0, t = tail; i < count; i++, t = (t + 1) % capacity) out.push(buf[t]);
      return out;
    },
  };
}
```

### Edge cases / traps
1. **Full vs empty.** With head==tail, you can't tell full from empty; either keep a `count`, or reserve one slot (`capacity-1` usable).
2. **Wraparound.** `(idx + 1) % capacity` — easy to forget the modulo.
3. **Overflow policy** — overwrite oldest (most common), reject new, or grow. Pick one explicitly.
4. **GC** — null out the slot on shift, else removed objects stay reachable.
5. **Iteration order** — must walk from `tail`, not from index 0.
6. **Capacity 0** — disallow or treat as no-op.
7. **Concurrent access** — Node single-thread fine; SharedArrayBuffer + Atomics for cross-worker.

## Mental Model

A **fixed circular track** with two pointers chasing each other:

```
   capacity=5
   buf:  [ a  b  c  _  _ ]
                  ^      ^
                 head   (head=3, tail=0, count=3)
   tail
   
   push(d) → buf[3]=d; head=4; count=4
   buf:  [ a  b  c  d  _ ]
                       ^
                      head, tail=0

   push(e) → buf[4]=e; head=0; count=5
   buf:  [ a  b  c  d  e ]
            ^
           head, tail=0, count=5 (FULL)

   push(f) → buf[0]=f; head=1; FULL → tail=(0+1)%5=1; count stays 5
   buf:  [ f  b  c  d  e ]
            ^   ^
            head tail
   shift() → returns b; tail=2; count=4
```

## Why interviewers care

- **Closure encapsulation** — internal state hidden.
- **Modular arithmetic** — wraparound is a classic gotcha.
- **Policy thinking** — overflow behavior is a design choice.

## Common confusion

- **"`head === tail` means empty."** Could mean full. Use explicit `count`.
- **"Use Array.shift/push."** O(n) shift (array reindex) defeats the point of a ring buffer.
- **"Just keep an Array, never mind."** Fine for small N, but breaks bound guarantees.

## Brute force

```js
class Naive {
  buf = [];
  capacity;
  push(v) { this.buf.push(v); if (this.buf.length > this.capacity) this.buf.shift(); }  // O(n)
}
```

`Array.shift()` is O(n). Ring buffer is O(1).

## Optimal approach

Fixed-size array, head/tail pointers, count tracker, modulo wraparound. Closure hides all of it.

## Solution

See "Syntax to lock in" above. Production usage:

```js
const recentLogs = createRingBuffer(1000);
function log(msg) {
  recentLogs.push({ ts: Date.now(), msg });
}
// On crash, dump recentLogs.toArray() for context.

// Streaming audio sample buffer
const samples = createRingBuffer(48000);    // 1 second @ 48kHz
function onAudioSample(s) { samples.push(s); }
function getLatest() { return samples.toArray(); }
```

## Dry run

`capacity=3`, push a, b, c, d:

```
init   head=0 tail=0 count=0  buf=[_,_,_]
push a head=1 tail=0 count=1  buf=[a,_,_]
push b head=2 tail=0 count=2  buf=[a,b,_]
push c head=0 tail=0 count=3  buf=[a,b,c]   FULL
push d buf[0]=d; head=1; was full → tail=1; count stays 3
       buf=[d,b,c]; tail=1 (next read is b)
shift()→ b; buf[1]=undefined; tail=2; count=2; buf=[d,_,c]
shift()→ c; tail=0; count=1; buf=[d,_,_]
shift()→ d; tail=1; count=0
shift()→ undefined (empty)
```

## How to think aloud

> "Closure encloses `buf`, `head`, `tail`, `count`. Push writes at head, advances head modulo capacity; if full, also advances tail (overwrite oldest). Shift reads at tail, advances tail. Explicit count distinguishes full vs empty without the 'leave one slot empty' trick. Null out slot on shift for GC. iteration walks from tail for `count` steps."

## Important takeaways

- **head/tail/count + modulo wraparound** = the recipe.
- **Overflow policy explicit** — overwrite oldest is the default.
- **Null on shift** for GC.
- **Iteration starts at tail.**
- **Closure hides all internal state** — only methods exposed.

## Variants

- **Drop-newest** on overflow (instead of drop-oldest).
- **Resizable** — grow when full (defeats the "fixed memory" guarantee).
- **Typed-array backed** — `Float32Array` for numeric streams (audio, metrics).
- **Generic over types** — usual in TS.
- **Lock-free SAB** — `Atomics`-based for cross-worker.

## Revision notes

```
createRingBuffer(cap):
  closure: buf=Array(cap), head=0, tail=0, count=0
  push(v): buf[head]=v; head=(head+1)%cap; if count==cap: tail=(tail+1)%cap else count++
  shift(): if !count: undefined; v=buf[tail]; buf[tail]=undef; tail=(tail+1)%cap; count--; return v
  
TRAPS:
  - head==tail ambiguous; use count
  - Array.shift is O(n); use ring
  - GC: null slots on shift
  - iterate from tail
overflow policy: overwrite oldest (default) | reject new | grow
```
