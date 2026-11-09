"""Pruebas automáticas de la capa bronce (sin red: usan datos de ejemplo)."""
import urllib.robotparser

import pandas as pd

from extractores import denue, sniim
from extractores.base import ExtractorEtico, user_agent
from extractores.bronce import ocultar_token

HTML_CONSULTA = """
<select id="ddlProducto">
  <option value="-1">Seleccione</option>
  <option value="514">Limón con semilla # 5</option>
  <option value="600">Aguacate Hass</option>
  <option value="700">Manzana Golden</option>
</select>
<select id="ddlDestino">
  <option value="-1">Todos</option>
  <option value="60">Colima: Centros de Distribución de Colima</option>
  <option value="10">Jalisco: Mercado de Abasto de Guadalajara</option>
</select>
"""

HTML_RESULTADOS = """
<table id="tblResultados">
  <tr><td>Fecha</td><td>Presentación</td><td>Origen</td><td>Destino</td>
      <td>Mín</td><td>Máx</td><td>Frec</td><td>Obs</td></tr>
  <tr><td colspan="8">encabezado</td></tr>
  <tr><td>04/11/2026</td><td>Kilogramo</td><td>Colima</td><td>Colima: Centros de Distribución de Colima</td>
      <td>18.00</td><td>22.00</td><td>20.00</td><td></td></tr>
  <tr><td>05/11/2026</td><td>Kilogramo</td><td>Colima</td><td>Colima: Centros de Distribución de Colima</td>
      <td>19.00</td><td>23.00</td><td>21.00</td><td></td></tr>
</table>
"""


def test_catalogo_detecta_productos_y_destino_colima():
    productos, destinos = sniim.leer_catalogo(HTML_CONSULTA)
    elegidos = sniim.filtrar_productos(productos, ["limon", "aguacate"])
    assert [p[1] for p in elegidos] == ["514", "600"]  # la manzana no es insumo clave
    assert any("Colima" in t for t, _ in destinos)


def test_papa_no_confunde_papaya():
    productos = [("Papa Alpha - Primera", "740"), ("Papaya Maradol - Primera", "609")]
    assert sniim.filtrar_productos(productos, ["papa alpha"]) == [("Papa Alpha - Primera", "740")]
    assert sniim.filtrar_productos(productos, ["papa"]) == [("Papa Alpha - Primera", "740")]


def test_solo_conserva_el_mercado_de_colima():
    df = pd.DataFrame({"destino": ["Colima: Centros de distribución de Colima", "Jalisco: Mercado de Abasto de Guadalajara"],
                       "precio_frec": ["20.00", "18.00"]})
    filtrado = sniim.solo_destino(df, "Colima:")
    assert list(filtrado["precio_frec"]) == ["20.00"]


def test_parseo_resultados_conserva_texto_crudo():
    df = sniim.parsear_resultados(HTML_RESULTADOS)
    assert len(df) == 2
    assert df.loc[0, "precio_frec"] == "20.00"  # bronce no convierte tipos
    assert list(df.columns) == sniim.CAMPOS


def test_tabla_inexistente_devuelve_vacio():
    assert sniim.parsear_resultados("<html></html>").empty


def test_denue_elimina_datos_personales():
    df = pd.DataFrame([{
        "CLEE": "x", "Nombre": "CAFETERIA EJEMPLO", "Razon_social": "JUAN PEREZ",
        "Telefono": "3120000000", "Correo_e": "a@b.mx", "Sitio_internet": "", "Latitud": "19.2",
    }])
    limpio = denue.quitar_datos_personales(df, ["Razon_social", "Telefono", "Correo_e", "Sitio_internet"])
    assert not {"Razon_social", "Telefono", "Correo_e", "Sitio_internet"} & set(limpio.columns)
    assert "Nombre" in limpio.columns and "Latitud" in limpio.columns


def test_token_nunca_se_guarda():
    url = "https://www.inegi.org.mx/app/api/denue/v1/consulta/Buscar/x/1/2/0123abcd-4567-89ab-cdef-0123456789ab"
    assert "0123abcd" not in ocultar_token(url)


def test_user_agent_honesto():
    ua = user_agent("equipo@colima.tecnm.mx")
    assert "TDL-Observatorio" in ua and "equipo@colima.tecnm.mx" in ua


def test_robots_bloquea_rutas_prohibidas():
    ext = ExtractorEtico(pausa=0, contacto="prueba@colima.tecnm.mx")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(["User-agent: *", "Disallow: /privado/"])
    ext.robots["https://ejemplo.mx"] = rp
    assert ext.permitido("https://ejemplo.mx/publico/precios")
    assert not ext.permitido("https://ejemplo.mx/privado/datos")


class _RespuestaFalsa:
    def __init__(self, status, headers=None):
        self.status_code = status
        self.headers = headers or {}
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_respeta_retry_after_en_429(monkeypatch):
    """Resiliencia: ante un 429 espera lo que dice Retry-After y reintenta (sesión 12)."""
    import extractores.base as base

    respuestas = iter([_RespuestaFalsa(429, {"Retry-After": "7"}), _RespuestaFalsa(200)])
    esperas = []
    monkeypatch.setattr(base.requests, "get", lambda *a, **k: next(respuestas))
    monkeypatch.setattr(base.time, "sleep", esperas.append)

    ext = ExtractorEtico(pausa=0, contacto="prueba@colima.tecnm.mx")
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(["User-agent: *", "Allow: /"])
    ext.robots["https://ejemplo.mx"] = rp
    assert ext.get("https://ejemplo.mx/datos").status_code == 200
    assert 7 in esperas
