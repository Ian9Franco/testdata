# Rúbrica

El CSV lo puntúa `python3 -m ops_lab.grade`. El resto se corrige a mano. Total 100.

## A — Triage (40)

El script da 40 × aciertos / 11, menos 4 por cada penalización, con piso 0.

Un acierto es el asset, el equipo y la prioridad juntos. `Field service` vale; `Field Ops` no. Un asset puede tener dos filas. SCN-LKS-02 a Customer Success no reemplaza la fila de SCN-LKS-01: la auditoría está en el infeed.

Penaliza abrir ruido (mantenimiento planificado, umbrales que no se cruzan, el robot gemelo sano) y mandar al equipo contrario cuando el playbook ya separó la causa. Mandar RBT-LKS-01 a Customer Success, como nota de saturación, no penaliza. Mandarlo a Field Service o Perception, sí.

## B — Llamada (15)

- 5: nombra RBT-CDR-01, 06:45–08:30 PT, e-stop, cinta en movimiento, aire normal, y que los otros dos robots siguen.
- 4: el guion de seguridad está. Nadie puentea el e-stop. El reset lo hace la planta con la tarjeta publicada.
- 4: no inventa que ya quedó funcionando. El último bucket sigue en falla.
- 2: el mail está en inglés, corto, y no echa la culpa al supervisor.

## C — Aceptación (20)

- 8: el scorecard coincide con el daily pack. Fallan solo picks/min y aluminio de RBT-RVB-01, y los 300 minutos de SCN-RVB-03. El uptime 0.967 pasa. El rate mezclado no alcanza para aprobar el aluminio.
- 4: la ventana es 4–7 nov, por asset. El burn-in queda afuera. El blip del miércoles se cita y no se vuelve a paginar.
- 4: acepta residuo (robot y scanner) y el infeed de contenedores. No firma el robot de contenedores ni SCN-RVB-03.
- 4: el mail está en inglés, dice que no se firma el sitio entero hoy, y no promete una hora de visita que no controlás.

## D — Redline (15)

HOLD es obligatorio. Cada ítem vale cerca de 2 puntos: el nombre Harbour, el 93% sin los buckets malos, el deploy de HBR-04, el QC duplicado (15,236 y no 30,472), el 21% que es Lakeshore y no Harbor, el 15:00 PT que en realidad es las 07:00 y solo el robot sano marca 96 psi. Cerrar con "figures are final → no se envía" es el punto que falta.

Si reescribís un mail "ya corregido" y lo mandarías hoy, con HBR-04 todavía tirando OCC, no está listo.

## E — Handoff (10)

- 4: P1 son el e-stop y el OCC de HBR-04, con dueño y con lo que sigue desconocido.
- 3: el sábado "quiet" queda desmentido con la ventana de aire, y el draft queda en HOLD.
- 3: Riverbend, el lente sucio y los tres temas de datos están, separados de lo que no se pagina.

## Lo que suele bajar la nota

Mirar solo el uptime. Promediar la semana. Creer el log del sábado. Contar un agarre de OCC como éxito porque la pinza cerró. Tratar un lente sucio como si hubiera desaparecido el papel. Firmar Riverbend porque "están corriendo". Inventar el desenlace de la llamada.
