# Chunk an array — `chunk(arr, size)`

> **Difficulty:** Foundation   |   **Time:** ~8 min   |   **Prereqs:** [polyfill-map.md](./polyfill-map.md)
>
> **Source:** LeetCode #2677. Lodash `_.chunk`. Pagination/batching everywhere.

---

## 1. Problem statement

Split an array into chunks of fixed size. Last chunk may be shorter.

**Verification examples**

```js
chunk([1, 2, 3, 4, 5], 2);              // [[1, 2], [3, 4], [5]]
chunk([1, 2, 3, 4], 2);                 // [[1, 2], [3, 4]]
chunk([], 3);                            // []
chunk([1, 2, 3], 0);                     // [] or throw — define behavior
chunk([1, 2, 3], 5);                     // [[1, 2, 3]]
```

**Constraints**
- `size > 0` (define behavior for 0 / negative).
- Last chunk handles remainder naturally via `slice(start, start+size)`.
- O(n) total work — `slice` is O(k) per window.
- Two canonical impls: functional `Array.from` vs imperative `for`.

---

## 2. Plain-English restatement

Walk the array in fixed-size windows of `size`. Push each window's slice to output. Last chunk shorter if remainder. O(n) total.

---

## 3. Why this matters in interviews

Batches everywhere — DB batched inserts, webhook fan-out windows, worker queues. Tests `Array.from(length, mapper)` literacy + `slice` semantics + lazy generator variant.

---

## 4. Mental model

```
   Functional (one-liner):
     bucketCount = ceil(n / size)
     result = Array.from({length: bucketCount}, (_, i) => 
       arr.slice(i*size, (i+1)*size)
     )

   Imperative:
     out = []
     for i = 0; i < n; i += size:
       out.push(arr.slice(i, i + size))

   Both O(n). slice copies the window O(k); sum O(n).
   
   slice(start, end):
     - Non-mutating.
     - end > length: clips to length (no padding).
     - end omitted: defaults to length.
   
   Lazy variant (generator):
     function* chunks(arr, size) {
       for (let i = 0; i < arr.length; i += size) yield arr.slice(i, i+size);
     }
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What if `size > arr.length`?
> 2. What if `size = 0`?
> 3. Is `slice` O(1) or O(k)?

---

## 6. Brute force — walked through

```js
function chunk(arr, size) {
  if (size <= 0) return [];
  const out = [];
  let cur = [];
  for (const v of arr) {
    cur.push(v);
    if (cur.length === size) { out.push(cur); cur = []; }
  }
  if (cur.length) out.push(cur);
  return out;
}
```

Works; more verbose. Slice variant is cleaner.

---

## 7. The unlocking insight

> **Iterate by step `size`, slice each window. `slice(i, i+size)` clips naturally at end. `Array.from({length}, mapper)` for one-liner.**

Three properties:

1. **Step by `size`** — fixed window.
2. **`slice(start, end)` clips** — no special-case last chunk.
3. **`Array.from`** for functional one-liner.

---

## 8. Solution (annotated)

```js
// Imperative — most readable
function chunk(arr, size) {
  if (size <= 0) return [];                                              // step 1: guard
  const out = [];
  for (let i = 0; i < arr.length; i += size) {                          // step 2: step by size
    out.push(arr.slice(i, i + size));                                    // step 3: slice clips at end
  }
  return out;
}

// Functional one-liner
function chunkFn(arr, size) {
  if (size <= 0) return [];
  return Array.from(                                                     // step 4: pre-compute buckets
    { length: Math.ceil(arr.length / size) },
    (_, i) => arr.slice(i * size, (i + 1) * size),
  );
}

// Lazy generator
function* chunksLazy(arr, size) {
  if (size <= 0) return;
  for (let i = 0; i < arr.length; i += size) {
    yield arr.slice(i, i + size);                                        // step 5: yield window
  }
}
```

**Try it yourself**

```js
chunk([1, 2, 3, 4, 5], 2);                                    // [[1,2], [3,4], [5]]
chunk([1, 2, 3, 4], 2);                                       // [[1,2], [3,4]]
chunk([], 3);                                                  // []
chunk([1, 2, 3], 5);                                          // [[1, 2, 3]]
chunk([1, 2, 3], 0);                                          // []

// Lazy use — stop early
for (const c of chunksLazy(bigArray, 100)) {
  if (shouldStop(c)) break;
  await batchInsert(c);
}

// Balanced chunks (close to equal sizes)
function chunkBalanced(arr, count) {
  const out = Array.from({ length: count }, () => []);
  arr.forEach((v, i) => out[i % count].push(v));
  return out;
}
chunkBalanced([1, 2, 3, 4, 5], 3);                            // [[1, 4], [2, 5], [3]]

// Chunk by predicate (split on)
function splitOn(arr, pred) {
  const out = []; let cur = [];
  for (const v of arr) {
    if (pred(v)) { if (cur.length) out.push(cur); cur = []; }
    else cur.push(v);
  }
  if (cur.length) out.push(cur);
  return out;
}
```

---

## 9. Step-by-step dry run

```
chunk([1, 2, 3, 4, 5], 2):
  i=0: out.push(slice(0, 2)) = [1, 2]. out = [[1,2]].
  i=2: out.push(slice(2, 4)) = [3, 4]. out = [[1,2], [3,4]].
  i=4: out.push(slice(4, 6)) = [5]. (slice clips at length 5).
       out = [[1,2], [3,4], [5]].
  i=6 ≥ 5 → exit.
  Return [[1,2], [3,4], [5]].

chunk([1, 2, 3], 5):
  i=0: out.push(slice(0, 5)) = [1, 2, 3]. (clips).
  i=5 ≥ 3 → exit.
  Return [[1, 2, 3]].

chunk([], 3):
  i=0 ≥ 0 → loop skipped.
  Return [].

Lazy generator (BigArray, 100):
  Yields one chunk at a time; consumer can break.
  Memory: only current chunk + iter state.
  vs eager: all chunks allocated up front.
```

---

## 10. Common confusion + traps

1. **Forget `Math.ceil`** in Array.from → wrong bucket count.
2. **Handle `size = 0`** — divide by zero (Infinity), define behavior.
3. **Negative size** — return [] or throw.
4. **Slice is O(k)** — yes; total O(n) is fine.
5. **Mutate original** — chunk doesn't mutate; slice copies.
6. **Last chunk shorter** — slice(start, end) handles it; no special case.
7. **Lazy generator unused** — fine for large arrays.

---

## 11. Senior follow-ups & variants

### Variant 1 — Generator (lazy)
Yield chunks; consumer breaks early.

### Variant 2 — Balanced chunks
Round-robin distribute into N buckets.

### Variant 3 — Split on predicate
Drop separators; group consecutive matching.

### Variant 4 — Sliding (overlapping) windows
Window of size k stepping by 1.

### Variant 5 — Async batches
`for await (const c of chunksLazy(arr, n)) await process(c);`

---

## 12. How to think aloud

> "Chunk is the batching primitive: walk by step `size`, slice each window. `slice(start, end)` naturally clips at array end — no special-case for the last (possibly shorter) chunk. Two clean implementations: imperative `for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size))`, or functional `Array.from({length: Math.ceil(n/size)}, (_, i) => slice(i*size, (i+1)*size))`. Both O(n). For very large arrays, a generator yields chunks lazily — consumer can `break` to stop early; memory bounded by chunk size. Guards: `size <= 0` returns `[]` (or throw — define). Lodash matches the imperative version. Variants: balanced chunks (round-robin into N buckets), split-on-predicate (drop separators), sliding windows. Trap: forget `Math.ceil` (off-by-one bucket); divide by zero for size 0; expecting O(1) slice (it's O(k))."

---

## 13. 60-second revision

> - **Step by `size`, `slice(i, i+size)`** — slice clips at end.
> - **O(n) total** — slice is O(k); sum O(n).
> - **`Array.from({length: ceil(n/size)}, ...)`** for one-liner.
> - **Lazy generator** for huge arrays / early break.
> - **`size = 0`** → return [] (define).
> - **Variants:** balanced, split-on, sliding window.
> - **Trap:** forget ceil; div-by-zero size; mutate (don't).

---

**Related:** [polyfill-map.md](./polyfill-map.md) · [sliding-window-helper.md](./sliding-window-helper.md) · [`10-machine-coding-patterns/promise-pool.md`](../10-machine-coding-patterns/promise-pool.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
