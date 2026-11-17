# Tests

The test suite uses only Python's standard library.

Run from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

The GitHub Actions workflow also compiles all Python files and checks shell-script syntax on pushes and pull requests.
