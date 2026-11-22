billing.utils.money.to_cents_legacy() truncates floats and is deprecated. Replace every use of it in the billing package with to_cents() (watch for aliases and module-qualified calls), then delete to_cents_legacy. Keep all public function names and signatures.

Run: /Users/johnbenjamincastrosanabria/Developer/ornith/benchmarks/.venv/bin/python -m pytest -q -p no:cacheprovider
Do not modify tests or project dependency files.
