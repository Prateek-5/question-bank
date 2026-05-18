# Clock skew and Spanner's TrueTime: ordering with confidence intervals

## Source / Origin
- Lamport (1978) showed wall clocks aren't sufficient for ordering.
- Google Spanner paper (2012): TrueTime API.
- Production: Spanner, CockroachDB HLC, Yugabyte HLC.
- Concept reference: `backend-data-prep/distributed-systems/time.md`.

## Why this question matters in interviews
"Why can't you use NTP timestamps for ordering events across nodes?" is the prototypical distributed-time question. If you can explain skew, drift, the impossibility of perfect synchronisation, and how Spanner uses TrueTime's uncertainty interval to deliver external consistency, you signal you understand why time is hard.

## Concepts involved

### Syntax / mechanism to lock in

```
Clock skew = instantaneous difference between two clocks.
Clock drift = rate of change of skew (ppm).

NTP: 1-100 ms skew on the public internet; <1 ms on LAN.
PTP (IEEE 1588): sub-microsecond on LAN with hardware support.
TrueTime: GPS + atomic clocks; bounded uncertainty ε = ~7 ms.

TrueTime API:
  TT.now() → returns [earliest, latest] interval.
  TT.after(t) → true if t is definitely past.
  TT.before(t) → true if t is definitely future.

Spanner commit-wait:
  At commit time s, leader picks s = TT.now().latest.
  Then waits until TT.now().earliest > s before releasing locks.
  Guarantees: any later transaction sees s in its real-time past.

HLC (hybrid logical clock):
  ts = max(wall_clock, last_received_ts) + ε for monotonicity.
  Bounds skew at logical level; CockroachDB, YugabyteDB use HLC.
```

### Edge cases / interview traps

1. **NTP can jump backwards** if the local clock drifts too far; use monotonic clocks for durations, wall clocks only for timestamps.
2. **Clock skew breaks LWW** — writer with skewed-future clock wins forever.
3. **Spanner's TrueTime requires GPS + atomic** in each DC; expensive infrastructure.
4. **CockroachDB's max_offset** parameter (default 500ms) is the bound; exceed it → node panics.
5. **TAI vs UTC vs POSIX time.** Leap seconds in UTC complicate ordering.
6. **VM clocks drift more** than bare-metal; cloud distributed systems must tolerate larger ε.
7. **External consistency** ≠ linearizability without TrueTime — Spanner achieves it via commit-wait.

## Mental Model

Wall clocks are bureaucrats: each one runs its own pace, occasionally syncs with a central authority, but never agrees exactly. TrueTime is a bureaucrat who admits the uncertainty: "the current time is somewhere between 12:00:00 and 12:00:07." Spanner waits out the uncertainty before declaring commits final.

```
TrueTime interval at three nodes:

Node A:  [────────|────────]    earliest=10.000  latest=10.014  ε=7ms
Node B:  [────|────]            earliest=10.005  latest=10.011  ε=3ms
Node C:  [─────────|────]       earliest=9.998   latest=10.012  ε=7ms

If A says "commit at TT.now().latest = 10.014", A waits until
TT.now().earliest > 10.014 before releasing locks (commit-wait).
At that point, every node's "earliest" is past 10.014, so any
transaction starting now will see A's commit as in its past.

Commit-wait pays ε of latency per transaction to guarantee external consistency.
```

## Why interviewers care
- Tests understanding of fundamental distributed-systems limitations.
- Reveals knowledge of Spanner, CockroachDB, HLC.
- Bridges to causality (vector clocks) and LWW pitfalls.

## Common beginner confusion
- "NTP gives synchronised clocks." It gives bounded skew, not synchronisation.
- "Use UTC timestamps for LWW." Skew across nodes can resurrect old data.
- "TrueTime makes clocks accurate." It makes uncertainty *bounded and known*.
- "Monotonic clock fixes everything." Monotonic prevents jumps backward in one process; doesn't help across nodes.

## Brute force approach

Use `time.time()` everywhere and hope NTP is good enough. Works until a node's clock jumps; then data corruption, LWW errors, or ordering bugs.

## Optimal approach

For ordering inside a process: monotonic clock for durations, wall clock for human-readable timestamps. For ordering across nodes: HLC (combines wall and logical), or vector clocks. For strict global ordering: TrueTime-style bounded uncertainty + commit-wait.

## Solution

```python
# Hybrid Logical Clock
class HLC:
    def __init__(self):
        self.l = 0   # logical time
        self.c = 0   # counter

    def now(self):
        pt = time.time_ns()
        if pt > self.l:
            self.l = pt
            self.c = 0
        else:
            self.c += 1
        return (self.l, self.c)

    def update(self, l_msg, c_msg):
        pt = time.time_ns()
        new_l = max(self.l, l_msg, pt)
        if new_l == self.l == l_msg:
            self.c = max(self.c, c_msg) + 1
        elif new_l == self.l:
            self.c += 1
        elif new_l == l_msg:
            self.c = c_msg + 1
        else:
            self.c = 0
        self.l = new_l
        return (self.l, self.c)
```

```python
# Spanner-style commit-wait sketch
def commit(txn):
    s = TT.now().latest         # candidate commit timestamp
    persist(txn, s)
    while not TT.after(s):
        time.sleep(0.001)        # commit-wait until s is definitely past
    release_locks(txn)
    return s
```

## Step-by-step dry run

Two-DC system, two transactions T1 then T2 in real-time order. Without commit-wait first:

```
Without TrueTime / commit-wait:

t=0    Node A (in DC1) commits T1 at A_clock=10.000.
t=1    Node B (in DC2, clock skewed +5ms ahead) commits T2 at B_clock=10.010.
       Real-time order: T1 → T2.
       Logged timestamps: T1=10.000, T2=10.010. Looks ordered. Good.

t=2    Same scenario but T2 lands on Node C (clock skewed -8ms behind).
       T2 logged at C_clock=9.998.
       Logged order: T2 < T1. BAD — real time says T1 → T2.

----------------------------------------------------------------------
With TrueTime commit-wait:

t=0    Node A: TT.now() = [9.997, 10.014]. Latest = 10.014. s_T1 = 10.014.
       Persist T1 with s=10.014.
       Commit-wait until TT.now().earliest > 10.014.
       Say at real time 10.022 we have TT.now() = [10.015, 10.029].
       earliest = 10.015 > 10.014 → release locks.

t=23ms Real time. T1 considered committed.

t=24   Node C (real-time after T1): TT.now() = [10.019, 10.030] (with -8ms skew
       its uncertainty interval still aligns with global UTC because TrueTime
       reports honest bounds). Pick s_T2 = 10.030. Always > 10.014.

       T2 sees T1 in its past. Externally consistent.

Cost: commit latency = ε (typically 5-10ms in Google DCs).
```

## How to think aloud in the interview

> "Wall clocks across machines are never perfectly synchronised. NTP gives 1-100ms skew on the internet, sub-ms on LAN. PTP with hardware support gets to microseconds. Skew breaks last-write-wins and makes wall-clock timestamps unreliable for ordering.
>
> Spanner introduced TrueTime: an API that returns not a point but an interval `[earliest, latest]`, with a bounded uncertainty ε of about 7ms thanks to GPS + atomic clocks in each DC. Transactions commit at `latest`, then *wait* until `now.earliest > commit_ts` before releasing locks. This commit-wait guarantees external consistency: any later transaction sees the commit in its real-time past.
>
> Without dedicated hardware, you use HLC — a hybrid of wall and logical time. CockroachDB and YugabyteDB use HLC with a configured max-offset (default 500ms); if a node's wall clock drifts past that, it panics.
>
> The takeaway: never use raw wall-clock timestamps for ordering across nodes. Use HLC or monotonic logical clocks; reserve wall time for display and SLAs."

## Important takeaways
- Wall clocks across nodes have skew (μs to 100ms) and drift.
- LWW with wall clocks can resurrect data on skew.
- TrueTime = bounded uncertainty interval + commit-wait → external consistency.
- HLC = practical alternative without GPS/atomic; CockroachDB, Yugabyte.
- Monotonic clocks for durations; wall clocks for display only.
- Cloud VMs have larger skew than bare-metal.

## Variants
1. **NTP / chrony** — typical sync; 1-100ms.
2. **PTP (IEEE 1588)** — hardware-assisted sub-μs sync.
3. **TrueTime** (Google) — GPS + atomic; ε ~ 7ms.
4. **HLC** — hybrid wall + logical; no special hardware.
5. **Bound-loose NTP + max_offset panic** — CockroachDB's pragmatic approach.

## Revision notes

> **clock-skew — 60 second recap**
> - Clocks across nodes have skew (NTP: 1-100ms) and drift; never trust raw timestamps for ordering.
> - LWW with wall clocks resurrects data on skew.
> - Spanner TrueTime: [earliest, latest]; commit-wait until earliest > commit_ts → external consistency.
> - HLC: practical hybrid; CockroachDB, Yugabyte.
> - Use monotonic clock for durations; wall for display.
> - Cloud VMs: expect larger skew; configure max_offset accordingly.
