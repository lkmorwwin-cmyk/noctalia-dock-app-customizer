<div align="center">

# Noctalia Dock App Customizer

### Make every pinned app feel like yours.

[🇷🇺 Русский](README.ru.md) · [🇬🇧 English](README.en.md)

![Linux](https://img.shields.io/badge/platform-Linux-2ea44f?style=flat-square&logo=linux&logoColor=white)
![Noctalia](https://img.shields.io/badge/desktop-Noctalia-7c3aed?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-2563eb?style=flat-square)
![Status](https://img.shields.io/badge/status-early%20development-f59e0b?style=flat-square)

**A small, automatic desktop-entry customizer for Noctalia Dock.**

</div>

---

## ✨ At a glance

| 🖼️ Change icon | ✏️ Rename app | ↩️ Reset appearance |
|:--:|:--:|:--:|
| Pick a custom image | Choose a display name | Restore original values |

The project integrates with Noctalia through standard Linux **Desktop Actions**. A user-level watcher keeps launcher entries in sync with the apps pinned to the Dock.

> [!NOTE]
> This is an independent community utility. It is **not** an official Noctalia plugin and does not patch or replace Noctalia itself.

## 🌍 Documentation

- 🇷🇺 **[Русская документация](README.ru.md)**
- 🇬🇧 **[English documentation](README.en.md)**

## 🧭 Project status

The repository is being prepared for public testing. Compatibility depends on the desktop environment, application packaging format, and the structure of installed `.desktop` launchers. Features are documented conservatively; see the language-specific guides for current implementation status and limitations.

## 💡 Design goals

- Keep all customizations in the user's home directory.
- Never overwrite an existing user-managed launcher.
- Track files created by the utility and clean up only those files.
- Make changes persistent across logins.
- Keep the background service lightweight and its logs bounded.

---

<div align="center">

**Personalize your Dock. Keep your system files untouched.**

MIT License · Contributions and bug reports are welcome.

</div>
