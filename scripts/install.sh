#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"
DATA_DIR="${HOME}/.local/share"
CONFIG="${HOME}/.local/state/noctalia/settings.toml"

command -v python3 >/dev/null || { echo "Python 3 is required." >&2; exit 1; }
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
  echo "Python 3.11 or newer is required (tomllib is used)." >&2
  exit 1
}
command -v systemctl >/dev/null || { echo "systemd is required." >&2; exit 1; }

mkdir -p "$BIN_DIR" "$UNIT_DIR" "$DATA_DIR"
install -Dm755 "$ROOT/src/noctalia_app_customize.py" "$BIN_DIR/noctalia-app-customize"
install -Dm755 "$ROOT/src/noctalia_dock_watch.py" "$BIN_DIR/noctalia-dock-watch"
install -Dm644 "$ROOT/systemd/noctalia-dock-watch.service" "$UNIT_DIR/noctalia-dock-watch.service"

systemctl --user daemon-reload
systemctl --user enable --now noctalia-dock-watch.service

echo
echo "Noctalia Dock App Customizer installed."
echo "Watcher service: systemctl --user status noctalia-dock-watch.service"
echo "Log: ~/.local/state/noctalia-dock-watch.log"
if [[ ! -f "$CONFIG" ]]; then
  echo "Note: Noctalia settings were not found yet at $CONFIG"
fi
if ! command -v zenity >/dev/null; then
  echo "Note: install zenity to use the graphical rename and icon dialogs."
fi
