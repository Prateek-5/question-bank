# Ugly Number II

**Problem Link:**
<a href="https://leetcode.com/problems/ugly-number-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/ugly-number-ii/</a>

**Topic:**
Two Pointers

----------------------------------------

## Step 1: What's an Ugly Number?

An **ugly number** is a positive integer whose only prime factors are 2, 3, or 5. Numbers like 1, 2, 3, 4, 5, 6, 8, 9, 10, 12, ... are ugly. Numbers like 7, 11, 14 (which have prime factors outside {2, 3, 5}) are not.

Convention: 1 is ugly (it has no prime factors, so trivially all its factors are in {2, 3, 5}).

Problem: return the **n-th ugly number** (1-indexed).

Examples:
- n = 1: 1.
- n = 10: the first 10 ugly numbers are 1, 2, 3, 4, 5, 6, 8, 9, 10, 12. Answer: 12.
- n = 1690: answer is 2123366400.

----------------------------------------

## Step 2: List a Few Ugly Numbers by Hand

Let me generate the first 15:
- 1 (base case).
- 2, 3, 5 (the primes themselves).
- 4 = 2·2.
- 6 = 2·3.
- 8 = 2·2·2.
- 9 = 3·3.
- 10 = 2·5.
- 12 = 2·2·3.
- 15 = 3·5.
- 16 = 2·2·2·2.
- 18 = 2·3·3.
- 20 = 2·2·5.
- 24 = 2·2·2·3.
- 25 = 5·5.

Notice any structure? Every ugly number (other than 1) is some earlier ugly number multiplied by 2, 3, or 5.

- 2 = 1·2, 3 = 1·3, 5 = 1·5.
- 4 = 2·2, 6 = 2·3 or 3·2 (same number), 9 = 3·3, 10 = 2·5 or 5·2.
- And so on.

So we can **generate** ugly numbers by repeatedly multiplying earlier ugly numbers by 2, 3, and 5.

----------------------------------------

## Step 3: Brute Force — Check Each Integer

For each integer i = 1, 2, 3, ..., check if it's ugly by dividing out 2, 3, 5 and seeing if we reach 1. Count ugly numbers until we hit the n-th.

```python
def is_ugly(n):
    for p in [2, 3, 5]:
        while n % p == 0: n //= p
    return n == 1

count = 0
i = 0
while count < n:
    i += 1
    if is_ugly(i): count += 1
return i
```

Works, but slow. Ugly numbers become sparse — the gap between consecutive ugly numbers grows. For large n, we iterate through many non-ugly numbers, each with its own factor-dividing work.

For n = 1690, the answer is ~2 billion, so we'd loop 2 billion times. No good.

We need to generate ugly numbers directly, not check them.

----------------------------------------

## Step 4: Direct Generation via a Min-Heap

Idea: maintain a priority queue of candidate ugly numbers. Start with 1. Each time we pop an ugly number x, we push x·2, x·3, x·5 as new candidates.

To avoid duplicates (since e.g. 6 = 2·3 = 3·2), keep a set of already-seen numbers.

```python
pq = [1]
seen = {1}
for _ in range(n):
    x = heapq.heappop(pq)
    for p in [2, 3, 5]:
        v = x * p
        if v not in seen:
            seen.add(v)
            heapq.heappush(pq, v)
return x
```

Runs in O(n log n) time, O(n) space. Much better than brute force. But there's an even slicker approach.

----------------------------------------

## Step 5: A Three-Pointer Approach (No Heap, No Set)

Look back at how ugly numbers are generated: every new ugly number is some earlier ugly number multiplied by 2, 3, or 5.

If I maintain an array `ugly[]` with the first k ugly numbers in sorted order, the (k+1)-th ugly number is the **smallest** among:
- Some ugly[i] · 2 (for some i where i2 = the pointer into "multiplied by 2").
- Some ugly[i] · 3.
- Some ugly[i] · 5.

Specifically, for each of 2, 3, 5, maintain a pointer `i2, i3, i5` indicating "the next ugly[i] that multiplied by this prime hasn't yet been added to our result."

Next ugly = `min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5)`.

Whichever produced the min, advance that pointer. If two produce the same min (e.g., 6 = 2·3 = 3·2), advance **both** pointers to skip the duplicate.

```python
ugly = [1] * n
i2 = i3 = i5 = 0
for k in range(1, n):
    next2 = ugly[i2] * 2
    next3 = ugly[i3] * 3
    next5 = ugly[i5] * 5
    next_ugly = min(next2, next3, next5)
    ugly[k] = next_ugly
    if next_ugly == next2: i2 += 1
    if next_ugly == next3: i3 += 1
    if next_ugly == next5: i5 += 1
return ugly[n-1]
```

O(n) time. Super clean. And no heap, no set.

----------------------------------------

## Step 6: Why Three Pointers Work

**Claim:** the (k+1)-th ugly number is always min(ugly[i2]·2, ugly[i3]·3, ugly[i5]·5).

**Proof sketch:** Every ugly number > 1 can be expressed as u·p where u is an earlier ugly number and p ∈ {2, 3, 5}. So the next ugly number, having not yet been added, must be the smallest u·p where u is already in our list and u·p hasn't been added yet.

The three pointers exactly track "the smallest u for each p such that u·p hasn't been added." Their min is the next ugly number.

When we advance a pointer, we mark "u·p has been added." Advancing both pointers on ties handles duplicates cleanly — e.g., when 6 = ugly[1]·3 = ugly[2]·2 both equal the next ugly number, we advance both i2 and i3.

----------------------------------------

## Step 7: Trace for n = 10

```
ugly = [1, _, _, _, _, _, _, _, _, _]
i2 = i3 = i5 = 0.

k=1: next2=1·2=2, next3=1·3=3, next5=1·5=5. min=2. ugly[1]=2. i2++.
k=2: next2=ugly[1]·2=4, next3=3, next5=5. min=3. ugly[2]=3. i3++.
k=3: next2=4, next3=ugly[1]·3=6, next5=5. min=4. ugly[3]=4. i2++.
k=4: next2=ugly[2]·2=6, next3=6, next5=5. min=5. ugly[4]=5. i5++.
k=5: next2=6, next3=6, next5=ugly[1]·5=10. min=6. ugly[5]=6. i2++, i3++.
k=6: next2=ugly[3]·2=8, next3=ugly[2]·3=9, next5=10. min=8. ugly[6]=8. i2++.
k=7: next2=ugly[4]·2=10, next3=9, next5=10. min=9. ugly[7]=9. i3++.
k=8: next2=10, next3=ugly[3]·3=12, next5=10. min=10. ugly[8]=10. i2++, i5++.
k=9: next2=ugly[5]·2=12, next3=12, next5=ugly[2]·5=15. min=12. ugly[9]=12.
```

Return ugly[9] = **12**. ✓ Matches expected.

The tie-handling at k=5 (where both next2 and next3 were 6) advanced both pointers; without that, we'd record 6 twice.

----------------------------------------

## Step 8: Name the Technique

This is a **multi-pointer merge of infinite sequences**. Specifically, we're merging the three sequences:
- 2·1, 2·2, 2·3, 2·4, ... (ugly numbers times 2)
- 3·1, 3·2, 3·3, 3·4, ... (ugly numbers times 3)
- 5·1, 5·2, 5·3, 5·4, ... (ugly numbers times 5)

But these sequences reference the ugly list itself, which is being built as we go — a beautiful self-referential generation.

Related patterns: the "3-way merge" is a generalization of 2-way merge from merge-sort. The min-heap version is a k-way merge.

----------------------------------------

## Step 9: Complexity

Time: **O(n)** for the pointer version, O(n log n) for the heap version.
Space: **O(n)** for the ugly array.

Both are huge improvements over brute force.

----------------------------------------

## Step 10: C++ Implementation

Pointer version (elegant):

```cpp
int nthUglyNumber(int n) {
    vector<int> ugly(n);
    ugly[0] = 1;
    int i2 = 0, i3 = 0, i5 = 0;
    for (int k = 1; k < n; ++k) {
        int next2 = ugly[i2] * 2;
        int next3 = ugly[i3] * 3;
        int next5 = ugly[i5] * 5;
        int next = min({next2, next3, next5});
        ugly[k] = next;
        if (next == next2) i2++;
        if (next == next3) i3++;
        if (next == next5) i5++;
    }
    return ugly[n - 1];
}
```

Use `long long` if n is large enough that `ugly[i] * 5` could overflow a 32-bit int. For n up to 1690 (LeetCode's constraint), int is safe.

----------------------------------------

## Step 11: Follow-up Questions

- **Super Ugly Numbers (custom prime list).** Use a heap, or generalize three-pointer approach to k-pointer.
- **n-th number whose prime factors are all in a set S (arbitrary).** Same heap/merge technique works for any finite S.
- **n-th number with at least one prime factor in S.** Different — it's "everything except non-ugly." Inclusion-exclusion or sieve.
- **Count ugly numbers ≤ N.** Harder — generate all up to N, or use a mathematical closed-form for small prime sets.
- **Can we find the n-th ugly number faster than O(n)?** For unbounded primes, no known sub-linear algorithm. For fixed primes like {2, 3, 5}, no better worst-case bound known, but logarithmic-time algorithms exist for specialized query patterns.
