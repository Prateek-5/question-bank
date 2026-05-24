# Distribute Candies — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Distribute_Candies.md`](../Distribute_Candies.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/distribute-candies/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: this isn't a search problem — it's a one-line math observation. Alice can eat n/2 candies. She wants distinct types. Answer = `min(n/2, distinct_count)`.**

**Map of this file (7 sections):**

1. Read the problem
2. What limits the answer?
3. The formula
4. Code
5. Trace it
6. Common pitfalls
7. The shape — quota-vs-availability min

---

## 1. Read the problem

`candyType` is an array of even length n. Each entry is a type. Alice's doctor restricts her to n/2 candies total. She wants to MAXIMIZE the number of distinct types she eats.

**Examples:**

- `[1, 1, 2, 2, 3, 3]` → n=6, budget=3. 3 distinct types available. Pick one of each → **3**.
- `[1, 1, 2, 3]` → n=4, budget=2. 3 distinct types but only budget for 2 → **2**.
- `[6, 6, 6, 6]` → n=4, budget=2. Only 1 distinct type → **1**.

---

## 2. What limits the answer?

> **Mini-refresher: two limits, take the min.**
>
> Alice picks at most n/2 candies. Distinct types she sees ≤ distinct types available. So her distinct-types-eaten ≤ MIN of:
> - **n/2** (eating budget — even with infinite variety, she can't exceed this)
> - **distinct_count** (variety budget — even with infinite eating, she can't see more than what exists)
>
> Both bounds are achievable: just pick one of each distinct type up to n/2.

---

## 3. The formula

```
distinct = len(set(candyType))
return min(n // 2, distinct)
```

That's the entire algorithm. O(n) for set construction.

---

## 4. Code

**C++:**

```cpp
int distributeCandies(vector<int>& candyType) {
    unordered_set<int> types(candyType.begin(), candyType.end());
    return min((int)types.size(), (int)candyType.size() / 2);
}
```

**Python:**

```python
def distributeCandies(candyType):
    return min(len(set(candyType)), len(candyType) // 2)
```

Complexity: **O(n)** time, **O(n)** space.

---

## 5. Trace it

- `[1, 1, 2, 2, 3, 3]`: set = {1, 2, 3} → size 3. n/2 = 3. min(3, 3) = **3**.
- `[1, 1, 2, 3]`: set = {1, 2, 3} → 3. n/2 = 2. min(3, 2) = **2**.
- `[6, 6, 6, 6]`: set = {6} → 1. n/2 = 2. min(1, 2) = **1**.

---

## 6. Common pitfalls

1. **Returning n/2 unconditionally.** Wrong when distinct < n/2.
2. **Returning distinct unconditionally.** Wrong when distinct > n/2.
3. **Sorting + manual counting.** Works but O(n log n) — wasteful when a set is O(n).
4. **Worrying about WHICH specific candies to pick.** Don't — only counts matter for distinct-type maximization.
5. **Forgetting integer division for n/2.** In C++ both operands are int → integer division. In Python use `//`, not `/`.

---

## 7. The shape — quota-vs-availability min

The pattern: **answer = min(what you can do, what's available).**

| Problem | Quota | Availability |
|---|---|---|
| **This problem** | n/2 candies | distinct types |
| Maximum Units on a Truck | truck capacity | total units across boxes |
| Diet Plan Performance | k days | length of calories array |
| Maximum Number of Coins You Can Get | n turns | floor(3n/3) pairs |

**Pattern to internalize:**

> "When the answer is bounded by TWO independent constraints, the answer is often the min. Watch for 'at most X' + 'at most Y' phrasings."

---

> **Self-check — the question to ask next time.**
>
> When the problem describes a budget plus a variety question, ask:
>
> > **"Is the answer `min(budget, available)`? Count distinct items once; compare to budget."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Distribute_Candies.md`](../Distribute_Candies.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Assign_Cookies.md`](./Assign_Cookies.md).
  - Coming next: [`Maximum_Product_of_Three_Numbers.md`](./Maximum_Product_of_Three_Numbers.md), [`Maximize_Sum_After_K_Negations.md`](./Maximize_Sum_After_K_Negations.md).
