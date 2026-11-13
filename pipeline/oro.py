"""Capa oro: el modelo de datos integrado que usan el pronóstico y el tablero.

Integra fuentes heterogéneas resolviendo sus conflictos:
  - Fechas: el SNIIM usa dd/mm/aaaa diario; el INPC usa aaaa/mm mensual -> todo a mes "aaaa-mm".
  - Unidades: $/kg (SNIIM) e índice (INPC) -> se guardan en columnas separadas, nunca se mezclan.
  - Nombres: "Limón c/semilla # 5 - Primera" -> "limon" (catálogo en pipeline/catalogos.py).
  - Geografía: mercado del SNIIM y municipio del DENUE -> clave de municipio del INEGI (06002...).

Tablas:
  dim_insumo.csv            jerarquía insumo -> tipo -> canasta
  dim_municipio.csv         jerarquía municipio -> estado, con lo que cada fuente aporta
  precios_mensuales.csv     precio mensual por insumo (reducción diario -> mensual)
  indice_costo_taco.csv     índice de la canasta taquera (base promedio 2021 = 100)
  competencia_municipio.csv negocios por municipio y tipo (DENUE)
"""

from pathlib import Path

import pandas as pd

from extractores.config import DATA, RAIZ
from pipeline.catalogos import MUNICIPIOS, PRODUCTOS_SNIIM

ORO = DATA / "oro"
DICCIONARIO = RAIZ / "docs" / "E1" / "diccionario_oro.md"
ANIO_BASE = 2021


def dim_insumo() -> pd.DataFrame:
    filas = [{"insumo": i, "tipo": t, "canasta": c, "producto_sniim": p} for p, (i, t, c) in PRODUCTOS_SNIIM.items()]
    return pd.DataFrame(filas).sort_values(["canasta", "tipo", "insumo"]).reset_index(drop=True)


def precios_mensuales(plata: pd.DataFrame) -> pd.DataFrame:
    """Agrega de diario a mensual con la mediana (robusta a atípicos) y rellena meses sin publicación.

    Los meses faltantes se rellenan por interpolación lineal en el tiempo y quedan marcados
    (imputado=True). No se rellena antes del primer ni después del último dato observado.
    """
    df = plata.copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["mes"] = df["fecha"].dt.to_period("M")
    df["atipico"] = df["atipico"].astype(str).str.lower().eq("true")
    agg = (
        df.groupby(["insumo", "mes"])
        .agg(
            precio_mediana=("precio_frec", "median"),
            precio_promedio=("precio_frec", "mean"),
            precio_min=("precio_min", "min"),
            precio_max=("precio_max", "max"),
            n_registros=("precio_frec", "size"),
            n_atipicos=("atipico", "sum"),
        )
        .reset_index()
    )
    partes = []
    for insumo, g in agg.groupby("insumo"):
        meses = pd.period_range(g["mes"].min(), g["mes"].max(), freq="M")
        g = g.set_index("mes").reindex(meses)
        g.index.name = "mes"
        g["insumo"] = insumo
        g["imputado"] = g["precio_mediana"].isna()
        g["n_registros"] = g["n_registros"].fillna(0).astype(int)
        g["n_atipicos"] = g["n_atipicos"].fillna(0).astype(int)
        serie = g["precio_mediana"].copy()
        serie.index = serie.index.to_timestamp()
        g["precio_mediana"] = serie.interpolate(method="time").values
        g["metodo"] = g["imputado"].map({True: "interpolacion_lineal", False: "observado"})
        partes.append(g.reset_index())
    salida = pd.concat(partes, ignore_index=True)
    salida = salida.merge(dim_insumo()[["insumo", "tipo", "canasta"]], on="insumo", how="left")
    salida["mes"] = salida["mes"].astype(str)
    cols = [
        "mes",
        "insumo",
        "tipo",
        "canasta",
        "precio_mediana",
        "precio_promedio",
        "precio_min",
        "precio_max",
        "n_registros",
        "n_atipicos",
        "imputado",
        "metodo",
    ]
    return salida[cols].sort_values(["insumo", "mes"]).round(2).reset_index(drop=True)


def indice_costo_taco(mensual: pd.DataFrame, anio_base: int = ANIO_BASE) -> pd.DataFrame:
    """Índice de Laspeyres simplificado con pesos iguales: 100 = costo promedio de la canasta en el año base.

    Solo se calcula en meses donde están los 8 insumos (observados o imputados).
    """
    tabla = mensual.pivot(index="mes", columns="insumo", values="precio_mediana")
    tabla = tabla.dropna()
    base = tabla[tabla.index.str.startswith(str(anio_base))].mean()
    relativos = tabla.div(base) * 100
    indice = relativos.mean(axis=1)
    imputados = mensual[mensual["imputado"]].groupby("mes")["insumo"].apply(lambda s: ",".join(sorted(s)))
    salida = pd.DataFrame({"mes": indice.index, "indice": indice.values})
    salida["variacion_mensual_pct"] = salida["indice"].pct_change() * 100
    salida["variacion_anual_pct"] = salida["indice"].pct_change(12) * 100
    salida["costo_canasta_kg"] = tabla.sum(axis=1).values
    salida["insumos_imputados"] = salida["mes"].map(imputados).astype(object).fillna("")
    return salida.round(2)


def competencia_municipio(denue: pd.DataFrame) -> pd.DataFrame:
    df = denue.copy()
    df["es_micro"] = df["tamano"].eq("micro")
    df["es_semifijo"] = df["establecimiento"].eq("Semifijo")
    salida = (
        df.groupby(["municipio_clave", "municipio", "tipo_negocio"])
        .agg(negocios=("clee", "size"), micro=("es_micro", "sum"), semifijos=("es_semifijo", "sum"))
        .reset_index()
    )
    salida["pct_micro"] = (salida["micro"] / salida["negocios"] * 100).round(1)
    total = salida.groupby("municipio_clave")["negocios"].transform("sum")
    salida["pct_del_municipio"] = (salida["negocios"] / total * 100).round(1)
    return salida.sort_values(["municipio_clave", "negocios"], ascending=[True, False]).reset_index(drop=True)


def dim_municipio(denue: pd.DataFrame, plata_sniim: pd.DataFrame) -> pd.DataFrame:
    negocios = denue.groupby("municipio_clave").size() if len(denue) else pd.Series(dtype=int)
    con_precios = set(plata_sniim["municipio_clave"].astype(str)) if len(plata_sniim) else set()
    filas = []
    for clave3, nombre in MUNICIPIOS.items():
        clave = "06" + clave3
        filas.append(
            {
                "municipio_clave": clave,
                "municipio": nombre,
                "estado": "Colima",
                "negocios_denue": int(negocios.get(clave, 0)),
                "mercado_sniim": clave in con_precios,
            }
        )
    return pd.DataFrame(filas)


def inpc_mensual(carpeta_bronce: Path) -> pd.DataFrame:
    """Integra el INPC si ya hay series en bronce (se activa en cuanto se configuren en fuentes.yaml)."""
    archivos = sorted((carpeta_bronce / "inegi").glob("fecha=*/*.csv"))
    if not archivos:
        return pd.DataFrame()
    df = pd.read_csv(archivos[-1], dtype=str)
    df["mes"] = df["TIME_PERIOD"].str.replace("/", "-", regex=False).str[:7]
    df["valor"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    return df.pivot_table(index="mes", columns="serie", values="valor").reset_index()


DESCRIPCIONES = {
    "dim_insumo": {
        "_tabla": "Jerarquía conceptual de insumos: insumo -> tipo -> canasta.",
        "insumo": "Nombre normalizado del insumo en el observatorio.",
        "tipo": "Subcategoría: fruta, verdura o chile.",
        "canasta": "Categoría: canasta del tipo de negocio al que pertenece (taquera).",
        "producto_sniim": "Nombre original del producto en el SNIIM (resolución de nombres).",
    },
    "dim_municipio": {
        "_tabla": "Jerarquía geográfica municipio -> estado con lo que aporta cada fuente.",
        "municipio_clave": "Clave INEGI de 5 dígitos (estado 06 + municipio).",
        "municipio": "Nombre oficial del municipio.",
        "estado": "Entidad federativa.",
        "negocios_denue": "Negocios de preparación de alimentos registrados en el DENUE.",
        "mercado_sniim": "True si el SNIIM reporta precios de un mercado en ese municipio.",
    },
    "precios_mensuales": {
        "_tabla": "Precio mensual por insumo en los Centros de distribución de Colima (reducción de diario a mensual).",
        "mes": "Mes en formato aaaa-mm.",
        "insumo": "Insumo normalizado (ver dim_insumo).",
        "tipo": "Subcategoría del insumo.",
        "canasta": "Categoría del insumo.",
        "precio_mediana": "Mediana mensual del precio frecuente (MXN/kg); en meses imputados, interpolación lineal.",
        "precio_promedio": "Promedio mensual del precio frecuente (MXN/kg); vacío en meses imputados.",
        "precio_min": "Mínimo de los precios mínimos del mes (MXN/kg).",
        "precio_max": "Máximo de los precios máximos del mes (MXN/kg).",
        "n_registros": "Registros diarios válidos usados en el mes.",
        "n_atipicos": "Registros del mes marcados como atípicos (z robusto > 3.5).",
        "imputado": "True si el mes no tuvo publicación y se rellenó.",
        "metodo": "observado o interpolacion_lineal.",
    },
    "indice_costo_taco": {
        "_tabla": "Índice de Costo del Taco: canasta de 8 insumos con pesos iguales, base promedio 2021 = 100.",
        "mes": "Mes en formato aaaa-mm.",
        "indice": "Valor del índice (100 = costo promedio de 2021).",
        "variacion_mensual_pct": "Cambio porcentual contra el mes anterior.",
        "variacion_anual_pct": "Cambio porcentual contra el mismo mes del año anterior.",
        "costo_canasta_kg": "Suma de la mediana mensual de los 8 insumos (1 kg de cada uno, MXN).",
        "insumos_imputados": "Insumos cuyo precio de ese mes fue imputado.",
    },
    "competencia_municipio": {
        "_tabla": "Negocios de comida por municipio y tipo de negocio (DENUE, sin datos personales).",
        "municipio_clave": "Clave INEGI del municipio.",
        "municipio": "Nombre del municipio.",
        "tipo_negocio": "Tipo de negocio derivado de la clase SCIAN.",
        "negocios": "Número de establecimientos.",
        "micro": "Establecimientos con 0 a 10 personas.",
        "semifijos": "Establecimientos semifijos (puestos).",
        "pct_micro": "Porcentaje de micronegocios del tipo en el municipio.",
        "pct_del_municipio": "Porcentaje que representa el tipo dentro del municipio.",
    },
}


CONTRATO_PRONOSTICO = [
    "## Contrato del pronóstico (lo escribe el cuaderno de pronóstico, lo lee el tablero)",
    "",
    "`pronostico.csv`: serie objetivo `indice_costo_taco.indice`.",
    "",
    "| Columna | Tipo | Descripción |",
    "|---|---|---|",
    "| `mes` | texto aaaa-mm | Mes. |",
    "| `valor` | float | Índice observado o pronosticado. |",
    "| `tipo` | texto | `observado` o `pronostico`. |",
    "| `li_95` | float | Límite inferior del intervalo de 95% (vacío en observados). |",
    "| `ls_95` | float | Límite superior del intervalo de 95% (vacío en observados). |",
    "| `modelo` | texto | Modelo elegido (SES, Holt, Holt-Winters o ARIMA). |",
    "",
    "`comparacion_modelos.csv`: una fila por modelo con `modelo`, `mae`, `rmse`, `mape` "
    "(sobre el conjunto de prueba) y `elegido` (True en el de menor error).",
    "",
]


def escribir_diccionario(tablas: dict[str, pd.DataFrame], ruta: Path = DICCIONARIO) -> None:
    lineas = [
        "# Diccionario de datos · capa oro",
        "",
        "Generado automáticamente por `pipeline/oro.py` en cada ejecución del pipeline.",
        "",
    ]
    for nombre, df in tablas.items():
        desc = DESCRIPCIONES.get(nombre, {})
        lineas += [f"## `{nombre}.csv`", "", desc.get("_tabla", ""), "", f"Filas: **{len(df):,}**", ""]
        lineas += ["| Columna | Tipo | Descripción | Ejemplo |", "|---|---|---|---|"]
        for c in df.columns:
            ejemplo = df[c].dropna().iloc[0] if df[c].notna().any() else ""
            lineas.append(f"| `{c}` | {df[c].dtype} | {desc.get(c, '')} | {ejemplo} |")
        lineas.append("")
    lineas += CONTRATO_PRONOSTICO
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def construir_oro(datos: Path = DATA, diccionario: Path = DICCIONARIO) -> dict[str, int]:
    plata_sniim = pd.read_csv(datos / "plata" / "sniim_precios.csv", dtype={"municipio_clave": str})
    ruta_denue = datos / "plata" / "denue_negocios.csv"
    denue = pd.read_csv(ruta_denue, dtype={"municipio_clave": str, "cp": str}) if ruta_denue.exists() else pd.DataFrame()

    mensual = precios_mensuales(plata_sniim)
    tablas = {
        "dim_insumo": dim_insumo(),
        "dim_municipio": dim_municipio(denue, plata_sniim),
        "precios_mensuales": mensual,
        "indice_costo_taco": indice_costo_taco(mensual),
    }
    if len(denue):
        tablas["competencia_municipio"] = competencia_municipio(denue)
    inpc = inpc_mensual(datos / "bronce")
    if len(inpc):
        tablas["indice_costo_taco"] = tablas["indice_costo_taco"].merge(inpc, on="mes", how="left")

    (datos / "oro").mkdir(parents=True, exist_ok=True)
    for nombre, df in tablas.items():
        df.to_csv(datos / "oro" / f"{nombre}.csv", index=False)
    escribir_diccionario(tablas, diccionario)
    return {k: len(v) for k, v in tablas.items()}
