# Sorting / Divide & Conquer — Concepts

## Core Theory
Sorting rearranges elements by a key. Merge sort (stable, O(n log n), O(n) space) and quicksort (in-place, O(n log n) avg) are the classic divide-and-conquer sorts. Counting/Radix sorts run in O(n) for bounded ranges.

## Common Patterns
- **Merge sort counting pairs** (inversions, reverse pairs).
- **Quickselect** for k-th statistics.
- **Bucket/radix sort** for integer keys.
- **Three-way partition** for Dutch flag.

## When to Use
For algorithmic primitives (O(n log n) sorts) or when problem structure — like inversion counting — naturally benefits from divide-and-conquer.

## Template
```cpp
void merge(vector<int>& a, int l, int m, int r) { /* ... */ }
void mergeSort(vector<int>& a, int l, int r) {
    if (l >= r) return; int m = (l + r) / 2;
    mergeSort(a, l, m); mergeSort(a, m+1, r); merge(a, l, m, r);
}
```

## Common Mistakes
- Using quicksort without randomization on adversarial inputs.
- Unstable sort where stability is required.
- Misuse of `std::sort` custom comparator (must be strict weak ordering).
