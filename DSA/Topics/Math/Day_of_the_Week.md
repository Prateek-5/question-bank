# Day of the Week

## Problem Link
https://leetcode.com/problems/day-of-the-week/

## Topic
Math

## Core Concept
Zeller's congruence or day-of-year counting from a known anchor date.

## Intuition
Pick a reference date whose weekday is known, then count the total days elapsed and take modulo 7 to find the target weekday.

## Detailed Explanation
From 1971-01-01 (Friday, index 5 if Sunday=0), compute the total number of days to the query date: account for leap years and days in months. Convert (5 + total_days) % 7 to a weekday name.

## Dry Run
Query 2019-08-31. Days from 1971 = sum of year-days + months-in-2019 + 31-1. Modulo 7 yields 6 → Saturday.

## Approach
Day-counting from epoch, with leap-year handling. Alternative: Zeller's formula.

## Time and Space Complexity
O(year-1971) per query.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

string dayOfTheWeek(int d, int m, int y) {
    vector<string> days = {"Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"};
    vector<int> md = {31,28,31,30,31,30,31,31,30,31,30,31};
    auto leap = [](int y){ return (y%4==0 && y%100!=0) || y%400==0; };
    int total = 0;
    for (int yy = 1971; yy < y; ++yy) total += leap(yy) ? 366 : 365;
    for (int mm = 0; mm < m - 1; ++mm) total += md[mm] + (mm == 1 && leap(y));
    total += d - 1;
    return days[(5 + total) % 7]; // 1971-01-01 was Friday
}
```

## Follow-up Questions
- Handle BC dates or a wider range.
- Use Zeller's congruence for O(1).
- Compute day of year; Julian day number.
