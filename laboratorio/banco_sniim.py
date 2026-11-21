"""Banco de pruebas local del extractor del SNIIM para el diseño de experimentos de E2.

Por qué local: medir contra el sitio real mezclaría el efecto de los factores con la latencia de la red
y cargaría al servidor del SNIIM con cientos de consultas repetidas. El banco reproduce el trabajo del
extractor (leer páginas de resultados, extraer la tabla, guardar el resultado) sobre una copia fija.

Las páginas:
  - Usan la estructura real de la tabla de resultados del SNIIM (tests/fixtures/sniim_resultados_real.html).
  - Las filas de Colima son las reales de la serie histórica en bronce (8 insumos, 2020-2026).
  - Para que cada página tenga el tamaño de una respuesta real ("todos los mercados", unas 21 filas
    por día de consulta), se agregan filas de otros mercados derivadas de las de Colima (precio con una
    variación fija). Están marcadas como sintéticas en el manifiesto.
  - El 12 % de las páginas se daña a propósito con fallas que vimos o que pueden pasar en la captura:
      truncada      la descarga se cortó a la mitad
      sin_cierres   celdas sin </td> (HTML mal formado; el navegador lo tolera)
      sin_id        la tabla cambió de id (cambio de diseño del sitio)
      mojibake      acentos dañados por una mala decodificación (UTF-8 leído como Latin-1)

Respuestas que mide cada corrida:
  tiempo_s     segundos de reloj desde abrir el primer archivo hasta escribir el resultado
               (incluye arrancar los procesos, porque es costo real de usar paralelismo)
  tasa_error   % de filas esperadas que se perdieron o se leyeron con otro contenido

Uso:
    python -m laboratorio.banco_sniim generar     # crea laboratorio/banco/ (una sola vez; es determinista)
    python -m laboratorio.banco_sniim probar      # una corrida de prueba con la configuración base
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "laboratorio" / "banco"
PAGINAS = BANCO / "paginas"
MANIFIESTO = BANCO / "manifiesto.csv"
SEMILLA = 2026
PROPORCION_DANADAS = 0.12
MERCADOS_POR_FILA = 12  # filas de otros mercados por cada fila de Colima
CAMPOS = ["fecha", "presentacion", "origen", "destino", "precio_min", "precio_max", "precio_frec", "obs"]
OTROS_MERCADOS = [
    "Aguascalientes: Centro Comercial Agropecuario de Aguascalientes",
    "Baja California: Central de Abasto INDIA de Tijuana",
    "Chihuahua: Central de Abasto de Chihuahua",
    "Coahuila: Central de Abasto de La Laguna, Torreón",
    "DF: Central de Abasto de Iztapalapa DF",
    "Durango: Centro de Distribución y Abasto de Gómez Palacio",
    "Guanajuato: Central de Abasto de León",
    "Guerrero: Central de Abastos de Acapulco",
    "Jalisco: Mercado de Abasto de Guadalajara",
    "Jalisco: Mercado Felipe Ángeles de Guadalajara",
    "Michoacán: Mercado de Abasto de Morelia",
    "Morelos: Central de Abasto de Cuautla",
    "Nayarit: Mercado de abastos 'Adolfo López Mateos' de Tepic",
    "Nuevo León: Central de Abasto de Guadalupe, Nvo. León",
    "Oaxaca: Módulo de Abasto de Oaxaca",
    "Puebla: Central de Abasto de Puebla",
    "Querétaro: Mercado de Abasto de Querétaro",
    "San Luis Potosí: Centro de Abasto de San Luis Potosí",
    "Sinaloa: Central de Abasto de Culiacán",
    "Sonora: Central de Abasto de Cd. Obregón",
    "Tabasco: Central de Abasto de Villahermosa",
    "Veracruz: Central de Abasto de Jalapa",
    "Yucatán: Central de Abasto de Mérida",
    "Zacatecas: Mercado de Abasto de Zacatecas",
]
ENCABEZADO = (
    '<table id="{id}" cellspacing="0" cellpadding="0"><tr>'
    + "".join(
        f'<td class="titDATtab2">{t}</td>'
        for t in ["Fecha", "Presentación", "Origen", "Destino", "Precio Mín", "Precio Max", "Precio Frec", "Obs."]
    )
    + '</tr>\n<tr><td class="encabACT2" colspan="8">Frutas y Hortalizas</td></tr>\n'
)


# ------------------------------------------------------------------ generación del banco


def _fila_html(f: dict, cerrar: bool = True) -> str:
    celdas = [f'<td class="Datos2" colspan="1">{f["fecha"]}</td>'] + [f'<td class="Datos2">{f[c]}</td>' for c in CAMPOS[1:]]
    if cerrar:
        return "<tr>" + "".join(celdas) + "</tr>\n"
    return "<tr>" + "".join(c.replace("</td>", "") for c in celdas) + "</tr>\n"  # celdas sin </td>


def _pagina(filas: list[dict], dano: str) -> str:
    tabla_id = "tblResultadosNuevo" if dano == "sin_id" else "tblResultados"
    cuerpo = "".join(_fila_html(f, cerrar=dano != "sin_cierres") for f in filas)
    html = "<html><body>\n" + ENCABEZADO.format(id=tabla_id) + cuerpo + "</table>\n</body></html>\n"
    if dano == "truncada":
        html = html[: int(len(html) * 0.6)]
    if dano == "mojibake":
        html = html.encode("utf-8").decode("latin-1")
    return html


def _huella(filas) -> str:
    texto = "\n".join("|".join(str(v) for v in f) for f in filas)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def generar() -> pd.DataFrame:
    historico = sorted((RAIZ / "data" / "bronce" / "sniim").glob("fecha=*/sniim_historico_*.csv"))[0]
    df = pd.read_csv(historico, dtype=str).fillna("")
    df["trimestre"] = pd.to_datetime(df["fecha"], dayfirst=True).dt.to_period("Q").astype(str)
    azar = random.Random(SEMILLA)
    PAGINAS.mkdir(parents=True, exist_ok=True)
    registros = []
    for (producto, trimestre), g in df.groupby(["producto", "trimestre"], sort=True):
        filas = []
        for _, r in g.iterrows():
            base = {c: r[c] for c in CAMPOS}
            filas.append(base)
            for j, mercado in enumerate(OTROS_MERCADOS[:MERCADOS_POR_FILA]):
                factor = 0.85 + 0.3 * ((j * 7 + len(r["fecha"])) % 10) / 10
                otra = dict(base, destino=mercado)
                for c in ("precio_min", "precio_max", "precio_frec"):
                    otra[c] = f"{float(r[c]) * factor:.2f}" if r[c] else ""
                filas.append(otra)
        registros.append({"producto": producto, "trimestre": trimestre, "filas": filas})
    danos = ["truncada", "sin_cierres", "sin_id", "mojibake"]
    indices = list(range(len(registros)))
    azar.shuffle(indices)
    n_danadas = round(len(registros) * PROPORCION_DANADAS)
    tipo = {i: danos[k % len(danos)] for k, i in enumerate(indices[:n_danadas])}
    manifiesto = []
    for i, reg in enumerate(registros):
        dano = tipo.get(i, "ninguno")
        nombre = f"pagina_{i:04d}.html"
        (PAGINAS / nombre).write_text(_pagina(reg["filas"], dano), encoding="utf-8")
        esperadas = [tuple(f[c] for c in CAMPOS) for f in reg["filas"]]
        manifiesto.append(
            {
                "pagina": nombre,
                "producto": reg["producto"],
                "trimestre": reg["trimestre"],
                "dano": dano,
                "filas_esperadas": len(esperadas),
                "filas_colima_reales": sum(f["destino"].startswith("Colima") for f in reg["filas"]),
                "huella_filas": _huella(esperadas),
            }
        )
    salida = pd.DataFrame(manifiesto)
    salida.to_csv(MANIFIESTO, index=False)
    (BANCO / "esperado.json").write_text(
        json.dumps({r["pagina"]: [list(f) for f in r["filas"]] for r in _esperadas(registros, manifiesto)}),
        encoding="utf-8",
    )
    return salida


def _esperadas(registros, manifiesto):
    for reg, m in zip(registros, manifiesto, strict=True):
        yield {"pagina": m["pagina"], "filas": [tuple(f[c] for c in CAMPOS) for f in reg["filas"]]}


# ------------------------------------------------------------------ corrida


def leer_pagina(tarea: tuple[str, str]) -> tuple[str, list[tuple]]:
    """Lo mismo que extractores/sniim.py::parsear_resultados, con el parser como parámetro."""
    ruta, parser = tarea
    html = Path(ruta).read_text(encoding="utf-8")
    tabla = BeautifulSoup(html, parser).select_one("table#tblResultados")
    filas = []
    if tabla is not None:
        for tr in tabla.find_all("tr"):
            celdas = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(celdas) == len(CAMPOS) and celdas[0][:1].isdigit():
                filas.append(tuple(celdas))
    return Path(ruta).name, filas


def tasa_error(resultados: list[tuple[str, list[tuple]]], esperado: dict) -> tuple[float, int]:
    """% de filas esperadas que no se recuperaron idénticas (perdidas o con otro contenido)."""
    total = malas = 0
    for nombre, filas in resultados:
        objetivo = [tuple(f) for f in esperado[nombre]]
        total += len(objetivo)
        leidas = set(filas)
        malas += sum(f not in leidas for f in objetivo)
    return round(100 * malas / total, 3), total


def correr(procesos: int, parser: str, formato: str, lote: int = 10) -> dict:
    """Una corrida completa sobre todas las páginas del banco. Devuelve tiempo y tasa de error."""
    if not MANIFIESTO.exists():
        raise SystemExit("Primero genera el banco: python -m laboratorio.banco_sniim generar")
    paginas = sorted(PAGINAS.glob("pagina_*.html"))
    tareas = [(str(p), parser) for p in paginas]
    with tempfile.TemporaryDirectory() as tmp:
        inicio = time.perf_counter()
        if procesos == 1:
            resultados = [leer_pagina(t) for t in tareas]
        else:
            with Pool(procesos) as pool:
                resultados = pool.map(leer_pagina, tareas, chunksize=lote)
        tabla = pd.DataFrame([f for _, filas in resultados for f in filas], columns=CAMPOS)
        destino = Path(tmp) / f"salida.{formato}"
        if formato == "csv":
            tabla.to_csv(destino, index=False)
        else:
            tabla.to_parquet(destino, index=False)
        tiempo = time.perf_counter() - inicio
        peso_kb = destino.stat().st_size / 1024
    esperado = json.loads((BANCO / "esperado.json").read_text(encoding="utf-8"))
    error, filas_esperadas = tasa_error(resultados, esperado)
    return {
        "tiempo_s": round(tiempo, 4),
        "tasa_error": error,
        "filas_leidas": int(len(tabla)),
        "filas_esperadas": int(filas_esperadas),
        "paginas": len(paginas),
        "peso_salida_kb": round(peso_kb, 1),
    }


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "probar"
    if accion == "generar":
        m = generar()
        print(f"{len(m)} páginas, {m['filas_esperadas'].sum():,} filas esperadas")
        print(m["dano"].value_counts().to_string())
    else:
        print(correr(1, "html.parser", "csv"))
