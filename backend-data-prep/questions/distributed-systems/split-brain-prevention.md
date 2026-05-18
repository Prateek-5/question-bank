# Split-brain prevention: quorum, fencing, and STONITH

## Source / Origin
- HA cluster literature (Pacemaker, Linux-HA); Raft and Paxos formalised the quorum solution.
- Production: etcd, Consul, ZooKeeper, MongoDB, Elasticsearch, Patroni.
- Concept reference: `backend-data-prep/distributed-systems/leader-election.md`.

## Why this question matters in interviews
"Two leaders accept conflicting writes" is the canonical distributed-system disaster. If you can explain the three pillars — quorum-based election, leader leases / fencing tokens, and STONITH for shared-resource cases — you signal you understand HA failover beyond "use ZooKeeper".

## Concepts involved

### Syntax / mechanism to lock in

```
Split-brain causes:
  Network partition isolates leader from followers.
  Followers elect new leader; old leader still thinks it's leader.
  Both accept writes → divergent state.

Three defences:

1. Quorum-based election (W > N/2).
   Only a majority can elect a leader. Two majorities can't exist.
   Implies: ≥ 3 nodes, odd preferred to avoid even-split.

2. Leader lease / fencing token.
   Leader holds a time-bound lease.
   When elected, increments a monotonic epoch / term / fencing-token.
   Resources reject writes with stale tokens.

3. STONITH (Shoot The Other Node In The Head).
   When a node is suspected dead, physically power-off / fence it
   via IPMI, PDU, or kill-process script before promoting a new leader.
```

### Edge cases / interview traps

1. **Even-numbered clusters** can deadlock on a 2-2 partition; always use odd N.
2. **A leader who lost contact with majority but keeps writing** is the classic split-brain — fencing tokens at the storage layer block this.
3. **Lease time vs detection time.** Lease must expire before new leader is promoted, accounting for clock skew.
4. **Asymmetric partitions** (A sees B, B doesn't see A) are nightmares — quorum saves you.
5. **Witness nodes** (lightweight quorum tiebreakers) help in 2-DC setups.
6. **Storage-level fencing** required when leader writes directly to shared storage; locks alone don't help.
7. **MongoDB primary stepDown** does NOT prevent split-brain on its own; need w:majority writes and replica set with odd voters.

## Mental Model

A nuclear launch requires two keys, both turned simultaneously. No single officer can launch alone. Quorum elections are the same: no single subset can claim leadership without a majority. Fencing is the second lock: even if a stale leader thinks they're in charge, the missile silo (storage) refuses orders with an old key.

```
Cluster of 5 nodes. Partition splits them 3-2.

Side A (3 nodes):  [A1 A2 A3]   ← majority → can elect leader (term=7)
Side B (2 nodes):  [B1 B2]      ← minority → cannot elect → no leader on this side

Fencing token (term=7):
  Old leader on side B tries to write with token=6 → storage rejects.
  New leader on side A writes with token=7 → storage accepts.

         ┌─────────┐                      ┌─────────┐
         │ Side A  │  ←── partition ──→   │ Side B  │
         │ 3 nodes │                      │ 2 nodes │
         │ leader  │                      │ no lead │
         └─────────┘                      └─────────┘
              │
              ▼
         shared storage (fenced by term token)
```

## Why interviewers care
- Tests understanding of HA failover under network failure.
- Reveals knowledge of Raft, ZooKeeper, etcd, Patroni internals.
- Reveals whether you can design fencing at the storage layer.

## Common beginner confusion
- "Heartbeat is enough." Heartbeat alone gives detection but not arbitration. Need quorum.
- "Use a load balancer to elect." LB doesn't have a consistent view of cluster state; can route to two leaders.
- "Even clusters are fine." 2-2 partition → no quorum → stuck (or worse, both halves elect).
- "Locks prevent split-brain." Lock can be held by a dead leader; need a lease or fencing token.

## Brute force approach

Pick a primary manually; on failure, page an engineer to promote a replica after confirming the primary is dead. Works at small scale; slow MTTR; humans make mistakes under pressure.

## Optimal approach

Three layers:
1. **Quorum election** via Raft/Paxos/ZAB; odd N ≥ 3.
2. **Term/epoch/fencing token** monotonically increasing on every election; storage and clients reject stale tokens.
3. **Lease-based leader** so old leader auto-steps-down when it can't reach majority within lease period.

For shared-block-storage clusters, add STONITH to physically isolate suspected-dead nodes before promotion.

## Solution

### Raft-style leader election with fencing

```python
class RaftNode:
    def __init__(self, id, peers):
        self.id = id
        self.peers = peers
        self.term = 0
        self.state = "follower"
        self.voted_for = None
        self.lease_until = 0

    def start_election(self):
        self.term += 1
        self.state = "candidate"
        self.voted_for = self.id
        votes = 1
        for p in self.peers:
            try:
                if rpc_call(p, "request_vote", self.term, self.id):
                    votes += 1
            except Exception:
                pass
        if votes > (len(self.peers) + 1) / 2:
            self.become_leader()

    def become_leader(self):
        self.state = "leader"
        self.lease_until = time.time() + LEASE_SEC
        # Notify storage: my fencing token is self.term
        storage.set_min_term(self.term)


def write_to_storage(node, key, value):
    if not node.is_leader():
        raise NotLeader()
    if time.time() > node.lease_until:
        raise LeaseExpired("step down")
    return storage.put(key, value, term=node.term)


# storage layer
class FencedStorage:
    def __init__(self):
        self.min_term = 0

    def put(self, key, value, term):
        if term < self.min_term:
            raise StaleLeader(f"reject: term={term} min={self.min_term}")
        self.min_term = max(self.min_term, term)
        self._put(key, value)
```

### MongoDB w:majority

```javascript
db.collection("orders").insertOne(doc, { writeConcern: { w: "majority", wtimeout: 5000 } });
// Won't ack until majority of replica set has written; old primary
// in minority partition can't satisfy this → write fails fast.
```

### Patroni / etcd lease

```bash
# Patroni uses etcd leases (TTL) for Postgres leader election.
# Primary refreshes its key every leader_loop seconds; if TTL expires,
# a replica can claim primacy via compare-and-swap on the etcd key.
```

## Step-by-step dry run

5-node MongoDB replica set; network partitions 3-2.

```
Before partition:
  P (primary) at term=10.
  S1, S2 (secondaries), votes: 3.
  S3, S4 (secondaries), votes: 2.

t=0   Partition: {P, S1, S2} vs {S3, S4}.

t=5   P writes with w:majority → ack (has 3 of 5).

t=30  S3, S4 cannot reach P → election timeout.
      S3 starts election with term=11.
      S3 needs 3 votes; only S4 reachable → 2 votes < majority.
      S3 stays candidate. No new primary on this side. 

t=35  Old P at term=10 still primary on its side. Continues writes.
      With w:majority, writes succeed: P, S1, S2 ack.

t=120 Partition heals.
      S3, S4 rejoin. They see P at term=10. Replicate from P. No data loss.

----------------------------------------------------------------------
Bad scenario (no fencing, no majority):

  4-node cluster; partition 2-2.
  Side A: [P, S1] — P thinks it's still primary.
  Side B: [S2, S3] — S2 elects itself primary (assumes 2/4 quorum is fine).
  Both write. Divergence. Manual reconciliation needed.

Fix: 5-node cluster (odd) OR use witness/arbiter to break ties.
```

## How to think aloud in the interview

> "Split-brain is two leaders accepting conflicting writes after a partition. The three defences:
>
> First, quorum-based election — Raft requires W > N/2 votes. Two majorities can't exist; only one side can elect a leader. Always use odd N to avoid 2-2 deadlocks.
>
> Second, fencing tokens — each election bumps a monotonic term. Storage and clients reject writes with stale terms. Even if a partitioned old leader still 'thinks' it's leader, the storage layer refuses its writes.
>
> Third, leases — leader holds a TTL on its leadership; if it can't refresh (can't reach majority), it self-demotes. Combined with election timeout, this bounds the split-brain window.
>
> For shared-disk HA clusters (Pacemaker-style), add STONITH — physically power-off the suspected-dead node via IPMI before promoting its replacement. That eliminates ambiguity.
>
> Real systems: etcd, Consul, ZooKeeper for coordination; Raft/ZAB internally; MongoDB with w:majority and odd voters; Patroni for Postgres."

## Important takeaways
- Quorum election prevents two leaders by majority requirement.
- Fencing tokens prevent stale leaders from writing.
- Leases bound the time an old leader can act post-partition.
- Always odd N to avoid even-split deadlocks.
- Witness/arbiter helps in 2-DC setups.
- STONITH for shared-resource HA clusters.

## Variants
1. **Witness node / arbiter** — non-data tiebreaker for 2-DC.
2. **Leader lease + clock skew margin** — lease shorter than detection by skew bound.
3. **Storage-level CAS** — every write includes term; storage compares-and-swaps.
4. **Pre-vote** (Raft optimisation) — candidate confirms it could win before bumping term.
5. **Dynamic membership changes** — joint consensus to avoid split during reconfig.

## Revision notes

> **split-brain — 60 second recap**
> - Three defences: quorum, fencing token, lease (+ STONITH for shared HW).
> - Quorum: W > N/2; odd N.
> - Fencing: monotonic term/epoch; storage rejects stale.
> - Lease: leader auto-steps-down when can't reach majority.
> - Real: etcd, ZooKeeper, MongoDB w:majority, Patroni.
> - Witness arbiter for 2-DC tiebreak; STONITH for shared block storage.
