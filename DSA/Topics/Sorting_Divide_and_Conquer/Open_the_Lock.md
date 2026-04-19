# Open the Lock

**Problem Link:**
https://leetcode.com/problems/open-the-lock/

**Topic:**
Sorting / Divide and Conquer (really a BFS problem)

----------------------------------------

## Step 1: The Scenario

You have a 4-digit rotating lock. Each wheel shows a digit 0..9. You can rotate any wheel up by one (9 → 0 wraps) or down by one (0 → 9 wraps) per move.

Starting from `"0000"`, find the **minimum number of moves** to reach `target`. Some combinations are **deadends** — landing on any deadend is forbidden.

Return -1 if the target is unreachable (deadends block every path).

Example: `deadends = ["0201","0101","0102","1212","2002"]`, `target = "0202"`.

Many direct routes like 0000 → 0001 → ... → 0201 → 0202 hit deadends. A valid path: `"0000" → "1000" → "1100" → "1200" → "1201" → "1202" → "0202"`. Length **6**.

----------------------------------------

## Step 2: Why BFS?

We want the minimum number of moves between two states. Each state is a 4-digit string; from each, there are **8 neighbors** (4 wheels × 2 directions). State count is 10⁴ = 10,000.

"Minimum number of moves in an unweighted graph" → **BFS**. BFS from "0000" explores states in order of distance.

----------------------------------------

## Step 3: Define the Graph Structure

- **Nodes**: 10⁴ possible 4-digit strings "0000" to "9999".
- **Edges**: two strings are connected if they differ by one wheel turn (one digit by ±1, with 0↔9 wrap).
- **Source**: "0000".
- **Target**: the given target string.
- **Blocked**: every string in `deadends` is unreachable (don't enqueue it).

Also block "0000" if it's in deadends — if so, return -1 immediately.

----------------------------------------

## Step 4: BFS Algorithm

```
if "0000" in deadends: return -1
if target == "0000": return 0

visited = set(deadends) ∪ {"0000"}
queue = [("0000", 0)]

while queue not empty:
    (state, depth) = queue.pop_front()
    for each neighbor n of state:
        if n == target: return depth + 1
        if n not in visited:
            visited.add(n)
            queue.push((n, depth + 1))

return -1
```

Neighbor generation: for each of 4 wheel positions, produce two rotations:
- `digit + 1 mod 10`
- `(digit + 9) mod 10` (equivalent to -1 mod 10).

----------------------------------------

## Step 5: Trace on a Tiny Example

Suppose `target = "0001"`, no deadends.

```
visited = {"0000"}. queue = [("0000", 0)].

Pop ("0000", 0). Generate 8 neighbors:
  wheel 0: "1000", "9000"
  wheel 1: "0100", "0900"
  wheel 2: "0010", "0090"
  wheel 3: "0001", "0009"
Check "0001" — it's the target. Return 0 + 1 = 1.
```

Answer: **1** move. Correct — rotate wheel 3 from 0 to 1.

For the deadend example (target = "0202"), BFS explores layer by layer, skipping deadends. The first time "0202" appears in BFS, its depth is the answer.

----------------------------------------

## Step 6: Optimization — Bidirectional BFS

For large state spaces, **bidirectional BFS** doubles speed:
- Simultaneously expand from "0000" and from `target`.
- When the two frontiers meet, the total depth = sum of the two expansions.

Why faster? BFS explores O(b^d) nodes where b = branching factor (here 8) and d = depth. Two BFSs of depth d/2 each explore O(2 · b^(d/2)) — much smaller than b^d for moderate d.

For this problem with 10,000 total states, regular BFS is already fast enough.

----------------------------------------

## Step 7: Why This Isn't Really a "Sorting" Problem

Despite the topic label, this is a pure BFS / shortest-path problem. The "sorting / divide-and-conquer" label is likely because it pairs well with other level-order-exploration problems.

The mental model: treat the problem as a graph where nodes = states, edges = one-move transitions. BFS from start finds shortest path, naturally respecting all blocked states.

----------------------------------------

## Step 8: Name It

**BFS on implicit state graph.** A hallmark pattern for:
- Sliding puzzles (8-puzzle, 15-puzzle).
- Word ladder (word-to-word one-letter swap).
- Minimum genetic mutations.
- Shortest path in a maze.
- Rubik's cube (though state space becomes astronomical; needs smarter).

The graph isn't materialized — neighbors are computed on-demand from the current state.

----------------------------------------

## Step 9: Complexity

State space: **10⁴ = 10,000**. Each state has 8 neighbors. BFS is O(|V| · 8) = O(80,000) operations — fast.

Time: **O(|V| · b)** where b = 8.
Space: **O(|V|)** for visited set and queue.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int openLock(vector<string>& deadends, string target) {
    unordered_set<string> visited(deadends.begin(), deadends.end());
    if (visited.count("0000")) return -1;
    if (target == "0000") return 0;

    visited.insert("0000");
    queue<pair<string, int>> q;
    q.push({"0000", 0});

    while (!q.empty()) {
        auto [state, depth] = q.front(); q.pop();
        for (int i = 0; i < 4; ++i) {
            for (int d : {1, -1}) {
                string next = state;
                next[i] = '0' + ((state[i] - '0' + d + 10) % 10);
                if (next == target) return depth + 1;
                if (!visited.count(next)) {
                    visited.insert(next);
                    q.push({next, depth + 1});
                }
            }
        }
    }
    return -1;
}
```

Neighbor loop: 4 wheels × 2 directions = 8 per state. `(digit + d + 10) % 10` handles 0 → 9 wrap without negative modulo issues.

----------------------------------------

## Step 11: Follow-up Questions

- **Return the actual path (sequence of states), not just count.** Track parent pointers; reconstruct from target.
- **Multi-direction rotations (e.g., ±2 in one move).** Add more neighbor types.
- **5-wheel or 10-wheel lock.** State space grows exponentially; bidirectional BFS becomes essential.
- **Weighted moves (some rotations cost more).** Dijkstra instead of BFS.
- **Very large target space (can't enumerate visited).** Use A* with a heuristic like "sum of wheel distances to target."
- **Why BFS, not DFS?** BFS guarantees shortest path; DFS may find the target via a long path first.
