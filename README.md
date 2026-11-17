<div align="center">

# Noctalia Dock App Customizer

### Make every pinned app feel like yours.

[🇷🇺 Русский](README.ru.md) · [🇬🇧 English](README.en.md)

![Linux](https://img.shields.io/badge/platform-Linux-2ea44f?style=flat-square&logo=linux&logoColor=white)
![Noctalia](https://img.shields.io/badge/desktop-Noctalia-7c3aed?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-2563eb?style=flat-square)
![Status](https://img.shields.io/badge/status-public%20testing-f59e0b?style=flat-square)

**A lightweight utility for customizing app icons and names in Noctalia Dock.**

</div>

---

## ✨ At a glance

| 🖼️ Change icon | ✏️ Rename app | ↩️ Reset appearance |
|:--:|:--:|:--:|
| Pick a custom image | Choose a display name | Restore original values |

The utility integrates through standard Linux **Desktop Actions**. A user-level watcher keeps launcher entries in sync with the apps pinned to the Dock.

> [!NOTE]
> This is an independent community utility, not an official Noctalia plugin. It does not patch or replace Noctalia.

## 🚀 Quick start

**Requirements:** Linux, Noctalia, Python 3.11+, systemd user session, and Zenity for graphical dialogs.

```bash
git clone https://github.com/lkmorwwin-cmyk/noctalia-dock-app-customizer.git
cd noctalia-dock-app-customizer
bash scripts/install.sh
```

To uninstall:

```bash
bash scripts/uninstall.sh
```

## 🌍 Documentation

- 🇷🇺 **[Русская документация](README.ru.md)**
- 🇬🇧 **[English documentation](README.en.md)**

## 🧭 Project structure

| Path | Purpose |
|:--|:--|
| `src/noctalia_app_customize.py` | Desktop Actions and icon/name editing |
| `src/noctalia_dock_watch.py` | Pinned-app watcher and managed-file cleanup |
| `systemd/` | User service unit |
| `scripts/` | Installer and uninstaller |

## 🧪 Tests

Run the standard-library test suite from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

## 🔍 Service and logs

```bash
systemctl --user status noctalia-dock-watch.service
journalctl --user -u noctalia-dock-watch.service -f
tail -f ~/.local/state/noctalia-dock-watch.log
```

The watcher log rotates at 256 KiB and keeps one previous copy.

## 🛡️ Safety notes

- System desktop-entry files are not modified.
- The watcher records launcher copies it creates in a manifest.
- Unpin cleanup is restricted to files recorded in that manifest.
- Existing user-level desktop entries are not deleted by the watcher.

---

<div align="center">

**Personalize your Dock. Keep your system files untouched.**

MIT License · Contributions welcome

</div>
