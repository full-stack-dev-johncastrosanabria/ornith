Complete FastAPI POST /items. Use Pydantic validation: name must be stripped and nonempty, quantity 1..100, price >=0. Respond 201 with exactly name (stripped) and total (quantity*price); invalid inputs return 422.

Run: /Users/johnbenjamincastrosanabria/Developer/ornith/benchmarks/.venv/bin/python -m pytest -q -p no:cacheprovider
Do not modify tests or project dependency files.
