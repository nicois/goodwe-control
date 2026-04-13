#!/usr/bin/env bash
# Sync the vendored smart_battery/ from the canonical source in foxess-control.
#
# Usage:
#   scripts/sync_smart_battery.sh                  # from main branch
#   scripts/sync_smart_battery.sh some-branch      # from a specific branch
set -euo pipefail

CANONICAL_REPO="https://github.com/nicois/foxess-control.git"
BRANCH="${1:-main}"
DEST="custom_components/goodwe_battery_control/smart_battery"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "Fetching smart_battery/ from foxess-control@${BRANCH}..."
git clone --depth 1 --branch "$BRANCH" --filter=blob:none --sparse \
    "$CANONICAL_REPO" "$TMPDIR/canonical" 2>&1 | tail -1
cd "$TMPDIR/canonical" && git sparse-checkout set smart_battery && cd -

echo "Replacing $DEST..."
rm -rf "$DEST"
cp -r "$TMPDIR/canonical/smart_battery" "$DEST"
# Remove any pycache
find "$DEST" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "Done. Verify with: diff -r $TMPDIR/canonical/smart_battery $DEST"
echo "Run tests:        pytest tests/"
