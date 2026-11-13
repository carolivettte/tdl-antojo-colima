"""Puerta de calidad 1 (bronce -> plata): esquemas de validación con Pandera.

Cada regla lleva un mensaje en español que se guarda como motivo de rechazo
cuando un registro va a cuarentena. Revisa: esquema, tipos, rangos, unicidad
y reglas de negocio.
"""
import pandera.pandas as pa

from pipeline.catalogos import LATITUD, LONGITUD, MUNICIPIOS, PRECIO_KG, PRODUCTOS_SNIIM, TAMANO, TIPO_NEGOCIO

INSUMOS = sorted({v[0] for v in PRODUCTOS_SNIIM.values()})
P_MIN, P_MAX = PRECIO_KG


def _precio(nombre):
    return pa.Column(
        float,
        [
            pa.Check.in_range(P_MIN, P_MAX, error=f"{nombre} fuera del rango plausible ({P_MIN:g} a {P_MAX:g} $/kg)"),
        ],
        nullable=False,
    )


ESQUEMA_SNIIM = pa.DataFrameSchema(
    {
        "fecha": pa.Column("datetime64[ns]", nullable=False),
        "insumo": pa.Column(str, pa.Check.isin(INSUMOS, error="insumo fuera del catálogo del observatorio")),
        "tipo": pa.Column(str, pa.Check.isin(["fruta", "verdura", "chile"], error="tipo de insumo desconocido")),
        "presentacion": pa.Column(str, pa.Check.eq("Kilogramo", error="presentación distinta de kilogramo")),
        "municipio_clave": pa.Column(str, pa.Check.str_matches(r"^06\d{3}$", error="clave de municipio inválida")),
        "precio_min": _precio("precio mínimo"),
        "precio_max": _precio("precio máximo"),
        "precio_frec": _precio("precio frecuente"),
    },
    checks=[
        pa.Check(
            lambda d: (d["precio_min"] <= d["precio_frec"]) & (d["precio_frec"] <= d["precio_max"]),
            error="regla de negocio: debe cumplirse mínimo <= frecuente <= máximo",
        ),
    ],
    unique=["insumo", "fecha", "presentacion", "origen"],
    report_duplicates="all",
    strict=False,
    coerce=False,
)

ESQUEMA_DENUE = pa.DataFrameSchema(
    {
        "clee": pa.Column(str, pa.Check.str_length(min_value=10, error="CLEE incompleta"), unique=True),
        "nombre": pa.Column(str, nullable=False),
        "tipo_negocio": pa.Column(str, pa.Check.isin(list(TIPO_NEGOCIO.values()), error="clase SCIAN fuera del catálogo")),
        "tamano": pa.Column(str, pa.Check.isin(sorted(set(TAMANO.values())), error="estrato de personal desconocido")),
        "municipio": pa.Column(str, pa.Check.isin(list(MUNICIPIOS.values()), error="municipio fuera del estado de Colima")),
        "municipio_clave": pa.Column(str, pa.Check.str_matches(r"^06\d{3}$", error="clave de municipio inválida")),
        "latitud": pa.Column(float, pa.Check.in_range(*LATITUD, error="latitud fuera del estado de Colima")),
        "longitud": pa.Column(float, pa.Check.in_range(*LONGITUD, error="longitud fuera del estado de Colima")),
    },
    strict=False,
    coerce=False,
)
