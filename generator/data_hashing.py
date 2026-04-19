DATA = {
"Maximum Size Subarray Sum Equals K": {
  "concept": "Prefix-sum + hashmap of first occurrence.",
  "intuition": "If prefix[j] - prefix[i] = k, subarray (i,j] sums to k. Track earliest index per prefix value to maximize length.",
  "explanation": "Map m[0] = -1. Iterate with cumulative sum; if (sum-k) in m, update best length = i - m[sum-k]. Record first sum occurrence.",
  "dry_run": "nums=[1,-1,5,-2,3], k=3. Prefix sums 1,0,5,3,6. Check each; best length 4.",
  "approach": "Hashmap of prefix sums.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxSubArrayLen(vector<int>& a, int k) {
    unordered_map<long long,int> m; m[0] = -1;
    long long s = 0; int best = 0;
    for (int i = 0; i < (int)a.size(); ++i) {
        s += a[i];
        if (m.count(s - k)) best = max(best, i - m[s - k]);
        if (!m.count(s)) m[s] = i;
    }
    return best;
}""",
  "followups": "- Count subarrays summing to k.\n- Longest subarray with sum ≤ k.\n- 2D variant."
},

"Longest Consecutive Sequence": {
  "concept": "Hash set + sequence anchor (only start from sequence starts).",
  "intuition": "For each value v, it's the start of a sequence only if v-1 isn't in the set. From such starts, count consecutive values.",
  "explanation": "Insert all into set. For each v with (v-1) absent, extend upward counting v, v+1, ... while present. Track max.",
  "dry_run": "nums=[100,4,200,1,3,2]. Start at 1 → 1,2,3,4 length 4. Start at 100,200 lengths 1 each. Answer=4.",
  "approach": "Hash set, amortized O(n).",
  "complexity": "Time: O(n) average. Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int longestConsecutive(vector<int>& a) {
    unordered_set<int> s(a.begin(), a.end());
    int best = 0;
    for (int v : s) if (!s.count(v - 1)) {
        int u = v, len = 1;
        while (s.count(u + 1)) { u++; len++; }
        best = max(best, len);
    }
    return best;
}""",
  "followups": "- Return the sequence.\n- Consecutive with gap tolerance.\n- Streaming variant."
},

"Longest Substring Without Repeating Characters": {
  "concept": "Sliding window with char→last-index map.",
  "intuition": "Maintain a window [l, r] with distinct chars. When a repeat enters at r, jump l to the position after the previous occurrence of that char.",
  "explanation": "For each r: if last[c]>=l, l=last[c]+1. Update last[c]=r; track max window size.",
  "dry_run": "s='abcabcbb'. Windows 'abc','bca','cab','abc','cb','b' → max length 3.",
  "approach": "Sliding window.",
  "complexity": "Time: O(n). Space: O(Σ).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int lengthOfLongestSubstring(string s) {
    vector<int> last(256, -1);
    int l = 0, best = 0;
    for (int r = 0; r < (int)s.size(); ++r) {
        if (last[s[r]] >= l) l = last[s[r]] + 1;
        last[s[r]] = r;
        best = max(best, r - l + 1);
    }
    return best;
}""",
  "followups": "- At most k distinct chars.\n- With repeating but ≤ k times each.\n- Longest unique substring in a stream."
},

"Max Points on a Line": {
  "concept": "For each point, count slopes of lines to all others using hashmap with normalized slope keys.",
  "intuition": "Pick a pivot; group other points by slope (dy/dx reduced by gcd and signed). Max count + 1 (pivot) is best through that point.",
  "explanation": "For each i, clear map; for each j≠i compute (dx,dy), normalize by gcd and sign (dx first). Increment count[(dx,dy)]. Track global max.",
  "dry_run": "points=[[1,1],[2,2],[3,3]] → 3.",
  "approach": "O(n²) with hashmap.",
  "complexity": "Time: O(n²). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxPoints(vector<vector<int>>& pts) {
    int n = pts.size(), best = 0;
    if (n <= 2) return n;
    for (int i = 0; i < n; ++i) {
        map<pair<int,int>, int> cnt;
        int localMax = 0;
        for (int j = 0; j < n; ++j) if (i != j) {
            int dx = pts[j][0] - pts[i][0], dy = pts[j][1] - pts[i][1];
            int g = __gcd(abs(dx), abs(dy));
            if (g == 0) g = 1;
            dx /= g; dy /= g;
            if (dx < 0) { dx = -dx; dy = -dy; }
            if (dx == 0 && dy < 0) dy = -dy;
            localMax = max(localMax, ++cnt[{dx, dy}]);
        }
        best = max(best, localMax + 1);
    }
    return best;
}""",
  "followups": "- Weighted points (count with weights).\n- 3D lines.\n- Cluster points forming triangles."
},

"Minimum Window Substring": {
  "concept": "Sliding window with required-char count.",
  "intuition": "Expand r until the window contains all chars of t; then contract l to shrink while still valid. Track smallest.",
  "explanation": "Maintain need[] of counts from t and have[]; cnt of matched distinct chars. Expand r incrementing; when matched equals required distinct, try shrinking by incrementing l and updating best.",
  "dry_run": "s='ADOBECODEBANC', t='ABC'. Smallest window 'BANC' length 4.",
  "approach": "Two-pointer sliding window.",
  "complexity": "Time: O(n). Space: O(Σ).",
  "code": """#include <bits/stdc++.h>
using namespace std;
string minWindow(string s, string t) {
    vector<int> need(256, 0);
    for (char c : t) need[c]++;
    int required = 0;
    for (int x : need) if (x) required++;
    vector<int> have(256, 0);
    int matched = 0, l = 0, bestL = 0, bestLen = INT_MAX;
    for (int r = 0; r < (int)s.size(); ++r) {
        char c = s[r]; have[c]++;
        if (need[c] > 0 && have[c] == need[c]) matched++;
        while (matched == required) {
            if (r - l + 1 < bestLen) { bestLen = r - l + 1; bestL = l; }
            char d = s[l++]; have[d]--;
            if (need[d] > 0 && have[d] < need[d]) matched--;
        }
    }
    return bestLen == INT_MAX ? \"\" : s.substr(bestL, bestLen);
}""",
  "followups": "- Window covering at least k chars of each.\n- Minimum window subsequence.\n- Smallest window in a stream."
},

"Palindrome Pairs": {
  "concept": "For each word, check split points and see if the reverse of each half exists.",
  "intuition": "A pair (a,b) forms palindrome iff (a+b) is palindrome. Split word at each index; if left is palindrome and reverse(right) is another word, that other word can be prefix. Symmetric for suffix.",
  "explanation": "Build map word→index. For each word, for each split i [0..|w|]: if left palindrome and reverse(right) in map (and different index) → pair. If i<|w| and right palindrome and reverse(left) in map.",
  "dry_run": "['abcd','dcba','lls','s','sssll']. Pairs like [0,1],[1,0],[3,2],[2,4].",
  "approach": "Hashmap of reversed words.",
  "complexity": "Time: O(N·L²). Space: O(N·L).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool isPal(const string& s, int l, int r) { while (l<r) if (s[l++]!=s[r--]) return false; return true; }
vector<vector<int>> palindromePairs(vector<string>& w) {
    unordered_map<string,int> idx;
    for (int i = 0; i < (int)w.size(); ++i) idx[w[i]] = i;
    vector<vector<int>> res;
    for (int i = 0; i < (int)w.size(); ++i) {
        string s = w[i]; int n = s.size();
        for (int j = 0; j <= n; ++j) {
            if (isPal(s, j, n-1)) {
                string pre(s.begin(), s.begin()+j);
                reverse(pre.begin(), pre.end());
                if (idx.count(pre) && idx[pre] != i) res.push_back({i, idx[pre]});
            }
            if (j && isPal(s, 0, j-1)) {
                string suf(s.begin()+j, s.end());
                reverse(suf.begin(), suf.end());
                if (idx.count(suf) && idx[suf] != i) res.push_back({idx[suf], i});
            }
        }
    }
    return res;
}""",
  "followups": "- Palindrome triples.\n- Using a trie.\n- Large-word streaming."
},

"Subarray Sum Equals K": {
  "concept": "Prefix-sum + hashmap counting.",
  "intuition": "#subarrays ending at i with sum k equals count of previous prefix sums equal to current-k.",
  "explanation": "m[0]=1; run sum; ans += m[sum-k]; ++m[sum].",
  "dry_run": "nums=[1,1,1], k=2. Sums 1,2,3. ans=2.",
  "approach": "Hashmap prefix counts.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int subarraySum(vector<int>& a, int k) {
    unordered_map<int,int> m; m[0] = 1;
    int s = 0, ans = 0;
    for (int x : a) { s += x; ans += m[s - k]; m[s]++; }
    return ans;
}""",
  "followups": "- Longest subarray sum = k.\n- Count subarrays divisible by k.\n- 2D version."
},

"Valid Anagram": {
  "concept": "Character frequency comparison.",
  "intuition": "Two strings are anagrams iff each character occurs the same number of times.",
  "explanation": "Count each char in s; decrement from t; all counts zero → anagram.",
  "dry_run": "s='anagram', t='nagaram' → counts match → true.",
  "approach": "26-element array.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """bool isAnagram(string s, string t) {
    if (s.size() != t.size()) return false;
    int c[26] = {};
    for (char ch : s) c[ch-'a']++;
    for (char ch : t) if (--c[ch-'a'] < 0) return false;
    return true;
}""",
  "followups": "- Anagram groups.\n- Unicode anagrams.\n- Check with streaming chars."
},

"Valid Sudoku": {
  "concept": "Three tracking sets — rows, cols, 3×3 boxes.",
  "intuition": "For each filled cell, record it in row, column, and box; any duplicate means invalid.",
  "explanation": "Use boolean[9][9] for row, col, box. For (i,j): d = board[i][j]-'1'; b = (i/3)*3 + j/3. If any of the three already true → invalid. Else mark them true.",
  "dry_run": "Standard valid Sudoku → true.",
  "approach": "Single pass.",
  "complexity": "Time: O(81). Space: O(81).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool isValidSudoku(vector<vector<char>>& b) {
    bool r[9][9] = {}, c[9][9] = {}, bx[9][9] = {};
    for (int i = 0; i < 9; ++i) for (int j = 0; j < 9; ++j) if (b[i][j] != '.') {
        int d = b[i][j] - '1', k = (i/3)*3 + j/3;
        if (r[i][d] || c[j][d] || bx[k][d]) return false;
        r[i][d] = c[j][d] = bx[k][d] = true;
    }
    return true;
}""",
  "followups": "- Sudoku solver (backtracking).\n- Bigger boards (16x16).\n- Partial validation."
},

"Largest Subarray With 0 Sum": {
  "concept": "Prefix-sum + hashmap of first occurrence.",
  "intuition": "Subarray with zero sum means two prefix sums are equal. Track earliest index of each sum; at later index compute length.",
  "explanation": "m[0]=-1. Running sum; if sum seen earlier update best = i - m[sum]. Else record m[sum]=i.",
  "dry_run": "arr=[15,-2,2,-8,1,7,10,23]. Prefix sums include a repeat → longest subarray length 5.",
  "approach": "Hashmap.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int largestZeroSumSubarray(vector<int>& a) {
    unordered_map<int,int> m; m[0] = -1;
    int s = 0, best = 0;
    for (int i = 0; i < (int)a.size(); ++i) {
        s += a[i];
        if (m.count(s)) best = max(best, i - m[s]);
        else m[s] = i;
    }
    return best;
}""",
  "followups": "- Count zero-sum subarrays.\n- Target-sum variant.\n- 2D zero sum submatrix."
},
}
