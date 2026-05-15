# Generate all permutations of an array

## Source
- Canonical recursion / backtracking interview problem.
- LeetCode #46 "Permutations": https://leetcode.com/problems/permutations/
- LeetCode #47 "Permutations II" (with duplicates) is the natural follow-up: https://leetcode.com/problems/permutations-ii/

## Why this question matters in interviews
Permutations is the **first true backtracking problem** every senior candidate is expected to nail in under 15 minutes. It tests three things at once: **recursion with branching**, **state restoration** (the "undo" step that turns a brute-force tree walk into backtracking), and **awareness that n! grows catastrophically** (n=12 already produces 479M permutations). Backend interviewers like it because the same skeleton powers permutation-based test-input generation, scheduling search, configuration enumeration, and brute-force constraint solvers. If you can't write the backtracking template for permutations, you can't write it for N-queens, sudoku, or word-search either — interviewers know this.

## Concepts involved

### Syntax to lock in

Two canonical solutions. Memorize both.

```js
// (A) Pick-and-recurse with a used[] flag set
function permutations(nums) {
  const result = [];
  const current = [];
  const used = new Array(nums.length).fill(false);

  function backtrack() {
    if (current.length === nums.length) {
      result.push([...current]);          // snapshot, not the live array
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true;                     // choose
      current.push(nums[i]);
      backtrack();                        // explore
      current.pop();                      // un-choose (the backtracking step)
      used[i] = false;
    }
  }

  backtrack();
  return result;
}

// (B) Swap-based in-place — generates permutations of nums[start..end]
function permutationsSwap(nums) {
  const result = [];
  const a = nums.slice();

  function backtrack(start) {
    if (start === a.length) {
      result.push(a.slice());
      return;
    }
    for (let i = start; i < a.length; i++) {
      [a[start], a[i]] = [a[i], a[start]];   // swap into position
      backtrack(start + 1);
      [a[start], a[i]] = [a[i], a[start]];   // swap back (restore)
    }
  }

  backtrack(0);
  return result;
}
```

### Runtime / engine behavior
- **Output size is `n!`** — fixed by the problem. Time is `O(n * n!)` because each of the n! results is a length-n array we copy out. You can't beat n! — interviewers test whether you *acknowledge* this rather than try.
- **Call-stack depth is `O(n)`** — only n nested frames at any moment, not n!. V8's default stack is ~10–15k frames, so recursion depth is never the bottleneck here; memory of the result array is.
- **Auxiliary memory:** `current` is `O(n)`, `used` is `O(n)`, output is `O(n * n!)`. The latter dominates.
- **`result.push([...current])`** — the spread copy is mandatory. `result.push(current)` pushes the same live reference n! times; by the time recursion unwinds, every entry is `[]`. Classic interview bug.
- **Swap variant skips the `used[]` array** — it implicitly tracks "what's left to place" via the array suffix `a[start..end]`. Lower constant memory, but it mutates the input order during recursion (restored on backtrack).

### Edge cases
1. **Empty input** — `[]` has exactly one permutation, the empty permutation `[[]]`. Many candidates return `[]`. Wrong.
2. **Single element** — `[1]` returns `[[1]]`.
3. **Duplicates** — `[1, 1, 2]` produces 6 results but only 3 *distinct* permutations. To deduplicate, sort first and skip `if (i > start && a[i] === a[i-1] && !used[i-1])` (LeetCode #47).
4. **n!! catastrophe** — at n=10, you get 3.6M results; n=12 gives 479M (likely OOM in Node). Cap `n <= 8` in any real test.
5. **Reference aliasing** — `result.push(current)` instead of a copy is the #1 bug. Always snapshot.
6. **Output order is implementation-defined** — pick-and-recurse yields lexicographic if input is sorted; swap-based yields a different order. Don't assume.
7. **Immutability of input** — pick-and-recurse leaves `nums` untouched. Swap-based mutates a copy, but if you forget `.slice()`, you mutate the caller's array.

## Brute force approach
"Generate all length-n strings over the alphabet `nums` (n^n combinations) and filter to those with no duplicates." For n=8 that's 16M candidates filtered down to 40K — 400x wasted work. Not acceptable in interview; mention only to dismiss.

## Optimal approach
Backtracking. Build one permutation incrementally; on each recursive call, try every unused element at the next position. The `used[]`/swap trick prunes the search to exactly n! leaves. There is no asymptotically faster algorithm — n! results require n! work. Optimization here means **constant-factor** wins: swap variant avoids the `used[]` array and produces in-place generation.

## Solution (JavaScript)

```js
/**
 * Returns every permutation of `nums` as a fresh array.
 * Time: O(n * n!) — n! results, each of length n.
 * Space: O(n * n!) for output, O(n) call stack.
 */
function permutations(nums) {
  const result = [];
  const current = [];
  const used = new Array(nums.length).fill(false);

  function backtrack() {
    if (current.length === nums.length) {
      result.push([...current]);
      return;
    }
    for (let i = 0; i < nums.length; i++) {
      if (used[i]) continue;
      used[i] = true;
      current.push(nums[i]);
      backtrack();
      current.pop();
      used[i] = false;
    }
  }

  backtrack();
  return result;
}

/**
 * Generator variant — yields permutations one at a time.
 * Critical when n! would OOM but you only need to scan results.
 */
function* permutationsLazy(nums) {
  const a = nums.slice();
  function* go(start) {
    if (start === a.length) {
      yield a.slice();
      return;
    }
    for (let i = start; i < a.length; i++) {
      [a[start], a[i]] = [a[i], a[start]];
      yield* go(start + 1);
      [a[start], a[i]] = [a[i], a[start]];
    }
  }
  yield* go(0);
}
```

## Step-by-step dry run

Input: `permutations([1, 2, 3])`.

State stack (`current`, `used`):
- `[]`, `[F,F,F]` → try i=0
  - `[1]`, `[T,F,F]` → try i=1
    - `[1,2]`, `[T,T,F]` → try i=2
      - `[1,2,3]`, `[T,T,T]` → leaf → push `[1,2,3]`
    - pop → `[1]`, `[T,F,F]`
    - try i=2
      - `[1,3]`, `[T,F,T]` → try i=1
        - `[1,3,2]`, `[T,T,T]` → leaf → push `[1,3,2]`
  - pop → `[]`, `[F,F,F]` → try i=1
  - `[2]`, `[F,T,F]` → ...produces `[2,1,3]`, `[2,3,1]`
  - ...produces `[3,1,2]`, `[3,2,1]`

Final: `[[1,2,3], [1,3,2], [2,1,3], [2,3,1], [3,1,2], [3,2,1]]` — exactly 3! = 6 results.

The key mental model: the recursion tree is n levels deep, branching by "how many unused remain" at each level (n, n-1, n-2, ..., 1). Product = n!. The `pop()`/`used[i]=false` lines are what reset state so a sibling branch starts clean.

## Important takeaways

**Syntax to memorize**
- `result.push([...current])` — **snapshot**, never push the live array.
- `used[]` flag flip pattern: set true → recurse → set false. Always paired.
- Swap variant: `[a[i], a[j]] = [a[j], a[i]]` twice — once to choose, once to restore.
- Base case: `current.length === nums.length`, not `nums.length === 0`.

**Patterns to reuse**
- The "choose / explore / un-choose" triplet is **the backtracking template**. It's the same skeleton for: subsets (power set), combinations, N-queens, sudoku, word-search-in-grid, generate-parentheses. Lock this template in once and you have 5 problems for free.
- `used[]` flag-set pattern works any time you can't mutate input. Swap pattern works when you can.

**Common mistakes**
- Pushing `current` instead of `[...current]` → all entries become `[]`.
- Forgetting `used[i] = false` after the recursive call → only one permutation emitted.
- Trying to memoize permutations — there's nothing to memoize. Every leaf is unique. Memoization is for **counting** permutations, not generating them.
- Using `nums.splice(i, 1)` then `nums.unshift` — works but mutates input and is O(n) per call; pessimal constant factor.
- Returning permutations for n > 10 in production. Interviewers will ask "what if n = 20?" Answer: "I'd switch to lazy generation (yield) and likely reframe the problem — n=20 is 2.4 quintillion permutations; the user doesn't want a list."

**Related questions**
- Power set / all subsets (`09-recursion/power-set.md`)
- Combinations (n choose k)
- Generate parentheses (`09-recursion/generate-parentheses.md`)
- N-queens, sudoku solver, word search

## Variants

1. **Permutations II (with duplicates)** — sort input, skip `if (i > 0 && nums[i] === nums[i-1] && !used[i-1])`. The `!used[i-1]` check ensures duplicates only fire in their canonical "left-most first" order, eliminating duplicate output without a `Set`.

2. **k-permutations (P(n, k))** — change the base case to `current.length === k` to stop early. Output size: `n! / (n-k)!`.

3. **Next permutation in lexicographic order (LC #31)** — O(n) iterative algorithm: find longest non-increasing suffix, swap pivot with smallest greater in suffix, reverse suffix. Important because it lets you iterate permutations in O(n) per step rather than O(n!) total memory.

4. **Streaming with generator** — return `function*` that `yield`s each permutation. Caller can `break` out of `for...of` after finding the first valid one — saves memory when search space is huge but answer is shallow.

## Revision notes

> **permutations — 60 second recap**
> - Output size **n!** — `n=10` is 3.6M, `n=12` is 479M (OOM risk).
> - Backtracking template: **choose → explore → un-choose**.
> - Two solutions:
>   - (A) `used[]` flag set + `current[]` builder (clean, non-mutating).
>   - (B) Swap-based in-place — lower constant memory, mutates a copy.
> - **Trap 1:** `result.push(current)` instead of `[...current]` → all entries empty.
> - **Trap 2:** forgetting to un-set `used[i]` → emits only one perm.
> - Time `O(n · n!)`, stack `O(n)`, output dominates space.
> - For huge n: switch to generator (`function*` + `yield`) — lazy emission.
> - Duplicates → sort + skip rule (LC #47). Next-perm → O(n) iterative.
