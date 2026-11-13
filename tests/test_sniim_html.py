"""Pruebas del parseo del HTML del SNIIM con páginas reales guardadas, sin conexión a red.

Las páginas están en tests/fixtures/ (fragmentos reales guardados el 2026-11-13; ver el comentario
al inicio de cada archivo). Todas las pruebas de este módulo bloquean la red: si algún código
intentara conectarse a internet, la prueba fallaría.
"""
import socket
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from extractores import sniim
from extractores.config import cargar_config
from pipeline.catalogos import PRODUCTOS_SNIIM
from pipeline.esquemas import ESQUEMA_SNIIM
from pipeline.plata import preparar_sniim, validar

FIXTURES = Path(__file__).parent / "fixtures"
CONSULTA = (FIXTURES / "sniim_consulta_real.html").read_text(encoding="utf-8")
RESULTADOS = (FIXTURES / "sniim_resultados_real.html").read_text(encoding="utf-8")
SIN_FILAS = '<table id="tblResultados"><tr><td>Fecha</td></tr></table>'


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    """Cualquier intento de abrir una conexión de red hace fallar la prueba."""

    def bloqueado(*args, **kwargs):
        raise AssertionError("la prueba intentó usar la red")

    monkeypatch.setattr(socket.socket, "connect", bloqueado)
    monkeypatch.setattr(socket, "create_connection", bloqueado)


class RespuestaFalsa:
    def __init__(self, texto):
        self.text = texto


class ExtractorSinRed:
    """Sustituye a ExtractorEtico: responde con las páginas guardadas en lugar de ir a internet."""

    ua = "pruebas-sin-red"

    def __init__(self):
        self.pedidos = []

    def get(self, url, params=None):
        self.pedidos.append((url, params))
        if url.endswith("ConsultaFrutasYHortalizas.aspx"):
            return RespuestaFalsa(CONSULTA)
        if params and params.get("ProductoId") == "421":  # solo el limón tiene página guardada
            return RespuestaFalsa(RESULTADOS)
        return RespuestaFalsa(SIN_FILAS)


def test_catalogo_real_lee_todos_los_productos_y_el_mercado_de_colima():
    productos, destinos = sniim.leer_catalogo(CONSULTA)
    assert len(productos) == 222  # 223 opciones menos "Todos"
    assert ("Limón c/semilla # 5 - Primera", "421") in productos
    # La página real tiene varias listas de destino; el mercado de Colima debe estar con su id 80.
    assert ("Colima: Centros de distribución de Colima", "80") in destinos


def test_catalogo_real_elige_exactamente_los_8_insumos_sin_confundir_parecidos():
    productos, _ = sniim.leer_catalogo(CONSULTA)
    elegidos = sniim.filtrar_productos(productos, cargar_config()["sniim"]["productos_clave"])
    nombres = {nombre for nombre, _ in elegidos}
    # Los nombres elegidos son exactamente los que el pipeline sabe convertir en insumos.
    assert nombres == set(PRODUCTOS_SNIIM)
    assert len(elegidos) == 8
    # Productos parecidos de la página real que NO deben entrar.
    for parecido in ["Papaya Maradol - Primera", "Cebolla Bola grande - Primera",
                     "Aguacate Hass adelantado - Primera", "Aguacate Hass - Calidad extra",
                     "Limón c/semilla # 4 - Primera", "Tomate Bola - Primera"]:
        assert parecido not in nombres


def test_resultados_reales_saltan_titulos_y_encabezados_de_grupo():
    df = sniim.parsear_resultados(RESULTADOS)
    # 9 filas en la tabla: 1 de títulos + 1 encabezado "Frutas" + 7 de datos.
    assert len(df) == 7
    assert list(df.columns) == sniim.CAMPOS
    assert df["fecha"].str.match(r"^\d{2}/\d{2}/\d{4}$").all()
    assert "Frutas" not in df["fecha"].values


def test_resultados_reales_conservan_texto_crudo_y_acentos():
    df = sniim.parsear_resultados(RESULTADOS)
    assert df.loc[0, "precio_frec"] == "15.79"  # bronce no convierte tipos
    assert "Michoacán" in df["origen"].values  # los acentos llegan intactos
    assert (df["obs"] == "").all()


def test_resultados_reales_filtran_solo_el_mercado_de_colima():
    colima = sniim.solo_destino(sniim.parsear_resultados(RESULTADOS), "Colima:")
    assert list(colima["fecha"]) == ["03/11/2026", "06/11/2026"]
    assert set(colima["presentacion"]) == {"Kilogramo"}
    assert list(colima["precio_frec"]) == ["36.00", "36.00"]
    # El origen "Colima" en otros mercados no se confunde con el destino Colima.
    assert len(colima) == 2


def test_extractor_completo_funciona_sin_red_con_paginas_reales():
    ext = ExtractorSinRed()
    datos, meta = sniim.ExtractorSNIIM(ext=ext).capturar(date(2026, 11, 3), date(2026, 11, 6))
    assert len(datos) == 2
    assert set(datos["producto"]) == {"Limón c/semilla # 5 - Primera"}
    assert len(meta["productos"]) == 8
    assert len(ext.pedidos) == 1 + 8  # el catálogo y una consulta por insumo


def test_de_la_pagina_real_a_plata_pasa_la_puerta_de_calidad():
    datos, _ = sniim.ExtractorSNIIM(ext=ExtractorSinRed()).capturar(date(2026, 11, 3), date(2026, 11, 6))
    datos["archivo_origen"] = "sniim_prueba.csv"
    datos["capturado_utc"] = pd.Timestamp("2026-11-13T00:00:00Z")
    preparado, rechazos = preparar_sniim(datos)
    validos, invalidos = validar(preparado, ESQUEMA_SNIIM)
    assert len(rechazos) == 0 and len(invalidos) == 0
    assert list(validos["insumo"]) == ["limon", "limon"]
    assert validos["precio_frec"].tolist() == [36.0, 36.0]
    assert validos["municipio_clave"].unique().tolist() == ["06002"]
