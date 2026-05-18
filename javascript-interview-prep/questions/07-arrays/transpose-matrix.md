# Transpose Matrix

## Source / Origin
- LeetCode 867; classic array problem.
- Asked at: every interview that touches matrices.
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
Quick, fits in 10 lines, tests array indexing and zero-allocation patterns. Senior bar: you produce the standard form, the `Array.from` one-liner, and discuss in-place for square matrices.

## Concepts involved

```js
// Out-of-place — works for non-square
function transpose(m) {
  const rows = m.length, cols = m[0].length;
  const out = Array.from({ length: cols }, () => new Array(rows));
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++)
      out[c][r] = m[r][c];
  return out;
}

// One-liner
const t = m[0].map((_, c) => m.map(row => row[c]));

// In-place (square only)
function transposeInPlace(m) {
  const n = m.length;
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++)
      [m[i][j], m[j][i]] = [m[j][i], m[i][j]];
}
```

### Edge cases / traps
1. **Rectangular vs square.** In-place only works for square; output dimensions otherwise.
2. **Empty matrix** — return `[]`.
3. **Jagged rows** — assume rectangular; otherwise need max-cols + undefined padding.
4. **Big matrices** — pre-allocate output via `new Array(rows)` per column to avoid push.
5. **Element kinds** (V8) — Array.from with map fn keeps PACKED.
6. **Typed-array variant** — for numeric matrices, single Float64Array indexed `r*cols+c` is much faster.

## Mental Model

```
   m:    [a b c]              t:     [a d]
         [d e f]                     [b e]
                                     [c f]

   t[c][r] = m[r][c]
```

## Solution

```js
// Standard
function transpose(m) {
  const rows = m.length;
  if (!rows) return [];
  const cols = m[0].length;
  const out = Array.from({ length: cols }, () => new Array(rows));
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) out[c][r] = m[r][c];
  return out;
}

// Functional one-liner (slower for big matrices due to allocation overhead)
const transposeFn = m => m[0].map((_, c) => m.map(row => row[c]));

// In-place (square)
function transposeSquare(m) {
  const n = m.length;
  for (let i = 0; i < n; i++)
    for (let j = i + 1; j < n; j++)
      [m[i][j], m[j][i]] = [m[j][i], m[i][j]];
}

// Numeric matrix with TypedArray (faster, cache-friendly)
function transposeFloat(m, rows, cols) {
  const out = new Float64Array(rows * cols);
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++)
      out[c * rows + r] = m[r * cols + c];
  return out;
}

// Rotate 90° clockwise = transpose + reverse each row
function rotate90(m) {
  transposeSquare(m);
  m.forEach(row => row.reverse());
}
```

## Dry run

```js
m = [[1,2,3], [4,5,6]]
rows=2, cols=3
out = Array(3) of Array(2)

r=0, c=0: out[0][0] = 1
r=0, c=1: out[1][0] = 2
r=0, c=2: out[2][0] = 3
r=1, c=0: out[0][1] = 4
r=1, c=1: out[1][1] = 5
r=1, c=2: out[2][1] = 6

out = [[1,4], [2,5], [3,6]]
```

## How to think aloud

> "Transpose: out[c][r] = m[r][c]. For rectangular, allocate a fresh output. For square in-place, swap m[i][j] with m[j][i] for j > i. For numeric, a typed array indexed `r*cols+c` is much faster — better cache locality and no V8 element-kind issues. Rotation 90° is transpose followed by reverse each row."

## Important takeaways

- **`out[c][r] = m[r][c]`.**
- **In-place only for square**; swap upper triangle with lower.
- **`Array.from({length:cols}, () => new Array(rows))`** for pre-allocation.
- **Typed array** for numeric perf.
- **Rotate 90° = transpose + row-reverse.**

## Variants

- **Sparse matrix** — store (r, c, v) triples; transpose by swapping r↔c.
- **Block transpose** — for very large matrices, cache-friendly tiling.
- **GPU transpose** — WebGL/WebGPU compute shader.

## Revision notes

```
out[c][r] = m[r][c]

out-of-place:
  Array.from({length:cols}, () => new Array(rows))
  for r,c: out[c][r] = m[r][c]

in-place (square only):
  for i in 0..n: for j in i+1..n: swap m[i][j], m[j][i]

rotate 90° CW:
  transpose; then reverse each row

numeric: use Float64Array(rows*cols), index r*cols+c
```
