# Interleaving String

**Problem Link:**
https://leetcode.com/problems/interleaving-string/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Nail Down What "Interleave" Means

Given three strings `s1`, `s2`, `s3`, decide whether `s3` can be formed by **interleaving** `s1` and `s2` — keeping each one's relative order intact, but mixing them in any way.

Concretely, imagine two ribbons `s1` and `s2`. You read characters left-to-right off each (never going back). Each step you pick from whichever ribbon you want. Your output is `s3`.

`s1 = "aab"`, `s2 = "axy"`, `s3 = "aaxaby"`.

Is `s3` an interleave? Let me try to reconstruct:
- `s3[0] = 'a'`. Could come from s1[0]=a or s2[0]=a. Try s1[0].
- `s3[1] = 'a'`. s1 now at pos 1 (='a'). s2 still at pos 0 (='a'). Either works. Try s1[1].
- `s3[2] = 'x'`. s1 at 2 (='b'), s2 at 0 (='a'). Neither matches x.

Back up. At s3[1], try s2[0] instead.
- After s3[0] from s1: s1 at 1, s2 at 0.
- s3[1] = 'a' from s2[0]: s1 at 1, s2 at 1.
- s3[2] = 'x' from s2[1]: ok. s1 at 1, s2 at 2.
- s3[3] = 'a' from s1[1]: ok. s1 at 2, s2 at 2.
- s3[4] = 'b' from s1[2]: ok. s1 at 3, s2 at 2.
- s3[5] = 'y' from s2[2]: ok. Done.

So yes, `"aaxaby"` interleaves `"aab"` and `"axy"`.

Notice the exploration: at each step we could pick from either string if the next character matches. That branching is where the interesting algorithmic question lives.

----------------------------------------

## Step 2: A Pre-Check

If `|s1| + |s2| != |s3|`, we can't interleave to form s3 (characters would be missing or extra). Return false immediately. That's the first line of any solution.

From now on assume the length condition holds.

----------------------------------------

## Step 3: Try Brute Force

At each position in `s3`, we either take a character from `s1` (advance its pointer) or from `s2`. At each step, one or two choices are valid (depends on whether the next characters of `s1` and/or `s2` match `s3`'s next character).

Recursive brute force:

```
def canInterleave(i, j):   # i = position in s1, j = position in s2
    if i == len(s1) and j == len(s2): return True
    k = i + j              # position in s3 we're building
    ok = False
    if i < len(s1) and s1[i] == s3[k]:
        ok |= canInterleave(i+1, j)
    if j < len(s2) and s2[j] == s3[k]:
        ok |= canInterleave(i, j+1)
    return ok
```

At worst we branch at every step. 2^(n+m) branches. Exponential.

But the state is just `(i, j)` — there are only `(n+1)(m+1)` distinct states. Many of the recursive calls reach the same state via different paths. That's the DP hook: **memoize on (i, j)**.

----------------------------------------

## Step 4: The Two-Dimensional DP

Let `f(i, j) = True` if `s3[0..i+j)` can be formed by interleaving `s1[0..i)` and `s2[0..j)`.

Transitions:

- `f(i, j)` is true if **either**
  - `s1[i-1] == s3[i+j-1]` and `f(i-1, j)` is true (the last char came from s1), OR
  - `s2[j-1] == s3[i+j-1]` and `f(i, j-1)` is true (the last char came from s2).

Base: `f(0, 0) = True` (all empty strings trivially interleave to empty). `f(0, j)` requires s3[0..j) == s2[0..j). `f(i, 0)` requires s3[0..i) == s1[0..i).

Answer: `f(n, m)` where n = |s1|, m = |s2|.

----------------------------------------

## Step 5: Fill the Table

Example: s1 = "aab", s2 = "axy", s3 = "aaxaby". n=3, m=3.

```
         ""   'a'    'x'    'y'
""       T   s2      s2    s2
         | s3[0]=a | s3[1]=a (match)
'a'      ?    ?      ?      ?
'a'      
'b'
```

Let me fill row by row.

Row 0 (i=0 — only from s2):
- f(0, 0) = T.
- f(0, 1) requires s3[0] == s2[0]. s3[0]='a', s2[0]='a'. T.
- f(0, 2) requires previous T and s3[1] == s2[1]. s3[1]='a', s2[1]='x'. Mismatch. F.
- f(0, 3) = F (prev was F).

Row 1 (i=1, s1[0]='a'):
- f(1, 0): s3[0] == s1[0]? 'a'=='a' yes. Came from f(0,0)=T. So T.
- f(1, 1): options — from s1: s1[0]='a'==s3[1]='a' AND f(0,1)=T → T. Or from s2: s2[0]='a'==s3[1]='a' AND f(1,0)=T → T. Either way T.
- f(1, 2): from s1: s1[0]='a'==s3[2]='x'? no. From s2: s2[1]='x'==s3[2]='x' AND f(1,1)=T → T.
- f(1, 3): from s1: s1[0]='a'==s3[3]='a' AND f(0,3)=F → F. From s2: s2[2]='y'==s3[3]='a'? no. F.

Row 2 (i=2, s1[1]='a'):
- f(2, 0): s3[1] == s1[1]? s3[1]='a'==s1[1]='a' AND f(1,0)=T → T.
- f(2, 1): from s1: s1[1]='a'==s3[2]='x'? no. From s2: s2[0]='a'==s3[2]='x'? no. F.
- f(2, 2): from s1: s1[1]='a'==s3[3]='a' AND f(1,2)=T → T.
- f(2, 3): from s1: s1[1]='a'==s3[4]='b'? no. From s2: s2[2]='y'==s3[4]='b'? no. F.

Row 3 (i=3, s1[2]='b'):
- f(3, 0): s3[2] == s1[2]? s3[2]='x'==s1[2]='b'? no. F.
- f(3, 1): from s1: s1[2]='b'==s3[3]='a'? no. From s2: s2[0]='a'==s3[3]='a' AND f(3,0)=F → F. F.
- f(3, 2): from s1: s1[2]='b'==s3[4]='b' AND f(2,2)=T → T.
- f(3, 3): from s1: s1[2]='b'==s3[5]='y'? no. From s2: s2[2]='y'==s3[5]='y' AND f(3,2)=T → T.

Final: f(3, 3) = T. ✓

Matches our hand exploration — the interleave exists.

----------------------------------------

## Step 6: Why This Is Polynomial

Each cell `(i, j)` has O(1) work (two comparisons, two lookups). Total cells: (n+1)(m+1). Total time: O(n·m). Compared to the O(2^(n+m)) brute force, that's the massive speedup DP buys us here.

The state `(i, j)` captures **everything we need to know about the past** — how many characters of s1 and s2 we've already placed into s3. No other state matters.

----------------------------------------

## Step 7: Name the Shape

This is a **2D DP on two strings** — classic partner problem to LCS, Edit Distance, Regex Matching. The state is "positions into both strings," and transitions consider what happened at the very last character.

Once you've internalized one of these, recognizing the next one becomes quick. The trick is always: "what's the minimal state that determines the future?"

----------------------------------------

## Step 8: Complexity

Time: **O(n · m)**.
Space: **O(n · m)** full table. Optimizable to **O(min(n, m))** by keeping just the previous row (similar to LCS).

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool isInterleave(string s1, string s2, string s3) {
    int n = s1.size(), m = s2.size();
    if (n + m != (int)s3.size()) return false;
    vector<vector<bool>> dp(n + 1, vector<bool>(m + 1, false));
    dp[0][0] = true;
    for (int i = 0; i <= n; ++i) {
        for (int j = 0; j <= m; ++j) {
            if (i == 0 && j == 0) continue;
            bool fromS1 = i > 0 && dp[i - 1][j] && s1[i - 1] == s3[i + j - 1];
            bool fromS2 = j > 0 && dp[i][j - 1] && s2[j - 1] == s3[i + j - 1];
            dp[i][j] = fromS1 || fromS2;
        }
    }
    return dp[n][m];
}
```

Two booleans per cell — one for each "last char came from s1 / s2" option. We OR them together.

----------------------------------------

## Step 10: Follow-up Questions

- **Reconstruct an actual interleave sequence.** Track parent pointers (which direction came from). Walk back from (n, m).
- **Interleave of three strings.** 3D DP, state (i, j, k).
- **Count the number of distinct interleaves (not just yes/no).** Change `bool` to `int`: `dp[i][j] = (fromS1 ? dp[i-1][j] : 0) + (fromS2 ? dp[i][j-1] : 0)`.
- **Interleave with one character swap allowed.** Harder; state grows by one flag.
- **Streaming s3 (characters arrive one at a time).** Maintain a frontier of valid (i, j) pairs; update per new character.
