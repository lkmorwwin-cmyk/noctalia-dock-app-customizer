<div align="center">

# Noctalia Dock App Customizer

### Make every pinned app feel like yours.

[🇷🇺 Русский](README.ru.md) · [🇬🇧 English](README.en.md)

![Linux](https://img.shields.io/badge/platform-Linux-2ea44f?style=flat-square&logo=linux&logoColor=white)
![Noctalia](https://img.shields.io/badge/desktop-Noctalia-7c3aed?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-2563eb?style=flat-square)
![Status](https://img.shields.io/badge/status-early%20development-f59e0b?style=flat-square)

**A lightweight utility for automatically customizing app icons and names in Noctalia Dock.**

</div>

---

## ✨ Features

| Action | Result |
|:--|:--|
| 🖼️ **Change icon** | Pick a custom image using a graphical file dialog |
| ✏️ **Rename** | Set a custom application display name |
| ↩️ **Reset appearance** | Restore the original name and icon |
| ⚙️ **Automatic tracking** | Watch the Dock's pinned application list |
| 🧹 **Careful cleanup** | Remove only files created and tracked by this utility |
| 🔁 **Background operation** | Start automatically as a systemd user service |

## 🧩 How the integration works

The utility uses the standard **Desktop Actions** mechanism from the Desktop Entry Specification. It creates user-level copies of application launcher files and adds actions that Noctalia Dock can display in its context menu.

1. Reads the pinned-app list from Noctalia settings.
2. Locates the corresponding system `.desktop` launchers.
3. Creates user-level copies in `~/.local/share/applications` without modifying system files.
4. Adds actions for changing the icon, renaming, and resetting.
5. A background watcher tracks changes to the pinned-app list.

> [!NOTE]
> This is an independent community utility, not an official Noctalia plugin and not a modification of Noctalia's source code.

## 📦 Requirements

- Linux with Desktop Entry Specification support.
- Noctalia Dock.
- Python 3.
- `systemd --user` for automatic background operation.
- `zenity` for graphical dialogs.
- Applications with discoverable desktop-entry files.

Launcher paths and application ID formats vary by distribution and installation method.

## 🚀 Installation

The project is in early preparation for public testing. An installer and setup instructions will be published after the implementation has been verified in a clean user session.

For now, do not run installation commands from unverified sources. Watch the [Releases](../../releases) page for updates.

## 🛡️ Safety principles

- System desktop-entry files must remain untouched.
- Existing user-managed launchers must never be overwritten.
- Cleanup must be limited to files created by the utility and recorded in its manifest.
- Custom icons and metadata should be stored separately from system files.
- Back up user-level launcher files before testing on a daily-use system.

## ⚠️ Limitations and compatibility

- Menu actions depend on the Dock supporting Desktop Actions.
- This is not a universal context-menu extension API.
- The Dock may take a short while to refresh after a launcher changes.
- Flatpak, Snap, and non-standard installation methods need separate verification.
- Compatibility with every Noctalia version and Linux distribution is not yet claimed.

## 🗺️ Roadmap

- [ ] Bring in and verify the original watcher and customizer implementation.
- [ ] Build an installer and safe upgrade flow.
- [ ] Add tests for desktop-file discovery and application ID handling.
- [ ] Verify correct behaviour when apps are pinned and unpinned.
- [ ] Test Flatpak/Snap support.
- [ ] Publish the first stable release.

## 🤝 Contributing

Bug reports and suggestions are welcome. When opening an issue, include:

- distribution and version;
- Noctalia version;
- application installation method;
- application ID and desktop-file path;
- relevant watcher log excerpt with personal data removed.

## 📄 License

This project is distributed under the [MIT License](LICENSE).

---

<div align="center">

**More personality. Less manual work.**

[🇷🇺 Русская документация](README.ru.md)

</div>
