"""Pruebas del linaje (E2): de una fila de oro a su archivo de bronce, con fecha de ingesta y SHA-256."""

import hashlib
import json

import pandas as pd

from pipeline.linaje import catalogo_linaje, resolver_derivadas, separar_origenes, unir_origenes
from pipeline.oro import competencia_municipio, precios_mensuales


def bronce(tmp_path, nombre="sniim_diario_20261119T230229Z.csv", contenido=b"a,b\n1,2\n", alterar=False):
    carpeta = tmp_path / "data" / "bronce" / "sniim" / "fecha=2026-11-19"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_bytes(contenido)
    sha = hashlib.sha256(contenido).hexdigest()
    meta = {"fuente": "sniim", "capturado_utc": "2026-11-19T23:02:29+00:00", "registros": 1, "sha256": sha}
    (carpeta / nombre).with_suffix(".meta.json").write_text(json.dumps(meta), encoding="utf-8")
    if alterar:
        (carpeta / nombre).write_bytes(contenido + b"3,4\n")  # alguien editó bronce a mano
    return nombre


def test_unir_y_separar_origenes():
    assert unir_origenes(pd.Series(["b.csv", "a.csv", "b.csv", None])) == "a.csv;b.csv"
    assert separar_origenes("a.csv;b.csv") == ["a.csv", "b.csv"]
    assert separar_origenes("") == [] and separar_origenes(None) == []


def test_catalogo_detecta_bronce_integro_y_alterado(tmp_path):
    bueno = bronce(tmp_path)
    malo = bronce(tmp_path, nombre="sniim_diario_20261118T225632Z.csv", alterar=True)
    oro = pd.DataFrame({"x": [1, 2], "archivos_bronce": [bueno, f"{bueno};{malo}"]})
    cat = catalogo_linaje({"t": oro}, tmp_path / "data" / "bronce", tmp_path)
    estado = cat.set_index("archivo_bronce")["integro"]
    assert bool(estado[bueno]) is True and bool(estado[malo]) is False
    assert cat.loc[cat["archivo_bronce"] == bueno, "ruta_bronce"].iloc[0].startswith("data/bronce/sniim/")


def test_archivo_inexistente_no_es_integro(tmp_path):
    oro = pd.DataFrame({"archivos_bronce": ["no_existe.csv"]})
    cat = catalogo_linaje({"t": oro}, tmp_path, tmp_path)
    assert not cat["integro"].iloc[0]


def plata_sniim():
    filas = []
    for fecha, archivo in [("2026-08-05", "h.csv"), ("2026-10-07", "d1.csv"), ("2026-10-20", "d2.csv")]:
        filas.append(
            {
                "fecha": fecha,
                "insumo": "limon",
                "precio_frec": 20.0,
                "precio_min": 18.0,
                "precio_max": 22.0,
                "atipico": False,
                "archivo_origen": archivo,
                "capturado_utc": f"2026-11-1{len(filas)}T10:00:00+00:00",
            }
        )
    return pd.DataFrame(filas)


def test_precios_mensuales_llevan_linaje_y_el_mes_imputado_hereda_de_sus_vecinos():
    m = precios_mensuales(plata_sniim()).set_index("mes")
    assert m.loc["2026-10", "archivos_bronce"] == "d1.csv;d2.csv"
    assert m.loc["2026-10", "ingesta_min"] == "2026-11-11T10:00:00Z"
    assert bool(m.loc["2026-09", "imputado"]) is True
    assert m.loc["2026-09", "archivos_bronce"] == "d1.csv;d2.csv;h.csv"


def test_competencia_lleva_linaje():
    denue = pd.DataFrame(
        {
            "clee": ["1", "2"],
            "municipio_clave": ["06002", "06002"],
            "municipio": ["Colima", "Colima"],
            "tipo_negocio": ["taqueria", "taqueria"],
            "tamano": ["micro", "micro"],
            "establecimiento": ["Fijo", "Semifijo"],
            "archivo_origen": ["denue.csv", "denue.csv"],
            "capturado_utc": ["2026-11-09T08:12:42+00:00"] * 2,
        }
    )
    c = competencia_municipio(denue)
    assert c["archivos_bronce"].iloc[0] == "denue.csv" and c["ingesta_max"].iloc[0] == "2026-11-09T08:12:42Z"


def test_tabla_derivada_hereda_linaje_por_mes():
    madre = pd.DataFrame({"mes": ["2026-09", "2026-10"], "archivos_bronce": ["a.csv", "b.csv"]})
    hija = pd.DataFrame({"mes": ["2026-10", "2027-01"], "derivado_de": "indice_costo_taco"})
    t = resolver_derivadas({"indice_costo_taco": madre, "pronostico": hija})["pronostico"]
    assert list(t["archivos_bronce"]) == ["b.csv", "a.csv;b.csv"]
