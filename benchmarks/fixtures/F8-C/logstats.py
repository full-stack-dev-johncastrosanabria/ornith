"""Summaries of the service log format described in LOGFORMAT.md."""
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

LINE = re.compile(r"^(?P<ts>\S+) (?P<level>[A-Z]+) (?P<service>[\w-]+) (?P<msg>.*)$")
REQ = re.compile(r"^req .*path=(?P<path>\S+) .*dur=(?P<dur>\d+)")
USER = re.compile(r"user=(?P<user>u\d+)")
CODE = re.compile(r"code=(?P<code>E\d+)")


def parse(path):
    records = []
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            match = LINE.match(line)
            if match:
                records.append({"ts": match["ts"], "level": match["level"], "service": match["service"], "msg": match["msg"]})
            else:
                records.append({"ts": None, "level": "UNKNOWN", "service": "", "msg": line})
    return records


def _when(ts):
    return datetime.fromisoformat(ts[:19]).replace(tzinfo=timezone.utc)


def p95(values):
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def summarize(path, since=None):
    records = parse(path)
    if since is not None:
        records = [r for r in records if r["ts"] and _when(r["ts"]) >= since]
    durations = defaultdict(list)
    users = set()
    for record in records:
        request = REQ.search(record["msg"])
        if request:
            durations[request["path"]].append(float(request["dur"]))
        user = USER.search(record["msg"])
        if user:
            users.add(user["user"])
    return {
        "records": len(records),
        "levels": dict(Counter(r["level"] for r in records)),
        "errors_by_code": dict(Counter(m["code"] for r in records if r["level"] == "ERROR" for m in [CODE.search(r["msg"])] if m)),
        "p95_ms": {path: p95(values) for path, values in durations.items()},
        "users": len(users),
    }
