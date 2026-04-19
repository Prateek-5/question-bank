# Hashing / Sliding Window — Concepts Guide

----------------------------------------

## 1. Introduction

Two of the most versatile algorithmic patterns combined. Hashing gives O(1) membership and counting; sliding window maintains a dynamic range with monotonic bounds. Together, they solve a huge slice of interview problems that at first look O(n²) or worse.

----------------------------------------

## 2. Real-Life Analogy

Think of a moving window of seats on a train. As you walk from car 1 to car n, the window slides with you. You want to know 'how many unique passengers are currently visible?' — a hash map (passenger → count) tracks that in O(1) per step. When a passenger moves out of the window, decrement; when a new one appears, increment. That's sliding window + hashing.

----------------------------------------

## 3. Core Idea

Hash maps / sets give O(1) average insert, lookup, and delete. Sliding windows maintain two pointers `l` and `r` that advance forward. At each `r`, we extend the window with `a[r]`; when the window violates our invariant, we shrink from the left. Combined: a hash map tracks per-window statistics, and the window slides with monotonic l and r.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals for hashing or sliding window:

- **'Subarray with sum equals k'** → prefix-sum + hashmap.
- **'Longest substring with at most k distinct chars'** → sliding window.
- **'Find duplicates / anagrams'** → hash counting.
- **'Count pairs with some property'** → hashmap pass.

----------------------------------------

## 5. Types / Variations

- **Prefix-sum + hashmap** for subarray-sum problems.
- **Two-pointer sliding window** with invariant.
- **Fixed-size window** (average over k consecutive).
- **Hash set for membership**, hash map for counting.
- **Rolling hash** for string substring matching (Rabin-Karp).

----------------------------------------

## 6. Step-by-Step Working

**Subarray sum equals k (hashing):**
1. map[0] = 1 (empty prefix).
2. Run sum as you scan.
3. At each step, `ans += map[sum - k]` counts subarrays ending here with sum k.
4. Increment map[sum].

**Longest substring without repeating chars (sliding window):**
1. l = 0, best = 0.
2. For each r, if `s[r]` was seen at index ≥ l, move l to `last[s[r]] + 1`.
3. Update `last[s[r]] = r`.
4. Track `best = max(best, r - l + 1)`.

----------------------------------------

## 7. Visual Explanation

**Sliding window for 'abcabcbb' (longest unique substring):**

```
l=0, r=0: 'a'     best=1
l=0, r=1: 'ab'    best=2
l=0, r=2: 'abc'   best=3
l=0, r=3: 'abca' → 'a' already in window, l→1, 'bca' best=3
l=1, r=4: 'bcab' → 'b' repeat, l→2, 'cab'  best=3
...
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Subarray sum equals k
int subarraySum(vector<int>& a, int k) {
    unordered_map<int,int> m; m[0] = 1;
    int sum = 0, ans = 0;
    for (int x : a) {
        sum += x;
        ans += m[sum - k];
        m[sum]++;
    }
    return ans;
}

// Longest substring without repeats
int lengthOfLongestSubstring(string s) {
    vector<int> last(256, -1);
    int l = 0, best = 0;
    for (int r = 0; r < (int)s.size(); ++r) {
        if (last[s[r]] >= l) l = last[s[r]] + 1;
        last[s[r]] = r;
        best = max(best, r - l + 1);
    }
    return best;
}
```

----------------------------------------

## 9. Common Mistakes

- **Forgetting `map[0] = 1`** for prefix-sum counting.
- **Not removing stale entries** as the window shrinks.
- **Using hash maps where arrays suffice** (slower).
- **Iterating and mutating the map** simultaneously.

----------------------------------------

## 10. Interview Insights

Hashing/sliding window questions reward clean pattern recognition. Interviewers want to see:

1. **Quick identification of the pattern.**
2. **Clean window invariants.**
3. **Correct update/shrink logic.**
4. **Awareness of O(1) vs O(n) map ops.**

Memorize the two templates — prefix-sum + hashmap and sliding window — and 30% of array problems become routine.
