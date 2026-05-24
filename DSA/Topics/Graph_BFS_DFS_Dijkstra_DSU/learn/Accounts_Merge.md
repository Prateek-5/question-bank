# Accounts Merge — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Accounts_Merge.md`](../Accounts_Merge.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/accounts-merge/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: model EMAILS as nodes, "shared in same account" as edges → find CONNECTED COMPONENTS. DSU is the clean tool: for each account, union all its emails with the first one. At the end, group by root, sort, prepend name.**

**Map of this file (9 sections):**

1. Read the problem
2. The emails-as-graph reframe
3. Union strategy — link to first email per account
4. The 4-step algorithm
5. Code
6. Trace it
7. Why DSU over BFS here
8. Common pitfalls
9. The shape — DSU for component discovery

---

## 1. Read the problem

Each account is a list `[name, email1, email2, ...]`. Two accounts belong to the SAME person if they share at least one email. Merge all accounts of the same person. Output: each merged account as `[name, sorted_unique_emails...]`.

**Example:**

```
[
  ["John", "john@mail.com", "j@mail.com"],
  ["John", "john@mail.com", "work@mail.com"],
  ["Mary", "mary@mail.com"]
]
```

Account 0 and Account 1 share `john@mail.com` → same person.

Result:
```
[
  ["John", "j@mail.com", "john@mail.com", "work@mail.com"],
  ["Mary", "mary@mail.com"]
]
```

Note: names can REPEAT across different people — emails are the identifiers.

---

## 2. The emails-as-graph reframe

> **Mini-refresher: treat emails as nodes, "in same account" as edges.**
>
> Two emails are connected iff they appear in the same account. Two accounts are merged iff their email sets are in the same CONNECTED COMPONENT.
>
> This converts a messy "merge accounts by overlap" problem into a clean "find connected components on emails" problem.

---

## 3. Union strategy — link to first email per account

For account `[name, e1, e2, e3, ...]`, we don't need to union every pair. Just union e2 with e1, e3 with e1, etc. All of e1..ek end up in one component (transitively).

Number of unions per account = (emails in account) - 1. Total unions = O(N) where N is the total email count.

---

## 4. The 4-step algorithm

```
1. Build email → unique integer ID. Also record email → name.
2. For each account: union all its emails with the first one.
3. Group emails by DSU root.
4. For each group: sort emails, prepend name (from any email in the group).
```

---

## 5. Code

**C++:**

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
    for (auto& acc : accounts) {
        int firstId = emailId[acc[1]];
        for (int i = 2; i < (int)acc.size(); ++i) {
            dsu.unite(firstId, emailId[acc[i]]);
        }
    }

    unordered_map<int, vector<string>> groups;
    for (auto& [email, id] : emailId) {
        groups[dsu.find(id)].push_back(email);
    }

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

Complexity: **O(N log N)** time (dominated by per-component sorting), **O(N)** space.

---

## 6. Trace it

Accounts:
```
A0 = ["John", "john@", "j@"]
A1 = ["John", "john@", "work@"]
A2 = ["Mary", "mary@"]
```

**Step 1: assign IDs.**
- john@ → 0, j@ → 1, work@ → 2, mary@ → 3.
- emailName = {john@: John, j@: John, work@: John, mary@: Mary}.

**Step 2: union within each account.**
- A0: union(0, 1) (john@ with j@).
- A1: union(0, 2) (john@ with work@).
- A2: only one email — no unions.

DSU state: {0, 1, 2} in one group, {3} alone.

**Step 3: group by root.**
- find(0), find(1), find(2) → all same root → group [john@, j@, work@].
- find(3) → group [mary@].

**Step 4: sort + prepend name.**
- Group 1: sorted [j@, john@, work@]. name = John. → ["John", "j@", "john@", "work@"].
- Group 2: ["Mary", "mary@"].

Matches expected.  ✓

---

## 7. Why DSU over BFS here

| Aspect | DSU | BFS |
|---|---|---|
| Code length | ~15 lines | ~25 lines (explicit graph + traversal) |
| Naturally incremental | yes | needs precomputed graph |
| Edge enumeration | implicit (union within account) | explicit (per-account adjacency) |
| Complexity | O(N · α(N) + N log N) | O(N + N log N) |

Either works; DSU is more compact and the union pattern fits the "one element per account links to rep" structure beautifully.

---

## 8. Common pitfalls

1. **Storing names by account-index instead of by email.** Names are consistent within a person's accounts, but it's cleaner to attach the name to any email in the group.
2. **Sorting all emails globally before grouping.** Wastes time — sort within each component.
3. **Using `dsu.find(emailId[email])` lazily in the hash key.** Be careful: hash maps don't auto-update when DSU updates — group by `find(id)` AT THE TIME of grouping.
4. **Forgetting the name as element [0] of output.** Output is `[name, emails...]`, not just emails.
5. **Treating same-named accounts as automatically same.** No! Two Johns with different emails are different people.

---

## 9. The shape — DSU for component discovery

The pattern: **items grouped by shared attribute → DSU.**

| Problem | Shared attribute |
|---|---|
| **This problem** | shared email |
| Friend Circles | shared friendship |
| Number of Connected Components | edge endpoints |
| Most Stones Removed | shared row/column |
| Number of Islands II | grid adjacency (4-dir) |
| Couples Holding Hands | seating-row pairing |

**Pattern to internalize:**

> "Items group by sharing some attribute → DSU. For each item, union it with previously-seen items that share. At end, group by find()."

---

> **Self-check — the question to ask next time.**
>
> When the problem says "merge items that share something," ask:
>
> > **"Can I assign IDs, union by shared attribute, then group by root? That's DSU; O(N · α(N) + N log N) with sorting."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Accounts_Merge.md`](../Accounts_Merge.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Redundant_Connection.md`](./Redundant_Connection.md), [`Number_of_Provinces.md`](./Number_of_Provinces.md), [`Number_of_Operations_to_Make_Network_Connected.md`](./Number_of_Operations_to_Make_Network_Connected.md).
  - Coming next: [`Most_Stones_Removed_with_Same_Row_or_Column.md`](./Most_Stones_Removed_with_Same_Row_or_Column.md), [`Satisfiability_of_Equality_Equations.md`](./Satisfiability_of_Equality_Equations.md).
