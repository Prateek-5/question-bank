# render-diagrams

Walks the repo's diagram source trees (`LLD/diagrams/`, `HLD/diagrams/`) and exports every `.excalidraw` file to a sibling `.png`. Keeps the walkthrough `.md` files (in `LLD/Topics/`, `HLD/Topics/`) free of any binary or source diagram clutter — they just reference the rendered PNGs via relative path.

## Directory contract

This is the layout the engine assumes:

```
bosscode-question-bank/
├── tools/render-diagrams/                           ← (you are here)
│   ├── package.json
│   ├── render.js
│   ├── renderer.html
│   └── README.md
│
├── LLD/
│   ├── Topics/<Bucket>/<Question>.md                ← clean: narrative + image refs
│   └── diagrams/<Bucket>/<Question>/                ← all diagram sources + renders
│       ├── <name>.excalidraw                        ← editable source
│       └── <name>.png                               ← rendered output (engine-managed)
│
└── HLD/
    ├── Topics/<Bucket>/<Question>.md
    └── diagrams/<Bucket>/<Question>/
        ├── <name>.excalidraw
        └── <name>.png
```

**The walkthrough `.md` files reference images via relative path**, e.g.:

```markdown
![Iteration 1 — naive class diagram](../../diagrams/Object_Oriented_Design/Parking_Lot/iteration-1.png)
```

From `LLD/Topics/Object_Oriented_Design/Parking_Lot.md`, that resolves to `LLD/diagrams/Object_Oriented_Design/Parking_Lot/iteration-1.png` — the engine's output.

## Workflow

### One-time setup

```bash
cd tools/render-diagrams
npm install          # installs puppeteer + Chromium (~150 MB)
```

### Author or edit a diagram

1. Open the relevant `.excalidraw` file in [excalidraw.com](https://excalidraw.com) (`File → Open`).
2. Edit visually.
3. `File → Save to disk` — overwrite the `.excalidraw` file.
4. Run the engine:

   ```bash
   cd tools/render-diagrams
   npm run diagrams           # incremental: only re-renders sources newer than their PNG
   npm run diagrams:force     # re-render everything
   npm run diagrams:lld       # only LLD/
   npm run diagrams:hld       # only HLD/
   ```
5. Commit both the `.excalidraw` and the regenerated `.png`.

### What the engine does

1. Walks the diagram source trees.
2. For each `.excalidraw` whose mtime exceeds its sibling PNG (or whose PNG doesn't exist):
   - Spawns a headless Chromium via puppeteer.
   - Loads `renderer.html`, which boots `@excalidraw/excalidraw`'s `exportToCanvas` utility from a CDN.
   - Posts the scene JSON to the page; the page exports to a PNG data-URL at 2× scale for sharpness.
   - Decodes the data-URL and writes the PNG next to the source.
3. If puppeteer can't launch (sandboxed CI, missing Chromium), the engine falls back to invoking `npx excalidraw_export` per file — slower but no local install needed.

## Why this architecture

| Concern | How it's addressed |
|---|---|
| Walkthrough `.md` files stay readable | Only contain narrative + `![]()` image refs. No mermaid blocks, no ASCII art, no SVG blobs. |
| Diagram sources are editable | Live as `.excalidraw` JSON. Open in excalidraw.com to refine. |
| Diagram outputs render inline | PNG siblings co-located in the `diagrams/` tree. Markdown viewers show them automatically. |
| No clutter in the `Topics/` directory | All diagram files live under a parallel `diagrams/` tree. |
| Programmatic refresh | Single command (`npm run diagrams`) re-exports every diagram that changed. Easy to wire into CI later. |
| Reproducibility | Renders happen at 2× scale; PNGs are deterministic given the input JSON. Same scene → same PNG bytes. |

## Naming convention

Inside `<vertical>/diagrams/<Bucket>/<Question>/`, name each diagram by what it depicts in the walkthrough — NOT by which section:

✅ `iteration-1.excalidraw` (the naive design)
✅ `pricing-strategy.excalidraw` (the Strategy slice after Pivot 1)
✅ `ticket-state.excalidraw` (the State slice after Pivot 2)
✅ `final-inventory.excalidraw`, `final-policy.excalidraw`, `final-lifecycle.excalidraw` (the three §12 sub-views)
✅ `sequence-park.excalidraw`, `sequence-pay-exit.excalidraw` (the two phases of §14)

❌ `section-7.excalidraw` (if §7 gets renumbered, the filename rots)
❌ `diagram.excalidraw` (not descriptive)

## Adding a new diagram

1. Create the `.excalidraw` source in the right `diagrams/<Bucket>/<Question>/` directory.
2. Run `npm run diagrams`.
3. In the walkthrough `.md`, reference the PNG via relative path:

   ```markdown
   ![<descriptive alt text>](../../diagrams/<Bucket>/<Question>/<name>.png)

   *Editable source: [`../../diagrams/<Bucket>/<Question>/<name>.excalidraw`](../../diagrams/<Bucket>/<Question>/<name>.excalidraw)*

   **Tour of this diagram.**
   1. ...
   2. ...
   ```

The alt text matters — it's what readers see if the image fails to load, and it's what search indexes.

## Troubleshooting

- **`Error: Failed to launch the browser process`** — usually means Chromium didn't install. Run `npx puppeteer browsers install chrome`.
- **`exportToCanvas is not a function`** — the CDN URL in `renderer.html` may be out of date. Bump the `@excalidraw/excalidraw` version pin in the URL and in `package.json`.
- **All PNGs look blank** — check that the `.excalidraw` file is valid JSON (`python3 -c "import json; json.load(open('file.excalidraw'))"`). A corrupt file produces a blank canvas.
- **Want SVG instead of PNG** — swap `exportToCanvas` for `exportToSvg` in `renderer.html`; adjust `render.js` to write `.svg`.

## Future hooks

- **Pre-commit:** add a git hook that runs `npm run diagrams` before commit so PNGs are never stale.
- **CI:** add a GitHub Action that runs the engine and fails if any PNG would change (gates against forgetting to re-export).
- **Watch mode:** add `--watch` to re-render on `.excalidraw` save.

None of these are wired up yet — current state is "run it manually after editing."
