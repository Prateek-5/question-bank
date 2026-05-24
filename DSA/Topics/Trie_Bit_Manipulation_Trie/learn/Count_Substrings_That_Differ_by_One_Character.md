# Count Substrings That Differ by One Character — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Count_Substrings_That_Differ_by_One_Character.md`](../Count_Substrings_That_Differ_by_One_Character.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/count-substrings-that-differ-by-one-character/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **A DP problem (mislabeled as trie).** The lesson: **for each potential mismatch position (i, j) in (s, t), count how far MATCHING extensions go LEFT and RIGHT. Multiply for total substring pairs with that mismatch.** **Read [`Longest_Common_Subsequence.md`](../../Dynamic_Programming_DP/learn/Longest_Common_Subsequence.md) — wait, that's not done yet — read [`Construct_Binary_Tree_from_Inorder_and_Postorder.md`](../../Trees_Binary_Trees/learn/Construct_Binary_Tree_from_Inorder_and_Postorder.md) instead for the 2D-DP feel.**

**Map of this file (8 short sections):**

1. Read the problem
2. The brute force
3. The pivot — fix the mismatch position
4. Forward and backward DP tables
5. The combination count
6. Code
7. Trace it
8. The shape — pivot + extend-in-both-directions

---

## 1. Read the problem

Given two strings `s` and `t`, count substring pairs `(s[i..i+L-1], t[j..j+L-1])` (same length L) that differ in **EXACTLY ONE** character at the same position.

**Example:** `s = "aba"`, `t = "baba"`.

Some matching pairs (differing by exactly 1 char):
- ("a", "b"), ("b", "a"), ("a", "b") at various positions.
- ("ab", "bb"), etc.

Expected count: **6**.

---

## 2. The brute force

For each starting (i, j) and length L, compare substrings and count mismatches. Three nested loops → O(m × n × min(m, n)²). Way too slow.

We need to exploit shared structure.

---

## 3. The pivot — fix the mismatch position

> **Mini-refresher: think of the MISMATCH as a pivot.**
>
> For each pair of positions (i, j) where `s[i] ≠ t[j]`, count substrings where THIS position is the SINGLE mismatch.
>
> Such a substring extends some number of MATCHING characters to the LEFT, then has the mismatch at (i, j), then some number of MATCHING characters to the RIGHT.
>
> Total count for this mismatch position = (1 + matched_left) × (1 + matched_right).
>
> Sum over all mismatch positions.

The "+1" accounts for including the mismatch position itself (zero left or right extension still counts).

---

## 4. Forward and backward DP tables

Precompute:

- **`forward[i][j]`** = length of longest common prefix starting at `s[i:]` and `t[j:]`. (How far do matches extend RIGHT from (i, j)?)
- **`backward[i][j]`** = length of longest common suffix ending at `s[:i+1]` and `t[:j+1]`. (How far do matches extend LEFT to (i, j)?)

Computed in O(m × n) each:

```
# Backward (longest common suffix ending at (i, j))
for i in 0..m-1:
    for j in 0..n-1:
        if s[i] == t[j]:
            backward[i+1][j+1] = backward[i][j] + 1
        else:
            backward[i+1][j+1] = 0

# Forward (longest common prefix starting at (i, j))
for i in m-1..0:
    for j in n-1..0:
        if s[i] == t[j]:
            forward[i][j] = forward[i+1][j+1] + 1
        else:
            forward[i][j] = 0
```

> **Mini-refresher: why the offset (i+1, j+1) in backward?**
>
> To avoid -1 indexing for the base case (when i=0 or j=0), we shift to 1-indexed. `backward[i+1][j+1]` corresponds to "match ending AT s[i], t[j]". `backward[0][_]` and `backward[_][0]` are 0 (no prior chars).

---

## 5. The combination count

For each (i, j) where `s[i] ≠ t[j]` (potential mismatch position):

- **Left extension** = `backward[i][j]` (matched chars ending JUST BEFORE i, j).
- **Right extension** = `forward[i+1][j+1]` (matched chars starting JUST AFTER i, j).

Substring pairs with this single mismatch = `(left + 1) × (right + 1)`.

Sum over all such (i, j).

---

## 6. Code

**C++:**

```cpp
int countSubstrings(string s, string t) {
    int m = s.size(), n = t.size();
    vector<vector<int>> forward(m + 1, vector<int>(n + 1, 0));
    vector<vector<int>> backward(m + 1, vector<int>(n + 1, 0));

    // Backward: longest common suffix ending at (i, j)
    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j)
            if (s[i] == t[j])
                backward[i + 1][j + 1] = backward[i][j] + 1;

    // Forward: longest common prefix starting at (i, j)
    for (int i = m - 1; i >= 0; --i)
        for (int j = n - 1; j >= 0; --j)
            if (s[i] == t[j])
                forward[i][j] = forward[i + 1][j + 1] + 1;

    int count = 0;
    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j)
            if (s[i] != t[j]) {
                int L = backward[i][j];
                int R = forward[i + 1][j + 1];
                count += (L + 1) * (R + 1);
            }
    return count;
}
```

**Python:**

```python
def countSubstrings(s, t):
    m, n = len(s), len(t)
    forward = [[0] * (n + 1) for _ in range(m + 1)]
    backward = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m):
        for j in range(n):
            if s[i] == t[j]:
                backward[i + 1][j + 1] = backward[i][j] + 1
    
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            if s[i] == t[j]:
                forward[i][j] = forward[i + 1][j + 1] + 1
    
    count = 0
    for i in range(m):
        for j in range(n):
            if s[i] != t[j]:
                count += (backward[i][j] + 1) * (forward[i + 1][j + 1] + 1)
    return count
```

Complexity: **O(m × n) time and space.**

---

## 7. Trace it

`s = "aba"`, `t = "baba"`. m=3, n=4.

Backward (longest common suffix ending at (i, j), 1-indexed):

```
        b   a   b   a
   ┌   0   0   0   0
 a │   0   0   1   0   1
 b │   0   1   0   2   0
 a │   0   0   2   0   3
```

Forward:

```
        b   a   b   a
 a │    0   1   0   1   0
 b │    1   0   2   0   0
 a │    0   1   0   1   0
   └    0   0   0   0   0
```

(For brevity, only key values shown.)

For each (i, j) with `s[i] ≠ t[j]`:

- (0,0): a≠b. L=backward[0][0]=0. R=forward[1][1]=0. Contribution = 1.
- (0,2): a≠b. L=backward[0][2]=0. R=forward[1][3]=0. Contribution = 1.
- (1,1): b≠a. L=backward[1][1]=0. R=forward[2][2]=0. Contribution = 1.
- (1,3): b≠a. L=backward[1][3]=0. R=forward[2][4]=0. Contribution = 1.
- (2,0): a≠b. L=backward[2][0]=0. R=forward[3][1]=0. Contribution = 1.
- (2,2): a≠b. L=backward[2][2]=0. R=forward[3][3]=0. Contribution = 1.

Total: **6**. ✓

---

## 8. The shape — pivot + extend-in-both-directions

The pattern this problem teaches:

> **"For 'count configurations with property P at a SPECIAL position' problems, FIX the special position (the PIVOT), measure EXTENT in both directions independently, and MULTIPLY."**

| Problem | Pivot | Extents |
|---|---|---|
| **This problem** | mismatch position (i, j) | matched left × matched right |
| Longest Palindromic Substring (expand around center) | center character | expand left and right |
| Count Palindromic Substrings | each center | expand |
| Maximum Number of Occurrences (with center constraint) | center | both directions |

**Pattern to internalize:**

> "For 'count substrings/subarrays/positions with property P' on TWO STRINGS or with a SPECIAL position, fix the pivot, compute LEFT-EXTENSION and RIGHT-EXTENSION DPs, and multiply. O(mn)."

---

## Cross-references

- **Reference card (post-mastery):** [`../Count_Substrings_That_Differ_by_One_Character.md`](../Count_Substrings_That_Differ_by_One_Character.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Trie topic complete!
  - Next: Heap_Priority_Queue topic.
