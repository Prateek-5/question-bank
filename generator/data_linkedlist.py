DATA = {
"Delete Node in a Linked List": {
  "concept": "Copy next node's data and bypass it.",
  "intuition": "Without access to head or prev, we can't unlink this node. Instead, overwrite its value with next's, then unlink next.",
  "explanation": "node.val = node.next.val; node.next = node.next.next;",
  "dry_run": "List 4→5→1→9, delete 5. Copy 1 into 5's slot → 4→1→1→9. Remove the duplicate by linking to 9 → 4→1→9.",
  "approach": "Overwrite-next trick.",
  "complexity": "O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
void deleteNode(ListNode* n) { n->val = n->next->val; n->next = n->next->next; }""",
  "followups": "- When the node is the tail — undefined; must have prev.\n- Delete all occurrences of value (requires traversal).\n- Delete range of nodes."
},

"Linked List Cycle": {
  "concept": "Floyd's tortoise and hare — two pointers at different speeds.",
  "intuition": "If there is a cycle, a fast pointer (2 steps) will eventually lap a slow pointer (1 step) inside the cycle.",
  "explanation": "slow=fast=head. While fast && fast->next: slow=slow->next; fast=fast->next->next; if they meet return true. Else false.",
  "dry_run": "1→2→3→4→2. fast cycles and meets slow.",
  "approach": "Two-pointer cycle detection.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
bool hasCycle(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) {
        s = s->next; f = f->next->next;
        if (s == f) return true;
    }
    return false;
}""",
  "followups": "- Detect cycle start (Cycle II).\n- Length of the cycle.\n- Multi-cycle scenarios (impossible in singly linked lists)."
},

"Merge Two Sorted Lists": {
  "concept": "Iterative or recursive merge using a dummy head.",
  "intuition": "At each step pick the smaller head and advance. Continue until one list empties, then attach the rest.",
  "explanation": "Dummy head d; tail=d. While both non-null: pick smaller, attach, advance. Attach remaining list.",
  "dry_run": "A:1→2→4, B:1→3→4. Merged: 1→1→2→3→4→4.",
  "approach": "Two-pointer merge with dummy.",
  "complexity": "Time: O(n+m). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; ListNode(int x):val(x),next(nullptr){} };
ListNode* mergeTwoLists(ListNode* a, ListNode* b) {
    ListNode d(0); auto t = &d;
    while (a && b) {
        if (a->val <= b->val) { t->next = a; a = a->next; }
        else { t->next = b; b = b->next; }
        t = t->next;
    }
    t->next = a ? a : b;
    return d.next;
}""",
  "followups": "- Merge k sorted lists (heap).\n- Merge in place without dummy.\n- Merge by a custom comparator."
},

"Reverse Linked List": {
  "concept": "Iterative pointer rotation.",
  "intuition": "Walk the list reversing each next pointer by remembering the previous node.",
  "explanation": "prev=null, cur=head. While cur: next=cur->next; cur->next=prev; prev=cur; cur=next. Return prev.",
  "dry_run": "1→2→3 → 3→2→1.",
  "approach": "Three-pointer sweep.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
ListNode* reverseList(ListNode* h) {
    ListNode* prev = nullptr;
    while (h) { auto* n = h->next; h->next = prev; prev = h; h = n; }
    return prev;
}""",
  "followups": "- Recursive reverse.\n- Reverse only a sub-range (Reverse II).\n- Reverse in groups of k."
},

"Convert Binary Number in a Linked List to Integer": {
  "concept": "Left-shift accumulator while traversing.",
  "intuition": "Process bits from MSB to LSB: res = res*2 + node.val.",
  "explanation": "Traverse the list, updating res.",
  "dry_run": "1→0→1 → 101₂=5.",
  "approach": "Single pass.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
int getDecimalValue(ListNode* h) {
    int r = 0;
    while (h) { r = r * 2 + h->val; h = h->next; }
    return r;
}""",
  "followups": "- Big integer (BigInt) support.\n- Base other than 2.\n- LSB-first list."
},

"Design Linked List": {
  "concept": "Implement standard operations on a singly linked list.",
  "intuition": "Build a class with head pointer (often with dummy) supporting get/addAtHead/addAtTail/addAtIndex/deleteAtIndex.",
  "explanation": "Keep size and dummy head. For index ops, walk dummy next k times. For delete unlink. For add create node and splice.",
  "dry_run": "Add 1, add 3, addAtIndex(1,2), get(1)=2, deleteAtIndex(1), get(1)=3.",
  "approach": "Dummy-head linked list class.",
  "complexity": "Each op O(n) worst.",
  "code": """#include <bits/stdc++.h>
using namespace std;
class MyLinkedList {
    struct N { int v; N* n; N(int x):v(x),n(nullptr){} };
    N* dummy; int sz;
public:
    MyLinkedList(): dummy(new N(0)), sz(0) {}
    int get(int i) {
        if (i < 0 || i >= sz) return -1;
        N* c = dummy->n;
        while (i--) c = c->n;
        return c->v;
    }
    void addAtIndex(int i, int v) {
        if (i < 0 || i > sz) return;
        N* p = dummy; while (i--) p = p->n;
        N* n = new N(v); n->n = p->n; p->n = n; sz++;
    }
    void addAtHead(int v) { addAtIndex(0, v); }
    void addAtTail(int v) { addAtIndex(sz, v); }
    void deleteAtIndex(int i) {
        if (i < 0 || i >= sz) return;
        N* p = dummy; while (i--) p = p->n;
        N* t = p->n; p->n = t->n; delete t; sz--;
    }
};""",
  "followups": "- Doubly linked list implementation.\n- Skip-list (random levels).\n- Concurrent linked list."
},

"Linked List Cycle II": {
  "concept": "Floyd's algorithm — after meeting, reset one pointer to head.",
  "intuition": "If slow and fast meet inside the cycle, the distance from head to start equals the distance from meeting point to start (mod cycle length). Reset one to head and advance both one step at a time to find the cycle's entry.",
  "explanation": "Detect meeting. Then slow=head; move both one step until they meet — that's the cycle start.",
  "dry_run": "1→2→3→4→5→3. Slow/fast meet inside. Reset slow to 1; both step → meet at node 3.",
  "approach": "Floyd's phase 2.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
ListNode* detectCycle(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) {
        s = s->next; f = f->next->next;
        if (s == f) { s = h; while (s != f) { s = s->next; f = f->next; } return s; }
    }
    return nullptr;
}""",
  "followups": "- Cycle length calculation.\n- Remove the cycle.\n- Multiple lists sharing nodes."
},

"Middle of the Linked List": {
  "concept": "Slow/fast pointers.",
  "intuition": "Fast moves 2 steps for slow's 1. When fast reaches the end, slow is at the middle.",
  "explanation": "slow=fast=head. While fast && fast->next: slow=slow->next; fast=fast->next->next. Return slow.",
  "dry_run": "1→2→3→4→5. slow ends at 3.",
  "approach": "Tortoise-hare.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
ListNode* middleNode(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) { s = s->next; f = f->next->next; }
    return s;
}""",
  "followups": "- Return the first middle in even length.\n- Find k-th from middle.\n- Middle element removal."
},

"Palindrome Linked List": {
  "concept": "Find middle, reverse second half, compare halves.",
  "intuition": "Comparing across the list with O(1) memory needs us to mirror the second half by reversing.",
  "explanation": "Find middle (slow/fast). Reverse slow (second half). Walk both halves comparing values. Optionally restore the list.",
  "dry_run": "1→2→2→1. Middle at 2 (second). Reverse second → 1→2. Compare 1,2 with 1,2 → palindrome.",
  "approach": "In-place O(1) memory.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; };
ListNode* rev(ListNode* h) { ListNode* p = nullptr; while (h) { auto* n = h->next; h->next = p; p = h; h = n; } return p; }
bool isPalindrome(ListNode* h) {
    auto s = h, f = h;
    while (f && f->next) { s = s->next; f = f->next->next; }
    auto r = rev(s);
    while (r) { if (h->val != r->val) return false; h = h->next; r = r->next; }
    return true;
}""",
  "followups": "- Without modifying the list (stack-based).\n- Doubly linked list palindrome.\n- Palindromic partitions."
},

"Remove Linked List Elements": {
  "concept": "Dummy head with filter pass.",
  "intuition": "A dummy head simplifies removing the actual head. Walk with a prev pointer skipping nodes whose value matches.",
  "explanation": "dummy->next=head. prev=dummy. While prev->next: if prev->next->val==val unlink; else advance prev.",
  "dry_run": "List 1→2→6→3→6, val=6 → 1→2→3.",
  "approach": "Single pass.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; ListNode(int x):val(x),next(nullptr){} };
ListNode* removeElements(ListNode* h, int v) {
    ListNode d(0); d.next = h;
    auto p = &d;
    while (p->next) {
        if (p->next->val == v) p->next = p->next->next;
        else p = p->next;
    }
    return d.next;
}""",
  "followups": "- Remove all duplicates (keep distinct).\n- Recursive version.\n- Remove by predicate function."
},

"Remove Nth Node From End of List": {
  "concept": "Two-pointer gap of n+1 nodes.",
  "intuition": "If one pointer moves n+1 ahead, both pointers advancing together until the lead hits null leaves the trailing pointer just before the target.",
  "explanation": "Dummy head; fast=slow=dummy. Advance fast n+1 steps. Then advance both until fast==null. slow->next = slow->next->next.",
  "dry_run": "1→2→3→4→5, n=2. After gap, slow ends at 3; remove 4 → 1→2→3→5.",
  "approach": "Two-pointer single pass.",
  "complexity": "Time: O(L). Space: O(1).",
  "code": """struct ListNode { int val; ListNode* next; ListNode(int x):val(x),next(nullptr){} };
ListNode* removeNthFromEnd(ListNode* h, int n) {
    ListNode d(0); d.next = h;
    auto s = &d, f = &d;
    for (int i = 0; i <= n; ++i) f = f->next;
    while (f) { s = s->next; f = f->next; }
    s->next = s->next->next;
    return d.next;
}""",
  "followups": "- Remove k-th from end in doubly linked.\n- Remove multiple nodes at once.\n- Insert nth-from-end node."
},
}
