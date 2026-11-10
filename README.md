# Laboratorio de operaciones de flota

Práctica para un puesto de **Data and Robotics Operations Analyst**: monitorear robots y scanners en plantas de reciclaje, separar una falla real del ruido, escalarla al equipo correcto y escribir en inglés sin inventar un número.

La empresa del ejercicio es **Northline**. No es Glacier, no usa datos de clientes reales y no es una prueba oficial. El mapa con el aviso de Glacier está en [`docs/guia_es.md`](docs/guia_es.md).

## Empezá por acá

1. Leé [`docs/guia_es.md`](docs/guia_es.md) (horario de Argentina incluido).
2. Corré el paquete del lunes:

```bash
python3 -m ops_lab.console briefing
```

3. Hacé [`exercises/TAKEHOME.md`](exercises/TAKEHOME.md) con el reloj en 150 minutos, sin abrir `solutions/` ni `tests/`.
4. Recién después:

```bash
python3 -m ops_lab.grade my_work/escalations.csv
```

La rúbrica y las respuestas modelo están en `solutions/`.

## Qué hay en el repo

| Ruta | Para qué |
| --- | --- |
| `data/glacier_ops.sqlite` | Una semana de flota, ya generada |
| `ops_lab/sql/daily_pack.sql` | Las consultas del proceso |
| `playbooks/` | Definiciones, umbrales, guion de llamada, reportes |
| `inbox/` | Tickets, logs del turno anterior y un draft que no está listo |
| `exercises/TAKEHOME.md` | La prueba |
| `solutions/` | Spoilers |

No hace falta instalar paquetes. Python 3.11+ y `sqlite3`.

```bash
python3 -m ops_lab.console list
python3 -m ops_lab.console query low_air_islands
python3 -m unittest tests.test_lab -v
python3 -m ops_lab.generate   # rehace la base, el inbox y el snapshot
```

`my_work/` es tuyo y no se versiona. Copiá `exercises/escalations_template.csv` ahí cuando arranques.
