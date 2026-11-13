"""Ejecuta el pipeline completo: bronce -> plata (puerta de calidad) -> oro.

Uso:
    python -m pipeline.ejecutar            # lo corre GitHub Actions después de cada captura
    python -m pipeline.ejecutar --verificar  # en integración continua: falla si la puerta baja del umbral

El umbral es el objetivo de calidad 3 de E0: al menos 98% de registros válidos.
"""

import sys

from extractores.base import logger
from pipeline.oro import construir_oro
from pipeline.plata import construir_plata

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
