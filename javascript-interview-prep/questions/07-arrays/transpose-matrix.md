# Transpose matrix

> **Difficulty:** Foundation   |   **Time:** ~8 min   |   **Prereqs:** [zip-unzip.md](./zip-unzip.md)
>
> **Source:** LeetCode #867. Universal.

---

## 1. Problem statement

Swap rows and columns of a 2D array. `m[r][c]` becomes `m'[c][r]`.

**Verification examples**

```js
transpose([[1, 2, 3], [4, 5, 6]]);           // [[1, 4], [2, 5], [3, 6]]
transpose([[1, 2], [3, 4]]);                 // [[1, 3], [2, 4]]
transpose([]);                                // []
transpose([[1]]);                             // [[1]]
```

**Constraints**
- Out-of-place version handles rectangular.
- In-place version requires square matrix.
- O(rows × cols) time.

---

## 2. Plain-English restatement

`out[c][r] = m[r][c]`. Out-of-place: allocate cols×rows, copy. In-place: swap upper triangle with lower (square only).

---

## 3. Why this matters in interviews

Quick test of array indexing, pre-allocation, in-place pattern. Square in-place is concise (10 lines).

---

## 4. Mental model

```
   Out-of-place (any shape):
     rows = m.length; cols = m[0].length
     out = Array.from({length: cols}, () => new Array(rows))
     for r in 0..rows-1:
       for c in 0..cols-1:
         out[c][r] = m[r][c]
   
   One-liner:
     m[0].map((_, c) => m.map(row => row[c]))
   
   In-place (square only):
     n = m.length
     for i in 0..n-1:
       for j in i+1..n-1:           ← upper triangle
         swap m[i][j], m[j][i]
   
   zip(...m) == transpose(m).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is in-place only for square?
> 2. What's the relation between zip and transpose?
> 3. Output dimensions for 2×3 input?

---

## 6. Brute force — walked through

```js
function transpose(m) {
  const out = [];
  for (let c = 0; c < m[0].length; c++) {
    out.push([]);
    for (let r = 0; r < m.length; r++) out[c].push(m[r][c]);
  }
  return out;
}
```

Works. `push` is fine — pre-allocate avoids minor reallocation.

---

## 7. The unlocking insight

> **`out[c][r] = m[r][c]`. Pre-allocate cols×rows. For square in-place, swap upper-triangle entries `(i,j)` with `(j,i)`.**

Three properties:

1. **Index swap** — `[r][c]` → `[c][r]`.
2. **Pre-allocate** for efficiency.
3. **Square in-place** — upper triangle only.

---

## 8. Solution (annotated)

```js
function transpose(m) {
  if (m.length === 0) return [];                                          // step 1: empty
  const rows = m.length;
  const cols = m[0].length;
  const out = Array.from({ length: cols }, () => new Array(rows));        // step 2: pre-allocate cols×rows
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      out[c][r] = m[r][c];                                                 // step 3: swap indices
    }
  }
  return out;
}

// One-liner (functional)
const transposeFn = (m) =>
  m[0]?.map((_, c) => m.map((row) => row[c])) ?? [];

// In-place (square only)
function transposeInPlace(m) {
  const n = m.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {                                     // step 4: upper triangle
      [m[i][j], m[j][i]] = [m[j][i], m[i][j]];                            // step 5: swap
    }
  }
}
```

**Try it yourself**

```js
transpose([[1, 2, 3], [4, 5, 6]]);                            // [[1,4], [2,5], [3,6]]
transpose([[1]]);                                              // [[1]]
transpose([]);                                                 // []

// Square in-place
const sq = [[1, 2, 3], [4, 5, 6], [7, 8, 9]];
transposeInPlace(sq);
console.log(sq);                                              // [[1,4,7], [2,5,8], [3,6,9]]

// Rotate 90° = transpose then reverse rows
function rotate90(m) {
  transposeInPlace(m);
  for (const row of m) row.reverse();
}

// zip = transpose
const zip = (...arrays) => transpose(arrays);
zip([1, 2], ['a', 'b']);                                      // [[1, 'a'], [2, 'b']]
```

---

## 9. Step-by-step dry run

```
transpose([[1,2,3],[4,5,6]]):
  rows=2, cols=3.
  out = Array.from({length: 3}, () => new Array(2)) → [[_,_],[_,_],[_,_]].
  
  r=0 c=0: out[0][0] = m[0][0] = 1.
  r=0 c=1: out[1][0] = m[0][1] = 2.
  r=0 c=2: out[2][0] = m[0][2] = 3.
  r=1 c=0: out[0][1] = m[1][0] = 4.
  r=1 c=1: out[1][1] = m[1][1] = 5.
  r=1 c=2: out[2][1] = m[1][2] = 6.
  
  Return [[1,4], [2,5], [3,6]].

transposeInPlace([[1,2,3],[4,5,6],[7,8,9]]):
  n=3.
  i=0:
    j=1: swap m[0][1]=2 and m[1][0]=4.
    j=2: swap m[0][2]=3 and m[2][0]=7.
  i=1:
    j=2: swap m[1][2]=6 and m[2][1]=8.
  Result: [[1,4,7],[2,5,8],[3,6,9]]. ✓

Why upper triangle only?
  If we swap both (i,j) AND (j,i) when i<j, then again when i>j, we undo.
  Iterate i<j only — each pair swapped once.
```

---

## 10. Common confusion + traps

1. **In-place on rectangular** — dimensions change; can't reuse storage.
2. **Forget pre-allocate** — push works but minor reallocation overhead.
3. **Jagged rows** — assume rectangular; otherwise need max-cols + undefined padding.
4. **Empty matrix** — return `[]`.
5. **Single row** — `[[1,2,3]]` → `[[1],[2],[3]]`.
6. **Swap whole row** — wrong; transpose is per-element.
7. **`m[0].map`** when `m[0]` undefined — handle empty.

---

## 11. Senior follow-ups & variants

### Variant 1 — Rotate 90°
Transpose + reverse rows (or reverse rows + transpose).

### Variant 2 — `zip(...arrays)`
Equivalent to `transpose(arrays)`.

### Variant 3 — Sparse / jagged
Pad with undefined or use Map<row, Map<col, val>>.

### Variant 4 — Big matrix
Use typed arrays (Float32Array etc.) for memory locality.

### Variant 5 — Cache-friendly transpose
Block-based for very large matrices (CPU cache locality).

---

## 12. How to think aloud

> "Transpose: `out[c][r] = m[r][c]`. Out-of-place handles any shape: pre-allocate cols×rows via `Array.from({length: cols}, () => new Array(rows))`, double loop, copy. One-liner: `m[0].map((_, c) => m.map(row => row[c]))`. In-place requires square (output dimensions same as input); iterate upper triangle only — `for i in 0..n-1, for j in i+1..n-1: swap m[i][j], m[j][i]` — each pair swapped exactly once. `zip(...arrays) === transpose(arrays)`. Rotate 90° = transpose + reverse each row. Variants: typed arrays for memory (Float32Array etc.); block-transpose for cache locality on huge matrices. Trap: in-place on rectangular (impossible); jagged rows (assume rectangular or pad); whole-row swap (wrong direction)."

---

## 13. 60-second revision

> - **`out[c][r] = m[r][c]`** — index swap.
> - **Pre-allocate** cols × rows.
> - **In-place: square only**, upper triangle.
> - **Each pair swapped once** — iterate `j > i`.
> - **One-liner:** `m[0].map((_, c) => m.map(r => r[c]))`.
> - **`zip(...m) === transpose(m)`**.
> - **Rotate 90° = transpose + reverse rows.**
> - **Trap:** in-place non-square; jagged rows; whole-row swap.

---

**Related:** [zip-unzip.md](./zip-unzip.md) · [rotate-array.md](./rotate-array.md) · [polyfill-map.md](./polyfill-map.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
