DATA = {
"Minimum Cost to Connect Ropes": {
  "concept": "Min-heap (priority queue) — repeatedly combine the two smallest elements to minimize total cost.",
  "intuition": "Connecting two ropes costs the sum of their lengths. To minimize total cost, we always want the smallest ropes combined first so their lengths contribute to fewer future sums. This is exactly the Huffman-coding greedy idea: always merge the two smallest.",
  "explanation": "Push all rope lengths into a min-heap. Repeatedly pop the two smallest, sum them, add the sum to a running cost, and push the sum back. Stop when only one rope remains. Each merge's cost equals the sum of the two smallest currently available, which is provably optimal by an exchange argument.",
  "dry_run": "Ropes = [4, 3, 2, 6]. Heap = [2,3,4,6]. Pop 2 and 3, cost = 5, push 5 → heap [4,5,6]. Pop 4 and 5, cost += 9 = 14, push 9 → heap [6,9]. Pop 6 and 9, cost += 15 = 29. Answer = 29.",
  "approach": "Greedy with a min-heap. At each step pick the two minimums (O(log n) per op). The total cost accumulates as you build a Huffman-like binary tree of merges.",
  "complexity": "Time: O(n log n) — n pushes and n pops each O(log n). Space: O(n) for the heap.",
  "code": """#include <bits/stdc++.h>
using namespace std;

long long minCost(vector<int>& ropes) {
    priority_queue<long long, vector<long long>, greater<long long>> pq;
    for (int x : ropes) pq.push(x);
    long long cost = 0;
    while (pq.size() > 1) {
        long long a = pq.top(); pq.pop();
        long long b = pq.top(); pq.pop();
        cost += a + b;
        pq.push(a + b);
    }
    return cost;
}""",
  "followups": "- What if we wanted the *maximum* cost instead? Use a max-heap.\n- How would you do this with a k-way merge cost function?\n- Can you reduce space using an already-sorted input?"
},

"Find K Pairs with Smallest Sums": {
  "concept": "Min-heap over pair indices — BFS-like expansion from the smallest sum.",
  "intuition": "Sorted arrays nums1 and nums2 mean the smallest possible sum is nums1[0] + nums2[0]. The next smallest comes from expanding either the first-array or second-array index. Treat it like a shortest-path expansion in a grid of sums.",
  "explanation": "Push (nums1[0]+nums2[0], 0, 0) into a min-heap. Pop the smallest pair, record it, and push its neighbors (i+1, j) and (i, j+1). Use a visited set to avoid duplicates. Stop when we have k pairs or the heap is empty. This explores sums in non-decreasing order.",
  "dry_run": "nums1 = [1,7,11], nums2 = [2,4,6], k = 3. Heap: (3,0,0). Pop (1,2). Push (5,1,0),(7,0,1). Pop (5,1,0) → (7,2). Push (9,2,0),(11,1,1). Pop (7,0,1) → (1,4). Result = [[1,2],[7,2],[1,4]].",
  "approach": "Start at corner (0,0), grow the frontier via a min-heap of sums. Mark visited cells. This yields the k smallest sums efficiently without enumerating all n*m pairs.",
  "complexity": "Time: O(k log k). Space: O(k) for heap and visited set.",
  "code": """#include <bits/stdc++.h>
using namespace std;

vector<vector<int>> kSmallestPairs(vector<int>& a, vector<int>& b, int k) {
    using T = tuple<int,int,int>;
    priority_queue<T, vector<T>, greater<T>> pq;
    set<pair<int,int>> seen;
    pq.push({a[0]+b[0], 0, 0});
    seen.insert({0,0});
    vector<vector<int>> res;
    while (k-- && !pq.empty()) {
        auto [s, i, j] = pq.top(); pq.pop();
        res.push_back({a[i], b[j]});
        if (i+1 < (int)a.size() && !seen.count({i+1,j})) {
            pq.push({a[i+1]+b[j], i+1, j}); seen.insert({i+1,j});
        }
        if (j+1 < (int)b.size() && !seen.count({i,j+1})) {
            pq.push({a[i]+b[j+1], i, j+1}); seen.insert({i,j+1});
        }
    }
    return res;
}""",
  "followups": "- Generalize to k sorted arrays (Merge k Sorted Lists).\n- What if arrays are not sorted? Pre-sort first — O(n log n + k log k).\n- Solve the k-th smallest sum (return only one value)."
},

"Find Median from Data Stream": {
  "concept": "Two heaps: max-heap for lower half, min-heap for upper half.",
  "intuition": "The median is the middle of a sorted stream. Maintain two halves — the smaller half (max-heap on top) and the larger half (min-heap on top). Balance sizes so the median is either the top of the larger heap or the average of both tops.",
  "explanation": "On add: push into max-heap, then move its top into the min-heap (to keep ordering). If min-heap grows larger, move its top back to max-heap. This keeps max-heap size ≥ min-heap size by at most 1. Median is max-heap top (odd total) or average of both tops (even total).",
  "dry_run": "Add 1 → lo=[1], hi=[]; median=1. Add 2 → lo=[1], hi=[2]; median=1.5. Add 3 → lo=[2,1], hi=[3]; median=2. Add 4 → lo=[2,1], hi=[3,4]; median=2.5.",
  "approach": "Use std::priority_queue (max-heap by default) and one with greater<> (min-heap). Rebalance after every insert. O(log n) insert, O(1) query.",
  "complexity": "Time: O(log n) per add, O(1) per median. Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;

class MedianFinder {
    priority_queue<int> lo; // max-heap
    priority_queue<int, vector<int>, greater<int>> hi; // min-heap
public:
    void addNum(int x) {
        lo.push(x);
        hi.push(lo.top()); lo.pop();
        if (hi.size() > lo.size()) { lo.push(hi.top()); hi.pop(); }
    }
    double findMedian() {
        if (lo.size() > hi.size()) return lo.top();
        return (lo.top() + hi.top()) / 2.0;
    }
};""",
  "followups": "- What if the stream contains only integers in [0,100]? Use a bucket/count array.\n- What if 99% of values are in [0,100] but some are outside?\n- Support removeNum(x) — use multisets or lazy deletion."
},

"K Closest Points to Origin": {
  "concept": "Max-heap of size k keyed by squared distance — keeps k smallest.",
  "intuition": "We want the k points nearest to the origin. A max-heap of size k acts as a filter: if a new point has smaller distance than the heap top, it replaces it. After processing, the heap holds the k closest.",
  "explanation": "For each point, compute d² = x²+y² (avoid sqrt to keep integers). Push into a max-heap. If size exceeds k, pop the largest. After the loop, the heap contains the k closest. Alternatively, use nth_element / quickselect for O(n) average.",
  "dry_run": "points = [[1,3],[-2,2]], k=1. d² = 10 and 8. Heap after insert: [10]. Next push 8, size>1, pop 10 → heap [8]. Result: point with d²=8 → [-2,2].",
  "approach": "Heap of size k with custom comparator by distance. Pop when size > k. Output the heap contents.",
  "complexity": "Time: O(n log k). Space: O(k).",
  "code": """#include <bits/stdc++.h>
using namespace std;

vector<vector<int>> kClosest(vector<vector<int>>& points, int k) {
    auto cmp = [](auto& a, auto& b){
        return a[0]*a[0]+a[1]*a[1] < b[0]*b[0]+b[1]*b[1];
    };
    priority_queue<vector<int>, vector<vector<int>>, decltype(cmp)> pq(cmp);
    for (auto& p : points) {
        pq.push(p);
        if ((int)pq.size() > k) pq.pop();
    }
    vector<vector<int>> res;
    while (!pq.empty()) { res.push_back(pq.top()); pq.pop(); }
    return res;
}""",
  "followups": "- Solve in O(n) average using Quickselect.\n- Solve when points stream in one by one.\n- Support weighted distances (e.g., Manhattan)."
},

"Kth Smallest Element in Sorted Matrix": {
  "concept": "Min-heap BFS from top-left; or binary search on value range.",
  "intuition": "Rows and columns are sorted. The smallest element is at (0,0); the next smallest is among (0,1) or (1,0). A min-heap expands the frontier in non-decreasing order — the k-th pop is the answer.",
  "explanation": "Push (matrix[0][0], 0, 0) into a min-heap. Repeatedly pop the smallest and push its right and down neighbors, marking visited. After k-1 pops, the top is the answer. An alternative O(n log(max-min)) approach binary-searches the value range and counts how many are ≤ mid per row.",
  "dry_run": "matrix=[[1,5,9],[10,11,13],[12,13,15]], k=8. Heap order pops: 1,5,9,10,11,12,13,13. 8th pop = 13.",
  "approach": "Heap + visited set — simple and O(k log k). For large matrices prefer binary search on value.",
  "complexity": "Heap: O(k log k). Binary search: O(n log(max-min)).",
  "code": """#include <bits/stdc++.h>
using namespace std;

int kthSmallest(vector<vector<int>>& mat, int k) {
    int n = mat.size();
    using T = tuple<int,int,int>;
    priority_queue<T, vector<T>, greater<T>> pq;
    vector<vector<int>> seen(n, vector<int>(n, 0));
    pq.push({mat[0][0], 0, 0}); seen[0][0] = 1;
    while (--k) {
        auto [v, r, c] = pq.top(); pq.pop();
        if (r+1 < n && !seen[r+1][c]) { pq.push({mat[r+1][c], r+1, c}); seen[r+1][c]=1; }
        if (c+1 < n && !seen[r][c+1]) { pq.push({mat[r][c+1], r, c+1}); seen[r][c+1]=1; }
    }
    return get<0>(pq.top());
}""",
  "followups": "- Solve in O(n) per query using binary search on value.\n- Handle dynamic updates (row/col sorted, but values mutate).\n- Generalize to k-way sorted streams."
},

"Last Stone Weight": {
  "concept": "Max-heap — repeatedly smash the two largest stones.",
  "intuition": "Each round we need the two largest stones. A max-heap answers this in O(log n). The remaining difference is pushed back. Repeat until ≤1 stone.",
  "explanation": "Push all stones into a max-heap. Pop top two (y ≥ x). If y != x, push y − x. Continue until fewer than two stones remain. Return 0 if empty, else the top.",
  "dry_run": "stones=[2,7,4,1,8,1]. Heap top order: 8,7 → push 1. Heap=[4,2,1,1,1]. Pop 4,2 → push 2 → [2,1,1,1]. Pop 2,1 → push 1 → [1,1,1]. Pop 1,1 → nothing → [1]. Answer=1.",
  "approach": "Greedy with a max-heap. Each iteration is O(log n). Correct because the optimal strategy is fixed — always smash the two largest.",
  "complexity": "Time: O(n log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;

int lastStoneWeight(vector<int>& stones) {
    priority_queue<int> pq(stones.begin(), stones.end());
    while (pq.size() > 1) {
        int y = pq.top(); pq.pop();
        int x = pq.top(); pq.pop();
        if (y != x) pq.push(y - x);
    }
    return pq.empty() ? 0 : pq.top();
}""",
  "followups": "- Last Stone Weight II — can we split into two subsets with minimal difference? (DP/subset-sum.)\n- What if smashing allows partial destruction?\n- Stream version: stones arrive online."
},

"Merge K Sorted Lists": {
  "concept": "Min-heap over the heads of each list.",
  "intuition": "To merge k sorted lists, we need the overall minimum repeatedly. A min-heap of the current heads gives that in O(log k). Each pop advances one list and pushes its next node.",
  "explanation": "Insert the first node of each non-empty list into a min-heap keyed by value. Pop the smallest, append to the output tail, and if it has a next pointer push that into the heap. Continue until the heap is empty.",
  "dry_run": "Lists: [1,4,5],[1,3,4],[2,6]. Heap heads: 1,1,2. Pop 1 (push 4). Pop 1 (push 3). Pop 2 (push 6). Heap: 3,4,4,5,6. Continue → merged: 1,1,2,3,4,4,5,6.",
  "approach": "Divide-and-conquer merge pairs (O(N log k)) or use a priority queue (same complexity).",
  "complexity": "Time: O(N log k). Space: O(k).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct ListNode { int val; ListNode* next; ListNode(int x): val(x), next(nullptr) {} };

ListNode* mergeKLists(vector<ListNode*>& lists) {
    auto cmp = [](ListNode* a, ListNode* b){ return a->val > b->val; };
    priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);
    for (auto* h : lists) if (h) pq.push(h);
    ListNode dummy(0); ListNode* tail = &dummy;
    while (!pq.empty()) {
        auto* n = pq.top(); pq.pop();
        tail->next = n; tail = n;
        if (n->next) pq.push(n->next);
    }
    return dummy.next;
}""",
  "followups": "- Pairwise merge using divide and conquer.\n- External merge-sort (disk-based k-way).\n- Stream-based merge with bounded memory."
},

"Top K Frequent Elements": {
  "concept": "Frequency map + min-heap of size k (or bucket sort by frequency).",
  "intuition": "We want the k most frequent values. Count frequencies, then keep only the top k. A min-heap of size k filters efficiently, or buckets indexed by frequency give O(n).",
  "explanation": "Build a hash map {value: count}. Push (count, value) into a min-heap; pop when size > k. Final heap holds top-k. Bucket approach: create n+1 buckets; place each value into buckets[count]; scan from high to low and collect k.",
  "dry_run": "nums=[1,1,1,2,2,3], k=2. Counts: {1:3,2:2,3:1}. Heap filter: push 1(3),2(2),3(1), pop smallest (3,1). Remaining heap {2:2,1:3}. Answer: [1,2].",
  "approach": "Bucket sort by frequency for O(n), or heap for O(n log k).",
  "complexity": "Heap: O(n log k). Bucket: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;

vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int,int> cnt;
    for (int x : nums) cnt[x]++;
    using P = pair<int,int>; // {count, value}
    priority_queue<P, vector<P>, greater<P>> pq;
    for (auto& [v, c] : cnt) {
        pq.push({c, v});
        if ((int)pq.size() > k) pq.pop();
    }
    vector<int> res;
    while (!pq.empty()) { res.push_back(pq.top().second); pq.pop(); }
    return res;
}""",
  "followups": "- Return the top-k least frequent.\n- Stream version with updates.\n- Tie-breaking by lexicographic order."
},

"Kth Largest Element in an Array": {
  "concept": "Min-heap of size k, or Quickselect.",
  "intuition": "Keep the k largest seen so far in a min-heap. The smallest among them (heap top) is the k-th largest overall after processing all elements.",
  "explanation": "Iterate numbers, push into a min-heap, and pop when size > k. Final heap top is the answer. Quickselect partitions around a pivot and recurses into the half containing the k-th index for O(n) average.",
  "dry_run": "nums=[3,2,1,5,6,4], k=2. Heap: 3, [2,3], [1,2,3] (pop 1) → [2,3], push 5 → pop 2 → [3,5], push 6 → pop 3 → [5,6], push 4 (size=3>2) pop 4 → [5,6]. Top=5.",
  "approach": "Heap is simple and stable. Quickselect is faster on average but has O(n²) worst case unless randomized.",
  "complexity": "Heap: O(n log k). Quickselect: O(n) avg.",
  "code": """#include <bits/stdc++.h>
using namespace std;

int findKthLargest(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> pq;
    for (int x : nums) {
        pq.push(x);
        if ((int)pq.size() > k) pq.pop();
    }
    return pq.top();
}""",
  "followups": "- Implement via Quickselect.\n- Find the k-th smallest instead.\n- Stream version with online updates."
},

"Kth Largest Element in a Stream": {
  "concept": "Bounded min-heap of size k maintained across add calls.",
  "intuition": "For any incoming value, we only care about keeping track of the k largest seen so far. A min-heap of size k where the top is the k-th largest is perfect and each add is O(log k).",
  "explanation": "Initialize: push all initial values, pop while size > k. For add(x): push x, pop if size > k, return top. This maintains invariant that heap contains the top-k values and its top is the k-th largest.",
  "dry_run": "k=3, nums=[4,5,8,2]. Heap=[4,5,8]. add(3): push → [3,4,5,8], pop → [4,5,8], return 4. add(5): push → [4,5,5,8], pop → [5,5,8], return 5.",
  "approach": "Min-heap of fixed size k. Only one heap needed.",
  "complexity": "Init: O(n log k). Per add: O(log k). Space: O(k).",
  "code": """#include <bits/stdc++.h>
using namespace std;

class KthLargest {
    priority_queue<int, vector<int>, greater<int>> pq;
    int k;
public:
    KthLargest(int k, vector<int>& nums): k(k) {
        for (int x : nums) add(x);
    }
    int add(int x) {
        pq.push(x);
        if ((int)pq.size() > k) pq.pop();
        return pq.top();
    }
};""",
  "followups": "- What if k changes over time?\n- Support delete operations.\n- Return the top-k list on demand."
},

"Find K Closest Elements": {
  "concept": "Binary search for the left boundary of a k-length window around x.",
  "intuition": "Array is sorted. We need the window of size k whose elements are closest to x. Binary search finds the left index lo such that arr[lo..lo+k-1] is optimal — by comparing |arr[mid] - x| vs |arr[mid+k] - x|.",
  "explanation": "Maintain lo=0, hi=n-k. While lo < hi, let mid=(lo+hi)/2. If x - arr[mid] > arr[mid+k] - x, lo=mid+1 (the right element is closer so shift right), else hi=mid. End: window [lo..lo+k-1].",
  "dry_run": "arr=[1,2,3,4,5], k=4, x=3. lo=0, hi=1. mid=0. x-arr[0]=2, arr[4]-x=2. 2>2? no → hi=0. Loop ends. Window = arr[0..3] = [1,2,3,4].",
  "approach": "Binary search on left boundary in O(log(n-k)). Much faster than heap O(n log k).",
  "complexity": "Time: O(log(n-k) + k). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;

vector<int> findClosestElements(vector<int>& arr, int k, int x) {
    int lo = 0, hi = arr.size() - k;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (x - arr[mid] > arr[mid + k] - x) lo = mid + 1;
        else hi = mid;
    }
    return vector<int>(arr.begin()+lo, arr.begin()+lo+k);
}""",
  "followups": "- If array is unsorted, sort first or use a max-heap by |a - x|.\n- What if there are duplicates? Behavior unchanged.\n- Solve with two pointers shrinking from both ends."
},
}
