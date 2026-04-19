DATA = {
"Four Divisors": {
  "concept": "For each n, find divisors up to sqrt; only sum if divisor count is exactly 4.",
  "intuition": "A number with exactly 4 divisors has divisors {1, p, q, pq} for primes p≠q, or {1, p, p², p³} for prime p. Detect by enumerating up to sqrt(n).",
  "explanation": "For each n, collect divisors ≤ sqrt(n); pair with n/d unless d*d==n. If count is 4, add sum to answer.",
  "dry_run": "nums=[21,4,7]. 21: divisors 1,3,7,21 → sum=32. 4: 1,2,4 → 3 divisors. 7: 2 divisors. Answer=32.",
  "approach": "sqrt scan per number.",
  "complexity": "Time: O(N·sqrt(max)). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int sumFourDivisors(vector<int>& nums) {
    int ans = 0;
    for (int n : nums) {
        int cnt = 0, sum = 0;
        for (int i = 1; (long long)i*i <= n && cnt <= 4; ++i) if (n % i == 0) {
            cnt++; sum += i;
            if (i != n / i) { cnt++; sum += n / i; }
        }
        if (cnt == 4) ans += sum;
    }
    return ans;
}""",
  "followups": "- Numbers with exactly k divisors.\n- Sum of divisors sieve for many n.\n- Euler totient counting."
},

"Pow(x, n)": {
  "concept": "Binary exponentiation.",
  "intuition": "x^n = (x²)^(n/2) if n even; x * x^(n-1) if odd. Repeated squaring yields O(log n) multiplications.",
  "explanation": "If n < 0: x = 1/x, n = -n. Loop: if n odd multiply result by x; x = x*x; n >>= 1.",
  "dry_run": "x=2, n=10. x^10 = 4^5 = (16)·4 = 64·16 = 1024.",
  "approach": "Iterative binary exponentiation.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """double myPow(double x, int n) {
    long long N = n;
    if (N < 0) { x = 1.0 / x; N = -N; }
    double r = 1.0;
    while (N) {
        if (N & 1) r *= x;
        x *= x; N >>= 1;
    }
    return r;
}""",
  "followups": "- Modular exponentiation (x^n mod M).\n- Matrix exponentiation (Fibonacci).\n- Handle underflow/overflow."
},

"Largest Multiple of Three": {
  "concept": "Digit sum mod 3 analysis + greedy digit removal.",
  "intuition": "Sum of digits mod 3 determines divisibility. If sum%3==r, we must remove digits whose mods sum to r — preferring fewest and smallest digits.",
  "explanation": "Count digits. Compute total mod 3. If r>0, remove one digit ≡ r (smallest), else two digits ≡ 3-r. After removal, sort digits desc, handle leading zeros.",
  "dry_run": "digits=[8,1,9]. Sum=18, mod 3=0 → keep all. Sort desc → '981'.",
  "approach": "Digit-count + greedy.",
  "complexity": "Time: O(n log n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
string largestMultipleOfThree(vector<int>& d) {
    sort(d.begin(), d.end());
    int s = accumulate(d.begin(), d.end(), 0);
    auto removeOne = [&](int mod) {
        for (int i = 0; i < (int)d.size(); ++i) if (d[i] % 3 == mod) { d.erase(d.begin()+i); return true; }
        return false;
    };
    if (s % 3 == 1) { if (!removeOne(1)) { removeOne(2); removeOne(2); } }
    else if (s % 3 == 2) { if (!removeOne(2)) { removeOne(1); removeOne(1); } }
    sort(d.rbegin(), d.rend());
    string r; for (int x : d) r += char('0'+x);
    if (!r.empty() && r[0] == '0') return \"0\";
    return r;
}""",
  "followups": "- Largest multiple of N.\n- Smallest multiple of 3 using subset of digits.\n- Digit rearrangement to reach a divisibility class."
},

"Ugly Number": {
  "concept": "Divide out 2, 3, 5; final value must be 1.",
  "intuition": "An ugly number's prime factors only include 2, 3, 5. Keep dividing and check if 1 remains.",
  "explanation": "While n%2==0 n/=2; while n%3==0 n/=3; while n%5==0 n/=5. Return n==1.",
  "dry_run": "n=14 → divide 2 → 7. 7≠1 → false.",
  "approach": "Iterative factor stripping.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """bool isUgly(int n) {
    if (n <= 0) return false;
    for (int p : {2, 3, 5}) while (n % p == 0) n /= p;
    return n == 1;
}""",
  "followups": "- Ugly Number II (nth ugly).\n- Super Ugly (arbitrary prime list).\n- Count uglies up to N."
},

"Max Consecutive Ones": {
  "concept": "Running counter reset on 0.",
  "intuition": "Track the length of the current streak of 1s; update the max when it grows.",
  "explanation": "cur=0, best=0. For each x: cur = x?cur+1:0; best=max(best,cur).",
  "dry_run": "nums=[1,1,0,1,1,1]. Streaks 2 then 3 → best=3.",
  "approach": "Single pass.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findMaxConsecutiveOnes(vector<int>& a) {
    int cur = 0, best = 0;
    for (int x : a) { cur = x ? cur + 1 : 0; best = max(best, cur); }
    return best;
}""",
  "followups": "- Flip at most k zeros (sliding window).\n- Longest run of any value.\n- 2D grid variant."
},

"Number of Good Pairs": {
  "concept": "For each value of count c, pairs = C(c,2).",
  "intuition": "Two indices i<j form a good pair iff nums[i]==nums[j]. For each value with count c, pairs = c*(c-1)/2.",
  "explanation": "Count occurrences; sum c*(c-1)/2.",
  "dry_run": "nums=[1,2,3,1,1,3]. Counts {1:3,2:1,3:2}. Pairs 3+0+1=4.",
  "approach": "Hashmap frequency.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int numIdenticalPairs(vector<int>& a) {
    unordered_map<int,int> c;
    int ans = 0;
    for (int x : a) ans += c[x]++;
    return ans;
}""",
  "followups": "- Good pairs at distance ≤ k.\n- Ordered pairs (i<j with constraint).\n- With updates."
},

"Self Dividing Numbers": {
  "concept": "For each n in [L,R], check all its digits are non-zero and divide n.",
  "intuition": "A self-dividing number has only digits that are divisors of itself. Enumerate and test.",
  "explanation": "For each n: d=n; while d: q=d%10; if q==0 or n%q!=0 fail; d/=10. If pass, add n.",
  "dry_run": "Range [1,22]. Numbers 1..9 all qualify. 11 works (1,1). 12 (1,2) works. 13 (1,3) 13%3≠0 fail. Etc.",
  "approach": "Brute force digit test.",
  "complexity": "Time: O((R-L+1)·logR). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> selfDividingNumbers(int L, int R) {
    vector<int> r;
    for (int n = L; n <= R; ++n) {
        int d = n; bool ok = true;
        while (d) {
            int q = d % 10;
            if (!q || n % q) { ok = false; break; }
            d /= 10;
        }
        if (ok) r.push_back(n);
    }
    return r;
}""",
  "followups": "- Self-dividing with custom base.\n- Harshad numbers.\n- Armstrong numbers."
},

"Subsequence of Size K With Largest Sum": {
  "concept": "Partition-based selection of k largest keeping original order.",
  "intuition": "The largest-sum subsequence is the k largest values. We need to preserve original order — so record their indices.",
  "explanation": "Pair values with indices. nth_element by value descending to get top k by value. Sort those k by original index. Output values.",
  "dry_run": "nums=[2,1,3,3], k=2. Top 2 values: 3,3 (indices 2,3). Output [3,3].",
  "approach": "Selection + sort by index.",
  "complexity": "Time: O(n log k). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> maxSubsequence(vector<int>& a, int k) {
    int n = a.size();
    vector<int> idx(n); iota(idx.begin(), idx.end(), 0);
    nth_element(idx.begin(), idx.begin()+k, idx.end(), [&](int x, int y){ return a[x] > a[y]; });
    vector<int> pick(idx.begin(), idx.begin()+k);
    sort(pick.begin(), pick.end());
    vector<int> r;
    for (int i : pick) r.push_back(a[i]);
    return r;
}""",
  "followups": "- Minimum-sum subsequence.\n- Tie-break by earliest indices.\n- Streaming version."
},

"Subtract Product and Sum of Digits": {
  "concept": "Compute digit product and sum in one pass.",
  "intuition": "Simple decomposition of n into digits.",
  "explanation": "While n>0: d=n%10; p*=d; s+=d; n/=10. Return p-s.",
  "dry_run": "n=234 → digits 2,3,4. p=24, s=9 → 15.",
  "approach": "Loop.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """int subtractProductAndSum(int n) {
    int p = 1, s = 0;
    while (n) { int d = n % 10; p *= d; s += d; n /= 10; }
    return p - s;
}""",
  "followups": "- Handle arbitrary base.\n- Digit GCD/LCM.\n- Digit power sum."
},

"Memoization / DP Basics": {
  "concept": "Memoized recursion — cache results to avoid recomputation.",
  "intuition": "DP problems often have overlapping subproblems; caching transforms exponential recursion into polynomial.",
  "explanation": "Identify state; write recurrence; cache via map/array; base case; return cached on hit.",
  "dry_run": "Fibonacci f(5)=f(4)+f(3); each subproblem computed once with memo[].",
  "approach": "Top-down recursion with memoization.",
  "complexity": "Depends on state count × work per state.",
  "code": """#include <bits/stdc++.h>
using namespace std;
int fib(int n, vector<int>& memo) {
    if (n < 2) return n;
    if (memo[n] != -1) return memo[n];
    return memo[n] = fib(n-1, memo) + fib(n-2, memo);
}""",
  "followups": "- Bottom-up conversion.\n- Space optimization with rolling arrays.\n- Recognizing DP states in new problems."
},

"Divisor Game": {
  "concept": "Parity observation — Alice wins iff n is even.",
  "intuition": "Working backward, n=1 loses (no moves). n=2 wins. By induction, even → winning; odd → losing. So answer is n%2==0.",
  "explanation": "Return n%2==0 — Alice always picks 1, forcing Bob onto an odd number, and so on.",
  "dry_run": "n=2 → true. n=3 → false.",
  "approach": "Parity check.",
  "complexity": "O(1).",
  "code": """bool divisorGame(int n) { return n % 2 == 0; }""",
  "followups": "- Divisor game with different rules.\n- Game DP proof.\n- Mis`ere variant."
},

"Implement Rand10() Using Rand7()": {
  "concept": "Rejection sampling from a uniform 49-sample space.",
  "intuition": "rand7()·7+rand7() generates uniform [1..49]. Keep only 1..40 for uniform [1..10] via mod.",
  "explanation": "Loop: x = (rand7()-1)*7 + rand7() ∈ [1,49]. If x <= 40, return 1 + (x-1)%10.",
  "dry_run": "Expected rejection chance 9/49. On accept, value 1..10 uniform.",
  "approach": "Rejection sampling.",
  "complexity": "Expected O(1) samples.",
  "code": """int rand7();
int rand10() {
    while (true) {
        int x = (rand7() - 1) * 7 + rand7();
        if (x <= 40) return 1 + (x - 1) % 10;
    }
}""",
  "followups": "- Generate rand(n) using rand(m).\n- Minimize expected calls.\n- Rand10 from rand2 (binary expansion)."
},

"Largest Number That Divides X and Is Co-Prime with Y": {
  "concept": "Divide x by gcd(x,y) repeatedly — remove all prime factors shared with y.",
  "intuition": "We want d | x and gcd(d,y)=1. Strip from x all prime factors it shares with y, leaving the largest coprime divisor.",
  "explanation": "Loop: g = gcd(x, y). If g == 1 stop. Else x /= g. Return x.",
  "dry_run": "x=12, y=15. gcd=3, x=4. gcd(4,15)=1 → 4. 4 divides 12 and gcd(4,15)=1.",
  "approach": "Iterative gcd peeling.",
  "complexity": "Time: O(log x). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int largestCoprimeDivisor(int x, int y) {
    while (__gcd(x, y) != 1) x /= __gcd(x, y);
    return x;
}""",
  "followups": "- Smallest coprime divisor >1.\n- Coprime divisors count.\n- Modular variant."
},

"Lucky Numbers in a Matrix": {
  "concept": "Row min ∩ column max.",
  "intuition": "A lucky number is the minimum in its row and simultaneously the maximum in its column. Precompute row-mins and col-maxes and intersect.",
  "explanation": "Compute rowMin[i], colMax[j]. For each cell equal to both rowMin[i] and colMax[j], add to result.",
  "dry_run": "M=[[3,7,8],[9,11,13],[15,16,17]]. rowMin=[3,9,15]. colMax=[15,16,17]. Only 15 matches both → answer [15].",
  "approach": "Two passes.",
  "complexity": "Time: O(n·m). Space: O(n+m).",
  "code": """#include <bits/stdc++.h>
using namespace std;
vector<int> luckyNumbers(vector<vector<int>>& M) {
    int n = M.size(), m = M[0].size();
    vector<int> rmn(n, INT_MAX), cmx(m, INT_MIN);
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) { rmn[i]=min(rmn[i], M[i][j]); cmx[j]=max(cmx[j], M[i][j]); }
    vector<int> res;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (M[i][j]==rmn[i] && M[i][j]==cmx[j]) res.push_back(M[i][j]);
    return res;
}""",
  "followups": "- Median-based lucky numbers.\n- Matrix with ties (multiple minima).\n- Sparse matrices."
},

"Number of Digit One": {
  "concept": "Digit-DP counting ones across positions.",
  "intuition": "For each digit position, count how many times '1' appears there among numbers 1..n by comparing the digit at that position with high and low parts.",
  "explanation": "For factor f from 1 upward while n >= f: high = n / (f*10); cur = (n / f) % 10; low = n % f. If cur > 1: add (high+1)*f. If cur == 1: add high*f + low + 1. Else add high*f.",
  "dry_run": "n=13. f=1: high=1,cur=3,low=0 → 2. f=10: high=0,cur=1,low=3 → 0+3+1=4. Total=6.",
  "approach": "Digit-position counting.",
  "complexity": "Time: O(log n). Space: O(1).",
  "code": """int countDigitOne(int n) {
    long long res = 0, f = 1;
    while ((long long)f <= n) {
        long long h = n / (f * 10), cur = (n / f) % 10, low = n % f;
        if (cur > 1) res += (h + 1) * f;
        else if (cur == 1) res += h * f + low + 1;
        else res += h * f;
        f *= 10;
    }
    return (int)res;
}""",
  "followups": "- Count digit d (other than 1).\n- Digit-DP for sums/XOR over ranges.\n- Count numbers with specific digit property."
},

"Number of Open Doors": {
  "concept": "Perfect-square toggles — i doors open iff i is a perfect square.",
  "intuition": "Door i is toggled once per divisor. Divisors pair up symmetrically except for perfect squares — which have an odd divisor count, leaving them toggled (open).",
  "explanation": "Count of open doors after n passes = floor(sqrt(n)).",
  "dry_run": "n=10 → sqrt=3 → 3 doors open (1,4,9).",
  "approach": "Closed form.",
  "complexity": "O(1).",
  "code": """#include <cmath>
int openDoors(int n) { return (int)sqrt((double)n); }""",
  "followups": "- Which doors are open (list).\n- K-pass toggling variant.\n- Prime-indexed toggling."
},

"Rectangle Area": {
  "concept": "Sum of two rectangle areas minus overlap (inclusion-exclusion).",
  "intuition": "Total covered = A + B − overlap. Overlap is the intersection rectangle area; 0 if they don't overlap.",
  "explanation": "A = (ax2-ax1)*(ay2-ay1); similar for B. Overlap width = max(0, min(ax2,bx2) - max(ax1,bx1)); height analogous. Total = A + B - overlap.",
  "dry_run": "A rect=(−3,0)-(3,4), B=(0,−1)-(9,2). A=24, B=27, overlap width=3, height=2 → 6. Total=45.",
  "approach": "Inclusion-exclusion of two axis-aligned rectangles.",
  "complexity": "O(1).",
  "code": """int computeArea(int a,int b,int c,int d,int e,int f,int g,int h) {
    int A = (c-a)*(d-b), B = (g-e)*(h-f);
    int w = max(0, min(c,g) - max(a,e));
    int ht = max(0, min(d,h) - max(b,f));
    return A + B - w * ht;
}""",
  "followups": "- N rectangles union area (sweep line).\n- 3D axis-aligned boxes.\n- Rectangles with rotation (convex polygon overlap)."
},

"Teemo Attacking": {
  "concept": "Sum of overlap-adjusted durations.",
  "intuition": "Each attack poisons for duration, but a new attack before the previous one ends just resets the end. Accumulate min(duration, nextStart - thisStart).",
  "explanation": "For i=0..n-2: add min(duration, timeSeries[i+1] - timeSeries[i]). Add duration for last attack.",
  "dry_run": "timeSeries=[1,4], duration=2. min(2, 3)=2, +2 last = 4.",
  "approach": "Single pass.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int findPoisonedDuration(vector<int>& t, int d) {
    int total = 0;
    for (int i = 0; i + 1 < (int)t.size(); ++i)
        total += min(d, t[i+1] - t[i]);
    return total + (t.empty() ? 0 : d);
}""",
  "followups": "- Variable per-attack duration.\n- Minimum attacks to poison fully.\n- Interval merging generalization."
},

"Total Number of Divisors of a Given Number": {
  "concept": "Divisor-count via prime factorization: (e1+1)(e2+1)...",
  "intuition": "Each divisor corresponds to a choice of exponents within the prime factorization. Sum up exponent+1 product gives divisor count.",
  "explanation": "Factorize n by trial division up to sqrt(n). For each prime p with exponent e, multiply answer by (e+1).",
  "dry_run": "n=12=2²·3. (2+1)(1+1)=6 → divisors: 1,2,3,4,6,12.",
  "approach": "Trial division + exponent collection.",
  "complexity": "Time: O(sqrt n). Space: O(1).",
  "code": """int divisorCount(int n) {
    int ans = 1;
    for (int p = 2; (long long)p*p <= n; ++p) {
        if (n % p) continue;
        int e = 0; while (n % p == 0) { n /= p; e++; }
        ans *= (e + 1);
    }
    if (n > 1) ans *= 2;
    return ans;
}""",
  "followups": "- Sum of divisors formula.\n- Count divisors sieve for many n.\n- Aliquot sum."
},
}
