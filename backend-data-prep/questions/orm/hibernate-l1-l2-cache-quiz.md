# Hibernate caches — L1, L2, query cache, when each is safe

## Source / Origin
- Hibernate User Guide §16 (Caching).
- Vlad Mihalcea, *High-Performance Java Persistence* — the definitive reference.
- The most misunderstood feature in the Hibernate ecosystem.

## Why this question matters in interviews
Hibernate's three caches are an interview goldmine because the **defaults are surprising** and the **failure modes are silent**. L1 (session) is always on; L2 (across sessions) is off by default; query cache is off by default and *requires* L2 to be useful. Senior engineers should know:
1. What each cache stores (entities vs query results).
2. The invalidation contract (and how raw SQL bypasses it).
3. When L2 is a win and when it's a memory bomb / staleness footgun.

If you can name `@Cacheable`, `CacheConcurrencyStrategy`, the regions, and explain why L2 is dangerous in a multi-writer environment, you sound senior. If you also know about the **query cache stampede** and why it's almost always wrong to enable, you sound senior+.

## Concepts involved

### The three caches

```
   ┌─────────────────────────────────────────────────────────────────┐
   │                          APPLICATION                            │
   │  ┌─────────────────┐    ┌─────────────────┐                     │
   │  │   Session A     │    │   Session B     │                     │
   │  │  ┌──────────┐   │    │  ┌──────────┐   │                     │
   │  │  │  L1      │   │    │  │  L1      │   │  L1 = identity map  │
   │  │  │  (id-map)│   │    │  │  (id-map)│   │  per-session,        │
   │  │  └──────────┘   │    │  └──────────┘   │  always on           │
   │  └────────┬────────┘    └────────┬────────┘                     │
   │           │                      │                              │
   │  ┌────────▼──────────────────────▼─────────┐                    │
   │  │              L2 CACHE                   │ L2 = per-SF,        │
   │  │   region: User → {1: User#1, ...}       │ across sessions,    │
   │  │   region: Order → {99: Order#99, ...}   │ off by default      │
   │  └────────────┬────────────────────────────┘                    │
   │               │                                                 │
   │  ┌────────────▼─────────────┐                                   │
   │  │    QUERY CACHE           │ key = JPQL+bind params            │
   │  │    "SELECT u WHERE..."   │ value = list of entity IDs        │
   │  │      → [1, 5, 9]         │ requires L2 to resolve            │
   │  └──────────────────────────┘                                   │
   └─────────────────────────────────────────────────────────────────┘
```

### Syntax to lock in

```java
// Enable L2 cache for User entity
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class User { ... }

// application.yml
spring.jpa.properties.hibernate.cache.use_second_level_cache: true
spring.jpa.properties.hibernate.cache.use_query_cache: true
spring.jpa.properties.hibernate.cache.region.factory_class: org.hibernate.cache.jcache.JCacheRegionFactory
spring.jpa.properties.hibernate.javax.cache.provider: org.ehcache.jsr107.EhcacheCachingProvider

// Use query cache
List<User> users = em.createQuery("SELECT u FROM User u WHERE u.active = true", User.class)
        .setHint("org.hibernate.cacheable", true)
        .getResultList();
```

### Cache concurrency strategies

| Strategy | Use when | Cost |
|---|---|---|
| `READ_ONLY` | Reference data (countries, currencies) | Cheapest; can't update |
| `NONSTRICT_READ_WRITE` | Rare writes, brief staleness OK | Invalidates on commit, no locking |
| `READ_WRITE` | Frequent writes, no cluster | Soft locks during writes |
| `TRANSACTIONAL` | JTA + distributed cache | Slow, expensive |

### Edge cases / interview traps

1. **L1 is mandatory.** You can't turn it off. It IS the session's identity map.
2. **L2 invalidation only happens through Hibernate.** A raw `UPDATE users SET ...` via JDBC or another app bypasses L2 → stale reads forever (until manual eviction).
3. **`em.refresh(user)`** evicts that entity from L1 and re-reads from DB. Does **not** evict from L2 — `sessionFactory.getCache().evict(User.class, 1L)` does.
4. **Query cache stores IDs**, not full entities. Without L2 enabled for the entity, every query-cache hit fires N SELECTs by ID to resolve. Worse than no cache.
5. **Query cache invalidation** = any write to any row of any table referenced by the query invalidates the entire region. One UPDATE blows away cached queries that referenced even unrelated rows.
6. **`SELECT count(*)`** can't use query cache effectively in most scenarios — too invalidation-prone.
7. **`@NaturalIdCache`** is the underrated cousin — caches lookups by a unique business key (email, slug).
8. **Distributed L2** (Infinispan, Hazelcast) avoids single-node staleness but adds latency on every miss.
9. **`StatelessSession`** has no L1 — useful for bulk operations; loses identity map and dirty checking.
10. **`@Cache(region = "...")` partitioning** — different regions can have different eviction/TTL policies.

## Mental Model

**L1** is your scratchpad inside one session. It's there to prevent the same `find(User, 1)` from issuing 2 SELECTs in one request.

**L2** is a shared between-session cache. It's a *bet* that the same entity will be read by many sessions and that no one outside Hibernate will write to it.

**Query cache** is a shortcut from "JPQL + params" to "list of IDs". The IDs then hit L2 (or fall back to DB). It's a cache for **query plans + result-set IDs**, not for entity state.

The crucial mental switch: L2 is **per-entity**, query cache is **per-query**. Their invalidation contracts are different and one doesn't imply the other.

## Why interviewers care

- Defaults are surprising → reveals whether you've configured Hibernate in production or only read the tutorial.
- Invalidation contract is non-obvious → reveals whether you've debugged stale-cache bugs.
- Trade-offs are real → reveals whether you can argue *against* turning on a cache.

## Common beginner confusion

- "L2 is always on." It's off by default.
- "Query cache is independent of L2." It's not — query cache stores IDs that must resolve via L2 or DB.
- "L2 will save me from N+1." It won't — N+1 is N round-trips of `findById`; L2 only helps if those entities are already cached, and on cold cache the first request still does N round-trips.
- "I can mix raw SQL freely with L2 on." No. Raw writes bypass L2 invalidation. Either disable L2 for that entity or evict manually.

## Brute force approach

Enable L2 + query cache on every entity. Then watch:
- Memory balloons (entire User table in cache).
- Stale data when an admin tool updates rows directly.
- The query cache hit rate is 2% because invalidation thrashes.
- A 10x DB load when the cache expires en masse and a stampede hits the DB.

## Optimal approach

Three rules:

1. **L1: leave on, never close-and-reopen mid-request.**
2. **L2: enable per-entity, only for reference data or read-mostly entities you fully own.** Use `READ_ONLY` if possible.
3. **Query cache: avoid unless you have proven hit rate.** When you do use it, restrict to (a) keyed by stable params, (b) referencing entities that are L2-cached and rarely-mutated.

For natural-key lookups (`findByEmail`), prefer `@NaturalIdCache` over query cache.

## Solution

### Entity-level L2

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(
    usage = CacheConcurrencyStrategy.READ_WRITE,
    region = "user_cache")
@NaturalIdCache(region = "user_naturalid_cache")
public class User {
    @Id Long id;
    @NaturalId @Column(unique = true) String email;
    @Column String name;
}

// fast lookup via natural-id cache
User u = session.byNaturalId(User.class)
    .using("email", "a@x.com")
    .load();
```

### Query cache, with care

```java
List<Country> countries = em.createQuery("FROM Country ORDER BY code", Country.class)
        .setHint("org.hibernate.cacheable", true)
        .setHint("org.hibernate.cacheRegion", "country_list")
        .getResultList();
```

Region `country_list` should have a long TTL because countries change rarely; invalidation will be near-zero.

### Manual eviction when bypassing Hibernate

```java
// Admin tool issued a raw UPDATE — sync the L2 cache.
sessionFactory.getCache().evictEntityData(User.class, 1L);
sessionFactory.getCache().evictQueryRegion("country_list");
```

### Stateless session for bulk

```java
StatelessSession ss = sessionFactory.openStatelessSession();
Transaction tx = ss.beginTransaction();
try (Stream<User> stream = ss.createQuery("FROM User", User.class).stream()) {
    stream.forEach(this::reindex);
}
tx.commit();
ss.close();
// No L1, no L2 interaction, no dirty checking — minimal memory.
```

### Ehcache config (XML)

```xml
<config xmlns="http://www.ehcache.org/v3">
  <cache alias="user_cache">
    <expiry><ttl unit="seconds">300</ttl></expiry>
    <heap unit="entries">10000</heap>
  </cache>
  <cache alias="user_naturalid_cache">
    <expiry><ttl unit="seconds">300</ttl></expiry>
    <heap unit="entries">10000</heap>
  </cache>
</config>
```

## Step-by-step dry run

### Scenario: User entity, L2 enabled, query cache enabled

```
SESSION A:
  s.get(User, 1)
    L1 miss → L2 miss → DB SELECT → load User#1 into L1 + L2
  s.get(User, 1)
    L1 HIT → no SQL

SESSION B (concurrent):
  s.get(User, 1)
    L1 miss → L2 HIT → User#1 hydrated from L2 → no SQL ✓

SESSION C:
  s.createQuery("FROM User WHERE active=true").setHint("cacheable", true).getResultList()
    Query cache miss → DB SELECT → [1, 5, 9]
    For each id: L2 HIT → no SQL ✓
    Cache the IDs [1, 5, 9] in the query region.

SESSION D (some time later):
  same query
    Query cache HIT → IDs [1, 5, 9]
    L2 HITs → 0 SQL ✓

SESSION E:
  UPDATE User#5: u.setName("...") then commit
    L2 invalidates User#5
    Query cache for "FROM User WHERE active=true" — invalidates ENTIRE User query region
    (because Hibernate doesn't know which queries would be affected)

ADMIN VIA RAW JDBC:
  UPDATE users SET name='X' WHERE id=7
    L2 NOT invalidated → SESSION F reading User#7 will see stale name
    Must call sessionFactory.getCache().evictEntityData(User.class, 7L) manually
```

### Stampede on TTL expiry

```
T=0     Cache populated; 1000 sessions/sec hitting L2 → 0 SQL
T=300   TTL expires for User#1 in L2
T=300.0 1000 sessions miss L2 simultaneously → 1000 concurrent SELECTs → DB load spike

Mitigation: stagger TTLs, use refresh-ahead, or accept staleness with NONSTRICT_READ_WRITE.
```

## How to think aloud in the interview

> "Three caches, three contracts:
>
> 1. **L1 / session cache** — the identity map. Always on. Per-session. Closes when the session closes.
>
> 2. **L2 / second-level cache** — across sessions, per-entity. Off by default. You enable with `@Cacheable` + a region factory like Ehcache or Infinispan. Concurrency strategy matters: `READ_ONLY` for reference data, `READ_WRITE` for mutable. The contract: invalidation only happens through Hibernate. Raw SQL or another app writing to the same DB → stale forever until manual eviction.
>
> 3. **Query cache** — JPQL + params → list of IDs. Off by default. Useless without L2 (you'd just round-trip per ID). Invalidates aggressively: any write to a referenced table blows the whole region. Hit rate is usually disappointing.
>
> My defaults:
> - L1: leave alone.
> - L2: enable for reference data (countries, currencies, role definitions) with `READ_ONLY`. Maybe for read-mostly entities I fully own.
> - Query cache: skip unless I have data showing positive hit rate.
> - `@NaturalIdCache` for email/slug lookups — better than query cache for that shape.
>
> Trap I always raise: shared DB with another app means L2 is risky. Trap two: cache stampede on TTL — need staggered expiry."

## Important takeaways

- **L1** = session identity map; always on; per-session.
- **L2** = per-SessionFactory, per-entity; off by default; only invalidated via Hibernate.
- **Query cache** = per-query result IDs; requires L2; aggressive invalidation; rarely worth it.
- **`@NaturalIdCache`** is the underrated win for lookup-by-unique-key.
- **Raw SQL bypasses L2** — manual eviction or disable L2 for the affected entity.
- **`StatelessSession`** for bulk: no L1, no dirty tracking, no L2 hydration overhead.
- **Concurrency strategy matters**: READ_ONLY → cheapest, READ_WRITE → standard, TRANSACTIONAL → only with JTA.
- **Stampedes** on TTL expiry — stagger or use refresh-ahead.

## Variants

1. **"Can L2 work with multiple JVMs?"** Yes via distributed cache (Infinispan, Hazelcast). Adds network on miss; helps on hit. Invalidation propagates via cluster messaging.
2. **"How do you handle cache when running migrations?"** Evict everything (`sessionFactory.getCache().evictAll()`) after migration, or restart the app.
3. **"What's the difference between `evict()` and `clear()` on a session?"** `evict(entity)` removes one from L1. `clear()` empties L1.
4. **"Why don't queries by ID hit the query cache?"** They don't go through JPQL — they're entity-load paths and use L1 → L2 → DB directly. Query cache is only for JPQL/Criteria queries explicitly marked cacheable.
5. **"What's the per-region statistics API?"** `sessionFactory.getStatistics()` exposes hit/miss/put counts per region. Monitor before enabling more caching.

## Revision notes

> **hibernate-cache — 60 second recap**
> - L1 = session identity map. Always on. Per-session.
> - L2 = across sessions, per-entity. Off by default. `@Cacheable` + region factory.
> - Query cache = JPQL+params → IDs. Off by default. Useless without L2.
> - Strategies: READ_ONLY (cheapest), READ_WRITE (standard), TRANSACTIONAL (JTA).
> - **Raw SQL bypasses L2** → stale; manual evict.
> - Query cache invalidates aggressively (whole region) on any referenced-table write.
> - `@NaturalIdCache` for unique-business-key lookups — often better than query cache.
> - `StatelessSession` = no L1, no dirty tracking; for bulk.
> - **Trap:** stampedes on TTL expiry; stagger or refresh-ahead.
