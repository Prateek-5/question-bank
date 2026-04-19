# Minimum Jumps to Reach Home

**Problem Link:**
https://leetcode.com/problems/minimum-jumps-to-reach-home/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Read the Problem

A bug is at position 0 on a number line. It wants to reach home at position `x`. Each move, the bug can:
- **Jump forward** `a` units (always allowed).
- **Jump backward** `b` units (allowed only if the previous move was not also a backward jump).

Some positions are **forbidden**: a list `forbidden[]` of integers the bug can never land on. Also, positions must be ≥ 0.

Return the **minimum number of jumps** to reach x, or -1 if impossible.

Example: `forbidden = [14, 4, 18, 1, 15]`, a = 3, b = 15, x = 9.

The bug can do: 0 → 3 → 6 → 9. Three forward jumps of size 3. Zero backward jumps needed. Answer: **3**.

----------------------------------------

## Step 2: Think About the State

Each moment, we track:
- **Current position.**
- **Whether the previous jump was backward** (because we can't do two backward jumps in a row).

So state is a pair `(position, last_was_backward)`. Minimum-jumps question in a state graph = BFS (unweighted shortest path).

Transitions from state (p, b):
- Forward: (p + a, false). Always allowed if p + a is not forbidden and in bounds.
- Backward: (p - b, true). Allowed if `b == false` (last was not backward) and `p - b >= 0` and not forbidden.

BFS from (0, false). Find shortest path to any state (x, *).

----------------------------------------

## Step 3: Bounded Search Space

Positions in theory can be unbounded. In practice, there's an upper bound we don't need to exceed.

**Claim:** we never need to reach positions beyond some limit L. What's L?

Intuition: forward jumps increase position by a; backward by b. If we go too far forward, we can only go back one step (then a forward again). The constraint "no two backward in a row" limits how much we can go back after going forward.

A reasonable safe bound: `L = max(x + b, max_forbidden + a + b) + some_safety`. Most solutions use `L = 6000` or compute tighter bounds analytically. The exact proof is beyond the scope, but the key idea: we never benefit from going past x by more than (a + b) times the forbidden-array size.

For simplicity, we'll use L = 6000 (LeetCode's constraint range is small).

----------------------------------------

## Step 4: BFS Algorithm

```
forbidden_set = set(forbidden)
visited = {(0, false)}
queue = [(0, false, 0)]   # (position, last_backward, jumps)

while queue not empty:
    (p, b, j) = queue.pop_front()
    if p == x: return j

    # forward jump
    next_p = p + a
    if next_p <= LIMIT and next_p not in forbidden_set and (next_p, false) not in visited:
        visited.add((next_p, false))
        queue.push((next_p, false, j + 1))

    # backward jump (only if last was not backward)
    if not b:
        back_p = p - b
        if back_p >= 0 and back_p not in forbidden_set and (back_p, true) not in visited:
            visited.add((back_p, true))
            queue.push((back_p, true, j + 1))

return -1
```

BFS guarantees shortest number of jumps.

----------------------------------------

## Step 5: Why We Need Position × LastMove State, Not Just Position

If we tracked only position, we'd lose information about what jumps are currently legal. Two paths arriving at the same position with different "last-was-backward" flags have different future options. So we must track both.

This is a common DP / BFS pattern: **state dimension matches the facts that affect future moves**.

----------------------------------------

## Step 6: Trace on the Example

`forbidden = {14, 4, 18, 1, 15}`, a = 3, b = 15, x = 9.

```
Start: (0, F, 0). visited = {(0, F)}.

Pop (0, F, 0).
  Forward: (3, F). Not forbidden, not visited. Enqueue. visited += (3, F).
  Backward: last wasn't backward, so OK. But 0 - 15 = -15 < 0. Skip.

Pop (3, F, 1).
  Forward: (6, F). Enqueue.
  Backward: 3 - 15 = -12. Skip.

Pop (6, F, 2).
  Forward: (9, F). Enqueue.
  Backward: -9. Skip.

Pop (9, F, 3). p == x = 9. Return 3.
```

✓ Matches.

For harder examples involving backward jumps, the state machine correctly models the restriction. E.g., if we jumped back once, we can't jump back again immediately — we must jump forward first.

----------------------------------------

## Step 7: Complexity

Time: BFS over O(L) positions × 2 (for the last-direction flag) = O(L). Each state explores O(1) neighbors. **O(L)** total.
Space: O(L) for the visited set and queue.

With L = 6000, this is extremely fast.

----------------------------------------

## Step 8: Name It

This is **BFS on a state graph** where the state is richer than just "position" — it also encodes recent-history information ("was my last jump backward?").

The trick of adding a state dimension for "last move" applies widely:
- Knight tour with "no three of the same move in a row."
- Paint House (where each color depends on previous).
- Cooldown-based stock trading DP.

Whenever a problem says "you can't do X twice in a row" or similar, add a state flag for "did I just do X?"

----------------------------------------

## Step 9: C++ Implementation

```cpp
int minimumJumps(vector<int>& forbidden, int a, int b, int x) {
    unordered_set<int> forbiddenSet(forbidden.begin(), forbidden.end());
    const int LIMIT = 6000;   // safe upper bound
    
    // Visited: (position, last_was_backward) → encoded as position * 2 + (last_backward ? 1 : 0)
    unordered_set<int> visited;
    visited.insert(0);   // (0, false)
    
    queue<tuple<int, bool, int>> q;
    q.push({0, false, 0});

    while (!q.empty()) {
        auto [p, backLast, jumps] = q.front(); q.pop();
        if (p == x) return jumps;

        // forward
        int fp = p + a;
        if (fp <= LIMIT && !forbiddenSet.count(fp)) {
            int key = fp * 2 + 0;   // forward: lastBackward = false
            if (!visited.count(key)) {
                visited.insert(key);
                q.push({fp, false, jumps + 1});
            }
        }
        // backward (only if last was not backward)
        if (!backLast) {
            int bp = p - b;
            if (bp >= 0 && !forbiddenSet.count(bp)) {
                int key = bp * 2 + 1;
                if (!visited.count(key)) {
                    visited.insert(key);
                    q.push({bp, true, jumps + 1});
                }
            }
        }
    }
    return -1;
}
```

Visited set encodes (position, lastBackward) as a single integer. The BFS runs until we reach x or exhaust the state space.

----------------------------------------

## Step 10: Follow-up Questions

- **Allow k backward jumps in a row (not 1).** Extend state to (position, consecutive_backward).
- **Dynamic forbidden list.** Each jump, some cells become forbidden. Use a dynamic data structure.
- **Weighted jumps (different costs).** Use Dijkstra instead of BFS.
- **Return the actual sequence of jumps.** Track parent pointers during BFS.
- **Prove the L bound more carefully.** Related to worst-case oscillation between forward and backward jumps.
- **What if a = b?** Doesn't fundamentally change the problem; same algorithm.
