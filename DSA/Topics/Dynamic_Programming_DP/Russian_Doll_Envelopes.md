# Russian Doll Envelopes

**Problem Link:**
https://leetcode.com/problems/russian-doll-envelopes/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Read the Problem

You have `envelopes[i] = [width, height]`. Envelope A can fit inside envelope B if A's width < B's width **and** A's height < B's height (both **strictly** less).

Nesting must be proper — no rotations allowed, and equal sizes don't nest.

Return the **maximum number** of envelopes that can be nested.

Example: `envelopes = [[5, 4], [6, 4], [6, 7], [2, 3]]`.
- [2, 3] < [5, 4]? Yes. Can nest.
- [5, 4] < [6, 7]? Yes.
- So [2, 3] → [5, 4] → [6, 7] is a chain of 3 envelopes. Does [6, 4] fit anywhere? Into [6, 7]: 6 < 6? No. Doesn't fit. Before [5, 4]? [6, 4] < [5, 4]? 6 > 5. No.

Max chain length: **3**.

----------------------------------------

## Step 2: A 1D Warm-Up

Ignore the 2D (width × height) aspect for a moment. Imagine envelopes had only one dimension, and we wanted the longest sequence where each fits strictly inside the next.

With 1D values like `[5, 2, 6, 5, 3]`, the answer is the **Longest Strictly Increasing Subsequence** — `[2, 3, 5]` or `[2, 3, 6]`, length 3.

LIS is a classic problem solvable in O(n log n) with patience sorting.

Can we somehow reduce our 2D envelope problem to a 1D LIS problem?

----------------------------------------

## Step 3: Sort First — But How?

If we sort envelopes by width (ascending), then in the sorted order, **any nesting chain is a sequence where widths are non-decreasing**. That's progress — but widths must be *strictly* less for nesting, not just ≤.

So after sorting by width, we need to find the longest chain where both width and height strictly increase. Widths are already non-decreasing, but they could be equal. If two envelopes have the same width, neither can contain the other — so within a "same-width group," we can pick at most one.

Here's a clever trick: **sort primarily by width ascending, secondarily by height descending**. Why descending for height? Because within a same-width group, we do NOT want to pick multiple of them. If we sort heights descending within the group, then the LIS on heights would naturally skip same-width entries (a later entry in the group has smaller or equal height, so it can't extend the LIS).

Let me verify with an example. Envelopes `[[6, 4], [6, 7]]`. Sort width asc, height desc: `[[6, 7], [6, 4]]`. LIS on heights `[7, 4]` is 1 (just 7, or just 4). Correct — you can't nest both same-width envelopes.

If instead we'd sorted heights ascending within same-width, we'd get `[[6, 4], [6, 7]]` → LIS on [4, 7] would be 2, which would falsely say we can nest two same-width envelopes.

So the secondary sort order matters crucially.

----------------------------------------

## Step 4: Boil It Down to LIS on Heights

After sorting (width asc, height desc on ties), we need the LIS (strictly increasing) on the heights array.

Why does this work?
- After sort, widths are non-decreasing.
- A strictly increasing sequence of heights (in the sorted order) gives a valid nesting chain, because:
  - Heights strictly increase (directly).
  - Widths also strictly increase (because if widths were equal, heights would be decreasing in the sorted order, so heights wouldn't be strictly increasing).
- And any valid nesting chain corresponds to some strictly increasing height sequence in sorted order.

So the 2D problem collapses to **LIS** on the sorted heights.

----------------------------------------

## Step 5: LIS in O(n log n)

Classical patience sorting: maintain a `tails[]` array where `tails[i]` is the smallest tail of an increasing sequence of length i+1. For each incoming h:
- Binary search for the first position in `tails` where `tails[pos] >= h`.
- Replace `tails[pos]` with h (or append if pos is past the end).
- The length of tails at the end is the LIS length.

For strictly increasing, use `lower_bound` (find first ≥); for non-strict, `upper_bound`.

We want strictly increasing → `lower_bound`.

```cpp
vector<int> tails;
for (int h : heights) {
    auto it = lower_bound(tails.begin(), tails.end(), h);
    if (it == tails.end()) tails.push_back(h);
    else *it = h;
}
return tails.size();
```

----------------------------------------

## Step 6: Trace on the Example

`envelopes = [[5, 4], [6, 4], [6, 7], [2, 3]]`.

Sort width asc, height desc: `[[2, 3], [5, 4], [6, 7], [6, 4]]`. (Note how `[6, 7]` comes before `[6, 4]` — heights descending within width=6.)

Heights: `[3, 4, 7, 4]`.

Apply LIS:
```
tails = []
h=3: tails empty, append. tails = [3].
h=4: 4 > 3, append. tails = [3, 4].
h=7: 7 > 4, append. tails = [3, 4, 7].
h=4: find first >=4 in [3, 4, 7]. Position 1 (value 4). Replace. tails = [3, 4, 7].
```

Length = 3. ✓

Notice the last h=4 would have extended to length 3 naively if we'd sorted height ascending ([[6, 4], [6, 7]] would give heights [3, 4, 4, 7] and LIS 3, but the chain would include both [6, 4] and [6, 7] which don't actually nest). The desc sort on ties correctly prevents this.

----------------------------------------

## Step 7: Name It

This is **LIS on a 2D domain via sort-and-reduce**. The general technique: when you have pairs and need a chain in both dimensions, sort by one (with a careful tie-break) and LIS on the other.

The tie-break rule is the subtle part. Sort one dimension ascending, the other descending (on ties) to make LIS respect strict inequality in both dimensions.

The same trick extends to 3D (sort by one, LIS on 2D remainder — but 2D LIS is harder, often O(n²) or O(n² log n)).

----------------------------------------

## Step 8: Complexity

Time:
- Sort: O(n log n).
- LIS: O(n log n).
- Total: **O(n log n)**.

Space: O(n) for tails.

A naive approach — sort by width then do an O(n²) LIS on heights — is O(n²) and works but is slower. The log-n LIS is the standard answer for this problem.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int maxEnvelopes(vector<vector<int>>& envelopes) {
    sort(envelopes.begin(), envelopes.end(),
         [](const vector<int>& a, const vector<int>& b) {
             if (a[0] != b[0]) return a[0] < b[0];   // width ascending
             return a[1] > b[1];                      // height descending on ties
         });

    vector<int> tails;
    for (auto& e : envelopes) {
        int h = e[1];
        auto it = lower_bound(tails.begin(), tails.end(), h);
        if (it == tails.end()) tails.push_back(h);
        else *it = h;
    }
    return tails.size();
}
```

Key details:
- The comparator: width asc, height desc. Critical for correctness.
- `lower_bound` for strictly increasing LIS. Using `upper_bound` would count same-width envelopes, giving wrong answers.

----------------------------------------

## Step 10: Follow-up Questions

- **Return the actual nesting chain.** Track parent pointers during LIS construction; walk them back.
- **Number of distinct maximum chains.** Harder — needs counting in the LIS DP.
- **Allow rotations (envelope can be rotated 90°).** Pre-process by normalizing each envelope's dimensions (e.g., `min(w,h)` as width).
- **3D nesting (boxes).** Same trick extended — sort by one dim, LIS on pairs. Complexity usually O(n²).
- **What if envelopes can be scaled uniformly?** Doesn't change the combinatorics if the "strictly less" comparison is unchanged.
- **Why lower_bound (not upper_bound) for strict?** Because we want to replace the *first* position ≥ h (not strictly >), preserving all earlier tails for sequences of length < current.
