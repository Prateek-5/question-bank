DATA = {
"Baseball Game": {
  "concept": "Stack of recent scores processing special tokens.",
  "intuition": "'+' is sum of last two, 'D' is double last, 'C' removes last, number is a new score. A stack matches these operations.",
  "explanation": "Iterate tokens; apply to stack accordingly. Final answer is the sum of stack.",
  "dry_run": "ops=['5','2','C','D','+']. Stack: [5]→[5,2]→[5]→[5,10]→[5,10,15]. Sum=30.",
  "approach": "Stack simulation.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int calPoints(vector<string>& ops) {
    vector<int> st;
    for (auto& o : ops) {
        if (o == \"C\") st.pop_back();
        else if (o == \"D\") st.push_back(2 * st.back());
        else if (o == \"+\") st.push_back(st[st.size()-1] + st[st.size()-2]);
        else st.push_back(stoi(o));
    }
    return accumulate(st.begin(), st.end(), 0);
}""",
  "followups": "- Undo across multiple Cs.\n- Sum after each operation.\n- Streaming tokens."
},

"Daily Temperatures": {
  "concept": "Monotonic decreasing stack of indices.",
  "intuition": "For each day, look ahead for the next warmer day. A stack of unresolved indices works: whenever a warmer day appears, pop and record distance.",
  "explanation": "Iterate i; while stack non-empty and T[i]>T[stack.top()], pop j and set res[j]=i-j. Push i.",
  "dry_run": "T=[73,74,75,71,69,72,76,73]. Answer [1,1,4,2,1,1,0,0].",
  "approach": "Monotonic stack.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> dailyTemperatures(vector<int>& T) {
    int n = T.size(); vector<int> res(n, 0); stack<int> st;
    for (int i = 0; i < n; ++i) {
        while (!st.empty() && T[i] > T[st.top()]) { res[st.top()] = i - st.top(); st.pop(); }
        st.push(i);
    }
    return res;
}""",
  "followups": "- Next colder day.\n- Previous warmer day.\n- Circular day array."
},

"Evaluate Reverse Polish Notation": {
  "concept": "Stack of operands; on operator pop two, apply, push result.",
  "intuition": "RPN naturally evaluates with a stack — operators act on the top two values.",
  "explanation": "For each token: if numeric push; else pop b, a, compute a OP b, push result.",
  "dry_run": "tokens=['2','1','+','3','*']. Stack 2,1 → 3 → 3,3 → 9.",
  "approach": "Stack simulation.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int evalRPN(vector<string>& t) {
    stack<long long> st;
    for (auto& x : t) {
        if (x == \"+\" || x == \"-\" || x == \"*\" || x == \"/\") {
            long long b = st.top(); st.pop();
            long long a = st.top(); st.pop();
            if (x == \"+\") st.push(a + b);
            else if (x == \"-\") st.push(a - b);
            else if (x == \"*\") st.push(a * b);
            else st.push(a / b);
        } else st.push(stoll(x));
    }
    return (int)st.top();
}""",
  "followups": "- Convert infix to postfix.\n- Handle unary minus.\n- Add parentheses/precedence parser."
},

"Remove All Adjacent Duplicates in String": {
  "concept": "Stack — cancel adjacent duplicates.",
  "intuition": "Treat the string as a stack of chars; pushing a char equal to top cancels both.",
  "explanation": "Iterate chars; if top==c pop, else push. Result is stack contents joined.",
  "dry_run": "'abbaca' → 'a','ab','abb'→'a','ac'→'ac','aca'.",
  "approach": "String as stack.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """string removeDuplicates(string s) {
    string r;
    for (char c : s) {
        if (!r.empty() && r.back() == c) r.pop_back();
        else r += c;
    }
    return r;
}""",
  "followups": "- Remove k consecutive equals.\n- Remove via pattern-match.\n- Streaming version."
},

"Largest Rectangle in Histogram": {
  "concept": "Monotonic increasing stack of bar indices.",
  "intuition": "For each bar, the largest rectangle with it as the shortest bar has width equal to the distance between the previous smaller and next smaller bars.",
  "explanation": "Append sentinel 0. For each i: while top's height > h[i], pop as height; width = stack.empty() ? i : i - stack.top() - 1. Track max. Push i.",
  "dry_run": "h=[2,1,5,6,2,3] → max area 10.",
  "approach": "Monotonic stack.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int largestRectangleArea(vector<int>& h) {
    h.push_back(0);
    stack<int> st; int best = 0;
    for (int i = 0; i < (int)h.size(); ++i) {
        while (!st.empty() && h[st.top()] > h[i]) {
            int top = st.top(); st.pop();
            int w = st.empty() ? i : i - st.top() - 1;
            best = max(best, h[top] * w);
        }
        st.push(i);
    }
    h.pop_back();
    return best;
}""",
  "followups": "- Maximal rectangle in 0/1 matrix.\n- Rectangles with at most k ones.\n- Dynamic histogram queries."
},

"Min Stack": {
  "concept": "Auxiliary stack tracking current minimum.",
  "intuition": "A parallel stack stores the running min at each depth, enabling O(1) getMin.",
  "explanation": "Push: record on data stack; also push min(currMin, x) on min stack. Pop: pop both. getMin: top of min stack.",
  "dry_run": "Push -2,0,-3. Mins [-2,-2,-3]. Pop → mins [-2,-2]. getMin = -2.",
  "approach": "Two stacks.",
  "complexity": "All ops O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class MinStack {
    stack<int> s, m;
public:
    void push(int x) { s.push(x); if (m.empty() || x <= m.top()) m.push(x); else m.push(m.top()); }
    void pop() { s.pop(); m.pop(); }
    int top() { return s.top(); }
    int getMin() { return m.top(); }
};""",
  "followups": "- Single-stack encoding (difference trick).\n- Max stack.\n- Immutable functional stack."
},

"Next Greater Element I": {
  "concept": "Monotonic stack on nums2; map each value to its next greater.",
  "intuition": "Scan nums2, maintain a decreasing stack. When a larger value appears, all smaller on stack know their next greater.",
  "explanation": "For each x in nums2: while stack non-empty and top<x, map[st.top()]=x, pop. Push x. Then for nums1 look up map (default -1).",
  "dry_run": "nums2=[1,3,4,2]. map {1→3, 3→4, 4→-1, 2→-1}. nums1=[4,1,2] → [-1,3,-1].",
  "approach": "Monotonic stack + hashmap.",
  "complexity": "Time: O(n1+n2). Space: O(n2).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> nextGreaterElement(vector<int>& a, vector<int>& b) {
    unordered_map<int,int> nxt;
    stack<int> st;
    for (int x : b) {
        while (!st.empty() && st.top() < x) { nxt[st.top()] = x; st.pop(); }
        st.push(x);
    }
    vector<int> res;
    for (int x : a) res.push_back(nxt.count(x) ? nxt[x] : -1);
    return res;
}""",
  "followups": "- Next Greater Element II (circular).\n- Previous greater element.\n- Next Greater Node in linked list."
},

"Remove Outermost Parentheses": {
  "concept": "Track depth; skip chars at depth 0↔1 transitions.",
  "intuition": "An outermost '(' starts a primitive (depth 0→1) and its matching ')' ends it (depth 1→0). Skip those transitions.",
  "explanation": "Iterate; open increments depth. Append char unless depth just became 1 (on '(') or just returned to 0 (on ')').",
  "dry_run": "s='(()())(())'. Result '()()()'.",
  "approach": "Depth counter.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """string removeOuterParentheses(string s) {
    string r; int d = 0;
    for (char c : s) {
        if (c == '(' && d++ > 0) r += c;
        else if (c == ')' && --d > 0) r += c;
    }
    return r;
}""",
  "followups": "- Balance types (multi-bracket).\n- Depth-k outer removal.\n- Parse primitives list."
},

"Valid Parentheses": {
  "concept": "Stack matching each closer to the last opener.",
  "intuition": "Use a stack: on open push; on close check top matches and pop. Valid iff stack is empty at end.",
  "explanation": "Iterate; map close→open. Handle early fail when top doesn't match.",
  "dry_run": "s='()[]{}' → stack shrinks each pair → valid.",
  "approach": "Stack matching.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') st.push(c);
        else {
            if (st.empty()) return false;
            char t = st.top(); st.pop();
            if ((c == ')' && t != '(') || (c == ']' && t != '[') || (c == '}' && t != '{')) return false;
        }
    }
    return st.empty();
}""",
  "followups": "- Minimum edits to make valid.\n- Longest valid substring.\n- Streaming version."
},

"Expression Contains Redundant Bracket or Not": {
  "concept": "Stack scanning for a pair of parens enclosing zero operators.",
  "intuition": "A subexpression in parens is redundant iff no operator exists between the opening '(' and its matching ')'.",
  "explanation": "Push each char onto stack. On ')': pop until '('; if no operator was popped, it's redundant.",
  "dry_run": "expr='((a+b))' → innermost '(a+b)' ok; outer '(' ')' encloses only '(a+b)' → redundant.",
  "approach": "Stack parsing.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
bool hasRedundantBrackets(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == ')') {
            bool hasOp = false;
            while (!st.empty() && st.top() != '(') {
                if (st.top() == '+' || st.top() == '-' || st.top() == '*' || st.top() == '/') hasOp = true;
                st.pop();
            }
            if (!st.empty()) st.pop();
            if (!hasOp) return true;
        } else st.push(c);
    }
    return false;
}""",
  "followups": "- Find position of redundant bracket.\n- Remove redundant brackets.\n- Evaluate expression validity."
},
}
