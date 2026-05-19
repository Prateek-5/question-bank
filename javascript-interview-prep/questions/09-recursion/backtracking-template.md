# Backtracking template

> **Difficulty:** Medium-Senior   |   **Time:** ~10 min   |   **Prereqs:** [generate-parentheses.md](./generate-parentheses.md), [permutations.md](./permutations.md)
>
> **Source:** N-Queens, Sudoku, permutations, subsets, word break, palindrome partitioning. Every senior interview.

---

## 1. Problem statement

Memorize the backtracking template: choose, explore, unchoose. Apply to permutations, subsets, combinations, N-Queens.

**Verification examples**

```js
// Permutations
function permutations(nums) {
  const out = [];
  const cur = [];
  const used = new Array(nums.length).fill(false);
  function bt() {
    if (cur.length === nums.length) { out.push([...cur]); return; }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true; cur.push(nums[i]);
      bt();
      cur.pop(); used[i] = false;
    }
  }
  bt();
  return out;
}

// Subsets (include/exclude)
function subsets(nums) {
  const out = [];
  function bt(i, cur) {
    if (i === nums.length) { out.push([...cur]); return; }
    bt(i + 1, cur);                          // exclude
    cur.push(nums[i]);
    bt(i + 1, cur);                          // include
    cur.pop();                                // unchoose
  }
  bt(0, []);
  return out;
}
```

**Constraints**
- Push COPY to results (state mutates).
- Unchoose on every return.
- Prune via `isValid` predicate.
- Order-insensitive subsets: iterate from `start`, not 0.

---

## 2. Plain-English restatement

Search the solution space tree by choosing one option, recursing, then unchoosing (backtracking). Prune invalid branches early. Snapshot complete solutions.

---

## 3. Why this matters in interviews

Canonical search pattern. Senior bar: produce template on demand, identify pruning, reason about exponential complexity.

---

## 4. Mental model

```
   backtrack(state):
     if isComplete(state):
       results.push([...state])    ← SNAPSHOT (copy, not ref)
       return
     for choice of choices(state):
       if !isValid(state, choice):
         continue                    ← prune
       state.push(choice)            ← choose
       backtrack(state)              ← explore
       state.pop()                    ← unchoose
   
   4 ingredients:
     1. State — partial solution.
     2. Choices at this step.
     3. isValid(state, choice) — pruning predicate.
     4. isComplete(state) — accept condition.
   
   Common shapes:
     Permutations: used[] flag set.
     Subsets: iterate from `start` to avoid duplicates.
     Combinations: nC(k) — iterate from `start`, fix size.
     N-Queens: track rows, diag1, diag2 as Sets.
     Sudoku: track rows[9], cols[9], boxes[9] as Sets of digits.
   
   Time complexity:
     Exponential at worst (O(2^n) / O(n!)).
     Pruning tightens — N-Queens is super-exponential without, polynomial branches with.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why push a copy not the state?
> 2. What's the #1 bug?
> 3. When use `start` parameter vs `used` flags?

---

## 6. Brute force — walked through

```js
// Common bug: push live state, no unchoose
function buggy(nums) {
  const out = [];
  function bt(cur) {
    if (cur.length === nums.length) { out.push(cur); return; }  // push live!
    for (const n of nums) {
      cur.push(n);                                                // never unchoose
      bt(cur);
    }
  }
  bt([]);
  return out;
}
```

Bugs: shared array (mutated for all entries); no unchoose (infinite growth); no `used[]` (repeats).

---

## 7. The unlocking insight

> **Choose → explore → unchoose. Snapshot copies on complete. Prune via predicate. State `used[]` or `start` for dedup.**

Three properties:

1. **Choose / explore / unchoose** template.
2. **Snapshot copy** at complete.
3. **Prune early** — exponential search.

---

## 8. Solution (annotated)

```js
// Generic template
function backtrack(state, choices, isComplete, isValid, results) {
  if (isComplete(state)) {
    results.push([...state]);                                              // step 1: snapshot
    return;
  }
  for (const choice of choices(state)) {
    if (!isValid(state, choice)) continue;                                 // step 2: prune
    state.push(choice);                                                    // step 3: choose
    backtrack(state, choices, isComplete, isValid, results);              // step 4: explore
    state.pop();                                                            // step 5: unchoose
  }
}

// N-Queens
function nQueens(n) {
  const result = [];
  const cols = new Set();
  const diag1 = new Set();     // r - c
  const diag2 = new Set();     // r + c
  const board = [];

  function place(r) {
    if (r === n) { result.push([...board]); return; }
    for (let c = 0; c < n; c++) {
      if (cols.has(c) || diag1.has(r - c) || diag2.has(r + c)) continue;  // prune
      cols.add(c); diag1.add(r - c); diag2.add(r + c);
      board.push(c);
      place(r + 1);
      cols.delete(c); diag1.delete(r - c); diag2.delete(r + c);          // unchoose
      board.pop();
    }
  }
  place(0);
  return result;
}

// Combination sum
function combinationSum(candidates, target) {
  const out = [];
  candidates.sort((a, b) => a - b);
  function bt(start, sum, cur) {
    if (sum === target) { out.push([...cur]); return; }
    if (sum > target) return;
    for (let i = start; i < candidates.length; i++) {
      if (i > start && candidates[i] === candidates[i - 1]) continue;     // skip duplicates
      cur.push(candidates[i]);
      bt(i + 1, sum + candidates[i], cur);
      cur.pop();
    }
  }
  bt(0, 0, []);
  return out;
}
```

**Try it yourself**

```js
permutations([1, 2, 3]).length;                               // 6 = 3!
subsets([1, 2, 3]).length;                                    // 8 = 2^3
nQueens(4).length;                                            // 2 solutions for 4-queens
nQueens(8).length;                                            // 92 solutions
combinationSum([2, 3, 6, 7], 7);                              // [[7], [2,2,3]]

// Word break
function wordBreak(s, dict) {
  const set = new Set(dict);
  const memo = new Map();
  function bt(i) {
    if (i === s.length) return true;
    if (memo.has(i)) return memo.get(i);
    for (let j = i + 1; j <= s.length; j++) {
      if (set.has(s.slice(i, j)) && bt(j)) {
        memo.set(i, true); return true;
      }
    }
    memo.set(i, false);
    return false;
  }
  return bt(0);
}

// Palindrome partitioning
function palinPartition(s) {
  const out = [];
  function isP(l, r) { while (l < r) if (s[l++] !== s[r--]) return false; return true; }
  function bt(i, cur) {
    if (i === s.length) { out.push([...cur]); return; }
    for (let j = i; j < s.length; j++) {
      if (!isP(i, j)) continue;
      cur.push(s.slice(i, j + 1));
      bt(j + 1, cur);
      cur.pop();
    }
  }
  bt(0, []);
  return out;
}
```

---

## 9. Step-by-step dry run

```
permutations([1, 2, 3]):

bt(): cur=[], used=[F,F,F].
  i=0: used[0]=T, cur=[1].
    bt(): cur=[1].
      i=1: used[1]=T, cur=[1,2].
        bt(): cur=[1,2].
          i=2: used[2]=T, cur=[1,2,3].
            bt(): len 3 = nums.length → push [1,2,3]. return.
          cur.pop()=3. used[2]=F.
        return.
      cur.pop()=2. used[1]=F.
      i=2: used[2]=T, cur=[1,3].
        bt() → i=1 → cur=[1,3,2] → push.
        cur.pop. used[1]=F.
    cur.pop=1. used[0]=F.
  i=1: similar → [2,1,3], [2,3,1].
  i=2: → [3,1,2], [3,2,1].
  
  Result: 6 permutations.

Subsets [1,2]:
  bt(0, []):
    bt(1, []):     // exclude 1
      bt(2, []):   // exclude 2 → push [].
      push 2: bt(2, [2]) → push [2]. pop.
    push 1: bt(1, [1]):
      bt(2, [1]) → push [1].
      push 2: bt(2, [1,2]) → push [1,2]. pop.
    pop.
  Result: [[], [2], [1], [1,2]].

Snapshot vs live:
  out.push(cur) without spread:
    All entries point to same array.
    After bt pops everything: all entries become [].
  out.push([...cur]):
    New array. Independent.
```

---

## 10. Common confusion + traps

1. **Push live state** — all entries become final state.
2. **Forget unchoose** — state grows unbounded.
3. **No pruning** — exponential explodes.
4. **`used` vs `start`** — used for permutations, start for subsets.
5. **Iterate from 0 in subsets** — generates duplicates.
6. **Mutate input** — common in N-Queens.
7. **`for..of` with index needed** — use index loop.

---

## 11. Senior follow-ups & variants

### Variant 1 — Iterative with explicit stack
For depth-safety.

### Variant 2 — Branch-and-bound
Add objective bound for pruning.

### Variant 3 — Memoize (DP)
For overlapping subproblems.

### Variant 4 — Constraint propagation (AC-3)
Sudoku: domain reduction.

### Variant 5 — Random sampling
For huge spaces; sample paths.

---

## 12. How to think aloud

> "Backtracking is choose → explore → unchoose. Generic template: if `isComplete(state)`, push `[...state]` (snapshot, NOT live reference) to results; else for each `choice` in `choices(state)`, if `isValid(state, choice)` push choice onto state, recurse, pop choice. Four ingredients: state (partial solution), choices, isValid predicate, isComplete predicate. Common shapes: permutations use `used[]` flag set (no repeats); subsets use `start` parameter (avoid duplicates by iterating from current index); combinations same as subsets but with size constraint; N-Queens tracks columns + two diagonal sets as O(1) lookup; Sudoku tracks 9 row sets + 9 column sets + 9 box sets. Pruning is the whole game — naive O(n!) for permutations, but N-Queens prunes super-exponential branches to polynomial via the three sets. Memoize when subproblems overlap → DP. Snapshot copy is the #1 bug: pushing the live state means all results point to the final empty state after backtracking pops everything. Unchoose on every return is the #2 bug. Trap: live snapshot; forgetting unchoose; iterating 0 for subsets (duplicates); ignoring pruning."

---

## 13. 60-second revision

> - **Choose / explore / unchoose** template.
> - **Snapshot copy** on complete — `[...state]`.
> - **Prune via predicate** — exponential without.
> - **`used[]` for perms; `start` for subsets/combos.**
> - **N-Queens:** cols + 2 diagonals as Sets.
> - **Memoize** → DP for overlapping.
> - **Iterative + explicit stack** for depth safety.
> - **Trap:** live snapshot; no unchoose; no prune; start=0 for subsets.

---

**Related:** [permutations.md](./permutations.md) · [power-set.md](./power-set.md) · [generate-parentheses.md](./generate-parentheses.md) · [climbing-stairs-memoized.md](./climbing-stairs-memoized.md) · [iterative-from-recursive.md](./iterative-from-recursive.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
