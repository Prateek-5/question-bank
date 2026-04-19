DATA = {
"Generate Parentheses": {
  "concept": "Backtracking on open/close counts.",
  "intuition": "Build string character by character; only append '(' if opens<n, only append ')' if closes<opens. Guarantees validity.",
  "explanation": "dfs(s, open, close): if s.length==2n record. If open<n: dfs with '('. If close<open: dfs with ')'.",
  "dry_run": "n=3 → ['((()))','(()())','(())()','()(())','()()()'].",
  "approach": "DFS with count constraints.",
  "complexity": "Time: O(Catalan(n)). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void dfs(int n, int o, int c, string& s, vector<string>& res) {
    if ((int)s.size() == 2*n) { res.push_back(s); return; }
    if (o < n) { s += '('; dfs(n, o+1, c, s, res); s.pop_back(); }
    if (c < o) { s += ')'; dfs(n, o, c+1, s, res); s.pop_back(); }
}
vector<string> generateParenthesis(int n) { vector<string> res; string s; dfs(n, 0, 0, s, res); return res; }""",
  "followups": "- Count only (Catalan numbers).\n- Multiple bracket types.\n- Lexicographic generation."
},

"Gray Code": {
  "concept": "Reflect-and-prefix construction.",
  "intuition": "A Gray code of n bits is the (n-1)-bit code followed by its reverse with MSB set.",
  "explanation": "Start with [0,1]. For each bit from 1 to n-1: duplicate list in reverse, OR top bit (1<<i) onto the new half.",
  "dry_run": "n=2: start [0,1]. Reflect → [0,1,1,0]. OR with 2 on new half → [0,1,3,2].",
  "approach": "Iterative reflection.",
  "complexity": "Time: O(2^n). Space: O(2^n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> grayCode(int n) {
    vector<int> r = {0};
    for (int i = 0; i < n; ++i) {
        int sz = r.size();
        for (int j = sz - 1; j >= 0; --j) r.push_back(r[j] | (1 << i));
    }
    return r;
}""",
  "followups": "- Direct formula: i ^ (i>>1).\n- Gray code for non-powers-of-two.\n- Balanced Gray code."
},

"Palindrome Partitioning": {
  "concept": "Backtracking with palindrome check on each prefix.",
  "intuition": "For each cut point, if the prefix is a palindrome, recurse on the suffix. Collect all decompositions.",
  "explanation": "dfs(start): if start==n record current. For end=start..n-1: if s.substr(start, end-start+1) palindrome, push, recurse with end+1, pop.",
  "dry_run": "s='aab' → [['a','a','b'],['aa','b']].",
  "approach": "DFS with palindrome check.",
  "complexity": "Time: O(2^n·n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool pal(const string& s, int l, int r) { while (l<r) if (s[l++]!=s[r--]) return false; return true; }
void dfs(const string& s, int i, vector<string>& cur, vector<vector<string>>& res) {
    if (i == (int)s.size()) { res.push_back(cur); return; }
    for (int j = i; j < (int)s.size(); ++j) if (pal(s, i, j)) {
        cur.push_back(s.substr(i, j - i + 1));
        dfs(s, j + 1, cur, res);
        cur.pop_back();
    }
}
vector<vector<string>> partition(string s) { vector<vector<string>> res; vector<string> cur; dfs(s, 0, cur, res); return res; }""",
  "followups": "- Minimum cuts (DP).\n- Count distinct palindromic partitions.\n- Palindromic substring DP preprocessing."
},

"Sudoku Solver": {
  "concept": "Backtracking with row/col/box masks.",
  "intuition": "Fill empty cells one at a time. For each, try digits 1–9; check validity with masks; recurse.",
  "explanation": "Maintain rowMask[9], colMask[9], boxMask[9] of used digits. DFS over empty cells trying 1–9 where masks allow.",
  "dry_run": "Standard 9x9 fills left-to-right, top-down.",
  "approach": "Backtracking with bitmasks.",
  "complexity": "Exponential worst; fast with masking.",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool solve(vector<vector<char>>& b, int r, int c, int rm[9], int cm[9], int bm[9]) {
    if (r == 9) return true;
    if (c == 9) return solve(b, r+1, 0, rm, cm, bm);
    if (b[r][c] != '.') return solve(b, r, c+1, rm, cm, bm);
    int bi = (r/3)*3 + c/3;
    for (int d = 0; d < 9; ++d) {
        int bit = 1 << d;
        if ((rm[r] | cm[c] | bm[bi]) & bit) continue;
        b[r][c] = '1' + d;
        rm[r] |= bit; cm[c] |= bit; bm[bi] |= bit;
        if (solve(b, r, c+1, rm, cm, bm)) return true;
        b[r][c] = '.';
        rm[r] &= ~bit; cm[c] &= ~bit; bm[bi] &= ~bit;
    }
    return false;
}
void solveSudoku(vector<vector<char>>& b) {
    int rm[9] = {}, cm[9] = {}, bm[9] = {};
    for (int i = 0; i < 9; ++i) for (int j = 0; j < 9; ++j) if (b[i][j] != '.') {
        int d = b[i][j] - '1', bi = (i/3)*3 + j/3;
        rm[i] |= 1<<d; cm[j] |= 1<<d; bm[bi] |= 1<<d;
    }
    solve(b, 0, 0, rm, cm, bm);
}""",
  "followups": "- Count all solutions.\n- Difficulty estimation via solve steps.\n- 16×16 Sudoku."
},
}
