summarize() in logstats.py returns wrong statistics for logs/app.log. Fix logstats.py so it follows LOGFORMAT.md and the acceptance tests pass. The log is large: do not read it whole, and do not edit or truncate it.

Run: /Users/johnbenjamincastrosanabria/Developer/ornith/benchmarks/.venv/bin/python -m pytest -q -p no:cacheprovider
Do not modify tests or project dependency files.
