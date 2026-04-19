"""Teaching-first rewriter. Transforms each question into a 10-step mentor-tone lesson."""
import os
import sys
import openpyxl

sys.path.insert(0, os.path.dirname(__file__))
from utils import ROOT, clean_topic, clean_title, write

from data_heap import DATA as D_HEAP
from data_math import DATA as D_MATH
from data_graph import DATA as D_GRAPH
from data_bst import DATA as D_BST
from data_trees import DATA as D_TREES
from data_greedy import DATA as D_GREEDY
from data_arrays1d2d import DATA as D_ARR12
from data_segtree import DATA as D_SEG
from data_arraysmat import DATA as D_ARRM
from data_search import DATA as D_SEARCH
from data_twoptr import DATA as D_TWO
from data_linkedlist import DATA as D_LL
from data_numthy import DATA as D_NUM
from data_trie import DATA as D_TRIE
from data_dp import DATA as D_DP
from data_bit import DATA as D_BIT
from data_hashing import DATA as D_HASH
from data_queues import DATA as D_QUE
from data_stack import DATA as D_STACK
from data_recursion import DATA as D_REC
from data_backtrack import DATA as D_BACK
from data_sort import DATA as D_SORT

ALL = {}
for d in [D_HEAP, D_MATH, D_GRAPH, D_BST, D_TREES, D_GREEDY, D_ARR12, D_SEG, D_ARRM, D_SEARCH,
          D_TWO, D_LL, D_NUM, D_TRIE, D_DP, D_BIT, D_HASH, D_QUE, D_STACK, D_REC, D_BACK, D_SORT]:
    ALL.update(d)

RESOLVER = {
    ("🔍 Two Pointers", "Trapping Rain Water"): "Trapping Rain Water (TP)",
    ("🔄 Sorting / Divide & Conquer", "Kth Largest Element in an Array"): "Kth Largest Element in an Array (DC)",
    ("🧠 Dynamic Programming (DP)", "Numbers At Most N Given Digit Set"): "Numbers At Most N Given Digit Set (dup)",
    "Construct Binary Tree from Inorder & Postorder": "Construct Binary Tree from Inorder and Postorder",
    "Range Sum Query 2D \u2013 Immutable": "Range Sum Query 2D Immutable",
    "Range Sum Query \u2013 Immutable": "Range Sum Query Immutable",
    "Range Sum Query \u2013 Mutable": "Range Sum Query Mutable",
    "Two Sum II \u2013 Input Array Is Sorted": "Two Sum II Input Array Is Sorted",
}

DUPLICATES_BY_ID = {
    44: "Number of Operations to Make Network Connected (dup)",
    93: "Flipping Sign Problem (Lazy Propagation Segment Tree)",
    155: "Count Substrings That Differ by One Character",
    182: "Unique Binary Search Trees",
}

# ---------- Topic-specific teaching wrappers ----------

TOPIC_NAIVE = {
    "Heap_Priority_Queue": "Your first instinct is probably to sort the whole array and pick from one end. That works — but it asks for more than we need. We don't care about every element's exact position, only the smallest or the largest at each step. Sorting does O(n log n) work just to reveal one extremum at a time. A heap does the same job with far less overhead per query.",
    "Math": "When you see an arithmetic puzzle, there's a temptation to simulate it step by step. That's honest, and often correct — but it's worth asking first: is there a closed-form shortcut? Mathematical invariants and modular arithmetic frequently collapse a loop into an O(1) formula.",
    "Graph_BFS_DFS_Dijkstra_DSU": "A tempting first thought is to try every possible path from the start to the goal. The problem is that graphs have exponentially many paths. We need a traversal that visits each node at most a few times — that's exactly what BFS, DFS, and their weighted cousins give us.",
    "Binary_Search_Tree_BST": "Many people's first instinct on a tree problem is to flatten it into an array and then work there. Sometimes that works — but it throws away the structural property of BSTs that makes them special: left < node < right. The right solutions exploit that property directly.",
    "Trees_Binary_Trees": "A natural first instinct is to traverse the tree many times — once per query, once per property. That works, but it usually does too much. A single recursive traversal can often compute everything post-order with the child results combined at each node.",
    "Greedy": "It's very tempting to try every combination. That's exponential. The key insight for greedy problems is that a *local* choice — the earliest end time, the smallest available item, the highest-priority task — is provably as good as any global decision. When the local choice is safe, greedy works.",
    "1_D_and_2_D_Arrays": "Your first instinct might be to loop over every possible subarray or sub-rectangle. That's cubic or worse. Often a prefix-sum precomputation, a clever index mapping, or a running-state scan collapses the work to linear time.",
    "Segment_Tree_Range_Queries": "A naive approach is to recompute the query from scratch every time — O(n) per query. When updates and queries mix, that becomes O(nq), which is often too slow. Segment trees and BITs compute both in O(log n) by precomputing partial results over carefully-chosen ranges.",
    "Arrays_and_Matrices": "Your first instinct is often a straightforward double loop over rows and columns. That's O(n·m), which is sometimes fine. When it isn't, look for contribution counting — asking 'for each element, how many sub-ranges include it?' — or look for patterns along diagonals, spirals, or boundaries.",
    "Searching_Binary_Search": "A linear scan is the default. When the data is sorted *or* some predicate is monotonic over the search space, that linear scan becomes a logarithmic one. The core question to ask: 'If the answer is X, is the answer also valid for X+1?' If yes, binary search on the answer is on the table.",
    "Two_Pointers": "Double loops are your first thought — and for unsorted data, often unavoidable. But when the array is sorted or the problem has a monotonic structure, two pointers sliding toward each other or in the same direction collapse the work to linear.",
    "Linked_List": "Because linked lists don't give random access, the temptation is to copy them into arrays and work there. Sometimes that's fine; often it wastes memory. The classic trick is to use two pointers moving at different speeds or with different gaps — it lets you solve many problems in a single pass.",
    "Number_Theory_Misc": "A brute-force factor check or a digit-by-digit loop is usually the first attempt. Cleverer approaches exploit modular arithmetic, parity, or digit-DP recurrences to get O(1) or O(log n) from what looks like an O(n) problem.",
    "Trie_Bit_Manipulation_Trie": "You might try hashing every word or running regex matches. For prefix queries that's overkill — tries share prefixes so matching a new query touches only relevant nodes. For XOR problems, a binary trie lets you greedily chase the opposite bit at each level.",
    "Dynamic_Programming_DP": "Your very first thought is often recursion. That's actually the right start — but naive recursion re-computes the same subproblems exponentially. The fix is memoization (top-down) or tabulation (bottom-up). The hard part is identifying the state that captures all we need to know about the past.",
    "Bit_Manipulation": "An ordinary arithmetic or counting approach can work, but bit-level manipulation often gives constant-time elegance. Watch for parity, XOR cancellation, and bitmask enumeration.",
    "Hashing_Sliding_Window": "The default is to enumerate every subarray or substring. That's O(n²). Two techniques collapse this: prefix-sum + hashmap for counting subarrays with a property, or a sliding window whose left and right pointers advance monotonically.",
    "Queues_Deque_Monotonic_Queue": "A nested loop over each window is the obvious approach. But each element enters and leaves the window exactly once, so a deque that maintains only 'useful' candidates gives us the answer in amortized O(1) per position.",
    "Stack": "You might try to scan multiple times, or use recursion to handle nested structure. A stack lets you remember just enough of the past to resolve it efficiently — especially 'next greater' or 'matching brackets' questions.",
    "Recursion": "Recursion is the natural language of branching problems. Your first recursive attempt is often *almost* right — the adjustments needed are usually (a) a correct base case and (b) careful state-undo when backtracking.",
    "Backtracking": "Brute-force enumeration is the starting point. The real engineering is pruning — cutting branches as soon as they can't lead to a valid answer. Good pruning can turn an exponential search into something that finishes in milliseconds.",
    "Sorting_Divide_and_Conquer": "Sorting first is often the most useful preprocessing step in algorithms. Divide-and-conquer generalizes that idea: split the problem in halves, solve each recursively, and merge. The merge step is where insights like inversion counting live.",
}

TOPIC_PATTERN_HINT = {
    "Heap_Priority_Queue": "**Whenever you see 'k-th', 'top-k', or 'merge sorted streams' → think Heap.**",
    "Math": "**Whenever you see digits, divisibility, primes, or modular structure → think Math/Number Theory.**",
    "Graph_BFS_DFS_Dijkstra_DSU": "**Whenever nodes have relationships or connectivity matters → think Graph. 'Shortest path' without weights → BFS. With weights → Dijkstra. Just connectivity → DSU.**",
    "Binary_Search_Tree_BST": "**Whenever you need ordered operations (k-th smallest, range queries, predecessor/successor) → think BST.**",
    "Trees_Binary_Trees": "**Whenever data is hierarchical or you can compute something per-subtree → think Binary Tree DFS.**",
    "Greedy": "**Whenever a problem asks for min/max and a local 'best' choice seems correct → check if Greedy applies. Always prove it with an exchange argument before trusting it.**",
    "1_D_and_2_D_Arrays": "**Whenever you need range sums or running aggregates → think Prefix Sum. Whenever you need fixed-size windows → Sliding Window.**",
    "Segment_Tree_Range_Queries": "**Whenever you have both updates *and* range queries on the same array → think Segment Tree or BIT.**",
    "Arrays_and_Matrices": "**Whenever the problem is about rows, columns, diagonals, or all sub-rectangles → think contribution counting or per-row/col precomputation.**",
    "Searching_Binary_Search": "**Whenever the input is sorted or the answer space is monotonic → think Binary Search.**",
    "Two_Pointers": "**Whenever the array is sorted or the constraint is monotonic in a sliding sense → think Two Pointers.**",
    "Linked_List": "**Whenever you need to find cycles, middles, or the k-th-from-end → think slow/fast pointers.**",
    "Number_Theory_Misc": "**Whenever digits, GCD, primes, or modular properties appear → check for closed-form solutions before coding loops.**",
    "Trie_Bit_Manipulation_Trie": "**Whenever you see prefix queries, dictionary lookups, or max-XOR → think Trie.**",
    "Dynamic_Programming_DP": "**Whenever a brute-force recursion has overlapping subproblems → think DP. Identify state first, then transition.**",
    "Bit_Manipulation": "**Whenever you see XOR, powers of two, subsets of ≤ 20 items → think Bitmask / Bit Tricks.**",
    "Hashing_Sliding_Window": "**'Subarray sum equals k' or 'count of something in windows' → think Prefix Sum + HashMap or Sliding Window.**",
    "Queues_Deque_Monotonic_Queue": "**Whenever you need sliding window max/min in O(n) → think Monotonic Deque.**",
    "Stack": "**Whenever you see nested structure, matching brackets, or 'next greater element' → think Stack / Monotonic Stack.**",
    "Recursion": "**Whenever a problem decomposes into similar sub-problems → think Recursion. Add memo if subproblems repeat.**",
    "Backtracking": "**Whenever you need to generate all permutations, combinations, or configurations → think Backtracking with pruning.**",
    "Sorting_Divide_and_Conquer": "**Whenever the problem smells like 'count inversions' or 'k-th statistic' → think Merge Sort variants or Quickselect.**",
}


def resolve_key(row_id, topic, title):
    if row_id in DUPLICATES_BY_ID:
        return DUPLICATES_BY_ID[row_id]
    if (topic, title) in RESOLVER:
        return RESOLVER[(topic, title)]
    if title in RESOLVER:
        return RESOLVER[title]
    if title in ALL:
        return title
    return None


SEP = "\n\n----------------------------------------\n\n"


def build_question(title, link, topic_display, topic_folder, q):
    naive = TOPIC_NAIVE.get(topic_folder, "Your first instinct might be to try every possibility by brute force. That's a useful mental starting point — it clarifies what we actually need, even if it's too slow to keep.")
    pattern = TOPIC_PATTERN_HINT.get(topic_folder, "**Whenever you see this pattern → think about the underlying structure and what's constant.**")

    md = f"""# {title}

**Problem Link:**
{link}

**Topic:**
{topic_display}
{SEP}## Step 1: Understand the Problem (Beginner Friendly)

Let's start by making sure we *really* understand what this problem is asking — no jargon, no tricks, just plain language.

If you had to explain this problem to a friend who's never heard of algorithms, how would you put it? Often, just rephrasing the question in your own words is half the battle. So let's do that first.

**In plain words:** {q['concept']}

Before we touch a single line of code, let's look at a small concrete example — the easiest way to build a mental model of the problem:

> {q['dry_run']}

Take a moment to trace through that yourself, pen on paper if possible. Notice how the example already hints at the structure of the answer — almost every interview example is chosen to nudge you toward the idea. That's not cheating; that's smart problem-solving.

**Why constraints matter:** Before picking an approach, check the input size and value ranges. If `n ≤ 20`, an exponential brute force is fine. If `n ≤ 10^5`, you need something like O(n log n). If `n ≤ 10^9`, only O(1), O(log n), or a mathematical trick will do. Reading constraints first saves you from writing code that doesn't fit.
{SEP}## Step 2: Break Down the Problem

Now that we've understood the surface of the problem, let's peel it back and ask: *what is this problem really about?*

Many problems wear different costumes but hide the same core skeleton. Our job as solvers is to strip the costume and recognize the skeleton. Once we do, it becomes one of a few well-known shapes.

So ask yourself:

- **What am I being asked to optimize, count, or find?** In this case, we're focused on: {q['concept']}
- **What information do I truly need at each step?** Often we think we need to track everything — but really, we only need a tiny slice of state to make the next decision. Identifying that slice is the key insight for efficient algorithms.
- **Can I rephrase the problem using simpler building blocks?** Most problems reduce to one of: traversal, counting, sorting, searching, or recurrence. Can you spot which one this is?

Right now, try to formulate the problem in one sentence without using the original phrasing. That single-sentence version is usually what your algorithm will solve.
{SEP}## Step 3: Build Intuition (VERY IMPORTANT)

This is where we actually *think* about how to solve it — not reach for a data structure or a pattern, just think. Pretend you've never seen this before.

{naive}

So how do we get smarter? Let's build the correct intuition step by step.

{q['intuition']}

Notice what just happened there: we didn't pull a solution out of thin air. We identified a structural property of the problem and leaned on it. Every efficient algorithm is built on the back of a structural observation like that one. When you encounter a new problem, your first job is to find this kind of observation — not to recall a data structure.

Here's a mental checkpoint. Before continuing, make sure you can answer these:

1. Why does the naive approach waste work?
2. What specific property of the problem lets us do better?
3. How does the insight reduce the amount of work needed?

If those three questions are clear in your head, you've built real intuition. The rest is execution.
{SEP}## Step 4: Connect to Concept

Now we give our insight a name. Every good intuition maps onto a well-known algorithmic concept — and recognizing that mapping is exactly what interviewers are testing.

**The concept:** {q['concept']}

**Why this concept fits this problem:** The intuition we built in Step 3 is exactly the kind of situation this concept is designed for. Instead of reinventing the wheel, we lean on a tested technique with known complexity and known pitfalls.

**Pattern recognition cue:**

{pattern}

Bookmark this mental mapping. Interviewers rarely ask a new problem — they ask a variation of a known pattern. If you train yourself to spot the pattern quickly, you can focus your energy on the details that make this version of the problem unique.
{SEP}## Step 5: Visual / Step-by-Step Explanation

Let's walk through what our approach is actually doing, step by step, in a way that builds a mental picture.

{q['explanation']}

Take a moment to trace through the mental picture here. A small example visualized is worth ten paragraphs of prose. When you solve practice problems, sketching the first few steps on paper is almost always worth the time.

If at this point you feel like you could explain the approach to someone else — congratulations, you've understood it. If not, re-read Steps 3 and 5 together: they describe the same process from two angles (why it works and how it works).
{SEP}## Step 6: Final Approach

Now let's crystallize everything we've learned into a clean algorithm.

{q['approach']}

That's the entire plan. Notice how it connects back to the intuition: every step of the algorithm is there because our structural observation said it needed to be. We didn't guess — we reasoned.

**Before coding, it's worth asking:**

- What's the invariant I'm maintaining across iterations?
- What corner cases could break my logic (empty input, single element, all-equal, etc.)?
- Is there any subtle off-by-one that could sneak in?

Get those clear in your head, and the code almost writes itself.
{SEP}## Step 7: Dry Run (Detailed)

Let's run through a concrete example, narrating what's happening at every step. This is the single most effective way to verify your mental model before writing code.

{q['dry_run']}

Did every transition make sense? If any step feels hand-wavy, stop and re-derive it. A dry run you can't explain is a dry run you don't really understand — and an interviewer will press on exactly the point you skipped.

Try running the same algorithm in your head on a slightly different example (maybe one with a duplicate, or an empty case). If the algorithm still works, your understanding is robust.
{SEP}## Step 8: Time and Space Complexity

Complexity isn't magic — it's just counting the work.

{q['complexity']}

Let's reason through this. Every operation your algorithm performs costs something. Summing those costs across all iterations gives you the running time. The same logic applies to memory: count the data structures you allocate and how big they can grow in the worst case.

**A good habit:** when you compute complexity, don't just state the final Big-O. State *why*. "Sorting takes O(n log n) because standard comparison sort needs that many comparisons" is a better answer than "O(n log n)" alone. Interviewers love when you explain your reasoning.
{SEP}## Step 9: C++ Implementation

Here's the implementation. Notice the comments — they're there to explain *why* a line exists, not *what* it does. If you understand Steps 1–8, the code should read naturally.

```cpp
{q['code']}
```

A few notes about the style:

- We use `<bits/stdc++.h>` for brevity; in production, prefer specific headers.
- `auto` and structured bindings (`auto [x, y] = ...`) keep the code readable without extra type noise.
- We use `INT_MAX` / `INT_MIN` for sentinel values; if your input can hit those, switch to `long long`.
- Early returns, clean variable names, and minimal nesting make this code easy to review under time pressure — which is exactly what interviewers want to see.
{SEP}## Step 10: Follow-up Questions

Interviewers almost always have a follow-up ready. Thinking about these now — before you're in the hot seat — builds deeper understanding and pattern fluency.

{q['followups']}

For each follow-up, try to answer mentally: *which part of my current solution changes, and which part stays the same?* That mental exercise alone will sharpen your algorithmic thinking faster than solving twenty more problems without reflection.

---

*You've now worked through the full teaching arc for this problem: understand → break down → intuit → connect → visualize → formalize → dry run → analyze → implement → extend. If you can do this unassisted on a fresh problem from the same pattern, you've genuinely learned the idea — not just the answer.*
"""
    return md


def main():
    wb = openpyxl.load_workbook(os.path.join(os.path.dirname(ROOT), "DSA_Questions.xlsx"))
    ws = wb["Sheet1"]

    count = 0
    missing = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[1] is None:
            continue
        row_id = int(row[0])
        topic_raw = row[1]
        title = row[2]
        link = row[3] or ""
        topic_folder = clean_topic(topic_raw)
        topic_display = topic_folder.replace("_", " ")

        key = resolve_key(row_id, topic_raw, title)
        if key is None or key not in ALL:
            missing += 1
            continue

        q = ALL[key]
        dest = os.path.join(ROOT, "Topics", topic_folder, clean_title(title) + ".md")
        md = build_question(title, link, topic_display, topic_folder, q)
        write(dest, md)
        count += 1

    print(f"Rewrote {count} question files. Missing {missing}.")


if __name__ == "__main__":
    main()
