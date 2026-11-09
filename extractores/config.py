"""Lectura de configuración y rutas del proyecto."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

try:  # lee INEGI_TOKEN desde el archivo .env, igual que en las sesiones 41 y 42
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
BRONCE = DATA / "bronce"
BITACORA = DATA / "bitacora" / "ejecuciones.csv"


_CONFIG: dict | None = None


def cargar_config() -> dict:
    """Lee config/fuentes.yaml una sola vez y la guarda en memoria."""
    global _CONFIG
    if _CONFIG is None:
        with open(RAIZ / "config" / "fuentes.yaml", encoding="utf-8") as f:
            _CONFIG = yaml.safe_load(f)
    return _CONFIG


def token_inegi() -> str:
    """El token vive en el secreto INEGI_TOKEN de GitHub o, en tu compu, en el archivo .env.

    Nunca se escribe en archivos del repositorio.
    """
    token = os.environ.get("INEGI_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Falta la variable de entorno INEGI_TOKEN (secreto de GitHub).")
    return token
