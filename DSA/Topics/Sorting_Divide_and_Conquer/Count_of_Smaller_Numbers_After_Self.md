# Count of Smaller Numbers After Self

**Problem Link:**
https://leetcode.com/problems/count-of-smaller-numbers-after-self/

**Topic:**
Sorting / Divide & Conquer

----------------------------------------

## Step 1: Understand the Problem

Given an integer array `nums`, return a new array `result` where `result[i]` is the **count of numbers to the right of nums[i] that are strictly less than nums[i]**.

Example: `nums = [5, 2, 6, 1]`.
- nums[0] = 5. To its right: [2, 6, 1]. Numbers < 5: 2 and 1. Count = 2.
- nums[1] = 2. Right: [6, 1]. Numbers < 2: 1. Count = 1.
- nums[2] = 6. Right: [1]. Numbers < 6: 1. Count = 1.
- nums[3] = 1. Right: []. Count = 0.

Result: `[2, 1, 1, 0]`.

----------------------------------------

## Step 2: Brute Force and Its Limit

For each i, scan everything to the right and count smaller. O(n²). For n = 10^5, too slow.

We need something better. Let's think about the structure.

----------------------------------------

## Step 3: Reframing as an Inversion Problem

"Count of smaller numbers after self" is a variant of **inversion counting** in sorting. An inversion is a pair (i, j) with i < j and nums[i] > nums[j]. The classic way to count inversions: **merge sort**.

Merge sort naturally decomposes into left and right halves. When merging two sorted halves, any time we pick an element from the right half, it's because it's smaller than some remaining element(s) in the left half. That's where inversion counts live.

For our problem, we need per-element counts (not just the total). That changes the approach slightly: we'll count how many "right-half" elements end up being placed before each "left-half" element during merges.

----------------------------------------

## Step 4: Mergesort With Per-Element Counting

Here's the plan:
- Work on **indices**, not values directly. Sort indices by the value at that index. Keep track of the original index for each.
- During merge, when we place a right-half element before a left-half element, increment the counts of all remaining left-half elements (they have found one more "smaller-after-them").

Let me get specific.

Maintain an `indices` array (initially `[0, 1, 2, ..., n-1]`) and a `count` array (initially zeros). Mergesort sorts `indices` by `nums[index]`. During merges:
- We have two sorted sub-arrays of indices: left and right.
- When merging, we compare values `nums[left[i]]` and `nums[right[j]]`.
- If `nums[right[j]] < nums[left[i]]`: place right[j] first. But more importantly, every remaining element in the left half has a "smaller after it" — specifically, right[j] was originally to the right of them (because it's in the right half, and the right half has larger original indices).
  
  Wait, we need to be careful. In mergesort on **indices**, the "left half" and "right half" correspond to original index positions (assuming we did the top-level split by index range). So yes: everything in the right half has a higher original index than everything in the left half.
  
  So when we place right[j] before some remaining elements of left (those at position i, i+1, ...), each of those left elements has one more "smaller after them" (namely, right[j]).

Actually the cleaner way: when we place a **left** element, count how many right elements have been placed **before** it in this merge. Those are exactly the "smaller after self" for this left element.

----------------------------------------

## Step 5: Refined Counting Step

Modify merge as follows:
```
def merge(left, right, indices, counts):
    i = 0  # pointer into left
    j = 0  # pointer into right
    merged = []
    while i < len(left) and j < len(right):
        if nums[left[i]] <= nums[right[j]]:   # left wins
            # all right[0..j-1] were placed before left[i].
            # They're "smaller after" left[i] (j elements).
            counts[left[i]] += j
            merged.append(left[i])
            i++
        else:  # right wins
            merged.append(right[j])
            j++
    while i < len(left):
        counts[left[i]] += j   # all of right was already placed
        merged.append(left[i])
        i++
    merged.extend(right[j:])
    return merged
```

Reading this: every time we pick a left element, we know how many right elements have been placed so far (that's `j`). Those right elements are all originally to the right of `left[i]` (since they came from the right half of the index range). And they were all placed before left[i] in the sorted order, meaning they're all smaller than left[i]. So add `j` to `counts[left[i]]`.

After all merges finish, `counts` has the final answer.

----------------------------------------

## Step 6: Trace on `[5, 2, 6, 1]`

Initial: indices = [0, 1, 2, 3]. counts = [0, 0, 0, 0].

Split into [0, 1] and [2, 3]. Recurse.

**Left half [0, 1]:**
Split into [0] and [1]. No merge needed within.
Merge [0] (value 5) with [1] (value 2):
  i=0, j=0: nums[left[0]]=5, nums[right[0]]=2. 5 > 2, right wins. Append right[0]=1. j=1.
  i=0, j=1: left only. Add j=1 to counts[0]. counts = [1, 0, 0, 0]. Append left[0]=0. i=1.
  Done. Merged = [1, 0].

**Right half [2, 3]:**
Similarly, merge [2] and [3]:
  nums[2]=6, nums[3]=1. 6 > 1. Append 3. j=1.
  Add j=1 to counts[2]. counts = [1, 0, 1, 0]. Append 2.
  Merged = [3, 2].

**Top-level merge of [1, 0] (values 2, 5) and [3, 2] (values 1, 6):**
  i=0, j=0: nums[left[0]]=2, nums[right[0]]=1. 2 > 1. Append right[0]=3. j=1.
  i=0, j=1: 2 vs 6. 2 <= 6, left wins. Add j=1 to counts[left[0]] = counts[1]. counts = [1, 1, 1, 0]. Append 1. i=1.
  i=1, j=1: nums[left[1]]=5 vs 6. 5 <= 6. Add j=1 to counts[left[1]] = counts[0]. counts = [2, 1, 1, 0]. Append 0. i=2.
  Remaining right: [2]. Append.
  Merged = [3, 1, 0, 2].

Final counts: `[2, 1, 1, 0]`. ✓ Matches expected.

----------------------------------------

## Step 7: Why This Works

During a merge of left and right halves:
- Every element in right has a higher **original** index than every element in left (because we split by index ranges in mergesort).
- If a right element is placed **before** a remaining left element during merge, that right element is smaller than the left element (merge order). And it's originally to the right. So it contributes to the left element's "smaller-after-self" count.

By adding `j` to `counts[left[i]]` when we place `left[i]`, we capture exactly those right elements placed before it.

This counting happens at every merge step; across all levels of mergesort, each pair of indices is visited exactly once in the relevant comparison. So we count every qualifying pair.

----------------------------------------

## Step 8: Complexity

Time: mergesort is O(n log n); counting adds O(1) per merge step. **O(n log n)** total.
Space: O(n) for the merge buffer and counts array.

Huge win over O(n²) brute force.

Alternative: use a **Fenwick tree (BIT)**. Iterate from right to left; for each value, query "count of values less than this" in the BIT; then insert this value. Also O(n log n). Either approach works.

----------------------------------------

## Step 9: Name It

This is **mergesort-based inversion counting**, adapted for per-element counts.

The core idea — "each merge detects certain cross-half pairs" — is the same as counting total inversions. For per-element counts, we just track where the contribution lands (which left element gets credited).

Related:
- Reverse Pairs (count pairs where nums[i] > 2 · nums[j]).
- Count of smaller elements before self (symmetric; iterate left-to-right instead).
- Number of Range Sum (similar DP with mergesort).

----------------------------------------

## Step 10: C++ Implementation

```cpp
class Solution {
    vector<int> counts;
    vector<int> nums;

    void mergeSort(vector<int>& indices, int lo, int hi) {
        if (lo >= hi) return;
        int mid = (lo + hi) / 2;
        mergeSort(indices, lo, mid);
        mergeSort(indices, mid + 1, hi);

        // Merge indices[lo..mid] and indices[mid+1..hi] by nums[index] value.
        vector<int> merged;
        int i = lo, j = mid + 1;
        while (i <= mid && j <= hi) {
            if (nums[indices[i]] <= nums[indices[j]]) {
                // indices[j..j-1] (i.e., j-1 - (mid+1) + 1 = j - mid - 1 elements) came from right
                counts[indices[i]] += (j - mid - 1);
                merged.push_back(indices[i++]);
            } else {
                merged.push_back(indices[j++]);
            }
        }
        while (i <= mid) {
            counts[indices[i]] += (j - mid - 1);   // all of right half placed already
            merged.push_back(indices[i++]);
        }
        while (j <= hi) merged.push_back(indices[j++]);

        for (int k = 0; k < (int)merged.size(); ++k) indices[lo + k] = merged[k];
    }

public:
    vector<int> countSmaller(vector<int>& input) {
        nums = input;
        int n = nums.size();
        counts.assign(n, 0);
        vector<int> indices(n);
        iota(indices.begin(), indices.end(), 0);
        mergeSort(indices, 0, n - 1);
        return counts;
    }
};
```

Key detail: when merging range `[lo, mid]` and `[mid+1, hi]`, the number of right-half elements already placed before the current left-half element (at index `i`) is `j - mid - 1`. Add this to `counts[indices[i]]`.

----------------------------------------

## Step 11: Follow-up Questions

- **Count smaller elements BEFORE self (not after).** Symmetric: iterate right-to-left or reverse the array first.
- **Count of equal elements (nums[i] == nums[j]).** Change `<=` to `<` in the comparison so equals aren't counted; or handle separately.
- **Total inversion count (sum of all counts).** Either sum the counts array, or adapt the algorithm to just track a total.
- **Find the k-th pair by inversion index.** Harder — combination of mergesort with binary search.
- **Fenwick tree approach.** Coordinate-compress values, then for each from right to left: query BIT for "count of values < current"; then add 1 to BIT at current.
- **Why not sort and binary search?** Sorting loses original positions; we need per-original-index counts.
