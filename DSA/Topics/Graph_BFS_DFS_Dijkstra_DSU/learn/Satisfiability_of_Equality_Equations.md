# Satisfiability of Equality Equations — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Satisfiability_of_Equality_Equations.md`](../Satisfiability_of_Equality_Equations.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/satisfiability-of-equality-equations/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/satisfiability-of-equality-equations/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: equality equations create EQUIVALENCE CLASSES (DSU). Inequality equations must connect DIFFERENT classes. Process `==` first, then check `!=` — contradiction = both in same class.**

**Map of this file (9 sections):**

1. Read the problem
2. The equivalence-class reframe
3. Why DSU fits
4. Two-pass order matters
5. Code
6. Trace it
7. Common pitfalls
8. The shape — constraint satisfaction via DSU
9. Self-check

---

## 1. Read the problem

You have a list of equations, each of the form `"a==b"` or `"a!=b"` where each side is a single lowercase letter (a..z). Decide if there's any assignment of integer values to letters that satisfies ALL equations simultaneously.

**Examples:**

- `["a==b", "b!=a"]` → contradiction. **false**.
- `["b==a", "a==b"]` → both say the same. **true**.
- `["a==b", "b==c", "a==c"]` → consistent. **true**.

---

## 2. The equivalence-class reframe

> **Mini-refresher: `==` defines EQUIVALENCE CLASSES.**
>
> All variables connected by `==` chains must have the same value. They form an equivalence class.
>
> Two variables are in the same class iff there's a chain of `==` between them.

After processing all `==`, variables are partitioned into classes. Each class can be assigned any distinct value (e.g., 0, 1, 2, ...).

An `!=` equation is satisfied iff its two sides are in DIFFERENT classes.

---

## 3. Why DSU fits

DSU is literally the equivalence-class data structure:
- `unite(a, b)` declares a and b are in the same class.
- `find(a) == find(b)` checks class membership.

There are only 26 letters → DSU over 26 elements. O(m · α(26)) = essentially O(m).

---

## 4. Two-pass order matters

> **Mini-refresher: process ALL `==` before ANY `!=`.**
>
> If you interleave, an `!=` check might fire BEFORE a later `==` would have merged the classes — false negative.
>
> The fix: PASS 1 unions all equalities (finalizes classes). PASS 2 checks all inequalities against the now-final classes.

```
pass 1: for each "a==b", unite(a, b)
pass 2: for each "a!=b", if find(a) == find(b) → return false
return true
```

---

## 5. Code

**C++:**

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) {
        return parent[x] == x ? x : parent[x] = find(parent[x]);
    }
    void unite(int a, int b) {
        parent[find(a)] = find(b);
    }
};

bool equationsPossible(vector<string>& equations) {
    DSU dsu(26);

    for (const string& e : equations) {
        if (e[1] == '=') dsu.unite(e[0] - 'a', e[3] - 'a');
    }

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

**Python:**

```python
def equationsPossible(equations):
    parent = list(range(26))
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def unite(a, b):
        parent[find(a)] = find(b)

    for e in equations:
        if e[1] == '=':
            unite(ord(e[0]) - ord('a'), ord(e[3]) - ord('a'))
    for e in equations:
        if e[1] == '!':
            if find(ord(e[0]) - ord('a')) == find(ord(e[3]) - ord('a')):
                return False
    return True
```

Complexity: **O(m · α(26)) ≈ O(m)** time, **O(26)** space.

---

## 6. Trace it

**`["a==b", "b!=c", "c==a"]`:**

Letters: a=0, b=1, c=2.

```
Pass 1 (==):
  a==b: unite(0, 1). parent[0]=1.
  c==a: unite(2, 0). find(2)=2, find(0)=1. parent[2]=1.
  Classes: {0, 1, 2}.

Pass 2 (!=):
  b!=c: find(1)=1, find(2)=1. SAME. Return false.  ✓
```

The chain `a==b, c==a` puts all three in one class, contradicting `b!=c`.

**`["a==b", "b==c", "a!=d"]`:**

```
Pass 1: unite(0,1), unite(1,2). Classes: {0,1,2}, {3}.
Pass 2: a!=d → find(0)=class1, find(3)=3. Different. OK.
Return true.  ✓
```

---

## 7. Common pitfalls

1. **Interleaving passes.** Inequality before its merging equality → false negative.
2. **Hardcoding indices for the wrong positions.** The equation format is 4 chars: `[0]` var, `[1]` `=` or `!`, `[2]` `=`, `[3]` var. Easy to confuse.
3. **Treating `==` and `!=` symmetrically (e.g., both as edges).** Only `==` declares same-class; `!=` is a CONSTRAINT, not a class-merger.
4. **Reading more than 26 variables.** The problem restricts to single lowercase letters; DSU of size 26 is enough.
5. **Forgetting that `a!=a` is automatically false.** Implicit case — usually not in inputs, but worth knowing.

---

## 8. The shape — constraint satisfaction via DSU

The pattern: **"same as" + "different from" constraints → DSU + post-check.**

| Problem | Constraints |
|---|---|
| **This problem** | `==` and `!=` |
| Type unification in compilers | equality between type variables |
| Social network "friend"/"enemy" consistency | symmetric pos/neg constraints |
| Database integrity (row equivalence) | equality and disjointness |
| Conditional graph coloring (2-color) | bipartite check |

**Pattern to internalize:**

> "Equality constraints build equivalence classes via DSU. Inequality constraints check membership AFTER all equalities are processed."

---

## 9. Self-check

> **The question to ask next time:**
>
> > **"Are constraints 'same as' or 'different from'? Run two passes: union all `same as`, then check `different from` against classes."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Satisfiability_of_Equality_Equations.md`](../Satisfiability_of_Equality_Equations.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Redundant_Connection.md`](./Redundant_Connection.md), [`Accounts_Merge.md`](./Accounts_Merge.md), [`Most_Stones_Removed_with_Same_Row_or_Column.md`](./Most_Stones_Removed_with_Same_Row_or_Column.md).
  - Coming next: [`Knight_Probability_in_Chessboard.md`](./Knight_Probability_in_Chessboard.md), [`Count_Primes.md`](./Count_Primes.md).
