"""Extractor del SNIIM: precios de frutas y hortalizas en el mercado de Colima.

Fuente: Sistema Nacional de Información e Integración de Mercados (SNIIM),
Secretaría de Economía. Página pública de consulta; se hace scraping ético
con ExtractorEtico (robots.txt, User-Agent honesto, pausa mínima de 1.5 s).
"""
import re
import unicodedata
from datetime import timedelta

import pandas as pd
from bs4 import BeautifulSoup

from extractores.base import ExtractorEtico, logger
from extractores.bronce import guardar_bronce
from extractores.config import cargar_config

CAMPOS = ["fecha", "presentacion", "origen", "destino", "precio_min", "precio_max", "precio_frec", "obs"]


def normalizar(texto):
    t = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower().strip()


def leer_catalogo(html):
    """Devuelve (productos, destinos) como listas de (texto, id) del formulario."""
    soup = BeautifulSoup(html, "html.parser")
    productos, destinos = [], []
    for sel in soup.find_all("select"):
        sid = normalizar(sel.get("id", "") + sel.get("name", ""))
        opciones = [(o.get_text(strip=True), o.get("value", "")) for o in sel.find_all("option")]
        opciones = [(t, v) for t, v in opciones if v not in ("", "-1")]
        if "producto" in sid:
            productos = opciones
        elif "destino" in sid:
            destinos = opciones
    return productos, destinos


def filtrar_productos(productos, claves):
    """Elige los productos cuyo nombre contiene alguna clave como palabra completa.

    Así "papa alpha" no confunde "papaya" (defecto encontrado el 8 de noviembre).
    """
    patrones = [re.compile(r"(?<!\w)" + re.escape(normalizar(c)) + r"(?!\w)") for c in claves]
    return [(t, v) for t, v in productos if any(p.search(normalizar(t)) for p in patrones)]


def solo_destino(df, texto):
    """Conserva solo las filas del mercado destino indicado (por ejemplo, Colima)."""
    if df.empty:
        return df
    return df[df["destino"].map(normalizar).str.contains(normalizar(texto), regex=False)].reset_index(drop=True)


def parsear_resultados(html):
    """Lee la tabla de resultados del SNIIM tal como viene (texto crudo)."""
    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.select_one("table#tblResultados")
    if tabla is None:
        return pd.DataFrame(columns=CAMPOS)
    filas = []
    for tr in tabla.find_all("tr"):
        celdas = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(celdas) == len(CAMPOS) and celdas[0][:1].isdigit():
            filas.append(dict(zip(CAMPOS, celdas, strict=True)))
    return pd.DataFrame(filas, columns=CAMPOS)


class ExtractorSNIIM:
    """Consulta el SNIIM producto por producto y conserva solo el mercado de Colima.

    El filtro de destino del SNIIM no funciona (si se pide DestinoId de Colima regresa
    0 filas), así que se piden todos los mercados y se filtra aquí por el texto del destino.
    """

    def __init__(self, ext=None):
        self.cfg = cargar_config()["sniim"]
        self.ext = ext or ExtractorEtico()
        self._productos = None

    def preparar(self):
        r = self.ext.get(self.cfg["base_url"] + self.cfg["pagina_consulta"])
        productos, _ = leer_catalogo(r.text)
        self._productos = filtrar_productos(productos, self.cfg["productos_clave"])
        return self._productos

    def consultar(self, producto, inicio, fin):
        """Regresa (filas de Colima, total de filas que mandó el SNIIM)."""
        nombre, pid = producto
        params = {
            "fechaInicio": inicio.strftime("%d/%m/%Y"),
            "fechaFinal": fin.strftime("%d/%m/%Y"),
            "ProductoId": pid,
            "OrigenId": "-1",
            "Origen": "Todos",
            "DestinoId": "-1",
            "Destino": "Todos",
            "PreciosPorId": self.cfg["precios_por_id"],
            "RegistrosPorPagina": str(self.cfg["registros_por_pagina"]),
        }
        r = self.ext.get(self.cfg["base_url"] + self.cfg["pagina_resultados"], params=params)
        todas = parsear_resultados(r.text)
        df = solo_destino(todas, self.cfg["destino_texto"])
        df.insert(0, "producto", nombre)
        df.insert(1, "producto_id", pid)
        return df, len(todas)

    def capturar(self, inicio, fin):
        """Captura todos los productos clave entre dos fechas, en bloques de fechas."""
        productos = self._productos if self._productos is not None else self.preparar()
        bloque = int(self.cfg.get("bloque_dias", 92))
        limite = int(self.cfg["registros_por_pagina"])
        partes, avisos = [], []
        for prod in productos:
            a = inicio
            while a <= fin:
                b = min(a + timedelta(days=bloque - 1), fin)
                df, total = self.consultar(prod, a, b)
                if total >= limite:
                    avisos.append(f"{prod[0]} {a}..{b}: posible truncamiento ({total} filas)")
                    logger.warning(avisos[-1])
                partes.append(df)
                a = b + timedelta(days=1)
            logger.info(f"SNIIM {prod[0]}: listo")
        columnas = ["producto", "producto_id", *CAMPOS]
        datos = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=columnas)
        meta = {
            "url": self.cfg["base_url"] + self.cfg["pagina_resultados"],
            "rango": f"{inicio}..{fin}",
            "destino": self.cfg["destino_texto"],
            "productos": [p[0] for p in productos],
            "avisos": avisos,
            "user_agent": self.ext.ua,
        }
        return datos, meta


def ejecutar(inicio, fin, nombre):
    ex = ExtractorSNIIM()
    datos, meta = ex.capturar(inicio, fin)
    if len(datos):
        guardar_bronce(datos, "sniim", nombre, meta)
    return len(datos)
