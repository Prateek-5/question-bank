# Sorting / Divide & Conquer — Concepts Guide

----------------------------------------

## 1. Introduction

Sorting is a foundational tool — it's often the preprocessing step that turns hard problems into easy ones. Divide and conquer generalizes the pattern: split the problem, solve the pieces, merge. Mastering this unlocks merge sort, quicksort, Quickselect, and a family of 'counting during merge' tricks.

----------------------------------------

## 2. Real-Life Analogy

Think of how you'd sort a huge pile of documents. You'd split it in half, give each half to an assistant, and then carefully merge the two sorted piles. That's merge sort — divide and conquer in physical form. Every divide-and-conquer algorithm has the same spirit: break into smaller pieces, recurse, combine.

----------------------------------------

## 3. Core Idea

Divide-and-conquer has three steps: (1) divide — split the input into smaller pieces; (2) conquer — recursively solve each piece; (3) combine — merge the results. The merge step is often where the cleverness lives: counting inversions during merge, finding the pivot for quickselect, finding cut points in the closest-pair problem.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Reach for divide-and-conquer when:

- **The problem naturally splits** into independent subproblems.
- **Sorting is an enabling step** for the main algorithm.
- **You need O(n log n) for a problem that looks O(n²).**
- **Counting inversions / pairs with a property** — merge sort variant.

----------------------------------------

## 5. Types / Variations

- **Merge sort** — stable O(n log n) sort.
- **Quicksort** — in-place, fast on average.
- **Quickselect** — O(n) average for k-th statistic.
- **Counting sort / Radix sort** — O(n) for bounded integer keys.
- **Three-way partition** (Dutch flag) for 0/1/2 values.

----------------------------------------

## 6. Step-by-Step Working

**Merge sort:**
1. If size ≤ 1, return.
2. Split in the middle.
3. Recursively sort each half.
4. Merge the two sorted halves into one.

**Quickselect (k-th smallest):**
1. Pick a random pivot.
2. Partition around pivot.
3. If pivot index == k, return it.
4. Else recurse on the side containing k.

----------------------------------------

## 7. Visual Explanation

**Merge sort on [3, 1, 4, 1, 5, 9, 2, 6]:**

```
                [3,1,4,1,5,9,2,6]
                 /              \
           [3,1,4,1]         [5,9,2,6]
            /    \             /    \
          [3,1] [4,1]       [5,9] [2,6]
          /  \   /  \       /  \   /  \
        [3] [1] [4] [1]   [5] [9] [2] [6]
         merge   merge     merge   merge
         [1,3]  [1,4]     [5,9]  [2,6]
          merge              merge
           [1,1,3,4]          [2,5,6,9]
                   merge
              [1,1,2,3,4,5,6,9]
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Merge sort with inversion count
long long mergeAndCount(vector<int>& a, int l, int m, int r) {
    vector<int> tmp;
    int i = l, j = m + 1;
    long long inv = 0;
    while (i <= m && j <= r) {
        if (a[i] <= a[j]) tmp.push_back(a[i++]);
        else { tmp.push_back(a[j++]); inv += m - i + 1; }
    }
    while (i <= m) tmp.push_back(a[i++]);
    while (j <= r) tmp.push_back(a[j++]);
    for (int k = l; k <= r; ++k) a[k] = tmp[k - l];
    return inv;
}
long long sortAndCount(vector<int>& a, int l, int r) {
    if (l >= r) return 0;
    int m = (l + r) / 2;
    return sortAndCount(a, l, m) + sortAndCount(a, m + 1, r) + mergeAndCount(a, l, m, r);
}

// Quickselect (k-th smallest)
int quickselect(vector<int>& a, int k) {
    int lo = 0, hi = a.size() - 1;
    while (true) {
        int pivot = a[lo + rand() % (hi - lo + 1)];
        int i = lo, j = hi, p = lo;
        while (p <= j) {
            if (a[p] < pivot) swap(a[p++], a[i++]);
            else if (a[p] > pivot) swap(a[p], a[j--]);
            else p++;
        }
        if (k < i) hi = i - 1;
        else if (k > j) lo = j + 1;
        else return pivot;
    }
}
```

----------------------------------------

## 9. Common Mistakes

- **Non-stable sort** where stability was required.
- **Bad pivot choice** in quicksort → O(n²) worst case. Randomize.
- **Misuse of `std::sort` comparator** — must be strict weak ordering.
- **Merge step overflow** — use `long long` for counts.

----------------------------------------

## 10. Interview Insights

Sorting questions test both implementation and pattern recognition. Interviewers want to see:

1. **Clean merge logic** — the hardest part of merge sort.
2. **Correct partition** in quicksort/quickselect.
3. **Stable vs unstable awareness.**
4. **Recognition of 'count during merge' patterns** for inversions, reverse pairs, etc.
