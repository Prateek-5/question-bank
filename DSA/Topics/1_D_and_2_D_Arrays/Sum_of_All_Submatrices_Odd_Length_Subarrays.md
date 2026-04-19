# Sum of All Odd-Length Subarrays

**Problem Link:**
https://leetcode.com/problems/sum-of-all-odd-length-subarrays/

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: Understand the Target

Given an array `arr`, compute the sum of all **odd-length contiguous subarrays**.

An odd-length subarray is a contiguous slice `arr[i..j]` where `j - i + 1` is odd (1, 3, 5, ...).

Example: `arr = [1, 4, 2, 5, 3]`.

Odd-length subarrays and sums:
- Length 1: [1]=1, [4]=4, [2]=2, [5]=5, [3]=3. Sum = 15.
- Length 3: [1,4,2]=7, [4,2,5]=11, [2,5,3]=10. Sum = 28.
- Length 5: [1,4,2,5,3]=15. Sum = 15.

Total: 15 + 28 + 15 = **58**.

----------------------------------------

## Step 2: Brute Force

Three nested loops: outer for length (1, 3, 5, ...), middle for start index, inner for summing. O(n³).

Or with prefix sums: O(n²) (O(1) per subarray sum).

For n ≤ 100, O(n²) is fine.

----------------------------------------

## Step 3: Per-Element Contribution — O(n)

Swap perspective: instead of summing subarrays, ask "how many odd-length subarrays contain element arr[i]? Multiply arr[i] by that count."

For each index i:
- Number of subarrays containing i = (i + 1) × (n - i).
  - i + 1 choices for start (0 to i).
  - n - i choices for end (i to n - 1).
- Of these, how many are odd-length? 

For a subarray [start, end] containing i, length = end - start + 1. Parity of length = parity of (end - start).

Number of (start, end) pairs with end ≥ i ≥ start AND (end - start) even:

Hmm, this requires some thought. Let me derive the count of **odd-length** subarrays containing index i.

Total subarrays containing i: T = (i + 1) × (n - i).

Among them, how many have odd length?

The length is `end - start + 1`. It's odd iff `end - start` is even, i.e., end and start have the same parity.

Let's count:
- Starts in [0, i]: count is i + 1. Among these, even starts: floor((i + 2) / 2) = floor(i/2) + 1. Odd starts: floor((i + 1) / 2).
- Ends in [i, n-1]: count is n - i. Even ends: depends on n and i. Odd ends: depends.

This is getting fiddly. A cleaner formula:

**Number of odd-length subarrays containing i = ceil(T / 2) = ((T + 1) / 2)** using integer division.

Why? Because roughly half of all subarrays containing i have odd length, rounded up.

More precisely:
```
odd_count(i) = ((i + 1) * (n - i) + 1) / 2
```

This is a known combinatorial identity for this problem. Each element's contribution is `arr[i] * odd_count(i)`.

Sum over all i:
```
total = sum of arr[i] * ((i + 1) * (n - i) + 1) / 2
```

O(n). Much better than O(n²).

----------------------------------------

## Step 4: Verify the Formula

For `arr = [1, 4, 2, 5, 3]`, n = 5.

- i = 0: T = 1 * 5 = 5. Odd count = (5 + 1) / 2 = 3. Contribution: 1 * 3 = 3.
- i = 1: T = 2 * 4 = 8. Odd count = 9 / 2 = 4. Contribution: 4 * 4 = 16.
- i = 2: T = 3 * 3 = 9. Odd count = 10 / 2 = 5. Contribution: 2 * 5 = 10.
- i = 3: T = 4 * 2 = 8. Odd count = 9 / 2 = 4. Contribution: 5 * 4 = 20.
- i = 4: T = 5 * 1 = 5. Odd count = 6 / 2 = 3. Contribution: 3 * 3 = 9.

Total: 3 + 16 + 10 + 20 + 9 = **58**. ✓

----------------------------------------

## Step 5: Why the Formula Works

Let's count (start, end) pairs with `start ≤ i ≤ end` and (end - start) even.

start can be 0, 1, ..., i (i + 1 options).
end can be i, i + 1, ..., n - 1 (n - i options).

For each pair, end - start even iff start and end have same parity.

Split starts by parity: starts with same parity as i, starts with different. Let `a = #starts with parity same as i`, `b = #starts with parity different`. Then a + b = i + 1.

For end, split similarly: c = #ends with parity same as i, d = #ends with parity different, c + d = n - i.

Odd-length subarrays containing i = pairs where start and end have same parity. Same-parity-with-i: a * c. Different-parity-with-i (both different from i = both same as each other): b * d. Total = a*c + b*d.

Even-length = a*d + b*c.

Total: (a+b)(c+d) = (i+1)(n-i) = T.

For arbitrary a, b, c, d with a+b and c+d fixed, a*c + b*d ranges around T/2. The exact formula requires computing a, b, c, d explicitly — and the result turns out to be `ceil(T / 2) = (T + 1) / 2`.

This is a clean closed-form but proving it rigorously needs the a,b,c,d calculation. For interview, memorize the formula or derive through small-case induction.

----------------------------------------

## Step 6: Name It

**Per-element contribution with combinatorial counting.** A classic technique: instead of iterating over all subarrays (O(n²) or more), count how each element contributes and sum.

Applied to:
- Sum of minimums over all subarrays (monotonic stack + contribution).
- Sum of all subarray ranges (similar).
- Any "sum over all subarrays of f(subarray)" where f is local per element.

The formula trick here is specific to this problem, but the meta-pattern (contribution counting) is broadly useful.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** with the formula. O(n²) with prefix sums. O(n³) brute force.
Space: **O(1)**.

----------------------------------------

## Step 8: C++ Implementation

**Formula (O(n)):**

```cpp
int sumOddLengthSubarrays(vector<int>& arr) {
    int total = 0;
    int n = arr.size();
    for (int i = 0; i < n; ++i) {
        int subarrays = (i + 1) * (n - i);
        int oddCount = (subarrays + 1) / 2;
        total += arr[i] * oddCount;
    }
    return total;
}
```

Six lines. Clean and fast.

**Brute with prefix sums (O(n²)):**

```cpp
int sumOddLengthSubarrays(vector<int>& arr) {
    int n = arr.size();
    vector<int> prefix(n + 1, 0);
    for (int i = 0; i < n; ++i) prefix[i + 1] = prefix[i] + arr[i];
    int total = 0;
    for (int i = 0; i < n; ++i) {
        for (int j = i; j < n; j += 2) {   // j = i, i+2, i+4, ... (odd lengths)
            total += prefix[j + 1] - prefix[i];
        }
    }
    return total;
}
```

Works too, slightly slower.

----------------------------------------

## Step 9: Follow-up Questions

- **Even-length subarrays.** Change odd_count to even_count = T - odd_count = T / 2.
- **Sum of subarrays of length exactly k.** Enumerate starts, compute prefix-sum differences.
- **Product (not sum) over all odd-length subarrays.** Much harder — different technique needed.
- **Sum of subarrays filtered by a property (e.g., sum > K).** Often doesn't reduce cleanly; might need O(n²) or DP.
- **Can we derive the formula using Pascal's triangle or binomial coefficients?** Possibly — combinatorial identities of this flavor exist.
- **2D analog: sum of odd-sized sub-rectangles.** Each element has a "how many odd-rectangles contain it" count. Similar derivation.
