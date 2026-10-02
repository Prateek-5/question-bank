#!/usr/bin/env bash
# validate-mermaid.sh — render every mermaid block in the repo via mmdc
# (the same headless-Chrome renderer GitHub uses) and fail if any block errors.
#
# WHY THIS EXISTS
#   GitHub's mermaid v10 renderer is strict. Prior manual sweeps (regex-based)
#   left ~12 broken diagrams unnoticed. mmdc catches them all because it IS a
#   full mermaid render, not a syntactic guess.
#
# WHEN TO RUN
#   Before every commit that touches mermaid blocks (new walkthroughs, edits
#   to existing diagrams, or template changes). CI-safe: exit code = number
#   of failed blocks.
#
# USAGE
#   ./tools/validate-mermaid.sh                    # scan the whole repo
#   ./tools/validate-mermaid.sh path/to/one.md     # scan one file
#
# ONE-TIME SETUP
#   Requires Node 18+. First run downloads @mermaid-js/mermaid-cli (~200 MB
#   because of headless Chromium) into a cache directory under /tmp; that
#   cache is reused across runs. No repo commit of node_modules.

set -u
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${MERMAID_VALIDATOR_CACHE:-/tmp/mermaid_validator_cache}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ---------- ensure mmdc is available ----------
if [ ! -x "$CACHE/node_modules/.bin/mmdc" ]; then
  echo ">> First run: installing @mermaid-js/mermaid-cli into $CACHE (one-time, ~200 MB)"
  mkdir -p "$CACHE"
  ( cd "$CACHE" && npm install --silent --no-save --no-audit --no-fund @mermaid-js/mermaid-cli >/dev/null 2>&1 )
fi
MMDC="$CACHE/node_modules/.bin/mmdc"

# ---------- pick files to scan ----------
if [ $# -gt 0 ]; then
  FILE_ARGS=("$@")
else
  FILE_ARGS=("$REPO_ROOT")
fi

# ---------- extract every mermaid block ----------
python3 - "$WORK" "${FILE_ARGS[@]}" <<'PYEOF'
import os, re, sys
WORK = sys.argv[1]
targets = sys.argv[2:]
MERMAID = re.compile(r'```mermaid\n(.*?)\n```', re.DOTALL)

files = []
for t in targets:
    if os.path.isfile(t):
        files.append(t)
    else:
        for dp, _, fs in os.walk(t):
            if '/.git' in dp or '/node_modules' in dp or '/leetlens-import' in dp:
                continue
            for fn in fs:
                if fn.endswith('.md'):
                    files.append(os.path.join(dp, fn))

idx = 0
manifest = []
for p in files:
    try:
        txt = open(p, encoding='utf-8').read()
    except (UnicodeDecodeError, OSError):
        continue
    for mm in MERMAID.finditer(txt):
        line_no = txt[:mm.start()].count('\n') + 1
        with open(f'{WORK}/{idx:05d}.mmd', 'w') as fh:
            fh.write(mm.group(1))
        manifest.append(f'{idx:05d}\t{p}\t{line_no}')
        idx += 1
open(f'{WORK}/manifest.tsv', 'w').write('\n'.join(manifest))
print(f'Extracted {idx} mermaid blocks from {len(files)} .md files')
PYEOF

# ---------- run mmdc on each ----------
total=0
failures=0
failure_log="$WORK/failures.log"
: > "$failure_log"

for f in "$WORK"/*.mmd; do
  total=$((total+1))
  idx=$(basename "$f" .mmd)
  if ! "$MMDC" -i "$f" -o "$WORK/$idx.svg" 2>"$WORK/$idx.err" >/dev/null; then
    failures=$((failures+1))
    info=$(grep "^${idx}"$'\t' "$WORK/manifest.tsv")
    printf '\n❌ %s\n' "$info" | tee -a "$failure_log"
    # first useful error line (skip stack)
    grep -m1 'Error:' "$WORK/$idx.err" | sed 's/^/   /' | tee -a "$failure_log"
    grep -A1 -m1 '\^' "$WORK/$idx.err" | sed 's/^/   /' | tee -a "$failure_log"
  fi
done

echo
echo "=== SUMMARY ==="
echo "Total blocks:  $total"
echo "Passed:        $((total-failures))"
echo "Failed:        $failures"
if [ "$failures" -gt 0 ]; then
  echo
  echo "Full failure log: $failure_log"
  echo "Per-block stderr: $WORK/<idx>.err  (temp dir preserved on failure)"
  # keep temp dir for post-mortem
  trap - EXIT
  echo "Temp dir kept at: $WORK"
  exit "$failures"
fi
exit 0
