# Concatenation of Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Concatenation_of_Array.md`](../Concatenation_of_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/concatenation-of-array/

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~8 minutes. This is genuinely a warm-up problem — no algorithmic trick — so this walkthrough is short. The point here is to build the **index-arithmetic reflex** (`i` and `i + n` referring to the same value in two places) that shows up everywhere later.

**Map of this file (8 short sections):**

1. Read the problem
2. The shape of the answer (visual)
3. The direct approach
4. Code
5. Trace it
6. Why this approach is good enough
7. Common pitfalls
8. The shape — where index arithmetic like this appears later

---

## 1. Read the problem

You're given an integer array `nums` with `n` elements. Return a new array of length `2n` that's just `nums` followed by `nums` again.

Example:

```
nums   = [1, 2, 1]                  (n = 3)
output = [1, 2, 1, 1, 2, 1]         (length 2n = 6)
```

That's it. Take the array, glue another copy of itself onto the end, return it.

> **Mini-refresher: what "concatenation" means.**
>
> To concatenate two sequences is to lay them end-to-end. `[1, 2]` concatenated with `[3, 4]` is `[1, 2, 3, 4]`. The original two sequences appear, in order, with no gaps and no overlap.
>
> Here, both sequences happen to be `nums`. So we're concatenating `nums` with itself.

---

## 2. The shape of the answer (visual)

Lay out the indices side-by-side to see what we need to produce:

```
position in output:   0    1    2    3    4    5
                      ─────────────────────────────
output value:        n[0] n[1] n[2] n[0] n[1] n[2]
                      └─── 1st copy ──┘└─── 2nd copy ──┘
                          (indices 0..n-1)   (indices n..2n-1)
```

So:

- Output position **`i`** (for `0 ≤ i < n`) should hold `nums[i]` — that's the first copy.
- Output position **`i + n`** (for the same `i` in `0 ≤ i < n`) should hold `nums[i]` — that's the second copy.

**Key observation:** both output positions `i` and `i + n` get filled with the same value `nums[i]`. Looking at it that way, a single loop over `i = 0 .. n−1` is enough — each iteration fills two output slots that happen to share a value.

---

## 3. The direct approach

Allocate the output array of size `2n` up front. Walk `i` from `0` to `n − 1`. Each iteration writes `nums[i]` into both `output[i]` (first copy) and `output[i + n]` (second copy).

```
output = new array of size 2*n

for i in 0..n-1:
    output[i]      = nums[i]      # first copy
    output[i + n]  = nums[i]      # second copy

return output
```

That's the whole algorithm. There's nothing to optimize — we have to write `2n` values, and we're writing exactly `2n` values, each in O(1) time.

> **Mini-refresher: O(n) and why no further optimization is possible here.**
>
> "O(n)" means "the running time grows roughly proportionally to `n`." If the input doubles, the running time doubles.
>
> For this problem, the output itself has size `2n`. We *must* write each of those `2n` values at least once. So no algorithm can be faster than O(n). The direct loop already hits that lower bound — there's nothing left to improve.

---

## 4. Code

```cpp
vector<int> getConcatenation(vector<int>& nums) {
    int n = nums.size();
    vector<int> output(2 * n);                  // allocate length-2n array, zero-filled
    for (int i = 0; i < n; i++) {
        output[i]     = nums[i];                // first copy at index i
        output[i + n] = nums[i];                // second copy at index i+n
    }
    return output;
}
```

In Python:

```python
def getConcatenation(nums):
    n = len(nums)
    return nums + nums            # works because Python lists support +

# or, if you want the explicit-loop style:
def getConcatenation(nums):
    n = len(nums)
    output = [0] * (2 * n)
    for i in range(n):
        output[i]     = nums[i]
        output[i + n] = nums[i]
    return output
```

In JavaScript:

```javascript
function getConcatenation(nums) {
    return [...nums, ...nums];    // spread operator
}
```

The explicit-loop form is the one that **teaches the index-arithmetic reflex**. The one-liner forms are fine to ship but they hide what's happening at the index level.

---

## 5. Trace it

`nums = [1, 3, 2, 1]`, so `n = 4`. Allocate `output` of size 8, initially `[0, 0, 0, 0, 0, 0, 0, 0]`.

```
i = 0:
    output[0]   = nums[0] = 1.       output = [1, 0, 0, 0, 0, 0, 0, 0]
    output[0+4] = nums[0] = 1.       output = [1, 0, 0, 0, 1, 0, 0, 0]

i = 1:
    output[1]   = nums[1] = 3.       output = [1, 3, 0, 0, 1, 0, 0, 0]
    output[1+4] = nums[1] = 3.       output = [1, 3, 0, 0, 1, 3, 0, 0]

i = 2:
    output[2]   = nums[2] = 2.       output = [1, 3, 2, 0, 1, 3, 0, 0]
    output[2+4] = nums[2] = 2.       output = [1, 3, 2, 0, 1, 3, 2, 0]

i = 3:
    output[3]   = nums[3] = 1.       output = [1, 3, 2, 1, 1, 3, 2, 0]
    output[3+4] = nums[3] = 1.       output = [1, 3, 2, 1, 1, 3, 2, 1]

Return output = [1, 3, 2, 1, 1, 3, 2, 1].  ✓
```

Notice the same loop iteration writes **two** positions of the output, and those two positions are always `n` apart.

---

## 6. Why this approach is good enough

> Sections "brute force" and "pivot" don't really apply to this problem — there isn't a slow approach that needs replacing. Every approach is O(n).

That said, there ARE multiple valid implementations, and it's worth knowing which is which:

| Style | What it does | When to use |
|---|---|---|
| **Single-loop, dual-write** (the version above) | Write `output[i]` and `output[i + n]` in one pass | The teaching version. Builds index-arithmetic intuition. |
| Two-loop append | Write `output[0..n-1]` first, then `output[n..2n-1]` | Equally fast. Some find it clearer. |
| Spread / `+` (Python, JS) | `nums + nums` or `[...nums, ...nums]` | Production code; less educational. |
| `insert` with iterators (C++) | `result.insert(result.end(), nums.begin(), nums.end())` twice | Idiomatic STL; relies on knowing what iterators are. |

All four are O(n) in time and O(n) in space (for the output). Pick what's clearest in your language.

---

## 7. Common pitfalls

1. **Forgetting to pre-allocate, then `push_back` in a hot loop with no `reserve()`.** In C++, each `push_back` may trigger a reallocation as the vector grows. For large `n`, that's slow. Either pre-allocate the full `2 * n` (as we did) or call `result.reserve(2 * n)` first.

2. **Off-by-one when writing the second copy.** A common bug is writing `output[i + n - 1]` or `output[i + n + 1]` "to leave room for indexing from 1." Don't — the formula is `i + n`, full stop, when `i` ranges over `0 .. n-1`.

3. **Trying to do this "in place" by extending the original array.** It's almost never worth the trouble. Allocating a fresh `2n` array is fine — the problem explicitly asks for the doubled length.

4. **Using `2 * nums.size()` inside the loop condition (C++).** `nums.size()` returns `size_t` (unsigned). Multiplying then comparing with signed `i` may warn or wrap. Cache `n = nums.size()` once outside the loop.

---

## 8. The shape — where index arithmetic like this appears later

The pattern is **"index `i` and index `i + offset` refer to logically-paired positions."** It shows up in surprisingly many later problems:

| Where you'll see it | Offset interpretation |
|---|---|
| **This problem** (Concatenation) | `i` and `i + n`: same value in two array copies |
| Spiral matrix simulation | `(r, c)` and `(r, c + 1)` / `(r + 1, c)` to walk neighbors |
| 2D-as-flat array indexing | `(r, c)` ↔ `r * cols + c` (single offset formula) |
| Rolling hash / KMP | `i` and `i − pattern_length` slide a window |
| Circular array problems | `i % n` to wrap around |
| Kadane / sliding window | `i` is right end, `i − k + 1` is left end |

The **muscle** to build: when you see `i + something` as an array index, immediately ask "what does that `something` mean in terms of the problem?" — usually it's "shift by one copy," "next row," "next column," or "rotate by k."

---

> **Self-check — the question to ask next time.**
>
> When a problem describes the output as **"the same data appearing at two (or more) related positions,"** before reaching for `push_back` and a sequence of inserts, ask yourself:
>
> > **"Can I write a single loop that fills BOTH positions per iteration using `i` and `i + offset`?"**
>
> If yes, you've collapsed two passes into one — cleaner code and slightly better cache behavior.

---

## Cross-references

- **Reference card (post-mastery):** [`../Concatenation_of_Array.md`](../Concatenation_of_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`Total_Hamming_Distance.md`](./Total_Hamming_Distance.md) (per-position contribution — different shape, same "look at indices, not the whole array" mindset)
