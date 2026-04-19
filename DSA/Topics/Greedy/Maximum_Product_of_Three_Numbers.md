# Maximum Product of Three Numbers

**Problem Link:**
https://leetcode.com/problems/maximum-product-of-three-numbers/

**Topic:**
Greedy


----------------------------------------

## Step 1: Understand the Problem (Beginner Friendly)

Let's start by making sure we *really* understand what this problem is asking — no jargon, no tricks, just plain language.

If you had to explain this problem to a friend who's never heard of algorithms, how would you put it? Often, just rephrasing the question in your own words is half the battle. So let's do that first.

**In plain words:** Consider either the top 3 or the two smallest (negatives) × the largest.

Before we touch a single line of code, let's look at a small concrete example — the easiest way to build a mental model of the problem:

> nums=[-10,-10,1,3,2]. Sorted: [-10,-10,1,2,3]. top3: 1*2*3=6. neg2*max: -10*-10*3=300 → answer 300.

Take a moment to trace through that yourself, pen on paper if possible. Notice how the example already hints at the structure of the answer — almost every interview example is chosen to nudge you toward the idea. That's not cheating; that's smart problem-solving.

**Why constraints matter:** Before picking an approach, check the input size and value ranges. If `n ≤ 20`, an exponential brute force is fine. If `n ≤ 10^5`, you need something like O(n log n). If `n ≤ 10^9`, only O(1), O(log n), or a mathematical trick will do. Reading constraints first saves you from writing code that doesn't fit.


----------------------------------------

## Step 2: Break Down the Problem

Now that we've understood the surface of the problem, let's peel it back and ask: *what is this problem really about?*

Many problems wear different costumes but hide the same core skeleton. Our job as solvers is to strip the costume and recognize the skeleton. Once we do, it becomes one of a few well-known shapes.

So ask yourself:

- **What am I being asked to optimize, count, or find?** In this case, we're focused on: Consider either the top 3 or the two smallest (negatives) × the largest.
- **What information do I truly need at each step?** Often we think we need to track everything — but really, we only need a tiny slice of state to make the next decision. Identifying that slice is the key insight for efficient algorithms.
- **Can I rephrase the problem using simpler building blocks?** Most problems reduce to one of: traversal, counting, sorting, searching, or recurrence. Can you spot which one this is?

Right now, try to formulate the problem in one sentence without using the original phrasing. That single-sentence version is usually what your algorithm will solve.


----------------------------------------

## Step 3: Build Intuition (VERY IMPORTANT)

This is where we actually *think* about how to solve it — not reach for a data structure or a pattern, just think. Pretend you've never seen this before.

It's very tempting to try every combination. That's exponential. The key insight for greedy problems is that a *local* choice — the earliest end time, the smallest available item, the highest-priority task — is provably as good as any global decision. When the local choice is safe, greedy works.

So how do we get smarter? Let's build the correct intuition step by step.

Maximum product uses either three largest positives or two largest-magnitude negatives plus the biggest positive.

Notice what just happened there: we didn't pull a solution out of thin air. We identified a structural property of the problem and leaned on it. Every efficient algorithm is built on the back of a structural observation like that one. When you encounter a new problem, your first job is to find this kind of observation — not to recall a data structure.

Here's a mental checkpoint. Before continuing, make sure you can answer these:

1. Why does the naive approach waste work?
2. What specific property of the problem lets us do better?
3. How does the insight reduce the amount of work needed?

If those three questions are clear in your head, you've built real intuition. The rest is execution.


----------------------------------------

## Step 4: Connect to Concept

Now we give our insight a name. Every good intuition maps onto a well-known algorithmic concept — and recognizing that mapping is exactly what interviewers are testing.

**The concept:** Consider either the top 3 or the two smallest (negatives) × the largest.

**Why this concept fits this problem:** The intuition we built in Step 3 is exactly the kind of situation this concept is designed for. Instead of reinventing the wheel, we lean on a tested technique with known complexity and known pitfalls.

**Pattern recognition cue:**

**Whenever a problem asks for min/max and a local 'best' choice seems correct → check if Greedy applies. Always prove it with an exchange argument before trusting it.**

Bookmark this mental mapping. Interviewers rarely ask a new problem — they ask a variation of a known pattern. If you train yourself to spot the pattern quickly, you can focus your energy on the details that make this version of the problem unique.


----------------------------------------

## Step 5: Visual / Step-by-Step Explanation

Let's walk through what our approach is actually doing, step by step, in a way that builds a mental picture.

Sort. Return max(nums[n-1]*nums[n-2]*nums[n-3], nums[0]*nums[1]*nums[n-1]).

Take a moment to trace through the mental picture here. A small example visualized is worth ten paragraphs of prose. When you solve practice problems, sketching the first few steps on paper is almost always worth the time.

If at this point you feel like you could explain the approach to someone else — congratulations, you've understood it. If not, re-read Steps 3 and 5 together: they describe the same process from two angles (why it works and how it works).


----------------------------------------

## Step 6: Final Approach

Now let's crystallize everything we've learned into a clean algorithm.

Sort + compare two candidates.

That's the entire plan. Notice how it connects back to the intuition: every step of the algorithm is there because our structural observation said it needed to be. We didn't guess — we reasoned.

**Before coding, it's worth asking:**

- What's the invariant I'm maintaining across iterations?
- What corner cases could break my logic (empty input, single element, all-equal, etc.)?
- Is there any subtle off-by-one that could sneak in?

Get those clear in your head, and the code almost writes itself.


----------------------------------------

## Step 7: Dry Run (Detailed)

Let's run through a concrete example, narrating what's happening at every step. This is the single most effective way to verify your mental model before writing code.

nums=[-10,-10,1,3,2]. Sorted: [-10,-10,1,2,3]. top3: 1*2*3=6. neg2*max: -10*-10*3=300 → answer 300.

Did every transition make sense? If any step feels hand-wavy, stop and re-derive it. A dry run you can't explain is a dry run you don't really understand — and an interviewer will press on exactly the point you skipped.

Try running the same algorithm in your head on a slightly different example (maybe one with a duplicate, or an empty case). If the algorithm still works, your understanding is robust.


----------------------------------------

## Step 8: Time and Space Complexity

Complexity isn't magic — it's just counting the work.

Time: O(n log n). Space: O(1).

Let's reason through this. Every operation your algorithm performs costs something. Summing those costs across all iterations gives you the running time. The same logic applies to memory: count the data structures you allocate and how big they can grow in the worst case.

**A good habit:** when you compute complexity, don't just state the final Big-O. State *why*. "Sorting takes O(n log n) because standard comparison sort needs that many comparisons" is a better answer than "O(n log n)" alone. Interviewers love when you explain your reasoning.


----------------------------------------

## Step 9: C++ Implementation

Here's the implementation. Notice the comments — they're there to explain *why* a line exists, not *what* it does. If you understand Steps 1–8, the code should read naturally.

```cpp
#include <bits/stdc++.h>
using namespace std;
int maximumProduct(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size();
    return max(a[n-1]*a[n-2]*a[n-3], a[0]*a[1]*a[n-1]);
}
```

A few notes about the style:

- We use `<bits/stdc++.h>` for brevity; in production, prefer specific headers.
- `auto` and structured bindings (`auto [x, y] = ...`) keep the code readable without extra type noise.
- We use `INT_MAX` / `INT_MIN` for sentinel values; if your input can hit those, switch to `long long`.
- Early returns, clean variable names, and minimal nesting make this code easy to review under time pressure — which is exactly what interviewers want to see.


----------------------------------------

## Step 10: Follow-up Questions

Interviewers almost always have a follow-up ready. Thinking about these now — before you're in the hot seat — builds deeper understanding and pattern fluency.

- O(n) single pass tracking top3/bottom2.
- Product of k numbers — DP or careful greedy.
- Subarray product maximum.

For each follow-up, try to answer mentally: *which part of my current solution changes, and which part stays the same?* That mental exercise alone will sharpen your algorithmic thinking faster than solving twenty more problems without reflection.

---

*You've now worked through the full teaching arc for this problem: understand → break down → intuit → connect → visualize → formalize → dry run → analyze → implement → extend. If you can do this unassisted on a fresh problem from the same pattern, you've genuinely learned the idea — not just the answer.*
