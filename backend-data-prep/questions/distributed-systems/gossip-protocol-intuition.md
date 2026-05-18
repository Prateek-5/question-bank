# Gossip protocols: epidemic propagation for membership and state

## Source / Origin
- Demers et al., "Epidemic Algorithms for Replicated Database Maintenance" (Xerox PARC, 1987).
- Production: Cassandra, DynamoDB, Consul, Akka Cluster, Serf, ScyllaDB, Redis Cluster.
- Concept reference: `backend-data-prep/distributed-systems/membership.md`.

## Why this question matters in interviews
Gossip is the answer to "how does Cassandra discover that a node went down without a central coordinator?" If you can explain push vs pull vs push-pull, fanout, convergence in O(log N) rounds, and the SWIM variant for failure detection, you signal you understand decentralised state propagation.

## Concepts involved

### Syntax / mechanism to lock in

```
Every T seconds, each node picks K random peers and exchanges state.

Push:       I send my state to peer.
Pull:       I ask peer for their state.
Push-Pull:  exchange both directions.

For N nodes with fanout K and round time T:
  Convergence: O(log_K N) rounds → O(T · log_K N) wall time.
  Bandwidth per node: O(K · |state|) per round.

SWIM (Scalable Weakly-consistent Infection-style Membership):
  1. Ping random peer.
  2. If no ack, ask K other peers to ping it (indirect probe).
  3. If still no ack, mark suspect → eventually dead, gossip the suspicion.
```

### Edge cases / interview traps

1. **Push-only has the "rumor saturation" problem**: when most nodes know, pushes are wasted. Push-pull is usually preferred.
2. **Fanout vs convergence trade-off.** K=3..5 typically; higher fanout = faster convergence but more bandwidth.
3. **Anti-entropy vs rumor mongering.** Anti-entropy compares full state for completeness; rumor mongering sends only new info, stops after some rounds.
4. **SWIM's incarnation numbers** prevent stale "suspect" messages from re-killing a node that came back.
5. **Gossip is not just for membership.** Cassandra gossips schema versions, tokens, load, generation.
6. **Network partitions split the rumor universe** — gossip resumes propagation when partition heals.
7. **Beware "self-fulfilling" failure detection** under high load — SWIM's indirect probes mitigate this.

## Mental Model

Think of how a rumour spreads in a school: each person, on hearing it, tells a few others at random. Even though no one has a megaphone, within O(log N) re-tellings, everyone knows. The math is identical to viral spread.

```
Round 0:   A knows                                B C D E F G H ...
Round 1:   A,B,C   (A gossipped to 2)             D E F G H ...
Round 2:   A,B,C,D,E,F,G                          H I ...
Round 3:   everyone

Convergence in ceil(log_K N) rounds with high probability.
```

## Why interviewers care
- Tests understanding of decentralised systems without master coordinators.
- Reveals knowledge of Cassandra, Consul, Akka Cluster internals.
- Probe-and-suspect logic is a classic distributed-systems building block.

## Common beginner confusion
- "Gossip is broadcast." No — each node talks to K random peers, not all.
- "Gossip needs consensus." No — gossip is eventually consistent membership/state.
- "Gossip is slow." It's O(log N) rounds; for N=1000 and T=1s, full convergence is ~10s. Fast for membership.
- "SWIM is just heartbeat." It has indirect probes that distinguish "node down" from "network blip".

## Brute force approach

All-to-all heartbeats: every node pings every other every T seconds. Bandwidth = O(N²). Dies above ~100 nodes.

## Optimal approach

Gossip with K=3..5 fanout, push-pull style. Convergence O(log N) with bandwidth O(K·N) total per round. Add SWIM for failure detection: direct ping, indirect probe, suspicion timer, incarnation numbers.

## Solution

```python
import random, time, threading

class GossipNode:
    def __init__(self, node_id, peers):
        self.id = node_id
        self.peers = peers          # list of peer addresses
        self.state = {self.id: (time.time(), "ALIVE", 0)}  # id -> (hb, status, incarnation)
        self.fanout = 3
        self.round_interval = 1.0

    def heartbeat_loop(self):
        while True:
            t = time.time()
            inc = self.state[self.id][2]
            self.state[self.id] = (t, "ALIVE", inc)
            self.gossip_round()
            time.sleep(self.round_interval)

    def gossip_round(self):
        targets = random.sample(self.peers, min(self.fanout, len(self.peers)))
        for peer in targets:
            try:
                peer_state = rpc_call(peer, "exchange", self.state)
                self.merge(peer_state)
            except Exception:
                self.handle_no_ack(peer)

    def merge(self, incoming):
        for node_id, (hb, status, inc) in incoming.items():
            cur = self.state.get(node_id)
            if cur is None or (inc, hb) > (cur[2], cur[0]):
                self.state[node_id] = (hb, status, inc)

    def handle_no_ack(self, peer):
        # SWIM indirect probe
        helpers = random.sample([p for p in self.peers if p != peer], k=3)
        if not any(rpc_call(h, "ping_via", peer) for h in helpers):
            self.mark_suspect(peer)

    def mark_suspect(self, peer):
        hb, _, inc = self.state.get(peer, (time.time(), "ALIVE", 0))
        self.state[peer] = (time.time(), "SUSPECT", inc)
```

## Step-by-step dry run

8-node cluster, fanout 2, push-pull, A learns of new metadata:

```
Round 0    A: knows X       others: don't know X
           [A]              [B C D E F G H]

Round 1    A gossips to {C, F}, exchanges state.
           [A C F] know X
           [B D E G H] don't.

Round 2    A→{B,H}, C→{D,G}, F→{E,A}
           [A B C D E F G H] all know X.   8 nodes, log_2(8) = 3 rounds (actual 2 here because random went well).

Failure detection example:

Round 0:  H crashes silently.
Round 1:  C pings H — no ack within T_probe.
Round 2:  C asks D and G to ping H — none get ack.
Round 3:  C marks H as SUSPECT (incarnation=H_inc, hb=T_now). Gossips it.
Round 4-6: SUSPECT propagates; after T_suspect timer with no contradicting "ALIVE"
          message from H, H is marked DEAD by all nodes.

If H comes back: H increments its own incarnation (inc=H_inc+1), broadcasts ALIVE
with higher incarnation. Higher incarnation wins → SUSPECT/DEAD overridden.
```

## How to think aloud in the interview

> "Gossip is epidemic state propagation. Each node, every T seconds, picks K random peers and exchanges state. Convergence is O(log_K N) rounds, bandwidth is O(K·|state|) per node per round. That's why Cassandra and Consul scale to thousands of nodes without a coordinator.
>
> Three styles: push, pull, push-pull. Push-pull is typical because it avoids the rumor-saturation waste.
>
> For failure detection, SWIM adds indirect probes — if A can't reach B, A asks 3 other nodes to ping B. If they fail too, A marks B SUSPECT with an incarnation number, and gossips it. SUSPECT becomes DEAD after a timer. Incarnation numbers handle revivals: a node that comes back bumps its own incarnation, overriding stale SUSPECT messages.
>
> The trade-off is eventual consistency on membership — there's a window where different nodes have different views — but that's acceptable for routing decisions backed by client retries."

## Important takeaways
- Gossip: each node talks to K random peers per round; O(log N) convergence.
- Push, pull, push-pull; push-pull is usually best.
- SWIM = direct + indirect probe + suspect timer + incarnation numbers.
- Used by Cassandra, Consul, Akka Cluster, ScyllaDB, Redis Cluster.
- Gives eventually consistent membership and metadata.
- Anti-entropy vs rumor mongering: full state vs deltas-only.

## Variants
1. **HyParView / Plumtree** — gossip with overlay network optimisation.
2. **Epidemic Broadcast Trees** — combines reliable broadcast with gossip.
3. **Lifeguard** — improvements to SWIM for tail latency and false positives.
4. **Anti-entropy schedules** — periodic full-state reconciliation for completeness.
5. **Gossip over TCP vs UDP** — UDP for speed, TCP for reliability of large payloads.

## Revision notes

> **gossip — 60 second recap**
> - Pick K random peers per round; exchange state. O(log_K N) convergence.
> - Push / pull / push-pull (push-pull preferred).
> - SWIM: direct probe → indirect probe → SUSPECT (incarnation) → DEAD.
> - Eventually consistent; not consensus. Use Raft for leader/config.
> - Real systems: Cassandra, Consul, Akka, Serf, Redis Cluster.
> - Bandwidth O(K·N) per round; fanout K=3..5 typical.
