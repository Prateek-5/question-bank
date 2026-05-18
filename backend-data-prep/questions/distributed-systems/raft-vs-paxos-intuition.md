# Raft vs Paxos — Same Result, Different Cognitive Load

## Source / Origin
- Lamport, "The Part-Time Parliament" (1998) and "Paxos Made Simple" (2001).
- Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm" (Raft, 2014).
- Heidi Howard's *Flexible Paxos* (2016) and "Paxos vs Raft" survey paper.
- Interview prompt: "Why did Raft displace Paxos in modern systems?" — common at Cockroach, Google Cloud, MongoDB rounds.

## Why this question matters in interviews
Senior infrastructure interviewers love the comparison because it forces you to talk about *cognitive engineering* — why Raft's exposition won the industry even though Paxos came first and has the same theoretical guarantees. Candidates who can articulate "they solve the same problem; Raft adds *strong leadership* and *log contiguity* constraints that make implementation tractable" demonstrate they've actually built or read consensus systems, not just memorised the buzzwords. It's a 10-minute deep-dive question that separates surface-level knowledge from real understanding.

## Concepts involved

### Syntax / mechanism to lock in

**Paxos (single-decree, the classic form):**
```
Phase 1 — Prepare:
   Proposer picks ballot number n, sends PREPARE(n) to acceptors.
   Acceptor: if n > highest seen, promise not to accept lower ballots; reply with any prior accepted (n', v').

Phase 2 — Accept:
   Proposer picks v = highest (n', v') from promises, or its own value if none.
   Sends ACCEPT(n, v).
   Acceptor: if n still ≥ promise, accept (n, v) and respond.

Decision: once a majority accepts (n, v), v is chosen.

Multi-Paxos: skip Phase 1 once a stable proposer is elected; it can keep proposing in subsequent slots.
```

**Raft (described elsewhere; here the comparison surface):**
```
Strong leader: only the leader proposes log entries.
Term: monotonic; acts as a ballot.
Log: contiguous, appended in order.
Election: explicit phase, separate from replication.
Replication: AppendEntries with prevLogIdx/prevLogTerm matching.
```

### Edge cases / interview traps
1. **"Paxos = Raft" — false in the details.** They both achieve majority-quorum consensus. Raft enforces stricter invariants (single leader, contiguous log) which restrict the legal states. Paxos allows more concurrency in theory; Raft constrains for clarity.
2. **Multi-Paxos vs Paxos.** Single-decree Paxos agrees on one value. Multi-Paxos chains it for a log. Most production "Paxos" systems are Multi-Paxos. Mention this explicitly.
3. **Ballot number ≈ term, but not identical.** Paxos ballot numbers are issued per proposer (e.g., (round, proposer-id)). Raft terms are global. The flexibility costs clarity.
4. **Paxos allows holes in the log.** Slot 5 can be decided before slot 4. Raft forbids this — the log is contiguous. Trade: Paxos can be faster under partial outages, Raft is simpler to reason about.
5. **Leader election is explicit in Raft, implicit in Paxos.** A Paxos proposer that completes Phase 1 successfully *is* the de-facto leader; Raft makes the phase a first-class concept.
6. **Live-lock in single-decree Paxos.** Two proposers with increasing ballots can perpetually preempt each other. Multi-Paxos and Raft both solve this with stable-leader assumption + back-off.
7. **Flexible Paxos** decouples Phase-1 and Phase-2 quorums; you only need them to intersect. Useful for read-optimised configurations. Raft doesn't natively expose this.
8. **EPaxos / Generalised Paxos** allow leaderless operation with conflict-aware commit. Strictly stronger throughput in geo-distributed setups; correspondingly harder to reason about.

## Mental Model

Paxos is jazz; Raft is a march. Same destination — agreement on a value — but different aesthetics.

```
        Paxos                               Raft
  ┌──────────────────────┐           ┌──────────────────────┐
  │ Anyone can propose   │           │ Only leader proposes │
  │ Ballots are local    │           │ Terms are global     │
  │ Log can have holes   │           │ Log is contiguous    │
  │ Phase 1 optional in  │           │ Election is explicit │
  │   stable Multi-Paxos │           │   and named          │
  │ More concurrency     │           │ Easier to debug      │
  └──────────────────────┘           └──────────────────────┘

        Both guarantee:
          - safety: at most one value chosen per slot
          - liveness: progress with stable majority
          - correctness under up-to-(N-1)/2 failures
```

## Why interviewers care
- The comparison reveals whether you've *implemented* consensus or only *heard* of it.
- Talking about why Raft is teachable forces you to identify which Paxos design choices are *essential* and which are *historical*.
- It's a gateway to richer topics: EPaxos, Flexible Paxos, Compartmentalised Raft, BFT consensus.
- Engineers picking between consensus libraries (etcd, ZooKeeper, custom Multi-Paxos) need to justify the choice — and that justification is essentially this comparison.

## Common beginner confusion
- **"Paxos is older so it's the foundation."** Lamport showed the equivalence and Raft is provably as correct. Age does not imply primacy in implementation.
- **"Raft is slower because it serialises through a leader."** Multi-Paxos also serialises through a stable proposer. Throughput is similar in practice.
- **"Paxos handles partitions better."** Both require majority quorum; partition tolerance is identical.
- **"You can mix Paxos and Raft in one cluster."** Don't. Pick one. Mixing them defeats their invariants.
- **"Paxos is unsafe — Lamport wrote about it being unimplementable."** He wrote it was *hard to teach*. Practical Paxos has been deployed at Google (Chubby), Microsoft (Azure Storage), Yahoo (ZAB-derived).

## Brute force approach
"Pick whichever the team knows." Pragmatic but answer-less for the interview.

"Always pick Raft." Often correct, but you must justify *why*. The bullet-proof reasons: stronger leader, contiguous log, named election phase, better tooling (etcd, Raft visualisation), wider library availability.

## Optimal approach

In an interview, structure the comparison along five axes:

| Axis              | Paxos                        | Raft                          |
|-------------------|------------------------------|-------------------------------|
| Leader            | implicit (stable proposer)   | explicit, first-class         |
| Sequence number   | ballot (proposer-local)      | term (global)                 |
| Log               | may have holes               | contiguous                    |
| Election phase    | merged with Phase 1          | separate, named               |
| Teachability      | hard                         | easier (the paper's goal)     |
| Production libs   | Chubby, Spinnaker, internal  | etcd, Consul, TiKV, KRaft     |
| Geo-distribution  | EPaxos for leaderless        | Multi-Raft for sharding       |
| Membership change | reconfig protocol            | joint consensus               |

Then state the verdict: "For greenfield systems in 2026 I default to Raft via etcd or a similar library. I'd reach for Paxos variants only when EPaxos's leaderless geo-replication wins a specific latency requirement."

## Solution (algorithm + pseudocode + diagram)

### Side-by-side phase comparison

```
Single-decree Paxos (round-trip view)

  Proposer P                                Acceptor A,B,C
     │
     │ PREPARE(n=5)
     │ ────────────────────────────────────►
     │
     │   PROMISE(n=5, last_acc=(3, v_old))
     │ ◄────────────────────────────────────
     │
     │ ACCEPT(n=5, v=v_old or new)
     │ ────────────────────────────────────►
     │
     │   ACCEPTED(5, v)
     │ ◄────────────────────────────────────
     │
   choose(v) once majority accepted

Raft replication (round-trip view)

  Leader L                                  Followers
     │
     │ AppendEntries(term=5, prev=10,
     │   entries=[v], leaderCommit=10)
     │ ────────────────────────────────────►
     │
     │   ack
     │ ◄────────────────────────────────────
     │
   commit(v) at idx=11 once majority acks
```

Note: a *stable* Multi-Paxos run looks almost identical to Raft — Phase 1 is amortised across many decrees.

### When the logs diverge

```
Paxos may produce:
  Slot 10:  v_10 chosen
  Slot 11:  (still in flight, no decision)
  Slot 12:  v_12 chosen        ← hole at 11

Raft forbids this:
  Slot 10:  committed
  Slot 11:  pending             ← cannot commit 12 until 11 is committed
  Slot 12:  not yet replicated  (or replicated but not committed)
```

Paxos has to *fill* slot 11 later (the new leader proposes a no-op if 11 is undecided). Raft never has this branch.

### Pseudocode — Multi-Paxos stable proposer

```
state = { promised_ballot: 0, slots: {} }

proposer_loop:
  if not is_stable_proposer:
    run_phase1_for_all_undecided_slots()
    is_stable_proposer = true
  on client command c:
    slot = next_slot()
    send ACCEPT(ballot, slot, c) to acceptors
    when majority ack:
      slots[slot].decided = c
      reply client

acceptor on ACCEPT(b, s, v):
  if b >= promised_ballot:
    slots[s].accepted = (b, v)
    promised_ballot = max(promised_ballot, b)
    reply ACCEPTED
```

Compare to Raft leader: the structure is the same — one round-trip from leader to majority — but Raft enforces `slot = lastLogIdx + 1` strictly.

## Step-by-step dry run

**Scenario: 3-node cluster {A, B, C}; A is the current leader/proposer at term/ballot 5; client SET x=7.**

**Raft path:**

| Step | Actor | Action                                    | State        |
|------|-------|-------------------------------------------|--------------|
| 1    | client → A | SET x=7                               | log idx 11   |
| 2    | A     | append [T5 idx 11 SET x=7]                | uncommitted  |
| 3    | A → B, C | AppendEntries(term=5, prev=10, entries=[SET x=7]) | |
| 4    | B, C  | check prevLogIdx=10 matches local         | log ok       |
| 5    | B, C  | append, ack                               |              |
| 6    | A     | majority ack → commit idx 11              | x=7 applied  |
| 7    | A → client | OK                                    |              |

**Multi-Paxos path (stable proposer):**

| Step | Actor | Action                                    | State        |
|------|-------|-------------------------------------------|--------------|
| 1    | client → A | SET x=7                               | slot 11      |
| 2    | A     | pick slot 11 (next free)                  |              |
| 3    | A → B, C | ACCEPT(ballot=5, slot=11, v=SET x=7) |              |
| 4    | B, C  | b >= promised? yes → accept              |              |
| 5    | B, C  | ACCEPTED                                  |              |
| 6    | A     | majority ACCEPTED → decided                | x=7 applied  |
| 7    | A → client | OK                                    |              |

**Identical in steady state.** The differences emerge under failure:

**Failure scenario: A dies just after step 3.**

In Raft, B times out, becomes candidate at term 6, requests votes. Whichever of B/C has the most up-to-date log wins. The new leader's log is examined; if SET x=7 wasn't replicated to either, it's lost; if it was replicated to at least one (the winning candidate), it's preserved. New leader appends a no-op at term 6 to make its log entries up to idx 11 committable.

In Multi-Paxos, B initiates Phase 1 with ballot 6. It collects promises from B and C. If either reports `accepted=(5, SET x=7)` for slot 11, B must propose that value in Phase 2 for slot 11. Otherwise slot 11 is open and B can fill it with a no-op or a new value. Same outcome, more steps.

**Where Paxos diverges in non-trivial ways:**

```
Multi-Paxos:  slot 12 can be decided while slot 11 is still being recovered.
              Two concurrent proposers can race; the higher ballot wins eventually.

Raft:         slot 12 cannot be committed until slot 11 is committed.
              Only one leader at a time; no race possible.
```

## How to think aloud in the interview

"Raft and Paxos solve the same problem — distributed consensus on a log of values, tolerant to up to N/2 - 1 failures with majority quorum. The interesting question isn't 'which is correct' — both are. It's 'which is *teachable* and *implementable*', and that's where Raft won.

Concretely, Raft makes four explicit design choices that Paxos leaves flexible. First, *strong leader* — only the leader proposes, all others are followers; in Paxos any proposer can race. Second, *terms are global integers*; Paxos ballots are proposer-local pairs. Third, *the log is strictly contiguous* — Raft cannot commit slot 12 before 11; Paxos can. Fourth, *leader election is a named phase* — in Paxos it's implicit in completing Phase 1 successfully.

These restrictions don't change the safety guarantees; they constrain the state space. That's why Raft is easier to debug — fewer reachable states means fewer surprises. The cost is theoretical flexibility — Paxos variants like EPaxos exploit the looser constraints to achieve leaderless geo-distributed consensus, which Raft can't easily match.

In production in 2026, I default to Raft via etcd or Consul. The libraries are mature, the visualisations exist, the failure modes are well-documented. I'd reach for Paxos-derived systems — ZAB in ZooKeeper, EPaxos in research-grade deployments — only when I have a specific latency requirement that the leaderless or flexible-quorum variant solves.

One subtle point: in steady state, Multi-Paxos and Raft are operationally identical. The differences manifest only during leader change or partial failures. So when someone says 'we use Paxos' they almost always mean Multi-Paxos with a stable leader, which is one short conceptual hop from Raft."

## Important takeaways
- **Same problem, same safety, same fault tolerance.** Different exposition.
- **Raft = strong leader + contiguous log + explicit election.** These are *restrictions*, not features.
- **Paxos = more flexibility, harder to teach.** Multi-Paxos in practice resembles Raft.
- **In steady state they're identical.** Differences emerge during failures.
- **Pick Raft for greenfield projects in 2026** unless a specific Paxos variant solves a real constraint.
- **EPaxos and Flexible Paxos** are the modern reasons to consider non-Raft.
- **Ballot ≠ term, but functionally similar.**
- **Paxos allows log holes; Raft does not.** A common talking point.

## Variants
1. **EPaxos** — leaderless, conflict-aware, lower latency for geo-distributed writes.
2. **Flexible Paxos** — decouples Phase 1 and Phase 2 quorums for tunable trade-offs.
3. **Generalised Paxos** — allows commutative operations to commit out of order.
4. **ZAB (ZooKeeper Atomic Broadcast)** — Paxos-derived; ZooKeeper's internal protocol.
5. **Multi-Raft** — many Raft groups, one per key range (CockroachDB, TiKV).
6. **Compartmentalised Raft** — separates roles (proposer, voter, learner) to scale throughput.
7. **BFT consensus** — PBFT, Tendermint, HotStuff — Byzantine generalisations of the same idea.

## Revision notes

> **Raft vs Paxos — 60 second recap**
> - Same safety, same fault tolerance, same quorum.
> - Raft adds: strong leader, global term, contiguous log, named election.
> - Paxos: more flexible, ballot is local, log can have holes, election implicit in Phase 1.
> - In steady state they're indistinguishable; failures expose the differences.
> - Production 2026: default to Raft (etcd/Consul/KRaft).
> - Reach for EPaxos only for geo-distributed latency reasons.
> - **Trap:** claiming Paxos and Raft are different in safety. They aren't.
