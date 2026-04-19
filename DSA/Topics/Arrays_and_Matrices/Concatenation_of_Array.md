# Concatenation of Array

**Problem Link:**
https://leetcode.com/problems/concatenation-of-array/

**Topic:**
Arrays & Matrices

----------------------------------------

## Step 1: Understand the Task

Given an array `nums` of length n, return a new array of length 2n where:
- `result[i] = nums[i]` for `0 ≤ i < n`.
- `result[i + n] = nums[i]` for `0 ≤ i < n`.

In other words, return `nums` concatenated with itself.

Example: `nums = [1, 2, 1]`. Return `[1, 2, 1, 1, 2, 1]`.

This is a "warm-up" type problem — the real point is practicing basic array manipulation.

----------------------------------------

## Step 2: Just Allocate and Copy

Allocate a result of size 2n. Walk through nums once, and set `result[i]` and `result[i+n]` simultaneously.

```
result = new array of size 2n
for i in 0..n-1:
    result[i] = nums[i]
    result[i + n] = nums[i]
return result
```

O(n) time, O(n) space.

Alternatively: copy nums to result, then append again.

----------------------------------------

## Step 3: C++ Idioms

C++ has a few elegant ways:

**Option A: explicit loop.**
```cpp
vector<int> result(2 * nums.size());
for (int i = 0; i < (int)nums.size(); ++i) {
    result[i] = nums[i];
    result[i + nums.size()] = nums[i];
}
```

**Option B: construct via copy.**
```cpp
vector<int> result(nums.begin(), nums.end());
result.insert(result.end(), nums.begin(), nums.end());
```

**Option C: reserve + double insert.**
```cpp
vector<int> result;
result.reserve(2 * nums.size());
result.insert(result.end(), nums.begin(), nums.end());
result.insert(result.end(), nums.begin(), nums.end());
```

All three are O(n) and equivalent. Option B is the shortest; Option A is the most explicit.

----------------------------------------

## Step 4: Trace

`nums = [1, 3, 2, 1]`. n = 4.

Option A:
- i=0: result[0]=1, result[4]=1.
- i=1: result[1]=3, result[5]=3.
- i=2: result[2]=2, result[6]=2.
- i=3: result[3]=1, result[7]=1.

Final result: [1, 3, 2, 1, 1, 3, 2, 1]. ✓

----------------------------------------

## Step 5: Edge Cases

- Empty nums (n = 0). Return empty array. All approaches handle this — the loop doesn't run, or the insert copies nothing.
- Single element. Return [x, x]. Straightforward.

No tricky cases.

----------------------------------------

## Step 6: Name It

Not a specific algorithm — this is basic array manipulation. But it illustrates:
- **Pre-allocation** for performance (`vector` constructor with size).
- **STL idioms** (`insert` with iterators).
- **Index arithmetic** (`i + n`).

Real-world analogs:
- Circular buffer simulation.
- Period-2 or repeated sequence construction.
- Image tiling.

----------------------------------------

## Step 7: Complexity

Time: **O(n)**.
Space: **O(n)** for the result.

----------------------------------------

## Step 8: C++ Implementation

```cpp
vector<int> getConcatenation(vector<int>& nums) {
    vector<int> result(2 * nums.size());
    for (int i = 0; i < (int)nums.size(); ++i) {
        result[i] = nums[i];
        result[i + nums.size()] = nums[i];
    }
    return result;
}
```

Clean and clear. The "set both copies in one loop iteration" approach is slightly more cache-friendly than two separate loops.

----------------------------------------

## Step 9: Follow-up Questions

- **K-fold concatenation.** Multiply size by k; loop over copies.
- **Concatenate two different arrays.** `result.insert(result.end(), nums2.begin(), nums2.end())`.
- **Concatenate without allocating 2n memory** (logical concatenation via iterator or index mapping). Wrap in a lazy structure.
- **Reverse concatenation (reverse of nums + nums).** Construct the reversed part differently.
- **In-place doubling.** Not possible without extra buffer (the original array has no room).
- **Streaming concatenation.** For very large nums, generate output incrementally.
