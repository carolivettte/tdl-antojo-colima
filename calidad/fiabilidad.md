# Fiabilidad y disponibilidad de la captura

Generado automáticamente por `scripts/fiabilidad.py` el 2026-11-24T02:53:45+00:00 a partir de `data/bitacora/ejecuciones.csv`. Se recalcula después de cada captura.

Servicio medido: captura diaria del SNIIM en bronce. Periodo: 2026-11-09 a 2026-11-24T02:53+00:00 UTC (362.9 h).

Ventana que pide E1: 2026-11-06 a 2026-11-13. La captura programada empezó a operar el 2026-11-09: los días anteriores no había sistema que medir, así que la medición cubre 15 días y no 7.

| Métrica | Valor | Cómo se calcula |
|---|---|---|
| **Tasa de éxito por ejecución** | **97.6 %** | 40 de 41 ejecuciones de todas las fuentes terminaron sin error |
| Tasa de éxito de las ejecuciones programadas | 100.0 % | de 14 ejecuciones programadas del SNIIM |
| Días esperados | 15 | Un día por cada ventana programada cerrada (16:00–18:00 UTC) |
| Días exitosos | 14 | Ejecución programada con estado ok |
| **Tasa de éxito por día** | **93.3 %** | exitosos / esperados (objetivo ≥ 95%: no cumple) |
| Fallas | 1 | Días sin ejecución programada o con error |
| **MTBF** | **357.56 h** | tiempo en operación / fallas |
| **MTTR** | **5.34 h** | tiempo de reparación total / fallas |
| **Disponibilidad A** | **98.5 %** | MTBF / (MTBF + MTTR) |

## Fallas

| Día | Tipo | Hora esperada (UTC) | Restablecida (UTC) | Horas de reparación |
|---|---|---|---|---|
| 2026-11-09 | no se ejecuto | 16:15 | 2026-11-09 21:35 | 5.34 |

Causas y acciones correctivas: `calidad/incidentes.csv`.

## Día por día

| Día | Estado | Ejecuciones programadas |
|---|---|---|
| 2026-11-09 | no se ejecuto | 0 |
| 2026-11-10 | ok | 1 |
| 2026-11-11 | ok | 1 |
| 2026-11-12 | ok | 1 |
| 2026-11-13 | ok | 1 |
| 2026-11-14 | ok | 1 |
| 2026-11-15 | ok | 1 |
| 2026-11-16 | ok | 1 |
| 2026-11-17 | ok | 1 |
| 2026-11-18 | ok | 1 |
| 2026-11-19 | ok | 1 |
| 2026-11-20 | ok | 1 |
| 2026-11-21 | ok | 1 |
| 2026-11-22 | ok | 1 |
| 2026-11-23 | ok | 1 |

## Todas las ejecuciones por fuente, tipo y estado

| Fuente | Tipo | Estado | Ejecuciones |
|---|---|---|---|
| denue | manual | error | 1 |
| denue | manual | ok | 1 |
| denue_afluencia | manual | ok | 2 |
| inegi | manual | vacio | 1 |
| marco_geo | manual | ok | 2 |
| sniim | manual | ok | 19 |
| sniim | manual | vacio | 1 |
| sniim | programada | ok | 14 |
