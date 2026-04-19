DATA = {
"Design Add and Search Words DS": {
  "concept": "Trie with '.' wildcard handled via DFS.",
  "intuition": "A trie stores words prefix-compactly. Wildcard '.' at search time branches into all children of the current node.",
  "explanation": "addWord walks the trie creating nodes. search(word,node): if char '.', recurse on every existing child. Else follow exact child or fail. At end check node.isEnd.",
  "dry_run": "Add 'bad','dad','mad'. Search 'pad'→false. Search '.ad'→true. Search 'b..'→true.",
  "approach": "Standard Trie + DFS for wildcards.",
  "complexity": "Add O(L), search O(26^w · L) worst-case.",
  "code": """#include <bits/stdc++.h>
using namespace std;
class WordDictionary {
    struct N { N* c[26] = {}; bool end = false; };
    N* root = new N();
    bool dfs(const string& s, int i, N* n) {
        if (!n) return false;
        if (i == (int)s.size()) return n->end;
        char ch = s[i];
        if (ch == '.') {
            for (auto* k : n->c) if (dfs(s, i+1, k)) return true;
            return false;
        }
        return dfs(s, i+1, n->c[ch-'a']);
    }
public:
    void addWord(string w) {
        auto* n = root;
        for (char ch : w) { if (!n->c[ch-'a']) n->c[ch-'a'] = new N(); n = n->c[ch-'a']; }
        n->end = true;
    }
    bool search(string w) { return dfs(w, 0, root); }
};""",
  "followups": "- Support '*' (zero-or-more).\n- Delete word from dictionary.\n- Prefix search."
},

"Implement Trie (Prefix Tree)": {
  "concept": "26-ary tree nodes; insert, search, startsWith operations.",
  "intuition": "Each node represents a prefix; children map letters to next nodes. Marked isEnd distinguishes word endings.",
  "explanation": "Each operation walks the tree creating (insert) or following (search/startsWith) child links by character.",
  "dry_run": "Insert 'apple'. Search 'apple'→true. Search 'app'→false. startsWith 'app'→true.",
  "approach": "Fixed-size array per node for simplicity.",
  "complexity": "Each op O(L).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class Trie {
    struct N { N* c[26] = {}; bool end = false; };
    N* root = new N();
public:
    void insert(string w) {
        auto* n = root;
        for (char ch : w) { if (!n->c[ch-'a']) n->c[ch-'a'] = new N(); n = n->c[ch-'a']; }
        n->end = true;
    }
    bool search(string w) {
        auto* n = root;
        for (char ch : w) { n = n->c[ch-'a']; if (!n) return false; }
        return n->end;
    }
    bool startsWith(string p) {
        auto* n = root;
        for (char ch : p) { n = n->c[ch-'a']; if (!n) return false; }
        return true;
    }
};""",
  "followups": "- Memory-efficient Trie (unordered_map children).\n- Compressed Trie / Radix Tree.\n- Persistent Trie."
},

"Shortest Unique prefix for every word": {
  "concept": "Trie with prefix counts; walk to first node with count 1.",
  "intuition": "For each word, the shortest unique prefix is the first depth at which no other word passes through. Store at each node how many words traverse it.",
  "explanation": "Insert all words, incrementing cnt at each node. For each word, walk letters; first node with cnt==1 is its unique prefix end.",
  "dry_run": "Words: ['zebra','dog','duck','dove']. Results: ['z','dog','du','dov'].",
  "approach": "Trie with pass-count per node.",
  "complexity": "Time: O(total chars). Space: O(total chars).",
  "code": """#include <bits/stdc++.h>
using namespace std;
struct N { N* c[26] = {}; int cnt = 0; };

vector<string> shortestUniquePrefix(vector<string>& words) {
    N* root = new N();
    for (auto& w : words) { auto* n = root; for (char ch : w) { if (!n->c[ch-'a']) n->c[ch-'a'] = new N(); n = n->c[ch-'a']; n->cnt++; } }
    vector<string> res;
    for (auto& w : words) {
        string p; auto* n = root;
        for (char ch : w) { p += ch; n = n->c[ch-'a']; if (n->cnt == 1) break; }
        res.push_back(p);
    }
    return res;
}""",
  "followups": "- Longest common prefix.\n- Unique suffix (reverse).\n- k-th shortest unique prefix."
},

"Maximum XOR of Two Numbers": {
  "concept": "Bit Trie (size-2 branches) to pair bits maximizing XOR.",
  "intuition": "Insert each number's bits into a binary trie. For each number, traverse preferring the opposite bit at each level to maximize XOR.",
  "explanation": "Build a bit-trie (MSB to LSB). For each x, greedily pick child with bit (1 - xbit) where possible; accumulate XOR value.",
  "dry_run": "nums=[3,10,5,25,2,8]. Max XOR = 25 ^ 5 = 28.",
  "approach": "Bit-Trie with 32-level depth.",
  "complexity": "Time: O(n·32). Space: O(n·32).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findMaximumXOR(vector<int>& a) {
    struct N { N* c[2] = {}; };
    N* root = new N();
    for (int x : a) { auto* n = root; for (int b = 31; b >= 0; --b) { int bit = (x >> b) & 1; if (!n->c[bit]) n->c[bit] = new N(); n = n->c[bit]; } }
    int best = 0;
    for (int x : a) {
        auto* n = root; int v = 0;
        for (int b = 31; b >= 0; --b) {
            int want = 1 - ((x >> b) & 1);
            if (n->c[want]) { v |= (1 << b); n = n->c[want]; }
            else n = n->c[1 - want];
        }
        best = max(best, v);
    }
    return best;
}""",
  "followups": "- Max XOR of subarray.\n- Max XOR with at most k modifications.\n- Min XOR pair."
},

"Prefix and Suffix Search": {
  "concept": "Trie indexed by 'suffix#prefix' concatenations.",
  "intuition": "Insert every (suffix + '#' + word) variant into a trie; a prefix+suffix query becomes a single trie lookup for 'suf#pre'. Store word index at each node for latest match.",
  "explanation": "For each word at index i, for each suffix s, insert s + '#' + word; at each node mark idx = i. Query: walk trie on 'suffix#prefix'; return stored idx or -1.",
  "dry_run": "Words ['apple']. Suffixes 'apple','pple','ple','le','e',''. Insert each + '#apple'. Query ('a','e'): 'e#a' → node has idx 0.",
  "approach": "Trie with combined key.",
  "complexity": "Build O(sum L²). Query O(P+S).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class WordFilter {
    struct N { N* c[27] = {}; int idx = -1; };
    N* root = new N();
    int cix(char ch) { return ch == '#' ? 26 : ch - 'a'; }
public:
    WordFilter(vector<string>& words) {
        for (int i = 0; i < (int)words.size(); ++i) {
            string w = words[i];
            for (int s = 0; s <= (int)w.size(); ++s) {
                string key = w.substr(s) + \"#\" + w;
                auto* n = root;
                for (char ch : key) { if (!n->c[cix(ch)]) n->c[cix(ch)] = new N(); n = n->c[cix(ch)]; n->idx = i; }
            }
        }
    }
    int f(string pre, string suf) {
        string key = suf + \"#\" + pre;
        auto* n = root;
        for (char ch : key) { n = n->c[cix(ch)]; if (!n) return -1; }
        return n->idx;
    }
};""",
  "followups": "- With weighted words.\n- Online insertions.\n- Overlapping prefix/suffix."
},

"Count Substrings That Differ by One Character": {
  "concept": "DP counting matching suffix lengths with a single mismatch.",
  "intuition": "For each alignment (i, j) in s and t, maintain counts of matching characters before and after a potential mismatch; their product counts substrings ending with the alignment and differing by exactly one.",
  "explanation": "For each (i, j), track prev (matching run) and cur (running mismatch-allowed). When s[i]==t[j], cur extends; else reset. Sum prev*cur via careful recurrence over start positions.",
  "dry_run": "s='aba', t='baba'. Answer = 6.",
  "approach": "Two DP tables over (i,j).",
  "complexity": "Time: O(|s|·|t|). Space: O(|s|·|t|).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int countSubstrings(string s, string t) {
    int n = s.size(), m = t.size(), res = 0;
    vector<vector<int>> pre(n+1, vector<int>(m+1,0)), suf(n+2, vector<int>(m+2,0));
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) pre[i+1][j+1] = s[i]==t[j] ? pre[i][j]+1 : 0;
    for (int i=n-1;i>=0;i--) for (int j=m-1;j>=0;j--) suf[i][j] = s[i]==t[j] ? suf[i+1][j+1]+1 : 0;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (s[i]!=t[j]) res += (pre[i][j]+1) * (suf[i+1][j+1]+1);
    return res;
}""",
  "followups": "- Allow k differences.\n- Longest common substring with ≤k diffs.\n- Case-insensitive variant."
},

"Subarrays with XOR Less Than K (Concept)": {
  "concept": "Binary-trie over prefix XORs to count subarrays with XOR < K.",
  "intuition": "For each prefix XOR p, count earlier prefix XORs q such that p ^ q < K. A bit-trie lets us count candidates branch-by-branch using bits of K.",
  "explanation": "Insert prefix XORs into bit-trie; maintain subtree counts. For query p, traverse bits of K: if K's bit is 1, all numbers with different-current-bit in opposite branch satisfy strict-less; descend into same-bit branch to check the rest. If K's bit is 0, descend into same-bit.",
  "dry_run": "arr=[1,2,3,4], K=4. Build prefix XOR; count pairs (p,q) with p^q<4 → answer derived via trie.",
  "approach": "Bit trie with subtree counters.",
  "complexity": "Time: O(n·log max). Space: O(n·log max).",
  "code": """// Template omitted for brevity; see Maximum XOR trie structure with additional subtree counts.""",
  "followups": "- XOR subarrays equal to K.\n- XOR in a range K1..K2.\n- Max XOR of subarray."
},
}
