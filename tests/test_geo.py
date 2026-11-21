"""Pruebas de la fuente geoespacial (E2) con datos sintéticos: puerta del Marco, privacidad y uniones espaciales."""

import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon, box

from pipeline.catalogos import MUNICIPIOS
from pipeline.esquemas import verificar_privacidad
from pipeline.geo import construir_geo, plata_marco
from pipeline.plata import preparar_afluencia

CAPTURA = "2026-11-20T14:41:05+00:00"


def cuadro(i: int):
    """Un cuadro de ~0.1° por municipio, en fila, dentro de Colima continental."""
    x0 = -104.5 + 0.1 * i
    return box(x0, 19.0, x0 + 0.1, 19.1)


def escribir_marco(carpeta, filas):
    destino = carpeta / "bronce" / "marco_geo" / "fecha=2026-11-20"
    destino.mkdir(parents=True)
    gdf = gpd.GeoDataFrame(filas, geometry="geometry", crs="EPSG:4326")
    ruta = destino / "mgem_colima_20261120T144105Z.geojson"
    gdf.to_file(ruta, driver="GeoJSON")
    ruta.with_suffix(".meta.json").write_text(json.dumps({"capturado_utc": CAPTURA, "sha256": "x"}), encoding="utf-8")
    return ruta


def marco_completo():
    return [{"cvegeo": "06" + c, "nomgeo": n, "geometry": cuadro(i)} for i, (c, n) in enumerate(MUNICIPIOS.items())]


def test_marco_completo_pasa_sin_cuarentena(tmp_path):
    escribir_marco(tmp_path, marco_completo())
    r = plata_marco(tmp_path / "bronce", tmp_path, CAPTURA)
    assert r["validos_plata"] == 10 and r["cuarentena"] == 0 and r["tasa_validez"] == 1.0
    assert (tmp_path / "plata" / "marco_municipios.geojson").exists()


def test_marco_detecta_fuera_de_colima_faltante_y_repara_invalida(tmp_path):
    filas = marco_completo()
    moño = Polygon([(-104.5, 19.0), (-104.4, 19.1), (-104.4, 19.0), (-104.5, 19.1)])  # se cruza a sí mismo
    filas[0]["geometry"] = moño
    filas[1]["cvegeo"] = "14039"  # Guadalajara: fuera de Colima -> cuarentena, y 06002 queda faltante
    escribir_marco(tmp_path, filas)
    r = plata_marco(tmp_path / "bronce", tmp_path, CAPTURA)
    assert r["geometrias_reparadas"] == 1
    assert r["motivos"]["clave de municipio fuera de Colima"] == 1
    assert r["motivos"]["municipio faltante en el Marco Geoestadístico"] == 1
    assert r["validos_plata"] == 9


def test_privacidad_rechaza_columnas_personales():
    with pytest.raises(ValueError, match="privacidad"):
        verificar_privacidad(["CLEE", "Nombre", "Latitud"])
    verificar_privacidad(["CLEE", "Clase_actividad", "Latitud"])  # sin personales: no falla


def crudo_afluencia(**cambios):
    fila = {
        "CLEE": "06002611122000343000000000U7",
        "Clase_actividad": "Escuelas de educación primaria del sector público",
        "Estrato": "11 a 30 personas",
        "Colonia": "NUEVO MILENIO",
        "CP": "28048",
        "Ubicacion": "COLIMA,Colima,COLIMA",
        "Longitud": "-103.7048",
        "Latitud": "19.2266",
        "CLASE_ACTIVIDAD_ID": "611122",
        "AreaGeo": "060020001",
        "tipo_afluencia": "educacion",
        "capa_scian": "611/0/0",
        "archivo_origen": "denue_afluencia_colima_20261120T144104Z.csv",
        "capturado_utc": CAPTURA,
    }
    fila.update(cambios)
    return pd.DataFrame([fila])


def test_afluencia_conserva_linaje_y_rechaza_municipio_inconsistente():
    ok, rech = preparar_afluencia(crudo_afluencia())
    assert len(ok) == 1 and ok.iloc[0]["municipio_clave"] == "06002"
    assert ok.iloc[0]["archivo_origen"].startswith("denue_afluencia")
    malo, rech = preparar_afluencia(crudo_afluencia(Ubicacion="TECOMAN,Tecomán,COLIMA"))
    assert len(malo) == 0 and len(rech) == 1


def test_construir_geo_produce_tablas_sin_nombres_y_con_linaje(tmp_path):
    escribir_marco(tmp_path, marco_completo())
    plata_marco(tmp_path / "bronce", tmp_path, CAPTURA)
    # Dentro del cuadro de Colima (índice 1 en MUNICIPIOS): 2 escuelas, 1 taquería fija, 1 semifija.
    x, y = -104.35, 19.05
    taq = pd.DataFrame(
        {
            "clee": ["T1", "T2"],
            "nombre": ["TACOS PRUEBA", "TACOS DOS"],
            "tipo_negocio": ["taqueria", "taqueria"],
            "establecimiento": ["Fijo", "Semifijo"],
            "municipio_clave": ["06002", "06002"],
            "latitud": [y, y + 0.001],
            "longitud": [x, x + 0.001],
            "archivo_origen": "denue_colima_722_20261109T081242Z.csv",
            "capturado_utc": "2026-11-09T08:12:42+00:00",
        }
    )
    afl = pd.DataFrame(
        {
            "clee": ["E1", "E2"],
            "tipo_afluencia": ["educacion", "salud"],
            "municipio_clave": ["06002", "06002"],
            "latitud": [y + 0.002, y - 0.002],
            "longitud": [x, x],
            "archivo_origen": "denue_afluencia_colima_20261120T144104Z.csv",
            "capturado_utc": CAPTURA,
        }
    )
    taq.to_csv(tmp_path / "plata" / "denue_negocios.csv", index=False)
    afl.to_csv(tmp_path / "plata" / "denue_afluencia.csv", index=False)

    tablas = construir_geo(tmp_path)
    assert tablas["geo_municipios"] == 10 and tablas["geo_puntos"] == 4
    puntos = pd.read_csv(tmp_path / "oro" / "geo_puntos.csv", dtype=str)
    assert "nombre" not in puntos.columns
    assert puntos["archivos_bronce"].str.contains("mgem_colima").all()
    assert set(puntos["municipio_clave_marco"]) == {"06002"}
    mun = pd.read_csv(tmp_path / "oro" / "geo_municipios.csv", dtype={"municipio_clave": str})
    colima = mun.set_index("municipio_clave").loc["06002"]
    assert colima["taquerias"] == 2 and colima["afluencia"] == 2 and colima["area_km2"] > 0
    reporte = json.loads((tmp_path / "plata" / "reporte_geo.json").read_text(encoding="utf-8"))
    assert reporte["puntos_fuera_de_los_limites"] == 0
    assert reporte["radio"]["con_al_menos_una_taqueria"] == 2
