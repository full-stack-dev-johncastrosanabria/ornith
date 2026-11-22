# Service log format

Each record starts on a new line:

    <timestamp> <LEVEL> <service> <message>

- `timestamp` is ISO-8601 with seconds and an explicit UTC offset, for example `2026-03-01T10:15:02+02:00`.
  Services run in several time zones, so offsets differ between lines. Comparisons (the `since` argument of
  `summarize`) are made on the absolute instant, that is, in UTC.
- `LEVEL` is one of DEBUG, INFO, WARN, ERROR.
- A record may span several lines. Continuation lines start with whitespace or with `Traceback`; they belong to
  the record above them and are never records themselves. Text in continuation lines (including words such as
  ERROR or fields such as user=...) is ignored by every statistic.
- Request records have a message starting with `req `, e.g. `req method=GET path=/api/orders status=200 dur=12.5ms user=u042`.
  `dur` is in milliseconds and may have decimals.
- Error records may carry `code=E1234` in their message.

`summarize(path, since=None)` returns:

- `records`: the number of records;
- `levels`: records per level;
- `errors_by_code`: ERROR records per `code`;
- `p95_ms`: per request path, the 95th percentile of `dur` with the nearest-rank method
  (sort ascending; take the element at position ceil(0.95 × n), counting from 1);
- `users`: the number of distinct `user` values in request records.
