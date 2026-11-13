"""Respaldo de la capa bronce con restauración de prueba.

Un respaldo solo cuenta si se puede restaurar. Este script:
  1. Comprime data/bronce en respaldos/bronce_<fecha>.zip.
  2. Lo restaura en una carpeta temporal.
  3. Comprueba que cada CSV restaurado tiene la misma huella SHA-256 que guardó su .meta.json
     al momento de la captura (integridad de extremo a extremo).
  4. Anota el resultado en data/bitacora/respaldos.csv. Si algo no coincide, termina con error.

GitHub Actions lo corre después de cada captura y sube el .zip como artefacto (90 días),
así que hay una copia fuera del repositorio.

Uso:
    python -m scripts.respaldo
"""

import hashlib
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from extractores.config import DATA, RAIZ

BRONCE = DATA / "bronce"
DESTINO = RAIZ / "respaldos"
BITACORA = DATA / "bitacora" / "respaldos.csv"


def sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def crear(bronce: Path = BRONCE, destino: Path = DESTINO) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    zip_ruta = destino / f"bronce_{marca}.zip"
    with zipfile.ZipFile(zip_ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(bronce.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(bronce))
    return zip_ruta


def verificar(zip_ruta: Path) -> dict:
    """Restaura el zip en una carpeta temporal y compara cada CSV contra su metadato."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_ruta) as z:
            z.extractall(tmp)
        metas = list(Path(tmp).rglob("*.meta.json"))
        fallas = []
        for m in metas:
            meta = json.loads(m.read_text(encoding="utf-8"))
            csv = m.with_name(meta["archivo"])
            if not csv.exists():
                fallas.append(f"falta {meta['archivo']}")
            elif sha256(csv) != meta["sha256"]:
                fallas.append(f"huella distinta en {meta['archivo']}")
    return {"archivos_verificados": len(metas), "fallas": fallas}


def main() -> int:
    zip_ruta = crear()
    resultado = verificar(zip_ruta)
    estado = "ok" if not resultado["fallas"] and resultado["archivos_verificados"] > 0 else "error"
    fila = pd.DataFrame(
        [
            {
                "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "archivo": zip_ruta.name,
                "bytes": zip_ruta.stat().st_size,
                "sha256_zip": sha256(zip_ruta),
                "archivos_verificados": resultado["archivos_verificados"],
                "estado": estado,
                "detalle": "; ".join(resultado["fallas"])[:300],
            }
        ]
    )
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    fila.to_csv(BITACORA, mode="a", header=not BITACORA.exists(), index=False)
    print(f"Respaldo {zip_ruta.name}: {resultado['archivos_verificados']} archivos restaurados y verificados, estado {estado}")
    for f in resultado["fallas"]:
        print(f"  FALLA: {f}")
    return 0 if estado == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
