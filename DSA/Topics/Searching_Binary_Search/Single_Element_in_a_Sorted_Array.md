# Single Element in a Sorted Array

**Problem Link:**
<a href="https://leetcode.com/problems/single-element-in-a-sorted-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/single-element-in-a-sorted-array/</a>

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: The Setup

You have a **sorted** array where every element appears **exactly twice**, except for **one** element that appears once. Find that single element.

The solution must run in **O(log n)** time and O(1) space.

Example: `nums = [1, 1, 2, 3, 3, 4, 4, 8, 8]`.
- Pairs: (1,1), (3,3), (4,4), (8,8).
- Single: 2.

Return **2**.

Another: `nums = [3, 3, 7, 7, 10, 11, 11]`. Single: 10.

----------------------------------------

## Step 2: Simple Approaches

**XOR all elements.** For any array where each value appears twice except one, XOR-ing all elements gives the lonely one (since x XOR x = 0). This is O(n) time — works, but doesn't meet the O(log n) requirement.

**Linear scan for a mismatched pair.** Walk through pairs (indices 0-1, 2-3, 4-5, ...) until we find one where they differ. That's where the single is. O(n).

The O(log n) demand says we must use the **sorted** property. Let's think.

----------------------------------------

## Step 3: The Parity Pattern

Look at `[1, 1, 2, 3, 3, 4, 4, 8, 8]` and indices:
```
idx: 0  1  2  3  4  5  6  7  8
val: 1  1  2  3  3  4  4  8  8
```

**Before** the single element (index 2):
- Pair starts at even indices: `[0, 1]`.

**After** the single element:
- Pair starts at odd indices: `[3, 4]`, `[5, 6]`, `[7, 8]`.

So the "single" disrupts the even-then-same-then-odd pattern. On the **left** of the single, pairs are `(even, odd)` where `a[even] == a[even + 1]`. On the **right**, pairs are `(odd, even)` where `a[odd] == a[odd + 1]`.

Or simpler:
- Left of single: `a[even] == a[even + 1]`.
- Right of single: `a[even] != a[even + 1]`.

This is a **monotonic predicate** as a function of index: "does `a[even] == a[even + 1]`?" is true for even indices left of single, false for even indices right of single. We can binary search for the boundary.

----------------------------------------

## Step 4: The Binary Search

Binary search over even indices. At midpoint index `m` (forced to be even):
- If `a[m] == a[m + 1]`: we're on the left side of the single. The single is at index > m + 1. Move lo to m + 2.
- Else: we're at or right of the single. Single is at index ≤ m. Move hi to m.

```
lo = 0, hi = n - 1
while lo < hi:
    mid = lo + (hi - lo) / 2
    if mid is odd: mid--   # force mid to be even
    if a[mid] == a[mid + 1]:
        lo = mid + 2
    else:
        hi = mid
return a[lo]
```

When lo == hi, we've zeroed in on the single element's index.

----------------------------------------

## Step 5: Trace on the Example

`[1, 1, 2, 3, 3, 4, 4, 8, 8]`. n = 9. lo=0, hi=8.

```
Iter 1: mid=(0+8)/2=4. Even. a[4]=3, a[5]=4. Not equal. hi=4.
Iter 2: lo=0, hi=4. mid=2. Even. a[2]=2, a[3]=3. Not equal. hi=2.
Iter 3: lo=0, hi=2. mid=1. Odd, mid--=0. a[0]=1, a[1]=1. Equal. lo=2.
Iter 4: lo=2, hi=2. Exit loop.
Return a[2]=2.
```

Return 2. ✓

----------------------------------------

## Step 6: Why the "Force Mid to Even" Trick

We want to check pairs aligned at even indices. If mid lands on an odd index, we'd be checking `a[odd] == a[odd + 1]` — but that's checking a shifted pair. The force-to-even step keeps us aligned with the pairing structure.

An equivalent trick: use bitwise `mid = mid & ~1` (clear the least significant bit). Same effect.

----------------------------------------

## Step 7: Why the Predicate Is Monotonic

Think about why the predicate `a[even] == a[even + 1]` flips exactly once.

Before the single: every even-odd pair is equal. Predicate holds.

At the single's position (say index s, which has some parity):
- If s is even: `a[s] != a[s + 1]` (since a[s] is the single, a[s + 1] starts a new pair). Predicate fails.
- If s is odd: `a[s - 1] != a[s]` (single pushes the pair boundary). For the even index `s - 1`, predicate fails.

Either way, the predicate transitions from "true" to "false" at one specific even index (either s or s - 1). Binary search on this transition.

----------------------------------------

## Step 8: Name It

This is **binary search on a parity-based predicate**. The core pattern:
1. Identify a property that's true on one half, false on the other.
2. Binary search for the boundary.
3. The boundary is (or is adjacent to) our answer.

Same template solves:
- First Bad Version (monotonic bad/good).
- Peak Element (local maximum via parity-like condition).
- Longest Subarray With Given Property (binary search on length).

Not all binary-search problems are on sorted arrays — the key is monotonic predicates over indices or values.

----------------------------------------

## Step 9: Complexity

Time: **O(log n)**. Each iteration halves the range.
Space: **O(1)**.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int singleNonDuplicate(vector<int>& nums) {
    int lo = 0, hi = nums.size() - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (mid % 2 == 1) mid--;   // force mid to be even
        if (nums[mid] == nums[mid + 1]) {
            lo = mid + 2;           // single is to the right
        } else {
            hi = mid;                // single is here or to the left
        }
    }
    return nums[lo];
}
```

Seven lines. The parity alignment is the subtle trick.

----------------------------------------

## Step 11: Follow-up Questions

- **Unsorted array with the same property.** XOR approach gives O(n); no log n trick.
- **Two single elements (others appear twice).** XOR gives their XOR; then bit-manipulate to separate them.
- **All elements appear three times except one (which appears once).** Different approach — bit-count mod 3, or state-machine.
- **Find the single in a nearly-sorted array.** Tricky; structural assumptions change.
- **If the pairs-except-one structure is guaranteed by the problem.** Simplifies the algorithm. Otherwise, add validation.
- **Why not just check `nums[0..n-1]` via `i += 2` and compare `nums[i] == nums[i+1]`?** That's O(n). We want O(log n) via binary search.
