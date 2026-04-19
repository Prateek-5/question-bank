# Unique Binary Search Trees

**Problem Link:**
https://leetcode.com/problems/unique-binary-search-trees/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Read the Problem, Understand What Varies

Given `n`, count the number of **structurally different** Binary Search Trees you can form using exactly `n` nodes with values `1` through `n`.

Important: "structurally different" means the *shape* matters. Two BSTs storing the same values but in different arrangements count as distinct.

Example for `n = 3`:

```
   1          1           2           3         3
    \          \         / \         /         /
     2          3       1   3       2         1
      \        /                   /           \
       3      2                   1             2
```

That's 5 distinct trees. Let me verify with smaller cases.

----------------------------------------

## Step 2: Count by Hand for Small n

**n = 0:** The "empty tree" — one possibility. Count = 1.

**n = 1:** One node, one tree. Count = 1.

**n = 2:** Values 1, 2. Two possible trees:
- 1 as root, 2 as right child.
- 2 as root, 1 as left child.

Count = 2.

**n = 3:** I drew 5 above. Count = 5.

Let me try **n = 4** carefully. We have values 1, 2, 3, 4. A BST's root can be any of them:

- If root = 1: left subtree has no values (empty), right subtree has {2, 3, 4}. Any valid BST on {2, 3, 4} works, and that's 5 shapes.
- If root = 2: left = {1}, right = {3, 4}. Left has 1 shape, right has 2 shapes. Total: 1 × 2 = 2.
- If root = 3: left = {1, 2}, right = {4}. 2 × 1 = 2.
- If root = 4: left = {1, 2, 3}, right = {}. 5 × 1 = 5.

Total: 5 + 2 + 2 + 5 = **14**.

Counts so far: 1, 1, 2, 5, 14.

----------------------------------------

## Step 3: The Pattern Is Really the Reasoning

Look at what I just did for n = 4. For each possible choice of root, I multiplied the count of shapes of the left subtree by the count of shapes of the right subtree. The sizes of the left and right subtrees are determined by the root choice: if the root is the k-th smallest value, then the left has `k-1` values and the right has `n-k` values.

And here's the key insight: **the count of shapes of a BST depends only on the *number* of values, not on which specific values they are.** A BST on `{2, 3, 4}` has the same number of shapes as a BST on `{1, 2, 3}` — because both are "three sorted values." The values' exact identities don't affect shape count.

So if we let `C(n)` = count of BST shapes on `n` nodes, then choosing the k-th smallest as root:

```
C(n) = Σ (for k from 1 to n) C(k - 1) * C(n - k)
```

Left subtree has `k - 1` values, right subtree has `n - k` values. Independent choices multiply.

Let me re-verify with n = 4:
```
C(4) = C(0)*C(3) + C(1)*C(2) + C(2)*C(1) + C(3)*C(0)
     = 1*5 + 1*2 + 2*1 + 5*1
     = 14.
```

Matches. ✓

----------------------------------------

## Step 4: The Recurrence Gives Us an Algorithm

To compute `C(n)`, we compute `C(0), C(1), ..., C(n)` in order. Each `C(i)` takes O(i) work (sum over choices of root). Total work: O(n²).

Base: `C(0) = 1`, `C(1) = 1`.

```
def countBST(n):
    C = [0] * (n + 1)
    C[0] = 1
    for i in range(1, n + 1):
        for k in range(1, i + 1):
            C[i] += C[k - 1] * C[i - k]
    return C[n]
```

Let me trace for n = 4:
- C[1] = C[0]*C[0] = 1
- C[2] = C[0]*C[1] + C[1]*C[0] = 1 + 1 = 2
- C[3] = C[0]*C[2] + C[1]*C[1] + C[2]*C[0] = 2 + 1 + 2 = 5
- C[4] = C[0]*C[3] + C[1]*C[2] + C[2]*C[1] + C[3]*C[0] = 5 + 2 + 2 + 5 = 14

All match. ✓

----------------------------------------

## Step 5: Name the Numbers

The sequence 1, 1, 2, 5, 14, 42, 132, 429, ... is famous enough to have a name: these are **Catalan numbers**. They appear in many combinatorial contexts — balanced parentheses, ways to triangulate polygons, paths in a grid that don't cross a diagonal, and here, BST shape counts.

There's a closed-form formula: `C_n = C(2n, n) / (n + 1)`. But for interview-scale n (≤ ~20 or so), the O(n²) DP is simpler and avoids big integers.

What's worth noticing: we arrived at Catalan numbers by *asking the right local question* ("what's the root?"), not by pulling the formula out of a hat.

----------------------------------------

## Step 6: Complexity

Time: **O(n²)** for the DP.
Space: **O(n)** for the array.

Using the closed form: **O(n)** time, **O(1)** space — but requires 64-bit integers for moderate n, and big integers beyond n ≈ 30.

----------------------------------------

## Step 7: C++ Implementation

```cpp
int numTrees(int n) {
    vector<long long> C(n + 1, 0);
    C[0] = 1;
    for (int i = 1; i <= n; ++i) {
        for (int k = 1; k <= i; ++k) {
            C[i] += C[k - 1] * C[i - k];
        }
    }
    return (int)C[n];
}
```

Using `long long` because Catalan numbers grow fast — `C(20)` is already over 6 billion. For the standard n ≤ 19, int is fine, but `long long` is safer.

----------------------------------------

## Step 8: Follow-up Questions

- **Generate all unique BSTs, not just count them.** Recursively construct — for each root value, enumerate left subtree shapes and right subtree shapes, combine all pairs. Exponential in n (there are Catalan(n) trees to output).
- **With duplicate values.** The shape-counting argument breaks; you'd need to be careful about which values go in which subtree.
- **Counting BSTs with a specific weight / structural property.** Variant DPs, typically still O(n²) or O(n³).
- **Count the number of sorted permutations that produce the same BST.** Different counting problem.
- **Build a BST that minimizes expected lookup cost given value probabilities.** Optimal BST — another O(n³) DP.
