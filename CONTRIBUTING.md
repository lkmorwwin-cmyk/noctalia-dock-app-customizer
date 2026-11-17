<div align="center">

# Contributing

**Thanks for helping improve Noctalia Dock App Customizer.**

Small, focused contributions are very welcome.

</div>

---

## Before opening an issue

Please check whether the issue has already been reported. Include the details below when relevant:

| Detail | Example / notes |
|:--|:--|
| Linux distribution | Name and version |
| Noctalia version | Exact version if possible |
| Application source | Native package, Flatpak, Snap, etc. |
| Desktop-file ID and path | The affected `.desktop` entry |
| Logs | Only the relevant excerpt; remove usernames and other personal information |

## Development guidelines

1. Keep changes focused and explain their user-visible impact.
2. Do not modify system desktop-entry files.
3. Never overwrite or delete pre-existing user-managed launchers.
4. Restrict cleanup to files explicitly tracked as created by this project.
5. Avoid adding dependencies unless they are necessary and documented.
6. Update both Russian and English documentation when behavior or setup changes.
7. Add or update tests for behavior changes where practical.

## Pull requests

A useful pull request description covers:

- **Problem:** what is currently wrong or missing?
- **Approach:** what did you change, and why?
- **Verification:** which tests or manual checks did you run?
- **Compatibility:** are there distribution- or version-specific assumptions?

> [!IMPORTANT]
> Do not claim compatibility that has not been tested. If a check was not performed, say so clearly.

## Local checks

Run these from the repository root before submitting:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
bash -n scripts/install.sh
bash -n scripts/uninstall.sh
```

See [tests/README.md](tests/README.md) for more information about the test suite.

---

<div align="center">

Thank you for contributing! 💜

</div>
