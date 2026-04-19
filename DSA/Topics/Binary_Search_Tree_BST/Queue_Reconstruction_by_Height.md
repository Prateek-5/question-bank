# Queue Reconstruction by Height

**Problem Link:**
https://leetcode.com/problems/queue-reconstruction-by-height/

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Understand the Input

You have a list of people. Each person is described by `[h, k]`:
- `h`: their height.
- `k`: number of people in front of them in the queue who are **at least as tall**.

The queue has been shuffled. Reconstruct it.

Example: `people = [[7,0], [4,4], [7,1], [5,0], [6,1], [5,2]]`.

- [7, 0]: 7ft tall, 0 people ≥ 7 in front.
- [7, 1]: 7ft tall, 1 person ≥ 7 in front.
- [6, 1]: 6ft tall, 1 person ≥ 6 in front.
- [5, 0]: 5ft tall, 0 people ≥ 5 in front.
- [5, 2]: 5ft tall, 2 people ≥ 5 in front.
- [4, 4]: 4ft tall, 4 people ≥ 4 in front.

The unique queue satisfying everyone's k is:
```
[[5,0], [7,0], [5,2], [6,1], [4,4], [7,1]]
```

Verify [7, 0]: 0 people before [5, 0]... before [7, 0] is [5, 0] who is 5 < 7. So 0 people ≥ 7. ✓
Verify [4, 4]: before are [5, 0], [7, 0], [5, 2], [6, 1] — all ≥ 4. That's 4. ✓

----------------------------------------

## Step 2: Why It's Not Immediately Obvious

At first glance you might think to sort by height. But sorting alone doesn't tell you where to place each person — you need to figure out their exact index based on k.

The hard part: a person's k depends on **who else is in front of them** at the final position. If we place people in the wrong order, we can't compute k correctly.

We need an ordering that lets us place people one at a time without later placements messing with earlier k values.

----------------------------------------

## Step 3: Key Insight — Process Tallest First

Here's the trick. Imagine we're placing people into an empty queue one at a time. Order the processing so that **when we place a person, all people in front of them have already been placed**.

The person [4, 4] is 4ft with 4 taller people in front. So we'd want to place [4, 4] **after** those 4 taller people. Let's process taller people first.

Sort by height descending (and by k ascending within the same height, for a reason I'll explain). Then insert each into the answer list at the exact position `k`.

Why does this work?
- When we process someone at height h, every already-placed person has height ≥ h (we sorted descending). They count toward this person's k if they're in front.
- We place this person at index k in the current answer list. Their k taller predecessors are exactly the k people at positions 0 to k-1.
- Future inserts? They'll be shorter than this person (or equal). They **don't** count toward this person's k.

Wait — future inserts at a position ≤ k would push this person's final index to k+1 or later, making their k stale. Let me re-think.

Future person at height ≤ h, inserted at some index `j`. If `j ≤ current_position_of_this_person`, the person we placed earlier moves one step back. But we inserted them **at index k**; does that change after?

Actually yes — if we insert someone at index j ≤ k later, our person's position shifts to k+1. But wait — that later person is shorter, so they **don't** count toward this person's k anyway. The "front" entries that are ≥ h are still the original k entries (now at positions 0 to k-1 shifted by whatever). But there might be NEW people at positions 0 to k-1!

Hmm, let me reconsider.

After inserting someone at position j ≤ k, our person is now at position k+1. People in front of them are now at 0 to k. Of those k+1 people, only the k taller originals count toward the k condition. One new shorter person got in front but doesn't count. Wait, the k condition says "k people ≥ h in front." Still k. So k is preserved. ✓

So inserting shorter people in front of a taller person **doesn't change their k**. That's the key.

This is why "tallest first" works: we establish the skeleton of tall people in the right order, and shorter people slip in later without affecting established k's.

----------------------------------------

## Step 4: Why Sort by k Ascending Within Same Height?

When two people have the same height, they still have potentially different k's. Within a group of equal heights, we should insert the lower-k ones first.

Why? Because a higher-k person gets placed further back. If we place a higher-k same-height person first, the lower-k one inserted later might push the higher-k one's "k" count off (since equal-height counts too).

Sorting by k ascending within equal heights ensures when we insert [7, 0] first, then [7, 1], both land correctly at their respective k positions.

Putting it together: **sort by height descending, k ascending.** Then insert each at index k.

----------------------------------------

## Step 5: Trace on the Example

`people = [[7,0], [4,4], [7,1], [5,0], [6,1], [5,2]]`.

Sort by (height desc, k asc):
```
(7, 0), (7, 1), (6, 1), (5, 0), (5, 2), (4, 4)
```

Insert into an empty list, each at index k:

```
Insert (7, 0) at index 0: [[7,0]].
Insert (7, 1) at index 1: [[7,0], [7,1]].
Insert (6, 1) at index 1: [[7,0], [6,1], [7,1]].
Insert (5, 0) at index 0: [[5,0], [7,0], [6,1], [7,1]].
Insert (5, 2) at index 2: [[5,0], [7,0], [5,2], [6,1], [7,1]].
Insert (4, 4) at index 4: [[5,0], [7,0], [5,2], [6,1], [4,4], [7,1]].
```

Final: `[[5,0], [7,0], [5,2], [6,1], [4,4], [7,1]]`. ✓ Matches expected.

Notice at each step, the newly-inserted person has k taller (or equal-height earlier-placed) people in front, exactly as required.

----------------------------------------

## Step 6: Why This Algorithm Is Clever

The insight is an example of **commutative insertion**: later inserts of shorter people preserve earlier taller people's "in front" counts. This commutativity lets us place people in a principled order (tallest first), which in turn lets us use simple index-insertion.

If we tried to place shortest first, we'd have no way to know where they go — their k depends on taller people who aren't placed yet. The ordering "taller first" breaks this circular dependency.

----------------------------------------

## Step 7: Name It

This is a **greedy reconstruction** problem. It's listed under BST, but the canonical solution is sort + insert — no tree data structure required. A balanced BST with order-statistic augmentation would let us do O(log n) inserts, giving O(n log n) total, but ordinary list insertion is O(n) per insert, total O(n²), which is fine for typical constraints.

The technique generalizes to problems where:
- Each item has a constraint involving "other items of type X."
- Processing items in an order that makes the constraint locally satisfiable works.

----------------------------------------

## Step 8: Complexity

Time: sort O(n log n) + n inserts, each O(n) into a dynamic array = **O(n²)**.

For a faster version, use a balanced BST or Fenwick tree with order-statistic queries, giving **O(n log n)**.

Space: O(n) for the output list.

----------------------------------------

## Step 9: C++ Implementation

```cpp
vector<vector<int>> reconstructQueue(vector<vector<int>>& people) {
    sort(people.begin(), people.end(), [](const vector<int>& a, const vector<int>& b) {
        if (a[0] != b[0]) return a[0] > b[0];   // height descending
        return a[1] < b[1];                      // k ascending within same height
    });

    vector<vector<int>> result;
    for (auto& p : people) {
        result.insert(result.begin() + p[1], p);
    }
    return result;
}
```

Elegant. Two-line sort, four-line loop. The sort encodes the ordering insight; the insert at index k directly realizes the placement rule.

----------------------------------------

## Step 10: Follow-up Questions

- **"k shorter people in front" instead of "k ≥ tall in front."** Flip sorting order.
- **k based on weight or some other attribute.** Generalize accordingly.
- **Very large n.** Use a Fenwick tree with order statistics — O(n log n).
- **Return any valid queue (if there are multiple).** Usually the answer is unique given the constraints, but ties in height with different k can yield multiple.
- **Adversarial input: what if no valid queue exists?** Detect by checking if any insertion would require an invalid index.
- **Why is BST helpful here?** For the O(n log n) version: balanced BSTs support order-statistics queries in O(log n) — "give me the k-th empty slot."
