<div align="center">

# Test suite

**A quick guide to running the project's automated checks.**

</div>

---

## What's covered

The test suite uses only the **Python standard library** — no third-party test framework is required.

It includes checks for:

- Desktop Actions creation, editing, and cleanup;
- desktop-file ID normalization and lookup;
- Russian and English locale selection;
- rejection of unsafe paths and malformed manifest data;
- atomic state-file writes and private permissions;
- preservation of replaced files and symlinks;
- safe resolution of Flatpak export symlinks, while rejecting arbitrary symlinks;
- user-level desktop-entry priority over system launchers;
- synchronization of package source fields while preserving custom names, icons, and Noctalia actions.

## Run tests

Execute from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

## Run the full local checks

```bash
# Unit tests
python3 -m unittest discover -s tests -v

# Python syntax / bytecode compilation
python3 -m compileall -q src tests

# Shell script syntax
bash -n scripts/install.sh
bash -n scripts/uninstall.sh
```

## Current verification status

The current suite contains **21 tests**. The local verification on CachyOS completed successfully on November 17, 2026: all 21 tests passed, Python compilation succeeded, both shell scripts passed syntax checks, and the user service restarted successfully.

Runtime launcher discovery was checked with Bottles installed through Flatpak and Happ installed through AUR/yay. Termius confirmed that an existing user-level launcher takes priority over a package launcher. Snap was not tested because Snap CLI and snapd were not installed.

## Continuous integration

GitHub Actions runs the test suite, Python compilation, and shell-script syntax checks on pushes and pull requests using Python 3.11 and 3.12.

## Reporting a failure

When reporting a failing test, include:

1. The exact command you ran.
2. The complete relevant test output.
3. Your Python version and Linux distribution.
4. Any steps needed to reproduce the failure.

Remove usernames, personal paths, tokens, and other private information before posting logs.

---

[← Back to the project](../README.md)
