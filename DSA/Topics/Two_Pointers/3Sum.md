# 3Sum

**Problem Link:**
<a href="https://leetcode.com/problems/3sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/3sum/</a>

**Topic:**
Two Pointers

----------------------------------------

## Step 1: The Problem

Given an array `nums`, return all **unique** triplets `(a, b, c)` that sum to 0.

"Unique" means we don't return the same triplet twice, even if the original array has duplicates. So for `nums = [-1, 0, 1, 2, -1, -4]`, valid triplets are `[-1, -1, 2]` and `[-1, 0, 1]`. The fact that `-1` appears twice doesn't give us two copies of `[-1, 0, 1]`.

----------------------------------------

## Step 2: The Brute Force

Three nested loops. For each `(i, j, k)` with `i < j < k`, check if `a[i] + a[j] + a[k] == 0`.

```cpp
for (int i = 0; i < n; ++i)
    for (int j = i+1; j < n; ++j)
        for (int k = j+1; k < n; ++k)
            if (a[i] + a[j] + a[k] == 0)
                result.push_back({a[i], a[j], a[k]});
```

O(n³). And we still have to dedupe afterward. Bad on both counts.

What could help? Let me think: can we at least find triplets summing to 0 faster than O(n³)?

----------------------------------------

## Step 3: Reducing to a Simpler Problem

Here's a useful reframing. If I fix one element (say `a[i]`), the remaining problem is:

> Find **pairs** `(j, k)` with `j, k > i` such that `a[j] + a[k] == -a[i]`.

That's **two-sum** on the remaining part of the array, with target `-a[i]`.

Two-sum can be done in O(n) if the array is sorted (two-pointer scan from both ends) or if we use a hashmap. So the total work becomes O(n²) — n choices for `i`, and O(n) for the inner two-sum.

The two-pointer version is especially clean and naturally handles duplicates. Let's go with that.

----------------------------------------

## Step 4: Sort, Then Fix-and-Sweep

1. **Sort the array** ascending. This lets us use two-pointer two-sum, and also makes deduplication natural.
2. **For each i from 0 to n-3:**
   - If `a[i] > 0`, we can stop — all remaining sums are positive.
   - If `a[i] == a[i-1]` (and `i > 0`), skip to avoid duplicate triplets.
   - Run two-pointer two-sum for target `-a[i]` on the range `(i, n-1)`.

The duplicate-skip rule deserves attention. Why does it work? Because after sorting, equal elements sit next to each other. If I already used the first copy of `-1` as my `i`-th element and found all triplets involving it, then the second copy of `-1` as `i` would produce *exactly the same triplets*, just picking different copies of `-1`. Skipping is safe and necessary.

----------------------------------------

## Step 5: Two-Pointer Two-Sum Inside

Given sorted range `[l..r]`, find all pairs summing to `target = -a[i]`.

```
l = i + 1, r = n - 1
while l < r:
    s = a[l] + a[r]
    if s == target:
        record (a[i], a[l], a[r])
        advance l past duplicates of a[l]
        advance r past duplicates of a[r]
        l++, r--
    elif s < target:
        l++
    else:
        r--
```

Why move `l++` when `s < target`? Because we need a larger sum, and the array is sorted — a larger `l` value gives a larger `a[l]`. Symmetric for `r--`.

Why advance past duplicates after recording a hit? Same reasoning as skipping duplicate `a[i]`: different copies of the same value at `l` or `r` would yield the same triplet.

----------------------------------------

## Step 6: Dry Run on `[-1, 0, 1, 2, -1, -4]`

Sort first: `[-4, -1, -1, 0, 1, 2]`.

```
i=0, a[i]=-4. Target = 4. Two-pointer l=1, r=5:
  a[1]+a[5] = -1+2 = 1. 1<4, l++.
  a[2]+a[5] = -1+2 = 1. 1<4, l++.
  a[3]+a[5] = 0+2 = 2. 2<4, l++.
  a[4]+a[5] = 1+2 = 3. 3<4, l++.
  l=5, r=5. Exit.
  No triplets from i=0.

i=1, a[i]=-1. Target = 1. l=2, r=5:
  a[2]+a[5] = -1+2 = 1. = target. Record (-1, -1, 2).
  Skip duplicates: a[2]=-1 unique (a[3]=0). l=3. a[5]=2 unique (a[4]=1). r=4.
  a[3]+a[4] = 0+1 = 1. Record (-1, 0, 1).
  Skip duplicates: a[3]=0 unique. l=4. a[4]=1 unique. r=3. l >= r. Exit.

i=2, a[i]=-1. a[i]==a[i-1]. Skip.

i=3, a[i]=0. Target = 0. l=4, r=5:
  a[4]+a[5] = 1+2 = 3. 3>0, r--. l=4, r=4. Exit.

i=4, a[i]=1. a[i] > 0. Actually we were going to break but we only break when a[i] > 0? yes, 1 > 0 → break.
```

Result: `[(-1, -1, 2), (-1, 0, 1)]`. ✓

Trace notes:
- The `a[i] > 0` short-circuit is an optimization: once `a[i]` is positive, `a[j]` and `a[k]` (both ≥ `a[i]`) make the sum strictly positive.
- The dedup pattern "skip repeated `a[i]`" plus "skip repeated `a[l]` / `a[r]` after a hit" gives us unique triplets without needing a `set<tuple>` wrapper.

----------------------------------------

## Step 7: Why Sort Helps So Much

Sorting is O(n log n) — a cost we pay once. In exchange:

1. **Two-pointer two-sum** becomes O(n) per outer iteration.
2. **Duplicate handling** becomes simple — equal values are adjacent, so skipping is a comparison.
3. **Early termination** (`a[i] > 0` break) becomes possible.

If the array weren't sorted, we'd need a hashmap for two-sum (fine but messier dedup) or we'd have to sort anyway to dedupe at the end.

----------------------------------------

## Step 8: Complexity

Time: sort is O(n log n). Main loop: n iterations, each running O(n) two-pointer. **O(n²)** total.

Space: O(1) auxiliary besides the output (sort is in-place or uses O(log n) stack).

For `n = 3000`, O(n²) is 9 million ops — easily fast enough. For `n = 10^5` it's 10^10 — too slow, but that's above what interviewers usually test.

----------------------------------------

## Step 9: C++ Implementation

```cpp
vector<vector<int>> threeSum(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    int n = nums.size();
    vector<vector<int>> res;
    for (int i = 0; i < n - 2; ++i) {
        if (nums[i] > 0) break;                     // no negative left to balance
        if (i > 0 && nums[i] == nums[i-1]) continue; // skip duplicate i
        int l = i + 1, r = n - 1, target = -nums[i];
        while (l < r) {
            int s = nums[l] + nums[r];
            if (s == target) {
                res.push_back({nums[i], nums[l], nums[r]});
                while (l < r && nums[l] == nums[l+1]) l++;
                while (l < r && nums[r] == nums[r-1]) r--;
                l++; r--;
            } else if (s < target) l++;
            else r--;
        }
    }
    return res;
}
```

One subtle bug to avoid: after recording a hit, you must advance both `l` and `r` by at least 1 (the `l++; r--;` at the end). Otherwise you'd loop forever on the same pair.

----------------------------------------

## Step 10: Follow-up Questions

- **3Sum Closest:** find the triplet whose sum is closest to a target. Same structure; track the minimum `|s - target|`.
- **3Sum Smaller (count triplets with sum < target):** same two-pointer; when `s < target`, every `k` from `l+1..r` gives a valid triplet — add `r - l` to count, then `l++`.
- **4Sum:** wrap another outer loop `i`, run 3Sum on the remainder with target `-a[i]`. O(n³).
- **k-Sum (general):** recursive wrap around 2Sum base case. O(n^(k-1)).
- **3Sum with no duplicates in input:** can skip the dedup skips, but still need to sort to use two-pointer.
- **What if values are huge (negatives/large positives) — worry about overflow?** Use `long long` for the sum.
