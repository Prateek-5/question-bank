# Find the Town Judge

**Problem Link:**
<a href="https://leetcode.com/problems/find-the-town-judge/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-the-town-judge/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Setup

In a town of n people labeled 1 to n, there is a "judge." The judge has two defining properties:
1. **The judge trusts nobody.**
2. **Everyone (except the judge themselves) trusts the judge.**

Given a list `trust[][]` where `trust[i] = [a, b]` means person a trusts person b, find the judge (their label) or return -1 if there's no valid judge.

Example: `n = 3`, `trust = [[1, 3], [2, 3]]`.

Who trusts whom:
- 1 trusts 3.
- 2 trusts 3.

Does 3 trust anyone? No (not in any `[3, x]`). ✓ (property 1)
Does everyone else trust 3? Person 1 does. Person 2 does. ✓ (property 2)

Judge: 3.

Example: `n = 3`, `trust = [[1, 3], [2, 3], [3, 1]]`.

- 3 trusts 1. So 3 fails property 1. No judge. Return -1.

----------------------------------------

## Step 2: Recast as a Graph

Model trust as a directed edge: `a → b` means "a trusts b."

The judge is the node where:
- **Out-degree = 0** (trusts nobody).
- **In-degree = n - 1** (everyone else trusts them).

Simple: count in-degree and out-degree for each node. The judge has in-degree n - 1 and out-degree 0.

----------------------------------------

## Step 3: One-Pass Counting Trick

Instead of tracking in-degree and out-degree separately, we can track one **score** per person:
- `score[p] = in-degree(p) - out-degree(p)`.

For the judge: score = (n-1) - 0 = n - 1.
For anyone else: they trust someone (out-degree ≥ 1), so score < n - 1 at most by that much.

For each trust `[a, b]`: `score[a]--` (a has an outgoing edge), `score[b]++` (b has an incoming edge).

At the end, find the node with score == n - 1. If exactly one exists, return it. Otherwise -1.

```
score = [0] * (n + 1)   # 1-indexed
for (a, b) in trust:
    score[a]--
    score[b]++
for p in 1..n:
    if score[p] == n - 1: return p
return -1
```

O(trust length + n).

Why does "score == n - 1" uniquely identify the judge? Because:
- Score n - 1 requires in-degree + (-out-degree) = n - 1, i.e., in - out = n - 1.
- Max in-degree is n - 1 (everyone trusts them). Min out-degree is 0. Their difference: n - 1.
- To achieve n - 1, we **must** have in = n - 1 AND out = 0 (no room for slack). That's the judge.

----------------------------------------

## Step 4: Trace

`n = 3`, `trust = [[1, 3], [2, 3]]`.

Initial: score = [_, 0, 0, 0]. (Index 0 unused.)

```
[1, 3]: score[1]-- = -1. score[3]++ = 1.
[2, 3]: score[2]-- = -1. score[3]++ = 2.
```

Final: score = [_, -1, -1, 2]. n - 1 = 2. Person 3 has score 2. Return 3. ✓

For `n = 3, trust = [[1, 3], [2, 3], [3, 1]]`:
```
[1, 3]: score[1]=-1, score[3]=1.
[2, 3]: score[2]=-1, score[3]=2.
[3, 1]: score[3]=1, score[1]=0.
```

Final: score = [_, 0, -1, 1]. n-1 = 2. No one has score 2. Return -1. ✓

----------------------------------------

## Step 5: Edge Case — n = 1

With only one person, no trust edges. Does that one person qualify as judge?
- Out-degree 0: trivially, no edges to send. ✓
- In-degree: 0 ≠ n - 1 = 0. Wait, it *does* equal n - 1 when n = 1.

So for n = 1 and empty trust, score[1] = 0 = n - 1. Return 1.

Our algorithm handles this correctly.

----------------------------------------

## Step 6: Name It

**In-degree/out-degree analysis** — a foundational graph technique. Used when you want to identify nodes with specific degree properties:
- Judges (high in, zero out).
- Leaves (degree 1).
- Hubs (high total degree).

The one-pass score trick combines two counters into one, saving code.

----------------------------------------

## Step 7: Complexity

Time: O(trust length + n) = **O(m + n)** where m = trust list size.
Space: O(n) for the score array.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int findJudge(int n, vector<vector<int>>& trust) {
    vector<int> score(n + 1, 0);
    for (auto& t : trust) {
        score[t[0]]--;
        score[t[1]]++;
    }
    for (int p = 1; p <= n; ++p) {
        if (score[p] == n - 1) return p;
    }
    return -1;
}
```

Five lines. Very tight.

----------------------------------------

## Step 9: Follow-up Questions

- **Multiple judges allowed.** Return a list. All nodes with score n - 1.
- **Judge trusts *exactly* one person (not zero).** Adjust: judge's score = (n - 2) - 1 = n - 3. Check accordingly.
- **Weighted trust (varying magnitudes).** Instead of ±1, add/subtract weights.
- **Why does score == n - 1 imply in = n - 1 and out = 0 uniquely?** Because in ≤ n - 1 (bound on incoming) and out ≥ 0. So in - out ≤ n - 1 with equality only at (n - 1, 0).
- **Detect judge in a dynamic graph (edges added over time).** Maintain scores; each update is O(1).
- **Tree-of-trust structures (who trusts whom transitively).** Different problem — involves graph traversal.
