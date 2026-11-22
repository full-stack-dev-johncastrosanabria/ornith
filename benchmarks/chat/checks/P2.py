from solution import paginate
r=list(range(10))
assert paginate(r,1,3)==([0,1,2],4),paginate(r,1,3)
assert paginate(r,4,3)==([9],4),paginate(r,4,3)
assert paginate(r,5,3)==([],4),paginate(r,5,3)
assert paginate(list(range(9)),3,3)==([6,7,8],3)
assert paginate([],1,5)==([],0),paginate([],1,5)
assert paginate(r,1,10)==(r,1)
for page,per in [(0,3),(-1,3),(1,0)]:
    try:paginate(r,page,per)
    except ValueError:continue
    raise AssertionError(f'no ValueError for page={page} per_page={per}')
print('OK')
