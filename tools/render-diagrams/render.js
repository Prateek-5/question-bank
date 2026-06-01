#!/usr/bin/env node
/**
 * render-diagrams — walk the repo's diagram source tree and export every
 * `.excalidraw` file to a sibling `.png` snapshot, keeping the bosscode-question-bank
 * walkthroughs free of binary clutter and the diagram sources cleanly co-located.
 *
 * Layout this script assumes:
 *
 *   bosscode-question-bank/
 *     LLD/diagrams/<Bucket>/<Question>/<name>.excalidraw   → produces <name>.png
 *     HLD/diagrams/<Bucket>/<Question>/<name>.excalidraw   → produces <name>.png
 *
 * Usage (from this directory):
 *
 *   npm install              # one-time
 *   npm run diagrams         # incremental: re-render only sources newer than their PNG
 *   npm run diagrams:force   # render everything regardless of mtimes
 *   npm run diagrams:lld     # restrict to LLD/
 *   npm run diagrams:hld     # restrict to HLD/
 *
 * How it works:
 *   1. Walks the diagram source trees.
 *   2. For each `.excalidraw` whose mtime > sibling PNG's mtime (or PNG missing):
 *      a. Launches a headless Chromium via puppeteer.
 *      b. Loads `renderer.html` (a tiny page that boots @excalidraw/excalidraw).
 *      c. Posts the scene JSON to the page.
 *      d. The page exports the scene to a PNG data-URL via excalidraw's own
 *         `exportToCanvas` utility, which preserves the hand-drawn aesthetic.
 *      e. The data-URL is decoded and written next to the source as `.png`.
 *
 * Failure mode: if puppeteer / chromium can't start (CI env without sandbox, etc.)
 * the script falls back to invoking `npx excalidraw_export` per file. That npm
 * package is an off-the-shelf wrapper around the same machinery; it's slower but
 * needs no local dependency install beyond Node + npm.
 */

const fs = require('fs/promises');
const path = require('path');
const { spawn } = require('child_process');

const SCRIPT_DIR  = __dirname;
const REPO_ROOT   = path.resolve(SCRIPT_DIR, '..', '..');
const DIAGRAM_ROOTS = [
  { vertical: 'LLD', dir: path.join(REPO_ROOT, 'LLD', 'diagrams') },
  { vertical: 'HLD', dir: path.join(REPO_ROOT, 'HLD', 'diagrams') },
];
const RENDERER_HTML = path.join(SCRIPT_DIR, 'renderer.html');

const args = new Set(process.argv.slice(2));
const FORCE = args.has('--force');
const ONLY  = (() => {
  const idx = process.argv.indexOf('--only');
  return idx >= 0 ? process.argv[idx + 1] : null;
})();

const log = (msg) => process.stdout.write(msg + '\n');
const warn = (msg) => process.stderr.write('  WARN: ' + msg + '\n');

async function exists(p) {
  try { await fs.access(p); return true; } catch { return false; }
}

async function walkExcalidraw(root) {
  const out = [];
  async function visit(dir) {
    let entries;
    try { entries = await fs.readdir(dir, { withFileTypes: true }); }
    catch (e) { if (e.code === 'ENOENT') return; throw e; }
    for (const ent of entries) {
      const full = path.join(dir, ent.name);
      if (ent.isDirectory()) await visit(full);
      else if (ent.name.endsWith('.excalidraw')) out.push(full);
    }
  }
  await visit(root);
  return out;
}

async function needsRender(src, dst) {
  if (FORCE) return true;
  if (!(await exists(dst))) return true;
  const [s, d] = await Promise.all([fs.stat(src), fs.stat(dst)]);
  return s.mtimeMs > d.mtimeMs;
}

function relRepo(p) { return path.relative(REPO_ROOT, p); }

// ─── Renderer: puppeteer path ──────────────────────────────────────────────
let puppeteer, browser;
async function ensureBrowser() {
  if (browser) return browser;
  try {
    puppeteer = require('puppeteer');
  } catch {
    return null;  // puppeteer not installed → caller falls back
  }
  browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  return browser;
}

async function renderWithPuppeteer(src) {
  const b = await ensureBrowser();
  if (!b) return false;
  const page = await b.newPage();
  await page.goto('file://' + RENDERER_HTML, { waitUntil: 'networkidle0' });

  // Wait until the renderer page has loaded excalidraw UMD + exposed the render function.
  await page.waitForFunction(
    'typeof window.renderToPngDataUrl === "function" && window.__readyForRender === true',
    { timeout: 30000 }
  );

  const scene = JSON.parse(await fs.readFile(src, 'utf8'));
  const dataUrl = await page.evaluate(async (scene) => {
    return await window.renderToPngDataUrl(scene);
  }, scene);
  await page.close();

  if (!dataUrl || !dataUrl.startsWith('data:image/png;base64,')) {
    throw new Error(`bad data-url from renderer for ${src}`);
  }
  const base64 = dataUrl.split(',', 2)[1];
  const dst = src.replace(/\.excalidraw$/, '.png');
  await fs.writeFile(dst, Buffer.from(base64, 'base64'));
  return true;
}

// ─── Fallback: shell out to `npx excalidraw_export` ────────────────────────
function renderWithCli(src) {
  return new Promise((resolve, reject) => {
    const outDir = path.dirname(src);
    const child = spawn('npx', ['--yes', 'excalidraw_export', src, '--output-dir', outDir, '--format', 'png'], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stderr = '';
    child.stderr.on('data', (b) => { stderr += b.toString(); });
    child.on('exit', (code) => {
      if (code === 0) resolve(true);
      else reject(new Error(`excalidraw_export CLI failed for ${src} (exit ${code}): ${stderr.slice(-400)}`));
    });
    child.on('error', reject);
  });
}

async function renderOne(src) {
  // try puppeteer first; on any failure, fall back to the CLI.
  try {
    const ok = await renderWithPuppeteer(src);
    if (ok) return 'puppeteer';
  } catch (e) {
    warn(`puppeteer render failed (${e.message}); trying CLI fallback`);
  }
  await renderWithCli(src);
  return 'cli';
}

// ─── Main ──────────────────────────────────────────────────────────────────
async function main() {
  let total = 0, rendered = 0, skipped = 0, failed = 0;
  const tStart = Date.now();

  for (const { vertical, dir } of DIAGRAM_ROOTS) {
    if (ONLY && ONLY !== vertical) continue;
    if (!(await exists(dir))) {
      log(`(${vertical}) skip — no diagrams/ directory yet`);
      continue;
    }
    const srcs = await walkExcalidraw(dir);
    log(`(${vertical}) found ${srcs.length} .excalidraw files`);
    for (const src of srcs) {
      total++;
      const dst = src.replace(/\.excalidraw$/, '.png');
      if (!(await needsRender(src, dst))) {
        skipped++;
        log(`  skip   ${relRepo(src)}`);
        continue;
      }
      log(`  render ${relRepo(src)}`);
      try {
        const via = await renderOne(src);
        rendered++;
        log(`    → ${relRepo(dst)}  (${via})`);
      } catch (e) {
        failed++;
        warn(e.message);
      }
    }
  }

  if (browser) await browser.close();

  const elapsed = ((Date.now() - tStart) / 1000).toFixed(1);
  log('');
  log(`Done in ${elapsed}s. total=${total}, rendered=${rendered}, skipped=${skipped}, failed=${failed}.`);
  if (failed > 0) process.exitCode = 1;
}

main().catch(e => { console.error(e); process.exit(1); });
