"""Evaluación de la calidad de los DATOS de la capa oro con el modelo ISO/IEC 25012.

Mide las 15 características del modelo (inherentes, inherentes y dependientes del sistema, y
dependientes del sistema) con una métrica calculada sobre los archivos reales, un umbral y su veredicto.

Uso:
    python -m scripts.iso25012     # escribe calidad/iso25012.md y calidad/iso25012.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pandas as pd

from extractores.config import DATA, RAIZ
from pipeline.catalogos import LATITUD, LONGITUD
from pipeline.esquemas import COLUMNAS_PERSONALES

ORO = DATA / "oro"
SALIDA_MD = RAIZ / "calidad" / "iso25012.md"
SALIDA_JSON = RAIZ / "calidad" / "iso25012.json"
DICCIONARIO = RAIZ / "docs" / "E1" / "diccionario_oro.md"

# Columnas que pueden ir vacías por diseño (no cuentan para completitud).
OPCIONALES = {
    "precios_mensuales": {"precio_promedio", "precio_min", "precio_max"},  # vacías en meses imputados
    "indice_costo_taco": {"variacion_mensual_pct", "variacion_anual_pct", "insumos_imputados"},
    "pronostico": {"li_95", "ls_95"},  # vacías en meses observados
    "comparacion_modelos": {"detalle"},
    "geo_municipios": {"afluencia_por_taqueria", "pct_semifijas"},
}
# Frecuencia esperada de actualización por fuente (días): base de la métrica de actualidad.
VIGENCIA_DIAS = {"sniim": 7, "denue": 365, "denue_afluencia": 365, "marco_geo": 365}
FUENTES_OFICIALES = {"sniim", "denue", "denue_afluencia", "marco_geo", "inegi"}


def leer_oro() -> dict[str, pd.DataFrame]:
    return {r.stem: pd.read_csv(r, dtype=str, encoding="utf-8") for r in sorted(ORO.glob("*.csv"))}


def pct(a: float, b: float) -> float:
    return round(100 * a / b, 2) if b else 100.0


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def exactitud(t):
    """Valores dentro de su dominio válido (exactitud sintáctica)."""
    checks = []
    pm = t["precios_mensuales"]
    checks.append(("precio_mediana > 0", (num(pm["precio_mediana"]) > 0).sum(), len(pm)))
    checks.append(("mes con formato aaaa-mm", pm["mes"].str.fullmatch(r"\d{4}-\d{2}").sum(), len(pm)))
    if "geo_puntos" in t:
        gp = t["geo_puntos"]
        lat, lon = num(gp["latitud"]), num(gp["longitud"])
        dentro = lat.between(LATITUD[0] - 0.1, LATITUD[1] + 0.1) & lon.between(LONGITUD[0] - 0.1, LONGITUD[1] + 0.1)
        checks.append(("coordenada dentro de Colima", dentro.sum(), len(gp)))
        checks.append(("municipio_clave 06###", gp["municipio_clave"].str.fullmatch(r"06\d{3}").sum(), len(gp)))
    ok, total = sum(c[1] for c in checks), sum(c[2] for c in checks)
    return pct(ok, total), "; ".join(f"{n}: {pct(a, b)}%" for n, a, b in checks)


def completitud(t):
    llenas = total = 0
    peores = []
    for nombre, df in t.items():
        cols = [c for c in df.columns if c not in OPCIONALES.get(nombre, set())]
        n = df[cols].notna() & df[cols].ne("")
        llenas += int(n.values.sum())
        total += n.size
        if n.size and n.values.mean() < 1:
            peores.append(f"{nombre} {100 * n.values.mean():.2f}%")
    return pct(llenas, total), "Celdas obligatorias llenas en todas las tablas de oro. " + (
        "Con faltantes: " + ", ".join(peores) if peores else "Sin faltantes."
    )


def consistencia(t):
    reglas = []
    pm = t["precios_mensuales"]
    obs = pm[pm["imputado"] == "False"]
    r1 = (num(obs["precio_min"]) <= num(obs["precio_mediana"])) & (num(obs["precio_mediana"]) <= num(obs["precio_max"]))
    reglas.append(("mínimo ≤ mediana ≤ máximo", r1.sum(), len(obs)))
    if "geo_municipios" in t:
        gm = t["geo_municipios"]
        r2 = num(gm["taquerias"]) == num(gm["taqueria_fija"]) + num(gm["taqueria_semifija"])
        r3 = num(gm["afluencia"]) == num(gm["escuela"]) + num(gm["salud"])
        reglas += [("taquerías = fijas + semifijas", r2.sum(), len(gm)), ("afluencia = escuelas + salud", r3.sum(), len(gm))]
    if "geo_puntos" in t:
        gp = t["geo_puntos"]
        r4 = gp["municipio_clave"] == gp["municipio_clave_marco"]
        reglas.append(("municipio DENUE = municipio Marco", r4.sum(), len(gp)))
    ok, total = sum(r[1] for r in reglas), sum(r[2] for r in reglas)
    return pct(ok, total), "; ".join(f"{n}: {pct(a, b)}%" for n, a, b in reglas)


def credibilidad(t):
    lin = t.get("linaje", pd.DataFrame())
    if lin.empty:
        return 0.0, "Sin linaje."
    oficiales = lin["fuente"].isin(FUENTES_OFICIALES)
    return pct(oficiales.sum(), len(lin)), (
        f"Archivos de bronce de fuentes oficiales (SNIIM-SE, INEGI): {oficiales.sum()} de {len(lin)} referencias."
    )


def actualidad(t, ahora):
    lin = t.get("linaje", pd.DataFrame()).drop_duplicates("archivo_bronce")
    if lin.empty:
        return 0.0, "Sin linaje."
    lin = lin.assign(_t=pd.to_datetime(lin["capturado_utc"], utc=True, format="ISO8601"))
    ultima = lin.groupby("fuente")["_t"].max()
    edades = {f: (ahora - ts).total_seconds() / 86400 for f, ts in ultima.items()}
    vigentes = sum(edades[f] <= VIGENCIA_DIAS.get(f, 30) for f in edades)
    detalle = "; ".join(f"{f}: {d:.1f} días (máx. {VIGENCIA_DIAS.get(f, 30)})" for f, d in sorted(edades.items()))
    return pct(vigentes, len(edades)), "Antigüedad de la última ingesta por fuente: " + detalle


def accesibilidad(t):
    archivos = list(ORO.glob("*.csv")) + list(ORO.glob("*.geojson"))
    legibles = 0
    for r in archivos:
        try:
            r.read_text(encoding="utf-8")
            legibles += 1
        except UnicodeDecodeError:
            pass
    return pct(legibles, len(archivos)), (
        f"{legibles} de {len(archivos)} archivos de oro en UTF-8, formatos abiertos, públicos en el repositorio y en el tablero."
    )


def conformidad(_t):
    puerta = json.loads((DATA / "plata" / "reporte_puerta.json").read_text(encoding="utf-8"))
    tasas = {r["fuente"]: r["tasa_validez"] for r in puerta if r.get("tasa_validez") is not None}
    return round(100 * min(tasas.values()), 2), "Validez de la puerta Pandera por fuente: " + "; ".join(
        f"{f}: {100 * v:.2f}%" for f, v in tasas.items()
    )


def confidencialidad(t):
    hallazgos = [f"{n}.{c}" for n, df in t.items() for c in df.columns if c.lower() in COLUMNAS_PERSONALES]
    geo = [f"{n}.nombre" for n, df in t.items() if n.startswith("geo_") and "nombre" in df.columns]
    total = len(hallazgos) + len(geo)
    return float(total), "Columnas personales en oro: " + (", ".join(hallazgos + geo) if total else "ninguna")


def eficiencia(t):
    peso = sum(r.stat().st_size for r in ORO.iterdir() if r.is_file() and not r.name.startswith(".")) / 1e6
    filas = sum(len(df) for df in t.values())
    return round(peso, 2), f"{peso:.2f} MB para {filas:,} filas ({1e6 * peso / filas:.0f} bytes por fila)."


def precision(t):
    gp = t.get("geo_puntos", pd.DataFrame())
    if gp.empty:
        return 0.0, "Sin puntos."
    dec = gp["latitud"].str.extract(r"\.(\d+)$")[0].str.len().fillna(0)
    return pct((dec >= 5).sum(), len(gp)), (
        "Coordenadas con ≥ 5 decimales (≈ 1 m): necesarias para asignar el punto al municipio y a la celda de 1 km."
    )


def trazabilidad(t):
    filas = trazables = 0
    for nombre, df in t.items():
        if nombre == "linaje":
            continue
        if "archivos_bronce" in df.columns:
            filas += len(df)
            trazables += int(df["archivos_bronce"].fillna("").ne("").sum())
        elif "derivado_de" in df.columns:
            filas += len(df)
            trazables += int(df["derivado_de"].isin(t).sum())
    lin = t.get("linaje", pd.DataFrame()).drop_duplicates("archivo_bronce")
    integros = int((lin["integro"] == "True").sum()) if len(lin) else 0
    return pct(trazables, filas), (
        f"{trazables:,} de {filas:,} filas de oro apuntan a bronce (directo o vía derivado_de); "
        f"{integros} de {len(lin)} archivos de bronce con SHA-256 íntegro."
    )


def comprensibilidad(t):
    texto = DICCIONARIO.read_text(encoding="utf-8") if DICCIONARIO.exists() else ""
    total = documentadas = 0
    for nombre, df in t.items():
        bloque = texto.split(f"## `{nombre}.csv`")
        cuerpo = bloque[1].split("\n## ")[0] if len(bloque) > 1 else ""
        for c in df.columns:
            total += 1
            fila = re.search(rf"^\| `{re.escape(c)}` \| [^|]+ \| ([^|]*) \|", cuerpo, re.M)
            documentadas += bool(fila and fila.group(1).strip())
    return pct(documentadas, total), f"{documentadas} de {total} columnas de oro con descripción en el diccionario."


def disponibilidad(_t):
    ruta = DATA / "bitacora" / "fiabilidad.json"
    if not ruta.exists():
        return 0.0, "Sin bitácora de fiabilidad."
    f = json.loads(ruta.read_text(encoding="utf-8"))
    return round(100 * f["disponibilidad"], 2), (
        f"A = MTBF / (MTBF + MTTR) de la captura diaria (scripts/fiabilidad.py), calculada el {f['calculado_utc'][:10]}."
    )


def portabilidad(_t):
    archivos = [r for r in ORO.iterdir() if r.is_file() and not r.name.startswith(".")]
    abiertos = [r for r in archivos if r.suffix in {".csv", ".geojson", ".json"}]
    return pct(len(abiertos), len(archivos)), (
        f"{len(abiertos)} de {len(archivos)} archivos de oro en CSV o GeoJSON (RFC 7946, WGS84); sin formatos propietarios."
    )


def recuperabilidad(_t):
    datos = [r for r in (DATA / "bronce").rglob("*") if r.is_file() and r.suffix in {".csv", ".geojson"}]
    con_meta = 0
    for r in datos:
        m = r.with_suffix(".meta.json")
        con_meta += m.exists() and "sha256" in json.loads(m.read_text(encoding="utf-8"))
    return pct(con_meta, len(datos)), (
        f"{con_meta} de {len(datos)} archivos de bronce con .meta.json y SHA-256: oro se reconstruye desde bronce con "
        "`python -m pipeline.ejecutar`; respaldos con scripts/respaldo.py."
    )


# (característica, categoría, métrica, función, umbral, sentido)
MODELO = [
    ("Exactitud", "Inherente", "% de valores dentro de su dominio", exactitud, 99.0, ">="),
    ("Completitud", "Inherente", "% de celdas obligatorias llenas", completitud, 98.0, ">="),
    ("Consistencia", "Inherente", "% de reglas entre columnas y fuentes que se cumplen", consistencia, 98.0, ">="),
    ("Credibilidad", "Inherente", "% de referencias de bronce de fuentes oficiales", credibilidad, 100.0, ">="),
    ("Actualidad", "Inherente", "% de fuentes con última ingesta dentro de su vigencia", actualidad, 100.0, ">="),
    ("Accesibilidad", "Inherente y del sistema", "% de archivos de oro legibles en UTF-8", accesibilidad, 100.0, ">="),
    ("Conformidad", "Inherente y del sistema", "Validez mínima de la puerta Pandera (%)", conformidad, 98.0, ">="),
    ("Confidencialidad", "Inherente y del sistema", "Columnas personales en oro", confidencialidad, 0.0, "<="),
    ("Eficiencia", "Inherente y del sistema", "Tamaño de la capa oro (MB)", eficiencia, 25.0, "<="),
    ("Precisión", "Inherente y del sistema", "% de coordenadas con ≥ 5 decimales", precision, 99.0, ">="),
    ("Trazabilidad", "Inherente y del sistema", "% de filas de oro rastreables a bronce", trazabilidad, 100.0, ">="),
    ("Comprensibilidad", "Inherente y del sistema", "% de columnas documentadas", comprensibilidad, 100.0, ">="),
    ("Disponibilidad", "Dependiente del sistema", "Disponibilidad A de la captura (%)", disponibilidad, 95.0, ">="),
    ("Portabilidad", "Dependiente del sistema", "% de archivos en formatos abiertos", portabilidad, 100.0, ">="),
    (
        "Recuperabilidad",
        "Dependiente del sistema",
        "% de archivos de bronce con huella para reconstruir",
        recuperabilidad,
        100.0,
        ">=",
    ),
]


def evaluar(ahora: datetime | None = None) -> list[dict]:
    ahora = ahora or datetime.now(timezone.utc)
    t = leer_oro()
    filas = []
    for nombre, categoria, metrica, f, umbral, sentido in MODELO:
        valor, evidencia = f(t, ahora) if f is actualidad else f(t)
        cumple = valor >= umbral if sentido == ">=" else valor <= umbral
        filas.append(
            {
                "caracteristica": nombre,
                "categoria": categoria,
                "metrica": metrica,
                "valor": valor,
                "umbral": f"{sentido} {umbral:g}",
                "cumple": bool(cumple),
                "evidencia": evidencia,
            }
        )
    return filas


def escribir(filas: list[dict], ahora: datetime) -> None:
    cumplen = sum(f["cumple"] for f in filas)
    lineas = [
        "# Calidad de los datos de la capa oro · ISO/IEC 25012",
        "",
        f"Generado por `python -m scripts.iso25012` el {ahora:%Y-%m-%d %H:%M} UTC sobre `data/oro/`. "
        f"**{cumplen} de {len(filas)} características cumplen su umbral.**",
        "",
        "| Característica | Categoría | Métrica | Valor | Umbral | Cumple | Evidencia |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in filas:
        marca = "Sí" if f["cumple"] else "**No**"
        lineas.append(
            f"| {f['caracteristica']} | {f['categoria']} | {f['metrica']} | {f['valor']:g} | {f['umbral']} | {marca} | "
            f"{f['evidencia']} |"
        )
    lineas += [
        "",
        "Categorías del modelo: *inherente* (propia del dato), *inherente y dependiente del sistema* y *dependiente "
        "del sistema* (depende de cómo lo guardamos y servimos). Los umbrales de completitud y conformidad son los "
        "del objetivo de calidad 3 de E0 (≥ 98 %).",
        "",
    ]
    SALIDA_MD.write_text("\n".join(lineas), encoding="utf-8")
    SALIDA_JSON.write_text(
        json.dumps({"calculado_utc": ahora.isoformat(timespec="seconds"), "resultados": filas}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    momento = datetime.now(timezone.utc)
    resultados = evaluar(momento)
    escribir(resultados, momento)
    for r in resultados:
        print(f"{'OK ' if r['cumple'] else 'NO '} {r['caracteristica']:<17} {r['valor']:>8g}  ({r['umbral']})")
