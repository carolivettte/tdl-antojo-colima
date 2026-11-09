"""Extractor del DENUE (INEGI): negocios de preparación de alimentos en Colima.

Se usa el método BuscarAreaAct de la API oficial (token gratuito del INEGI).
Antes de guardar NADA se eliminan las columnas con datos de contacto o que
pueden ser nombres de personas físicas (Ley Federal de Protección de Datos
Personales en Posesión de los Particulares).
"""
from __future__ import annotations

import pandas as pd

from extractores.base import ExtractorEtico
from extractores.bronce import guardar_bronce
from extractores.config import cargar_config, token_inegi

# Orden de campos de BuscarAreaAct según la documentación del INEGI (29 campos)
CAMPOS_AREA_ACT = [
    "CLEE", "Id", "Nombre", "Razon_social", "Clase_actividad", "Estrato", "Tipo_vialidad",
    "Calle", "Num_Exterior", "Num_Interior", "Colonia", "CP", "Ubicacion", "Telefono",
    "Correo_e", "Sitio_internet", "Tipo", "Longitud", "Latitud", "tipo_corredor_industrial",
    "nom_corredor_industrial", "numero_local", "AGEB", "Manzana", "Edificio",
    "id_clase", "id_sector", "id_subsector", "id_rama",
]


def quitar_datos_personales(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    a_quitar = [c for c in df.columns if c.lower() in {x.lower() for x in columnas}]
    return df.drop(columns=a_quitar)


def a_tabla(js) -> pd.DataFrame:
    if not js:
        return pd.DataFrame()
    if isinstance(js, list) and isinstance(js[0], dict):
        return pd.DataFrame(js)
    if isinstance(js, list) and isinstance(js[0], list):
        return pd.DataFrame(js, columns=CAMPOS_AREA_ACT[: len(js[0])])
    return pd.DataFrame()


def capturar(ext: ExtractorEtico | None = None) -> int:
    cfg = cargar_config()
    d = cfg["denue"]
    ent = cfg["colima"]["entidad_inegi"]
    ext = ext or ExtractorEtico()
    token = token_inegi()
    partes, inicio = [], 1
    while True:
        fin = inicio + d["tamano_pagina"] - 1
        url = (
            f"{d['base_url']}/BuscarAreaAct/{ent}/0/0/0/0/{d['sector']}/{d['subsector']}/0/0/0/"
            f"{inicio}/{fin}/0/{token}"
        )
        js = ext.get(url).json()
        df = a_tabla(js)
        if df.empty:
            break
        partes.append(quitar_datos_personales(df, d["columnas_personales"]))
        if len(df) < d["tamano_pagina"]:
            break
        inicio = fin + 1
    datos = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    if len(datos):
        guardar_bronce(
            datos,
            "denue",
            "denue_colima_722",
            {
                "url": f"{d['base_url']}/BuscarAreaAct/{ent}/.../{d['subsector']}/... (token oculto)",
                "columnas_eliminadas": d["columnas_personales"],
                "user_agent": ext.ua,
            },
        )
    return len(datos)
