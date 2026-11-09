"""Extractor de clima diario de Colima (Open-Meteo, API sin llave).

Histórico: API de archivo (ERA5), desde 2018. Diario: API de pronóstico con
los últimos días observados. Open-Meteo pide atribución (CC BY 4.0) y uso no
comercial por debajo de 10,000 llamadas diarias; aquí se hacen 1 o 2 al día.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from extractores.base import ExtractorEtico
from extractores.bronce import guardar_bronce
from extractores.config import cargar_config


def _a_tabla(js: dict) -> pd.DataFrame:
    diario = js.get("daily", {})
    return pd.DataFrame(diario)


def _params(cfg: dict, extra: dict) -> dict:
    col = cargar_config()["colima"]
    return {
        "latitude": col["latitud"],
        "longitude": col["longitud"],
        "daily": ",".join(cfg["variables_diarias"]),
        "timezone": col["zona_horaria"],
        **extra,
    }


def historico(fin: date, ext: ExtractorEtico | None = None) -> int:
    cfg = cargar_config()["clima"]
    ext = ext or ExtractorEtico()
    params = _params(cfg, {"start_date": cfg["historico_desde"], "end_date": fin.isoformat()})
    r = ext.get(cfg["archivo_url"], params=params)
    df = _a_tabla(r.json())
    if len(df):
        guardar_bronce(df, "clima", "clima_historico", {"url": r.url, "user_agent": ext.ua})
    return len(df)


def recientes(ext: ExtractorEtico | None = None) -> int:
    cfg = cargar_config()["clima"]
    ext = ext or ExtractorEtico()
    params = _params(cfg, {"past_days": cfg["dias_recientes"], "forecast_days": 1})
    r = ext.get(cfg["pronostico_url"], params=params)
    df = _a_tabla(r.json())
    if len(df):
        guardar_bronce(df, "clima", "clima_diario", {"url": r.url, "user_agent": ext.ua})
    return len(df)
