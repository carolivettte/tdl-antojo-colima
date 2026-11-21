# Auditoría cruzada E2

Quality Lead E2: Avlix Eduardo Jiménez Cuevas. Proceso basado en ISO 9001 (cláusula 9.2, auditoría interna) e ISO/IEC 25040 (evaluación): criterios definidos antes de auditar, evidencia verificable para cada hallazgo, severidad y recomendación con responsable.

**Severidad**

| Nivel | Significa | Ejemplo |
|---|---|---|
| **Crítico** | El sistema entrega datos incorrectos, expone datos personales o secretos, o incumple un entregable obligatorio | Un token en el repositorio; oro con filas que no se pueden rastrear |
| **Mayor** | Un requisito o una característica de calidad no se cumple, pero hay forma de detectarlo o rodearlo | La puerta de calidad deja pasar un formato inválido; una prueba que no corre en CI |
| **Menor** | Afecta la claridad, la documentación o el mantenimiento, no el resultado | Una gráfica sin explicación; un nombre de columna confuso |

**Alcance (según el proyecto):** del jueves 19 al lunes 23 de noviembre, cada equipo audita el observatorio de otro equipo asignado **en su estado de E1** (etiqueta `e1`), con **ISO/IEC 25010** (producto) e **ISO/IEC 25012** (datos de la capa oro). Al mismo tiempo, otro equipo audita el nuestro.

**Criterios:** las 8 características de ISO/IEC 25010 y las características de ISO/IEC 25012, verificadas con evidencia reproducible (comandos, archivos y commits), más los entregables de E1 que sostienen esas características (puerta de calidad, fiabilidad, CI, seguridad y respaldo).

---

## 1. Auditoría de nuestro sistema por otro equipo

*Equipo auditor:* **pendiente de asignación por los docentes** · *Fecha:* — · *Versión auditada:* etiqueta `e1`

| ID | Hallazgo | Criterio | Severidad | Evidencia | Recomendación | Responsable | Estado |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

**Respuesta del equipo:** *(por cada hallazgo: acción, commit que lo corrige y fecha).*

---

## 2. Auditoría que hacemos al otro equipo

*Equipo auditado:* **pendiente de asignación** · *Repositorio:* — · *Versión auditada:* su etiqueta `e1` · *Fecha:* —

Lista de verificación que se aplicará:

| # | Norma y característica | Qué se revisa en su etiqueta `e1` | Cómo se verifica |
|---|---|---|---|
| 1 | 25010 · Adecuación funcional | Los entregables de E1 existen y hacen lo que dicen | Clonar en `e1`, instalar y correr su pipeline y sus pruebas |
| 2 | 25010 · Eficiencia de desempeño | Duración de su pipeline y de su captura | Medir el tiempo de su corrida completa; revisar la duración de sus jobs en Actions |
| 3 | 25010 · Compatibilidad | Su capa oro se lee con otra herramienta | Abrir sus CSV con el módulo `csv` de Python y revisar codificación y columnas |
| 4 | 25010 · Capacidad de interacción | Su tablero se entiende sin explicación | Abrir el tablero; cada vista explica qué muestra y sus límites |
| 5 | 25010 · Fiabilidad | Disponibilidad y MTTR calculados de su bitácora | Recalcular con su bitácora de ejecuciones |
| 6 | 25010 · Seguridad | Secretos, datos personales y dependencias | Buscar tokens y columnas personales; correr `pip-audit` |
| 7 | 25010 · Mantenibilidad | Pruebas, cobertura y estilo | `pytest --cov`; linter; revisar su CI |
| 8 | 25010 · Portabilidad | Corre en otra máquina | Instalar desde cero siguiendo su README; buscar rutas fijas |
| 9 | 25012 · Exactitud, completitud y consistencia | Sobre su capa oro | Contar valores fuera de dominio, vacíos y reglas entre columnas |
| 10 | 25012 · Credibilidad, actualidad y trazabilidad | Origen y antigüedad de sus datos | Seguir 3 filas de oro elegidas al azar hasta su fuente y fecha |
| 11 | 25012 · Confidencialidad | Datos personales en sus capas | Revisar columnas y muestras de bronce, plata y oro |

| ID | Hallazgo | Criterio | Severidad | Evidencia | Recomendación | Responsable sugerido |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## 3. Autoauditoría previa (antes de entregar)

Hecha por el Quality Lead con los mismos criterios, para llegar a la auditoría externa con lo encontrado ya corregido. Cada hallazgo también está en el registro PSP de defectos.

| ID | Hallazgo | Criterio | Severidad | Evidencia | Acción tomada | Estado |
|---|---|---|---|---|---|---|
| AP-01 | El extractor usa `html.parser`, que con celdas sin `</td>` junta los textos y guarda filas con contenido equivocado **sin avisar** (pasan el filtro de 8 celdas) | ISO 25012 exactitud · ISO 25010 corrección funcional | **Mayor** | Banco de pruebas: 0 % de esas filas bien leídas con `html.parser` y 100 % con `lxml`; prueba `test_celdas_sin_cierre_engañan_a_html_parser_pero_no_a_lxml` | Cambiar el parser del extractor a `lxml`, según el resultado del experimento y la corrida de confirmación | Se cierra con la confirmación |
| AP-02 | La capa de salud omitía los centros de salud públicos (SCIAN 621112) | Completitud (ISO 25012) | Mayor | Primera captura: 31 clínicas; segunda: 1,235 puntos en total | Se agregó la clase y se recapturó | Cerrado (defecto 22) |
| AP-03 | Índice de zonas con sesgo de números pequeños | Exactitud semántica · ética (sesgos) | Mayor | 25 de 75 celdas "alta" tenían 2 o menos puntos de afluencia | Umbral mínimo de 3 puntos de afluencia | Cerrado (defecto 24) |
| AP-04 | La pestaña Competencia del tablero no explicaba qué muestra ni sus límites | ISO 25010 usabilidad | Menor | `scripts/iso25010.py`: 4 de 5 pestañas con texto | Se agregó la explicación con el sesgo del DENUE | Cerrado |
| AP-05 | El registro del experimento guardaba la hora de fin en la columna `inicio_utc` | Trazabilidad del experimento | Menor | Bloque 1 de 2k3 y bifactorial | Corregido para los bloques siguientes; documentado en `laboratorio/experimento.py` | Cerrado |
| AP-06 | Cinco filas del PSP de Carol no se podían leer como CSV (comas dentro de la descripción) | ISO 9001 7.5 información documentada | Menor | `pandas.read_csv` fallaba en la fila 21 | Comas cambiadas por punto y coma | Cerrado (defecto 29) |
