"""Pruebas de la puerta de calidad (bronce -> plata) y de la capa oro, con datos sintéticos."""

import pandas as pd

from pipeline.esquemas import ESQUEMA_SNIIM
from pipeline.oro import dim_insumo, indice_costo_taco, precios_mensuales
from pipeline.plata import marcar_atipicos, preparar_sniim, resolver_duplicados, validar

LIMON = "Limón c/semilla # 5 - Primera"
MERCADO = "Colima: Centros de distribución de Colima"


def fila(
    fecha="04/11/2026", producto=LIMON, minimo="18", maximo="22", frec="20", destino=MERCADO, captura="2026-11-09T21:35:09Z"
):
    return {
        "producto": producto,
        "producto_id": "1",
        "fecha": fecha,
        "presentacion": "Kilogramo",
        "origen": "Colima",
        "destino": destino,
        "precio_min": minimo,
        "precio_max": maximo,
        "precio_frec": frec,
        "obs": "",
        "archivo_origen": "prueba.csv",
        "capturado_utc": pd.Timestamp(captura),
    }


def puerta(filas):
    preparado, rechazos = preparar_sniim(pd.DataFrame(filas))
    validos, invalidos = validar(preparado, ESQUEMA_SNIIM)
    return validos, pd.concat([rechazos, invalidos], ignore_index=True)


def test_registro_correcto_pasa_a_plata():
    validos, cuarentena = puerta([fila()])
    assert len(validos) == 1 and len(cuarentena) == 0
    assert validos.iloc[0]["insumo"] == "limon"
    assert validos.iloc[0]["municipio_clave"] == "06002"


def test_cada_rechazo_lleva_motivo():
    filas = [
        fila(fecha="2026-11-04"),  # fecha en formato distinto
        fila(frec=""),  # precio faltante
        fila(producto="Manzana Golden"),  # producto sin equivalencia en el catálogo
        fila(minimo="30", maximo="20"),  # viola mínimo <= frecuente <= máximo
        fila(frec="900", maximo="950"),  # fuera de rango plausible ($/kg)
    ]
    validos, cuarentena = puerta(filas)
    assert len(validos) == 0
    assert len(cuarentena) == 5
    assert cuarentena["motivo"].notna().all()
    assert (cuarentena["motivo"].str.len() > 0).all()


def test_mercado_distinto_va_a_cuarentena():
    _, cuarentena = puerta([fila(destino="Jalisco: Mercado de Abasto de Guadalajara")])
    assert len(cuarentena) == 1


def test_duplicado_exacto_se_resuelve_y_conflicto_va_a_cuarentena():
    filas = [
        fila(captura="2026-11-09T21:00:00Z"),
        fila(captura="2026-11-10T21:00:00Z"),  # misma observación, otra captura
        fila(fecha="05/11/2026", frec="20"),
        fila(fecha="05/11/2026", frec="21", captura="2026-11-10T21:00:00Z"),  # mismo día, otro precio
    ]
    preparado, _ = preparar_sniim(pd.DataFrame(filas))
    unicos, conflictos, exactos = resolver_duplicados(
        preparado, ["insumo", "fecha", "presentacion", "origen"], ["precio_min", "precio_max", "precio_frec"]
    )
    assert exactos == 1
    assert len(unicos) + len(conflictos) == 3
    if len(conflictos):
        assert conflictos["motivo"].notna().all()


def test_atipico_se_marca_pero_no_se_borra():
    fechas = pd.date_range("2026-01-01", periods=30, freq="3D").strftime("%d/%m/%Y")
    filas = [fila(fecha=f, minimo="18", maximo="22", frec="20") for f in fechas]
    filas[-1] = fila(fecha=fechas[-1], minimo="90", maximo="99", frec="95")
    validos, _ = puerta(filas)
    marcado = marcar_atipicos(validos)
    assert len(marcado) == 30
    assert marcado["atipico"].iloc[-1]
    assert marcado["atipico"].sum() == 1


def _plata_sintetica():
    filas = []
    from pipeline.catalogos import PRODUCTOS_SNIIM

    for insumo, _tipo, _canasta in PRODUCTOS_SNIIM.values():
        for mes in ["2021-01", "2021-02", "2021-04"]:  # falta marzo
            filas.append(
                {
                    "fecha": f"{mes}-05",
                    "insumo": insumo,
                    "precio_frec": 20.0,
                    "precio_min": 18.0,
                    "precio_max": 22.0,
                    "atipico": "False",
                }
            )
    return pd.DataFrame(filas)


def test_mes_faltante_se_imputa_y_queda_marcado():
    mensual = precios_mensuales(_plata_sintetica())
    marzo = mensual[mensual["mes"] == "2021-03"]
    assert len(marzo) == len(dim_insumo())
    assert marzo["imputado"].all()
    assert (marzo["metodo"] == "interpolacion_lineal").all()
    assert marzo["precio_mediana"].notna().all()


def test_indice_base_2021_vale_100():
    indice = indice_costo_taco(precios_mensuales(_plata_sintetica()))
    assert indice["indice"].round(6).eq(100).all()
    assert indice.loc[indice["mes"] == "2021-03", "insumos_imputados"].iloc[0] != ""


def test_respaldo_detecta_archivo_alterado(tmp_path):
    import hashlib
    import json
    import zipfile

    from scripts.respaldo import crear, verificar

    bronce = tmp_path / "bronce" / "sniim" / "fecha=2026-11-09"
    bronce.mkdir(parents=True)
    csv = bronce / "sniim_diario_20261109T000000Z.csv"
    csv.write_text("a,b\n1,2\n", encoding="utf-8")
    meta = {"archivo": csv.name, "sha256": hashlib.sha256(csv.read_bytes()).hexdigest()}
    (bronce / "sniim_diario_20261109T000000Z.meta.json").write_text(json.dumps(meta), encoding="utf-8")

    zip_ok = crear(tmp_path / "bronce", tmp_path / "respaldos")
    assert verificar(zip_ok) == {"archivos_verificados": 1, "fallas": []}

    csv.write_text("a,b\n1,999\n", encoding="utf-8")  # alguien modifica el dato crudo
    zip_malo = tmp_path / "respaldos" / "alterado.zip"
    with zipfile.ZipFile(zip_malo, "w") as z:
        for f in (tmp_path / "bronce").rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(tmp_path / "bronce"))
    assert verificar(zip_malo)["fallas"]


def test_pipeline_completo_bronce_a_oro(tmp_path):
    """Integración: bronce sintético -> plata + cuarentena + bitácora -> oro + diccionario."""
    from pipeline.catalogos import PRODUCTOS_SNIIM
    from pipeline.oro import construir_oro
    from pipeline.plata import construir_plata

    sniim = tmp_path / "bronce" / "sniim" / "fecha=2026-11-09"
    sniim.mkdir(parents=True)
    filas = []
    for producto in PRODUCTOS_SNIIM:
        for fecha in pd.date_range("2021-01-05", "2021-12-28", freq="14D"):
            filas.append({**fila(fecha=fecha.strftime("%d/%m/%Y"), producto=producto), "capturado_utc": None})
    filas.append({**fila(minimo="40", maximo="30"), "capturado_utc": None})  # irá a cuarentena
    pd.DataFrame(filas).drop(columns=["archivo_origen", "capturado_utc"]).to_csv(
        sniim / "sniim_historico_20261109T080451Z.csv", index=False
    )

    denue = tmp_path / "bronce" / "denue" / "fecha=2026-11-09"
    denue.mkdir(parents=True)
    base = {
        "Nombre": "TAQUERIA X",
        "Clase_actividad": "x",
        "Estrato": "0 a 5 personas",
        "Colonia": "CENTRO",
        "CP": "28000",
        "Tipo": "Fijo",
        "Longitud": "-103.7",
        "Latitud": "19.2",
        "CLASE_ACTIVIDAD_ID": "722514",
        "Fecha_Alta": "2010-07",
    }
    pd.DataFrame(
        [
            {**base, "CLEE": "06002722514000000000000000A0", "Ubicacion": "COLIMA, Colima, COLIMA", "AreaGeo": "06002"},
            {**base, "CLEE": "06007722514000000000000000B0", "Ubicacion": "MANZANILLO, Manzanillo, COLIMA", "AreaGeo": "06007"},
            {**base, "CLEE": "06009722514000000000000000C0", "Ubicacion": "COLIMA, Colima, COLIMA", "AreaGeo": "06009"},
        ]
    ).to_csv(denue / "denue_fotografia_20261109T081242Z.csv", index=False)

    reportes = construir_plata(tmp_path / "bronce", tmp_path)
    assert reportes["sniim"]["cuarentena"] == 1
    assert reportes["denue"]["validos_plata"] == 2 and reportes["denue"]["cuarentena"] == 1
    assert (tmp_path / "bitacora" / "puerta_calidad.csv").exists()
    cuarentena = pd.read_csv(tmp_path / "cuarentena" / "sniim_cuarentena.csv")
    assert cuarentena["motivo"].str.contains("regla de negocio").all()

    tablas = construir_oro(tmp_path, tmp_path / "diccionario.md")
    assert tablas["dim_insumo"] == 8 and tablas["dim_municipio"] == 10
    indice = pd.read_csv(tmp_path / "oro" / "indice_costo_taco.csv")
    assert abs(indice["indice"].mean() - 100) < 1e-6
    assert "precios_mensuales" in (tmp_path / "diccionario.md").read_text(encoding="utf-8")


def test_fiabilidad_cuenta_dia_sin_ejecucion_como_falla(tmp_path):
    from scripts.fiabilidad import cargar, evaluar

    ruta = tmp_path / "ejecuciones.csv"
    pd.DataFrame(
        [
            # día 9: sin programada; se recupera manualmente a las 21:35
            {
                "inicio_utc": "2026-11-09T21:34:00+00:00",
                "fin_utc": "2026-11-09T21:35:00+00:00",
                "fuente": "sniim",
                "modo": "diaria",
                "estado": "ok",
                "registros": 8,
            },
            {
                "inicio_utc": "2026-11-10T16:29:00+00:00",
                "fin_utc": "2026-11-10T16:30:00+00:00",
                "fuente": "sniim",
                "modo": "diaria",
                "estado": "ok",
                "registros": 8,
            },
        ]
    ).to_csv(ruta, index=False)
    r = evaluar(cargar(ruta), pd.Timestamp("2026-11-10T20:00:00+00:00"))
    assert r["dias_esperados"] == 2 and r["dias_exitosos"] == 1
    assert r["fallas"][0]["horas_reparacion"] == 5.33
    assert 0 < r["disponibilidad"] < 1
    assert r["ejecuciones_totales"] == 2 and r["tasa_exito_ejecucion"] == 1.0
    assert r["ejecuciones_programadas"] == 1
