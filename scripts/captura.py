"""Orquestador de la captura en capa bronce.

Uso:
    python -m scripts.captura diaria      # lo corre GitHub Actions cada día
    python -m scripts.captura historico   # descarga la serie histórica (una vez)
    python -m scripts.captura denue       # vuelve a tomar la fotografía del DENUE

Cada fuente corre de forma independiente: si una falla, las demás siguen y
el fallo queda en data/bitacora/ejecuciones.csv (insumo de fiabilidad en E1).
"""
import sys
import time
from datetime import date, timedelta

from extractores import clima, denue, inegi_inpc, sniim
from extractores.base import logger
from extractores.bronce import ahora_utc, ocultar_token, registrar_ejecucion
from extractores.config import cargar_config


def correr(fuente, modo, funcion):
    """Ejecuta un extractor, mide cuánto tardó y lo anota en la bitácora."""
    inicio = ahora_utc()
    t0 = time.time()
    fila = {"fuente": fuente, "modo": modo, "registros": 0, "mensaje": ""}
    try:
        fila["registros"] = funcion()
        fila["estado"] = "ok" if fila["registros"] > 0 else "vacio"
        logger.info(f"[OK] {fuente} {modo}: {fila['registros']} registros")
    except Exception as e:
        fila["estado"] = "error"
        fila["mensaje"] = ocultar_token(f"{type(e).__name__}: {e}")[:300]
        logger.exception(f"[ERROR] {fuente} {modo}")
    fila["inicio_utc"] = inicio.isoformat()
    fila["fin_utc"] = ahora_utc().isoformat()
    fila["duracion_s"] = round(time.time() - t0, 1)
    registrar_ejecucion(fila)
    return fila["estado"] != "error"


def clima_activo():
    # Open-Meteo está desactivado: su robots.txt prohíbe el acceso (ver config/fuentes.yaml)
    return cargar_config()["clima"].get("activo", False)


def diaria():
    hoy = date.today()
    resultados = [
        # Últimos 3 días para cubrir publicaciones tardías del SNIIM (los duplicados se depuran en plata)
        correr("sniim", "diaria", lambda: sniim.ejecutar(hoy - timedelta(days=3), hoy, "sniim_diario")),
    ]
    if clima_activo():
        resultados.append(correr("clima", "diaria", clima.recientes))
    return resultados


def historico():
    hoy = date.today()
    desde = date.fromisoformat(cargar_config()["sniim"]["historico_desde"])
    resultados = [
        correr("sniim", "historico", lambda: sniim.ejecutar(desde, hoy, "sniim_historico")),
        correr("denue", "historico", denue.capturar),
        correr("inegi", "historico", inegi_inpc.capturar),
    ]
    if clima_activo():
        resultados.append(correr("clima", "historico", lambda: clima.historico(hoy - timedelta(days=6))))
    return resultados


def solo_denue():
    return [correr("denue", "fotografia", denue.capturar)]


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "diaria"
    resultados = {"diaria": diaria, "historico": historico, "denue": solo_denue}[modo]()
    # Falla el job solo si TODAS las fuentes fallaron (así la bitácora siempre se guarda)
    sys.exit(0 if any(resultados) else 1)
