# Maximum Number of Words Found in Sentences

## Problem Link
https://leetcode.com/problems/maximum-number-of-words-found-in-sentences/

## Topic
Arrays and Matrices

## Core Concept
Count spaces per sentence, add 1, track max.

## Intuition
Word count in a space-separated string = number of spaces + 1.

## Detailed Explanation
For each sentence count spaces and compare to max.

## Dry Run
sentences=['alice a b','hello world']. 2+1=3, 1+1=2. max=3.

## Approach
Linear scan.

## Time and Space Complexity
Time: O(total chars). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int mostWordsFound(vector<string>& s) {
    int best = 0;
    for (auto& x : s) {
        int c = 1;
        for (char ch : x) if (ch == ' ') c++;
        best = max(best, c);
    }
    return best;
}
```

## Follow-up Questions
- Using stringstream per sentence.
- Ignore consecutive spaces.
- Unicode word boundaries.
