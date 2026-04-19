# Two Pointers — Concepts Guide

----------------------------------------

## 1. Introduction

Two-pointer techniques exploit order or monotonic structure to collapse nested loops into a single pass. Whenever data is sorted or a constraint advances monotonically, two pointers turn O(n²) brute force into O(n).

----------------------------------------

## 2. Real-Life Analogy

Imagine you have two readers starting at opposite ends of a sorted book and they need to find two pages whose numbers sum to a target. One reader stays slightly ahead or behind based on feedback — they never backtrack, never cross the same territory twice. That's two pointers.

----------------------------------------

## 3. Core Idea

The technique comes in two main flavors. **Opposite-end pointers** start at the two ends and move toward each other — used for pair-sum problems on sorted arrays and palindrome checks. **Same-direction pointers** (sliding window or fast/slow) both move forward but at different rates — used for window-based problems and cycle detection in linked lists.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Look for two pointers when:

- **Input is sorted and you want pairs/triplets with some sum property.**
- **Contiguous subarray with a monotonic constraint** (sliding window).
- **Palindrome or mirror checks.**
- **Linked-list cycle or middle finding** (fast/slow).
- **Merge-like operations** (merging sorted arrays, intersection).

----------------------------------------

## 5. Types / Variations

- **Opposite-end pointers:** two-sum on sorted, container with most water, valid palindrome.
- **Same-direction / sliding window:** longest substring without repeats, min window substring.
- **Fast/slow:** cycle detection, middle of linked list.
- **Three pointers:** Dutch national flag partition.

----------------------------------------

## 6. Step-by-Step Working

**Two-sum on sorted array:**
1. l = 0, r = n-1.
2. While l < r: s = a[l] + a[r].
3. If s == target → return {l, r}.
4. If s < target → l++ (need larger sum).
5. Else → r-- (need smaller sum).

**Floyd's tortoise-hare cycle:**
1. slow = fast = head.
2. Advance slow by 1 step, fast by 2 steps.
3. If they meet → cycle exists.
4. If fast reaches null → no cycle.

----------------------------------------

## 7. Visual Explanation

**Two-sum on `[2, 7, 11, 15]`, target `18`:**

```
l=0, r=3: 2 + 15 = 17 < 18  → l++
l=1, r=3: 7 + 15 = 22 > 18  → r--
l=1, r=2: 7 + 11 = 18 ✓    → return {1, 2}
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Two-sum on sorted array
vector<int> twoSumSorted(vector<int>& a, int t) {
    int l = 0, r = a.size() - 1;
    while (l < r) {
        int s = a[l] + a[r];
        if (s == t) return {l, r};
        if (s < t) l++;
        else r--;
    }
    return {};
}

// Fast/slow cycle detection
bool hasCycle(ListNode* head) {
    auto s = head, f = head;
    while (f && f->next) {
        s = s->next;
        f = f->next->next;
        if (s == f) return true;
    }
    return false;
}

// Sliding window skeleton
int l = 0, best = 0;
for (int r = 0; r < n; ++r) {
    // extend with a[r]
    while (/* invalid */) {
        // shrink with a[l], l++
    }
    best = max(best, r - l + 1);
}
```

----------------------------------------

## 9. Common Mistakes

- **Moving the wrong pointer** when sums are equal.
- **Forgetting duplicate handling** in 3Sum-style problems.
- **Applying two pointers on unsorted data** without preprocessing.
- **Infinite loop** from not advancing a pointer on boundary cases.

----------------------------------------

## 10. Interview Insights

Two-pointer problems reward a clean, precise style. Interviewers want to see:

1. **Clear invariants** — what does `l` and `r` represent?
2. **Correct pointer updates** in all branches.
3. **Handling ties and duplicates.**
4. **Ability to shift from nested loops to two pointers when possible.**

Before coding, trace the pointer movement on a 5–6 element example. You'll catch boundary bugs before they bite.
