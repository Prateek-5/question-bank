# Richest Customer Wealth — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Richest_Customer_Wealth.md`](../Richest_Customer_Wealth.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/richest-customer-wealth/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~8 minutes. The problem is trivial — sum each row, track the largest sum. But it teaches **the running-max idiom**, which you'll reuse in every "find the best X among N candidates" problem.

**Map of this file (8 short sections):**

1. Read the problem
2. 2D matrix layout refresher
3. The natural approach: row-sum + running max
4. The running-max idiom in detail
5. Code
6. Trace it
7. Common pitfalls
8. The shape — running-max appears everywhere

---

## 1. Read the problem

You're given a 2D matrix `accounts` of size `m × n`.

- `accounts[i][j]` is how much money customer `i` has in bank account `j`.
- A customer's **wealth** is the sum of all their accounts.
- Return the wealth of the **richest** customer.

Example:

```
accounts =
  [1, 5]      customer 0
  [7, 3]      customer 1
  [3, 5]      customer 2
```

- Customer 0's wealth = 1 + 5 = 6
- Customer 1's wealth = 7 + 3 = 10
- Customer 2's wealth = 3 + 5 = 8

Richest customer's wealth = **10**.

Note: we return the **value of the maximum**, not the customer's index. The problem just wants the number.

---

## 2. 2D matrix layout refresher

> **Mini-refresher: how a 2D array is laid out.**
>
> A 2D array is an "array of arrays" — each outer element is itself a row.
>
> ```
> accounts = [
>   [1, 5],       ← row 0 (customer 0)
>   [7, 3],       ← row 1 (customer 1)
>   [3, 5]        ← row 2 (customer 2)
> ]
> ```
>
> So `accounts[1]` is the row `[7, 3]`. `accounts[1][0]` is the first value in that row, `7`.
>
> **First subscript = row (customer here). Second subscript = column (account number).**
>
> `accounts.size()` returns the number of rows (m = 3 above). `accounts[0].size()` returns the number of columns (n = 2). In this problem both dimensions are independent; rows can have any width as long as it's consistent.
>
> Already comfortable with 2D matrix indexing? Skim and move on.

---

## 3. The natural approach: row-sum + running max

For each row, compute the row's sum (customer's wealth). Track the largest sum we've seen as we go.

```
maxWealth = 0
for each row in accounts:
    wealth = sum of values in row
    if wealth > maxWealth:
        maxWealth = wealth
return maxWealth
```

That's it. The problem doesn't have an algorithmic trick. The cleverness comes from how cleanly you compute "wealth" and "max."

- Per row: O(n) additions.
- Across rows: O(m) iterations.
- **Total: O(m · n)** — touches every cell exactly once.

There's no way to do better; the problem requires examining every cell at least once.

---

## 4. The running-max idiom in detail

> **Mini-refresher: the running-max (or running-min) idiom.**
>
> When you need to find the maximum (or minimum) value across a sequence of items, the standard pattern is:
>
> ```
> best = SENTINEL                              # see below for what SENTINEL is
> for each item in the sequence:
>     compute the item's "score"
>     if score > best:
>         best = score
> return best
> ```
>
> The trick is **picking `SENTINEL` correctly**. Three common choices:
>
> 1. **`SENTINEL = INT_MIN`** (or `-Infinity`). Works for any input, including arrays where every score is negative. Most defensive.
>
> 2. **`SENTINEL = 0`** (only when scores are guaranteed non-negative). Cleaner if you know the constraint.
>
> 3. **`SENTINEL = first item's score`**, then start the loop from index 1. Avoids needing a sentinel at all, but adds an edge case for empty input.
>
> For Richest Customer Wealth, the problem guarantees `accounts[i][j] ≥ 0`, so the smallest possible wealth is 0 (a customer with all-zero accounts). Choosing `maxWealth = 0` is safe and simple — even an empty row produces wealth 0, which doesn't break the running max.

Apply this to our problem: each customer's wealth is the "score"; the running max is `maxWealth`.

---

## 5. Code

**C++ — explicit loop:**

```cpp
int maximumWealth(vector<vector<int>>& accounts) {
    int maxWealth = 0;
    for (const auto& row : accounts) {           // each row = one customer
        int wealth = 0;
        for (int x : row) wealth += x;            // sum the row
        if (wealth > maxWealth) maxWealth = wealth;
    }
    return maxWealth;
}
```

**C++ — using STL:**

```cpp
int maximumWealth(vector<vector<int>>& accounts) {
    int maxWealth = 0;
    for (const auto& row : accounts) {
        int wealth = accumulate(row.begin(), row.end(), 0);
        maxWealth = max(maxWealth, wealth);
    }
    return maxWealth;
}
```

> **Mini-refresher: `std::accumulate` (C++).**
>
> `accumulate(begin, end, init)` returns `init + *begin + *(begin+1) + ... + *(end-1)`. With `init = 0` it just sums the range.
>
> Why is this useful? It saves a few lines and signals intent ("this is a sum reduction") to the reader. For a quick row sum, it's idiomatic C++.

**Python:**

```python
def maximumWealth(accounts):
    return max(sum(row) for row in accounts)
```

Two operations: `sum(row)` for each customer, `max(...)` over all the sums. The generator expression keeps memory O(1) — no full list of sums materialized.

**JavaScript:**

```javascript
function maximumWealth(accounts) {
    return Math.max(...accounts.map(row => row.reduce((a, b) => a + b, 0)));
}
```

`map` produces an array of row sums; `Math.max(...)` finds the largest.

---

## 6. Trace it

`accounts = [[1, 5], [7, 3], [3, 5]]`.

```
maxWealth = 0.

Iter 1: row = [1, 5].
        wealth = 0 + 1 + 5 = 6.
        6 > 0 → maxWealth = 6.

Iter 2: row = [7, 3].
        wealth = 0 + 7 + 3 = 10.
        10 > 6 → maxWealth = 10.

Iter 3: row = [3, 5].
        wealth = 0 + 3 + 5 = 8.
        8 > 10? No → maxWealth stays at 10.

Return 10.  ✓
```

The running max climbed from 0 → 6 → 10 → 10 across the rows.

---

## 7. Common pitfalls

1. **Initializing `maxWealth = INT_MAX` (or a very large number) by mistake.** Some people copy idioms from finding *minimums*. If you initialize wrong, the `>` comparison can fail and you return the sentinel itself. Use `INT_MIN`, `0`, or "first row's wealth" depending on the constraint.

2. **Iterating `accounts.size()` columns by mistake.** If the matrix is `m × n` and you write `for (int j = 0; j < accounts.size(); j++)` thinking it's columns, you're iterating rows. Use `accounts[0].size()` for the column dimension, or `accounts[i].size()` to be safe with jagged rows (not the case here, but a good habit).

3. **Returning the customer's INDEX instead of the wealth.** Re-read the problem. This one wants the wealth value. Some sibling problems want the index.

4. **Using `accumulate` with the wrong starting value.** `accumulate(row.begin(), row.end(), 0)` is correct. If you write `accumulate(row.begin(), row.end(), 0.0)` (double zero), C++ deduces a double sum, which is fine for integers but a subtle code smell. Match types.

5. **Overflow on summation.** If `accounts[i][j]` is large and `n` is large, an int row-sum could overflow. For LeetCode #1672 the constraints are small, but in general use `long long` for sums of arbitrary integer arrays.

---

## 8. The shape — running-max appears everywhere

The "compute a per-item score, track the best" pattern is THE most universal idiom in algorithm problems:

| Problem | Per-item score | "Best" choice |
|---|---|---|
| **This problem** (Richest Customer) | row sum | max |
| Maximum Subarray | running running-sum (with Kadane reset) | max |
| Best Time to Buy and Sell Stock | `price[i] - min_so_far` | max |
| Container With Most Water | `(r - l) × min(h[l], h[r])` | max |
| Largest Rectangle in Histogram | rectangle area at each "popped" bar | max |
| Minimum in Rotated Array | element value | min |
| Find Peak Element | element value (with neighbor constraints) | max (peak) |

**Pattern to internalize:**

> "Loop over candidates. For each, compute its score in O(1) (or O(k), if reading some local data). Compare to the running best and update. Return the best."

The variations across problems are:

- **What's the score?** (sum, product, length, area, count, …)
- **What's "best"?** (max, min, longest, smallest, …)
- **How much state do you carry?** (just a number, a window, a stack, …)

But the skeleton — *iterate, score, compare, update* — is constant. Once you internalize this skeleton, half of array problems become "fill in the blanks."

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking for the **maximum / minimum / best of something across a sequence**, before reaching for sort + index-0, ask:
>
> > **"Can I compute each candidate's score in O(1) per item and maintain a running best in a single pass?"**
>
> If yes, you have an O(n) algorithm. Sorting (O(n log n)) is rarely needed when you only want the single best.

---

## Cross-references

- **Reference card (post-mastery):** [`../Richest_Customer_Wealth.md`](../Richest_Customer_Wealth.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) (prefix sum — different aggregation pattern over arrays)
  - Coming later: Max_Chunks_To_Make_Sorted (running max with a clever invariant)
