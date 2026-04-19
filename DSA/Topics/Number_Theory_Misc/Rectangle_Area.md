# Rectangle Area

## Problem Link
https://leetcode.com/problems/rectangle-area/description/

## Topic
Number Theory Misc

## Core Concept
Sum of two rectangle areas minus overlap (inclusion-exclusion).

## Intuition
Total covered = A + B − overlap. Overlap is the intersection rectangle area; 0 if they don't overlap.

## Detailed Explanation
A = (ax2-ax1)*(ay2-ay1); similar for B. Overlap width = max(0, min(ax2,bx2) - max(ax1,bx1)); height analogous. Total = A + B - overlap.

## Dry Run
A rect=(−3,0)-(3,4), B=(0,−1)-(9,2). A=24, B=27, overlap width=3, height=2 → 6. Total=45.

## Approach
Inclusion-exclusion of two axis-aligned rectangles.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
int computeArea(int a,int b,int c,int d,int e,int f,int g,int h) {
    int A = (c-a)*(d-b), B = (g-e)*(h-f);
    int w = max(0, min(c,g) - max(a,e));
    int ht = max(0, min(d,h) - max(b,f));
    return A + B - w * ht;
}
```

## Follow-up Questions
- N rectangles union area (sweep line).
- 3D axis-aligned boxes.
- Rectangles with rotation (convex polygon overlap).
