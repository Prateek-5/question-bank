# Leader Election — The Bully Algorithm

## Source / Origin
- Garcia-Molina, "Elections in a Distributed Computer System" (1982).
- Standard textbook coverage: Tanenbaum *Distributed Systems*, Coulouris *Distributed Systems: Concepts and Design*.
- Interview prompt variants: "How do you elect a coordinator when nodes have unique IDs?", "Walk me through Bully" — common at MongoDB, Cassandra-flavoured rounds where the engine internally uses a Bully-derived scheme (older MongoDB <4.0 used a variant).

## Why this question matters in interviews
Bully is the first leader-election algorithm any senior backend engineer should be able to whiteboard end-to-end in 10 minutes. It tests three things at once: (a) can you reason about *message exchanges* between identified peers (not just "nodes talk"), (b) do you understand *failure detection by timeout*, and (c) can you spot the *split-brain risk* the algorithm carries when network partitions are introduced. Interviewers use Bully as the warm-up before pulling you into Raft. Fumbling Bully is a strong negative signal because it is the simplest possible election protocol.

## Concepts involved

### Syntax / mechanism to lock in
Three message types only:
```
ELECTION(from=X)         → "I'm starting an election; anyone bigger than me?"
OK / ALIVE(from=Y)       → "Yes, I'm alive and bigger; back off."
COORDINATOR(from=Z)      → "I am the new leader; everyone update."
```

Algorithm (process P notices coordinator dead):
```
1. P sends ELECTION to all processes with ID > P.
2. If no OK arrives within timeout T → P wins → P broadcasts COORDINATOR.
3. If any OK arrives → P drops out, waits for COORDINATOR from someone bigger.
4. If P then doesn't see COORDINATOR within T' → P restarts step 1.
```

Recovery rule: when a previously-failed process restarts, if its ID is larger than the current coordinator, it starts a new election (hence the name *bully* — the biggest ID always wins).

### Edge cases / interview traps
1. **No tie-breaker beyond ID.** IDs must be globally unique and totally ordered. If two nodes have ID=5, the protocol breaks.
2. **Network partition = split brain.** If the cluster splits 3+2, both partitions can independently elect leaders. Bully has *no quorum requirement*. This is the #1 follow-up question.
3. **O(n²) messages worst case.** When the lowest-ID node detects failure, it pings everyone above, each of whom pings everyone above them. For n=100, that's ~5000 messages.
4. **Timeout tuning.** Too short → false elections. Too long → slow failover.
5. **The "bully restarts and wins" pathology.** A flapping high-ID node causes constant re-elections; productive work stalls.
6. **Concurrent elections.** Two low-ID nodes detect failure simultaneously and both start; merge by the highest-ID surviving node winning.
7. **Asymmetric failure detection.** Node X thinks the leader is dead but the leader is actually fine and reachable from others. X starts an election; the existing leader sees ELECTION from X, replies OK, X stops. The existing leader stays — but only if it bothers to listen for ELECTIONs.

## Mental Model

Think of a corporate hierarchy where the senior-most employee in the office is the boss. When the boss disappears, anyone who notices shouts "hey, anyone more senior than me here?" If a senior responds, the junior shuts up. The most senior remaining person eventually declares themselves boss. When the original boss returns, they walk in and reclaim the chair — *because they're more senior, they bully their way back to leadership*.

```
   IDs:  1   2   3   4   5(LEADER, dies)

   Step 1: Node 2 detects timeout from 5
           Node 2 sends ELECTION to {3, 4, 5}

           2 ──ELECTION──► 3
           2 ──ELECTION──► 4
           2 ──ELECTION──► 5  (no response — dead)

   Step 2: 3 and 4 reply OK to 2; both start their own elections
           3 ──ELECTION──► {4, 5}
           4 ──ELECTION──► {5}

   Step 3: 4 receives OK from no one (5 dead, nobody bigger)
           4 broadcasts COORDINATOR(4) to {1, 2, 3}

   New leader: 4
```

## Why interviewers care
- It's the **simplest correct election protocol with explicit message sequencing** — proves you can reason about peer-to-peer state transitions.
- The natural follow-up "what happens during a partition?" leads to quorum, fencing, witness, and ultimately Raft.
- Engineers who can draw the message exchange under pressure also tend to handle Paxos / Raft conversations confidently.
- The O(n²) message count question separates candidates who think about *cost* from those who only think about *correctness*.

## Common beginner confusion
- **"Bully needs majority quorum."** It doesn't. That's exactly its weakness. Raft does; Bully doesn't.
- **"The lowest ID wins because they started it."** No — *highest* ID always wins. The starter usually loses.
- **"COORDINATOR is acknowledged."** It's typically a fire-and-forget broadcast. Nodes that miss it learn from the next heartbeat.
- **"Bully prevents split brain."** It doesn't. Two partitions can independently each elect their highest-ID-locally.
- **"You need to re-elect on every failure."** Only on *leader* failure. Follower failures don't trigger elections.

## Brute force approach
"Pick the node with the lowest IP and always trust it." Static config. Fails the moment that node dies — no automated failover. Not an election at all.

"Use a shared file or DB row as a lock." Now you've outsourced the problem to a single point of failure. Reasonable as a *production* pattern (ZooKeeper / etcd lease) — but it's no longer an election protocol; it's external coordination.

## Optimal approach
Bully is itself the "obvious" baseline. The senior framing is: **Bully is correct under perfect failure detection and absence of partitions**. In real systems we replace it with:

1. **Raft / Paxos** — quorum-based; partition-safe.
2. **ZooKeeper / etcd lease** — externalised consensus; one ZK ensemble elects for many client apps.
3. **Ring-based election (Chang-Roberts)** — O(n) messages instead of O(n²), at cost of slower latency.

In an interview you describe Bully, then *immediately* state when you would and wouldn't use it. "Bully works for small, well-connected clusters with reliable network — say, a 5-node management plane. For data-plane elections under partitions, I'd reach for Raft."

## Solution (algorithm + pseudocode + diagram)

```
state = { id: self.id, leader: null, peers: [list of peer IDs], coordinator_seen_at: now }

on_heartbeat_timeout():
    if now - coordinator_seen_at > HEARTBEAT_TIMEOUT:
        start_election()

start_election():
    higher = [p for p in peers if p.id > self.id]
    if not higher:
        declare_leader()
        return
    responses = []
    for p in higher:
        send ELECTION → p
    wait OK_TIMEOUT:
        collect any OK messages
    if no OK received:
        declare_leader()
    else:
        wait COORDINATOR_TIMEOUT for COORDINATOR message
        if no COORDINATOR seen:
            start_election()        # restart

on_receive_ELECTION(from):
    send OK → from
    start_election()                # I'm bigger; I'll try to win

on_receive_COORDINATOR(from):
    leader = from
    coordinator_seen_at = now

declare_leader():
    leader = self.id
    broadcast COORDINATOR(self.id) to all peers
```

### Message-flow diagram (5 nodes, leader=5 dies)

```
Time →

  N1 |
  N2 |  detects timeout
     |       │
     |       ▼
     |   ELECTION ─────────► N3
     |   ELECTION ──────────────────► N4
     |   ELECTION ───────────────────────────► N5 (dead)
     |       ▲
     |       │  OK from N3, OK from N4
     |       │
     |   (N2 drops out)
     |
  N3 |       ELECTION ──────► N4
     |       ELECTION ───────────────► N5 (dead)
     |          ▲
     |          │  OK from N4
     |       (N3 drops out)
     |
  N4 |              ELECTION ────────► N5 (dead)
     |              (no OK; timeout fires)
     |              COORDINATOR(4) ──► N1, N2, N3
     |
   Result: N4 is leader. Total messages: ~9 for n=5.
```

## Step-by-step dry run

Cluster of 5 nodes IDs {1, 2, 3, 4, 5}. Leader = 5. 5 crashes at t=0.

| t (ms) | Event                                               | Sender → Receiver | State after                       |
|--------|-----------------------------------------------------|-------------------|-----------------------------------|
| 0      | Node 5 crashes                                      | —                 | leader=5, but unreachable         |
| 200    | Node 2 misses heartbeat, timeout fires             | —                 | 2 starts election                 |
| 201    | ELECTION sent to {3, 4, 5}                          | 2 → 3, 2 → 4, 2 → 5 | 5 silent                        |
| 205    | OK received from 3                                   | 3 → 2             | 2 will drop out                    |
| 206    | OK received from 4                                   | 4 → 2             | 2 drops out, waits for COORDINATOR|
| 210    | Node 3 starts its own election (it's bigger than 2)  | 3 → {4, 5}        | 5 silent                          |
| 215    | OK from 4 to 3                                       | 4 → 3             | 3 drops out                       |
| 220    | Node 4 starts its own election                       | 4 → {5}           | 5 silent                          |
| 320    | OK_TIMEOUT on node 4 — no response                   | —                 | 4 declares itself leader          |
| 321    | COORDINATOR(4) broadcast                             | 4 → {1, 2, 3}     | All update leader=4               |
| 322    | All nodes' heartbeat target → 4                      | —                 | Stable                            |

**Total: 9 inter-node messages for n=5.** Worst case is O(n²); average for "lowest detects" is closer to O(n² / 2).

Now 5 recovers at t=10s. It sees the cluster still operating; it broadcasts ELECTION (it's still bigger). Everyone replies OK. 5 collects no OKs from higher (none exist), declares itself COORDINATOR(5). 4 steps down. *The bully returns.*

## How to think aloud in the interview

"Bully is the canonical leader-election protocol you'd teach in a 101 class. Three messages: ELECTION, OK, COORDINATOR. The protocol guarantees that the highest-ID alive node wins, eventually. Let me walk through it on a 5-node cluster.

I notice node 5, the current leader, has missed heartbeats. I — say I'm node 2 — fire ELECTION at every node with ID greater than mine. If any of them respond OK, I drop out; they're alive and bigger, so they'll handle the election. If nobody responds within a timeout, I declare myself leader and broadcast COORDINATOR. Each recipient of an ELECTION starts its own election upward — so the work cascades to the highest living ID.

The properties to call out: (1) message complexity is O(n²) worst case — not great for large clusters; (2) it's *bully*-shaped because a recovered high-ID node immediately reclaims leadership, which can cause thrash; (3) and critically — **it doesn't tolerate partitions**. There's no quorum step. If the network splits, both sides can elect their own local maximum, and you get split brain.

In production I wouldn't use raw Bully for anything that holds state. I'd use it for ephemeral coordinator roles inside a small management plane — say, who's responsible for emitting cluster-wide metrics. For real state-machine replication I'd use Raft, which adds the missing quorum constraint. ZooKeeper or etcd is the typical externalised version."

## Important takeaways
- **Three messages: ELECTION, OK, COORDINATOR.** Memorise them.
- **Highest live ID wins.** Lowest-detector often starts the election.
- **O(n²) messages** worst case — quadratic.
- **No quorum → split-brain risk on partitions.** This is the headline weakness.
- **Bully = recovered high-ID reclaims leadership** — can cause thrashing under flapping.
- **Use it for:** small, well-connected clusters, ephemeral coordinator roles.
- **Avoid it for:** state-machine replication, anything needing partition safety.

## Variants
1. **Chang-Roberts ring election** — O(n) messages, logical ring topology, slower but cheaper.
2. **Modified Bully with majority confirmation** — declare leader only after >n/2 responses; closes split-brain gap.
3. **Invitation algorithm** — for asynchronous systems where Bully's timeouts are unreliable; the leader actively invites members.
4. **ZooKeeper ephemeral-sequential leader election** — externalised; the lowest-sequence znode is leader; watchers on the predecessor handle failover.
5. **Raft leader election** — Bully's grown-up cousin; adds terms, votes, and majority quorum (see `leader-election-raft-intuition.md`).

## Revision notes

> **Bully — 60 second recap**
> - Three messages: ELECTION, OK, COORDINATOR.
> - On detect: ping all higher IDs. If silence → I'm leader → broadcast.
> - Receiving ELECTION → reply OK, start your own.
> - Highest live ID wins. Recovered high-ID reclaims (the "bully" trait).
> - O(n²) messages, no quorum, no partition safety → split brain possible.
> - Use for small clusters / ephemeral roles. For real systems use Raft or ZK lease.
> - **Trap:** assuming Bully is partition-safe. It is not.
