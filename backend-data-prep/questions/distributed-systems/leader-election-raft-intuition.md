# Leader Election in Raft — Terms, Votes, and Log Replication

## Source / Origin
- Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm" (USENIX ATC '14).
- The Raft paper: https://raft.github.io/raft.pdf
- Production systems: etcd, Consul, CockroachDB, TiKV, MongoDB ≥3.4, Kafka KRaft, Redis Raft.
- Interview prompt: "Walk me through how Raft elects a leader and replicates writes" — staple of senior backend / infrastructure rounds.

## Why this question matters in interviews
Raft is *the* consensus algorithm interviewers expect you to be able to discuss in 2026. It replaced Paxos as the de-facto teaching standard because the paper was deliberately written for human understanding. A senior candidate must be able to (a) define a *term*, (b) describe the *RequestVote* and *AppendEntries* RPCs, (c) explain why majority quorum prevents split brain, and (d) state the *log matching property*. Companies using etcd, Consul, CockroachDB, or any KRaft-based Kafka will probe you here; getting Raft wrong is the difference between a senior offer and a level-down.

## Concepts involved

### Syntax / mechanism to lock in

Three roles, three RPCs, one logical clock called *term*:

```
Roles:    Follower → Candidate → Leader
RPCs:     RequestVote(term, candidateId, lastLogIdx, lastLogTerm)
          AppendEntries(term, leaderId, prevLogIdx, prevLogTerm, entries[], leaderCommit)
          InstallSnapshot(...)  -- for log truncation, ignored here

Term:     monotonically increasing integer; every RPC carries it.
          Rule: if you see term > yours → step down to follower, update term.
```

Election timer: each follower has a randomised timeout (typically 150–300 ms). If no AppendEntries arrives before the timer fires, the follower becomes a candidate.

```
Candidate steps:
  1. term += 1
  2. votedFor = self
  3. send RequestVote(term, self.id, lastLogIdx, lastLogTerm) to all peers
  4. count votes (including own); if ≥ majority → become leader
  5. if AppendEntries with term ≥ current arrives → step down
  6. if timeout fires before majority → start a new election
```

### Edge cases / interview traps
1. **Randomised election timeout is mandatory.** If all followers timed out simultaneously, every election would split the vote and progress would stall. Randomisation breaks symmetry.
2. **Vote is granted at most once per term.** A follower sets `votedFor = X` and refuses subsequent vote requests in the same term.
3. **Log up-to-date check.** A candidate wins only if its log is at least as up-to-date as the voter's — defined as: same lastLogTerm and ≥ lastLogIdx, or higher lastLogTerm. Prevents data loss.
4. **Split votes.** If two candidates tie at majority-minus-one, both timeout, both restart with new terms. Randomisation makes this rare.
5. **Term inflation under partition.** A partitioned follower keeps timing out and incrementing its term. When it rejoins, its term is much higher; current leader sees the higher term and steps down. Then a new election runs. This can cause unnecessary churn — modern Raft uses *pre-vote* to avoid it.
6. **Pre-vote phase.** Optional optimisation: candidates first ask "would you vote for me?" without bumping their term. Avoids partition-induced term churn.
7. **Leader completeness.** Only entries committed in the leader's term can be considered committed. Old entries from a previous term need a current-term entry on top to become committed (the Figure-8 problem from the paper).
8. **No-op on election win.** New leader appends a no-op entry to bring all prior entries forward into its term. Critical detail many candidates miss.

## Mental Model

Think of it as a parliament with strict rules: only one prime minister per term; if the PM goes quiet for too long, any MP can call a confidence vote; you need a majority to be sworn in; you can't be sworn in if your draft of the laws lags behind what others have already passed.

```
       Term 1                   Term 2                  Term 3
   ┌────────────┐           ┌────────────┐          ┌────────────┐
   │ Leader: A  │   A dies  │ Election → │ B wins   │ Leader: B  │
   │            ├──────────►│ Candidates │─────────►│            │
   │ Followers: │           │ B, C try   │          │ Followers: │
   │ B, C, D, E │           │            │          │ A?, C, D, E│
   └────────────┘           └────────────┘          └────────────┘
                            (no leader during election)
```

## Why interviewers care
- Tests understanding of **majority quorum** — the core mechanism that prevents split brain.
- The **term** concept is the *logical clock for leadership*. Candidates who understand it think correctly about distributed consensus.
- AppendEntries is both **heartbeat and replication** in one — elegant; interviewers love asking why.
- Raft drives etcd, Consul, MongoDB, Kafka KRaft — knowing it well is directly applicable to production debugging.

## Common beginner confusion
- **"Raft uses Paxos."** No. Raft is an *alternative* to Paxos with the same guarantees and (arguably) simpler exposition.
- **"All nodes vote on every write."** No. Only the leader handles writes; followers replicate. Voting happens during *elections*, not writes.
- **"Majority means 51%."** Means strictly more than half: in a 5-node cluster, 3.
- **"You need an odd number of nodes."** Not strictly — you need odd majority math; 4 nodes tolerate the same 1 failure as 3 nodes (still need 3 to make majority), so even sizes are wasteful, not wrong.
- **"Leader can commit any entry as soon as majority replicates."** Only entries in the leader's *current term* — Figure 8 of the paper covers exactly this.
- **"Heartbeats and AppendEntries are different."** Same RPC; a heartbeat is just an AppendEntries with empty `entries[]`.

## Brute force approach
"Use Bully + a shared log file." Bully has no quorum; you'd have split brain. The shared log file is a single point of failure. This is what Raft *replaces*.

"Two-phase commit for every write." 2PC blocks on coordinator failure and is not designed for replication. Wrong tool.

## Optimal approach
Raft itself. The structure is:

1. **Election phase** (when no leader / leader silent).
2. **Replication phase** (leader appends client commands, replicates via AppendEntries, commits when majority ack).
3. **Safety properties** ensure: at most one leader per term; committed entries are never lost.

You describe these three pieces with the specific RPCs and the term-based ordering. That's a complete senior-level answer.

## Solution (algorithm + pseudocode + diagram)

### Pseudocode (follower → candidate → leader transitions)

```
loop forever:
  if state == FOLLOWER:
    if AppendEntries received with term ≥ currentTerm:
      reset election timer
      respond to leader
    if election_timer_expired:
      state = CANDIDATE
      start_election()

  if state == CANDIDATE:
    currentTerm += 1
    votedFor = self
    votesReceived = 1
    reset election timer (randomised)
    send RequestVote to all peers
    on receive RequestVoteResponse(granted=true):
      votesReceived += 1
      if votesReceived > N/2:
        state = LEADER
        send no-op AppendEntries to all (claim leadership)
    on receive AppendEntries(term ≥ currentTerm):
      state = FOLLOWER
    on election_timer_expired:
      start_election()    # new term, retry

  if state == LEADER:
    on client command C:
      append C to local log
      send AppendEntries with C to all followers
      when majority ack:
        commit C, apply to state machine, respond to client
    every HEARTBEAT_INTERVAL:
      send empty AppendEntries (heartbeats) to all followers
    on receive RPC with term > currentTerm:
      state = FOLLOWER
```

### Vote-handling rule (follower)

```
on receive RequestVote(term, candId, lastLogIdx, lastLogTerm):
    if term < currentTerm:
        reply (term=currentTerm, granted=false)
    if term > currentTerm:
        currentTerm = term
        votedFor = null
        state = FOLLOWER
    if votedFor in (null, candId) AND log_is_at_least_as_up_to_date(lastLogIdx, lastLogTerm):
        votedFor = candId
        reset election timer
        reply (term=currentTerm, granted=true)
    else:
        reply (term=currentTerm, granted=false)
```

### Diagram: log replication after election

```
Cluster: A, B, C, D, E. B is the new leader at term 3.

Client → B:  SET x = 7
                │
                ▼
         B's log: [...] [T3 SET x=7]
                │
                ├──AppendEntries(T3, prev=10, entries=[SET x=7])──► A
                ├──AppendEntries──► C
                ├──AppendEntries──► D
                └──AppendEntries──► E

         Responses:  A: success
                     C: success
                     D: success
                     E: (slow)

         Quorum = 3, B has 3 acks including itself + A + C → commit.
         commitIndex = 11
         B applies SET x=7; responds to client OK.

         Next AppendEntries to all carries leaderCommit=11.
         A, C, D apply locally. E eventually catches up.
```

### Diagram: split-vote → re-election

```
Term 3: A times out. A becomes candidate, term=3.
Term 3: B also times out simultaneously. B becomes candidate, term=3.
        Both bump term to 3 (or one to 3 and one to 4).

A requests votes:  A → {B, C, D, E}
                   B: NO  (already voted for self in term 3)
                   C: YES
                   D: YES
                   E: NO   (already voted for B)

A has 3 of 5 → A wins. B steps down on next heartbeat.

If instead A got C and B got D, E:
   A has 2, B has 2 → no leader → both election timers expire → new term.
   Randomised timeout ensures one fires first → likely wins cleanly.
```

## Step-by-step dry run

5-node cluster {A, B, C, D, E}, current term 2, leader=A. A crashes at t=0.

| t (ms) | Event                                                     | Term | Leader | Notes                                |
|--------|-----------------------------------------------------------|------|--------|--------------------------------------|
| 0      | A crashes                                                 | 2    | none   | Heartbeats stop                       |
| 175    | B's election timer fires first (randomised 150–300ms)     | 3    | none   | B → candidate                         |
| 176    | B votes for self, sends RequestVote(term=3) to C, D, E    | 3    | none   |                                       |
| 180    | C grants vote (log up-to-date)                            | 3    | none   | C.votedFor = B                        |
| 181    | D grants vote                                              | 3    | none   | D.votedFor = B                        |
| 183    | B has 3 votes ≥ majority(3) → leader                       | 3    | B      |                                       |
| 184    | B sends no-op AppendEntries(term=3) to all                | 3    | B      | Claims leadership, brings logs forward|
| 184    | E receives B's AppendEntries; updates leader=B, term=3    | 3    | B      |                                       |
| 200    | Client SET x=7 lands on B                                  | 3    | B      |                                       |
| 201    | B appends [T3 SET x=7] to local log at idx 11             | 3    | B      |                                       |
| 202    | B sends AppendEntries to C, D, E                          | 3    | B      |                                       |
| 205    | C, D, E ack                                                | 3    | B      | majority reached                      |
| 206    | B commits idx 11, applies x=7, responds OK to client      | 3    | B      |                                       |
| 250    | A recovers, comes back as follower with stale term=2      | 3    | B      |                                       |
| 251    | A receives heartbeat from B with term=3 → A updates term  | 3    | B      | A is just a follower now              |

**Election latency:** ~10 ms (one RTT). **Write latency:** one RTT to a majority. **Total commit:** ~5 ms in good networks.

## How to think aloud in the interview

"Raft splits consensus into three sub-problems: leader election, log replication, and safety. Let me walk through each.

Each node is in one of three states — follower, candidate, leader — and time is divided into *terms*, which act as a logical clock. Every RPC carries the sender's term; whenever you see a higher term, you step down to follower and update yours. That single rule prevents zombies.

Followers expect heartbeats — really empty AppendEntries — from the leader on a randomised timeout, typically 150 to 300 milliseconds. If the timer fires, the follower becomes a candidate, increments its term, votes for itself, and broadcasts RequestVote to all peers. If it gets votes from a majority, it's the leader. The randomisation is important — without it, every follower would time out at the same instant and we'd split the vote indefinitely.

There's a critical rule on the vote: a follower grants a vote only if the candidate's log is at least as up-to-date as its own. This is what ensures we never elect a leader that would have to delete already-committed data — the safety property called Leader Completeness.

Once elected, the leader handles all client writes. It appends to its local log, sends AppendEntries to followers, and once a majority — including itself — has replicated, it commits and applies to its state machine. AppendEntries doubles as the heartbeat, so during steady-state operation there's no idle traffic.

The subtle bit is committing entries from previous terms. The leader can only consider entries committed once it's replicated an entry from its own current term — this is Figure 8 in the paper. A common trick is for a new leader to append a no-op entry immediately on winning, which brings previous-term entries forward into the current term.

For partition handling — if a leader gets partitioned away from the majority, it can no longer commit (no quorum), and meanwhile the majority side elects a new leader with a higher term. When the old leader comes back, it sees the higher term and steps down. Pre-vote, an extension, avoids unnecessary term churn from flapping followers.

In production I use Raft via etcd or Consul rather than rolling my own. The hard parts — snapshots, log compaction, dynamic membership changes via joint consensus — are battle-tested in those libraries."

## Important takeaways
- **Three roles, three RPCs, one term**. RequestVote, AppendEntries, InstallSnapshot.
- **Majority quorum** prevents split brain — strictly more than N/2.
- **Randomised election timeout** breaks ties.
- **Log up-to-date check** during voting protects committed data.
- **AppendEntries is heartbeat + replication** in one RPC.
- **Only current-term entries can be considered committed** by the leader (Figure 8); use a no-op on election win.
- **Term acts as a logical clock for leadership**; higher term always wins, lower term always steps down.
- **Pre-vote** avoids partition-induced term churn.

## Variants
1. **Multi-Raft** — many Raft groups in one cluster, each owning a key range (CockroachDB, TiKV).
2. **Joint consensus** — Raft's mechanism for safe membership changes; commits in two stages (Cold,new → Cnew).
3. **Learner nodes** — non-voting replicas; used for read scaling and pre-joining members.
4. **Witness nodes** — vote-only, no data; reduces storage cost while maintaining quorum.
5. **Raft with pre-vote** — extra phase before bumping term; avoids unnecessary churn.
6. **Flexible Paxos / Raft** — separate read and write quorums so reads can use fewer replicas.

## Revision notes

> **Raft — 60 second recap**
> - 3 roles (follower/candidate/leader), 3 RPCs (RequestVote, AppendEntries, InstallSnapshot), 1 term (logical clock).
> - Randomised election timeout (150–300 ms); on timeout, follower → candidate.
> - Candidate bumps term, votes self, asks others. Majority wins.
> - Vote requires candidate log ≥ voter log (up-to-date rule).
> - Leader replicates via AppendEntries; commits on majority ack.
> - AppendEntries = heartbeat when empty.
> - **Trap:** committing entries from earlier terms — only via a current-term entry on top (no-op trick).
> - Pre-vote prevents partition-induced term churn.
