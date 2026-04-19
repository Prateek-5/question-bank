"""Teaching-first concepts generator."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import ROOT, write

# Per-topic content for the 10-section teaching concept guides.
# Each entry must provide: display, intro, analogy, core, when_to_use, variations,
#                         step_by_step, visual, code, mistakes, interview.
TOPICS = {
"Heap_Priority_Queue": {
    "display": "Heap / Priority Queue",
    "intro": "A heap is a specialized data structure that gives you quick access to the maximum (or minimum) element in a collection. It's the data structure you reach for whenever the question asks for *'the largest so far'*, *'the k smallest'*, or *'process items by priority'*. Without a heap, those questions would require repeated sorting — slow and wasteful. A heap does the job in O(log n) per update.",
    "analogy": "Think of a hospital emergency room. Patients arrive in some random order, but they're *not* treated first-come-first-served — they're treated by priority. The nurse at the triage desk is the heap: at any moment, she can tell you who the highest-priority patient is. When a new patient arrives, she slots them into the right priority position. That's exactly what a heap does with numbers (or any comparable items).",
    "core": "A heap is a complete binary tree with one strict rule: every parent satisfies a comparison with its children (parent ≤ children for a min-heap, parent ≥ children for a max-heap). This invariant means the root is always the extremum — the minimum or the maximum of the entire set. Because the tree is complete, we can store it compactly in an array: the children of index i live at 2i+1 and 2i+2. When we insert, we place the new element at the end and 'bubble up' to restore the invariant. When we extract the root, we replace it with the last element and 'sift down'. Both operations are O(log n) because the tree has log n levels.",
    "when_to_use": "Reach for a heap when any of these signals appear in a problem:\n\n- **'Top k'** or **'k-th largest/smallest'** — maintain a bounded heap of size k.\n- **Streaming median** — two heaps, one for each half of the data, balanced by size.\n- **Scheduling by priority** — highest-priority task first.\n- **Greedy merges** — repeatedly combine the two smallest elements (Huffman coding, connect ropes).\n- **K-way merge** — push one head from each list into a min-heap, pop, advance, repeat.\n- **Dijkstra's algorithm** — extract the next-nearest node via a min-heap keyed on distance.\n\nIf you see any of these keywords or structures, a heap is almost certainly the right tool.",
    "variations": "**Min-Heap vs Max-Heap:** a min-heap's root is the smallest element; a max-heap's root is the largest. In C++, `priority_queue<int>` is a max-heap by default. To build a min-heap, use `priority_queue<int, vector<int>, greater<int>>`.\n\n**Indexed (Mutable) Heap:** a regular heap doesn't allow decreasing a specific key. For problems like Dijkstra with updates to intermediate distances, we either use lazy deletion (push a new entry and ignore stale ones on pop) or maintain an index map for O(log n) decrease-key.\n\n**d-ary Heap:** instead of binary, children are d-ary. Useful when decrease-key is cheaper than extract-min.\n\n**Fibonacci Heap:** theoretical O(1) amortized decrease-key. Rarely used in practice but worth knowing exists.",
    "step_by_step": "**Insertion (push):**\n1. Place the new element at the next array slot.\n2. Compare with its parent (at index (i-1)/2).\n3. If the heap property is violated, swap with the parent.\n4. Repeat from step 2 until the property holds or we reach the root.\n\n**Extraction (pop):**\n1. Save the root as the returned value.\n2. Move the last array element into the root slot.\n3. Shrink the array by one.\n4. Sift down: compare the root with its smaller child; if violated, swap. Repeat until the property holds or we reach a leaf.\n\nEach of these operations walks at most one root-to-leaf path — that's log n steps.",
    "visual": "Imagine this min-heap:\n\n```\n         2\n       /   \\\n      5     3\n     / \\   / \\\n    7   9 6   4\n```\n\nInserting `1`: place at the next slot (right of `4`), then bubble up.\n\n```\n         2                1\n       /   \\            /   \\\n      5     3    →     5     2\n     / \\   / \\        / \\   / \\\n    7   9 6   4      7   9 6   3\n     \\                \\          \\\n      1                4          <- bubble path\n```\n\nAfter bubbling, `1` is the new root, and the heap property is restored everywhere.",
    "code": """```cpp
// Max-heap (default)
priority_queue<int> max_pq;

// Min-heap
priority_queue<int, vector<int>, greater<int>> min_pq;

// Custom comparator (e.g., pair by second value)
auto cmp = [](const pair<int,int>& a, const pair<int,int>& b) {
    return a.second > b.second;  // min-heap on .second
};
priority_queue<pair<int,int>, vector<pair<int,int>>, decltype(cmp)> pq(cmp);

// Top-k smallest: keep a max-heap of size k
priority_queue<int> topK;
for (int x : nums) {
    topK.push(x);
    if ((int)topK.size() > k) topK.pop();
}
// topK now holds the k smallest; topK.top() is the k-th smallest.
```""",
    "mistakes": "- **Assuming `priority_queue<int>` is a min-heap.** It's a max-heap by default.\n- **Using a heap when you need random access.** Heaps only guarantee fast access to the extremum, not to arbitrary elements.\n- **Updating a key in place.** Heaps don't support this cleanly. Use lazy deletion or an indexed heap.\n- **Forgetting tie-breakers.** Two equal-priority items have unspecified relative order unless your comparator breaks the tie.\n- **Calling `top()` on an empty heap.** Always check `empty()` first — `top()` on an empty priority_queue is undefined behavior.",
    "interview": "When an interviewer gives you a problem involving 'top k', 'streaming', or 'merge', they're almost always testing whether you'll reach for a heap. The interviewer wants to see:\n\n1. **Can you identify the pattern?** Just naming 'priority queue' in the first minute scores huge points.\n2. **Can you pick the right polarity?** Knowing whether you need min-heap or max-heap (and why) shows you understand the mechanic, not just the name.\n3. **Can you analyze complexity correctly?** 'n log k' vs 'n log n' matters; be ready to explain which one your approach achieves.\n4. **Can you handle edge cases?** Empty input, k > n, and duplicates are the usual traps.\n\nUnder pressure, narrate your thinking out loud: 'I need the k smallest, so I'll use a max-heap of size k — every push is log k, and I pop when it exceeds k.' That sentence alone often convinces the interviewer you know what you're doing.",
},
"Math": {
    "display": "Math",
    "intro": "Math problems in DSA interviews are rarely about advanced mathematics. They're about noticing structure — divisibility, modular arithmetic, digit properties, closed-form identities — that lets you skip the loop and jump to the answer. The reward for recognizing this structure is enormous: O(n) problems often collapse to O(1) formulas once you see the pattern.",
    "analogy": "Picture a long division problem you had as a kid. At first, you did it digit by digit — it took forever. Later, you noticed shortcuts: 'oh, if the last digit is 0 or 5, it's divisible by 5.' That observation turned minutes of work into a single glance. Math problems in interviews are exactly the same. Simulation always works, but the insight collapses the problem.",
    "core": "The fundamental tools here are modular arithmetic (remainders have beautiful closure properties), the Euclidean algorithm (GCD in O(log n) via repeated remainders), digit manipulation (extract via `% 10`, strip via `/ 10`), and combinatorial identities (sum of 1..n, binomial coefficients, Catalan numbers). Most math problems reduce to applying one of these tools, or combining two.",
    "when_to_use": "Signals that suggest a math approach:\n\n- The problem mentions **primes, divisors, GCD, or LCM**.\n- You're working with **digits of a number** (add/subtract/count them).\n- **Modular constraints** appear: 'find count modulo M'.\n- The input size is **huge (10^9 or more)**, suggesting no loop can scan it.\n- You spot a **parity, symmetry, or pairing** pattern.\n\nBefore writing a loop, always ask: is there a formula for this? Often yes.",
    "variations": "- **Modular arithmetic** for large computations and counting problems mod some prime.\n- **Sieve of Eratosthenes** for generating all primes up to N.\n- **Fast exponentiation** for a^b mod m in O(log b).\n- **Digit DP** for counting numbers in a range with digit constraints.\n- **Bezout / Extended Euclidean** for solving linear Diophantine equations.",
    "step_by_step": "**Example — Digital Root (sum of digits iteratively until single digit):**\n\n1. Observation: 10 ≡ 1 (mod 9), so any number is ≡ sum of its digits (mod 9).\n2. Therefore digital root is determined entirely by n mod 9.\n3. Edge case: multiples of 9 should return 9, not 0. The formula `1 + (n-1) % 9` handles this beautifully.\n\nThis is the archetype of math problems: observe a modular invariant → derive a closed form → handle the edge cases.",
    "visual": "**Modular arithmetic cycle (mod 5):**\n\n```\n  0 → 1 → 2 → 3 → 4 → 0 → 1 → 2 → 3 → 4 → ...\n```\n\n**GCD via Euclid (a=48, b=18):**\n\n```\ngcd(48, 18) → gcd(18, 48%18=12)\n            → gcd(12, 18%12=6)\n            → gcd(6,  12%6=0)\n            → 6\n```\n\nEach step halves one value on average — that's why Euclid's algorithm is O(log min(a,b)).",
    "code": """```cpp
// GCD and LCM
int g = __gcd(a, b);
long long l = (long long)a / g * b;

// Fast power (a^b mod m)
long long power(long long a, long long b, long long m) {
    long long r = 1 % m; a %= m;
    while (b) {
        if (b & 1) r = r * a % m;
        a = a * a % m;
        b >>= 1;
    }
    return r;
}

// Sieve of Eratosthenes
vector<bool> sieve(int n) {
    vector<bool> is_prime(n + 1, true);
    is_prime[0] = is_prime[1] = false;
    for (int i = 2; (long long)i * i <= n; ++i) if (is_prime[i])
        for (int j = i * i; j <= n; j += i) is_prime[j] = false;
    return is_prime;
}
```""",
    "mistakes": "- **Integer overflow** on multiplication — use `long long` when in doubt.\n- **Negative modulo**: `((x % k) + k) % k` to handle negatives correctly.\n- **Off-by-one in inclusive/exclusive ranges** — clarify before coding.\n- **Assuming 0 is prime** (it's not, and neither is 1).\n- **Forgetting that `/` is integer division** on int operands — `5 / 2 = 2`, not `2.5`.",
    "interview": "Math problems are where interviewers test your willingness to observe before you code. They want to see:\n\n1. **Do you pause to find structure, or do you immediately loop?** Pausing is the right habit.\n2. **Can you articulate *why* a formula works?** Stating 'it's just `1 + (n-1) % 9`' without justification is weak; explaining 'because 10 ≡ 1 (mod 9)' is strong.\n3. **Do you handle edge cases (zero, one, negatives, overflow)?** Math questions are a goldmine for these.\n\nTip: if the problem constraints allow n up to 10^9 or more, there's almost certainly a formula — don't waste time looking for a loop-based solution.",
},
"Graph_BFS_DFS_Dijkstra_DSU": {
    "display": "Graph (BFS / DFS / Dijkstra / DSU)",
    "intro": "Graphs model relationships — between cities, between tasks, between people, between anything. The core algorithms (BFS, DFS, Dijkstra, Union-Find) let us answer questions like 'Can we get from A to B?', 'What's the shortest path?', and 'Are these two things connected?'. Master these four, and a surprising fraction of interview problems become routine.",
    "analogy": "Imagine a subway map. Each station is a node; each line between stations is an edge. 'How do I get from my apartment to the airport?' — that's BFS if every line takes the same time, or Dijkstra if lines take different times. 'Is Station X reachable from Station Y?' — that's DFS or Union-Find. 'Can I connect all stations with the fewest lines?' — that's a minimum spanning tree. Graphs are just this, abstracted.",
    "core": "A graph is a set of vertices V and edges E connecting them. Traversals (BFS, DFS) visit each vertex at most once by marking it visited, giving us O(V + E) time. BFS uses a queue and produces shortest-path distances in unweighted graphs because it explores level-by-level. DFS uses a stack (or recursion) and is the workhorse for topological sort, cycle detection, and connectivity. Dijkstra upgrades BFS with a priority queue for weighted graphs (non-negative weights). Union-Find (DSU) answers connectivity queries in near-constant time after O(α(n)) preprocessing per operation.",
    "when_to_use": "Signals for each algorithm:\n\n- **'Shortest path in an unweighted graph'** → BFS.\n- **'Shortest path with non-negative weights'** → Dijkstra.\n- **'Shortest path with negative weights or k-stop constraint'** → Bellman-Ford.\n- **'All-pairs shortest paths on a small graph'** → Floyd-Warshall.\n- **'Connectivity, components, cycle detection'** → DFS or Union-Find.\n- **'Topological order, course schedule'** → Kahn's BFS or DFS post-order.\n- **'Bipartite check'** → 2-coloring via BFS/DFS.",
    "variations": "- **Directed vs Undirected:** directed edges require separate handling (in-degree matters for topo sort).\n- **Weighted vs Unweighted:** BFS for unweighted, Dijkstra for weighted-positive, Bellman-Ford for weighted-general.\n- **Dense vs Sparse:** adjacency matrix for dense (small n), adjacency list for sparse (large n).\n- **Multi-source BFS:** start BFS from *multiple* nodes at once — used in 'nearest 0' or 'rotten oranges' style problems.\n- **Bidirectional BFS:** BFS from both start and end simultaneously; meets in the middle for faster search.",
    "step_by_step": "**BFS:**\n1. Enqueue the source; mark it visited.\n2. Pop from the queue. For each unvisited neighbor, mark visited and enqueue.\n3. Repeat until the queue is empty.\n\n**DFS (recursive):**\n1. Mark the current node visited.\n2. Recurse on each unvisited neighbor.\n\n**Dijkstra:**\n1. Push (0, source) into a min-heap. Set dist[source] = 0.\n2. Pop (d, u). If d > dist[u], skip (stale entry).\n3. For each neighbor v with edge weight w, if dist[u] + w < dist[v], update dist[v] and push.\n4. Repeat until the heap is empty.\n\n**Union-Find:**\n1. `find(x)` — walk parent pointers to the root, with path compression.\n2. `union(a, b)` — attach the shorter tree under the taller; update ranks.",
    "visual": "**BFS expanding layer by layer from source S:**\n\n```\n     Layer 0:   [S]\n     Layer 1:   [A, B]\n     Layer 2:   [C, D, E]\n     Layer 3:   [F]\n```\n\nEach layer corresponds to one BFS round and represents all nodes at that distance from S.\n\n**DSU component merges:**\n\n```\n  Initially: {0}, {1}, {2}, {3}, {4}\n  union(0, 1): {0, 1}, {2}, {3}, {4}\n  union(2, 3): {0, 1}, {2, 3}, {4}\n  union(1, 3): {0, 1, 2, 3}, {4}\n```\n\nOnce components merge, `find(0) == find(3)` because they're in the same set.",
    "code": """```cpp
// BFS
queue<int> q; q.push(src);
vector<int> dist(n, -1); dist[src] = 0;
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : g[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        q.push(v);
    }
}

// Dijkstra
priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
vector<int> dist(n, INT_MAX);
dist[src] = 0; pq.push({0, src});
while (!pq.empty()) {
    auto [d, u] = pq.top(); pq.pop();
    if (d > dist[u]) continue;
    for (auto [v, w] : g[u]) if (d + w < dist[v]) {
        dist[v] = d + w;
        pq.push({dist[v], v});
    }
}

// Union-Find
struct DSU {
    vector<int> p, r;
    DSU(int n): p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a;
        if (r[a] == r[b]) r[a]++;
        return true;
    }
};
```""",
    "mistakes": "- **Forgetting to mark visited** — causes infinite loops in cyclic graphs.\n- **Using BFS for weighted shortest paths** — it only works for unweighted graphs.\n- **Not skipping stale entries in Dijkstra** — can blow up the queue and complexity.\n- **Directed vs undirected confusion** — always add reverse edges for undirected graphs.\n- **Off-by-one in 0-indexed vs 1-indexed inputs.**\n- **Stack overflow on deep DFS** — switch to iterative for very deep trees.",
    "interview": "Graph problems are a staple of interviews because they test multiple skills at once: modeling, algorithm selection, and implementation. Interviewers want to see:\n\n1. **Can you model the problem as a graph?** Often the hardest step — recognizing that 'tasks with dependencies' is a graph with directed edges.\n2. **Can you choose the right algorithm?** BFS vs DFS vs Dijkstra is a quick decision if you know the signals.\n3. **Can you handle edge cases?** Isolated nodes, multiple components, self-loops, multigraphs.\n4. **Can you implement cleanly?** Adjacency list setup, visited tracking, and pop/push order are all easy to mess up under pressure.\n\nNarrate the graph in your head before coding: 'Nodes are cities, edges are flights with cost as weight — so this is Dijkstra with a positive-weight graph.' That narration alone saves you from going down the wrong path.",
},
"Binary_Search_Tree_BST": {
    "display": "Binary Search Tree (BST)",
    "intro": "A Binary Search Tree is a tree where every node's value is greater than everything in its left subtree and less than everything in its right subtree. That simple rule gives us O(log n) search, insert, and delete *on average* — plus the ability to traverse keys in sorted order without sorting. BSTs are the bridge between trees (structural thinking) and sorted arrays (ordered access).",
    "analogy": "Think of a well-organized library where books are placed by their dewey decimal number. To find a specific book, you don't scan every shelf — you navigate to the right section first, then the right row. That's exactly what a BST does: at every node, you decide 'left or right' based on how the target compares, and you eliminate half the remaining possibilities with each step.",
    "core": "The BST invariant — left < node < right for every node — is powerful because it creates a globally sorted structure from local comparisons. In-order traversal (left, root, right) visits nodes in sorted order, which turns many questions into 'walk the BST in sorted order and do X'. Balanced BSTs (AVL, red-black) enforce O(log n) height; unbalanced BSTs can degrade to O(n) (essentially a linked list), which is why production code almost always uses a balanced variant.",
    "when_to_use": "Reach for a BST (or a built-in balanced equivalent like `std::set`/`std::map`) when you need:\n\n- **Sorted iteration** combined with dynamic insert/delete.\n- **Nearest predecessor or successor** of a value.\n- **Range queries** (all keys in [lo, hi]).\n- **K-th smallest/largest** with changes over time.\n- **Ordered statistics** — rank of an element, element at a rank.\n\nIf you only need unordered membership tests, use a hash set instead — it's O(1) on average.",
    "variations": "- **Unbalanced BST:** simple to implement, can degrade to O(n) height.\n- **Balanced BSTs:** AVL trees (rigid balance), red-black trees (looser balance, used in `std::set`), splay trees (self-adjusting).\n- **Augmented BST:** store extra info per node (subtree size, subtree sum) to support rank/select queries in O(log n).\n- **B-tree:** generalization with more than two children per node — used in databases and filesystems.",
    "step_by_step": "**Search(node, key):**\n1. If node is null, return null.\n2. If key == node.val, return node.\n3. If key < node.val, recurse on node.left.\n4. Else recurse on node.right.\n\n**Insert(node, key):**\n1. If node is null, create and return a new node.\n2. If key < node.val, node.left = insert(node.left, key).\n3. Else node.right = insert(node.right, key).\n4. Return node.\n\n**In-order traversal (gives sorted order):**\n1. Recurse on left.\n2. Visit current.\n3. Recurse on right.",
    "visual": "**BST after inserting 5, 3, 7, 1, 4, 6, 8:**\n\n```\n         5\n       /   \\\n      3     7\n     / \\   / \\\n    1   4 6   8\n```\n\n**In-order traversal visits:** 1 → 3 → 4 → 5 → 6 → 7 → 8 (sorted!).\n\n**Searching for 4:** compare 4 with 5 (go left) → compare with 3 (go right) → compare with 4 (found).\n\nNotice we only looked at 3 of the 7 nodes. That's the O(log n) magic of a balanced tree.",
    "code": """```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x): val(x), left(nullptr), right(nullptr) {}
};

TreeNode* insert(TreeNode* root, int v) {
    if (!root) return new TreeNode(v);
    if (v < root->val) root->left = insert(root->left, v);
    else root->right = insert(root->right, v);
    return root;
}

bool search(TreeNode* root, int v) {
    while (root) {
        if (v == root->val) return true;
        root = v < root->val ? root->left : root->right;
    }
    return false;
}

// In-order iterator (stack-based, O(1) amortized next)
class BSTIterator {
    stack<TreeNode*> st;
    void pushLeft(TreeNode* n) { while (n) { st.push(n); n = n->left; } }
public:
    BSTIterator(TreeNode* root) { pushLeft(root); }
    bool hasNext() { return !st.empty(); }
    int next() {
        TreeNode* n = st.top(); st.pop();
        pushLeft(n->right);
        return n->val;
    }
};
```""",
    "mistakes": "- **Assuming the tree is balanced.** Worst-case height can be O(n) for an unbalanced BST.\n- **Deletion is subtle** — particularly when removing a node with two children (use in-order successor or predecessor).\n- **Duplicate keys policy must be explicit** — left? right? skip? — decide before coding.\n- **Recursive traversals stack-overflowing** on deep trees — prefer iterative when depth can be large.\n- **Confusing BST invariant with heap invariant** — they are different. BSTs are ordered left-to-right; heaps are ordered root-to-children.",
    "interview": "BST problems check whether you can exploit the ordering invariant rather than treating the tree as an arbitrary binary tree. Interviewers want to see:\n\n1. **Do you use the BST property?** Walking into a BST question and doing a full tree traversal when O(log n) was possible signals you missed the point.\n2. **Can you reason about in-order traversal?** Many problems become trivial once you realize in-order yields a sorted sequence.\n3. **Can you handle balance and worst cases?** Follow-up questions often ask about balanced trees.\n4. **Do you know when *not* to use a BST?** If you just need membership, a hash set is better.\n\nMantra: 'If the problem mentions a BST, the first question to ask yourself is — does the BST property let me skip half the tree?' Usually the answer is yes.",
},
"Trees_Binary_Trees": {
    "display": "Trees / Binary Trees",
    "intro": "Binary trees are hierarchical structures where each node has up to two children. They show up everywhere — from expression parsing to decision trees to game state trees. The key skill isn't memorizing algorithms; it's learning to *think recursively*. Almost every binary tree problem has the shape: 'solve it for the two subtrees, then combine'.",
    "analogy": "Think of a family tree. If you want to know how many descendants someone has, you don't count them manually — you ask each of their children 'how many descendants do you have?', sum the answers, and add 1 (for the person themselves). That's divide-and-conquer on a tree. Every binary tree algorithm is basically this recursive conversation.",
    "core": "The foundational operations on binary trees are the four traversals: preorder (root, left, right), inorder (left, root, right), postorder (left, right, root), and level-order (BFS). Most problems map naturally to one of these. Post-order is the workhorse for problems that aggregate information from subtrees: the recursive call returns child data, we combine it, we return the combined result. If you master that pattern, you can solve a wide class of tree problems almost by reflex.",
    "when_to_use": "You're probably working with a binary tree when the problem describes:\n\n- **Hierarchical data** (parent-child relationships).\n- **Expression parsing** (operators as internal nodes, operands as leaves).\n- **Decision processes** (each node is a decision with two outcomes).\n- **Any structure with 'each node has at most two children'.**\n\nFor problems on such structures, ask yourself: 'What's the answer for a subtree?' — that's the recursive subproblem.",
    "variations": "- **Full binary tree:** every node has 0 or 2 children.\n- **Complete binary tree:** all levels filled except possibly the last, which is filled left-to-right.\n- **Perfect binary tree:** all internal nodes have two children and all leaves are at the same depth.\n- **BST (Binary Search Tree):** adds the ordering invariant.\n- **Balanced tree:** AVL, red-black — height is O(log n).\n- **N-ary tree:** generalization where each node has up to N children.",
    "step_by_step": "**The recursive template for most tree problems:**\n\n1. Base case: if the node is null, return the identity value (0, null, true — depends on the problem).\n2. Recurse on the left child → get `leftResult`.\n3. Recurse on the right child → get `rightResult`.\n4. Combine `leftResult`, `rightResult`, and the current node's data.\n5. Return the combined result.\n\n**Example — Compute height:**\n- Base: null → return 0.\n- Recurse left and right.\n- Return 1 + max(leftHeight, rightHeight).\n\n**Example — Sum of all node values:**\n- Base: null → return 0.\n- Recurse left and right.\n- Return node.val + leftSum + rightSum.\n\nNotice the pattern is the same — only the combine step changes.",
    "visual": "**A sample tree:**\n\n```\n         1\n       /   \\\n      2     3\n     / \\     \\\n    4   5     6\n```\n\n- **Preorder** (root, L, R): 1 → 2 → 4 → 5 → 3 → 6\n- **Inorder** (L, root, R): 4 → 2 → 5 → 1 → 3 → 6\n- **Postorder** (L, R, root): 4 → 5 → 2 → 6 → 3 → 1\n- **Level-order**: 1 → 2 → 3 → 4 → 5 → 6\n\nEach traversal paints a different picture; pick the one that fits your problem.",
    "code": """```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x): val(x), left(nullptr), right(nullptr) {}
};

// Generic postorder aggregator template
int solve(TreeNode* root) {
    if (!root) return /* identity */;
    int l = solve(root->left);
    int r = solve(root->right);
    return /* combine l, r, root->val */;
}

// Height
int height(TreeNode* r) {
    if (!r) return 0;
    return 1 + max(height(r->left), height(r->right));
}

// Level-order
vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        vector<int> lvl;
        while (sz--) {
            auto* n = q.front(); q.pop();
            lvl.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(lvl);
    }
    return res;
}
```""",
    "mistakes": "- **Missing null checks.** A single unguarded dereference will crash your code.\n- **Confusing preorder, inorder, postorder.** Write them down as strings and trace each before coding.\n- **Using BFS when DFS is needed (or vice versa).** Level-order = BFS; divide-and-conquer = DFS.\n- **Recursion depth issues on skewed trees.** For very deep trees, iterative traversals with an explicit stack are safer.\n- **Forgetting to update the result when the subtree itself is the answer.** (Diameter is a classic example — the longest path might not include the root.)",
    "interview": "Binary tree problems are interviewer favorites because they reveal whether you can think recursively. Interviewers want to see:\n\n1. **Do you formulate the recursive subproblem clearly?** Naming what each call returns is half the battle.\n2. **Do you pick the right traversal?** A clear justification scores points.\n3. **Do you handle edge cases?** Empty tree, single node, skewed tree.\n4. **Can you convert recursion to iteration if asked?** Many follow-ups test this.\n\nTip: when you're stuck on a tree problem, ask 'what does the answer look like for a single node? For a leaf?' Those extremes usually seed the recursion.",
},
"Greedy": {
    "display": "Greedy",
    "intro": "Greedy algorithms are deceptively simple: at each step, make the locally optimal choice and hope it leads to a globally optimal answer. Sometimes it does, sometimes it doesn't — and that's the hard part. The discipline of a greedy algorithm is proving that the local choice is safe.",
    "analogy": "Think of packing for a trip with a weight limit. A greedy strategy: pack the most valuable item you can still afford, repeat. For some problems this is optimal (e.g., items are infinitely divisible). For others it isn't (the classic 0/1 knapsack). Recognizing which is which is the core skill.",
    "core": "Greedy works when the problem has the **greedy-choice property** (a globally optimal solution contains the local greedy pick) and **optimal substructure** (optimal solutions for the whole are built from optimal solutions for parts). When both hold, sort or heap-prioritize by the right key, pick greedily, and move on. Proving it requires an exchange argument: show that swapping any other choice with the greedy choice doesn't make things worse.",
    "when_to_use": "Signals that suggest greedy:\n\n- **'Minimum' or 'maximum' with no overlap complications.**\n- **Scheduling, interval, or resource-allocation problems.**\n- **Huffman-style problems** (combine two smallest).\n- **Problems where local and global optimum visibly align.**\n\nWhen greedy is wrong, DP is almost always right. If your greedy produces a wrong answer on a small test case, abandon it — don't patch.",
    "variations": "- **Activity Selection / Interval Scheduling:** sort by end time, pick earliest-ending non-overlapping.\n- **Huffman coding / Connect ropes:** min-heap of two smallest.\n- **Fractional knapsack:** sort by value/weight ratio.\n- **Job scheduling with deadlines:** sort by deadline (or by profit, depending on variant).\n- **Minimum spanning tree:** Kruskal's uses edge-sorted greedy; Prim's uses heap-frontier greedy.",
    "step_by_step": "**Interval Scheduling:**\n1. Sort intervals by end time ascending.\n2. Pick the first (earliest-ending) interval.\n3. For each subsequent interval, if its start is ≥ the last picked interval's end, pick it.\n4. Skip otherwise.\n\n**Huffman merge cost:**\n1. Put all weights in a min-heap.\n2. Extract the two smallest, combine their sum, push back.\n3. Accumulate the combined sum as cost.\n4. Repeat until one element remains.",
    "visual": "**Interval scheduling on [ [1,3], [2,4], [3,5], [5,7] ]:**\n\n```\nSort by end:  [1,3] [2,4] [3,5] [5,7]\n\nPick [1,3]: accepted\n[2,4]: start 2 < 3, skip\n[3,5]: start 3 ≥ 3, accept, last end = 5\n[5,7]: start 5 ≥ 5, accept\n\nFinal kept: [1,3], [3,5], [5,7]  → 3 intervals\n```",
    "code": """```cpp
// Interval scheduling (max non-overlapping)
sort(intervals.begin(), intervals.end(),
     [](const auto& a, const auto& b) { return a[1] < b[1]; });
int lastEnd = INT_MIN, count = 0;
for (auto& iv : intervals) {
    if (iv[0] >= lastEnd) {
        count++;
        lastEnd = iv[1];
    }
}

// Huffman-style min cost to merge
priority_queue<long long, vector<long long>, greater<long long>> pq;
for (int x : weights) pq.push(x);
long long cost = 0;
while (pq.size() > 1) {
    long long a = pq.top(); pq.pop();
    long long b = pq.top(); pq.pop();
    cost += a + b;
    pq.push(a + b);
}
```""",
    "mistakes": "- **Applying greedy without proof.** It feels right, but produces wrong answers on adversarial inputs.\n- **Wrong sort key.** 'Sort by start' vs 'sort by end' drastically changes correctness for interval problems.\n- **Not handling ties.** Decide the tie-break rule explicitly.\n- **Confusing greedy with DP.** If local choices interact, you probably need DP.",
    "interview": "Greedy problems test whether you can justify your algorithm, not just state it. Interviewers want to see:\n\n1. **Can you articulate the greedy choice and why it's safe?**\n2. **Can you sketch an exchange argument for correctness?**\n3. **Can you recognize when greedy *doesn't* work and switch to DP?**\n4. **Can you pick the right sort key?**\n\nIf you ever catch yourself saying 'I think this greedy works', try one or two small adversarial cases before coding. That five-minute test saves twenty-five minutes of debugging.",
},
"1_D_and_2_D_Arrays": {
    "display": "1-D & 2-D Arrays",
    "intro": "Arrays are the most fundamental data structure — a contiguous block of memory giving you O(1) random access. Most 'array' problems are really problems in disguise: sliding window, prefix sums, two pointers, or clever indexing. Mastering arrays means mastering those patterns.",
    "analogy": "Think of a row of mailboxes. Each mailbox has an address (index) and a piece of content (value). You can walk directly to any mailbox — that's O(1) access. If you want the running total of letters in mailboxes 0 through i, you don't want to recount every time — you precompute a prefix sum, and answer any prefix query in O(1). Arrays are exactly this: addressable storage with clever precomputation on top.",
    "core": "Array problems usually reduce to one of three tools: **prefix sums** (for range sum queries), **sliding window** (for contiguous subarray constraints), or **in-place transformations** (rotate, reverse, partition). 2D arrays add row/column/diagonal traversals and 2D prefix sums. The trick is spotting which tool applies — often just rephrasing the problem in your head is enough.",
    "when_to_use": "Array techniques are useful when:\n\n- **You need range sums or aggregates** → prefix sum.\n- **You're looking at contiguous sub-segments** → sliding window or prefix sum.\n- **Input is sorted** → two pointers or binary search.\n- **You need to transform in place** → careful index manipulation.\n- **2D structure matters (rows/columns/diagonals)** → per-row/col precomputation.",
    "variations": "- **1D prefix sum:** O(1) range sum queries.\n- **2D prefix sum:** O(1) rectangular sum queries via inclusion-exclusion.\n- **Difference array:** O(1) range update, O(n) reconstruct.\n- **In-place rotation:** reverse-reverse-reverse trick for cyclic shifts.\n- **Spiral / diagonal traversals** for matrices.",
    "step_by_step": "**Prefix sum (1D):**\n1. Build `P[0] = 0`, `P[i] = P[i-1] + a[i-1]`.\n2. Query sum of `a[l..r]` = `P[r+1] - P[l]`.\n\n**2D prefix sum:**\n1. `P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j]`.\n2. Rectangle `(r1,c1)-(r2,c2)` sum = `P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1]`.\n\n**Sliding window:**\n1. Extend right pointer `r` greedily.\n2. When the window violates a constraint, advance left pointer `l`.\n3. Track the best value so far.",
    "visual": "**Prefix sum on `a = [3, 1, 4, 1, 5]`:**\n\n```\ni:  0  1  2  3  4  5\nP:  0  3  4  8  9  14\n```\n\n**Sum of a[1..3] = P[4] - P[1] = 9 - 3 = 6** (matches 1 + 4 + 1).\n\n**Sliding window on longest substring with ≤ 2 distinct chars:**\n\n```\ns = 'eceba'\n\nStep 1: l=0, r=0 → 'e'      distinct=1  best=1\nStep 2: l=0, r=1 → 'ec'     distinct=2  best=2\nStep 3: l=0, r=2 → 'ece'    distinct=2  best=3\nStep 4: l=0, r=3 → 'eceb'   distinct=3, shrink l until distinct=2 → l=2\n                  'eb'      best=3\n...\n```",
    "code": """```cpp
// 1D prefix sum
vector<int> P(n + 1, 0);
for (int i = 0; i < n; ++i) P[i+1] = P[i] + a[i];
int rangeSum = P[r+1] - P[l];

// 2D prefix sum
int n = M.size(), m = M[0].size();
vector<vector<int>> P(n+1, vector<int>(m+1, 0));
for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j)
    P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j];

// Sliding window skeleton
int l = 0, best = 0;
for (int r = 0; r < n; ++r) {
    // include a[r]
    while (/* window invalid */) {
        // exclude a[l], l++
    }
    best = max(best, r - l + 1);
}
```""",
    "mistakes": "- **Off-by-one errors** with prefix arrays. Always use size n+1 and query `P[r+1] - P[l]`.\n- **Row-major vs column-major confusion** in 2D problems.\n- **Forgetting to reset state** between multiple test cases.\n- **Mutating an array being iterated** — classic source of bugs.\n- **Integer overflow** on sums of large arrays — use `long long`.",
    "interview": "Array problems test core competence. Interviewers want to see:\n\n1. **Do you spot the pattern quickly?** Prefix sum, sliding window, or two pointers should be immediate reflexes.\n2. **Can you index without errors?** Off-by-ones cost easy points.\n3. **Can you reason about in-place vs extra-space trade-offs?**\n4. **Do you know STL helpers** (`partial_sum`, `accumulate`, `sort`)?\n\nMany interview problems that look complex reduce to a 10-line array loop once you see the pattern. Train your eye for those shapes.",
},
"Segment_Tree_Range_Queries": {
    "display": "Segment Tree / Range Queries",
    "intro": "Segment trees are the 'Swiss Army knife' of range problems. When you need to answer *range queries* (sum, min, max over a subarray) *and* support *point or range updates*, a plain prefix sum isn't enough — updates would cost O(n). Segment trees give you O(log n) for both.",
    "analogy": "Imagine a company org chart where every department reports a rolled-up number (like revenue) to its parent. If the CEO wants the total revenue of the West Coast region, he just reads the West Coast VP's roll-up — O(log n) if the hierarchy is balanced. When one salesperson updates their number, only their chain of managers needs to recompute — again O(log n). That's exactly what a segment tree does with array indices.",
    "core": "A segment tree is a balanced binary tree over array indices. Each node covers a sub-range and stores the aggregated value for that range. Queries and updates walk at most two root-to-leaf paths — O(log n) each. Lazy propagation adds deferred updates: a node can say 'all my descendants have had X applied to them' and push that down only when necessary, keeping range updates in O(log n) too.",
    "when_to_use": "Use a segment tree when:\n\n- **You need range queries AND updates on the same array.**\n- **The aggregation is associative** (sum, min, max, XOR, gcd).\n- **You need O(log n) per operation on a large array.**\n\nFor static arrays (no updates), prefer simpler tools: prefix sums for sum, sparse table for idempotent ops (min/max/gcd). For single-type updates with prefix-sum queries, a Fenwick/BIT is simpler.",
    "variations": "- **Range sum + point update.**\n- **Range min/max + point update.**\n- **Range update + point query** (via difference-array BIT or lazy segtree).\n- **Range update + range query** (lazy propagation segtree).\n- **Persistent segment tree** (versioned queries).\n- **Merge-sort tree / wavelet tree** for harder queries (k-th order statistics, range distinct).",
    "step_by_step": "**Build (recursive):**\n1. If l == r, store leaf value.\n2. Else recurse on [l, mid] and [mid+1, r], then combine.\n\n**Point update:**\n1. Recurse to the leaf corresponding to index i.\n2. Update leaf value.\n3. On the way back, recombine parents.\n\n**Range query [ql, qr]:**\n1. If current [l, r] is disjoint from [ql, qr], return identity.\n2. If current [l, r] is fully inside [ql, qr], return stored value.\n3. Otherwise, recurse on both children and combine.\n\n**Lazy propagation (range update + range query):**\n- Before recursing, push any pending update to children.\n- On full-cover updates, apply directly to the node and mark lazy; don't recurse.",
    "visual": "**Segment tree for [1, 3, 5, 7] with sum aggregation:**\n\n```\n          16  (sum of [1,3,5,7])\n         /  \\\n        4    12\n       / \\   / \\\n      1   3 5   7\n```\n\n**Query sum of [1..2] (values 3 and 5):**\n- Root [0..3]: partial overlap → recurse.\n- Left [0..1]: partial overlap → recurse. Right child [1..1] fully inside → return 3.\n- Right [2..3]: partial overlap → recurse. Left child [2..2] fully inside → return 5.\n- Combine: 3 + 5 = 8.",
    "code": """```cpp
class SegTree {
    int n;
    vector<long long> t;
    void build(int v, int l, int r, vector<int>& a) {
        if (l == r) { t[v] = a[l]; return; }
        int m = (l + r) / 2;
        build(2*v, l, m, a);
        build(2*v+1, m+1, r, a);
        t[v] = t[2*v] + t[2*v+1];
    }
    void upd(int v, int l, int r, int i, int val) {
        if (l == r) { t[v] = val; return; }
        int m = (l + r) / 2;
        if (i <= m) upd(2*v, l, m, i, val);
        else upd(2*v+1, m+1, r, i, val);
        t[v] = t[2*v] + t[2*v+1];
    }
    long long qry(int v, int l, int r, int ql, int qr) {
        if (ql > r || qr < l) return 0;
        if (ql <= l && r <= qr) return t[v];
        int m = (l + r) / 2;
        return qry(2*v, l, m, ql, qr) + qry(2*v+1, m+1, r, ql, qr);
    }
public:
    SegTree(vector<int>& a): n(a.size()) {
        t.assign(4 * n, 0);
        build(1, 0, n - 1, a);
    }
    void update(int i, int v) { upd(1, 0, n - 1, i, v); }
    long long query(int l, int r) { return qry(1, 0, n - 1, l, r); }
};
```""",
    "mistakes": "- **Allocating too small an array** — 4·n is a safe upper bound for the tree.\n- **Off-by-one in [l, r] vs [l, r)** conventions — pick one and stick to it.\n- **Forgetting to push lazy before descending.**\n- **Not handling 'no overlap' case correctly** in queries (return identity, not 0 for min queries).\n- **Recomputing parent without re-combining children** on updates.",
    "interview": "Segment tree questions test whether you can build a non-trivial data structure under time pressure. Interviewers want to see:\n\n1. **Clean recursion structure** — build, update, query.\n2. **Correct identity handling** (0 for sum, INT_MAX for min, INT_MIN for max).\n3. **Awareness of lazy propagation** for range updates.\n4. **Trade-off reasoning** — when BIT or sparse table is sufficient.\n\nIf the problem has static queries only, mention sparse table as a simpler alternative — it shows depth.",
},
"Arrays_and_Matrices": {
    "display": "Arrays & Matrices",
    "intro": "Array and matrix problems test your spatial reasoning and your ability to recognize counting patterns. Many of them have clever O(n) or O(n log n) solutions hiding behind what looks like a cubic brute force. The skill is seeing the pattern.",
    "analogy": "Think of a building with rooms arranged in a grid. If someone asks 'how many rooms with view-of-ocean exist on floors 3 through 7?', you could walk and count every room — or you could keep per-floor pre-counts and sum five numbers. The second is the prefix-sum / per-row precomputation approach.",
    "core": "Array and matrix problems often reduce to: prefix sums for range queries, sliding windows for contiguous constraints, contribution counting (asking 'how many sub-ranges include this element?'), and clever traversals (spirals, diagonals, boundaries). The matrix versions just extend 1D ideas to two axes.",
    "when_to_use": "You're in array/matrix territory when:\n\n- **You're scanning sub-ranges or sub-rectangles.**\n- **The problem involves rows, columns, diagonals, or boundaries.**\n- **You need per-element aggregated info across rows/columns.**\n- **The problem is about in-place mutation** (rotate, transpose).",
    "variations": "- **Per-row/column precomputation** (lucky numbers: row min ∩ col max).\n- **Contribution counting** (sum of all subarray ranges, trapping rain water).\n- **Boundary / spiral traversals.**\n- **2D binary search** (staircase search).\n- **In-place matrix rotation** (transpose + reverse).",
    "step_by_step": "**Trapping Rain Water (two-pointer):**\n1. Maintain two pointers l, r and running `leftMax`, `rightMax`.\n2. Move the pointer with the smaller height inward.\n3. If its current height is ≥ maxOnItsSide, update maxOnItsSide. Else add (maxOnItsSide - height) to water.\n4. Continue until l == r.\n\n**Sum of all subarray ranges via contribution:**\n1. Each element `a[i]` appears in `(i+1) * (n-i)` subarrays.\n2. Sum contribution accordingly.",
    "visual": "**Spiral traversal of a 3×3 matrix:**\n\n```\n1 → 2 → 3\n        ↓\n8 → 9   4\n↑       ↓\n7 ← 6 ← 5\n```\n\nOrder: 1, 2, 3, 4, 5, 6, 7, 8, 9 — walking the perimeter, shrinking boundaries, then continuing inward.",
    "code": """```cpp
// Trapping Rain Water (two-pointer)
int trap(vector<int>& h) {
    int l = 0, r = h.size() - 1, ml = 0, mr = 0, water = 0;
    while (l < r) {
        if (h[l] < h[r]) {
            ml = max(ml, h[l]);
            water += ml - h[l];
            l++;
        } else {
            mr = max(mr, h[r]);
            water += mr - h[r];
            r--;
        }
    }
    return water;
}

// Matrix rotation 90 CW: transpose + reverse rows
for (int i = 0; i < n; ++i)
    for (int j = i + 1; j < n; ++j) swap(M[i][j], M[j][i]);
for (auto& row : M) reverse(row.begin(), row.end());
```""",
    "mistakes": "- **Boundary errors** on spiral / diagonal traversals.\n- **Integer overflow** when summing large matrices.\n- **Forgetting to reset shared state** across test cases.\n- **In-place transforms that corrupt unvisited cells** — use a marker or a buffer.",
    "interview": "Array/matrix problems favor candidates who think visually. Interviewers want to see:\n\n1. **A small diagram sketched to clarify indices.**\n2. **Recognition of the underlying pattern** (prefix sum, sliding window, contribution).\n3. **Careful index handling** without buggy off-by-ones.\n4. **In-place vs extra-space trade-offs.**\n\nDraw the first few iterations on paper if allowed. It's the fastest way to catch your own bugs.",
},
"Searching_Binary_Search": {
    "display": "Searching / Binary Search",
    "intro": "Binary search is one of the most elegant algorithms in CS — halving the search space each step, turning O(n) into O(log n). But classic binary search on sorted arrays is just the tip of the iceberg. The real power is **binary search on the answer**: reframe any problem where the answer space is monotonic, and binary search it.",
    "analogy": "You're guessing a number between 1 and 100. Every time you guess, you're told 'higher' or 'lower'. Do you scan 1, 2, 3, ...? No — you guess 50, then 25 or 75, then halve again. That's binary search. The same intuition applies to algorithms: if you can efficiently check 'is answer X feasible?' with a monotonic predicate, binary search the answer.",
    "core": "Binary search works on a **monotonic predicate**: `ok(x)` is false for all x < T and true for all x ≥ T (or vice versa). The search finds the boundary T in O(log range) feasibility checks. For sorted arrays, the predicate is 'is a[mid] ≥ target?'. For 'binary search on answer' problems, the predicate is problem-specific (capacity works? days enough?).",
    "when_to_use": "Look for binary search when:\n\n- **Input is sorted** (classic).\n- **The answer space is numeric and monotonic** ('if X works, so does X+1').\n- **Brute-force over the answer would be O(n·range)** and the range is huge.\n- **Keywords:** 'minimum capacity', 'maximum rate', 'fewest days'.",
    "variations": "- **Classic binary search** for exact match.\n- **Lower bound** — first index ≥ target.\n- **Upper bound** — first index > target.\n- **Binary search on answer** — search a numeric range with a feasibility function.\n- **Binary search on a function** — find where f(x) crosses zero.\n- **Exponential search** for unbounded arrays (double until overshoot, then binary search).",
    "step_by_step": "**Classic search for target:**\n1. lo = 0, hi = n - 1.\n2. While lo ≤ hi: m = (lo + hi) / 2.\n3. If a[m] == target, return m.\n4. If a[m] < target, lo = m + 1.\n5. Else hi = m - 1.\n6. Return -1 (not found).\n\n**Binary search on answer (smallest X such that ok(X)):**\n1. Pick lo and hi as the valid range of answers.\n2. While lo < hi: m = (lo + hi) / 2.\n3. If ok(m), hi = m.\n4. Else lo = m + 1.\n5. Return lo.",
    "visual": "**Binary search for 7 in [1, 3, 5, 7, 9, 11]:**\n\n```\n[1, 3, 5, 7, 9, 11]\n        ↑ mid=5, 5 < 7, go right\n\n         [7, 9, 11]\n              ↑ mid=9, 9 > 7, go left\n\n         [7]\n          ↑ found!\n```",
    "code": """```cpp
// Classic binary search
int binary_search(vector<int>& a, int target) {
    int lo = 0, hi = a.size() - 1;
    while (lo <= hi) {
        int m = lo + (hi - lo) / 2;
        if (a[m] == target) return m;
        if (a[m] < target) lo = m + 1;
        else hi = m - 1;
    }
    return -1;
}

// Binary search on answer: smallest capacity so that ok(cap) is true
int lo = maxPackage, hi = totalSum;
while (lo < hi) {
    int m = lo + (hi - lo) / 2;
    if (ok(m)) hi = m;
    else lo = m + 1;
}
return lo;
```""",
    "mistakes": "- **Overflow in `(lo + hi) / 2`** for large ints — use `lo + (hi - lo) / 2`.\n- **Off-by-one** in `while (lo < hi)` vs `while (lo <= hi)`.\n- **Wrong branch update** causing infinite loops.\n- **Misidentifying the monotonic predicate** — test it on 2–3 small cases.\n- **Assuming sortedness that isn't there.**",
    "interview": "Binary search problems test precision. Interviewers want to see:\n\n1. **Clean invariants** — state clearly what `lo` and `hi` mean.\n2. **Correct boundary updates.**\n3. **Recognition of 'binary search on answer'** for non-sorted-array problems.\n4. **Awareness of overflow** and edge cases.\n\nAlways verify your binary search on the *smallest* possible input (size 0, 1, 2) — that's where off-by-one errors live.",
},
"Two_Pointers": {
    "display": "Two Pointers",
    "intro": "Two-pointer techniques exploit order or monotonic structure to collapse nested loops into a single pass. Whenever data is sorted or a constraint advances monotonically, two pointers turn O(n²) brute force into O(n).",
    "analogy": "Imagine you have two readers starting at opposite ends of a sorted book and they need to find two pages whose numbers sum to a target. One reader stays slightly ahead or behind based on feedback — they never backtrack, never cross the same territory twice. That's two pointers.",
    "core": "The technique comes in two main flavors. **Opposite-end pointers** start at the two ends and move toward each other — used for pair-sum problems on sorted arrays and palindrome checks. **Same-direction pointers** (sliding window or fast/slow) both move forward but at different rates — used for window-based problems and cycle detection in linked lists.",
    "when_to_use": "Look for two pointers when:\n\n- **Input is sorted and you want pairs/triplets with some sum property.**\n- **Contiguous subarray with a monotonic constraint** (sliding window).\n- **Palindrome or mirror checks.**\n- **Linked-list cycle or middle finding** (fast/slow).\n- **Merge-like operations** (merging sorted arrays, intersection).",
    "variations": "- **Opposite-end pointers:** two-sum on sorted, container with most water, valid palindrome.\n- **Same-direction / sliding window:** longest substring without repeats, min window substring.\n- **Fast/slow:** cycle detection, middle of linked list.\n- **Three pointers:** Dutch national flag partition.",
    "step_by_step": "**Two-sum on sorted array:**\n1. l = 0, r = n-1.\n2. While l < r: s = a[l] + a[r].\n3. If s == target → return {l, r}.\n4. If s < target → l++ (need larger sum).\n5. Else → r-- (need smaller sum).\n\n**Floyd's tortoise-hare cycle:**\n1. slow = fast = head.\n2. Advance slow by 1 step, fast by 2 steps.\n3. If they meet → cycle exists.\n4. If fast reaches null → no cycle.",
    "visual": "**Two-sum on `[2, 7, 11, 15]`, target `18`:**\n\n```\nl=0, r=3: 2 + 15 = 17 < 18  → l++\nl=1, r=3: 7 + 15 = 22 > 18  → r--\nl=1, r=2: 7 + 11 = 18 ✓    → return {1, 2}\n```",
    "code": """```cpp
// Two-sum on sorted array
vector<int> twoSumSorted(vector<int>& a, int t) {
    int l = 0, r = a.size() - 1;
    while (l < r) {
        int s = a[l] + a[r];
        if (s == t) return {l, r};
        if (s < t) l++;
        else r--;
    }
    return {};
}

// Fast/slow cycle detection
bool hasCycle(ListNode* head) {
    auto s = head, f = head;
    while (f && f->next) {
        s = s->next;
        f = f->next->next;
        if (s == f) return true;
    }
    return false;
}

// Sliding window skeleton
int l = 0, best = 0;
for (int r = 0; r < n; ++r) {
    // extend with a[r]
    while (/* invalid */) {
        // shrink with a[l], l++
    }
    best = max(best, r - l + 1);
}
```""",
    "mistakes": "- **Moving the wrong pointer** when sums are equal.\n- **Forgetting duplicate handling** in 3Sum-style problems.\n- **Applying two pointers on unsorted data** without preprocessing.\n- **Infinite loop** from not advancing a pointer on boundary cases.",
    "interview": "Two-pointer problems reward a clean, precise style. Interviewers want to see:\n\n1. **Clear invariants** — what does `l` and `r` represent?\n2. **Correct pointer updates** in all branches.\n3. **Handling ties and duplicates.**\n4. **Ability to shift from nested loops to two pointers when possible.**\n\nBefore coding, trace the pointer movement on a 5–6 element example. You'll catch boundary bugs before they bite.",
},
"Linked_List": {
    "display": "Linked List",
    "intro": "Linked lists are deceptively simple — a chain of nodes with pointers — but their problems are beloved by interviewers because they demand precise pointer handling without the safety net of random access. Master them and you've mastered pointer thinking.",
    "analogy": "Imagine a treasure hunt where each clue points to the next location. You can only find the 5th clue by reading the first four in sequence — no shortcut. That's a linked list: each node holds a piece of data and a pointer to the next, and you always start from the head.",
    "core": "A linked list is a sequence of nodes, each holding a value and a pointer to the next. Operations are O(n) for random access but O(1) for insertion and deletion at a known position. Most linked-list problems revolve around pointer manipulation: reversing, merging, finding middle/end, detecting cycles. A **dummy head node** is a common technique to simplify edge cases.",
    "when_to_use": "Reach for linked-list thinking when:\n\n- **Dynamic sizing is needed** with frequent inserts/deletes.\n- **Random access isn't required.**\n- **The problem explicitly gives a linked list.**\n- **Memory fragmentation is a concern** (though rare in interviews).",
    "variations": "- **Singly linked list:** one `next` pointer per node.\n- **Doubly linked list:** `next` and `prev` pointers, enabling backward traversal.\n- **Circular linked list:** tail links back to head.\n- **Skip list:** hierarchical linked list with O(log n) search, used by Redis.",
    "step_by_step": "**Reverse a singly linked list:**\n1. prev = null, cur = head.\n2. While cur:\n   - Save `next = cur.next`.\n   - `cur.next = prev`.\n   - `prev = cur; cur = next`.\n3. Return `prev` as the new head.\n\n**Find the middle (Floyd):**\n1. slow = fast = head.\n2. While fast and fast.next: slow = slow.next; fast = fast.next.next.\n3. Return slow.\n\n**Detect cycle (Floyd):**\n1. Same as middle-finding.\n2. If slow == fast at any point, cycle exists.",
    "visual": "**Reversing `1 → 2 → 3 → null`:**\n\n```\nStart:  prev=null,  cur=1,  [1 → 2 → 3]\nStep 1: prev=1,     cur=2,  [1] [2 → 3]   (1 now points to null)\nStep 2: prev=2,     cur=3,  [2 → 1] [3]\nStep 3: prev=3,     cur=null, [3 → 2 → 1]\nReturn prev → head of reversed list = 3\n```",
    "code": """```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x): val(x), next(nullptr) {}
};

// Reverse
ListNode* reverse(ListNode* head) {
    ListNode* prev = nullptr;
    while (head) {
        auto* next = head->next;
        head->next = prev;
        prev = head;
        head = next;
    }
    return prev;
}

// Middle (Floyd)
ListNode* middle(ListNode* head) {
    auto s = head, f = head;
    while (f && f->next) {
        s = s->next;
        f = f->next->next;
    }
    return s;
}

// Merge two sorted lists (dummy-head pattern)
ListNode* merge(ListNode* a, ListNode* b) {
    ListNode dummy(0);
    auto* t = &dummy;
    while (a && b) {
        if (a->val <= b->val) { t->next = a; a = a->next; }
        else { t->next = b; b = b->next; }
        t = t->next;
    }
    t->next = a ? a : b;
    return dummy.next;
}
```""",
    "mistakes": "- **Losing the head pointer** by overwriting it.\n- **Null dereference** — always null-check before `.next`.\n- **Missing the dummy head trick** — it simplifies insert/delete at the head.\n- **Forgetting to null-terminate** after rewiring — leads to cycles.\n- **Stack overflow on recursive solutions** — use iterative when lists are long.",
    "interview": "Linked-list questions test pointer precision. Interviewers want to see:\n\n1. **Clean use of a dummy head** when appropriate.\n2. **Careful pointer rewiring** without cycles or lost nodes.\n3. **Slow/fast pointer recognition** for cycle and middle problems.\n4. **Edge cases:** empty list, single node, exactly two nodes.\n\nDraw the pointer diagram before coding. It's the single best way to avoid bugs.",
},
"Number_Theory_Misc": {
    "display": "Number Theory / Misc",
    "intro": "Number theory problems are elegance in disguise. An O(n) brute force often hides an O(1) formula, an O(n²) check often hides an O(log n) trick. The skill is recognizing the structure quickly — digit patterns, divisibility, modular arithmetic — before racing to code.",
    "analogy": "Think of a lock with a specific combination pattern (every third digit must be even, say). A brute-force solver tries every combination. A pattern-recognizer enumerates only the valid ones — maybe 1/10th the work. Number theory gives us the tools to identify those patterns and skip ahead.",
    "core": "The core tools are: modular arithmetic (closure, inverse), prime factorization (trial division up to √n), the Euclidean algorithm (GCD/LCM), digit decomposition (% 10 / divide by 10), and digit-DP for counting-over-ranges problems. Most 'miscellaneous' problems combine two of these tools.",
    "when_to_use": "Signals for number theory:\n\n- **Digits of a number are involved.**\n- **Primes, factors, divisors are mentioned.**\n- **Constraints are gigantic (10^9+)** — formula required.\n- **Counts modulo a prime.**\n- **Periodicity or parity shows up.**",
    "variations": "- **Sieve of Eratosthenes** for listing primes up to N.\n- **Fast exponentiation** for a^b mod m in O(log b).\n- **Euler's totient** for counting integers coprime to n.\n- **Digit DP** for counting numbers in [L, R] with some digit property.\n- **Chinese Remainder Theorem** for systems of congruences.",
    "step_by_step": "**Digit sum / digital root:**\n1. Observation: 10 ≡ 1 (mod 9), so digit sum ≡ n (mod 9).\n2. Therefore digital root = 1 + (n-1) mod 9 for n ≥ 1.\n\n**Sieve:**\n1. Mark 0 and 1 as non-prime.\n2. For i = 2 to √n: if i is prime, mark i·i, i·i+i, ... as composite.\n3. Remaining unmarked indices are prime.",
    "visual": "**Sieve up to 10:**\n\n```\nInit: 2 3 4 5 6 7 8 9 10  (all candidate)\ni=2 (prime): cross out 4, 6, 8, 10\nRemaining: 2 3 5 7 9\ni=3 (prime): cross out 9\nRemaining: 2 3 5 7\n\n√10 ≈ 3.16, stop.\n\nPrimes ≤ 10: 2, 3, 5, 7.\n```",
    "code": """```cpp
// Sieve
vector<bool> sieve(int n) {
    vector<bool> p(n + 1, true);
    p[0] = p[1] = false;
    for (int i = 2; (long long)i * i <= n; ++i) if (p[i])
        for (int j = i * i; j <= n; j += i) p[j] = false;
    return p;
}

// Divisor count via factorization
int divisorCount(int n) {
    int ans = 1;
    for (int p = 2; (long long)p * p <= n; ++p) {
        if (n % p) continue;
        int e = 0;
        while (n % p == 0) { n /= p; e++; }
        ans *= (e + 1);
    }
    if (n > 1) ans *= 2;
    return ans;
}
```""",
    "mistakes": "- **Integer overflow** on products of large numbers.\n- **Negative modulo** — always `((x % m) + m) % m`.\n- **Forgetting that 1 is not prime.**\n- **Sieving without `i * i` optimization** — doubles runtime.\n- **Confusing GCD and LCM formulas.**",
    "interview": "Number theory problems test structural observation. Interviewers want to see:\n\n1. **You pause to find a formula before coding.**\n2. **You can explain *why* the formula works.**\n3. **You handle edge cases** (0, 1, negatives).\n4. **You're aware of overflow.**\n\nIf n ≤ 10^6, a sieve is probably fine. If n ≤ 10^9, you need a formula or a per-query O(√n). If n ≤ 10^18, only O(log n) or O(1) survives.",
},
"Trie_Bit_Manipulation_Trie": {
    "display": "Trie / Bit Manipulation Trie",
    "intro": "A trie is a tree where each path from the root spells out a string (or a bit sequence). It's the Swiss Army knife of prefix-based problems: dictionary lookups, autocomplete, word-filter, and — with bits — maximum XOR queries. Tries share prefixes, so they're memory-efficient for structured data.",
    "analogy": "Imagine a library organized not by full book title, but by nested drawers: the top drawer contains books starting with 'A', inside which another drawer for 'AP', inside another for 'APP'. To find 'APPLE' you navigate five drawers. To find all books starting with 'APP' you just look inside that one drawer. That's a trie.",
    "core": "Each trie node has a child for each possible next character (or bit). Insert walks down the tree, creating missing nodes. Search walks down, failing at a missing child. For XOR tries, each node has two children (0 and 1). To maximize XOR with a query number, at each bit level greedily pick the opposite-bit child — if available, that bit contributes to the XOR.",
    "when_to_use": "Reach for a trie when:\n\n- **You need prefix-based queries** (autocomplete, 'all words starting with X').\n- **Dictionary membership with many lookups.**\n- **Max XOR of a number with others** → bit trie.\n- **Word filter with prefix + suffix** → combined-key trie.",
    "variations": "- **Character trie** for strings over an alphabet.\n- **Bit trie** for integers (often 30 or 32 bits).\n- **Compressed / Patricia trie** for sparse tries.\n- **Suffix trie** for substring queries (related: suffix tree).",
    "step_by_step": "**Insert word:**\n1. Start at root.\n2. For each char c, go to `root.children[c]`; if missing, create it.\n3. At the end, mark the node as `end = true`.\n\n**Search word:**\n1. Start at root.\n2. For each char c, go to `root.children[c]`; if missing, return false.\n3. Return `node.end`.\n\n**Max XOR with x (bit trie):**\n1. Start at root.\n2. For each bit b from MSB to LSB:\n   - Compute desired bit = 1 - (x's bit at b).\n   - If child[desired] exists, go there and set bit b in the XOR value.\n   - Else go to child[other].",
    "visual": "**Trie after inserting 'app', 'apple', 'bat':**\n\n```\n            root\n           /    \\\n          a      b\n          |      |\n          p      a\n          |      |\n          p*     t*\n          |\n          l\n          |\n          e*\n```\n\n`*` marks end-of-word. 'app' and 'apple' share the prefix 'app'.",
    "code": """```cpp
struct TrieNode {
    TrieNode* children[26] = {};
    bool end = false;
};

class Trie {
    TrieNode* root = new TrieNode();
public:
    void insert(const string& w) {
        auto* n = root;
        for (char c : w) {
            int idx = c - 'a';
            if (!n->children[idx]) n->children[idx] = new TrieNode();
            n = n->children[idx];
        }
        n->end = true;
    }
    bool search(const string& w) {
        auto* n = root;
        for (char c : w) {
            n = n->children[c - 'a'];
            if (!n) return false;
        }
        return n->end;
    }
    bool startsWith(const string& p) {
        auto* n = root;
        for (char c : p) {
            n = n->children[c - 'a'];
            if (!n) return false;
        }
        return true;
    }
};
```""",
    "mistakes": "- **Memory blowup** with large alphabets — consider unordered_map children.\n- **Forgetting the end marker** — causes false positives in `search`.\n- **Deleting nodes incorrectly** — reference counts / marker flags help.\n- **Confusing `search` vs `startsWith`** — they differ by the end marker.",
    "interview": "Trie problems test whether you can build a non-trivial data structure on the fly. Interviewers want to see:\n\n1. **Clean node structure.**\n2. **Correct end-marker handling.**\n3. **Prefix queries in linear-in-length time.**\n4. **For XOR problems: greedy opposite-bit traversal.**\n\nTip: always diagram your trie state after 2–3 insertions. That cements correctness before you code the tricky operations.",
},
"Dynamic_Programming_DP": {
    "display": "Dynamic Programming (DP)",
    "intro": "Dynamic programming is the art of trading time for memory: you identify overlapping subproblems in a recursion and remember their answers so you don't re-solve them. The hard part is almost never the memo — it's identifying the right **state** (what uniquely defines a subproblem).",
    "analogy": "Imagine you're climbing stairs and someone asks 'how many ways to reach step n?'. You'd quickly realize: ways to reach n = ways to reach n-1 (take 1 step) + ways to reach n-2 (take 2 steps). That's the recurrence. But if you compute it naively, you'll compute ways-to-reach-5 many times as you compute ways-to-reach-10. DP is just writing them down as you go.",
    "core": "DP has three ingredients: (1) **state** — the parameters that describe a subproblem, (2) **transition** — the recurrence that expresses a state in terms of smaller states, (3) **base cases** — the atomic subproblems you solve directly. Top-down DP (memoization) writes recursion with a cache; bottom-up DP (tabulation) fills an array in dependency order. Space optimization replaces full tables with rolling windows when only the last 1 or 2 rows matter.",
    "when_to_use": "Classic signals for DP:\n\n- **Overlapping subproblems** in a recursive formulation.\n- **Optimal substructure** — optimal solution composed of optimal sub-solutions.\n- **'Count the number of ways'** — almost always DP.\n- **'Find the minimum/maximum cost / length'** with choices at each step.\n- **State can be captured in a small number of parameters** (index, remaining capacity, last choice, etc.).",
    "variations": "- **1D DP** (Climbing Stairs, LIS, Kadane).\n- **2D DP** (LCS, Edit Distance, Interleaving).\n- **Knapsack** (0/1, unbounded, bounded).\n- **Interval DP** (Matrix Chain, Palindrome Partitioning).\n- **Tree DP** (subtree computations).\n- **Bitmask DP** (TSP-like when n ≤ ~20).\n- **Digit DP** (count numbers in range with digit property).",
    "step_by_step": "**General DP recipe:**\n1. **Identify state.** What parameters uniquely determine the subproblem?\n2. **Write the recurrence.** How does the answer for a state depend on smaller states?\n3. **Specify base cases.** What are the atomic answers?\n4. **Pick top-down or bottom-up.** Top-down is easier to write; bottom-up is often faster due to no call overhead.\n5. **Consider space optimization.** Often only the last few rows matter.",
    "visual": "**LCS of `s = 'abc'` and `t = 'ac'`:**\n\n```\n      \"\"  a  c\n\"\" |  0  0  0\na  |  0  1  1\nb  |  0  1  1\nc  |  0  1  2\n```\n\nEach cell dp[i][j] = LCS of first i chars of s and first j chars of t. Cell dp[3][2] = 2 → LCS 'ac'.",
    "code": """```cpp
// Memoized recursion (top-down)
int memo[MAXN];
int solve(int i) {
    if (i <= 1) return 1;
    if (memo[i] != -1) return memo[i];
    return memo[i] = solve(i-1) + solve(i-2);
}

// Tabulation (bottom-up) with space optimization
int climbStairs(int n) {
    int a = 1, b = 1;
    for (int i = 2; i <= n; ++i) {
        int c = a + b;
        a = b; b = c;
    }
    return b;
}

// Classic 2D DP (LCS)
int lcs(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));
    for (int i = 1; i <= n; ++i) for (int j = 1; j <= m; ++j)
        dp[i][j] = (s[i-1] == t[j-1]) ? dp[i-1][j-1] + 1
                                      : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][m];
}
```""",
    "mistakes": "- **Wrong state definition** — missing a dimension (e.g., needing 'last char used').\n- **Off-by-one in base cases.**\n- **Iteration order** must respect dependencies in bottom-up.\n- **Forgetting to initialize memo.**\n- **Overflow in counting DPs** — use long long or mod.",
    "interview": "DP interviews test state-thinking. Interviewers want to see:\n\n1. **You articulate the state clearly** before coding.\n2. **You write a clean recurrence.**\n3. **You handle base cases explicitly.**\n4. **You analyze time and space correctly.**\n5. **You can convert top-down to bottom-up if asked.**\n\nThe most common mistake under pressure is trying to code before defining state. Resist. Spend the first minutes on 'what parameters describe a subproblem?' That's the single highest-leverage moment in the interview.",
},
"Bit_Manipulation": {
    "display": "Bit Manipulation",
    "intro": "Bit manipulation is the closest most of us get to talking directly to hardware. A handful of operators — AND, OR, XOR, NOT, and shifts — unlock elegant O(1) or O(log n) solutions for problems that look much harder at first glance.",
    "analogy": "Think of bits as a row of light switches. AND turns off all lights that aren't on in both rows; OR turns on all lights that are on in either row; XOR flips lights that differ between rows. These basic operations compose into rich tricks — like 'flip only the lights that were off before' or 'count the lit bulbs'.",
    "core": "The essential tools: AND (`&`) masks, OR (`|`) sets, XOR (`^`) toggles, NOT (`~`) inverts, and shifts (`<<`, `>>`) scale by powers of two. Two particularly powerful tricks: `n & (n-1)` clears the lowest set bit (useful for popcount), and `n & -n` isolates the lowest set bit (useful for binary indexed trees).",
    "when_to_use": "Bit manipulation shines when:\n\n- **XOR elegantly handles 'paired' data** (find the lone non-duplicate).\n- **Sets of size ≤ 32 can be represented as bitmasks.**\n- **Powers of two** are central to the problem.\n- **Bit tricks provide constant-factor speedups.**\n\nIf n ≤ 20, bitmask DP is often feasible (2^20 ≈ 10^6 states).",
    "variations": "- **Basic tricks** (popcount, isolate low bit, toggle bit).\n- **Bitmask DP** for subset problems.\n- **Bit trie** for max XOR.\n- **Hamming weight / distance** computations.\n- **SWAR (SIMD within a register)** for parallel bit tricks.",
    "step_by_step": "**Popcount via Brian Kernighan:**\n1. cnt = 0.\n2. While n != 0: n &= n-1; cnt++.\n3. Return cnt.\n\n**Iterate over all subsets of a mask:**\n1. sub = mask.\n2. While sub != 0: process sub; sub = (sub - 1) & mask.\n3. Process the empty subset separately if needed.",
    "visual": "**`n & (n-1)` strips the lowest set bit:**\n\n```\nn    = 10110100\nn-1  = 10110011\nAND  = 10110000   ← lowest '1' cleared\n```\n\n**XOR cancels pairs in `[4, 1, 2, 1, 2]`:**\n\n```\n0 ^ 4 = 4\n4 ^ 1 = 5\n5 ^ 2 = 7\n7 ^ 1 = 6\n6 ^ 2 = 4\n```\n\nOnly the lone `4` survives.",
    "code": """```cpp
// Popcount\nint popcount(int n) {\n    int c = 0;\n    while (n) { n &= (n - 1); c++; }\n    return c;\n}\n\n// Check if power of two\nbool isPow2(int n) { return n > 0 && (n & (n - 1)) == 0; }\n\n// Iterate over subsets of mask\nfor (int sub = mask; sub; sub = (sub - 1) & mask) { /* process sub */ }\n// Don't forget the empty subset\n\n// Set, clear, toggle, test bit b\nn |= (1 << b);\nn &= ~(1 << b);\nn ^= (1 << b);\nbool on = n & (1 << b);
```""",
    "mistakes": "- **Signed right shift** on negatives — use unsigned types.\n- **Shifting by ≥ bit width** is undefined behavior.\n- **Forgetting operator precedence** — always parenthesize bit ops in comparisons.\n- **Assuming 32-bit** when values can exceed 2^31 — use `long long`.",
    "interview": "Bit manipulation questions test sharpness. Interviewers want to see:\n\n1. **Quick recall of tricks** like popcount and subset iteration.\n2. **Clear reasoning** about what each bit represents.\n3. **Parenthesization and overflow awareness.**\n\nKnowing `__builtin_popcount` and `__builtin_ctz` saves time; knowing how to implement them from scratch shows depth.",
},
"Hashing_Sliding_Window": {
    "display": "Hashing / Sliding Window",
    "intro": "Two of the most versatile algorithmic patterns combined. Hashing gives O(1) membership and counting; sliding window maintains a dynamic range with monotonic bounds. Together, they solve a huge slice of interview problems that at first look O(n²) or worse.",
    "analogy": "Think of a moving window of seats on a train. As you walk from car 1 to car n, the window slides with you. You want to know 'how many unique passengers are currently visible?' — a hash map (passenger → count) tracks that in O(1) per step. When a passenger moves out of the window, decrement; when a new one appears, increment. That's sliding window + hashing.",
    "core": "Hash maps / sets give O(1) average insert, lookup, and delete. Sliding windows maintain two pointers `l` and `r` that advance forward. At each `r`, we extend the window with `a[r]`; when the window violates our invariant, we shrink from the left. Combined: a hash map tracks per-window statistics, and the window slides with monotonic l and r.",
    "when_to_use": "Signals for hashing or sliding window:\n\n- **'Subarray with sum equals k'** → prefix-sum + hashmap.\n- **'Longest substring with at most k distinct chars'** → sliding window.\n- **'Find duplicates / anagrams'** → hash counting.\n- **'Count pairs with some property'** → hashmap pass.",
    "variations": "- **Prefix-sum + hashmap** for subarray-sum problems.\n- **Two-pointer sliding window** with invariant.\n- **Fixed-size window** (average over k consecutive).\n- **Hash set for membership**, hash map for counting.\n- **Rolling hash** for string substring matching (Rabin-Karp).",
    "step_by_step": "**Subarray sum equals k (hashing):**\n1. map[0] = 1 (empty prefix).\n2. Run sum as you scan.\n3. At each step, `ans += map[sum - k]` counts subarrays ending here with sum k.\n4. Increment map[sum].\n\n**Longest substring without repeating chars (sliding window):**\n1. l = 0, best = 0.\n2. For each r, if `s[r]` was seen at index ≥ l, move l to `last[s[r]] + 1`.\n3. Update `last[s[r]] = r`.\n4. Track `best = max(best, r - l + 1)`.",
    "visual": "**Sliding window for 'abcabcbb' (longest unique substring):**\n\n```\nl=0, r=0: 'a'     best=1\nl=0, r=1: 'ab'    best=2\nl=0, r=2: 'abc'   best=3\nl=0, r=3: 'abca' → 'a' already in window, l→1, 'bca' best=3\nl=1, r=4: 'bcab' → 'b' repeat, l→2, 'cab'  best=3\n...\n```",
    "code": """```cpp
// Subarray sum equals k
int subarraySum(vector<int>& a, int k) {\n    unordered_map<int,int> m; m[0] = 1;\n    int sum = 0, ans = 0;\n    for (int x : a) {\n        sum += x;\n        ans += m[sum - k];\n        m[sum]++;\n    }\n    return ans;\n}\n\n// Longest substring without repeats\nint lengthOfLongestSubstring(string s) {\n    vector<int> last(256, -1);\n    int l = 0, best = 0;\n    for (int r = 0; r < (int)s.size(); ++r) {\n        if (last[s[r]] >= l) l = last[s[r]] + 1;\n        last[s[r]] = r;\n        best = max(best, r - l + 1);\n    }\n    return best;\n}
```""",
    "mistakes": "- **Forgetting `map[0] = 1`** for prefix-sum counting.\n- **Not removing stale entries** as the window shrinks.\n- **Using hash maps where arrays suffice** (slower).\n- **Iterating and mutating the map** simultaneously.",
    "interview": "Hashing/sliding window questions reward clean pattern recognition. Interviewers want to see:\n\n1. **Quick identification of the pattern.**\n2. **Clean window invariants.**\n3. **Correct update/shrink logic.**\n4. **Awareness of O(1) vs O(n) map ops.**\n\nMemorize the two templates — prefix-sum + hashmap and sliding window — and 30% of array problems become routine.",
},
"Queues_Deque_Monotonic_Queue": {
    "display": "Queues / Deque / Monotonic Queue",
    "intro": "Queues give us FIFO (first-in-first-out) access. Deques generalize to both ends. Monotonic deques add a twist: they only keep 'useful' candidates, giving us sliding window max/min in O(n).",
    "analogy": "Think of a line at a grocery counter. A queue: first in, first out. A deque: customers can join or leave from either end. A monotonic queue: a 'VIP line' where, as a VIP joins, any less-senior customer ahead of them is kicked out — so the line is always ordered by priority. That selectivity is what makes monotonic deques efficient.",
    "core": "A queue (FIFO) has O(1) push-back and pop-front. A deque (double-ended queue) has O(1) at both ends. A monotonic deque maintains elements in increasing or decreasing order: when inserting, pop everything that violates the order. Each element is inserted and popped once, giving amortized O(1) per operation and O(n) total for a pass over the array.",
    "when_to_use": "Reach for queues/deques when:\n\n- **BFS** — always a queue.\n- **Sliding window max/min in O(n)** — monotonic deque.\n- **Implementing queue via stacks or vice versa** — classic interview.\n- **Tasks arriving with priorities** — priority_queue (heap) rather than plain queue.",
    "variations": "- **Plain queue / deque** for BFS and general FIFO.\n- **Monotonic increasing deque** for min queries.\n- **Monotonic decreasing deque** for max queries.\n- **Priority queue** (heap) when priority matters more than insertion order.",
    "step_by_step": "**Sliding window maximum (decreasing deque):**\n1. For each index i:\n   - Remove front if it's out of the window (index ≤ i - k).\n   - Remove back while `a[back] ≤ a[i]` (they can never be the max).\n   - Push i to the back.\n   - If i ≥ k - 1, the max for this window is `a[dq.front()]`.",
    "visual": "**Sliding window max for [1, 3, -1, -3, 5, 3, 6, 7], k=3:**\n\n```\ni=0, a[i]=1: dq=[0]\ni=1, a[i]=3: pop 0 (a[0]=1<3), push 1; dq=[1]\ni=2, a[i]=-1: push 2; dq=[1,2]  window max=3\ni=3, a[i]=-3: push 3; dq=[1,2,3] window max=3\ni=4, a[i]=5: pop 3,2,1 (all ≤5), push 4; dq=[4] window max=5\n...\n\nFinal maxes: [3, 3, 5, 5, 6, 7]\n```",
    "code": """```cpp
// BFS template
queue<int> q; q.push(src);
vector<int> dist(n, -1); dist[src] = 0;
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : g[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        q.push(v);
    }
}

// Sliding window maximum (monotonic decreasing deque)
vector<int> maxSlidingWindow(vector<int>& a, int k) {
    deque<int> dq; vector<int> res;
    for (int i = 0; i < (int)a.size(); ++i) {
        if (!dq.empty() && dq.front() <= i - k) dq.pop_front();
        while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();
        dq.push_back(i);
        if (i >= k - 1) res.push_back(a[dq.front()]);
    }
    return res;
}
```""",
    "mistakes": "- **Storing values instead of indices** in monotonic deques — losing the position info.\n- **Wrong pop direction** for min vs max queues.\n- **Using queue when deque is needed.**\n- **Off-by-one in window bounds.**",
    "interview": "Queue/deque problems test whether you can design the right container for the job. Interviewers want to see:\n\n1. **Recognition of monotonic-deque patterns** for O(n) sliding-window queries.\n2. **Clean amortized analysis** (each element in/out once).\n3. **Clear differentiation** between queue, deque, and priority queue.",
},
"Stack": {
    "display": "Stack",
    "intro": "Stacks give LIFO (last-in-first-out) access. They shine in problems with nested structure (parentheses, expression evaluation) and in 'next greater / previous smaller' sweeps via **monotonic stacks** — a pattern that appears in dozens of interview favorites.",
    "analogy": "Think of a stack of trays in a cafeteria. The last tray placed is the first one taken. You can only access the top. That LIFO discipline turns out to be perfect for matching brackets, evaluating expressions, and resolving 'find the next bigger thing' questions.",
    "core": "A stack supports push, pop, and peek in O(1). A **monotonic stack** additionally maintains a sorted order: when inserting, pop elements that violate the order first. This technique resolves 'next greater element', 'previous smaller', and 'largest rectangle in histogram' in a single linear pass.",
    "when_to_use": "Signals for stacks:\n\n- **Nested or matching structure** (parentheses, HTML tags).\n- **Expression evaluation** (RPN, infix → postfix).\n- **'Next/previous greater/smaller'** → monotonic stack.\n- **'Largest rectangle in histogram'** → monotonic stack.\n- **Simulating recursion iteratively.**",
    "variations": "- **Plain stack** for matching/parsing.\n- **Monotonic increasing stack** (finds next smaller).\n- **Monotonic decreasing stack** (finds next greater).\n- **Two-stack approaches** (min stack, stack-queue simulation).",
    "step_by_step": "**Next greater element (monotonic decreasing stack):**\n1. Iterate i from 0 to n-1.\n2. While stack is non-empty and `a[stack.top()] < a[i]`: pop and record `answer[top] = a[i]`.\n3. Push i.\n4. After iteration, remaining stack elements have no next greater (answer = -1).\n\n**Largest rectangle in histogram:**\n1. Walk through bars; maintain an increasing-height stack of indices.\n2. When a new bar is shorter, pop: for each popped bar, its rectangle's width is (current - stack.top() - 1).\n3. Track the max area.",
    "visual": "**Next greater element in [2, 1, 2, 4, 3]:**\n\n```\ni=0: stack=[0]  ([2])\ni=1: a[1]=1 < a[0]=2, push; stack=[0,1]  ([2,1])\ni=2: a[2]=2, pop 1 (a[1]=1<2): answer[1]=2\n     a[2]=2 == a[0]=2, push; stack=[0,2]  ([2,2])\ni=3: a[3]=4, pop 2 (2<4): answer[2]=4\n     pop 0 (2<4): answer[0]=4\n     push; stack=[3]  ([4])\ni=4: a[4]=3<4, push; stack=[3,4]  ([4,3])\n\nRemaining: 3 and 4 have no next greater → answer = -1\nFinal: [4, 2, 4, -1, -1]\n```",
    "code": """```cpp
// Valid parentheses
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') st.push(c);
        else {
            if (st.empty()) return false;
            char t = st.top(); st.pop();
            if ((c == ')' && t != '(') ||
                (c == ']' && t != '[') ||
                (c == '}' && t != '{')) return false;
        }
    }
    return st.empty();
}

// Next greater element
vector<int> nextGreater(vector<int>& a) {
    int n = a.size();
    vector<int> res(n, -1);
    stack<int> st;
    for (int i = 0; i < n; ++i) {
        while (!st.empty() && a[st.top()] < a[i]) {
            res[st.top()] = a[i];
            st.pop();
        }
        st.push(i);
    }
    return res;
}
```""",
    "mistakes": "- **Not accounting for unmatched opens** at the end.\n- **Mixing index and value semantics.**\n- **Recursion-based solutions overflowing** on deep inputs — prefer iterative stacks.\n- **Forgetting sentinels** that simplify end-of-array handling.",
    "interview": "Stack problems reward pattern recognition. Interviewers want to see:\n\n1. **Quick identification of monotonic-stack patterns.**\n2. **Clean invariants on the stack's order.**\n3. **Correct sentinel use.**\n4. **Linear-time reasoning** via amortized analysis.",
},
"Recursion": {
    "display": "Recursion",
    "intro": "Recursion is the natural language of self-similar problems. A function calls itself on a smaller version of the input, combines results, and returns. Once you internalize the recipe — base case, recursive case, combine — a huge slice of interview problems becomes writable almost by reflex.",
    "analogy": "Think of Russian nesting dolls. To count the dolls, you open one and 'ask' the inner doll how many it contains — then add 1 for yourself. Each doll delegates the counting to its inside. That's recursion: solve by delegating to smaller versions of yourself.",
    "core": "Recursion has three parts: (1) a **base case** that solves the smallest input directly, (2) a **recursive call** on a smaller version, (3) a **combine step** that uses the recursive result. The key discipline is ensuring the recursive call actually shrinks the input — otherwise you have infinite recursion. Backtracking is a recursion pattern that tries a choice, recurses, then *undoes* the choice before trying the next.",
    "when_to_use": "Recursion is natural when:\n\n- **The problem has self-similar subproblems** (trees, subsets, permutations).\n- **Divide-and-conquer** fits.\n- **Backtracking exploration** of a state space.\n- **Problems defined recursively** (Fibonacci, factorial).\n\nIf subproblems overlap, add memoization and you have DP.",
    "variations": "- **Plain recursion** for divide-and-conquer.\n- **Backtracking** (try, recurse, undo) for enumeration.\n- **Memoized recursion** (top-down DP).\n- **Tail recursion** (can be iteratively rewritten).",
    "step_by_step": "**Generic recursion recipe:**\n1. Write the base case — what's the smallest input's answer?\n2. Write the recursive case — how does a non-base input decompose?\n3. Combine child results with the current input.\n4. Verify the recursion terminates (input always shrinks).\n\n**Backtracking recipe:**\n1. If the current state is a valid solution, record it.\n2. For each possible next choice:\n   - Apply the choice (update state).\n   - Recurse.\n   - Undo the choice (revert state).",
    "visual": "**Subsets of [1, 2, 3] via backtracking:**\n\n```\nstart: []\n  choose 1:        [1]\n    choose 2:      [1,2]\n      choose 3:    [1,2,3]  record\n      undo 3\n    undo 2\n    choose 3:      [1,3]    record\n    undo 3\n  undo 1\n  ... etc.\n\nAll subsets: [], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]\n```",
    "code": """```cpp
// Simple recursion (factorial)
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}

// Backtracking template
void bt(State& s, vector<Solution>& results) {
    if (isGoal(s)) { results.push_back(snapshot(s)); return; }
    for (auto choice : choices(s)) {
        if (!feasible(s, choice)) continue;
        apply(s, choice);
        bt(s, results);
        undo(s, choice);
    }
}

// Subsets (classic backtracking)
void dfs(vector<int>& a, int start, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = start; i < (int)a.size(); ++i) {
        cur.push_back(a[i]);
        dfs(a, i + 1, cur, res);
        cur.pop_back();
    }
}
```""",
    "mistakes": "- **Missing or wrong base case** — infinite recursion or wrong answer.\n- **Forgetting to undo state** in backtracking.\n- **Stack overflow on deep recursion.**\n- **Redundant work** without memoization when subproblems overlap.",
    "interview": "Recursion problems reveal your comfort with self-reference. Interviewers want to see:\n\n1. **Clear statement of base case and recursive case.**\n2. **Explicit parameter choices** (what defines a subproblem?).\n3. **Clean state-undo in backtracking.**\n4. **Awareness of when to add memoization.**\n\nIf your recursion feels hard to write, you likely haven't nailed the state. Spend another minute on that before coding.",
},
"Backtracking": {
    "display": "Backtracking",
    "intro": "Backtracking is DFS through a solution space with aggressive pruning. At each decision point, try an option, recurse, and undo. The key skill isn't the recursion — it's recognizing infeasible branches early and cutting them.",
    "analogy": "Think of a maze-solving robot. It tries a direction, walks until it hits a wall, then backs up and tries another direction. It never ignores a wall — instead, it *learns* from the failure and marks the dead-end so it doesn't retry it. That's backtracking: try, fail, rewind, try differently.",
    "core": "Backtracking is recursion with three reliable phases: (1) if the state is a solution, record it. (2) for each valid next choice, apply → recurse → undo. (3) return when no more choices. Without pruning, backtracking is exponential — with pruning, it can solve surprisingly large problems in reasonable time.",
    "when_to_use": "Signals for backtracking:\n\n- **'Generate all solutions'** (permutations, combinations, subsets).\n- **Constraint satisfaction** (N-Queens, Sudoku, crosswords).\n- **Path enumeration** in trees or grids.\n- **Combinatorial generation with constraints.**",
    "variations": "- **Subset / permutation generation** with skip-duplicate rules.\n- **Constraint-based** (N-Queens, Sudoku with row/col/box masks).\n- **Path enumeration** (palindrome partitioning).\n- **Game-tree search** with alpha-beta pruning.",
    "step_by_step": "**Generic backtracking template:**\n1. If current state satisfies the goal → record.\n2. For each possible next move:\n   - If not feasible (violates constraint), skip.\n   - Apply move.\n   - Recurse.\n   - Undo move.",
    "visual": "**N-Queens (4×4):**\n\n```\n. . . .\n. . . .\n. . . .\n. . . .\n\nTry col 0 row 0:\nQ . . .\n.(try row 2): . . Q .\n. (try row 3): ?  no safe spot\n  undo\n.(try row 3):\n. . . Q\n. (try row 1): ? no safe spot\n  undo\n undo\n... continue ...\nFinal valid: [1, 3, 0, 2]\n```",
    "code": """```cpp
// Generate parentheses
void gen(int n, int o, int c, string& s, vector<string>& res) {
    if ((int)s.size() == 2*n) { res.push_back(s); return; }
    if (o < n) { s += '('; gen(n, o+1, c, s, res); s.pop_back(); }
    if (c < o) { s += ')'; gen(n, o, c+1, s, res); s.pop_back(); }
}

// N-Queens
vector<vector<string>> solveNQueens(int n) {
    vector<vector<string>> res;
    vector<string> board(n, string(n, '.'));
    vector<int> col(n, 0), d1(2*n, 0), d2(2*n, 0);
    function<void(int)> bt = [&](int r) {
        if (r == n) { res.push_back(board); return; }
        for (int c = 0; c < n; ++c) {
            if (col[c] || d1[r+c] || d2[r-c+n]) continue;
            board[r][c] = 'Q';
            col[c] = d1[r+c] = d2[r-c+n] = 1;
            bt(r + 1);
            board[r][c] = '.';
            col[c] = d1[r+c] = d2[r-c+n] = 0;
        }
    };
    bt(0);
    return res;
}
```""",
    "mistakes": "- **Forgetting to undo state** — corrupts later iterations.\n- **Weak pruning** — TLE.\n- **Skip-duplicate rules misapplied.**\n- **Mutating shared state without backup.**",
    "interview": "Backtracking interviews test discipline. Interviewers want to see:\n\n1. **Clean recursion with apply → recurse → undo.**\n2. **Early pruning** based on constraints.\n3. **Handling of duplicate inputs.**\n4. **Clear base case and goal check.**",
},
"Sorting_Divide_and_Conquer": {
    "display": "Sorting / Divide & Conquer",
    "intro": "Sorting is a foundational tool — it's often the preprocessing step that turns hard problems into easy ones. Divide and conquer generalizes the pattern: split the problem, solve the pieces, merge. Mastering this unlocks merge sort, quicksort, Quickselect, and a family of 'counting during merge' tricks.",
    "analogy": "Think of how you'd sort a huge pile of documents. You'd split it in half, give each half to an assistant, and then carefully merge the two sorted piles. That's merge sort — divide and conquer in physical form. Every divide-and-conquer algorithm has the same spirit: break into smaller pieces, recurse, combine.",
    "core": "Divide-and-conquer has three steps: (1) divide — split the input into smaller pieces; (2) conquer — recursively solve each piece; (3) combine — merge the results. The merge step is often where the cleverness lives: counting inversions during merge, finding the pivot for quickselect, finding cut points in the closest-pair problem.",
    "when_to_use": "Reach for divide-and-conquer when:\n\n- **The problem naturally splits** into independent subproblems.\n- **Sorting is an enabling step** for the main algorithm.\n- **You need O(n log n) for a problem that looks O(n²).**\n- **Counting inversions / pairs with a property** — merge sort variant.",
    "variations": "- **Merge sort** — stable O(n log n) sort.\n- **Quicksort** — in-place, fast on average.\n- **Quickselect** — O(n) average for k-th statistic.\n- **Counting sort / Radix sort** — O(n) for bounded integer keys.\n- **Three-way partition** (Dutch flag) for 0/1/2 values.",
    "step_by_step": "**Merge sort:**\n1. If size ≤ 1, return.\n2. Split in the middle.\n3. Recursively sort each half.\n4. Merge the two sorted halves into one.\n\n**Quickselect (k-th smallest):**\n1. Pick a random pivot.\n2. Partition around pivot.\n3. If pivot index == k, return it.\n4. Else recurse on the side containing k.",
    "visual": "**Merge sort on [3, 1, 4, 1, 5, 9, 2, 6]:**\n\n```\n                [3,1,4,1,5,9,2,6]\n                 /              \\\n           [3,1,4,1]         [5,9,2,6]\n            /    \\             /    \\\n          [3,1] [4,1]       [5,9] [2,6]\n          /  \\   /  \\       /  \\   /  \\\n        [3] [1] [4] [1]   [5] [9] [2] [6]\n         merge   merge     merge   merge\n         [1,3]  [1,4]     [5,9]  [2,6]\n          merge              merge\n           [1,1,3,4]          [2,5,6,9]\n                   merge\n              [1,1,2,3,4,5,6,9]\n```",
    "code": """```cpp
// Merge sort with inversion count
long long mergeAndCount(vector<int>& a, int l, int m, int r) {
    vector<int> tmp;
    int i = l, j = m + 1;
    long long inv = 0;
    while (i <= m && j <= r) {
        if (a[i] <= a[j]) tmp.push_back(a[i++]);
        else { tmp.push_back(a[j++]); inv += m - i + 1; }
    }
    while (i <= m) tmp.push_back(a[i++]);
    while (j <= r) tmp.push_back(a[j++]);
    for (int k = l; k <= r; ++k) a[k] = tmp[k - l];
    return inv;
}
long long sortAndCount(vector<int>& a, int l, int r) {
    if (l >= r) return 0;
    int m = (l + r) / 2;
    return sortAndCount(a, l, m) + sortAndCount(a, m + 1, r) + mergeAndCount(a, l, m, r);
}

// Quickselect (k-th smallest)
int quickselect(vector<int>& a, int k) {
    int lo = 0, hi = a.size() - 1;
    while (true) {
        int pivot = a[lo + rand() % (hi - lo + 1)];
        int i = lo, j = hi, p = lo;
        while (p <= j) {
            if (a[p] < pivot) swap(a[p++], a[i++]);
            else if (a[p] > pivot) swap(a[p], a[j--]);
            else p++;
        }
        if (k < i) hi = i - 1;
        else if (k > j) lo = j + 1;
        else return pivot;
    }
}
```""",
    "mistakes": "- **Non-stable sort** where stability was required.\n- **Bad pivot choice** in quicksort → O(n²) worst case. Randomize.\n- **Misuse of `std::sort` comparator** — must be strict weak ordering.\n- **Merge step overflow** — use `long long` for counts.",
    "interview": "Sorting questions test both implementation and pattern recognition. Interviewers want to see:\n\n1. **Clean merge logic** — the hardest part of merge sort.\n2. **Correct partition** in quicksort/quickselect.\n3. **Stable vs unstable awareness.**\n4. **Recognition of 'count during merge' patterns** for inversions, reverse pairs, etc.",
},
}


def build_concept_md(folder, data):
    d = data[folder]
    return f"""# {d['display']} — Concepts Guide

----------------------------------------

## 1. Introduction

{d['intro']}

----------------------------------------

## 2. Real-Life Analogy

{d['analogy']}

----------------------------------------

## 3. Core Idea

{d['core']}

----------------------------------------

## 4. When to Use This (Pattern Recognition)

{d['when_to_use']}

----------------------------------------

## 5. Types / Variations

{d['variations']}

----------------------------------------

## 6. Step-by-Step Working

{d['step_by_step']}

----------------------------------------

## 7. Visual Explanation

{d['visual']}

----------------------------------------

## 8. Code Templates (C++)

{d['code']}

----------------------------------------

## 9. Common Mistakes

{d['mistakes']}

----------------------------------------

## 10. Interview Insights

{d['interview']}
"""


def main():
    from utils import ROOT as R
    for folder, _ in TOPICS.items():
        dest = os.path.join(R, "Topics", folder, "Concepts.md")
        write(dest, build_concept_md(folder, TOPICS))
    print(f"Wrote {len(TOPICS)} concept files.")


if __name__ == "__main__":
    main()
