# Number of Good Pairs

**Problem Link:**
<a href="https://leetcode.com/problems/number-of-good-pairs/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-good-pairs/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: Define "Good Pair"

Given an integer array `nums`, a pair `(i, j)` is **good** if `nums[i] == nums[j]` and `i < j`.

Return the count of good pairs.

Example: `nums = [1, 2, 3, 1, 1, 3]`.

Good pairs:
- Indices (0, 3): nums[0] = nums[3] = 1. ✓
- Indices (0, 4): nums[0] = nums[4] = 1. ✓
- Indices (3, 4): nums[3] = nums[4] = 1. ✓
- Indices (2, 5): nums[2] = nums[5] = 3. ✓

Count: 4.

----------------------------------------

## Step 2: Brute Force

Two nested loops. For each pair (i, j) with i < j, check if nums[i] == nums[j]. Count matches.

O(n²). Fine for small n.

----------------------------------------

## Step 3: Group By Value — O(n)

For each distinct value `v`, count how many times it appears. If v appears `c` times, the number of good pairs among them is `C(c, 2) = c * (c - 1) / 2`.

Total = sum over values of `C(count[v], 2)`.

```
count = frequency map of nums
total = 0
for c in count.values():
    total += c * (c - 1) / 2
return total
```

O(n) to count + O(distinct values) to sum. Total O(n).

For `[1, 2, 3, 1, 1, 3]`: count = {1:3, 2:1, 3:2}. Pairs: C(3,2) + C(1,2) + C(2,2) = 3 + 0 + 1 = **4**. ✓

----------------------------------------

## Step 4: One-Pass Counting Trick

Even slicker: as we iterate, for each element, count how many times we've **already seen** that value. That's the number of new good pairs this element contributes.

```
count = {}
total = 0
for x in nums:
    total += count.get(x, 0)   # each previous occurrence gives a good pair (prev, current)
    count[x] = count.get(x, 0) + 1
return total
```

Single pass, O(n) time, O(distinct values) space.

Elegance check: for `[1, 2, 3, 1, 1, 3]`:
- x=1: count[1] = 0. total += 0. count[1] = 1.
- x=2: count[2] = 0. total += 0. count[2] = 1.
- x=3: count[3] = 0. total += 0. count[3] = 1.
- x=1: count[1] = 1. total += 1 = 1. count[1] = 2.
- x=1: count[1] = 2. total += 2 = 3. count[1] = 3.
- x=3: count[3] = 1. total += 1 = 4. count[3] = 2.

Total: **4**. ✓

----------------------------------------

## Step 5: Why the Running-Count Works

For each new occurrence of value v, the number of new good pairs it creates is **exactly the count of previous v's**. Why? Because the current index j paired with each previous index i (same value) gives a good pair (i, j). There are as many such previous indices as count[v] before incrementing.

Summing across all elements gives the total pair count. Mathematically equivalent to `sum of C(c, 2)`.

----------------------------------------

## Step 6: Name It

**Pair counting via grouping / running counts.** Same skeleton applied to:
- Count pairs with XOR equal to K.
- Count pairs with sum divisible by K.
- Count inversions (harder — needs merge sort).
- Count triplets satisfying some property.

The general idea: "for each element, count pairs it closes with previous matches." Usually one pass with a hashmap.

----------------------------------------

## Step 7: Complexity

Time: **O(n)**.
Space: O(distinct values) — O(n) worst case.

----------------------------------------

## Step 8: C++ Implementation

**Running-count version (single pass):**

```cpp
int numIdenticalPairs(vector<int>& nums) {
    unordered_map<int, int> count;
    int total = 0;
    for (int x : nums) {
        total += count[x];   // previous occurrences pair with current
        count[x]++;
    }
    return total;
}
```

Five lines. Running-count is the simplest version.

**Group-then-count version:**

```cpp
int numIdenticalPairs(vector<int>& nums) {
    unordered_map<int, int> count;
    for (int x : nums) count[x]++;
    int total = 0;
    for (auto& [val, c] : count) total += c * (c - 1) / 2;
    return total;
}
```

Same asymptotic, slightly more code.

----------------------------------------

## Step 9: Follow-up Questions

- **Good pairs with a max distance constraint (j - i ≤ k).** Use sliding window + hashmap.
- **Good triples (i < j < k with nums[i] == nums[j] == nums[k]).** Sum of C(c, 3).
- **Pairs with nums[i] != nums[j].** Total pairs = C(n, 2); subtract good pairs.
- **Pairs with |nums[i] - nums[j]| = k.** Hashmap counting with k-offset lookup.
- **Streaming input.** Running-count adapts naturally.
- **Why does running-count always equal C(c, 2)?** Combinatorially: each pair (i, j) with same value counted exactly once when j arrives and sees i already in count.
