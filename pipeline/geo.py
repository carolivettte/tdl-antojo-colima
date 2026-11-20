"""Fuente especializada geoespacial (E2): puerta del Marco Geoestadístico y uniones espaciales.

Capas que se cruzan:
  - Taquerías del DENUE (plata), fijas y semifijas.
  - Generadores de afluencia del DENUE (plata): escuelas, centros de salud y hospitales.
  - Límites municipales del Marco Geoestadístico del INEGI (plata, GeoJSON validado).

Qué produce en oro:
  geo_municipios.csv / .geojson  área (km²), taquerías y afluencia por municipio y sus densidades
  geo_zonas.csv                  cuadrícula de 1 km: afluencia, taquerías registradas e índice de
                                 "zona probable de competencia no registrada u oportunidad"
  geo_puntos.csv                 puntos para el mapa, SIN nombres (solo clave, categoría y coordenadas)
  plata/reporte_geo.json         consistencia espacial, análisis de radio y validación del índice

Sobre el índice: el DENUE registra negocios fijos y semifijos, pero no ambulantes. No inventamos
puestos: medimos dónde hay mucha afluencia y poca competencia registrada. Es un indicador
relativo (alta, media, baja), no un conteo, y se valida contra los semifijos registrados.

Sistemas de coordenadas: los datos llegan en WGS84 (EPSG:4326, grados). Para medir áreas, radios
y la cuadrícula en metros se proyecta a UTM zona 13N (EPSG:32613), donde cae todo Colima.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from shapely.geometry import box
from shapely.validation import make_valid

from extractores.config import DATA, cargar_config
from pipeline.catalogos import LATITUD, LONGITUD, MUNICIPIOS

CRS_GEOGRAFICO = "EPSG:4326"
CLAVES_ESPERADAS = {"06" + c for c in MUNICIPIOS}
# Caja del territorio continental de Colima (con margen). Recorta islas lejanas si el Marco las trae
# dentro de un municipio, para que el área y la densidad describan donde están los negocios.
CAJA_CONTINENTAL = box(LONGITUD[0] - 0.1, LATITUD[0] - 0.1, LONGITUD[1] + 0.1, LATITUD[1] + 0.1)


def _columna(gdf: pd.DataFrame, opciones: list[str]) -> str | None:
    for c in opciones:
        if c in gdf.columns:
            return c
    return None


# ------------------------------------------------------------------ puerta del Marco Geoestadístico


def plata_marco(carpeta_bronce: Path, salida: Path, evaluado_utc: str) -> dict | None:
    """Valida los polígonos municipales y deja en plata solo los correctos (cuarentena con motivo)."""
    archivos = sorted((carpeta_bronce / "marco_geo").glob("fecha=*/*.geojson"))
    if not archivos:
        return None
    ruta = archivos[-1]
    meta_ruta = ruta.with_suffix(".meta.json")
    capturado = json.loads(meta_ruta.read_text(encoding="utf-8"))["capturado_utc"] if meta_ruta.exists() else ""
    gdf = gpd.read_file(ruta)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_GEOGRAFICO)  # RFC 7946: GeoJSON sin CRS = WGS84
    col_clave = _columna(gdf, ["cvegeo", "CVEGEO", "cve_geo"])
    col_nombre = _columna(gdf, ["nomgeo", "NOMGEO", "nom_mun", "NOM_MUN", "nombre"])
    gdf = gdf.rename(columns={col_clave: "cvegeo", col_nombre: "nomgeo"})
    gdf["cvegeo"] = gdf["cvegeo"].astype(str).str.zfill(5)
    gdf["archivo_origen"] = ruta.name
    gdf["capturado_utc"] = capturado

    motivos = pd.Series("", index=gdf.index)
    motivos[~gdf["cvegeo"].isin(CLAVES_ESPERADAS)] += "clave de municipio fuera de Colima; "
    motivos[gdf.geometry.isna() | gdf.geometry.is_empty] += "geometría vacía; "
    invalida = gdf.geometry.notna() & ~gdf.geometry.is_valid
    gdf.loc[invalida, "geometry"] = gdf.loc[invalida, "geometry"].apply(make_valid)  # se repara y se cuenta
    sigue_mal = gdf.geometry.notna() & ~gdf.geometry.is_valid
    motivos[sigue_mal] += "geometría inválida que no se pudo reparar; "
    duplicado = gdf["cvegeo"].duplicated(keep="last")
    motivos[duplicado] += "municipio duplicado (se conserva el último); "

    malos = motivos != ""
    cuarentena = pd.DataFrame(gdf.loc[malos].drop(columns="geometry"))
    cuarentena["motivo"] = motivos[malos].str.rstrip("; ")
    faltantes = sorted(CLAVES_ESPERADAS - set(gdf.loc[~malos, "cvegeo"]))
    for clave in faltantes:
        cuarentena = pd.concat(
            [
                cuarentena,
                pd.DataFrame(
                    [
                        {
                            "cvegeo": clave,
                            "archivo_origen": ruta.name,
                            "capturado_utc": capturado,
                            "motivo": "municipio faltante en el Marco Geoestadístico",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
    validos = gdf.loc[~malos, ["cvegeo", "nomgeo", "archivo_origen", "capturado_utc", "geometry"]]

    (salida / "plata").mkdir(parents=True, exist_ok=True)
    (salida / "cuarentena").mkdir(parents=True, exist_ok=True)
    validos.to_file(salida / "plata" / "marco_municipios.geojson", driver="GeoJSON")
    cuarentena.assign(evaluado_utc=evaluado_utc).to_csv(salida / "cuarentena" / "marco_geo_cuarentena.csv", index=False)
    evaluados = len(gdf) - int(duplicado.sum()) + len(faltantes)
    return {
        "fuente": "marco_geo",
        "registros_bronce": int(len(gdf)),
        "duplicados_exactos_resueltos": int(duplicado.sum()),
        "registros_evaluados": int(evaluados),
        "validos_plata": int(len(validos)),
        "cuarentena": int(len(cuarentena) - int(duplicado.sum())),
        "tasa_validez": round(len(validos) / evaluados, 4) if evaluados else None,
        "motivos": {k: int(v) for k, v in cuarentena["motivo"].value_counts().items()},
        "geometrias_reparadas": int(invalida.sum()),
        "evaluado_utc": evaluado_utc,
    }


# ------------------------------------------------------------------ uniones espaciales y capa oro


def _puntos(df: pd.DataFrame, categoria: pd.Series) -> gpd.GeoDataFrame:
    gdf = gpd.GeoDataFrame(
        {
            "clee": df["clee"].values,
            "categoria": categoria.values,
            "municipio_clave": df["municipio_clave"].astype(str).values,
            "latitud": df["latitud"].values,
            "longitud": df["longitud"].values,
            "archivo_origen": df["archivo_origen"].values,
            "capturado_utc": df["capturado_utc"].astype(str).values,
        },
        geometry=gpd.points_from_xy(df["longitud"], df["latitud"]),
        crs=CRS_GEOGRAFICO,
    )
    return gdf


def _origenes(serie: pd.Series) -> str:
    return ";".join(sorted(set(serie.dropna().astype(str))))


def construir_geo(datos: Path = DATA) -> dict:
    cfg = cargar_config()["geo"]
    crs_m, radio, celda = cfg["crs_metrico"], cfg["radio_m"], cfg["celda_m"]
    ruta_afl = datos / "plata" / "denue_afluencia.csv"
    ruta_mun = datos / "plata" / "marco_municipios.geojson"
    ruta_den = datos / "plata" / "denue_negocios.csv"
    if not (ruta_afl.exists() and ruta_mun.exists() and ruta_den.exists()):
        return {}

    denue = pd.read_csv(ruta_den, dtype={"municipio_clave": str, "clee": str})
    taq = denue[denue["tipo_negocio"] == "taqueria"]
    afl = pd.read_csv(ruta_afl, dtype={"municipio_clave": str, "clee": str})
    puntos = pd.concat(
        [
            _puntos(
                taq,
                pd.Series(np.where(taq["establecimiento"].eq("Semifijo"), "taqueria_semifija", "taqueria_fija"), index=taq.index),
            ),
            _puntos(afl, afl["tipo_afluencia"].map({"educacion": "escuela", "salud": "salud"})),
        ],
        ignore_index=True,
    )
    puntos = gpd.GeoDataFrame(puntos, geometry="geometry", crs=CRS_GEOGRAFICO)

    municipios = gpd.read_file(ruta_mun)
    municipios["geometry"] = municipios.geometry.intersection(CAJA_CONTINENTAL)

    # 1) Unión espacial punto-en-polígono: ¿en qué municipio cae cada punto según el Marco?
    unidos = gpd.sjoin(puntos, municipios[["cvegeo", "nomgeo", "geometry"]], how="left", predicate="within")
    unidos = unidos[~unidos.index.duplicated(keep="first")]
    dentro = unidos["cvegeo"].notna()
    coincide = unidos.loc[dentro, "cvegeo"] == unidos.loc[dentro, "municipio_clave"]

    # 2) Municipios: área en km² (proyección métrica) y densidades
    mun_m = municipios.to_crs(crs_m)
    conteo = unidos[dentro].groupby(["cvegeo", "categoria"]).size().unstack(fill_value=0)
    for c in ["taqueria_fija", "taqueria_semifija", "escuela", "salud"]:
        if c not in conteo.columns:
            conteo[c] = 0
    origen_mun = unidos[dentro].groupby("cvegeo")["archivo_origen"].apply(_origenes)
    tabla_mun = pd.DataFrame(
        {
            "municipio_clave": municipios["cvegeo"],
            "municipio": municipios["nomgeo"],
            "area_km2": (mun_m.geometry.area / 1e6).round(1).values,
        }
    )
    tabla_mun = tabla_mun.merge(conteo, left_on="municipio_clave", right_index=True, how="left").fillna(0)
    for c in ["taqueria_fija", "taqueria_semifija", "escuela", "salud"]:
        tabla_mun[c] = tabla_mun[c].astype(int)
    tabla_mun["taquerias"] = tabla_mun["taqueria_fija"] + tabla_mun["taqueria_semifija"]
    tabla_mun["afluencia"] = tabla_mun["escuela"] + tabla_mun["salud"]
    tabla_mun["taquerias_km2"] = (tabla_mun["taquerias"] / tabla_mun["area_km2"]).round(3)
    tabla_mun["afluencia_km2"] = (tabla_mun["afluencia"] / tabla_mun["area_km2"]).round(3)
    tabla_mun["afluencia_por_taqueria"] = (tabla_mun["afluencia"] / tabla_mun["taquerias"].replace(0, np.nan)).round(2)
    tabla_mun["pct_semifijas"] = (tabla_mun["taqueria_semifija"] / tabla_mun["taquerias"].replace(0, np.nan) * 100).round(1)
    tabla_mun["fuente"] = "DENUE (taquerías y afluencia) + Marco Geoestadístico"
    tabla_mun["archivos_bronce"] = (
        tabla_mun["municipio_clave"].map(origen_mun).fillna("") + ";" + municipios["archivo_origen"].values
    ).str.strip(";")
    tabla_mun["capturado_utc"] = municipios["capturado_utc"].values
    tabla_mun = tabla_mun.sort_values("municipio_clave").reset_index(drop=True)

    # 3) Radio de 1 km alrededor de cada escuela o centro de salud: ¿cuántas taquerías registradas hay?
    pm = puntos.to_crs(crs_m)
    afl_m = pm[pm["categoria"].isin(["escuela", "salud"])].copy()
    taq_m = pm[pm["categoria"].str.startswith("taqueria")]
    zonas_radio = afl_m.copy()
    zonas_radio["geometry"] = afl_m.buffer(radio)
    cerca = gpd.sjoin(taq_m[["categoria", "geometry"]], zonas_radio[["clee", "geometry"]], how="inner", predicate="within")
    por_punto = cerca.groupby("index_right").size().reindex(afl_m.index, fill_value=0)
    radio_resumen = {
        "radio_m": radio,
        "puntos_afluencia": int(len(afl_m)),
        "con_al_menos_una_taqueria": int((por_punto > 0).sum()),
        "pct_con_taqueria": round(float((por_punto > 0).mean() * 100), 1) if len(afl_m) else None,
        "mediana_taquerias": float(por_punto.median()) if len(afl_m) else None,
        "sin_taqueria_registrada": int((por_punto == 0).sum()),
    }

    # 4) Cuadrícula de 1 km: afluencia contra competencia registrada
    xy = np.floor(np.c_[pm.geometry.x, pm.geometry.y] / celda).astype(int)
    pm["celda"] = [f"{a}_{b}" for a, b in xy]
    pm["archivo_origen"] = puntos["archivo_origen"].values
    zonas = pm.groupby(["celda", "categoria"]).size().unstack(fill_value=0)
    for c in ["taqueria_fija", "taqueria_semifija", "escuela", "salud"]:
        if c not in zonas.columns:
            zonas[c] = 0
    zonas["afluencia"] = zonas["escuela"] + zonas["salud"]
    zonas["taquerias_registradas"] = zonas["taqueria_fija"] + zonas["taqueria_semifija"]
    zonas["presion_demanda"] = (zonas["afluencia"] / (zonas["taquerias_registradas"] + 1)).round(3)
    # Mitigación de sesgo por números pequeños: una celda con 1 o 2 escuelas y 0 taquerías saldría "alta"
    # solo por azar. Por debajo del mínimo de afluencia la celda no se clasifica.
    minimo = cfg.get("afluencia_minima", 3)
    con_afl = zonas["afluencia"] >= minimo
    zonas["categoria_zona"] = np.where(zonas["afluencia"] > 0, "afluencia insuficiente", "sin afluencia")
    if con_afl.sum() >= 3:
        rangos = zonas.loc[con_afl, "presion_demanda"].rank(method="first", pct=True)
        zonas.loc[con_afl, "categoria_zona"] = pd.cut(rangos, [0, 1 / 3, 2 / 3, 1], labels=["baja", "media", "alta"]).astype(str)
    cx = (np.array([int(c.split("_")[0]) for c in zonas.index]) + 0.5) * celda
    cy = (np.array([int(c.split("_")[1]) for c in zonas.index]) + 0.5) * celda
    centros = gpd.GeoSeries(gpd.points_from_xy(cx, cy), crs=crs_m).to_crs(CRS_GEOGRAFICO)
    zonas["longitud"] = centros.x.round(5).values
    zonas["latitud"] = centros.y.round(5).values
    centros_mun = gpd.sjoin(
        gpd.GeoDataFrame(geometry=centros.values, crs=CRS_GEOGRAFICO),
        municipios[["cvegeo", "geometry"]],
        how="left",
        predicate="within",
    )
    centros_mun = centros_mun[~centros_mun.index.duplicated(keep="first")]
    zonas["municipio_clave"] = centros_mun["cvegeo"].values
    zonas["fuente"] = "DENUE (taquerías y afluencia)"
    marco_archivo = str(municipios["archivo_origen"].iloc[0])
    zonas["archivos_bronce"] = (
        (
            pd.Series(pm.groupby("celda")["archivo_origen"].apply(_origenes).reindex(zonas.index).values).fillna("")
            + ";"
            + marco_archivo
        )
        .str.strip(";")
        .values
    )
    zonas["capturado_utc"] = pm.groupby("celda")["capturado_utc"].max().reindex(zonas.index).values
    zonas = zonas.reset_index().rename(columns={"index": "celda"})

    # 5) Validación del índice: ¿donde hay más afluencia también hay más puestos semifijos registrados?
    activas = zonas[(zonas["afluencia"] > 0) | (zonas["taquerias_registradas"] > 0)]
    rho_semi, p_semi = spearmanr(activas["afluencia"], activas["taqueria_semifija"]) if len(activas) > 2 else (np.nan, np.nan)
    rho_fija, p_fija = spearmanr(activas["afluencia"], activas["taqueria_fija"]) if len(activas) > 2 else (np.nan, np.nan)

    # 6) Salidas
    oro = datos / "oro"
    oro.mkdir(parents=True, exist_ok=True)
    tabla_mun.to_csv(oro / "geo_municipios.csv", index=False)
    cols_zona = [
        "celda",
        "municipio_clave",
        "latitud",
        "longitud",
        "escuela",
        "salud",
        "afluencia",
        "taqueria_fija",
        "taqueria_semifija",
        "taquerias_registradas",
        "presion_demanda",
        "categoria_zona",
        "fuente",
        "archivos_bronce",
        "capturado_utc",
    ]
    zonas[cols_zona].to_csv(oro / "geo_zonas.csv", index=False)
    puntos_salida = pd.DataFrame(unidos.drop(columns=["geometry", "index_right"], errors="ignore"))
    puntos_salida = puntos_salida.rename(columns={"cvegeo": "municipio_clave_marco", "nomgeo": "municipio_marco"})
    puntos_salida["fuente"] = np.where(
        puntos_salida["categoria"].str.startswith("taqueria"), "DENUE preparación de alimentos", "DENUE afluencia"
    )
    # Linaje del punto: su archivo del DENUE + el archivo del Marco que le asignó el municipio.
    puntos_salida["archivos_bronce"] = puntos_salida.pop("archivo_origen") + ";" + marco_archivo
    puntos_salida.to_csv(oro / "geo_puntos.csv", index=False)
    mapa = municipios[["cvegeo", "nomgeo", "geometry"]].merge(
        tabla_mun.drop(columns=["municipio", "fuente", "archivos_bronce", "capturado_utc"]),
        left_on="cvegeo",
        right_on="municipio_clave",
    )
    mapa["geometry"] = mapa.geometry.simplify(0.002, preserve_topology=True)
    mapa.to_file(oro / "geo_municipios.geojson", driver="GeoJSON")

    reporte = {
        "puntos": int(len(puntos)),
        "puntos_dentro_de_algun_municipio": int(dentro.sum()),
        "puntos_fuera_de_los_limites": int((~dentro).sum()),
        "consistencia_municipio_pct": round(float(coincide.mean() * 100), 2) if len(coincide) else None,
        "radio": radio_resumen,
        "zonas_1km": int(len(zonas)),
        "zonas_con_afluencia": int(con_afl.sum()),
        "afluencia_minima_para_clasificar": int(minimo),
        "zonas_por_categoria": {k: int(v) for k, v in zonas["categoria_zona"].value_counts().items()},
        "validacion_indice": {
            "spearman_afluencia_vs_semifijas": None if np.isnan(rho_semi) else round(float(rho_semi), 3),
            "p_semifijas": None if np.isnan(p_semi) else float(p_semi),
            "spearman_afluencia_vs_fijas": None if np.isnan(rho_fija) else round(float(rho_fija), 3),
            "p_fijas": None if np.isnan(p_fija) else float(p_fija),
        },
        "crs_metrico": crs_m,
    }
    (datos / "plata" / "reporte_geo.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"geo_municipios": len(tabla_mun), "geo_zonas": len(zonas), "geo_puntos": len(puntos_salida)}
