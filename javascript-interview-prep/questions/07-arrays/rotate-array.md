# Rotate array by K positions

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [move-zeros-in-place.md](./move-zeros-in-place.md)
>
> **Source:** LeetCode #189. Universal.

---

## 1. Problem statement

Rotate array right by `k` positions. Solve in O(n) time, O(1) space (in-place reverse trick).

**Verification examples**

```js
rotateRight([1, 2, 3, 4, 5], 2);          // [4, 5, 1, 2, 3]
rotateRight([1, 2, 3, 4, 5], 7);          // [4, 5, 1, 2, 3]  (k mod n)
rotateRight([1, 2, 3], 0);                // [1, 2, 3]
rotateRight([], 3);                       // []
rotateRight([1, 2, 3, 4, 5], -1);         // [2, 3, 4, 5, 1]  (left by 1)
```

**Constraints**
- O(n) time.
- O(1) extra space (in-place).
- Handle `k > n` via modulo.
- Negative `k` via `((k % n) + n) % n`.
- Left rotation = right by `n - k`.

---

## 2. Plain-English restatement

Move elements `k` positions to the right, wrapping around. Three-reverse trick: reverse whole array, reverse first k, reverse rest.

---

## 3. Why this matters in interviews

Trivial with extra space; classic O(n)/O(1) with reverse-three-times. Handles negative k and k > n. Tests in-place algorithm thinking.

---

## 4. Mental model

```
   Reverse trick:
     k = ((k % n) + n) % n         ← normalize
     reverse(arr, 0, n-1)          ← reverse whole
     reverse(arr, 0, k-1)          ← reverse first k
     reverse(arr, k, n-1)          ← reverse rest
   
   Why it works:
     [1,2,3,4,5] k=2
     reverse all:       [5,4,3,2,1]
     reverse first 2:   [4,5,3,2,1]
     reverse rest:      [4,5,1,2,3]   ✓
   
   Extra-space version:
     return arr.slice(-k).concat(arr.slice(0, -k));    ← O(n)/O(n)
   
   Alternative: cyclic replacements (gcd dance) — O(n)/O(1) but messy.

   Negative k:
     -1 % 5 = -1 (JS).
     ((-1 % 5) + 5) % 5 = 4.
     Right by 4 = left by 1. ✓
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why reverse THREE times?
> 2. How to handle `k > n`?
> 3. How to handle negative `k`?

---

## 6. Brute force — walked through

```js
// O(n*k) — pop and unshift
for (let i = 0; i < k; i++) arr.unshift(arr.pop());
```

unshift is O(n) per call; total O(nk). Bad.

```js
// O(n)/O(n) extra space — simple
return arr.slice(-k).concat(arr.slice(0, -k));
```

Works but allocates.

---

## 7. The unlocking insight

> **Three-reverse trick: reverse whole, reverse first k, reverse rest. O(n)/O(1). Normalize k via `((k % n) + n) % n`.**

Three properties:

1. **Normalize k** — modulo handles k > n and negatives.
2. **Three reverses** = rotation, O(n) total.
3. **In-place** swap with two pointers — O(1) extra.

---

## 8. Solution (annotated)

```js
function rotateRight(arr, k) {
  const n = arr.length;
  if (n <= 1) return arr;                                                // step 1: trivial
  k = ((k % n) + n) % n;                                                 // step 2: normalize (negatives, k>n)
  if (k === 0) return arr;

  reverse(arr, 0, n - 1);                                                // step 3: whole
  reverse(arr, 0, k - 1);                                                // step 4: first k
  reverse(arr, k, n - 1);                                                // step 5: rest
  return arr;
}

function reverse(arr, lo, hi) {
  while (lo < hi) {
    [arr[lo], arr[hi]] = [arr[hi], arr[lo]];                             // swap; O(1) extra
    lo++; hi--;
  }
}

// Extra-space version (clearer but O(n) memory)
function rotateRightCopy(arr, k) {
  const n = arr.length;
  if (n === 0) return [];
  k = ((k % n) + n) % n;
  return arr.slice(-k).concat(arr.slice(0, -k));
}
```

**Try it yourself**

```js
rotateRight([1, 2, 3, 4, 5], 2);                              // [4, 5, 1, 2, 3]
rotateRight([1, 2, 3, 4, 5], 7);                              // [4, 5, 1, 2, 3] (7 % 5 = 2)
rotateRight([1, 2, 3, 4, 5], -1);                             // [2, 3, 4, 5, 1] (left 1)
rotateRight([1], 100);                                         // [1]
rotateRight([], 5);                                            // []

// Left rotation
function rotateLeft(arr, k) {
  const n = arr.length;
  if (n <= 1) return arr;
  return rotateRight(arr, n - ((k % n + n) % n));
}

// Cyclic gcd-based variant (one pass, no extra space)
function rotateCyclic(arr, k) {
  const n = arr.length;
  k = ((k % n) + n) % n;
  let count = 0;
  for (let start = 0; count < n; start++) {
    let current = start;
    let prev = arr[start];
    do {
      const next = (current + k) % n;
      [arr[next], prev] = [prev, arr[next]];
      current = next;
      count++;
    } while (start !== current);
  }
}
```

---

## 9. Step-by-step dry run

```
rotateRight([1,2,3,4,5], 2):
  n=5. k = ((2%5)+5)%5 = 2.
  
  reverse(arr, 0, 4):
    swap arr[0],arr[4] → [5,2,3,4,1].
    swap arr[1],arr[3] → [5,4,3,2,1].
    arr[2] middle; lo=hi stop.
    Result: [5,4,3,2,1].
  
  reverse(arr, 0, 1):
    swap arr[0],arr[1] → [4,5,3,2,1].
    Result: [4,5,3,2,1].
  
  reverse(arr, 2, 4):
    swap arr[2],arr[4] → [4,5,1,2,3].
    swap arr[3] (middle skipped, lo=hi).
    Result: [4,5,1,2,3].
  
  Return [4,5,1,2,3]. ✓

rotateRight([1,2,3,4,5], -1):
  k = ((-1 % 5) + 5) % 5 = (((-1) + 5) % 5) = 4. (Right by 4 = left by 1.)
  reverse all: [5,4,3,2,1].
  reverse first 4: [2,3,4,5,1].
  reverse rest (4..4): [2,3,4,5,1].
  Return [2,3,4,5,1]. ✓

rotateRight([1,2,3], 0):
  k normalized 0. Early return.
```

---

## 10. Common confusion + traps

1. **`k % n` for negatives** — JS returns negative; needs `+n` correction.
2. **`k > n`** — modulo first.
3. **Empty / single-element** — early return.
4. **In-place vs return new** — interviewer often wants in-place.
5. **Off-by-one in reverse bounds** — `k-1` for first k, `n-1` for last.
6. **Left rotation** — `n - k_normalized`.
7. **unshift/pop in loop** — O(nk); bad for large.

---

## 11. Senior follow-ups & variants

### Variant 1 — Cyclic gcd-based
One pass; counts iterations via gcd(n, k).

### Variant 2 — Left rotation
Same as right by `n - k`.

### Variant 3 — Rotate string (immutable)
Convert to array, rotate, join — O(n)/O(n).

### Variant 4 — Rotate doubly linked list
Pointer manipulation — true O(1).

### Variant 5 — Rotate 2D matrix
LeetCode #48; transpose + reverse rows.

---

## 12. How to think aloud

> "Rotate by k is the classic in-place algorithm question. Naive: pop+unshift O(nk). Easy: `slice(-k).concat(slice(0,-k))` O(n)/O(n). Optimal O(n)/O(1): three-reverse trick — reverse whole array, reverse first k, reverse rest. Why it works: reversing positions then reversing each segment lands them in rotated order. Normalize k first via `((k % n) + n) % n` — handles both k > n and negative k (JS `-1 % 5` is `-1`, so we add n). Edge cases: empty array, single element, k=0 — early return. Left rotation = right by `n - k`. Other variant: cyclic gcd-based (one pass, true O(1) — but harder to get right). Trap: `k % n` for negatives; off-by-one in reverse bounds; unshift/pop loop (O(nk)); mutate vs return (interviewer wants in-place typically)."

---

## 13. 60-second revision

> - **`k = ((k % n) + n) % n`** — normalize (k>n, negatives).
> - **Three reverses:** whole, first k, rest.
> - **O(n)/O(1)** in-place.
> - **Swap pointers** for reverse.
> - **`unshift+pop` is O(nk)** — avoid.
> - **Left = right by `n - k`.**
> - **Cyclic variant** — one pass, gcd dance.
> - **Trap:** negative `k % n`; off-by-one bounds; unshift/pop loop.

---

**Related:** [move-zeros-in-place.md](./move-zeros-in-place.md) · [transpose-matrix.md](./transpose-matrix.md) · [polyfill-flat.md](./polyfill-flat.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
