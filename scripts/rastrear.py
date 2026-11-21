"""Rastrea una fila de oro hasta su archivo de bronce y su fecha de ingesta, y verifica el SHA-256.

Uso:
    python -m scripts.rastrear precios_mensuales --donde insumo=limon mes=2026-10
    python -m scripts.rastrear geo_puntos --donde clee=06007722514005991000000000U1
    python -m scripts.rastrear indice_costo_taco --fila 0
    python -m scripts.rastrear --verificar      # todos los archivos de linaje.csv íntegros (sale con 1 si no)

Para cada fila muestra: los archivos de bronce de los que sale, su ruta, la fecha de ingesta, si el
SHA-256 actual coincide con el registrado al capturar y, cuando se puede, los registros crudos de bronce
que la originan (por CLEE en el DENUE, o por producto y mes en el SNIIM).
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from extractores.config import DATA, RAIZ
from pipeline.catalogos import PRODUCTOS_SNIIM
from pipeline.esquemas import COLUMNAS_PERSONALES
from pipeline.linaje import ficha_bronce, separar_origenes, tablas_oro


def registros_crudos(archivo: str, fila: pd.Series) -> pd.DataFrame:
    ficha = ficha_bronce(archivo, DATA / "bronce", RAIZ)
    if not ficha["ruta_bronce"] or not ficha["ruta_bronce"].endswith(".csv"):
        return pd.DataFrame()
    crudo = pd.read_csv(RAIZ / ficha["ruta_bronce"], dtype=str)
    # Al mostrar en pantalla no se exhiben nombres ni domicilios, aunque el bronce del DENUE los traiga.
    crudo = crudo.drop(columns=[c for c in crudo.columns if c.lower() in COLUMNAS_PERSONALES])
    if "clee" in fila and "CLEE" in crudo.columns:
        return crudo[crudo["CLEE"] == fila["clee"]]
    if {"insumo", "mes"} <= set(fila.index) and "producto" in crudo.columns:
        productos = [p for p, (i, _, _) in PRODUCTOS_SNIIM.items() if i == fila["insumo"]]
        mes = pd.to_datetime(crudo["fecha"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m")
        return crudo[crudo["producto"].isin(productos) & (mes == fila["mes"])]
    return pd.DataFrame()


def rastrear(tabla: str, fila: pd.Series) -> bool:
    print(f"\n=== {tabla} ===")
    visibles = [c for c in fila.index if c != "archivos_bronce"]
    print(fila[visibles].to_string())
    archivos = separar_origenes(fila.get("archivos_bronce", ""))
    if not archivos:
        print("SIN LINAJE: la fila no apunta a ningún archivo de bronce")
        return False
    todo_ok = True
    for archivo in archivos:
        ficha = ficha_bronce(archivo, DATA / "bronce", RAIZ)
        estado = "ÍNTEGRO" if ficha["integro"] else "NO COINCIDE / NO ENCONTRADO"
        todo_ok &= bool(ficha["integro"])
        print(f"\n  -> {ficha.get('ruta_bronce') or archivo}")
        print(f"     fuente: {ficha.get('fuente', '')} | ingesta: {ficha.get('capturado_utc', '')}")
        print(f"     sha256: {ficha.get('sha256_actual', '')[:16]}...  [{estado}]")
        crudos = registros_crudos(archivo, fila)
        if len(crudos):
            print(f"     registros crudos que la originan: {len(crudos)}")
            print("     " + crudos.head(3).to_string(index=False).replace("\n", "\n     "))
    return todo_ok


def verificar_todo() -> int:
    ruta = DATA / "oro" / "linaje.csv"
    if not ruta.exists():
        print("No existe data/oro/linaje.csv: corre primero python -m pipeline.ejecutar")
        return 1
    lin = pd.read_csv(ruta).drop_duplicates("archivo_bronce")
    malos = lin[~lin["integro"].astype(bool)]
    print(f"{len(lin) - len(malos)}/{len(lin)} archivos de bronce íntegros")
    if len(malos):
        print(malos[["archivo_bronce", "ruta_bronce"]].to_string(index=False))
    return 1 if len(malos) else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tabla", nargs="?", help="tabla de oro (sin .csv)")
    ap.add_argument("--donde", nargs="*", default=[], help="filtros columna=valor")
    ap.add_argument("--fila", type=int, help="número de fila (desde 0)")
    ap.add_argument("--verificar", action="store_true", help="verifica el SHA-256 de todo linaje.csv")
    a = ap.parse_args(argv)
    if a.verificar:
        return verificar_todo()
    if not a.tabla:
        ap.print_help()
        return 1
    tablas = tablas_oro(DATA / "oro")
    if a.tabla not in tablas:
        print(f"Tabla desconocida. Disponibles: {', '.join(sorted(tablas))}")
        return 1
    df = tablas[a.tabla]
    for filtro in a.donde:
        col, _, valor = filtro.partition("=")
        df = df[df[col].astype(str) == valor]
    if a.fila is not None:
        df = df.iloc[[a.fila]]
    if df.empty:
        print("Ninguna fila coincide con el filtro.")
        return 1
    ok = all(rastrear(a.tabla, f) for _, f in df.head(5).iterrows())
    if len(df) > 5:
        print(f"\n({len(df) - 5} filas más coinciden; afina el filtro con --donde)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
