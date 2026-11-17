#!/usr/bin/env python3
"""Watch Noctalia pinned apps and manage only launchers created by this tool."""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, time, tomllib
from pathlib import Path

HOME = Path.home()
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local/state"))
CONFIG = STATE_HOME / "noctalia/settings.toml"
LOCAL_APPS = DATA_HOME / "applications"
CUSTOMIZER = Path.home() / ".local/bin/noctalia-app-customize"
STATE = DATA_HOME / "noctalia-app-customizer"
ICONS = DATA_HOME / "icons/noctalia-app-customizer"
LOG = STATE_HOME / "noctalia-dock-watch.log"
MANIFEST = STATE_HOME / "noctalia-dock-managed.json"
MAX_LOG = 256 * 1024
POLL_SECONDS = 3

def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if LOG.exists() and LOG.stat().st_size >= MAX_LOG:
        backup = LOG.with_suffix(".log.1")
        backup.unlink(missing_ok=True)
        LOG.replace(backup)
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(time.strftime("%F %T ") + message + "\n")

def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

def save_manifest(managed: set[str]) -> None:
    atomic_json(MANIFEST, sorted(managed))

def load_manifest() -> set[str]:
    if MANIFEST.exists():
        try:
            data = json.loads(MANIFEST.read_text(encoding="utf-8"))
            return {x for x in data if isinstance(x, str) and x.endswith(".desktop")}
        except Exception as exc:
            log("Could not read managed manifest: " + str(exc))
            return set()
    # Import entries recorded by the previous version's log.
    managed = set()
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.search(r"Создан пользовательский desktop-файл: (.+)$", line)
            if match:
                managed.add(match.group(1).strip())
    save_manifest(managed)
    return managed

def normalize_id(app_id: str) -> str:
    if not app_id or app_id in {".", ".."} or "/" in app_id or "\\" in app_id:
        raise ValueError("Invalid pinned application ID: " + repr(app_id))
    return app_id if app_id.endswith(".desktop") else app_id + ".desktop"

def data_directories() -> list[Path]:
    configured = os.environ.get("XDG_DATA_DIRS")
    system_dirs = configured.split(":") if configured else ["/usr/local/share", "/usr/share"]
    paths = [DATA_HOME, *(Path(p) for p in system_dirs if p),
             Path("/usr/local/share"), Path("/usr/share")]
    return list(dict.fromkeys(paths))

def find_desktop(app_id: str) -> Path | None:
    filename = normalize_id(app_id)
    for directory in data_directories():
        root = directory / "applications"
        direct = root / filename
        if direct.is_file():
            return direct
        if root.is_dir():
            try:
                found = next(root.rglob(filename), None)
            except OSError:
                found = None
            if found and found.is_file():
                return found
    return None

def metadata_path(filename: str) -> Path:
    return STATE / (Path(filename).stem + ".json")

def remove_custom_icon(filename: str) -> None:
    meta = metadata_path(filename)
    if not meta.is_file():
        return
    try:
        custom_icon = json.loads(meta.read_text(encoding="utf-8")).get("CustomIcon", "")
        if custom_icon:
            candidate = Path(custom_icon)
            candidate.resolve().relative_to(ICONS.resolve())
            candidate.unlink(missing_ok=True)
    except (OSError, ValueError, TypeError):
        pass

def remove_managed_file(filename: str, managed: set[str]) -> None:
    target = LOCAL_APPS / filename
    if target.is_file():
        try:
            target.unlink()
            log("Removed managed launcher: " + filename)
        except OSError as exc:
            log("Could not remove " + filename + ": " + str(exc))
            return
    remove_custom_icon(filename)
    metadata_path(filename).unlink(missing_ok=True)
    managed.discard(filename)
    save_manifest(managed)

def process_pinned(managed: set[str]) -> set[str]:
    if not CONFIG.is_file():
        log("No Noctalia settings file at " + str(CONFIG))
        return managed
    try:
        settings = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
        pinned = settings.get("dock", {}).get("pinned", [])
        pinned_files = {normalize_id(item) for item in pinned if isinstance(item, str) and item}
    except Exception as exc:
        log("Could not parse Noctalia settings: " + str(exc))
        return managed

    for filename in sorted(managed - pinned_files):
        remove_managed_file(filename, managed)

    for filename in sorted(pinned_files):
        target = LOCAL_APPS / filename
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
        try:
            result = subprocess.run(
                [sys.executable, str(CUSTOMIZER), "install", filename],
                check=False, capture_output=True, text=True,
            )
            if result.returncode:
                log("Customizer failed for " + filename + ": " + result.stderr.strip())
        except OSError as exc:
            log("Could not launch customizer for " + filename + ": " + str(exc))
    return managed

def cleanup_all(managed: set[str]) -> None:
    for filename in sorted(managed.copy()):
        remove_managed_file(filename, managed)
    MANIFEST.unlink(missing_ok=True)
    log("Managed launcher cleanup completed")

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
