#!/usr/bin/env python3
"""Detect pairwise bounding-box overlaps in .excalidraw files.

Walks LLD/diagrams/ + HLD/diagrams/, reads each .excalidraw, and reports
element-pairs whose bounding boxes intersect — minus the legitimate cases:

  - Text elements bound to their container (containerId set) — these are
    SUPPOSED to overlap their container.
  - Arrow lines passing through whitespace — they're 1D, not really
    "overlapping" in the spatial sense.
  - The white background rectangles I added behind arrow labels — intentional.
  - Lifeline dashed lines in sequence diagrams — they're 1D dividers.

Output: per-file list of (element-A, element-B, overlap-region) tuples,
prioritizing TEXT-on-TEXT and TEXT-on-BOX overlaps (which are the visible
ones causing user complaints).
"""
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIAGRAM_ROOTS = [
    os.path.join(REPO_ROOT, "LLD", "diagrams"),
    os.path.join(REPO_ROOT, "HLD", "diagrams"),
]


def bbox(el):
    """Return (x0, y0, x1, y1) bounding box of an element."""
    x, y = el.get("x", 0), el.get("y", 0)
    w, h = el.get("width", 0), el.get("height", 0)
    return (x, y, x + w, y + h)


def overlaps(a, b, slack=0):
    """Two bboxes overlap if they share any 2D area (with optional slack)."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 + slack <= bx0 or bx1 + slack <= ax0 or
                ay1 + slack <= by0 or by1 + slack <= ay0)


def overlap_area(a, b):
    """Area of the overlap region (0 if no overlap)."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    iw = max(0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0, min(ay1, by1) - max(ay0, by0))
    return iw * ih


def find_overlaps(file_path):
    """Return list of overlap tuples for one .excalidraw file."""
    with open(file_path) as f:
        data = json.load(f)
    elements = data.get("elements", [])

    # Index containers
    container_ids = set()
    for el in elements:
        cid = el.get("containerId")
        if cid:
            container_ids.add(cid)

    # Identify label-background rectangles (we added these; intentional overlap with labels)
    label_bg_ids = {el["id"] for el in elements
                    if el.get("type") == "rectangle"
                    and el.get("backgroundColor") == "#ffffff"
                    and el.get("strokeColor") == "#ffffff"}

    overlaps_found = []
    for i, a in enumerate(elements):
        # Skip arrows and lines (1D)
        if a.get("type") in ("arrow", "line"):
            continue
        # Skip deleted
        if a.get("isDeleted"):
            continue

        ba = bbox(a)
        for j in range(i + 1, len(elements)):
            b = elements[j]
            if b.get("type") in ("arrow", "line"):
                continue
            if b.get("isDeleted"):
                continue

            # Skip: text bound to its container
            if a.get("type") == "text" and a.get("containerId") == b["id"]:
                continue
            if b.get("type") == "text" and b.get("containerId") == a["id"]:
                continue

            # Skip: label background rectangle paired with its label text
            # (rectangle and text were generated as a pair; intentional)
            if a["id"] in label_bg_ids and b.get("type") == "text":
                continue
            if b["id"] in label_bg_ids and a.get("type") == "text":
                continue

            # Skip: both are label backgrounds (these don't visually overlap each other unless dense)
            if a["id"] in label_bg_ids and b["id"] in label_bg_ids:
                continue

            bb = bbox(b)
            area = overlap_area(ba, bb)
            if area > 50:  # ignore tiny overlaps (< 50 sq px)
                overlaps_found.append({
                    "a_type": a["type"],
                    "a_id":   a["id"][:8],
                    "a_text": a.get("text", "")[:60] if a.get("type") == "text" else "",
                    "a_bbox": ba,
                    "b_type": b["type"],
                    "b_id":   b["id"][:8],
                    "b_text": b.get("text", "")[:60] if b.get("type") == "text" else "",
                    "b_bbox": bb,
                    "area":   int(area),
                })
    return overlaps_found


def severity(o):
    """Higher = worse: text-on-text > text-on-rect/ellipse > rect-on-rect."""
    if o["a_type"] == "text" and o["b_type"] == "text":
        return 3 + (o["area"] / 1000)
    if o["a_type"] == "text" or o["b_type"] == "text":
        return 2 + (o["area"] / 1000)
    return 1 + (o["area"] / 1000)


def main():
    total_overlaps = 0
    total_files = 0
    by_file_overlap_count = []

    for root in DIAGRAM_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for fn in sorted(filenames):
                if not fn.endswith(".excalidraw"):
                    continue
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, REPO_ROOT)
                ovs = find_overlaps(fp)
                ovs.sort(key=severity, reverse=True)
                total_files += 1
                total_overlaps += len(ovs)
                by_file_overlap_count.append((rel, len(ovs), ovs))

    # Summary
    print(f"\n{'='*72}")
    print(f"OVERLAP REPORT — {total_files} files, {total_overlaps} non-trivial overlaps")
    print('='*72)

    # Sort files by overlap count
    by_file_overlap_count.sort(key=lambda x: -x[1])
    for rel, count, ovs in by_file_overlap_count:
        if count == 0:
            continue
        print(f"\n  {rel}  ({count} overlaps)")
        # Show top 5 per file by severity
        for o in ovs[:5]:
            tag_a = f"{o['a_type']}({o['a_text'][:30]})" if o['a_text'] else o['a_type']
            tag_b = f"{o['b_type']}({o['b_text'][:30]})" if o['b_text'] else o['b_type']
            print(f"    {tag_a:<50}  ⨉  {tag_b:<50}  ({o['area']}px²)")
        if count > 5:
            print(f"    ... and {count - 5} more")

    clean = [rel for rel, c, _ in by_file_overlap_count if c == 0]
    if clean:
        print(f"\n  Clean files (no non-trivial overlaps):")
        for rel in clean:
            print(f"    {rel}")


if __name__ == "__main__":
    main()
