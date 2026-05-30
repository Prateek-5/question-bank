# Maximum XOR of Two Numbers — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_XOR_of_Two_Numbers.md`](../Maximum_XOR_of_Two_Numbers.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~24 minutes. **The lesson: use a BIT TRIE (binary trie indexed by each bit). For each number, walk the trie greedily preferring OPPOSITE BITS at each level — opposite bits XOR to 1 (good).** Senior-bar problem. **Read [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md) and [`Number_of_1_Bits.md`](../../Bit_Manipulation/learn/Number_of_1_Bits.md) first.**

**Map of this file (10 sections):**

1. Read the problem
2. The brute force O(n²)
3. Greedy bit-by-bit from MSB
4. The bit trie data structure
5. Greedy walk for max XOR
6. Code
7. Trace it
8. Why MSB-first greedy is optimal
9. Common pitfalls
10. The shape — binary tries

---

## 1. Read the problem

Given an integer array `nums`, return the **MAXIMUM** value of `a XOR b` over all pairs `(a, b)` from the array.

**Example:** `nums = [3, 10, 5, 25, 2, 8]`.

Max XOR: 25 XOR 5 = 28. Return **28**.

---

## 2. The brute force O(n²)

Try every pair, compute XOR, track max.

```
max_xor = 0
for i in 0..n-1:
    for j in i+1..n-1:
        max_xor = max(max_xor, nums[i] ^ nums[j])
return max_xor
```

O(n²). For n = 10⁵, 10¹⁰ ops — TLE.

We need O(n) or O(n log V).

---

## 3. Greedy bit-by-bit from MSB

> **Mini-refresher: max XOR via greedy bit construction.**
>
> Build the maximum XOR ONE BIT AT A TIME, from MOST SIGNIFICANT to LEAST.
>
> At bit position k (highest first): can we find two numbers whose XOR has a 1 at this bit? If yes, set this bit in our answer. If no, leave it 0 — no pair achieves a 1 here.
>
> Higher bits are EXPONENTIALLY more valuable (2^k). Setting a 1 at bit 30 dominates all bits 0..29 combined. Greedy MSB-first is optimal.

For each bit, we check: does there EXIST a pair where this bit XORs to 1? If yes, commit.

To check efficiently, we use a BINARY TRIE.

---

## 4. The bit trie data structure

> **Mini-refresher: binary trie.**
>
> A **binary trie** is a trie where each node has at most TWO children (one for bit `0`, one for bit `1`). Insert a number by walking its bits MSB→LSB; create children as needed.
>
> The trie has DEPTH 32 (for 32-bit ints). Insertion is O(32). Each path from root to leaf represents one number's bit pattern.

```
class BitTrieNode:
    children = [null, null]   # indexed by bit (0 or 1)
```

Insertion:
```
def insert(n):
    cur = root
    for bit in range(30, -1, -1):
        b = (n >> bit) & 1
        if cur.children[b] is null:
            cur.children[b] = new BitTrieNode()
        cur = cur.children[b]
```

---

## 5. Greedy walk for max XOR

To find the max XOR of `n` with any number in the trie:

For each bit (MSB first), TRY TO GO THE OPPOSITE DIRECTION of n's bit. Opposite bits XOR to 1.

```
def max_xor_with(n):
    cur = root
    result = 0
    for bit in range(30, -1, -1):
        b = (n >> bit) & 1
        opposite = 1 - b
        if cur.children[opposite]:
            result |= (1 << bit)        # we can set this bit to 1
            cur = cur.children[opposite]
        else:
            cur = cur.children[b]        # forced to go same direction
    return result
```

Algorithm: insert all numbers into the trie; for each number, query the trie for its max XOR partner; track the overall max.

```
for n in nums: trie.insert(n)
best = 0
for n in nums: best = max(best, trie.max_xor_with(n))
return best
```

O(n × 32) = **O(n)** time for 32-bit ints.

---

## 6. Code

**C++:**

```cpp
struct TrieNode {
    TrieNode* ch[2] = {nullptr, nullptr};
};

class Solution {
    TrieNode* root = new TrieNode();

    void insert(int n) {
        TrieNode* cur = root;
        for (int bit = 30; bit >= 0; --bit) {
            int b = (n >> bit) & 1;
            if (!cur->ch[b]) cur->ch[b] = new TrieNode();
            cur = cur->ch[b];
        }
    }

    int maxXorWith(int n) {
        TrieNode* cur = root;
        int result = 0;
        for (int bit = 30; bit >= 0; --bit) {
            int b = (n >> bit) & 1;
            int opp = 1 - b;
            if (cur->ch[opp]) {
                result |= (1 << bit);
                cur = cur->ch[opp];
            } else {
                cur = cur->ch[b];
            }
        }
        return result;
    }

public:
    int findMaximumXOR(vector<int>& nums) {
        for (int n : nums) insert(n);
        int best = 0;
        for (int n : nums) best = max(best, maxXorWith(n));
        return best;
    }
};
```

**Python:**

```python
def findMaximumXOR(nums):
    root = {}
    
    def insert(n):
        cur = root
        for bit in range(30, -1, -1):
            b = (n >> bit) & 1
            if b not in cur:
                cur[b] = {}
            cur = cur[b]
    
    def max_xor_with(n):
        cur = root
        result = 0
        for bit in range(30, -1, -1):
            b = (n >> bit) & 1
            opp = 1 - b
            if opp in cur:
                result |= (1 << bit)
                cur = cur[opp]
            else:
                cur = cur[b]
        return result
    
    for n in nums: insert(n)
    return max(max_xor_with(n) for n in nums)
```

Complexity: **O(n × 32) = O(n) time, O(n × 32) space.**

---

## 7. Trace it

**`nums = [3, 10, 5]`.** Expected max: 10 XOR 5 = 15 (binary 1111).

Binary representations:
- 3 = 011.
- 10 = 1010.
- 5 = 101.

For brevity, use 4 bits.

Insert all into trie:
```
root
 ├── 0
 │    └── 0
 │         └── 1
 │              └── 1   (3)
 ├── 1
 │    ├── 0
 │    │    ├── 1
 │    │    │    └── 0   (10)
 │    │    └── 0
 │    │         └── 1   (5)
 (etc.)
```

(Sketchy ASCII — actual structure has 4 levels of {0, 1} children.)

**maxXorWith(10) = ?** (10 = 1010, want partner whose bits differ).

Walk:
- bit 3: 10's bit = 1. Try opp = 0. root has child 0 (for 3). result |= 8 → 8. Go to 0.
- bit 2: 10's bit = 0. Try opp = 1. Current is 0 (root.0). Does it have child 1? No (only 3 = 0011 went through here; bit 2 of 3 is 0). Go to 0.
- bit 1: 10's bit = 1. Try opp = 0. ... walking through 3's bits.
- bit 0: 10's bit = 0. Try opp = 1. Reaches 3's leaf.

Result for 10 vs 3: bits differ as 10⊕3 = 9. Less than 15.

Actually with 5 in the trie too, the path for opp at bit 3 leads to **5 too** (since 5 = 0101, bit 3 of 5 is 0). The trie has both 3 and 5 in the 0-subtree at bit 3.

When we walk for 10:
- bit 3: opp = 0 → 0-subtree (contains 3 and 5).
- bit 2: 10's bit = 0, opp = 1 → 0/1-subtree (5 went 0→1; 3 went 0→0). Subtree has 5.
- bit 1: 10's bit = 1, opp = 0 → 5's path goes 0→1→0. Match.
- bit 0: 10's bit = 0, opp = 1 → 5's bit 0 is 1. Match.

result = 8 | 4 | 2 | 1 = 15. ✓

So max_xor_with(10) = 15 = 10 XOR 5.

Final max across all queries: 15.

---

## 8. Why MSB-first greedy is optimal

> **Mini-refresher: MSB dominates LSBs.**
>
> Bit k has value 2^k. Bit 30 = ~10⁹. Bits 0-29 sum to less than 2^30.
>
> So setting a 1 at bit 30 ALONE beats setting 1's at every other bit.
>
> Greedy: at each bit from MSB to LSB, take a 1 if possible.

The trie lets us check "can we get a 1 at this bit while staying consistent with bits already chosen?" in O(1) per bit (just check if the opposite child exists).

---

## 9. Common pitfalls

1. **Walking LSB to MSB.** Greedy fails because lower bits don't dominate. ALWAYS MSB first.

2. **Trying brute force.** O(n²); TLE.

3. **Bit shift errors.** `(n >> bit) & 1` extracts bit `bit`. Don't confuse with `n & (1 << bit)`.

4. **Off-by-one in bit range.** For 32-bit ints, bit range is 0..31. The problem typically restricts to non-negative, so 30 is sufficient (max value 10⁹ < 2^30).

5. **Inserting and querying with different bit lengths.** Be consistent.

6. **Forgetting to insert all numbers before querying.** Insert first, then query.

7. **Allocating `ch[]` with wrong size.** Bit trie has 2 children, not 26.

---

## 10. The shape — binary tries

The pattern:

> **"For XOR-related problems over integers, use a BINARY TRIE (bits as edges). MSB-first greedy gives optimal XOR matching in O(32) per query."**

| Problem | Use of binary trie |
|---|---|
| **This problem** | max XOR of pair |
| Max XOR With an Element From Array | online query: max XOR(x, nums[i]) with i ≤ some bound |
| XOR Queries of a Subarray | prefix XOR + trie |
| Sum of XORs of subsets | similar bit reasoning |
| Maximum Genetic Difference Query | trie + tree DFS |

**Pattern to internalize:**

> "Tries aren't just for strings. A BINARY TRIE indexed by BITS solves XOR maximization problems by exploiting bit-level greedy."

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_XOR_of_Two_Numbers.md`](../Maximum_XOR_of_Two_Numbers.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md), [`Design_Add_and_Search_Words_DS.md`](./Design_Add_and_Search_Words_DS.md).
  - [`../../Bit_Manipulation/learn/Single_Number.md`](../../Bit_Manipulation/learn/Single_Number.md) — XOR algebra.
