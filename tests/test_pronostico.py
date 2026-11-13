"""Pruebas del pronóstico con una serie sintética (tendencia + ruido)."""

import numpy as np
import pandas as pd

from pipeline.pronostico import HORIZONTE, MODELOS, comparar, construir_pronostico, errores


def serie_sintetica(n=60, semilla=7):
    rng = np.random.default_rng(semilla)
    meses = pd.date_range("2021-01-01", periods=n, freq="MS")
    return pd.Series(100 + 0.3 * np.arange(n) + rng.normal(0, 2, n), index=meses)


def test_errores_conocidos():
    real, pred = pd.Series([100.0, 200.0]), pd.Series([110.0, 190.0])
    e = errores(real, pred)
    assert e["mae"] == 10 and e["rmse"] == 10
    assert abs(e["mape"] - 7.5) < 1e-9


def test_comparar_evalua_los_cuatro_y_elige_uno():
    tabla, predicciones = comparar(serie_sintetica())
    assert set(tabla["modelo"]) == set(MODELOS)
    assert tabla["elegido"].sum() == 1
    assert tabla.loc[tabla["elegido"], "rmse"].iloc[0] == tabla["rmse"].min()
    assert all(len(p) == 12 for p in predicciones.values())


def test_pronostico_publica_intervalo_y_quita_mes_incompleto(tmp_path):
    s = serie_sintetica()
    (tmp_path / "oro").mkdir()
    (tmp_path / "plata").mkdir()
    pd.DataFrame({"mes": s.index.strftime("%Y-%m"), "indice": s.values}).to_csv(
        tmp_path / "oro" / "indice_costo_taco.csv", index=False
    )
    # el último mes solo tiene datos hasta el día 10: no está completo y no debe usarse
    pd.DataFrame({"fecha": [f"{s.index[-1]:%Y-%m}-10"]}).to_csv(tmp_path / "plata" / "sniim_precios.csv", index=False)
    construir_pronostico(tmp_path)
    salida = pd.read_csv(tmp_path / "oro" / "pronostico.csv")
    pron = salida[salida["tipo"] == "pronostico"]
    assert len(pron) == HORIZONTE
    assert (pron["li_95"] < pron["valor"]).all() and (pron["valor"] < pron["ls_95"]).all()
    assert (salida["tipo"] == "observado").sum() == len(s) - 1
    assert pron["mes"].iloc[0] == f"{s.index[-1]:%Y-%m}"
