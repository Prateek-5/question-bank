DATA = {
"Count of Smaller Numbers After Self": {
  "concept": "Merge sort counting inversions on the right side.",
  "intuition": "During merge, when taking an element from the left half, elements already moved from the right half are smaller and all come after in the original array — count them.",
  "explanation": "Sort indices by value via merge sort; in each merge step, when copying left[i], increment counts[idx[left[i]]] by number of right elements already taken.",
  "dry_run": "nums=[5,2,6,1]. counts=[2,1,1,0].",
  "approach": "Merge sort on indices.",
  "complexity": "Time: O(n log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void merge(vector<int>& idx, vector<int>& tmp, vector<int>& nums, vector<int>& counts, int l, int r) {
    if (l >= r) return;
    int m = (l + r) / 2;
    merge(idx, tmp, nums, counts, l, m);
    merge(idx, tmp, nums, counts, m+1, r);
    int i = l, j = m+1, k = l, right = 0;
    while (i <= m && j <= r) {
        if (nums[idx[i]] <= nums[idx[j]]) { counts[idx[i]] += right; tmp[k++] = idx[i++]; }
        else { right++; tmp[k++] = idx[j++]; }
    }
    while (i <= m) { counts[idx[i]] += right; tmp[k++] = idx[i++]; }
    while (j <= r) tmp[k++] = idx[j++];
    for (int x = l; x <= r; ++x) idx[x] = tmp[x];
}
vector<int> countSmaller(vector<int>& nums) {
    int n = nums.size();
    vector<int> idx(n), tmp(n), counts(n, 0);
    iota(idx.begin(), idx.end(), 0);
    merge(idx, tmp, nums, counts, 0, n-1);
    return counts;
}""",
  "followups": "- Number of inversions total.\n- BIT-based approach.\n- Online queries."
},

"Reverse Pairs": {
  "concept": "Merge sort counting pairs (i,j) with i<j and nums[i] > 2·nums[j].",
  "intuition": "After sorting halves, count valid (i,j) via two-pointer before merging.",
  "explanation": "Mergesort. Before merging, for i in left, advance j in right while nums[i]>2·nums[j]; add (j-m-1) to count. Then merge normally.",
  "dry_run": "nums=[1,3,2,3,1]. Pairs: (3,1),(3,1) from two 3s vs 1s → total 2.",
  "approach": "Merge sort counting phase.",
  "complexity": "Time: O(n log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int mergeCount(vector<int>& a, int l, int r) {
    if (l >= r) return 0;
    int m = (l + r) / 2;
    int cnt = mergeCount(a, l, m) + mergeCount(a, m+1, r);
    int j = m + 1;
    for (int i = l; i <= m; ++i) {
        while (j <= r && a[i] > 2LL * a[j]) j++;
        cnt += j - m - 1;
    }
    inplace_merge(a.begin()+l, a.begin()+m+1, a.begin()+r+1);
    return cnt;
}
int reversePairs(vector<int>& nums) { return mergeCount(nums, 0, nums.size()-1); }""",
  "followups": "- BIT / Fenwick approach.\n- Generalized k·nums[j].\n- Online updates."
},

"Kth Largest Element in an Array (DC)": {
  "concept": "Quickselect partition around a pivot.",
  "intuition": "Hoare's partition places the pivot in its final sorted position; if that's the target rank, done. Else recurse into the correct side.",
  "explanation": "Pick random pivot, partition, compare pivot index with target (n-k). Recurse on the appropriate side.",
  "dry_run": "nums=[3,2,1,5,6,4], k=2 → target idx = 4. Quickselect returns 5.",
  "approach": "Randomized quickselect.",
  "complexity": "Time: O(n) avg, O(n²) worst. Space: O(log n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findKthLargest(vector<int>& nums, int k) {
    int n = nums.size(), target = n - k, lo = 0, hi = n - 1;
    while (true) {
        int pivot = nums[lo + rand() % (hi - lo + 1)];
        int i = lo, j = hi, p = lo;
        while (p <= j) {
            if (nums[p] < pivot) swap(nums[p++], nums[i++]);
            else if (nums[p] > pivot) swap(nums[p], nums[j--]);
            else p++;
        }
        if (target < i) hi = i - 1;
        else if (target > j) lo = j + 1;
        else return pivot;
    }
}""",
  "followups": "- Median-of-medians for O(n) worst.\n- Bucket for bounded ranges.\n- Streaming median."
},

"Minimum Number of Bottles Visible": {
  "concept": "Greedy subtraction of consumed bottles based on exchange ratio.",
  "intuition": "Each exchange reduces total bottles; the minimum visible at end is (initial - fully consumed). Iteratively exchange until fewer than needed remain.",
  "explanation": "total = numBottles. empty = numBottles. While empty >= numExchange: new = empty / numExchange; total += new; empty = new + empty % numExchange.",
  "dry_run": "numBottles=9, numExchange=3. Drink 9. Exchange 9/3=3 → drink 3. Exchange 3/3=1 → drink 1. Total=13.",
  "approach": "Iterative exchange loop.",
  "complexity": "Time: O(log). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numWaterBottles(int nB, int nE) {
    int total = nB, empty = nB;
    while (empty >= nE) {
        int got = empty / nE;
        total += got;
        empty = got + empty % nE;
    }
    return total;
}""",
  "followups": "- Upper bound formula (nB + (nB-1)/(nE-1)).\n- Multi-currency exchange.\n- Rate-limited exchanges."
},

"Open the Lock": {
  "concept": "BFS over states (4-digit combinations).",
  "intuition": "Each dial state has 8 neighbors (each wheel +1 or -1). BFS from '0000' avoiding deadends, stopping at target.",
  "explanation": "Queue initial '0000'. Generate 8 neighbors per state; skip visited/deadend. Levels = minimum moves.",
  "dry_run": "deadends=['0201','0101','0102','1212','2002'], target='0202'. BFS yields 6.",
  "approach": "BFS on 10000 states.",
  "complexity": "Time: O(10000). Space: O(10000).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int openLock(vector<string>& dead, string target) {
    unordered_set<string> blocked(dead.begin(), dead.end());
    if (blocked.count(\"0000\")) return -1;
    if (target == \"0000\") return 0;
    queue<pair<string,int>> q; q.push({\"0000\", 0});
    blocked.insert(\"0000\");
    while (!q.empty()) {
        auto [s, d] = q.front(); q.pop();
        for (int i = 0; i < 4; ++i) for (int dd : {-1, 1}) {
            string t = s;
            t[i] = ((t[i] - '0' + dd + 10) % 10) + '0';
            if (blocked.count(t)) continue;
            if (t == target) return d + 1;
            blocked.insert(t);
            q.push({t, d + 1});
        }
    }
    return -1;
}""",
  "followups": "- Bi-directional BFS for speed.\n- Weighted moves.\n- N-dial variant."
},

"Sort Colors": {
  "concept": "Dutch National Flag — three-way partition.",
  "intuition": "Partition array into <1, ==1, >1 using three pointers lo, mid, hi. Swap nums[mid] with nums[lo] or nums[hi] depending on value.",
  "explanation": "lo=0, mid=0, hi=n-1. While mid<=hi: if nums[mid]==0 swap(lo,mid), lo++,mid++; ==1 mid++; ==2 swap(mid,hi), hi--.",
  "dry_run": "nums=[2,0,2,1,1,0] → [0,0,1,1,2,2].",
  "approach": "Three-pointer partition.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void sortColors(vector<int>& a) {
    int lo = 0, mid = 0, hi = a.size() - 1;
    while (mid <= hi) {
        if (a[mid] == 0) swap(a[lo++], a[mid++]);
        else if (a[mid] == 1) mid++;
        else swap(a[mid], a[hi--]);
    }
}""",
  "followups": "- k colors (k-way partition).\n- Stable partition.\n- Sort 0s/1s only."
},
}
