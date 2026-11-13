# Plan de Aseguramiento de la Calidad del Software (SQA)
**Observatorio Antojo Colima** · estructura basada en IEEE 730 · versión 1.0 (E1, noviembre de 2026)

Autor: Avlix Eduardo Jiménez Cuevas · Revisó: Carol Ivette Rodríguez Lepe

## 1. Propósito y alcance

Este plan define cómo el equipo asegura que el observatorio entregue **datos correctos, a tiempo y seguros**, y que el pronóstico que se publica sea el que mejor funciona. Cubre todo el sistema del repositorio `carolivettte/tdl-antojo-colima`:

| Componente | Incluido |
|---|---|
| Extractores y captura programada (bronce) | Sí |
| Puerta de calidad y capas plata y oro (`pipeline/`) | Sí |
| Pronóstico y cuadernos de análisis (`pipeline/pronostico.py`, `laboratorio/`) | Sí |
| Tablero Streamlit (`tablero/`) | Sí |
| Las fuentes externas (SNIIM, DENUE) | No: se controlan sus datos al entrar, no la fuente |

Vigencia: E1 a E3. Se revisa al cerrar cada entrega (sección 17).

**Aseguramiento contra control de calidad.** Este plan es de *aseguramiento*: define el proceso (revisión cruzada, CI que bloquea, registros PSP) para que los defectos no lleguen a `main`. El *control* son las verificaciones del producto: la puerta de calidad sobre cada registro, las pruebas y la medición de fiabilidad. El plan dice quién hace cada control, cuándo y qué pasa si falla.

## 2. Documentos de referencia

* IEEE 730, *Software Quality Assurance Processes*.
* ISO/IEC 25010, modelo de calidad del producto (atributos de los requerimientos no funcionales).
* PSP (Personal Software Process): registros de tiempo y defectos.
* [Objetivos de calidad](objetivos.md) · [Requerimientos verificables](../docs/E1/requerimientos.md) · [Diccionario de datos](../docs/E1/diccionario_oro.md) · [Propuesta E0](../docs/E0/propuesta.md).

## 3. Gestión

### 3.1 Organización y roles

| Rol | Responsable | Responsabilidades de calidad |
|---|---|---|
| Ingeniera de datos y líder de calidad E1 | Carol | Extractores, puerta de calidad, pipeline, CI, respaldo, cálculo de fiabilidad; aprueba los PR de datos |
| Analista estadístico y responsable del plan SQA | Avlix | Limpieza justificada, pronóstico y su validación, requerimientos, este plan; aprueba los PR de análisis |
| Revisor cruzado | El otro integrante | Todo PR lo revisa quien **no** lo escribió antes de hacer merge a `main` |

Las dos personas tienen el mismo peso en la decisión de liberar una entrega (etiqueta `eN`).

### 3.2 Tareas de SQA por entrega

| Tarea | Cuándo | Responsable | Salida |
|---|---|---|---|
| Revisar que cada requerimiento tenga evidencia | Antes de la etiqueta | Avlix | Tabla de requerimientos con enlaces vivos |
| Revisar la ficha `ENTREGA.md` contra la rúbrica | Antes de la etiqueta | Carol y Avlix | Ficha completa |
| Calcular fiabilidad con la bitácora | Automático, cada captura | CI | `calidad/fiabilidad.md` |
| Revisar la cuarentena y sus motivos | Semanal | Carol | Nuevos defectos o reglas si aparece un motivo nuevo |
| Revisar el pronóstico publicado contra el real del mes que cerró | Mensual | Avlix | Nota en la relatoría |
| Registrar tiempo y defectos (PSP) | Cada sesión de trabajo | Cada integrante | `tiempo-*.csv`, `defectos-*.csv` |

## 4. Documentación

| Documento | Ubicación | Cómo se valida |
|---|---|---|
| Ficha de entrega por etapa | `docs/EN/ENTREGA.md` | Revisión cruzada contra la rúbrica |
| Requerimientos verificables | `docs/E1/requerimientos.md` | Cada fila con método y evidencia |
| Diccionario de datos de oro | `docs/E1/diccionario_oro.md` | Se **genera** desde el código en cada corrida: no puede desactualizarse |
| Reporte de fiabilidad | `calidad/fiabilidad.md` | Se genera desde la bitácora en cada captura |
| Cuadernos de limpieza y pronóstico | `laboratorio/E1_*.ipynb` | Se ejecutan completos antes del commit; ruff los revisa en CI |
| Relatoría | `docs/relatoria-EN.md` (máximo 2 páginas) | Responde las 6 preguntas con fechas, responsables y evidencia |
| README | `README.md` | Las instrucciones de ejecución se prueban en una copia limpia |

## 5. Estándares, prácticas, convenciones y métricas

**Estándares y convenciones**

* Python 3.11, estilo verificado con `ruff` (línea de 130 caracteres; reglas E, F, I, B).
* Commits con prefijo (`feat:`, `fix:`, `docs:`, `data:`), en español, una idea por commit; cada integrante con su propia identidad de git.
* Ramas `nombre/tema`; a `main` solo se entra por pull request.
* Datos: bronce **inmutable** (nunca se edita a mano); plata y oro se **reconstruyen** desde bronce; fechas ISO (aaaa-mm-dd), claves INEGI de 5 dígitos.
* CSV de calidad: se editan solo con el Bloc de notas (Excel cambió el formato de fechas; defecto 4 de Avlix).

**Métricas**

| Métrica | Fórmula | Umbral | Fuente |
|---|---|---|---|
| Tasa de éxito de la captura | días programados exitosos / días esperados | ≥ 95 % | `fiabilidad.md` |
| Disponibilidad A | MTBF / (MTBF + MTTR) | se reporta; meta ≥ 95 % | `fiabilidad.md` |
| MTTR | horas de reparación / fallas | < 24 h | `fiabilidad.md` |
| Validez de la puerta | válidos / evaluados, por fuente | ≥ 98 % | `reporte_puerta.json`, CI |
| Cobertura de pruebas del pipeline | líneas ejecutadas / líneas | ≥ 80 % | CI |
| Secretos y vulnerabilidades | hallazgos de gitleaks y pip-audit | 0 | CI |
| Error del pronóstico | RMSE y MAPE en 12 meses de prueba | se reporta; alerta si MAPE > 15 % | `comparacion_modelos.csv` |
| Densidad de defectos | defectos PSP / horas registradas | se reporta por integrante | `defectos-*.csv`, `tiempo-*.csv` |
| Eficiencia de remoción | defectos eliminados antes de `main` / defectos totales | se reporta | `defectos-*.csv` (fase eliminado) |

## 6. Revisiones y auditorías

| Revisión | Qué se revisa | Criterio para aprobar |
|---|---|---|
| Revisión de PR (cada cambio) | Código, datos de ejemplo, documentación | CI en verde + aprobación del otro integrante |
| Revisión de la puerta (semanal) | Motivos nuevos en `data/cuarentena/` | Cada motivo nuevo se entiende y, si es un error del sistema, tiene defecto registrado |
| Auditoría de entrega (antes de cada etiqueta) | Ficha `ENTREGA.md` contra la rúbrica, enlaces, que el tablero cargue | Cada criterio de la rúbrica tiene una evidencia que abre |
| Revisión del pronóstico (mensual) | Valor publicado contra el valor real del mes cerrado | Si el real cae fuera del intervalo de 95 % dos meses seguidos, se reabre la selección de modelo |

## 7. Pruebas

| Nivel | Qué cubre | Herramienta | Cuándo corre |
|---|---|---|---|
| Unitarias | Extractores (robots.txt, Retry-After, datos personales, token), reglas de la puerta, imputación, índice, métricas de error | pytest | Cada push y PR |
| Integración | Bronce sintético → plata → cuarentena → oro → diccionario; pronóstico completo sobre una serie sintética | pytest | Cada push y PR |
| Datos reales | Puerta de calidad sobre los datos del repositorio (falla si la validez < 98 %) | `pipeline.ejecutar --verificar` | Cada push y PR |
| Respaldo | Restauración de bronce y verificación de cada SHA-256 | `scripts/respaldo.py` | Cada push, PR y captura |
| Validación del modelo | 12 meses fuera de muestra, Ljung-Box, normalidad de residuos | `laboratorio/E1_pronostico.ipynb` | Cada cambio de modelo |
| Aceptación | Tablero publicado con las cuatro secciones (RF-13) | Demostración | Antes de la etiqueta |

Una prueba que falla **bloquea** el merge. Las pruebas nuevas se escriben cuando aparece un defecto (por ejemplo, el defecto 16 de Carol se encontró con `test_atipico_se_marca_pero_no_se_borra`).

## 8. Reporte de problemas y acción correctiva

1. **Detección**: falla del CI, ejecución con `error` o día sin ejecución en la bitácora, motivo nuevo en la cuarentena, o revisión.
2. **Registro**: si afecta la operación, en `calidad/incidentes.csv` (qué pasó, impacto, causa, acción); en todos los casos, en el `defectos-*.csv` de quien lo corrige, con tipo PSP, fase en que se introdujo y fase en que se eliminó.
3. **Corrección**: rama `nombre/fix-…`, prueba que reproduce el defecto, corrección, PR.
4. **Cierre**: el incidente pasa a `cerrado` cuando la siguiente ejecución programada sale `ok`. El tiempo hasta ese momento entra al MTTR.

Ejemplo real: el `schedule` de GitHub no se disparó el 9 de noviembre (incidente I2, defecto 14 de Carol). Acción correctiva: disparador externo con cron-job.org; MTTR de 5.3 h.

## 9. Herramientas, técnicas y metodologías

GitHub (repositorio, PR, Actions), Python (pandas, Pandera para los esquemas, statsmodels para el pronóstico), pytest y pytest-cov, ruff, gitleaks, pip-audit, Streamlit, cron-job.org (disparador externo), Jupyter. Metodología: arquitectura medallón (bronce, plata, oro) y PSP para la medición personal.

## 10. Control de código

* `main` protegida por convención: solo se entra por PR revisado y con CI en verde.
* Cada entrega se congela con una etiqueta (`e0`, `e1`, …) que no se mueve.
* El robot de captura (`tdl-captura-bot`) solo hace commit de datos y reportes generados, nunca de código.

## 11. Control de medios (respaldo)

* Bronce vive en el repositorio (historial de git) y, además, en un .zip por captura que se guarda **90 días como artefacto de GitHub Actions**, fuera del repositorio.
* El respaldo se considera válido solo si se restauró: `scripts/respaldo.py` lo descomprime en una carpeta temporal y compara cada CSV con la huella SHA-256 que guardó su `.meta.json` al capturarse. Resultado en `data/bitacora/respaldos.csv`.
* Secretos: el token del INEGI solo existe como secreto de GitHub (`INEGI_TOKEN`) y en el `.env` local, que está en `.gitignore`; el token de cron-job.org es de grano fino, limitado a este repositorio y al permiso de Actions.

## 12. Control de proveedores

Las fuentes externas no se controlan, pero sí su efecto:

| Proveedor | Riesgo | Control |
|---|---|---|
| SNIIM | Cambia el formato o deja de publicar | La puerta manda a cuarentena lo que no cumple el esquema; un día `vacio` o `error` aparece en la fiabilidad |
| INEGI (DENUE) | Token vencido o API caída | El error queda en la bitácora sin detener las demás fuentes |
| GitHub Actions | El `schedule` no se dispara | Disparador externo diario (cron-job.org) |
| Dependencias de Python | Vulnerabilidades | pip-audit en cada push |

## 13. Registros: recolección, mantenimiento y retención

| Registro | Archivo | Retención |
|---|---|---|
| Ejecuciones de la captura | `data/bitacora/ejecuciones.csv` | Todo el proyecto (git) |
| Resultado de la puerta por corrida | `data/bitacora/puerta_calidad.csv` | Todo el proyecto |
| Respaldos y su verificación | `data/bitacora/respaldos.csv` | Todo el proyecto; los .zip, 90 días |
| Incidentes | `calidad/incidentes.csv` | Todo el proyecto |
| Tiempo y defectos PSP | `calidad/tiempo-*.csv`, `calidad/defectos-*.csv` | Todo el proyecto |
| Corridas de CI | Pestaña Actions de GitHub | Según GitHub (90 días) |

## 14. Capacitación

| Tema | Quién | Cómo |
|---|---|---|
| Pandera y la puerta de calidad | Avlix | Lectura de `pipeline/esquemas.py` y sus pruebas con Carol |
| Modelos de pronóstico y su diagnóstico | Carol | Recorrido del cuaderno `E1_pronostico.ipynb` con Avlix |
| Edición segura de CSV (sin Excel) | Los dos | Regla de la sección 5 |

## 15. Gestión de riesgos

| Riesgo | Probabilidad | Impacto | Mitigación | Disparador |
|---|---|---|---|---|
| El SNIIM cambia su página y la captura trae 0 registros | Media | Alto | Bitácora, fiabilidad y prueba del parser con HTML de ejemplo | Dos días seguidos `vacio` o `error` |
| El `schedule` de GitHub vuelve a fallar | Ya ocurrió | Medio | Disparador externo | Día sin ejecución en `fiabilidad.md` |
| Huecos MNAR (cebolla 2021–2022) sesgan el índice | Ya ocurrió | Medio | Meses imputados marcados; validación del modelo solo con meses completos | Nuevo hueco de más de 2 meses |
| Un choque de precios (helada, sequía) sale del intervalo | Media | Medio | Se comunica el intervalo, no solo el valor central; revisión mensual | Real fuera del intervalo dos meses seguidos |
| Se filtra un token | Baja | Alto | gitleaks, `.env` ignorado, tokens de mínimo privilegio | Hallazgo de gitleaks |
| Edición manual corrompe un CSV de calidad | Ya ocurrió | Bajo | Solo Bloc de notas; revisión en el PR | El CSV no se puede leer con pandas |
| Una sola persona sabe operar una parte | Media | Medio | Revisión cruzada y capacitación (sección 14) | Ausencia de un integrante cerca de una entrega |

## 16. Glosario

**Bronce / plata / oro**: datos crudos / limpios y validados / integrados para el análisis. **Cuarentena**: registros rechazados por la puerta, con motivo. **Puerta de calidad**: validación automática entre bronce y plata. **MTBF / MTTR**: tiempo medio entre fallas / tiempo medio de reparación. **MNAR**: faltante que depende del valor que falta.

## 17. Cambios a este plan

Se revisa al cerrar cada entrega. Cualquier integrante puede proponer cambios por PR; se aprueban con la revisión del otro. Las versiones quedan en el historial de git.
