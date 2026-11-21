# Marco normativo de calidad · de ISO/IEC 9126 a SQuaRE e ISO 9001

Quality Lead E2: Avlix Eduardo Jiménez Cuevas. Esta tabla ubica cada norma que usa el observatorio: de qué norma viene, qué la reemplazó y **dónde se aplica en el repositorio**, con su evidencia medida.

## 1. Evolución: de ISO/IEC 9126 y 14598 a la familia SQuaRE (ISO/IEC 25000)

| Norma anterior | Qué cubría | La reemplaza (SQuaRE) | Qué cambió | Cómo la aplicamos | Evidencia |
|---|---|---|---|---|---|
| ISO/IEC 9126-1:2001 | Modelo de calidad del producto con 6 características (funcionalidad, fiabilidad, usabilidad, eficiencia, mantenibilidad, portabilidad) | **ISO/IEC 25010:2011**, actualizada por **ISO/IEC 25010:2023** | 2011: 8 características (se agregan seguridad y compatibilidad; funcionalidad pasa a ser adecuación funcional). 2023: 9 características (se agrega protección o *safety*; usabilidad pasa a *capacidad de interacción* y portabilidad a *flexibilidad*; madurez pasa a *ausencia de fallas*) | Una métrica medida por cada una de las 8 características que pide el proyecto, con el nombre de 2023 donde cambió (capacidad de interacción); *protección* se declara no aplicable | [iso25010.md](iso25010.md) · `python -m scripts.iso25010` |
| ISO/IEC 9126-2, -3 y -4 | Métricas externas, internas y de calidad en uso | **ISO/IEC 25023** (medición del producto) e **ISO/IEC 25022** (calidad en uso) | Las métricas se separan del modelo y se definen como funciones de medición con su fórmula | Cada métrica tiene fórmula, umbral y se calcula con código, no a mano | [scripts/iso25010.py](../scripts/iso25010.py) |
| *(no existía en 9126)* | Calidad de los **datos** | **ISO/IEC 25012:2008** (modelo) e **ISO/IEC 25024** (medición) | 15 características en tres grupos: inherentes, inherentes y dependientes del sistema, y dependientes del sistema | Las 15 medidas sobre la capa oro en cada corrida diaria | [iso25012.md](iso25012.md) · `python -m scripts.iso25012` |
| ISO/IEC 14598 (partes 1 a 6) | Proceso de evaluación del producto | **ISO/IEC 25040** (proceso de evaluación) | Un solo proceso: establecer requisitos, especificar, diseñar, ejecutar y concluir la evaluación | Requisitos → métricas con umbral → script que mide → reporte con veredicto → auditoría cruzada | Este documento · [auditoria-E2.md](auditoria-E2.md) |
| ISO/IEC 9126 (requisitos implícitos) | — | **ISO/IEC 25030** (requisitos de calidad) | Los requisitos de calidad se escriben verificables y rastreables | RNF con atributo de 25010, criterio, método y evidencia | [requerimientos.md](../docs/E1/requerimientos.md) |

Divisiones de SQuaRE que usamos: **2500n** gestión de la calidad, **2501n** modelos (25010, 25012), **2502n** medición (25022, 25023, 25024), **2503n** requisitos (25030), **2504n** evaluación (25040).

## 2. ISO 9001: sistema de gestión de la calidad

La edición vigente es **ISO 9001:2026**, publicada el 16 de septiembre de 2026; reemplaza a la de 2015, que sigue siendo válida para certificación durante la transición, hasta el 30 de septiembre de 2029. La revisión es moderada: conserva el enfoque a procesos, el ciclo PHVA (planear, hacer, verificar, actuar) y el pensamiento basado en riesgos. La tabla usa los números de cláusula de la estructura armonizada, la misma en ambas ediciones.

| Requisito de ISO 9001 | Qué pide | Cómo lo cumple el observatorio | Evidencia |
|---|---|---|---|
| 4.4 Procesos | Procesos definidos con entradas, salidas y responsables | Bronce → plata → oro, con responsable por etapa y una corrida diaria automatizada | [pipeline/README.md](../pipeline/README.md) · [captura.yml](../.github/workflows/captura.yml) |
| 6.1 Riesgos y oportunidades | Identificar riesgos y planear acciones | Riesgos éticos, legales y de sesgo con su mitigación | [etica-datos.md](../docs/etica-datos.md) · [plan_sqa.md](plan_sqa.md) |
| 6.2 Objetivos de la calidad | Objetivos medibles con seguimiento | 3 objetivos con métrica, umbral y fuente de evidencia | [objetivos.md](objetivos.md) |
| 7.5 Información documentada | Controlar los documentos y registros | Todo versionado en git; bronce inmutable con SHA-256 | Historial de git · `data/bronce/**/*.meta.json` |
| 8.5.2 Identificación y trazabilidad | Identificar las salidas y rastrear su origen | Linaje: cada fila de oro apunta a su archivo de bronce y su fecha de ingesta | [linaje.csv](../data/oro/linaje.csv) · `python -m scripts.rastrear` |
| 8.7 Control de las salidas no conformes | Separar lo que no cumple para que no se use | Cuarentena con motivo en la puerta de calidad | [data/cuarentena/](../data/cuarentena/) |
| 9.1 Seguimiento, medición, análisis y evaluación | Medir el desempeño y la eficacia | Fiabilidad (MTBF, MTTR, disponibilidad), ISO 25012 diario e ISO 25010 por entrega | [fiabilidad.md](fiabilidad.md) · [iso25012.md](iso25012.md) · [iso25010.md](iso25010.md) |
| 9.2 Auditoría interna | Auditar a intervalos planificados | Auditoría cruzada entre equipos, con severidad, evidencia y recomendación | [auditoria-E2.md](auditoria-E2.md) |
| 10.2 No conformidad y acción correctiva | Registrar la causa y corregirla | Registros PSP de defectos (fase de origen y de detección) e incidentes | [defectos-avlix.csv](defectos-avlix.csv) · [defectos-carol.csv](defectos-carol.csv) · [incidentes.csv](incidentes.csv) |
| 10.3 Mejora continua | Mejorar con base en datos | Diseño de experimentos para elegir la configuración del extractor | [E2_experimento.ipynb](../laboratorio/E2_experimento.ipynb) |

## 3. Cómo se relacionan

ISO 9001 dice **cómo se gestiona** la calidad (procesos, registros, auditoría y mejora). SQuaRE dice **qué se mide** del producto (25010) y de los datos (25012), y **cómo se evalúa** (25040). En el observatorio, la cláusula 9.1 de ISO 9001 se cumple con las mediciones de 25010 y 25012, y la 9.2 con la auditoría cruzada.

## Referencias

- ISO. *ISO 9001:2026 Quality management systems — Requirements*, publicada el 2026-09-16 (reemplaza a ISO 9001:2015 y su enmienda 1:2024).
- ISO/IEC. *ISO/IEC 25010:2023 Product quality model* (2.ª edición, noviembre de 2023; reemplaza a ISO/IEC 25010:2011, que a su vez reemplazó a ISO/IEC 9126-1).
- ISO/IEC. *ISO/IEC 25012:2008 Data quality model*.
- ISO/IEC. *ISO/IEC 25040 Evaluation process* (reemplaza a la serie ISO/IEC 14598).
