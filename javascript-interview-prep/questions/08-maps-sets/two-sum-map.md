# Two-Sum with a Map (O(n))

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md)
>
> **Source:** LeetCode #1. Most-asked interview problem.

---

## 1. Problem statement

Given `nums` and `target`, return indices of two numbers summing to target. O(n) with a Map.

**Verification examples**

```js
twoSum([2, 7, 11, 15], 9);              // [0, 1]
twoSum([3, 3], 6);                       // [0, 1]
twoSum([3, 2, 4], 6);                    // [1, 2]
twoSum([1, 2], 5);                       // [] (no pair)
twoSum([0, 0], 0);                       // [0, 1]
```

**Constraints**
- Single pass O(n) time, O(n) space.
- Check `seen.has(need)` BEFORE `seen.set(num, i)` — handles duplicates.
- Return any one valid pair (per spec).

---

## 2. Plain-English restatement

For each `num`, look for the complement `target - num` in a Map. If found, return `[seenIndex, currentIndex]`. Otherwise, record current num → index.

---

## 3. Why this matters in interviews

Canonical hash-trick problem — "trade space for time with a Map." Senior interviewers expect <5 min single-pass solution. Generalizes to: duplicate transactions, order book matching, batch FK resolution.

---

## 4. Mental model

```
   single pass O(n):
     seen = Map<value, index>
     for i = 0..n-1:
       need = target - nums[i]
       if seen.has(need):
         return [seen.get(need), i]
       seen.set(nums[i], i)
     return []
   
   Order matters:
     CHECK first, SET after.
     Otherwise [3, 3] target 6: 
       i=0: set(3, 0).
       i=1: need=3, has → [0, 1]. ✓
     If we set before check:
       i=0: set(3, 0). need=3, has → [0, 0]. ✗
   
   Variants:
     Sorted input: two pointers, O(1) space.
     All pairs: enumerate; different problem.
     Return values vs indices: re-read prompt.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why check `has` BEFORE `set`?
> 2. Why Map over plain object?
> 3. Sorted input — better approach?

---

## 6. Brute force — walked through

```js
function twoSum(nums, target) {
  for (let i = 0; i < nums.length; i++) {
    for (let j = i + 1; j < nums.length; j++) {
      if (nums[i] + nums[j] === target) return [i, j];
    }
  }
  return [];
}
```

O(n²) — dies above n=10k.

---

## 7. The unlocking insight

> **Map<value, index>: for each num, check `has(target - num)`. Trade space for time. Check before set to handle dupes.**

Three properties:

1. **Map for O(1) lookup**.
2. **Check then set** order.
3. **Single pass** — O(n).

---

## 8. Solution (annotated)

```js
function twoSum(nums, target) {
  const seen = new Map();                                                 // step 1: value → index
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];                                         // step 2: complement
    if (seen.has(need)) return [seen.get(need), i];                       // step 3: check first
    seen.set(nums[i], i);                                                  // step 4: record after
  }
  return [];                                                                // step 5: no pair
}

// Sorted input: two-pointer, O(1) space
function twoSumSorted(nums, target) {
  let lo = 0, hi = nums.length - 1;
  while (lo < hi) {
    const s = nums[lo] + nums[hi];
    if (s === target) return [lo, hi];
    if (s < target) lo++;
    else hi--;
  }
  return [];
}

// All pairs
function twoSumAll(nums, target) {
  const seen = new Map();
  const out = [];
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (seen.has(need)) {
      for (const j of seen.get(need)) out.push([j, i]);
    }
    if (!seen.has(nums[i])) seen.set(nums[i], []);
    seen.get(nums[i]).push(i);
  }
  return out;
}
```

**Try it yourself**

```js
twoSum([2, 7, 11, 15], 9);                                    // [0, 1]
twoSum([3, 3], 6);                                            // [0, 1]
twoSum([3, 2, 4], 6);                                         // [1, 2] (not [0])
twoSum([], 5);                                                 // []
twoSum([0, 0], 0);                                            // [0, 1]

// Sorted
twoSumSorted([1, 2, 3, 4], 5);                                // [0, 3] or [1, 2]

// 3-Sum extension — fix one, two-sum the rest
function threeSum(nums) {
  nums = [...nums].sort((a, b) => a - b);
  const out = [];
  for (let i = 0; i < nums.length - 2; i++) {
    if (i > 0 && nums[i] === nums[i - 1]) continue;            // dedup
    let lo = i + 1, hi = nums.length - 1;
    while (lo < hi) {
      const s = nums[i] + nums[lo] + nums[hi];
      if (s === 0) {
        out.push([nums[i], nums[lo], nums[hi]]);
        while (lo < hi && nums[lo] === nums[lo + 1]) lo++;
        while (lo < hi && nums[hi] === nums[hi - 1]) hi--;
        lo++; hi--;
      } else if (s < 0) lo++;
      else hi--;
    }
  }
  return out;
}
```

---

## 9. Step-by-step dry run

```
twoSum([2, 7, 11, 15], 9):
  seen = Map{}.
  i=0 num=2: need=7. seen.has(7)? No. seen.set(2, 0). Map{2→0}.
  i=1 num=7: need=2. seen.has(2)? Yes (idx 0). Return [0, 1].

twoSum([3, 3], 6):
  i=0 num=3: need=3. seen.has(3)? No. seen.set(3, 0). Map{3→0}.
  i=1 num=3: need=3. seen.has(3)? Yes (idx 0). Return [0, 1].
  
  ✓ Works because CHECK was before SET.
  Buggy version (set first): i=0 would set(3,0); on need=3 has(3)→true, would return [0, 0]. Wrong.

twoSum([1, 2], 5):
  i=0: need=4. No. set(1, 0).
  i=1: need=3. No. set(2, 1).
  Return [].

twoSumSorted([1, 2, 3, 4], 5):
  lo=0, hi=3. sum=1+4=5 → return [0, 3].

vs brute O(n²):
  For n=10000, brute does ~50M ops. Map does ~10k. 5000x.
```

---

## 10. Common confusion + traps

1. **Set before check** — `[3, 3]` returns `[0, 0]`.
2. **Use Object instead** — string coercion can cause bugs (numeric keys).
3. **Floating point** — `0.1 + 0.2 !== 0.3`; integer-only safe.
4. **Multiple pairs** — return one; don't enumerate unless asked.
5. **Sorted input** — switch to two-pointer for O(1) space.
6. **Empty array** — return `[]`; don't crash.
7. **Return indices vs values** — re-read prompt.

---

## 11. Senior follow-ups & variants

### Variant 1 — Two-Sum sorted (two-pointer)
O(n) time, O(1) space.

### Variant 2 — Three-Sum (LeetCode #15)
Fix one + two-sum sorted rest.

### Variant 3 — All pairs
Map<value, indices[]>.

### Variant 4 — Pair with K diff
`nums[i] - nums[j] === k`; similar Map approach.

### Variant 5 — Streaming
Process online with O(window) memory if "find sum in last K".

---

## 12. How to think aloud

> "Two-Sum is the canonical hash-trick — trade space for time with a Map. O(n²) brute force is obvious; the senior signal is producing the O(n) single-pass Map solution in under five minutes. Algorithm: keep `Map<value, index>`; for each `nums[i]`, compute `need = target - nums[i]`; if `seen.has(need)`, return `[seen.get(need), i]`; else `seen.set(nums[i], i)`. **Order matters: check BEFORE set** — otherwise `[3, 3]` target 6 returns `[0, 0]` (same index). Use Map over object: object stringifies keys (`obj[5] === obj['5']`), Map preserves type. Map has SameValueZero — `0` and `-0` collide, NaN keys work. Floating-point input is unsafe (`0.1 + 0.2 !== 0.3`); usually integer per problem. Variants: sorted input → two-pointer O(1) space; all pairs → Map<value, indices[]>; Three-Sum → fix outer, two-sum-sorted the rest. Trap: set before check; object instead of Map; float input; expecting all pairs."

---

## 13. 60-second revision

> - **Single pass + Map**: O(n) time, O(n) space.
> - **`Map<value, index>`**; check then set.
> - **Check before set** — duplicates `[3, 3]`.
> - **Map over Object** — no key coercion.
> - **Sorted input → two-pointer** O(1) space.
> - **All pairs** → Map<value, indices[]>.
> - **Three-Sum** = fix + two-sum.
> - **Trap:** set-first bug; float precision; expect all pairs.

---

**Related:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [first-non-repeating-char.md](./first-non-repeating-char.md) · [group-anagrams.md](./group-anagrams.md) · [multiset-counter.md](./multiset-counter.md) · [`07-arrays/sliding-window-helper.md`](../07-arrays/sliding-window-helper.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
