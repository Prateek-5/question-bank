# Move zeros to end — in-place, preserve order

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [rotate-array.md](./rotate-array.md)
>
> **Source:** LeetCode #283. Two-pointer gateway problem.

---

## 1. Problem statement

In-place: move all zeros to end, preserve relative order of non-zeros. O(1) extra space.

**Verification examples**

```js
const a = [0, 1, 0, 3, 12];
moveZeros(a);
console.log(a);                          // [1, 3, 12, 0, 0]

moveZeros([]);                           // []
moveZeros([0]);                          // [0]
moveZeros([1, 2, 3]);                    // [1, 2, 3]
moveZeros([0, 0, 0]);                    // [0, 0, 0]
```

**Constraints**
- In-place mutation.
- O(1) extra space.
- O(n) time.
- Preserve order of non-zero elements (stable).
- Don't return new array (caller's ref must be modified).

---

## 2. Plain-English restatement

Two-pointer: `read` scans the array; `write` advances only when a non-zero is written. Then fill remainder with zeros. The gap between pointers = number of zeros seen.

---

## 3. Why this matters in interviews

Two-pointer gateway. Tests: (1) two-pointer write-index pattern, (2) in-place mutation vs functional, (3) off-by-one awareness, (4) swap-based alternative tradeoffs.

---

## 4. Mental model

```
   Two-pointer (overwrite):
     write = 0
     for read = 0 .. n-1:
       if arr[read] !== 0:
         arr[write++] = arr[read]
     while write < n:
       arr[write++] = 0
   
   Two-pointer (swap):
     write = 0
     for read = 0 .. n-1:
       if arr[read] !== 0:
         swap(arr[write], arr[read])
         write++
   
   Swap version preserves elements (good for moves that aren't to-zero).
   Overwrite is 1× writes per non-zero + final fill. Faster.

   Wrong: filter + concat:
     [...arr.filter(x => x !== 0), ...arr.filter(x => x === 0)]
     ✗ allocates O(n) — not in-place.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Difference between overwrite vs swap?
> 2. Why is `filter+concat` wrong?
> 3. Edge case: all zeros?

---

## 6. Brute force — walked through

```js
// O(n) time, O(n) memory — NOT in-place
function wrong(arr) {
  const nonZero = arr.filter(x => x !== 0);
  const zeros = arr.filter(x => x === 0);
  return [...nonZero, ...zeros];          // ✗ returns new; caller's ref unchanged
}
```

Fails constraint: in-place.

---

## 7. The unlocking insight

> **Two-pointer write-index: read scans, write advances on non-zero. Fill remainder with zeros. O(n)/O(1).**

Three properties:

1. **Two pointers** — read & write.
2. **In-place overwrite** — non-zeros to front.
3. **Trailing fill** — zeros at end.

---

## 8. Solution (annotated)

```js
function moveZeros(arr) {
  const n = arr.length;
  let write = 0;
  for (let read = 0; read < n; read++) {                                 // step 1: scan
    if (arr[read] !== 0) {
      arr[write++] = arr[read];                                          // step 2: write non-zero
    }
  }
  while (write < n) {
    arr[write++] = 0;                                                    // step 3: fill zeros
  }
}

// Swap-based alternative
function moveZerosSwap(arr) {
  let write = 0;
  for (let read = 0; read < arr.length; read++) {
    if (arr[read] !== 0) {
      [arr[write], arr[read]] = [arr[read], arr[write]];                 // step 4: swap
      write++;
    }
  }
}
```

**Try it yourself**

```js
const a1 = [0, 1, 0, 3, 12];
moveZeros(a1);
console.log(a1);                                              // [1, 3, 12, 0, 0]

const a2 = [];
moveZeros(a2);                                                // []

moveZeros([0, 0, 0]);                                         // [0, 0, 0]
moveZeros([1, 2, 3]);                                         // [1, 2, 3]
moveZeros([0]);                                               // [0]

// Generalized — move "bad" values to end
function moveToEnd(arr, isBad) {
  let w = 0;
  for (let r = 0; r < arr.length; r++) {
    if (!isBad(arr[r])) arr[w++] = arr[r];
  }
  // Caller fills tail or remembers cut point at w.
  return w;  // first "bad" index after compaction
}

// Sparse arrays (holes)
moveZeros([1, , 3]);                                          // edge — `,` reads as undefined !== 0.
                                                              // depends on spec — usually treat hole = falsy not zero.
```

---

## 9. Step-by-step dry run

```
moveZeros([0, 1, 0, 3, 12]):
  n=5. write=0.
  
  read=0: arr[0]=0 → skip.
  read=1: arr[1]=1, not 0 → arr[0]=1 → arr=[1,1,0,3,12]. write=1.
  read=2: arr[2]=0 → skip.
  read=3: arr[3]=3 → arr[1]=3 → arr=[1,3,0,3,12]. write=2.
  read=4: arr[4]=12 → arr[2]=12 → arr=[1,3,12,3,12]. write=3.
  
  Fill loop: write=3 < 5:
    arr[3]=0 → arr=[1,3,12,0,12]. write=4.
    arr[4]=0 → arr=[1,3,12,0,0]. write=5.
  
  Done.

moveZeros([0, 0, 0]):
  write=0.
  read=0,1,2: all zero → skip.
  Fill: write=0 < 3 → arr[0]=0, arr[1]=0, arr[2]=0. write=3.
  No-op effectively.

moveZeros([1, 2, 3]):
  write tracks read exactly: 1,2,3. write=3.
  Fill: write=3, no run.
```

---

## 10. Common confusion + traps

1. **`filter+concat`** — not in-place; allocates.
2. **`while (w <= n)`** — off-by-one; writes past end.
3. **Mutate vs return** — must mutate caller's ref.
4. **Swap version** — 2× writes per non-zero on average; slower.
5. **Sparse arrays** — hole !== 0; spec must define.
6. **All zeros** — write stays 0; fill rewrites zeros. Correct, no special-case.
7. **Stability** — order of non-zeros preserved naturally.

---

## 11. Senior follow-ups & variants

### Variant 1 — Generalize: move predicate-matching to end
Compact non-matching; fill matching at tail.

### Variant 2 — Move zeros to FRONT
Mirror: scan reverse; write decreasing.

### Variant 3 — Remove duplicates (LeetCode #26)
Same two-pointer; condition is "different from prev write".

### Variant 4 — Sort colors (LeetCode #75)
Dutch national flag — three pointers for 3 values.

### Variant 5 — Stable partition
Partition with predicate, preserving order — same algorithm.

---

## 12. How to think aloud

> "Move-zeros tests the two-pointer write-index pattern. Two pointers: `read` scans the array; `write` advances only when we copy a non-zero. After the scan, `write` is the count of non-zeros. Fill `[write..n-1]` with zeros. O(n) time, O(1) space, stable order. Wrong approach: `arr.filter(x=>x!==0).concat(arr.filter(x=>x===0))` — allocates O(n); not in-place; returns new (caller's ref unchanged). Swap variant: swap arr[write] with arr[read] when non-zero — preserves the displaced element (irrelevant when overwriting with zeros). Overwrite faster (1 write per non-zero + tail fill). Edges: empty array, all zeros, no zeros — all naturally handled. Sparse arrays: holes read as undefined !== 0, so they'd be 'kept' as undefined; spec it. Generalizes to: 'move predicate-matching to end' (variant), remove duplicates, Dutch flag sort. Trap: filter+concat (not in-place); off-by-one in fill (`<= n` writes past end); expecting return value vs mutation."

---

## 13. 60-second revision

> - **Two-pointer write-index.**
> - **Read scans; write advances on non-zero.**
> - **Tail fill** with zeros after scan.
> - **O(n)/O(1) in-place stable.**
> - **`filter+concat` allocates** — not in-place.
> - **Swap variant** — 2× writes; overwrite faster.
> - **Generalizes** to predicate-matching, dedup, Dutch flag.
> - **Trap:** off-by-one fill; return vs mutate; holes !== 0.

---

**Related:** [rotate-array.md](./rotate-array.md) · [find-runs.md](./find-runs.md) · [array-dedup.md](./array-dedup.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
