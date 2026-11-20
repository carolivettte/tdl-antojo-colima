# Pipeline bronce → plata → oro

```bash
python -m pipeline.ejecutar              # lo corre GitHub Actions después de cada captura
python -m pipeline.ejecutar --verificar  # en CI: falla si la validez baja de 98 % (objetivo de calidad 3)
```

| Módulo | Qué hace |
|---|---|
| `catalogos.py` | Equivalencias de nombres (SNIIM → insumo), municipios INEGI, tipos de negocio SCIAN y rangos plausibles |
| `esquemas.py` | Esquemas Pandera de la puerta de calidad: tipos, rangos, catálogos, unicidad y regla mínimo ≤ frecuente ≤ máximo |
| `plata.py` | Puerta de calidad 1: une bronce, resuelve duplicados entre capturas, valida y manda cada registro a `data/plata/` o a `data/cuarentena/` con su motivo; marca atípicos (no los borra) |
| `oro.py` | Integra las fuentes: precios mensuales, Índice de Costo del Taco, competencia por municipio y dimensiones; genera `docs/E1/diccionario_oro.md` |
| `geo.py` | E2: puerta del Marco Geoestadístico (claves, geometrías vacías o inválidas, faltantes) y uniones espaciales en UTM 13N: puntos en municipio, radio de 1 km, cuadrícula de 1 km e índice de zonas validado con Spearman |
| `linaje.py` | E2: catálogo `data/oro/linaje.csv` (cada archivo de bronce que alimenta cada tabla de oro, con su SHA-256) |
| `ejecutar.py` | Corre todo en orden y registra el resultado de la puerta en `data/bitacora/puerta_calidad.csv` |

Cada fila de oro lleva `archivos_bronce` y su fecha de ingesta; `python -m scripts.rastrear` la sigue hasta bronce.

Bronce nunca se modifica: plata y oro se reconstruyen completos desde bronce en cada ejecución.
