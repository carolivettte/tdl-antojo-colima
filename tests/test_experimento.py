"""Pruebas del banco y de los diseños de experimentos de E2 (sin correr el experimento completo)."""

import numpy as np
import pytest

from laboratorio.banco_sniim import CAMPOS, _pagina, leer_pagina, tasa_error
from laboratorio.experimento import configuracion, plan

FILAS = [
    {
        "fecha": "02/10/2020",
        "presentacion": "Kilogramo",
        "origen": "Jalisco",
        "destino": "Colima: Centros de distribución de Colima",
        "precio_min": "46.00",
        "precio_max": "70.00",
        "precio_frec": "70.00",
        "obs": "",
    },
    {
        "fecha": "06/10/2020",
        "presentacion": "Kilogramo",
        "origen": "Michoacán",
        "destino": "Jalisco: Mercado de Abasto de Guadalajara",
        "precio_min": "40.00",
        "precio_max": "60.00",
        "precio_frec": "55.00",
        "obs": "",
    },
]
ESPERADO = {"p.html": [[f[c] for c in CAMPOS] for f in FILAS]}


def leer(tmp_path, dano, parser):
    ruta = tmp_path / "p.html"
    ruta.write_text(_pagina(FILAS, dano), encoding="utf-8")
    return [leer_pagina((str(ruta), parser))]


@pytest.mark.parametrize("parser", ["html.parser", "lxml"])
def test_pagina_sana_se_lee_completa(tmp_path, parser):
    assert tasa_error(leer(tmp_path, "ninguno", parser), ESPERADO)[0] == 0


def test_celdas_sin_cierre_engañan_a_html_parser_pero_no_a_lxml(tmp_path):
    assert tasa_error(leer(tmp_path, "sin_cierres", "html.parser"), ESPERADO)[0] == 100
    assert tasa_error(leer(tmp_path, "sin_cierres", "lxml"), ESPERADO)[0] == 0


@pytest.mark.parametrize("dano", ["sin_id", "mojibake"])
def test_danos_que_ningun_parser_corrige(tmp_path, dano):
    for parser in ["html.parser", "lxml"]:
        assert tasa_error(leer(tmp_path, dano, parser), ESPERADO)[0] > 0


def test_2k3_es_ortogonal_y_balanceado():
    m = plan("2k3")[["procesos", "parser", "formato"]].to_numpy()
    assert len(m) == 8 and (m.sum(axis=0) == 0).all()
    assert (m.T @ m == 8 * np.eye(3)).all()


def test_media_fraccion_2k4_es_resolucion_iv():
    m = plan("2k4")
    fr = m[m["en_media_fraccion"]]
    assert len(m) == 16 and len(fr) == 8
    a, b, c, d = (fr[x].to_numpy() for x in ["procesos", "parser", "formato", "lote"])
    assert (d == a * b * c).all()  # generador D = ABC, relación de definición I = ABCD
    assert (a * b == c * d).all()  # las interacciones dobles quedan confundidas por pares


def test_bifactorial_tiene_tres_niveles_de_procesos():
    m = plan("bifactorial")
    assert sorted(m["procesos_n"].unique()) == [1, 2, 4] and len(m) == 6
    assert configuracion("bifactorial", m.iloc[0])["formato"] == "csv"
