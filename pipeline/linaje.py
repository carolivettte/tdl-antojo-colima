"""Linaje: cada registro de oro se puede rastrear hasta su archivo de bronce y su fecha de ingesta.

Cómo funciona la cadena:
  bronce  -> cada archivo tiene su .meta.json con capturado_utc y SHA-256 (extractores/bronce.py).
  plata   -> cada fila conserva archivo_origen y capturado_utc del archivo de bronce del que salió.
  oro     -> cada fila lleva archivos_bronce (uno o varios, separados por ";") y la fecha de ingesta
             (capturado_utc o ingesta_min / ingesta_max cuando agrega varios archivos).
  linaje.csv -> catálogo de todos los archivos de bronce que alimentan oro, con su ruta, su SHA-256
             registrado al capturar y el SHA-256 recalculado ahora (integro = coinciden).

scripts/rastrear.py usa este catálogo para ir de una fila de oro a su archivo de bronce.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

SEPARADOR = ";"
COLUMNAS_LINAJE = [
    "tabla_oro",
    "fuente",
    "archivo_bronce",
    "ruta_bronce",
    "capturado_utc",
    "registros_bronce",
    "sha256_registrado",
    "sha256_actual",
    "integro",
]


def unir_origenes(serie: pd.Series) -> str:
    """Lista ordenada y sin repetidos de archivos de bronce, separada por ';'."""
    return SEPARADOR.join(sorted({str(v) for v in serie.dropna() if str(v)}))


def separar_origenes(valor: str) -> list[str]:
    return [v for v in str(valor or "").split(SEPARADOR) if v and v != "nan"]


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 16), b""):
            h.update(bloque)
    return h.hexdigest()


def ubicar_bronce(archivo: str, carpeta_bronce: Path) -> Path | None:
    """Busca data/bronce/<fuente>/fecha=AAAA-MM-DD/<archivo>."""
    encontrados = sorted(carpeta_bronce.glob(f"*/fecha=*/{archivo}"))
    return encontrados[0] if encontrados else None


def ficha_bronce(archivo: str, carpeta_bronce: Path, raiz: Path) -> dict:
    ruta = ubicar_bronce(archivo, carpeta_bronce)
    if ruta is None:
        return {"archivo_bronce": archivo, "ruta_bronce": "", "integro": False}
    meta_ruta = ruta.with_suffix(".meta.json")
    meta = json.loads(meta_ruta.read_text(encoding="utf-8")) if meta_ruta.exists() else {}
    actual = sha256_archivo(ruta)
    registrado = meta.get("sha256", "")
    return {
        "fuente": meta.get("fuente", ruta.parent.parent.name),
        "archivo_bronce": archivo,
        "ruta_bronce": ruta.relative_to(raiz).as_posix(),
        "capturado_utc": meta.get("capturado_utc", ""),
        "registros_bronce": meta.get("registros", ""),
        "sha256_registrado": registrado,
        "sha256_actual": actual,
        "integro": bool(registrado) and registrado == actual,
    }


def catalogo_linaje(tablas: dict[str, pd.DataFrame], carpeta_bronce: Path, raiz: Path) -> pd.DataFrame:
    """Una fila por (tabla de oro, archivo de bronce) que la alimenta."""
    fichas: dict[str, dict] = {}
    filas = []
    for nombre, df in tablas.items():
        if "archivos_bronce" not in df.columns:
            continue
        archivos = sorted({a for v in df["archivos_bronce"] for a in separar_origenes(v)})
        for archivo in archivos:
            if archivo not in fichas:
                fichas[archivo] = ficha_bronce(archivo, carpeta_bronce, raiz)
            filas.append({"tabla_oro": nombre, **fichas[archivo]})
    return pd.DataFrame(filas, columns=COLUMNAS_LINAJE)


def tablas_oro(carpeta_oro: Path) -> dict[str, pd.DataFrame]:
    tablas = {r.stem: pd.read_csv(r, dtype=str) for r in sorted(carpeta_oro.glob("*.csv")) if r.stem != "linaje"}
    return resolver_derivadas(tablas)


def resolver_derivadas(tablas: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Tablas derivadas de otra tabla de oro (columna derivado_de, p. ej. el pronóstico) heredan su linaje.

    Si comparten la columna mes, cada fila hereda el linaje de ese mes; si no (meses pronosticados o tablas
    resumen), heredan la unión de todos los archivos de la tabla madre.
    """
    for nombre, df in tablas.items():
        if "archivos_bronce" in df.columns or "derivado_de" not in df.columns:
            continue
        madre = tablas.get(str(df["derivado_de"].dropna().iloc[0])) if df["derivado_de"].notna().any() else None
        if madre is None or "archivos_bronce" not in madre.columns:
            continue
        todos = unir_origenes(pd.Series([a for v in madre["archivos_bronce"] for a in separar_origenes(v)]))
        if "mes" in df.columns and "mes" in madre.columns:
            por_mes = madre.set_index("mes")["archivos_bronce"]
            df = df.assign(archivos_bronce=df["mes"].map(por_mes).fillna(todos))
        else:
            df = df.assign(archivos_bronce=todos)
        tablas[nombre] = df
    return tablas


def escribir_linaje(datos: Path, raiz: Path) -> dict:
    """Escribe data/oro/linaje.csv y devuelve un resumen para el log y para la métrica de trazabilidad."""
    tablas = tablas_oro(datos / "oro")
    catalogo = catalogo_linaje(tablas, datos / "bronce", raiz)
    catalogo.to_csv(datos / "oro" / "linaje.csv", index=False)
    con_linaje = {n: df for n, df in tablas.items() if "archivos_bronce" in df.columns}
    filas = sum(len(df) for df in con_linaje.values())
    trazables = sum(df["archivos_bronce"].map(lambda v: len(separar_origenes(v)) > 0).sum() for df in con_linaje.values())
    return {
        "tablas_con_linaje": sorted(con_linaje),
        "tablas_sin_linaje": sorted(set(tablas) - set(con_linaje)),
        "filas_oro_con_linaje": int(filas),
        "filas_trazables": int(trazables),
        "pct_trazable": round(100 * trazables / filas, 2) if filas else 0.0,
        "archivos_bronce": int(catalogo["archivo_bronce"].nunique()) if len(catalogo) else 0,
        "archivos_integros": int(catalogo.drop_duplicates("archivo_bronce")["integro"].sum()) if len(catalogo) else 0,
    }
