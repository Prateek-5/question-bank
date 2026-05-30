# Find the Smallest Binary Digit Multiple of Given Number

**Problem Link:**
<a href="https://www.geeksforgeeks.org/dsa/find-the-smallest-binary-digit-multiple-of-given-number/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/find-the-smallest-binary-digit-multiple-of-given-number/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: State the Task

Given a positive integer `n`, find the **smallest positive multiple of n that consists only of digits 0 and 1** (a "binary digit" number written in base 10).

Example: n = 2. Smallest such multiple is **10** (digits 1 and 0).
Example: n = 3. Smallest is **111** (3 × 37).
Example: n = 5. Smallest is **10** (digits 1 and 0).
Example: n = 7. Smallest is **1001001** (7 × 143).

We want the **smallest in numerical value**. Note: such a multiple always exists.

----------------------------------------

## Step 2: Why Does a Solution Exist?

Consider the numbers `1, 11, 111, 1111, 11111, ...` There are infinitely many. By the **pigeonhole principle**, two of them have the same remainder mod n. Say they're `R_i` and `R_j` with i < j and `R_i ≡ R_j (mod n)`.

Then `R_j - R_i` is divisible by n. And `R_j - R_i = 111...1 000...0` — a number with some 1's followed by zeros. Those are exactly the digits we allow!

So a valid multiple always exists. Now: how to find the smallest?

----------------------------------------

## Step 3: Build the Search Space

Every candidate has digits only in {0, 1}, with a leading 1. So candidates are:

```
1, 10, 11, 100, 101, 110, 111, 1000, 1001, 1010, 1011, 1100, ...
```

These are the **binary representations read as decimal digit strings**. If we enumerate them in this order (1, then all 2-digit starting with 1, then all 3-digit starting with 1, ...), we scan from smallest upward.

For each, check if it's divisible by n. The first one that is, return.

This works but can generate huge numbers (beyond 64-bit) for moderate n.

----------------------------------------

## Step 4: BFS in "Remainder Space"

Here's the trick. Instead of tracking the full number, track its **remainder mod n**. We care only about the remainder (to decide divisibility) and the digit string (to report the answer).

Consider a graph where:
- **Nodes** are remainders 0, 1, ..., n-1.
- Starting node: remainder of `"1"` = 1 mod n.
- From remainder `r`, we can extend our digit string by appending a `0` or `1`:
  - Append `0`: new number = 10·old_number. New remainder = (10·r) mod n.
  - Append `1`: new number = 10·old_number + 1. New remainder = (10·r + 1) mod n.

So from node `r`, we have edges to `(10·r) mod n` and `(10·r + 1) mod n`.

**Goal:** reach node 0 (remainder 0 = divisible).

**BFS** from node 1 finds the shortest path to 0, i.e., the fewest-digit binary-digit multiple. Track the digit string along each BFS path; return when we hit 0.

----------------------------------------

## Step 5: Algorithm

```
if n == 1: return "1"

queue = [(remainder=1, string="1")]
visited = {1}

while queue not empty:
    (r, s) = dequeue
    if r == 0: return s                  # found multiple
    for digit in ['0', '1']:
        new_r = (r * 10 + int(digit)) % n
        if new_r not in visited:
            visited.add(new_r)
            enqueue((new_r, s + digit))
```

At most `n` distinct remainders, so the BFS terminates in O(n) work. Each node enqueued once.

----------------------------------------

## Step 6: Trace — n = 3

Start: queue = [(1, "1")]. visited = {1}.

```
Dequeue (1, "1"). r = 1, not 0.
  Append '0': new_r = (1·10 + 0) % 3 = 10 % 3 = 1. Already visited. Skip.
  Append '1': new_r = (1·10 + 1) % 3 = 11 % 3 = 2. Enqueue (2, "11"). visited = {1, 2}.

Dequeue (2, "11"). r = 2, not 0.
  Append '0': new_r = 20 % 3 = 2. Visited. Skip.
  Append '1': new_r = 21 % 3 = 0. Enqueue (0, "111"). visited = {0, 1, 2}.

Dequeue (0, "111"). r = 0. Return "111".
```

Output: **111**. ✓ (3 × 37 = 111.)

Note how we never actually computed 111 as a big integer — only remainders.

----------------------------------------

## Step 7: Why BFS (not DFS)?

BFS explores shortest paths first. Since each step appends one digit, BFS produces the answer with **fewest digits** — which is the smallest number (fewer digits = smaller magnitude, among numbers with a leading 1).

Within the same length, BFS would explore 0-first before 1-first if we enqueue '0' before '1'. So among equal-length candidates, we get the lexicographically smallest — which for binary-digit strings with leading 1 is also numerically smallest.

DFS wouldn't guarantee either property.

----------------------------------------

## Step 8: Name It

**BFS on a finite state space** (remainders mod n). The broader pattern:
- State = some invariant we care about (here, remainder).
- Transitions = bounded moves (append digit 0 or 1).
- Goal = reach a target state (remainder 0).

This same pattern solves:
- Open the Lock (state = 4-digit code; transitions = rotate any wheel ±1).
- Jug-filling problems (state = (jug1, jug2); transitions = fill/empty/pour).
- Word ladder (state = word; transitions = change one letter).

Recognizing "smallest X satisfying Y" + bounded state space → BFS.

----------------------------------------

## Step 9: Complexity

Time: **O(n)** — at most n distinct remainders, each dequeued once. Constructing the answer string is O(digit count) = O(log of the answer), bounded by O(n).
Space: **O(n)** for the queue and visited set.

----------------------------------------

## Step 10: C++ Implementation

```cpp
string smallestBinaryDigitMultiple(int n) {
    if (n == 1) return "1";

    queue<pair<int, string>> q;
    vector<bool> visited(n, false);
    q.push({1 % n, "1"});
    visited[1 % n] = true;

    while (!q.empty()) {
        auto [r, s] = q.front(); q.pop();
        if (r == 0) return s;
        for (char d : {'0', '1'}) {
            int nr = (r * 10 + (d - '0')) % n;
            if (!visited[nr]) {
                visited[nr] = true;
                q.push({nr, s + d});
            }
        }
    }
    return "";   // unreachable by pigeonhole argument
}
```

Storing the full string in the queue can bloat memory for large n. Alternative: store only the **predecessor** per state and reconstruct the path when we find 0.

----------------------------------------

## Step 11: Follow-up Questions

- **Return just the length, not the string.** Drop the string tracking — pure BFS distance.
- **Digits allowed only {0, 1} and {2}.** Three-way branching; same algorithm.
- **Largest such multiple ≤ N.** Different problem — digit DP.
- **Avoid the string explosion for huge n.** Track parent pointers; reconstruct the digit sequence when we hit 0.
- **Pigeonhole intuition for existence.** Among n + 1 consecutive repunits (1, 11, ..., 11...1), two share a remainder; their difference is a valid candidate.
- **Why start from remainder 1 % n?** The smallest candidate is "1"; every candidate must start with digit 1 (no leading zeros).
