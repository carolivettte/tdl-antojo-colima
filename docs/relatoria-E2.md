# Relatoría E2 · Experimento, fuente especializada y auditoría

Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas · 20 de noviembre de 2026

## 1. ¿Qué nos propusimos?

1. Integrar una fuente geoespacial al pipeline y al tablero, sin datos personales, con cada fila de oro rastreable hasta bronce.
2. Decir con un experimento factorial qué configuración del extractor es la mejor y cuánto mejora, y confirmarlo.
3. Medir el sistema con ISO/IEC 25010 y los datos de oro con ISO/IEC 25012.

## 2. ¿Qué hicimos?

| Fecha y hora | Quién | Qué | Tiempo |
|---|---|---|---|
| 20 nov 06:50–07:50 | Carol | Plan de E2 contra el PDF y la lista del docente; diseño de la fuente geoespacial y del índice de zonas; captura y uniones espaciales, probadas con datos sintéticos | 60 min |
| 20 nov 07:50–08:42 | Carol | Clon limpio, captura real (1,213 puntos), defecto 22, recaptura (1,235 puntos) | 37 min efectivos |
| 20 nov 08:42–09:21 | Carol | Linaje, rastreador, pestaña Mapa, ISO 25012, ética; 6 commits | 39 min |
| 20 nov 09:22–09:42 | Avlix | Diseño del experimento, banco local y sesión 1 (bloque 1) | 20 min |
| 20 nov 13:50–14:13 | Avlix | Sesión 2: 2³, bifactorial y 2⁴ (bloque 2) | 23 min |
| 20 nov 21:45–22:39 | Avlix | Sesión 3 (bloque 3) y corrida de confirmación | 12 min |
| 20 nov 22:40–23:00 | Avlix | Análisis, cambio de parser, ISO 25010, normativa y auditoría | 20 min |

Detalle: [tiempo-carol.csv](../calidad/tiempo-carol.csv) · [tiempo-avlix.csv](../calidad/tiempo-avlix.csv). El código se escribió con apoyo de un asistente de IA (declarado en la ficha). Las corridas, las capturas, la revisión y las decisiones fueron del equipo.

## 3. ¿Qué decidimos y por qué?

1. **No inventar puestos ambulantes.** El DENUE solo registra negocios fijos y semifijos, y en Colima la informalidad laboral es de 47.4 %. Descartamos estimar un número de puestos, porque sería un dato inventado. Usamos escuelas y centros de salud como generadores de afluencia y construimos un índice **relativo** por celda de 1 km. Antes de publicarlo lo validamos contra los semifijos que sí están registrados (Spearman ρ = 0.40, p ≈ 5×10⁻¹¹).
2. **Experimentar contra una copia local, bloqueando por sesión.** Medir contra el sitio real habría mezclado la latencia de la red con los factores y cargado al servidor del SNIIM con cientos de consultas. Bloquear fue la decisión que salvó el análisis: la tarde salió 2.4 veces más lenta en todo, y el bloque explica tanta variación como los procesos.
3. **Confirmar la razón, no el tiempo absoluto.** Con un bloque tan grande, predecir los segundos de una sesión nueva no sirve. La confirmación intercala la configuración actual y la mejor en la misma sesión y compara cuántas veces más rápida es una que la otra: el modelo predijo de 3.14 a 3.59 y se observó 3.46. Entre CSV y Parquet nos quedamos con CSV, porque el formato no cambia el tiempo (p = 0.64).

## 4. ¿Qué salió mal y cómo lo corregimos?

* **El extractor guardaba filas equivocadas sin avisar desde E0** (Avlix 30). Con una celda sin `</td>`, `html.parser` juntaba los textos (`"03/11/2026Caja de 19 kg.Colima…"`) y la fila pasaba el filtro de 8 celdas. Lo encontró el experimento; lo comprobamos con la página real del SNIIM y cambiamos el extractor a `lxml`, con una prueba nueva. Es el hallazgo más valioso de la etapa.
* **La primera captura de salud traía solo 31 clínicas** (Carol 22). Los centros de salud públicos están en otra clase del SCIAN (621112). Se agregó la clase y se recapturó.
* **El índice de zonas premiaba al azar** (Carol 24). 25 de 75 zonas "alta" tenían 2 escuelas o menos. Ahora una celda necesita al menos 3 para clasificarse.
* **El banco de pruebas no terminaba** (Avlix 31 y 32). Al quitar `</tr>`, `html.parser` anidaba miles de filas, y con 128 mil filas cada corrida pasaba de 2 minutos. Se limitó el daño a `</td>` y el banco se redujo a 66,625 filas.
* **El primer Tukey no encontraba diferencias** (Avlix 34). La variación entre sesiones inflaba el error; se aplicó sobre log(tiempo) ajustado por bloque.
* **Pendiente:** la auditoría cruzada. A la fecha de la ficha, los docentes no han asignado equipos. La plantilla y 6 hallazgos de autoauditoría ya están en [auditoria-E2.md](../calidad/auditoria-E2.md).

## 5. ¿Qué aprendimos de cada materia?

**Ingeniería de Datos.** Una unión espacial solo es confiable si se mide en un sistema de coordenadas métrico. Las áreas y los radios de 1 km se calculan en UTM 13N, no en grados, y además hubo que recortar las islas Revillagigedo: sin el recorte, Colima tendría 157 km² de más y todas sus densidades bajarían. La ética también se mide: el umbral contra números pequeños redujo de 23 a 2 las zonas "alta" sin ninguna taquería.

**Análisis Estadístico.** El bloqueo no es un trámite. Sin él, el efecto del parser (p = 0.018 en la escala original) se habría perdido entre las sesiones; en log(tiempo), con el bloque en el modelo, es inequívoco (p < 0.0001). La media fracción 2⁴⁻¹ llegó a las mismas conclusiones que el 2⁴ con la mitad de las corridas, porque los factores que sobraban (formato y lote) no hacían nada.

**Calidad.** Medir encuentra lo que revisar no encuentra. El script de ISO 25010 detectó que la pestaña Competencia no explicaba nada (defecto 36). El experimento, que era la evidencia de eficiencia, terminó siendo evidencia de exactitud (ISO 25012): el parser de E0 leía mal en silencio.

## 6. Evidencias

* Commits de Carol `6f3ec3a`, `10a149f`, `a808af0`, `1d757b3`, `dc0db76` y `3d56753` en la rama `carol/e2-geo`. Los de Avlix están en la rama `avlix/e2-experimento`.
* [E2_experimento.ipynb](../laboratorio/E2_experimento.ipynb) · [laboratorio/resultados/](../laboratorio/resultados/) (66 corridas y 10 de confirmación).
* [reporte_geo.json](../data/plata/reporte_geo.json) · [linaje.csv](../data/oro/linaje.csv) · pestaña Mapa del [tablero](https://tdl-antojo-colima.streamlit.app/).
* [iso25010.md](../calidad/iso25010.md) · [iso25012.md](../calidad/iso25012.md) · [normativa.md](../calidad/normativa.md) · [etica-datos.md](etica-datos.md).
