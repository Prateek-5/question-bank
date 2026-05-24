# Sort Colors — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Sort_Colors.md`](../Sort_Colors.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/sort-colors/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The introduction to the Dutch National Flag algorithm.** The lesson: **three pointers (`lo`, `mid`, `hi`) maintain four regions of the array — sorted 0s, sorted 1s, unexamined, sorted 2s. One pass, O(1) space.** This 3-way partition is used as a subroutine in quicksort with duplicates.

**Map of this file (10 short sections):**

1. Read the problem
2. The two-pass solutions
3. The three regions invariant
4. The three cases on `nums[mid]`
5. Why `nums[mid] == 2` swap doesn't advance mid
6. Code
7. Trace it
8. Why the asymmetry (case 0 vs case 2)
9. Common pitfalls
10. The shape — 3-way partition

---

## 1. Read the problem

Given an array `nums` with `n` elements, where each element is `0`, `1`, or `2`, **sort the array IN PLACE** so that all `0`s come first, then all `1`s, then all `2`s.

**Required:** one pass, O(1) extra space.

**Examples:**

- `[2, 0, 2, 1, 1, 0]` → `[0, 0, 1, 1, 2, 2]`.
- `[2, 0, 1]` → `[0, 1, 2]`.
- `[0]` → `[0]`.

---

## 2. The two-pass solutions

**Counting sort (two-pass):**

```
count[0], count[1], count[2] = 0, 0, 0
for x in nums: count[x] += 1
i = 0
for c in [0, 1, 2]:
    for _ in range(count[c]):
        nums[i] = c; i += 1
```

O(n), O(1) space. Correct, but TWO passes (one to count, one to write).

**Standard sort:** `nums.sort()`. O(n log n). Wasteful for only 3 distinct values.

The challenge: **ONE pass, O(1) space.** That requires the Dutch Flag.

---

## 3. The three regions invariant

We maintain three pointers and four regions of the array.

- `lo`: boundary BEFORE which everything is 0.
- `mid`: the CURRENT EXAMINING position. Everything `[lo, mid)` is 1.
- `hi`: boundary AFTER which everything is 2.

**Invariant:**

```
[0, lo)        all 0s     ← finalized
[lo, mid)      all 1s     ← finalized
[mid, hi]      unexamined ← we're working here
(hi, n)        all 2s     ← finalized
```

Initially: `lo = 0, mid = 0, hi = n - 1`. The entire array is unexamined.

We're done when `mid > hi` (no more unexamined positions).

> **Mini-refresher: half-open vs closed intervals.**
>
> `[lo, mid)` means "start at lo, end before mid" — inclusive of lo, exclusive of mid. Common in array notation.
>
> `[mid, hi]` is "inclusive of both endpoints."
>
> Mixing notations is fine if you're CONSISTENT about WHERE THE BOUNDARIES POINT (just-before vs just-after). The Dutch flag mixes them naturally.

---

## 4. The three cases on `nums[mid]`

At each step, examine `nums[mid]`:

**Case `nums[mid] == 0`:**
- It belongs in the 0s-region. Swap with `nums[lo]`.
- The value that comes TO `mid` from `lo` was at the START of the 1s-region, so it was a 1. The new `[lo, mid + 1)` is still all 1s.
- Advance BOTH `lo` (the 0s-region grew) AND `mid` (we know the value just moved to `mid` is a correct 1).

**Case `nums[mid] == 1`:**
- It's already in the right region. Just advance `mid`.

**Case `nums[mid] == 2`:**
- It belongs in the 2s-region. Swap with `nums[hi]`.
- The value that comes TO `mid` from `hi` was UNEXAMINED — could be 0, 1, or 2.
- Decrement `hi` (the 2s-region grew). DO NOT advance `mid` — we need to examine the new value at `mid` next.

---

## 5. Why `nums[mid] == 2` swap doesn't advance mid

This is the trickiest detail. Let's understand WHY.

When `nums[mid] == 0`:
- Before swap: `nums[lo]` is a 1 (in the 1s-region). `nums[mid]` is a 0.
- After swap: `nums[lo]` is 0 (correct for the 0s-region). `nums[mid]` is 1 (correct for the 1s-region).
- Both positions are now correct → advance both lo and mid.

When `nums[mid] == 2`:
- Before swap: `nums[hi]` is UNEXAMINED (could be 0, 1, or 2). `nums[mid]` is 2.
- After swap: `nums[hi]` is 2 (correct for the 2s-region). `nums[mid]` is whatever was at `hi` — STILL UNEXAMINED.
- We don't know if the new `nums[mid]` is correct. We must re-examine it.
- So advance hi (decrement), but DON'T advance mid.

> **Mini-refresher: don't advance past unexamined values.**
>
> The general rule: only advance the cursor past KNOWN-CORRECT values. After swap with `lo`, the new mid is a known 1. After swap with `hi`, the new mid is unknown — re-examine.

---

## 6. Code

**C++:**

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
        } else {  // nums[mid] == 2
            swap(nums[mid], nums[hi]);
            hi--;
            // do NOT advance mid
        }
    }
}
```

**Python:**

```python
def sortColors(nums):
    lo, mid, hi = 0, 0, len(nums) - 1
    while mid <= hi:
        if nums[mid] == 0:
            nums[lo], nums[mid] = nums[mid], nums[lo]
            lo += 1
            mid += 1
        elif nums[mid] == 1:
            mid += 1
        else:
            nums[mid], nums[hi] = nums[hi], nums[mid]
            hi -= 1
```

**JavaScript:**

```javascript
function sortColors(nums) {
    let lo = 0, mid = 0, hi = nums.length - 1;
    while (mid <= hi) {
        if (nums[mid] === 0) {
            [nums[lo], nums[mid]] = [nums[mid], nums[lo]];
            lo++; mid++;
        } else if (nums[mid] === 1) {
            mid++;
        } else {
            [nums[mid], nums[hi]] = [nums[hi], nums[mid]];
            hi--;
        }
    }
}
```

Complexity: **O(n) time, O(1) space, ONE pass.**

---

## 7. Trace it

**`nums = [2, 0, 2, 1, 1, 0]`.**

```
Initial: lo=0, mid=0, hi=5. Array = [2, 0, 2, 1, 1, 0].

mid=0, val=2: swap mid and hi=5. Array=[0, 0, 2, 1, 1, 2]. hi=4. mid stays.
mid=0, val=0: swap mid and lo=0 (no-op). lo=1, mid=1.
mid=1, val=0: swap mid and lo=1 (no-op). lo=2, mid=2.
mid=2, val=2: swap mid and hi=4. Array=[0, 0, 1, 1, 2, 2]. hi=3. mid stays.
mid=2, val=1: advance. mid=3.
mid=3, val=1: advance. mid=4.

mid=4 > hi=3. EXIT.

Final: [0, 0, 1, 1, 2, 2].  ✓
```

The first iteration's swap brought a 0 to position 0 — we re-examined it (since we didn't advance mid in the `== 2` branch). The 0 case then moved it correctly.

---

## 8. Why the asymmetry (case 0 vs case 2)

Some students wonder: why is the `== 0` case symmetric-looking but the `== 2` case asymmetric?

Because the SWAP DESTINATION differs:
- Swapping with `nums[lo]` brings in a value from the FINALIZED 1s region — known to be 1.
- Swapping with `nums[hi]` brings in a value from the UNEXAMINED region — unknown.

So:
- `== 0` case: both pointers move (we know what came in).
- `== 2` case: only `hi` moves (we don't know what came in).

The asymmetry isn't arbitrary — it follows from where the regions sit relative to `mid`.

---

## 9. Common pitfalls

1. **Advancing `mid` in the `== 2` case.** The MOST common bug. You'll skip over a value that came from `hi` without examining it.

2. **Using `mid < hi` instead of `mid <= hi`.** With `<`, when `mid == hi` (a single unexamined element), you'd skip it. Use `<=`.

3. **Forgetting to handle the `== 1` case.** Some try only two branches; you need three.

4. **Using a different partition pattern.** Some try to start `mid = lo` always — that's correct but redundant; just initialize `mid = 0`.

5. **Off-by-one in `hi` initialization.** Use `hi = n - 1` (the last valid index). Using `n` causes out-of-bounds on the first `nums[hi]` access.

6. **Believing this is O(n log n).** It's O(n) — single pass.

7. **Trying to "stable sort."** Dutch flag is NOT stable. The relative order of equal-value elements is not preserved. Counting sort is stable.

8. **Forgetting to handle empty input.** Initial `hi = -1, mid = 0, mid > hi` → loop doesn't run. Returns the empty input. Correct.

---

## 10. The shape — 3-way partition

The Dutch Flag algorithm is the **3-way partition** primitive — split an array into THREE parts based on comparison with a pivot.

Where it's used:

| Problem | Application |
|---|---|
| **This problem** | sort 0/1/2 |
| Quicksort with 3-way partition | handles many duplicates efficiently |
| Sort by parity | partition into 2 (could be Dutch with `mid = 1` case absent) |
| Wiggle Sort II | 3-way partition then placement |
| Move zeroes to the end | simpler 2-way partition |
| Sort an array of two values | 2-way Dutch (one fewer pointer) |
| Group elements into < pivot / = pivot / > pivot | exact match for Dutch |

**Pattern to internalize:**

> "When you need to sort an array based on a 3-valued comparison (less / equal / greater), use Dutch National Flag: three pointers, four regions, one pass."

For more than 3 values, fall back to counting sort.

---

> **Self-check — the question to ask next time.**
>
> When you face an array with only a FEW distinct values that needs in-place sorting, ask:
>
> > **"Can I partition by 'less / equal / greater' using three pointers — Dutch National Flag? One pass, O(1) space."**
>
> If yes, you've got Dijkstra's algorithm from 1976.

---

## Cross-references

- **Reference card (post-mastery):** [`../Sort_Colors.md`](../Sort_Colors.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Kth_Largest_Element_in_an_Array.md`](./Kth_Largest_Element_in_an_Array.md) — quickselect uses 2-way partition.
  - Coming after: Reverse_Pairs, Count_of_Smaller_Numbers_After_Self — merge sort.
