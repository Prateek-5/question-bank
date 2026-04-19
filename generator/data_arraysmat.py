DATA = {
"Total Hamming Distance": {
  "concept": "Bitwise counting — per bit, contribution = ones * zeros.",
  "intuition": "Hamming distance sums over pairs. Each bit position contributes count_of_1s * count_of_0s pairs that differ in that bit.",
  "explanation": "For each bit b (0..31): count ones among nums with (num>>b)&1. answer += ones * (n - ones). Sum over all bits.",
  "dry_run": "nums=[4,14,2]. Bit 1: binaries 100,1110,010. ones=2, zeros=1 → 2. Bit 2: ones=1,zeros=2→2. Bit 3: ones=1,zeros=2→2. Total=6.",
  "approach": "32 * n per-bit count.",
  "complexity": "Time: O(32n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int totalHammingDistance(vector<int>& nums) {
    int n = nums.size(), ans = 0;
    for (int b = 0; b < 32; ++b) {
        int ones = 0;
        for (int x : nums) ones += (x >> b) & 1;
        ans += ones * (n - ones);
    }
    return ans;
}""",
  "followups": "- Hamming distance of single pair.\n- Total weighted Hamming distance.\n- Minimum Hamming distance via sorting."
},

"Concatenation of Array": {
  "concept": "Build [nums, nums] concatenated.",
  "intuition": "Just double the array: answer[i]=nums[i%n].",
  "explanation": "Create ans of size 2n; copy nums twice.",
  "dry_run": "nums=[1,2,1]. Answer=[1,2,1,1,2,1].",
  "approach": "Single loop copy.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> getConcatenation(vector<int>& a) {
    int n = a.size();
    vector<int> r(2*n);
    for (int i = 0; i < 2*n; ++i) r[i] = a[i % n];
    return r;
}""",
  "followups": "- Generalize to k concatenations.\n- Reverse-concatenation.\n- Memory-efficient virtual concatenation."
},

"Fizz Buzz": {
  "concept": "Modulo classification.",
  "intuition": "For each i from 1..n print 'FizzBuzz' if i%15==0, 'Fizz' if i%3==0, 'Buzz' if i%5==0, else the number.",
  "explanation": "Straightforward loop with modulo checks.",
  "dry_run": "n=5 → ['1','2','Fizz','4','Buzz'].",
  "approach": "One pass.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<string> fizzBuzz(int n) {
    vector<string> r;
    for (int i = 1; i <= n; ++i) {
        if (i % 15 == 0) r.push_back(\"FizzBuzz\");
        else if (i % 3 == 0) r.push_back(\"Fizz\");
        else if (i % 5 == 0) r.push_back(\"Buzz\");
        else r.push_back(to_string(i));
    }
    return r;
}""",
  "followups": "- Arbitrary divisors and tokens.\n- Multi-threaded FizzBuzz.\n- Reverse order."
},

"Matrix Diagonal Sum": {
  "concept": "Sum primary + secondary diagonal; subtract center if n is odd.",
  "intuition": "Every element on the primary diagonal satisfies i==j. Secondary satisfies i+j==n-1. If n is odd the middle element is counted twice.",
  "explanation": "sum = Σ mat[i][i] + Σ mat[i][n-1-i]. If n is odd, subtract mat[n/2][n/2].",
  "dry_run": "n=3. mat=[[1,2,3],[4,5,6],[7,8,9]]. Primary=1+5+9=15, secondary=3+5+7=15. Sum=30, subtract 5 → 25.",
  "approach": "Single loop.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int diagonalSum(vector<vector<int>>& M) {
    int n = M.size(), s = 0;
    for (int i = 0; i < n; ++i) s += M[i][i] + M[i][n-1-i];
    if (n & 1) s -= M[n/2][n/2];
    return s;
}""",
  "followups": "- Anti-diagonal sum by row+col constant.\n- 3D diagonal.\n- Sum of diagonals at distance k from main."
},

"Maximum Gap": {
  "concept": "Bucket/pigeonhole sort for O(n) max adjacent gap.",
  "intuition": "With n elements in range [min,max], dividing into n-1 buckets of size (max-min)/(n-1) guarantees the max gap lies across two buckets (not within one) by pigeonhole.",
  "explanation": "Find min and max. Bucket width w = ceil((max-min)/(n-1)). For each num compute bucket idx (num-min)/w. Track each bucket's min and max. Max gap = max over consecutive non-empty buckets of (nextMin - prevMax).",
  "dry_run": "nums=[3,6,9,1]. min=1,max=9, n=4, w=3. Buckets: idx 0:{1,3}, idx 1:{6}, idx 2:{9}. Gaps 6-3=3, 9-6=3. Answer=3.",
  "approach": "Bucket sort is O(n). Radix sort also works.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maximumGap(vector<int>& nums) {
    int n = nums.size();
    if (n < 2) return 0;
    int mn = *min_element(nums.begin(), nums.end()),
        mx = *max_element(nums.begin(), nums.end());
    if (mn == mx) return 0;
    int w = max(1, (mx - mn + n - 2) / (n - 1));
    int cnt = (mx - mn) / w + 1;
    vector<int> bmin(cnt, INT_MAX), bmax(cnt, INT_MIN);
    for (int x : nums) {
        int b = (x - mn) / w;
        bmin[b] = min(bmin[b], x);
        bmax[b] = max(bmax[b], x);
    }
    int prev = mn, ans = 0;
    for (int i = 0; i < cnt; ++i) if (bmin[i] != INT_MAX) {
        ans = max(ans, bmin[i] - prev);
        prev = bmax[i];
    }
    return ans;
}""",
  "followups": "- Stream version.\n- Top-k adjacent gaps.\n- 2D extension (nearest-pair)."
},

"Spiral Matrix II": {
  "concept": "Fill n×n matrix by spiraling boundaries inward.",
  "intuition": "Simulate walking in a spiral: right, down, left, up, shrinking boundaries each loop.",
  "explanation": "Maintain top, bottom, left, right bounds. Alternate filling row/column, then shrink the used boundary.",
  "dry_run": "n=3 → [[1,2,3],[8,9,4],[7,6,5]].",
  "approach": "Four-direction simulation.",
  "complexity": "Time: O(n²). Space: O(n²) for output.",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> generateMatrix(int n) {
    vector<vector<int>> m(n, vector<int>(n, 0));
    int t = 0, b = n-1, l = 0, r = n-1, x = 1;
    while (t <= b && l <= r) {
        for (int j = l; j <= r; ++j) m[t][j] = x++;
        t++;
        for (int i = t; i <= b; ++i) m[i][r] = x++;
        r--;
        if (t <= b) for (int j = r; j >= l; --j) m[b][j] = x++;
        b--;
        if (l <= r) for (int i = b; i >= t; --i) m[i][l] = x++;
        l++;
    }
    return m;
}""",
  "followups": "- Spiral Matrix I (read instead of fill).\n- Rectangular spiral.\n- Diagonal/zigzag fill."
},

"Trapping Rain Water": {
  "concept": "Two-pointer sweep comparing left_max and right_max.",
  "intuition": "Water above each bar equals min(max_left, max_right) − height. Moving pointer from the smaller side lets us compute contribution instantly.",
  "explanation": "l=0, r=n-1, ml=mr=0. While l<r: if h[l]<h[r]: if h[l]>=ml ml=h[l] else water+=ml-h[l]; l++. Symmetric for r.",
  "dry_run": "height=[0,1,0,2,1,0,1,3,2,1,2,1]. Answer=6.",
  "approach": "Two pointers O(n).",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int trap(vector<int>& h) {
    int l = 0, r = h.size() - 1, ml = 0, mr = 0, water = 0;
    while (l < r) {
        if (h[l] < h[r]) { ml = max(ml, h[l]); water += ml - h[l]; l++; }
        else { mr = max(mr, h[r]); water += mr - h[r]; r--; }
    }
    return water;
}""",
  "followups": "- Trapping Rain Water II (2D, priority queue BFS).\n- Return the water level for each bar.\n- Variable cell widths."
},

"Maximum Number of Words Found in Sentences": {
  "concept": "Count spaces per sentence, add 1, track max.",
  "intuition": "Word count in a space-separated string = number of spaces + 1.",
  "explanation": "For each sentence count spaces and compare to max.",
  "dry_run": "sentences=['alice a b','hello world']. 2+1=3, 1+1=2. max=3.",
  "approach": "Linear scan.",
  "complexity": "Time: O(total chars). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int mostWordsFound(vector<string>& s) {
    int best = 0;
    for (auto& x : s) {
        int c = 1;
        for (char ch : x) if (ch == ' ') c++;
        best = max(best, c);
    }
    return best;
}""",
  "followups": "- Using stringstream per sentence.\n- Ignore consecutive spaces.\n- Unicode word boundaries."
},

"Maximum Absolute Value Expression": {
  "concept": "Simplify |a|+|b|+|c| over four sign combinations; scan with prefix maxima/minima.",
  "intuition": "|x1-x2|+|y1-y2|+|i-j| simplifies to one of 4 sign combos of (±x ± y ± i). For each combo track max and min; best diff is max-min.",
  "explanation": "For each of 4 sign combos s1, s2 ∈ {+1,-1}: val[i] = s1*x[i] + s2*y[i] + i. answer = max over combos of (max(val) - min(val)).",
  "dry_run": "arr1=[1,2,3,4], arr2=[-1,4,5,6]. Best combo yields 13.",
  "approach": "4 sign combinations × O(n).",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxAbsValExpr(vector<int>& a, vector<int>& b) {
    int n = a.size(), ans = 0;
    for (int sx : {1, -1}) for (int sy : {1, -1}) {
        int mn = INT_MAX, mx = INT_MIN;
        for (int i = 0; i < n; ++i) {
            int v = sx*a[i] + sy*b[i] + i;
            mn = min(mn, v); mx = max(mx, v);
        }
        ans = max(ans, mx - mn);
    }
    return ans;
}""",
  "followups": "- 3D extension.\n- Maximize over pairs with distance constraint.\n- Stream version."
},
}
