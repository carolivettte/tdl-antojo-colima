"""Extractor de series del INPC (API del Banco de Indicadores del INEGI).

Las series a descargar se configuran en config/fuentes.yaml (inegi.series).
Si no hay series configuradas, la ejecución se registra como "vacio".
"""
from __future__ import annotations

import pandas as pd

from extractores.base import ExtractorEtico
from extractores.bronce import guardar_bronce
from extractores.config import cargar_config, token_inegi


def capturar(ext: ExtractorEtico | None = None) -> int:
    cfg = cargar_config()["inegi"]
    if not cfg.get("series"):
        return 0
    ext = ext or ExtractorEtico()
    token = token_inegi()
    partes = []
    for s in cfg["series"]:
        url = f"{cfg['base_url']}/{s['id']}/es/{s.get('geo', '00')}/false/{s.get('banco', 'BIE')}/2.0/{token}"
        js = ext.get(url, params={"type": "json"}).json()
        for serie in js.get("Series", []):
            obs = pd.DataFrame(serie.get("OBSERVATIONS", []))
            obs.insert(0, "serie", s["nombre"])
            obs.insert(1, "indicador", serie.get("INDICADOR"))
            obs.insert(2, "frecuencia", serie.get("FREQ"))
            obs.insert(3, "ultima_actualizacion", serie.get("LASTUPDATE"))
            partes.append(obs)
    datos = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    if len(datos):
        meta = {"url": cfg["base_url"] + "/... (token oculto)", "series": cfg["series"], "user_agent": ext.ua}
        guardar_bronce(datos, "inegi", "inpc", meta)
    return len(datos)
