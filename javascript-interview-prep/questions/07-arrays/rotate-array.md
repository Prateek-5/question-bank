# Rotate Array (by K positions)

## Source / Origin
- LeetCode 189; standard array manipulation.
- Asked at: every interview at some point.
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
"Rotate this array right by K." Trivial with extra space; classic with the in-place "reverse three times" trick. Senior bar: you produce the O(n)/O(1) solution and handle k > n via modulo.

## Concepts involved

```js
// O(n)/O(n) — easy
function rotateRight(arr, k) {
  const n = arr.length;
  k = ((k % n) + n) % n;
  return arr.slice(-k).concat(arr.slice(0, -k));
}

// O(n)/O(1) — in-place reverse trick
function rotateRightInPlace(arr, k) {
  const n = arr.length;
  k = ((k % n) + n) % n;
  reverse(arr, 0, n - 1);
  reverse(arr, 0, k - 1);
  reverse(arr, k, n - 1);
}
function reverse(arr, lo, hi) {
  while (lo < hi) { [arr[lo], arr[hi]] = [arr[hi], arr[lo]]; lo++; hi--; }
}
```

### Edge cases / traps
1. **`k > n`** — modulo: `k = k % n`.
2. **Negative `k`** — `((k % n) + n) % n` normalizes.
3. **`k = 0`** — no-op; reverse-trick still works.
4. **Empty array or n=1** — no-op.
5. **Left rotation** — equivalent to right rotation by `n-k`.
6. **Mutating vs returning** — interviewer often wants in-place.
7. **`Array.prototype.copyWithin`** is an alternative for some cases.

## Mental Model

The 3-reverse trick:

```
   arr = [1, 2, 3, 4, 5, 6, 7], k = 3
   want: [5, 6, 7, 1, 2, 3, 4]

   step 1: reverse whole       [7, 6, 5, 4, 3, 2, 1]
   step 2: reverse first k=3   [5, 6, 7, 4, 3, 2, 1]
   step 3: reverse rest        [5, 6, 7, 1, 2, 3, 4]
```

## Why interviewers care

- **In-place + O(1) extra space.**
- **Modulo handling.**
- **The "reverse 3 times" trick** is a senior-level move.

## Common confusion

- **"`splice + unshift`."** Allocates new array each step; O(n*k).
- **"`arr.slice + concat`."** Works but uses O(n) extra space.
- **"Rotate one at a time, k times."** O(n*k) — worst.
- **"Forget modulo."** `k > n` crashes or wraps unexpectedly.

## Brute force

```js
for (let i = 0; i < k; i++) arr.unshift(arr.pop());   // O(n*k); unshift is O(n)
```

## Optimal approach

3-reverse trick: O(n) time, O(1) space, in-place.

## Solution

```js
function reverse(arr, lo, hi) {
  while (lo < hi) {
    const tmp = arr[lo];
    arr[lo++] = arr[hi];
    arr[hi--] = tmp;
  }
}

function rotateRight(arr, k) {
  const n = arr.length;
  if (n < 2) return arr;
  k = ((k % n) + n) % n;
  if (k === 0) return arr;
  reverse(arr, 0, n - 1);
  reverse(arr, 0, k - 1);
  reverse(arr, k, n - 1);
  return arr;
}

function rotateLeft(arr, k) {
  return rotateRight(arr, -k);
}

// Cyclic-replacement variant (O(n)/O(1), one pass)
function rotateCyclic(arr, k) {
  const n = arr.length;
  k = ((k % n) + n) % n;
  if (k === 0) return arr;
  let count = 0;
  for (let start = 0; count < n; start++) {
    let curr = start;
    let prev = arr[start];
    do {
      const next = (curr + k) % n;
      [arr[next], prev] = [prev, arr[next]];
      curr = next;
      count++;
    } while (start !== curr);
  }
  return arr;
}
```

## Dry run

`arr=[1,2,3,4,5], k=2`:

```
n=5, k=(2 % 5 + 5) % 5 = 2

step 1: reverse 0..4    [5,4,3,2,1]
step 2: reverse 0..1    [4,5,3,2,1]
step 3: reverse 2..4    [4,5,1,2,3]
```

Result: `[4,5,1,2,3]` (right-rotate by 2 = last 2 → front).

## How to think aloud

> "Normalize k with `((k % n) + n) % n`. Three reverses: whole, first k, rest. O(n) time, O(1) space, in-place. Cyclic replacement is another O(n)/O(1) — visit each index exactly once, moving values forward by k. For non-mutating return, slice/concat works at O(n) space."

## Important takeaways

- **3-reverse trick** = O(n) time, O(1) space, in-place.
- **Modulo for k**: `((k % n) + n) % n`.
- **Left rotation = right rotation by `n-k`.**
- **Cyclic replacement** is an alternative.
- **`slice + concat` for non-mutating.**

## Variants

- **Rotate 2D matrix** — transpose + reverse rows (90° CW).
- **Rotate linked list** by k — find length, find new head, rewire.
- **Rotate string** — same trick, work on char array.

## Revision notes

```
right rotate by k:
  k = ((k % n) + n) % n
  reverse all
  reverse first k
  reverse rest
  O(n) / O(1) / in-place

left rotate by k = right rotate by n-k

cyclic replacement: visit each index once, move by k

non-mutating: arr.slice(-k).concat(arr.slice(0, -k))
```
