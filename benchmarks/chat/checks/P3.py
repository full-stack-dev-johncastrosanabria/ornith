from solution import merge_intervals
cases=[([(1,3),(2,6),(8,10),(15,18)],[(1,6),(8,10),(15,18)]),([(5,6),(1,3),(3,4)],[(1,4),(5,6)]),([(1,2),(3,4)],[(1,2),(3,4)]),
       ([],[]),([(1,10),(2,3)],[(1,10)]),([(4,4)],[(4,4)]),([(6,8),(1,9),(2,4)],[(1,9)])]
for given,want in cases:
    copy=list(given);got=merge_intervals(given)
    assert given==copy,('input modified',given)
    assert got==want,(given,got,want)
try:merge_intervals([(3,1)])
except ValueError:print('OK')
else:raise AssertionError('no ValueError for (3, 1)')
