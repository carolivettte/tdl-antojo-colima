"""Guarda una copia fechada del robots.txt de cada dominio usado.

Es la evidencia del análisis ético: qué decía robots.txt el día que se consultó.
Uso: python -m scripts.verificar_robots
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

import requests

from extractores.base import user_agent
from extractores.config import RAIZ, cargar_config

cfg = cargar_config()
URLS = {
    "sniim": cfg["sniim"]["base_url"],
    "inegi": cfg["denue"]["base_url"],
    "open-meteo-archivo": cfg["clima"]["archivo_url"],
    "open-meteo": cfg["clima"]["pronostico_url"],
}

if __name__ == "__main__":
    destino = RAIZ / "docs" / "etica" / "robots"
    destino.mkdir(parents=True, exist_ok=True)
    resumen = [f"# Revisión de robots.txt ({date.today()})", "", "| Fuente | URL | HTTP | Archivo |", "|---|---|---|---|"]
    for nombre, url in URLS.items():
        p = urlparse(url)
        robots = f"{p.scheme}://{p.netloc}/robots.txt"
        try:
            r = requests.get(robots, headers={"User-Agent": user_agent()}, timeout=30)
            archivo = destino / f"{nombre}_{date.today()}.txt"
            archivo.write_text(f"# {robots} · HTTP {r.status_code}\n{r.text}", encoding="utf-8")
            resumen.append(f"| {nombre} | {robots} | {r.status_code} | {archivo.name} |")
        except requests.RequestException as e:
            resumen.append(f"| {nombre} | {robots} | error: {type(e).__name__} | — |")
    (destino / "RESUMEN.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    print("\n".join(resumen))
