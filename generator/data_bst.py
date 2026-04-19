DATA = {
"All Elements in Two BSTs": {
  "concept": "In-order traversal produces sorted arrays; merge both sorted lists.",
  "intuition": "In-order traversal of a BST yields keys in sorted order. Do it for both trees to get two sorted lists, then merge them like merge-step of merge sort.",
  "explanation": "Traverse tree1 in-order into v1; tree2 into v2. Use two pointers to merge into a single sorted list.",
  "dry_run": "Tree1 in-order: [1,2,4]; Tree2: [0,3,5]. Merge: [0,1,2,3,4,5].",
  "approach": "Two in-order traversals + linear merge.",
  "complexity": "Time: O(n1+n2). Space: O(n1+n2).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void inorder(TreeNode* r, vector<int>& v) { if (!r) return; inorder(r->left,v); v.push_back(r->val); inorder(r->right,v); }

vector<int> getAllElements(TreeNode* a, TreeNode* b) {
    vector<int> v1, v2, res;
    inorder(a, v1); inorder(b, v2);
    int i=0, j=0;
    while (i < (int)v1.size() && j < (int)v2.size())
        res.push_back(v1[i] <= v2[j] ? v1[i++] : v2[j++]);
    while (i < (int)v1.size()) res.push_back(v1[i++]);
    while (j < (int)v2.size()) res.push_back(v2[j++]);
    return res;
}""",
  "followups": "- Do it with O(h) memory using two iterator stacks.\n- Intersect keys instead of merging.\n- k-th smallest across both BSTs."
},

"Binary Search Tree Iterator": {
  "concept": "Lazy in-order iterator using a stack.",
  "intuition": "An iterator should expose next() in O(1) amortized. Maintain a stack storing the left spine of the current subtree; on next() pop top, then push the left spine of its right child.",
  "explanation": "Init: push left-spine of root. next(): pop node, if it has a right child, push left-spine of the right. hasNext(): stack non-empty.",
  "dry_run": "BST 7,3,15,_,_,9,20. Stack after init: [7,3]. next→3; stack=[7]. next→7, push 15 then 9 → [15,9]. next→9, stack=[15]. next→15, push 20 → [20].",
  "approach": "Amortized O(1) per next with O(h) space.",
  "complexity": "Time: O(1) amortized. Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

class BSTIterator {
    stack<TreeNode*> st;
    void pushLeft(TreeNode* n) { while (n) { st.push(n); n = n->left; } }
public:
    BSTIterator(TreeNode* root) { pushLeft(root); }
    int next() {
        TreeNode* n = st.top(); st.pop();
        pushLeft(n->right);
        return n->val;
    }
    bool hasNext() { return !st.empty(); }
};""",
  "followups": "- prev() operation (requires parent pointers or Morris).\n- Range iterator [lo, hi].\n- Iterator with updates during iteration."
},

"Binary Tree Left Side View": {
  "concept": "BFS level-order, pick first node of each level; or DFS tracking depth.",
  "intuition": "The left view shows the first node visible from the left at each depth — the leftmost node per level.",
  "explanation": "BFS level-by-level: push the first node dequeued per level. DFS approach: pre-order with depth; record node if depth matches result size.",
  "dry_run": "Tree 1,2,3,4,_,_,5. Levels: [1],[2,3],[4,5]. Left view: [1,2,4].",
  "approach": "BFS level size tracking.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<int> leftSideView(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        for (int i = 0; i < sz; ++i) {
            auto* n = q.front(); q.pop();
            if (i == 0) res.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
    }
    return res;
}""",
  "followups": "- Bottom view; top view using column indexing.\n- Right view by picking the last node per level.\n- Boundary traversal."
},

"Binary Tree Right Side View": {
  "concept": "BFS level-order, pick last node of each level.",
  "intuition": "Right view shows the rightmost node at each depth.",
  "explanation": "Level-by-level BFS; in each level push only the last node's value. Alternatively reverse-preorder DFS.",
  "dry_run": "Tree 1,2,3,_,5,_,4. Levels [1],[2,3],[5,4]. Right view: [1,3,4].",
  "approach": "BFS level size.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<int> rightSideView(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        for (int i = 0; i < sz; ++i) {
            auto* n = q.front(); q.pop();
            if (i == sz - 1) res.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
    }
    return res;
}""",
  "followups": "- Variation: both left and right views combined.\n- Column-wise view.\n- Top view."
},

"Convert Sorted Array to BST": {
  "concept": "Divide and conquer — middle element becomes root, recurse on halves.",
  "intuition": "A balanced BST emerges when we always pick the median of the current range as root; its left half forms the left subtree, right half the right subtree.",
  "explanation": "Function build(lo, hi): if lo>hi return null; mid=(lo+hi)/2; node = nums[mid]; node.left = build(lo, mid-1); node.right = build(mid+1, hi). Returns a height-balanced BST.",
  "dry_run": "nums=[-10,-3,0,5,9]. mid=2→0. Left [-10,-3] mid→-10 then -3 as right. Right [5,9] similarly. Height 3.",
  "approach": "Recursive median picking.",
  "complexity": "Time: O(n). Space: O(log n) recursion.",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

TreeNode* build(vector<int>& a, int lo, int hi) {
    if (lo > hi) return nullptr;
    int mid = (lo + hi) / 2;
    auto* n = new TreeNode(a[mid]);
    n->left = build(a, lo, mid - 1);
    n->right = build(a, mid + 1, hi);
    return n;
}
TreeNode* sortedArrayToBST(vector<int>& a) { return build(a, 0, a.size() - 1); }""",
  "followups": "- Convert sorted linked list to BST (O(n) with in-order build).\n- Weight-balanced variant.\n- Iterative approach."
},

"Kth Smallest Element in BST": {
  "concept": "In-order traversal with early termination at k-th visit.",
  "intuition": "In-order yields sorted values. Stop at the k-th node visited.",
  "explanation": "Use an iterative in-order traversal; decrement k on each pop; when k==0, return that node's value.",
  "dry_run": "BST 3,1,4,_,2, k=1. Push left spine: [3,1]. Pop 1, k=0, return 1.",
  "approach": "Iterative in-order with stack.",
  "complexity": "Time: O(h+k). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int kthSmallest(TreeNode* root, int k) {
    stack<TreeNode*> st;
    TreeNode* cur = root;
    while (cur || !st.empty()) {
        while (cur) { st.push(cur); cur = cur->left; }
        cur = st.top(); st.pop();
        if (--k == 0) return cur->val;
        cur = cur->right;
    }
    return -1;
}""",
  "followups": "- With frequent modifications — augment nodes with subtree size.\n- k-th largest.\n- Range count queries."
},

"Lowest Common Ancestor of BST": {
  "concept": "Walk down the BST using BST property until p and q split.",
  "intuition": "If both p and q are smaller than current, go left. If both are bigger, go right. Otherwise current is the split point — their LCA.",
  "explanation": "Iteratively traverse from root. Compare values: if p.val < cur.val and q.val < cur.val go left; if both > cur.val go right; else return cur.",
  "dry_run": "BST root=6, p=2, q=4. 2<6, 4<6 → go left to 2. Then 2==cur → return 2.",
  "approach": "Top-down pointer walk.",
  "complexity": "Time: O(h). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    while (root) {
        if (p->val < root->val && q->val < root->val) root = root->left;
        else if (p->val > root->val && q->val > root->val) root = root->right;
        else return root;
    }
    return nullptr;
}""",
  "followups": "- Normal binary tree LCA.\n- LCA with parent pointers.\n- Persistent LCA queries."
},

"Merge Two BSTs": {
  "concept": "Convert to sorted arrays, merge, build balanced BST.",
  "intuition": "Combine the sorted sequences of both BSTs then reconstruct a balanced BST from the merged sorted array.",
  "explanation": "In-order traverse both trees into vectors; merge; build balanced BST using median-picking recursion.",
  "dry_run": "Tree1 [2,4]; Tree2 [1,3,5]. Merge [1,2,3,4,5]. Build root 3, left 1-2, right 4-5.",
  "approach": "Three-phase: flatten, merge, rebuild.",
  "complexity": "Time: O(n1+n2). Space: O(n1+n2).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

void io(TreeNode* r, vector<int>& v) { if (!r) return; io(r->left,v); v.push_back(r->val); io(r->right,v); }
TreeNode* build(vector<int>& a, int lo, int hi) {
    if (lo > hi) return nullptr;
    int m = (lo + hi) / 2;
    auto* n = new TreeNode(a[m]);
    n->left = build(a, lo, m-1); n->right = build(a, m+1, hi);
    return n;
}
TreeNode* mergeBSTs(TreeNode* a, TreeNode* b) {
    vector<int> va, vb, merged;
    io(a, va); io(b, vb);
    merge(va.begin(),va.end(),vb.begin(),vb.end(),back_inserter(merged));
    return build(merged, 0, merged.size()-1);
}""",
  "followups": "- Keep BST structure unchanged (BST iterator merge).\n- Remove duplicates during merge.\n- Merge k BSTs."
},

"Construct Binary Tree from Traversals": {
  "concept": "Reconstruct from preorder+inorder (or postorder+inorder) using index split.",
  "intuition": "Preorder's first element is the root. Locate it in inorder to split left/right subtrees' sizes. Recurse on the two halves.",
  "explanation": "Build a map value→index in inorder for O(1) lookup. Maintain a preorder pointer. In build(lo, hi): root = preorder[p++]; split at inorderIndex[root]; build left then right.",
  "dry_run": "pre=[3,9,20,15,7], in=[9,3,15,20,7]. root=3, split at idx 1. Left in [9] → root 9. Right in [15,20,7] → root 20, etc.",
  "approach": "Recursive construction with hash map.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

class Sol {
    unordered_map<int,int> idx;
    vector<int> pre;
    int p = 0;
    TreeNode* build(int lo, int hi) {
        if (lo > hi) return nullptr;
        int v = pre[p++];
        auto* n = new TreeNode(v);
        n->left = build(lo, idx[v]-1);
        n->right = build(idx[v]+1, hi);
        return n;
    }
public:
    TreeNode* buildTree(vector<int>& preorder, vector<int>& inorder) {
        pre = preorder;
        for (int i = 0; i < (int)inorder.size(); ++i) idx[inorder[i]] = i;
        return build(0, inorder.size()-1);
    }
};""",
  "followups": "- Build from inorder + postorder.\n- Build from preorder + postorder (ambiguous — may need BST assumption).\n- Serialize/deserialize."
},

"Range Sum of BST": {
  "concept": "DFS pruning using BST property.",
  "intuition": "Use BST structure to skip subtrees outside [L,R]. If current < L, only right subtree matters; if > R, only left.",
  "explanation": "rangeSum(node): if null 0; if val < L return rangeSum(right); if val > R return rangeSum(left); else val + rangeSum(left) + rangeSum(right).",
  "dry_run": "BST 10,5,15,3,7,_,18, L=7,R=15. 10 in range → add 10+rs(5)+rs(15). rs(5): 5<7 → rs(7)=7. rs(15)→15+rs(_)+rs(18, 18>15 →rs(left)=0)=15. Total 32.",
  "approach": "Recursive pruning.",
  "complexity": "Time: O(n) worst, O(h+k) with skew. Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int rangeSumBST(TreeNode* r, int L, int R) {
    if (!r) return 0;
    if (r->val < L) return rangeSumBST(r->right, L, R);
    if (r->val > R) return rangeSumBST(r->left, L, R);
    return r->val + rangeSumBST(r->left, L, R) + rangeSumBST(r->right, L, R);
}""",
  "followups": "- Count nodes in range.\n- Range sum with frequent updates — augmented BST.\n- K-th element in range."
},

"Queue Reconstruction by Height": {
  "concept": "Sort by height desc, k asc; insert at position k.",
  "intuition": "If we process people from tallest to shortest, when inserting each person, taller people (already placed) are the only ones that matter for their k value; the current person's k equals exactly their target index.",
  "explanation": "Sort people by (−h, k). Iterate; for each (h,k) insert at position k in the result list. List insertion ensures taller-already-placed count equals k.",
  "dry_run": "Input [[7,0],[4,4],[7,1],[5,0],[6,1],[5,2]]. Sort desc h: [[7,0],[7,1],[6,1],[5,0],[5,2],[4,4]]. Insert: [7,0]; [7,0],[7,1]; [7,0],[6,1],[7,1]; ... final [[5,0],[7,0],[5,2],[6,1],[4,4],[7,1]].",
  "approach": "Sort + list.insert.",
  "complexity": "Time: O(n²). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> reconstructQueue(vector<vector<int>>& p) {
    sort(p.begin(), p.end(), [](auto& a, auto& b){
        return a[0] != b[0] ? a[0] > b[0] : a[1] < b[1];
    });
    vector<vector<int>> res;
    for (auto& x : p) res.insert(res.begin() + x[1], x);
    return res;
}""",
  "followups": "- Use a Fenwick tree for O(n log n).\n- What if k counts shorter people?\n- Stream reconstruction."
},
}
