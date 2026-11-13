"""Pronóstico del Índice de Costo del Taco con cuatro modelos y selección por error.

Modelos: SES, Holt (tendencia amortiguada), Holt-Winters (tendencia y estacionalidad aditivas,
periodo 12) y ARIMA (orden elegido por AIC). Los tres de suavizamiento se ajustan como modelos
ETS de statsmodels para obtener intervalos de predicción comparables con los de ARIMA.

Validación: los últimos 12 meses completos son el conjunto de prueba; se ajusta con el resto y se
pronostica 12 pasos. Se elige el modelo con menor RMSE (desempate por MAE) y se reajusta con toda la
serie para pronosticar los próximos meses con intervalo de 95 %.

Uso:
    python -m pipeline.pronostico   # también lo corre pipeline.ejecutar después de la capa oro
"""

import itertools
import warnings

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

from extractores.config import DATA

PRUEBA = 12
HORIZONTE = 3
PERIODO = 12
DIA_MES_COMPLETO = 25  # un mes cuenta como completo si hay precios publicados después de este día


def serie_indice(datos=DATA) -> pd.Series:
    """Serie mensual del índice; quita el último mes si todavía no está completo."""
    indice = pd.read_csv(datos / "oro" / "indice_costo_taco.csv")
    serie = pd.Series(indice["indice"].values, index=pd.PeriodIndex(indice["mes"], freq="M").to_timestamp(), name="indice")
    serie = serie.asfreq("MS")
    plata = pd.read_csv(datos / "plata" / "sniim_precios.csv", usecols=["fecha"])
    ultima = pd.to_datetime(plata["fecha"]).max()
    if ultima.to_period("M") == serie.index[-1].to_period("M") and ultima.day < DIA_MES_COMPLETO:
        serie = serie.iloc[:-1]
    return serie


def diferencias_necesarias(serie: pd.Series, alfa: float = 0.05, maximo: int = 2) -> int:
    d, s = 0, serie.dropna()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        while d < maximo and adfuller(s, autolag="AIC")[1] > alfa:
            s, d = s.diff().dropna(), d + 1
    return d


def orden_arima(serie: pd.Series) -> tuple[int, int, int]:
    d = diferencias_necesarias(serie)
    mejor, orden = np.inf, (0, d, 0)
    for p, q in itertools.product(range(3), range(3)):
        try:
            aic = SARIMAX(serie, order=(p, d, q), trend="c" if d == 0 else "n").fit(disp=False).aic
        except (ValueError, np.linalg.LinAlgError):
            continue
        if aic < mejor:
            mejor, orden = aic, (p, d, q)
    return orden


def _ets(serie: pd.Series, trend=None, damped=False, seasonal=None):
    return ETSModel(
        serie,
        error="add",
        trend=trend,
        damped_trend=damped,
        seasonal=seasonal,
        seasonal_periods=PERIODO if seasonal else None,
    ).fit(disp=False)


def ajustar(nombre: str, serie: pd.Series, orden=None):
    if nombre == "SES":
        return _ets(serie)
    if nombre == "Holt":
        return _ets(serie, trend="add", damped=True)
    if nombre == "Holt-Winters":
        return _ets(serie, trend="add", damped=True, seasonal="add")
    if nombre == "ARIMA":
        orden = orden or orden_arima(serie)
        return SARIMAX(serie, order=orden, trend="c" if orden[1] == 0 else "n").fit(disp=False)
    raise ValueError(nombre)


MODELOS = ["SES", "Holt", "Holt-Winters", "ARIMA"]


def pronosticar(modelo, pasos: int, alfa: float = 0.05) -> pd.DataFrame:
    """Pronóstico puntual e intervalo (1 - alfa) para cualquiera de los cuatro modelos."""
    if isinstance(modelo.model, ETSModel):
        pred = modelo.get_prediction(start=len(modelo.data.endog), end=len(modelo.data.endog) + pasos - 1)
        marco = pred.summary_frame(alpha=alfa)
        return pd.DataFrame({"valor": marco["mean"], "li": marco["pi_lower"], "ls": marco["pi_upper"]})
    pred = modelo.get_forecast(pasos)
    ci = pred.conf_int(alpha=alfa)
    return pd.DataFrame({"valor": pred.predicted_mean, "li": ci.iloc[:, 0], "ls": ci.iloc[:, 1]})


def errores(real: pd.Series, pred: pd.Series) -> dict:
    e = real.values - pred.values
    return {
        "mae": float(np.mean(np.abs(e))),
        "rmse": float(np.sqrt(np.mean(e**2))),
        "mape": float(np.mean(np.abs(e / real.values)) * 100),
    }


def comparar(serie: pd.Series, prueba: int = PRUEBA) -> tuple[pd.DataFrame, dict]:
    """Ajusta los cuatro modelos con entrenamiento y los evalúa en los últimos `prueba` meses."""
    entrenamiento, test = serie.iloc[:-prueba], serie.iloc[-prueba:]
    filas, predicciones = [], {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)
        for nombre in MODELOS:
            modelo = ajustar(nombre, entrenamiento)
            pred = pronosticar(modelo, prueba)
            pred.index = test.index
            predicciones[nombre] = pred
            detalle = f"orden {modelo.model.order}" if nombre == "ARIMA" else ""
            filas.append({"modelo": nombre, **errores(test, pred["valor"]), "aic": float(modelo.aic), "detalle": detalle})
    tabla = pd.DataFrame(filas).sort_values(["rmse", "mae"]).reset_index(drop=True)
    tabla["elegido"] = tabla.index == 0
    return tabla.round(3), predicciones


def construir_pronostico(datos=DATA, horizonte: int = HORIZONTE) -> pd.DataFrame:
    serie = serie_indice(datos)
    tabla, _ = comparar(serie)
    elegido = tabla.loc[tabla["elegido"], "modelo"].iloc[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo = ajustar(elegido, serie)
        futuro = pronosticar(modelo, horizonte)
    observado = pd.DataFrame({"mes": serie.index.strftime("%Y-%m"), "valor": serie.values, "tipo": "observado"})
    pron = pd.DataFrame(
        {
            "mes": futuro.index.strftime("%Y-%m"),
            "valor": futuro["valor"].values,
            "tipo": "pronostico",
            "li_95": futuro["li"].values,
            "ls_95": futuro["ls"].values,
        }
    )
    salida = pd.concat([observado, pron], ignore_index=True)
    salida["modelo"] = elegido
    (datos / "oro").mkdir(parents=True, exist_ok=True)
    salida.round(2).to_csv(datos / "oro" / "pronostico.csv", index=False)
    tabla.to_csv(datos / "oro" / "comparacion_modelos.csv", index=False)
    return tabla


if __name__ == "__main__":
    print(construir_pronostico().to_string(index=False))
    print(pd.read_csv(DATA / "oro" / "pronostico.csv").tail(HORIZONTE + 1).to_string(index=False))
