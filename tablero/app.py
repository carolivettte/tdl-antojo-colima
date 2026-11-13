"""Tablero del Observatorio Antojo Colima (capa oro).

Correr en local:
    pip install -r tablero/requirements.txt
    streamlit run tablero/app.py

Lee solo archivos de data/oro, data/plata, data/cuarentena y data/bitacora; no consulta fuentes.
El pronóstico lo produce el cuaderno de pronóstico en data/oro/pronostico.csv y
data/oro/comparacion_modelos.csv (contrato en docs/E1/diccionario_oro.md).
"""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"
AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#8a8984"

st.set_page_config(page_title="Observatorio Antojo Colima", layout="wide")


@st.cache_data(ttl=3600)
def leer(ruta: str, **kw) -> pd.DataFrame:
    p = DATA / ruta
    return pd.read_csv(p, **kw) if p.exists() else pd.DataFrame()


indice = leer("oro/indice_costo_taco.csv")
precios = leer("oro/precios_mensuales.csv")
competencia = leer("oro/competencia_municipio.csv", dtype={"municipio_clave": str})
pronostico = leer("oro/pronostico.csv")
modelos = leer("oro/comparacion_modelos.csv")
cuarentena = leer("cuarentena/sniim_cuarentena.csv")
puerta = (
    json.loads((DATA / "plata/reporte_puerta.json").read_text(encoding="utf-8"))
    if (DATA / "plata/reporte_puerta.json").exists()
    else []
)
fiab = (
    json.loads((DATA / "bitacora/fiabilidad.json").read_text(encoding="utf-8"))
    if (DATA / "bitacora/fiabilidad.json").exists()
    else {}
)

st.title("Observatorio Antojo Colima")
st.caption(
    "¿Cuándo conviene promoción y cuándo subir precio? "
    "Precios de insumos del SNIIM (Centros de distribución de Colima) y competencia del DENUE."
)

# ---------------- Resumen ----------------
if len(indice):
    # Se resume el último mes COMPLETO: el pronóstico no usa el mes en curso, así que el resumen tampoco.
    meses_obs = pronostico.loc[pronostico["tipo"] == "observado", "mes"] if len(pronostico) else indice["mes"]
    ult = indice[indice["mes"] == meses_obs.iloc[-1]].iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        f"Índice de Costo del Taco ({ult['mes']})",
        f"{ult['indice']:.1f}",
        f"{ult['variacion_mensual_pct']:+.1f}% vs mes anterior",
        delta_color="inverse",
    )
    c2.metric(
        "Costo de la canasta (1 kg c/u)",
        f"${ult['costo_canasta_kg']:,.0f}",
        f"{ult['variacion_anual_pct']:+.1f}% anual",
        delta_color="inverse",
    )
    if len(pronostico):
        sig = pronostico[pronostico["tipo"] == "pronostico"].head(1)
        if len(sig):
            s = sig.iloc[0]
            c3.metric(
                f"Pronóstico {s['mes']}", f"{s['valor']:.1f}", f"{s['valor'] - ult['indice']:+.1f} puntos", delta_color="inverse"
            )
    sig = pronostico[pronostico["tipo"] == "pronostico"] if len(pronostico) else pd.DataFrame()
    cambio = sig["valor"].iloc[0] - ult["indice"] if len(sig) else ult["variacion_mensual_pct"]
    c4.metric(
        "Lectura",
        "Promoción" if cambio < 0 else "Cuidar precio",
        help="Si se espera que la canasta baje, hay margen para promoción; si se espera que suba, conviene cuidar el precio. "
        "Revisa el intervalo: si es muy ancho, la señal es débil.",
    )

tab_pron, tab_ins, tab_comp, tab_cal = st.tabs(["Pronóstico", "Insumos", "Competencia", "Calidad de datos"])

# ---------------- Pronóstico ----------------
with tab_pron:
    st.subheader("Índice de Costo del Taco y pronóstico (base 2021 = 100)")
    if len(pronostico):
        obs = pronostico[pronostico["tipo"] == "observado"]
        pro = pronostico[pronostico["tipo"] == "pronostico"]
        # la línea del pronóstico arranca en el último mes observado para que se vea continua
        pro_linea = pd.concat([obs.tail(1), pro], ignore_index=True)
        pro_linea["li_95"] = pro_linea["li_95"].fillna(pro_linea["valor"])
        pro_linea["ls_95"] = pro_linea["ls_95"].fillna(pro_linea["valor"])
        base = (
            alt.Chart(obs)
            .mark_line(color=AZUL, strokeWidth=2)
            .encode(
                x=alt.X("mes:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
                y=alt.Y("valor:Q", title="Índice", scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("mes:T", format="%Y-%m"), alt.Tooltip("valor:Q", format=".1f", title="observado")],
            )
        )
        banda = alt.Chart(pro_linea).mark_area(color=NARANJA, opacity=0.18).encode(x="mes:T", y="li_95:Q", y2="ls_95:Q")
        linea = (
            alt.Chart(pro_linea)
            .mark_line(color=NARANJA, strokeWidth=2, strokeDash=[6, 3], point=alt.OverlayMarkDef(size=60))
            .encode(
                x="mes:T",
                y="valor:Q",
                tooltip=[
                    alt.Tooltip("mes:T", format="%Y-%m"),
                    alt.Tooltip("valor:Q", format=".1f", title="pronóstico"),
                    alt.Tooltip("li_95:Q", format=".1f", title="límite inferior 95%"),
                    alt.Tooltip("ls_95:Q", format=".1f", title="límite superior 95%"),
                ],
            )
        )
        st.altair_chart((banda + base + linea).properties(height=360), use_container_width=True)
        modelo = pro["modelo"].iloc[0] if len(pro) else ""
        st.caption(f"Azul: observado. Naranja punteado: pronóstico del modelo **{modelo}** con intervalo de 95%.")
        if len(modelos):
            st.markdown("**Selección del modelo por error en los 12 meses de prueba** (se elige el de menor RMSE)")
            columnas = [c for c in ["modelo", "mae", "rmse", "mape", "detalle", "elegido"] if c in modelos.columns]
            st.dataframe(modelos.sort_values("rmse")[columnas], hide_index=True, use_container_width=True)
    elif len(indice):
        st.info("Aún no hay pronóstico publicado (data/oro/pronostico.csv). Se muestra la serie observada.")
        st.altair_chart(
            alt.Chart(indice)
            .mark_line(color=AZUL, strokeWidth=2)
            .encode(
                x=alt.X("mes:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
                y=alt.Y("indice:Q", title="Índice", scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("mes:T", format="%Y-%m"), alt.Tooltip("indice:Q", format=".1f")],
            )
            .properties(height=360),
            use_container_width=True,
        )

# ---------------- Insumos ----------------
with tab_ins:
    if len(precios):
        insumo = st.selectbox("Insumo", sorted(precios["insumo"].unique()))
        d = precios[precios["insumo"] == insumo]
        lineas = (
            alt.Chart(d)
            .mark_line(color=AZUL, strokeWidth=2)
            .encode(
                x=alt.X("mes:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
                y=alt.Y("precio_mediana:Q", title="MXN por kg"),
                tooltip=[
                    alt.Tooltip("mes:T", format="%Y-%m"),
                    alt.Tooltip("precio_mediana:Q", format="$.2f", title="mediana"),
                    "n_registros:Q",
                    "n_atipicos:Q",
                    "metodo:N",
                ],
            )
        )
        imputados = (
            alt.Chart(d[d["imputado"]])
            .mark_point(color=GRIS, size=70, filled=False, strokeWidth=2)
            .encode(x="mes:T", y="precio_mediana:Q")
        )
        st.altair_chart((lineas + imputados).properties(height=340), use_container_width=True)
        st.caption("Mediana mensual del precio frecuente. Círculos grises: meses sin publicación, rellenados por interpolación.")

# ---------------- Competencia ----------------
with tab_comp:
    if len(competencia):
        tipo = st.selectbox(
            "Tipo de negocio", sorted(competencia["tipo_negocio"].dropna().unique()), index=None, placeholder="Todos"
        )
        d = competencia if tipo is None else competencia[competencia["tipo_negocio"] == tipo]
        d = d.groupby("municipio", as_index=False)["negocios"].sum()
        st.altair_chart(
            alt.Chart(d)
            .mark_bar(color=AZUL, cornerRadiusEnd=4, size=18)
            .encode(
                x=alt.X("negocios:Q", title="Negocios (DENUE)"),
                y=alt.Y("municipio:N", sort="-x", title=None),
                tooltip=["municipio:N", "negocios:Q"],
            )
            .properties(height=320),
            use_container_width=True,
        )

# ---------------- Calidad ----------------
with tab_cal:
    st.subheader("Puerta de calidad (bronce → plata)")
    if puerta:
        cols = st.columns(len(puerta))
        for col, r in zip(cols, puerta, strict=True):
            col.metric(f"{r['fuente'].upper()} · validez", f"{r['tasa_validez'] * 100:.2f}%")
            col.caption(
                f"{r['registros_bronce']:,} en bronce · {r['duplicados_exactos_resueltos']} duplicados resueltos · "
                f"{r['validos_plata']:,} a plata · {r['cuarentena']} a cuarentena"
            )
    if len(cuarentena):
        st.markdown("**Registros en cuarentena y su motivo**")
        st.dataframe(
            cuarentena[["motivo", "fecha", "producto_sniim", "precio_min", "precio_frec", "precio_max", "archivo_origen"]],
            hide_index=True,
            use_container_width=True,
        )
    if fiab:
        st.subheader("Fiabilidad de la captura diaria")
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Tasa de éxito", f"{fiab['tasa_exito'] * 100:.1f}%", help=f"Objetivo ≥ {fiab['objetivo']:.0%}")
        f2.metric("MTBF", f"{fiab['mtbf_h']} h" if fiab["mtbf_h"] else "sin fallas")
        f3.metric("MTTR", f"{fiab['mttr_h']} h")
        f4.metric("Disponibilidad", f"{fiab['disponibilidad'] * 100:.1f}%")
        st.dataframe(pd.DataFrame(fiab["dias"]), hide_index=True, use_container_width=True)
