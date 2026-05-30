# Frog Jump

**Problem Link:**
<a href="https://leetcode.com/problems/frog-jump/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/frog-jump/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Set Up the Scenario

A frog is at position 0 (the first stone). It wants to reach the last stone. Stones are at sorted positions given in `stones[]`. Between stones, there's water — the frog must land exactly on a stone.

Jump rule: if the frog's *previous jump* was of size `k`, the next jump can be `k-1`, `k`, or `k+1` (but must be ≥ 1). The frog's **first jump must be of size 1**.

Return true if the frog can reach the last stone.

Example: `stones = [0, 1, 3, 5, 6, 8, 12, 17]`.

Can the frog make it?
- Start at 0, jump 1 → 1. (Last jump = 1.)
- From 1, can jump 1, 2 (not 0). Options: 2 (not a stone), 3 (yes, size=2).
- From 3, last jump was 2. Options: 1, 2, 3. Lands at 4, 5, or 6. 5 and 6 are stones.
- Try 5 (last=2): options 1, 2, 3. Lands at 6, 7, 8. Stones: 6, 8.
  - Try 6 (last=1): options 1, 2. Lands at 7 or 8. 8 stone (last=2).
    - From 8, last=2: 9, 10, 11. None are stones. Fail this branch.
  - Try 8 (last=3): options 2, 3, 4. Lands at 10, 11, 12. 12 stone (last=4).
    - From 12, last=4: 15, 16, 17. 17 is the last stone! ✓

Yes, the frog can reach 17. Return true.

----------------------------------------

## Step 2: Identify the State

At any moment, the frog's **state** consists of:
- Which stone it's on (position).
- The jump size that brought it here.

The jump size matters because it constrains the next possible jumps. So the state is **(stone, last_jump)**, not just (stone).

If we just tracked (stone) without knowing the last jump, we couldn't decide what jumps are legal from there.

----------------------------------------

## Step 3: Brute Force DFS

Try all valid jumps from the current state:

```
def canReach(pos, lastJump):
    if pos == lastStone: return True
    for next_k in [lastJump - 1, lastJump, lastJump + 1]:
        if next_k <= 0: continue
        nextPos = pos + next_k
        if nextPos is a stone:
            if canReach(nextPos, next_k): return True
    return False
```

Start: `canReach(0, 0)`. The initial "lastJump = 0" triggers the "first jump of size 1" via `next_k = 1` (the `lastJump - 1` = -1 is rejected, `lastJump` = 0 is rejected because ≤ 0, `lastJump + 1` = 1 is valid).

The state space is bounded by (stones × possible jump sizes). On an n-stone array, the largest meaningful jump is ~n (can't jump farther than the length of the array). So state space is O(n²), but the naive DFS explores paths exponentially because it doesn't memoize.

Memoize on (pos, lastJump) and we're back to O(n²) states with O(1) transitions each → O(n²) total. That's tractable.

----------------------------------------

## Step 4: Let's Convert the DFS Into a Clean DP

Make the state concrete. For each stone position, we want to know: which last-jump sizes can *reach* this stone? If that set is non-empty, this stone is reachable.

Build a map: `reachable_jumps[position]` = set of jump sizes with which the frog can arrive at `position`.

Initialize `reachable_jumps[0] = {0}` (frog starts at 0 with "no previous jump" — represented as 0).

For each stone in order, for each jump size `k` that can reach it, try jumps `k-1, k, k+1` from it. If the landing position is a stone, add that new jump size to the landing stone's set.

The frog reaches the last stone iff `reachable_jumps[lastStone]` is non-empty at the end.

----------------------------------------

## Step 5: Trace on `[0, 1, 3, 5, 6, 8, 12, 17]`

Use `rj` for `reachable_jumps`. Let me track it as a dict.

Put stones in a set for O(1) membership check: `stoneSet = {0, 1, 3, 5, 6, 8, 12, 17}`.

```
rj[0] = {0}.
rj[1], rj[3], ..., rj[17] = {} initially.

Process stone 0 with jumps {0}:
  k=0: next jumps = -1, 0, 1. Only 1 is valid (>=1).
    Land at 0 + 1 = 1. Is 1 a stone? Yes. rj[1].add(1). rj[1] = {1}.

Process stone 1 with jumps {1}:
  k=1: next = 0, 1, 2. Valid: 1, 2.
    Land at 2 — not a stone. Skip.
    Land at 3 — stone. rj[3].add(2). rj[3] = {2}.

Process stone 3 with jumps {2}:
  k=2: next = 1, 2, 3.
    Land at 4 — not stone.
    Land at 5 — stone. rj[5].add(2). rj[5] = {2}.
    Land at 6 — stone. rj[6].add(3). rj[6] = {3}.

Process stone 5 with jumps {2}:
  k=2: next 1, 2, 3.
    Land at 6 — stone. rj[6].add(1). rj[6] = {1, 3}.
    Land at 7 — not stone.
    Land at 8 — stone. rj[8].add(3). rj[8] = {3}.

Process stone 6 with jumps {1, 3}:
  k=1: next 1, 2.
    Land at 7 — skip.
    Land at 8 — stone. rj[8].add(2). rj[8] = {2, 3}.
  k=3: next 2, 3, 4.
    Land at 8 — stone. rj[8].add(3). (already there)
    Land at 9 — skip. Land at 10 — skip.

Process stone 8 with jumps {2, 3}:
  k=2: next 1, 2, 3. Lands at 9, 10, 11 — none stones.
  k=3: next 2, 3, 4. Lands at 10, 11, 12. 12 is stone. rj[12].add(4). rj[12] = {4}.

Process stone 12 with jumps {4}:
  k=4: next 3, 4, 5. Lands at 15, 16, 17. 17 is stone. rj[17].add(5).

rj[17] = {5}, non-empty. Return true. ✓
```

----------------------------------------

## Step 6: Implementation Details

Data structures:
- `unordered_map<int, unordered_set<int>> rj` — position → set of last-jumps that reach here.
- `unordered_set<int> stoneSet` — for O(1) membership check.

Iterate stones in sorted order (they come sorted). For each, iterate its current jump-set (caveat: don't add to the set you're iterating). Try three candidate jumps from each.

----------------------------------------

## Step 7: Why It Works

**Claim:** the set `rj[p]` at the end of processing is exactly the set of jump sizes that can reach stone p via some valid sequence.

**Proof by induction over stones in order:** The first stone has `rj[0] = {0}` — trivially true (frog starts there). When we process a stone p, we've already processed all stones < p (sorted). For each jump size k in `rj[p]`, we try jumping from p with sizes k-1, k, k+1. If the landing is a stone q > p, we add the jump size to `rj[q]`.

This exactly captures "arrive at q via a jump from p." We cover all predecessors of q because p < q and we've processed all such p.

Hence `rj[q]` accumulates all valid entry jump sizes for q.

----------------------------------------

## Step 8: Name It

This is **DP over states (position, lastJump)**. It's different from usual 1D / 2D grid DPs because the "state" has two dimensions tied together. The same technique applies to:
- Knight's tour variations with state (position, moves_made).
- Games where future moves depend on past moves' structure.
- Keystroke counting problems with state machines.

The general recipe: identify what *future decisions depend on* (here: the last jump) and include it in the state.

----------------------------------------

## Step 9: Complexity

Time: For each stone, we consider up to O(n) possible jump sizes (bounded by stone positions), and for each do O(1) work. Total: **O(n²)**.
Space: **O(n²)** worst case for `rj`.

For `n = 2000`, that's 4 million operations — comfortable.

----------------------------------------

## Step 10: C++ Implementation

```cpp
bool canCross(vector<int>& stones) {
    unordered_set<int> stoneSet(stones.begin(), stones.end());
    unordered_map<int, unordered_set<int>> rj;
    for (int s : stones) rj[s] = {};
    rj[0] = {0};

    for (int pos : stones) {
        // Copy current set to avoid iterating while modifying (shouldn't happen, but safe)
        vector<int> jumps(rj[pos].begin(), rj[pos].end());
        for (int k : jumps) {
            for (int next_k : {k - 1, k, k + 1}) {
                if (next_k <= 0) continue;
                int nextPos = pos + next_k;
                if (stoneSet.count(nextPos)) {
                    rj[nextPos].insert(next_k);
                }
            }
        }
    }

    return !rj[stones.back()].empty();
}
```

Key details:
- We copy the current jump set to `jumps` before iterating to avoid any concern with adding to the set being iterated (though in practice we add to *later* positions, not the current one).
- The triple "next_k in {k-1, k, k+1}" loop compactly handles the three jump options.
- `next_k <= 0` guard rejects non-positive jumps.

----------------------------------------

## Step 11: Follow-up Questions

- **Minimum number of jumps to reach the end.** Different DP — track min jumps to reach each stone.
- **Frog can jump backward too.** Much harder — cycles become possible.
- **Count distinct ways to reach the end.** Switch boolean set to integer count; sum over predecessors.
- **What if jump rule is k±2 instead of k±1?** Same structure, different transitions.
- **Return an actual jump sequence.** Store parent pointers when updating `rj[nextPos]`; reconstruct by walking back.
- **Stones have weights that limit the frog's jump.** Add a state dimension for cumulative weight.
