# Entrega E0 · Observatorio Antojo Colima

Equipo: Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas · Etiqueta: `e0` · Tablero: _(se publica en E1)_ · Repositorio: https://github.com/carolivettte/tdl-antojo-colima

## Resumen en tres líneas

1. Observatorio de precios de insumos y competencia para taquerías y cafeterías del estado de Colima.
2. Captura automática diaria (GitHub Actions) del SNIIM, más una fotografía del DENUE (7,397 negocios sin datos personales), en capa bronce con metadatos y bitácora.
3. Serie histórica del SNIIM desde enero de 2020: 5,125 registros y de 67 a 80 meses por insumo (se piden 36), base del pronóstico de E1.

## Ingeniería de Datos

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Plan de recopilación (estructura, formato, frecuencia, acceso) | [propuesta.md §4.1](propuesta.md#41-fuentes) | SNIIM y DENUE activas, INPC para E1; Open-Meteo y NASA POWER descartadas por su robots.txt |
| Análisis ético y legal (robots.txt y términos) | [propuesta.md §4.2](propuesta.md#42-análisis-ético-y-legal) · [docs/etica/robots/](../etica/robots/) | Copia fechada de cada robots.txt; el DENUE se guarda sin razón social, teléfono, correo ni sitio web |
| Extractor ético | [extractores/base.py](../../extractores/base.py) | robots.txt, User-Agent con contacto del equipo, pausa ≥ 1.5 s, Retry-After en 429 y espera exponencial |
| Captura programada con GitHub Actions | [.github/workflows/captura.yml](../../.github/workflows/captura.yml) · [pestaña Actions](https://github.com/carolivettte/tdl-antojo-colima/actions) | Diaria a las 10:15 (hora de Colima); modos manuales `historico` y `denue` |
| Datos en bronce con metadatos de captura | [data/bronce/](../../data/bronce/) | Cada CSV tiene su `.meta.json` (URL sin token, fecha UTC, registros, SHA-256) |
| Dos fuentes funcionando | [extractores/sniim.py](../../extractores/sniim.py) · [extractores/denue.py](../../extractores/denue.py) | SNIIM (scraping, programado) y DENUE (API, 7,397 negocios) |

## Análisis Estadístico

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Pregunta central del observatorio | [propuesta.md §1](propuesta.md#1-ficha-del-observatorio) · [entrevista §2](propuesta.md#2-entrevista-de-campo) | Cliente con motivo para pagar respaldado por la entrevista |
| Tres preguntas analíticas (E1, E2, E3) | [propuesta.md §3](propuesta.md#3-las-tres-preguntas-analíticas) | E1 pronóstico, E2 factorial 2³, E3 PCA y MANOVA |
| Serie histórica identificada y descargada (≥ 36 periodos) | [serie_historica.md](serie_historica.md) · [data/bronce/sniim/](../../data/bronce/sniim/) | 8 de 8 insumos con 36 o más meses |

## Calidad en los Sistemas de Información

| Criterio de la rúbrica | Evidencia (enlace) | Nota del equipo |
|---|---|---|
| Registro de tiempo individual | [tiempo-carol.csv](../../calidad/tiempo-carol.csv) · [tiempo-avlix.csv](../../calidad/tiempo-avlix.csv) | Un registro por integrante |
| Registro de defectos individual | [defectos-carol.csv](../../calidad/defectos-carol.csv) · [defectos-avlix.csv](../../calidad/defectos-avlix.csv) | Tipos PSP, fase en que se introdujo y en que se eliminó |
| Bitácora de ejecuciones de la captura | [data/bitacora/ejecuciones.csv](../../data/bitacora/ejecuciones.csv) | Registra éxitos y fallas reales (ej. DENUE sin secreto, defecto 11); base de la fiabilidad en E1 |
| Tres objetivos de calidad medibles | [calidad/objetivos.md](../../calidad/objetivos.md) | |
| Pruebas automáticas e integración continua | [tests/](../../tests/) · [.github/workflows/ci.yml](../../.github/workflows/ci.yml) | ruff, 10 pruebas de pytest y gitleaks en cada push y PR |

## Relatoría de etapa

No aplica en E0 (inicia en E1: `docs/relatoria-E1.md`).

## Issues de la entrega anterior

No aplica (primera entrega).

## Uso de IA generativa

- Claude (Anthropic): apoyo en la selección del sector del observatorio, en el desarrollo y la depuración de los extractores (SNIIM y DENUE), del flujo de GitHub Actions y de las pruebas automáticas, y en la redacción de borradores de la propuesta y de la ficha de entrega.
- ChatGPT (OpenAI): apoyo en la verificación de la serie histórica y en la redacción de las respuestas de la entrevista a partir de las notas del equipo.

Las decisiones del proyecto (sector, fuentes, preguntas analíticas, descarte de fuentes por robots.txt) fueron del equipo. Todo el contenido fue revisado por ambos integrantes y cada uno puede explicar su parte y la del compañero.