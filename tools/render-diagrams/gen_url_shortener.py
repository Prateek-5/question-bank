#!/usr/bin/env python3
"""Regenerate all 7 URL_Shortener .excalidraw files using excalidraw_gen library.

Output: HLD/diagrams/URL_Shortener/URL_Shortener_Design/<name>.excalidraw
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from excalidraw_gen import (
    box, ellipse, arrow, composes, aggregates, uses,
    title, note, divider, callout, flatten, save,
    sequence_lane, sequence_msg,
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO_ROOT, "HLD", "diagrams", "URL_Shortener", "URL_Shortener_Design")
os.makedirs(OUT, exist_ok=True)


# ─── 1. data-model.excalidraw ───────────────────────────────────────────────
def gen_data_model():
    els = []
    els += title("Data model — url_mappings",
                 subtitle="One table. Two writes per second average. Thirty-thousand reads per second peak. "
                          "Every architecture choice falls out of this asymmetry.")

    tbl = box(
        "url_mappings\n\n"
        "short_code         char(7)      PRIMARY KEY      ← 7-char base62\n"
        "long_url           varchar(2048)  NOT NULL\n"
        "user_id            uuid           nullable        ← FK → identity svc\n"
        "created_at         timestamptz    NOT NULL\n"
        "expires_at         timestamptz    nullable        ← NULL = no expiry\n"
        "is_custom_alias    bool           default false",
        role="storage", x=80, y=160, w=820, h=240, font_size=14)
    els += tbl.elements

    idx = callout(
        "Indexes:\n"
        "  • PK on short_code           — every redirect uses this\n"
        "  • INDEX on user_id            — \"list my URLs\"\n"
        "  • PARTIAL INDEX on expires_at WHERE expires_at IS NOT NULL  — TTL sweep",
        x=80, y=440, w=820, h=130,
        bg="#fff3bf", stroke="#e67700", font_size=13)
    els += idx

    ap = callout(
        "Access patterns (the only thing that matters):\n\n"
        "READ:    SELECT long_url WHERE short_code = ?    ~30K/sec   <5ms p99\n"
        "WRITE:   INSERT INTO url_mappings (...)           ~40/sec    <50ms\n"
        "LIST:    SELECT WHERE user_id = ? LIMIT 50        rare        <200ms\n"
        "SWEEP:   DELETE WHERE expires_at < now()           periodic    bg",
        x=80, y=600, w=820, h=190,
        bg="#d3f9d8", stroke="#2f9e44", font_size=13)
    els += ap

    els += note(
        "The 100:1 read:write asymmetry IS the design constraint.\n"
        "Everything downstream (cache thickness, replica count, write-path complexity) derives from it.",
        x=80, y=820, color="#868e96", size=13)

    save(os.path.join(OUT, "data-model.excalidraw"), els)


# ─── 2. iteration-1-naive.excalidraw ────────────────────────────────────────
def gen_iteration_1_naive():
    els = []
    els += title("Iteration 1 — naive: single Postgres + single app",
                 subtitle="Where does this break at 30K reads/sec peak?")

    # Use wider vertical spacing so arrow labels have clear room between boxes
    client = box("Client\n(browser)", role="actor", x=480, y=140, w=200, h=80)
    api    = box("API server\n(single Node.js instance)\n\n~3K RPS sustained",
                 role="warning", x=460, y=340, w=240, h=120)
    db     = box("Primary DB (Postgres)\n\n~5K reads/sec ceiling\nfor full-row lookups",
                 role="storage", x=460, y=560, w=240, h=120)
    els += flatten(client, api, db)

    # Auto-position labels (perpendicular to vertical arrows = label to the right)
    els += arrow(client.bottom(), api.top(), label="HTTPS  GET /:code")
    els += arrow(api.bottom(),    db.top(),  label="SELECT long_url WHERE code = ?")

    # Annotations on the right — align with their corresponding boxes
    els += callout(
        "⚠ One app instance saturates around 3K RPS\n"
        "    (CPU-bound on request parsing + cache misses).",
        x=760, y=340, w=400, h=80,
        bg="#ffc9c9", stroke="#c92a2a", font_size=13)
    els += callout(
        "⚠ Postgres maxes ~5K reads/sec for full-row\n"
        "    SELECTs on a hot table.",
        x=760, y=560, w=400, h=80,
        bg="#ffc9c9", stroke="#c92a2a", font_size=13)

    els += callout(
        "Capacity check (from §6):\n"
        "  Target:       30,000 reads/sec peak\n"
        "  This design:   3,000 (app)  ·  5,000 (DB)\n"
        "  → BREAKS by 6–10× before we approach target.",
        x=80, y=760, w=560, h=160,
        bg="#fff9db", stroke="#fab005", font_size=14)
    els += callout(
        "Pivot question:\n"
        "Where's the read amplification?\n"
        "→ Most reads hit the SAME hot keys.\n"
        "→ We can CACHE them.  (Iteration 2)",
        x=680, y=760, w=480, h=160,
        bg="#d3f9d8", stroke="#2f9e44", font_size=14)

    save(os.path.join(OUT, "iteration-1-naive.excalidraw"), els)


# ─── 3. iteration-2-with-cache.excalidraw ───────────────────────────────────
def gen_iteration_2():
    els = []
    els += title("Iteration 2 — add Redis cache in front",
                 subtitle="Reaches 30K reads/sec. But hot keys, cache stampede, and the single API server still hurt.")

    client = box("Client", role="actor", x=480, y=140, w=200, h=60)
    api    = box("API server\n+ cache-aside logic\n  (Redis first, DB on miss)",
                 role="concrete", x=440, y=240, w=280, h=120)
    redis  = box("Redis Cluster\n(per-region cache)\n\n~100K ops/sec/shard",
                 role="cache", x=80, y=420, w=280, h=140)
    db     = box("Primary DB (Postgres)\n\nDB load now ~20% of reads\n(cache miss rate)",
                 role="storage", x=800, y=420, w=280, h=140)
    els += flatten(client, api, redis, db)

    els += arrow(client.bottom(), api.top(), label="GET /:code")
    els += arrow(api.bottom(), redis.top(),
                 label="1. GET code", color="#a61e4d", label_offset=(0, -16))
    els += arrow(api.bottom(), db.top(),
                 label="2. MISS → DB", label_offset=(0, -16))

    els += callout(
        "✓ Reads served by Redis hit our 30K target.\n"
        "✓ DB load drops ~5× (cache miss rate ≈ 20%).",
        x=80, y=600, w=540, h=100,
        bg="#d3f9d8", stroke="#2f9e44", font_size=14)

    els += callout(
        "⚠ Hot keys: one viral link can saturate one Redis shard.\n"
        "⚠ Cache stampede on cold start: all instances hit DB simultaneously.\n"
        "⚠ Single API instance still a bottleneck → need LB + replicas.\n"
        "⚠ No async write path → analytics blocks the redirect.",
        x=640, y=600, w=520, h=160,
        bg="#ffc9c9", stroke="#c92a2a", font_size=13)

    els += callout(
        "Pivot: split the load, distribute the hot keys, decouple analytics.\n"
        "→ Add CDN (extreme hot keys), LB + replicas (horizontal scale), Kafka (async).",
        x=80, y=780, w=1080, h=80,
        bg="#fff9db", stroke="#fab005", font_size=14)

    save(os.path.join(OUT, "iteration-2-with-cache.excalidraw"), els)


# ─── 4. final-architecture.excalidraw ───────────────────────────────────────
def gen_final_architecture():
    els = []
    els += title("§10.C — Final architecture",
                 subtitle="Read tier: client → CDN → LB → API → Redis → DB.  "
                          "Write tier: same path, plus Counter alloc + Blocklist on create.  "
                          "Side channels: Kafka for click events + DB CDC, three consumers downstream.")

    # Layout: tall vertical stack with side services in their own ROWS (not jammed
    # alongside the API fleet) so arrow labels have clean space.
    #
    #  Row 1   ───────  Client
    #  Row 2   ───────  DNS  +  CDN
    #  Row 3   ───────  Load Balancer
    #  Row 4   ───────  API fleet (3 instances)
    #  Row 5   ───────  Counter Alloc          Blocklist          (side services — own row)
    #  Row 6   ───────  Redis  +  Primary DB
    #  Row 7   ───────  Kafka
    #  Row 8   ───────  3 consumers

    # Legend lives in its own top row (y=80-220) so nothing else shares its space.
    # All other rows shift DOWN by 160px to make room for it.
    Y = {
        "legend":    100,
        "client":    280,
        "dns_cdn":   400,
        "lb":        520,
        "api":       640,
        "side":      780,
        "cache_db":  920,
        "kafka":    1080,
        "consumer": 1200,
    }
    client = box("Client (browser)", role="actor", x=720, y=Y["client"], w=240, h=60, font_size=14)
    dns = box("Anycast DNS\n(routes to nearest POP)", role="concrete", x=340, y=Y["dns_cdn"], w=280, h=80, font_size=13)
    cdn = box("CDN / Edge\n(302 cached for popular codes)", role="cache", x=720, y=Y["dns_cdn"], w=320, h=80, font_size=13)
    lb = box("Load Balancer (L7)\n(per-region, health-checked)", role="concrete", x=700, y=Y["lb"], w=360, h=80, font_size=13)
    # API fleet — three side-by-side in their own row
    api1 = box("API svc 1", role="impl", x=520, y=Y["api"], w=160, h=80, font_size=13)
    api2 = box("API svc 2", role="impl", x=720, y=Y["api"], w=160, h=80, font_size=13)
    api3 = box("API svc N\n(stateless, autoscale)", role="impl", x=920, y=Y["api"], w=200, h=80, font_size=13)
    # Side services in their own row — well below the API fleet
    counter   = box("Counter Alloc\n(Zookeeper)\nblock-allocates IDs",
                    role="process", x=100, y=Y["side"], w=240, h=100, font_size=13)
    blocklist = box("Validation /\nBlocklist Svc",
                    role="process", x=1200, y=Y["side"], w=240, h=100, font_size=13)
    redis = box("Redis Cluster\n(consistent-hashed)\n~16 shards × 5GB",
                role="cache", x=480, y=Y["cache_db"], w=280, h=110, font_size=13)
    db    = box("Primary DB\n(Postgres or Cassandra)\nasync replicate region B/C",
                role="storage", x=880, y=Y["cache_db"], w=340, h=110, font_size=13)
    kafka = box("Kafka  (click events + DB CDC)", role="async",
                x=680, y=Y["kafka"], w=400, h=80, font_size=14)
    analytics = box("Analytics → Cassandra\n(time-series clicks)",
                    role="process", x=240, y=Y["consumer"], w=280, h=80, font_size=13)
    sweeper   = box("TTL Sweeper\n(deletes expired)",
                    role="process", x=620, y=Y["consumer"], w=280, h=80, font_size=13)
    rescan    = box("Anti-abuse rescan\n(consumes CDC)",
                    role="process", x=1000, y=Y["consumer"], w=280, h=80, font_size=13)

    els += flatten(client, dns, cdn, lb, api1, api2, api3,
                   counter, blocklist, redis, db, kafka,
                   analytics, sweeper, rescan)

    # Top-level downward flow (mostly vertical — auto label-position offset goes to the right)
    els += arrow(client.bottom(), cdn.top(), label="HTTPS")
    els += arrow(dns.right(), cdn.left(), label="POP", dashed=True)
    els += arrow(cdn.bottom(), lb.top(), label="miss → origin")
    # LB fans out to API fleet — three arrows, no labels (the fan-out shape conveys it)
    els += arrow(lb.bottom(), api1.top())
    els += arrow(lb.bottom(), api2.top())
    els += arrow(lb.bottom(), api3.top())
    # API → cache, DB (api2 is the central one we trace)
    els += arrow(api2.bottom(), redis.top(), color="#a61e4d", label="GET code")
    els += arrow(api2.bottom(), db.top(),    label="SELECT")
    # API → side services: route from the END of the API row, no labels (arrows alone are clear)
    els += arrow(api1.bottom(), counter.top(), dashed=True, color="#fab005",
                 waypoints=[(api1.cx() - 80, Y["side"] - 30)])
    els += arrow(api3.bottom(), blocklist.top(), dashed=True, color="#fab005",
                 waypoints=[(api3.cx() + 80, Y["side"] - 30)])
    # DB → Kafka (CDC) — no label; orange-dashed style + DB-to-Kafka context is clear enough
    els += arrow(db.bottom(), kafka.top(), color="#e8590c", dashed=True)
    # API → Kafka (click events, async)
    els += arrow(api2.bottom(), kafka.top(), color="#e8590c", dashed=True,
                 waypoints=[(api2.cx() - 100, Y["kafka"] - 40)])
    # Kafka → 3 consumers (no labels — the orange-dashed pattern + 3-way fan-out conveys async)
    els += arrow(kafka.bottom(), analytics.top(), color="#e8590c", dashed=True)
    els += arrow(kafka.bottom(), sweeper.top(),   color="#e8590c", dashed=True)
    els += arrow(kafka.bottom(), rescan.top(),    color="#e8590c", dashed=True)

    # Legend — top header row, full-width, in its own dedicated band (Y["legend"])
    els += callout(
        "Color legend  —   "
        "Blue solid: sync redirect path  ·  "
        "Pink: cache (Redis)  ·  "
        "Indigo: durable storage (DB)  ·  "
        "Orange dashed: async / fire-and-forget (clicks, CDC, consumers)  ·  "
        "Yellow: stateful side-services",
        x=80, y=Y["legend"], w=1360, h=100,
        bg="#fff9db", stroke="#fab005", font_size=13)

    save(os.path.join(OUT, "final-architecture.excalidraw"), els)


# ─── 5. sequence-shorten.excalidraw ─────────────────────────────────────────
def gen_sequence_shorten():
    els = []
    els += title("Sequence — POST /shorten  (create flow)",
                 subtitle="Counter is touched only when an instance's block runs out. "
                          "Cache is SEEDED on create so the first redirect is fast.")
    lanes = [
        ("User",       100, "actor"),
        ("API",        260, "concrete"),
        ("Blocklist",  430, "process"),
        ("Counter",    600, "process"),
        ("DB",         770, "storage"),
        ("Redis",      940, "cache"),
    ]
    lane_x = {}
    for name, x, role in lanes:
        lane_elems, lx = sequence_lane(name, x, role=role, top_y=140, bottom_y=860)
        els.extend(lane_elems)
        lane_x[name] = lx

    msgs = [
        ("User",      "API",       210, "1: POST {long_url}",              False, False),
        ("API",       "Blocklist", 270, "2: check(long_url)",              False, False),
        ("Blocklist", "API",       330, "3: → ok / blocked",               True,  False),
        ("API",       "Counter",   390, "4: allocId()  [from preallocated block]", False, False),
        ("Counter",   "API",       450, "5: → id = 421337",                True,  False),
        ("API",       "API",       510, "6: code = base62(421337) = 'abc1234'", False, False),
        ("API",       "DB",        570, "7: INSERT (abc1234, long_url, ...)", False, False),
        ("DB",        "API",       630, "8: → OK",                         True,  False),
        ("API",       "Redis",     690, "9: SET cache TTL 24h",            False, True),
        ("API",       "User",      770, "10: 201 Created { short: '/abc1234' }", True, False),
    ]
    for src, dst, y, lbl, ret, asyn in msgs:
        if src == dst:
            # self-message — small arc to the right
            els.extend(arrow((lane_x[src], y), (lane_x[src] + 40, y + 8),
                             label=lbl, color="#e8590c",
                             label_offset=(60, -16)))
        else:
            els.extend(sequence_msg(lane_x[src], lane_x[dst], y, lbl, is_return=ret, is_async=asyn))

    save(os.path.join(OUT, "sequence-shorten.excalidraw"), els)


# ─── 6. sequence-redirect-hit.excalidraw ────────────────────────────────────
def gen_sequence_hit():
    els = []
    els += title("Sequence — GET /:code with CDN HIT  (~5 ms total)",
                 subtitle="Popular code lives at the edge. No origin contact. Most peak traffic is absorbed here.")
    lanes = [
        ("User",   100, "actor"),
        ("DNS",    280, "concrete"),
        ("CDN",    460, "cache"),
        ("LB",     640, "concrete"),
        ("API",    820, "concrete"),
        ("Redis", 1000, "cache"),
        ("DB",    1180, "storage"),
    ]
    lane_x = {}
    for name, x, role in lanes:
        lane_elems, lx = sequence_lane(name, x, role=role, top_y=140, bottom_y=500)
        els.extend(lane_elems)
        lane_x[name] = lx

    msgs = [
        ("User", "DNS", 210, "1: resolve nearest POP",        False, False),
        ("DNS",  "User", 270, "2: → anycast IP",               True,  False),
        ("User", "CDN", 330, "3: GET /abc1234",                False, False),
        ("CDN",  "User", 390, "4: → 302 (cached)",             True,  False),
    ]
    for src, dst, y, lbl, ret, asyn in msgs:
        els.extend(sequence_msg(lane_x[src], lane_x[dst], y, lbl, is_return=ret, is_async=asyn))

    els += callout(
        "Total round-trip ~5ms.  No origin contact.\n"
        "→ Top ~5% codes (by traffic) absorbed entirely at the edge.",
        x=200, y=540, w=900, h=80,
        bg="#d3f9d8", stroke="#2f9e44", font_size=14)

    save(os.path.join(OUT, "sequence-redirect-hit.excalidraw"), els)


# ─── 7. sequence-redirect-miss.excalidraw ───────────────────────────────────
def gen_sequence_miss():
    els = []
    els += title("Sequence — GET /:code with CDN MISS + Redis MISS → DB  (~60 ms)",
                 subtitle="Cold key. Falls through all three cache layers to DB. Click event "
                          "fires async — never blocks the redirect.")
    lanes = [
        ("User",   100, "actor"),
        ("CDN",    280, "cache"),
        ("LB",     460, "concrete"),
        ("API",    640, "concrete"),
        ("Redis",  820, "cache"),
        ("DB",    1000, "storage"),
        ("Kafka", 1180, "async"),
    ]
    lane_x = {}
    for name, x, role in lanes:
        lane_elems, lx = sequence_lane(name, x, role=role, top_y=140, bottom_y=900)
        els.extend(lane_elems)
        lane_x[name] = lx

    msgs = [
        ("User",  "CDN",   210, "1: GET /xyz789",                  False, False),
        ("CDN",   "LB",    270, "2: miss → origin",                False, False),
        ("LB",    "API",   330, "3: route to API instance",        False, False),
        ("API",   "Redis", 390, "4: GET xyz789",                   False, False),
        ("Redis", "API",   450, "5: → MISS (cold key)",            True,  False),
        ("API",   "DB",    510, "6: SELECT long_url WHERE code='xyz789'", False, False),
        ("DB",    "API",   570, "7: → long_url",                   True,  False),
        ("API",   "Redis", 630, "8: SET cache (TTL 5 min)",        False, False),
        ("API",   "User",  690, "9: 302 → long_url",               True,  False),
        ("API",   "Kafka", 770, "10: fire-and-forget click event", False, True),
    ]
    for src, dst, y, lbl, ret, asyn in msgs:
        els.extend(sequence_msg(lane_x[src], lane_x[dst], y, lbl, is_return=ret, is_async=asyn))

    els += callout(
        "Three latency tiers, well-separated:  CDN ~5ms · Redis ~15ms · DB ~60ms.\n"
        "Click event to Kafka is FIRE-AND-FORGET — drops if broker is slow, never blocks the user.",
        x=200, y=940, w=900, h=80,
        bg="#fff9db", stroke="#fab005", font_size=14)

    save(os.path.join(OUT, "sequence-redirect-miss.excalidraw"), els)


# ─── main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"writing to {OUT}")
    gen_data_model()
    gen_iteration_1_naive()
    gen_iteration_2()
    gen_final_architecture()
    gen_sequence_shorten()
    gen_sequence_hit()
    gen_sequence_miss()
    print("\nDone — regenerated 7 .excalidraw files.")
    print("Now run:  npm run diagrams:hld")
