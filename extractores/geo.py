"""Fuente especializada geoespacial (E2).

Dos capas oficiales del INEGI:

1. Generadores de afluencia del DENUE: escuelas de todos los niveles (SCIAN 611), centros de salud
   y clínicas sin hospitalización (rama 6214) y hospitales (622). Son los lugares donde se concentra
   la gente y donde suelen instalarse puestos de comida, registrados o no.
   PRIVACIDAD: muchos consultorios y escuelas pequeñas llevan el nombre de una persona, y el análisis
   no necesita nombres ni domicilios. Antes de guardar NADA se eliminan nombre, razón social,
   contacto y domicilio; solo quedan la clave del INEGI (CLEE), la clase de actividad, el tamaño,
   la colonia, el código postal y las coordenadas.

2. Límites municipales del Marco Geoestadístico (servicio web oficial del INEGI en GeoJSON,
   sin token): https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/06

Las dos pasan por el extractor ético (robots.txt, identificación, pausas) y se guardan en bronce
con su .meta.json y su huella SHA-256, igual que el SNIIM y el DENUE.
"""

from __future__ import annotations

import hashlib
import json

import pandas as pd

from extractores.base import ExtractorEtico
from extractores.bronce import ahora_utc, guardar_bronce, ocultar_token
from extractores.config import BRONCE, cargar_config, token_inegi
from extractores.denue import a_tabla, quitar_datos_personales


def url_area_act(
    base: str, entidad: str, sector: str, subsector: str, rama: str, inicio: int, fin: int, token: str, clase: str = "0"
) -> str:
    # BuscarAreaAct/{entidad}/{municipio}/{localidad}/{ageb}/{manzana}/{sector}/{subsector}/{rama}/{clase}/
    #               {nombre}/{inicio}/{fin}/{id}/{token}
    return f"{base}/BuscarAreaAct/{entidad}/0/0/0/0/{sector}/{subsector}/{rama}/{clase}/0/{inicio}/{fin}/0/{token}"


def capturar_afluencia(ext: ExtractorEtico | None = None) -> int:
    cfg = cargar_config()
    d, g = cfg["denue"], cfg["geo"]
    ent = cfg["colima"]["entidad_inegi"]
    ext = ext or ExtractorEtico()
    token = token_inegi()
    partes = []
    for capa in g["afluencia"]:
        inicio = 1
        while True:
            fin = inicio + d["tamano_pagina"] - 1
            url = url_area_act(
                d["base_url"], ent, capa["sector"], capa["subsector"], capa["rama"], inicio, fin, token, capa.get("clase", "0")
            )
            df = a_tabla(ext.get(url).json())
            if df.empty:
                break
            df = quitar_datos_personales(df, g["columnas_eliminadas"])
            df["tipo_afluencia"] = capa["tipo"]
            df["capa_scian"] = f"{capa['subsector']}/{capa['rama']}/{capa.get('clase', '0')}"
            partes.append(df)
            if len(df) < d["tamano_pagina"]:
                break
            inicio = fin + 1
    datos = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    if len(datos):
        guardar_bronce(
            datos,
            "denue_afluencia",
            "denue_afluencia_colima",
            {
                "url": f"{d['base_url']}/BuscarAreaAct/{ent}/... (token oculto)",
                "capas": g["afluencia"],
                "columnas_eliminadas": g["columnas_eliminadas"],
                "user_agent": ext.ua,
            },
        )
    return len(datos)


def guardar_bronce_geojson(contenido: bytes, fuente: str, nombre: str, meta: dict):
    """Guarda un GeoJSON tal cual llegó (bronce inmutable) con su .meta.json y su SHA-256."""
    marca = ahora_utc()
    carpeta = BRONCE / fuente / f"fecha={marca:%Y-%m-%d}"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}_{marca:%Y%m%dT%H%M%SZ}.geojson"
    ruta.write_bytes(contenido)
    datos = json.loads(contenido)
    meta = {
        "fuente": fuente,
        "archivo": ruta.name,
        "capturado_utc": marca.isoformat(),
        "registros": len(datos.get("features", [])),
        "columnas": sorted(datos["features"][0]["properties"]) if datos.get("features") else [],
        "sha256": hashlib.sha256(contenido).hexdigest(),
        "metadatos_fuente": datos.get("metadatos", {}),
        **{k: ocultar_token(v) if isinstance(v, str) else v for k, v in meta.items()},
    }
    ruta.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def capturar_marco(ext: ExtractorEtico | None = None) -> int:
    cfg = cargar_config()
    ext = ext or ExtractorEtico()
    url = cfg["geo"]["marco_url"].format(entidad=cfg["colima"]["entidad_inegi"])
    respuesta = ext.get(url)
    contenido = respuesta.content
    n = len(json.loads(contenido).get("features", []))
    if n:
        guardar_bronce_geojson(contenido, "marco_geo", "mgem_colima", {"url": url, "user_agent": ext.ua})
    return n
