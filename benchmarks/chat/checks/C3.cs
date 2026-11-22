void Check(bool ok,string what){if(!ok){Console.WriteLine("FAIL "+what);Environment.Exit(1);}}
var cases=new Dictionary<string,string[]>{["a,b,c"]=new[]{"a","b","c"},["a,,b"]=new[]{"a","","b"},["a,"]=new[]{"a",""},[""]=new[]{""},
  ["\"x,y\",z"]=new[]{"x,y","z"},["\"di \"\"hola\"\"\",2"]=new[]{"di \"hola\"","2"},[" a , b "]=new[]{" a "," b "},["\"\""]=new[]{""},[",\"\","]=new[]{"","",""}};
foreach(var (given,want) in cases){var got=Csv.ParseLine(given);Check(got.SequenceEqual(want),$"{given} -> [{string.Join("|",got)}]");}
try{Csv.ParseLine("\"abc");Check(false,"no FormatException");}catch(FormatException){}
Console.WriteLine("OK");
