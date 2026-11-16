# Fiabilidad y disponibilidad de la captura

Generado automáticamente por `scripts/fiabilidad.py` el 2026-11-16T16:29:52+00:00 a partir de `data/bitacora/ejecuciones.csv`. Se recalcula después de cada captura.

Servicio medido: captura diaria del SNIIM en bronce. Periodo: 2026-11-09 a 2026-11-16T16:29+00:00 UTC (184.5 h).

Ventana que pide E1: 2026-11-06 a 2026-11-13. La captura programada empezó a operar el 2026-11-09: los días anteriores no había sistema que medir, así que la medición cubre 7 días y no 7.

| Métrica | Valor | Cómo se calcula |
|---|---|---|
| **Tasa de éxito por ejecución** | **95.5 %** | 21 de 22 ejecuciones de todas las fuentes terminaron sin error |
| Tasa de éxito de las ejecuciones programadas | 100.0 % | de 7 ejecuciones programadas del SNIIM |
| Días esperados | 7 | Un día por cada ventana programada cerrada (16:00–18:00 UTC) |
| Días exitosos | 6 | Ejecución programada con estado ok |
| **Tasa de éxito por día** | **85.7 %** | exitosos / esperados (objetivo ≥ 95%: no cumple) |
| Fallas | 1 | Días sin ejecución programada o con error |
| **MTBF** | **179.16 h** | tiempo en operación / fallas |
| **MTTR** | **5.34 h** | tiempo de reparación total / fallas |
| **Disponibilidad A** | **97.1 %** | MTBF / (MTBF + MTTR) |

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

## Todas las ejecuciones por fuente, tipo y estado

| Fuente | Tipo | Estado | Ejecuciones |
|---|---|---|---|
| denue | manual | error | 1 |
| denue | manual | ok | 1 |
| inegi | manual | vacio | 1 |
| sniim | manual | ok | 11 |
| sniim | manual | vacio | 1 |
| sniim | programada | ok | 7 |
