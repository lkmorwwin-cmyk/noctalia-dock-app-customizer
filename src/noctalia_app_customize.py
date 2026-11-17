#!/usr/bin/env python3
"""Customize a user-level desktop entry with Noctalia Dock actions."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

HOME = Path.home()
DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share"))
APPS = DATA_HOME / "applications"
STATE = DATA_HOME / "noctalia-app-customizer"
ICONS = DATA_HOME / "icons/noctalia-app-customizer"
SCRIPT = Path(__file__).resolve()
PYTHON = Path(sys.executable).resolve()
def is_russian() -> bool:
    """Detect Russian from the desktop session locale."""
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(variable, "").strip()
        if not value:
            continue
        locale_name = value.split(":", 1)[0].split(".", 1)[0].split("@", 1)[0]
        return locale_name.lower().startswith("ru")
    return False

def tr(english: str, russian: str) -> str:
    return russian if is_russian() else english

ACTIONS = (
    ("NoctaliaChangeIcon", "Change icon", "Сменить иконку", "icon"),
    ("NoctaliaRename", "Rename", "Переименовать", "rename"),
    ("NoctaliaReset", "Reset appearance", "Сбросить оформление", "reset"),
)

def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise

def filename_for(app_id: str) -> str:
    if not app_id or app_id in {".", ".."} or "/" in app_id or "\\" in app_id:
        raise ValueError(tr("Invalid desktop file ID", "Недопустимый идентификатор desktop-файла"))
    return app_id if app_id.endswith(".desktop") else app_id + ".desktop"

def desktop_path(app_id: str) -> Path:
    path = APPS / filename_for(app_id)
    if not path.is_file():
        raise FileNotFoundError(tr("User desktop file not found: ", "Пользовательский desktop-файл не найден: ") + str(path))
    return path

def metadata_path(app_id: str) -> Path:
    return STATE / (Path(filename_for(app_id)).stem + ".json")

def read_main(lines: list[str]) -> dict[str, str]:
    inside, values = False, {}
    for line in lines:
        item = line.strip()
        if item.startswith("[") and item.endswith("]"):
            inside = item == "[Desktop Entry]"
        elif inside and "=" in item and not item.startswith("#"):
            key, value = item.split("=", 1)
            values[key] = value
    return values

def dialog(*args: str):
    return subprocess.run(["zenity", *args], text=True, capture_output=True, check=False)

def notify(message: str, error: bool = False) -> None:
    if shutil.which("zenity"):
        dialog("--error" if error else "--info", "--title=Noctalia Dock App Customizer", "--text=" + message)

def quote_exec(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return '"' + value + '"'

def save_baseline(path: Path, app_id: str) -> Path:
    meta = metadata_path(app_id)
    if not meta.exists():
        legacy = STATE / (filename_for(app_id) + ".json")
        if legacy.is_file():
            STATE.mkdir(parents=True, exist_ok=True)
            legacy.replace(meta)
            return meta
        values = read_main(path.read_text(encoding="utf-8", errors="replace").splitlines())
        payload = {"Name": values.get("Name", Path(filename_for(app_id)).stem),
                   "Icon": values.get("Icon", ""), "CustomIcon": ""}
        atomic_write(meta, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return meta

def edit_main(path: Path, name: str | None = None, icon: str | None = None) -> None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out, inside, name_done, icon_done = [], False, False, False
    for line in lines:
        item = line.strip()
        if item.startswith("[") and item.endswith("]"):
            if inside:
                if name is not None and not name_done:
                    out.extend(["Name=" + name, "Name[ru]=" + name])
                    name_done = True
                if icon is not None and not icon_done:
                    out.append("Icon=" + icon)
                    icon_done = True
            inside = item == "[Desktop Entry]"
            out.append(line)
            continue
        if inside and "=" in item and not item.startswith("#"):
            key = item.split("=", 1)[0]
            if name is not None and (key == "Name" or key.startswith("Name[")):
                if not name_done:
                    out.extend(["Name=" + name, "Name[ru]=" + name])
                    name_done = True
                continue
            if icon is not None and key == "Icon":
                if not icon_done:
                    out.append("Icon=" + icon)
                    icon_done = True
                continue
        out.append(line)
    if inside:
        if name is not None and not name_done:
            out.extend(["Name=" + name, "Name[ru]=" + name])
        if icon is not None and not icon_done:
            out.append("Icon=" + icon)
    atomic_write(path, "\n".join(out) + "\n")

def add_actions(app_id: str) -> None:
    path = desktop_path(app_id)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == "[Desktop Entry]"), None)
    if start is None:
        raise ValueError(tr("Missing [Desktop Entry] section", "Отсутствует секция [Desktop Entry]"))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("[")), len(lines))
    action_index = next((i for i in range(start + 1, end) if lines[i].startswith("Actions=")), None)
    current = [x for x in lines[action_index].split("=", 1)[1].split(";") if x] if action_index is not None else []
    for action_id, _, _, _ in ACTIONS:
        if action_id not in current:
            current.append(action_id)
    action_line = "Actions=" + ";".join(current) + ";"
    if action_index is None:
        lines.insert(end, action_line)
    else:
        lines[action_index] = action_line
    prefix = quote_exec(str(PYTHON)) + " " + quote_exec(str(SCRIPT))
    for action_id, label, label_ru, command in ACTIONS:
        section = "[Desktop Action " + action_id + "]"
        if section not in lines:
            lines.extend(["", section, "Name=" + label, "Name[ru]=" + label_ru,
                          "Exec=" + prefix + " " + command + " " + quote_exec(filename_for(app_id))])
    atomic_write(path, "\n".join(lines) + "\n")


def remove_actions(path: Path) -> None:
    action_ids = {item[0] for item in ACTIONS}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    output: list[str] = []
    skip_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section_id = stripped[len("[Desktop Action "):-1] if stripped.startswith("[Desktop Action ") else ""
            skip_section = section_id in action_ids
            if skip_section:
                continue
        if skip_section:
            continue
        if stripped.startswith("Actions="):
            remaining = [item for item in stripped.split("=", 1)[1].split(";") if item and item not in action_ids]
            if remaining:
                output.append("Actions=" + ";".join(remaining) + ";")
            continue
        output.append(line)
    atomic_write(path, "\n".join(output) + "\n")


def uninstall_app(path: Path, app_id: str) -> None:
    meta = metadata_path(app_id)
    if meta.is_file():
        original = json.loads(meta.read_text(encoding="utf-8"))
        edit_main(path, name=original.get("Name", ""), icon=original.get("Icon", ""))
        remove_custom_icon(original.get("CustomIcon", ""))
        meta.unlink(missing_ok=True)
    remove_actions(path)

def update_meta(meta: Path, **changes: str) -> dict:
    data = json.loads(meta.read_text(encoding="utf-8"))
    data.update(changes)
    atomic_write(meta, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return data

def remove_custom_icon(value: str) -> None:
    if not value:
        return
    candidate = Path(value)
    try:
        candidate.resolve().relative_to(ICONS.resolve())
    except (ValueError, OSError):
        return
    candidate.unlink(missing_ok=True)

def main() -> int:
    if len(sys.argv) != 3:
        print(tr("Usage: noctalia-app-customize <install|icon|rename|reset|uninstall> <app.desktop>", "Использование: noctalia-app-customize <install|icon|rename|reset|uninstall> <app.desktop>"), file=sys.stderr)
        return 2
    command, app_id = sys.argv[1:3]
    try:
        filename = filename_for(app_id)
        path = desktop_path(filename)
        if command == "install":
            add_actions(filename)
            return 0
        if command == "uninstall":
            uninstall_app(path, filename)
            return 0
        meta = save_baseline(path, filename)
        values = read_main(path.read_text(encoding="utf-8", errors="replace").splitlines())
        if command == "rename":
            result = dialog("--entry", "--title=" + tr("Rename application", "Переименовать приложение"), "--text=" + tr("New name:", "Новое название:"),
                            "--entry-text=" + values.get("Name", ""))
            if result.returncode == 0 and result.stdout.strip():
                edit_main(path, name=result.stdout.strip().replace("\n", " "))
                notify(tr("Application name updated.", "Название приложения изменено."))
        elif command == "icon":
            result = dialog("--file-selection", "--title=" + tr("Choose an icon", "Выбрать иконку"),
                            "--file-filter=" + tr("Images", "Изображения") + " | *.png *.svg *.jpg *.jpeg *.webp *.ico")
            if result.returncode == 0 and result.stdout.strip():
                source = Path(result.stdout.strip()).expanduser()
                if not source.is_file():
                    raise FileNotFoundError(tr("Selected image does not exist", "Выбранный файл изображения не существует"))
                ICONS.mkdir(parents=True, exist_ok=True)
                destination = ICONS / (Path(filename).stem + source.suffix.lower())
                shutil.copy2(source, destination)
                previous = json.loads(meta.read_text(encoding="utf-8")).get("CustomIcon", "")
                edit_main(path, icon=str(destination))
                update_meta(meta, CustomIcon=str(destination))
                if previous and previous != str(destination):
                    remove_custom_icon(previous)
                notify(tr("Application icon updated.", "Иконка приложения изменена."))
        elif command == "reset":
            if not meta.exists():
                notify(tr("No saved original appearance was found.", "Сохранённое исходное оформление не найдено."))
                return 0
            original = json.loads(meta.read_text(encoding="utf-8"))
            edit_main(path, name=original.get("Name", ""), icon=original.get("Icon", ""))
            remove_custom_icon(original.get("CustomIcon", ""))
            meta.unlink(missing_ok=True)
            notify(tr("Original appearance restored.", "Исходное оформление восстановлено."))
        else:
            print(tr("Unknown command: ", "Неизвестная команда: ") + command, file=sys.stderr)
            return 2
        return 0
    except Exception as exc:
        print(tr("noctalia-app-customize: ", "noctalia-app-customize: ") + str(exc), file=sys.stderr)
        notify(tr("Error: ", "Ошибка: ") + str(exc), error=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
