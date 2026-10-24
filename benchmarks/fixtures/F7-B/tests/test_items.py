from fastapi.testclient import TestClient
from app import app
c=TestClient(app)
def test_total():
    r=c.post('/items',json=dict(name='  book  ',quantity=3,price=2.5))
    assert r.status_code==201
    assert r.json()==dict(name='book',total=7.5)
def test_invalid():
    for payload in [dict(name='',quantity=1,price=2),dict(name='  ',quantity=1,price=2),dict(name='a',quantity=0,price=2),dict(name='a',quantity=101,price=2),dict(name='a',quantity=1,price=-1)]:
        assert c.post('/items',json=payload).status_code==422
def test_boundary():
    assert c.post('/items',json=dict(name='free',quantity=100,price=0)).json()==dict(name='free',total=0)
