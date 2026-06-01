"""excalidraw_gen — programmatic excalidraw scene authoring.

Used by per-walkthrough generator scripts (`gen_parking_lot.py`, `gen_url_shortener.py`).
Produces .excalidraw JSON that the Node render engine in this same directory
converts into PNGs via puppeteer + @excalidraw/excalidraw.

Design goals:
  - Bound text:   text elements are children of their containing rectangle
                  (excalidraw renders them centered automatically)
  - Grid layout:  all positions snap to a 40px grid for consistent alignment
  - Role palette: every box has a semantic role (interface, impl, storage, etc.)
                  that maps to a (background, stroke) color pair
  - Smart arrows: labels supported; dashed for async / returns
  - Reusable:     two-vertical samples (LLD, HLD) consume the same library
"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ─── Palette ────────────────────────────────────────────────────────────────
# role → (background, stroke)
PALETTE: Dict[str, Tuple[str, str]] = {
    "concrete":  ("#e7f5ff", "#1971c2"),   # domain class, blue
    "interface": ("#fff3bf", "#e67700"),   # abstract / interface, amber
    "impl":      ("#d3f9d8", "#2f9e44"),   # concrete impl / leaf, green
    "async":     ("#ffd8a8", "#e8590c"),   # queue / fire-and-forget, orange
    "storage":   ("#bac8ff", "#4263eb"),   # DB / persistence, indigo
    "cache":     ("#ffe0e9", "#a61e4d"),   # cache layer, pink
    "warning":   ("#ffc9c9", "#c92a2a"),   # pain point / problem, red
    "actor":     ("#e7f5ff", "#1971c2"),   # user / actor in sequences
    "process":   ("#fff9db", "#fab005"),   # processing / consumer, yellow
}

# ─── Constants ──────────────────────────────────────────────────────────────
GRID = 40
PAD = 16
FONT_TITLE = 1   # excalidraw Virgil (hand-drawn)
FONT_BODY  = 1   # we use Virgil throughout for consistency
FONT_MONO  = 3   # Cascadia monospace, for code-shaped labels

DEFAULT_BG = "#ffffff"

# ─── Internals ──────────────────────────────────────────────────────────────
_seed_counter = 0

def _seed(s: str = "") -> int:
    """Stable-ish numeric seed per element id."""
    global _seed_counter
    _seed_counter += 1
    if s:
        return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % 2_000_000
    return _seed_counter * 100

def _id(prefix: str = "") -> str:
    """16-char id derived from a stable seed prefix."""
    h = hashlib.md5(f"{prefix}-{_seed(prefix)}".encode()).hexdigest()[:16]
    return h

def _snap(v: int) -> int:
    return round(v / GRID) * GRID

def _measure(text: str, font_size: int = 16) -> Tuple[int, int]:
    """Rough text bounding box."""
    lines = text.split("\n")
    w = max((len(l) for l in lines), default=0) * (font_size * 0.6)
    h = len(lines) * (font_size + 8)
    return int(w), int(h)


# ─── Box (container + bound text) ───────────────────────────────────────────
@dataclass
class Box:
    label: str
    role: str = "concrete"
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    rect_id: str = ""
    text_id: str = ""
    elements: List[Dict] = field(default_factory=list)
    is_interface: bool = False
    is_abstract: bool = False

    def cx(self): return self.x + self.w // 2
    def cy(self): return self.y + self.h // 2
    def top(self):    return (self.cx(), self.y)
    def bottom(self): return (self.cx(), self.y + self.h)
    def left(self):   return (self.x, self.cy())
    def right(self):  return (self.x + self.w, self.cy())


def box(label: str, role: str = "concrete",
        x: int = 0, y: int = 0,
        w: Optional[int] = None, h: Optional[int] = None,
        is_interface: bool = False, is_abstract: bool = False,
        font_size: int = 16, font_family: int = FONT_BODY) -> Box:
    """Create a rectangle + bound centered text. Returns a Box."""
    bg, stroke = PALETTE.get(role, PALETTE["concrete"])

    display = label
    if is_interface:
        display = f"«interface»\n{label}"
    elif is_abstract:
        display = f"«abstract»\n{label}"

    tw, th = _measure(display, font_size)
    if w is None:
        w = max(160, _snap(tw + 2 * PAD + 24))
    if h is None:
        h = max(60, _snap(th + 2 * PAD))

    rect_id = _id(f"rect-{label}")
    text_id = _id(f"text-{label}")

    rect = {
        "id": rect_id,
        "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h,
        "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None,
        "roundness": {"type": 3},
        "seed": _seed(f"rect-{label}"),
        "version": 1, "versionNonce": _seed(f"rectn-{label}"),
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text_id}],
        "updated": 1, "link": None, "locked": False,
    }
    # For bound text in excalidraw, the text element's bbox should MATCH the
    # container's bbox exactly. Excalidraw then centers the text inside that
    # bbox using textAlign + verticalAlign. (Inset coordinates here cause the
    # text block to appear slightly off-center relative to the visible box.)
    text = {
        "id": text_id,
        "type": "text",
        "x": x, "y": y,
        "width": w, "height": h,
        "angle": 0,
        "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"text-{label}"),
        "version": 1, "versionNonce": _seed(f"textn-{label}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "fontSize": font_size, "fontFamily": font_family,
        "text": display,
        "textAlign": "center", "verticalAlign": "middle",
        "baseline": font_size - 2,
        "containerId": rect_id,
        "originalText": display, "lineHeight": 1.25,
    }
    b = Box(label=label, role=role, x=x, y=y, w=w, h=h,
            rect_id=rect_id, text_id=text_id,
            is_interface=is_interface, is_abstract=is_abstract)
    b.elements = [rect, text]
    return b


def ellipse(label: str, role: str = "concrete",
            x: int = 0, y: int = 0,
            w: Optional[int] = None, h: Optional[int] = None,
            font_size: int = 16) -> Box:
    """An ellipse with bound centered text. Same API as box(), returns Box-like
    so callers can use .top()/.bottom()/etc."""
    bg, stroke = PALETTE.get(role, PALETTE["concrete"])
    tw, th = _measure(label, font_size)
    if w is None:
        w = max(180, _snap(tw + 2 * PAD + 32))
    if h is None:
        h = max(80, _snap(th + 2 * PAD + 16))

    ellipse_id = _id(f"el-{label}")
    text_id = _id(f"eltext-{label}")

    elt = {
        "id": ellipse_id, "type": "ellipse",
        "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"el-{label}"),
        "version": 1, "versionNonce": _seed(f"eln-{label}"),
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text_id}],
        "updated": 1, "link": None, "locked": False,
    }
    text = {
        "id": text_id, "type": "text",
        "x": x, "y": y,
        "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"eltext-{label}"),
        "version": 1, "versionNonce": _seed(f"eltextn-{label}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "fontSize": font_size, "fontFamily": FONT_BODY,
        "text": label, "textAlign": "center", "verticalAlign": "middle",
        "baseline": font_size - 2, "containerId": ellipse_id,
        "originalText": label, "lineHeight": 1.25,
    }
    b = Box(label=label, role=role, x=x, y=y, w=w, h=h,
            rect_id=ellipse_id, text_id=text_id)
    b.elements = [elt, text]
    return b


# ─── Arrow ──────────────────────────────────────────────────────────────────
def arrow(start: Tuple[int, int], end: Tuple[int, int],
          label: str = "",
          dashed: bool = False,
          color: str = "#1e1e1e",
          end_arrowhead: Optional[str] = "arrow",
          start_arrowhead: Optional[str] = None,
          waypoints: Optional[List[Tuple[int, int]]] = None,
          label_offset: Optional[Tuple[int, int]] = None) -> List[Dict]:
    """Arrow from start to end, with optional label, dashing, custom arrowheads, waypoints.

    Label positioning is direction-aware: horizontal arrows → label ABOVE midpoint;
    vertical arrows → label to the RIGHT of midpoint (perpendicular to arrow line so
    label text doesn't overlap the line). Pass label_offset explicitly to override.

    Labels render with an opaque white background rectangle so they remain readable
    when placed over other elements.
    """
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy

    pts: List[List[float]] = [[0, 0]]
    if waypoints:
        for wx, wy in waypoints:
            pts.append([wx - sx, wy - sy])
    pts.append([dx, dy])

    arr_id = _id(f"arr-{sx}-{sy}-{ex}-{ey}-{label}")
    arrow_elem = {
        "id": arr_id, "type": "arrow",
        "x": sx, "y": sy,
        "width": max(abs(dx), 1), "height": max(abs(dy), 1), "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 2,
        "strokeStyle": "dashed" if dashed else "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 2},
        "seed": _seed(f"arr-{sx}-{sy}-{ex}-{ey}"),
        "version": 1, "versionNonce": _seed(f"arrn-{sx}-{sy}-{ex}-{ey}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "startBinding": None, "endBinding": None,
        "lastCommittedPoint": None,
        "startArrowhead": start_arrowhead,
        "endArrowhead": end_arrowhead,
        "points": pts,
    }
    elems = [arrow_elem]

    if label:
        # Auto-orient label perpendicular to arrow direction (overridable).
        if label_offset is None:
            if abs(dx) >= abs(dy) * 1.2:
                # Mostly horizontal: label above midpoint
                label_offset = (0, -24)
            elif abs(dy) >= abs(dx) * 1.2:
                # Mostly vertical: label to the right (clears the arrow line)
                label_offset = (28, 0)
            else:
                # Diagonal: offset up-and-right perpendicular-ish
                label_offset = (20, -18)

        mid_x = (sx + ex) // 2 + label_offset[0]
        mid_y = (sy + ey) // 2 + label_offset[1]
        lw, lh = _measure(label, 12)
        # Box label tightly
        bg_w = lw + 12
        bg_h = lh + 6
        label_x = mid_x - lw // 2
        label_y = mid_y - lh // 2

        # White background rectangle BEHIND label (renders before label in element order)
        elems.append({
            "id": _id(f"arrbg-{arr_id}"),
            "type": "rectangle",
            "x": label_x - 6, "y": label_y - 3,
            "width": bg_w, "height": bg_h, "angle": 0,
            "strokeColor": "#ffffff", "backgroundColor": "#ffffff",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 0, "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": None,
            "seed": _seed(f"arrbg-{arr_id}"),
            "version": 1, "versionNonce": _seed(f"arrbgn-{arr_id}"),
            "isDeleted": False, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
        })
        # Label text on top, Helvetica (more readable at small sizes than Virgil)
        elems.append({
            "id": _id(f"arrlbl-{arr_id}"),
            "type": "text",
            "x": label_x, "y": label_y,
            "width": lw + 4, "height": lh, "angle": 0,
            "strokeColor": color, "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 1, "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": None,
            "seed": _seed(f"arrlbl-{arr_id}"),
            "version": 1, "versionNonce": _seed(f"arrlbln-{arr_id}"),
            "isDeleted": False, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
            "fontSize": 12, "fontFamily": 2,   # 2 = Helvetica (readable small)
            "text": label, "textAlign": "center", "verticalAlign": "top",
            "baseline": 10, "containerId": None,
            "originalText": label, "lineHeight": 1.25,
        })
    return elems


# ─── Composition / inheritance arrows (UML semantics) ──────────────────────
def composes(parent_box: Box, child_box: Box, label: str = "") -> List[Dict]:
    """Composition (filled diamond at parent / 'whole'). No default text label —
    the diamond arrowhead carries the meaning. Pass label="" by omission."""
    return arrow(parent_box.bottom(), child_box.top(),
                 label=label,
                 start_arrowhead="diamond", end_arrowhead="arrow")

def aggregates(parent_box: Box, child_box: Box, label: str = "") -> List[Dict]:
    """Aggregation (open diamond at parent). No default text label — the open
    diamond carries the meaning."""
    return arrow(parent_box.bottom(), child_box.top(),
                 label=label,
                 start_arrowhead="diamond_outline", end_arrowhead="arrow")

def inherits(child_box: Box, parent_box: Box, label: str = "",
             waypoint: Optional[Tuple[int, int]] = None) -> List[Dict]:
    """Inheritance / implementation (triangle at parent). No default text label
    — the triangle arrowhead carries the meaning. Optional waypoint to route
    around obstacles (e.g., another impl box between this child and its parent)."""
    return arrow(child_box.top(), parent_box.bottom(),
                 label=label,
                 dashed=False,
                 end_arrowhead="triangle",
                 waypoints=[waypoint] if waypoint else None)

def uses(from_box: Box, to_box: Box, label: str = "uses") -> List[Dict]:
    """Plain association (dashed). Default label 'uses' because dashed-arrow
    alone is ambiguous; the label is informational."""
    return arrow(from_box.right(), to_box.left(),
                 label=label, dashed=True, end_arrowhead="arrow")


# ─── Title, subtitle, note, divider ─────────────────────────────────────────
def title(text: str, x: int = 60, y: int = 30,
          subtitle: str = "",
          size: int = 24) -> List[Dict]:
    tw, th = _measure(text, size)
    elems = [{
        "id": _id(f"title-{text[:30]}"),
        "type": "text",
        "x": x, "y": y, "width": tw + 20, "height": th + 4, "angle": 0,
        "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"title-{text[:30]}"),
        "version": 1, "versionNonce": _seed(f"titlen-{text[:30]}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "fontSize": size, "fontFamily": FONT_TITLE,
        "text": text, "textAlign": "left", "verticalAlign": "top",
        "baseline": size - 2, "containerId": None,
        "originalText": text, "lineHeight": 1.25,
    }]
    if subtitle:
        sw, sh = _measure(subtitle, 15)
        elems.append({
            "id": _id(f"sub-{subtitle[:30]}"),
            "type": "text",
            "x": x, "y": y + th + 10, "width": sw + 20, "height": sh, "angle": 0,
            "strokeColor": "#868e96", "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
            "roughness": 1, "opacity": 100,
            "groupIds": [], "frameId": None, "roundness": None,
            "seed": _seed(f"sub-{subtitle[:30]}"),
            "version": 1, "versionNonce": _seed(f"subn-{subtitle[:30]}"),
            "isDeleted": False, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
            "fontSize": 15, "fontFamily": FONT_BODY,
            "text": subtitle, "textAlign": "left", "verticalAlign": "top",
            "baseline": 13, "containerId": None,
            "originalText": subtitle, "lineHeight": 1.25,
        })
    return elems


def note(text: str, x: int, y: int, color: str = "#868e96",
         size: int = 13, font_family: int = FONT_BODY) -> List[Dict]:
    tw, th = _measure(text, size)
    return [{
        "id": _id(f"note-{text[:30]}"),
        "type": "text",
        "x": x, "y": y, "width": tw + 20, "height": th + 4, "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"note-{text[:30]}"),
        "version": 1, "versionNonce": _seed(f"noten-{text[:30]}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "fontSize": size, "fontFamily": font_family,
        "text": text, "textAlign": "left", "verticalAlign": "top",
        "baseline": size - 2, "containerId": None,
        "originalText": text, "lineHeight": 1.25,
    }]


def divider(y: int, x0: int = 60, x1: int = 1200,
            label: str = "", color: str = "#dee2e6") -> List[Dict]:
    """Horizontal dashed divider; optional label above."""
    elems = [{
        "id": _id(f"div-{y}"), "type": "line",
        "x": x0, "y": y, "width": x1 - x0, "height": 1, "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "dashed",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"div-{y}"),
        "version": 1, "versionNonce": _seed(f"divn-{y}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "points": [[0, 0], [x1 - x0, 0]],
    }]
    if label:
        elems.extend(note(label, x0, y - 22, color="#868e96"))
    return elems


def callout(text: str, x: int, y: int, w: int = 320, h: int = 80,
            bg: str = "#fff3bf", stroke: str = "#e67700",
            font_size: int = 13) -> List[Dict]:
    """Light box with text — for inline annotations / pivot questions."""
    rect_id = _id(f"co-{text[:20]}")
    text_id = _id(f"cotxt-{text[:20]}")
    rect = {
        "id": rect_id, "type": "rectangle",
        "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": {"type": 3},
        "seed": _seed(f"co-{text[:20]}"),
        "version": 1, "versionNonce": _seed(f"con-{text[:20]}"),
        "isDeleted": False,
        "boundElements": [{"type": "text", "id": text_id}],
        "updated": 1, "link": None, "locked": False,
    }
    txt = {
        "id": text_id, "type": "text",
        "x": x, "y": y,
        "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"cotxt-{text[:20]}"),
        "version": 1, "versionNonce": _seed(f"cotxtn-{text[:20]}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "fontSize": font_size, "fontFamily": FONT_BODY,
        "text": text, "textAlign": "center", "verticalAlign": "middle",
        "baseline": font_size - 2, "containerId": rect_id,
        "originalText": text, "lineHeight": 1.25,
    }
    return [rect, txt]


# ─── Sequence-diagram helpers ───────────────────────────────────────────────
def sequence_lane(name: str, x: int, role: str = "concrete",
                  top_y: int = 80, bottom_y: int = 800) -> Tuple[List[Dict], int]:
    """Header box + vertical lifeline. Returns (elements, x of lifeline)."""
    head = box(name, role=role, x=x - 60, y=top_y, w=120, h=40, font_size=15)
    lifeline = [{
        "id": _id(f"lifeline-{name}"), "type": "line",
        "x": x, "y": top_y + 40, "width": 1, "height": bottom_y - top_y - 40,
        "angle": 0, "strokeColor": "#adb5bd", "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "dashed",
        "roughness": 0, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": None,
        "seed": _seed(f"lifeline-{name}"),
        "version": 1, "versionNonce": _seed(f"lifelinen-{name}"),
        "isDeleted": False, "boundElements": [],
        "updated": 1, "link": None, "locked": False,
        "points": [[0, 0], [0, bottom_y - top_y - 40]],
    }]
    return head.elements + lifeline, x


def sequence_msg(from_x: int, to_x: int, y: int, label: str,
                 is_return: bool = False, is_async: bool = False) -> List[Dict]:
    """Sequence-diagram message arrow from one lane to another."""
    if is_return:
        color = "#2f9e44"
    elif is_async:
        color = "#e8590c"
    else:
        color = "#1971c2"
    return arrow((from_x, y), (to_x, y), label=label,
                 dashed=is_return or is_async, color=color,
                 label_offset=(0, -18))


# ─── Scene packaging ────────────────────────────────────────────────────────
def scene(elements: List[Dict], view_bg: str = DEFAULT_BG) -> Dict:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"gridSize": GRID, "viewBackgroundColor": view_bg},
        "files": {},
    }


def save(path: str, elements: List[Dict]):
    with open(path, "w") as f:
        json.dump(scene(elements), f, indent=2)
    print(f"  wrote {path.rsplit('/', 1)[-1]} ({len(elements)} elements)")


def flatten(*groups) -> List[Dict]:
    """Flatten nested lists of element groups into a single list."""
    out: List[Dict] = []
    for g in groups:
        if isinstance(g, Box):
            out.extend(g.elements)
        elif isinstance(g, list):
            for e in g:
                if isinstance(e, Box):
                    out.extend(e.elements)
                else:
                    out.append(e)
        elif isinstance(g, dict):
            out.append(g)
    return out
