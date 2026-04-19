# Max Chunks To Make Sorted

**Problem Link:**
https://leetcode.com/problems/max-chunks-to-make-sorted/

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: Set the Stage

You have an array `arr` that's a permutation of `[0, 1, 2, ..., n-1]`. Split it into the **maximum number of "chunks"** such that, if you sort each chunk individually and concatenate, the result is the sorted array `[0, 1, 2, ..., n-1]`.

Return the maximum number of chunks.

Example: `arr = [1, 0, 2, 3, 4]`.
- Chunk 1: [1, 0]. Sort → [0, 1].
- Chunk 2: [2]. Sort → [2].
- Chunk 3: [3]. → [3].
- Chunk 4: [4]. → [4].
- Concatenation: [0, 1, 2, 3, 4]. ✓

4 chunks. Can we do 5? That'd mean one chunk per element — but arr[0] = 1, sorted_arr[0] = 0. They differ, so a singleton chunk at index 0 can't stay "1" where "0" should be.

Answer: 4.

Example: `arr = [4, 3, 2, 1, 0]`. The smallest values are at the end; we must keep everything in one chunk. Answer: 1.

----------------------------------------

## Step 2: Spot the Invariant

A chunk from index i to j (inclusive) is "correctly placed" iff, after sorting the chunk, the values at positions i to j are **exactly** the integers from i to j (since the final sorted array is 0, 1, ..., n-1).

Equivalently: the **max** of arr[0..j] must equal j. If max up to index j equals j, that means all values 0, 1, ..., j are somewhere in arr[0..j]. (Because arr is a permutation, the only way max of arr[0..j] = j with j+1 elements is if those are exactly {0, ..., j}.)

So the chunks end at indices where `max(arr[0..j]) == j`.

----------------------------------------

## Step 3: The Algorithm

```
max_so_far = -1
chunks = 0

for i in 0..n-1:
    max_so_far = max(max_so_far, arr[i])
    if max_so_far == i:
        chunks++   # chunk ends here

return chunks
```

O(n) time, O(1) space. Single pass with a running max.

----------------------------------------

## Step 4: Trace on `[1, 0, 2, 3, 4]`

```
i=0: max_so_far = 1. 1 == 0? No. No chunk.
i=1: max_so_far = 1. 1 == 1? Yes. Chunk! chunks = 1.
i=2: max_so_far = 2. 2 == 2? Yes. chunks = 2.
i=3: max_so_far = 3. chunks = 3.
i=4: max_so_far = 4. chunks = 4.
```

Return 4. ✓

For `[4, 3, 2, 1, 0]`:

```
i=0: max = 4. 4 == 0? No.
i=1: max = 4. 4 == 1? No.
i=2: max = 4. 4 == 2? No.
i=3: max = 4. 4 == 3? No.
i=4: max = 4. 4 == 4? Yes. chunks = 1.
```

Return 1. ✓

For `[0, 2, 1]`:

```
i=0: max = 0. 0 == 0? Yes. chunks = 1.
i=1: max = 2. 2 == 1? No.
i=2: max = 2. 2 == 2? Yes. chunks = 2.
```

Return 2. Intuitively: chunk [0], then chunk [2, 1] which sorts to [1, 2]. Concatenation: [0, 1, 2]. ✓

----------------------------------------

## Step 5: Why "Running Max Equals Index" Is the Right Condition

**Claim:** the running max at index j equals j iff arr[0..j] is a permutation of {0, 1, ..., j}.

**Proof:**
- (⇐) If arr[0..j] = {0, ..., j}, their max is j. ✓
- (⇒) If max(arr[0..j]) = j, and arr is a permutation with j+1 elements in arr[0..j], all ≤ j, and the max is j... the values are j+1 distinct integers in {0, ..., n-1} each ≤ j. There are only j+1 integers that are ≤ j (namely 0, 1, ..., j). So arr[0..j] must be exactly {0, ..., j}. ✓

When this condition holds at index j, we can sort arr[0..j] locally to get [0, 1, ..., j], and subsequent chunks handle the rest independently.

----------------------------------------

## Step 6: Why This Is the Maximum

Every valid chunk must end at an index j where `max(arr[0..j]) == j`. Why? If max(arr[0..j]) > j, that means arr[0..j] contains a value v > j, which belongs to position v in the sorted output — not in positions 0..j. Sorting arr[0..j] doesn't place v correctly.

So chunks can **only** end at indices where running max equals index. Maximizing the number of chunks means ending a chunk at every such index. The algorithm does exactly that — hence optimal.

----------------------------------------

## Step 7: Name It

**Running max invariant** — a structural observation specific to permutations of 0..n-1. The general "single-pass with a running condition" pattern applies broadly.

Related:
- Max Chunks II (harder variant without the 0..n-1 restriction; use monotonic stack).
- Longest Turbulent Subarray.
- Can Place Flowers.

These problems all hinge on spotting what invariant changes as we walk the array.

----------------------------------------

## Step 8: Complexity

Time: **O(n)**.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int maxChunksToSorted(vector<int>& arr) {
    int maxSoFar = -1;
    int chunks = 0;
    for (int i = 0; i < (int)arr.size(); ++i) {
        maxSoFar = max(maxSoFar, arr[i]);
        if (maxSoFar == i) chunks++;
    }
    return chunks;
}
```

Six lines. Clean.

----------------------------------------

## Step 10: Follow-up Questions

- **Max Chunks II (general array, not permutation of 0..n-1).** The running-max-equals-index trick fails. Use: partition such that `max(chunk[i]) ≤ min(chunk[i+1])`. Monotonic stack approach: O(n).
- **Minimum number of chunks to break the sorted property.** Different question — probably O(n) with careful scanning.
- **Chunks that when sorted give a different permutation.** Adapt the condition.
- **What if we allow in-place sort per chunk (not just value equality)?** Same problem — our chunks already do this.
- **How to reconstruct the chunk boundaries.** Record positions where the condition fires.
- **Generalization to circular array.** Much harder; treat starting index as a parameter.
