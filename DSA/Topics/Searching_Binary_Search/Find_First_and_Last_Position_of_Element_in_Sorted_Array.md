# Find First and Last Position of Element in Sorted Array

**Problem Link:**
<a href="https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/</a>

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: Understand the Problem

Given a sorted array (ascending) possibly with duplicates, and a target, return the **first** and **last** positions of target. If target isn't in the array, return `[-1, -1]`.

Example: `nums = [5, 7, 7, 8, 8, 10]`, target = 8.
- 8 first appears at index 3, last at index 4. Return `[3, 4]`.

`target = 6`: 6 isn't present. Return `[-1, -1]`.

`target = 7`: first = 1, last = 2. Return `[1, 2]`.

Required: **O(log n)** time.

----------------------------------------

## Step 2: Brute Force First

Linear scan for the first target, then for the last. O(n). Fine for small arrays, but the sorted-array + O(log n) constraint says we must use binary search.

One obvious approach: **standard binary search finds *some* occurrence** of the target. Then linear-scan left and right to find the boundaries. But if the target appears many times (say, all n elements are the target), the linear scan is O(n) — we're back to where we started.

We need binary search that finds boundaries directly.

----------------------------------------

## Step 3: Binary Search for "Leftmost Occurrence"

Here's the trick. Instead of searching for "is target here?", search for the **smallest index where `nums[i] >= target`**. That gives the leftmost position where target could appear.

Why? Because the array is sorted. All positions to the left of this index hold values `< target`, so they can't be target. If `nums[i] == target` exactly, we've found the first occurrence. If `nums[i] > target`, target isn't present at all.

Binary search for this "first index ≥ target" uses the standard pattern:
```
lo = 0, hi = n
while lo < hi:
    mid = (lo + hi) / 2
    if nums[mid] >= target:
        hi = mid
    else:
        lo = mid + 1
return lo
```

Loop invariant: target's first occurrence (if any) lies in `[lo, hi]`. Shrinks in half each step. Exits when lo == hi, and that's the answer.

----------------------------------------

## Step 4: Binary Search for "Rightmost Occurrence"

Symmetrically, find the smallest index where `nums[i] > target`. That's the position **just past** the last target. Subtract 1 to get the last target's index.

```
lo = 0, hi = n
while lo < hi:
    mid = (lo + hi) / 2
    if nums[mid] > target:
        hi = mid
    else:
        lo = mid + 1
return lo
```

Only difference from the leftmost search: we use `>` instead of `>=`. That one character flip changes the boundary from "first ≥" to "first strictly >."

These two patterns are **lower_bound** and **upper_bound** in C++ STL. If you've used `std::lower_bound` and `std::upper_bound`, that's exactly this code.

----------------------------------------

## Step 5: Combine Them

```
first = lower_bound(target)          // first index with value >= target
last  = upper_bound(target) - 1      // last index with value == target

if first == n or nums[first] != target:
    return [-1, -1]                  // target not present
return [first, last]
```

The check `first == n or nums[first] != target` handles the "not present" case — if `lower_bound` returned n (past the end) or the value at `first` isn't target, target isn't in the array.

----------------------------------------

## Step 6: Trace on `[5, 7, 7, 8, 8, 10]`, target = 8

**Lower bound (first ≥ 8):**
```
lo=0, hi=6. mid=3. nums[3]=8 >= 8. hi=3.
lo=0, hi=3. mid=1. nums[1]=7 < 8. lo=2.
lo=2, hi=3. mid=2. nums[2]=7 < 8. lo=3.
lo=3, hi=3. Return 3.
```

first = 3.

**Upper bound (first > 8):**
```
lo=0, hi=6. mid=3. nums[3]=8 not > 8. lo=4.
lo=4, hi=6. mid=5. nums[5]=10 > 8. hi=5.
lo=4, hi=5. mid=4. nums[4]=8 not > 8. lo=5.
lo=5, hi=5. Return 5.
```

last = 5 - 1 = 4.

Result: `[3, 4]`. ✓

For target 6:
- Lower bound: finds first ≥ 6 → index 1 (value 7). But nums[1]=7 ≠ 6. Return `[-1, -1]`.

----------------------------------------

## Step 7: Why Two Binary Searches, Not One

A naïve attempt might be "find any occurrence with standard binary search, then expand." But as noted, expansion can be O(n). Two separate log-n searches for the two boundaries is cleaner and guaranteed O(log n).

The pattern "search for leftmost valid" and "search for rightmost valid" is a classic. The trick: change the comparison slightly (>= vs >) to pick the boundary you want.

----------------------------------------

## Step 8: Name the Technique

**Binary search for boundaries**, or **lower_bound / upper_bound** style. Once you see the pattern (search for the smallest index satisfying a monotonic condition), it applies broadly:
- First index where array value ≥ target.
- First index where some boolean predicate is true.
- Search-on-answer problems.

Tip: in C++ interviews, using `std::lower_bound` and `std::upper_bound` directly is totally acceptable and shows you know the STL. Writing the binary search manually is also fine and demonstrates understanding.

----------------------------------------

## Step 9: Complexity

Time: two binary searches, each **O(log n)**.
Space: **O(1)**.

----------------------------------------

## Step 10: C++ Implementation

Using STL:

```cpp
vector<int> searchRange(vector<int>& nums, int target) {
    auto lb = lower_bound(nums.begin(), nums.end(), target);
    if (lb == nums.end() || *lb != target) return {-1, -1};
    auto ub = upper_bound(nums.begin(), nums.end(), target);
    return {(int)(lb - nums.begin()), (int)(ub - nums.begin() - 1)};
}
```

Compact. The two STL calls do exactly the two binary searches we derived.

Hand-rolled:

```cpp
vector<int> searchRange(vector<int>& nums, int target) {
    int n = nums.size();
    auto lowerBound = [&](int t) {
        int lo = 0, hi = n;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] >= t) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    };
    auto upperBound = [&](int t) {
        int lo = 0, hi = n;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] > t) hi = mid;
            else lo = mid + 1;
        }
        return lo;
    };
    int first = lowerBound(target);
    if (first == n || nums[first] != target) return {-1, -1};
    int last = upperBound(target) - 1;
    return {first, last};
}
```

Two lambdas for clarity. Both run in O(log n).

----------------------------------------

## Step 11: Follow-up Questions

- **Count occurrences of target.** `upperBound(target) - lowerBound(target)`.
- **Nearest value to target (if target not in array).** Check both `lb - 1` and `lb`, pick whichever is closer.
- **If array is rotated/sorted:** different problem (Search in Rotated Sorted Array). Use a different binary search variant.
- **What if we want the k-th occurrence of target?** Just use `lowerBound(target) + k - 1` (after bounds check).
- **What if the array has duplicates and we want a random occurrence uniformly?** Find lb and ub, pick a random index in [lb, ub).
- **Why not just std::equal_range?** Equivalent — returns the pair (lb, ub). Cleaner for this exact problem.
