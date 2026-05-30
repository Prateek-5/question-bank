# Satisfiability of Equality Equations

**Problem Link:**
<a href="https://leetcode.com/problems/satisfiability-of-equality-equations/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/satisfiability-of-equality-equations/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Problem

You have a list of equations like `"a==b"` or `"a!=b"`, where each equation uses lowercase letters (variables).

Determine if there's a way to assign integer values to the variables so that **all equations are simultaneously satisfied**.

Example: `["a==b", "b!=a"]`. 
- First: a and b are equal.
- Second: a and b are NOT equal.
- Contradiction. Return false.

Example: `["b==a", "a==b"]`. Both say the same thing. Return true.

Example: `["a==b", "b==c", "a==c"]`. All consistent. Return true.

----------------------------------------

## Step 2: Classify Variables by Equality

All `==` equations partition the variables into **equivalence classes**: variables that must be equal to each other.

Any two variables in the same class must have the same value. Variables in different classes can be assigned different values.

Now the `!=` equations say: variables on both sides must be in **different** classes. If any `!=` equation has both sides in the **same** class (as determined by the `==` equations), that's a contradiction — return false.

Otherwise, we can assign distinct values to different classes and satisfy everything.

----------------------------------------

## Step 3: Union-Find Is a Perfect Fit

Union-Find (DSU) exactly models equivalence classes:
- Union(a, b) puts a and b in the same class.
- Find(a) returns the class representative.
- Two variables are in the same class iff find(a) == find(b).

Algorithm:
1. Process all `==` equations, union the two variables.
2. Process all `!=` equations; for each, check if find(a) == find(b). If yes, contradiction.

Two passes: first all equalities, then all inequalities.

----------------------------------------

## Step 4: Trace on `["a==b", "b!=c", "c==a"]`

Variables as indices: a=0, b=1, c=2.

Pass 1: `==` equations.
- `a==b`: union(0, 1). Classes: {0, 1}, {2}.
- `c==a`: union(2, 0). Classes: {0, 1, 2}.

Pass 2: `!=` equations.
- `b!=c`: find(1) == find(2)? Both are in {0, 1, 2}. Same root. CONTRADICTION. Return false.

----------------------------------------

## Step 5: Trace on `["a==b", "b==c", "a!=d"]`

Variables: a=0, b=1, c=2, d=3.

Pass 1:
- `a==b`: union(0, 1).
- `b==c`: union(1, 2). Now {0, 1, 2}, {3}.

Pass 2:
- `a!=d`: find(0) = root of {0,1,2}, find(3) = 3. Different. OK.

No contradictions. Return true.

----------------------------------------

## Step 6: Why Two Passes, Not Interleaved?

If we processed equations in their original order, an `!=` might appear before an `==` that would have unified the classes involved. The `!=` check would falsely pass at that moment, only to become invalid later.

By processing **all `==` first**, we finalize all equivalence classes. Then `!=` checks have accurate class information.

----------------------------------------

## Step 7: Name It

**Union-Find for equivalence constraint satisfaction.** The pattern:
1. Process equality constraints to build equivalence classes.
2. Check inequality constraints against class membership.

Applicable to:
- Type unification in compilers.
- Social network "friends" / "not-friends" consistency.
- Graph coloring variants.
- Database integrity constraints.

Whenever constraints come in "same as" and "different from" flavors, DSU for same-as + post-check for different-from is the go-to.

----------------------------------------

## Step 8: Complexity

Time: O(number of equations × α(26)) — each union/find is nearly O(1). Total **O(m)** where m = number of equations.
Space: O(26) for the DSU (26 lowercase letters).

Very fast.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) { return parent[x] == x ? x : parent[x] = find(parent[x]); }
    void unite(int a, int b) { parent[find(a)] = find(b); }
};

bool equationsPossible(vector<string>& equations) {
    DSU dsu(26);

    // Pass 1: union all "=="
    for (const string& e : equations) {
        if (e[1] == '=') {
            dsu.unite(e[0] - 'a', e[3] - 'a');
        }
    }

    // Pass 2: check all "!="
    for (const string& e : equations) {
        if (e[1] == '!') {
            if (dsu.find(e[0] - 'a') == dsu.find(e[3] - 'a')) {
                return false;
            }
        }
    }

    return true;
}
```

Tight and clear. The format of each equation is consistent: 4 chars, positions 0 and 3 are variables, position 1 is `=` or `!`.

----------------------------------------

## Step 10: Follow-up Questions

- **Variables with multi-character names.** Use a hashmap `name → int_id` to map variables to DSU indices.
- **Inequality between non-adjacent classes — add a "must differ" constraint.** Graph coloring territory; harder in general.
- **Weighted equality (like a - b = 3).** Extended DSU with offsets; track relative values.
- **Dynamic: equations arrive over time.** DSU handles incremental unions; inequality checks can be done online too.
- **Arithmetic constraints (a + b == c).** Moves beyond simple DSU; use constraint propagation.
- **Why not graph BFS/DFS for equality connectivity?** Works too, but DSU is tighter and more natural for pure equality/union.
