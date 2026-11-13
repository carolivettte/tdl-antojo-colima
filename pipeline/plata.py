"""Capa plata: datos tipados, sin duplicados y validados por la puerta de calidad.

Flujo por fuente:
  1. Leer todos los archivos de bronce (bronce nunca se modifica).
  2. Convertir tipos; lo que no se puede convertir va a cuarentena con su motivo.
  3. Resolver duplicados entre capturas (la captura diaria pide 3 días y se encima).
  4. Validar con Pandera (esquema, tipos, rangos, unicidad, reglas de negocio).
  5. Guardar válidos en data/plata/ y rechazados en data/cuarentena/ con motivo.
Nada se borra en silencio: cada registro que entra sale en plata o en cuarentena.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa

from extractores.config import DATA
from pipeline.catalogos import MERCADOS_SNIIM, MUNICIPIOS, PRODUCTOS_SNIIM, TAMANO, TIPO_NEGOCIO
from pipeline.esquemas import ESQUEMA_DENUE, ESQUEMA_SNIIM

BRONCE = DATA / "bronce"
PLATA = DATA / "plata"
CUARENTENA = DATA / "cuarentena"
BITACORA_PUERTA = DATA / "bitacora" / "puerta_calidad.csv"
COLUMNAS_CUARENTENA_SNIIM = [
    "motivo", "fecha", "producto_sniim", "insumo", "presentacion", "origen", "mercado",
    "precio_min", "precio_max", "precio_frec", "obs", "archivo_origen", "capturado_utc",
]
_MARCA = re.compile(r"_(\d{8}T\d{6}Z)\.csv$")


def leer_bronce(fuente: str, carpeta: Path = BRONCE) -> pd.DataFrame:
    """Une todos los CSV de bronce de una fuente, con el archivo y la hora de captura."""
    partes = []
    for ruta in sorted((carpeta / fuente).glob("fecha=*/*.csv")):
        df = pd.read_csv(ruta, dtype=str, keep_default_na=False, na_values=[""])
        marca = _MARCA.search(ruta.name)
        df["archivo_origen"] = ruta.name
        df["capturado_utc"] = pd.to_datetime(marca.group(1), format="%Y%m%dT%H%M%SZ", utc=True) if marca else pd.NaT
        partes.append(df)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def _rechazos(df: pd.DataFrame, mascara: pd.Series, motivo: str) -> pd.DataFrame:
    r = df[mascara].copy()
    r["motivo"] = motivo
    return r


def _numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")


def validar(df: pd.DataFrame, esquema: pa.DataFrameSchema) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica el esquema completo (lazy) y separa válidos de rechazados con todos sus motivos."""
    try:
        esquema.validate(df, lazy=True)
        return df, df.iloc[0:0].assign(motivo=pd.Series(dtype=str))
    except pa.errors.SchemaErrors as err:
        fallas = err.failure_cases.dropna(subset=["index"])
        motivos = fallas.groupby("index")["check"].apply(lambda s: "; ".join(sorted(set(map(str, s)))))
        malos = df.index.isin(motivos.index)
        rechazados = df[malos].copy()
        rechazados["motivo"] = motivos.reindex(rechazados.index).values
        return df[~malos], rechazados


# ---------------------------------------------------------------- SNIIM

def preparar_sniim(crudo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tipos e integración de nombres; devuelve (preparados, rechazados al convertir)."""
    df = crudo.copy()
    rechazos = []

    df["fecha_dt"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    for c in ("precio_min", "precio_max", "precio_frec"):
        df[c + "_num"] = _numero(df[c])

    sin_fecha = df["fecha_dt"].isna()
    rechazos.append(_rechazos(df, sin_fecha, "fecha no tiene el formato dd/mm/aaaa"))
    sin_precio = ~sin_fecha & df[["precio_min_num", "precio_max_num", "precio_frec_num"]].isna().any(axis=1)
    rechazos.append(_rechazos(df, sin_precio, "precio faltante o no numérico"))
    sin_producto = ~sin_fecha & ~sin_precio & ~df["producto"].isin(PRODUCTOS_SNIIM)
    rechazos.append(_rechazos(df, sin_producto, "producto del SNIIM sin equivalencia en el catálogo"))
    sin_mercado = ~sin_fecha & ~sin_precio & ~sin_producto & ~df["destino"].isin(MERCADOS_SNIIM)
    rechazos.append(_rechazos(df, sin_mercado, "mercado destino distinto de Colima"))

    ok = df[~(sin_fecha | sin_precio | sin_producto | sin_mercado)].copy()
    jer = ok["producto"].map(PRODUCTOS_SNIIM)
    salida = pd.DataFrame(
        {
            "fecha": ok["fecha_dt"],
            "insumo": jer.str[0],
            "tipo": jer.str[1],
            "canasta": jer.str[2],
            "producto_sniim": ok["producto"],
            "presentacion": ok["presentacion"],
            "unidad": "kg",
            "origen": ok["origen"],
            "mercado": ok["destino"].map(lambda d: MERCADOS_SNIIM[d][0]),
            "municipio_clave": ok["destino"].map(lambda d: MERCADOS_SNIIM[d][1]),
            "precio_min": ok["precio_min_num"],
            "precio_max": ok["precio_max_num"],
            "precio_frec": ok["precio_frec_num"],
            "obs": ok["obs"],
            "archivo_origen": ok["archivo_origen"],
            "capturado_utc": ok["capturado_utc"],
        },
        index=ok.index,
    )
    rech = pd.concat(rechazos)
    return salida, rech


def resolver_duplicados(df: pd.DataFrame, llave: list[str], valores: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    """Resolución de entidades entre capturas.

    - Mismo registro en varias capturas (mismos valores): se conserva uno (el más reciente).
    - Misma llave con valores distintos (conflicto): se conserva la captura más reciente
      y las anteriores van a cuarentena con su motivo.
    Devuelve (únicos, conflictos, cantidad de duplicados exactos eliminados).
    """
    orden = df.sort_values("capturado_utc")
    exactos = orden.duplicated(llave + valores, keep="last")
    n_exactos = int(exactos.sum())
    orden = orden[~exactos]
    conflicto = orden.duplicated(llave, keep="last")
    conflictos = orden[conflicto].copy()
    conflictos["motivo"] = "conflicto entre capturas: misma llave con valores distintos; se conservó la captura más reciente"
    return orden[~conflicto], conflictos, n_exactos


def marcar_atipicos(df: pd.DataFrame, ventana: str = "120D", umbral: float = 3.5) -> pd.DataFrame:
    """Marca (no elimina) atípicos con puntaje z robusto contra la mediana móvil del insumo.

    z = 0.6745 * (x - mediana) / MAD, sobre los 120 días anteriores. |z| > 3.5 se marca.
    Se usa la mediana móvil porque los precios tienen tendencia (inflación): un precio
    alto en 2026 no es atípico contra 2020.
    Si el precio no se movió en la ventana (MAD = 0) se usa la desviación absoluta media
    (Iglewicz y Hoaglin): z = (x - mediana) / (1.253314 * MeanAD).
    """
    partes = []
    for _, g in df.sort_values("fecha").groupby("insumo", sort=False):
        s = g.set_index("fecha")["precio_frec"]
        med = s.rolling(ventana, min_periods=5).median()
        desv = (s - med).abs()
        mad = desv.rolling(ventana, min_periods=5).median()
        meanad = desv.rolling(ventana, min_periods=5).mean()
        z_mad = 0.6745 * (s - med) / mad.replace(0, np.nan)
        z_mean = (s - med) / (1.253314 * meanad.replace(0, np.nan))
        z = z_mad.where(mad > 0, z_mean)
        g = g.copy()
        g["z_robusto"] = z.round(2).values
        g["atipico"] = (z.abs() > umbral).fillna(False).values
        partes.append(g)
    return pd.concat(partes).sort_values(["insumo", "fecha"])


def plata_sniim(carpeta_bronce: Path = BRONCE) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    crudo = leer_bronce("sniim", carpeta_bronce)
    preparados, rech_tipos = preparar_sniim(crudo)
    unicos, conflictos, n_exactos = resolver_duplicados(
        preparados, ["insumo", "fecha", "presentacion", "origen"], ["precio_min", "precio_max", "precio_frec"]
    )
    validos, rech_puerta = validar(unicos, ESQUEMA_SNIIM)
    validos = marcar_atipicos(validos)
    crudos = rech_tipos.rename(columns={"producto": "producto_sniim", "destino": "mercado"})
    cuarentena = pd.concat([_a_texto(crudos), _a_texto(conflictos), _a_texto(rech_puerta)], ignore_index=True)
    cuarentena = cuarentena.reindex(columns=COLUMNAS_CUARENTENA_SNIIM)
    reporte = _reporte("sniim", len(crudo), n_exactos, len(validos), cuarentena)
    reporte["atipicos_marcados"] = int(validos["atipico"].sum())
    return validos, cuarentena, reporte


# ---------------------------------------------------------------- DENUE

def preparar_denue(crudo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = crudo.copy()
    ubic = df["Ubicacion"].fillna("").str.split(",")
    mun_texto = ubic.str[1].str.strip()
    mun_clave = df["AreaGeo"].fillna("").str[2:5]
    mun_por_clave = mun_clave.map(MUNICIPIOS)
    inconsistente = mun_por_clave.notna() & (mun_texto != mun_por_clave)
    rechazos = [_rechazos(df, inconsistente, "municipio del texto no coincide con la clave geográfica (AreaGeo)")]
    ok = df[~inconsistente]
    salida = pd.DataFrame(
        {
            "clee": ok["CLEE"],
            "nombre": ok["Nombre"].str.strip(),
            "clase_scian": ok["CLASE_ACTIVIDAD_ID"],
            "clase_actividad": ok["Clase_actividad"],
            "tipo_negocio": ok["CLASE_ACTIVIDAD_ID"].map(TIPO_NEGOCIO),
            "estrato": ok["Estrato"],
            "tamano": ok["Estrato"].map(TAMANO),
            "establecimiento": ok["Tipo"],
            "colonia": ok["Colonia"].str.strip().str.title(),
            "cp": ok["CP"],
            "localidad": ubic[~inconsistente].str[0].str.strip().str.title(),
            "municipio": mun_por_clave[~inconsistente].fillna(mun_texto[~inconsistente]),
            "municipio_clave": "06" + mun_clave[~inconsistente],
            "estado": "Colima",
            "latitud": _numero(ok["Latitud"]),
            "longitud": _numero(ok["Longitud"]),
            "fecha_alta": ok["Fecha_Alta"],
            "archivo_origen": ok["archivo_origen"],
            "capturado_utc": ok["capturado_utc"],
        },
        index=ok.index,
    )
    return salida, pd.concat(rechazos)


def plata_denue(carpeta_bronce: Path = BRONCE) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    crudo = leer_bronce("denue", carpeta_bronce)
    if crudo.empty:
        return pd.DataFrame(), pd.DataFrame(), _reporte("denue", 0, 0, 0, pd.DataFrame())
    # Solo la fotografía más reciente: el DENUE es un directorio, no una serie
    crudo = crudo[crudo["capturado_utc"] == crudo["capturado_utc"].max()]
    preparados, rech_tipos = preparar_denue(crudo)
    unicos, conflictos, n_exactos = resolver_duplicados(preparados, ["clee"], ["nombre", "latitud", "longitud"])
    validos, rech_puerta = validar(unicos, ESQUEMA_DENUE)
    cuarentena = pd.concat([_a_texto(rech_tipos), _a_texto(conflictos), _a_texto(rech_puerta)], ignore_index=True)
    return validos, cuarentena, _reporte("denue", len(crudo), n_exactos, len(validos), cuarentena)


# ---------------------------------------------------------------- utilidades

def _a_texto(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].astype(str)
    return df


def _reporte(fuente, recibidos, exactos, validos, cuarentena) -> dict:
    evaluados = validos + len(cuarentena)
    motivos = cuarentena["motivo"].value_counts().to_dict() if len(cuarentena) else {}
    return {
        "fuente": fuente,
        "registros_bronce": int(recibidos),
        "duplicados_exactos_resueltos": int(exactos),
        "registros_evaluados": int(evaluados),
        "validos_plata": int(validos),
        "cuarentena": int(len(cuarentena)),
        "tasa_validez": round(validos / evaluados, 4) if evaluados else None,
        "motivos": {k: int(v) for k, v in motivos.items()},
    }


def construir_plata(carpeta_bronce: Path = BRONCE, salida: Path = DATA) -> dict:
    """Ejecuta la puerta de calidad para todas las fuentes y guarda plata, cuarentena y reporte."""
    (salida / "plata").mkdir(parents=True, exist_ok=True)
    (salida / "cuarentena").mkdir(parents=True, exist_ok=True)
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    reportes = []
    for fuente, funcion, nombre in (("sniim", plata_sniim, "sniim_precios"), ("denue", plata_denue, "denue_negocios")):
        validos, cuarentena, rep = funcion(carpeta_bronce)
        if len(validos):
            _a_texto(validos).to_csv(salida / "plata" / f"{nombre}.csv", index=False)
        cuarentena = cuarentena.assign(evaluado_utc=ahora)
        cuarentena.to_csv(salida / "cuarentena" / f"{fuente}_cuarentena.csv", index=False)
        rep["evaluado_utc"] = ahora
        reportes.append(rep)
    (salida / "plata" / "reporte_puerta.json").write_text(json.dumps(reportes, ensure_ascii=False, indent=2), encoding="utf-8")
    _bitacora_puerta(reportes, salida / "bitacora" / "puerta_calidad.csv")
    return {r["fuente"]: r for r in reportes}


def _bitacora_puerta(reportes: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    filas = pd.DataFrame(
        [{k: r[k] for k in ("evaluado_utc", "fuente", "registros_bronce", "duplicados_exactos_resueltos",
                            "registros_evaluados", "validos_plata", "cuarentena", "tasa_validez")} for r in reportes]
    )
    filas.to_csv(ruta, mode="a", header=not ruta.exists(), index=False)
