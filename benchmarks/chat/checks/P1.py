from solution import parse_duration
cases={'1h30m':5400,'45s':45,'2h5m10s':7510,' 1h 30m ':5400,'0s':0,'90m':5400,'10m5s':605,'100h':360000,'1h10s':3610}
for s,want in cases.items():
    got=parse_duration(s);assert got==want,(s,got,want)
for s in ['','   ','5x','30m1h','1h1h','h','1.5h','-1h','1h30','m5','2s3m']:
    try:parse_duration(s)
    except ValueError:continue
    raise AssertionError(f'no ValueError for {s!r}')
print('OK')
