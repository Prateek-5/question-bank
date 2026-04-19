# Running Sum of 1D Array

**Problem Link:**
https://leetcode.com/problems/running-sum-of-1d-array/

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: What's a Running Sum?

Given an array `nums`, compute `result[i] = nums[0] + nums[1] + ... + nums[i]` for each `i`.

Example: `nums = [1, 2, 3, 4]`.
- result[0] = 1.
- result[1] = 1 + 2 = 3.
- result[2] = 1 + 2 + 3 = 6.
- result[3] = 1 + 2 + 3 + 4 = 10.

Return `[1, 3, 6, 10]`.

Also known as: **prefix sum**.

----------------------------------------

## Step 2: Observe the Pattern

Look at consecutive entries:
- result[0] = nums[0].
- result[1] = result[0] + nums[1].
- result[2] = result[1] + nums[2].
- result[i] = result[i-1] + nums[i].

Each entry builds on the previous. So we can compute result with a single pass, maintaining a running total.

```
result[0] = nums[0]
for i in 1..n-1:
    result[i] = result[i-1] + nums[i]
```

O(n) time, O(n) space for the output.

----------------------------------------

## Step 3: In-Place Version

Even cleaner: modify `nums` in place.

```
for i in 1..n-1:
    nums[i] += nums[i-1]
return nums
```

O(n) time, O(1) extra space.

For this problem specifically, the return type often expects a new array, but most languages permit modifying and returning the input since it's passed by reference.

----------------------------------------

## Step 4: Trace

`nums = [1, 2, 3, 4]`.

```
i=1: nums[1] += nums[0] = 2 + 1 = 3. nums = [1, 3, 3, 4].
i=2: nums[2] += nums[1] = 3 + 3 = 6. nums = [1, 3, 6, 4].
i=3: nums[3] += nums[2] = 4 + 6 = 10. nums = [1, 3, 6, 10].
```

Return `[1, 3, 6, 10]`. ✓

Or with a fresh array:

```
result[0] = 1.
result[1] = 1 + 2 = 3.
result[2] = 3 + 3 = 6.
result[3] = 6 + 4 = 10.
```

Same values.

----------------------------------------

## Step 5: Why Running Sums Matter

This is a fundamental **preprocessing technique** — the building block of prefix-sum algorithms:
- **Subarray sum query**: sum(l..r) = prefix[r+1] - prefix[l]. Answer in O(1) after O(n) preprocessing.
- **Subarray Sum Equals K.**
- **Maximum Size Subarray Sum Equals K.**
- **Range Sum Query Immutable.**

Mastering prefix sums is a rite of passage for array problems.

----------------------------------------

## Step 6: Name It

**Prefix sum** — a classic. Also called "cumulative sum" or "running total." Shows up in:
- Financial data (cumulative profits).
- Game mechanics (health over time).
- Histogram visualization.

The variations extend to 2D (submatrix sums), 3D, and more general "prefix operations" like prefix XOR, prefix max, etc.

----------------------------------------

## Step 7: Complexity

Time: **O(n)**.
Space: O(n) with a new array, O(1) in-place.

----------------------------------------

## Step 8: C++ Implementation

```cpp
vector<int> runningSum(vector<int>& nums) {
    for (int i = 1; i < (int)nums.size(); ++i) {
        nums[i] += nums[i-1];
    }
    return nums;
}
```

Four lines. The simplest array operation after "return the array unchanged."

Alternative with STL:

```cpp
vector<int> runningSum(vector<int>& nums) {
    partial_sum(nums.begin(), nums.end(), nums.begin());
    return nums;
}
```

`std::partial_sum` does exactly this operation. Even shorter.

----------------------------------------

## Step 9: Follow-up Questions

- **2D running sum (submatrix sums).** 2D prefix: `P[i][j] = sum of submatrix (0,0)-(i,j)`. Formula: `P[i][j] = nums[i][j] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]`.
- **Prefix product, prefix max, prefix XOR.** Same structure, different operation.
- **Reverse (suffix sum): `sum of nums[i..n-1]`.** Iterate right-to-left.
- **Range update + point query.** Use difference array, then prefix sum at the end.
- **Range update + range query.** Segment tree with lazy propagation, or Binary Indexed Tree with range ops.
- **Running average.** Compute running sum, then divide by index + 1.
