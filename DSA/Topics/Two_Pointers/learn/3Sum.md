# 3Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../3Sum.md`](../3Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/3sum/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~30 minutes. 3Sum is **the textbook two-pointer extension**: "fix one element, two-pointer the rest." The shape generalizes to 4Sum, k-Sum, and many combinatorial-search problems. The hardest part isn't the two-pointer scan — it's **deduplication**, and that's where most candidates trip up. **Read [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) first**.

**Map of this file (12 short sections):**

1. Read the problem
2. Understanding "unique triplets"
3. The natural brute force
4. The pivot — reduce 3Sum to Two Sum
5. Why sorting first is crucial
6. The dedup rule for the OUTER loop
7. The two-pointer two-sum inner loop
8. The dedup rule for the INNER loop
9. Code
10. Trace it
11. Common pitfalls
12. The shape — k-Sum and beyond

---

## 1. Read the problem

You're given an integer array `nums`. Find **all unique triplets** `[a, b, c]` from `nums` such that `a + b + c == 0`. Return them as a list of lists.

Each triplet uses **three different indices** in `nums` (you can't use the same array index twice). But values can repeat — `[-1, -1, 2]` is fine if `nums` has at least two `-1`s.

**Example:** `nums = [-1, 0, 1, 2, -1, -4]`.

Valid triplets summing to 0:

- Indices `(0, 2, 4)`: values `-1, 1, -1` → sum 0. As a sorted triplet: `[-1, -1, 1]`. Wait, let me recompute: `-1 + 1 + (-1) = -1`. Not 0. Let me try again.

- Indices `(0, 1, 2)`: `-1 + 0 + 1 = 0`. ✓ Triplet `[-1, 0, 1]`.
- Indices `(2, 3, 4)`: `1 + 2 + (-1) = 2`. ✗
- Indices `(0, 3, 4)`: `-1 + 2 + (-1) = 0`. ✓ Triplet `[-1, 2, -1]` — sorted: `[-1, -1, 2]`.
- Indices `(1, 2, 4)`: `0 + 1 + (-1) = 0`. ✓ Same triplet `[-1, 0, 1]` (already found).

Unique sorted triplets: `[[-1, -1, 2], [-1, 0, 1]]`. Return these two.

---

## 2. Understanding "unique triplets"

> **Mini-refresher: what "unique" means here.**
>
> Two triplets are **the same** if, when sorted, they contain the same values. So `[-1, 0, 1]` and `[1, 0, -1]` are the SAME triplet (same multiset).
>
> "Unique" means we return each multiset exactly once — even if the array has duplicate values that form multiple INDEX combinations producing the same multiset.
>
> For `nums = [-1, -1, 0, 1]`:
> - Indices `(0, 2, 3)`: `-1 + 0 + 1 = 0`. ✓ Sorted: `[-1, 0, 1]`.
> - Indices `(1, 2, 3)`: `-1 + 0 + 1 = 0`. ✓ Sorted: `[-1, 0, 1]`. **Same triplet** — don't return twice.
>
> Final unique answer: `[[-1, 0, 1]]`.

So we need to:
1. Find triplets summing to 0.
2. Avoid returning duplicates.

Both parts are non-trivial. The two-pointer trick handles step 1; sorting + careful "skip duplicate" logic handles step 2.

---

## 3. The natural brute force

Three nested loops over all triplets of indices:

```cpp
vector<vector<int>> threeSum(vector<int>& nums) {
    int n = nums.size();
    set<vector<int>> uniqueTriplets;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            for (int k = j + 1; k < n; k++) {
                if (nums[i] + nums[j] + nums[k] == 0) {
                    vector<int> triplet = {nums[i], nums[j], nums[k]};
                    sort(triplet.begin(), triplet.end());
                    uniqueTriplets.insert(triplet);          // set deduplicates
                }
            }
        }
    }
    return vector<vector<int>>(uniqueTriplets.begin(), uniqueTriplets.end());
}
```

- Three nested loops: **O(n³)**.
- Storing sorted triplets in a set for dedup: each insert is O(log T × triplet_length).

For `n = 3000`, that's `~2.7 × 10¹⁰` ops — TLE.

We need to do better.

---

## 4. The pivot — reduce 3Sum to Two Sum

Here's the structural observation. The triplet sum `a + b + c == 0` can be rewritten as:

```
b + c == -a
```

If I **fix** `a` (one element of the array) and ask "find pairs `(b, c)` from the rest of the array summing to `-a`" — that's exactly the **Two Sum** problem with target `-a`.

So the algorithm becomes:

```
for each i in 0..n-1:
    a = nums[i]
    target = -a
    find all pairs (b, c) in nums[i+1..n-1] summing to target
    for each pair found, add (a, b, c) to results
```

(Using `nums[i+1..n-1]` instead of "all other elements" enforces `i < j < k` and avoids using the same index twice.)

The inner step is Two Sum. If we make the inner array sorted, we can use the **two-pointer** Two Sum from `Two_Sum_II_Input_Array_Is_Sorted.md` — O(n) per outer iteration.

Total: O(n) outer × O(n) inner = **O(n²)** time. A massive improvement over O(n³).

---

## 5. Why sorting first is crucial

To use the two-pointer Two Sum inside, the array (or at least the portion we two-pointer over) must be sorted.

But sorting also has a second, equally important benefit: **it makes deduplication easy**.

Without sorting: duplicate triplets would have to be tracked via a `set<vector<int>>` (slow, allocations everywhere).

With sorting: **equal values are adjacent**, so duplicates can be skipped by checking "is this value equal to the previous one?" Constant-time check, no extra memory.

So sort once at the start. The sort costs O(n log n), but the outer/inner loop is already O(n²), which dominates. Net cost: still O(n²).

---

## 6. The dedup rule for the OUTER loop

After sorting, equal values sit next to each other. Consider `nums = [-1, -1, 0, 1]` (already sorted). If I fix `i = 0` (value `-1`) and find all triplets, I get `[-1, 0, 1]` from the inner Two Sum.

If I then fix `i = 1` (also value `-1`) and run the inner Two Sum on `nums[2..3] = [0, 1]`, target = 1, I'll find `0 + 1 = 1`. So I'd record the triplet `[-1, 0, 1]` AGAIN.

That's a duplicate. To prevent it, **skip `i` if `nums[i] == nums[i-1]` AND `i > 0`**.

```
for i = 0..n-1:
    if i > 0 and nums[i] == nums[i-1]:
        continue              # this value already tried as the "outer" element
    ... inner Two Sum ...
```

The first occurrence of any value is used as the outer; subsequent occurrences with the same value are skipped (they'd produce the same triplets).

**Common confusion:** "Doesn't skipping mean I miss triplets like `[-1, -1, 2]` (two `-1`s)?" No — when `i` is at the FIRST `-1`, the inner two-pointer can still discover the second `-1` later in the array as one of the pair members. The skip applies only to the OUTER `i`, not to which values can appear in the inner pair.

---

## 7. The two-pointer two-sum inner loop

Inside the outer loop (with `a = nums[i]` fixed), we need to find pairs in `nums[i+1..n-1]` summing to `-a`. Standard two-pointer on a sorted range:

```
target = -nums[i]
l = i + 1
r = n - 1
while l < r:
    s = nums[l] + nums[r]
    if s == target:
        record (nums[i], nums[l], nums[r])
        ...dedup logic (next section)...
        l++
        r--
    elif s < target:
        l++
    else:
        r--
```

Why `l = i + 1`? Because we already used `nums[i]` as the outer; the inner pair must come from indices STRICTLY greater than `i` to ensure all three indices are distinct.

This is exactly Two Sum II's two-pointer scan, with target `−nums[i]` and search range `[i+1, n-1]`.

---

## 8. The dedup rule for the INNER loop

Just like the outer skips repeated values, the inner two-pointer can find duplicate triplets if the inner array has repeats. Example: after finding a match at `(l, r)`, if `nums[l+1] == nums[l]`, the next pair `(l+1, r')` for some `r' < r` might give the same triplet.

After recording a match, advance past duplicates on BOTH sides before continuing:

```
record (nums[i], nums[l], nums[r])
while l < r and nums[l] == nums[l + 1]: l++       # skip duplicate l values
while l < r and nums[r] == nums[r - 1]: r--       # skip duplicate r values
l++         # move past the last duplicate's position
r--
```

**Important order:** advance `l` past duplicates first (those are equal to nums[l] BEFORE the advance), then do one final `l++` to move off the last duplicate. Otherwise you'd stay at the same value and re-record.

After these skips, the next iteration considers genuinely different `nums[l]` and `nums[r]` values.

---

## 9. Code

```cpp
vector<vector<int>> threeSum(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    int n = nums.size();
    vector<vector<int>> result;

    for (int i = 0; i < n - 2; i++) {
        // Early termination: once nums[i] > 0, all remaining sums are > 0
        if (nums[i] > 0) break;

        // Outer dedup: skip duplicate "i" values
        if (i > 0 && nums[i] == nums[i - 1]) continue;

        int l = i + 1;
        int r = n - 1;
        int target = -nums[i];

        while (l < r) {
            int s = nums[l] + nums[r];
            if (s == target) {
                result.push_back({nums[i], nums[l], nums[r]});

                // Inner dedup
                while (l < r && nums[l] == nums[l + 1]) l++;
                while (l < r && nums[r] == nums[r - 1]) r--;

                l++;
                r--;
            } else if (s < target) {
                l++;
            } else {
                r--;
            }
        }
    }

    return result;
}
```

The `if (nums[i] > 0) break;` is an optimization: once the outer element is positive, the inner pair would also have to sum to a NEGATIVE number — impossible if both are ≥ outer. Stop early.

**Python:**

```python
def threeSum(nums):
    nums.sort()
    n = len(nums)
    result = []

    for i in range(n - 2):
        if nums[i] > 0:
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue

        l, r = i + 1, n - 1
        target = -nums[i]
        while l < r:
            s = nums[l] + nums[r]
            if s == target:
                result.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif s < target:
                l += 1
            else:
                r -= 1
    return result
```

**JavaScript:**

```javascript
function threeSum(nums) {
    nums.sort((a, b) => a - b);
    const n = nums.length;
    const result = [];

    for (let i = 0; i < n - 2; i++) {
        if (nums[i] > 0) break;
        if (i > 0 && nums[i] === nums[i - 1]) continue;

        let l = i + 1, r = n - 1;
        const target = -nums[i];
        while (l < r) {
            const s = nums[l] + nums[r];
            if (s === target) {
                result.push([nums[i], nums[l], nums[r]]);
                while (l < r && nums[l] === nums[l + 1]) l++;
                while (l < r && nums[r] === nums[r - 1]) r--;
                l++;
                r--;
            } else if (s < target) {
                l++;
            } else {
                r--;
            }
        }
    }
    return result;
}
```

---

## 10. Trace it

`nums = [-1, 0, 1, 2, -1, -4]`.

**Sort first:** `[-4, -1, -1, 0, 1, 2]`. n = 6.

```
i = 0, nums[0] = -4.  target = 4.   l = 1, r = 5.
    Iter:  nums[1]+nums[5] = -1+2 = 1.  1<4 → l++.
    Iter:  nums[2]+nums[5] = -1+2 = 1.  1<4 → l++.
    Iter:  nums[3]+nums[5] = 0+2 = 2.   2<4 → l++.
    Iter:  nums[4]+nums[5] = 1+2 = 3.   3<4 → l++.
    l = 5, r = 5. Loop exits.
    No triplets from i = 0.

i = 1, nums[1] = -1.  target = 1.   l = 2, r = 5.
    Iter:  nums[2]+nums[5] = -1+2 = 1.  Match! Record [-1, -1, 2].
        Inner dedup: nums[2] == nums[3]? -1 == 0? No, no skip.
                     nums[5] == nums[4]? 2 == 1? No, no skip.
        l++, r--. l = 3, r = 4.
    Iter:  nums[3]+nums[4] = 0+1 = 1.   Match! Record [-1, 0, 1].
        Inner dedup: nums[3] == nums[4]? 0 == 1? No.
                     nums[4] == nums[3]? 1 == 0? No.
        l++, r--. l = 4, r = 3. l ≥ r, loop exits.

i = 2, nums[2] = -1.  nums[2] == nums[1] (both -1) → SKIP (outer dedup).

i = 3, nums[3] = 0.   target = 0.    l = 4, r = 5.
    Iter:  nums[4]+nums[5] = 1+2 = 3.  3>0 → r--. r = 4. l ≥ r, exit.
    No triplets.

i = 4? nums[4] = 1 > 0 → break.

Result: [[-1, -1, 2], [-1, 0, 1]].  ✓
```

Notice the outer dedup at `i = 2` skipped a duplicate `-1` correctly. The inner two-pointer found both triplets within a single outer iteration `i = 1`.

---

## 11. Common pitfalls

1. **Forgetting to sort.** Without sorting, the inner two-pointer doesn't work, AND dedup becomes much harder (need a `set<vector<int>>`). ALWAYS sort first.

2. **Outer dedup with `nums[i] == nums[i + 1]` instead of `nums[i - 1]`.** The skip rule compares to the PREVIOUS element, not the next. If you check the next, you'd skip the FIRST occurrence of a value (wrong) and process the LAST occurrence (also wrong — by then, valid triplets are already missed because the inner range has shrunk).

3. **Inner dedup advancing past the last duplicate THEN advancing once more — and getting it wrong.** The pattern is `while (l < r && nums[l] == nums[l+1]) l++;` THEN `l++;`. The while-loop stops at the LAST instance of the duplicate value; the final `l++` moves past it. Skipping one of these steps leaves `l` at a duplicate, and you'd re-record the same triplet.

4. **Returning indices instead of values.** This problem (LC #15) asks for the VALUES `[a, b, c]`, not the indices. Re-read the spec.

5. **Forgetting the `i > 0` guard on the outer dedup.** Checking `nums[i] == nums[i-1]` when `i == 0` is an out-of-bounds read (in C++) or grabs the last element (in Python via negative index — silent bug). The `i > 0 &&` guard prevents this.

6. **Using `nums[i] >= 0` for early termination.** Should be `> 0`, not `>= 0`. If `nums[i] == 0`, we can still have triplet `[0, 0, 0]` (if there are three zeros). Don't terminate at zero.

7. **Integer overflow on the sum.** For typical constraints (`nums[i]` in `[-10⁵, 10⁵]`), the sum fits in `int32`. For larger constraints, use `long long`.

---

## 12. The shape — k-Sum and beyond

3Sum is the canonical "reduce k-Sum to (k-1)-Sum by fixing one element" problem. The technique generalizes:

| Problem | Approach |
|---|---|
| **Two Sum** (unsorted) | hashmap, O(n) |
| **Two Sum II** (sorted) | two pointers, O(n) |
| **3Sum** (this problem) | sort + outer fix + inner Two Sum, O(n²) |
| **3Sum Closest** | 3Sum framework, track |s - target| instead of `== 0` |
| **3Sum Smaller** | 3Sum framework, when `s < target` count `r - l` triplets (every k ≤ r works) |
| **4Sum** | sort + two outer fixes + inner Two Sum, O(n³) |
| **k-Sum (general)** | recursive: k-Sum reduces to k=2 base case via (k-2) outer fixes, O(n^(k-1)) |

**Pattern to internalize:**

> "For k-Sum problems, **sort first**, then **fix `k - 2` elements** via nested outer loops, **two-pointer the last two** as Two Sum. **Dedup at every level** by skipping equal-to-previous values (and after a match, skipping equal duplicates on both two-pointer ends)."

Time complexity grows by a factor of `n` per extra layer: 2Sum O(n), 3Sum O(n²), 4Sum O(n³), ..., k-Sum O(n^(k-1)).

The dedup rules are MORE intricate at higher layers but follow the same shape: "skip duplicates of the OUTER fix value; advance past duplicates on the inner pair after a match."

---

> **Self-check — the question to ask next time.**
>
> When you face a **k-sum problem** (find tuples summing to a target), before reaching for `O(n^k)` brute force, ask:
>
> > **"Can I sort the array, fix `k-2` elements via outer loops, and run a two-pointer Two Sum for the last two? With dedup-by-skipping-equal-to-previous at every layer?"**
>
> If yes, you've turned `O(n^k)` into `O(n^(k-1))` and handled deduplication without extra storage.

---

## Cross-references

- **Reference card (post-mastery):** [`../3Sum.md`](../3Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) — the building block (required reading)
  - [`Container_With_Most_Water.md`](./Container_With_Most_Water.md) — sibling pattern (move dominated side)
  - Coming later: Permutations (Recursion topic) and Subsets (Recursion topic) — different combinatorial enumeration shape; share the "sort + skip duplicates" dedup idiom.
