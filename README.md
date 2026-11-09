# Observatorio Antojo Colima

Observatorio de precios de insumos y competencia para **taquerías y cafeterías del estado de Colima**. Proyecto integrador *Trusted Data Lab* (TecNM Colima): Ingeniería de Datos, Análisis Estadístico y Calidad en los Sistemas de Información.

**Pregunta central:** ¿en qué meses le conviene a una taquería o cafetería de Colima hacer promociones o ajustar precios, según lo que le cuestan sus insumos y lo que hace su competencia?

Equipo: Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas

## Fuentes

| Fuente | Qué aporta | Captura |
|---|---|---|
| SNIIM (Secretaría de Economía) | Precios de insumos en los Centros de distribución de Colima | Diaria, automática |
| DENUE (INEGI) | Negocios de comida del estado (sin datos personales) | Fotografía |
| Banco de Indicadores (INEGI) | INPC de loncherías, taquerías, restaurantes y café | Mensual (E1) |

Atribución: precios del SNIIM, Secretaría de Economía; DENUE e INPC, INEGI. Open-Meteo y NASA POWER se descartaron porque su robots.txt prohíbe el acceso.

## Estructura

```
config/        parámetros de las fuentes (fuentes.yaml)
extractores/   un módulo por fuente + extractor ético base
scripts/       orquestador de captura y verificación de robots.txt
pipeline/      bronce -> plata -> oro y puertas de calidad (E1)
data/bronce/   datos crudos por fuente y fecha, con .meta.json
data/bitacora/ ejecuciones de la captura (fiabilidad)
laboratorio/   notebooks de series, experimento y multivariado
tablero/       Streamlit (E1 en adelante)
calidad/       registros PSP de tiempo y defectos, objetivos de calidad
docs/          fichas de entrega, propuesta, relatorías y ética
tests/         pruebas automáticas
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
cp .env.example .env                    # y pega tu token en .env (no se sube a GitHub)
python -m scripts.captura historico     # serie histórica (una vez)
python -m scripts.captura diaria        # captura del día
pytest -q && ruff check .
```

En GitHub, el token vive en **Settings → Secrets and variables → Actions → `INEGI_TOKEN`** y la captura corre sola todos los días (`.github/workflows/captura.yml`).
