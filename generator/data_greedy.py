DATA = {
"Non-overlapping Intervals": {
  "concept": "Greedy by earliest end time — classic activity-selection.",
  "intuition": "To remove the minimum number of intervals, keep as many non-overlapping as possible. Sorting by end time and always picking the interval ending earliest maximizes the count kept.",
  "explanation": "Sort intervals by end. Iterate; if the current start < last end, it overlaps → remove (answer++). Else accept and update last end.",
  "dry_run": "Intervals [[1,2],[2,3],[3,4],[1,3]]. Sort by end: [[1,2],[2,3],[1,3],[3,4]]. Keep [1,2]. [2,3] start>=last end 2 → keep. [1,3] start<3 → remove. [3,4] keep. Removed=1.",
  "approach": "Sort + one scan.",
  "complexity": "Time: O(n log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int eraseOverlapIntervals(vector<vector<int>>& a) {
    sort(a.begin(), a.end(), [](auto& x, auto& y){ return x[1] < y[1]; });
    int cnt = 0, end = INT_MIN;
    for (auto& iv : a) {
        if (iv[0] < end) cnt++;
        else end = iv[1];
    }
    return cnt;
}""",
  "followups": "- Return the kept intervals.\n- Weighted interval scheduling (DP).\n- Minimum number of rooms (sweep line)."
},

"Assign Cookies": {
  "concept": "Greedy two-pointer — pair smallest sufficient cookie with smallest greed.",
  "intuition": "Satisfy the least greedy child with the smallest cookie that fits — saves bigger cookies for greedier children.",
  "explanation": "Sort greed g and cookies s. i=j=0. If s[j]>=g[i], satisfy i++. Always j++. Answer = i.",
  "dry_run": "g=[1,2,3], s=[1,1]. j=0,i=0 match→i=1. j=1,i=1: 1<2 → skip. End. Satisfied=1.",
  "approach": "Two-pointer sweep.",
  "complexity": "Time: O(n log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findContentChildren(vector<int>& g, vector<int>& s) {
    sort(g.begin(),g.end()); sort(s.begin(),s.end());
    int i = 0, j = 0;
    while (i < (int)g.size() && j < (int)s.size()) {
        if (s[j] >= g[i]) i++;
        j++;
    }
    return i;
}""",
  "followups": "- Multiple cookies per child.\n- Cost per cookie — minimize cost to satisfy.\n- Online version with streaming children."
},

"Bulb Switcher": {
  "concept": "Perfect-square observation — bulbs toggled an odd number of times remain on.",
  "intuition": "Bulb i is toggled once per divisor of i. Divisors come in pairs except when i is a perfect square. So only perfect squares end ON. Count perfect squares ≤ n = floor(sqrt(n)).",
  "explanation": "Return floor(sqrt(n)). Based on parity of divisor count.",
  "dry_run": "n=3. sqrt(3)≈1.73 → 1 bulb on (bulb 1).",
  "approach": "Closed form.",
  "complexity": "O(1).",
  "code": """#include <cmath>
int bulbSwitch(int n) { return (int)sqrt((double)n); }""",
  "followups": "- Bulb switcher II (4 operations, pattern recognition).\n- Bulb Switcher III (time until all blue).\n- Generalized toggling with k-divisor rule."
},

"Distribute Candies": {
  "concept": "Return min(unique kinds, n/2).",
  "intuition": "Sister can get at most n/2 candies. Among those, distinct kinds are capped by the number of unique candies overall.",
  "explanation": "Count unique types (set). Answer = min(unique, n/2).",
  "dry_run": "candies=[1,1,2,2,3,3]. unique=3, n/2=3 → 3.",
  "approach": "Single pass + set.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int distributeCandies(vector<int>& c) {
    return min((int)c.size()/2, (int)unordered_set<int>(c.begin(), c.end()).size());
}""",
  "followups": "- Distribute among k siblings.\n- Weighted candies (different value per type).\n- Maximize minimum across siblings."
},

"Maximize Sum After K Negations": {
  "concept": "Always flip the smallest element; parity determines final move.",
  "intuition": "Flipping the smallest maximizes gain if negative; if all positive, remaining flips should target the smallest absolute value. After all flips, parity of remaining k determines if we lose the min.",
  "explanation": "Sort asc. For i from 0 with k>0 and nums[i]<0: nums[i]=-nums[i], k--. Sum all; if remaining k odd, subtract 2*min|value|.",
  "dry_run": "nums=[-2,-3,-1], k=1. Flip -3 → [-2,3,-1] sum=0. But smallest abs=1. No remaining flips. Correction: sort abs→ sum=0.",
  "approach": "Sort + selective negation.",
  "complexity": "Time: O(n log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int largestSumAfterKNegations(vector<int>& a, int k) {
    sort(a.begin(), a.end());
    for (int i = 0; i < (int)a.size() && k > 0 && a[i] < 0; ++i, --k) a[i] = -a[i];
    int s = accumulate(a.begin(), a.end(), 0);
    if (k % 2) s -= 2 * *min_element(a.begin(), a.end());
    return s;
}""",
  "followups": "- What if we cannot flip twice the same element?\n- Maximize sum after k increments/decrements.\n- Multiple test cases with same array."
},

"Maximum Product of Three Numbers": {
  "concept": "Consider either the top 3 or the two smallest (negatives) × the largest.",
  "intuition": "Maximum product uses either three largest positives or two largest-magnitude negatives plus the biggest positive.",
  "explanation": "Sort. Return max(nums[n-1]*nums[n-2]*nums[n-3], nums[0]*nums[1]*nums[n-1]).",
  "dry_run": "nums=[-10,-10,1,3,2]. Sorted: [-10,-10,1,2,3]. top3: 1*2*3=6. neg2*max: -10*-10*3=300 → answer 300.",
  "approach": "Sort + compare two candidates.",
  "complexity": "Time: O(n log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maximumProduct(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size();
    return max(a[n-1]*a[n-2]*a[n-3], a[0]*a[1]*a[n-1]);
}""",
  "followups": "- O(n) single pass tracking top3/bottom2.\n- Product of k numbers — DP or careful greedy.\n- Subarray product maximum."
},

"Minimum Platforms": {
  "concept": "Sweep-line / two-pointer over sorted arrivals and departures.",
  "intuition": "Count maximum simultaneous trains at any time. Sort arrivals and departures separately; advance one pointer at a time to track the count's maximum.",
  "explanation": "i=0 (arr), j=0 (dep), count=0, peak=0. While i<n: if arr[i]<=dep[j] count++, i++; else count--, j++. Track max count.",
  "dry_run": "arr=[900,940,950,1100,1500,1800], dep=[910,1200,1120,1130,1900,2000]. Peak concurrent=3 → answer 3.",
  "approach": "Two pointers on sorted arrays.",
  "complexity": "Time: O(n log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findPlatform(vector<int>& arr, vector<int>& dep) {
    sort(arr.begin(), arr.end()); sort(dep.begin(), dep.end());
    int n = arr.size(), i=0, j=0, cnt=0, peak=0;
    while (i < n) {
        if (arr[i] <= dep[j]) { cnt++; i++; }
        else { cnt--; j++; }
        peak = max(peak, cnt);
    }
    return peak;
}""",
  "followups": "- Return the actual platform assignment per train.\n- Handle equal time-ties (pick policy).\n- Variable platform costs."
},
}
