# Accounts Merge

## Problem Link
https://leetcode.com/problems/accounts-merge/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
DSU on emails — union emails sharing an account, group by root.

## Intuition
Each account gives a list of emails that should be in the same component. Union all emails within one account. Then group emails by DSU root and attach each group's name.

## Detailed Explanation
Map each unique email to an id. For each account, union all its emails with the first. Also map email→name. After processing, group emails by DSU root; sort each group; prepend the owner's name.

## Dry Run
Accounts: [John, a@, b@], [John, b@, c@], [Mary, x@]. Union a-b, b-c → {a,b,c} component. Group {a@,b@,c@} → John. {x@} → Mary. Output two accounts.

## Approach
DSU with string-id mapping; careful with sorting emails within each group.

## Time and Space Complexity
Time: O(N log N α) where N is total emails. Space: O(N).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
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
}
```

## Follow-up Questions
- Very large datasets — can we avoid string interning overhead?
- Streamed accounts — incremental merges.
- Detect and split accidental merges (quality checks).
