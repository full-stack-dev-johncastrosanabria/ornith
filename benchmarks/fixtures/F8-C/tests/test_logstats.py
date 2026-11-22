from datetime import datetime, timezone

import pytest

from logstats import summarize

LOG = "logs/app.log"
FULL = {'records': 620, 'levels': {'INFO': 437, 'WARN': 90, 'DEBUG': 32, 'ERROR': 61}, 'errors_by_code': {'E2001': 14, 'E5000': 13, 'E2104': 9, 'E4040': 6, 'E1301': 11, 'E1302': 8}, 'p95_ms': {'/api/items': 862.7, '/api/invoices': 842.9, '/api/profile': 816.8, '/api/search': 857.6, '/api/login': 816.0, '/api/orders': 875.5}, 'users': 136}
SINCE = {'records': 157, 'levels': {'INFO': 111, 'WARN': 25, 'ERROR': 14, 'DEBUG': 7}, 'errors_by_code': {'E2001': 5, 'E2104': 1, 'E4040': 2, 'E5000': 2, 'E1302': 2, 'E1301': 2}, 'p95_ms': {'/api/invoices': 851.1, '/api/items': 868.0, '/api/login': 793.8, '/api/search': 844.3, '/api/profile': 816.8, '/api/orders': 885.0}, 'users': 76}


def test_records():
    assert summarize(LOG)["records"] == FULL["records"]


def test_levels():
    assert summarize(LOG)["levels"] == FULL["levels"]


def test_error_codes():
    assert summarize(LOG)["errors_by_code"] == FULL["errors_by_code"]


def test_p95():
    assert summarize(LOG)["p95_ms"] == pytest.approx(FULL["p95_ms"])


def test_users():
    assert summarize(LOG)["users"] == FULL["users"]


def test_since_compares_instants():
    result = summarize(LOG, since=datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc))
    assert result["records"] == SINCE["records"] and result["levels"] == SINCE["levels"]


def test_continuation_lines(tmp_path):
    sample = tmp_path / "s.log"
    sample.write_text(
        "2026-03-01T10:00:00+02:00 ERROR orders db deadlock code=E2001\n"
        "Traceback (most recent call last):\n"
        '  File "/srv/orders/db.py", line 9, in commit\n'
        "    raise RuntimeError(\"ERROR req path=/x dur=5ms user=u999\")\n"
        "2026-03-01T08:00:01+00:00 INFO orders req method=GET path=/api/orders status=200 dur=12.5ms user=u001\n"
    )
    result = summarize(str(sample))
    assert result["records"] == 2
    assert result["levels"] == {"ERROR": 1, "INFO": 1}
    assert result["users"] == 1
    assert result["p95_ms"] == {"/api/orders": 12.5}
