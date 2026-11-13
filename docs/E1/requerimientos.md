# Requerimientos verificables · Observatorio Antojo Colima

Cada requerimiento dice **qué** debe cumplir el sistema, **cómo** se verifica y **dónde** está la evidencia. Si un requerimiento no tiene una forma objetiva de comprobarse, no está en esta lista.

Métodos de verificación: **P** = prueba automática (pytest, corre en CI), **A** = análisis de bitácora o de datos, **I** = inspección, **D** = demostración.

## Funcionales

| ID | Requerimiento | Criterio de aceptación | Método | Evidencia |
|---|---|---|---|---|
| RF-01 | El sistema debe capturar diariamente los precios del SNIIM de los 8 insumos de la canasta taquera en el mercado de Colima. | Una ejecución por día en la ventana de 16:00 a 18:00 UTC, con estado `ok` en la bitácora. | A | [ejecuciones.csv](../../data/bitacora/ejecuciones.csv) · [fiabilidad.md](../../calidad/fiabilidad.md) |
| RF-02 | La captura diaria debe incluir al menos una publicación del SNIIM aunque la fuente publique solo dos veces por semana. | La ventana de consulta cubre los últimos 7 días. | I | [scripts/captura.py](../../scripts/captura.py) (`diaria`) · defecto 15 de Carol |
| RF-03 | Cada archivo de bronce debe tener metadatos de captura. | Cada CSV tiene su `.meta.json` con URL sin token, fecha UTC, número de registros y SHA-256. | I · P | [data/bronce/](../../data/bronce/) · `test_token_nunca_se_guarda` (la URL se guarda sin token) · `scripts/respaldo.py` verifica cada SHA-256 en cada captura |
| RF-04 | La puerta de calidad debe mandar cada registro a plata o a cuarentena, sin perder ninguno. | registros de bronce = válidos + cuarentena + duplicados exactos resueltos. | P · A | `test_pipeline_completo_bronce_a_oro` · [reporte_puerta.json](../../data/plata/reporte_puerta.json) |
| RF-05 | Todo registro rechazado debe llevar un motivo legible. | La columna `motivo` existe y no está vacía en el 100 % de la cuarentena. | P | `test_cada_rechazo_lleva_motivo` · [data/cuarentena/](../../data/cuarentena/) |
| RF-06 | Los duplicados entre capturas traslapadas deben resolverse sin intervención. | Un duplicado exacto deja un solo registro (la captura más reciente); si el precio difiere, ambos van a cuarentena. | P | `test_duplicado_exacto_se_resuelve_y_conflicto_va_a_cuarentena` |
| RF-07 | Los atípicos deben marcarse, no eliminarse. | Un precio atípico conserva su fila en plata con `atipico = True` y su `z_robusto`. | P | `test_atipico_se_marca_pero_no_se_borra` |
| RF-08 | Los meses sin publicación deben imputarse y quedar identificados. | Cada mes imputado tiene `imputado = True` y `metodo = interpolacion_lineal`; no se extrapola fuera del rango observado. | P | `test_mes_faltante_se_imputa_y_queda_marcado` |
| RF-09 | La capa oro debe integrar SNIIM y DENUE con claves comunes. | Insumos con nombre normalizado y municipios con clave INEGI de 5 dígitos (06001 a 06010) en las dos fuentes. | P · I | `test_pipeline_completo_bronce_a_oro` · [diccionario_oro.md](diccionario_oro.md) |
| RF-10 | El Índice de Costo del Taco debe valer 100 en promedio en 2021. | Promedio de `indice` en 2021 = 100 ± 0.01. | P | `test_indice_base_2021_vale_100` |
| RF-11 | El sistema debe comparar cuatro modelos de pronóstico y publicar el de menor error. | `comparacion_modelos.csv` tiene SES, Holt, Holt-Winters y ARIMA con MAE, RMSE y MAPE, y exactamente un `elegido = True`, el de menor RMSE. | P | `test_comparar_evalua_los_cuatro_y_elige_uno` · [E1_pronostico.ipynb](../../laboratorio/E1_pronostico.ipynb) |
| RF-12 | El pronóstico debe publicarse con intervalo de 95 % y sin usar el mes en curso incompleto. | 3 meses pronosticados con `li_95 < valor < ls_95`; un mes con datos solo hasta antes del día 25 no entra al ajuste. | P | `test_pronostico_publica_intervalo_y_quita_mes_incompleto` |
| RF-13 | El tablero debe mostrar el pronóstico elegido, la tabla de errores, la cuarentena con motivos y la fiabilidad. | Las cuatro secciones aparecen al abrir el tablero publicado. | D | [tablero/app.py](../../tablero/app.py) · enlace del tablero en [ENTREGA.md](ENTREGA.md) |
| RF-14 | El DENUE debe guardarse sin datos personales. | Bronce y plata no contienen razón social, teléfono, correo ni sitio web. | P | `test_denue_elimina_datos_personales` |

## No funcionales

| ID | Atributo (ISO/IEC 25010) | Requerimiento | Criterio de aceptación | Método | Evidencia |
|---|---|---|---|---|---|
| RNF-01 | Fiabilidad · disponibilidad | La captura diaria debe estar disponible. | Tasa de éxito ≥ 95 % de los días programados (objetivo de calidad 1); disponibilidad A = MTBF / (MTBF + MTTR) reportada. | A | [fiabilidad.md](../../calidad/fiabilidad.md), regenerado en cada captura |
| RNF-02 | Fiabilidad · recuperabilidad | Una falla de la captura debe repararse en menos de un día. | MTTR < 24 h. | A | [fiabilidad.md](../../calidad/fiabilidad.md) · [incidentes.csv](../../calidad/incidentes.csv) |
| RNF-03 | Exactitud de datos | Al menos 98 % de los registros de cada fuente deben pasar la puerta (objetivo de calidad 3). | `tasa_validez ≥ 0.98`; si baja, el CI falla. | P · A | `python -m pipeline.ejecutar --verificar` en [ci.yml](../../.github/workflows/ci.yml) |
| RNF-04 | Seguridad · confidencialidad | El repositorio no debe contener secretos. | gitleaks sin hallazgos en todo el historial; el token solo vive en el secreto `INEGI_TOKEN`. | P | job de gitleaks en [ci.yml](../../.github/workflows/ci.yml) · `test_token_nunca_se_guarda` |
| RNF-05 | Seguridad · dependencias | Las dependencias no deben tener vulnerabilidades conocidas. | pip-audit sin hallazgos en `requirements.txt`. | P | paso pip-audit en [ci.yml](../../.github/workflows/ci.yml) |
| RNF-06 | Seguridad · integridad y respaldo | Bronce debe poder restaurarse íntegro. | El respaldo se restaura en una carpeta temporal y el 100 % de los CSV coinciden con su SHA-256; copia fuera del repositorio por 90 días. | P · A | `test_respaldo_detecta_archivo_alterado` · [respaldos.csv](../../data/bitacora/respaldos.csv) |
| RNF-07 | Ética · uso de fuentes | El extractor debe respetar robots.txt, identificarse y no saturar los sitios. | Rutas prohibidas por robots.txt no se consultan; User-Agent con contacto; pausa ≥ 1.5 s; respeta `Retry-After` en 429. | P | `test_robots_bloquea_rutas_prohibidas` · `test_user_agent_honesto` · `test_respeta_retry_after_en_429` |
| RNF-08 | Mantenibilidad · capacidad de prueba | El pipeline debe tener pruebas automáticas suficientes. | Cobertura de líneas de `pipeline/` ≥ 80 %; si baja, el CI falla. | P | `pytest --cov=pipeline --cov-fail-under=80` en [ci.yml](../../.github/workflows/ci.yml) |
| RNF-09 | Mantenibilidad · analizabilidad | El código debe seguir un estilo único. | `ruff check .` sin errores (incluye los cuadernos). | P | paso ruff en [ci.yml](../../.github/workflows/ci.yml) |
| RNF-10 | Trazabilidad | Todo dato de oro debe poder rastrearse hasta su archivo de bronce. | Plata conserva `archivo_origen` y `capturado_utc`; oro se reconstruye completo desde bronce en cada corrida. | I | [plata.py](../../pipeline/plata.py) · [diccionario_oro.md](diccionario_oro.md) |
| RNF-11 | Eficiencia | La corrida diaria completa (captura, pipeline, pronóstico y respaldo) no debe tardar más de 10 minutos. | Duración del job de Actions < 10 min. | A | historial de la [pestaña Actions](https://github.com/carolivettte/tdl-antojo-colima/actions) |

## Revisión contra las características de un buen requerimiento

Cada requerimiento se revisó con cuatro preguntas. Si alguna fallaba, se reescribió.

* **Necesario**: ¿qué pasa si no se cumple? Si nada, sobra.
* **No ambiguo**: ¿dos personas lo leerían igual? Se eliminaron palabras como "rápido", "confiable" o "suficiente" y se cambiaron por números.
* **Verificable**: ¿hay una prueba, un cálculo o una inspección que diga sí o no?
* **Rastreable**: ¿de dónde viene (objetivo de calidad de E0, pregunta del observatorio o criterio de la rúbrica) y dónde se prueba?

| ID | Necesario porque… | Rastreable a |
|---|---|---|
| RF-01 | Sin captura diaria no hay serie que pronosticar | Objetivo 1 · Puerta 1 (validación) |
| RF-02 | El SNIIM publica 2 veces por semana; con menos días se pierden publicaciones (defecto 15) | Objetivo 1 · incidente I3 |
| RF-03 | Sin metadatos no se puede probar la integridad ni el origen de un dato | Seguridad · linaje |
| RF-04 | Si un registro desaparece sin motivo, la puerta borra en silencio | Rúbrica: puerta de calidad |
| RF-05 | Un rechazo sin motivo no se puede corregir | Rúbrica: puerta de calidad |
| RF-06 | Las capturas se traslapan a propósito; sin esto el precio se contaría doble | Rúbrica: integración (duplicados) |
| RF-07 | Un pico de precio puede ser el hallazgo más importante | Rúbrica: atípicos |
| RF-08 | Los modelos necesitan una serie mensual sin huecos | Rúbrica: faltantes |
| RF-09 | Sin claves comunes, SNIIM y DENUE no se pueden cruzar | Rúbrica: integración |
| RF-10 | El cliente entiende "10 % más que en 2021", no un precio suelto | Pregunta del observatorio |
| RF-11 | Gana el modelo con menor error, no el más sofisticado | Rúbrica: selección por error |
| RF-12 | Un pronóstico sin intervalo promete de más; un mes incompleto lo sesga | Rúbrica: residuos y comunicación |
| RF-13 | El cliente consulta el tablero, no el repositorio | Rúbrica: terminado cuando |
| RF-14 | La ley de datos personales y el compromiso ético de E0 | Objetivo 2 |
| RNF-01 | El cliente necesita el dato cuando lo consulta | Objetivo 1 · rúbrica: fiabilidad |
| RNF-02 | Una falla larga deja huecos que luego hay que imputar | Rúbrica: fiabilidad (MTTR) |
| RNF-03 | Si la validez cae, algo cambió en la fuente | Objetivo 3 |
| RNF-04 | Un token filtrado da acceso a la API a nombre del equipo | Objetivo 2 · rúbrica: seguridad |
| RNF-05 | Una dependencia vulnerable compromete el pipeline | Rúbrica: seguridad |
| RNF-06 | Bronce es la única copia del dato crudo; si se pierde, no se recupera | Rúbrica: seguridad (respaldo) |
| RNF-07 | Robots.txt y la carga a los servidores públicos son compromisos de E0 | Plan ético de E0 |
| RNF-08 | Sin pruebas, un cambio puede romper la puerta sin que nadie lo note | Rúbrica: integración continua |
| RNF-09 | Un estilo único facilita la revisión cruzada | Plan SQA §5 |
| RNF-10 | Un auditor debe poder seguir un dato de oro hasta su archivo | Linaje (E2) |
| RNF-11 | La corrida diaria no debe acercarse al límite de tiempo de Actions | Plan SQA §5 |

**Cambios que dejó la revisión**

| Antes | Problema | Después |
|---|---|---|
| "La captura debe ser confiable" | Ambiguo: ¿qué es confiable? | RNF-01: tasa de éxito ≥ 95 % por día, con A = MTBF / (MTBF + MTTR) reportada |
| "Los datos deben estar limpios" | No verificable | Se partió en RF-04 a RF-08, cada uno con su prueba |
| "El pronóstico debe ser bueno" | Ambiguo | RF-11 y RF-12: menor RMSE en 12 meses de prueba, intervalo de 95 % |
| RF-03 marcado como prueba automática | Ninguna prueba revisaba que existiera el `.meta.json`; solo se verificaba su huella | Método cambiado a inspección + verificación del respaldo; queda como mejora para E2 escribir esa prueba |
| "El pipeline debe ser rápido" | Sin número | RNF-11: menos de 10 minutos por corrida |

## Matriz de trazabilidad con los objetivos de calidad

| Objetivo de calidad ([objetivos.md](../../calidad/objetivos.md)) | Requerimientos |
|---|---|
| 1. Éxito de la captura programada ≥ 95 % | RF-01, RF-02, RNF-01, RNF-02 |
| 2. Cero secretos y cero datos personales | RF-14, RNF-04 |
| 3. Validez de precios ≥ 98 % | RF-04, RF-05, RF-06, RNF-03 |
