# Richest Customer Wealth

**Problem Link:**
<a href="https://leetcode.com/problems/richest-customer-wealth/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/richest-customer-wealth/</a>

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: What's Asked

You have an m × n matrix `accounts` where `accounts[i][j]` is the money in customer i's j-th bank account.

A customer's **wealth** is the sum of money across their accounts. Return the wealth of the **richest** customer.

Example: `accounts = [[1, 2, 3], [3, 2, 1]]`.
- Customer 0: 1 + 2 + 3 = 6.
- Customer 1: 3 + 2 + 1 = 6.

Max: 6.

Example: `accounts = [[1, 5], [7, 3], [3, 5]]`.
- Customer 0: 6. Customer 1: 10. Customer 2: 8.

Max: 10.

----------------------------------------

## Step 2: Direct Approach

For each row (customer), sum the values. Track the max.

```
max_wealth = 0
for each row in accounts:
    wealth = sum(row)
    max_wealth = max(max_wealth, wealth)
return max_wealth
```

O(m · n). Absolutely nothing clever.

----------------------------------------

## Step 3: Trace

accounts = [[1, 5], [7, 3], [3, 5]].

```
max_wealth = 0.

Row [1, 5]: wealth = 6. max = 6.
Row [7, 3]: wealth = 10. max = 10.
Row [3, 5]: wealth = 8. max = 10.
```

Return 10. ✓

----------------------------------------

## Step 4: Name It

This is the most basic matrix processing: **row-wise aggregation with a running max**. Not algorithmically interesting, but it exercises:
- 2D array iteration.
- Accumulation within rows.
- Running max.

----------------------------------------

## Step 5: Complexity

Time: **O(m · n)** — touch each cell once.
Space: **O(1)** extra.

----------------------------------------

## Step 6: C++ Implementation

```cpp
int maximumWealth(vector<vector<int>>& accounts) {
    int maxWealth = 0;
    for (const auto& row : accounts) {
        int wealth = accumulate(row.begin(), row.end(), 0);
        maxWealth = max(maxWealth, wealth);
    }
    return maxWealth;
}
```

Five lines. `std::accumulate` sums a range; `std::max` for the running max.

Hand-rolled version:

```cpp
int maximumWealth(vector<vector<int>>& accounts) {
    int maxWealth = 0;
    for (const auto& row : accounts) {
        int wealth = 0;
        for (int x : row) wealth += x;
        if (wealth > maxWealth) maxWealth = wealth;
    }
    return maxWealth;
}
```

Either works. Use whichever you find clearer.

----------------------------------------

## Step 7: Follow-up Questions

- **Return the index of the richest customer.** Track the argmax during the scan.
- **Second richest customer.** Track top-2 during iteration.
- **Top-k richest customers.** Use a heap of size k, or sort customers by wealth.
- **Customer with most accounts.** Count non-zero entries per row and take max.
- **Average wealth across customers.** Sum all cells, divide by m.
- **Wealth distribution / percentiles.** Compute all wealths, then statistics.
