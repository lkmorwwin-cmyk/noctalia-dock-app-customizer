#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"

if command -v systemctl >/dev/null; then
  systemctl --user disable --now noctalia-dock-watch.service 2>/dev/null || true
fi

WATCHER="$BIN_DIR/noctalia-dock-watch"
if [[ -x "$WATCHER" ]]; then
  "$WATCHER" --cleanup || {
    echo "Managed launcher cleanup failed; keeping state for manual recovery." >&2
    exit 1
  }
fi

rm -f "$UNIT_DIR/noctalia-dock-watch.service"
rm -f "$BIN_DIR/noctalia-app-customize" "$BIN_DIR/noctalia-dock-watch"
if command -v systemctl >/dev/null; then
  systemctl --user daemon-reload
fi

echo "Noctalia Dock App Customizer removed."
echo "The watcher removes only launcher copies recorded in its managed manifest."
echo "Logs and unrelated user data are left untouched."
