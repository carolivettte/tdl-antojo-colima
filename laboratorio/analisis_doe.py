"""Análisis estadístico de los diseños de E2 (lo usa laboratorio/E2_experimento.ipynb).

Todo lo que se reporta sale de laboratorio/resultados/*.csv: no hay números escritos a mano.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

RESULTADOS = Path(os.environ.get("DOE_RESULTADOS", Path(__file__).resolve().parent / "resultados"))
NOMBRES = {"procesos": "A", "parser": "B", "formato": "C", "lote": "D"}
ALFA = 0.05


def cargar(diseno: str) -> pd.DataFrame:
    df = pd.read_csv(RESULTADOS / f"{diseno}.csv")
    df["bloque"] = df["bloque"].astype(str)
    return df


# ------------------------------------------------------------------ 2^k con réplicas y bloques


def modelo_2k(df: pd.DataFrame, factores: list[str], respuesta: str = "tiempo_s", bloques: bool = True):
    termino = " * ".join(factores)
    formula = f"{respuesta} ~ {termino}" + (" + C(bloque, Sum)" if bloques else "")
    return smf.ols(formula, data=df).fit()


def tabla_anova(modelo) -> pd.DataFrame:
    t = anova_lm(modelo, typ=2)
    t = t.rename(columns={"sum_sq": "SC", "df": "gl", "F": "F0", "PR(>F)": "valor_p"})
    t["CM"] = t["SC"] / t["gl"]
    t.index = [renombrar(i) for i in t.index]
    t["significativo"] = t["valor_p"] < ALFA
    return t[["SC", "gl", "CM", "F0", "valor_p", "significativo"]]


def renombrar(termino: str) -> str:
    if termino.startswith("C(bloque"):
        return "Bloque (sesión)"
    if termino == "Residual":
        return "Error"
    partes = termino.split(":")
    return "".join(NOMBRES.get(p, p) for p in partes) + f" ({' × '.join(partes)})"


def efectos(modelo, factores: list[str]) -> pd.DataFrame:
    """Efecto = 2 × coeficiente en unidades codificadas (-1, +1): cambio medio al pasar de bajo a alto."""
    filas = []
    for k in range(1, len(factores) + 1):
        for combo in itertools.combinations(factores, k):
            nombre = ":".join(combo)
            coef = modelo.params[nombre]
            ee = modelo.bse[nombre]
            filas.append(
                {
                    "termino": "".join(NOMBRES[c] for c in combo),
                    "factores": " × ".join(combo),
                    "efecto": 2 * coef,
                    "error_estandar": 2 * ee,
                    "t0": coef / ee,
                    "valor_p": modelo.pvalues[nombre],
                }
            )
    t = pd.DataFrame(filas)
    t["significativo"] = t["valor_p"] < ALFA
    return t.sort_values("efecto", key=abs, ascending=False).reset_index(drop=True)


def medias_por_combinacion(df: pd.DataFrame, factores: list[str], respuesta: str = "tiempo_s") -> pd.DataFrame:
    valores = [f"{f}_valor" for f in factores]
    g = df.groupby(valores)[respuesta].agg(media="mean", desv="std", n="count").reset_index()
    return g.sort_values("media").reset_index(drop=True)


def prediccion(modelo, combinacion: dict, nuevas: int = 5) -> dict:
    """Media predicha (promediando bloques) y su intervalo de predicción al 95 % para la media de `nuevas` corridas.

    Con la codificación Sum de los bloques, poner sus columnas en 0 da la media marginal sobre las sesiones.
    """
    datos = modelo.model.data.frame
    coincide = np.ones(len(datos), dtype=bool)
    for k, v in combinacion.items():
        coincide &= (datos[k] == v).to_numpy()
    if not coincide.any():
        raise ValueError(f"La combinación {combinacion} no está en el diseño")
    x = modelo.model.exog[np.argmax(coincide)].copy()
    nombres = modelo.model.exog_names
    x[[i for i, n in enumerate(nombres) if n.startswith("C(bloque")]] = 0.0
    media = float(x @ modelo.params.to_numpy())
    var_media = float(x @ modelo.cov_params().to_numpy() @ x)
    var_pred = var_media + modelo.mse_resid / nuevas
    t = stats.t.ppf(0.975, modelo.df_resid)
    return {
        "media_predicha": media,
        "li_95": media - t * np.sqrt(var_pred),
        "ls_95": media + t * np.sqrt(var_pred),
        "gl_error": int(modelo.df_resid),
    }


def _fila_codificada(modelo, combinacion: dict) -> np.ndarray:
    datos = modelo.model.data.frame
    coincide = np.ones(len(datos), dtype=bool)
    for k, v in combinacion.items():
        coincide &= (datos[k] == v).to_numpy()
    x = modelo.model.exog[np.argmax(coincide)].copy()
    x[[i for i, n in enumerate(modelo.model.exog_names) if n.startswith("C(bloque")]] = 0.0
    return x


def razon_predicha(modelo_log, base: dict, mejor: dict, nuevas: int = 5) -> dict:
    """Con el modelo en log(tiempo): cuántas veces más rápida es `mejor` que `base`.

    La razón no depende del bloque (en escala log el bloque es aditivo y se cancela), por eso es lo que se
    puede confirmar en una sesión nueva. Devuelve el IC 95 % de la razón media y el intervalo de predicción
    95 % para la razón entre las medias geométricas de `nuevas` corridas de cada configuración.
    """
    d = _fila_codificada(modelo_log, base) - _fila_codificada(modelo_log, mejor)
    est = float(d @ modelo_log.params.to_numpy())
    var = float(d @ modelo_log.cov_params().to_numpy() @ d)
    t = stats.t.ppf(0.975, modelo_log.df_resid)
    var_pred = var + 2 * modelo_log.mse_resid / nuevas
    return {
        "razon": float(np.exp(est)),
        "ic95": (float(np.exp(est - t * np.sqrt(var))), float(np.exp(est + t * np.sqrt(var)))),
        "ip95": (float(np.exp(est - t * np.sqrt(var_pred))), float(np.exp(est + t * np.sqrt(var_pred)))),
        "reduccion_pct": float(100 * (1 - np.exp(-est))),
        "ic95_reduccion_pct": (
            float(100 * (1 - np.exp(-(est - t * np.sqrt(var))))),
            float(100 * (1 - np.exp(-(est + t * np.sqrt(var))))),
        ),
    }


def razones_por_bloque(df: pd.DataFrame, base: dict, mejor: dict, respuesta: str = "tiempo_s") -> pd.DataFrame:
    """Razón actual/mejor dentro de cada bloque (misma sesión)."""

    def media(g, cfg):
        m = np.ones(len(g), dtype=bool)
        for k, v in cfg.items():
            m &= g[f"{k}_valor"].astype(str) == str(v)
        return g.loc[m, respuesta].mean()

    filas = []
    for b, g in df.groupby("bloque"):
        a, m = media(g, base), media(g, mejor)
        filas.append({"bloque": b, "sesion": g["sesion"].iloc[0], "actual_s": a, "mejor_s": m, "veces_mas_rapido": a / m})
    return pd.DataFrame(filas)


def mejora(df: pd.DataFrame, base: dict, mejor: dict, respuesta: str = "tiempo_s") -> dict:
    """Tamaño de la mejora entre la configuración actual y la mejor, con IC 95 % (Welch)."""

    def filtrar(cfg):
        m = np.ones(len(df), dtype=bool)
        for k, v in cfg.items():
            m &= df[f"{k}_valor"].astype(str) == str(v)
        return df.loc[m, respuesta]

    a, b = filtrar(base), filtrar(mejor)
    dif = a.mean() - b.mean()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    gl = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
    t = stats.t.ppf(0.975, gl)
    return {
        "media_actual": a.mean(),
        "media_mejor": b.mean(),
        "reduccion_s": dif,
        "reduccion_pct": 100 * dif / a.mean(),
        "ic95_reduccion_s": (dif - t * np.sqrt(va + vb), dif + t * np.sqrt(va + vb)),
        "veces_mas_rapido": a.mean() / b.mean(),
        "n": (len(a), len(b)),
    }


def supuestos(modelo, tratamientos: list[str]) -> dict:
    """Normalidad (Shapiro-Wilk), varianza constante entre tratamientos (Levene) e independencia (Durbin-Watson
    con los residuos en el orden en que se corrieron)."""
    from statsmodels.stats.stattools import durbin_watson

    datos = modelo.model.data.frame.assign(_r=modelo.resid)
    sw = stats.shapiro(datos["_r"])
    grupos = [g["_r"].to_numpy() for _, g in datos.groupby(tratamientos) if len(g) > 1]
    lev = stats.levene(*grupos, center="median") if len(grupos) > 1 else None
    orden = datos.sort_values(["bloque", "orden"])["_r"] if "orden" in datos else datos["_r"]
    return {
        "shapiro_W": float(sw.statistic),
        "shapiro_p": float(sw.pvalue),
        "levene_p": float(lev.pvalue) if lev else float("nan"),
        "durbin_watson": float(durbin_watson(orden)),
    }


# ------------------------------------------------------------------ bifactorial con 3 niveles


def modelo_bifactorial(df: pd.DataFrame, respuesta: str = "tiempo_s"):
    d = df.assign(procesos=df["procesos_valor"].astype(str), parser=df["parser_valor"])
    return smf.ols(f"{respuesta} ~ C(procesos) * C(parser) + C(bloque, Sum)", data=d).fit()


def tabla_anova_bifactorial(modelo) -> pd.DataFrame:
    t = anova_lm(modelo, typ=2).rename(columns={"sum_sq": "SC", "df": "gl", "F": "F0", "PR(>F)": "valor_p"})
    t["CM"] = t["SC"] / t["gl"]
    nombres = {
        "C(procesos)": "Procesos (1, 2, 4)",
        "C(parser)": "Parser",
        "C(procesos):C(parser)": "Procesos × parser",
        "C(bloque, Sum)": "Bloque (sesión)",
        "Residual": "Error",
    }
    t.index = [nombres.get(i, i) for i in t.index]
    t["significativo"] = t["valor_p"] < ALFA
    return t[["SC", "gl", "CM", "F0", "valor_p", "significativo"]]


def tukey_procesos(df: pd.DataFrame, parser: str, respuesta: str = "tiempo_s"):
    """Tukey HSD entre niveles de procesos sobre log(tiempo) ajustado por bloque.

    Se resta a cada corrida la media de su bloque (en log): así la variación entre sesiones no infla el error
    de la comparación, igual que en el ANOVA con bloques.
    """
    d = df[df["parser_valor"] == parser].copy()
    d["_log"] = np.log(d[respuesta])
    d["_ajustado"] = d["_log"] - d.groupby("bloque")["_log"].transform("mean") + d["_log"].mean()
    return pairwise_tukeyhsd(d["_ajustado"], d["procesos_valor"].astype(str), alpha=ALFA)


# ------------------------------------------------------------------ 2^4 contra 2^(4-1)


def estructura_alias() -> pd.DataFrame:
    """Alias de la media fracción con generador D = ABC (relación de definición I = ABCD)."""
    letras = "ABCD"
    terminos = ["".join(c) for k in range(1, 5) for c in itertools.combinations(letras, k)]
    vistos, filas = set(), []
    for t in terminos:
        if t in vistos:
            continue
        alias = "".join(sorted(set(t) ^ set("ABCD")))
        vistos |= {t, alias}
        filas.append({"efecto": t, "alias": alias or "I", "orden": f"{len(t)} con {len(alias)}" if alias else "—"})
    return pd.DataFrame(filas)


def efectos_sin_replica(df: pd.DataFrame, factores: list[str], respuesta: str = "tiempo_s") -> pd.DataFrame:
    """Efectos por contrastes (una sola réplica) y su significancia con el método de Lenth."""
    X = df[factores].to_numpy()
    y = df[respuesta].to_numpy()
    filas = []
    for k in range(1, len(factores) + 1):
        for combo in itertools.combinations(range(len(factores)), k):
            signo = np.prod(X[:, combo], axis=1)
            efecto = (y[signo == 1].mean() - y[signo == -1].mean()) if len(np.unique(signo)) > 1 else np.nan
            filas.append({"termino": "".join(NOMBRES[factores[i]] for i in combo), "efecto": efecto})
    t = pd.DataFrame(filas).dropna()
    abs_ef = t["efecto"].abs()
    s0 = 1.5 * abs_ef.median()
    pse = 1.5 * abs_ef[abs_ef < 2.5 * s0].median()
    m = len(t)
    t_me = stats.t.ppf(1 - ALFA / 2, m / 3)
    t["ME_lenth"] = t_me * pse
    t["significativo_lenth"] = abs_ef > t["ME_lenth"]
    return t.sort_values("efecto", key=abs, ascending=False).reset_index(drop=True)


def comparar_completo_vs_fraccion(df4: pd.DataFrame, respuesta: str = "tiempo_s") -> pd.DataFrame:
    factores = ["procesos", "parser", "formato", "lote"]
    completo = efectos_sin_replica(df4, factores, respuesta).set_index("termino")
    fr = df4[df4["en_media_fraccion"]]
    fraccion = efectos_sin_replica(fr, factores, respuesta)
    # En la fracción, cada contraste estima la suma de un efecto y su alias: se queda el de menor orden.
    alias = {r.efecto: r.alias for r in estructura_alias().itertuples()}
    fraccion = fraccion[fraccion["termino"].map(lambda t: t in alias)].set_index("termino")
    filas = []
    for t, r in fraccion.iterrows():
        a = alias[t]
        filas.append(
            {
                "contraste": f"{t} + {a}" if a != "I" else t,
                "estimado_2k4-1": r["efecto"],
                "efecto_2k4": completo.loc[t, "efecto"],
                "alias_en_2k4": completo.loc[a, "efecto"] if a in completo.index else 0.0,
            }
        )
    out = pd.DataFrame(filas)
    out["suma_2k4"] = out["efecto_2k4"] + out["alias_en_2k4"]
    out["diferencia"] = out["estimado_2k4-1"] - out["suma_2k4"]
    return out.sort_values("estimado_2k4-1", key=abs, ascending=False).reset_index(drop=True)
