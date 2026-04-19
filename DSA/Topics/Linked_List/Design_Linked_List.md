# Design Linked List

## Problem Link
https://leetcode.com/problems/design-linked-list/

## Topic
Linked List

## Core Concept
Implement standard operations on a singly linked list.

## Intuition
Build a class with head pointer (often with dummy) supporting get/addAtHead/addAtTail/addAtIndex/deleteAtIndex.

## Detailed Explanation
Keep size and dummy head. For index ops, walk dummy next k times. For delete unlink. For add create node and splice.

## Dry Run
Add 1, add 3, addAtIndex(1,2), get(1)=2, deleteAtIndex(1), get(1)=3.

## Approach
Dummy-head linked list class.

## Time and Space Complexity
Each op O(n) worst.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
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
};
```

## Follow-up Questions
- Doubly linked list implementation.
- Skip-list (random levels).
- Concurrent linked list.
