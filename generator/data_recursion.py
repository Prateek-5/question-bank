DATA = {
"Combination Sum II": {
  "concept": "Backtracking over sorted candidates; skip duplicates.",
  "intuition": "Each candidate used at most once — sort and, during recursion, skip sibling duplicates at the same depth.",
  "explanation": "Sort. dfs(start, remaining, path). For i from start: if i>start and c[i]==c[i-1] skip. If c[i]>remaining break. Recurse with i+1 and remaining-c[i].",
  "dry_run": "c=[10,1,2,7,6,1,5], target=8 → [[1,1,6],[1,2,5],[1,7],[2,6]].",
  "approach": "Sorted backtracking with dup pruning.",
  "complexity": "Time: O(2^n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& c, int s, int t, vector<int>& cur, vector<vector<int>>& res) {
    if (t == 0) { res.push_back(cur); return; }
    for (int i = s; i < (int)c.size(); ++i) {
        if (i > s && c[i] == c[i-1]) continue;
        if (c[i] > t) break;
        cur.push_back(c[i]);
        dfs(c, i+1, t - c[i], cur, res);
        cur.pop_back();
    }
}
vector<vector<int>> combinationSum2(vector<int>& c, int t) {
    sort(c.begin(), c.end());
    vector<vector<int>> res; vector<int> cur;
    dfs(c, 0, t, cur, res);
    return res;
}""",
  "followups": "- With repetition allowed (Combination Sum).\n- Count rather than list.\n- Lexicographic order variants."
},

"N-Queens": {
  "concept": "Backtracking placing one queen per row; track columns and diagonals.",
  "intuition": "Recurse row by row trying each column. Maintain sets for used columns and two diagonal keys (r+c, r-c).",
  "explanation": "cols[col], d1[r+c], d2[r-c+n]. For each row try columns; on success record. Undo on backtrack.",
  "dry_run": "n=4 → 2 distinct solutions.",
  "approach": "Classical backtracking.",
  "complexity": "Time: O(N!). Space: O(N).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<vector<string>> solveNQueens(int n) {
    vector<vector<string>> res;
    vector<string> board(n, string(n, '.'));
    vector<int> cols(n, 0), d1(2*n, 0), d2(2*n, 0);
    function<void(int)> bt = [&](int r) {
        if (r == n) { res.push_back(board); return; }
        for (int c = 0; c < n; ++c) {
            if (cols[c] || d1[r+c] || d2[r-c+n]) continue;
            board[r][c] = 'Q';
            cols[c] = d1[r+c] = d2[r-c+n] = 1;
            bt(r+1);
            board[r][c] = '.';
            cols[c] = d1[r+c] = d2[r-c+n] = 0;
        }
    };
    bt(0);
    return res;
}""",
  "followups": "- N-Queens II (count only).\n- Bitmask optimization.\n- Place k queens in a larger board."
},

"Permutations": {
  "concept": "Backtracking swapping in place.",
  "intuition": "At each recursion level pick an element for the current position by swapping from remaining.",
  "explanation": "bt(s): if s==n record current. For i from s to n-1: swap(s,i); bt(s+1); swap back.",
  "dry_run": "nums=[1,2,3] → 6 perms.",
  "approach": "In-place recursion.",
  "complexity": "Time: O(n!·n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void bt(vector<int>& a, int s, vector<vector<int>>& res) {
    if (s == (int)a.size()) { res.push_back(a); return; }
    for (int i = s; i < (int)a.size(); ++i) { swap(a[s], a[i]); bt(a, s+1, res); swap(a[s], a[i]); }
}
vector<vector<int>> permute(vector<int>& nums) {
    vector<vector<int>> res; bt(nums, 0, res); return res;
}""",
  "followups": "- Permutations II (with duplicates).\n- Next permutation.\n- k-th permutation sequence."
},

"Permutations II": {
  "concept": "Sorted backtracking with used[] skipping sibling duplicates.",
  "intuition": "To avoid duplicate permutations, ensure duplicates are chosen in order by skipping a duplicate whose twin hasn't been used yet at the same level.",
  "explanation": "Sort. dfs with used[]; for i: if used[i] or (i>0 && a[i]==a[i-1] && !used[i-1]) skip.",
  "dry_run": "nums=[1,1,2] → 3 unique perms.",
  "approach": "Sorted dfs with used-array rule.",
  "complexity": "Time: O(n!·n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& a, vector<bool>& used, vector<int>& cur, vector<vector<int>>& res) {
    if (cur.size() == a.size()) { res.push_back(cur); return; }
    for (int i = 0; i < (int)a.size(); ++i) {
        if (used[i]) continue;
        if (i > 0 && a[i] == a[i-1] && !used[i-1]) continue;
        used[i] = true; cur.push_back(a[i]);
        dfs(a, used, cur, res);
        cur.pop_back(); used[i] = false;
    }
}
vector<vector<int>> permuteUnique(vector<int>& a) {
    sort(a.begin(), a.end());
    vector<vector<int>> res; vector<int> cur; vector<bool> used(a.size(), false);
    dfs(a, used, cur, res);
    return res;
}""",
  "followups": "- Lexicographic order.\n- Unrank permutations.\n- Count distinct permutations."
},

"Subsets": {
  "concept": "Backtracking including/excluding each index.",
  "intuition": "Each element is either chosen or not — binary tree of choices yields 2^n subsets.",
  "explanation": "dfs(start): record current. For i from start: push, dfs(i+1), pop.",
  "dry_run": "nums=[1,2,3] → 8 subsets.",
  "approach": "Classical subset backtracking.",
  "complexity": "Time: O(2^n·n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& a, int s, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = s; i < (int)a.size(); ++i) { cur.push_back(a[i]); dfs(a, i+1, cur, res); cur.pop_back(); }
}
vector<vector<int>> subsets(vector<int>& a) { vector<vector<int>> res; vector<int> cur; dfs(a, 0, cur, res); return res; }""",
  "followups": "- Subsets with duplicates (II).\n- Bitmask enumeration.\n- Iterative generation by doubling."
},

"Subsets II": {
  "concept": "Sort + skip duplicates at same depth.",
  "intuition": "After sorting, duplicates appear consecutively. Skip them after the first to avoid duplicate subsets.",
  "explanation": "Sort. dfs(start): record current. For i=start..n-1: if i>start and a[i]==a[i-1] skip. Push, recurse, pop.",
  "dry_run": "nums=[1,2,2] → [[],[1],[1,2],[1,2,2],[2],[2,2]].",
  "approach": "Sorted subset backtracking.",
  "complexity": "Time: O(2^n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& a, int s, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = s; i < (int)a.size(); ++i) {
        if (i > s && a[i] == a[i-1]) continue;
        cur.push_back(a[i]); dfs(a, i+1, cur, res); cur.pop_back();
    }
}
vector<vector<int>> subsetsWithDup(vector<int>& a) {
    sort(a.begin(), a.end());
    vector<vector<int>> res; vector<int> cur;
    dfs(a, 0, cur, res);
    return res;
}""",
  "followups": "- Count distinct subsets.\n- Fixed-size subsets with duplicates.\n- Lexicographic order."
},
}
