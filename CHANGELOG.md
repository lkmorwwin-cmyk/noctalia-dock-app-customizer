# Changelog

All notable changes to Noctalia Dock App Customizer are documented here.

## [1.1.0] — 2026-11-17

### Documentation
- Add source-based update instructions, including reinstalling user-level files and restarting the watcher service.
- Update documentation version references to 1.1.0.

### Installer
- Automatically detect pacman, APT, DNF, or Zypper and install missing Python 3.11+ and Zenity dependencies.
- Verify the Python version and the availability of a running systemd user session before installing the utility.
- Keep Noctalia and systemd as pre-existing environment requirements; they are not installed by the script.

### Verification
- Installer syntax and execution checks passed on CachyOS; all dependencies were already present.
- All 21 automated tests passed; Python compilation completed successfully.
- GitHub Actions CI passed for the release candidate commit.

## [1.0.0] — 2026-11-17

First stable release.

### Features
- Add **Change icon**, **Rename**, and **Reset appearance** actions to Noctalia Dock context menus.
- Automatically track pinned applications and remove only recognized managed launcher copies when applications are unpinned.
- Preserve pre-existing user desktop entries and avoid modifying system desktop files.
- Automatically select Russian or English labels based on the desktop session locale.
- Refresh managed launcher source fields after package updates while preserving custom names, icons, and Noctalia actions.
- Support validated Flatpak-exported desktop launcher symlinks.

### Reliability and security
- Validate launcher filenames and manifest data.
- Reject arbitrary symlinks and preserve replaced or unrecognized launchers.
- Write state files atomically with private permissions.
- Add automated tests for launcher editing, Flatpak discovery, source synchronization, and safe cleanup.

### Verification
- 21 automated tests passed on CachyOS.
- Python compilation and shell-script syntax checks passed.
- The user-level systemd service installed, restarted, and ran successfully.
- Runtime launcher discovery was checked with Bottles (Flatpak) and Happ (AUR/yay); existing user-launcher priority was checked with Termius.

### Installation
- Install from source using `scripts/install.sh`.
- Uninstall using `scripts/uninstall.sh`.
