# Sort Colors

**Problem Link:**
<a href="https://leetcode.com/problems/sort-colors/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/sort-colors/</a>

**Topic:**
Sorting / Divide & Conquer

----------------------------------------

## Step 1: Read the Problem

You're given an array where each element is **0, 1, or 2** (representing red, white, blue). Sort it in place so all 0s come first, then all 1s, then all 2s.

The challenge: can you do this in **one pass** with **O(1) extra memory** and **O(n) time**?

Example: `[2, 0, 2, 1, 1, 0]` → `[0, 0, 1, 1, 2, 2]`.

----------------------------------------

## Step 2: Easy Two-Pass Approaches

Before tackling the one-pass challenge, let's note some simpler approaches:

**Counting sort.** Count the number of 0s, 1s, and 2s. Overwrite the array with that many 0s, then 1s, then 2s.

```cpp
int count[3] = {0, 0, 0};
for (int x : nums) count[x]++;
int idx = 0;
for (int c = 0; c < 3; ++c)
    for (int i = 0; i < count[c]; ++i) nums[idx++] = c;
```

O(n) time, O(1) extra space, **but two passes**. Easy and efficient; perfectly valid unless the problem asks for one pass.

**Standard sort.** Just call `sort(nums.begin(), nums.end())`. O(n log n). Simplest code but asymptotically slower.

The challenge is: can we do it in **one pass**?

----------------------------------------

## Step 3: Set Up Three Regions

One pass implies we're moving elements as we see them, not counting first. As we scan, we partition the array into three regions:
- **Left region**: all 0s, already sorted.
- **Middle region**: all 1s, already sorted.
- **Right region**: all 2s, already sorted.

Let's formalize with three pointers:
- `lo` = index where the next 0 should go (the boundary between the 0s-region and the 1s-region).
- `mid` = the current cursor, examining the element at `mid`.
- `hi` = index where the next 2 should go, filling from the right.

Invariant at any moment:
- `nums[0..lo)` are all 0s.
- `nums[lo..mid)` are all 1s.
- `nums[mid..hi]` are unexamined (could be anything).
- `nums[hi+1..n)` are all 2s.

Initially, `lo = 0`, `mid = 0`, `hi = n - 1`. The unexamined region is the whole array.

----------------------------------------

## Step 4: The Three Cases

At each step, we look at `nums[mid]`:

**Case `nums[mid] == 0`:** it belongs in the 0s-region. Swap it with `nums[lo]` (whatever was there was a 1 from the 1s-region, so swapping keeps the invariant). Then advance both `lo` and `mid`.

**Case `nums[mid] == 1`:** it's already in the right place (the 1s-region just extends). Advance `mid` only.

**Case `nums[mid] == 2`:** it belongs in the 2s-region. Swap with `nums[hi]`. But don't advance `mid` — the value that just came from the right (`nums[hi]`) is unexamined; we need to check it next. Decrement `hi`.

The loop continues while `mid <= hi`. When `mid > hi`, the unexamined region is empty and we're done.

----------------------------------------

## Step 5: Why the Asymmetric Pointer Update on `2`s

When we swap `nums[mid] == 0` with `nums[lo]`, the value that comes to `mid` was previously at `lo`, inside the 1s-region — so it's a 1. Advancing `mid` is safe because we know the swapped-in value is correctly placed (it's a 1 at the start of the 1s-region, which just extended).

When we swap `nums[mid] == 2` with `nums[hi]`, the value that comes to `mid` was from the unexamined region — it could be anything. So we must not advance `mid`; examine this new value on the next iteration.

This is the subtlety that makes the algorithm work. Getting it wrong (e.g., always advancing mid) introduces bugs.

----------------------------------------

## Step 6: Trace on `[2, 0, 2, 1, 1, 0]`

```
lo=0, mid=0, hi=5. Array: [2, 0, 2, 1, 1, 0]

mid=0, val=2: swap with hi=5. Array: [0, 0, 2, 1, 1, 2]. hi=4. mid stays.
mid=0, val=0: swap with lo=0 (no-op). Array unchanged. lo=1, mid=1.
mid=1, val=0: swap with lo=1 (no-op). lo=2, mid=2.
mid=2, val=2: swap with hi=4. Array: [0, 0, 1, 1, 2, 2]. hi=3. mid stays.
mid=2, val=1: advance. mid=3.
mid=3, val=1: advance. mid=4.
mid=4, hi=3. Loop exits (mid > hi).
```

Final array: `[0, 0, 1, 1, 2, 2]`. ✓

Note the moment at mid=0 after swapping the 2 with hi=5: the value that came to position 0 was `nums[5] = 0`. We didn't advance mid — and correctly so, because the next iteration needs to process this 0.

----------------------------------------

## Step 7: Name It

This is the classic **Dutch National Flag algorithm**, devised by Edsger Dijkstra. The name comes from the Dutch flag having three colored horizontal stripes (red, white, blue), matching the three values we're partitioning.

The algorithm's core trick — three pointers maintaining three regions — generalizes to any **3-way partition** problem: sort 0/1/2, split array around a pivot into less/equal/greater, etc.

For **quicksort with 3-way partitioning** (handling arrays with many duplicate keys), this is the partition step.

----------------------------------------

## Step 8: Complexity

Time: each element is examined at most twice (once when it's at mid, possibly once more after being swapped to mid from hi). **O(n)**.
Space: three pointers. **O(1)**.
Passes: **one**.

Beats counting sort's two-pass by being single-pass, though both are O(n).

----------------------------------------

## Step 9: C++ Implementation

```cpp
void sortColors(vector<int>& nums) {
    int lo = 0, mid = 0, hi = nums.size() - 1;
    while (mid <= hi) {
        if (nums[mid] == 0) {
            swap(nums[lo], nums[mid]);
            lo++;
            mid++;
        } else if (nums[mid] == 1) {
            mid++;
        } else {   // nums[mid] == 2
            swap(nums[mid], nums[hi]);
            hi--;
            // don't advance mid — we need to examine the new value
        }
    }
}
```

The three branches mirror the three cases. Clean. The critical detail: **don't increment mid in the `== 2` branch**.

----------------------------------------

## Step 10: Follow-up Questions

- **More than 3 distinct values (e.g., 0, 1, 2, 3).** Dutch flag doesn't directly extend. Use counting sort (O(n + k)) or multi-pass Dutch flag.
- **What if values are arbitrary ints with a known pivot?** 3-way partition around the pivot: less, equal, greater. Same structure.
- **Handle arrays with very few distinct values (say k distinct).** Counting sort still O(n + k). For small k, fast.
- **Stable sort (preserve relative order among equal elements).** Dutch flag is not stable. Use counting sort or stable_sort.
- **In a streaming setting where the array size is unknown.** Buffer chunks; sort each. Less clean.
- **External sort for massive arrays on disk.** Partition and sort chunks that fit in memory; merge.
