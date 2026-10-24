"""Public, equivalent F7 fixtures. No historical solutions or hidden rubrics."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'benchmarks/fixtures'

def write(task,files,prompt,command):
    d=BASE/task;d.mkdir(parents=True,exist_ok=True)
    for name,text in files.items():
        p=d/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n')
    (d/'TASK.md').write_text(prompt+'\n\nRun: '+command+'\nDo not modify tests or project dependency files.\n')
    return {'task':task,'command':command,'files':{str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in d.rglob('*') if p.is_file()}}

def main():
    py=str(ROOT/'benchmarks/.venv/bin/python');rows=[]
    rows.append(write('F7-A',{
    'src/App.csproj':'<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><TargetFramework>net10.0</TargetFramework><Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings></PropertyGroup></Project>',
    'src/Program.cs':'''var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.MapPost("/orders", (Order order) => Results.StatusCode(501));
app.Run();
public record Order(string? Sku, int Quantity, decimal UnitPrice);
public partial class Program { }''',
    'tests/Acceptance.csproj':'''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><IsTestProject>true</IsTestProject><ImplicitUsings>enable</ImplicitUsings></PropertyGroup><ItemGroup><PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="10.0.1"/><PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.14.1"/><PackageReference Include="xunit" Version="2.9.3"/><PackageReference Include="xunit.runner.visualstudio" Version="3.1.1"/><ProjectReference Include="../src/App.csproj"/></ItemGroup></Project>''',
    'tests/OrdersTests.cs':'''using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;
public class OrdersTests : IClassFixture<WebApplicationFactory<Program>> {
 readonly HttpClient client;
 public OrdersTests(WebApplicationFactory<Program> app) { client=app.CreateClient(); }
 [Fact] public async Task ValidOrder() {
 var r=await client.PostAsJsonAsync("/orders",new {sku="ABC",quantity=3,unitPrice=2.50m});
 Assert.Equal(HttpStatusCode.Created,r.StatusCode);
 var j=await r.Content.ReadFromJsonAsync<System.Text.Json.JsonElement>();
 Assert.Equal(7.50m,j.GetProperty("total").GetDecimal());
 }
 [Theory] [InlineData("",1,2)] [InlineData(" ",1,2)] [InlineData("A",0,2)] [InlineData("A",101,2)] [InlineData("A",1,-1)]
 public async Task InvalidOrder(string sku,int quantity,decimal unitPrice) {
 var r=await client.PostAsJsonAsync("/orders",new {sku,quantity,unitPrice});Assert.Equal(HttpStatusCode.BadRequest,r.StatusCode);
 }
}'''
    },'Implement POST /orders in ASP.NET Core. Accept sku (nonblank), quantity (1..100 inclusive), unitPrice (>=0). Return HTTP 201 with JSON total = quantity * unitPrice for valid input, otherwise HTTP 400. Preserve public record signature.','dotnet test tests/Acceptance.csproj --no-restore --disable-build-servers -p:UseSharedCompilation=false -v minimal'))
    rows.append(write('F7-B',{
    'app.py':'''from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()
class Item(BaseModel):
    name: str
    quantity: int
    price: float
@app.post("/items", status_code=201)
def create_item(item: Item):
    return {"total": 0}''',
    'tests/test_items.py':'''from fastapi.testclient import TestClient
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
    assert c.post('/items',json=dict(name='free',quantity=100,price=0)).json()==dict(name='free',total=0)'''
    },'Complete FastAPI POST /items. Use Pydantic validation: name must be stripped and nonempty, quantity 1..100, price >=0. Respond 201 with exactly name (stripped) and total (quantity*price); invalid inputs return 422.',f'{py} -m pytest -q -p no:cacheprovider'))
    rows.append(write('F7-C',{
    'pricing.py':'''def quote(kind, amount):
    if kind == 'regular':
        return round(amount * 1.2, 2)
    if kind == 'member':
        return round(amount * 0.9 * 1.2, 2)
    if kind == 'staff':
        return round(amount * 0.8 * 1.2, 2)
    raise ValueError('unknown kind')''',
    'tests/test_pricing.py':'''import ast
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
    assert sum(isinstance(n,ast.If) for n in ast.walk(fn))<=1, 'remove branch duplication' ''',
    },'Refactor quote(kind, amount) to use a data mapping instead of duplicated branches. Preserve behavior, rounding, public signature and ValueError message for unknown kinds. Do not add dependencies.',f'{py} -m pytest -q -p no:cacheprovider'))
    rows.append(write('F7-D',{
    'rates.py':"DISCOUNTS = {'regular': 0.0, 'member': 10.0}\nTAX_RATE = 0.20",
    'calculator.py':'''from rates import DISCOUNTS, TAX_RATE
def total(amount, kind):
    discounted = amount * (1-DISCOUNTS[kind])
    return round(discounted + amount * TAX_RATE, 2)''',
    'service.py':'''from calculator import total
def invoice(amount, kind):
    return {'kind': kind, 'total': total(amount, kind)}''',
    'tests/test_invoice.py':'''import pytest
from service import invoice
from rates import DISCOUNTS
def test_member(): assert invoice(100,'member')==dict(kind='member',total=108)
def test_regular(): assert invoice(100,'regular')['total']==120
def test_fraction(): assert DISCOUNTS['member']==0.10
@pytest.mark.parametrize('amount,expected',[(0,0),(10,10.8),(2.5,2.7)])
def test_amounts(amount,expected): assert invoice(amount,'member')['total']==expected'''
    },'Find and fix the multi-file invoice bug. Member discount is 10 percent, regular discount is zero. Tax is 20 percent applied AFTER the discount. Preserve service API and round the final total to 2 decimals.',f'{py} -m pytest -q -p no:cacheprovider'))
    # Public development task only. Final F7 tasks are never used for proposal feedback.
    rows.append(write('DEV',{'normalize.py':"def normalize(values):\n    return values",'tests/test_normalize.py':"from normalize import normalize\ndef test_normalize(): assert normalize([' B ','a','b',' ']) == ['a','b']"},'Implement normalize(values): strip strings, lowercase, drop blank values and duplicates, return sorted output.',f'{py} -m pytest -q -p no:cacheprovider'))
    (BASE/'manifest.json').write_text(json.dumps({'provenance':'New public equivalents; historical original fixtures not located in inspected Bonsai directories or Spotlight. Different from historical F7; no direct historical score comparison.','tasks':rows},indent=2)+'\n')
    print('Created',len(rows),'public fixtures')
if __name__=='__main__':main()
