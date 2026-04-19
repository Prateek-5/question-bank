DATA = {
"01 Matrix": {
  "concept": "Multi-source BFS from all zeros simultaneously.",
  "intuition": "Each cell's answer is the distance to the *nearest* zero. Instead of BFS from every one cell, invert it — start BFS from every zero at distance 0 and propagate outward. Each cell is first reached at its correct distance.",
  "explanation": "Initialize dist[r][c] = 0 if cell is 0, else INF. Push all zeros into a queue. BFS: for the front cell, visit 4 neighbors; if neighbor's distance > current+1, update and push. BFS guarantees shortest distance in unweighted graphs.",
  "dry_run": "mat=[[0,0,0],[0,1,0],[1,1,1]]. Zeros pushed at dist 0. BFS expands: (1,1)=1, (2,0)=1, (2,2)=1, (2,1)=2. Result matches shortest-zero distances.",
  "approach": "Multi-source BFS gives O(n*m).",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> updateMatrix(vector<vector<int>>& mat) {
    int n = mat.size(), m = mat[0].size();
    vector<vector<int>> d(n, vector<int>(m, INT_MAX));
    queue<pair<int,int>> q;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (!mat[i][j]) { d[i][j]=0; q.push({i,j}); }
    int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1};
    while (!q.empty()) {
        auto [r,c] = q.front(); q.pop();
        for (int k=0;k<4;k++) {
            int nr=r+dr[k], nc=c+dc[k];
            if (nr<0||nc<0||nr>=n||nc>=m) continue;
            if (d[nr][nc] > d[r][c] + 1) { d[nr][nc] = d[r][c] + 1; q.push({nr,nc}); }
        }
    }
    return d;
}""",
  "followups": "- Use two-pass DP for the same problem.\n- Weighted variant with Dijkstra.\n- 3D matrix analog."
},

"Number of Operations to Make Network Connected": {
  "concept": "Count connected components via DSU/BFS; need (components - 1) spare edges.",
  "intuition": "If we have c components we need c-1 links to connect them all. Each operation *moves* a cable. A cable is spare if it creates a cycle (both endpoints already connected). We must have enough spare cables.",
  "explanation": "Use DSU. For each edge: if endpoints are in the same component, it's spare (extra). Otherwise union. Count components at end. If spare_edges >= components - 1, return components - 1; else return -1.",
  "dry_run": "n=4, edges=[[0,1],[0,2],[1,2]]. Edges: (0,1) union. (0,2) union. (1,2) same comp → spare=1. Components: {0,1,2},{3} = 2. Need 1 move; spare=1 → answer=1.",
  "approach": "Union-find counts components and detects redundant edges in one pass.",
  "complexity": "Time: O(E α(n)). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct DSU {
    vector<int> p, r;
    DSU(int n): p(n), r(n,0) { iota(p.begin(),p.end(),0); }
    int f(int x){ return p[x]==x?x:p[x]=f(p[x]); }
    bool u(int a,int b){ a=f(a); b=f(b); if(a==b) return false; if(r[a]<r[b]) swap(a,b); p[b]=a; if(r[a]==r[b]) r[a]++; return true; }
};
int makeConnected(int n, vector<vector<int>>& edges) {
    if ((int)edges.size() < n - 1) return -1;
    DSU d(n);
    for (auto& e : edges) d.u(e[0], e[1]);
    int comps = 0;
    for (int i=0;i<n;i++) if (d.f(i)==i) comps++;
    return comps - 1;
}""",
  "followups": "- Return the set of edges to move.\n- Weighted connectivity (MST).\n- Dynamic connectivity updates."
},

"Accounts Merge": {
  "concept": "DSU on emails — union emails sharing an account, group by root.",
  "intuition": "Each account gives a list of emails that should be in the same component. Union all emails within one account. Then group emails by DSU root and attach each group's name.",
  "explanation": "Map each unique email to an id. For each account, union all its emails with the first. Also map email→name. After processing, group emails by DSU root; sort each group; prepend the owner's name.",
  "dry_run": "Accounts: [John, a@, b@], [John, b@, c@], [Mary, x@]. Union a-b, b-c → {a,b,c} component. Group {a@,b@,c@} → John. {x@} → Mary. Output two accounts.",
  "approach": "DSU with string-id mapping; careful with sorting emails within each group.",
  "complexity": "Time: O(N log N α) where N is total emails. Space: O(N).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

vector<vector<string>> accountsMerge(vector<vector<string>>& acc) {
    unordered_map<string,int> id;
    unordered_map<string,string> name;
    int cnt = 0;
    for (auto& a : acc)
        for (int i = 1; i < (int)a.size(); ++i) {
            if (!id.count(a[i])) { id[a[i]] = cnt++; name[a[i]] = a[0]; }
        }
    DSU d(cnt);
    for (auto& a : acc)
        for (int i = 2; i < (int)a.size(); ++i) d.u(id[a[1]], id[a[i]]);
    unordered_map<int, vector<string>> groups;
    for (auto& [e, i] : id) groups[d.f(i)].push_back(e);
    vector<vector<string>> res;
    for (auto& [_, emails] : groups) {
        sort(emails.begin(), emails.end());
        vector<string> row = {name[emails[0]]};
        row.insert(row.end(), emails.begin(), emails.end());
        res.push_back(row);
    }
    return res;
}""",
  "followups": "- Very large datasets — can we avoid string interning overhead?\n- Streamed accounts — incremental merges.\n- Detect and split accidental merges (quality checks)."
},

"Cheapest Flights Within K Stops": {
  "concept": "Bellman-Ford limited to K+1 edge relaxations, or modified Dijkstra tracking stops.",
  "intuition": "We can take at most K intermediate stops = K+1 edges. Bellman-Ford performs one edge-relaxation pass per allowable edge, so K+1 passes compute shortest paths with at most K+1 edges.",
  "explanation": "Init dist[src]=0. Repeat K+1 times: snapshot dist, for each edge (u,v,w) update newDist[v] = min(newDist[v], snapshot[u]+w). Return dist[dst] or -1 if unreachable. Snapshotting prevents using two edges in one pass.",
  "dry_run": "n=3, flights=[[0,1,100],[1,2,100],[0,2,500]], src=0, dst=2, K=1. Pass 1: dist=[0,100,500]. Pass 2: dist=[0,100,200]. Answer=200.",
  "approach": "Bellman-Ford with snapshot (cleanest) or Dijkstra with (cost, node, stops) state.",
  "complexity": "Time: O((K+1)·E). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findCheapestPrice(int n, vector<vector<int>>& f, int src, int dst, int k) {
    const int INF = 1e9;
    vector<int> dist(n, INF); dist[src] = 0;
    for (int i = 0; i <= k; ++i) {
        vector<int> nd = dist;
        for (auto& e : f) {
            if (dist[e[0]] == INF) continue;
            nd[e[1]] = min(nd[e[1]], dist[e[0]] + e[2]);
        }
        dist = nd;
    }
    return dist[dst] == INF ? -1 : dist[dst];
}""",
  "followups": "- Return the actual path.\n- Variant: at most K *hops* (edges).\n- Negative-weight edges (Bellman-Ford already handles)."
},

"Check if There Is a Valid Path in a Graph": {
  "concept": "Union-Find connectivity test between source and destination.",
  "intuition": "A valid path between two nodes exists iff they are in the same connected component. DSU answers this in near-constant time after processing all edges.",
  "explanation": "Build DSU over n nodes; union each edge's endpoints. Return find(source)==find(destination).",
  "dry_run": "n=3, edges=[[0,1],[1,2],[2,0]], src=0, dst=2. Union 0-1, 1-2, 2-0. find(0)==find(2) → true.",
  "approach": "DSU is simplest; BFS/DFS also works in O(V+E).",
  "complexity": "Time: O(V+E α). Space: O(V).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

bool validPath(int n, vector<vector<int>>& edges, int src, int dst) {
    DSU d(n);
    for (auto& e : edges) d.u(e[0], e[1]);
    return d.f(src) == d.f(dst);
}""",
  "followups": "- Return the actual path.\n- Shortest path (BFS).\n- Dynamic connectivity with deletions (harder)."
},

"Course Schedule II": {
  "concept": "Topological sort via Kahn's algorithm (BFS on in-degree).",
  "intuition": "Courses with prerequisites form a DAG. A valid order is any topological ordering. Kahn's BFS repeatedly takes zero-indegree nodes, yielding a valid order or detecting a cycle (when not all nodes processed).",
  "explanation": "Compute in-degree for each course. Queue all zero-indegree nodes. Pop, append to order, and for each outgoing edge decrement indegree — push if it hits 0. If final order size < n, return [] (cycle).",
  "dry_run": "n=4, prereqs=[[1,0],[2,0],[3,1],[3,2]]. In-deg: [0,1,1,2]. Queue {0}. Pop 0 → order=[0], decrement 1 and 2 to 0, push both. Pop 1 → order=[0,1], 3→1. Pop 2 → order=[0,1,2], 3→0, push. Pop 3 → order=[0,1,2,3].",
  "approach": "Kahn BFS — handles cycle detection naturally.",
  "complexity": "Time: O(V + E). Space: O(V + E).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> findOrder(int n, vector<vector<int>>& pre) {
    vector<vector<int>> g(n);
    vector<int> ind(n, 0);
    for (auto& p : pre) { g[p[1]].push_back(p[0]); ind[p[0]]++; }
    queue<int> q;
    for (int i = 0; i < n; ++i) if (!ind[i]) q.push(i);
    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        for (int v : g[u]) if (--ind[v] == 0) q.push(v);
    }
    return (int)order.size() == n ? order : vector<int>{};
}""",
  "followups": "- Course Schedule I (just detect feasibility).\n- DFS-based topo sort with cycle detection.\n- Parallel course scheduling — minimum semesters."
},

"Find Eventual Safe States": {
  "concept": "Topological sort on the reverse graph (or DFS with three-color marking).",
  "intuition": "A safe node leads only to terminal (no outgoing) or other safe nodes. Reverse edges and BFS from terminal nodes; any node reached is safe. Equivalently, nodes not on any cycle.",
  "explanation": "Reverse the graph. Start BFS from nodes with original out-degree 0. Decrement in the reversed graph's in-degree when their predecessors are processed. All processed nodes are safe.",
  "dry_run": "graph=[[1,2],[2,3],[5],[0],[5],[],[]] → safes are 2,4,5,6. Terminal 5,6 initially, then 2 (points only to 5), then 4 (points to 5).",
  "approach": "Reverse graph + Kahn, or three-color DFS (white/gray/black).",
  "complexity": "Time: O(V + E). Space: O(V + E).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> eventualSafeNodes(vector<vector<int>>& g) {
    int n = g.size();
    vector<vector<int>> rev(n);
    vector<int> outd(n);
    for (int u = 0; u < n; ++u) {
        outd[u] = g[u].size();
        for (int v : g[u]) rev[v].push_back(u);
    }
    queue<int> q;
    for (int i = 0; i < n; ++i) if (!outd[i]) q.push(i);
    vector<int> safe;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        safe.push_back(u);
        for (int v : rev[u]) if (--outd[v] == 0) q.push(v);
    }
    sort(safe.begin(), safe.end());
    return safe;
}""",
  "followups": "- Detect cycle nodes vs safe nodes.\n- Count of strongly connected components.\n- Nodes from which all paths end in a target set."
},

"Find the City With the Smallest Number of Neighbors": {
  "concept": "All-pairs shortest paths via Floyd-Warshall under distance threshold.",
  "intuition": "We want, for each city, how many others are within threshold distance. With small n (≤100), Floyd-Warshall O(n³) is fine. Count reachable cities per node and pick the city with the smallest count, breaking ties by larger index.",
  "explanation": "Init dist[i][i]=0, dist[u][v]=w for edges (both directions). For k,i,j: dist[i][j]=min(dist[i][j], dist[i][k]+dist[k][j]). For each node, count j with dist[i][j]<=threshold. Output the node with min count (largest index on tie).",
  "dry_run": "n=4, edges=[[0,1,3],[1,2,1],[1,3,4],[2,3,1]], threshold=4. After FW: from 3, neighbors within 4 = {1,2} (count 2). From 0, {1,2} (count 2). Tie → choose larger idx → 3.",
  "approach": "Floyd-Warshall then scan counts.",
  "complexity": "Time: O(n³). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findTheCity(int n, vector<vector<int>>& edges, int t) {
    const int INF = 1e9;
    vector<vector<int>> d(n, vector<int>(n, INF));
    for (int i=0;i<n;i++) d[i][i]=0;
    for (auto& e : edges) { d[e[0]][e[1]] = e[2]; d[e[1]][e[0]] = e[2]; }
    for (int k=0;k<n;k++) for (int i=0;i<n;i++) for (int j=0;j<n;j++)
        if (d[i][k]+d[k][j] < d[i][j]) d[i][j] = d[i][k]+d[k][j];
    int best = -1, cnt = INT_MAX;
    for (int i=0;i<n;i++) {
        int c = 0;
        for (int j=0;j<n;j++) if (i!=j && d[i][j]<=t) c++;
        if (c <= cnt) { cnt = c; best = i; }
    }
    return best;
}""",
  "followups": "- Use n Dijkstras for O(n·E log n).\n- What if threshold queries come online?\n- Maximize instead of minimize neighbor count."
},

"Find the Town Judge": {
  "concept": "In/out-degree counting.",
  "intuition": "The judge is trusted by n-1 people (in-degree n-1) and trusts nobody (out-degree 0). Track in- and out-degrees and find the node satisfying both.",
  "explanation": "For each trust (a,b): out[a]++, in[b]++. The judge i satisfies in[i]=n-1 and out[i]=0. If exactly one such exists, return it; else -1.",
  "dry_run": "n=3, trust=[[1,3],[2,3]]. in=[_,0,0,2], out=[_,1,1,0]. Node 3: in=2=n-1, out=0 → judge.",
  "approach": "Two arrays, one scan.",
  "complexity": "Time: O(n + E). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findJudge(int n, vector<vector<int>>& trust) {
    vector<int> score(n + 1, 0);
    for (auto& t : trust) { score[t[0]]--; score[t[1]]++; }
    for (int i = 1; i <= n; ++i) if (score[i] == n - 1) return i;
    return -1;
}""",
  "followups": "- Multiple judges (all nodes with in-degree n-1 and out-degree 0).\n- Trust chains (transitive).\n- Dynamic updates — does the judge change?"
},

"Is Graph Bipartite": {
  "concept": "Two-coloring via BFS/DFS.",
  "intuition": "A graph is bipartite iff nodes can be 2-colored so adjacent nodes differ in color. BFS from each unvisited node assigns alternating colors; a conflict means non-bipartite (odd cycle).",
  "explanation": "color[i] ∈ {0, 1, -1}. For each uncolored node start BFS: color root 0, for each neighbor assign opposite color and push. If a neighbor is already colored the same, return false.",
  "dry_run": "graph=[[1,3],[0,2],[1,3],[0,2]]. BFS from 0: color 0=A, 1=B, 3=B. From 1: color 2=A. No conflict → true.",
  "approach": "BFS coloring across all components.",
  "complexity": "Time: O(V+E). Space: O(V).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool isBipartite(vector<vector<int>>& g) {
    int n = g.size();
    vector<int> col(n, -1);
    for (int s = 0; s < n; ++s) if (col[s] == -1) {
        queue<int> q; q.push(s); col[s] = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v : g[u]) {
                if (col[v] == -1) { col[v] = 1 - col[u]; q.push(v); }
                else if (col[v] == col[u]) return false;
            }
        }
    }
    return true;
}""",
  "followups": "- Find the two partitions.\n- DSU-based check.\n- k-colorability (NP-hard for k≥3)."
},

"Keys and Rooms": {
  "concept": "BFS/DFS connectivity from room 0.",
  "intuition": "Treat rooms as nodes and keys as directed edges. Can we reach all rooms from room 0? Standard traversal.",
  "explanation": "DFS from 0, marking visited rooms. Each visit pushes all keys found. At end, check all rooms visited.",
  "dry_run": "rooms=[[1],[2],[3],[]]. DFS 0→1→2→3. All visited → true.",
  "approach": "Iterative DFS using a stack.",
  "complexity": "Time: O(V+E). Space: O(V).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool canVisitAllRooms(vector<vector<int>>& rooms) {
    int n = rooms.size();
    vector<int> seen(n, 0);
    stack<int> st; st.push(0); seen[0] = 1;
    int cnt = 1;
    while (!st.empty()) {
        int u = st.top(); st.pop();
        for (int v : rooms[u]) if (!seen[v]) { seen[v] = 1; cnt++; st.push(v); }
    }
    return cnt == n;
}""",
  "followups": "- Minimum keys to visit all rooms.\n- Variant: each key unlocks once.\n- Weighted: time cost per room."
},

"Knight Probability in Chessboard": {
  "concept": "DP over (moves_left, row, col) with transitions over 8 knight moves.",
  "intuition": "Probability of staying on board after k moves from (r,c) is average over 8 legal moves of the probability from those positions after k-1 moves. Base: p(0, r, c) = 1 if in-board else 0.",
  "explanation": "Let f(k, r, c) = probability. Transition: f(k, r, c) = (1/8) Σ f(k-1, r', c') over 8 moves (counting off-board as 0). Bottom-up DP over two layers.",
  "dry_run": "n=3, k=2, start (0,0). From (0,0) knight has 2 in-board moves: (1,2) and (2,1). Each contributes 1/8 * p(1,...). Expand recursively until 0 moves.",
  "approach": "DP with two 2D layers, rolling.",
  "complexity": "Time: O(k·n²). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
double knightProbability(int n, int k, int r, int c) {
    vector<vector<double>> dp(n, vector<double>(n, 0));
    dp[r][c] = 1.0;
    int dr[] = {-2,-2,-1,-1,1,1,2,2}, dc[] = {-1,1,-2,2,-2,2,-1,1};
    for (int step = 0; step < k; ++step) {
        vector<vector<double>> nd(n, vector<double>(n, 0));
        for (int i=0;i<n;i++) for (int j=0;j<n;j++) if (dp[i][j] > 0) {
            for (int m=0;m<8;m++) {
                int ni=i+dr[m], nj=j+dc[m];
                if (ni>=0&&nj>=0&&ni<n&&nj<n) nd[ni][nj] += dp[i][j] / 8.0;
            }
        }
        dp = nd;
    }
    double s = 0;
    for (auto& row : dp) for (double v : row) s += v;
    return s;
}""",
  "followups": "- Expected number of steps to leave the board.\n- Probability of reaching a target cell in ≤k moves.\n- Variable-size board."
},

"Max Area of Island": {
  "concept": "DFS flood-fill counting connected land cells.",
  "intuition": "Each island is a 4-connected component of 1s. DFS/BFS from each unvisited 1 cell to count its size; track the max.",
  "explanation": "Iterate cells. On a 1, launch DFS marking cells as visited (or flip to 0) and counting. Update the global max area.",
  "dry_run": "grid=[[1,1,0],[0,1,0],[0,0,1]]. From (0,0) DFS visits (0,0),(0,1),(1,1) → area 3. From (2,2) area 1. Max=3.",
  "approach": "DFS with boundary and visited checks.",
  "complexity": "Time: O(n·m). Space: O(n·m) stack.",
  "code": """#include <bits/stdc++.h>
using namespace std;
int maxAreaOfIsland(vector<vector<int>>& g) {
    int n = g.size(), m = g[0].size(), best = 0;
    function<int(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||!g[r][c]) return 0;
        g[r][c] = 0;
        return 1 + dfs(r+1,c) + dfs(r-1,c) + dfs(r,c+1) + dfs(r,c-1);
    };
    for (int i=0;i<n;i++) for (int j=0;j<m;j++)
        if (g[i][j]) best = max(best, dfs(i,j));
    return best;
}""",
  "followups": "- Count number of islands instead.\n- 8-connected instead of 4-connected.\n- Find the island containing a given cell."
},

"Most Stones Removed with Same Row or Column": {
  "concept": "DSU grouping stones that share a row or column; answer is n - components.",
  "intuition": "Stones in the same row/column can all be removed except one (you need one stone remaining as the last). So within each connected group (via shared row/column) you remove size-1 stones. Total = n - #components.",
  "explanation": "Union stones that share a row or column (map each row/column index to its first stone). Count DSU components. Answer = n - components.",
  "dry_run": "stones = [[0,0],[0,1],[1,0],[1,2],[2,1],[2,2]]. All in one component → answer = 6 - 1 = 5.",
  "approach": "DSU over stone indices with row/column index mapping.",
  "complexity": "Time: O(n α). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

int removeStones(vector<vector<int>>& s) {
    int n = s.size();
    DSU d(n);
    unordered_map<int,int> rowMap, colMap;
    for (int i = 0; i < n; ++i) {
        int r = s[i][0], c = s[i][1];
        if (rowMap.count(r)) d.u(i, rowMap[r]); else rowMap[r] = i;
        if (colMap.count(c)) d.u(i, colMap[c]); else colMap[c] = i;
    }
    int comps = 0;
    for (int i = 0; i < n; ++i) if (d.f(i) == i) comps++;
    return n - comps;
}""",
  "followups": "- Maximum stones removed given removal constraints.\n- Weighted stones.\n- Queries on dynamic stone addition/removal."
},

"Network Delay Time": {
  "concept": "Single-source shortest path (Dijkstra).",
  "intuition": "Signal propagates to all reachable nodes; the total time is the max of shortest distances from k. If any node is unreachable, return -1.",
  "explanation": "Build adjacency with weights. Run Dijkstra from k. After relaxation, the answer is max of dist[] if all are finite, else -1.",
  "dry_run": "times=[[2,1,1],[2,3,1],[3,4,1]], k=2. dist[2]=0, [1]=1, [3]=1, [4]=2. Max=2.",
  "approach": "Standard min-heap Dijkstra.",
  "complexity": "Time: O((V+E) log V). Space: O(V+E).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int networkDelayTime(vector<vector<int>>& times, int n, int k) {
    vector<vector<pair<int,int>>> g(n + 1);
    for (auto& t : times) g[t[0]].push_back({t[1], t[2]});
    vector<int> dist(n + 1, INT_MAX); dist[k] = 0;
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, k});
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d > dist[u]) continue;
        for (auto [v, w] : g[u]) if (d + w < dist[v]) {
            dist[v] = d + w; pq.push({dist[v], v});
        }
    }
    int ans = 0;
    for (int i = 1; i <= n; ++i) {
        if (dist[i] == INT_MAX) return -1;
        ans = max(ans, dist[i]);
    }
    return ans;
}""",
  "followups": "- Weighted with negative edges → Bellman-Ford.\n- Return the actual delay tree.\n- Multiple sources → multi-source Dijkstra."
},

"Number of Enclaves": {
  "concept": "Flood-fill from border land cells and count remaining interior land.",
  "intuition": "Enclaves are land cells that cannot reach the boundary. Remove all land connected to the border; what remains are enclaves.",
  "explanation": "DFS/BFS from every boundary cell that is 1, marking connected land as 0. Then count total 1s remaining.",
  "dry_run": "grid=[[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]. Border cells: no 1 on border. So all interior 1s are enclaves → count = 4.",
  "approach": "Border DFS then scan.",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numEnclaves(vector<vector<int>>& g) {
    int n = g.size(), m = g[0].size();
    function<void(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||!g[r][c]) return;
        g[r][c] = 0;
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);
    };
    for (int i=0;i<n;i++) { dfs(i,0); dfs(i,m-1); }
    for (int j=0;j<m;j++) { dfs(0,j); dfs(n-1,j); }
    int cnt = 0;
    for (auto& r : g) for (int v : r) cnt += v;
    return cnt;
}""",
  "followups": "- Variation where diagonal moves allowed.\n- Count of separate enclave components.\n- Largest enclave."
},

"Number of Islands": {
  "concept": "Count connected components of 1s via DFS/BFS.",
  "intuition": "Each island is a 4-connected component. Iterate all cells; whenever we hit an unvisited 1, flood-fill the whole island and increment a counter.",
  "explanation": "DFS from each unvisited land cell, marking visited by setting '1'→'0'. Each DFS launch counts as one island.",
  "dry_run": "grid=[['1','1','0'],['0','1','0'],['0','0','1']]. From (0,0) flood {(0,0),(0,1),(1,1)} → 1 island. From (2,2) → 2 islands.",
  "approach": "DFS; could use BFS to avoid deep recursion.",
  "complexity": "Time: O(n·m). Space: O(n·m) in the worst case.",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numIslands(vector<vector<char>>& g) {
    int n = g.size(), m = g[0].size(), cnt = 0;
    function<void(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||g[r][c]!='1') return;
        g[r][c] = '0';
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);
    };
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (g[i][j]=='1') { cnt++; dfs(i,j); }
    return cnt;
}""",
  "followups": "- Variant with 8-connectivity.\n- Count islands in a streamed grid (add land operations).\n- Largest island."
},

"Redundant Connection": {
  "concept": "Union-Find — first edge whose endpoints are already connected creates a cycle.",
  "intuition": "A tree on n nodes has n-1 edges. The input has n edges → exactly one extra edge creates a cycle. That's the one whose endpoints are already in the same DSU component.",
  "explanation": "Iterate edges in order; for each edge, if find(u)==find(v), return it. Otherwise union.",
  "dry_run": "edges=[[1,2],[1,3],[2,3]]. Union 1-2, 1-3. On (2,3): find(2)==find(3) → return [2,3].",
  "approach": "Single DSU pass.",
  "complexity": "Time: O(N α). Space: O(N).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} };

vector<int> findRedundantConnection(vector<vector<int>>& edges) {
    DSU d(edges.size() + 1);
    for (auto& e : edges) {
        int a = d.f(e[0]), b = d.f(e[1]);
        if (a == b) return e;
        d.p[a] = b;
    }
    return {};
}""",
  "followups": "- Directed variant (Redundant Connection II).\n- If multiple cycles exist, find the earliest/latest.\n- Weighted: remove the heaviest edge in the cycle."
},

"Rotting Oranges": {
  "concept": "Multi-source BFS from all rotten oranges simultaneously.",
  "intuition": "Every minute the infection spreads one step in all directions from every rotten orange. BFS level = minute. Answer is the last level that changed state.",
  "explanation": "Push all rotten cells at time 0. BFS expands to fresh neighbors, marking them rotten with time+1. After BFS, if any fresh remains → -1, else return max time observed.",
  "dry_run": "grid=[[2,1,1],[1,1,0],[0,1,1]]. Minute 0: (0,0). Minute 1: (0,1),(1,0). Minute 2: (0,2),(1,1). Minute 3: (2,1). Minute 4: (2,2). Answer=4.",
  "approach": "BFS with level tracking and fresh-count.",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int orangesRotting(vector<vector<int>>& g) {
    int n=g.size(), m=g[0].size(), fresh=0, minutes=0;
    queue<pair<int,int>> q;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) {
        if (g[i][j]==2) q.push({i,j});
        else if (g[i][j]==1) fresh++;
    }
    int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1};
    while (!q.empty() && fresh) {
        int sz = q.size(); minutes++;
        while (sz--) {
            auto [r,c] = q.front(); q.pop();
            for (int k=0;k<4;k++) {
                int nr=r+dr[k], nc=c+dc[k];
                if (nr<0||nc<0||nr>=n||nc>=m||g[nr][nc]!=1) continue;
                g[nr][nc]=2; fresh--; q.push({nr,nc});
            }
        }
    }
    return fresh ? -1 : minutes;
}""",
  "followups": "- Infection with variable speed per cell.\n- Source selection — minimize infection time with k sources.\n- 3D rotting grid."
},

"Satisfiability of Equality Equations": {
  "concept": "Union-Find — union equals, then check inequalities for contradictions.",
  "intuition": "Equalities form equivalence classes. Inequalities must separate classes. Process equalities first to build classes, then verify each inequality has endpoints in different classes.",
  "explanation": "For each '==' equation union the two variables. For each '!=' equation ensure find(a) != find(b). If any fails, return false.",
  "dry_run": "['a==b','b!=a']. Union a,b. Check a!=b: find(a)==find(b) → false.",
  "approach": "Two-pass DSU over 26 lowercase letters.",
  "complexity": "Time: O(N α). Space: O(26).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

bool equationsPossible(vector<string>& eq) {
    DSU d(26);
    for (auto& e : eq) if (e[1]=='=') d.u(e[0]-'a', e[3]-'a');
    for (auto& e : eq) if (e[1]=='!' && d.f(e[0]-'a')==d.f(e[3]-'a')) return false;
    return true;
}""",
  "followups": "- Generalize to arbitrary variable names.\n- Arithmetic relations (a - b = k).\n- Incremental online constraints."
},

"Shortest Path in Binary Matrix": {
  "concept": "BFS in 8-directional grid.",
  "intuition": "Unweighted shortest path → BFS. From (0,0), expand to 8-direction neighbors that are 0, recording distance.",
  "explanation": "If start or end is 1 return -1. BFS from (0,0) with dist=1. Expand 8 neighbors; when reaching (n-1,n-1), return dist.",
  "dry_run": "grid=[[0,0,0],[1,1,0],[1,1,0]]. Path (0,0)→(0,1)→(0,2)→(1,2)→(2,2). Distance 5.",
  "approach": "BFS with 8 moves and grid cell marking.",
  "complexity": "Time: O(n²). Space: O(n²).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int shortestPathBinaryMatrix(vector<vector<int>>& g) {
    int n = g.size();
    if (g[0][0] || g[n-1][n-1]) return -1;
    queue<tuple<int,int,int>> q; q.push({0,0,1});
    g[0][0] = 1;
    int dr[] = {-1,-1,-1,0,0,1,1,1}, dc[] = {-1,0,1,-1,1,-1,0,1};
    while (!q.empty()) {
        auto [r,c,d] = q.front(); q.pop();
        if (r==n-1 && c==n-1) return d;
        for (int k=0;k<8;k++) {
            int nr=r+dr[k], nc=c+dc[k];
            if (nr<0||nc<0||nr>=n||nc>=n||g[nr][nc]) continue;
            g[nr][nc] = 1; q.push({nr,nc,d+1});
        }
    }
    return -1;
}""",
  "followups": "- Weighted cells — Dijkstra.\n- A* with Chebyshev heuristic.\n- Multi-goal shortest path."
},

"Surrounded Regions": {
  "concept": "Flood-fill from boundary Os to identify safe ones; flip the rest.",
  "intuition": "An 'O' is surrounded iff it cannot escape to the boundary. Mark all 'O's reachable from the boundary as safe; flip all other 'O's to 'X'.",
  "explanation": "DFS/BFS from every boundary 'O', marking as temporary '#'. Then scan: '#' → 'O' (safe), 'O' → 'X' (surrounded).",
  "dry_run": "board=[['X','X','X','X'],['X','O','O','X'],['X','X','O','X'],['X','O','X','X']]. Border O at (3,1) only is safe. Others flipped to X.",
  "approach": "Two passes after boundary DFS.",
  "complexity": "Time: O(n·m). Space: O(n·m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
void solve(vector<vector<char>>& b) {
    int n = b.size(), m = b[0].size();
    function<void(int,int)> dfs = [&](int r, int c) {
        if (r<0||c<0||r>=n||c>=m||b[r][c]!='O') return;
        b[r][c] = '#';
        dfs(r+1,c); dfs(r-1,c); dfs(r,c+1); dfs(r,c-1);
    };
    for (int i=0;i<n;i++) { dfs(i,0); dfs(i,m-1); }
    for (int j=0;j<m;j++) { dfs(0,j); dfs(n-1,j); }
    for (int i=0;i<n;i++) for (int j=0;j<m;j++)
        b[i][j] = (b[i][j]=='#' ? 'O' : 'X');
}""",
  "followups": "- In-place variant with constant extra memory.\n- 8-connected variant.\n- Detect number of surrounded regions."
},

"Count Primes": {
  "concept": "Sieve of Eratosthenes.",
  "intuition": "Start from 2; for each prime, mark its multiples composite. What remains unmarked below n are primes.",
  "explanation": "Create isComposite[n] = false. For i from 2 to sqrt(n): if !isComposite[i], mark i*i, i*i+i, ... up to n-1. Count unmarked indices from 2..n-1.",
  "dry_run": "n=10. i=2: mark 4,6,8. i=3: mark 9. Unmarked 2..9: 2,3,5,7 → 4 primes.",
  "approach": "Classic sieve.",
  "complexity": "Time: O(n log log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int countPrimes(int n) {
    if (n < 3) return 0;
    vector<char> comp(n, 0);
    int cnt = 0;
    for (int i = 2; i < n; ++i) {
        if (comp[i]) continue;
        cnt++;
        if ((long long)i * i < n)
            for (int j = i*i; j < n; j += i) comp[j] = 1;
    }
    return cnt;
}""",
  "followups": "- Segmented sieve for huge n.\n- Prime factorization using smallest-prime-factor array.\n- Count primes in a range [L,R]."
},

"Minimum Weight Cycle": {
  "concept": "For each edge (u,v,w), remove it and compute shortest u→v path; answer = min over edges of (w + shortest_path).",
  "intuition": "A minimum-weight cycle must contain at least one edge; enumerating each possible 'closing' edge and finding the shortest alternative route yields the minimum cycle weight.",
  "explanation": "For each edge (u,v,w): temporarily remove it, run Dijkstra from u to v, cycle weight = w + dist. Track minimum. Return INF if no cycle.",
  "dry_run": "Edges {(0,1,1),(1,2,1),(2,0,3)}. Remove (0,1,1): path 0→2→1 = 4, cycle=5. Remove (1,2,1): 1→0→2=4, cycle=5. Remove (2,0,3): 2→1→0=2, cycle=5. Answer=5.",
  "approach": "O(E · (V+E) log V). For small graphs use Floyd-Warshall based O(V³).",
  "complexity": "Time: O(V·E log V) with Dijkstra.",
  "code": """#include <bits/stdc++.h>
using namespace std;
int dijk(vector<vector<pair<int,int>>>& g, int s, int t, int banU, int banV) {
    int n = g.size();
    vector<int> d(n, INT_MAX); d[s] = 0;
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, s});
    while (!pq.empty()) {
        auto [dd, u] = pq.top(); pq.pop();
        if (dd > d[u]) continue;
        for (auto [v, w] : g[u]) {
            if ((u==banU && v==banV) || (u==banV && v==banU)) continue;
            if (dd + w < d[v]) { d[v] = dd + w; pq.push({d[v], v}); }
        }
    }
    return d[t];
}
int minWeightCycle(int n, vector<vector<int>>& edges) {
    vector<vector<pair<int,int>>> g(n);
    for (auto& e : edges) { g[e[0]].push_back({e[1], e[2]}); g[e[1]].push_back({e[0], e[2]}); }
    int best = INT_MAX;
    for (auto& e : edges) {
        int d = dijk(g, e[0], e[1], e[0], e[1]);
        if (d != INT_MAX) best = min(best, d + e[2]);
    }
    return best;
}""",
  "followups": "- Directed graph minimum cycle.\n- Only positive weights guaranteed? Use BFS for unweighted.\n- Minimum mean cycle (Karp's algorithm)."
},

"Find the Smallest Binary Digit Multiple of Given Number": {
  "concept": "BFS over remainders mod n with digits 0 and 1.",
  "intuition": "Numbers consisting only of 0/1 digits form a tree. BFS by appending '0' or '1' and tracking remainder mod n. The first remainder 0 we reach (with leading '1') gives the minimal-length answer.",
  "explanation": "Start with '1' remainder 1%n. BFS: from (rem, num_str), expand to (rem*10 % n, num+'0') and (rem*10+1 % n, num+'1'). Mark remainders visited. Return the string when rem==0.",
  "dry_run": "n=4. Start '1' rem=1. Expand '10' rem=2, '11' rem=3. Expand '100' rem=0 → return '100'.",
  "approach": "BFS with remainder memoization — at most n states.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
string smallestBinaryMultiple(int n) {
    queue<pair<int,string>> q; q.push({1 % n, \"1\"});
    vector<int> seen(n, 0); seen[1 % n] = 1;
    while (!q.empty()) {
        auto [r, s] = q.front(); q.pop();
        if (r == 0) return s;
        for (int d : {0, 1}) {
            int nr = (r * 10 + d) % n;
            if (!seen[nr]) { seen[nr] = 1; q.push({nr, s + char('0'+d)}); }
        }
    }
    return \"\";
}""",
  "followups": "- Multiples of n with digits only 0 and k.\n- Smallest multiple with sum of digits ≤ s.\n- Modular BFS general technique."
},

"Number of Operations to Make Network Connected (dup)": {
  "concept": "Duplicate of earlier problem — see the first entry.",
  "intuition": "Same as 'Number of Operations to Make Network Connected': DSU; components-1 moves if enough extra cables.",
  "explanation": "Count components via DSU; count extra edges (those that would form a cycle). If extras >= components-1, answer = components-1; else -1.",
  "dry_run": "See 'Number of Operations to Make Network Connected'.",
  "approach": "Union-Find.",
  "complexity": "Time: O(E α). Space: O(n).",
  "code": """// See 'Number of Operations to Make Network Connected' implementation above.""",
  "followups": "- See original entry."
},

"Number of Provinces": {
  "concept": "Connected components in an adjacency matrix.",
  "intuition": "Cities directly or transitively connected form a province. Count components using DFS or DSU.",
  "explanation": "Iterate cities; for each unvisited city, DFS all connected ones and mark visited. Each DFS launch = +1 province.",
  "dry_run": "isConnected=[[1,1,0],[1,1,0],[0,0,1]]. From 0 visit 0,1. From 2 visit 2. Provinces=2.",
  "approach": "DFS or DSU over n×n.",
  "complexity": "Time: O(n²). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findCircleNum(vector<vector<int>>& g) {
    int n = g.size(); vector<int> seen(n, 0); int cnt = 0;
    function<void(int)> dfs = [&](int u) {
        seen[u] = 1;
        for (int v = 0; v < n; ++v) if (g[u][v] && !seen[v]) dfs(v);
    };
    for (int i = 0; i < n; ++i) if (!seen[i]) { cnt++; dfs(i); }
    return cnt;
}""",
  "followups": "- With adjacency list to avoid O(n²).\n- Dynamic province counting as edges arrive/leave.\n- Province with largest population."
},

"Shortest Path in an Undirected Graph": {
  "concept": "Unweighted BFS from source.",
  "intuition": "BFS layers correspond to hop-counts. The shortest path length from s to any node is the level it's first dequeued.",
  "explanation": "Initialize dist[s]=0, others -1. BFS; for each neighbor with dist==-1 set dist = dist[u]+1 and enqueue.",
  "dry_run": "Graph 0-1-2, 0-3. BFS from 0: level 0 {0}, level 1 {1,3}, level 2 {2}. dist=[0,1,2,1].",
  "approach": "Standard BFS.",
  "complexity": "Time: O(V+E). Space: O(V).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> shortestPath(int n, vector<vector<int>>& edges, int src) {
    vector<vector<int>> g(n);
    for (auto& e : edges) { g[e[0]].push_back(e[1]); g[e[1]].push_back(e[0]); }
    vector<int> d(n, -1); d[src] = 0;
    queue<int> q; q.push(src);
    while (!q.empty()) {
        int u = q.front(); q.pop();
        for (int v : g[u]) if (d[v] == -1) { d[v] = d[u] + 1; q.push(v); }
    }
    return d;
}""",
  "followups": "- Return parent pointers to reconstruct paths.\n- Weighted variant uses Dijkstra.\n- BFS from multiple sources."
},
}
