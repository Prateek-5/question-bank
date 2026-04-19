# Assign Cookies

**Problem Link:**
https://leetcode.com/problems/assign-cookies/

**Topic:**
Greedy

----------------------------------------

## Step 1: Setup

You have children with "greed factors" `g` and cookies with "sizes" `s`. Each child i wants a cookie of size at least `g[i]`.

You can give **at most one cookie** to each child, and **each cookie can only be given to one child**.

Return the **maximum number of children** you can content.

Example: `g = [1, 2, 3]`, `s = [1, 1]`.
- Child 0 (greed 1) can use cookie 0 or 1 (size 1 each).
- Child 1 (greed 2) needs size ≥ 2. No cookie qualifies.
- Child 2 (greed 3) needs ≥ 3. None.

Best: content child 0 with one cookie. Return 1.

Example: `g = [1, 2]`, `s = [1, 2, 3]`.
- Child 0 (greed 1): any cookie. Give cookie size 1.
- Child 1 (greed 2): needs size ≥ 2. Give cookie size 2.

Both children content. Return 2.

----------------------------------------

## Step 2: Greedy Strategy

The natural move: match the **least greedy child** with the **smallest sufficient cookie**. Save bigger cookies for greedier children who might actually need them.

To implement:
1. Sort `g` (greed) ascending.
2. Sort `s` (cookie sizes) ascending.
3. Two pointers: `i` over children (starting at 0), `j` over cookies (0).
4. For each cookie, if it satisfies the current child, assign it (advance both pointers). Else, try the next bigger cookie.

```
sort(g); sort(s)
i = 0, j = 0
while i < len(g) and j < len(s):
    if s[j] >= g[i]:
        i += 1   # child satisfied
    j += 1       # always move to the next cookie
return i
```

Each cookie is either assigned or skipped. Each child is assigned at most once.

----------------------------------------

## Step 3: Why Greedy Works — Exchange Argument

**Claim:** the greedy "smallest-cookie-for-smallest-greed" assignment maximizes contented children.

**Proof sketch:** suppose an optimal solution differs from greedy. Find the first position where they diverge: greedy gives child c the smallest sufficient cookie; optimal gives c a larger one (or leaves c unassigned).

Swap optimal's assignment to match greedy's at this position. This swap doesn't reduce the total content count: at most, it changes which specific cookies are assigned, but the number of satisfied children is preserved or improved (because we're using a smaller cookie, freeing larger ones for greedier kids).

Repeating this argument shows greedy matches the optimal count. ✓

This is the standard exchange argument for greedy correctness.

----------------------------------------

## Step 4: Trace on Both Examples

**Example 1:** `g = [1, 2, 3]`, `s = [1, 1]`.

Sorted: g = [1, 2, 3], s = [1, 1].

```
i=0, j=0: s[0]=1 >= g[0]=1. Assign. i=1. j=1.
i=1, j=1: s[1]=1 >= g[1]=2? No. j=2.
j=2: out of range. Exit.
```

Return i = 1. ✓

**Example 2:** `g = [1, 2]`, `s = [1, 2, 3]`.

Sorted: g = [1, 2], s = [1, 2, 3].

```
i=0, j=0: s[0]=1 >= g[0]=1. Assign. i=1, j=1.
i=1, j=1: s[1]=2 >= g[1]=2. Assign. i=2, j=2.
i=2: out of range. Exit.
```

Return i = 2. ✓

----------------------------------------

## Step 5: Name It

**Greedy matching with two-pointer sweep.** The pattern:
1. Sort both sides.
2. Pair greedily from smallest to largest.

Same structure as:
- Minimum Number of Platforms (arrival vs departure sorting).
- Best Meeting Point.
- Partition Labels.
- Matching customers to products.

Whenever "match from each list, minimize/maximize some count" and sorting both sides makes the assignment natural, this is the template.

----------------------------------------

## Step 6: Complexity

Time: **O(n log n + m log m)** for sorts; O(n + m) for the two-pointer sweep. Total O((n + m) log (n + m)).
Space: O(1) beyond sort overhead.

----------------------------------------

## Step 7: C++ Implementation

```cpp
int findContentChildren(vector<int>& g, vector<int>& s) {
    sort(g.begin(), g.end());
    sort(s.begin(), s.end());
    int i = 0, j = 0;
    while (i < (int)g.size() && j < (int)s.size()) {
        if (s[j] >= g[i]) {
            i++;   // child satisfied
        }
        j++;   // always move to next cookie
    }
    return i;
}
```

Eight lines of real logic. `i` is both the counter of content children and the index of the current unsatisfied child.

----------------------------------------

## Step 8: Follow-up Questions

- **Each child can receive multiple cookies.** Different problem — sum cookies until greed satisfied. Still greedy, but more involved.
- **Cookies have value; maximize total value of assigned cookies.** Bipartite matching with weights — more complex.
- **Children can be "partially" satisfied.** Problem needs a new definition.
- **Dynamic: children and cookies arrive over time.** Online algorithm; heap-based greedy may work.
- **Minimize unused cookies instead of maximize content kids.** Related but different objective.
- **Implementation without sorting.** If greed factors and cookie sizes are bounded small integers, bucket sort gives O(n + range).
