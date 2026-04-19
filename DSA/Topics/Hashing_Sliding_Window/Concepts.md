# Hashing / Sliding Window — Concepts

## Core Theory
Hashing maps keys to O(1) access. Sliding window maintains a dynamic range with monotonic bounds, ideal for contiguous subarray/substring problems.

## Common Patterns
- **Prefix-sum + hashmap** for subarray-sum counting.
- **Sliding window** with expand/shrink based on predicate.
- **Character-frequency maps** for anagrams and substrings.
- **Two-sum style lookup**.

## When to Use
Prefer hashing for unordered membership; sliding window when constraints are monotonic over contiguous segments.

## Template
```cpp
int l = 0;
for (int r = 0; r < n; ++r) {
    // expand with a[r]
    while (invalid) { /* shrink with a[l++] */ }
    best = max(best, r - l + 1);
}
```

## Common Mistakes
- Failing to update both window boundaries' counts.
- Using hashmap where an int array suffices (slower).
- Forgetting to remove stale entries when shrinking.
