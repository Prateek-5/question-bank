DATA = {
"Number of 1 Bits": {
  "concept": "Bit trick — n & (n-1) clears lowest set bit.",
  "intuition": "Each n&(n-1) drops exactly one set bit. Count iterations until zero.",
  "explanation": "while (n) { n &= n-1; cnt++; }.",
  "dry_run": "n=11 (1011). 1011→1010→1000→0000. 3 iterations → 3.",
  "approach": "Brian Kernighan's trick.",
  "complexity": "Time: O(popcount). Space: O(1).",
  "code": """int hammingWeight(unsigned n) { int c = 0; while (n) { n &= n - 1; c++; } return c; }""",
  "followups": "- Use __builtin_popcount.\n- SWAR parallel bit counting.\n- Hamming weight of a range of integers."
},

"Reverse Bits": {
  "concept": "Bit-by-bit reversal or swap-and-shift.",
  "intuition": "Read LSB of n, set it as the MSB of result. Shift both appropriately.",
  "explanation": "For 32 bits: r = (r << 1) | (n & 1); n >>= 1.",
  "dry_run": "n=43261596 (0000 0010 1001 0100 0001 1110 1001 1100) → reversed = 964176192.",
  "approach": "Loop 32 iterations.",
  "complexity": "Time: O(32). Space: O(1).",
  "code": """unsigned reverseBits(unsigned n) {
    unsigned r = 0;
    for (int i = 0; i < 32; ++i) { r = (r << 1) | (n & 1); n >>= 1; }
    return r;
}""",
  "followups": "- Parallel reversal via SWAR.\n- Reverse k-bit integer.\n- Cache repeated reversals with byte-lookup."
},

"Single Number": {
  "concept": "XOR accumulation cancels pairs.",
  "intuition": "x XOR x = 0 and XOR is commutative — paired values vanish; only the lone value survives.",
  "explanation": "XOR all elements; result is the single number.",
  "dry_run": "nums=[2,2,1] → 2^2^1=1.",
  "approach": "One pass XOR.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int singleNumber(vector<int>& a) { int x = 0; for (int v : a) x ^= v; return x; }""",
  "followups": "- Single Number II (others thrice).\n- Single Number III (two singletons).\n- Missing number."
},

"Single Number II": {
  "concept": "Bit counting mod 3 — every bit sums to 0 mod 3 except for the unique number.",
  "intuition": "For each of 32 bits, total count mod 3 is the bit of the lone number.",
  "explanation": "For each bit: ones=Σ((x>>b)&1); result bit = ones%3. Or use two-variable state machine (ones/twos).",
  "dry_run": "nums=[2,2,3,2] → each bit of 3 has one extra → result 3.",
  "approach": "Bit-count or state machine.",
  "complexity": "Time: O(32n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int singleNumberII(vector<int>& a) {
    int ones = 0, twos = 0;
    for (int x : a) {
        ones = (ones ^ x) & ~twos;
        twos = (twos ^ x) & ~ones;
    }
    return ones;
}""",
  "followups": "- Others appear k times.\n- Two numbers appear once.\n- Streaming variant."
},
}
