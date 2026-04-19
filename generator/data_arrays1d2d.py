DATA = {
"Convert 1D Array Into 2D Array": {
  "concept": "Index mapping i → (i/n, i%n).",
  "intuition": "A 1D array of length m*n maps to an m×n matrix where the k-th element goes to row k/n, col k%n.",
  "explanation": "If original.size() != m*n return []. Otherwise fill mat[i/n][i%n] = original[i].",
  "dry_run": "orig=[1,2,3,4], m=2,n=2 → [[1,2],[3,4]].",
  "approach": "Direct mapping in one pass.",
  "complexity": "Time: O(m*n). Space: O(m*n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> construct2DArray(vector<int>& a, int m, int n) {
    if ((int)a.size() != m*n) return {};
    vector<vector<int>> res(m, vector<int>(n));
    for (int i = 0; i < m*n; ++i) res[i/n][i%n] = a[i];
    return res;
}""",
  "followups": "- Reshape with a different ordering (column-major).\n- Partial fill with padding.\n- Transpose a matrix given as flat array."
},

"Max Chunks To Make Sorted": {
  "concept": "Count indices where running max equals current index.",
  "intuition": "A chunk ending at index i is valid iff max(a[0..i]) == i (since values are a permutation of 0..n-1). Each such index marks the end of an independent chunk.",
  "explanation": "Iterate with running max m. If m == i at index i, increment chunk count.",
  "dry_run": "arr=[1,0,2,3,4]. i=0,m=1 !=0. i=1,m=1==1 → chunk. i=2,m=2==2 → chunk. Similarly 3,4. Total 4 chunks.",
  "approach": "Single scan with running max.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxChunksToSorted(vector<int>& a) {
    int m = 0, cnt = 0;
    for (int i = 0; i < (int)a.size(); ++i) {
        m = max(m, a[i]);
        if (m == i) cnt++;
    }
    return cnt;
}""",
  "followups": "- General version where values aren't a permutation (Max Chunks II).\n- Prove correctness using permutation property.\n- Return the chunk boundaries."
},

"Range Sum Query 2D Immutable": {
  "concept": "2D prefix-sum inclusion-exclusion.",
  "intuition": "Precompute P[i][j] = sum of rectangle (0,0)-(i-1,j-1). Any sub-rectangle sum = P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1].",
  "explanation": "Build (n+1)×(m+1) prefix. Each query in O(1).",
  "dry_run": "matrix=[[3,0,1,4,2],...]. Precompute P. Query (2,1)-(4,3) = P[5][4]-P[2][4]-P[5][1]+P[2][1].",
  "approach": "2D prefix sums.",
  "complexity": "Build O(n*m), query O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class NumMatrix {
    vector<vector<int>> P;
public:
    NumMatrix(vector<vector<int>>& M) {
        int n = M.size(), m = M[0].size();
        P.assign(n+1, vector<int>(m+1, 0));
        for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j)
            P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j];
    }
    int sumRegion(int r1, int c1, int r2, int c2) {
        return P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1];
    }
};""",
  "followups": "- Mutable variant (Binary Indexed Tree 2D).\n- 3D prefix sum.\n- Sum over rotated rectangles."
},

"Richest Customer Wealth": {
  "concept": "Max of row sums.",
  "intuition": "Each customer's wealth is the sum of their row; answer is the maximum row sum.",
  "explanation": "Iterate rows, accumulate sum, track max.",
  "dry_run": "accounts=[[1,2,3],[3,2,1]]. Sums 6 and 6 → 6.",
  "approach": "Straightforward double loop.",
  "complexity": "Time: O(n*m). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maximumWealth(vector<vector<int>>& a) {
    int best = 0;
    for (auto& r : a) best = max(best, accumulate(r.begin(), r.end(), 0));
    return best;
}""",
  "followups": "- Tie-breaking by customer index.\n- Online updates to accounts.\n- Top-k richest customers."
},

"Running Sum of 1D Array": {
  "concept": "In-place prefix sum.",
  "intuition": "The i-th running sum is nums[i] + previous running sum. Build in one pass.",
  "explanation": "For i from 1: nums[i] += nums[i-1]. Return nums.",
  "dry_run": "[1,2,3,4] → [1,3,6,10].",
  "approach": "In-place accumulation.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> runningSum(vector<int>& a) {
    for (int i = 1; i < (int)a.size(); ++i) a[i] += a[i-1];
    return a;
}""",
  "followups": "- 2D running sum.\n- Range sum queries using this.\n- Suffix sum variant."
},

"Search a 2D Matrix II": {
  "concept": "Start from top-right (or bottom-left) and eliminate row or column each step.",
  "intuition": "Rows sorted left-to-right, columns top-to-bottom. From top-right, if value > target move left (column eliminated); if value < target move down (row eliminated).",
  "explanation": "r=0, c=m-1. While r<n and c>=0: if mat[r][c]==target return true; if mat[r][c]>target c--; else r++.",
  "dry_run": "matrix=[[1,4,7],[2,5,8],[3,6,9]], target=5. (0,2)=7>5 → c=1. (0,1)=4<5 → r=1. (1,1)=5 ✓.",
  "approach": "Staircase search.",
  "complexity": "Time: O(n+m). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool searchMatrix(vector<vector<int>>& M, int t) {
    int n = M.size(), m = M[0].size();
    int r = 0, c = m - 1;
    while (r < n && c >= 0) {
        if (M[r][c] == t) return true;
        if (M[r][c] > t) c--;
        else r++;
    }
    return false;
}""",
  "followups": "- Count occurrences of target.\n- Find closest value.\n- If matrix is fully sorted flat, use binary search."
},

"Special Positions in a Binary Matrix": {
  "concept": "Row/column sums; a position is special if its cell is 1 and row sum = col sum = 1.",
  "intuition": "A special 1 must be alone in its row and column. Precompute row/column sums, then count cells that are 1 with both sums equal to 1.",
  "explanation": "Compute rowSum, colSum. For each (i,j) with mat[i][j]==1 and rowSum[i]==1 and colSum[j]==1, increment.",
  "dry_run": "mat=[[1,0,0],[0,0,1],[1,0,0]]. rowSum=[1,1,1], colSum=[2,0,1]. (0,0):rowSum=1,colSum=2 → no. (1,2):1,1 → yes. Special=1.",
  "approach": "Two passes.",
  "complexity": "Time: O(n*m). Space: O(n+m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numSpecial(vector<vector<int>>& M) {
    int n = M.size(), m = M[0].size();
    vector<int> rs(n,0), cs(m,0);
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) { rs[i]+=M[i][j]; cs[j]+=M[i][j]; }
    int cnt = 0;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++)
        if (M[i][j]==1 && rs[i]==1 && cs[j]==1) cnt++;
    return cnt;
}""",
  "followups": "- Special positions in a non-binary matrix.\n- Return the positions.\n- Weighted version with thresholds."
},

"Sum of All Submatrices (Odd Length Subarrays)": {
  "concept": "Contribution counting: each element appears in a known number of odd-length subarrays.",
  "intuition": "For index i in array of size n, total subarrays containing i = (i+1)*(n-i). Out of these, odd-length ones = ((i+1)*(n-i)+1)/2.",
  "explanation": "Sum over i of arr[i] * ((i+1)*(n-i)+1)/2.",
  "dry_run": "arr=[1,4,2,5,3], n=5. For each i compute contribution; total = 58.",
  "approach": "Closed form per-element contribution.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int sumOddLengthSubarrays(vector<int>& a) {
    int n = a.size(), s = 0;
    for (int i = 0; i < n; ++i) {
        int c = ((i + 1) * (n - i) + 1) / 2;
        s += c * a[i];
    }
    return s;
}""",
  "followups": "- Even-length subarrays version.\n- Sum of min/max over all subarrays (monotonic stack).\n- Submatrices of a matrix."
},
}
