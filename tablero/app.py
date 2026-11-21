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
import pydeck as pdk
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"
AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#8a8984"


def frase_cliente(ultimo: pd.Series, siguiente: pd.Series) -> str:
    """Explica el pronóstico y su intervalo en palabras del taquero."""
    cambio = (siguiente["valor"] / ultimo["valor"] - 1) * 100
    direccion = "más" if cambio >= 0 else "menos"
    texto = (
        f"**Para {siguiente['mes']}** esperamos que tus insumos cuesten alrededor de **{abs(cambio):.0f} % {direccion}** "
        f"que en {ultimo['mes']}. Con 95 % de confianza, el índice quedará entre {siguiente['li_95']:.0f} y "
        f"{siguiente['ls_95']:.0f} (en {ultimo['mes']} estuvo en {ultimo['valor']:.0f}). "
    )
    if siguiente["ls_95"] < ultimo["valor"]:
        return texto + "Es muy probable que baje: **buen momento para una promoción**."
    if siguiente["li_95"] > ultimo["valor"]:
        return texto + "Es muy probable que suba: **cuida tus precios** antes de que te coma el margen."
    return texto + (
        "El rango incluye subir y bajar, así que la dirección no es segura: usa el valor central como guía, "
        "no como promesa, y revisa la pestaña Insumos para ver qué producto se está moviendo."
    )


st.set_page_config(page_title="Observatorio Antojo Colima", layout="wide")


@st.cache_data(ttl=3600)
def leer(ruta: str, **kw) -> pd.DataFrame:
    p = DATA / ruta
    return pd.read_csv(p, **kw) if p.exists() else pd.DataFrame()


indice = leer("oro/indice_costo_taco.csv")
precios = leer("oro/precios_mensuales.csv")
competencia = leer("oro/competencia_municipio.csv", dtype={"municipio_clave": str})
geo_mun = leer("oro/geo_municipios.csv", dtype={"municipio_clave": str})
geo_zonas = leer("oro/geo_zonas.csv", dtype={"municipio_clave": str})
geo_puntos = leer("oro/geo_puntos.csv", dtype={"municipio_clave": str})
reporte_geo = (
    json.loads((DATA / "plata/reporte_geo.json").read_text(encoding="utf-8"))
    if (DATA / "plata/reporte_geo.json").exists()
    else {}
)
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
    if len(sig):
        s0 = sig.iloc[0]
        lectura = (
            "Promoción"
            if s0["ls_95"] < ult["indice"]
            else ("Cuidar precio" if s0["li_95"] > ult["indice"] else "Sin señal clara")
        )
    else:
        lectura = "Promoción" if ult["variacion_mensual_pct"] < 0 else "Cuidar precio"
    c4.metric(
        "Lectura",
        lectura,
        help="Promoción: con 95 % de confianza la canasta baja. Cuidar precio: con 95 % de confianza sube. "
        "Sin señal clara: el intervalo incluye subir y bajar.",
    )

tab_pron, tab_ins, tab_comp, tab_mapa, tab_cal = st.tabs(["Pronóstico", "Insumos", "Competencia", "Mapa", "Calidad de datos"])

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
            .mark_line(
                color=NARANJA, strokeWidth=2, strokeDash=[6, 3], point=alt.OverlayMarkDef(size=60, color=NARANJA, filled=True)
            )
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
        if len(pro):
            st.info(frase_cliente(obs.iloc[-1], pro.iloc[0]))
        if len(modelos):
            st.markdown("**Selección del modelo por error en los 12 meses de prueba** (se elige el de menor RMSE)")
            columnas = [c for c in ["modelo", "mae", "rmse", "mape", "detalle", "elegido"] if c in modelos.columns]
            st.dataframe(modelos.sort_values("rmse")[columnas].fillna(""), hide_index=True, use_container_width=True)
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
        st.caption(
            "Negocios de preparación de alimentos registrados en el DENUE (INEGI) por municipio. El DENUE solo cuenta "
            "establecimientos fijos y semifijos: los puestos ambulantes no aparecen, así que la competencia real es mayor. "
            "La pestaña Mapa muestra dónde es más probable que existan."
        )

# ---------------- Mapa (fuente geoespacial, E2) ----------------
# Paleta categórica validada (orden fijo) y rampa secuencial de un solo tono para magnitudes.
COLOR_PUNTO = {
    "taqueria_fija": ("Taquería fija", "#2a78d6"),
    "taqueria_semifija": ("Taquería semifija", "#eb6834"),
    "escuela": ("Escuela", "#1baf7a"),
    "salud": ("Centro de salud u hospital", "#eda100"),
}
RAMPA = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
COLOR_ZONA = {"baja": "#86b6ef", "media": "#2a78d6", "alta": "#104281", "afluencia insuficiente": "#c3c2b7"}


def rgb(hexa: str, alfa: int = 210) -> list[int]:
    return [int(hexa[i : i + 2], 16) for i in (1, 3, 5)] + [alfa]


def leyenda(items: list[tuple[str, str]]) -> None:
    st.markdown(
        " &nbsp; ".join(
            f"<span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{c};"
            f"margin-right:4px'></span>{t}"
            for t, c in items
        ),
        unsafe_allow_html=True,
    )


VISTA = pdk.ViewState(latitude=19.1, longitude=-103.95, zoom=8.3)

with tab_mapa:
    if not len(geo_mun):
        st.info("Todavía no hay capa geoespacial: corre `python -m scripts.captura geo` y luego el pipeline.")
    else:
        capa = st.radio(
            "Qué ver",
            ["Zonas de 1 km", "Puntos", "Municipios"],
            horizontal=True,
            help="Zonas: afluencia contra competencia registrada. Puntos: cada negocio o escuela, sin nombres. "
            "Municipios: densidades por km² con los límites del Marco Geoestadístico.",
        )
        if capa == "Zonas de 1 km":
            z = geo_zonas[geo_zonas["categoria_zona"].isin(COLOR_ZONA)].copy()
            z["color"] = z["categoria_zona"].map(lambda c: rgb(COLOR_ZONA[c], 190))
            capa_pdk = pdk.Layer(
                "ScatterplotLayer",
                z,
                get_position="[longitud, latitud]",
                get_fill_color="color",
                get_radius=480,
                stroked=True,
                get_line_color=[252, 252, 251, 255],
                line_width_min_pixels=1,
                pickable=True,
            )
            tooltip = {
                "html": "<b>Zona {celda}</b><br/>Categoría: <b>{categoria_zona}</b><br/>Escuelas: {escuela} · "
                "Salud: {salud}<br/>Taquerías registradas: {taquerias_registradas} "
                "(semifijas {taqueria_semifija})<br/>Presión de demanda: {presion_demanda}"
            }
            leyenda(
                [
                    (f"Oportunidad {k}" if k in ("baja", "media", "alta") else "1–2 escuelas/clínicas (sin clasificar)", v)
                    for k, v in COLOR_ZONA.items()
                ]
            )
            st.caption(
                "Cada círculo es una celda de 1 km con al menos una escuela o centro de salud; las celdas con menos de 3 "
                "quedan en gris sin clasificar, para que un par de escuelas aisladas no parezcan zona caliente. "
                "**Alta** = mucha afluencia por cada taquería registrada: zona probable de competencia no registrada "
                "(ambulantes) **o** de oportunidad. Es un índice relativo por terciles, no un conteo de puestos."
            )
        elif capa == "Puntos":
            elegir = st.multiselect(
                "Capas",
                list(COLOR_PUNTO),
                default=["taqueria_semifija", "escuela", "salud"],
                format_func=lambda k: COLOR_PUNTO[k][0],
            )
            p = geo_puntos[geo_puntos["categoria"].isin(elegir)].copy()
            p["color"] = p["categoria"].map(lambda c: rgb(COLOR_PUNTO[c][1]))
            p["etiqueta"] = p["categoria"].map(lambda c: COLOR_PUNTO[c][0])
            capa_pdk = pdk.Layer(
                "ScatterplotLayer",
                p,
                get_position="[longitud, latitud]",
                get_fill_color="color",
                get_radius=90,
                radius_min_pixels=3,
                stroked=True,
                get_line_color=[252, 252, 251, 255],
                line_width_min_pixels=1,
                pickable=True,
            )
            tooltip = {"html": "<b>{etiqueta}</b><br/>{municipio_marco}<br/>CLEE {clee}"}
            leyenda([COLOR_PUNTO[k] for k in elegir])
            st.caption("Sin nombres ni domicilios: solo la clave del DENUE (CLEE), la categoría y la coordenada.")
        else:
            metricas = {
                "taquerias_km2": "Taquerías por km²",
                "afluencia_km2": "Escuelas y centros de salud por km²",
                "afluencia_por_taqueria": "Afluencia por taquería registrada",
                "pct_semifijas": "% de taquerías semifijas",
            }
            m = st.selectbox("Indicador", list(metricas), format_func=metricas.get)
            gj = json.loads((DATA / "oro/geo_municipios.geojson").read_text(encoding="utf-8"))
            valores = pd.Series([f["properties"].get(m) for f in gj["features"]], dtype=float)
            cortes = valores.quantile([0.2, 0.4, 0.6, 0.8]).tolist()
            for f, v in zip(gj["features"], valores, strict=True):
                paso = sum(v > c for c in cortes) if pd.notna(v) else 0
                f["properties"]["color"] = rgb(RAMPA[paso], 200)
                f["properties"]["valor"] = "s/d" if pd.isna(v) else f"{v:,.2f}"
            capa_pdk = pdk.Layer(
                "GeoJsonLayer",
                gj,
                get_fill_color="properties.color",
                get_line_color=[252, 252, 251, 255],
                line_width_min_pixels=2,
                pickable=True,
            )
            tooltip = {"html": f"<b>{{nomgeo}}</b><br/>{metricas[m]}: {{valor}}"}
            st.caption(f"{metricas[m]}: más oscuro = mayor (quintiles). Límites: INEGI, Marco Geoestadístico.")
        st.pydeck_chart(
            pdk.Deck(
                layers=[capa_pdk],
                initial_view_state=VISTA,
                map_provider="carto",
                map_style="light",
                tooltip={**tooltip, "style": {"backgroundColor": "#fcfcfb", "color": "#0b0b0b", "fontSize": "12px"}},
            ),
            use_container_width=True,
        )
        if reporte_geo:
            v = reporte_geo.get("validacion_indice", {})
            r = reporte_geo.get("radio", {})
            g1, g2, g3 = st.columns(3)
            g1.metric("Puntos dentro de un municipio", f"{reporte_geo['puntos_dentro_de_algun_municipio']:,}")
            g2.metric("Escuelas/clínicas con taquería a 1 km", f"{r.get('pct_con_taqueria', 0)}%")
            g3.metric("Spearman afluencia vs semifijas", v.get("spearman_afluencia_vs_semifijas", "s/d"))
        st.markdown("**Tabla por municipio**")
        st.dataframe(
            geo_mun.drop(columns=["fuente", "archivos_bronce", "capturado_utc"], errors="ignore"),
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "Sesgo declarado: el DENUE registra negocios fijos y semifijos, no ambulantes. No inventamos puestos; "
            "la afluencia (escuelas y centros de salud) indica dónde es probable que existan. "
            "Detalle en docs/etica-datos.md."
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
        objetivo = fiab["objetivo"]
        f0, f1, f2, f3, f4 = st.columns(5)
        if fiab.get("tasa_exito_ejecucion") is not None:
            f0.metric(
                "Éxito por ejecución",
                f"{fiab['tasa_exito_ejecucion'] * 100:.1f}%",
                f"{fiab['ejecuciones_exitosas']} de {fiab['ejecuciones_totales']}",
                delta_color="off",
            )
        f1.metric(
            "Éxito por día",
            f"{fiab['tasa_exito'] * 100:.1f}%",
            f"{fiab['dias_exitosos']} de {fiab['dias_esperados']} días",
            delta_color="off",
        )
        f2.metric("MTBF", f"{fiab['mtbf_h']} h" if fiab["mtbf_h"] else "sin fallas")
        f3.metric("MTTR", f"{fiab['mttr_h']} h")
        f4.metric("Disponibilidad A", f"{fiab['disponibilidad'] * 100:.1f}%", f"objetivo ≥ {objetivo:.0%}", delta_color="off")
        st.caption(
            f"Objetivo de E0: éxito ≥ {objetivo:.0%}. La captura programada opera desde el {fiab['periodo']['desde']}; "
            "A = MTBF / (MTBF + MTTR). Se recalcula con la bitácora en cada captura."
        )
        st.dataframe(pd.DataFrame(fiab["dias"]), hide_index=True, use_container_width=True)
