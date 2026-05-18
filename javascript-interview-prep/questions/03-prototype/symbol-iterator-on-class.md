# Symbol.iterator on a Custom Class

## Source / Origin
- ES2015 iteration protocol.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/prototype.md`, sibling `06-streams/custom-iterator.md`.

## Why this question matters in interviews
"Make this class iterable so it works in `for...of`." That's `Symbol.iterator`. Senior bar: you know the protocol (`return { next() { return { value, done } } }`), distinguish iterable from iterator, support multiple-pass iteration via separate iterator instances, and know about `Symbol.asyncIterator` for `for await ... of`.

## Concepts involved

### Syntax to lock in
```js
class Range {
  constructor(start, end, step = 1) { this.start = start; this.end = end; this.step = step; }
  [Symbol.iterator]() {
    let i = this.start;
    const { end, step } = this;
    return {
      next() {
        if (i < end) return { value: i, done: false }, i += step, { value: i - step, done: false };
        return { value: undefined, done: true };
      }
    };
  }
}
for (const n of new Range(1, 5)) console.log(n);   // 1 2 3 4
```

### Edge cases / traps
1. **Iterable vs iterator.** Iterable: has `[Symbol.iterator]()` returning an iterator. Iterator: has `next()`. The same object can be both (returns `this` from `[Symbol.iterator]`).
2. **Multiple passes.** `for (const n of r) {} for (const n of r) {}` should work twice. Each `[Symbol.iterator]()` call must return a *fresh* iterator. If you reuse one, second pass is empty.
3. **Generator shorthand.** `*[Symbol.iterator]() { yield* ... }` is cleaner than manual `next()`.
4. **`return()` and `throw()`.** Iterator protocol includes optional `return(value)` (early exit cleanup) and `throw(err)`. `for...of`'s `break` calls `return()`.
5. **Infinite iterators.** Fine — `for...of` with a `break`.
6. **`Symbol.asyncIterator`** — async version; required for `for await ... of`.
7. **Spread/destructure** — `[...iterable]`, `[a, b, ...rest] = iterable`. Same protocol.
8. **`Array.from` accepts iterables** — `Array.from(new Range(1, 5))`.

## Mental Model

```
   iterable                    iterator
   ┌────────────┐              ┌───────────────────────┐
   │ [SI]: fn   │── calls ──▶  │ next: ()=>{v,d}       │
   │            │              │ return?: ()=>{v,d}    │
   │            │              │ throw?: ()=>{v,d}     │
   └────────────┘              └───────────────────────┘
   each call returns FRESH iterator
   for...of pulls next() until done=true
```

## Why interviewers care

- **Spec literacy** — protocol-driven design.
- **Generator awareness** — they're the easy way.
- **Iterable vs iterator distinction** — common confusion.

## Common confusion

- **"`[Symbol.iterator]` returns the items array."** No — it returns an iterator object with `next()`.
- **"Iterator can be reused."** Only if your `[Symbol.iterator]` returns a fresh iterator each call.
- **"Generators are sync only."** `async function*` is async generator.
- **"`for...of` works on plain objects."** No — only on iterables (Array, Map, Set, String, custom).

## Brute force

`Array.from(thing)` only works if `thing` is iterable. Otherwise no `for...of`.

## Optimal approach

Implement `[Symbol.iterator]` via a generator function. Cleaner and supports `return()` automatically via `try/finally`.

## Solution

```js
class Range {
  constructor(start, end, step = 1) { this.start = start; this.end = end; this.step = step; }
  *[Symbol.iterator]() {
    for (let i = this.start; i < this.end; i += this.step) yield i;
  }
}

const r = new Range(1, 6);
[...r];                      // [1,2,3,4,5]
Array.from(r, x => x * x);   // [1,4,9,16,25]
for (const n of r) console.log(n);
for (const n of r) console.log(n);   // works again (fresh iterator)

// Async iterable
class FetchPages {
  constructor(url) { this.url = url; }
  async *[Symbol.asyncIterator]() {
    let cursor = null;
    while (true) {
      const res = await fetch(`${this.url}?cursor=${cursor ?? ''}`).then(r => r.json());
      for (const it of res.items) yield it;
      if (!res.next) return;
      cursor = res.next;
    }
  }
}
for await (const item of new FetchPages('/api')) console.log(item);

// Custom iteration with cleanup
class FileReader {
  *[Symbol.iterator]() {
    const handle = openFile(this.path);
    try {
      let line;
      while ((line = handle.readLine()) !== null) yield line;
    } finally {
      handle.close();
    }
  }
}
for (const line of new FileReader('/log')) {
  if (line.includes('ERROR')) break;        // triggers iterator.return() → runs finally
}
```

## Dry run

```js
class Range { *[Symbol.iterator]() { yield 1; yield 2; yield 3; } }
const r = new Range();
const iter = r[Symbol.iterator]();
iter.next();   // { value: 1, done: false }
iter.next();   // { value: 2, done: false }
iter.next();   // { value: 3, done: false }
iter.next();   // { value: undefined, done: true }

for (const n of r) console.log(n);   // calls [Symbol.iterator]() AGAIN → fresh iterator
```

## How to think aloud

> "I'd implement `[Symbol.iterator]` as a generator. Each call returns a fresh iterator — that's how `for...of` works twice. Generators give me `return()` cleanup for free via try/finally; `break` in `for...of` calls `return()` and runs my finally. For paginated data I'd use `[Symbol.asyncIterator]` with `for await...of` — same protocol, async."

## Important takeaways

- **`[Symbol.iterator]()` returns iterator** with `next() → {value, done}`.
- **Generator shorthand** (`*[Symbol.iterator]`) handles return/throw cleanup.
- **Fresh iterator per call** for multi-pass iteration.
- **`[Symbol.asyncIterator]()`** for `for await ... of`.
- **`break` calls `iterator.return()`** — cleanup happens.

## Variants

- **Iterable + iterator combined**: `[Symbol.iterator]() { return this }`; class itself has `next()`. Common for stream-like objects.
- **Lazy infinite iterable**: `function* naturals() { let n = 0; while (true) yield n++; }`.
- **Iterator helpers** (ES2024): `Iterator.prototype.map`, `.filter`, `.take` etc.
- **`.entries()`, `.keys()`, `.values()`** — convention from Array/Map/Set.

## Revision notes

```
class C {
  *[Symbol.iterator]() { yield ...; }
}
for (const v of new C()) ...

protocol:
  iterator: { next: () => { value, done }, return?, throw? }
  iterable: { [Symbol.iterator]: () => iterator }

generator simplifies:
  *[Symbol.iterator]() { yield ...; }   ← gives next/return/throw for free
  try { yield } finally { cleanup }     ← break triggers finally

async: [Symbol.asyncIterator] + async function* + for await...of

each [Symbol.iterator]() call should produce FRESH iterator (multi-pass)
```
