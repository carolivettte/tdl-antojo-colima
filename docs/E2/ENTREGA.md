# Entrega E2 · Experimento, fuente especializada y auditoría

> **AVISO IMPORTANTE · LA AUDITORÍA CRUZADA SE MUEVE A E3.** El profesor Mónico informó al grupo que **todo lo relacionado con la auditoría cruzada se pospone hasta la entrega E3**, y que él subirá los formularios correspondientes que se deberán llenar para esa auditoría. Por eso **las secciones 1 y 2 de [calidad/auditoria-E2.md](../../calidad/auditoria-E2.md) (la auditoría que otro equipo hace de nuestro sistema y la que nosotros hacemos a otro equipo) quedan sin llenar en la etiqueta `e2`**: no es una omisión del equipo, es una indicación del docente. Se completarán en E3 con los formularios oficiales. Lo que sí se entrega en E2 es la preparación: severidades, alcance, lista de verificación de 11 puntos y la autoauditoría previa (sección 3 de ese documento), con 6 hallazgos ya atendidos.

Equipo: Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas · Etiqueta: `e2` · Repositorio: https://github.com/carolivettte/tdl-antojo-colima · Tablero: https://tdl-antojo-colima.streamlit.app/

## Resumen en tres líneas

1. **Fuente especializada geoespacial:** escuelas, centros de salud y hospitales del DENUE (1,235 puntos, sin nombres) y los límites del Marco Geoestadístico del INEGI, unidos en GeoPandas con 7,397 negocios. Producen un índice de zonas validado contra los puestos semifijos (Spearman ρ = 0.40, p ≈ 5×10⁻¹¹) y una pestaña **Mapa** en el tablero.
2. **Experimento (ruta ingeniería):** la mejor configuración del extractor es **4 procesos + `lxml` + CSV**, **3.36 veces más rápida** que la actual (IC 95 %: 3.18 a 3.54; 70 % menos tiempo) y con **menos filas mal leídas** (8.5 % → 5.0 %). La confirmación en una sesión nueva dio 3.46 veces, dentro del intervalo de predicción. El extractor real ya usa `lxml`.
3. **Calidad medida, no declarada:** ISO/IEC 25010 cumple 8 de 8 e ISO/IEC 25012 sobre oro cumple 15 de 15, con scripts que miden el sistema. El 100 % de las filas de oro (4,503) se rastrea hasta su archivo de bronce, con su fecha de ingesta y su SHA-256.

## Cómo se cumple "terminado"

| Condición del proyecto | Evidencia |
|---|---|
| El equipo dice con evidencia qué combinación es la mejor y cuánto mejora | [E2_experimento.ipynb §4 y §7](../../laboratorio/E2_experimento.ipynb): 4 procesos + `lxml` + CSV, 3.36 veces más rápida (IC 95 %: 3.18 a 3.54), confirmada con 3.46 veces |
| El observatorio muestra su fuente especializada | Tablero, pestaña **Mapa** (zonas de 1 km, puntos sin nombres, municipios) · [pipeline/geo.py](../../pipeline/geo.py) en cada corrida diaria |
| Existe un reporte de auditoría de su sistema hecho por otro equipo | **Se mueve a E3 por indicación del profesor Mónico**, quien subirá los formularios para hacerla. Preparación entregada en [calidad/auditoria-E2.md](../../calidad/auditoria-E2.md) (ver el aviso al inicio de esta ficha) |

## Lista del docente (Ingeniería de Datos, 20 % de la unidad 4)

| Entregable | Dónde está |
|---|---|
| 1. Fuente especializada **geoespacial** (DENUE y Marco Geoestadístico, GeoPandas y mapa) | Captura: [extractores/geo.py](../../extractores/geo.py) (`python -m scripts.captura geo`, también en Actions) · Puerta del Marco y uniones espaciales: [pipeline/geo.py](../../pipeline/geo.py) · Oro: `data/oro/geo_municipios.csv`, `geo_zonas.csv`, `geo_puntos.csv`, `geo_municipios.geojson` · Mapa: [tablero/app.py](../../tablero/app.py), pestaña Mapa |
| 2. Declaración de ética y legalidad | [docs/etica-datos.md](../etica-datos.md): términos de uso, `robots.txt` (copias en [docs/etica/robots/](../etica/robots/)), licencias, privacidad (LFPDPPP 2025) y 8 sesgos con su mitigación medida |
| 3. Linaje oro → bronce con fecha de ingesta | Columnas `archivos_bronce` e `ingesta_min`/`ingesta_max` (o `capturado_utc`) en cada tabla de oro · [data/oro/linaje.csv](../../data/oro/linaje.csv) · [pipeline/linaje.py](../../pipeline/linaje.py) · `python -m scripts.rastrear precios_mensuales --donde insumo=limon mes=2026-11` · CI corre `python -m scripts.rastrear --verificar` |
| 4. Ficha y relatoría | Esta ficha · [docs/relatoria-E2.md](../relatoria-E2.md) |

## Ingeniería de Datos (rúbrica)

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Fuente especializada (45) | [geo.py](../../pipeline/geo.py) · [reporte_geo.json](../../data/plata/reporte_geo.json) · pestaña Mapa | **Integrada al pipeline:** bronce con `.meta.json` y SHA-256, puerta del Marco con cuarentena (clave fuera de Colima, geometría vacía o inválida, duplicado, municipio faltante) y oro en cada corrida. **Uniones espaciales en UTM 13N (EPSG:32613):** 3,278 de 3,278 puntos caen en un municipio, el municipio del DENUE coincide con el del Marco en 98.9 %, el 99.6 % de las escuelas y clínicas tiene una taquería a 1 km, y hay una cuadrícula de 1 km. **Sin datos personales:** los nombres y domicilios se eliminan antes de bronce y el pipeline se detiene si llega una columna personal. **Problema real:** el DENUE no registra ambulantes; no inventamos puestos, usamos la afluencia como indicador relativo (alta, media, baja) y lo validamos contra los semifijos registrados |
| Ética y legalidad (30) | [etica-datos.md](../etica-datos.md) | Por fuente: base legal, términos del INEGI (no alterar los metadatos, atribución, no aparentar aval), `robots.txt` (gaia.inegi.org.mx no publica uno: 404, sin restricciones según RFC 9309), licencias, privacidad y **8 sesgos con cifras**. Ejemplo: sin umbral, 25 de 75 zonas "alta" tenían 2 o menos escuelas; con un mínimo de 3, quedan 48 zonas "alta" con mediana de 6.5 |
| Linaje (15) | [linaje.csv](../../data/oro/linaje.csv) · [rastrear.py](../../scripts/rastrear.py) · [test_linaje.py](../../tests/test_linaje.py) | **4,503 de 4,503 filas de oro trazables; 7 de 7 archivos de bronce íntegros.** Un mes imputado hereda el linaje de sus meses vecinos; el pronóstico, el de `indice_costo_taco`. Una prueba altera un bronce y comprueba que el SHA-256 lo detecta |

## Análisis Estadístico (rúbrica)

Cuaderno: [laboratorio/E2_experimento.ipynb](../../laboratorio/E2_experimento.ipynb) · Banco: [banco_sniim.py](../../laboratorio/banco_sniim.py) · Corridas: [experimento.py](../../laboratorio/experimento.py) · Datos crudos: [laboratorio/resultados/](../../laboratorio/resultados/)

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| Diseño y principios (25) | Cuaderno §1 y §3 · [2k3.csv](../../laboratorio/resultados/2k3.csv) | 2³ (procesos 1/4 × parser `html.parser`/`lxml` × formato CSV/Parquet) sobre una **copia local** de 220 páginas del SNIIM (filas reales de Colima, 26 páginas dañadas a propósito), nunca contra el sitio. **3 réplicas**, **orden aleatorizado** en cada bloque con semilla registrada y **bloqueo por sesión** (mañana, tarde y noche del 20 de noviembre). El bloqueo fue necesario: la sesión de la tarde fue unas 2.4 veces más lenta en todo, y el bloque explica tanta variación como los procesos |
| Dos factores con interacción (20) | Cuaderno §5 · [bifactorial.csv](../../laboratorio/resultados/bifactorial.csv) | Procesos (**1, 2, 4**) × parser, 3 réplicas en bloques, ANOVA de dos vías en log(tiempo). Ambos factores son significativos (p < 0.0001); la interacción queda en el límite (p = 0.051): `lxml` ayuda un poco más con menos procesos. Tukey ajustado por bloque: cada nivel difiere del anterior, con rendimientos decrecientes (de 1 a 2 procesos, −43 %; de 2 a 4, otro −35 %) |
| Completo vs. fraccionado (20) | Cuaderno §6 · [2k4.csv](../../laboratorio/resultados/2k4.csv) | Matrices del 2⁴ (16 corridas, corridas de verdad) y de la media fracción 2⁴⁻¹ con **D = ABC, I = ABCD (resolución IV)**. Alias: A = BCD, B = ACD, C = ABD, D = ABC, AB = CD, AC = BD, AD = BC. **Ahorro:** 8 corridas (50 %) y 49.6 % del tiempo de máquina. La fracción identifica los mismos efectos activos (A y B, por el método de Lenth); su estimado es exactamente efecto + alias del 2⁴ |
| Análisis y confirmación (25) | Cuaderno §3, §4 y §7 · [confirmacion.csv](../../laboratorio/resultados/confirmacion.csv) | ANOVA de efectos fijos, efectos, Pareto, gráficas de efectos principales e interacción, residuos (Q-Q, contra ajustados y en el orden de corrida), Shapiro, Levene y Durbin-Watson. Box-Cox (λ = −0.16) justifica el modelo en log(tiempo). **Óptimo:** 4 procesos + `lxml` + CSV (C no es significativo, p = 0.64). **Confirmación:** 5 y 5 corridas intercaladas al azar en una sesión nueva: **3.46 veces más rápido**, dentro del intervalo de predicción de 95 % (3.14 a 3.59) |

**Qué se cambió en el sistema.** El experimento mostró que `html.parser`, el parser que usaba el extractor desde E0, **guarda en silencio filas con contenido equivocado** cuando una celda no se cierra. Se comprobó con la página real del SNIIM. El extractor ahora usa `lxml` ([sniim.py](../../extractores/sniim.py), `PARSER_HTML`) y hay una prueba nueva con la página real dañada. Los 4 procesos no se aplican a la captura en línea: ahí manda el compromiso ético de E0 (una petición a la vez, con pausa).

**Cambio de ruta respecto a E1.** En E1 se eligió la ruta negocio con la taquería de Manzanillo. El acuerdo con el cliente no se cerró a tiempo para diseñar, correr y replicar una campaña dentro de la semana de E2, así que se tomó la ruta ingeniería. Esta ruta además permite controlar el orden de corrida, replicar y bloquear con rigor.

## Calidad en los Sistemas de Información (rúbrica)

| Criterio | Evidencia | Nota del equipo |
|---|---|---|
| ISO/IEC 25010 (30) | [iso25010.md](../../calidad/iso25010.md) · `python -m scripts.iso25010` | **8 de 8** con una métrica medida al ejecutar el sistema. **Eficiencia de desempeño = el experimento**: 5.7 s contra 19.8 s para 220 páginas. **Fiabilidad = la de E1**: A = 97.97 %. La medición también encontró y corrigió una pestaña del tablero sin explicación (defecto 36) |
| ISO/IEC 25012 (25) | [iso25012.md](../../calidad/iso25012.md) · `python -m scripts.iso25012` (corre en cada captura) | **15 de 15** sobre la capa oro, incluidas exactitud, completitud, consistencia (99.1 %, con la regla municipio DENUE = municipio Marco), credibilidad, actualidad, confidencialidad (0 columnas personales) y trazabilidad (100 %) |
| Antecedentes normativos (10) | [normativa.md](../../calidad/normativa.md) | ISO/IEC 9126 y 14598 → SQuaRE (25010:2011 y 2023, 25012, 25022/23/24, 25030, 25040), con dónde se aplica cada una. ISO 9001:2026 (vigente desde el 16 de septiembre de 2026; la de 2015 vale hasta el 30 de septiembre de 2029), cláusula por cláusula con su evidencia |
| Auditoría cruzada (25) | [auditoria-E2.md](../../calidad/auditoria-E2.md) | **Se mueve a E3 por indicación del profesor Mónico**, con los formularios que él subirá. En E2 se entrega la preparación: severidades definidas (crítico, mayor, menor), alcance según el PDF (estado de E1 con 25010 y 25012), lista de verificación de 11 puntos para auditar al otro equipo y **6 hallazgos de autoauditoría** con evidencia y acción |
| Registros PSP | [tiempo-carol.csv](../../calidad/tiempo-carol.csv) · [defectos-carol.csv](../../calidad/defectos-carol.csv) · [tiempo-avlix.csv](../../calidad/tiempo-avlix.csv) · [defectos-avlix.csv](../../calidad/defectos-avlix.csv) | Defectos 22 a 29 de Carol y 30 a 40 de Avlix |

## Relatoría

[docs/relatoria-E2.md](../relatoria-E2.md)

## Uso de IA

Se usó un asistente de IA (Claude) como apoyo para escribir y depurar código, diseñar el análisis estadístico y redactar documentación. Las corridas del experimento, las capturas de datos, la validación de resultados y las decisiones son del equipo, que también es responsable del trabajo.
