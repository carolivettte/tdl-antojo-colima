"""Escritura en la capa bronce con metadatos de captura y bitácora de ejecuciones.

Es la misma idea de la zona de aterrizaje (landing zone) de la sesión 13:
- Datos tal como llegaron (sin limpiar), particionados por fuente y fecha de captura.
- Huella SHA-256 de cada archivo para validar su integridad.
- Una bitácora (CSV) con cada ejecución, como ya_procesados.txt.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from extractores.config import BITACORA, BRONCE

_TOKEN_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def ocultar_token(texto: str) -> str:
    """Reemplaza cualquier token con formato UUID por *** antes de guardarlo."""
    return _TOKEN_RE.sub("***", texto or "")


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def guardar_bronce(df: pd.DataFrame, fuente: str, nombre: str, meta: dict) -> Path:
    """Guarda un DataFrame crudo en data/bronce/<fuente>/fecha=AAAA-MM-DD/."""
    marca = ahora_utc()
    carpeta = BRONCE / fuente / f"fecha={marca:%Y-%m-%d}"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}_{marca:%Y%m%dT%H%M%SZ}.csv"
    df.to_csv(ruta, index=False, encoding="utf-8")
    contenido = ruta.read_bytes()
    meta = {
        "fuente": fuente,
        "archivo": ruta.name,
        "capturado_utc": marca.isoformat(),
        "registros": int(len(df)),
        "columnas": list(map(str, df.columns)),
        "sha256": hashlib.sha256(contenido).hexdigest(),
        **{k: ocultar_token(v) if isinstance(v, str) else v for k, v in meta.items()},
    }
    ruta.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


CAMPOS_BITACORA = ["inicio_utc", "fin_utc", "fuente", "modo", "estado", "registros", "duracion_s", "mensaje"]


def registrar_ejecucion(fila: dict) -> None:
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with open(BITACORA, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_BITACORA)
        if nuevo:
            w.writeheader()
        w.writerow({k: fila.get(k, "") for k in CAMPOS_BITACORA})
