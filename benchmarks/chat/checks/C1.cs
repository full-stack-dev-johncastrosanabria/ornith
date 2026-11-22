void Check(bool ok,string what){if(!ok){Console.WriteLine("FAIL "+what);Environment.Exit(1);}}
var cases=new Dictionary<string,string>{["¡Hola, Señor Niño! 2024"]="hola-senor-nino-2024",["  Ya   existe -- el C# "]="ya-existe-el-c",["Árbol_ÜBER"]="arbol-uber",
  ["---"]="",[""]="",["Crème brûlée"]="creme-brulee",["Año 2025: ¿qué tal?"]="ano-2025-que-tal"};
foreach(var (given,want) in cases){var got=Slug.Make(given);Check(got==want,$"{given} -> {got} (want {want})");}
try{Slug.Make(null);Check(false,"no ArgumentNullException");}catch(ArgumentNullException){}
Console.WriteLine("OK");
