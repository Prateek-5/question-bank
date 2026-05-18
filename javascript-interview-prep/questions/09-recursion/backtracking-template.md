# Backtracking Template

## Source / Origin
- Standard CS: N-Queens, Sudoku, permutations, subsets, word break, palindrome partitioning.
- Asked at: every senior interview.
- Concept reference: `concepts/recursion.md`.

## Why this question matters in interviews
Backtracking is the canonical "search the solution space, prune as you go" pattern. Senior bar: you can produce the template on demand, identify pruning conditions, and reason about time complexity (exponential, but tight via pruning).

## Concepts involved

### Syntax to lock in
```js
function backtrack(state, choices, isComplete, isValid, results) {
  if (isComplete(state)) { results.push([...state]); return; }
  for (const choice of choices(state)) {
    if (!isValid(state, choice)) continue;   // prune
    state.push(choice);                       // choose
    backtrack(state, choices, isComplete, isValid, results);
    state.pop();                              // unchoose (undo)
  }
}
```

### The 4 ingredients
1. **State** — partial solution being built (often an array).
2. **Choices** — set of next moves at this step.
3. **isValid(state, choice)** — pruning predicate.
4. **isComplete(state)** — accept condition.

### Edge cases / traps
1. **Push a *copy*** to `results`, not the state itself — backtracking mutates state.
2. **Undo on every return.** Missing the `state.pop()` is the #1 bug.
3. **Pruning is the whole game.** Naive backtracking is exponential; good pruning makes it tractable.
4. **Avoid revisiting** — for problems with order-insensitive results (subsets), iterate from `start`, not from 0.
5. **Memoize** if subproblems overlap — backtracking + memo = DP.
6. **Sort first** if pruning depends on monotonicity (e.g., combination sum).
7. **Iterative variant** uses explicit stack of frames — see `iterative-from-recursive.md`.

## Mental Model

Backtracking is **DFS over a decision tree**:

```
   root: state=[]
       ├── choose A → state=[A]
       │      ├── choose B → state=[A,B]
       │      │      └── prune (isValid false) → backtrack
       │      └── choose C → state=[A,C]
       │             └── complete → save → backtrack
       └── choose B → state=[B]
              └── ...
```

```
   At each node:
     if complete → record solution, backtrack
     else for each choice:
       if valid: choose, recurse, unchoose
```

## Why interviewers care

- **Search strategy** — fundamental algorithmic pattern.
- **Pruning intuition** — separates exponential blowup from tractable.
- **State management** — choose/unchoose discipline.

## Common confusion

- **"Backtracking is the same as DFS."** Backtracking *is* DFS — but with an explicit "undo" step. Plain DFS just visits.
- **"You can mutate state without undoing."** Sometimes — if you pass a *copy* down. But that's slower.
- **"Pruning early always helps."** Only if the predicate is cheap and useful — bad pruning makes it slower.
- **"Order doesn't matter."** Permutations: order matters. Subsets/combinations: order doesn't.

## Brute force

Generate all permutations of input then filter. O(n!) regardless of constraints. Backtracking with pruning often gets you orders-of-magnitude better.

## Optimal approach

Identify state, choices, prune-predicate, complete-predicate. Apply template.

## Solution

```js
// 1. Permutations
function permutations(nums) {
  const out = [], state = [], used = new Array(nums.length).fill(false);
  function back() {
    if (state.length === nums.length) { out.push([...state]); return; }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true; state.push(nums[i]);
      back();
      state.pop(); used[i] = false;
    }
  }
  back();
  return out;
}

// 2. Subsets — iterate from `start` to avoid duplicates
function subsets(nums) {
  const out = [], state = [];
  function back(start) {
    out.push([...state]);
    for (let i = start; i < nums.length; i++) {
      state.push(nums[i]);
      back(i + 1);
      state.pop();
    }
  }
  back(0);
  return out;
}

// 3. Combination Sum (with reuse, pruning via sort + early break)
function combinationSum(cands, target) {
  cands.sort((a,b) => a - b);
  const out = [], state = [];
  function back(start, remaining) {
    if (remaining === 0) { out.push([...state]); return; }
    for (let i = start; i < cands.length; i++) {
      if (cands[i] > remaining) break;          // sorted; can't fit anything bigger
      state.push(cands[i]);
      back(i, remaining - cands[i]);            // i, not i+1 — allow reuse
      state.pop();
    }
  }
  back(0, target);
  return out;
}

// 4. N-Queens
function nQueens(n) {
  const out = [], board = [];
  function back(row) {
    if (row === n) { out.push(board.map(c => '.'.repeat(c) + 'Q' + '.'.repeat(n-c-1))); return; }
    for (let col = 0; col < n; col++) {
      if (board.some((c, r) => c === col || Math.abs(c - col) === row - r)) continue;
      board.push(col);
      back(row + 1);
      board.pop();
    }
  }
  back(0);
  return out;
}

// 5. Word Break — backtracking + memo
function wordBreak(s, dict) {
  const set = new Set(dict);
  const memo = new Map();
  function back(i) {
    if (i === s.length) return [['']];
    if (memo.has(i)) return memo.get(i);
    const results = [];
    for (let j = i + 1; j <= s.length; j++) {
      const word = s.slice(i, j);
      if (set.has(word)) {
        for (const rest of back(j)) results.push([word, ...rest].filter(Boolean));
      }
    }
    memo.set(i, results);
    return results;
  }
  return back(0).map(arr => arr.join(' '));
}
```

## Dry run

`permutations([1,2,3])`:

```
back([])
  i=0, state=[1]
    back([1])
      i=1, state=[1,2]
        back([1,2])
          i=2, state=[1,2,3] → complete → push [1,2,3]; pop 3
          i=1 used; i=0 used
        pop 2
      i=2, state=[1,3]
        back([1,3])
          i=1, state=[1,3,2] → complete → push [1,3,2]; pop 2
        pop 3
    pop 1
  i=1, state=[2]
    ... [2,1,3], [2,3,1]
  i=2, state=[3]
    ... [3,1,2], [3,2,1]
```

6 results in canonical order.

## How to think aloud

> "Backtracking template: identify state, choices, validity, completeness. At each step: if complete, record (a copy!); else for each valid choice, push, recurse, pop. The 'pop' is the backtrack — must mirror every push. Pruning is the lever for tractability: sort first if predicate uses monotonicity; break early when a choice can't fit. For overlap (word break, palindrome partitioning), add memoization — that's basically DP."

## Important takeaways

- **Push copy to results.** State is mutated.
- **Choose → recurse → unchoose** mirrored.
- **Pruning** is what makes it tractable.
- **`start` index** for combination-style (avoid duplicates).
- **`used[]` array** for permutation-style.
- **Memo for overlapping subproblems** → DP.
- **Time complexity** depends on pruning; worst case exponential.

## Variants

- **Iterative backtracking** with explicit stack (see `iterative-from-recursive.md`).
- **Branch & bound** — backtrack with a bound function that prunes by best-so-far.
- **DFS with state mutation** vs **DFS with immutable state** (slower but no undo needed).
- **Parallel backtracking** — split decision tree across workers.

## Revision notes

```
function backtrack(state):
  if isComplete(state): record(copy of state); return
  for choice in choices(state):
    if not isValid(state, choice): continue   // prune
    state.push(choice)
    backtrack(state)
    state.pop()                                 // undo

INGREDIENTS:
  state       — partial solution (array)
  choices     — next moves
  isValid     — prune predicate
  isComplete  — accept

TEMPLATES:
  permutations  — used[] flag
  combinations  — start index
  N-queens      — board column-per-row
  word break    — slice + memo

PRUNING:
  sort first → break on monotonicity
  symmetry  → fix order
  bound     → branch & bound

MEMO ⇒ DP equivalent
```
