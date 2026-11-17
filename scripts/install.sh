#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
UNIT_DIR="${HOME}/.config/systemd/user"
DATA_DIR="${HOME}/.local/share"
CONFIG="${HOME}/.local/state/noctalia/settings.toml"

say() { printf '%s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

python_is_usable() {
  command -v python3 >/dev/null 2>&1 || return 1
  python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}

detect_package_manager() {
  if command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER=pacman
  elif command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER=apt
  elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER=dnf
  elif command -v zypper >/dev/null 2>&1; then
    PKG_MANAGER=zypper
  else
    PKG_MANAGER=""
  fi
}

run_privileged() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    command -v sudo >/dev/null 2>&1 || die "sudo is required to install missing system packages."
    sudo "$@"
  fi
}

install_dependencies() {
  local need_python=0 need_zenity=0
  python_is_usable || need_python=1
  command -v zenity >/dev/null 2>&1 || need_zenity=1

  if [[ "$need_python" -eq 0 && "$need_zenity" -eq 0 ]]; then
    say "Dependencies are already installed."
    return
  fi

  detect_package_manager
  [[ -n "$PKG_MANAGER" ]] || die "Could not detect a supported package manager (pacman, apt, dnf, or zypper). Install Python 3.11+ and Zenity manually, then run this installer again."

  local packages=()
  case "$PKG_MANAGER" in
    pacman)
      [[ "$need_python" -eq 0 ]] || packages+=(python)
      [[ "$need_zenity" -eq 0 ]] || packages+=(zenity)
      say "Installing missing dependencies with pacman: ${packages[*]}"
      run_privileged pacman -S --needed "${packages[@]}"
      ;;
    apt)
      [[ "$need_python" -eq 0 ]] || packages+=(python3)
      [[ "$need_zenity" -eq 0 ]] || packages+=(zenity)
      say "Refreshing APT package lists..."
      run_privileged apt-get update
      say "Installing missing dependencies with APT: ${packages[*]}"
      run_privileged apt-get install -y "${packages[@]}"
      ;;
    dnf)
      [[ "$need_python" -eq 0 ]] || packages+=(python3)
      [[ "$need_zenity" -eq 0 ]] || packages+=(zenity)
      say "Installing missing dependencies with DNF: ${packages[*]}"
      run_privileged dnf install -y "${packages[@]}"
      ;;
    zypper)
      [[ "$need_python" -eq 0 ]] || packages+=(python3)
      [[ "$need_zenity" -eq 0 ]] || packages+=(zenity)
      say "Installing missing dependencies with Zypper: ${packages[*]}"
      run_privileged zypper --non-interactive install "${packages[@]}"
      ;;
  esac

  python_is_usable || die "Python 3.11 or newer is required. The package manager did not provide a suitable python3. Install Python 3.11+ manually and run this installer again."
  command -v zenity >/dev/null 2>&1 || die "Zenity installation did not succeed. Install the 'zenity' package and run this installer again."
}

install_dependencies

command -v systemctl >/dev/null 2>&1 || die "systemd is required; systemctl was not found."
systemctl --user show-environment >/dev/null 2>&1 || die "A running systemd user session is required. Log in to your desktop session and run the installer again."

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
