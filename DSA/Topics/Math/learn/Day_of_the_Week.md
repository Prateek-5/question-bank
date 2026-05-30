# Day of the Week — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Day_of_the_Week.md`](../Day_of_the_Week.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/day-of-the-week/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/day-of-the-week/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. **A calendar-arithmetic problem.** The lesson: **pick a reference date with known weekday, count elapsed days, take mod 7.** Leap-year handling is the fiddly part. Calendar problems mostly come down to careful day counting plus the Gregorian leap-year rule.

**Map of this file (9 short sections):**

1. Read the problem
2. The approach — count days from a reference
3. Picking the reference date
4. The leap-year rule
5. Counting algorithm
6. Code
7. Trace it
8. Common pitfalls
9. The shape — calendar arithmetic

---

## 1. Read the problem

Given a date as three integers `day`, `month`, `year`, return the day of the week as a string (e.g., `"Sunday"`, `"Monday"`, ..., `"Saturday"`).

Valid date range: **1971-01-01 to 2100-12-31**.

**Examples:**

- `day=31, month=8, year=2019` → `"Saturday"`.
- `day=18, month=7, year=1999` → `"Sunday"`.
- `day=15, month=8, year=1993` → `"Sunday"`.

---

## 2. The approach — count days from a reference

> **Mini-refresher: day-of-week is purely modular.**
>
> Days of the week cycle every 7 days. If date D is a Sunday, then D + 7 is also Sunday, D + 14 is Sunday, etc. More generally:
>
> > **If date D is weekday w, then date D + k is weekday `(w + k) % 7`.**
>
> So if you KNOW the weekday of SOME reference date, and you can COUNT DAYS between that reference and the input date, you can compute the input's weekday via `(reference_weekday + days_elapsed) % 7`.

So the algorithm: pick a reference date with known weekday → count days from reference to input → apply mod 7.

---

## 3. Picking the reference date

The problem's range starts at 1971-01-01. Convenient choice: **1971-01-01 was a Friday.** (Historical fact; can be verified.)

So:
- Reference: 1971-01-01.
- Reference weekday: Friday.
- For weekday encoding, let's use: Sunday=0, Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5, Saturday=6.
- So reference weekday = 5.

Computing the answer:
```
days_elapsed = days from 1971-01-01 to input_date
weekday_index = (5 + days_elapsed) % 7
return weekdays[weekday_index]
```

---

## 4. The leap-year rule

> **Mini-refresher: Gregorian leap years.**
>
> A year `y` is a leap year iff:
> - `y % 4 == 0` AND `y % 100 != 0`, OR
> - `y % 400 == 0`.
>
> Compactly: `(y % 4 == 0 and y % 100 != 0) or y % 400 == 0`.
>
> Examples:
> - 2000: 2000 % 400 == 0 → leap.
> - 1900: 1900 % 100 == 0 but NOT % 400 → NOT leap.
> - 2020: 2020 % 4 == 0, 2020 % 100 != 0 → leap.
> - 2019: 2019 % 4 != 0 → not leap.
>
> Why the rule? Earth's year is ~365.2425 days. Adding a leap day every 4 years overshoots slightly (365.25). The century exception undershoots (365.24). The 400-year exception fine-tunes to 365.2425. Accurate to about 1 day in 3000 years.

Days per month: 31, 28 (or 29 in leap), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31.

---

## 5. Counting algorithm

```
def days_in_month(m, y):
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if m == 2 and is_leap(y): return 29
    return days[m - 1]

def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0

total = 0

# Add full years from 1971 to year - 1.
for y in range(1971, year):
    total += 366 if is_leap(y) else 365

# Add full months from January to month - 1 of the target year.
for m in range(1, month):
    total += days_in_month(m, year)

# Add days within the target month.
total += day - 1

# Weekday index
return weekdays[(5 + total) % 7]
```

Maximum loop iterations: ~130 (years from 1971 to 2100) + 11 (months). Constant for practical purposes.

---

## 6. Code

**C++:**

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

        vector<string> weekdays = {"Sunday", "Monday", "Tuesday", "Wednesday",
                                     "Thursday", "Friday", "Saturday"};
        return weekdays[(5 + total) % 7];
    }
};
```

**Python:**

```python
def dayOfTheWeek(day, month, year):
    def is_leap(y):
        return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0

    def days_in_month(m, y):
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if m == 2 and is_leap(y): return 29
        return days[m - 1]

    total = 0
    for y in range(1971, year):
        total += 366 if is_leap(y) else 365
    for m in range(1, month):
        total += days_in_month(m, year)
    total += day - 1

    weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday"]
    return weekdays[(5 + total) % 7]
```

Complexity: **O(year - 1971) ≈ O(1) for the bounded range.** O(1) space.

---

## 7. Trace it

**`day=31, month=8, year=2019`.**

Full years 1971..2018 (48 years):
- Leap years in range: 1972, 1976, 1980, 1984, 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016. Count: 12. (2000 is a leap year per the 400 rule.)
- Total days: 48 × 365 + 12 = 17,532.

Full months Jan..Jul of 2019: 31 + 28 + 31 + 30 + 31 + 30 + 31 = 212 days. (2019 is not leap.)

Days in August: 31 - 1 = 30.

Grand total: 17,532 + 212 + 30 = 17,774.

Weekday: `(5 + 17774) % 7 = 17779 % 7`. Compute: 17779 / 7 = 2539 remainder 17779 - 17773 = 6.

`weekdays[6]` = `"Saturday"`. ✓

---

## 8. Common pitfalls

1. **Wrong leap-year rule.** The "every 4 years" rule alone gives WRONG answers for centuries that aren't multiples of 400. Use the full Gregorian rule.

2. **Counting the target day's days within the target month wrong.** Use `day - 1` (we count days BEFORE the target date, since the reference is 0-day-elapsed).

3. **Wrong reference weekday.** 1971-01-01 was a Friday. Confirm against an authoritative source.

4. **Off-by-one in year/month loops.** Sum days for years STRICTLY BEFORE the target year (`range(1971, year)` in Python is `[1971, year - 1]`, correct). Months STRICTLY BEFORE the target month.

5. **Forgetting to handle February correctly.** Use the leap-year check ONLY for February.

6. **Floating-point arithmetic.** Day counting should be all integers. Don't use `(year - 1971) * 365.25` — accumulates error.

7. **Trying to use Zeller's congruence and getting confused by its weird conventions.** Zeller's is O(1) but uses bizarre conventions (Jan and Feb treated as months 13/14 of the previous year). For interview, day-counting is clearer.

8. **Forgetting that the problem expects a specific string format.** Capital first letter, full name (`"Saturday"`, not `"SAT"`).

---

## 9. The shape — calendar arithmetic

This is the canonical "calendar problem" template:

> **Reference date with known weekday + day counting + mod 7 = any calendar-day question solved.**

Other calendar problems:
- **Days between two dates:** count days from each to a common reference, subtract.
- **Add N days to a date:** count days, add, then "decompose" back into year/month/day.
- **Is this date valid?:** check month range, day range with leap-year adjustment.
- **Last day of month:** `days_in_month(m, y)`.
- **What day was X days ago?:** subtract X.

In real-world code, USE A DATE LIBRARY (`std::chrono` in C++20, `datetime` in Python). The DIY approach is for interviews and embedded systems.

> **Mini-refresher: real-world date libraries.**
>
> ```cpp
> // C++20 with std::chrono
> auto date = year{2019} / 8 / 31;
> auto sys = sys_days{date};
> auto weekday_num = weekday{sys}.iso_encoding();   // 6 = Saturday
> ```
>
> ```python
> import datetime
> datetime.date(2019, 8, 31).strftime("%A")  # 'Saturday'
> ```
>
> Libraries handle leap years, time zones, locale-aware names. In an interview, demonstrate you can write it manually too.

**Pattern to internalize:**

> "All calendar-day questions reduce to: (1) reference date with known weekday, (2) count elapsed days carefully with leap-year handling, (3) modulo 7."

---

> **Self-check — the question to ask next time.**
>
> When you face any "what day / how many days / weekday" question, ask:
>
> > **"Can I count days from a known-weekday reference, accounting for leap years, then apply mod 7?"**
>
> If yes, you've solved any calendar-day problem.

---

## Cross-references

- **Reference card (post-mastery):** [`../Day_of_the_Week.md`](../Day_of_the_Week.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Add_Digits.md`](./Add_Digits.md), [`Count_of_Matches_in_Tournament.md`](./Count_of_Matches_in_Tournament.md) — observation puzzles.
  - Coming next: [`Find_the_Pivot_Integer.md`](./Find_the_Pivot_Integer.md), [`Find_Greatest_Common_Divisor_of_Array.md`](./Find_Greatest_Common_Divisor_of_Array.md).
