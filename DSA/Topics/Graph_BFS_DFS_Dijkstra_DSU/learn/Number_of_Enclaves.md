# Number of Enclaves — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Enclaves.md`](../Number_of_Enclaves.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/number-of-enclaves/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-enclaves/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **Same template as Surrounded Regions: boundary flood-fill. Count remaining land cells.** **Read [`Surrounded_Regions.md`](./Surrounded_Regions.md) first.**

**Map of this file (6 sections):**

1. Read the problem
2. The boundary flood-fill approach
3. Code
4. Trace it
5. Common pitfalls
6. The shape

---

## 1. Read the problem

Given an `m × n` binary matrix (1 = land, 0 = water), an **enclave** is a land cell from which you CANNOT walk to the boundary via adjacent land cells.

Return the COUNT of enclave cells.

**Example:**
```
0 0 0 0
1 0 1 0
0 1 1 0
0 0 0 0
```

- (1, 0) is on the boundary → not enclave.
- (1, 2), (2, 1), (2, 2) form a cluster that's surrounded by water. They can't reach the boundary → 3 enclave cells.

Return **3**.

---

## 2. The boundary flood-fill approach

> **Mini-refresher: same as Surrounded Regions.**
>
> Land cells reachable from boundary = NOT enclaves. The rest are.
>
> 1. Flood-fill from every BORDER land cell, marking each as visited (or flip to 0).
> 2. Count remaining 1s — those are the enclaves.

---

## 3. Code

**C++:**

```cpp
int numEnclaves(vector<vector<int>>& grid) {
    int m = grid.size();
    if (m == 0) return 0;
    int n = grid[0].size();

    function<void(int, int)> flood = [&](int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n || grid[r][c] != 1) return;
        grid[r][c] = 0;
        flood(r+1, c); flood(r-1, c); flood(r, c+1); flood(r, c-1);
    };

    for (int r = 0; r < m; ++r) {
        flood(r, 0); flood(r, n - 1);
    }
    for (int c = 0; c < n; ++c) {
        flood(0, c); flood(m - 1, c);
    }

    int count = 0;
    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (grid[r][c] == 1) count++;
        }
    }
    return count;
}
```

**Python:**

```python
def numEnclaves(grid):
    if not grid: return 0
    m, n = len(grid), len(grid[0])
    
    def flood(r, c):
        if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] != 1: return
        grid[r][c] = 0
        flood(r+1, c); flood(r-1, c); flood(r, c+1); flood(r, c-1)
    
    for r in range(m): flood(r, 0); flood(r, n-1)
    for c in range(n): flood(0, c); flood(m-1, c)
    
    return sum(grid[r][c] for r in range(m) for c in range(n))
```

Complexity: **O(mn) time, O(mn) space.**

---

## 4. Trace it

```
Initial:
0 0 0 0
1 0 1 0
0 1 1 0
0 0 0 0
```

Step 1: flood from borders.
- Border land cells: just (1, 0).
- Flood (1, 0): mark to 0. No land neighbors.

Grid after:
```
0 0 0 0
0 0 1 0
0 1 1 0
0 0 0 0
```

Step 2: count remaining 1s: (1, 2), (2, 1), (2, 2) → **3**.

---

## 5. Common pitfalls

1. **Forgetting to flood from ALL border land cells.** Missing one creates phantom enclaves.

2. **Mutating the grid then re-flooding.** The boundary flood ALSO sets cells to 0; subsequent border passes are no-ops (no land left there).

3. **Counting BEFORE flooding.** Counts ALL land, not just enclaves.

4. **Counting boundary-flood-marked cells AS enclaves.** They're flipped to 0; only remaining 1s are enclaves.

---

## 6. The shape

> **"Boundary flood-fill template: mark boundary-reachable. Count or process the complement."**

| Problem | What to do with the complement |
|---|---|
| **This problem** | COUNT (= enclaves) |
| Surrounded Regions | FLIP O→X |
| Number of Closed Islands | COUNT components, not cells |
| Largest Closed Island | MAX area of components |

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Enclaves.md`](../Number_of_Enclaves.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Surrounded_Regions.md`](./Surrounded_Regions.md), [`Number_of_Islands.md`](./Number_of_Islands.md).
  - Coming next: [`Keys_and_Rooms.md`](./Keys_and_Rooms.md), [`Find_the_Town_Judge.md`](./Find_the_Town_Judge.md), [`Find_Eventual_Safe_States.md`](./Find_Eventual_Safe_States.md).
