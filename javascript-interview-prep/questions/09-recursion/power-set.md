# Generate the power set (all subsets) of an array

## Source
- Canonical recursion + bitmask interview problem.
- LeetCode #78 "Subsets": https://leetcode.com/problems/subsets/
- LeetCode #90 "Subsets II" (with duplicates) is the natural follow-up: https://leetcode.com/problems/subsets-ii/

## Why this question matters in interviews
Power set is the **simplest non-trivial recursion problem that has two genuinely different solutions** — include/exclude recursion and bitmask iteration. Senior interviewers love it because the *follow-up* "give me a second solution" instantly separates rote candidates from people who actually understand the structure (2^n subsets ↔ n-bit numbers). The bitmask variant is also a load-bearing technique in real backend work: feature-flag combinations, permission matrix enumeration, RBAC role-fan-out testing, and subset-sum / knapsack DP. If `n <= 20` you can enumerate every subset by iterating `for (let mask = 0; mask < 1 << n; mask++)`. Knowing this is a senior-level move.

## Concepts involved

### Syntax to lock in

Two canonical solutions. Memorize both.

```js
// (A) Include/exclude recursion
function powerSet(nums) {
  const result = [];
  function backtrack(index, current) {
    if (index === nums.length) {
      result.push([...current]);
      return;
    }
    // exclude nums[index]
    backtrack(index + 1, current);
    // include nums[index]
    current.push(nums[index]);
    backtrack(index + 1, current);
    current.pop();                    // restore
  }
  backtrack(0, []);
  return result;
}

// (B) Bitmask iteration — no recursion at all
function powerSetBitmask(nums) {
  const n = nums.length;
  const result = [];
  for (let mask = 0; mask < (1 << n); mask++) {   // 2^n iterations
    const subset = [];
    for (let i = 0; i < n; i++) {
      if (mask & (1 << i)) subset.push(nums[i]);  // bit i set ⇒ include
    }
    result.push(subset);
  }
  return result;
}
```

### Runtime / engine behavior
- **Output size is `2^n`** — fixed. Total work is `O(n · 2^n)` because each subset has average length `n/2` and we copy it out.
- **Recursion variant:** stack depth `O(n)`, branching factor 2, exactly `2^n` leaves. Tree is a perfect binary tree of height n.
- **Bitmask variant:** zero recursion. Uses the fact that there are exactly `2^n` n-bit integers, each corresponding to a unique subset (bit i = "include element i").
- **`1 << n` for n >= 32** breaks: JS bitwise ops are 32-bit signed. For `n=31` `1 << 31` is `-2147483648`. Use `2 ** n` or `BigInt` for `n >= 31`. (Realistically the loop OOMs first — `2^30` subsets is already infeasible.)
- **`mask & (1 << i)`** is `0` or non-zero, not strictly `true`/`false`. Use as truthy in an `if`, or compare `!== 0` for clarity.

### Edge cases
1. **Empty input** — `[]` has exactly one subset, the empty set `[[]]`. Don't return `[]`.
2. **Single element** — `[1]` returns `[[], [1]]`.
3. **Duplicates** — `[1, 1, 2]` produces 8 subsets but only 6 *distinct* (LC #90). To dedupe: sort, then skip the include branch when `nums[i] === nums[i-1]` and the previous wasn't included.
4. **Order of output** — include/exclude gives `[]` first; bitmask gives `[]` first (mask=0). But the **intermediate ordering differs**. Don't assume.
5. **n > 25** is operationally infeasible — `2^25` ≈ 33M subsets, several GB of arrays. Cap any test at `n <= 20`.
6. **Reference aliasing** — same trap as permutations: `result.push(current)` shares the live array. Always `[...current]` or build a fresh one (bitmask variant does this naturally).
7. **Bit shift gotcha at n=32** — `1 << 32` in JS is `1`, not `2^32`. Bitwise ops mod by 32. Don't use bitmask for `n >= 31`.

## Brute force approach
"Generate all permutations and dedupe to subsets." Wastes `n!` work to produce `2^n` results — for n=10 that's 3.6M perms reduced to 1024 subsets, ~3500x wasted. Mention only to dismiss.

## Optimal approach
Two equally optimal solutions at `O(n · 2^n)`:

**Recursive** is structural — clearly mirrors "for each element, two choices: in or out." Best for explanation and for problems where you need to *prune* (e.g., subsets summing to a target).

**Bitmask** is iterative, has no stack overhead, and is the canonical way to enumerate subsets for small `n` in competitive programming and backend feature-flag work. It also makes "the k-th subset" a constant-time lookup: just write `k` in binary.

Show both. State that you'd pick recursion when the subset has a *constraint* (so you can prune) and bitmask when you genuinely need all `2^n`.

## Solution (JavaScript)

```js
/**
 * Power set via include/exclude recursion.
 * Time: O(n · 2^n).  Space: O(n · 2^n) output, O(n) stack.
 */
function powerSet(nums) {
  const result = [];
  function backtrack(index, current) {
    if (index === nums.length) {
      result.push([...current]);
      return;
    }
    backtrack(index + 1, current);          // exclude
    current.push(nums[index]);
    backtrack(index + 1, current);          // include
    current.pop();
  }
  backtrack(0, []);
  return result;
}

/**
 * Power set via bitmask iteration.
 * Best when you need O(1) random access to the k-th subset.
 */
function powerSetBitmask(nums) {
  const n = nums.length;
  if (n >= 31) throw new RangeError('use BigInt or recursion for n >= 31');
  const total = 1 << n;
  const result = new Array(total);
  for (let mask = 0; mask < total; mask++) {
    const subset = [];
    for (let i = 0; i < n; i++) {
      if (mask & (1 << i)) subset.push(nums[i]);
    }
    result[mask] = subset;
  }
  return result;
}

/**
 * Lazy generator — yields one subset at a time. Useful when 2^n
 * would OOM but you only need to scan or filter.
 */
function* powerSetLazy(nums) {
  const n = nums.length;
  const current = [];
  function* go(i) {
    if (i === n) {
      yield current.slice();
      return;
    }
    yield* go(i + 1);
    current.push(nums[i]);
    yield* go(i + 1);
    current.pop();
  }
  yield* go(0);
}
```

## Step-by-step dry run

Input: `powerSet([1, 2, 3])`.

Recursion tree (exclude is left, include is right):
```
                          (i=0, [])
               exclude /            \ include
              (i=1, [])              (i=1, [1])
         excl /     \ incl       excl /      \ incl
    (i=2,[])      (i=2,[2])    (i=2,[1])   (i=2,[1,2])
    excl/ \incl   excl/ \incl  excl/ \incl excl/ \incl
   []   [3]      [2] [2,3]    [1] [1,3]   [1,2] [1,2,3]
```

Output: `[[], [3], [2], [2,3], [1], [1,3], [1,2], [1,2,3]]` — exactly 2³ = 8 subsets.

Now the bitmask variant for the same input, with `mask` from 0 to 7:

| mask (binary) | bits set | subset |
|--|--|--|
| 0 (000) | — | `[]` |
| 1 (001) | i=0 | `[1]` |
| 2 (010) | i=1 | `[2]` |
| 3 (011) | i=0,1 | `[1, 2]` |
| 4 (100) | i=2 | `[3]` |
| 5 (101) | i=0,2 | `[1, 3]` |
| 6 (110) | i=1,2 | `[2, 3]` |
| 7 (111) | i=0,1,2 | `[1, 2, 3]` |

Same 8 subsets, **different order**. Same `O(2^n)` count.

## Important takeaways

**Syntax to memorize**
- `(1 << n)` for the loop bound. `mask & (1 << i)` for "is bit i set."
- Include/exclude order matters for output order — recurse-then-modify-then-recurse keeps the inserts/pops paired.
- Always `result.push([...current])`, never the live array.

**Patterns to reuse**
- Bitmask enumeration is the foundation of **subset-DP** (e.g., Traveling Salesman O(n² · 2^n), bitmask DP for assignment problems). Lock the `for (mask = 0; mask < (1 << n); mask++)` skeleton in.
- Include/exclude recursion is the parent template for: combinations, partition problems, subset-sum, expression-add-operators, palindrome-partition.
- Counting trick: "number of subsets containing element i" = `2^(n-1)`. Number containing both i and j = `2^(n-2)`. These come up in expected-value questions.

**Common mistakes**
- Returning `[]` for empty input — should be `[[]]`.
- Pushing `current` instead of `[...current]` — every entry ends up empty.
- Using bitmask with `n >= 31` — `1 << 31` flips sign in JS.
- Forgetting `current.pop()` after the include branch — every subsequent subset stays polluted.
- Claiming bitmask is "asymptotically faster" — it isn't. Both are `O(n · 2^n)`. The bitmask variant just has lower constant factors and no recursion overhead.

**Related questions**
- Permutations (`09-recursion/permutations.md`) — n! vs 2^n; permutations branch by position, subsets branch by element.
- Combinations (n choose k) — restrict subset size in the same recursion.
- Subset sum / partition equal-sum — same template with a sum-tracking parameter and pruning.
- Bitmask DP (TSP, assignment).

## Variants

1. **Subsets II (with duplicates)** — sort input, then in the include/exclude tree skip the include branch if `i > 0 && nums[i] === nums[i-1] && !includedPrev`. Eliminates duplicate subsets without a `Set<string>`.

2. **K-th subset in O(n)** — given index `k`, return the k-th subset directly: iterate bits of `k`, push `nums[i]` for each set bit. No need to materialize the full power set. Senior-level answer to "I only need the 1000th subset, don't generate them all."

3. **Subsets of a fixed size k** — change the recursion's terminal condition to `current.length === k`. Output size: `C(n, k)` (binomial coefficient), not `2^n`.

4. **Subset with constraint** (e.g., sums to target) — same skeleton, prune branches when `currentSum > target` or `currentSum + remainingSum < target`. Pruning is why recursion beats bitmask in practice for constrained problems.

5. **Set.prototype representation** — instead of arrays, build `Set` objects per subset. Same complexity but useful when downstream needs `O(1)` membership.

## Revision notes

> **power set — 60 second recap**
> - Output size **2^n**. n=20 is 1M subsets, n=25 OOMs.
> - Two solutions — know both:
>   - (A) Include/exclude recursion: depth `n`, branching 2.
>   - (B) Bitmask: `for (mask = 0; mask < (1 << n); mask++)`; bit i = element i.
> - Both are `O(n · 2^n)`. Bitmask has lower constant, no stack.
> - **Trap 1:** empty input → return `[[]]`, not `[]`.
> - **Trap 2:** `1 << 31` flips sign — bitmask only works for `n < 31`.
> - **Trap 3:** `result.push(current)` instead of `[...current]` → all entries empty.
> - K-th subset = `O(n)` lookup via binary digits of k — don't materialize all 2^n if you only need one.
> - Duplicates → sort + skip-include rule (LC #90).
> - Use recursion when you can **prune** (constraint), bitmask when you genuinely want all 2^n.
