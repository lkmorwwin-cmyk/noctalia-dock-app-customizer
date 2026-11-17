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
- preservation of replaced files and symlinks.

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

## Continuous integration

The GitHub Actions workflow runs Python compilation and shell-script syntax checks on pushes and pull requests. The unit-test command above can also be run locally to reproduce the test-suite result.

## Reporting a failure

When reporting a failing test, include:

1. The exact command you ran.
2. The complete relevant test output.
3. Your Python version and Linux distribution.
4. Any steps needed to reproduce the failure.

Remove usernames, personal paths, tokens, and other private information before posting logs.

---

[← Back to the project](../README.md)
