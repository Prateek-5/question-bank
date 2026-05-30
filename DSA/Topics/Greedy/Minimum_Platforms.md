# Minimum Platforms

**Problem Link:**
<a href="https://www.geeksforgeeks.org/minimum-number-platforms-required-railwaybus-station/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/minimum-number-platforms-required-railwaybus-station/</a>

**Topic:**
Greedy

----------------------------------------

## Step 1: Paint the Station

You're in charge of a train station. You have two arrays: `arrival[i]` is when train `i` arrives, `departure[i]` is when it leaves. A train occupies **one platform** for the entire interval `[arrival, departure]`.

Return the **minimum number of platforms** needed so that every train can be accommodated (no two trains at the same platform simultaneously).

Example:
- arrival = `[900, 940, 950, 1100, 1500, 1800]`
- departure = `[910, 1200, 1120, 1130, 1900, 2000]`

Let's see which trains overlap at any moment.

- 900-910: only train 1 is present.
- 940-910? Wait, 910 is the earlier train's departure. At 940 train 2 arrives. Between 910 and 940, no trains. So at 940, train 2 alone.
- At 950, train 3 arrives. Now trains 2 and 3. Two platforms needed.
- At 1100, train 4 arrives. Train 2 is still there (leaves 1200), train 3 is still there (leaves 1120). So trains 2, 3, 4 present. **Three platforms.**
- At 1120, train 3 leaves. Trains 2 and 4 remain.
- At 1130, train 4 leaves. Train 2 alone.
- At 1200, train 2 leaves. No trains.
- At 1500, train 5 arrives.
- At 1800, train 6 arrives. Trains 5 and 6 present. Two.
- At 1900, train 5 leaves. Train 6 alone.
- At 2000, done.

Peak: **3**. That's the answer.

----------------------------------------

## Step 2: The Underlying Question

Stripping the train context: at any moment in time, how many intervals contain that moment? The maximum over all moments is the answer.

Approach 1: check every moment (discrete time). Count overlapping intervals at each. Slow if time range is huge.

Approach 2: for each interval, count how many others it overlaps. But that double-counts and it's O(n²).

Approach 3: **sweep line**. Process events (arrivals and departures) in time order. Track a running "trains currently present" counter. The max is the answer.

Sweep line is the clean one — O(n log n) from sorting — and it's what the hand-trace above does implicitly.

----------------------------------------

## Step 3: Making Sweep Line Precise

Create a list of events:
- For each train, an arrival event (time, +1) meaning "one more train present."
- For each train, a departure event (time, -1) meaning "one fewer."

Sort events by time. When times tie, **handle departures before arrivals** — a train that leaves at exactly 910 is gone by the time a new train arrives at 910, so they can share a platform.

Walk events in order. Maintain a counter `current`. Track `max(current)`.

Wait — do we need separate event objects, or can we cleverly use the arrival and departure arrays?

Alternative: sort arrival and departure arrays independently. Use two pointers i and j to walk them. Whichever next event is earlier (arrival vs. departure) drives the next step.

This is the classic **two-sorted-arrays merge** pattern for sweep line on interval problems.

----------------------------------------

## Step 4: Two-Pointer Sweep Step by Step

1. Sort arrivals and departures separately, both ascending.
2. Pointers i = 0 (arrivals), j = 0 (departures). Counter = 0, max = 0.
3. While i < n:
   - If `arrival[i] <= departure[j]`: a train is arriving (or exactly at same time as one leaving, but we count arrival first... wait, I need to be careful here).

Actually the question of tie-handling matters. If a train arrives exactly when another leaves, do they share a platform?

The problem usually says yes — a departure happening at time T frees the platform before a new arrival at time T. So at the tie, we should process the departure first, then the arrival.

Let me re-examine my two-pointer pseudocode:

- If `arrival[i] <= departure[j]`: we're about to add a new train. **But wait** — I want to process the departure first if they tie. So the condition should be: process arrival only if strict `arrival[i] < departure[j]`.

Actually, looking at standard interview answers, they use `arrival[i] <= departure[j]` to mean "arrival counts as arriving first" (giving the strict interpretation — the two trains conflict at that instant). This gives an *upper bound* on platforms.

If the problem allows sharing when times touch, use strict `<`.

For the given example, all times are distinct, so it doesn't matter. Let me proceed with strict `<` for the cleanest touching-allowed interpretation.

```
while i < n:
    if arrival[i] < departure[j]:
        current++
        max = max(max, current)
        i++
    else:
        current--
        j++
```

----------------------------------------

## Step 5: Trace on the Example

`arrival = [900, 940, 950, 1100, 1500, 1800]` (already sorted).
`departure = [910, 1200, 1120, 1130, 1900, 2000]` sorted: `[910, 1120, 1130, 1200, 1900, 2000]`.

```
i=0, j=0, current=0, max=0.

arrival[0]=900 < departure[0]=910? yes. current=1. max=1. i=1.
arrival[1]=940 < departure[0]=910? no (940 > 910). current=0. j=1.
arrival[1]=940 < departure[1]=1120? yes. current=1. max=1. i=2.
arrival[2]=950 < departure[1]=1120? yes. current=2. max=2. i=3.
arrival[3]=1100 < departure[1]=1120? yes. current=3. max=3. i=4.
arrival[4]=1500 < departure[1]=1120? no. current=2. j=2.
arrival[4]=1500 < departure[2]=1130? no. current=1. j=3.
arrival[4]=1500 < departure[3]=1200? no. current=0. j=4.
arrival[4]=1500 < departure[4]=1900? yes. current=1. max=3. i=5.
arrival[5]=1800 < departure[4]=1900? yes. current=2. max=3. i=6.

Loop exits (i == n).
```

Max = **3**. ✓ Matches the hand-analysis.

Cool thing about the trace: `max` is updated at each arrival (current's peak is always right after an arrival, never after a departure). So we could save the update to only arrival steps. Small optimization.

----------------------------------------

## Step 6: Why Sweep Line Is the Right Mental Model

Physically, the "number of trains present" is a step function over time: +1 at each arrival, -1 at each departure. The maximum of this step function is the answer. Any algorithm that computes this step function accurately — including our two-pointer merge over sorted arrival/departure arrays — solves the problem.

The sweep doesn't care about pairs of intervals overlapping in any specific way. It just tracks the running count. That's why it handles arbitrary overlap configurations with one pass.

----------------------------------------

## Step 7: Name the Technique

This is the **sweep-line algorithm**, specifically applied to interval overlap counting (sometimes called "interval partitioning"). The core pattern — sort events, walk them in order, maintain a running invariant — generalizes to many problems:
- Max concurrent meetings (same problem).
- Minimum rooms to schedule classes.
- Max overlap of satellite broadcast windows.
- Any "peak concurrency" question.

----------------------------------------

## Step 8: Complexity

Time: sorting both arrays. **O(n log n)**.
Space: **O(1)** beyond the sort (in-place) or **O(n)** (with separate event arrays).

----------------------------------------

## Step 9: C++ Implementation

```cpp
int findPlatform(vector<int>& arrival, vector<int>& departure) {
    int n = arrival.size();
    sort(arrival.begin(), arrival.end());
    sort(departure.begin(), departure.end());

    int i = 0, j = 0;
    int current = 0, peak = 0;
    while (i < n) {
        if (arrival[i] < departure[j]) {
            current++;
            peak = max(peak, current);
            i++;
        } else {
            current--;
            j++;
        }
    }
    return peak;
}
```

The loop exits when we've processed all arrivals. Remaining departures can't increase `current` (they only decrement), so we don't need to process them.

If the problem considers touching (arrival == departure) as overlap, change `<` to `<=`.

----------------------------------------

## Step 10: Follow-up Questions

- **Return the schedule (which train goes to which platform).** Maintain a min-heap of "platform next-free time"; for each arrival, pop the platform that's ready earliest (if ≤ this arrival), else allocate a new one.
- **Trains have different priority — minimize some cost.** Greedy might fail; use DP or min-cost matching.
- **Streaming version — trains arrive and depart in real time.** Use a min-heap of "next-free time" plus a counter for current occupancy.
- **Trains can be diverted to another station if no platform is free.** Now it's a rejection problem.
- **Trains have variable platform requirements (some need a "long platform," some need a "short").** Multi-dimensional matching — harder.
- **Can we avoid sorting departure separately — is the order guaranteed?** No — arrival and departure sort orders can differ; sort both.
