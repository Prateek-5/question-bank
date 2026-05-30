# Open the Lock — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Open_the_Lock.md`](../Open_the_Lock.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/open-the-lock/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/open-the-lock/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **A BFS problem mislabeled as "Sorting/Divide-and-Conquer."** The lesson: **shortest path in an unweighted graph = BFS. The graph here is the STATE GRAPH of lock combinations; edges are valid moves; deadends are blocked nodes.** Master this pattern; it powers Word Ladder, Sliding Puzzle, and many other shortest-path-on-states problems.

**Map of this file (10 short sections):**

1. Read the problem
2. The state graph model
3. Why BFS (not DFS)
4. Generating neighbors
5. Handling deadends
6. Code
7. Trace it
8. Bidirectional BFS (optimization)
9. Common pitfalls
10. The shape — BFS on implicit state graphs

---

## 1. Read the problem

You have a 4-digit rotating lock. Each wheel shows a digit 0-9. You can rotate any one wheel by 1 position (up or down, wrapping 9↔0) per move.

Start: `"0000"`. Target: a given 4-digit string. Some strings are **deadends** — you can never visit them.

Return the **MINIMUM number of moves** to reach the target. If impossible, return -1.

**Example:**
- `deadends = ["0201","0101","0102","1212","2002"]`, `target = "0202"`.
- A valid path: `"0000" → "1000" → "1100" → "1200" → "1201" → "1202" → "0202"`. Length **6**.

---

## 2. The state graph model

> **Mini-refresher: graph as a problem model.**
>
> Many "what's the minimum number of operations to transform X into Y?" problems become GRAPH SHORTEST PATH problems.
>
> - **Nodes**: all valid states.
> - **Edges**: pairs of states reachable in ONE operation.
> - **Source**: starting state.
> - **Target**: ending state.
> - **Blocked nodes**: deadends.
>
> The answer is the LENGTH of the shortest path from source to target.

For this problem:
- Nodes: all 10⁴ = 10,000 4-digit strings `"0000"` to `"9999"`.
- Edges: two states are connected iff they differ in EXACTLY ONE digit by ±1 (with wrap).
- Source: `"0000"`. Target: given. Blocked: deadends.

---

## 3. Why BFS (not DFS)

BFS explores states in INCREASING ORDER OF DISTANCE FROM THE SOURCE. When BFS first encounters the target, the depth equals the SHORTEST PATH LENGTH.

DFS could find a path, but not necessarily the shortest. It might wander deep before finding target.

For UNWEIGHTED graphs (all edges have the same cost — here, each move is "one step"), **BFS is the right tool for shortest path.**

> **Mini-refresher: BFS structure.**
>
> ```
> queue = [(source, 0)]
> visited = {source}
> while queue:
>     (state, depth) = queue.pop_front()   # FIFO — front of queue
>     if state == target: return depth
>     for neighbor in neighbors(state):
>         if neighbor not in visited:
>             visited.add(neighbor)
>             queue.push((neighbor, depth + 1))
> return -1
> ```
>
> FIFO ordering ensures we process states in order of distance.

---

## 4. Generating neighbors

For a 4-digit state, there are **8 neighbors** (4 wheels × 2 directions).

For each wheel position `i`:
- Rotate UP: `digit + 1 mod 10` (9 → 0).
- Rotate DOWN: `(digit + 9) mod 10` (0 → 9).

```
def neighbors(state):
    result = []
    for i in 0..3:
        digit = int(state[i])
        for d in [+1, -1]:
            new_digit = (digit + d + 10) % 10
            new_state = state[:i] + str(new_digit) + state[i+1:]
            result.append(new_state)
    return result
```

The `+ 10` before mod ensures non-negative even for `-1` (in languages where mod of negative gives negative).

---

## 5. Handling deadends

A deadend is a state we can NEVER enter. The cleanest approach: treat deadends as ALREADY VISITED. They'll be skipped when checking neighbors.

```
visited = set(deadends) ∪ {"0000"}
```

Exception: if `"0000"` itself is a deadend, return -1 immediately (we can't even start).

---

## 6. Code

**C++:**

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

**Python:**

```python
from collections import deque

def openLock(deadends, target):
    dead = set(deadends)
    if "0000" in dead:
        return -1
    if target == "0000":
        return 0

    visited = dead | {"0000"}
    q = deque([("0000", 0)])

    while q:
        state, depth = q.popleft()
        for i in range(4):
            for d in (1, -1):
                new_digit = (int(state[i]) + d) % 10
                next_state = state[:i] + str(new_digit) + state[i+1:]
                if next_state == target:
                    return depth + 1
                if next_state not in visited:
                    visited.add(next_state)
                    q.append((next_state, depth + 1))
    return -1
```

Complexity: **O(|V| × b)** where |V| = 10,000 states and b = 8 (branching factor). About **80,000 operations** — fast.

Space: **O(|V|)** for visited and queue.

---

## 7. Trace it

**Simple case: `target = "0001"`, no deadends.**

```
visited = {"0000"}. q = [("0000", 0)].

Pop ("0000", 0). Generate 8 neighbors:
  wheel 0: "1000", "9000".
  wheel 1: "0100", "0900".
  wheel 2: "0010", "0090".
  wheel 3: "0001", "0009".

Check each: "0001" == target. Return depth + 1 = 1.  ✓
```

**Complex case with deadends:** BFS explores level-by-level, skipping deadends and revisits, until the target appears in some neighbor expansion. The depth at that moment is the answer.

---

## 8. Bidirectional BFS (optimization)

For very large state spaces, **bidirectional BFS** dramatically speeds things up:

- Run BFS from BOTH the source and the target simultaneously.
- When the two frontiers MEET (some state visited from both sides), the total depth = source_depth + target_depth.

**Why faster?** Standard BFS at depth d explores `O(b^d)` nodes. Bidirectional BFS at depth d/2 from each side explores `O(2 * b^(d/2))` — exponentially smaller.

For this problem with only 10,000 states, regular BFS is already fast enough. But for problems with 10⁶+ states, bidirectional is essential.

---

## 9. Common pitfalls

1. **Using DFS.** DFS doesn't give shortest path. Use BFS for unweighted shortest path.

2. **Not adding deadends to visited.** Then BFS will explore them, slowly returning -1 or visiting unreachable areas.

3. **Forgetting to check if "0000" is a deadend.** Return -1 immediately if so.

4. **Forgetting target == "0000" edge case.** Return 0.

5. **Marking visited AFTER popping from queue instead of when ENQUEUEING.** Causes the same state to be enqueued multiple times. ALWAYS mark visited at enqueue time.

6. **Incorrect digit wrap.** Use `(digit + d + 10) % 10` to handle -1 correctly across languages.

7. **Returning the depth when popping the TARGET.** Either: (a) return depth when popping if state == target; or (b) return depth + 1 when generating a neighbor == target. Pick one and be consistent.

8. **Storing states as integers vs strings.** Either works. Strings are more readable; integers (e.g., 4-digit number) are more compact and faster to hash.

---

## 10. The shape — BFS on implicit state graphs

The pattern: **shortest path on a graph where nodes are STATES and edges are TRANSITIONS — even if the graph isn't materialized.**

Where this applies:

| Problem | States | Transitions |
|---|---|---|
| **This problem** | 4-digit lock states | one wheel ±1 |
| Word Ladder | dictionary words | change one letter |
| Sliding Puzzle (8-puzzle, 15-puzzle) | tile positions | swap blank with adjacent |
| Min Genetic Mutation | gene strings | one-character substitution |
| Shortest Bridge (matrix BFS) | grid cells | adjacent moves |
| Snakes and Ladders | board positions | dice roll + ladder/snake |
| Rotting Oranges | grid cells | adjacent infection spread |

**Pattern to internalize:**

> "Minimum NUMBER OF OPERATIONS to transform X into Y often = BFS on the STATE GRAPH. Nodes = states. Edges = single-operation transitions. Run BFS from X; return depth when you first reach Y."

The graph is rarely materialized in memory — neighbors are computed ON DEMAND from each state.

---

> **Self-check — the question to ask next time.**
>
> When you face "minimum number of moves/operations/steps to transform X into Y," ask:
>
> > **"What are the STATES? What are the one-step TRANSITIONS? Can I run BFS from X over this state graph?"**
>
> If yes, you've got an unweighted shortest path.

---

## Cross-references

- **Reference card (post-mastery):** [`../Open_the_Lock.md`](../Open_the_Lock.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Sorting topic complete!
  - Coming much later: Word_Ladder (in Graph topic) — same BFS pattern.
