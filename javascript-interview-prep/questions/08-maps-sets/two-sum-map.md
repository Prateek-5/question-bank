# Two-Sum with a Map (O(n))

## Source
- LeetCode #1 "Two Sum" — the most-asked interview problem on the planet: https://leetcode.com/problems/two-sum/
- Cracking the Coding Interview Ch. 11 (Arrays & Hash Tables), Frontend Masters, NeetCode 150.

## Why this question matters in interviews
Two-Sum is the **canonical hash-trick problem** — the one that teaches you "trade space for time with a Map." Every senior interviewer expects you to identify it instantly, articulate the O(n²) → O(n) jump, and write the single-pass Map solution in under five minutes. As a backend engineer it generalizes to: finding duplicate transactions, matching buy/sell orders in an order book, deduplicating webhook IDs, and resolving foreign keys in a batch. Failing this one signals weak fundamentals; nailing it cleanly is the price of admission.

## Concepts involved

### Syntax to lock in
```js
// Single-pass with Map<complement, index>
function twoSum(nums, target) {
  const seen = new Map();              // value -> index
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (seen.has(need)) return [seen.get(need), i];
    seen.set(nums[i], i);              // record AFTER checking
  }
  return [];
}
```

### Runtime / engine behavior
- `Map` lookups (`has`, `get`, `set`) are **amortized O(1)**. V8 backs Map with a hash table that supports any key type — strings, numbers, objects, NaN — using SameValueZero equality.
- Using a plain object `{}` is tempting but has two traps: numeric keys get stringified (`obj[5]` and `obj['5']` collide), and lookups must walk the prototype chain unless you use `Object.create(null)`. Map sidesteps both.
- For `nums.length = n`, total work is `n` map writes + at most `n` map reads = **2n ops, O(n) time, O(n) space**.

### Edge cases (these are the interview traps)
1. **Duplicates with target = 2x** — `[3, 3]`, `target = 6` must return `[0, 1]`. Works only if you check `seen.has(need)` **before** `seen.set(nums[i], i)` — otherwise the same index gets returned twice.
2. **No solution exists** — return `[]` (or `null`) by spec; some interviewers want a thrown error. Clarify.
3. **Negative numbers / zero** — `[0, 0]`, `target = 0` is a classic gotcha. Map handles `0` and `-0` as the same key (SameValueZero); fine for integers.
4. **Floating point** — `[0.1, 0.2]`, `target = 0.3` will fail because `0.3 - 0.1 !== 0.2` in IEEE 754. Out of scope for integer input but worth flagging.
5. **Multiple valid pairs** — spec says return *any one*. Don't try to enumerate all unless asked (different problem).
6. **Sorted input variant** — if interviewer says "sorted," switch to two-pointer (O(n) time, **O(1) space**) — see Variants.
7. **Returning values vs indices** — re-read the prompt. LeetCode #1 returns indices; some variants want the values.
8. **Empty / single-element input** — return `[]` immediately; don't crash on a 0-element loop.

## Brute force approach
Nested loop: for every `i`, scan every `j > i` and check `nums[i] + nums[j] === target`. **O(n²) time, O(1) space.** Acceptable only as a baseline you immediately discard. State it, then say "we can do O(n) with a hash map" and pivot.

## Optimal approach
One pass through the array. For each element `nums[i]`, ask: "have I already seen `target - nums[i]`?" If yes, the pair is `[seen.get(complement), i]`. If no, record `nums[i] → i` and continue. The Map turns the "have I seen X?" question from O(n) (linear scan) into O(1) (hash lookup). Net: **O(n) time, O(n) space**. The space is the unavoidable cost of the speedup — that trade is the entire point of the question.

## Solution (JavaScript)

```js
/**
 * Return indices of the two numbers in `nums` that sum to `target`.
 * Assumes exactly one solution exists.
 * @param {number[]} nums
 * @param {number} target
 * @returns {[number, number] | []}
 */
function twoSum(nums, target) {
  const seen = new Map();              // value -> index of that value

  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];

    // Check BEFORE inserting — handles duplicates like [3,3] target=6.
    if (seen.has(complement)) {
      return [seen.get(complement), i];
    }
    seen.set(nums[i], i);
  }

  return [];                           // no pair found
}
```

## Step-by-step dry run

Input: `nums = [2, 7, 11, 15]`, `target = 9`

| i | nums[i] | complement | seen.has? | action                    | seen after            |
|---|---------|------------|-----------|---------------------------|-----------------------|
| 0 | 2       | 7          | no        | seen.set(2, 0)            | `{2→0}`               |
| 1 | 7       | 2          | **yes**   | return `[seen.get(2), 1]` | —                     |

Output: `[0, 1]`. Done in 2 iterations.

Duplicate input: `nums = [3, 3]`, `target = 6`

| i | nums[i] | complement | seen.has? | action                    | seen after            |
|---|---------|------------|-----------|---------------------------|-----------------------|
| 0 | 3       | 3          | no        | seen.set(3, 0)            | `{3→0}`               |
| 1 | 3       | 3          | **yes**   | return `[seen.get(3), 1]` | —                     |

Output: `[0, 1]`. The check-before-insert order is what makes this work — flipping the two lines breaks duplicates.

## Important takeaways

**Syntax to memorize**
- `const seen = new Map()` — not `{}`.
- `seen.has(k)` / `seen.get(k)` / `seen.set(k, v)` — three methods, no surprises.
- **Check first, then insert** — order matters for duplicates.

**Patterns to reuse**
- "Map of value → index" is the hash-trick skeleton. Same pattern powers: **first-non-repeating-char** (char → count), **longest-substring-without-repeat** (char → last index), **subarray-sum-equals-k** (prefixSum → count), **group-anagrams** (key → bucket).
- "Single pass + complement lookup" generalizes: **3Sum** wraps a two-pointer around it; **4Sum** wraps another loop. The Map version is the inner kernel.

**Common mistakes**
- Using `{}` instead of `Map` — works for small int keys but breaks on negative numbers as keys in some patterns, and stringifies everything.
- Inserting before checking → duplicate values fail.
- Two nested loops with a Map "for safety" — defeats the purpose; it's still O(n²).
- Returning the values instead of indices (re-read the prompt).
- Forgetting the no-solution case — uncaught return leaks `undefined`.

**Big-O comparison**
| Approach              | Time       | Space | Notes                          |
|-----------------------|------------|-------|--------------------------------|
| Nested loop           | O(n²)      | O(1)  | Baseline only                  |
| Sort + two-pointer    | O(n log n) | O(1)* | *if sort is in-place; loses original indices |
| **Map (single pass)** | **O(n)**   | **O(n)** | The expected answer         |

The sort+two-pointer trade is worth mentioning: it wins on **space** but loses on **time** and **destroys the original indices**, so it's only acceptable when the problem says "return values" or "input is already sorted."

**Related questions**
- 3Sum / 4Sum (LeetCode #15, #18)
- Two Sum II — sorted input (LeetCode #167) — two-pointer variant
- Subarray Sum Equals K (LeetCode #560) — Map of prefix sums
- Longest Substring Without Repeating Characters (LeetCode #3)

## Variants

1. **Sorted-input variant (Two Sum II)** — input is sorted ascending. Use two pointers `lo=0, hi=n-1`; if `nums[lo]+nums[hi] < target` move `lo++`, if `>` move `hi--`. **O(n) time, O(1) space**. Beats the Map on space — the right answer when the array is sorted.

2. **Return all pairs** — different problem. Don't return on first hit; push `[seen.get(complement), i]` into a result array and **continue**. Watch for duplicate pairs if the array has repeated values — dedupe with a Set of canonicalized pair keys.

3. **K-Sum generalization** — `kSum(nums, target, k)` recursively reduces to `(k-1)Sum` with target adjusted. The base case `k=2` is the Map version above. Pattern used to solve 3Sum, 4Sum cleanly.

4. **Streaming / online variant** — numbers arrive one at a time over a stream; report a pair the moment one is possible. Same Map, but you never finish — `set` runs forever. Mention LRU eviction for bounded memory.

## Revision notes

> **two-sum-map — 60 second recap**
> - Single pass + `Map<value, index>`.
> - For each `nums[i]`: compute `complement = target - nums[i]`. If `seen.has(complement)`, return `[seen.get(complement), i]`. Else `seen.set(nums[i], i)`.
> - **Check before insert** — handles `[3,3] target=6`.
> - **O(n) time, O(n) space**. Beats nested-loop O(n²).
> - Sorted input → two-pointer O(n) time, **O(1) space** instead.
> - Use `Map`, not `{}` — avoids stringification + prototype chain.
> - Pattern generalizes to: 3Sum, prefix-sum-equals-k, longest-substring-without-repeat.
