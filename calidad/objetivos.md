# Objetivos de calidad · Observatorio Antojo Colima

Tres objetivos medibles que alimentan el plan SQA de E1. Cada uno tiene una métrica, una fuente de evidencia y un umbral.

| # | Objetivo | Métrica | Umbral | Evidencia | Se mide desde |
|---|---|---|---|---|---|
| 1 | **Éxito de la captura programada** | Ejecuciones programadas exitosas ÷ ejecuciones programadas esperadas × 100, por fuente | **≥ 95%** | `data/bitacora/ejecuciones.csv` y el historial de GitHub Actions | E0 (primera captura programada) |
| 2 | **Cero secretos y cero datos personales** | Hallazgos de gitleaks en el repositorio; columnas personales del DENUE presentes en bronce | **0 y 0** | Job de gitleaks en `ci.yml`; prueba `test_denue_elimina_datos_personales` | E0 |
| 3 | **Completitud y validez de precios** | Registros de precios del SNIIM con fecha válida, producto y precio frecuente numérico > 0 ÷ total de registros; el resto va a cuarentena con su motivo | **≥ 98%** (cuarentena ≤ 2%) | Puerta de calidad 1 (bronce → plata) y `data/cuarentena/` | E1 |

## Cómo se calcula el objetivo 1

Se medirá la tasa de éxito de las ejecuciones programadas por fuente durante el periodo observado:

```
tasa de éxito = ejecuciones programadas exitosas / ejecuciones programadas esperadas × 100
```

El objetivo es alcanzar al menos 95 %. Las ejecuciones manuales de prueba o de descarga histórica se registran por separado y no entran en este cálculo.

Una ejecución sin registros nuevos se considera exitosa únicamente si se comprueba que la consulta funcionó y que la fuente no publicó datos para ese periodo. Los errores de conexión o extracción cuentan como fallos.

Las ejecuciones programadas que no se realizaron cuentan como no exitosas y se identifican comparando el horario previsto con el historial de GitHub Actions.

Esta métrica mide éxito por ejecución; no equivale a disponibilidad medida por tiempo de operación. Los resultados se reportarán cuando existan bitácoras reales.

