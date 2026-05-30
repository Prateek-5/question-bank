# Subarrays with XOR Less Than K (Concept)

**Problem Link:**
<a href="https://leetcode.com/problems/subarray-xor-queries/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/subarray-xor-queries/</a>

**Topic:**
Trie / Bit Manipulation Trie

----------------------------------------

## Step 1: The Problem

Given an integer array `nums` and integer k, count the number of **subarrays** (contiguous) whose XOR is **less than** k.

Example: `nums = [1, 2, 3]`, k = 2.
- Subarrays and their XOR:
  - [1] = 1. 1 < 2 ✓.
  - [1, 2] = 3. ✗.
  - [1, 2, 3] = 0. 0 < 2 ✓.
  - [2] = 2. ✗.
  - [2, 3] = 1. ✓.
  - [3] = 3. ✗.

Count = **3**.

----------------------------------------

## Step 2: Brute Force

For each pair (i, j) with i ≤ j, compute XOR of nums[i..j] and check. Using prefix XORs, each query is O(1), so total O(n²). For n = 10⁵, that's 10¹⁰ — too slow.

We need something faster.

----------------------------------------

## Step 3: Prefix XOR Trick

Define `pre[0] = 0` and `pre[i] = nums[0] XOR nums[1] XOR ... XOR nums[i-1]`.

Then XOR of subarray nums[i..j-1] = `pre[j] XOR pre[i]`.

The problem becomes: count pairs (i, j) with i < j such that `pre[j] XOR pre[i] < k`.

Now the question is algorithmic: given n prefix-XOR values, count pairs whose mutual XOR is < k.

----------------------------------------

## Step 4: Enter the Binary Trie

Insert prefix-XOR values one at a time into a **binary trie** (each path encodes the bits of a value). For each pre[j] being processed, we want to count the already-inserted values p such that `p XOR pre[j] < k`.

The trie allows us to count these in **O(bit_width)** = O(30) per query.

Key idea: traverse the trie bit by bit (from most significant to least). At each bit, decide based on the corresponding bit of pre[j] and k:
- If k's bit is 1: any path in the trie where the XOR-with-pre[j] has bit 0 at this position yields XOR strictly less than k (regardless of lower bits). **Count those, then continue into the branch that keeps XOR's bit = 1.**
- If k's bit is 0: XOR at this bit must be 0 (else XOR >= 2 · this bit ≥ k). Continue into the branch matching pre[j]'s bit.

Each node in the trie stores a counter: how many values pass through it. This lets us "count entire subtrees" when we decide "everything on this side is valid."

----------------------------------------

## Step 5: Algorithm (Sketch)

```
trie = binary trie
answer = 0
trie.insert(0)        # prefix pre[0] = 0

pre = 0
for num in nums:
    pre ^= num
    answer += count_less_than_k(trie, pre, k)
    trie.insert(pre)
return answer

def count_less_than_k(trie, x, k):
    count = 0
    node = trie.root
    for bit from MSB to LSB:
        xb = bit of x
        kb = bit of k
        if kb == 1:
            # "XOR bit = 0" branch contributes whole subtree
            if node.child[xb] exists: count += node.child[xb].size
            # Move into "XOR bit = 1" branch (child with opposite bit of x)
            if node.child[1 - xb] exists: node = node.child[1 - xb]
            else: break
        else:  # kb == 0
            # XOR bit must be 0 → move into same-as-x child
            if node.child[xb] exists: node = node.child[xb]
            else: break
    return count
```

Insertion and each query are O(30). Total: **O(n · 30) = O(n)**.

----------------------------------------

## Step 6: Why This Works

The trie stores prefix-XOR values indexed by their bits. For each new pre[j], we want to find, among already-inserted p's, how many satisfy `p XOR pre[j] < k`.

Going bit-by-bit top-down:
- At the current bit, we've established that XOR matches k so far on higher bits. Now we decide the current bit.
- If we can make XOR's current bit strictly less than k's (possible only when k's bit is 1), then the rest of the lower bits don't matter — all of those values are valid.
- If XOR's current bit must equal k's (in the tight case), we commit and recurse to lower bits.

"Everything in a subtree" counts are available in O(1) per node if we store counters — no enumeration needed.

----------------------------------------

## Step 7: Small Trace (Conceptual)

`nums = [1, 2]`, k = 2.

pre = [0, 1, 3] (prefix XORs, binary: 00, 01, 11 in 2 bits).

Insert pre[0] = 0. Trie has one node for 00.

Process num=1, pre=1. Count in trie values p such that p XOR 1 < 2.
- p = 0: 0 XOR 1 = 1. 1 < 2 ✓. Count = 1.
Insert 1. Trie has 00 and 01.

Process num=2, pre=3. Count values p such that p XOR 3 < 2.
- p = 0: 3. Not < 2.
- p = 1: 2. Not < 2.
Count = 0.

Total = 1.

Sanity: subarrays of nums = [1, 2]:
- [1] = 1 ✓.
- [1, 2] = 3 ✗.
- [2] = 2 ✗.
Count = 1. ✓

----------------------------------------

## Step 8: Name It

**Binary trie for XOR-based counting**. A specialized but powerful structure.

Applications:
- Max XOR of two numbers in array (LeetCode 421).
- Count subarrays with XOR ≤ k.
- Max XOR queries.
- Similar patterns for "count pairs with some bit condition."

The trie generalizes hashing to support **range queries over bits**, which plain hashmaps can't do.

----------------------------------------

## Step 9: Complexity

Time: **O(n · B)** where B = bit width (≤ 32).
Space: **O(n · B)** for the trie nodes.

For n = 10⁵ and B = 30: about 3 × 10⁶ nodes — manageable.

----------------------------------------

## Step 10: C++ Implementation (Outline)

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
                // If there's a branch with XOR bit = 0, add its subtree count
                if (cur->ch[xb]) count += cur->ch[xb]->count;
                // Move into XOR bit = 1 branch
                cur = cur->ch[1 - xb];
            } else {
                // XOR bit must be 0; move into xb branch
                cur = cur->ch[xb];
            }
        }
        return count;
    }
};

int countSubarraysXorLessThanK(vector<int>& nums, int k) {
    XorTrie trie;
    trie.insert(0);
    int pre = 0, answer = 0;
    for (int num : nums) {
        pre ^= num;
        answer += trie.countLessThan(pre, k);
        trie.insert(pre);
    }
    return answer;
}
```

Each insert and query is O(30); total O(30 · n).

----------------------------------------

## Step 11: Follow-up Questions

- **Count subarrays with XOR equal to K.** Use a hashmap of prefix XOR counts (simpler; no trie needed).
- **Count subarrays with XOR ≥ K.** Same trie, mirror the logic.
- **Max XOR of any two elements in array.** Trie insert all; for each, greedily traverse to find opposite bits.
- **Generalize to sum or product.** Different structure — segment tree or Fenwick tree over values.
- **Memory too large?** Use path compression (radix trie) or persistent trie.
- **Why not sort prefix-XORs?** XOR-ordering doesn't align with value-ordering; sorting doesn't help for XOR range queries.
