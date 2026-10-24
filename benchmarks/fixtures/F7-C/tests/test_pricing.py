import ast
from pathlib import Path
import pytest
from pricing import quote
@pytest.mark.parametrize('kind,amount,total',[('regular',100,120),('member',100,108),('staff',100,96),('regular',0,0),('member',1.23,1.33),('staff',-10,-9.6)])
def test_behavior(kind,amount,total): assert quote(kind,amount)==total
def test_unknown():
    with pytest.raises(ValueError,match='unknown kind'): quote('other',10)
def test_refactor():
    tree=ast.parse(Path('pricing.py').read_text())
    assert any(isinstance(n,ast.Dict) for n in ast.walk(tree)), 'use a data mapping'
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='quote')
    assert sum(isinstance(n,ast.If) for n in ast.walk(fn))<=1, 'remove branch duplication'
