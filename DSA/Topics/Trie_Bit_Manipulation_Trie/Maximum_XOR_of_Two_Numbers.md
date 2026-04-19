# Maximum XOR of Two Numbers

**Problem Link:**
https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/

**Topic:**
Trie / Bit Manipulation Trie

----------------------------------------

## Step 1: What's XOR?

For two numbers, `a XOR b` compares them bit by bit. Each bit of the result is 1 if the corresponding bits of a and b **differ**, and 0 if they match.

Example in 5-bit:
- 3 (00011) XOR 5 (00101) = 00110 = 6. The two numbers differ in bits 1 and 2.
- 25 (11001) XOR 5 (00101) = 11100 = 28. Differ in bits 2, 3, 4.

**Maximizing XOR** means finding two numbers that differ in as many high-value bits as possible.

Given an array `nums`, find the max value of `a XOR b` over all pairs.

Example: `[3, 10, 5, 25, 2, 8]` → max XOR is 25 XOR 5 = 28.

----------------------------------------

## Step 2: Brute Force and Its Limit

Try all pairs: O(n²). Simple. For n = 10^5, that's 10^10 — too slow.

We need something smarter. The question becomes: can we find the optimal pair without checking every one?

----------------------------------------

## Step 3: Think Bit-by-Bit, Not Number-by-Number

Instead of picking two numbers and comparing, think about the **max XOR's binary representation**.

We want each bit of the max XOR to be 1, ideally. But we can't just freely choose 1s — we're constrained by what the array contains.

**Greedy idea:** go bit by bit from the most significant bit (say, bit 30) down to bit 0. At each bit, ask: **"Can we find two numbers in the array whose XOR has a 1 at this bit, consistent with the bits we've already 'locked in'?"**

If yes, set this bit to 1 in our running max. If no, it stays 0.

Higher bits matter more (bit 30 adds 2^30 ≈ 10^9 to the value), so this greedy is optimal: setting a 1 at a high bit beats anything we could gain at lower bits.

----------------------------------------

## Step 4: How to Answer "Can We Find Two Numbers With This XOR Pattern?"

Suppose we've decided max_xor's top bits so far. At the current bit, we want to check: does the array have two numbers x, y such that `x XOR y` equals `max_xor | (1 << current_bit)`, restricted to the bits decided so far?

Restricting to "bits decided so far" means we only care about the higher bits; ignore the lower ones.

Here's the trick. Let `mask` be a bitmask keeping bits from the current one upward. Compute the "high-bit prefix" of each number: `x & mask`. If two different prefixes in the array XOR to `candidate = max_xor | (1 << current_bit)`, then those prefixes' source numbers have the required XOR pattern at the high bits.

Mathematical insight: `a XOR b = candidate` is equivalent to `candidate XOR a = b`. So for each prefix `a`, check if `candidate XOR a` is also a prefix in the array. If yes, we've found a pair.

Using a hash set of prefixes makes the check O(1).

----------------------------------------

## Step 5: The Bit-by-Bit Algorithm

```
max_xor = 0
mask = 0

for bit in 30 down to 0:
    mask |= (1 << bit)          # include this bit in the mask

    prefixes = { x & mask for x in nums }   # set of all high-bit prefixes

    candidate = max_xor | (1 << bit)  # try to extend max_xor with a 1 at this bit

    for prefix p in prefixes:
        if (candidate XOR p) in prefixes:
            max_xor = candidate
            break          # confirmed: some pair achieves this XOR
    # if no match found, max_xor stays unchanged (this bit contributes 0)

return max_xor
```

Reading the inner check: we're looking for prefixes p, q where `p XOR q = candidate`. Equivalently, `candidate XOR p = q`. So for each p, we check "is `candidate XOR p` in the set?"

31 iterations (bits 30 to 0), each doing O(n) work. Total: **O(n · 32) = O(n)**.

----------------------------------------

## Step 6: Small Trace

`nums = [3, 10, 5]`. Expected max XOR is 3 XOR 10 = 9 (binary 1001), 3 XOR 5 = 6, 10 XOR 5 = 15. Max is 15.

In binary: 3 = 00011, 10 = 01010, 5 = 00101.

```
max_xor = 0, mask = 0.

bit 4 (value 16):
  mask = 10000.
  prefixes = {3 & 16, 10 & 16, 5 & 16} = {0, 0, 0} = {0}.
  candidate = 0 | 16 = 16.
  For p=0: 16 XOR 0 = 16. Is 16 in {0}? No.
  No match. max_xor stays 0.

bit 3 (value 8):
  mask = 11000.
  prefixes = {0, 8, 0} = {0, 8}.
  candidate = 0 | 8 = 8.
  For p=0: 8 XOR 0 = 8. In {0, 8}? Yes.
  max_xor = 8.

bit 2 (value 4):
  mask = 11100.
  prefixes = {0, 8, 4} = {0, 4, 8}.
  candidate = 8 | 4 = 12.
  For p=0: 12 XOR 0 = 12. Not in prefixes.
  For p=4: 12 XOR 4 = 8. In prefixes? Yes.
  max_xor = 12.

bit 1 (value 2):
  mask = 11110.
  prefixes = {2, 10, 4} = {2, 4, 10}.
  candidate = 12 | 2 = 14.
  For p=2: 14 XOR 2 = 12. Not in.
  For p=4: 14 XOR 4 = 10. In prefixes? Yes.
  max_xor = 14.

bit 0 (value 1):
  mask = 11111.
  prefixes = {3, 10, 5} (the originals).
  candidate = 14 | 1 = 15.
  For p=3: 15 XOR 3 = 12. Not in.
  For p=10: 15 XOR 10 = 5. In prefixes? Yes.
  max_xor = 15.
```

Final: 15. ✓ (10 XOR 5 = 15.)

Each bit we successfully set rules out some pairs and confirms there are compatible candidates. The greedy commits to each "1" as soon as it's possible.

----------------------------------------

## Step 7: Alternative — Build a Binary Trie

Another elegant approach: insert each number into a binary trie (where each node has at most 2 children, one for bit 0 and one for bit 1). Then for each number x, traverse the trie greedily: at each bit, try to go in the **opposite** direction of x's bit (since opposite XOR is 1). If that direction has a subtree, go there; else go the same direction.

After traversing all 32 bits, you've computed the max XOR of x with anything in the trie. Do this for each number; track the overall max.

Time: O(n · 32). Same complexity as the hashset approach, slightly more memory.

This is the "trie" flavor of the solution; the hashset is the "DP" flavor.

----------------------------------------

## Step 8: Name It

**Greedy bit-by-bit XOR maximization**, with either a **hashset** or **binary trie** for efficient lookups.

The key idea is that higher bits of XOR dominate, so a greedy "set bit if possible" strategy is optimal. The only algorithmic work is efficiently checking "is this bit achievable given our commitments so far?"

Similar patterns:
- Max XOR With Element in Array (offline query problem).
- Subarray XOR equals K (prefix-XOR + hashset).
- XOR-related problems generally lean on these tools.

----------------------------------------

## Step 9: Complexity

Time: **O(n · 32)** = O(n) for 32-bit ints.
Space: **O(n)** for the prefixes hashset (or O(n · 32) for the trie).

----------------------------------------

## Step 10: C++ Implementation

**Hashset version (cleaner):**

```cpp
int findMaximumXOR(vector<int>& nums) {
    int max_xor = 0;
    int mask = 0;
    for (int bit = 30; bit >= 0; --bit) {
        mask |= (1 << bit);
        unordered_set<int> prefixes;
        for (int x : nums) prefixes.insert(x & mask);

        int candidate = max_xor | (1 << bit);
        for (int p : prefixes) {
            if (prefixes.count(candidate ^ p)) {
                max_xor = candidate;
                break;
            }
        }
    }
    return max_xor;
}
```

The critical check is `prefixes.count(candidate ^ p)`. We're saying: "If `candidate = p ^ q`, then `q = candidate ^ p`. Does q's prefix exist in our set?"

**Binary trie version (more scalable):**

```cpp
struct TrieNode { TrieNode* ch[2] = {nullptr, nullptr}; };

class Trie {
    TrieNode* root = new TrieNode();
public:
    void insert(int n) {
        TrieNode* cur = root;
        for (int bit = 30; bit >= 0; --bit) {
            int b = (n >> bit) & 1;
            if (!cur->ch[b]) cur->ch[b] = new TrieNode();
            cur = cur->ch[b];
        }
    }
    int maxXor(int n) {
        TrieNode* cur = root;
        int result = 0;
        for (int bit = 30; bit >= 0; --bit) {
            int b = (n >> bit) & 1;
            int opp = 1 - b;
            if (cur->ch[opp]) { result |= (1 << bit); cur = cur->ch[opp]; }
            else cur = cur->ch[b];
        }
        return result;
    }
};

int findMaximumXOR(vector<int>& nums) {
    Trie trie;
    for (int x : nums) trie.insert(x);
    int best = 0;
    for (int x : nums) best = max(best, trie.maxXor(x));
    return best;
}
```

----------------------------------------

## Step 11: Follow-up Questions

- **Minimum XOR of two numbers.** Same trie approach, go in **same** direction (not opposite) greedily.
- **Max XOR with at most k elements.** Harder — combinatorial.
- **Max XOR of subarray.** Use prefix-XOR + trie.
- **Online queries: given x, find max XOR of x with previously-inserted numbers.** Trie is naturally online; hashset doesn't directly fit.
- **Why doesn't brute-force (O(n²)) work?** For n > 10^4, too slow. But it's fine for small inputs.
- **What if array contains duplicates?** No problem — duplicates XOR to 0, never best.
