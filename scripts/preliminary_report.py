"""Informe PDF de resultados preliminares (22 nov 2026). Cifras copiadas a mano de docs/ y benchmarks/reports/ (ver sección Fuentes).
Uso: python3 scripts/preliminary_report.py docs/resultados-preliminares-2026-11-22.pdf  (requiere reportlab; fuentes Arial de macOS)."""
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

F='/System/Library/Fonts/Supplemental/'
pdfmetrics.registerFont(TTFont('A',F+'Arial.ttf'));pdfmetrics.registerFont(TTFont('AB',F+'Arial Bold.ttf'))
pdfmetrics.registerFont(TTFont('AI',F+'Arial Italic.ttf'))
pdfmetrics.registerFontFamily('A',normal='A',bold='AB',italic='AI',boldItalic='AB')
INK=colors.HexColor('#1f2933');MUTED=colors.HexColor('#5b6670');RULE=colors.HexColor('#d5dae0');HEAD=colors.HexColor('#eef1f4')
ACC=colors.HexColor('#0b5cad');OK=colors.HexColor('#e3f1e6');BAD=colors.HexColor('#f8e3e1');NE=colors.HexColor('#f1f1f1')
S=lambda n,**k:ParagraphStyle(n,**({'fontName':'A','fontSize':9.5,'leading':13.2,'textColor':INK}|k))
body=S('b',spaceAfter=5);small=S('s',fontSize=8,leading=10.5,textColor=MUTED)
h1=S('h1',fontName='AB',fontSize=14,leading=18,spaceBefore=12,spaceAfter=6,textColor=ACC)
h2=S('h2',fontName='AB',fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4)
title=S('t',fontName='AB',fontSize=21,leading=26,spaceAfter=4);sub=S('st',fontSize=10.5,leading=14,textColor=MUTED,spaceAfter=10)
cell=S('c',fontSize=7.8,leading=9.6);cellb=S('cb',fontName='AB',fontSize=7.8,leading=9.6)
bul=S('bu',leftIndent=11,bulletIndent=2,spaceAfter=2.5)
P=lambda t,s=body:Paragraph(t,s)
def B(items):return [Paragraph(i,bul,bulletText='•') for i in items]
def T(rows,widths,shade=None,first_bold=True):
    data=[[P(c,cellb if (r==0 or (first_bold and j==0)) else cell) for j,c in enumerate(row)] for r,row in enumerate(rows)]
    st=[('GRID',(0,0),(-1,-1),.4,RULE),('BACKGROUND',(0,0),(-1,0),HEAD),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]
    for (c,r),col in (shade or {}).items():st.append(('BACKGROUND',(c,r),(c,r),col))
    t=Table(data,colWidths=[w*mm for w in widths],repeatRows=1);t.setStyle(TableStyle(st));t.spaceAfter=6;return t

story=[P('Laboratorio Ornith: resultados preliminares',title),
 P('Modelos locales para programar en un MacBook Air M3 de 16 GB · inferencia nativa en macOS · 22 de noviembre de 2026',sub),
 T([['Estado','Preliminar. Cada tarea se ejecutó entre 1 y 3 veces; las tareas las escribió el propio laboratorio y no están calibradas por personas. '
     'Las diferencias de 1 o 2 tareas no son concluyentes.']],[32,142],first_bold=True),
 P('1. Resumen',h1),
 P('<b>Recomendación actual.</b> <b>Para programar:</b> <b>Ornith 1.5 9B GGUF Q4_K_M</b> en OpenCode (agente <i>ornith-code</i>, router local con 24K de contexto), '
   'solo para cambios pequeños y bien acotados. <b>Para chat:</b> <b>GPT-OSS 20B</b> con el comando <i>ornith-chat</i> o la app Enchanted. Es el único modelo que pasa la barra de chat (23/24, mediana 78 s), '
   'pero ocupa unos 12,6 GB de 16 y solo pasa porque el usuario decidió ignorar el límite de memoria en esa prueba. Ningún modelo local resuelve las tareas largas.'),
 *B(['<b>Tareas cortas (F7, 4 tareas):</b> los mejores modelos resuelven 4/4. Ornith GGUF y Bonsai 2 27B llegaron a 8/8 en dos pasadas (cohorte oc226); en el cohorte oc232, Ornith GGUF y GPT-OSS 20B hicieron 4/4.',
     '<b>Tareas largas o de varios pasos (F8, 8 tareas):</b> casi nada pasa. Ornith GGUF 0/8, Bonsai 2 9B 1/8, GPT-OSS 0/8; la mayoría por tiempo agotado (1800 s).',
     '<b>Chat sin herramientas (8 preguntas × 3):</b> GPT-OSS 20B 23/24 (96 %, mediana 78 s), Ornith 15/24 (63 %), Bonsai 2 27B 15/24 (63 %, 213 s), Bonsai 2 9B 8/24 (33 %). La barra era 75 % y una mediana de 180 s o menos.',
     '<b>Memoria:</b> con 16 GB, Ornith GGUF, GPT-OSS y Bonsai 2 27B superaron el límite de memoria en algún momento. En el cohorte oc232, GPT-OSS (12,6 GiB fijos) queda fuera y a Ornith se le aplicó una exención posterior. En la prueba de chat de Bonsai 27B y GPT-OSS (D064), el usuario decidió ignorar el límite. Todas estas excepciones están señaladas.',
     '<b>Velocidad:</b> Ornith genera unos 13 t/s con el Mac en reposo, igual a 16K que a 24K. Tras más de 10 horas de carga continua bajó a 4 t/s; lo más probable es el calor (el Air no tiene ventilador) y la presión de memoria, no el contexto.']),
 P('Resumen por modelo',h2),
 T([['Modelo','Tareas cortas F7','Tareas largas F8','Chat','Memoria','Valoración'],
    ['Ornith 1.5 9B GGUF Q4_K_M','8/8 (oc226) · 4/4 (oc232)','0/8','15/24','Límite superado en sesiones largas (exención en oc232)','Ganador en oc226. Útil para cambios pequeños.'],
    ['Ternary-Bonsai-2-9B','3/4 (oc226) · 3/4 (oc232)','1/8','8/24','Limpio','Primero, provisional, en oc232 por velocidad; poco fiable.'],
    ['Bonsai 2 27B','8/8 (oc226) · 0/1 (oc232)','No medido (pausado)','15/24','Límite superado en chat (ignorado)','Correcto en tareas cortas pero lento (2–5 t/s).'],
    ['GPT-OSS 20B MXFP4','4/4 (oc232)','0/8','23/24','Límite superado (12,6 GiB fijos); ignorado en chat','El mejor en chat. Fuera de la clasificación de agente.'],
    ['Ornith 1.5 9B MLX 4-bit','2/4 (oc226) · 3/4 a 24K','—','—','—','Rápido, menos fiable.'],
    ['Qwen3.5 9B MLX 4-bit','2/4 (oc226)','—','—','—','Sin ventaja.'],
    ['Granite 4.1 8B, Gemma 4 12B, SERA-8B','N/E','—','—','—','No pasaron la prueba de integración con el agente.']],
   [36,28,22,14,37,37],{(5,1):OK,(5,4):OK,(3,4):OK,(5,7):NE}),
 P('2. Método',h1),
 *B(['Hardware: MacBook Air M3 (Mac15,12), 16 GB de memoria unificada, sin ventilador. Solo inferencia nativa (llama.cpp Metal o MLX); sin Docker, máquinas virtuales ni nube.',
     'Un solo modelo cargado a la vez, 300 s de enfriamiento entre modelos. Perfil fijo: 16K de contexto, 4096 tokens de salida, temperatura 0,6, top_p 0,95.',
     'Agente: OpenCode global (1.19.4 en octubre, 2.2.6 en oc226, 2.3.2 en oc232). Una nueva versión de OpenCode abre un cohorte nuevo; los cohortes no se mezclan.',
     'Puntuación: tests de aceptación ocultos e inmutables, ejecutados en un sandbox. Clasificación por tareas aprobadas, luego tiempo total y luego velocidad (regla D031).',
     'Un fallo de infraestructura no cuenta como fallo de calidad: se marca N/E. Límite de memoria: 3 muestras seguidas con menos del 10 % libre o swap +2 GiB sobre el inicio → ese modelo es N/E.',
     'F7: 4 tareas cortas de corrección (una API ASP.NET Core en C#, tres en Python). F8 (desde oc232): 8 tareas más duras: repositorio grande (55 archivos), especificación larga, log de 73 KiB, TypeScript, Java 21 + JUnit, migraciones SQLite, API .NET 10 con concurrencia optimista y una refactorización en varios archivos.']),
 P('3. Cronología de pruebas',h1),
 T([['Fecha','Prueba','Qué se midió','Resultado clave'],
    ['25 oct','Cohorte inicial (Mac despejado)','Bonsai 27B, Ornith MLX y GGUF; harness PPC local','Bonsai 27B 4/4; Ornith GGUF 3/4; Ornith MLX 2/4 completadas'],
    ['8 nov','oc226-control','Ornith MLX con OpenCode 2.2.6','2/4'],
    ['8–9 nov','oc226-nodocker','8 candidatos, regla D030/D031','Ornith GGUF 4/4 (1922 s) gana a Bonsai 27B 4/4 (2113 s)'],
    ['9 nov','oc226 r2 (repetición)','Los dos primeros otra vez','Ornith GGUF 8/8 en 3342 s; Bonsai 27B 8/8 en 4032 s'],
    ['9 nov','Brazo 24K / 8K salida','Contexto y salida mayores','No se adopta ningún cambio'],
    ['9 nov','Uso diario (D053–D058)','Router, 24K, guía y 40 pasos','Router automático; Bonsai 27B pasa de 85,6 a 53,5 min en un frontend'],
    ['20–21 nov','oc232-nodocker','12 tareas, 40 pasos, 1800 s, OpenCode 2.3.2','Provisional: Bonsai 9B y Ornith GGUF, 4/12 cada uno'],
    ['21 nov','Prueba a 24K','Bonsai 9B en F8-A y F8-C','0/2'],
    ['21 nov','Repeticiones .NET','F7-A y F8-G, 3 pasadas','Ornith gana F7-A (3/3); Bonsai 9B gana F8-G (2/3)'],
    ['21–22 nov','Modo chat (D062)','Ornith y Bonsai 9B, 8 preguntas × 3','Ninguno llega a la barra'],
    ['22 nov','16K frente a 24K (D063)','Velocidad de Ornith y prueba completa','Igual velocidad; OpenCode → router → Ornith funciona'],
    ['22 nov','Modo chat (D064)','Bonsai 27B y GPT-OSS, mismas preguntas','GPT-OSS 23/24 en 78 s: pasa la barra (memoria ignorada)'],
    ['22 nov','Chat diario (D065–D066)','GPT-OSS en el router, terminal y Enchanted','ornith-chat y Enchanted funcionan; OpenCode no sirve para chat']],
   [17,37,52,68]),
]

story+=[P('4. Pruebas previas',h1),
 P('4.1 Cohorte inicial, 25 de octubre (Mac despejado, OpenCode 1.19.4)',h2),
 T([['Configuración','Decode t/s','Prefill t/s','RSS máx.','Artefactos F7','Completadas','Mediana (completadas)'],
    ['Bonsai 2 27B ternario (llama.cpp)','4,65','22,05','7,27 GiB','4/4','4/4','578 s'],
    ['Ornith 9B MLX 4-bit','15,43','83,02','3,79 GiB','3/4','2/4','997 s'],
    ['Ornith 9B GGUF Q4_K_M (llama.cpp)','10,06','75,52','6,37 GiB','3/4','3/4','518 s'],
    ['Ornith MLX + PPC local','—','—','4,35 GiB','2/4','2/4','542 s']],
   [48,18,18,20,22,20,28]),
 P('Una sola pasada por tarea. El ejecutor oficial fijado (OpenCode compilado desde su código fuente) sobre Ornith MLX hizo 1/4: las tres fallas se cortaron en el límite de 4096 tokens de salida. El harness PPC local no mostró beneficio frente al control.',small),
 P('4.2 Cohorte oc226-nodocker, 8–9 de noviembre (OpenCode 2.2.6)',h2),
 T([['#','Modelo','F7','Total F7','Decode t/s','Huella máx.','Causas de fallo'],
    ['1','Ornith 1.5 9B GGUF Q4_K_M','4/4','1922 s','10,73','5,13 GiB','—'],
    ['2','Bonsai 2 27B PTQ1_0','4/4','2113 s','4,52','2,40 GiB','—'],
    ['3','Ternary-Bonsai-2-9B PTQ1_0','3/4','718 s','14,99','1,59 GiB','F7-A incorrecta'],
    ['4','Qwen3.5-9B MLX 4-bit','2/4','1636 s','13,35','8,05 GiB','F7-A, F7-C incorrectas'],
    ['5','Ornith 1.5 9B MLX 4-bit','2/4','3850 s','17,07','7,93 GiB','F7-A tiempo agotado, F7-B incorrecta'],
    ['N/E','Granite 4.1 8B, Gemma 4 12B, SERA-8B','N/E','N/E','N/E','N/E','Fallaron la prueba de integración (no es un 0/4)']],
   [9,46,11,17,17,19,55],first_bold=False),
 P('<b>Repetición r2 y veredicto:</b> Ornith GGUF 4/4 en 1420 s (8/8 y 3342 s en total) frente a Bonsai 27B 4/4 en 1919 s (8/8 y 4032 s). '
   'Ganador por la regla registrada de antemano: Ornith GGUF. Con n = 8 no hay diferencia de calidad detectable; la ventaja es de tiempo (−17 %) y de velocidad (unas 2,3 veces más rápido). '
   'Los dos dejaron los tests intactos y no introdujeron avisos de ruff ni de dotnet format; las diferencias en el código son de estilo.'),
 P('<b>Brazo 24K / 8192 de salida:</b> Ornith GGUF N/E por memoria (swap +2,7 GiB; 4/4 descriptivo); Bonsai 2 9B peor (0/4 frente a 3/4); Qwen3.5 N/E por integración; Ornith MLX 3/4 frente a 2/4, sin diferencia detectable. No se adoptó ningún cambio.'),
 P('4.3 Configuración de uso diario, 9 de noviembre (D053–D058)',h2),
 *B(['Router local en 127.0.0.1:8099: OpenCode elige el modelo y el router lo carga bajo demanda, uno a la vez, y lo descarga tras 15 min sin uso. Se inicia con la sesión (LaunchAgent).',
     'Contexto de uso diario subido a 24K en ambos modelos (KV de Ornith ≈ 768 MiB; Bonsai 27B ≈ 1,5 GiB), salida 4096.',
     'Prueba fuera del laboratorio con un frontend React + TypeScript: Ornith terminó en 40 min (24/25 pasos, build OK); Bonsai 27B en 85,6 min, llegó al límite de pasos.',
     'Tras añadir una guía corta y 40 pasos, Bonsai 27B repitió en 53,5 min (23/40 pasos, build OK). Es una sola pasada: la mejora se observa, no se atribuye.'])]

G=OK;X=BAD;N=NE
rows=[['Tarea','Ornith 1.5 9B GGUF','Ternary-Bonsai-2-9B','GPT-OSS 20B','Bonsai 2 27B'],
 ['F7-A (.NET)','OK · 314 s','Incorrecta · 1549 s','OK · 338 s','Tiempo agotado (paso 12)'],
 ['F7-B','OK · 320 s','OK · 120 s','OK · 204 s','Pausado'],
 ['F7-C','OK · 790 s','OK · 208 s','OK · 190 s','Pausado'],
 ['F7-D','OK · 399 s','OK · 210 s','OK · 451 s','Pausado'],
 ['F8-A repo grande','Tiempo agotado (12)','Incorrecta (40 pasos)','Incorrecta','Pausado'],
 ['F8-B especificación','Tiempo agotado (10)','Tiempo agotado (31)','Llamada perdida','Pausado'],
 ['F8-C log grande','Tiempo agotado (11)','Incorrecta (40 pasos)','Tiempo agotado (17)','Pausado'],
 ['F8-D TypeScript','Tiempo agotado (7)','Tiempo agotado (12)','Tiempo agotado (15)','Pausado'],
 ['F8-E Java','Tiempo agotado (11)','Tiempo agotado (23)','Tiempo agotado (8)','Pausado'],
 ['F8-F SQLite','Compactación fallida','Tiempo agotado (26)','Incorrecta','Pausado'],
 ['F8-G .NET API','Tiempo agotado (10)','OK · 570 s','Incorrecta','Pausado'],
 ['F8-H refactor','Tiempo agotado (14)','Incorrecta (40 pasos)','Incorrecta','Pausado'],
 ['Total','4/12 (F7 4, F8 0)','4/12 (F7 3, F8 1)','4/12 (F7 4, F8 0)','1 de 12 medida'],
 ['Tiempo total','15 594 s','13 725 s','9 285 s','—'],
 ['Decode t/s','13,3','18,4','N/E','4,7'],
 ['RSS máx. · swap','7,05 GiB · 1,7–7,9 GiB','3,70 GiB · 1,4–1,5 GiB','4,89 GiB · 1,6–7,3 GiB','7,63 GiB · 1,5 GiB'],
 ['Límite de memoria','Superado (exención)','Limpio','Superado → fuera','Limpio']]
shade={}
for r,row in enumerate(rows[1:13],1):
    for c,v in enumerate(row[1:],1):shade[(c,r)]=G if v.startswith('OK') else N if v=='Pausado' else X
shade.update({(1,17):X,(2,17):G,(3,17):X,(4,17):G})
story+=[P('5. Cohorte oc232-nodocker, 20–21 de noviembre',h1),
 P('OpenCode 2.3.2, 12 tareas (F7 + F8), 40 pasos de agente y 1800 s por tarea, perfil 16K/4096. Entre paréntesis, el paso en el que se agotó el tiempo.'),
 T(rows,[30,36,36,36,36],shade),
 P('<b>Clasificación provisional:</b> 1.º Ternary-Bonsai-2-9B, 2.º Ornith GGUF. Empatan a 4/12; en las tres tareas que aprobaron los dos, Bonsai tardó 538 s y Ornith 1510 s. '
   'Como la diferencia es de 1 tarea o menos, la regla pide repetir (r2), y eso está pendiente. El límite de memoria de Ornith se superó en su primera hora (swap de 1,8 a 8,1 GB); su exención se decidió después de ver los datos y está señalada. '
   'GPT-OSS ocupa 12,6 GiB fijos y queda fuera. Bonsai 27B se pausó tras F7-A (fallo al reiniciar el servidor, ya corregido); le quedan 11 tareas.'),
 P('<b>Prueba a 24K (descriptiva):</b> Bonsai 2 9B falló F8-A y F8-C también con 24K de contexto (0/2).'),
 P('5.1 Repeticiones .NET (3 pasadas por tarea)',h2),
 T([['Modelo','F7-A (API ASP.NET Core)','F8-G (.NET 10, concurrencia optimista)','Límite de memoria'],
    ['Ornith 1.5 9B GGUF','3/3 (314, 1710 y 1656 s)','0/3 (tiempo agotado)','Superado en las repeticiones'],
    ['Ternary-Bonsai-2-9B','0/3','2/3 (570 s, tiempo agotado, 703 s)','Limpio']],
   [40,44,56,34],{(1,1):OK,(2,1):BAD,(1,2):BAD,(2,2):OK}),
 P('Las dos últimas pasadas de Ornith en F7-A tardaron cinco veces más que la primera, tras horas de carga continua.',small)]

story+=[KeepTogether([P('6. Modo chat (D062 y D064), 21–22 de noviembre',h1),
 P('8 preguntas en español sin herramientas, 3 repeticiones, perfil de uso diario (24K/4096). Se califica el último bloque de código contra comprobaciones ocultas. '
   'Una respuesta cortada por el límite de tokens cuenta como fallo. Barra fijada de antemano: aprobar al menos el 75 % y una mediana de 180 s o menos. '
   'D062 midió Ornith y Bonsai 9B; D064 midió Bonsai 27B y GPT-OSS con las mismas preguntas, comprobaciones y calificador.'),
 T([['Modelo','P1','P2','P3','C1','C2','C3','S1','E1','Total','Cortadas','Mediana','Decode t/s (cohorte)','Veredicto'],
    ['GPT-OSS 20B','3/3','3/3','3/3','3/3','3/3','2/3','3/3','3/3','23/24','1','78 s','N/E','Usable (memoria ignorada)'],
    ['Ornith GGUF','0/3','3/3','3/3','1/3','2/3','0/3','3/3','3/3','15/24','6','503 s','4,2 (13,3)','N/E por memoria; no llega'],
    ['Bonsai 2 27B','3/3','3/3','2/3','0/3','2/3','2/3','3/3','0/3','15/24','0','213 s','1,9 (4,7)','No usable (memoria ignorada)'],
    ['Bonsai 2 9B','0/3','2/3','2/3','0/3','0/3','0/3','3/3','1/3','8/24','7','386 s','7,2 (18,4)','No usable']],
   [20,8.5,8.5,8.5,8.5,8.5,8.5,8.5,8.5,11,15,14,20,26],{(13,1):OK,(13,2):NE,(13,3):BAD,(13,4):BAD})]),
 P('P1–P3 Python (parse_duration, paginate, merge_intervals); C1–C3 C# .NET 10 (slug, LINQ, parser CSV); S1 consulta SQLite; E1 predecir la salida de un programa. '
   'Ornith perdió 6 respuestas que gastaron los 4096 tokens razonando sin escribir nada, y 3 por errores de compilación en C#. '
   'El único fallo de GPT-OSS fue también una respuesta cortada. Casi todo su tiempo es razonamiento antes del primer token visible (mediana 59 s), y su servidor no da un contador de velocidad comparable. '
   'Los fallos de Bonsai 27B en C# son errores reales del modelo, comprobados a mano. Su velocidad bajó de 3,1 a 1,7 t/s durante la prueba. '
   'Bonsai 27B y GPT-OSS superaron el límite de memoria; el usuario decidió ignorarlo en D064 después de ver la superación de Bonsai y antes de calificar ninguna respuesta.',small),
 P('7. Velocidad 16K frente a 24K y prueba completa (D063), 22 de noviembre',h1),
 T([['Brazo (orden ABA)','Decode mediana','Memoria fija con el modelo cargado'],['16K','13,4 t/s','11,0–11,35 GB'],['24K','13,3 t/s','11,0–11,35 GB'],['16K','13,5 t/s','11,0–11,35 GB']],[50,40,84]),
 P('El tamaño de contexto no explica la lentitud del chat, así que el router sigue con 24K. A 13 t/s, la respuesta mediana de Ornith tardaría unos 150 s, por debajo de 180 s; aun así, su 63 % de aciertos sigue por debajo del 75 %. '
   '<b>Prueba completa:</b> OpenCode → router → modelo respondió bien con los dos agentes: ornith-code en 172 s con el router manual y en 145 s con el LaunchAgent; bonsai9-code en 479 s (incluye el cambio de modelo), solo con el router manual.'),
 P('8. Configuración actual de uso diario (D065–D066)',h1),
 T([['Uso','Cómo','Modelo','Notas'],
    ['Programar (recomendado)','OpenCode, agente ornith-code','Ornith 1.5 9B GGUF','24K de contexto, 40 pasos; cambios pequeños'],
    ['Programar (alternativas)','OpenCode, bonsai9-code / bonsai-lab-code','Bonsai 2 9B / Bonsai 2 27B','Más rápido y menos fiable / correcto pero muy lento'],
    ['Chat (recomendado)','Terminal: ornith-chat','GPT-OSS 20B (por defecto)','Le llega solo la pregunta, como en D064. Probado: 2 turnos en 83 s con la carga'],
    ['Chat (app)','Enchanted → 127.0.0.1:8099','Cualquiera de los 4','El router imita la API de Ollama. Protocolo probado; la app en sí, no'],
    ['Chat en OpenCode','Agente gptoss-chat','GPT-OSS 20B','No recomendado: ~5.700 tokens de instrucciones por paso y llamadas a herramientas inexistentes']],
   [30,46,38,60],{(0,3):OK,(0,5):BAD}),
 P('Todo pasa por un router local (127.0.0.1:8099) que arranca con la sesión. Carga el modelo pedido, mantiene uno solo en memoria y lo descarga tras 15 minutos sin uso. '
   'Las peticiones de chat siempre usan el perfil medido (temperatura 0,6, top_p 0,95, 4096 tokens de salida). '
   'En conversaciones muy largas se descartan los mensajes más antiguos (~40.000 caracteres), para que GPT-OSS no se quede sin memoria.',small),
 P('9. Limitaciones',h1),
 *B(['Muestras pequeñas: 1 pasada por tarea en los cohortes y 3 en las repeticiones. Diferencias de 1–2 tareas no son concluyentes.',
     'Las tareas F8 y las preguntas de chat las escribió la misma sesión que opera el laboratorio: no son independientes ni están calibradas por personas.',
     'Bonsai frente a Ornith mezcla modelo, runtime y cuantización; no se puede atribuir una diferencia a un solo factor.',
     'Control y tratamiento se ejecutaron en momentos distintos en un portátil sin ventilador. El calor no se pudo medir (pmset no registra nada en Apple Silicon).',
     'La exención del límite de memoria de Ornith en oc232 y la decisión de ignorarlo en el chat de D064 se tomaron después de ver datos; ambas están señaladas.',
     'GPT-OSS es usable en chat solo si se acepta que ocupa unos 12,6 GB de 16: con otras apps abiertas el Mac usa swap y puede ir lento.',
     'La huella de memoria es aproximada entre runtimes: llama.cpp mapea los pesos desde el archivo.']),
 P('10. Pendientes',h1),
 *B(['Retomar la campaña de Bonsai 2 27B en oc232 (quedan 11 tareas).',
     'Repetición r2 de los dos primeros de oc232, que la regla exige por el empate.',
     'Harness² con Claude como editor fijo (D060): registrado de antemano, todavía sin ejecutar.',
     'Verificar bonsai9-code con el router en launchd.',
     'Probar la app Enchanted conectada al router (solo se probó el protocolo).']),
 P('11. Fuentes',h1),
 P('Repositorio del laboratorio (rama main): docs/RESULTS.md, docs/FINDINGS.md y docs/DECISIONS.md (D001–D066); '
   'benchmarks/reports/model-selection-oc226-*.json y model-selection-oc232-nodocker.json; benchmarks/results/ (tasks-*, chat-graded-20261122T014414.json, chat-graded-20261122T123556.json, micro-gguf-20261122T05*.json). '
   'Los resultados en bruto, incluidas las fallas, se conservan sin cambios.',small)]

def deco(c,d):
    c.saveState();c.setFont('A',7.5);c.setFillColor(MUTED)
    c.drawString(18*mm,10*mm,'Laboratorio Ornith · resultados preliminares · 22 nov 2026');c.drawRightString(A4[0]-18*mm,10*mm,f'Página {d.page}');c.restoreState()
doc=SimpleDocTemplate(sys.argv[1],pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=16*mm,bottomMargin=18*mm,
    title='Laboratorio Ornith: resultados preliminares',author='Laboratorio Ornith',subject='Modelos locales en MacBook Air M3 16 GB')
doc.build(story,onFirstPage=deco,onLaterPages=deco)
print('ok')
