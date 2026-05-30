# Day of the Week

**Problem Link:**
<a href="https://leetcode.com/problems/day-of-the-week/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/day-of-the-week/</a>

**Topic:**
Math

----------------------------------------

## Step 1: The Problem

Given a date (day, month, year), return the day of the week as a string (e.g., "Sunday", "Monday", ...).

Valid date range: 1971-01-01 to 2100-12-31.

Example: `day = 31, month = 8, year = 2019`. Output: "Saturday".

----------------------------------------

## Step 2: Approach — Count Days Since a Known Reference

Pick a reference date whose day-of-week we know. Compute the number of days between that reference and the input date. Modulo 7 gives the day-of-week offset.

LeetCode's problem constraint starts at 1971-01-01. **January 1, 1971 was a Friday.**

Algorithm:
1. Compute total days from 1971-01-01 to (day, month, year).
2. Compute `(friday_index + total_days) % 7` where Friday has some numeric index.
3. Map the result to a weekday name.

----------------------------------------

## Step 3: Counting Days Elapsed

Days between two dates = (years elapsed × days-per-year) + (days in completed months of target year) + (day - 1).

Leap year adjustment: a year is a leap year if divisible by 4 AND not by 100, except years divisible by 400.

```
def daysInYear(y):
    return 366 if leap(y) else 365

def daysInMonth(m, y):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if m == 2 and leap(y): return 29
    return days[m - 1]

total = 0
for y in 1971..year-1: total += daysInYear(y)
for m in 1..month-1: total += daysInMonth(m, year)
total += day - 1

weekday_index = (5 + total) % 7   # 5 = Friday's index if Sunday=0

weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
return weekdays[weekday_index]
```

O(year - 1971) ≈ O(100) for typical inputs. Tiny.

----------------------------------------

## Step 4: Trace for Aug 31, 2019

Days from 1971 to 2018 (years 1971..2018, 48 years):
- Leap years in range: 1972, 1976, ..., 2016. Count: (2016 - 1972) / 4 + 1 = 12. (Exclude 2000 centennial check: 2000 is divisible by 400, so it's a leap year. No exclusions needed.)
- Total: 48 × 365 + 12 = 17520 + 12 = 17532 days.

Days in 2019, months 1..7 (Jan through July):
- Jan (31) + Feb (28, 2019 not leap) + Mar (31) + Apr (30) + May (31) + Jun (30) + Jul (31) = 212 days.

Day offset in August: 31 - 1 = 30.

Total = 17532 + 212 + 30 = 17774 days.

(5 + 17774) % 7 = 17779 % 7 = ?
17779 / 7 = 2539 remainder ? Let me compute: 7 × 2539 = 17773. 17779 - 17773 = 6.

Weekday index 6 = "Saturday". ✓

----------------------------------------

## Step 5: Zeller's Congruence (Alternative)

A closed-form formula exists:

```
Zeller's Congruence:
h = (q + floor(13(m+1)/5) + K + floor(K/4) + floor(J/4) - 2J) mod 7
```

Where:
- q = day.
- m = month (with Jan and Feb treated as months 13 and 14 of the *previous* year).
- K = year mod 100.
- J = year / 100 (century).
- h = 0 for Saturday, 1 for Sunday, ..., 6 for Friday.

This is O(1) with no loop. The formula is from 19th-century astronomical calculations.

For interview, the day-counting approach is clearer. Mention Zeller's if the interviewer presses for O(1).

----------------------------------------

## Step 6: Why Count-Days Works

Given any reference date with a known weekday, every subsequent date has a weekday offset equal to the number of elapsed days modulo 7.

Math: if day D is weekday w, then day D + k is weekday `(w + k) % 7`.

Pick a reference early enough to cover all valid inputs, compute elapsed days, apply modulo.

----------------------------------------

## Step 7: Name It

**Day-counting with modular arithmetic**. A staple of calendar-related problems. The leap-year handling is fiddly but mechanical.

Related:
- Zeller's Congruence (closed form).
- Easter date calculation (more complex).
- ISO week number.
- Date arithmetic in databases (DATEDIFF, etc.).

----------------------------------------

## Step 8: Complexity

Time: **O(year - 1971)**. Essentially O(1) for bounded ranges.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class Solution {
    bool isLeap(int y) {
        return (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
    }

    int daysInMonth(int m, int y) {
        vector<int> days = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        if (m == 2 && isLeap(y)) return 29;
        return days[m - 1];
    }

public:
    string dayOfTheWeek(int day, int month, int year) {
        int total = 0;
        for (int y = 1971; y < year; ++y) {
            total += isLeap(y) ? 366 : 365;
        }
        for (int m = 1; m < month; ++m) {
            total += daysInMonth(m, year);
        }
        total += day - 1;

        // 1971-01-01 was a Friday. Sunday=0, Monday=1, ..., Saturday=6.
        // Friday = 5.
        vector<string> weekdays = {"Sunday", "Monday", "Tuesday", "Wednesday",
                                    "Thursday", "Friday", "Saturday"};
        return weekdays[(5 + total) % 7];
    }
};
```

Cleanly broken into helpers. The key fact is memorized: 1971-01-01 is Friday.

----------------------------------------

## Step 10: Follow-up Questions

- **Very old dates (before the Gregorian calendar).** Much more complex — Julian calendar rules.
- **Dates across time zones / DST.** Handled outside the "day of week" abstraction.
- **Computing days between two arbitrary dates.** Similar counting logic.
- **Zeller's Congruence for O(1).** Implementable directly.
- **Find all Mondays (or any weekday) in a year.** Enumerate Jan 1 to Dec 31, check each.
- **Why is 2000 a leap year but 1900 isn't?** Divisible by 400 vs just 100. The "fix" to the Julian calendar's drift.
