# C++ Concepts for DSA

A quick reference for the C++ features, STL patterns, and idioms you will use across the problems in this repository. The goal is to give you enough to read and write clean competitive-programming C++ without hunting for syntax.

## Table of Contents
1. STL Containers
2. STL Algorithms
3. Iterators and Range Idioms
4. Comparators and Lambdas
5. Priority Queues (Heaps)
6. Hashing Containers
7. Graph Representations
8. Common Patterns
9. Handy Utilities

---

## 1. STL Containers

### vector
- Dynamic array with O(1) amortized push_back.
- Random access via `v[i]` or `v.at(i)`.
- Resize: `v.resize(n)`, `v.resize(n, defaultVal)`.
- 2D: `vector<vector<int>> grid(n, vector<int>(m, 0));`

### deque
- Double-ended queue with O(1) push/pop at both ends.
- Used for monotonic deques and sliding-window extremes.

### stack / queue
- Adapters over deque. O(1) push/pop at one end.

### set / multiset
- Ordered containers (red-black tree) with O(log n) ops.
- Lookup via `s.find(x)`, ordered traversal via iterators.
- `lower_bound`, `upper_bound` give in-container iterators.

### map / multimap
- Ordered key→value. Great when keys must be traversed in order.

### string
- Mutable, random-access character sequence.
- Useful: `substr(start, len)`, `+=`, `find`, `push_back`, `pop_back`.

---

## 2. STL Algorithms

- `sort(begin, end)` — O(n log n) introsort.
- `stable_sort(begin, end)` — preserves equal-key order.
- `reverse(begin, end)`.
- `rotate(begin, new_first, end)`.
- `min_element`, `max_element`, `minmax_element`.
- `accumulate(begin, end, init)` — sum/fold.
- `iota(begin, end, start)` — fill with sequential values.
- `count`, `count_if`, `find`, `find_if`.
- `unique` — collapse consecutive duplicates; pair with `erase`.
- `next_permutation` / `prev_permutation`.
- `upper_bound` / `lower_bound` — binary search on sorted range.
- `partition` / `stable_partition`.
- `nth_element` — O(n) average rank-k partitioning.

---

## 3. Iterators and Range Idioms

```cpp
for (int x : v) { /* read */ }
for (auto& x : v) { /* mutate */ }
for (auto& [k, val] : map) { /* structured binding */ }
```

Reverse iteration:
```cpp
for (auto it = v.rbegin(); it != v.rend(); ++it) { /* ... */ }
```

Half-open ranges everywhere: `[begin, end)`.

---

## 4. Comparators and Lambdas

```cpp
sort(v.begin(), v.end(), [](const Pair& a, const Pair& b) {
    return a.cost < b.cost;  // strict weak ordering
});
```

For containers that need a comparator (set, priority_queue) capture the comparator:
```cpp
auto cmp = [](const Node& a, const Node& b){ return a.id < b.id; };
set<Node, decltype(cmp)> s(cmp);
```

Avoid returning `a <= b` from a sort comparator — sort requires *strict* ordering.

---

## 5. Priority Queues (Heaps)

```cpp
priority_queue<int> pq;                                    // max-heap
priority_queue<int, vector<int>, greater<int>> mn;          // min-heap

auto cmp = [](const Node& a, const Node& b){ return a.cost > b.cost; };
priority_queue<Node, vector<Node>, decltype(cmp)> pq(cmp);  // custom
```

Always `pq.top()`, then `pq.pop()`. Inserts and extractions are O(log n).

---

## 6. Hashing Containers

- `unordered_map<K, V>` and `unordered_set<K>`: average O(1).
- Use for membership tests and key lookups when order doesn't matter.
- For pairs / tuples, provide a custom hash, or use an ordered `map` if convenient.
- Beware adversarial inputs that make unordered_map slow (chain hash attacks).

---

## 7. Graph Representations

### Adjacency list (most common)
```cpp
vector<vector<int>> g(n);               // unweighted
vector<vector<pair<int,int>>> g(n);     // weighted: {neighbor, weight}
```

### Edge list
```cpp
vector<tuple<int,int,int>> edges;       // {u, v, w}
```

### Adjacency matrix (dense graphs only)
```cpp
vector<vector<int>> adj(n, vector<int>(n, 0));
```

---

## 8. Common Patterns

### BFS template
```cpp
queue<int> q; q.push(src);
vector<int> dist(n, -1); dist[src] = 0;
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : g[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        q.push(v);
    }
}
```

### DFS template
```cpp
function<void(int)> dfs = [&](int u) {
    visited[u] = true;
    for (int v : g[u]) if (!visited[v]) dfs(v);
};
```

### Dijkstra
```cpp
priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
pq.push({0, src}); dist[src] = 0;
while (!pq.empty()) {
    auto [d, u] = pq.top(); pq.pop();
    if (d > dist[u]) continue;
    for (auto [v, w] : g[u]) if (d + w < dist[v]) {
        dist[v] = d + w; pq.push({dist[v], v});
    }
}
```

### Union-Find (DSU)
```cpp
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

### Sliding window
```cpp
int l = 0;
for (int r = 0; r < n; ++r) {
    // expand with a[r]
    while (!valid()) { /* shrink with a[l++] */ }
    best = max(best, r - l + 1);
}
```

---

## 9. Handy Utilities

- `__builtin_popcount(x)` / `__builtin_popcountll(x)` — popcount.
- `__builtin_clz`, `__builtin_ctz` — leading / trailing zeros.
- `__gcd(a, b)` — Euclidean GCD.
- `to_string(x)`, `stoi(s)`, `stoll(s)`.
- `numeric_limits<int>::max()` / `min()` — constants.
- `ios_base::sync_with_stdio(false); cin.tie(nullptr);` — fast I/O.
- `<bits/stdc++.h>` — convenient single-include for competitive use.

### Typical main scaffold
```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(nullptr);
    // solve
    return 0;
}
```
