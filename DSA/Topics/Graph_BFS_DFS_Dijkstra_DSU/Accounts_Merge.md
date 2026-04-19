# Accounts Merge

**Problem Link:**
https://leetcode.com/problems/accounts-merge/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Problem Carefully

Each input "account" is a list: `[name, email1, email2, ...]`. Two accounts belong to the **same person** if they share at least one email. Multiple accounts could belong to the same person (with overlapping emails).

Task: merge accounts belonging to the same person. Output each merged account as `[name, sorted_unique_emails...]`.

Example:
```
[
  ["John", "john@mail.com", "j@mail.com"],
  ["John", "john@mail.com", "work@mail.com"],
  ["Mary", "mary@mail.com"]
]
```

The first two accounts share `"john@mail.com"`, so they're the same person. Merge them.

Result:
```
[
  ["John", "j@mail.com", "john@mail.com", "work@mail.com"],
  ["Mary", "mary@mail.com"]
]
```

Two key observations:
- Names can repeat. Two people could both be named "John" but have different emails.
- Emails are the identifiers for merging.

----------------------------------------

## Step 2: Think About What's Really Being Merged

If I think of emails as **nodes**, and "email A and email B both appear in the same account" as an **edge**, then merging accounts is the same as finding **connected components** in this email graph.

For the example, the email graph has:
- Edge between `john@` and `j@` (they're in account 1).
- Edge between `john@` and `work@` (account 2).
- `mary@` — no edges.

Connected components: {john@, j@, work@} and {mary@}. Each component represents one person's emails.

Now this is a classic graph problem: given edges, find connected components.

----------------------------------------

## Step 3: How to Find Connected Components

Three standard tools:
- **Union-Find (DSU):** elegant for "incrementally merge, then query components."
- **BFS/DFS:** build the graph explicitly, traverse each component.
- **Iterative union via sets:** merge sets when they share elements — doable but tricky to make efficient.

Let me think about which fits naturally.

The edges here are implicit in the input structure. Each account with k emails gives k-1 edges (union each email with the first in that account, say). So we never literally enumerate all pairs — just pick one representative per account and union the rest with it.

With DSU, after processing all accounts, each email's root tells us its component. Then group emails by root, attach the name, sort, output.

----------------------------------------

## Step 4: The Plan

1. Assign an integer ID to each unique email (use a hashmap `email -> id`).
2. Record each email's name (`email -> name`). Same email might appear in multiple accounts; we just overwrite — the name is the same because it belongs to one person (and the problem guarantees names are consistent within a merged account).
3. For each account, pick the first email as representative and union all others with it.
4. Group emails by their DSU root.
5. For each group, sort emails alphabetically, prepend the name, output.

----------------------------------------

## Step 5: Trace on the Example

Accounts:
```
A0 = ["John", "john@", "j@"]
A1 = ["John", "john@", "work@"]
A2 = ["Mary", "mary@"]
```

**Step 1: Email → ID map.**
- `john@` → 0. name[john@] = John.
- `j@` → 1. name[j@] = John.
- `work@` → 2. name[work@] = John.
- `mary@` → 3. name[mary@] = Mary.

**Step 2: Union emails within each account.**
- A0: union(0, 1).
- A1: union(0, 2).
- A2: singleton, no unions.

After unions: {0, 1, 2} in one component, {3} alone.

**Step 3: Group by root.**
- Root of 0, 1, 2: say 0 (depending on DSU details). Component {0, 1, 2}.
- Root of 3: 3. Component {3}.

**Step 4: Build output.**
- Component {0, 1, 2}: emails [john@, j@, work@]. Sort: [j@, john@, work@]. Prepend name "John": ["John", "j@", "john@", "work@"].
- Component {3}: ["Mary", "mary@"].

Matches expected. ✓

----------------------------------------

## Step 6: Why Union-Find Is a Great Fit

Each account gives us "these emails are in the same component." DSU is literally designed for "tell me two things are equivalent, then I'll answer connectivity queries." Perfect match.

The alternative — building an explicit graph and BFS/DFSing — also works but requires more code: construct adjacency list, then one traversal per component, then group.

DSU is more compact and more naturally incremental. I'd pick DSU for this.

----------------------------------------

## Step 7: Name the Pattern

This is **DSU for connected-components discovery**. Similar applications:
- Friends-of-friends groups.
- Component detection after incremental edge additions.
- Redundant Connection (previous problem).
- Kruskal's MST.
- Satisfiability of Equality Equations.

The trigger: "merge items that share a property, then report groups."

----------------------------------------

## Step 8: Complexity

Let N = total number of emails (across all accounts).

Time:
- Step 1 (email → ID map): O(N).
- Step 2 (unions): O(N · α(N)) — one union per email (minus a few).
- Step 3 (grouping): O(N · α(N)) — one find per email.
- Step 4 (sorting emails within each component): O(N log N) total across all components.

Overall: **O(N log N)** — dominated by the sorting step.

Space: **O(N)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);
        return parent[x];
    }
    void unite(int a, int b) {
        a = find(a); b = find(b);
        if (a != b) parent[a] = b;
    }
};

vector<vector<string>> accountsMerge(vector<vector<string>>& accounts) {
    unordered_map<string, int> emailId;
    unordered_map<string, string> emailName;
    int cnt = 0;

    // Assign IDs and record names.
    for (auto& acc : accounts) {
        const string& name = acc[0];
        for (int i = 1; i < (int)acc.size(); ++i) {
            if (!emailId.count(acc[i])) {
                emailId[acc[i]] = cnt++;
                emailName[acc[i]] = name;
            }
        }
    }

    DSU dsu(cnt);

    // Union emails within each account (link each to the first email).
    for (auto& acc : accounts) {
        int firstId = emailId[acc[1]];
        for (int i = 2; i < (int)acc.size(); ++i) {
            dsu.unite(firstId, emailId[acc[i]]);
        }
    }

    // Group emails by root.
    unordered_map<int, vector<string>> groups;
    for (auto& [email, id] : emailId) {
        groups[dsu.find(id)].push_back(email);
    }

    // Build output: each group gets its emails sorted + name prepended.
    vector<vector<string>> result;
    for (auto& [root, emails] : groups) {
        sort(emails.begin(), emails.end());
        vector<string> entry = {emailName[emails[0]]};
        entry.insert(entry.end(), emails.begin(), emails.end());
        result.push_back(entry);
    }
    return result;
}
```

Implementation notes:
- We use a basic DSU with path compression. Union-by-rank would squeeze out a bit more performance but isn't needed for this problem's size.
- Names are recorded per email but are guaranteed consistent within a component (problem spec).
- Sorting happens per-group, which is cheaper than sorting all emails globally.

----------------------------------------

## Step 10: Follow-up Questions

- **Huge numbers of accounts.** The algorithm is O(N log N); scales fine to millions.
- **Emails might have slight typos (johnSmith@ vs john.smith@).** Preprocess to canonicalize emails before merging.
- **What if merging requires more than one shared email** (e.g., at least two overlapping)? Different problem — harder; can't use simple DSU.
- **What if names could differ within a merged account (indicating different people with same emails)?** Problem becomes ambiguous; the definition of "same person" would need revisiting.
- **Streaming: accounts arrive over time.** DSU handles this naturally — just process each new account as it comes.
- **Graph approach (BFS) instead.** Build adjacency list, do BFS from each unvisited email. O(N) traversal. Similar total complexity.
