import pytest
from service import invoice
from rates import DISCOUNTS
def test_member(): assert invoice(100,'member')==dict(kind='member',total=108)
def test_regular(): assert invoice(100,'regular')['total']==120
def test_fraction(): assert DISCOUNTS['member']==0.10
@pytest.mark.parametrize('amount,expected',[(0,0),(10,10.8),(2.5,2.7)])
def test_amounts(amount,expected): assert invoice(amount,'member')['total']==expected
