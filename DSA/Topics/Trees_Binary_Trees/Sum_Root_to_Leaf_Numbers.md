# Sum Root to Leaf Numbers

**Problem Link:**
<a href="https://leetcode.com/problems/sum-root-to-leaf-numbers/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/sum-root-to-leaf-numbers/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What's the Problem?

You have a binary tree where each node holds a digit 0-9. Each root-to-leaf path represents a number formed by concatenating the digits along the path. Return the **sum** of all such root-to-leaf numbers.

Example:
```
    1
   / \
  2   3
```
- Path 1 → 2 forms the number 12.
- Path 1 → 3 forms the number 13.
- Sum = 12 + 13 = **25**.

Bigger example:
```
      4
     / \
    9   0
   / \
  5   1
```
- 4 → 9 → 5: number 495.
- 4 → 9 → 1: number 491.
- 4 → 0: number 40.
- Sum = 495 + 491 + 40 = **1026**.

----------------------------------------

## Step 2: How Does a Digit String Become a Number?

When we see digits `4, 9, 5` and want the number 495, we're doing:
- Start: 0.
- Add 4: 0 · 10 + 4 = 4.
- Add 9: 4 · 10 + 9 = 49.
- Add 5: 49 · 10 + 5 = 495.

Each new digit is appended by multiplying the running number by 10 and adding the new digit.

This accumulation pattern matters: as we descend a path, we can *carry* the running number into the recursion.

----------------------------------------

## Step 3: Plan a DFS with a Running Number

Visit the tree top-down. At each recursive call, pass the running number built from the path so far.

```
dfs(node, currentNumber):
    if node is null: return 0
    newNumber = currentNumber * 10 + node.val
    if node is a leaf: return newNumber    # we've completed a root-to-leaf number
    return dfs(node.left, newNumber) + dfs(node.right, newNumber)
```

Initial call: `dfs(root, 0)`.

The recursion:
- At a leaf, we've built a complete number — contribute it.
- At an internal node, we haven't reached a leaf yet — continue building via children, sum their results.
- Null nodes contribute 0 (we only count paths ending at leaves).

----------------------------------------

## Step 4: Trace on the Tree

```
      4
     / \
    9   0
   / \
  5   1
```

```
dfs(4, 0):
  newNumber = 0·10 + 4 = 4. Not leaf (has children).
  left = dfs(9, 4):
    newNumber = 4·10 + 9 = 49. Not leaf.
    left = dfs(5, 49):
      newNumber = 49·10 + 5 = 495. Leaf. Return 495.
    right = dfs(1, 49):
      newNumber = 491. Leaf. Return 491.
    return 495 + 491 = 986.
  right = dfs(0, 4):
    newNumber = 40. Leaf. Return 40.
  return 986 + 40 = 1026.
```

Sum = 1026. ✓

Notice the running number grows as we descend, and at leaves we commit it into the total.

----------------------------------------

## Step 5: Why Pass "currentNumber" Rather Than Building at Leaves

An alternative: collect each path as a list of digits, then at each leaf convert the list into a number and sum.

But that uses extra memory for the list and extra work for the conversion. Passing `currentNumber` as an integer during recursion lets us do the conversion incrementally — no list needed.

Also, passing by value (integers are small) means no accidental mutation across siblings. Each recursive call independently carries its own copy of `currentNumber`. Clean.

----------------------------------------

## Step 6: Why This Works — The Recursive Invariant

**Invariant:** when we enter `dfs(node, currentNumber)`, `currentNumber` is the number formed by digits along the path from the root to `node`'s parent (before including `node`).

Immediately we update: `newNumber = currentNumber · 10 + node.val`. This includes `node`'s digit.

At a leaf, `newNumber` is the full root-to-leaf number for this path — we return it.
At an internal node, recurse on children with `newNumber` as their carried-in number. They extend it further.

Summing results across the tree gives the total of all root-to-leaf numbers.

----------------------------------------

## Step 7: Name the Technique

This is **DFS with an accumulator parameter**. The accumulator — `currentNumber` here — carries context from ancestors to descendants. Same pattern appears in:
- Path Sum (accumulator: remaining target or running sum).
- Binary Tree Paths (accumulator: list of values on path).
- Count binary substrings (accumulator: running counts).

When a tree problem asks about values or properties along paths, carrying an accumulator through recursion is almost always the cleanest approach.

----------------------------------------

## Step 8: Edge Cases

- **Empty tree (root null):** no paths, sum = 0. Our `dfs(null, 0)` returns 0. ✓
- **Single node:** root is itself a leaf. dfs computes newNumber = 0·10 + root.val = root.val. Leaf check triggers. Return root.val. ✓
- **Long paths / large numbers.** If paths are deep (say 9 levels), numbers can reach 10-digit range. Integer overflow isn't usually a problem because paths are typically ≤ 20 digits, but use `long long` if depth can be enormous.

----------------------------------------

## Step 9: Complexity

Time: every node visited once, O(1) work per node. **O(n)**.
Space: **O(h)** for the recursion stack, where h is the tree's height.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int sumNumbers(TreeNode* root, int cur = 0) {
    if (!root) return 0;
    cur = cur * 10 + root->val;
    if (!root->left && !root->right) return cur;   // leaf — commit
    return sumNumbers(root->left, cur) + sumNumbers(root->right, cur);
}
```

Elegant — six lines. The default argument `cur = 0` handles the initial call without needing a wrapper.

Alternative: explicit wrapper and helper:

```cpp
int dfs(TreeNode* n, int cur) {
    if (!n) return 0;
    cur = cur * 10 + n->val;
    if (!n->left && !n->right) return cur;
    return dfs(n->left, cur) + dfs(n->right, cur);
}
int sumNumbers(TreeNode* root) { return dfs(root, 0); }
```

Both are correct; use whichever style you prefer.

----------------------------------------

## Step 11: Follow-up Questions

- **Binary digits instead of decimal.** Replace `*10` with `*2`.
- **Return the list of numbers, not just their sum.** Collect at leaves, concatenate going up.
- **Paths can end at any node, not just leaves.** Slightly different — return the sum at every node you visit.
- **Digits larger than 9 (multi-digit nodes).** `*10` no longer works; use `*10^digits_in_node` or concatenate as strings.
- **Return the largest root-to-leaf number.** Replace sum with max.
- **How does iterative BFS/DFS compare?** BFS with (node, cur) pairs is O(n) but uses more memory than DFS.
