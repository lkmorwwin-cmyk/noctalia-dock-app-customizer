#!/usr/bin/env python3
"""Watch Noctalia pinned apps and manage only launchers created by this tool."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

HOME = Path.home()
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local/state"))
CONFIG = STATE_HOME / "noctalia/settings.toml"
LOCAL_APPS = DATA_HOME / "applications"
CUSTOMIZER = HOME / ".local/bin/noctalia-app-customize"
STATE = DATA_HOME / "noctalia-app-customizer"
ICONS = DATA_HOME / "icons/noctalia-app-customizer"
LOG = STATE_HOME / "noctalia-dock-watch.log"
MANIFEST = STATE_HOME / "noctalia-dock-managed.json"
TRACKED = STATE_HOME / "noctalia-dock-actions.json"
MAX_LOG = 256 * 1024
POLL_SECONDS = 3
OWN_ACTIONS = ("NoctaliaChangeIcon", "NoctaliaRename", "NoctaliaReset")


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if LOG.exists() and LOG.stat().st_size >= MAX_LOG:
        backup = LOG.with_suffix(".log.1")
        backup.unlink(missing_ok=True)
        LOG.replace(backup)
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(time.strftime("%F %T ") + message + "\n")


def atomic_json(path: Path, value) -> None:
    """Write JSON atomically without following a predictable temporary path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def valid_filename(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.endswith(".desktop")
        and value not in {".desktop", "..desktop"}
        and not any(char in value for char in ("/", "\\", "\x00"))
        and Path(value).name == value
    )


def save_manifest(managed: set[str]) -> None:
    atomic_json(MANIFEST, sorted(managed))


def _load_names(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("expected a JSON list")
        return {item for item in data if valid_filename(item)}
    except FileNotFoundError:
        return set()
    except (OSError, ValueError, TypeError) as exc:
        log("Could not read " + path.name + ": " + str(exc))
        return set()


def load_manifest() -> set[str]:
    if MANIFEST.exists():
        return _load_names(MANIFEST)

    # Import entries recorded by the previous version's log.
    managed: set[str] = set()
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.search(r"Создан пользовательский desktop-файл: (.+)$", line)
            if match and valid_filename(match.group(1).strip()):
                managed.add(match.group(1).strip())
    save_manifest(managed)
    return managed


def load_tracked() -> set[str]:
    return _load_names(TRACKED)


def save_tracked(tracked: set[str]) -> None:
    atomic_json(TRACKED, sorted(tracked))


def has_our_actions(path: Path) -> bool:
    """Recognize our action sections before ever editing/removing a launcher."""
    try:
        if path.is_symlink() or not path.is_file():
            return False
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any("[Desktop Action " + action + "]" in content for action in OWN_ACTIONS)


def remove_actions_for(filename: str) -> bool:
    if not valid_filename(filename):
        return False
    target = LOCAL_APPS / filename
    # Do not let stale tracking metadata modify a file that has since been
    # replaced by the user or by another application.
    if not has_our_actions(target):
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(CUSTOMIZER), "uninstall", filename],
            check=False, capture_output=True, text=True,
        )
        if result.returncode:
            log("Could not remove custom actions from " + filename + ": " + result.stderr.strip())
            return False
        return True
    except OSError as exc:
        log("Could not run customizer cleanup for " + filename + ": " + str(exc))
        return False


def normalize_id(app_id: str) -> str:
    """Convert a pinned application ID to its desktop filename."""
    if (
        not app_id or app_id in {".", ".."}
        or any(char in app_id for char in ("/", "\\", "\x00"))
    ):
        raise ValueError("Invalid pinned application ID: " + repr(app_id))
    return app_id + ".desktop"


def data_directories() -> list[Path]:
    configured = os.environ.get("XDG_DATA_DIRS")
    system_dirs = configured.split(":") if configured else ["/usr/local/share", "/usr/share"]
    paths = [DATA_HOME, *(Path(p) for p in system_dirs if p),
             Path("/usr/local/share"), Path("/usr/share")]
    return list(dict.fromkeys(paths))


def _desktop_candidate(candidate: Path, data_directory: Path) -> Path | None:
    """Return a regular launcher, allowing only trusted Flatpak export symlinks."""
    if candidate.is_symlink():
        # Flatpak deliberately exposes app launchers through symlinks in
        # <installation>/exports/share/applications. Do not follow arbitrary
        # symlinks from user or system application directories.
        if not (
            data_directory.name == "share"
            and data_directory.parent.name == "exports"
            and data_directory.parent.parent.name == "flatpak"
        ):
            return None
        try:
            app_root = (data_directory.parent.parent / "app").resolve(strict=True)
            resolved = candidate.resolve(strict=True)
            relative = resolved.relative_to(app_root)
        except (OSError, ValueError, RuntimeError):
            return None
        if (
            len(relative.parts) < 4
            or relative.parts[-4:-1] != ("export", "share", "applications")
            or not resolved.is_file()
        ):
            return None
        return resolved
    return candidate if candidate.is_file() else None


def find_desktop(filename: str) -> Path | None:
    if not valid_filename(filename):
        return None
    for directory in data_directories():
        root = directory / "applications"
        direct = root / filename
        found = _desktop_candidate(direct, directory)
        if found is not None:
            return found
        if root.is_dir():
            try:
                candidates = root.rglob(filename)
                for candidate in candidates:
                    found = _desktop_candidate(candidate, directory)
                    if found is not None:
                        return found
            except OSError:
                pass
    return None


def metadata_path(filename: str) -> Path:
    if not valid_filename(filename):
        raise ValueError("Invalid desktop filename")
    return STATE / (Path(filename).stem + ".json")


def remove_custom_icon(filename: str) -> None:
    meta = metadata_path(filename)
    if not meta.is_file() or meta.is_symlink():
        return
    try:
        custom_icon = json.loads(meta.read_text(encoding="utf-8")).get("CustomIcon", "")
        if custom_icon:
            candidate = Path(custom_icon)
            candidate.resolve().relative_to(ICONS.resolve())
            if candidate.is_file() and not candidate.is_symlink():
                candidate.unlink()
    except (OSError, ValueError, TypeError):
        pass


def remove_managed_file(filename: str, managed: set[str]) -> None:
    if not valid_filename(filename):
        return
    target = LOCAL_APPS / filename
    # A manifest entry alone is insufficient: a user may have replaced the
    # managed copy. Only delete a regular file that still carries our marker.
    if target.is_symlink():
        log("Preserving symlink in place of managed launcher: " + filename)
        return
    if target.exists() and not has_our_actions(target):
        log("Preserving replaced or unrecognized launcher: " + filename)
        return
    if target.is_file():
        try:
            target.unlink()
            log("Removed managed launcher: " + filename)
        except OSError as exc:
            log("Could not remove " + filename + ": " + str(exc))
            return
    remove_custom_icon(filename)
    meta = metadata_path(filename)
    if meta.is_file() and not meta.is_symlink():
        meta.unlink(missing_ok=True)
    managed.discard(filename)
    save_manifest(managed)


def process_pinned(managed: set[str]) -> set[str]:
    if not CONFIG.is_file():
        log("No Noctalia settings file at " + str(CONFIG))
        return managed
    try:
        settings = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
        dock = settings.get("dock", {})
        if not isinstance(dock, dict):
            raise ValueError("dock settings must be a table")
        pinned = dock.get("pinned", [])
        if not isinstance(pinned, list):
            raise ValueError("dock.pinned must be a list")
        pinned_files = {normalize_id(item) for item in pinned if isinstance(item, str) and item}
    except Exception as exc:
        log("Could not parse Noctalia settings: " + str(exc))
        return managed

    tracked = load_tracked()
    for filename in sorted(tracked - pinned_files):
        remove_actions_for(filename)
        if filename in managed:
            remove_managed_file(filename, managed)
        # Do not delete metadata for a file that may have been replaced.
        tracked.discard(filename)
        save_tracked(tracked)

    for filename in sorted(pinned_files):
        target = LOCAL_APPS / filename
        if target.is_symlink():
            log("Refusing to customize symlink: " + filename)
            continue
        if not target.exists():
            source = find_desktop(filename)
            if source is None:
                log("No desktop entry found for " + filename)
                continue
            try:
                LOCAL_APPS.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                managed.add(filename)
                save_manifest(managed)
                log("Created managed desktop entry: " + filename)
            except OSError as exc:
                log("Could not create " + filename + ": " + str(exc))
                continue
        elif not target.is_file():
            log("Refusing to customize non-regular path: " + filename)
            continue
        try:
            result = subprocess.run(
                [sys.executable, str(CUSTOMIZER), "install", filename],
                check=False, capture_output=True, text=True,
            )
            if result.returncode:
                log("Customizer failed for " + filename + ": " + result.stderr.strip())
            else:
                tracked.add(filename)
                save_tracked(tracked)
        except OSError as exc:
            log("Could not launch customizer for " + filename + ": " + str(exc))
    return managed


def cleanup_all(managed: set[str]) -> None:
    for filename in sorted(load_tracked()):
        remove_actions_for(filename)
    TRACKED.unlink(missing_ok=True)
    for filename in sorted(managed.copy()):
        remove_managed_file(filename, managed)
    MANIFEST.unlink(missing_ok=True)
    log("Managed launcher and custom-action cleanup completed")


def main() -> int:
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in {"--once", "--cleanup"}):
        print("Usage: noctalia-dock-watch [--once|--cleanup]", file=sys.stderr)
        return 2
    managed = load_manifest()
    if len(sys.argv) == 2 and sys.argv[1] == "--cleanup":
        cleanup_all(managed)
        return 0
    if len(sys.argv) == 2 and sys.argv[1] == "--once":
        process_pinned(managed)
        return 0

    log("Watcher started")
    previous_stamp = object()
    while True:
        try:
            stamp = CONFIG.stat().st_mtime_ns if CONFIG.exists() else None
            if stamp != previous_stamp:
                managed = process_pinned(managed)
                previous_stamp = stamp
        except Exception as exc:
            log("Watcher error: " + str(exc))
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
