# Distribute Candies

**Problem Link:**
https://leetcode.com/problems/distribute-candies/

**Topic:**
Greedy

----------------------------------------

## Step 1: Read the Problem

You have an array `candyType` of even length where each entry represents a type of candy. Alice's doctor says she can only eat **n/2 candies** (half the total). Alice wants to **maximize the number of distinct candy types** she eats.

Return the max types she can eat.

Example: `candyType = [1, 1, 2, 2, 3, 3]`. n = 6. She can eat 3. Distinct types: {1, 2, 3}. If she picks one of each, she gets 3 types. Return 3.

Example: `candyType = [1, 1, 2, 3]`. n = 4. She can eat 2. Distinct types available: {1, 2, 3} (3 types). She can pick 2 distinct. Return 2.

Example: `candyType = [6, 6, 6, 6]`. n = 4. She can eat 2. Only 1 distinct type. Max types = 1. Return 1.

----------------------------------------

## Step 2: What Limits the Answer?

Alice can eat at most n/2 candies. She wants to maximize distinct types.

Two constraints:
1. The **number she can eat**: n/2.
2. The **number of distinct types in the bag**: count of unique values in candyType.

Answer: `min(n/2, number of distinct types)`.

Why? If she can eat n/2 candies and there are ≥ n/2 distinct types, she gets n/2 types. If there are fewer types, she's limited by type count.

Never need to worry about which specific candies — just counts.

----------------------------------------

## Step 3: Algorithm

1. Put all candy types into a set to count distinct values.
2. Return `min(n / 2, set.size())`.

```
distinct = len(set(candyType))
return min(n / 2, distinct)
```

O(n) time (set construction), O(n) space.

----------------------------------------

## Step 4: Trace

`candyType = [1, 1, 2, 2, 3, 3]`. n = 6, n/2 = 3.
Set: {1, 2, 3}, size 3.
min(3, 3) = 3.

`candyType = [1, 1, 2, 3]`. n = 4, n/2 = 2.
Set: {1, 2, 3}, size 3.
min(2, 3) = 2.

`candyType = [6, 6, 6, 6]`. n = 4, n/2 = 2.
Set: {6}, size 1.
min(2, 1) = 1.

All correct.

----------------------------------------

## Step 5: Why Greedy Trivially Works

Alice picks n/2 candies. To maximize distinct types, pick one of each type up to n/2.
- If types >= n/2, pick n/2 distinct types.
- If types < n/2, pick all distinct types plus duplicates to fill the count (those duplicates don't add new types).

The answer is always `min(n/2, distinct_count)`.

No actual "greedy choice" needed — the counting formula handles it.

----------------------------------------

## Step 6: Name It

**Direct math / counting** problem wrapped in a combinatorial-sounding statement. Not really a greedy algorithm in the algorithmic sense, but filed under greedy because it's a "take the best you can" pattern.

Similar feel to:
- "Maximize something under a quota" problems where the answer is a min of two quantities.
- "Can everybody get one?" problems.

The trick is recognizing the answer is `min(budget, availability)`.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** — set construction.
Space: **O(n)** worst case (all distinct).

----------------------------------------

## Step 8: C++ Implementation

```cpp
int distributeCandies(vector<int>& candyType) {
    unordered_set<int> types(candyType.begin(), candyType.end());
    return min((int)types.size(), (int)candyType.size() / 2);
}
```

Two lines. `unordered_set` auto-deduplicates. `min` clamps at the budget.

----------------------------------------

## Step 9: Follow-up Questions

- **Alice can eat k candies instead of n/2.** Return `min(k, distinct)`.
- **Each type has a count limit (can only eat k of each type).** Harder — becomes a bin-packing-ish problem.
- **Maximize eaten count, not types.** Easy: she just eats n/2.
- **Prefer candies by some priority (e.g., chocolates over mints).** Sort types by priority; pick top n/2 types.
- **Multi-person distribution.** If Alice and Bob share, it's a partition problem — far more complex.
- **Candies with weights (she can eat up to a total weight).** Different problem; Dijkstra / DP.
