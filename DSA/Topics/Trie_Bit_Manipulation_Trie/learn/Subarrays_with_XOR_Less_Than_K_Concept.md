# Subarrays with XOR Less Than K (Concept) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Subarrays_with_XOR_Less_Than_K_Concept.md`](../Subarrays_with_XOR_Less_Than_K_Concept.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/subarray-xor-queries/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: PREFIX XOR + BINARY TRIE for counting pairs where the pair-XOR has a property. Walk the trie bit-by-bit, counting "tight" matches.** Senior-bar problem. **Read [`Maximum_XOR_of_Two_Numbers.md`](./Maximum_XOR_of_Two_Numbers.md) and [`Subarray_Sums_Divisible_by_K.md`](../../Math/learn/Subarray_Sums_Divisible_by_K.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The brute force
3. Prefix XOR — reframe as pair counting
4. Bit trie augmented with subtree count
5. Counting "XOR < k" via tree walk
6. Code
7. Trace it
8. Common pitfalls
9. The shape — XOR + counting

---

## 1. Read the problem

Given an integer array `nums` and an integer `k`, count the number of **contiguous subarrays** whose XOR is **strictly less than k**.

**Example:** `nums = [1, 2, 3]`, `k = 2`.

Subarrays and their XOR:
- `[1]` → 1. < 2 ✓.
- `[1, 2]` → 3. ✗.
- `[1, 2, 3]` → 0. < 2 ✓.
- `[2]` → 2. ✗.
- `[2, 3]` → 1. < 2 ✓.
- `[3]` → 3. ✗.

Count = **3**.

---

## 2. The brute force

For each pair (i, j) with i ≤ j, compute XOR of nums[i..j]. Using prefix XORs, each XOR is O(1); so O(n²) total. For n = 10⁵: 10¹⁰ — TLE.

We need O(n × B) where B = bit width.

---

## 3. Prefix XOR — reframe as pair counting

> **Mini-refresher: prefix XOR.**
>
> Define `pre[0] = 0`, `pre[i] = nums[0] XOR nums[1] XOR ... XOR nums[i-1]`.
>
> XOR of subarray `nums[i..j-1]` = `pre[j] XOR pre[i]`.

**Reframe:** count pairs `(i, j)` with `i < j` such that `pre[j] XOR pre[i] < k`.

Equivalent: process prefix XORs one at a time. For each new `pre[j]`, count how many EARLIER prefixes `p` satisfy `pre[j] XOR p < k`. Sum over all j.

A binary trie can count efficiently.

---

## 4. Bit trie augmented with subtree count

Same binary trie as Maximum XOR, but each node stores `count` = number of values whose insertion path passes through this node.

```
class BitTrieNode:
    children = [null, null]   # indexed by bit (0 or 1)
    count = 0
```

Insert:
```
def insert(n):
    cur = root
    for bit in 30..0:
        b = (n >> bit) & 1
        if cur.children[b] is null:
            cur.children[b] = new BitTrieNode()
        cur = cur.children[b]
        cur.count += 1
```

After insertion, each node knows how many values stored share the prefix encoded by the path to it.

---

## 5. Counting "XOR < k" via tree walk

For each new `pre[j]`, count how many existing values `p` satisfy `pre[j] XOR p < k`.

> **Mini-refresher: greedy bit walk.**
>
> At each bit position (MSB to LSB), look at the bit of `pre[j]` and bit of `k`:
>
> - **If k's bit is 1**: ANY value `p` whose XOR with pre[j] has bit 0 here gives XOR_so_far + 0×2^b + (lower bits) < k_so_far + 1×2^b. The whole subtree on that branch is valid — count it. Then commit to the "XOR-bit = 1" branch to continue checking lower bits in the TIGHT case.
> - **If k's bit is 0**: XOR's bit must be 0 here (else we exceed k). Commit to the "XOR-bit = 0" branch.

Pseudocode:

```
def count_less_than_k(x, k):
    cur = root
    count = 0
    for bit in 30..0:
        xb = (x >> bit) & 1
        kb = (k >> bit) & 1
        if kb == 1:
            # "XOR-bit = 0" branch is the child matching xb (same bit)
            if cur.children[xb] exists:
                count += cur.children[xb].count
            # Now commit to "XOR-bit = 1" branch — go to opposite bit
            if cur.children[1 - xb] exists:
                cur = cur.children[1 - xb]
            else:
                break
        else:
            # XOR-bit must be 0 → same-bit child
            if cur.children[xb] exists:
                cur = cur.children[xb]
            else:
                break
    return count
```

Each iteration is O(1). Total: **O(B)** per query, where B = bit width.

---

## 6. Code

**C++:**

```cpp
struct TrieNode {
    int count = 0;
    TrieNode* ch[2] = {nullptr, nullptr};
};

class XorTrie {
    TrieNode* root = new TrieNode();
    static const int BITS = 30;

public:
    void insert(int x) {
        TrieNode* cur = root;
        for (int b = BITS - 1; b >= 0; --b) {
            int bit = (x >> b) & 1;
            if (!cur->ch[bit]) cur->ch[bit] = new TrieNode();
            cur = cur->ch[bit];
            cur->count++;
        }
    }

    int countLessThan(int x, int k) {
        TrieNode* cur = root;
        int count = 0;
        for (int b = BITS - 1; b >= 0 && cur; --b) {
            int xb = (x >> b) & 1;
            int kb = (k >> b) & 1;
            if (kb == 1) {
                if (cur->ch[xb]) count += cur->ch[xb]->count;
                cur = cur->ch[1 - xb];
            } else {
                cur = cur->ch[xb];
            }
        }
        return count;
    }
};

int countSubarraysXorLessThanK(vector<int>& nums, int k) {
    XorTrie trie;
    trie.insert(0);            // pre[0] = 0
    int pre = 0, answer = 0;
    for (int num : nums) {
        pre ^= num;
        answer += trie.countLessThan(pre, k);
        trie.insert(pre);
    }
    return answer;
}
```

Complexity: **O(n × B) = O(n) time** for B = 30, **O(n × B) space.**

---

## 7. Trace it

`nums = [1, 2]`, `k = 2`. Expected: 1.

`pre = [0, 1, 3]`.

```
Insert pre[0] = 0. Trie: 00 (in 2-bit).

Process num=1, pre=1. Count values p such that p XOR 1 < 2.
  Walk: bit 1: x=0, k=1. kb=1. xb=0. count += children[0].count = 1. Then go to children[1] (doesn't exist if only 00 inserted). Break.
  Count = 1.
Insert pre=1.

Process num=2, pre=3. Count values p such that p XOR 3 < 2.
  Walk: bit 1: x=1, k=1. kb=1. xb=1. count += children[1].count = 1 (for pre=1). Then go to children[0] (for pre=0). 
  bit 0: x=1, k=0. xb=1. Go to children[1]. children[0] of root has children[1]? pre=0 has bit 0 = 0; bit 0 path goes children[0] → children[0]. So root.children[0].children[1] doesn't exist. Break.
  Count = 1.
  
Wait, that gives count = 2 total, but expected is 1. Let me recheck.

For pre=3 query: count p ∈ {0, 1} where p XOR 3 < 2.
- p = 0: 3. NOT < 2.
- p = 1: 2. NOT < 2.
Count = 0.
```

Let me retrace more carefully.

`nums = [1, 2]`, k = 2 (binary 10).

```
Insert 0 (binary 00).

Process 1: pre = 0 XOR 1 = 1 (binary 01).
  countLessThan(x=1, k=2):
    bit 1 (value 2): xb = 0, kb = 1.
      kb==1: cur.ch[xb=0] is the root → 0 → ... path of 0. Has count 1. count += 1.
      Go to cur.ch[1-xb=1]. root.ch[1] doesn't exist. Break.
    count = 1.
  Insert 1.

Process 2: pre = 1 XOR 2 = 3 (binary 11).
  countLessThan(x=3, k=2):
    bit 1: xb = 1, kb = 1.
      kb==1: cur.ch[xb=1] = root.ch[1] doesn't exist. Don't add.
      Go to cur.ch[1-xb=0] = root.ch[0]. Now at "0-bit" subtree.
    bit 0: xb = 1, kb = 0.
      kb==0: cur.ch[xb=1] = node at path 0→1 (for pre=1). Exists. Move there.
    Loop ends. (No more bits beyond bit 0.)
    count = 0.
  Insert 3.

Total = 1 + 0 = 1. ✓
```

I miscounted earlier. The algorithm gives 1, matching expected.

---

## 8. Common pitfalls

1. **Forgetting the sentinel `insert(0)`.** Pre-seed `pre[0] = 0` for paths starting at index 0.

2. **Counting BEFORE inserting current prefix.** Order matters: count THEN insert, to avoid counting a value against itself.

3. **Misreading the bit logic.** The kb==1 case adds the "XOR-bit-0" branch's count THEN commits to "XOR-bit-1" branch.

4. **Forgetting subtree count.** Each node's `count` represents the WHOLE subtree's size, not just the node.

5. **Off-by-one in bit range.** For 32-bit ints, use BITS = 30 (values ≤ 10⁹ < 2³⁰).

6. **Confusing "less than" with "less than or equal".** Adjust the bit logic accordingly.

---

## 9. The shape — XOR + counting

The pattern:

> **"For counting subarrays with XOR-related properties, combine PREFIX XOR (to reframe as pair-XOR) with a BINARY TRIE augmented with SUBTREE COUNTS."**

| Problem | Counting target |
|---|---|
| **This problem** | pairs with XOR < k |
| Count Subarrays with XOR = K | hashmap (no trie needed) |
| Max XOR of Two Numbers | greedy bit walk (no count needed) |
| Count Triplets with XOR = 0 | hashmap-based prefix XOR |
| Max XOR for each query | persistent trie (offline) |

**Pattern to internalize:**

> "PREFIX XOR converts subarray problems to PAIR problems on prefixes. BINARY TRIES with subtree counts enable O(B) counting of pairs satisfying bit-level constraints."

---

## Cross-references

- **Reference card (post-mastery):** [`../Subarrays_with_XOR_Less_Than_K_Concept.md`](../Subarrays_with_XOR_Less_Than_K_Concept.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Maximum_XOR_of_Two_Numbers.md`](./Maximum_XOR_of_Two_Numbers.md), [`Implement_Trie_Prefix_Tree.md`](./Implement_Trie_Prefix_Tree.md).
  - [`../../Math/learn/Subarray_Sums_Divisible_by_K.md`](../../Math/learn/Subarray_Sums_Divisible_by_K.md) — prefix-sum cousin.
