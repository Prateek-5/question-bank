#!/usr/bin/env python3
"""Regenerate all 8 Parking_Lot .excalidraw files using excalidraw_gen library.

Output: LLD/diagrams/Object_Oriented_Design/Parking_Lot/<name>.excalidraw

Run from this directory:
    python3 gen_parking_lot.py

Then refresh PNGs:
    npm run diagrams
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from excalidraw_gen import (
    box, ellipse, arrow, composes, aggregates, inherits, uses,
    title, note, divider, callout, flatten, save,
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO_ROOT, "LLD", "diagrams", "Object_Oriented_Design", "Parking_Lot")
os.makedirs(OUT, exist_ok=True)


# ─── 1. iteration-1.excalidraw ──────────────────────────────────────────────
def gen_iteration_1():
    els = []
    els += title("Iteration 1 — naive design (no patterns yet)",
                 subtitle="Watch this fall apart in §8: every variability axis is hardcoded into a method.")

    # Top: ParkingLot
    lot = box("ParkingLot\n\nfloors : vector<Floor>\n\n+ park(v) → Ticket\n+ exit(t, m)",
              role="concrete", x=440, y=120, w=320, h=160)
    # Floor below ParkingLot
    floor = box("Floor\n\nnum    : int\nspots  : vector<Spot>",
                role="concrete", x=200, y=360, w=240, h=120)
    # Spot below Floor
    spot = box("Spot\n\nid       : string\ntype     : SpotSize\noccupied : bool\nvehicle  : Vehicle*",
               role="concrete", x=200, y=560, w=280, h=160)
    # Vehicle (abstract) to the right
    vehicle = box("Vehicle\n\nplate         : string\n+ sizeClass() : SpotSize",
                  role="concrete", x=560, y=360, w=280, h=140, is_abstract=True)
    car   = box("Car",   role="impl", x=560, y=560, w=120, h=60)
    bike  = box("Bike",  role="impl", x=700, y=560, w=120, h=60)
    truck = box("Truck", role="impl", x=840, y=560, w=120, h=60)
    # Ticket — the trouble zone, on the right
    ticket = box(
        "Ticket  ⚠ data bag\n\n"
        "status : enum  ACTIVE | PAID | EXITED\n"
        "entryAt, exitAt, spot, vehicle\n\n"
        "+ computeFee()    ⚠ hardcoded if/else\n"
        "+ charge(method)  ⚠ switch on method",
        role="warning", x=1000, y=360, w=420, h=240)

    els += flatten(lot, floor, spot, vehicle, car, bike, truck, ticket)
    # Composition arrows
    els += composes(lot, floor)
    els += composes(floor, spot)
    # Inheritance arrows — no text labels; the triangle arrowhead carries the meaning
    els += inherits(car, vehicle)
    els += inherits(bike, vehicle)
    els += inherits(truck, vehicle)
    # Spot → Vehicle pointer (uses) — let auto-orient handle the label position
    els += arrow(spot.right(), vehicle.left(), label="points to", dashed=True)
    # Ticket created by ParkingLot (uses) — diagonal arrow; default offset is fine
    els += arrow(lot.right(), ticket.top(), label="creates", dashed=True,
                 waypoints=[(960, 220)])
    # Bottom note
    els += callout(
        "What's missing (and will hurt in §8): no PricingStrategy, no TicketState,\n"
        "no PaymentMethodStrategy, no CompatibilityRule, no SpotAssignmentStrategy.\n"
        "Every axis of variation is HARDCODED inside the methods.",
        x=200, y=780, w=900, h=100)
    save(os.path.join(OUT, "iteration-1.excalidraw"), els)


# ─── 2. pivot-1-pricing-strategy.excalidraw ─────────────────────────────────
def gen_pivot_1():
    els = []
    els += title("Pivot 1 — Strategy for pricing  (before / after)",
                 subtitle="The most painful axis becomes a swappable algorithm. "
                          "Ticket loses computeFee(); ParkingLot gains a pricing field.")

    els += divider(y=120, x0=60, x1=580, label="BEFORE — naive")
    els += divider(y=120, x0=620, x1=1480, label="AFTER — Strategy")

    # BEFORE
    ticket_old = box(
        "Ticket\n\nstatus, entryAt, exitAt\n\n"
        "+ computeFee()\n  ⚠ hardcoded rate\n  ⚠ if/else by type",
        role="warning", x=160, y=180, w=320, h=200)
    els += ticket_old.elements

    # AFTER — left column: ParkingLot
    lot = box(
        "ParkingLot\n\nfloors\npricing : PricingStrategy*\n\n+ park, + exit",
        role="concrete", x=680, y=180, w=300, h=160)
    els += lot.elements

    # AFTER — middle: interface
    iface = box("PricingStrategy\n\n+ computeFee(t) → double",
                role="interface", x=1080, y=180, w=320, h=160, is_interface=True)
    els += iface.elements

    # Lot uses interface
    els += aggregates(lot, iface, label="◇ injected")
    # Adjust above call — it routes top-to-bottom by default. Override with right-to-left:
    # actually composing()/aggregates() route bottom-to-top — for side-by-side we want lateral
    # Manual override:
    # (just leave the default for now; it'll be a vertical arrow)

    # AFTER — bottom row: three impls
    impl1 = box("FlatRate\n\nhourlyByType", role="impl", x=720, y=460, w=200, h=120)
    impl2 = box("SubscriberAware\n(decorator)\n\nwraps base*", role="impl", x=960, y=460, w=200, h=120)
    impl3 = box("PeakMul\n(decorator)\n\nwraps base*", role="impl", x=1200, y=460, w=200, h=120)
    els += flatten(impl1, impl2, impl3)
    # Implements arrows
    els += inherits(impl1, iface, label="")
    els += inherits(impl2, iface, label="")
    els += inherits(impl3, iface, label="")
    # Decorators wrap base
    els += arrow(impl2.right(), impl3.left(), label="base*", dashed=True,
                 label_offset=(0, -16))

    # Bottom note
    els += callout(
        "Powerful consequence: decorators COMPOSE.\n"
        "    PeakMul( SubAware( FlatRate ) )   →   peak × subscriber × flat in ONE composed strategy.",
        x=160, y=640, w=1280, h=80,
        bg="#d3f9d8", stroke="#2f9e44")
    els += callout(
        "Pattern-discrimination: Strategy vs Template Method\n"
        "  Strategy:        whole algorithm in one swappable object, chosen at runtime (composition)\n"
        "  Template Method: skeleton in base class, subclasses fill hooks (inheritance)",
        x=160, y=740, w=1280, h=110,
        bg="#fff3bf", stroke="#e67700")
    save(os.path.join(OUT, "pivot-1-pricing-strategy.excalidraw"), els)


# ─── 3. pivot-2-ticket-state.excalidraw ─────────────────────────────────────
def gen_pivot_2():
    els = []
    els += title("Pivot 2 — State pattern for ticket lifecycle  (before / after)",
                 subtitle="The status enum + if/else branching becomes a class hierarchy. "
                          "Calling pay() on a PaidState throws — polymorphism IS the validation.")

    els += divider(y=120, x0=60, x1=580, label="BEFORE — enum + switch")
    els += divider(y=120, x0=620, x1=1480, label="AFTER — State pattern")

    ticket_old = box(
        "Ticket\n\nstatus : enum\n  ACTIVE | PAID | EXITED\n\n"
        "+ pay(m) { if/else }\n+ exit() { if/else }",
        role="warning", x=160, y=180, w=320, h=200)
    els += ticket_old.elements

    ticket_new = box(
        "Ticket\n\nstate : TicketState*\n  (unique_ptr — owns)\n\n"
        "+ pay(m) → state.pay()\n+ exit() → state.exit()\n+ transitionTo(s)",
        role="concrete", x=680, y=180, w=300, h=220)
    els += ticket_new.elements

    iface = box("TicketState\n\n+ pay(t, m)\n+ exit(t)",
                role="interface", x=1080, y=200, w=300, h=160, is_interface=True)
    els += iface.elements

    # Ticket composes (owns) TicketState (filled diamond)
    els += arrow((ticket_new.right()[0] + 20, ticket_new.right()[1]),
                 iface.left(),
                 label="◆ owns", end_arrowhead="arrow", start_arrowhead="diamond",
                 label_offset=(0, -16))

    # Four concrete states laid sequentially LEFT→RIGHT (240px stride: 220 wide + 20 gap)
    states = [
        ("ActiveState",  "+ pay  → Pricing.computeFee\n        → method.charge\n        → trans to Paid\n+ exit → throw"),
        ("PaidState",    "+ pay  → throw 'paid'\n+ exit → spot.release\n        → trans to Exited"),
        ("ExitedState",  "(terminal)\n+ pay  → throw\n+ exit → throw"),
        ("LostState",    "+ pay  → max-day fee\n        → trans to Paid\n+ exit → throw"),
    ]
    state_start_x = 80
    state_stride = 240
    for i, (name, body) in enumerate(states):
        b = box(f"{name}\n\n{body}", role="impl",
                x=state_start_x + i * state_stride, y=480, w=220, h=160, font_size=12)
        els += b.elements
        els += inherits(b, iface, label="")

    els += callout(
        "Pattern-discrimination: Strategy vs State\n"
        "  Strategy: CALLER picks; strategies usually unaware of peers       (external swap)\n"
        "  State:    OBJECT picks via internal transitions; states know peers (internal swap)",
        x=160, y=720, w=1280, h=120,
        bg="#fff3bf", stroke="#e67700")

    save(os.path.join(OUT, "pivot-2-ticket-state.excalidraw"), els)


# ─── 4. final-inventory.excalidraw ──────────────────────────────────────────
def gen_final_inventory():
    els = []
    els += title("§12.1 — The inventory spine (what the lot OWNS)",
                 subtitle="Composition chain: same lifetime as the lot. "
                          "Filled diamonds ◆ = composition.")
    lot   = box("ParkingLot\n(root coordinator)\n\nfloors : vector<Floor>",
                role="concrete", x=440, y=160, w=320, h=140)
    floor = box("Floor\n\nnum   : int\nspots : vector<Spot>",
                role="concrete", x=440, y=380, w=320, h=140)
    spot  = box("Spot\n\nid       : string\ntype     : SpotSize\noccupied : bool\nvehicle  : Vehicle*",
                role="concrete", x=440, y=600, w=320, h=180)
    els += flatten(lot, floor, spot)
    els += composes(lot, floor)
    els += composes(floor, spot)
    els += callout(
        "FILLED diamond (◆) marks composition — strong ownership, same lifetime.\n"
        "If the lot dies, every floor and every spot dies with it.",
        x=200, y=820, w=800, h=80)
    save(os.path.join(OUT, "final-inventory.excalidraw"), els)


# ─── 5. final-policy.excalidraw ─────────────────────────────────────────────
def gen_final_policy():
    els = []
    els += title("§12.2 — The policy injection (what the lot USES)",
                 subtitle="Open diamonds ◇ = aggregation. Strategies injected at construction.")
    lot = box(
        "ParkingLot\n\n"
        "pricing       : PricingStrategy*\n"
        "assignment    : SpotAssignmentStrategy*\n"
        "compatibility : CompatibilityRule*\n"
        "(injected at construction)",
        role="concrete", x=440, y=120, w=400, h=180)
    els += lot.elements

    iface_p = box("PricingStrategy\n\n+ computeFee(t)",
                  role="interface", x=80, y=400, w=300, h=120, is_interface=True)
    iface_a = box("SpotAssignmentStrategy\n\n+ findSpot(v, lot)",
                  role="interface", x=480, y=400, w=320, h=120, is_interface=True)
    iface_c = box("CompatibilityRule\n\n+ canPark(v, s)",
                  role="interface", x=900, y=400, w=280, h=120, is_interface=True)
    els += flatten(iface_p, iface_a, iface_c)
    els += aggregates(lot, iface_p)
    els += aggregates(lot, iface_a)
    els += aggregates(lot, iface_c)

    # Two impls per interface, laid HORIZONTALLY below to avoid stacked-arrow crossings.
    # Each interface gets 2 impls; arrows go straight up from impl.top() to iface.bottom()
    # at distinct x-coordinates.
    def render_two_impls_row(parent_iface, impls, base_y=620, box_w=180, gap=20):
        """Lay out two impls horizontally below the interface; route arrows straight up."""
        parent_x_left  = parent_iface.x
        parent_x_right = parent_iface.x + parent_iface.w
        parent_center  = (parent_x_left + parent_x_right) // 2
        # Position impls symmetrically around parent center
        impl_x = [
            parent_center - box_w - gap // 2,
            parent_center + gap // 2,
        ]
        for i, name in enumerate(impls):
            b = box(name, role="impl", x=impl_x[i], y=base_y, w=box_w, h=90, font_size=13)
            els.extend(b.elements)
            # Inherit arrow goes from top-center of impl to bottom of iface at the same x
            target_x = b.cx()
            target_y = parent_iface.y + parent_iface.h
            els.extend(arrow(b.top(), (target_x, target_y),
                             end_arrowhead="triangle"))

    render_two_impls_row(iface_p, ["FlatRate", "SubscriberAware\n(decorator)"])
    render_two_impls_row(iface_a, ["ClosestFreeSpot", "FloorBalanced"])
    render_two_impls_row(iface_c, ["SizeMatch", "EVRule"])

    # Footnote indicating additional impls exist
    els += note(
        "(+ PeakMul, VIPPrioritySpot, CompositeCompatibility, etc. — same shape.)",
        x=80, y=750, color="#868e96", size=12)
    els += callout(
        "Every Strategy interface follows the SAME shape: one method, multiple impls.\n"
        "ParkingLot stores each as unique_ptr<T>; injected at construction; never owned by Ticket.",
        x=80, y=820, w=1100, h=90,
        bg="#fff9db", stroke="#fab005", font_size=13)

    save(os.path.join(OUT, "final-policy.excalidraw"), els)


# ─── 6. final-lifecycle.excalidraw ──────────────────────────────────────────
def gen_final_lifecycle():
    """§12.3 — final lifecycle + payment diagram.

    LAYOUT INVARIANTS (apply to all similar "interface + impls" diagrams):

      Row A — three top-level boxes at SAME y_top:
        Ticket (concrete domain class) | TicketState (interface) | PaymentMethodStrategy (interface)
        — interfaces match each other in width and height
        — Ticket may be taller (more content); aligned at top edge

      Row B — impl rows at the SAME y level for both interface families:
        4 states (under TicketState) | 3 payment impls (under PaymentMethodStrategy)
        — all impl boxes same height
        — each group centered horizontally under its parent interface

      Row C — callouts BELOW impls, side by side at same y_top, same height.
    """
    els = []
    els += title("§12.3 — Lifecycle + payment  (State + Strategy meet here)",
                 subtitle="Ticket owns a TicketState (State pattern). ActiveState.pay() "
                          "consults TWO injected strategies (lot's Pricing — referenced in callout — "
                          "and caller's Payment — drawn at right).")

    # ─── Layout constants ───────────────────────────────────────────────
    ROW_A_Y       = 160          # top row: Ticket + 2 interfaces
    ROW_B_Y       = 420          # impl row (states + payment impls)
    ROW_C_Y       = 600          # callouts row
    H_INTERFACE   = 160
    H_IMPL        = 90
    H_TICKET      = 200          # Ticket is taller than interfaces (more content)
    W_INTERFACE   = 380          # both interfaces SAME width
    W_TICKET      = 320

    GAP_X         = 40           # horizontal gap between major elements

    # ─── Row A — Ticket + two interfaces, all aligned at y_top = ROW_A_Y ─
    ticket = box(
        "Ticket\n\nstate : TicketState* ◆\n\n+ pay(m)   → state.pay()\n"
        "+ exit()   → state.exit()\n+ transitionTo(s)",
        role="concrete", x=80, y=ROW_A_Y, w=W_TICKET, h=H_TICKET)

    iface_state_x = ticket.x + W_TICKET + GAP_X
    iface_state = box("TicketState\n\n+ pay(t, m)\n+ exit(t)",
                      role="interface",
                      x=iface_state_x, y=ROW_A_Y, w=W_INTERFACE, h=H_INTERFACE,
                      is_interface=True)

    iface_pay_x = iface_state.x + W_INTERFACE + GAP_X
    iface_pay = box("PaymentMethodStrategy\n\n+ charge(amount) → Receipt",
                    role="interface",
                    x=iface_pay_x, y=ROW_A_Y, w=W_INTERFACE, h=H_INTERFACE,
                    is_interface=True)
    els += flatten(ticket, iface_state, iface_pay)

    # Composition arrow: Ticket → TicketState (diamond carries the "owns" meaning, no text label)
    els += arrow(ticket.right(), iface_state.left(),
                 start_arrowhead="diamond", end_arrowhead="arrow")

    # ─── Row B — impl rows at same y level, each group centered under its parent ─
    # 4 states under TicketState
    state_names = ["ActiveState", "PaidState", "ExitedState", "LostState"]
    STATE_W = 80
    STATE_GAP = 8
    total_states_w = len(state_names) * STATE_W + (len(state_names) - 1) * STATE_GAP
    states_start_x = iface_state.cx() - total_states_w // 2
    for i, name in enumerate(state_names):
        sb = box(name, role="impl",
                 x=states_start_x + i * (STATE_W + STATE_GAP), y=ROW_B_Y,
                 w=STATE_W, h=H_IMPL, font_size=12)
        els += sb.elements
        els += inherits(sb, iface_state)

    # 3 payment impls under PaymentMethodStrategy
    pay_names = ["CardPayment", "CashPayment", "CryptoPayment"]
    PAY_W = 110
    PAY_GAP = 10
    total_pay_w = len(pay_names) * PAY_W + (len(pay_names) - 1) * PAY_GAP
    pay_start_x = iface_pay.cx() - total_pay_w // 2
    for i, name in enumerate(pay_names):
        pb = box(name, role="impl",
                 x=pay_start_x + i * (PAY_W + PAY_GAP), y=ROW_B_Y,
                 w=PAY_W, h=H_IMPL, font_size=12)
        els += pb.elements
        els += inherits(pb, iface_pay)

    # ─── Row C — callouts, side by side, equal height ────────────────────
    DIAGRAM_RIGHT = iface_pay.x + iface_pay.w   # right edge of diagram (~1320)
    DIAGRAM_LEFT  = ticket.x                     # left edge (80)
    CALLOUT_GAP = 40
    callout_total_w = DIAGRAM_RIGHT - DIAGRAM_LEFT - CALLOUT_GAP
    callout_w = callout_total_w // 2
    callout_h = 150

    els += callout(
        "ActiveState.pay() — the meeting point of three concerns:\n"
        "  1. fee = t.lot().pricing().computeFee(t)   ← lot's PricingStrategy (not drawn here; see §12.2)\n"
        "  2. method.charge(fee)                       ← caller's PaymentMethodStrategy (right column)\n"
        "  3. t.transitionTo(new PaidState(ref))      ← internal State transition (lower-left column)",
        x=DIAGRAM_LEFT, y=ROW_C_Y, w=callout_w, h=callout_h,
        bg="#fff9db", stroke="#fab005", font_size=13)
    els += callout(
        "Each strategy has a DIFFERENT owner:\n"
        "  · PricingStrategy → owned by ParkingLot (lot-wide policy)\n"
        "  · PaymentMethodStrategy → owned by caller, passed into pay()\n"
        "  · TicketState → owned by Ticket itself (unique_ptr)\n"
        "Three independent ownership lifetimes meet in ONE method call.",
        x=DIAGRAM_LEFT + callout_w + CALLOUT_GAP, y=ROW_C_Y,
        w=callout_w, h=callout_h,
        bg="#ffe0e9", stroke="#a61e4d", font_size=13)

    save(os.path.join(OUT, "final-lifecycle.excalidraw"), els)


# ─── 7. sequence-park.excalidraw ────────────────────────────────────────────
def gen_sequence_park():
    from excalidraw_gen import sequence_lane, sequence_msg
    els = []
    els += title("Phase 1 — park flow",
                 subtitle="The two Strategy interfaces (Assignment, Compatibility) are consulted; "
                          "Ticket is born holding ActiveState.")
    lanes = [
        ("Driver",       100, "actor"),
        ("EntryGate",    260, "concrete"),
        ("ParkingLot",   430, "concrete"),
        ("Assignment",   620, "interface"),
        ("Compatibility", 800, "interface"),
        ("Spot",         960, "concrete"),
        ("Ticket",      1120, "concrete"),
    ]
    lane_x = {}
    for name, x, role in lanes:
        lane_elems, lx = sequence_lane(name, x, role=role, top_y=140, bottom_y=820)
        els.extend(lane_elems)
        lane_x[name] = lx

    msgs = [
        ("Driver",       "EntryGate",     210, "1: approach",             False, False),
        ("EntryGate",    "ParkingLot",    270, "2: park(car)",            False, False),
        ("ParkingLot",   "Assignment",    330, "3: findSpot(car, lot)",   False, False),
        ("Assignment",   "ParkingLot",    390, "4: → Spot #42",           True,  False),
        ("ParkingLot",   "Compatibility", 450, "5: canPark(car, spot)",   False, False),
        ("Compatibility","ParkingLot",    510, "6: → true",               True,  False),
        ("ParkingLot",   "Spot",          570, "7: spot.assign(car)",     False, False),
        ("ParkingLot",   "Ticket",        630, "8: new Ticket(Active)",   False, False),
        ("ParkingLot",   "EntryGate",     690, "9: → Ticket #t1",         True,  False),
        ("EntryGate",    "Driver",        750, "10: ticket",              True,  False),
    ]
    for src, dst, y, label, ret, asyn in msgs:
        els.extend(sequence_msg(lane_x[src], lane_x[dst], y, label, is_return=ret, is_async=asyn))

    save(os.path.join(OUT, "sequence-park.excalidraw"), els)


# ─── 8. sequence-pay-exit.excalidraw ────────────────────────────────────────
def gen_sequence_pay_exit():
    from excalidraw_gen import sequence_lane, sequence_msg
    els = []
    els += title("Phase 2 — pay + exit flow",
                 subtitle="Three Strategies meet in ActiveState.pay(): pricing (from lot), "
                          "payment (from caller), state transition (within ticket).")
    lanes = [
        ("Driver",       100, "actor"),
        ("ExitGate",     250, "concrete"),
        ("ParkingLot",   410, "concrete"),
        ("Ticket",       570, "concrete"),
        ("ActiveState",  730, "impl"),
        ("Pricing",      890, "interface"),
        ("CardPayment", 1050, "interface"),
        ("PaidState",   1210, "impl"),
        ("Spot",        1370, "concrete"),
    ]
    lane_x = {}
    for name, x, role in lanes:
        lane_elems, lx = sequence_lane(name, x, role=role, top_y=140, bottom_y=1100)
        els.extend(lane_elems)
        lane_x[name] = lx

    msgs = [
        ("Driver",      "ExitGate",     210, "1: exit(t, card)",            False, False),
        ("ExitGate",    "ParkingLot",   270, "2: exit(t, card)",            False, False),
        ("ParkingLot",  "Ticket",       330, "3: ticket.pay(card)",         False, False),
        ("Ticket",      "ActiveState",  390, "4: state.pay(this, card)",    False, False),
        ("ActiveState", "Pricing",      450, "5: computeFee(t)",            False, False),
        ("Pricing",     "ActiveState",  510, "6: → $8.50",                  True,  False),
        ("ActiveState", "CardPayment",  570, "7: charge($8.50)",            False, False),
        ("CardPayment", "ActiveState",  630, "8: → {ok, TXN-xyz}",          True,  False),
        ("ActiveState", "Ticket",       690, "9: transitionTo(PaidState)",  False, False),
        ("ParkingLot",  "Ticket",       750, "10: ticket.exit()",           False, False),
        ("Ticket",      "PaidState",    810, "11: state.exit(this)",        False, False),
        ("PaidState",   "Spot",         870, "12: spot.release()",          False, False),
        ("PaidState",   "Ticket",       930, "13: transitionTo(Exited)",    False, False),
        ("ParkingLot",  "ExitGate",     990, "14: → ok",                    True,  False),
        ("ExitGate",    "Driver",      1050, "15: open gate",               True,  False),
    ]
    for src, dst, y, label, ret, asyn in msgs:
        els.extend(sequence_msg(lane_x[src], lane_x[dst], y, label, is_return=ret, is_async=asyn))

    save(os.path.join(OUT, "sequence-pay-exit.excalidraw"), els)


# ─── main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"writing to {OUT}")
    gen_iteration_1()
    gen_pivot_1()
    gen_pivot_2()
    gen_final_inventory()
    gen_final_policy()
    gen_final_lifecycle()
    gen_sequence_park()
    gen_sequence_pay_exit()
    print("\nDone — regenerated 8 .excalidraw files.")
    print("Now run:  npm run diagrams:lld")
