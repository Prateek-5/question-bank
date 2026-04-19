DATA = {
"Climbing Stairs": {
  "concept": "Fibonacci recurrence f(n) = f(n-1) + f(n-2).",
  "intuition": "To reach step n you come from step n-1 (one step) or n-2 (two steps). Ways combine additively.",
  "explanation": "Rolling variables a=1, b=1; loop n times: c=a+b; a=b; b=c.",
  "dry_run": "n=4: 1,2,3,5 → 5 ways.",
  "approach": "O(n) DP with O(1) space.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """int climbStairs(int n) {
    int a = 1, b = 1;
    for (int i = 2; i <= n; ++i) { int c = a + b; a = b; b = c; }
    return b;
}""",
  "followups": "- k-step climbing (DP over k).\n- Cost at each step (Min Cost Climbing).\n- Matrix exponentiation for large n."
},

"Decode Ways": {
  "concept": "DP over string index — valid one-digit and two-digit decodings.",
  "intuition": "At position i, ways(i) = ways(i+1) if s[i] is valid (1–9) + ways(i+2) if s[i..i+1] is valid (10–26).",
  "explanation": "dp[i] = (s[i]!='0' ? dp[i+1] : 0) + (valid(s[i..i+1]) ? dp[i+2] : 0). Base dp[n]=1.",
  "dry_run": "'226'. dp[3]=1. dp[2]=1 (from 6). dp[1]=dp[2]+dp[3]=2 (2 or 26). dp[0]=dp[1]+dp[2]=3.",
  "approach": "Bottom-up DP.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numDecodings(string s) {
    int n = s.size();
    if (n == 0 || s[0] == '0') return 0;
    int two = 1, one = 1;
    for (int i = 1; i < n; ++i) {
        int cur = 0;
        if (s[i] != '0') cur += one;
        int v = (s[i-1]-'0')*10 + (s[i]-'0');
        if (v >= 10 && v <= 26) cur += two;
        two = one; one = cur;
    }
    return one;
}""",
  "followups": "- Decode Ways II (wildcard '*').\n- Count unique decoded strings.\n- Decoding with a custom alphabet."
},

"Distinct Subsequences": {
  "concept": "DP dp[i][j] = ways to form t[0..j-1] from s[0..i-1].",
  "intuition": "At each (i,j), either skip s[i-1] (dp[i-1][j]) or consume it if s[i-1]==t[j-1] (+ dp[i-1][j-1]).",
  "explanation": "Init dp[i][0]=1. For i,j>0: dp[i][j] = dp[i-1][j] + (s[i-1]==t[j-1] ? dp[i-1][j-1] : 0).",
  "dry_run": "s='rabbbit', t='rabbit'. dp[n][m]=3.",
  "approach": "2D DP; can compress to 1D.",
  "complexity": "Time: O(n·m). Space: O(n·m) or O(m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numDistinct(string s, string t) {
    int n = s.size(), m = t.size();
    vector<unsigned long long> dp(m+1, 0); dp[0] = 1;
    for (int i = 1; i <= n; ++i)
        for (int j = m; j >= 1; --j)
            if (s[i-1] == t[j-1]) dp[j] += dp[j-1];
    return (int)dp[m];
}""",
  "followups": "- Number of distinct supersequences.\n- LCS variant (Edit-distance).\n- Regex subsequences."
},

"Dungeon Game": {
  "concept": "Bottom-up min-HP DP from bottom-right.",
  "intuition": "We need minimum starting HP so the knight never drops to ≤0. Work backward from the princess cell where needed health = max(1, 1 - room_value).",
  "explanation": "dp[i][j] = max(1, min(dp[i+1][j], dp[i][j+1]) - dungeon[i][j]). Base: dp[n-1][m-1] = max(1, 1 - dungeon[n-1][m-1]).",
  "dry_run": "dungeon=[[-2,-3,3],[-5,-10,1],[10,30,-5]]. Answer=7.",
  "approach": "Reverse DP in-place.",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int calculateMinimumHP(vector<vector<int>>& D) {
    int n = D.size(), m = D[0].size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, INT_MAX));
    dp[n][m-1] = dp[n-1][m] = 1;
    for (int i = n-1; i >= 0; --i)
        for (int j = m-1; j >= 0; --j)
            dp[i][j] = max(1, min(dp[i+1][j], dp[i][j+1]) - D[i][j]);
    return dp[0][0];
}""",
  "followups": "- 3D variant.\n- Include power-ups that cap HP.\n- Return the path."
},

"Edit Distance": {
  "concept": "Levenshtein DP: insert/delete/replace transitions.",
  "intuition": "dp[i][j] = minimum edits to convert s[0..i-1] → t[0..j-1]. Choose between matching, inserting, deleting, replacing.",
  "explanation": "Base: dp[0][j]=j, dp[i][0]=i. If chars match: dp[i][j]=dp[i-1][j-1]. Else 1+min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]).",
  "dry_run": "'horse'→'ros'. Answer 3.",
  "approach": "2D DP; 1D rolling possible.",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int minDistance(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));
    for (int i = 0; i <= n; ++i) dp[i][0] = i;
    for (int j = 0; j <= m; ++j) dp[0][j] = j;
    for (int i = 1; i <= n; ++i) for (int j = 1; j <= m; ++j)
        dp[i][j] = s[i-1] == t[j-1] ? dp[i-1][j-1] : 1 + min({dp[i-1][j], dp[i][j-1], dp[i-1][j-1]});
    return dp[n][m];
}""",
  "followups": "- Weighted operations.\n- Print actual edits.\n- Damerau-Levenshtein (transpositions)."
},

"Frog Jump": {
  "concept": "DP with states (position, last-jump); transitions to k-1, k, k+1.",
  "intuition": "Frog at stone i with last jump k can jump to stones i+k-1, i+k, i+k+1. Track reachable (stone, jump size) pairs.",
  "explanation": "Map stone → set of jump sizes that reach it. From each (stone, k), attempt to reach stone+k-1, stone+k, stone+k+1. Check if last stone is reachable.",
  "dry_run": "stones=[0,1,3,5,6,8,12,17]. From 0 with k=0 → 1(k=1). Continue reaching 17.",
  "approach": "Memoization or BFS.",
  "complexity": "Time: O(n²). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool canCross(vector<int>& s) {
    unordered_map<int, unordered_set<int>> d;
    for (int x : s) d[x] = {};
    d[0].insert(0);
    for (int x : s) for (int k : d[x])
        for (int dk : {k-1, k, k+1}) if (dk > 0 && d.count(x+dk)) d[x+dk].insert(dk);
    return !d[s.back()].empty();
}""",
  "followups": "- Minimum number of jumps.\n- Find a valid sequence of stones.\n- Allow negative jumps (back)."
},

"Interleaving String": {
  "concept": "2D DP checking whether s3 can be formed by interleaving s1,s2.",
  "intuition": "dp[i][j] = true if s3[0..i+j-1] is an interleave of s1[0..i-1] and s2[0..j-1]. Transition from using s1[i-1] or s2[j-1].",
  "explanation": "dp[i][j] = (dp[i-1][j] && s1[i-1]==s3[i+j-1]) || (dp[i][j-1] && s2[j-1]==s3[i+j-1]).",
  "dry_run": "s1='aab', s2='axy', s3='aaxaby'. dp[3][3]=true.",
  "approach": "Bottom-up 2D DP.",
  "complexity": "Time: O(n·m). Space: O(n·m) or O(m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool isInterleave(string s1, string s2, string s3) {
    int n = s1.size(), m = s2.size();
    if (n + m != (int)s3.size()) return false;
    vector<vector<bool>> dp(n+1, vector<bool>(m+1, false));
    dp[0][0] = true;
    for (int i = 0; i <= n; ++i) for (int j = 0; j <= m; ++j) {
        if (i > 0 && dp[i-1][j] && s1[i-1] == s3[i+j-1]) dp[i][j] = true;
        if (j > 0 && dp[i][j-1] && s2[j-1] == s3[i+j-1]) dp[i][j] = true;
    }
    return dp[n][m];
}""",
  "followups": "- 3-string interleave.\n- Count of distinct interleavings.\n- With wildcards."
},

"Longest Arithmetic Subsequence": {
  "concept": "DP over (index, common_difference) pairs.",
  "intuition": "For each index j and diff d, dp[j][d] = longest AP ending at j with difference d = dp[i][d]+1 over i<j with a[j]-a[i]=d.",
  "explanation": "Use a map per index. For each (i,j), d=a[j]-a[i]; dp[j][d] = max(dp[j][d], dp[i][d]+1). Track global max.",
  "dry_run": "nums=[9,4,7,2,10]. Longest AP 4,7,10 → length 3.",
  "approach": "O(n²) with hashmap dp.",
  "complexity": "Time: O(n²). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int longestArithSeqLength(vector<int>& a) {
    int n = a.size(), best = 2;
    vector<unordered_map<int,int>> dp(n);
    for (int j = 1; j < n; ++j) for (int i = 0; i < j; ++i) {
        int d = a[j] - a[i];
        dp[j][d] = dp[i].count(d) ? dp[i][d] + 1 : 2;
        best = max(best, dp[j][d]);
    }
    return best;
}""",
  "followups": "- Arithmetic slices count.\n- Geometric subsequence.\n- AP with fixed difference."
},

"Longest Common Subsequence": {
  "concept": "Classic 2D DP over (i,j).",
  "intuition": "dp[i][j] = LCS of s[0..i-1], t[0..j-1]. If chars match extend; else max of skipping one.",
  "explanation": "dp[i][j] = s[i-1]==t[j-1] ? dp[i-1][j-1]+1 : max(dp[i-1][j], dp[i][j-1]).",
  "dry_run": "s='abcde', t='ace' → LCS 'ace' length 3.",
  "approach": "Bottom-up DP.",
  "complexity": "Time: O(n·m). Space: O(n·m) or O(m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int longestCommonSubsequence(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));
    for (int i=1;i<=n;i++) for (int j=1;j<=m;j++)
        dp[i][j] = s[i-1]==t[j-1] ? dp[i-1][j-1]+1 : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][m];
}""",
  "followups": "- Print the LCS.\n- LCS of three strings.\n- Space-optimized to O(m)."
},

"Longest Increasing Subsequence": {
  "concept": "Patience sorting / binary search for O(n log n).",
  "intuition": "Keep tails[i] = smallest possible tail of an LIS of length i+1. For each number, replace the first tail ≥ number via lower_bound — or append if all smaller.",
  "explanation": "For each x in nums: position = lower_bound(tails.begin(),tails.end(),x); if position==end append else replace. Length of tails is LIS length.",
  "dry_run": "nums=[10,9,2,5,3,7,101,18]. tails evolves [10]→[9]→[2]→[2,5]→[2,3]→[2,3,7]→[2,3,7,101]→[2,3,7,18]. LIS=4.",
  "approach": "Patience sorting.",
  "complexity": "Time: O(n log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int lengthOfLIS(vector<int>& nums) {
    vector<int> t;
    for (int x : nums) {
        auto it = lower_bound(t.begin(), t.end(), x);
        if (it == t.end()) t.push_back(x); else *it = x;
    }
    return t.size();
}""",
  "followups": "- Print the LIS.\n- Non-decreasing variant (upper_bound).\n- Weighted LIS."
},

"Longest Palindromic Subsequence": {
  "concept": "LCS of s and reverse(s).",
  "intuition": "A palindromic subsequence of s corresponds to a common subsequence of s and reverse(s).",
  "explanation": "Compute LCS(s, reverse(s)).",
  "dry_run": "'bbbab'. LCS with 'babbb' = 'bbbb' length 4.",
  "approach": "Standard LCS DP.",
  "complexity": "Time: O(n²). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int longestPalindromeSubseq(string s) {
    string t(s.rbegin(), s.rend());
    int n = s.size();
    vector<vector<int>> dp(n+1, vector<int>(n+1, 0));
    for (int i=1;i<=n;i++) for (int j=1;j<=n;j++)
        dp[i][j] = s[i-1]==t[j-1] ? dp[i-1][j-1]+1 : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][n];
}""",
  "followups": "- Print the palindrome.\n- Longest palindromic substring (Manacher).\n- Palindrome partitioning."
},

"Matrix Chain Multiplication": {
  "concept": "Interval DP over splitting index.",
  "intuition": "To multiply chain p[i..j], pick a split k; cost = dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]. Try all splits, take min.",
  "explanation": "Standard interval DP with increasing length.",
  "dry_run": "p=[1,2,3,4]. Optimal 18.",
  "approach": "Bottom-up DP in increasing chain length.",
  "complexity": "Time: O(n³). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int mcm(vector<int>& p) {
    int n = p.size() - 1;
    vector<vector<int>> dp(n+1, vector<int>(n+1, 0));
    for (int len = 2; len <= n; ++len)
        for (int i = 1; i + len - 1 <= n; ++i) {
            int j = i + len - 1;
            dp[i][j] = INT_MAX;
            for (int k = i; k < j; ++k)
                dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + p[i-1]*p[k]*p[j]);
        }
    return dp[1][n];
}""",
  "followups": "- Reconstruct the parenthesization.\n- Optimal BST (similar DP).\n- Egg-drop DP."
},

"Maximal Rectangle": {
  "concept": "Histogram rectangle per row using largest-rectangle-in-histogram.",
  "intuition": "For each row treat consecutive 1s above as histogram bars; apply monotonic stack to find largest rectangle.",
  "explanation": "Maintain heights[j]; for each row update heights (reset on 0). Compute row's largest rectangle; track max.",
  "dry_run": "matrix=[['1','0','1','0','0'],...]. Answer=6.",
  "approach": "DP heights + monotonic stack per row.",
  "complexity": "Time: O(n·m). Space: O(m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int largestRectangleArea(vector<int>& h) {
    h.push_back(0);
    stack<int> st; int best = 0;
    for (int i = 0; i < (int)h.size(); ++i) {
        while (!st.empty() && h[st.top()] > h[i]) {
            int top = st.top(); st.pop();
            int w = st.empty() ? i : i - st.top() - 1;
            best = max(best, h[top] * w);
        }
        st.push(i);
    }
    h.pop_back();
    return best;
}
int maximalRectangle(vector<vector<char>>& M) {
    if (M.empty()) return 0;
    int m = M[0].size(), best = 0;
    vector<int> h(m, 0);
    for (auto& r : M) {
        for (int j = 0; j < m; ++j) h[j] = r[j]=='1' ? h[j]+1 : 0;
        best = max(best, largestRectangleArea(h));
    }
    return best;
}""",
  "followups": "- Maximum square (easier DP).\n- Count maximal rectangles.\n- Sub-rectangle with sum constraint."
},

"Maximum Subarray": {
  "concept": "Kadane's algorithm — running-sum reset.",
  "intuition": "Walk the array tracking current subarray sum; reset to current element whenever the running sum becomes negative.",
  "explanation": "cur=best=nums[0]. For i from 1: cur=max(nums[i], cur+nums[i]); best=max(best,cur).",
  "dry_run": "nums=[-2,1,-3,4,-1,2,1,-5,4] → best=6.",
  "approach": "Linear Kadane.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxSubArray(vector<int>& a) {
    int cur = a[0], best = a[0];
    for (int i = 1; i < (int)a.size(); ++i) { cur = max(a[i], cur + a[i]); best = max(best, cur); }
    return best;
}""",
  "followups": "- Return the actual subarray.\n- Circular subarray maximum.\n- 2D Kadane."
},

"Minimum Path Sum": {
  "concept": "DP from top-left: dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]).",
  "intuition": "At each cell the best path either came from above or from the left — take the cheaper.",
  "explanation": "Iterate rows/cols; handle first row/col separately (only one predecessor).",
  "dry_run": "grid=[[1,3,1],[1,5,1],[4,2,1]] → 7 (1→3→1→1→1).",
  "approach": "Bottom-up in-place.",
  "complexity": "Time: O(n·m). Space: O(1) if in-place.",
  "code": """#include <bits/stdc++.h>
using namespace std;
int minPathSum(vector<vector<int>>& g) {
    int n=g.size(), m=g[0].size();
    for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j) {
        if (i == 0 && j == 0) continue;
        int up = i ? g[i-1][j] : INT_MAX;
        int left = j ? g[i][j-1] : INT_MAX;
        g[i][j] += min(up, left);
    }
    return g[n-1][m-1];
}""",
  "followups": "- Return the path.\n- Allow diagonal moves.\n- K-th smallest path sum."
},

"Unique Binary Search Trees": {
  "concept": "Catalan numbers — dp[n] = Σ dp[i]·dp[n-1-i].",
  "intuition": "With n nodes, pick root i; left subtree has i-1 nodes, right has n-i — independent counts multiplied and summed over all roots.",
  "explanation": "dp[0]=1. For i=1..n: dp[i] = Σ dp[j]·dp[i-1-j] for j=0..i-1.",
  "dry_run": "n=3 → dp[3]=5.",
  "approach": "DP over n.",
  "complexity": "Time: O(n²). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numTrees(int n) {
    vector<int> dp(n+1, 0); dp[0] = 1;
    for (int i = 1; i <= n; ++i) for (int j = 0; j < i; ++j) dp[i] += dp[j] * dp[i-1-j];
    return dp[n];
}""",
  "followups": "- Generate all unique BSTs (Unique BSTs II).\n- Weighted BSTs (optimal BST).\n- Catalan formulas."
},

"Unique Paths": {
  "concept": "Combinations C(m+n-2, m-1) or DP.",
  "intuition": "Every path consists of (m-1) downs and (n-1) rights — total (m+n-2) moves chosen from either.",
  "explanation": "Compute binomial coefficient iteratively to avoid overflow.",
  "dry_run": "m=3,n=7 → C(8,2)=28.",
  "approach": "Iterative nCr.",
  "complexity": "Time: O(min(m,n)). Space: O(1).",
  "code": """int uniquePaths(int m, int n) {
    long long r = 1;
    for (int i = 1; i < m; ++i) r = r * (n - 1 + i) / i;
    return (int)r;
}""",
  "followups": "- With obstacles (Unique Paths II).\n- Paths with k moves.\n- Unique paths in 3D."
},

"Unique Paths II": {
  "concept": "DP over grid with obstacles.",
  "intuition": "dp[i][j] = 0 if obstacle; else sum of dp[i-1][j] and dp[i][j-1].",
  "explanation": "Bottom-up DP; base dp[0][0] = grid[0][0]==0.",
  "dry_run": "grid=[[0,0,0],[0,1,0],[0,0,0]] → 2 paths.",
  "approach": "Standard grid DP.",
  "complexity": "Time: O(n·m). Space: O(m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int uniquePathsWithObstacles(vector<vector<int>>& g) {
    int n=g.size(), m=g[0].size();
    vector<long long> dp(m, 0); dp[0] = g[0][0] ? 0 : 1;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) {
        if (g[i][j]) dp[j] = 0;
        else if (j > 0) dp[j] += dp[j-1];
    }
    return (int)dp[m-1];
}""",
  "followups": "- With weighted obstacles.\n- Minimize obstacles on path.\n- Count paths mod p."
},

"Min Cost Climbing Stairs": {
  "concept": "DP dp[i] = cost[i] + min(dp[i-1], dp[i-2]).",
  "intuition": "Reach top by stepping one or two at a time; minimize the sum of step costs incurred.",
  "explanation": "Iterate; a=b=0 initially (free at start). For each i: c = cost[i] + min(a, b); a = b; b = c. Answer min(a, b) at end.",
  "dry_run": "cost=[10,15,20] → 15.",
  "approach": "Rolling DP.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int minCostClimbingStairs(vector<int>& c) {
    int a = 0, b = 0;
    for (int x : c) { int cur = x + min(a, b); a = b; b = cur; }
    return min(a, b);
}""",
  "followups": "- k steps per move.\n- Stochastic costs (expected).\n- Reach exactly step n."
},

"Numbers at Most N Given Digit Set": {
  "concept": "Digit DP counting valid numbers length-by-length.",
  "intuition": "Any number shorter than n's length is free to choose any digit → d^length. Equal length requires tight comparison of each digit.",
  "explanation": "Let len(n)=L. Add d^k for k in 1..L-1. For k=L, go digit-by-digit: count digits < current strictly then multiply by d^(remaining); continue only if current digit is in set. If finished all digits, +1.",
  "dry_run": "digits=['1','3','5','7'], n=100. Count 1,3,5,7 (len 1); len 2 → 16; total 20.",
  "approach": "Digit DP closed form.",
  "complexity": "Time: O(L²). Space: O(L).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int atMostNGivenDigitSet(vector<string>& d, int n) {
    string s = to_string(n);
    int L = s.size(), D = d.size(), ans = 0;
    for (int k = 1; k < L; ++k) ans += pow(D, k);
    for (int i = 0; i < L; ++i) {
        bool match = false;
        for (auto& x : d) {
            if (x[0] < s[i]) ans += pow(D, L - i - 1);
            else if (x[0] == s[i]) match = true;
        }
        if (!match) return ans;
    }
    return ans + 1;
}""",
  "followups": "- Numbers within [L,R] using digits.\n- Digit set with uses-at-most constraints.\n- Digit DP with memo."
},

"Ones and Zeroes": {
  "concept": "0/1 knapsack over two capacities (0s and 1s).",
  "intuition": "Each string 'costs' its count of 0s and 1s; we maximize count of strings within budgets (m zeros, n ones).",
  "explanation": "dp[i][j] = max strings using at most i zeros and j ones. For each string with z zeros, o ones: dp[i][j] = max(dp[i][j], dp[i-z][j-o]+1) iterating i,j downward.",
  "dry_run": "strs=['10','0001','111001','1','0'], m=5,n=3 → 4.",
  "approach": "2D 0/1 knapsack.",
  "complexity": "Time: O(K·m·n). Space: O(m·n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findMaxForm(vector<string>& strs, int m, int n) {
    vector<vector<int>> dp(m+1, vector<int>(n+1, 0));
    for (auto& s : strs) {
        int z = count(s.begin(), s.end(), '0'), o = s.size() - z;
        for (int i = m; i >= z; --i) for (int j = n; j >= o; --j)
            dp[i][j] = max(dp[i][j], dp[i-z][j-o] + 1);
    }
    return dp[m][n];
}""",
  "followups": "- Minimize number of strings to meet a target.\n- 3D (0,1,2 digits).\n- Unbounded knapsack variant."
},

"Partition Equal Subset Sum": {
  "concept": "0/1 subset-sum DP target = total/2.",
  "intuition": "Can we pick a subset that sums to half the total? If total is odd, impossible; else boolean DP on reachable sums.",
  "explanation": "target = sum/2. dp bitset of size target+1; dp[0]=true. For each num: dp |= dp << num. Return dp[target].",
  "dry_run": "nums=[1,5,11,5]. sum=22, target=11. Reachable includes 11 → true.",
  "approach": "Bitset DP.",
  "complexity": "Time: O(n·target/64). Space: O(target/64).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool canPartition(vector<int>& a) {
    int s = accumulate(a.begin(), a.end(), 0);
    if (s & 1) return false;
    int t = s / 2;
    bitset<10001> dp; dp[0] = 1;
    for (int x : a) dp |= dp << x;
    return dp[t];
}""",
  "followups": "- k-partition into equal sums.\n- Minimum difference between two subsets.\n- Count subsets summing to target."
},

"Regular Expression Matching": {
  "concept": "DP over (i,j) handling '.' and '*'.",
  "intuition": "dp[i][j] = s[0..i-1] matches p[0..j-1]. '.' matches any char; '*' allows zero or more of preceding char.",
  "explanation": "If p[j-1]=='*': dp[i][j] = dp[i][j-2] || (match(s[i-1], p[j-2]) && dp[i-1][j]). Else: dp[i][j] = match && dp[i-1][j-1].",
  "dry_run": "s='aab', p='c*a*b' → true.",
  "approach": "Bottom-up DP.",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool isMatch(string s, string p) {
    int n = s.size(), m = p.size();
    vector<vector<bool>> dp(n+1, vector<bool>(m+1, false));
    dp[0][0] = true;
    for (int j = 1; j <= m; ++j) if (p[j-1] == '*') dp[0][j] = dp[0][j-2];
    auto match = [&](int i, int j){ return p[j-1]=='.' || s[i-1]==p[j-1]; };
    for (int i = 1; i <= n; ++i) for (int j = 1; j <= m; ++j) {
        if (p[j-1] == '*') dp[i][j] = dp[i][j-2] || (match(i, j-1) && dp[i-1][j]);
        else dp[i][j] = match(i, j) && dp[i-1][j-1];
    }
    return dp[n][m];
}""",
  "followups": "- Wildcard matching (?,* simpler).\n- NFA-based general regex.\n- Greedy + backtrack implementation."
},

"Russian Doll Envelopes": {
  "concept": "Sort by width asc, height desc for same width; run LIS on heights.",
  "intuition": "We want a chain where each envelope strictly fits inside the next. Sorting with the twist prevents same-width envelopes from nesting during LIS on heights.",
  "explanation": "Sort envelopes by w asc, h desc (tie-break). Then LIS on h sequence gives the answer.",
  "dry_run": "envelopes=[[5,4],[6,4],[6,7],[2,3]] → sort [[2,3],[5,4],[6,7],[6,4]]. LIS on heights [3,4,7,4]=3.",
  "approach": "Sort + patience-sort LIS.",
  "complexity": "Time: O(n log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxEnvelopes(vector<vector<int>>& e) {
    sort(e.begin(), e.end(), [](auto& x, auto& y){ return x[0]!=y[0] ? x[0]<y[0] : x[1]>y[1]; });
    vector<int> t;
    for (auto& x : e) {
        auto it = lower_bound(t.begin(), t.end(), x[1]);
        if (it == t.end()) t.push_back(x[1]); else *it = x[1];
    }
    return t.size();
}""",
  "followups": "- Allow equality in nesting.\n- 3D boxes.\n- Maximize sum of widths/heights along chain."
},

"Split Array with Same Average": {
  "concept": "Meet-in-the-middle subset-sum with fractional target.",
  "intuition": "Find subset of size k with sum = k * totalSum / n. Search subsets; for large n split in halves to combine.",
  "explanation": "Split nums into two halves. Compute subset sums per size from each half. For each size k, look for (sum_left, sum_right) pair with combined size k and combined sum target.",
  "dry_run": "nums=[1,2,3,4,5,6,7,8]. Target check across sizes 1..7.",
  "approach": "Meet-in-the-middle.",
  "complexity": "Time: O(2^(n/2)·n). Space: O(2^(n/2)).",
  "code": """// Full implementation is lengthy. Core idea: enumerate subset sums in halves, check fractional-avg match.
// For n<=30 brute force with memo; else MITM. See LeetCode editorial for complete code.""",
  "followups": "- Approximate average split.\n- k-way average split.\n- Prove NP-hardness in general."
},

"Triangle": {
  "concept": "Bottom-up DP on rows.",
  "intuition": "From the bottom row up, each cell's min path = its value + min of two children below.",
  "explanation": "Initialize dp=last row. For i from n-2 to 0: dp[j] = triangle[i][j] + min(dp[j], dp[j+1]).",
  "dry_run": "triangle=[[2],[3,4],[6,5,7],[4,1,8,3]]. Answer 11.",
  "approach": "O(n²) DP in-place.",
  "complexity": "Time: O(n²). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int minimumTotal(vector<vector<int>>& t) {
    vector<int> dp = t.back();
    for (int i = t.size() - 2; i >= 0; --i)
        for (int j = 0; j <= i; ++j)
            dp[j] = t[i][j] + min(dp[j], dp[j+1]);
    return dp[0];
}""",
  "followups": "- Path itself.\n- Max sum (same recurrence with max).\n- Stochastic weights."
},

"Numbers At Most N Given Digit Set (dup)": {
  "concept": "See 'Numbers at Most N Given Digit Set' above.",
  "intuition": "Duplicate entry.",
  "explanation": "See earlier entry.",
  "dry_run": "See earlier entry.",
  "approach": "Digit DP.",
  "complexity": "See earlier entry.",
  "code": """// See 'Numbers at Most N Given Digit Set' above.""",
  "followups": "- See earlier entry."
},

"Minimum Jumps to Reach Home": {
  "concept": "BFS on (position, direction) with forbidden squares.",
  "intuition": "Bug's state is (pos, lastDir). BFS expands forward b or backward a (only once consecutively). Track visited pairs.",
  "explanation": "Queue (pos, backJust, steps). Forward move: pos+a; if valid push. Backward move: pos-b if backJust==0 and pos-b>=0 and not forbidden. Upper bound pos<=6000 approx.",
  "dry_run": "forbidden=[14,4,18,1,15], a=3,b=15, x=9. BFS finds 3 jumps.",
  "approach": "BFS with (position, last-direction) state.",
  "complexity": "Time: O(bound). Space: O(bound).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int minimumJumps(vector<int>& f, int a, int b, int x) {
    set<int> forb(f.begin(), f.end());
    const int LIM = 6000;
    queue<tuple<int,int,int>> q; q.push({0, 0, 0});
    set<pair<int,int>> seen; seen.insert({0, 0});
    while (!q.empty()) {
        auto [p, back, s] = q.front(); q.pop();
        if (p == x) return s;
        int nf = p + a;
        if (nf <= LIM && !forb.count(nf) && !seen.count({nf, 0})) { seen.insert({nf,0}); q.push({nf,0,s+1}); }
        int nb = p - b;
        if (!back && nb >= 0 && !forb.count(nb) && !seen.count({nb, 1})) { seen.insert({nb,1}); q.push({nb,1,s+1}); }
    }
    return -1;
}""",
  "followups": "- Tighten the limit.\n- Continuous variant.\n- Weighted jumps."
},

"Maximum Height by Stacking Cuboids": {
  "concept": "Sort cuboid dimensions; find LIS-like chain maximizing height.",
  "intuition": "Each cuboid can be rotated; sort its dims so width≤depth≤height. Then sort cuboids and use DP where dp[i] = best stack ending with cuboid i.",
  "explanation": "For each cuboid sort its (a,b,c). Sort cuboids lexicographically. dp[i] = c[i] + max over j<i with a[j]≤a[i], b[j]≤b[i], c[j]≤c[i] of dp[j]. Answer max dp.",
  "dry_run": "cuboids=[[50,45,20],[95,37,53],[45,23,12]] → sort each and chain; answer 190.",
  "approach": "Sort-then-LIS DP.",
  "complexity": "Time: O(n²). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxHeight(vector<vector<int>>& c) {
    for (auto& v : c) sort(v.begin(), v.end());
    sort(c.begin(), c.end());
    int n = c.size(), best = 0;
    vector<int> dp(n);
    for (int i = 0; i < n; ++i) {
        dp[i] = c[i][2];
        for (int j = 0; j < i; ++j)
            if (c[j][0] <= c[i][0] && c[j][1] <= c[i][1] && c[j][2] <= c[i][2])
                dp[i] = max(dp[i], dp[j] + c[i][2]);
        best = max(best, dp[i]);
    }
    return best;
}""",
  "followups": "- Box stacking (3 orientations per box).\n- With weights constraint.\n- Maximize count of stacked cuboids."
},
}
