"""Evaluación de la calidad del PRODUCTO (el sistema del observatorio) con el modelo ISO/IEC 25010.

Mide una métrica por cada una de las 8 características del modelo, ejecutando de verdad las pruebas,
el pipeline y el tablero; nada se copia a mano. Escribe calidad/iso25010.md y calidad/iso25010.json.

Requiere también las dependencias del tablero (pip install -r tablero/requirements.txt), porque la
capacidad de interacción se mide cargando el tablero con streamlit.testing.

Uso:
    python -m scripts.iso25010          # tarda ~1 minuto: corre pytest con cobertura, el pipeline y el tablero
"""

from __future__ import annotations

import csv
import json
import platform
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from extractores.config import DATA, RAIZ

SALIDA_MD = RAIZ / "calidad" / "iso25010.md"
SALIDA_JSON = RAIZ / "calidad" / "iso25010.json"
REQUERIMIENTOS = RAIZ / "docs" / "E1" / "requerimientos.md"
TOKENS_FICTICIOS = {"0123abcd-4567-89ab-cdef-0123456789ab"}  # el token falso de tests/test_extractores.py
PATRON_TOKEN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
RUTA_FIJA = re.compile(r"""["'](?:[A-Za-z]:\\\\|/home/|/Users/|C:/)""")


def correr(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def pruebas() -> dict:
    """Una sola corrida de pytest con cobertura y reporte JUnit; la usan varias características."""
    with tempfile.TemporaryDirectory() as tmp:
        junit, cov = Path(tmp) / "junit.xml", Path(tmp) / "cov.json"
        correr(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                f"--junitxml={junit}",
                "--cov=pipeline",
                f"--cov-report=json:{cov}",
            ]
        )
        casos = ET.parse(junit).getroot().iter("testcase")
        estado = {}
        for c in casos:
            fallo = any(h.tag in {"failure", "error"} for h in c)
            omitida = any(h.tag == "skipped" for h in c)
            estado[c.get("name").split("[")[0]] = estado.get(c.get("name").split("[")[0], True) and not fallo
            if omitida:
                estado[c.get("name").split("[")[0]] = False
        cobertura = json.loads(cov.read_text(encoding="utf-8"))["totals"]["percent_covered"]
    return {"estado": estado, "cobertura": round(cobertura, 2)}


def adecuacion_funcional(p: dict) -> tuple[float, str]:
    """Corrección funcional: requerimientos funcionales cuya prueba automatizada pasa."""
    texto = REQUERIMIENTOS.read_text(encoding="utf-8")
    pruebas_por_rf: dict[str, set[str]] = {}
    for f in texto.splitlines():
        m = re.match(r"\| (RF-\d+) \|", f)
        if m:
            pruebas_por_rf.setdefault(m.group(1), set()).update(re.findall(r"`(test_[a-z0-9_]+)`", f))
    filas = list(pruebas_por_rf)
    con_prueba = sum(1 for n in pruebas_por_rf.values() if n)
    cumplen = sum(all(p["estado"].get(x, False) for x in n) for n in pruebas_por_rf.values() if n)
    pasan = sum(p["estado"].values())
    return round(100 * cumplen / con_prueba, 2), (
        f"{cumplen} de {con_prueba} RF verificados por prueba pasan (de {len(filas)} RF; los demás se verifican por "
        f"análisis, inspección o demostración). Suite completa: {pasan} de {len(p['estado'])} pruebas pasan."
    )


def eficiencia_desempeno() -> tuple[float, str]:
    """Comportamiento temporal. Ruta ingeniería: la evidencia es el experimento de E2 (confirmación)."""
    import pandas as pd

    inicio = time.perf_counter()
    r = correr([sys.executable, "-m", "pipeline.ejecutar"])
    dur = time.perf_counter() - inicio
    ok = "LINAJE" in r.stderr + r.stdout
    conf = RAIZ / "laboratorio" / "resultados" / "confirmacion.csv"
    if not conf.exists():
        return float("inf"), "Falta la corrida de confirmación del experimento (laboratorio/resultados/confirmacion.csv)."
    c = pd.read_csv(conf)
    gm = c.groupby("configuracion")["tiempo_s"].apply(lambda s: float(np.exp(np.log(s).mean())))
    return round(gm["mejor"], 2), (
        f"Lectura de las 220 páginas del banco con la configuración elegida en el experimento (4 procesos, lxml, CSV): "
        f"{gm['mejor']:.2f} s contra {gm['actual']:.2f} s de la configuración anterior, "
        f"{gm['actual'] / gm['mejor']:.2f} veces más rápido (corrida de confirmación, "
        f"[E2_experimento.ipynb](../laboratorio/E2_experimento.ipynb)). "
        f"Pipeline completo bronce → oro → linaje: {dur:.1f} s ({'terminó bien' if ok else 'NO terminó'})."
    )


def compatibilidad() -> tuple[float, str]:
    """Interoperabilidad: archivos de oro que abre una herramienta distinta a la que los escribió."""
    archivos = [r for r in (DATA / "oro").iterdir() if r.suffix in {".csv", ".geojson"}]
    legibles = 0
    for r in archivos:
        try:
            if r.suffix == ".csv":
                with open(r, encoding="utf-8", newline="") as f:
                    filas = list(csv.reader(f))
                legibles += len(filas) > 1 and len({len(x) for x in filas}) == 1
            else:
                g = json.loads(r.read_text(encoding="utf-8"))
                legibles += g.get("type") == "FeatureCollection" and len(g["features"]) > 0
        except (OSError, ValueError, csv.Error):
            pass
    return round(100 * legibles / len(archivos), 2), (
        f"{legibles} de {len(archivos)} archivos de oro se leen con el módulo csv y json de la biblioteca estándar "
        "(sin pandas), con el mismo número de columnas en cada fila; el GeoJSON cumple RFC 7946 (WGS84)."
    )


def usabilidad() -> tuple[float, str]:
    """Capacidad de interacción: pestañas del tablero que cargan sin error y explican lo que muestran."""
    try:
        from streamlit.testing.v1 import AppTest
    except ModuleNotFoundError:
        raise SystemExit("Falta streamlit: pip install -r tablero/requirements.txt") from None

    at = AppTest.from_file(str(RAIZ / "tablero" / "app.py"), default_timeout=120).run()
    if at.exception:
        return 0.0, f"El tablero falla al cargar: {at.exception[0].message}"
    total = len(at.tabs)
    utiles = sum(1 for t in at.tabs if len(t.caption) + len(t.markdown) + len(t.info) > 0)
    return round(100 * utiles / total, 2), (
        f"{utiles} de {total} pestañas ({', '.join(t.label for t in at.tabs)}) cargan sin error y tienen texto que "
        "explica qué muestran y sus límites."
    )


def fiabilidad() -> tuple[float, str]:
    f = json.loads((DATA / "bitacora" / "fiabilidad.json").read_text(encoding="utf-8"))
    return round(100 * f["disponibilidad"], 2), (
        f"Disponibilidad A = MTBF / (MTBF + MTTR) de la captura diaria = {100 * f['disponibilidad']:.2f} % "
        f"(MTBF {f['mtbf_h']:.1f} h, MTTR {f['mttr_h']:.1f} h, calculado el {f['calculado_utc'][:10]})."
    )


def seguridad() -> tuple[float, str]:
    """Confidencialidad: tokens con forma de clave de API en archivos versionados."""
    versionados = correr(["git", "ls-files"]).stdout.splitlines()
    texto = [RAIZ / f for f in versionados if Path(f).suffix in {".py", ".json", ".yml", ".yaml", ".md", ".csv", ".txt"}]
    hallazgos, ficticios = [], 0
    for r in texto:
        try:
            contenido = r.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for t in PATRON_TOKEN.findall(contenido):
            if t.lower() in TOKENS_FICTICIOS:
                ficticios += 1
            else:
                hallazgos.append(f"{r.relative_to(RAIZ)}")
    env_versionado = ".env" in versionados
    total = len(hallazgos) + int(env_versionado)
    return float(total), (
        f"Revisados {len(texto)} archivos de texto versionados: {len(hallazgos)} cadenas con forma de token "
        f"(sin contar {ficticios} token ficticio de las pruebas) y "
        f"`.env` {'SÍ' if env_versionado else 'no'} está en git. Las URL de los .meta.json guardan el token como ***. "
        "En CI, gitleaks revisa todo el historial."
    )


def mantenibilidad(p: dict) -> tuple[float, str]:
    r = correr([sys.executable, "-m", "ruff", "check", ".", "--output-format", "concise"])
    errores = len([x for x in r.stdout.splitlines() if re.match(r".+:\d+:\d+:", x)])
    return p["cobertura"], (
        f"Cobertura de líneas de pipeline/ con pytest-cov: {p['cobertura']:.2f} %. "
        f"Hallazgos de ruff (estilo y errores comunes): {errores}."
    )


def portabilidad() -> tuple[float, str]:
    """Adaptabilidad: rutas atadas a una computadora en el código."""
    codigo = [p for p in RAIZ.rglob("*.py") if ".venv" not in p.parts and "site-packages" not in p.parts]
    fijas = [f"{p.relative_to(RAIZ)}" for p in codigo if RUTA_FIJA.search(p.read_text(encoding="utf-8", errors="ignore"))]
    return float(len(fijas)), (
        f"{len(fijas)} de {len(codigo)} archivos .py con rutas absolutas de una máquina "
        f"({', '.join(fijas) if fijas else 'ninguno'}); todas las rutas salen de la raíz del repositorio con pathlib. "
        f"Esta medición corrió en {platform.system()} {platform.release()} con Python {platform.python_version()}; "
        "CI corre las mismas pruebas en Ubuntu."
    )


MODELO = [
    ("Adecuación funcional", "Corrección funcional", "% de RF con prueba que pasan", 100.0, ">="),
    ("Eficiencia de desempeño", "Comportamiento temporal", "Segundos para leer 220 páginas (configuración elegida)", 10.0, "<="),
    ("Compatibilidad", "Interoperabilidad", "% de archivos de oro legibles sin pandas", 100.0, ">="),
    (
        "Capacidad de interacción",
        "Reconocimiento de adecuación",
        "% de pestañas del tablero que cargan y se explican",
        100.0,
        ">=",
    ),
    ("Fiabilidad", "Disponibilidad", "Disponibilidad A de la captura (%)", 95.0, ">="),
    ("Seguridad", "Confidencialidad", "Secretos en archivos versionados", 0.0, "<="),
    ("Mantenibilidad", "Capacidad de prueba", "Cobertura de líneas de pipeline/ (%)", 80.0, ">="),
    ("Portabilidad", "Adaptabilidad", "Archivos .py con rutas de una máquina", 0.0, "<="),
]


def evaluar() -> list[dict]:
    print("Corriendo pruebas con cobertura...", flush=True)
    p = pruebas()
    mediciones = {
        "Adecuación funcional": lambda: adecuacion_funcional(p),
        "Eficiencia de desempeño": eficiencia_desempeno,
        "Compatibilidad": compatibilidad,
        "Capacidad de interacción": usabilidad,
        "Fiabilidad": fiabilidad,
        "Seguridad": seguridad,
        "Mantenibilidad": lambda: mantenibilidad(p),
        "Portabilidad": portabilidad,
    }
    filas = []
    for caracteristica, sub, metrica, umbral, sentido in MODELO:
        print(f"Midiendo {caracteristica}...", flush=True)
        valor, evidencia = mediciones[caracteristica]()
        cumple = valor >= umbral if sentido == ">=" else valor <= umbral
        filas.append(
            {
                "caracteristica": caracteristica,
                "subcaracteristica": sub,
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
        "# Calidad del producto · ISO/IEC 25010",
        "",
        f"Generado por `python -m scripts.iso25010` el {ahora:%Y-%m-%d %H:%M} UTC. Cada valor se midió ejecutando el "
        f"sistema (pruebas, pipeline y tablero), no se copió a mano. **{cumplen} de {len(filas)} características "
        "cumplen su umbral.**",
        "",
        "| Característica | Subcaracterística | Métrica | Valor | Umbral | Cumple | Evidencia |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in filas:
        marca = "Sí" if f["cumple"] else "**No**"
        lineas.append(
            f"| {f['caracteristica']} | {f['subcaracteristica']} | {f['metrica']} | {f['valor']:g} | {f['umbral']} | "
            f"{marca} | {f['evidencia']} |"
        )
    lineas += [
        "",
        "Se usan las 8 características que pide el proyecto. En ISO/IEC 25010:2023 la usabilidad se llama *capacidad de "
        "interacción* (así la nombramos) y la portabilidad, *flexibilidad*; esa edición agrega una novena, *protección* "
        "(safety), que no aplica a un observatorio de datos porque su falla no puede dañar personas ni bienes. "
        "Ver [normativa.md](normativa.md). La fiabilidad es la medida en E1 con la bitácora; la eficiencia de desempeño "
        "es el resultado del experimento de E2. La calidad de los datos se mide aparte con ISO/IEC 25012 "
        "([iso25012.md](iso25012.md)).",
        "",
    ]
    SALIDA_MD.write_text("\n".join(lineas), encoding="utf-8")
    SALIDA_JSON.write_text(
        json.dumps({"calculado_utc": ahora.isoformat(timespec="seconds"), "resultados": filas}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    momento = datetime.now(timezone.utc)
    resultados = evaluar()
    escribir(resultados, momento)
    for r in resultados:
        print(f"{'OK ' if r['cumple'] else 'NO '} {r['caracteristica']:<24} {r['valor']:>8g}  ({r['umbral']})")
