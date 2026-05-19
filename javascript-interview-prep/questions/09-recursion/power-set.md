# Power set — all subsets

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [permutations.md](./permutations.md), [backtracking-template.md](./backtracking-template.md)
>
> **Source:** LeetCode #78. Subsets II for duplicates (#90).

---

## 1. Problem statement

Generate all 2^n subsets. Two solutions: include/exclude recursion, and bitmask iteration.

**Verification examples**

```js
powerSet([1, 2, 3]);
// [[], [3], [2], [2,3], [1], [1,3], [1,2], [1,2,3]]

powerSet([]);                              // [[]]
powerSet([1]);                             // [[], [1]]

// Bitmask variant — order may differ
powerSetBitmask([1, 2]);
// [[], [1], [2], [1,2]]
```

**Constraints**
- 2^n outputs.
- Bitmask viable for n ≤ 30 (bit ops).
- Order: recursion natural; bitmask numeric.

---

## 2. Plain-English restatement

For each element: include or exclude. Two solutions: recursion (binary tree depth n) or bitmask iteration (for each integer 0..2^n-1, bits indicate inclusion).

---

## 3. Why this matters in interviews

Two genuinely different solutions. Follow-up "give second solution" separates rote from understanding (2^n ↔ n-bit numbers).

---

## 4. Mental model

```
   Include/exclude recursion:
     bt(index, current):
       if index === n: push [...current]; return
       bt(index + 1, current)      ← exclude
       current.push(nums[index])
       bt(index + 1, current)      ← include
       current.pop()                ← unchoose
   
   Bitmask iteration:
     for mask = 0; mask < (1 << n); mask++:
       subset = []
       for i = 0; i < n; i++:
         if (mask & (1 << i)) subset.push(nums[i])
       push subset
   
   Bitmask viable for n ≤ 30:
     1 << 30 = 1B; loop manageable but output limit.
     n=20: 1M subsets; OK.
     n=32: overflow in JS (>>> 0 handling).
   
   With duplicates (LeetCode #90):
     Sort + iterative include all + skip duplicates.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Output count?
> 2. Bitmask order vs recursion order?
> 3. Why is bitmask "interesting" follow-up?

---

## 6. Brute force — walked through

```js
// Iterative push-all
function ps(nums) {
  let result = [[]];
  for (const n of nums) {
    const next = [];
    for (const sub of result) next.push(sub, [...sub, n]);
    result = next;
  }
  return result;
}
```

Works. Conceptually: each new element doubles results (include/exclude each existing).

---

## 7. The unlocking insight

> **Include/exclude recursion OR bitmask iteration. 2^n subsets correspond to n-bit numbers. Pick by clarity.**

Three properties:

1. **Include/exclude** branch.
2. **2^n ↔ n bits** bitmask.
3. **`start` for dedup** (skip).

---

## 8. Solution (annotated)

```js
// (A) Include/exclude recursion
function powerSet(nums) {
  const result = [];
  function bt(index, current) {
    if (index === nums.length) {
      result.push([...current]);                                            // step 1: snapshot
      return;
    }
    bt(index + 1, current);                                                  // step 2: exclude
    current.push(nums[index]);
    bt(index + 1, current);                                                  // step 3: include
    current.pop();                                                            // step 4: unchoose
  }
  bt(0, []);
  return result;
}

// (B) Bitmask iteration — no recursion
function powerSetBitmask(nums) {
  const n = nums.length;
  const result = [];
  for (let mask = 0; mask < (1 << n); mask++) {                              // step 5: 2^n masks
    const subset = [];
    for (let i = 0; i < n; i++) {
      if (mask & (1 << i)) subset.push(nums[i]);                             // step 6: bit set
    }
    result.push(subset);
  }
  return result;
}

// (C) Iterative double
function powerSetDouble(nums) {
  let result = [[]];
  for (const n of nums) {
    const next = [];
    for (const sub of result) {
      next.push(sub);
      next.push([...sub, n]);                                                // step 7: double
    }
    result = next;
  }
  return result;
}

// With duplicates
function powerSetUnique(nums) {
  nums = [...nums].sort((a, b) => a - b);
  const result = [];
  function bt(start, current) {
    result.push([...current]);
    for (let i = start; i < nums.length; i++) {
      if (i > start && nums[i] === nums[i - 1]) continue;                   // step 8: skip dup
      current.push(nums[i]);
      bt(i + 1, current);
      current.pop();
    }
  }
  bt(0, []);
  return result;
}
```

**Try it yourself**

```js
powerSet([1, 2, 3]).length;                                   // 8 = 2^3
powerSet([]).length;                                          // 1 (just the empty set)
powerSet([1]);                                                // [[], [1]]

powerSetBitmask([1, 2]);                                      // [[], [1], [2], [1,2]]

// Feature flag combinations (real backend use)
const flags = ['darkmode', 'beta', 'experimental'];
powerSetBitmask(flags);                                       // all 8 combos for testing

// Subsets with constraint
function subsetsOfSize(nums, k) {
  const result = [];
  function bt(start, current) {
    if (current.length === k) { result.push([...current]); return; }
    for (let i = start; i < nums.length; i++) {
      current.push(nums[i]);
      bt(i + 1, current);
      current.pop();
    }
  }
  bt(0, []);
  return result;
}
subsetsOfSize([1, 2, 3, 4], 2);                               // [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
```

---

## 9. Step-by-step dry run

```
powerSet([1, 2]):

bt(0, []):
  bt(1, []):            // exclude 1
    bt(2, []):          // exclude 2 → push [].
    push 2: bt(2, [2]) → push [2]. pop.
  push 1: bt(1, [1]):
    bt(2, [1]) → push [1].
    push 2: bt(2, [1,2]) → push [1,2]. pop.
  pop.

Result: [[], [2], [1], [1,2]].

powerSetBitmask([1, 2]):
  n=2. masks 0, 1, 2, 3.
  mask=0 (00): no bits → [].
  mask=1 (01): bit 0 → [1].
  mask=2 (10): bit 1 → [2].
  mask=3 (11): bits 0, 1 → [1, 2].
  Result: [[], [1], [2], [1, 2]].

Bitmask order: by integer; recursion order: by include/exclude tree.

With dups [1, 1, 2]:
  sorted = [1, 1, 2].
  bt(0, []): push [].
    i=0 (1): push 1, bt(1, [1]): push [1].
      i=1 (1): push 1, bt(2, [1,1]): push [1,1].
        i=2 (2): push 2, bt(3, [1,1,2]): push [1,1,2]. pop.
      pop.
      i=2 (2): push 2, bt(3, [1,2]): push [1,2]. pop.
    pop.
    i=1 (1): i>start && nums[1]===nums[0] → SKIP.
    i=2 (2): push 2, bt(3, [2]): push [2]. pop.

  Result: [[], [1], [1,1], [1,1,2], [1,2], [2]]   (6 unique, vs 2^3=8).
```

---

## 10. Common confusion + traps

1. **Order differs** between recursion and bitmask.
2. **n > 30** — bitmask exceeds 32-bit; need BigInt.
3. **Push live current** — all entries final state.
4. **Dedup variant** — sort + `i > start` skip.
5. **`for..in` over mask** — wrong; numeric loop.
6. **Subsets of size k** — start parameter for combinations.
7. **n! vs 2^n** — perm vs subset.

---

## 11. Senior follow-ups & variants

### Variant 1 — Subsets of size k (combinations)
Add length check + start parameter.

### Variant 2 — Bitmask for feature flags
Real backend use.

### Variant 3 — Subsets with sum target
Subset-sum DP.

### Variant 4 — Sorted output
Match expected order.

### Variant 5 — Lazy generator
Yield one at a time.

---

## 12. How to think aloud

> "Power set = all 2^n subsets. Two genuinely different solutions: (A) Include/exclude recursion — for each index, recurse with element excluded, then push element, recurse with included, pop. Backtrack template. O(2^n) calls. (B) Bitmask iteration — for each integer `mask` in `[0, 2^n)`, check each bit `i`: if `mask & (1 << i)`, include `nums[i]`. O(n × 2^n) but no recursion. Valid for n ≤ 30 (32-bit JS bitwise); for n > 30 use BigInt. Senior signal: interviewer asks 'give me another' — bitmask answer shows you understand 2^n ↔ n-bit numbers. Real backend use: feature flag combinations for testing, RBAC permission matrices. With duplicates (Subsets II): sort + skip `i > start && nums[i] === nums[i-1]` — same dedup idea as combination-sum. Variants: subsets of size k (combinations, add length check + start parameter); subset-sum problem (DP); lazy generator yielding one subset at a time. Trap: push live state (all entries become final); n > 30 bitmask overflow; iterating order differs between solutions; expecting deterministic order from bitmask (it's numeric)."

---

## 13. 60-second revision

> - **2^n subsets.**
> - **Include/exclude recursion** OR **bitmask iteration**.
> - **Bitmask:** for `mask in [0, 2^n)`, `if mask & (1 << i)` include.
> - **n ≤ 30** for bitmask in JS.
> - **Dedup variant** — sort + `i > start` skip.
> - **Combinations** = subsets of size k.
> - **Feature flags** use bitmask.
> - **Trap:** push live; n > 30 overflow; order differs.

---

**Related:** [permutations.md](./permutations.md) · [backtracking-template.md](./backtracking-template.md) · [generate-parentheses.md](./generate-parentheses.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
