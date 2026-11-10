# Guía de práctica

El aviso al que aplicaste pide a alguien que mantenga una flota de robots y scanners en plantas de reciclaje: atender el llamado, correr consultas, detectar anomalías, escalar al equipo correcto y escribir reportes en inglés para gente técnica y no técnica. También cubre instalaciones nuevas y pruebas de aceptación.

Glacier, la empresa del aviso, publica dos productos: un robot que identifica y separa materiales sobre la cinta, y un sistema de analítica con cámaras para contar la corriente y avisar cuando algo se desvía (cinta vacía, material de valor que se escapa al residuo, equipo aguas arriba que dejó de clasificar). Este lab practica esas tareas con una empresa ficticia, Northline, y cinco plantas inventadas.

No afilia a Glacier. No uses estos textos como si fueran documentos internos.

## Cómo se traduce el aviso

| En el aviso | En este lab |
| --- | --- |
| Monitorear la flota con consultas y un proceso | `ops_lab/sql/daily_pack.sql` y `playbooks/daily_monitoring.md` |
| Primera línea de troubleshooting, con guion | `inbox/TCK-1042.md` y `playbooks/call_scripts.md` |
| Reportes internos y externos, sin errores | el draft de Harbor y `playbooks/reporting.md` |
| Escalar la anomalía al equipo correcto | `my_work/escalations.csv` |
| Instalación nueva y customer acceptance | Riverbend, ventana 4–7 nov |
| Atención al detalle | el log del sábado dice que estuvo tranquilo. Verificá. |

Los nombres Field Service, Perception, Deployment Engineering, Customer Success y Data Engineering son del ejercicio. En una empresa real los equipos se llaman distinto. Importa el criterio: hardware, modelo, puesta en marcha, planta del cliente, o dato roto.

## Horario, en hora Argentina

El puesto trabaja en Pacific Time, de lunes a miércoles, viernes y sábado. Jueves y domingo libres. En noviembre 2026 Estados Unidos ya salió del horario de verano (el cambio fue el 1 de noviembre), así que Pacific es PST, UTC−8. Argentina es UTC−3 todo el año. La diferencia es **5 horas**.

| Turno del aviso | Pacific | Argentina |
| --- | --- | --- |
| Lunes, martes, viernes | 08:00–16:00 | 13:00–21:00 |
| Miércoles | 09:00–16:00 | 14:00–21:00 |
| Sábado | 04:00–13:00 | 09:00–18:00 |

El sábado a las 04:00 PT son las 09:00 en Buenos Aires. El escenario del lab es el lunes 9 de noviembre de 2026 a las 08:30 PT, o sea 13:30 ART. El jueves 5, que para este puesto es franco, es justo el día en el que Lakeshore tuvo el evento de PET: el lunes hay que reconstruirlo porque el viernes no abrió esa planta.

Cuando Estados Unidos vuelva a PDT (segundo domingo de marzo), la diferencia con Argentina pasa a 4 horas. Pacific se mueve y Argentina no. Confirmalo la semana de una entrevista.

Otras ciudades del aviso, en noviembre: San Pablo y Santiago también van 5 horas adelante de Pacific; Venezuela, 4; Colombia y Perú, 3. El sábado a las 04:00 PT son las 07:00 en Bogotá o Lima.

## Cuatro sesiones

1. Leé los tres playbooks y el glosario. Corré el briefing y anotá, en una oración, qué pregunta contesta cada consulta. No escales todavía.
2. Hacé `exercises/TAKEHOME.md` con reloj, en inglés, sin `solutions/`.
3. Corré el grader. Leé la rúbrica. Reescribí el entregable más flojo sin mirar la respuesta modelo.
4. Repetí la parte A en un CSV en blanco, 45 minutos. La segunda vez importa más que la primera.

## Cómo se evalúa este tipo de prueba

Suele mirarse si seguís el proceso cuando el tablero está en verde, si no firmás un número que no recalculaste, y si el mail en inglés dice qué pasó y qué no podés afirmar todavía. Un 93% semanal que esconde seis horas al 62% es el error típico. También lo es inventar que la llamada ya se resolvió.

Escribí simple. Una oración corta y exacta vale más que un párrafo elegante.
