# Single Element in a Sorted Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Single_Element_in_a_Sorted_Array.md`](../Single_Element_in_a_Sorted_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/single-element-in-a-sorted-array/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **This is binary search using a PARITY INVARIANT.** The lesson: **the structural property "pairs start at even indices" creates a monotonic predicate you can binary-search.** Once the unique element appears, the alignment SHIFTS — and that shift is what you detect. **Read [`Find_Peak_Element.md`](./Find_Peak_Element.md) first** for the "binary search on local property" framing.

**Map of this file (10 short sections):**

1. Read the problem
2. The XOR shortcut (and why it's O(n))
3. The parity observation
4. Why this is monotonic — and binary-searchable
5. The "force mid to even" trick
6. Code
7. Trace it
8. Common pitfalls
9. Why this isn't just a curiosity
10. The shape — binary search via invariants

---

## 1. Read the problem

You're given a **sorted** array `nums` where every element appears **exactly twice**, EXCEPT for ONE element which appears once. Find that single element.

**Required:** O(log n) time, O(1) space.

**Examples:**

- `nums = [1, 1, 2, 3, 3, 4, 4, 8, 8]` → single = 2.
- `nums = [3, 3, 7, 7, 10, 11, 11]` → single = 10.
- `nums = [1, 1, 2]` → single = 2.
- `nums = [1]` → single = 1.

Sorted ascending, with duplicates aligned in pairs except for one outlier.

---

## 2. The XOR shortcut (and why it's O(n))

**XOR trick:** XOR all elements together. Every pair cancels (`x XOR x = 0`). The lonely element survives.

```
result = 0
for x in nums:
    result ^= x
return result
```

> **Mini-refresher: XOR properties.**
>
> - `x XOR x = 0` (any value XOR'd with itself is zero).
> - `x XOR 0 = x` (XOR with zero is identity).
> - XOR is commutative and associative — order doesn't matter.
>
> So XOR-ing a bunch of values cancels every pair, leaving only the un-paired one.

XOR works. But it's **O(n)** time — every element must be touched. The problem demands **O(log n)**, so XOR isn't good enough here.

We need to exploit the SORTED property to do better.

---

## 3. The parity observation

Look at the indices, not just the values:

```
idx:  0  1   2   3  4   5  6   7  8
val:  1  1   2   3  3   4  4   8  8
```

Pairs:
- (idx 0, idx 1) = (1, 1). Pair starts at **even** index 0.
- (idx 3, idx 4) = (3, 3). Pair starts at **odd** index 3.
- (idx 5, idx 6) = (4, 4). Pair starts at **odd** index 5.
- (idx 7, idx 8) = (8, 8). Pair starts at **odd** index 7.

Between idx 1 and idx 3, the single element `2` (at idx 2) DISRUPTED the alignment. Before the single, pairs start at EVEN indices. After the single, pairs start at ODD indices.

**Predicate:** for any EVEN index `m`, is `nums[m] == nums[m + 1]`?
- **Before** the single: YES (the even index is the START of a pair).
- **At or after** the single: NO (the alignment has shifted; the even index is the END of a pair, and the next value is different).

This predicate is monotonic — it transitions from TRUE to FALSE exactly once, at the single element's position (or just before it).

> **Mini-refresher: same idea, drawn out.**
>
> ```
> idx:  0  1 |  2  |   3  4   5  6   7  8
> val:  1  1 |  2  |   3  3   4  4   8  8
>           ↑        ↑
>           pair    single        pair
>           start   element       start (now odd!)
> ```
>
> The single "pushes" everything after it by ONE position. So `nums[even] == nums[even + 1]` holds only on the LEFT side of the single.

---

## 4. Why this is monotonic — and binary-searchable

The predicate `P(m) = (nums[m] == nums[m + 1])` for even `m`:

- Before the single's position: TRUE.
- At or after the single's position: FALSE.

This is exactly the kind of monotonic FALSE→TRUE (or here, TRUE→FALSE) boundary that binary search FINDS.

We binary-search for the SMALLEST EVEN INDEX where the predicate is FALSE. That's the single element's index.

```
lo, hi = 0, n - 1
while lo < hi:
    mid = (lo + hi) // 2
    if mid is ODD: mid -= 1     # force mid to be even
    if nums[mid] == nums[mid + 1]:
        # we're on the left side of the single
        lo = mid + 2
    else:
        # we're at the single (mid) or to its right
        hi = mid
return nums[lo]
```

When `lo == hi`, that index is the single.

---

## 5. The "force mid to even" trick

The predicate compares `nums[m]` and `nums[m + 1]` ASSUMING `m` is the START of a pair (even index in the "before" region).

If `mid` lands on an ODD index, comparing `nums[mid]` and `nums[mid + 1]` would be checking a SHIFTED pair — possibly misleading.

To stay aligned, force `mid` to an EVEN index. Two equivalent ways:

```
if mid % 2 == 1: mid -= 1
```

or with bitwise:

```
mid &= ~1     # clear the least significant bit
```

Both round `mid` down to the nearest even index.

> **Mini-refresher: why we don't lose progress.**
>
> Forcing `mid` from odd to (`mid - 1`) seems like we're moving backward. We're not — we're just adjusting the COMPARISON POINT. The search range `[lo, hi]` doesn't change. We're picking the right EVEN mid to test the predicate at.
>
> The search range still shrinks by half (or close to it) each iteration.

---

## 6. Code

**C++:**

```cpp
int singleNonDuplicate(vector<int>& nums) {
    int lo = 0, hi = nums.size() - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (mid % 2 == 1) mid--;                  // force mid to be even
        if (nums[mid] == nums[mid + 1]) {
            lo = mid + 2;                          // single is to the right
        } else {
            hi = mid;                              // single is here or to the left
        }
    }
    return nums[lo];
}
```

**Python:**

```python
def singleNonDuplicate(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if mid % 2 == 1:
            mid -= 1
        if nums[mid] == nums[mid + 1]:
            lo = mid + 2
        else:
            hi = mid
    return nums[lo]
```

**JavaScript:**

```javascript
function singleNonDuplicate(nums) {
    let lo = 0, hi = nums.length - 1;
    while (lo < hi) {
        let mid = Math.floor((lo + hi) / 2);
        if (mid % 2 === 1) mid--;
        if (nums[mid] === nums[mid + 1]) {
            lo = mid + 2;
        } else {
            hi = mid;
        }
    }
    return nums[lo];
}
```

Complexity: **O(log n) time, O(1) space.**

---

## 7. Trace it

`nums = [1, 1, 2, 3, 3, 4, 4, 8, 8]` (n = 9):

```
lo=0, hi=8.

Iter 1: mid = (0+8)/2 = 4. Even.
  nums[4]=3, nums[5]=4. NOT equal.
  → hi = 4.

Iter 2: lo=0, hi=4. mid = 2. Even.
  nums[2]=2, nums[3]=3. NOT equal.
  → hi = 2.

Iter 3: lo=0, hi=2. mid = 1. ODD → mid-- → mid = 0.
  nums[0]=1, nums[1]=1. EQUAL.
  → lo = mid + 2 = 2.

lo=2, hi=2. EXIT.

Return nums[2] = 2.  ✓
```

`nums = [3, 3, 7, 7, 10, 11, 11]` (n = 7):

```
lo=0, hi=6.

Iter 1: mid=3. ODD → mid=2.
  nums[2]=7, nums[3]=7. EQUAL.
  → lo = 4.

Iter 2: lo=4, hi=6. mid=5. ODD → mid=4.
  nums[4]=10, nums[5]=11. NOT equal.
  → hi = 4.

lo=4, hi=4. EXIT.

Return nums[4] = 10.  ✓
```

---

## 8. Common pitfalls

1. **Forgetting to force mid to even.** Without this, the predicate becomes meaningless (you'd be comparing the WRONG pair structure).

2. **Off-by-one in `lo = mid + 2`.** When the predicate holds at `mid` (we're on the left of the single), the next candidate even index is `mid + 2`, NOT `mid + 1`. Pairs start every TWO indices.

3. **Off-by-one in `hi = mid`.** Don't subtract — `mid` itself could be the single (when `nums[mid] != nums[mid + 1]`).

4. **Using `lo <= hi` instead of `lo < hi`.** Combined with `hi = mid`, that loops forever.

5. **Trying XOR.** It works but is O(n). Doesn't satisfy the constraint.

6. **Trying to compare `nums[mid - 1]` instead of `nums[mid + 1]`.** With `mid` forced even, `nums[mid - 1]` would only make sense for an "after" comparison. Stick with `nums[mid]` vs `nums[mid + 1]`.

7. **Treating the array length as always odd.** It IS odd (n = 2k + 1 for k pairs and 1 single), but you don't NEED to assume that explicitly. The algorithm handles correctly regardless.

8. **Forgetting that this assumes the input STRUCTURE.** If pairs aren't aligned (e.g., the input is not sorted, or duplicates appear in different patterns), the parity invariant breaks. The problem GUARANTEES the structure; trust the spec.

---

## 9. Why this isn't just a curiosity

The "parity / pair / alignment" pattern shows up in several problems:

- **Finding a missing number in [0, n] with one missing** can use binary search on `(nums[i] != i)`.
- **Finding a duplicate or missing element in cyclic / interleaved arrays** uses similar boundary-detection logic.
- **Pair-based structural invariants** (e.g., "every odd index has a paired prev" in interleaved arrays) are common in competitive problems.

The technique you learn here — INVARIANT-BASED binary search — generalizes.

---

## 10. The shape — binary search via invariants

The pattern:

> **"Identify a STRUCTURAL INVARIANT that holds in one part of the array and breaks in the other. Binary search the boundary where it breaks."**

| Problem | Invariant |
|---|---|
| **This problem** | `nums[even] == nums[even + 1]` (pairs aligned) |
| First Bad Version | "all versions ≤ i are good" |
| Missing Number (sorted [0, n]) | `nums[i] == i` |
| Find K-th Missing Positive Number | `nums[i] - (i + 1)` = missing count |
| First Negative in Sorted Array | `nums[i] >= 0` |
| Length of LIS (O(n log n)) | tails array invariant |

**Pattern to internalize:**

> "Binary search isn't just about VALUES. It's about MONOTONIC PREDICATES. Whenever you can compute a boolean function `P(i)` over indices, and `P` is monotonic, binary-search the boundary in O(log n)."

---

> **Self-check — the question to ask next time.**
>
> When you face a sorted-but-special-pattern problem requiring O(log n), ask:
>
> > **"Is there an INVARIANT (parity, equality, comparison) that holds on one side of the answer and breaks on the other? If so, binary-search that boundary."**
>
> If yes, you've found the structural hook.

---

## Cross-references

- **Reference card (post-mastery):** [`../Single_Element_in_a_Sorted_Array.md`](../Single_Element_in_a_Sorted_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_Peak_Element.md`](./Find_Peak_Element.md), [`Search_in_Rotated_Sorted_Array.md`](./Search_in_Rotated_Sorted_Array.md).
  - Coming next: [`Search_a_2D_Matrix.md`](./Search_a_2D_Matrix.md).
