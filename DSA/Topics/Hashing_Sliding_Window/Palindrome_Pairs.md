# Palindrome Pairs

## Problem Link
https://leetcode.com/problems/palindrome-pairs/

## Topic
Hashing Sliding Window

## Core Concept
For each word, check split points and see if the reverse of each half exists.

## Intuition
A pair (a,b) forms palindrome iff (a+b) is palindrome. Split word at each index; if left is palindrome and reverse(right) is another word, that other word can be prefix. Symmetric for suffix.

## Detailed Explanation
Build map word→index. For each word, for each split i [0..|w|]: if left palindrome and reverse(right) in map (and different index) → pair. If i<|w| and right palindrome and reverse(left) in map.

## Dry Run
['abcd','dcba','lls','s','sssll']. Pairs like [0,1],[1,0],[3,2],[2,4].

## Approach
Hashmap of reversed words.

## Time and Space Complexity
Time: O(N·L²). Space: O(N·L).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool isPal(const string& s, int l, int r) { while (l<r) if (s[l++]!=s[r--]) return false; return true; }
vector<vector<int>> palindromePairs(vector<string>& w) {
    unordered_map<string,int> idx;
    for (int i = 0; i < (int)w.size(); ++i) idx[w[i]] = i;
    vector<vector<int>> res;
    for (int i = 0; i < (int)w.size(); ++i) {
        string s = w[i]; int n = s.size();
        for (int j = 0; j <= n; ++j) {
            if (isPal(s, j, n-1)) {
                string pre(s.begin(), s.begin()+j);
                reverse(pre.begin(), pre.end());
                if (idx.count(pre) && idx[pre] != i) res.push_back({i, idx[pre]});
            }
            if (j && isPal(s, 0, j-1)) {
                string suf(s.begin()+j, s.end());
                reverse(suf.begin(), suf.end());
                if (idx.count(suf) && idx[suf] != i) res.push_back({idx[suf], i});
            }
        }
    }
    return res;
}
```

## Follow-up Questions
- Palindrome triples.
- Using a trie.
- Large-word streaming.
