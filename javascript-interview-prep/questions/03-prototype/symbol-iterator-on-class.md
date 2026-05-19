# `Symbol.iterator` on a custom class

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [`concepts/prototype.md`](../../concepts/prototype.md), [getter-setter-via-prototype.md](./getter-setter-via-prototype.md)
>
> **Source:** ES2015 iteration protocol. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Make a class iterable so it works in `for...of`, spread, destructuring.

**Verification examples**

```js
class Range {
  constructor(start, end, step = 1) { this.start = start; this.end = end; this.step = step; }
  [Symbol.iterator]() {
    let i = this.start;
    const { end, step } = this;
    return {
      next() {
        if (i < end) {
          const v = i;
          i += step;
          return { value: v, done: false };
        }
        return { value: undefined, done: true };
      },
    };
  }
}

for (const n of new Range(1, 5)) console.log(n);                         // 1, 2, 3, 4
[...new Range(1, 4)];                                                    // [1, 2, 3]
const [a, b] = new Range(10, 13);                                        // a=10, b=11
```

**Constraints**
- Iteration protocol: `[Symbol.iterator]()` returns an iterator.
- Iterator: `{ next() { return {value, done} } }`.
- Multiple iterations need fresh iterator each time.
- Generators (`function*`) are the cleanest implementation.

---

## 2. Plain-English restatement

The iteration protocol is two parts. **Iterable**: has a `[Symbol.iterator]()` method that returns an iterator. **Iterator**: has a `next()` method returning `{value, done}`. `for...of`, spread, and destructuring all call `[Symbol.iterator]()` to get a fresh iterator.

---

## 3. Why this matters in interviews

Tests well-known symbols + iteration protocol + understanding of language hooks.

---

## 4. Mental model

```
   Iterable protocol:
   - obj[Symbol.iterator]() → returns iterator
   
   Iterator protocol:
   - iterator.next() → returns { value, done }
   - done: true → end of sequence
   
   Iteration consumers:
   - for...of      → repeatedly call next() until done
   - spread [...x] → same
   - destructuring → same
   - Array.from(x) → same
   
   Cleanest: use generator
     [Symbol.iterator]() {
       const self = this;
       return (function*() {
         for (let i = self.start; i < self.end; i += self.step) yield i;
       })();
     }
   
   Or method shorthand:
     *[Symbol.iterator]() {
       for (let i = this.start; i < this.end; i += this.step) yield i;
     }
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `[Symbol.iterator]()` return — the iterator or the value?
> 2. Can you iterate a Range twice independently?
> 3. What's the simplest implementation using `function*`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `next()` directly on class
That's an iterator, not iterable. `for...of` needs the iterable protocol.

### Wrong attempt 2: single iterator stored on class
Second `for...of` finds done; can't restart.

### Wrong attempt 3: return primitive from next()
Must return `{value, done}` object.

---

## 7. The unlocking insight

> **`[Symbol.iterator]()` returns a fresh iterator. Iterator has `next()` returning `{value, done}`. Generators (`function*`) implement both protocols automatically — cleanest pattern.**

Three properties:

1. **Iterable vs iterator** — two protocols.
2. **Fresh iterator per call** — supports multi-pass.
3. **Generator method** — `*[Symbol.iterator]()` is the cleanest.

---

## 8. Solution (annotated)

```js
class Range {
  constructor(start, end, step = 1) {
    this.start = start; this.end = end; this.step = step;
  }

  *[Symbol.iterator]() {                                                  // step 1: generator method
    for (let i = this.start; i < this.end; i += this.step) {
      yield i;
    }
  }
}

// Use
for (const n of new Range(1, 5)) console.log(n);                         // 1, 2, 3, 4
[...new Range(1, 4)];                                                    // [1, 2, 3]
const [a, b, c] = new Range(10, 14);                                     // 10, 11, 12

// Multi-pass works (fresh iterator each call)
const r = new Range(1, 4);
[...r];                                                                   // [1, 2, 3]
[...r];                                                                   // [1, 2, 3] (fresh)
```

**Try it yourself — manual version:**

```js
class ManualRange {
  constructor(start, end, step = 1) {
    this.start = start; this.end = end; this.step = step;
  }
  [Symbol.iterator]() {                                                   // step 2: explicit iterator
    let i = this.start;
    const { end, step } = this;
    return {
      next() {
        if (i < end) {
          const v = i;
          i += step;
          return { value: v, done: false };
        }
        return { value: undefined, done: true };
      },
      // Optional: [Symbol.iterator]() { return this; }  — for iterator+iterable
    };
  }
}

// Async iteration with Symbol.asyncIterator
class AsyncRange {
  constructor(start, end) { this.start = start; this.end = end; }
  async *[Symbol.asyncIterator]() {
    for (let i = this.start; i < this.end; i++) {
      await new Promise((r) => setTimeout(r, 100));
      yield i;
    }
  }
}
// for await (const n of new AsyncRange(0, 3)) console.log(n);
```

---

## 9. Step-by-step dry run

```
for (const n of new Range(1, 4)) console.log(n):

1. const r = new Range(1, 4);
2. const iter = r[Symbol.iterator]():
     generator function called → returns iterator object.
3. loop:
     iter.next() → generator runs:
       yield 1 → { value: 1, done: false }
     log 1.
   iter.next() → resumes after yield:
       i = 2, yield 2 → { value: 2, done: false }
     log 2.
   iter.next() → i = 3, yield 3 → { value: 3, done: false }
     log 3.
   iter.next() → i = 4, i < 4? no, fall through → { value: undefined, done: true }
     loop exits.

Multi-pass:
  const r = new Range(1, 4);
  for (const x of r) {}   ← calls r[Symbol.iterator]() → fresh iterator
  for (const x of r) {}   ← calls again → ANOTHER fresh iterator
  Works because [Symbol.iterator] is a method that creates a new iterator each call.
```

---

## 10. Common confusion + traps

1. **Iterable = iterator** — separate protocols.
2. **`next()` directly on class** — that's an iterator, not iterable.
3. **Single iterator stored** — can't multi-pass.
4. **Return primitive from next()** — must be `{value, done}`.
5. **Generator inside arrow** — arrows can't be generators.
6. **`Symbol.asyncIterator` for async** — separate from `Symbol.iterator`.
7. **`return()` for early termination** — iterator can implement for cleanup.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async iterable
`*async [Symbol.asyncIterator]()` + `for await...of`.

### Variant 2 — Iterator + iterable
Iterator's own `[Symbol.iterator]() { return this; }` makes it both.

### Variant 3 — Early termination
`iter.return?.()` for cleanup when `for...of` breaks.

### Variant 4 — `Array.from(iterable, mapFn)`
Built on iteration protocol; spreads + maps.

### Variant 5 — Infinite iterables
Generator can yield forever; consumer breaks.

---

## 12. How to think aloud

> "Two protocols. Iterable: object with `[Symbol.iterator]()` method that returns an iterator. Iterator: object with `next()` method returning `{value, done}`. `for...of`, spread, destructuring all call `[Symbol.iterator]()` to get a fresh iterator. Use a generator method (`*[Symbol.iterator]()`) for the cleanest implementation — generators auto-implement both protocols and handle pause/resume. For async iteration use `*async [Symbol.asyncIterator]()` + `for await...of`. Multi-pass works automatically because each `for...of` calls `[Symbol.iterator]()` again, creating a fresh iterator. Trap: confusing iterable and iterator; storing single iterator on instance (breaks multi-pass); returning primitive from next() (must be object)."

---

## 13. 60-second revision

> - **Iterable:** `obj[Symbol.iterator]()` returns iterator.
> - **Iterator:** `iter.next()` returns `{value, done}`.
> - **Generator method** `*[Symbol.iterator]()` = cleanest.
> - **Multi-pass:** each `for...of` calls `[Symbol.iterator]()` fresh.
> - **Async:** `Symbol.asyncIterator` + `for await...of`.
> - **Early term:** `iter.return?.()` for cleanup.
> - **`Array.from(iterable, mapFn)`** uses protocol.
> - **Trap:** iterable vs iterator; single stored iterator; primitive from next.

---

**Related:** [`06-streams/custom-iterator.md`](../06-streams/custom-iterator.md) · [`04-promises/async-generator-producer.md`](../04-promises/async-generator-producer.md) · [tostring-symbol-tag-override.md](./tostring-symbol-tag-override.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md)
