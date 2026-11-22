void Check(bool ok,string what){if(!ok){Console.WriteLine("FAIL "+what);Environment.Exit(1);}}
var orders=new[]{new Order("Acme",10m,false),new Order("ACME",5m,false),new Order("beta",7m,true),new Order("Beta",3m,false),new Order("acme",2m,true),new Order("gamma",1m,true)};
var d=OrderStats.TotalsByCustomer(orders);
Check(d.Count==2,$"count {d.Count}: {string.Join(", ",d)}");
Check(d.Keys.Any(k=>k=="Acme")&&d.Keys.Any(k=>k=="Beta"),"keys "+string.Join(", ",d.Keys));
Check(d.First(p=>p.Key=="Acme").Value==15m&&d.First(p=>p.Key=="Beta").Value==3m,string.Join(", ",d));
Check(OrderStats.TotalsByCustomer(Array.Empty<Order>()).Count==0,"empty input");
Console.WriteLine("OK");
