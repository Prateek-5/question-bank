DATA = {
"K-diff Pairs in an Array": {
  "concept": "Hashmap frequency count — special-case k=0 for duplicates.",
  "intuition": "Count unique values. For k>0, count pairs (v, v+k) both present. For k=0, count values with frequency ≥ 2.",
  "explanation": "Build count map. If k==0: answer = number of keys with count>=2. Else: for each key v, if cnt contains v+k, answer++.",
  "dry_run": "nums=[3,1,4,1,5], k=2. Unique pairs (1,3),(3,5). Answer=2.",
  "approach": "Single hashmap pass.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findPairs(vector<int>& nums, int k) {
    if (k < 0) return 0;
    unordered_map<int,int> c;
    for (int x : nums) c[x]++;
    int ans = 0;
    for (auto& [v, f] : c) {
        if (k == 0 && f >= 2) ans++;
        if (k > 0 && c.count(v + k)) ans++;
    }
    return ans;
}""",
  "followups": "- Count ordered pairs instead of unique.\n- |diff|=k with two arrays.\n- k-diff triples."
},

"Container With Most Water": {
  "concept": "Two pointers — shrink from the side with smaller height.",
  "intuition": "Area is (r-l)*min(h[l],h[r]). Moving the taller pointer inward can never increase the area since the min height won't grow and width shrinks; so always move the smaller side.",
  "explanation": "l=0, r=n-1. Track max area; while l<r: compute area; if h[l]<h[r] l++ else r--.",
  "dry_run": "h=[1,8,6,2,5,4,8,3,7]. Max area=49 (indices 1..8).",
  "approach": "Two pointers O(n).",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxArea(vector<int>& h) {
    int l = 0, r = h.size() - 1, best = 0;
    while (l < r) {
        best = max(best, (r - l) * min(h[l], h[r]));
        if (h[l] < h[r]) l++; else r--;
    }
    return best;
}""",
  "followups": "- Widths non-uniform between indices.\n- Max area with at most k modifications.\n- 3D container problem."
},

"Trapping Rain Water (TP)": {
  "concept": "Two-pointer variant tracking max on each side; see Arrays topic for full details.",
  "intuition": "Same as 'Trapping Rain Water' — smaller-side pointer accumulates water.",
  "explanation": "See Arrays topic entry for detailed explanation.",
  "dry_run": "See Arrays topic entry.",
  "approach": "Two pointers O(n).",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """// See 'Trapping Rain Water' in Arrays topic.""",
  "followups": "- Same as original; see that entry."
},

"3Sum": {
  "concept": "Sort + fix first + two-pointer on remaining.",
  "intuition": "To find triplets summing to 0, sort, fix i, and two-pointer for j,k such that nums[j]+nums[k] = -nums[i]. Skip duplicates.",
  "explanation": "Sort. For each i: if nums[i]>0 break. Skip duplicate i. j=i+1, k=n-1; while j<k: compare sum; if zero, record and skip duplicates; adjust pointers.",
  "dry_run": "nums=[-1,0,1,2,-1,-4] → sorted [-4,-1,-1,0,1,2]. Triplets: [-1,-1,2],[-1,0,1].",
  "approach": "Sort + two pointers.",
  "complexity": "Time: O(n²). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> threeSum(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size();
    vector<vector<int>> res;
    for (int i = 0; i < n - 2; ++i) {
        if (a[i] > 0) break;
        if (i > 0 && a[i] == a[i-1]) continue;
        int j = i+1, k = n-1;
        while (j < k) {
            int s = a[i] + a[j] + a[k];
            if (s == 0) {
                res.push_back({a[i], a[j], a[k]});
                while (j < k && a[j] == a[j+1]) j++;
                while (j < k && a[k] == a[k-1]) k--;
                j++; k--;
            } else if (s < 0) j++;
            else k--;
        }
    }
    return res;
}""",
  "followups": "- 3Sum Closest.\n- 4Sum with k-sum recursion.\n- 3Sum Smaller."
},

"Two Sum II Input Array Is Sorted": {
  "concept": "Two-pointer sum on a sorted array.",
  "intuition": "If the current sum is too small, move left pointer right to increase; if too big, move right pointer left.",
  "explanation": "l=0, r=n-1. While l<r: s=a[l]+a[r]. If s==target return {l+1,r+1}; if s<target l++ else r--.",
  "dry_run": "a=[2,7,11,15], target=9. l=0,r=3: 17>9→r=2. 13>9→r=1. 9=9 → {1,2}.",
  "approach": "Two pointers O(n).",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> twoSum(vector<int>& a, int t) {
    int l = 0, r = a.size() - 1;
    while (l < r) {
        int s = a[l] + a[r];
        if (s == t) return {l+1, r+1};
        if (s < t) l++; else r--;
    }
    return {};
}""",
  "followups": "- All pairs with given sum.\n- Unsorted variant (hashmap).\n- Two-sum in a BST."
},

"Ugly Number II": {
  "concept": "Three-pointer merge of sequences ×2, ×3, ×5.",
  "intuition": "Every ugly number is 2^a * 3^b * 5^c. Generate in order by merging three ascending sequences: previous ugly numbers multiplied by 2, 3, 5.",
  "explanation": "u[0]=1; maintain pointers i2, i3, i5 into u. Next ugly = min(u[i2]*2, u[i3]*3, u[i5]*5). Advance whichever pointer matched (could be multiple to avoid dup).",
  "dry_run": "u=[1,2,3,4,5,6,8,9,10,12,...].",
  "approach": "Three-pointer DP.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int nthUglyNumber(int n) {
    vector<long long> u(n);
    u[0] = 1;
    int i2=0,i3=0,i5=0;
    for (int i = 1; i < n; ++i) {
        long long v = min({u[i2]*2, u[i3]*3, u[i5]*5});
        u[i] = v;
        if (v == u[i2]*2) i2++;
        if (v == u[i3]*3) i3++;
        if (v == u[i5]*5) i5++;
    }
    return (int)u[n-1];
}""",
  "followups": "- Super Ugly Number with arbitrary prime list.\n- Ugly numbers up to N.\n- k-th ugly number in streaming."
},

"Minimize Maximum Pair Sum in Array": {
  "concept": "Sort; pair smallest with largest, etc.",
  "intuition": "Pairing smallest with largest keeps all pair sums close to the mean, minimizing the maximum.",
  "explanation": "Sort. For i in [0, n/2), compute a[i] + a[n-1-i]; track max.",
  "dry_run": "a=[3,5,2,3]. Sort [2,3,3,5]. Pairs (2+5),(3+3)=7,6. Max=7.",
  "approach": "Sort + linear pairing.",
  "complexity": "Time: O(n log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int minPairSum(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size(), best = 0;
    for (int i = 0; i < n/2; ++i) best = max(best, a[i] + a[n-1-i]);
    return best;
}""",
  "followups": "- Prove optimality via exchange argument.\n- Triplet sum minimization.\n- Weighted pair sums."
},
}
