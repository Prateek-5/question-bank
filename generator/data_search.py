DATA = {
"Capacity To Ship Packages Within D Days": {
  "concept": "Binary search on answer — minimum ship capacity.",
  "intuition": "Capacity monotonic: if capacity C works, any C' > C also works. Binary search capacity in [max(weights), sum(weights)].",
  "explanation": "Check function: greedy fill day by day; if load + w > cap, start new day. Feasible iff days used <= D.",
  "dry_run": "weights=[1,2,3,4,5,6,7,8,9,10], D=5. Answer 15 (binary search between 10 and 55).",
  "approach": "Binary search + greedy feasibility.",
  "complexity": "Time: O(n log(sum)). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int shipWithinDays(vector<int>& w, int D) {
    int lo = *max_element(w.begin(), w.end()), hi = accumulate(w.begin(), w.end(), 0);
    auto feasible = [&](int cap) {
        int days = 1, load = 0;
        for (int x : w) {
            if (load + x > cap) { days++; load = 0; }
            load += x;
        }
        return days <= D;
    };
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (feasible(m)) hi = m; else lo = m + 1;
    }
    return lo;
}""",
  "followups": "- Fixed capacity, find min days.\n- Variable daily capacities.\n- Koko Eating Bananas / Split Array Largest Sum."
},

"Find Peak Element": {
  "concept": "Binary search using neighbor comparison.",
  "intuition": "An element is a peak iff greater than both neighbors. If nums[m] < nums[m+1], a peak exists in [m+1, n-1]; else in [0, m].",
  "explanation": "lo=0, hi=n-1. While lo<hi: m=(lo+hi)/2. If nums[m] < nums[m+1] lo=m+1 else hi=m. Return lo.",
  "dry_run": "nums=[1,2,3,1]. m=1:2<3 → lo=2. m=2: 3>1 → hi=2. Return 2.",
  "approach": "Binary search O(log n).",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findPeakElement(vector<int>& a) {
    int lo = 0, hi = a.size() - 1;
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (a[m] < a[m+1]) lo = m + 1;
        else hi = m;
    }
    return lo;
}""",
  "followups": "- Peak in 2D matrix.\n- Multiple peaks (return all).\n- Bitonic array peak."
},

"Magnetic Force Between Two Balls": {
  "concept": "Binary search on minimum distance.",
  "intuition": "Monotonic: if gap g is feasible (can place m balls with pairwise distance ≥ g), any smaller g is feasible. Binary search the largest feasible g.",
  "explanation": "Sort positions. Feasibility(g): greedy place balls; start with first, then next whose position ≥ last placed + g. Count placed; feasible if >= m.",
  "dry_run": "position=[1,2,3,4,7], m=3. Search in [1, max diff]. g=3 feasible (1,4,7). g=4 not. Answer=3.",
  "approach": "Sort + binary search + greedy.",
  "complexity": "Time: O(n log range). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxDistance(vector<int>& p, int m) {
    sort(p.begin(), p.end());
    int lo = 1, hi = p.back() - p.front();
    auto ok = [&](int g) {
        int cnt = 1, last = p[0];
        for (int i = 1; i < (int)p.size(); ++i)
            if (p[i] - last >= g) { cnt++; last = p[i]; }
        return cnt >= m;
    };
    while (lo < hi) {
        int md = (lo + hi + 1) / 2;
        if (ok(md)) lo = md; else hi = md - 1;
    }
    return lo;
}""",
  "followups": "- Minimum distance when balls can repel.\n- Variable ball sizes.\n- Maximize sum of min-distances."
},

"Search in Rotated Sorted Array": {
  "concept": "Binary search with rotation detection.",
  "intuition": "At each midpoint, one half is sorted. Check which half is sorted and whether target lies in it; discard the other half.",
  "explanation": "lo=0, hi=n-1. Loop: m=(lo+hi)/2. If a[m]==target return m. If a[lo]<=a[m] (left sorted): if a[lo]<=target<a[m] hi=m-1 else lo=m+1. Else right sorted: if a[m]<target<=a[hi] lo=m+1 else hi=m-1.",
  "dry_run": "nums=[4,5,6,7,0,1,2], target=0. m=3:7≠0, left sorted [4..7], 0 not in it → lo=4. m=5:1≠0, left sorted [0..1], 0 in it → hi=4. m=4: 0 found.",
  "approach": "Modified binary search.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int search(vector<int>& a, int t) {
    int lo = 0, hi = a.size() - 1;
    while (lo <= hi) {
        int m = (lo + hi) / 2;
        if (a[m] == t) return m;
        if (a[lo] <= a[m]) {
            if (a[lo] <= t && t < a[m]) hi = m - 1;
            else lo = m + 1;
        } else {
            if (a[m] < t && t <= a[hi]) lo = m + 1;
            else hi = m - 1;
        }
    }
    return -1;
}""",
  "followups": "- Variant with duplicates (harder).\n- Find min in rotated sorted array.\n- Multiple rotations."
},

"Find First and Last Position of Element in Sorted Array": {
  "concept": "Two binary searches — lower_bound and upper_bound.",
  "intuition": "Lower bound gives first index with value ≥ target, upper bound first index > target. If lower_bound's value matches target, positions are (lb, ub-1).",
  "explanation": "Use std::lower_bound and std::upper_bound on the sorted array.",
  "dry_run": "nums=[5,7,7,8,8,10], target=8. lb=3, ub=5 → [3,4].",
  "approach": "STL binary search helpers.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> searchRange(vector<int>& a, int t) {
    auto lb = lower_bound(a.begin(), a.end(), t);
    auto ub = upper_bound(a.begin(), a.end(), t);
    if (lb == a.end() || *lb != t) return {-1, -1};
    return {(int)(lb - a.begin()), (int)(ub - a.begin() - 1)};
}""",
  "followups": "- Count occurrences (ub-lb).\n- Find n-th occurrence by binary searching index.\n- Works on sorted linked list?"
},

"Search a 2D Matrix": {
  "concept": "Treat matrix as flat sorted array; binary search on n*m length.",
  "intuition": "Rows concatenate into a globally sorted array. Index i maps to (i/m, i%m).",
  "explanation": "Binary search indices [0, n*m-1]; at mid decode (r, c) and compare with target.",
  "dry_run": "Matrix sorted row-wise and first-of-row > last-of-prev-row. target=5 locates via binary search.",
  "approach": "Standard binary search with index mapping.",
  "complexity": "Time: O(log(nm)). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool searchMatrix(vector<vector<int>>& M, int t) {
    int n = M.size(), m = M[0].size();
    int lo = 0, hi = n*m - 1;
    while (lo <= hi) {
        int md = (lo + hi) / 2;
        int v = M[md/m][md%m];
        if (v == t) return true;
        if (v < t) lo = md + 1; else hi = md - 1;
    }
    return false;
}""",
  "followups": "- Variant II (only sorted per row and col).\n- Return position, not boolean.\n- Nearest value query."
},

"Single Element in a Sorted Array": {
  "concept": "Binary search on parity — single element breaks the paired pattern.",
  "intuition": "In a perfectly paired array, element at even i equals next odd i+1. Once the single element is encountered, this pairing shifts.",
  "explanation": "lo=0, hi=n-1. While lo<hi: m=(lo+hi)/2 & ~1 (make even). If a[m]==a[m+1] lo=m+2 else hi=m. Return a[lo].",
  "dry_run": "nums=[1,1,2,3,3,4,4,8,8]. m=4(even),a[4]=3,a[5]=4 ≠ → hi=4. m=2(even),a[2]=2,a[3]=3 ≠ → hi=2. m=0,a[0]=a[1] → lo=2. Answer a[2]=2.",
  "approach": "Binary search using pair parity.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int singleNonDuplicate(vector<int>& a) {
    int lo = 0, hi = a.size() - 1;
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (m % 2) m--;
        if (a[m] == a[m+1]) lo = m + 2;
        else hi = m;
    }
    return a[lo];
}""",
  "followups": "- Two single elements (XOR + bit split).\n- Unsorted variant (XOR).\n- Custom equality function."
},

"Smallest Good Base": {
  "concept": "For each possible base length m, binary search base k such that 1+k+k²+...+k^(m-1) = n.",
  "intuition": "If n has m representation digits of all 1s in base k, then n = (k^m - 1)/(k-1). For small m, solve for k by binary search.",
  "explanation": "For m from log2(n+1) down to 2: binary search k in [2, n^(1/(m-1))]. Evaluate polynomial; if equals n, return k. Default m=1 → k=n-1.",
  "dry_run": "n=13. m=3: binary search k; 1+k+k²=13 → k=3. Return '3'.",
  "approach": "Outer loop on digit count, inner binary search.",
  "complexity": "Time: O(log² n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
string smallestGoodBase(string s) {
    long long n = stoll(s);
    for (int m = 60; m >= 2; --m) {
        long long lo = 2, hi = pow(n, 1.0/(m-1)) + 1;
        while (lo <= hi) {
            long long k = (lo + hi) / 2, sum = 0, p = 1;
            bool over = false;
            for (int i = 0; i < m; ++i) {
                if (p > n) { over = true; break; }
                sum += p;
                if (i < m-1) p *= k;
            }
            if (!over && sum == n) return to_string(k);
            if (over || sum > n) hi = k - 1;
            else lo = k + 1;
        }
    }
    return to_string(n - 1);
}""",
  "followups": "- Largest good base instead.\n- Good base in fixed range of m.\n- Represent n with digits in [0,d]."
},
}
