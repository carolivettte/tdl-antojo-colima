"""Ejecuta el pipeline completo: bronce -> plata (puerta de calidad) -> oro (con la capa geoespacial) -> pronóstico -> linaje.

Uso:
    python -m pipeline.ejecutar            # lo corre GitHub Actions después de cada captura
    python -m pipeline.ejecutar --verificar  # en integración continua: falla si la puerta baja del umbral

El umbral es el objetivo de calidad 3 de E0: al menos 98% de registros válidos.
"""

import sys

from extractores.base import logger
from extractores.config import DATA, RAIZ
from pipeline.geo import construir_geo
from pipeline.linaje import escribir_linaje
from pipeline.oro import actualizar_diccionario, construir_oro
from pipeline.plata import construir_plata
from pipeline.pronostico import construir_pronostico

UMBRAL_VALIDEZ = 0.98


def main(verificar: bool = False) -> int:
    reportes = construir_plata()
    for fuente, r in reportes.items():
        logger.info(
            f"[PUERTA] {fuente}: {r['registros_bronce']} en bronce, {r['duplicados_exactos_resueltos']} duplicados "
            f"resueltos, {r['validos_plata']} a plata, {r['cuarentena']} a cuarentena (validez {r['tasa_validez']})"
        )
        for motivo, n in r["motivos"].items():
            logger.info(f"[CUARENTENA] {fuente}: {n} por '{motivo}'")
    tablas = construir_oro()
    logger.info(f"[ORO] tablas: {tablas}")
    geo = construir_geo()
    if geo:
        logger.info(f"[GEO] tablas: {geo}")
    try:
        modelos = construir_pronostico()
        elegido = modelos[modelos["elegido"]].iloc[0]
        logger.info(f"[PRONOSTICO] elegido {elegido['modelo']} (RMSE {elegido['rmse']}, MAPE {elegido['mape']}%)")
    except Exception:
        # Si el pronóstico falla, el tablero conserva el último publicado y el error queda en el log.
        logger.exception("[PRONOSTICO] no se pudo actualizar")
    linaje = escribir_linaje(DATA, RAIZ)
    logger.info(
        f"[LINAJE] {linaje['filas_trazables']}/{linaje['filas_oro_con_linaje']} filas de oro trazables "
        f"({linaje['pct_trazable']}%), {linaje['archivos_integros']}/{linaje['archivos_bronce']} archivos de bronce íntegros"
    )
    actualizar_diccionario()
    if linaje["tablas_sin_linaje"]:
        logger.warning(f"[LINAJE] tablas sin linaje: {linaje['tablas_sin_linaje']}")
    if verificar:
        bajos = {
            f: r["tasa_validez"]
            for f, r in reportes.items()
            if r["tasa_validez"] is not None and r["tasa_validez"] < UMBRAL_VALIDEZ
        }
        if bajos:
            logger.error(f"[PUERTA] validez por debajo de {UMBRAL_VALIDEZ:.0%}: {bajos}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(verificar="--verificar" in sys.argv))
