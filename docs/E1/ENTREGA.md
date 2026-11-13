# Entrega E1 · Capa plata, limpieza y puerta de calidad

Equipo: Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas · Etiqueta: `e1` · Repositorio: https://github.com/carolivettte/tdl-antojo-colima · Tablero: _(enlace de Streamlit Community Cloud)_

## Resumen en tres líneas

1. Cada captura diaria pasa sola por bronce → plata → oro en GitHub Actions: la puerta de calidad (esquemas Pandera) manda cada registro a plata o a cuarentena con su motivo.
2. La capa oro integra SNIIM y DENUE con claves comunes (insumo y municipio INEGI) y construye el **Índice de Costo del Taco** mensual (base 2021 = 100), que es la serie que se pronostica.
3. El tablero publica el pronóstico del modelo con menor error y la fiabilidad de la captura (tasa de éxito, MTBF, MTTR y disponibilidad) calculada de la bitácora.

## Cómo se cumple "terminado"

| Condición | Evidencia |
|---|---|
| Bronce → oro sin intervención | [captura.yml](../../.github/workflows/captura.yml): captura → `pipeline.ejecutar` → respaldo → fiabilidad → commit del bot. Ver los commits `captura: diaria …` y la [pestaña Actions](https://github.com/carolivettte/tdl-antojo-colima/actions) |
| La puerta muestra rechazos y motivos | [data/cuarentena/](../../data/cuarentena/) · [reporte_puerta.json](../../data/plata/reporte_puerta.json) · [bitácora de la puerta](../../data/bitacora/puerta_calidad.csv) · pestaña "Calidad de datos" del tablero |
| El tablero publica el pronóstico elegido por error | [tablero/app.py](../../tablero/app.py), pestaña "Pronóstico" (lee `data/oro/pronostico.csv` y `comparacion_modelos.csv`) |
| Disponibilidad demostrada con bitácoras | [calidad/fiabilidad.md](../../calidad/fiabilidad.md), regenerado en cada captura desde [ejecuciones.csv](../../data/bitacora/ejecuciones.csv) |

## Ingeniería de Datos

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Faltantes (MCAR/MAR/MNAR) | _(Avlix)_ `laboratorio/E1_limpieza.ipynb` · [oro.py `precios_mensuales`](../../pipeline/oro.py) | Los meses sin publicación del SNIIM se imputan por interpolación lineal en el tiempo y quedan marcados (`imputado`, `metodo`); nunca se rellena antes del primer ni después del último dato |
| Atípicos | [plata.py `marcar_atipicos`](../../pipeline/plata.py) · _(Avlix)_ cuaderno de limpieza | z robusto contra la mediana móvil de 120 días (\|z\| > 3.5). Se **marcan, no se borran**: un precio alto puede ser una helada real. Si MAD = 0 se usa la desviación absoluta media (defecto 16) |
| Normalización, discretización y reducción | _(Avlix)_ cuaderno de limpieza · [dim_insumo](../../data/oro/dim_insumo.csv) · [dim_municipio](../../data/oro/dim_municipio.csv) | Jerarquías insumo → tipo → canasta y municipio → estado; reducción diario → mensual con la mediana; índice con base 2021 = 100 |
| Integración de fuentes heterogéneas | [diccionario_oro.md](diccionario_oro.md) · [catalogos.py](../../pipeline/catalogos.py) · [oro.py](../../pipeline/oro.py) | Conflictos resueltos: **nombres** ("Limón c/semilla # 5 - Primera" → `limon`), **fechas** (dd/mm/aaaa diario → aaaa-mm), **unidades** ($/kg e índice nunca se mezclan), **geografía** (mercado SNIIM y municipio DENUE → clave INEGI 06xxx), **duplicados** entre capturas traslapadas (se conserva la última; si el precio difiere va a cuarentena), **consistencia DENUE** (municipio del texto contra la clave AreaGeo) |
| Puerta de calidad con esquemas | [esquemas.py](../../pipeline/esquemas.py) · [plata.py](../../pipeline/plata.py) · [pruebas](../../tests/test_pipeline.py) | Tipos, rangos plausibles ($1–$300/kg, coordenadas de Colima), catálogos, unicidad y la regla mínimo ≤ frecuente ≤ máximo. SNIIM: 5,157 en bronce, 24 duplicados exactos resueltos, 5,130 a plata, **3 a cuarentena** (validez 99.94 %). DENUE: 7,397 de 7,397. En CI la puerta falla si la validez baja de 98 % (objetivo 3) |

## Análisis Estadístico

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Caracterización de la serie | _(Avlix)_ `laboratorio/E1_pronostico.ipynb` | Serie: [indice_costo_taco.csv](../../data/oro/indice_costo_taco.csv), mensual desde 2020-04 |
| Estacionariedad y dependencia | _(Avlix)_ | |
| Cuatro modelos | _(Avlix)_ | SES, Holt, Holt-Winters y ARIMA |
| Selección por error | _(Avlix)_ · [comparacion_modelos.csv](../../data/oro/comparacion_modelos.csv) | MAE, RMSE y MAPE en el conjunto de prueba |
| Residuos y comunicación | _(Avlix)_ · tablero, pestaña "Pronóstico" | |

## Calidad en los Sistemas de Información

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad | [fiabilidad.md](../../calidad/fiabilidad.md) · [incidentes.csv](../../calidad/incidentes.csv) · [scripts/fiabilidad.py](../../scripts/fiabilidad.py) | Se calcula solo con la bitácora. Al corte del 12 de noviembre: 3 de 4 días programados exitosos (75 %), MTBF 90.6 h, MTTR 5.3 h, A = 94.4 %. La única falla es el `schedule` de GitHub del 9 de noviembre (incidente I2); desde el disparador externo, todos los días han sido exitosos. Aún no hay 7 días de operación: el reporte se recalcula en cada captura, así que el enlace siempre muestra el valor vigente |
| Seguridad y respaldo | [ci.yml](../../.github/workflows/ci.yml) · [scripts/respaldo.py](../../scripts/respaldo.py) · [respaldos.csv](../../data/bitacora/respaldos.csv) | gitleaks y **pip-audit** en cada push; el respaldo de bronce se **restaura** en una carpeta temporal y cada CSV se compara contra la huella SHA-256 de su `.meta.json`; el .zip se guarda 90 días como artefacto de Actions, fuera del repositorio |
| Requerimientos verificables | _(Avlix)_ `docs/E1/requerimientos.md` | |
| Plan SQA (IEEE 730) | _(Avlix)_ `calidad/plan_sqa.md` | |
| Integración continua | [ci.yml](../../.github/workflows/ci.yml) | ruff, 20 pruebas de pytest con **cobertura mínima de 80 %** en el pipeline, puerta de datos, respaldo restaurable, pip-audit y gitleaks |
| Registros PSP | [tiempo-carol.csv](../../calidad/tiempo-carol.csv) · [defectos-carol.csv](../../calidad/defectos-carol.csv) · [tiempo-avlix.csv](../../calidad/tiempo-avlix.csv) · [defectos-avlix.csv](../../calidad/defectos-avlix.csv) | Defectos 15 a 17 de Carol encontrados por las pruebas y la bitácora |

## Relatoría

_(Avlix)_ [relatoria.md](relatoria.md)

## Uso de IA

Se usó un asistente de IA (Claude) como apoyo para revisar y depurar código y redactar documentación. Las decisiones, la validación de resultados y la responsabilidad del trabajo son del equipo.
