Refactor quote(kind, amount) to use a data mapping instead of duplicated branches. Preserve behavior, rounding, public signature and ValueError message for unknown kinds. Do not add dependencies.

Run: /Users/johnbenjamincastrosanabria/Developer/ornith/benchmarks/.venv/bin/python -m pytest -q -p no:cacheprovider
Do not modify tests or project dependency files.
