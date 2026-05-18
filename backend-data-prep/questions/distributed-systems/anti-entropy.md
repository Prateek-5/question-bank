# Anti-entropy with Merkle trees: background reconciliation across replicas

## Source / Origin
- Demers et al. (1987) anti-entropy theory; Merkle (1979) hash tree.
- Production: Dynamo, Cassandra `nodetool repair`, Riak AAE, ZFS scrub.
- Concept reference: `backend-data-prep/distributed-systems/eventual-consistency.md`.

## Why this question matters in interviews
Anti-entropy is the answer to "cold keys that were never re-read after a missed write — how do you ever fix them?" If you can draw a Merkle tree, explain how two replicas exchange root hashes and recurse into mismatched subtrees, and why that's O(log N) bandwidth instead of O(N), you signal you understand background reconciliation at scale.

## Concepts involved

### Syntax / mechanism to lock in

```
Merkle tree:
  Leaves   = hash(key, value) for each key in a partition range.
  Internal = hash(left_child_hash || right_child_hash).
  Root     = hash of all data in the partition.

Reconciliation:
  Replica A sends root hash to replica B.
  If equal → no divergence in this range. Done. O(1) bandwidth.
  If different → exchange child hashes.
     For each mismatched child → recurse.
  Eventually identify the leaf keys that differ → reconcile those.

Bandwidth = O(d · log N) where d = number of divergent keys.
```

### Edge cases / interview traps

1. **Merkle tree rebuild is expensive.** Cassandra rebuilds at start of repair; takes minutes-hours for big nodes.
2. **Tree must be deterministic** across replicas — same hash function, same key ordering, same range partitioning.
3. **Repair sessions are heavy.** Cassandra's `nodetool repair -pr` repairs only the primary range to avoid double work.
4. **Tombstones** must be included in the hash; otherwise deleted keys "come back" after repair.
5. **Repair must complete within `gc_grace_seconds`** in Cassandra, or zombie data appears.
6. **Incremental repair** marks repaired SSTables to avoid re-repairing the same data.
7. **Streaming bandwidth** caps how fast repair runs; can saturate links and cause read latency spikes.

## Mental Model

Imagine two librarians comparing entire bookshelves. Naively, they check every book — O(N). With Merkle hashes, they first compare a single hash that summarises a whole shelf. If shelves match, skip. If different, drill in: compare hashes of half-shelves, then quarter-shelves, until they identify the few books that differ. Bandwidth proportional to differences, not catalogue size.

```
Merkle tree (4 keys per replica, shown only here as conceptual):

                root_h
              /        \
          h_AB          h_CD
         /    \        /    \
       h_A   h_B     h_C   h_D
        |     |       |     |
       k1    k2      k3    k4

Replica A and B exchange root_h.
  If equal → all 4 keys identical. Stop.
  If different:
    Compare h_AB and h_CD between the two replicas.
    Recurse into mismatched subtree.
    Find that, say, h_C differs → key k3 needs reconciliation.

Bandwidth: O(log N) per diff key vs O(N) naive.
```

## Why interviewers care
- Tests understanding of background reconciliation at scale.
- Reveals knowledge of Cassandra repair internals, Dynamo AAE, Riak AAE.
- Distinguishes anti-entropy from read-repair and hinted handoff.

## Common beginner confusion
- "Anti-entropy is real-time." It's a *background* job, run periodically (Cassandra: weekly).
- "It's the same as hinted handoff." Hints are a short-outage primitive; AE catches *anything* hints missed.
- "Merkle tree is for cryptographic verification." That too, but here it's for efficient diff.
- "Repair compares every key." Only when the entire tree differs; otherwise prunes most of the tree.

## Brute force approach

Periodically scan every key in every partition and compare across replicas. O(N) bandwidth per repair. Dies on TB-scale partitions.

## Optimal approach

Build a Merkle tree per partition range, exchange roots, recurse only into mismatched subtrees. Stream the actually-different keys between replicas. Incremental repair caches "this range is already reconciled" to avoid redoing work.

## Solution

```python
import hashlib

def leaf_hash(key, value, ts):
    return hashlib.sha256(f"{key}|{value}|{ts}".encode()).digest()

def build_merkle(sorted_kvs):
    """sorted_kvs: list of (key, value, ts) sorted by key."""
    nodes = [leaf_hash(k, v, t) for k, v, t in sorted_kvs]
    tree = [nodes]
    while len(nodes) > 1:
        if len(nodes) % 2: nodes.append(nodes[-1])  # duplicate last
        nodes = [hashlib.sha256(nodes[i] + nodes[i+1]).digest()
                 for i in range(0, len(nodes), 2)]
        tree.append(nodes)
    return tree                                       # tree[-1] = [root]

def diff(treeA, treeB, depth=None):
    """Return indices of differing leaves."""
    depth = depth or len(treeA) - 1
    if treeA[depth] == treeB[depth]:
        return []
    if depth == 0:
        return [i for i in range(len(treeA[0]))
                if treeA[0][i] != treeB[0][i]]
    diffs = []
    for i in range(len(treeA[depth])):
        if treeA[depth][i] != treeB[depth][i]:
            # recurse into children at depth-1
            lo, hi = i * (2 ** depth), (i + 1) * (2 ** depth)
            diffs.extend(j for j in range(lo, min(hi, len(treeA[0])))
                         if treeA[0][j] != treeB[0][j])
    return diffs
```

Cassandra-style repair driver:

```bash
# repair only primary range of this node, parallel streaming
nodetool repair -pr -par -j 4

# incremental repair: only newly-written SSTables
nodetool repair -inc

# repair a single keyspace
nodetool repair my_ks -pr
```

## Step-by-step dry run

4 keys in a partition; replicas A and B differ only on k3.

```
Replica A data:                     Replica B data:
  k1=v1@10  → h_A1                     k1=v1@10  → h_B1
  k2=v2@12  → h_A2                     k2=v2@12  → h_B2
  k3=v3@15  → h_A3                     k3=v3'@9  → h_B3   ← stale
  k4=v4@11  → h_A4                     k4=v4@11  → h_B4

Trees:
                rootA = H(h_AB || h_CD)
              /                       \
        H(h_A1||h_A2)             H(h_A3||h_A4)
        /          \              /          \
      h_A1        h_A2          h_A3        h_A4

Step 1: Exchange rootA, rootB.
        Differ → recurse.

Step 2: Exchange children of root.
        Left subtree hash: A and B equal (k1,k2 same on both).
        Right subtree hash: A and B differ.

Step 3: Recurse into right subtree.
        h_A3 vs h_B3: differ.
        h_A4 vs h_B4: equal.

Step 4: Identified divergent leaf: k3.
        Compare timestamps: A has ts=15, B has ts=9.
        A streams k3=v3@15 → B applies.

Bandwidth: 7 hashes exchanged + 1 key transferred. vs naive: 4 full key/value pairs.
For 1M-key partition with 10 diffs, savings are dramatic.
```

## How to think aloud in the interview

> "Anti-entropy reconciles long-term replica divergence using Merkle trees. Each replica builds a tree over its partition: leaves are hashes of (key, value, timestamp); internal nodes hash their children; root summarises all data. Replicas exchange roots; if equal, no work. If different, recurse into mismatched subtrees, identify the few divergent leaves, and reconcile those.
>
> Bandwidth is O(d log N) where d is the number of divergent keys, vs O(N) for naive scan. For million-key partitions with rare divergence, that's a huge win.
>
> Anti-entropy is the third leg of the Dynamo durability tripod: hinted handoff for short outages, read repair for fresh reads, anti-entropy for cold-key divergence. Cassandra's `nodetool repair` is the canonical implementation. Beware: must complete within `gc_grace_seconds` or tombstones come back as zombies."

## Important takeaways
- Merkle tree hashes a partition into a single root; recurse on mismatch.
- O(d log N) bandwidth — efficient when divergence is rare.
- Background job, not real-time; weekly or after node return.
- Must include tombstones; must finish before GC grace.
- Cassandra: incremental repair caches "already repaired" markers.
- Combine with hinted handoff (short outage) and read repair (live reads).

## Variants
1. **Incremental repair** (Cassandra) — only repair SSTables flushed since last repair.
2. **Subrange repair** — repair small key ranges to avoid long-running sessions.
3. **Continuous AAE** (Riak) — background full-disk Merkle scan + diff.
4. **AAE with Bloom filters** — quick filter before full Merkle comparison.
5. **Hash-based AAE for sets** (e.g., HLL) — probabilistic, less precise.

## Revision notes

> **anti-entropy — 60 second recap**
> - Merkle tree per partition; root summarises all data.
> - Exchange roots; recurse only into mismatched subtrees → O(d log N).
> - Background; complements hinted handoff and read repair.
> - Cassandra `nodetool repair`; must finish within gc_grace_seconds.
> - Include tombstones; otherwise zombie deletes.
> - Incremental repair = skip already-repaired SSTables.
