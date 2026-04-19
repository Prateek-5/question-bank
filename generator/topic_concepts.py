CONCEPTS = {
"Heap_Priority_Queue": """# Heap / Priority Queue — Concepts

## Core Theory
A heap is a complete binary tree where every parent satisfies a partial order with its children (min-heap: parent ≤ children; max-heap: parent ≥ children). It provides O(log n) insertion and extraction of the top element and O(1) peek. In C++, `std::priority_queue` is a max-heap by default; use `greater<>` comparator for a min-heap.

## Common Patterns
- **Top-K filtering:** maintain a bounded heap of size k (max-heap for k smallest, min-heap for k largest).
- **Streaming median:** two heaps (lo max-heap, hi min-heap) balanced to differ by at most 1.
- **Greedy merging:** combine smallest elements repeatedly (Huffman / connect ropes).
- **K-way merge:** push one head from each list; pop, emit, advance.
- **Graph shortest paths (Dijkstra):** min-heap keyed by distance.

## When to Use
When you need the minimum or maximum efficiently under insertions, or need to process items in priority order. Avoid when you need random access, sorted iteration, or frequent arbitrary updates to non-top items (use segment trees or indexed heaps instead).

## Template
```cpp
// Max-heap
priority_queue<int> pq;
// Min-heap
priority_queue<int, vector<int>, greater<int>> pq;
// Custom comparator (lambda)
auto cmp = [](const auto& a, const auto& b){ return a.cost > b.cost; };
priority_queue<Node, vector<Node>, decltype(cmp)> pq(cmp);
```

## Common Mistakes
- Forgetting that `priority_queue<int>` is a *max* heap by default.
- Using a heap where a sorted container is more appropriate.
- Pushing duplicate entries when modifying a key; use lazy deletion with a stale check.
- Not handling ties deterministically — include secondary keys.
""",

"Math": """# Math — Concepts

## Core Theory
Math problems often reduce to modular arithmetic, divisibility rules, combinatorics, or closed-form identities. Recognizing structure — like digital roots, pigeonhole principle, Euclidean GCD — converts naive simulations into O(1) or O(log n) solutions.

## Common Patterns
- **Digital root:** 1 + (n-1) % 9 for positive n.
- **Prefix sums modulo k:** detect subarrays divisible by k.
- **Pigeonhole:** n+1 items in n boxes forces a collision.
- **GCD via Euclid:** gcd(a, b) = gcd(b, a%b); O(log min).
- **Modular exponentiation:** binary fast power in O(log exp).

## When to Use
Whenever brute force over values or pairs feels excessive. Look for modular invariants, symmetries, and closed forms before coding a loop.

## Template
```cpp
long long power(long long a, long long b, long long m) {
    long long r = 1 % m; a %= m;
    while (b) { if (b & 1) r = r * a % m; a = a * a % m; b >>= 1; }
    return r;
}
```

## Common Mistakes
- Overflow on intermediate products (use 64-bit).
- Negative modulo: `((x % k) + k) % k`.
- Integer division rounding for floors/ceilings.
- Off-by-one with inclusive/exclusive ranges.
""",

"Graph_BFS_DFS_Dijkstra_DSU": """# Graph (BFS / DFS / Dijkstra / DSU) — Concepts

## Core Theory
Graphs model relations between nodes. Depending on the problem, choose representation (adjacency list / matrix), traversal (BFS, DFS), shortest path (Dijkstra, Bellman-Ford, Floyd-Warshall), cycle detection, topological sort, or connectivity (DSU).

## Common Patterns
- **BFS for shortest hops** in unweighted graphs; multi-source BFS for distance fields.
- **DFS for connectivity, topo order, strongly connected components, cycle detection.**
- **Dijkstra with min-heap** for non-negative weights.
- **Bellman-Ford** for negative weights or k-step constraints.
- **DSU (Union-Find)** for connectivity queries, Kruskal's MST, equation systems.

## When to Use
BFS for shortest unweighted path. DFS for recursive exploration and topo. Dijkstra for weighted shortest path. DSU when only connectivity matters and merges dominate queries.

## Template
```cpp
// DSU
struct DSU {
    vector<int> p, r;
    DSU(int n): p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a; if (r[a] == r[b]) r[a]++; return true;
    }
};
```

## Common Mistakes
- Forgetting to mark nodes visited causes infinite loops.
- Using `visited` inside Dijkstra's pop phase instead of checking on push.
- Directed vs undirected: omission of reverse edges or parent exclusion.
- Off-by-one when 1-indexed inputs meet 0-indexed adjacency arrays.
""",

"Binary_Search_Tree_BST": """# Binary Search Tree (BST) — Concepts

## Core Theory
A BST maintains the invariant that for every node, left subtree keys < node < right subtree keys. In-order traversal yields keys in sorted order. Balanced BSTs (red-black, AVL) guarantee O(log n) operations; unbalanced may degrade to O(n).

## Common Patterns
- **In-order traversal** for sorted operations.
- **Divide-and-conquer via median** for converting sorted arrays to balanced BSTs.
- **BST property pruning** when searching a range or finding LCA.
- **Iterator via stack** for O(1) amortized `next()`.

## When to Use
When ordered operations and dynamic inserts/deletes are both required. Use heaps if order-statistics are less important.

## Template
```cpp
struct Node { int val; Node *l, *r; };
Node* insert(Node* r, int v) {
    if (!r) return new Node{v, nullptr, nullptr};
    if (v < r->val) r->l = insert(r->l, v);
    else r->r = insert(r->r, v);
    return r;
}
```

## Common Mistakes
- Assuming tree is balanced — worst-case O(n) if not.
- Duplicate-key policies (left vs right vs ignore).
- Not restoring BST invariants after deletion.
""",

"Trees_Binary_Trees": """# Trees / Binary Trees — Concepts

## Core Theory
Binary trees represent hierarchical data with each node having up to two children. Traversals are the main tool: preorder, inorder, postorder (DFS) and level-order (BFS). Many problems reduce to post-order aggregation from children.

## Common Patterns
- **Post-order aggregation** (height, diameter, balanced check, path sum).
- **Pre-order / BFS serialization**.
- **Divide-and-conquer reconstruction** from two traversals (preorder+inorder, etc.).
- **DFS with state** (level, sum, path) for depth-related queries.

## When to Use
For hierarchical data, decision trees, expression parsing, or whenever divide-and-conquer via subtree structure fits.

## Template
```cpp
struct TreeNode { int val; TreeNode *left, *right; };
int height(TreeNode* r) { return r ? 1 + max(height(r->left), height(r->right)) : 0; }
```

## Common Mistakes
- Forgetting null checks before dereferencing children.
- Confusing in-order and pre-order during reconstruction.
- Stack overflow on deep skewed trees — prefer iterative or Morris traversal.
""",

"Greedy": """# Greedy — Concepts

## Core Theory
Greedy algorithms make a locally optimal choice at each step that also happens to lead to a global optimum. Correctness relies on either the **greedy-choice property** (a globally optimal solution contains a specific greedy choice) or a **matroid / exchange argument**.

## Common Patterns
- **Interval scheduling by end time** (activity selection, Non-overlapping Intervals).
- **Huffman-style two-smallest merges**.
- **Two-pointer pairing** for min-max problems after sorting.
- **Sweep-line counting** for concurrent resource usage.

## When to Use
When brute force is exponential and a careful local choice provably doesn't compromise future options. Verify by exchange argument before trusting a greedy.

## Template
```cpp
sort(intervals.begin(), intervals.end(), byEnd);
int last = INT_MIN, cnt = 0;
for (auto& iv : intervals) if (iv.start >= last) { last = iv.end; cnt++; }
```

## Common Mistakes
- Applying greedy without proof — DP is often safer.
- Wrong sort key (by start vs end vs length) changes correctness.
- Ignoring ties or boundary cases that break the invariant.
""",

"1_D_and_2_D_Arrays": """# 1-D & 2-D Arrays — Concepts

## Core Theory
Arrays are random-access containers. Mastery includes prefix sums, difference arrays, in-place transformations (rotation, spiral), and index arithmetic for 1D↔2D mapping.

## Common Patterns
- **Prefix sums (1D, 2D)** for range queries in O(1).
- **Sliding window** for contiguous subarray sums / constraints.
- **In-place matrix ops** (transpose, rotate, zero-out).
- **Index mapping**: flat idx ↔ (row, col).

## When to Use
Whenever constant-time random access is needed, or data naturally has spatial structure. Prefer hashmaps when keys are sparse.

## Template
```cpp
// 2D prefix sum
for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j)
    P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j];
```

## Common Mistakes
- Off-by-one in prefix indices (use P[0..n] of length n+1).
- Row-major vs column-major misuse.
- Forgetting to copy when passing arrays that may mutate.
""",

"Segment_Tree_Range_Queries": """# Segment Tree / Range Queries — Concepts

## Core Theory
Segment trees support range queries and updates in O(log n). They decompose an array into O(n) nodes, each covering a sub-range. Lazy propagation defers range updates to descendants only when needed, preserving O(log n) per operation.

## Common Patterns
- **Point update, range query** (sum / min / max).
- **Range update, range query** via lazy propagation.
- **Persistent segment trees** for versioned queries.
- **Binary search on segment tree** (first index ≥ x in range).

## When to Use
When you need both frequent updates *and* range queries on the same array. For static arrays, use sparse tables or prefix sums.

## Template
```cpp
// Skeleton for a segment tree
void build(int v, int l, int r) { /* ... */ }
void update(int v, int l, int r, int i, int val) { /* ... */ }
int query(int v, int l, int r, int ql, int qr) { /* ... */ }
```

## Common Mistakes
- Off-by-one in [l, r] vs [l, r) conventions.
- Forgetting to push lazy before descending.
- Sizing tree too small — 4·n is a safe upper bound.
""",

"Arrays_and_Matrices": """# Arrays & Matrices — Concepts

## Core Theory
Array and matrix problems emphasize traversal patterns (row/col scans, diagonals, spirals), counting contributions, and careful boundary handling.

## Common Patterns
- **Contribution counting:** each element's weight × number of subarrays it belongs to.
- **Two-pointer trapping** (rainwater).
- **Boundary traversals** (spiral, surrounded regions).
- **Per-row max/min tracking** (lucky numbers).

## When to Use
When input structure is naturally 2D or when you want O(1) random access.

## Template
```cpp
int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};
for (int k = 0; k < 4; ++k) { int nr = r + dr[k], nc = c + dc[k]; /* bounds */ }
```

## Common Mistakes
- Off-by-one in boundary checks.
- Forgetting to restart state between test cases.
- Using nested loops when a pattern-based closed form exists.
""",

"Searching_Binary_Search": """# Searching / Binary Search — Concepts

## Core Theory
Binary search works whenever the search space has a monotonic property — either the input is sorted, or some predicate is monotonic over the index/value. It halves the space per step, yielding O(log n).

## Common Patterns
- **Sorted-array search** (classic, upper/lower bound).
- **Binary search on answer:** search a numeric range with a feasibility function.
- **Staircase search in 2D**.
- **Rotated array search** with sorted-half detection.

## When to Use
Whenever monotonicity is present or a candidate answer can be checked faster than enumerating all answers.

## Template
```cpp
int lo = 0, hi = n - 1;
while (lo < hi) { int m = (lo + hi) / 2; if (ok(m)) hi = m; else lo = m + 1; }
```

## Common Mistakes
- Using `(lo + hi) / 2` with overflow risk on large ints — use `lo + (hi - lo) / 2`.
- Wrong boundary update causing infinite loop.
- Misidentifying the monotonic predicate.
""",

"Two_Pointers": """# Two Pointers — Concepts

## Core Theory
Two-pointer techniques exploit ordering or monotonic counts. Pointers usually move in the same direction (sliding window) or toward each other (opposite ends).

## Common Patterns
- **Opposite-end pointers** on sorted arrays (two-sum, container).
- **Same-direction pointers** for subarray sums, distinct counts.
- **Fast/slow pointers** for linked-list cycle detection and middle finding.
- **Three-pointer partitioning** (Dutch flag).

## When to Use
Any problem where constraints advance pointers monotonically without backtracking — often converts an O(n²) scan to O(n).

## Template
```cpp
int l = 0, r = n - 1;
while (l < r) { int s = a[l] + a[r]; if (s == t) ...; else if (s < t) l++; else r--; }
```

## Common Mistakes
- Moving the wrong pointer when both sides are equal.
- Missing duplicates handling on sorted arrays.
- Using two pointers on unsorted data without preprocessing.
""",

"Linked_List": """# Linked List — Concepts

## Core Theory
Linked lists store nodes connected by pointers. Singly linked lists support O(1) insert/delete at known nodes but O(n) random access. Most operations benefit from a dummy head to simplify edge cases.

## Common Patterns
- **Slow/fast pointers** (middle, cycle, k-th from end).
- **Reverse a sublist** by pointer rearrangement.
- **Dummy head** for cleaner insert/delete.
- **Merge k sorted lists** via min-heap.

## When to Use
When dynamic sizes and fast insert/delete at known positions matter, and random access isn't needed.

## Template
```cpp
struct ListNode { int val; ListNode* next; };
ListNode* reverse(ListNode* h) {
    ListNode* p = nullptr;
    while (h) { auto n = h->next; h->next = p; p = h; h = n; }
    return p;
}
```

## Common Mistakes
- Forgetting to update the last node's next to null after reversal.
- Losing track of head when manipulating pointers.
- Using recursion and hitting stack-overflow on long lists.
""",

"Number_Theory_Misc": """# Number Theory / Misc — Concepts

## Core Theory
Number theory problems involve primes, divisors, modular arithmetic, GCD/LCM, and digit manipulations. Efficient techniques: trial division up to √n, sieve of Eratosthenes, fast exponentiation, digit DP.

## Common Patterns
- **Sieve of Eratosthenes** for all primes up to N.
- **Digit extraction** via repeated `% 10` / `/ 10`.
- **Divisor enumeration** up to √n.
- **Digit DP** for counts over ranges.

## When to Use
When inputs relate to integers, digits, primes, or modular structure. Often O(1) closed forms lurk behind seemingly complex problems.

## Template
```cpp
vector<bool> sieve(int n) {
    vector<bool> p(n+1, true); p[0]=p[1]=false;
    for (int i = 2; (long long)i*i <= n; ++i) if (p[i])
        for (int j = i*i; j <= n; j += i) p[j] = false;
    return p;
}
```

## Common Mistakes
- Integer overflow in products.
- Forgetting 1 and n as trivial divisors.
- Negative numbers in modular arithmetic.
""",

"Trie_Bit_Manipulation_Trie": """# Trie / Bit Manipulation Trie — Concepts

## Core Theory
Tries store strings (or bit sequences) by prefixes, enabling fast prefix queries, spell-check, dictionary lookups, and XOR maximization. Each node has one child per alphabet letter or bit.

## Common Patterns
- **Word insert/search** (classic trie).
- **Prefix + suffix search** by concatenating suffix#word variants.
- **Bit-trie for max XOR** — traverse greedily preferring opposite bits.
- **Wildcard search via DFS**.

## When to Use
When prefix-based queries dominate or when the alphabet is small and fixed. For arbitrary strings, hashmaps may be simpler unless prefix operations are essential.

## Template
```cpp
struct TrieNode { TrieNode* c[26] = {}; bool end = false; };
```

## Common Mistakes
- Memory blowup with large alphabets; consider hashmap children.
- Forgetting the end-of-word marker.
- Off-by-one when computing trie depth vs string length.
""",

"Dynamic_Programming_DP": """# Dynamic Programming (DP) — Concepts

## Core Theory
DP solves problems by recurrence over overlapping subproblems with optimal substructure. Transforms exponential recursion into polynomial tables via memoization (top-down) or tabulation (bottom-up).

## Common Patterns
- **1D DP** over indices (climbing stairs, LIS, Kadane).
- **2D DP** over (i, j) (LCS, edit distance, interleaving).
- **Knapsack** (0/1, unbounded, bounded).
- **Interval DP** (matrix chain, palindrome partitioning).
- **Digit DP** for count-over-range problems.

## When to Use
When a brute force solution exhibits overlapping subproblems and the answer can be expressed recursively in terms of smaller inputs.

## Template
```cpp
// Top-down
int solve(int i, vector<int>& memo) {
    if (baseCase) return ...;
    if (memo[i] != -1) return memo[i];
    return memo[i] = combine(solve(i-1, memo), solve(i-2, memo));
}
```

## Common Mistakes
- Missing base cases or off-by-one at boundaries.
- Wrong state (too few or too many dimensions).
- Iteration order in bottom-up must respect dependencies.
- Forgetting to initialize memo table to a sentinel.
""",

"Bit_Manipulation": """# Bit Manipulation — Concepts

## Core Theory
Bit-level operations manipulate integers at the binary level. Common tricks involve AND/OR/XOR/NOT, shifts, and Brian Kernighan's trick (`n & (n-1)` clears the lowest set bit).

## Common Patterns
- **XOR cancels pairs** — single-number problems.
- **Masking subsets** via bitmask DP.
- **Popcount** via `__builtin_popcount`.
- **Bit reversal** by bit-by-bit loop or SWAR.

## When to Use
When problems hinge on binary properties, subset enumeration (n ≤ 20), or XOR invariants.

## Template
```cpp
for (int mask = 0; mask < (1 << n); ++mask)
    for (int sub = mask; sub; sub = (sub - 1) & mask) { /* iterate subsets */ }
```

## Common Mistakes
- Signed right-shift vs unsigned for top bits.
- Forgetting to clear bits before setting.
- Overflow with shifts ≥ bit width.
""",

"Hashing_Sliding_Window": """# Hashing / Sliding Window — Concepts

## Core Theory
Hashing maps keys to O(1) access. Sliding window maintains a dynamic range with monotonic bounds, ideal for contiguous subarray/substring problems.

## Common Patterns
- **Prefix-sum + hashmap** for subarray-sum counting.
- **Sliding window** with expand/shrink based on predicate.
- **Character-frequency maps** for anagrams and substrings.
- **Two-sum style lookup**.

## When to Use
Prefer hashing for unordered membership; sliding window when constraints are monotonic over contiguous segments.

## Template
```cpp
int l = 0;
for (int r = 0; r < n; ++r) {
    // expand with a[r]
    while (invalid) { /* shrink with a[l++] */ }
    best = max(best, r - l + 1);
}
```

## Common Mistakes
- Failing to update both window boundaries' counts.
- Using hashmap where an int array suffices (slower).
- Forgetting to remove stale entries when shrinking.
""",

"Queues_Deque_Monotonic_Queue": """# Queues / Deque / Monotonic Queue — Concepts

## Core Theory
Queues and deques provide FIFO access. Monotonic deques maintain elements in monotonic order, supporting sliding window min/max in O(n).

## Common Patterns
- **BFS queue** for level-order traversal.
- **Monotonic deque** for sliding window extremes.
- **Implementing stack via queues** and vice versa (design).

## When to Use
For breadth-first traversal, fairness, or sliding-window extremum queries.

## Template
```cpp
deque<int> dq;
for (int i = 0; i < n; ++i) {
    while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();
    dq.push_back(i);
    if (dq.front() <= i - k) dq.pop_front();
}
```

## Common Mistakes
- Pushing values instead of indices loses position info.
- Incorrect popping direction for min vs max queue.
- Using `queue` instead of `deque` when both ends are needed.
""",

"Stack": """# Stack — Concepts

## Core Theory
Stacks follow LIFO. They shine in problems with nested structure (parentheses) and in "next greater/smaller" sweeps via monotonic stacks.

## Common Patterns
- **Monotonic stack** for next greater / previous smaller.
- **Parentheses matching**.
- **Expression evaluation** (RPN).
- **Histogram largest rectangle**.

## When to Use
Whenever you need to remember context for a later operation, especially nested structure or bar-shaped scans.

## Template
```cpp
stack<int> st;
for (int i = 0; i < n; ++i) {
    while (!st.empty() && a[st.top()] < a[i]) st.pop();
    st.push(i);
}
```

## Common Mistakes
- Not accounting for unmatched elements at the end — use sentinels.
- Mixing index and value semantics.
- Recursion-based solutions overflowing stack with deep input.
""",

"Recursion": """# Recursion — Concepts

## Core Theory
Recursion expresses a problem in terms of smaller instances. Essential ingredients: base case, recursive case, and progress toward the base. Often paired with backtracking to explore combinatorial spaces.

## Common Patterns
- **Divide-and-conquer**: split, solve, combine.
- **Backtracking**: try, recurse, undo.
- **Tail recursion**: can be rewritten iteratively.

## When to Use
For tree/graph traversals, combinatorial enumeration, and any naturally self-similar problem. Beware deep recursion — convert to iterative with explicit stack when depth ~ n.

## Template
```cpp
void dfs(State s, vector<State>& out) {
    if (done(s)) { out.push_back(s); return; }
    for (Move m : moves(s)) { apply(s, m); dfs(s, out); undo(s, m); }
}
```

## Common Mistakes
- Missing or wrong base case.
- Forgetting to undo state after recursive call.
- Stack overflow on deep recursion — use iterative when possible.
""",

"Backtracking": """# Backtracking — Concepts

## Core Theory
Backtracking is DFS through a solution space with pruning. At each decision point, try an option, recurse, and undo. Prune infeasible branches as early as possible.

## Common Patterns
- **Permutations, combinations, subsets** with skip-duplicate rules.
- **Constraint satisfaction** (N-Queens, Sudoku) with row/col/box masks.
- **Palindrome / substring partitioning**.

## When to Use
For combinatorial problems whose state space is exponential but heavily prunable. If no effective pruning is available, consider DP or smarter greedy.

## Template
```cpp
void bt(State& s, Solution& ans) {
    if (goal(s)) { ans.record(s); return; }
    for (auto c : choices(s)) if (feasible(s, c)) {
        apply(s, c); bt(s, ans); undo(s, c);
    }
}
```

## Common Mistakes
- Not undoing state → incorrect enumeration.
- Weak pruning → TLE.
- Duplicate-skip rules misapplied (sibling vs descendant).
""",

"Sorting_Divide_and_Conquer": """# Sorting / Divide & Conquer — Concepts

## Core Theory
Sorting rearranges elements by a key. Merge sort (stable, O(n log n), O(n) space) and quicksort (in-place, O(n log n) avg) are the classic divide-and-conquer sorts. Counting/Radix sorts run in O(n) for bounded ranges.

## Common Patterns
- **Merge sort counting pairs** (inversions, reverse pairs).
- **Quickselect** for k-th statistics.
- **Bucket/radix sort** for integer keys.
- **Three-way partition** for Dutch flag.

## When to Use
For algorithmic primitives (O(n log n) sorts) or when problem structure — like inversion counting — naturally benefits from divide-and-conquer.

## Template
```cpp
void merge(vector<int>& a, int l, int m, int r) { /* ... */ }
void mergeSort(vector<int>& a, int l, int r) {
    if (l >= r) return; int m = (l + r) / 2;
    mergeSort(a, l, m); mergeSort(a, m+1, r); merge(a, l, m, r);
}
```

## Common Mistakes
- Using quicksort without randomization on adversarial inputs.
- Unstable sort where stability is required.
- Misuse of `std::sort` custom comparator (must be strict weak ordering).
""",
}
