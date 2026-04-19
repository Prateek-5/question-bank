DATA = {
"Add Digits": {
  "concept": "Digital root — closed-form using modulo 9.",
  "intuition": "Repeatedly summing digits until one digit remains is the digital root. For any positive n, the digital root equals 1 + (n-1) % 9. This works because 10 ≡ 1 (mod 9), so a number is congruent to the sum of its digits modulo 9.",
  "explanation": "If n == 0 return 0. Else return 1 + (n - 1) % 9. The formula handles the special case where n is a multiple of 9 (should yield 9, not 0). The iterative simulation is also O(log n) per layer but the closed form is O(1).",
  "dry_run": "n = 38. 1 + (37 % 9) = 1 + 1 = 2. Verify: 3+8=11 → 1+1=2. ✓",
  "approach": "Either simulate by summing digits in a loop or use the O(1) digital-root formula.",
  "complexity": "O(1) time and space.",
  "code": """int addDigits(int n) {
    if (n == 0) return 0;
    return 1 + (n - 1) % 9;
}""",
  "followups": "- What if n can be arbitrary precision (string input)? Sum ASCII digits, mod 9.\n- Generalize to any base b (digital root mod b-1).\n- Prove the closed form via modular arithmetic."
},

"Subarray Sums Divisible by K": {
  "concept": "Prefix-sum + modulo bucket counting.",
  "intuition": "If two prefix sums have the same remainder mod k, the subarray between them sums to a multiple of k. Count how many prefix sums share each remainder and combine in pairs.",
  "explanation": "Maintain count[r] = number of prefix sums with remainder r. Initialize count[0]=1 (empty prefix). For each element, update running sum, compute r = ((sum % k) + k) % k to handle negatives, add count[r] to the answer, then increment count[r].",
  "dry_run": "nums=[4,5,0,-2,-3,1], k=5. Prefix mods: 4,4,4,2,4,0. count[0]=1 initial. Step 1: r=4, add 0, count[4]=1. Step 2: r=4, add 1, count[4]=2. Step 3: r=4, add 2, count[4]=3. Step 4: r=2, add 0, count[2]=1. Step 5: r=4, add 3, count[4]=4. Step 6: r=0, add 1, count[0]=2. Total=7.",
  "approach": "One pass with a size-k bucket; uses pigeonhole over prefix remainders.",
  "complexity": "Time: O(n). Space: O(k).",
  "code": """#include <bits/stdc++.h>
using namespace std;

int subarraysDivByK(vector<int>& nums, int k) {
    vector<int> cnt(k, 0); cnt[0] = 1;
    int sum = 0, ans = 0;
    for (int x : nums) {
        sum += x;
        int r = ((sum % k) + k) % k;
        ans += cnt[r];
        cnt[r]++;
    }
    return ans;
}""",
  "followups": "- Return the actual subarrays (not just count).\n- Subarray sums divisible by K with minimum length.\n- What if we want sums divisible by any of several ks?"
},

"Count of Matches in Tournament": {
  "concept": "Single-elimination: total matches = n - 1.",
  "intuition": "Every match eliminates exactly one team. To go from n teams down to 1 champion, exactly n-1 teams must be eliminated, hence n-1 matches.",
  "explanation": "Whether the bracket has byes or not, the invariant holds: each match produces one loser. Therefore the answer is simply n-1, regardless of how odd n is handled.",
  "dry_run": "n=7: matches = 6. (Round 1: 3 matches + 1 bye → 4 teams; Round 2: 2 matches → 2 teams; Round 3: 1 match. Total 6.)",
  "approach": "Direct formula n-1.",
  "complexity": "O(1).",
  "code": """int numberOfMatches(int n) { return n - 1; }""",
  "followups": "- Double elimination tournaments.\n- Round-robin: C(n,2) matches.\n- Best-of-k series: multiply by k."
},

"Day of the Week": {
  "concept": "Zeller's congruence or day-of-year counting from a known anchor date.",
  "intuition": "Pick a reference date whose weekday is known, then count the total days elapsed and take modulo 7 to find the target weekday.",
  "explanation": "From 1971-01-01 (Friday, index 5 if Sunday=0), compute the total number of days to the query date: account for leap years and days in months. Convert (5 + total_days) % 7 to a weekday name.",
  "dry_run": "Query 2019-08-31. Days from 1971 = sum of year-days + months-in-2019 + 31-1. Modulo 7 yields 6 → Saturday.",
  "approach": "Day-counting from epoch, with leap-year handling. Alternative: Zeller's formula.",
  "complexity": "O(year-1971) per query.",
  "code": """#include <bits/stdc++.h>
using namespace std;

string dayOfTheWeek(int d, int m, int y) {
    vector<string> days = {\"Sunday\",\"Monday\",\"Tuesday\",\"Wednesday\",\"Thursday\",\"Friday\",\"Saturday\"};
    vector<int> md = {31,28,31,30,31,30,31,31,30,31,30,31};
    auto leap = [](int y){ return (y%4==0 && y%100!=0) || y%400==0; };
    int total = 0;
    for (int yy = 1971; yy < y; ++yy) total += leap(yy) ? 366 : 365;
    for (int mm = 0; mm < m - 1; ++mm) total += md[mm] + (mm == 1 && leap(y));
    total += d - 1;
    return days[(5 + total) % 7]; // 1971-01-01 was Friday
}""",
  "followups": "- Handle BC dates or a wider range.\n- Use Zeller's congruence for O(1).\n- Compute day of year; Julian day number."
},

"Determine Color of a Chessboard Square": {
  "concept": "Parity of (column_letter + row_number).",
  "intuition": "Chessboard colors alternate along both axes. A square is white if column index + row number is even — or equivalently, if their sum is odd when taking 'a'=1 the known rule inverts; careful with conventions.",
  "explanation": "Let c = coords[0] - 'a' (0-indexed column), r = coords[1] - '1' (0-indexed row). Return (c + r) % 2 == 0 ? false : true, where 'a1' is black (false). Alternatively: if (c + r) is odd → white.",
  "dry_run": "'a1': c=0, r=0, sum=0, even → black (false). 'h3': c=7, r=2, sum=9, odd → white (true).",
  "approach": "O(1) parity check.",
  "complexity": "O(1).",
  "code": """bool squareIsWhite(string c) {
    return (c[0] + c[1]) % 2 == 1;
}""",
  "followups": "- Generalize to rectangular boards.\n- Count squares of each color on an N×M grid.\n- Knight's color-changing property between moves."
},

"Find Greatest Common Divisor of Array": {
  "concept": "GCD(min, max) — GCD of array equals GCD of its smallest and largest elements only *if* the array is specified that way; generally you iterate.",
  "intuition": "The problem specifically asks for GCD of the smallest and largest elements in the array — a single gcd call suffices.",
  "explanation": "Find min and max in one pass (or with STL). Return gcd(min, max) using Euclid's algorithm.",
  "dry_run": "nums=[2,5,6,9,10]. min=2, max=10. gcd(2,10)=2.",
  "approach": "Linear scan for min/max, then Euclidean gcd.",
  "complexity": "Time: O(n + log max). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findGCD(vector<int>& nums) {
    int lo = *min_element(nums.begin(), nums.end());
    int hi = *max_element(nums.begin(), nums.end());
    return __gcd(lo, hi);
}""",
  "followups": "- Compute GCD of all elements (fold gcd).\n- LCM of array.\n- GCD over a sliding window (segment tree)."
},

"Find the Pivot Integer": {
  "concept": "Prefix-sum equation: sum(1..x) = sum(x..n).",
  "intuition": "Both sides share x once. We need x(x+1)/2 = (n(n+1) - x(x-1))/2. Solving gives x = sqrt(n(n+1)/2). Check if the square root is an integer.",
  "explanation": "Compute S = n*(n+1)/2. We need x² = S, so check if round(sqrt(S))² == S. If yes return that x, else -1.",
  "dry_run": "n=8. S=36. sqrt(36)=6 → return 6. Verify: 1+...+6=21, 6+7+8=21. ✓",
  "approach": "Closed-form derivation; O(1) with a single sqrt check.",
  "complexity": "O(1).",
  "code": """#include <cmath>
int pivotInteger(int n) {
    int S = n * (n + 1) / 2;
    int x = (int)sqrt((double)S);
    return x * x == S ? x : -1;
}""",
  "followups": "- Weighted pivot where elements are arbitrary.\n- Pivot in a generic array — use prefix sums.\n- Multiple pivots counting problem."
},
}
