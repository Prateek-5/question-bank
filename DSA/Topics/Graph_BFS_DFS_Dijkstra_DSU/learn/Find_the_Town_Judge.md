# Find the Town Judge — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_the_Town_Judge.md`](../Find_the_Town_Judge.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-the-town-judge/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: model "trust" as DIRECTED EDGES. The judge is a node with IN-DEGREE = n - 1 and OUT-DEGREE = 0. Collapse both counters into one score per node for a one-pass solution.**

**Map of this file (8 sections):**

1. Read the problem
2. Cast it as a graph
3. The two-counter version
4. The one-pass score trick
5. Code
6. Trace it
7. Why "score == n - 1" uniquely identifies the judge
8. The shape — degree-based identification

---

## 1. Read the problem

In a town of `n` people labeled `1..n`, there is a (possible) "town judge" with two defining properties:

1. **The judge trusts nobody.**
2. **Everyone else trusts the judge.**

Given a list `trust[][]` where `trust[i] = [a, b]` means "a trusts b," return the judge's label or `-1` if no valid judge exists.

**Examples:**

- `n = 2, trust = [[1, 2]]` → 2 is trusted by 1, trusts no one → judge is **2**.
- `n = 3, trust = [[1, 3], [2, 3]]` → 3 is trusted by 1, 2, trusts no one → judge is **3**.
- `n = 3, trust = [[1, 3], [2, 3], [3, 1]]` → 3 trusts 1, so 3 fails property 1 → **-1**.

---

## 2. Cast it as a graph

> **Mini-refresher: trust is a DIRECTED edge.**
>
> "a trusts b" means an edge `a → b`. Then:
> - The judge has **OUT-degree 0** (no outgoing edges — trusts no one).
> - The judge has **IN-degree n - 1** (every other person points at them).

Count both degrees per node; find the unique node satisfying both conditions.

---

## 3. The two-counter version

```
in_deg  = [0] * (n + 1)
out_deg = [0] * (n + 1)
for (a, b) in trust:
    out_deg[a]++
    in_deg[b]++
for p in 1..n:
    if in_deg[p] == n - 1 and out_deg[p] == 0:
        return p
return -1
```

Works. O(m + n) time, O(n) space. But we can collapse the two counters.

---

## 4. The one-pass score trick

> **Mini-refresher: combine two signed counters into ONE.**
>
> Let `score[p] = in_degree(p) - out_degree(p)`.
>
> For the judge: `score = (n - 1) - 0 = n - 1`. For everyone else: `score < n - 1` (proven in section 7).
>
> Each trust edge `[a, b]` does two things: `score[a]--` (a trusts someone) and `score[b]++` (b is trusted).

```
score = [0] * (n + 1)
for (a, b) in trust:
    score[a]--
    score[b]++
for p in 1..n:
    if score[p] == n - 1: return p
return -1
```

One array, one pass.

---

## 5. Code

**C++:**

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

**Python:**

```python
def findJudge(n, trust):
    score = [0] * (n + 1)
    for a, b in trust:
        score[a] -= 1
        score[b] += 1
    for p in range(1, n + 1):
        if score[p] == n - 1:
            return p
    return -1
```

Complexity: **O(m + n)** time (m = `len(trust)`), **O(n)** space.

---

## 6. Trace it

**`n = 3, trust = [[1, 3], [2, 3]]`:**

```
score start: [_, 0, 0, 0]
[1, 3]: score[1] = -1, score[3] = 1.
[2, 3]: score[2] = -1, score[3] = 2.
score end:   [_, -1, -1, 2]

Target = n - 1 = 2. Person 3 has score 2 → return 3.  ✓
```

**`n = 3, trust = [[1, 3], [2, 3], [3, 1]]`:**

```
[1, 3]: score = [_, -1, 0, 1]
[2, 3]: score = [_, -1, -1, 2]
[3, 1]: score = [_, 0, -1, 1]

Target = 2. No one has score 2 → return -1.  ✓
```

The `[3, 1]` edge knocks 3 down from "judge" status because it gives 3 an outgoing edge.

---

## 7. Why "score == n - 1" uniquely identifies the judge

Bound the score:
- `in_degree(p) ≤ n - 1` (at most n - 1 other people can point to p).
- `out_degree(p) ≥ 0`.

So `score(p) = in - out ≤ n - 1`, with equality iff `in = n - 1` AND `out = 0`. There's no slack — both conditions must hold simultaneously. That's exactly the judge.

> **Mini-refresher: this works only when the maximum is achievable by exactly one combination of `in` and `out`.**
>
> If we wanted "in = n - 2 AND out = 0" — a different combination summing to n - 2 might exist (in = n - 1, out = 1). Score alone wouldn't separate them; you'd need both counters.

---

## 8. The shape — degree-based identification

The pattern: **identify nodes by degree properties.**

| Property | Looks like |
|---|---|
| **Judge** | in = n - 1, out = 0 |
| **Universal sink** | in = n - 1, out = 0 (same shape; common interview question) |
| **Celebrity** | knows nobody, known by everyone (same shape) |
| **Leaf in a tree** | degree = 1 |
| **Hub** | high total degree |
| **Root of a directed tree** | in = 0 |

**Pattern to internalize:**

> "When the answer is characterized by IN- vs OUT-degree thresholds, count degrees in one pass. If two thresholds can collapse into one expression (`in - out = target`), use a single score array."

---

> **Self-check — the question to ask next time.**
>
> When the problem describes a special node by who-points-to-whom rules, ask:
>
> > **"Can I express the node's property as `in_degree = X` and `out_degree = Y`? Do those collapse into `in - out = X - Y` uniquely?"**

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_the_Town_Judge.md`](../Find_the_Town_Judge.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Keys_and_Rooms.md`](./Keys_and_Rooms.md).
  - Coming next: [`Find_Eventual_Safe_States.md`](./Find_Eventual_Safe_States.md), [`Is_Graph_Bipartite.md`](./Is_Graph_Bipartite.md).
