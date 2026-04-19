DATA = {
"Balanced Binary Tree": {
  "concept": "Post-order DFS returning height, propagating -1 on imbalance.",
  "intuition": "A tree is balanced if every node's two subtree heights differ by at most 1. Compute heights bottom-up and short-circuit when imbalance detected.",
  "explanation": "h(node): if null return 0. l=h(left); r=h(right). If l==-1 or r==-1 or |l-r|>1 return -1. Else return max(l,r)+1. Overall balanced iff h(root)!=-1.",
  "dry_run": "Tree 3,9,20,_,_,15,7. h(9)=1,h(15)=1,h(7)=1,h(20)=2,h(3)=3. No imbalance → balanced.",
  "approach": "Single post-order traversal, short-circuit via sentinel.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int h(TreeNode* r) {
    if (!r) return 0;
    int l = h(r->left); if (l == -1) return -1;
    int rr = h(r->right); if (rr == -1) return -1;
    if (abs(l - rr) > 1) return -1;
    return max(l, rr) + 1;
}
bool isBalanced(TreeNode* root) { return h(root) != -1; }""",
  "followups": "- Balanced within k instead of 1.\n- Weight-balanced tree check.\n- Convert unbalanced tree to balanced."
},

"Binary Tree Inorder Traversal": {
  "concept": "Recursive left-root-right traversal.",
  "intuition": "In-order visits left subtree, then node, then right subtree — yielding sorted order in a BST.",
  "explanation": "Recurse on left, push current value, recurse on right.",
  "dry_run": "Tree 1,_,2,3. In-order: 1,3,2.",
  "approach": "Simple recursion; iterative via stack also common.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void io(TreeNode* r, vector<int>& v) { if (!r) return; io(r->left, v); v.push_back(r->val); io(r->right, v); }
vector<int> inorderTraversal(TreeNode* root) { vector<int> v; io(root, v); return v; }""",
  "followups": "- Iterative inorder using stack.\n- Morris inorder in O(1) space.\n- BFS inorder for threaded trees."
},

"Binary Tree Postorder Traversal": {
  "concept": "Left-right-root traversal.",
  "intuition": "Postorder yields children before parents — useful for delete/free and dependency processing.",
  "explanation": "Recurse left, recurse right, then push current value.",
  "dry_run": "Tree 1,_,2,3. Postorder: 3,2,1.",
  "approach": "Recursion; iterative using two-stack trick or modified preorder reversed.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void po(TreeNode* r, vector<int>& v) { if (!r) return; po(r->left,v); po(r->right,v); v.push_back(r->val); }
vector<int> postorderTraversal(TreeNode* root) { vector<int> v; po(root, v); return v; }""",
  "followups": "- Iterative with stack.\n- Level-order reverse.\n- Morris postorder (trickier)."
},

"Binary Tree Preorder Traversal": {
  "concept": "Root-left-right traversal.",
  "intuition": "Preorder gives the root before children — suitable for tree copy/serialize.",
  "explanation": "Push current value, recurse left, recurse right.",
  "dry_run": "Tree 1,_,2,3. Preorder: 1,2,3.",
  "approach": "Recursion or iterative stack pushing right first.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void pr(TreeNode* r, vector<int>& v) { if (!r) return; v.push_back(r->val); pr(r->left,v); pr(r->right,v); }
vector<int> preorderTraversal(TreeNode* root) { vector<int> v; pr(root, v); return v; }""",
  "followups": "- Iterative preorder with stack.\n- Morris preorder.\n- Threaded binary tree traversals."
},

"Binary Tree Level Order Traversal": {
  "concept": "BFS using a queue, collecting each level.",
  "intuition": "Level-by-level iteration — process one level fully before moving to the next. A queue naturally achieves this.",
  "explanation": "Push root. While queue non-empty: record current level size; for that many iterations pop, record value, push children. Append level vector to result.",
  "dry_run": "Tree 3,9,20,_,_,15,7. Levels: [[3],[9,20],[15,7]].",
  "approach": "BFS with level-size bookkeeping.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size(); vector<int> level;
        while (sz--) {
            auto* n = q.front(); q.pop();
            level.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(level);
    }
    return res;
}""",
  "followups": "- Zigzag level order.\n- Bottom-up level order.\n- Level order with separators for null."
},

"Construct Binary Tree from Inorder and Postorder": {
  "concept": "Postorder's last element is root; split inorder around it.",
  "intuition": "Similar to preorder+inorder but process postorder right-to-left (building right subtree first).",
  "explanation": "Map inorder value→index. Use postorder pointer p from end. In build(lo, hi): v=post[p--]; root=v; build right first (idx+1..hi) then left (lo..idx-1).",
  "dry_run": "in=[9,3,15,20,7], post=[9,15,7,20,3]. root=3, split at 1. Right in [15,20,7] root=20, etc.",
  "approach": "Recursive with postorder pointer and hashmap.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

class Sol {
    unordered_map<int,int> idx;
    vector<int> post;
    int p;
    TreeNode* build(int lo, int hi) {
        if (lo > hi) return nullptr;
        int v = post[p--];
        auto* n = new TreeNode(v);
        n->right = build(idx[v]+1, hi);
        n->left = build(lo, idx[v]-1);
        return n;
    }
public:
    TreeNode* buildTree(vector<int>& inorder, vector<int>& postorder) {
        post = postorder; p = post.size() - 1;
        for (int i = 0; i < (int)inorder.size(); ++i) idx[inorder[i]] = i;
        return build(0, inorder.size()-1);
    }
};""",
  "followups": "- Build from pre+post (ambiguous).\n- Check that arrays are valid traversals.\n- Serialize the reconstructed tree."
},

"Binary Tree Inorder Traversal (Iterative)": {
  "concept": "Stack-based inorder: walk left, pop, go right.",
  "intuition": "Simulate recursion explicitly using a stack. Push left children until null; pop and visit; then move to right child.",
  "explanation": "cur = root. While cur or stack non-empty: push all left descendants of cur; pop, record value, set cur = popped->right.",
  "dry_run": "Tree 1,_,2,3. cur=1, push [1]. cur=null. pop 1→visit. cur=2. push [2,3]. pop 3→visit. pop 2→visit. Result [1,3,2].",
  "approach": "Explicit stack.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<int> inorderIter(TreeNode* root) {
    vector<int> res; stack<TreeNode*> st; auto* cur = root;
    while (cur || !st.empty()) {
        while (cur) { st.push(cur); cur = cur->left; }
        cur = st.top(); st.pop();
        res.push_back(cur->val);
        cur = cur->right;
    }
    return res;
}""",
  "followups": "- Morris traversal for O(1) space.\n- Iterative preorder and postorder.\n- Handle threaded binary trees."
},

"Invert Binary Tree": {
  "concept": "Recursively swap left and right at every node.",
  "intuition": "Mirroring the tree means left↔right swap at each node. Apply recursively in any order.",
  "explanation": "invert(node): if null return null; swap node->left and node->right; recurse on both. Return node.",
  "dry_run": "Tree 4,2,7,1,3,6,9. Swap becomes 4,7,2,9,6,3,1.",
  "approach": "Recursion or BFS iterative swap.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    swap(root->left, root->right);
    invertTree(root->left); invertTree(root->right);
    return root;
}""",
  "followups": "- Invert only specific levels.\n- Check if a tree equals its mirror.\n- Convert tree to its mirror iteratively."
},

"Maximum Depth of Binary Tree": {
  "concept": "1 + max(depth(left), depth(right)).",
  "intuition": "Depth is the longest root-to-leaf path. Recursion naturally decomposes the problem per subtree.",
  "explanation": "Base: null returns 0. Recursive: return 1 + max(depth(left), depth(right)).",
  "dry_run": "Tree 3,9,20,_,_,15,7. depth(3)=1+max(1,2)=3.",
  "approach": "Post-order recursion.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int maxDepth(TreeNode* r) {
    if (!r) return 0;
    return 1 + max(maxDepth(r->left), maxDepth(r->right));
}""",
  "followups": "- Minimum depth of a binary tree.\n- Diameter of a binary tree.\n- Depth of every node as an array."
},

"Lowest Common Ancestor of Binary Tree": {
  "concept": "Post-order recursion — node is LCA if p and q found in different subtrees.",
  "intuition": "Descend the tree; if both targets appear in different subtrees of a node, that node is their LCA; otherwise propagate the found one upward.",
  "explanation": "lca(node): if null or node==p or node==q, return node. L=lca(left); R=lca(right). If both non-null return node; else return the non-null one.",
  "dry_run": "Tree 3,5,1,..., p=5,q=1. From root: left returns 5, right returns 1 → root=3 is LCA.",
  "approach": "Post-order propagation.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

TreeNode* lowestCommonAncestor(TreeNode* r, TreeNode* p, TreeNode* q) {
    if (!r || r == p || r == q) return r;
    auto* l = lowestCommonAncestor(r->left, p, q);
    auto* R = lowestCommonAncestor(r->right, p, q);
    if (l && R) return r;
    return l ? l : R;
}""",
  "followups": "- What if p or q may be absent?\n- LCA with parent pointers (two-pointer technique).\n- Offline LCA queries (Tarjan's)."
},

"Path Sum": {
  "concept": "DFS decrementing target along root-to-leaf paths.",
  "intuition": "Check if any root-to-leaf path sums to target. At each node, subtract its value and recurse; at a leaf, check if remaining equals zero.",
  "explanation": "hasPath(node, sum): if null return false. If leaf: return node.val == sum. Else return hasPath(left, sum-node.val) || hasPath(right, sum-node.val).",
  "dry_run": "Tree 5,4,8,11,_,13,4,7,2, target=22. Path 5→4→11→2 sums 22 → true.",
  "approach": "Recursion.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

bool hasPathSum(TreeNode* r, int s) {
    if (!r) return false;
    if (!r->left && !r->right) return s == r->val;
    return hasPathSum(r->left, s - r->val) || hasPathSum(r->right, s - r->val);
}""",
  "followups": "- Return the path values.\n- Count all paths with sum = target.\n- Path from any node to any descendant."
},

"Path Sum II": {
  "concept": "Backtracking along root-to-leaf paths collecting matches.",
  "intuition": "Extend Path Sum by recording the current path. On a leaf with the target sum met, snapshot the path.",
  "explanation": "DFS with a running vector. On entry push node. On leaf with remaining sum zero, copy path to result. On exit pop node.",
  "dry_run": "Tree similar; collect each root-to-leaf path equaling target.",
  "approach": "Backtracking DFS.",
  "complexity": "Time: O(n²) worst case. Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void dfs(TreeNode* r, int s, vector<int>& cur, vector<vector<int>>& res) {
    if (!r) return;
    cur.push_back(r->val);
    if (!r->left && !r->right && s == r->val) res.push_back(cur);
    dfs(r->left, s - r->val, cur, res);
    dfs(r->right, s - r->val, cur, res);
    cur.pop_back();
}
vector<vector<int>> pathSum(TreeNode* r, int s) { vector<vector<int>> res; vector<int> cur; dfs(r, s, cur, res); return res; }""",
  "followups": "- Count paths with sum ≤ target.\n- Paths of exactly k edges.\n- Tolerate negative values (already works)."
},

"Path Sum III": {
  "concept": "Prefix-sum counts on paths — path-sum between any two nodes equals targetSum.",
  "intuition": "Paths don't need to start at root. Maintain a running prefix sum from root to current; any prefix that differs from current by targetSum defines a valid path ending at current.",
  "explanation": "DFS from root. Keep a map: prefixSum → count. On entering node, cur+=node.val. Add count[cur-target] to answer. Increment count[cur]. Recurse. On exit, decrement count[cur].",
  "dry_run": "Tree 10,5,-3,..., target=8. Count prefixes — multiple paths e.g. 5→3 sums 8, 5→2→1 sums 8. Total 3 paths.",
  "approach": "Prefix-sum + hashmap, DFS backtrack.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

class Sol {
    unordered_map<long long,int> cnt;
    long long target;
    int ans = 0;
    void dfs(TreeNode* r, long long cur) {
        if (!r) return;
        cur += r->val;
        ans += cnt[cur - target];
        cnt[cur]++;
        dfs(r->left, cur); dfs(r->right, cur);
        cnt[cur]--;
    }
public:
    int pathSum(TreeNode* root, int t) { target = t; cnt[0] = 1; dfs(root, 0); return ans; }
};""",
  "followups": "- Paths must have length ≥ k.\n- Paths with sum in a range.\n- Paths between arbitrary nodes (not just descending)."
},

"Sum Root to Leaf Numbers": {
  "concept": "DFS constructing numbers digit-by-digit; sum at leaves.",
  "intuition": "Each root-to-leaf path represents a number formed by concatenating digits. DFS accumulates the number as num*10+digit and adds it at each leaf.",
  "explanation": "dfs(node, cur): if null return 0. cur = cur*10 + node.val. If leaf return cur. Else return dfs(left, cur) + dfs(right, cur).",
  "dry_run": "Tree 1,2,3. Paths 12 and 13. Sum=25.",
  "approach": "Single DFS.",
  "complexity": "Time: O(n). Space: O(h).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int dfs(TreeNode* r, int cur) {
    if (!r) return 0;
    cur = cur * 10 + r->val;
    if (!r->left && !r->right) return cur;
    return dfs(r->left, cur) + dfs(r->right, cur);
}
int sumNumbers(TreeNode* root) { return dfs(root, 0); }""",
  "followups": "- Sum in a different base.\n- Print all numbers formed.\n- Product of numbers along path."
},

"Paths from root with a specified sum": {
  "concept": "DFS enumerating root-downward paths with running sum.",
  "intuition": "Generate every downward path from the root (full or partial) and check which sum equals the target.",
  "explanation": "Recurse with current path. At each node, add to current path; check each *suffix* starting from root to current equaling target (or use prefix-sum map for efficiency).",
  "dry_run": "Tree 10,5,-3,3,2,_,11,3,-2,_,1. Target=8. Paths: 5→3, 5→2→1, -3→11.",
  "approach": "DFS with prefix-sum map (see Path Sum III).",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """// See Path Sum III implementation — same pattern with prefix-sum map.""",
  "followups": "- Constrain path to a minimum length.\n- Count vs enumerate the paths.\n- Extend to any two nodes (not just downward)."
},
}
