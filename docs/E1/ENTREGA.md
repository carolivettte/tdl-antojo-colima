# Entrega E1 · Capa plata, limpieza y puerta de calidad

Equipo: Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas · Etiqueta: `e1` · Repositorio: https://github.com/carolivettte/tdl-antojo-colima · Tablero: https://tdl-antojo-colima.streamlit.app/

## Resumen en tres líneas

1. Cada captura diaria pasa sola por bronce → plata → oro en GitHub Actions: la puerta de calidad (esquemas Pandera) manda cada registro a plata o a cuarentena con su motivo.
2. La capa oro integra SNIIM y DENUE con claves comunes (insumo y municipio INEGI) y construye el **Índice de Costo del Taco** mensual (base 2021 = 100), que es la serie que se pronostica.
3. El tablero publica el pronóstico del modelo con menor error (hoy ARIMA(2,1,0), MAPE 7.8 %) y la fiabilidad de la captura (tasa de éxito, MTBF, MTTR y disponibilidad) calculada de la bitácora.

## Cómo se cumple "terminado"

| Condición | Evidencia |
|---|---|
| Bronce → oro sin intervención | [captura.yml](../../.github/workflows/captura.yml): captura → `pipeline.ejecutar` → respaldo → fiabilidad → commit del bot. Ver los commits `captura: diaria …` y la [pestaña Actions](https://github.com/carolivettte/tdl-antojo-colima/actions) |
| La puerta muestra rechazos y motivos | [data/cuarentena/](../../data/cuarentena/) · [reporte_puerta.json](../../data/plata/reporte_puerta.json) · [bitácora de la puerta](../../data/bitacora/puerta_calidad.csv) · pestaña "Calidad de datos" del tablero |
| El tablero publica el pronóstico elegido por error | [pipeline/pronostico.py](../../pipeline/pronostico.py) corre en cada captura y escribe `data/oro/pronostico.csv` y `comparacion_modelos.csv`; [tablero/app.py](../../tablero/app.py) los muestra en la pestaña "Pronóstico" |
| Disponibilidad demostrada con bitácoras | [calidad/fiabilidad.md](../../calidad/fiabilidad.md), regenerado en cada captura desde [ejecuciones.csv](../../data/bitacora/ejecuciones.csv) |

## Ingeniería de Datos

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Faltantes (MCAR/MAR/MNAR) | [E1_limpieza.ipynb §1](../../laboratorio/E1_limpieza.ipynb) · [oro.py `precios_mensuales`](../../pipeline/oro.py) | 37 de 661 meses-insumo sin publicación (5.6 %). Junio a agosto de 2020 faltan los 8 insumos (pandemia): **MAR** por la fecha. El hueco de la cebolla de 2021–2022 ocurre con precios 51 % y 106 % arriba de lo normal: **probable MNAR**, marcado y declarado como riesgo. La interpolación lineal ganó un experimento de reconstrucción (error 10 % contra 13–24 % de arrastre, media y spline) |
| Atípicos | [plata.py `marcar_atipicos`](../../pipeline/plata.py) · [E1_limpieza.ipynb §2](../../laboratorio/E1_limpieza.ipynb) | z robusto contra la mediana móvil de 120 días (\|z\| > 3.5). Se **marcan, no se borran**: un precio alto puede ser una helada real. Si MAD = 0 se usa la desviación absoluta media (defecto 16). Comparado contra IQR global y z clásico: las reglas globales marcan temporadas completas. Quitar los atípicos cambia la mediana mensual solo 0.7 % |
| Normalización, discretización y reducción | [E1_limpieza.ipynb §3–4](../../laboratorio/E1_limpieza.ipynb) · [dim_insumo](../../data/oro/dim_insumo.csv) · [dim_municipio](../../data/oro/dim_municipio.csv) | Min-max para el semáforo y z-score para el PCA (comparados); semáforo barato/normal/caro por terciles (contra igual ancho); jerarquías insumo → tipo → canasta y municipio → estado; reducción diario → mensual (87 % menos filas) y 8 insumos → 1 índice (correlación 0.95 con PC1) |
| Integración de fuentes heterogéneas | [diccionario_oro.md](diccionario_oro.md) · [catalogos.py](../../pipeline/catalogos.py) · [oro.py](../../pipeline/oro.py) | Conflictos resueltos: **nombres** ("Limón c/semilla # 5 - Primera" → `limon`), **fechas** (dd/mm/aaaa diario → aaaa-mm), **unidades** ($/kg e índice nunca se mezclan), **geografía** (mercado SNIIM y municipio DENUE → clave INEGI 06xxx), **duplicados** entre capturas traslapadas (se conserva la última; si el precio difiere va a cuarentena), **consistencia DENUE** (municipio del texto contra la clave AreaGeo) |
| Puerta de calidad con esquemas | [esquemas.py](../../pipeline/esquemas.py) · [plata.py](../../pipeline/plata.py) · [pruebas](../../tests/test_pipeline.py) | Tipos, rangos plausibles ($1–$300/kg, coordenadas de Colima), catálogos, unicidad y la regla mínimo ≤ frecuente ≤ máximo. Al corte del 13 de noviembre, SNIIM: 5,253 en bronce, 112 duplicados resueltos, 5,138 a plata, **3 a cuarentena** (validez 99.94 %; el reporte se actualiza en cada captura). DENUE: 7,397 de 7,397. En CI la puerta falla si la validez baja de 98 % (objetivo 3) |

## Análisis Estadístico

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Caracterización y descomposición | [E1_pronostico.ipynb §1](../../laboratorio/E1_pronostico.ipynb) | [indice_costo_taco.csv](../../data/oro/indice_costo_taco.csv): 79 meses completos (2020-04 a 2026-10), media 116.4, CV 15.6 %. STL: fuerza de tendencia 0.56, estacionalidad 0.00. **Modelo aditivo justificado**: la amplitud anual no crece con el nivel (correlación −0.73) y el residuo multiplicativo no mejora (8.76 contra 8.83 puntos) |
| Estacionariedad y dependencia | [E1_pronostico.ipynb §2–3](../../laboratorio/E1_pronostico.ipynb) | ADF y KPSS: no estacionaria en nivel, estacionaria en primera diferencia (d = 1). ACF/PACF: rezago 2 negativo (rebote). Correlación cruzada de cada insumo contra el resto de la canasta: ninguno se adelanta de forma confiable |
| Cuatro modelos | [pipeline/pronostico.py](../../pipeline/pronostico.py) · [E1_pronostico.ipynb §4](../../laboratorio/E1_pronostico.ipynb) | SES, Holt amortiguado, Holt-Winters y ARIMA con parámetros interpretados (α ≈ 1, β ≈ 0, γ = 0). ARIMA: d = 1 por la ADF; p = 2 por el corte de la PACF y el menor AIC (504.6, tabla de 9 órdenes). El mismo código corre cada día en el pipeline |
| Selección por error | [comparacion_modelos.csv](../../data/oro/comparacion_modelos.csv) · [E1_pronostico.ipynb §4](../../laboratorio/E1_pronostico.ipynb) | 12 meses fuera de muestra. Gana **ARIMA(2,1,0)**: RMSE 10.7, MAPE 7.8 %; Holt-Winters es el peor (RMSE 15.0) |
| Residuos y comunicación | [E1_pronostico.ipynb §5–6](../../laboratorio/E1_pronostico.ipynb) · tablero, pestaña "Pronóstico" | Ljung-Box p = 0.59 (sin autocorrelación); **varianza estable** (ARCH p = 0.66, Levene p = 0.51); Shapiro p = 0.06. El tablero publica el pronóstico a 3 meses con intervalo de 95 % y una **frase para el cliente** que explica el rango y si conviene promoción, cuidar el precio o si no hay señal clara |

## Calidad en los Sistemas de Información

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Fiabilidad y disponibilidad | [fiabilidad.md](../../calidad/fiabilidad.md) · [incidentes.csv](../../calidad/incidentes.csv) · [scripts/fiabilidad.py](../../scripts/fiabilidad.py) | Se calcula solo con la bitácora. Al corte del 13 de noviembre: **tasa de éxito por ejecución 93.8 %** (15 de 16), 4 de 5 días programados exitosos (80 %), MTBF 108.8 h, MTTR 5.3 h, **A = 95.3 %**, contra el objetivo de E0 de 95 %. La rúbrica pide la bitácora del 6 al 13 de noviembre; la captura empezó a operar el 9, así que se miden los días que existen y se declara. La única falla es el `schedule` de GitHub del 9 de noviembre (incidente I2); desde el disparador externo, todos los días han sido exitosos. Aún no hay 7 días de operación: el reporte se recalcula en cada captura, así que el enlace siempre muestra el valor vigente |
| Seguridad y respaldo | [ci.yml](../../.github/workflows/ci.yml) · [scripts/respaldo.py](../../scripts/respaldo.py) · [respaldos.csv](../../data/bitacora/respaldos.csv) · [plan_sqa.md §11](../../calidad/plan_sqa.md) | gitleaks (46 commits, sin hallazgos) y **pip-audit** (sin vulnerabilidades) en cada push. **Tokens de mínimo permiso**: el del INEGI solo como secreto `INEGI_TOKEN`; el de cron-job.org es de grano fino, limitado a este repositorio y a Actions; el respaldo de bronce se **restaura** en una carpeta temporal y cada CSV se compara contra la huella SHA-256 de su `.meta.json`; el .zip se guarda 90 días como artefacto de Actions, fuera del repositorio |
| Requerimientos verificables | [requerimientos.md](requerimientos.md) | 14 funcionales y 11 no funcionales (ISO/IEC 25010), cada uno con criterio, método y evidencia. **Revisados** contra necesario, no ambiguo, verificable y rastreable, con la tabla de cambios que dejó la revisión |
| Plan SQA (IEEE 730) | [plan_sqa.md](../../calidad/plan_sqa.md) | Roles, métricas con umbral, revisiones, pruebas por nivel, acción correctiva, control de código y medios, proveedores y riesgos |
| Integración continua | [ci.yml](../../.github/workflows/ci.yml) | ruff (también en los cuadernos), 23 pruebas de pytest con **cobertura mínima de 80 %** en el pipeline, puerta de datos, respaldo restaurable, pip-audit y gitleaks |
| Registros PSP | [tiempo-carol.csv](../../calidad/tiempo-carol.csv) · [defectos-carol.csv](../../calidad/defectos-carol.csv) · [tiempo-avlix.csv](../../calidad/tiempo-avlix.csv) · [defectos-avlix.csv](../../calidad/defectos-avlix.csv) | Defectos 15 a 17 de Carol y 5 a 11 de Avlix |

## Relatoría

[docs/relatoria-E1.md](../relatoria-E1.md)

## Preparación para E2

Ruta del experimento: **negocio**, con la taquería de Manzanillo entrevistada en E0. Acuerdo con el cliente: pendiente de acordar.

## Uso de IA

Se usó un asistente de IA (Claude) como apoyo para revisar y depurar código y redactar documentación. Las decisiones, la validación de resultados y la responsabilidad del trabajo son del equipo.
