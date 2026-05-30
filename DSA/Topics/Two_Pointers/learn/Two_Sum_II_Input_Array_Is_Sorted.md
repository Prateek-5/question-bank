# Two Sum II — Input Array Is Sorted — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Two_Sum_II_Input_Array_Is_Sorted.md`](../Two_Sum_II_Input_Array_Is_Sorted.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **This is THE introduction to the two-pointer technique on a sorted array.** Every other problem in the Two_Pointers topic builds on the elimination argument you'll meet in section 4. Take the time to read it carefully — the next 6 problems use the same shape.

**Map of this file (10 short sections):**

1. Read the problem
2. The hashmap version (regular Two Sum, for context)
3. What does "sorted" change?
4. The pivot — pick two endpoints, ask one question per step
5. Why the "wrong" endpoint can be safely eliminated (the proof)
6. The full two-pointer template
7. Trace it
8. Code
9. Common pitfalls
10. The shape — the two-pointer template is everywhere

---

## 1. Read the problem

You're given a **sorted** (ascending) 1-indexed array `numbers` and an integer `target`. Find two indices `i` and `j` (with `1 ≤ i < j ≤ numbers.length`) such that `numbers[i] + numbers[j] == target`. Return `[i, j]`.

Guarantees:
- **There is exactly one solution.** You don't have to handle "no answer."
- You may not use the same element twice (so `i < j`, strict).
- The array is **sorted ascending**.
- Indices are **1-indexed** (LeetCode quirk — first element is at index 1, not 0).

**Example 1:** `numbers = [2, 7, 11, 15]`, `target = 9`. Answer: `[1, 2]` (because `numbers[1] = 2` and `numbers[2] = 7`, and `2 + 7 = 9`).

**Example 2:** `numbers = [2, 3, 4]`, `target = 6`. Answer: `[1, 3]` (`2 + 4 = 6`).

**Example 3:** `numbers = [-1, 0]`, `target = -1`. Answer: `[1, 2]` (`-1 + 0 = -1`).

> **Mini-refresher: 1-indexed vs 0-indexed.**
>
> Most programming languages index arrays starting from 0 — `arr[0]` is the first element. But math conventions and some problem statements use 1-indexing where `arr[1]` is the first element.
>
> When the **problem** asks for 1-indexed positions, your code likely uses 0-indexed internal access; you have to **convert by adding 1** before returning. So if you found the answer at 0-indexed positions `l = 0, r = 1`, return `[l + 1, r + 1] = [1, 2]`.
>
> Easy to forget. Read the problem statement carefully and check examples to see which convention is wanted.

---

## 2. The hashmap version (regular Two Sum, for context)

If the array were **NOT** sorted (the regular "Two Sum" problem, LC #1), the standard solution uses a hashmap:

```cpp
vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int, int> seen;
    for (int i = 0; i < nums.size(); i++) {
        int need = target - nums[i];
        if (seen.count(need)) return {seen[need], i};
        seen[nums[i]] = i;
    }
    return {};
}
```

For each element `nums[i]`, check if its "complement" (`target − nums[i]`) has been seen before. If yes, we have a pair.

- Time: O(n).
- Space: O(n) for the hashmap.

This works regardless of order. But this problem GIVES us a sorted array — that's a stronger structural property. Can we use the sortedness to avoid the hashmap (and the O(n) space)?

---

## 3. What does "sorted" change?

> **Mini-refresher: what "sorted ascending" means.**
>
> An array is sorted ascending if every element is `≤` the next: `arr[0] ≤ arr[1] ≤ arr[2] ≤ ... ≤ arr[n−1]`. So the smallest element is at the start; the largest is at the end. Knowing this lets you make **comparisons** without scanning the whole array.
>
> For our problem: `numbers[0]` is the smallest value; `numbers[n−1]` is the largest. The sum of two values from the array is somewhere between `numbers[0] + numbers[1]` (the smallest two) and `numbers[n−2] + numbers[n−1]` (the largest two).

The key observation: in a sorted array, **picking which two elements to sum gives us monotonic control over the sum**. Increasing one pointer (moving from a smaller value to a larger one) increases the sum. Decreasing one pointer decreases the sum. We can navigate toward the target.

This is the doorway to the two-pointer technique.

---

## 4. The pivot — pick two endpoints, ask one question per step

Here's the pivot question:

> **"What if I pick the smallest value (index 0) and the largest value (index n−1), and use the comparison of their sum vs target to decide which one to move?"**

Initialize two pointers:

- `l = 0` (leftmost — smallest value)
- `r = n − 1` (rightmost — largest value)

At each step, compute `sum = numbers[l] + numbers[r]`:

- If `sum == target`: we're done! Return `[l + 1, r + 1]` (converting to 1-indexed).
- If `sum < target`: the sum is too small. We need a **bigger** sum.
- If `sum > target`: the sum is too big. We need a **smaller** sum.

Now the trick — when `sum < target`, what move can we make to get a bigger sum?

- Increasing `l` (move right toward larger values) increases the sum (since the array is sorted).
- Decreasing `r` (move left toward smaller values) DECREASES the sum.

So when `sum < target`, **move `l` right**.

Symmetrically, when `sum > target`, **move `r` left**.

```
while l < r:
    sum = numbers[l] + numbers[r]
    if sum == target: return [l+1, r+1]
    if sum < target: l += 1
    else: r -= 1
```

But wait — **is this safe**? Could we miss the answer by moving the wrong pointer? Section 5 proves we can't.

---

## 5. Why the "wrong" endpoint can be safely eliminated (the proof)

> **Claim:** When `numbers[l] + numbers[r] < target`, the current `numbers[l]` **cannot be part of the answer**. So advancing `l` is safe.

**Proof (by contradiction):**

Suppose the answer is `(l, k)` for some `k > l`. Then `numbers[l] + numbers[k] == target`.

We're considering moving `l` because `numbers[l] + numbers[r] < target`. So:

```
numbers[l] + numbers[r] < target
numbers[l] + numbers[k] = target          (the supposed answer)

Subtract: numbers[r] − numbers[k] < 0
                  numbers[r] < numbers[k]
```

But wait — since `k ≤ r` (we haven't gone past `r` yet), and the array is sorted ascending, `numbers[k] ≤ numbers[r]`. That contradicts what we just derived (`numbers[r] < numbers[k]`).

So no such `k` exists. The current `l` is NOT part of the answer. Moving `l` right is safe. ✓

**Symmetric proof** when `sum > target`: `r` cannot be part of the answer, so moving `r` left is safe.

---

> **Mini-refresher: why "by contradiction" works.**
>
> A common technique in algorithm correctness proofs: "Assume the OPPOSITE of what I want to prove. Derive a contradiction with known facts. Conclude that the assumption was wrong, so my original claim must be true."
>
> Here we wanted to show: "`numbers[l]` is not in the answer." We assumed the OPPOSITE — that `numbers[l]` IS in the answer — and derived a contradiction (a strict inequality that contradicts sortedness). So the assumption is false, meaning `numbers[l]` is not in the answer.

---

> **Why does "moving the smaller side" intuitively work?**
>
> Think of it this way: we're picking the two extremes. If their sum is too small, the smallest one is "obviously too weak" — pairing it with anything available (and even with the very biggest, we couldn't reach the target) means it shouldn't be in our final pair. Discard it; try the next-smallest.
>
> If the sum is too big, the largest one is "too strong" — even paired with the smallest we have, it overshoots. Discard it; try the next-largest.

---

## 6. The full two-pointer template

```
l = 0
r = n - 1
while l < r:
    sum = numbers[l] + numbers[r]
    if sum == target:
        return [l + 1, r + 1]
    if sum < target:
        l += 1
    else:  # sum > target
        r -= 1
```

**Loop guard:** `l < r` (strict). We require `l ≠ r` because we can't use the same element twice. When the pointers meet (`l == r`), we'd be summing an element with itself — disallowed.

**Termination:** each iteration moves exactly one pointer (either left or right). The pointers start `n − 1` apart and converge. After at most `n − 1` iterations, the loop ends. Since the problem GUARANTEES a solution exists, we always return before the loop terminates.

- Time: **O(n)** — at most `n − 1` iterations, each O(1).
- Space: **O(1)** — two integer pointers, regardless of `n`.

Compared to the hashmap version: same time, less space (O(1) vs O(n)). The win is **constant space** by exploiting sortedness.

---

## 7. Trace it

**Example 1:** `numbers = [2, 7, 11, 15]`, `target = 9`.

```
l = 0, r = 3.

Iteration 1:
    sum = numbers[0] + numbers[3] = 2 + 15 = 17.
    17 vs 9? 17 > 9 → too big → r--.    r = 2.

Iteration 2:
    sum = numbers[0] + numbers[2] = 2 + 11 = 13.
    13 vs 9? 13 > 9 → r--.    r = 1.

Iteration 3:
    sum = numbers[0] + numbers[1] = 2 + 7 = 9.
    9 == 9 → return [0 + 1, 1 + 1] = [1, 2].  ✓
```

**Example 2:** `numbers = [1, 2, 3, 4, 4, 9, 56, 90]`, `target = 8`.

```
l = 0, r = 7.

Iter 1:  1 + 90 = 91 > 8 → r--.  r = 6.
Iter 2:  1 + 56 = 57 > 8 → r--.  r = 5.
Iter 3:  1 +  9 = 10 > 8 → r--.  r = 4.
Iter 4:  1 +  4 =  5 < 8 → l++.  l = 1.
Iter 5:  2 +  4 =  6 < 8 → l++.  l = 2.
Iter 6:  3 +  4 =  7 < 8 → l++.  l = 3.
Iter 7:  4 +  4 =  8 == target → return [3+1, 4+1] = [4, 5].  ✓
```

Notice how the pointers walked through the array: `r` first eliminated large values from the right, then `l` walked rightward through the small values until both pointers converged on the pair.

---

## 8. Code

**C++:**

```cpp
vector<int> twoSum(vector<int>& numbers, int target) {
    int l = 0;
    int r = numbers.size() - 1;
    while (l < r) {
        int sum = numbers[l] + numbers[r];
        if (sum == target) return {l + 1, r + 1};      // 1-indexed
        if (sum < target) l++;
        else r--;
    }
    return {};   // unreachable given problem guarantee
}
```

Eight lines. Read each:

1. Initialize `l` to the leftmost (smallest) index and `r` to the rightmost (largest).
2. While they haven't met, compute the sum.
3. If it matches the target, return.
4. If too small, move `l` right (increase the sum next time).
5. If too big, move `r` left (decrease the sum next time).

**Python:**

```python
def twoSum(numbers, target):
    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            return [l + 1, r + 1]
        if s < target:
            l += 1
        else:
            r -= 1
    return []
```

**JavaScript:**

```javascript
function twoSum(numbers, target) {
    let l = 0, r = numbers.length - 1;
    while (l < r) {
        const sum = numbers[l] + numbers[r];
        if (sum === target) return [l + 1, r + 1];
        if (sum < target) l++;
        else r--;
    }
    return [];
}
```

All identical in shape.

---

## 9. Common pitfalls

1. **Returning 0-indexed indices instead of 1-indexed.** This problem (LC #167) is 1-indexed; LC #1 (regular Two Sum) is 0-indexed. Re-read the problem statement EVERY TIME. Adding `+ 1` to both index returns is easy to forget.

2. **Using `l ≤ r` instead of `l < r`.** Strict `<` is required — if `l == r`, you'd be summing an element with itself, which violates the "no using the same element twice" rule. The problem may not even crash on this (depending on inputs), but the answer would be wrong.

3. **Moving the WRONG pointer when the sum is off.** `sum < target` means we need a BIGGER sum, so move the SMALLER side (l) UP. Easy to mix up. Re-derive the direction from "what change would make the sum closer to target?" if uncertain.

4. **Using a hashmap "just in case."** That's the unsorted version's solution. Here, the two-pointer is strictly better — same O(n) time, less space, fewer allocations. Use the right tool.

5. **Integer overflow on `numbers[l] + numbers[r]`.** For typical constraints (`numbers[i]` in `[-10⁹, 10⁹]`), the sum can reach `±2 × 10⁹` — still fits in `int32` but BARELY. For safety, use `long long` (or 64-bit) on the sum if the constraints are larger.

6. **Trying binary search for the complement of each element.** That's O(n log n). The two-pointer is O(n) — strictly better. (Binary search for the complement is sometimes acceptable in interviews but two-pointer is the canonical answer here.)

---

## 10. The shape — the two-pointer template is everywhere

The template you just learned is one of the most reused patterns in interviews. The structure:

```
Sort the array (if not already sorted).
Place two pointers at the ends.
Repeat:
    Compute some quantity from numbers[l] and numbers[r].
    Compare to a target.
    Based on the comparison, MOVE THE POINTER THAT CAN'T BE PART OF THE ANSWER.
Until done.
```

Examples in this repo and beyond:

| Problem | What's compared | Move rule |
|---|---|---|
| **This problem** (Two Sum II) | `numbers[l] + numbers[r]` vs target | too small → l++; too big → r-- |
| Container With Most Water (next in this topic) | `min(h[l], h[r]) * (r - l)` vs current best | move the SHORTER side inward |
| 3Sum | fix `nums[i]`, two-pointer on `(i+1)..n-1` for target `−nums[i]` | same as Two Sum II inside |
| Trapping Rain Water (two-pointer version) | `height[l]` vs `height[r]` | process the shorter side |
| Valid Palindrome | `s[l]` vs `s[r]` | both move inward on match |
| Reverse a string in place | `s[l]` vs `s[r]` | swap, both move inward |
| Squares of a Sorted Array | `abs(nums[l])` vs `abs(nums[r])` | bigger one becomes next "max" |
| 4Sum | fix two outer indices, two-pointer on the rest | nested layers of two-pointer |

**Pattern to internalize:**

> "When you have a SORTED array (or a structure that can be sorted) AND you're looking for a pair / triple / configuration that satisfies some condition, **two pointers at the ends, moving toward each other based on a comparison, is your first move.** Time is O(n) instead of O(n²); space is O(1) instead of O(n)."

The hard part is convincing yourself you can SAFELY eliminate one side. The proof in §5 is the template for all such proofs — assume the discarded element is in the answer, derive a contradiction with sortedness.

---

> **Self-check — the question to ask next time.**
>
> When you see a problem where you need to **find a pair (or larger group) of elements in a SORTED array satisfying a sum / difference / product / area / palindrome condition**, before nesting loops, ask:
>
> > **"Can I put two pointers at the ends and move the one that 'can't be in the answer' based on the comparison?"**
>
> If yes, you've turned O(n²) into O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Two_Sum_II_Input_Array_Is_Sorted.md`](../Two_Sum_II_Input_Array_Is_Sorted.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next in this topic: Container_With_Most_Water (similar shape — move the shorter side), 3Sum (fix one + two-pointer the rest)
  - [`../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md`](../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md) (two-pointer with "process the shorter side" — a slightly different proof structure)
