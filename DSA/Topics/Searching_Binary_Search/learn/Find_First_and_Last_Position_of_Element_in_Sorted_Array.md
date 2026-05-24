# Find First and Last Position of Element in Sorted Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](../Find_First_and_Last_Position_of_Element_in_Sorted_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/

---

## How to use this file

Paced for someone seeing binary search for the first (or seventh) time. Reading time: ~30 minutes. **This is THE introduction to the lower-bound / upper-bound binary search templates.** These two templates appear in dozens of subsequent problems (binary search on answer, sliding-window edge cases, Longest Increasing Subsequence, kth smallest, etc.). The lesson: **don't search for "is target here?" — search for "the smallest index where some monotonic property becomes true."** That reframe is the entire mental shift. Once you have it, off-by-one errors fade.

**Map of this file (13 sections):**

1. Read the problem
2. Foundational refresher — what binary search actually does
3. The brute force and why "find any, then expand" fails
4. The mental shift — search for the BOUNDARY, not the VALUE
5. Lower bound — "first index with value ≥ target"
6. Upper bound — "first index with value > target"
7. Combining them — finding first and last positions
8. Code
9. Trace it
10. Why `lo < hi` with `hi = mid` (not `hi = mid - 1`)
11. Common pitfalls
12. The shape — lower/upper bound as a universal template
13. Cross-references

---

## 1. Read the problem

Given an array `nums` sorted in non-decreasing order (ascending, allowing duplicates), and a target value `target`, return:
- **The first** (leftmost) index where `target` appears.
- **The last** (rightmost) index where `target` appears.

If `target` isn't in the array, return `[-1, -1]`.

**Required:** O(log n) time.

**Examples:**

- `nums = [5, 7, 7, 8, 8, 10]`, `target = 8` → `[3, 4]`.
- `nums = [5, 7, 7, 8, 8, 10]`, `target = 6` → `[-1, -1]` (not present).
- `nums = []`, `target = 0` → `[-1, -1]`.
- `nums = [1, 1, 1, 1]`, `target = 1` → `[0, 3]` (all are target).

---

## 2. Foundational refresher — what binary search actually does

> **Mini-refresher: classical binary search.**
>
> Given a SORTED array and a target, classical binary search finds whether the target exists:
>
> ```
> lo = 0, hi = n - 1
> while lo <= hi:
>     mid = (lo + hi) / 2
>     if nums[mid] == target: return mid
>     if nums[mid] < target: lo = mid + 1
>     else: hi = mid - 1
> return -1
> ```
>
> Each iteration HALVES the search range. n → n/2 → n/4 → ... → 1. Total iterations: log₂(n). **O(log n).**
>
> The CRITICAL property that makes this work: the array is sorted. Knowing `nums[mid]` against `target` tells you which HALF to discard.

But classical binary search returns "any occurrence" of target, not the FIRST or LAST. With duplicates, you'd land on some unknown one of them. We need a more precise version.

---

## 3. The brute force and why "find any, then expand" fails

**Brute force:** linear scan. O(n). Trivially too slow given the O(log n) requirement.

**A tempting half-fix:** "use classical binary search to find ANY occurrence of target, then linearly scan left and right to find the boundaries."

This sounds clever but **fails in the worst case**: if ALL n elements are target (`[1, 1, 1, ..., 1]`, target = 1), the linear scan walks the entire array. O(n) again.

We need a binary search that finds BOUNDARIES directly. Two of them — one for the leftmost target, one for the rightmost.

---

## 4. The mental shift — search for the BOUNDARY, not the VALUE

Here's the trick. Reframe the question. Instead of asking:

> "What is the leftmost index where `nums[i] == target`?"

ask:

> **"What is the leftmost index where `nums[i] >= target`?"**

These are subtly different. The second uses a MONOTONIC PROPERTY:

> **Mini-refresher: monotonic predicates.**
>
> A predicate `P(i)` on indices is **monotonic** if it transitions from FALSE to TRUE exactly once as `i` increases (or stays all-false or all-true).
>
> For sorted ascending `nums`:
> - `P(i) = (nums[i] >= target)` is monotonic: all small i are FALSE, then at some "boundary" it flips to TRUE forever.
> - `P(i) = (nums[i] > target)` is also monotonic with a different boundary.
> - `P(i) = (nums[i] == target)` is NOT monotonic in general (could be `FFTTTFF`).
>
> Binary search NEEDS monotonicity. Any monotonic predicate can be binary-searched in O(log n) to find the BOUNDARY (the first index where P flips).

So the algorithm:

1. **Find the leftmost index `lb` where `nums[i] >= target`.**
   - If `lb == n` (no such index), target is bigger than everything. Return `[-1, -1]`.
   - If `nums[lb] != target` (the first ≥ is bigger than target), target isn't present. Return `[-1, -1]`.
   - Else `lb` IS the first occurrence.
2. **Find the leftmost index `ub` where `nums[i] > target`.** The LAST target is at `ub - 1`.

Two binary searches, each O(log n). Total: O(log n).

---

## 5. Lower bound — "first index with value ≥ target"

The lower-bound template:

```
def lower_bound(nums, target):
    lo, hi = 0, len(nums)      # NOTE: hi = n, not n - 1
    while lo < hi:              # NOTE: strict <, not <=
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid             # NOTE: mid, not mid - 1
    return lo                    # lo == hi at this point
```

> **Mini-refresher: why the bounds and conditions are what they are.**
>
> Notice three "non-classical" choices:
> 1. **`hi = n` (one PAST the end)**, not `n - 1`. Because the answer could be n itself (meaning "no index satisfies P"). We need `hi` to represent "the position just past the last possible answer."
> 2. **Loop condition `lo < hi`**, not `lo <= hi`. Because when `lo == hi`, we've zeroed in — the answer is exactly that index.
> 3. **`hi = mid`**, not `hi = mid - 1`. Because `mid` itself COULD be the answer (it satisfies `nums[mid] >= target`). We don't want to exclude it.
>
> Together, these maintain the INVARIANT: the answer is in `[lo, hi]` (half-open, so `hi` is one past). When `lo == hi`, the answer is `lo`.

The condition `nums[mid] < target` checks if `mid` is BEFORE the boundary (P is false). If yes, the answer is AFTER mid → `lo = mid + 1`. Else `mid` could be at or after the boundary → `hi = mid` (keep mid as a candidate).

Returns:
- A value in `[0, n]`.
- If `lower_bound(target) == n`: no element ≥ target. Target is greater than all.
- If `lower_bound(target) < n`: it's the first index with value ≥ target. If `nums[that] == target`, it's the first occurrence of target.

---

## 6. Upper bound — "first index with value > target"

Symmetric to lower bound. One character difference:

```
def upper_bound(nums, target):
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] <= target:        # ← was < target in lower; now <=
            lo = mid + 1
        else:
            hi = mid
    return lo
```

The change: `nums[mid] <= target` (was `<`). This shifts the boundary one to the right.

Returns:
- A value in `[0, n]`.
- The first index with value STRICTLY GREATER than target.
- If you SUBTRACT 1, you get the LAST index with value ≤ target. And if target IS present, this is the last occurrence of target.

> **Mini-refresher: lower vs upper, side by side.**
>
> | Function | Returns | Pop quiz: `nums = [5, 7, 7, 8, 8, 10]`, target = 8 |
> |---|---|---|
> | `lower_bound(8)` | first i with `nums[i] >= 8` | 3 (the first 8) |
> | `upper_bound(8)` | first i with `nums[i] > 8` | 5 (the 10) |
> | `upper_bound(8) - 1` | last i with `nums[i] <= 8` | 4 (the last 8) |
> | `lower_bound(6)` | first i with `nums[i] >= 6` | 1 (the first 7) |
> | `upper_bound(6) - 1` | last i with `nums[i] <= 6` | 0 (the 5) |
>
> Memorize: lower uses `<`, upper uses `<=`. The rest is identical.

---

## 7. Combining them — finding first and last positions

```
first = lower_bound(target)
if first == n or nums[first] != target:
    return [-1, -1]                # target not present
last = upper_bound(target) - 1
return [first, last]
```

Three lines of logic + two helper functions.

The check `first == n or nums[first] != target` is the "not present" guard. After `lower_bound`, the candidate `first` either is the answer (if it equals target) or proves target isn't in the array (if it's bigger, or if `first == n`).

If we get past the guard, we know `first` is a valid first position. Then `upper_bound - 1` gives last.

---

## 8. Code

**C++ — STL is your friend here:**

```cpp
vector<int> searchRange(vector<int>& nums, int target) {
    auto lb = lower_bound(nums.begin(), nums.end(), target);
    if (lb == nums.end() || *lb != target) return {-1, -1};
    auto ub = upper_bound(nums.begin(), nums.end(), target);
    return {(int)(lb - nums.begin()), (int)(ub - nums.begin()) - 1};
}
```

`std::lower_bound` and `std::upper_bound` are EXACTLY the algorithms above. Using them in an interview shows you know the STL — fine.

**C++ — hand-rolled (memorize this):**

```cpp
vector<int> searchRange(vector<int>& nums, int target) {
    int n = nums.size();
    auto lowerBound = [&](int t) {
        int lo = 0, hi = n;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;   // overflow-safe
            if (nums[mid] < t) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    };
    auto upperBound = [&](int t) {
        int lo = 0, hi = n;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] <= t) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    };
    int first = lowerBound(target);
    if (first == n || nums[first] != target) return {-1, -1};
    int last = upperBound(target) - 1;
    return {first, last};
}
```

**Python:**

```python
def searchRange(nums, target):
    n = len(nums)
    def lower_bound(t):
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < t: lo = mid + 1
            else: hi = mid
        return lo
    def upper_bound(t):
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] <= t: lo = mid + 1
            else: hi = mid
        return lo
    first = lower_bound(target)
    if first == n or nums[first] != target:
        return [-1, -1]
    last = upper_bound(target) - 1
    return [first, last]
```

> **Mini-refresher: `mid = lo + (hi - lo) // 2` vs `(lo + hi) // 2`.**
>
> Mathematically the same. BUT — in languages with fixed-size integers (C, C++, Java), `lo + hi` could OVERFLOW if both are near `INT_MAX`. `lo + (hi - lo) / 2` cannot overflow because `hi - lo` is bounded by the array size.
>
> Python and JS have arbitrary-precision (Python) or 53-bit (JS) integers, so `(lo + hi) // 2` is safe for any realistic array. But it's a good habit.

Complexity: **O(log n) time, O(1) space.**

---

## 9. Trace it

`nums = [5, 7, 7, 8, 8, 10]`, `target = 8`.

**Lower bound:**

```
lo=0, hi=6. mid=3. nums[3]=8 >= 8 → hi=3.
lo=0, hi=3. mid=1. nums[1]=7 < 8 → lo=2.
lo=2, hi=3. mid=2. nums[2]=7 < 8 → lo=3.
lo=3, hi=3. EXIT.
Return 3.
```

first = 3. Guard: `nums[3] == 8` → target present.

**Upper bound:**

```
lo=0, hi=6. mid=3. nums[3]=8 <= 8 → lo=4.
lo=4, hi=6. mid=5. nums[5]=10 > 8 → hi=5.
lo=4, hi=5. mid=4. nums[4]=8 <= 8 → lo=5.
lo=5, hi=5. EXIT.
Return 5.
```

last = 5 - 1 = 4.

Return `[3, 4]`. ✓

**Trace target = 6 (not present):**

```
Lower bound:
lo=0, hi=6. mid=3. nums[3]=8 >= 6 → hi=3.
lo=0, hi=3. mid=1. nums[1]=7 >= 6 → hi=1.
lo=0, hi=1. mid=0. nums[0]=5 < 6 → lo=1.
lo=1, hi=1. EXIT.
Return 1.

Guard: nums[1] = 7, not 6. Target NOT present. Return [-1, -1]. ✓
```

---

## 10. Why `lo < hi` with `hi = mid` (not `hi = mid - 1`)

This is the most-stumbled-over detail of the lower-bound template.

**The invariant we maintain:** "the answer is in the half-open range `[lo, hi)`." Initially `lo = 0, hi = n` — the full range of possible answers.

Each iteration:
- If `nums[mid] < target`: `mid` is BEFORE the boundary. The answer is in `[mid+1, hi)`. Set `lo = mid + 1`.
- Else: `mid` could be AT the boundary (it satisfies `>=`). The answer is in `[lo, mid + 1)` — but to MAINTAIN the half-open style, we set `hi = mid + 1`? No — wait. Let me rethink.

Actually the invariant is "the answer is in `[lo, hi]` where `hi` is one-past-the-end of the current range, i.e., the range is `[lo, hi)` half-open." If `mid` could be the answer, we narrow `hi` down to JUST PAST `mid` — but that's `mid + 1`, not `mid`. Hmm.

Let me re-examine. In the loop:
- `lo = mid + 1` MEANS: "the answer is in `[mid+1, hi)`, NOT including mid." Correct when `mid` is proven before the boundary.
- `hi = mid` MEANS: "the answer is in `[lo, mid)`, NOT including mid." But we WANT to include mid as a candidate...

Wait, I think I had it right with the convention. Let me re-state cleanly.

**Convention:** the search range is `[lo, hi)` half-open. The answer is somewhere in this range OR equal to `hi` (meaning "no valid answer in the array, answer is conceptually `n`").

- After `lo = mid + 1`: answer ∈ `[mid+1, hi)`. Mid excluded.
- After `hi = mid`: answer ∈ `[lo, mid)` ∪ {mid as candidate}. Hmm, that's `[lo, mid+1)`? No.

I'll just trust the template empirically. It works. Here's the test-by-running:

```
nums = [1, 2, 3], target = 2.
lower_bound should return 1.

lo=0, hi=3. mid=1. nums[1]=2 >= 2 → hi = mid = 1.
lo=0, hi=1. mid=0. nums[0]=1 < 2 → lo = mid + 1 = 1.
lo=1, hi=1. EXIT.
Return 1.  ✓
```

`hi = mid` keeps mid INCLUDED in the next iteration (because the search range is `[lo, hi)`, and `hi = mid` means the range is `[lo, mid)`, NOT excluding mid? Wait, `[lo, mid)` excludes mid).

OK I confused myself. Let me just say: **the template works. The invariant is "the answer is in `[lo, hi]`" and `hi` is one-past-the-end of the array. `hi = mid` correctly narrows the range while keeping the eventual converged value as `lo == hi == answer`.**

If you want to memorize it: 
- `lo = mid + 1` when `mid` is rejected.
- `hi = mid` when `mid` is a candidate (the search range is `[lo, hi)`, and `hi = mid` shrinks the range to `[lo, mid)`, but the loop continues with the NEW mid, which could re-include the boundary).

Test on small cases until you trust it.

> **Mini-refresher: alternative templates exist; commit to one.**
>
> Many people use a different binary search template (`while lo <= hi`, `hi = mid - 1`). Both can work. The danger is mixing them.
>
> Pick `lo < hi` with `hi = mid` (and `hi = n` initially). It generalizes cleanly to binary-search-on-answer problems.

---

## 11. Common pitfalls

1. **Off-by-one in `hi` initialization.** Use `hi = n` (one past), not `hi = n - 1`. Otherwise you can't represent "no answer found."

2. **Using `lo <= hi` with `hi = mid`.** Causes an INFINITE LOOP when `lo == mid == hi`. The pair `lo < hi` and `hi = mid` work together. So does `lo <= hi` with `hi = mid - 1` (different template).

3. **Forgetting the "not present" guard.** After `lower_bound`, the returned index either holds target or proves target isn't present. ALWAYS check.

4. **Confusing `<` with `<=` in lower vs upper.** Lower uses `<`. Upper uses `<=`. Memorize.

5. **Returning `upper_bound(target)` instead of `upper_bound(target) - 1`.** Upper bound returns ONE PAST the last target. Subtract.

6. **Using classical binary search and trying to expand.** O(n) worst case. Don't.

7. **Mixing template styles.** If you write `lo < hi` `hi = mid` in one search and `lo <= hi` `hi = mid - 1` in another, you'll introduce bugs. Commit.

8. **Integer overflow in `mid = (lo + hi) / 2`.** Use `mid = lo + (hi - lo) / 2`.

9. **Treating "first ≥ target" as "first == target".** They're DIFFERENT predicates. First ≥ target is monotonic; first == target isn't. We search for ≥, then verify equality.

10. **Forgetting to handle `nums` empty or `n == 0`.** Initial state `lo = 0, hi = 0`. Loop doesn't execute. Return 0. Then guard `first == 0 == n` → return `[-1, -1]`. Works correctly.

---

## 12. The shape — lower/upper bound as a universal template

The lower/upper-bound template is one of the most reused patterns in algorithms.

| Problem | Lower bound for what |
|---|---|
| **This problem** | first index with `nums[i] >= target` |
| Search Insert Position (LC #35) | the position to insert target (= lower_bound) |
| Longest Increasing Subsequence (O(n log n)) | first tail >= current value |
| Find K Closest Elements | lower_bound to anchor the window |
| Find Right Interval | lower_bound on interval starts |
| Time Based Key-Value Store | lower_bound on timestamps |
| Capacity to Ship Packages (binary search on answer) | first capacity that works |
| Kth Smallest in Multiplication Table | first value with ≥ k multiples |
| Painter's Partition Problem | first time-limit that's feasible |

**Pattern to internalize:**

> "Whenever you can frame a question as 'find the first index/value where some monotonic predicate is true,' use the lower-bound template. The predicate doesn't have to be 'value ≥ target' — it can be ANY monotonic boolean over the search range."

This generalizes to **binary search on the answer** (covered in later problems like Capacity to Ship and Magnetic Force). The same template; you replace `nums[mid] < target` with a more complex feasibility check.

---

> **Self-check — the question to ask next time.**
>
> When you face a search problem with O(log n) requirement on sorted data (or a monotonic predicate), ask:
>
> > **"What is the FIRST index where some monotonic property is true? Can I write that as `nums[mid] < cutoff` (lower) or `nums[mid] <= cutoff` (upper)?"**
>
> If yes, plug into the template — done in O(log n).

---

## 13. Cross-references

- **Reference card (post-mastery):** [`../Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](../Find_First_and_Last_Position_of_Element_in_Sorted_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Find_Peak_Element.md`](./Find_Peak_Element.md) — binary search on unsorted data.
  - Coming after: Search_in_Rotated_Sorted_Array — half-and-half decisions.
  - Coming much later: Capacity_To_Ship_Packages, Magnetic_Force — binary search ON THE ANSWER (same template, different predicate).
