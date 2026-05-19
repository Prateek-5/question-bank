# Generate all permutations

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [backtracking-template.md](./backtracking-template.md)
>
> **Source:** LeetCode #46.

---

## 1. Problem statement

Generate all `n!` permutations of an array. Backtracking with `used[]` or swap-in-place.

**Verification examples**

```js
permutations([1, 2, 3]);
// [[1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]]

permutations([1]);                       // [[1]]
permutations([]);                        // [[]]
permutations([1, 2]);                    // [[1,2], [2,1]]
```

**Constraints**
- Output count: n!.
- Backtracking template: choose, explore, unchoose.
- Snapshot copy `[...current]` per complete.
- Duplicates variant (LeetCode #47): sort + skip equal-prev when prev unused.

---

## 2. Plain-English restatement

For each position, pick any unused element; recurse for remaining positions; unchoose. Snapshot at complete.

---

## 3. Why this matters in interviews

First true backtracking. Tests: recursion + branching, state restoration, awareness n! grows fast.

---

## 4. Mental model

```
   used[] approach:
     for each position:
       try each unused element
       choose it (used[i] = true, current.push)
       recurse
       unchoose (current.pop, used[i] = false)
   
   Snapshot when current.length === nums.length.
   
   Swap-in-place approach (O(1) extra space beyond output):
     def perm(arr, start):
       if start == n: push [...arr]
       for i in start..n-1:
         swap arr[start], arr[i]
         perm(arr, start+1)
         swap back
   
   With duplicates (LeetCode #47):
     sort first.
     skip i if nums[i] === nums[i-1] && !used[i-1].
   
   Complexity:
     n! permutations × O(n) per snapshot = O(n × n!).
     n=12: 479M perms; pushing arrays is the bottleneck.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why snapshot copy?
> 2. Swap vs used[] tradeoff?
> 3. Duplicate handling logic?

---

## 6. Brute force — walked through

```js
// Push live state — all entries become final state
function buggy(nums) {
  const out = []; const cur = [];
  function bt() {
    if (cur.length === nums.length) { out.push(cur); return; }  // live!
    // ...
  }
}
// All entries in out point to same array → all []
```

---

## 7. The unlocking insight

> **`used[]` + push/pop with `[...current]` snapshot. Swap-in-place is O(1) extra. Duplicates: sort + skip dupes.**

Three properties:

1. **Backtrack template** choose/explore/unchoose.
2. **Snapshot copy** at complete.
3. **`used[]` or swap** for state.

---

## 8. Solution (annotated)

```js
// (A) Pick-and-recurse with used[]
function permutations(nums) {
  const result = [];
  const current = [];
  const used = new Array(nums.length).fill(false);

  function backtrack() {
    if (current.length === nums.length) {
      result.push([...current]);                                           // step 1: snapshot
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;                                                // step 2: skip used
      used[i] = true; current.push(nums[i]);                                // step 3: choose
      backtrack();
      current.pop(); used[i] = false;                                       // step 4: unchoose
    }
  }
  backtrack();
  return result;
}

// (B) Swap-in-place — O(1) extra beyond output
function permutationsSwap(nums) {
  const result = [];
  function bt(start) {
    if (start === nums.length) { result.push([...nums]); return; }
    for (let i = start; i < nums.length; i++) {
      [nums[start], nums[i]] = [nums[i], nums[start]];                     // step 5: swap in
      bt(start + 1);
      [nums[start], nums[i]] = [nums[i], nums[start]];                     // step 6: swap back
    }
  }
  bt(0);
  return result;
}

// With duplicates (LeetCode #47)
function permutationsUnique(nums) {
  nums = [...nums].sort((a, b) => a - b);
  const result = [];
  const current = [];
  const used = new Array(nums.length).fill(false);

  function bt() {
    if (current.length === nums.length) { result.push([...current]); return; }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      if (i > 0 && nums[i] === nums[i - 1] && !used[i - 1]) continue;     // step 7: dedup
      used[i] = true; current.push(nums[i]);
      bt();
      current.pop(); used[i] = false;
    }
  }
  bt();
  return result;
}
```

**Try it yourself**

```js
permutations([1, 2, 3]).length;                               // 6
permutations([1]).length;                                      // 1
permutations([]).length;                                       // 1 (one empty perm)

permutationsUnique([1, 1, 2]);                                // [[1,1,2], [1,2,1], [2,1,1]]   (3 not 6)

// Iterative via next-permutation
function nextPermutation(nums) {
  let i = nums.length - 2;
  while (i >= 0 && nums[i] >= nums[i + 1]) i--;
  if (i < 0) { nums.reverse(); return false; }
  let j = nums.length - 1;
  while (nums[j] <= nums[i]) j--;
  [nums[i], nums[j]] = [nums[j], nums[i]];
  nums.splice(i + 1, nums.length - i - 1, ...nums.slice(i + 1).reverse());
  return true;
}

function permutationsIter(nums) {
  const sorted = [...nums].sort((a, b) => a - b);
  const out = [[...sorted]];
  while (nextPermutation(sorted)) out.push([...sorted]);
  return out;
}
```

---

## 9. Step-by-step dry run

```
permutations([1, 2, 3]):

bt(): cur=[]
  i=0 (1): used[0]=T, cur=[1]
    bt(): cur=[1]
      i=1 (2): cur=[1,2]
        bt(): cur=[1,2]
          i=2 (3): cur=[1,2,3] → push [1,2,3]. pop.
        pop=2. used[1]=F.
      i=2 (3): cur=[1,3]
        bt(): cur=[1,3]
          i=1 (2): cur=[1,3,2] → push. pop.
        pop=3. used[2]=F.
    pop=1. used[0]=F.
  i=1 (2): similar → [2,1,3], [2,3,1].
  i=2 (3): similar → [3,1,2], [3,2,1].

Result: 6 permutations.

Swap variant for [1,2,3]:
  bt(0): swap(0,0). bt(1): swap(1,1). bt(2): push [1,2,3].
    swap(1,2). bt(2): push [1,3,2]. swap back.
  swap(0,1). [2,1,3]. bt(1): swap(1,1). bt(2): push [2,1,3].
    swap(1,2). bt(2): push [2,3,1]. swap back.
  swap back (0,1). [1,2,3].
  swap(0,2). [3,2,1]. ... continues.

With duplicates [1,1,2]:
  sorted: [1,1,2].
  i=0 (first 1): used[0]=T. recurse.
    i=0 used. i=1 (second 1): NO prev-skip needed (i>0 and same as prev BUT used[0]=T → skip-condition `!used[i-1]` is false → DO use). 
    Actually re-read: skip if `nums[i]===nums[i-1] && !used[i-1]`. !used[0]=false → don't skip. Use.
    Continue.
  Back at outer i=1: nums[1]===nums[0] and !used[0]=true → SKIP.
    (Already covered above branch.)
  i=2 (2): proceed.
```

---

## 10. Common confusion + traps

1. **Push live state** — all entries point to final.
2. **Forget unchoose** — exponential explosion.
3. **`used` reset** missed.
4. **Sort + dedup skip condition** — `!used[i-1]` not `used[i-1]`.
5. **Swap missed undo** — state corrupt.
6. **n! grows fast** — 12! = 479M; 15! crashes.
7. **`for..of`** without index — need index for used/swap.

---

## 11. Senior follow-ups & variants

### Variant 1 — Duplicates (LeetCode #47)
Sort + skip equal-prev when prev unused.

### Variant 2 — K-th permutation directly
Factorial number system; O(n²).

### Variant 3 — Next permutation
Lexicographic next; iterative O(n).

### Variant 4 — Random permutation
Fisher-Yates shuffle O(n).

### Variant 5 — Heap's algorithm
Single swap per perm; classic.

---

## 12. How to think aloud

> "Permutations: backtrack template with `used[]` flag set. For each position 0..n-1: try every unused element; mark used; push to current; recurse; pop; unmark. Snapshot copy `[...current]` when `current.length === nums.length`. Swap-in-place variant uses O(1) extra space beyond output: swap `nums[start]` with each `nums[i]` for i ≥ start, recurse with start+1, swap back. With duplicates (LeetCode #47): sort first, skip if `nums[i] === nums[i-1] && !used[i-1]` — this skips choosing duplicate-of-prev when prev wasn't used in the current path (avoids generating the same permutation twice). Time: O(n × n!) — n! permutations, O(n) per snapshot/push. n=12 produces 479M; n=15 crashes. Variants: k-th permutation directly via factorial number system O(n²); next-permutation lexicographic O(n); Fisher-Yates random shuffle O(n); Heap's algorithm one-swap-per-perm. Trap: push live state (all entries become final); forget unchoose (explosion); skip-condition `!used[i-1]` not `used[i-1]` (subtle dedup bug)."

---

## 13. 60-second revision

> - **Backtrack with `used[]`** or swap-in-place.
> - **Choose/explore/unchoose.**
> - **Snapshot `[...current]`** at complete.
> - **Dedup:** sort + skip `nums[i]===nums[i-1] && !used[i-1]`.
> - **Swap variant** O(1) extra space.
> - **n! grows fast** — n=12 = 479M.
> - **Next-permutation** lexicographic iter.
> - **Fisher-Yates** for random.
> - **Trap:** live snapshot; no unchoose; skip-condition subtle.

---

**Related:** [backtracking-template.md](./backtracking-template.md) · [power-set.md](./power-set.md) · [generate-parentheses.md](./generate-parentheses.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
