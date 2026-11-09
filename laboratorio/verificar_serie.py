"""Verifica que la serie histórica del SNIIM en bronce tenga al menos 36 periodos.

Uso: python -m laboratorio.verificar_serie
Lee todos los CSV de data/bronce/sniim/, cuenta meses con precio por producto
y guarda el resumen en docs/E0/serie_historica.md (evidencia para la entrega).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
MINIMO = 36


def cargar() -> pd.DataFrame:
    archivos = sorted((RAIZ / "data" / "bronce" / "sniim").glob("fecha=*/*.csv"))
    if not archivos:
        sys.exit("No hay archivos en data/bronce/sniim/. Corre primero la captura en modo historico.")
    df = pd.concat((pd.read_csv(a, dtype=str) for a in archivos), ignore_index=True)
    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    df["precio"] = pd.to_numeric(df["precio_frec"].str.replace(",", ""), errors="coerce")
    return df


def resumen(df: pd.DataFrame) -> pd.DataFrame:
    validos = df.dropna(subset=["fecha_dt", "precio"])
    validos = validos[validos["precio"] > 0].drop_duplicates(["producto", "presentacion", "origen", "fecha"])
    r = validos.groupby("producto").agg(
        desde=("fecha_dt", "min"),
        hasta=("fecha_dt", "max"),
        dias_con_precio=("fecha_dt", "nunique"),
        meses_con_precio=("fecha_dt", lambda s: s.dt.to_period("M").nunique()),
    )
    r["cumple_36"] = r["meses_con_precio"] >= MINIMO
    return r.sort_values("meses_con_precio", ascending=False)


if __name__ == "__main__":
    df = cargar()
    r = resumen(df)
    invalidos = len(df) - len(df.dropna(subset=["fecha_dt", "precio"]))
    texto = [
        "# Serie histórica inicial (SNIIM, Centros de Distribución de Colima)",
        "",
        f"Registros crudos leídos: **{len(df):,}** · con fecha o precio no válidos: **{invalidos:,}** "
        f"({invalidos / max(len(df), 1):.1%})",
        "",
        "```",
        r.to_string(),
        "```",
        "",
        f"Productos que cumplen ≥ {MINIMO} meses: **{int(r['cumple_36'].sum())} de {len(r)}**",
    ]
    salida = RAIZ / "docs" / "E0" / "serie_historica.md"
    salida.write_text("\n".join(texto) + "\n", encoding="utf-8")
    print("\n".join(texto))
