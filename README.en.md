<div align="center">

# Noctalia Dock App Customizer

### Make every pinned app feel like yours.

[🇷🇺 Русский](README.ru.md) · [🇬🇧 English](README.en.md)

![Linux](https://img.shields.io/badge/platform-Linux-2ea44f?style=flat-square&logo=linux&logoColor=white)
![Noctalia](https://img.shields.io/badge/desktop-Noctalia-7c3aed?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-2563eb?style=flat-square)
![Status](https://img.shields.io/badge/status-public%20testing-f59e0b?style=flat-square)

**A lightweight utility for changing application icons and names in Noctalia Dock.**

</div>

---

## ✨ Features

| Action | Result |
|:--|:--|
| 🖼️ **Change icon** | Pick an image using a graphical file dialog |
| ✏️ **Rename** | Set a custom display name |
| ↩️ **Reset appearance** | Restore the original name and icon |
| ⚙️ **Automatic tracking** | Watch the pinned application list |
| 🧹 **Careful cleanup** | Remove only launcher copies created by this utility |
| 🔁 **Background operation** | Run as a systemd user service |

## 🚀 Quick installation

**Requirements:** Linux, Noctalia, Python 3.11+, and a systemd user session. Zenity is required for graphical dialogs.

```bash
git clone https://github.com/lkmorwwin-cmyk/noctalia-dock-app-customizer.git
cd noctalia-dock-app-customizer
./scripts/install.sh
```

To uninstall:

```bash
./scripts/uninstall.sh
```

## 🧩 How it works

The utility uses standard **Desktop Actions**. It creates user-level launcher copies and adds actions that Noctalia Dock can display in its context menu.

1. Reads the pinned-app list from Noctalia settings.
2. Locates the corresponding system `.desktop` launchers.
3. Creates user-level copies in `~/.local/share/applications`.
4. Adds actions for changing the icon, renaming, and resetting.
5. A background service tracks changes to the pinned-app list.

> [!NOTE]
> This is an independent community utility, not an official Noctalia plugin and not a modification of Noctalia's source code.

## 🔍 Service and logs

```bash
systemctl --user status noctalia-dock-watch.service
journalctl --user -u noctalia-dock-watch.service -f
tail -f ~/.local/state/noctalia-dock-watch.log
```

The watcher log rotates at 256 KiB and keeps one previous copy.

## 🛡️ Safety

- System desktop-entry files are not modified.
- Created launcher copies are recorded in a manifest.
- Unpin cleanup removes only files listed in that manifest.
- Existing user-level desktop entries are never deleted by the watcher.
- Uninstallation leaves logs and unrelated user data untouched.

## ⚠️ Limitations and compatibility

- Menu actions depend on the Dock supporting Desktop Actions.
- This is not a universal context-menu extension API.
- The Dock may take a moment to refresh after a launcher changes.
- Flatpak, Snap, and non-standard installation methods need separate verification.
- Compatibility with every Noctalia version and Linux distribution is not yet guaranteed.
- If an application already has a user-level desktop entry, the utility adds actions to it; that file is not treated as a watcher-created copy and is not automatically removed.

## 🗺️ Roadmap

- [x] Move the watcher and customizer into standalone source files.
- [x] Add installation and uninstallation scripts.
- [ ] Add automated tests.
- [ ] Verify Flatpak/Snap support.
- [ ] Test more distributions and Noctalia versions.
- [ ] Publish the first stable release.

## 🤝 Contributing

Bug reports and suggestions are welcome. Include your distribution, Noctalia version, application installation method, launcher ID, and a relevant log excerpt with personal data removed.

## 📄 License

[MIT](LICENSE).

---

<div align="center">

**More personality. Less manual work.**

[🇷🇺 Русская документация](README.ru.md)

</div>
