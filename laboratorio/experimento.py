"""Corre los diseños de experimentos de E2 sobre el banco local del SNIIM (laboratorio/banco_sniim.py).

Pregunta de ingeniería: ¿qué configuración del extractor procesa más rápido las páginas del SNIIM
sin perder filas?

Factores y niveles (bajo = -1, alto = +1):
  A  procesos   1 | 4            procesos en paralelo que leen las páginas
  B  parser     html.parser | lxml   motor que interpreta el HTML
  C  formato    csv | parquet    formato en que se guarda el resultado
  D  lote       1 | 25           páginas que recibe cada proceso por tarea (solo en el 2^4)

Diseños:
  2k3           2^3 completo, 1 réplica por bloque. Se corren 3 bloques (sesiones) -> 3 réplicas, 24 corridas.
  bifactorial   procesos (1, 2, 4) x parser (2 niveles), 1 réplica por bloque -> 3 réplicas, 18 corridas.
  2k4           2^4 completo, una réplica (16 corridas). La media fracción 2^(4-1) con I = ABCD son las
                8 corridas con A*B*C*D = +1; se comparan sus estimaciones con las del 2^4.
  confirmacion  la mejor combinación y la actual, 5 corridas de cada una intercaladas al azar en una sesión
                nueva, para comparar la razón de tiempos observada con la que predice el modelo.

Bloqueo: cada bloque es una sesión de trabajo distinta (mañana, tarde, noche). Entre sesiones cambian
cosas que no controlamos (procesos del sistema, temperatura, caché del disco); el bloque absorbe esa
variación para que no se confunda con los factores.

Registro: inicio_utc es la hora en que empieza cada corrida. En el bloque 1 de 2k3 y de bifactorial se
guardó la hora en que terminó (defecto corregido después de esa sesión; la diferencia es de 6 a 20 s y no
cambia el orden de las corridas).

Aleatorización: dentro de cada bloque el orden de las corridas se sortea con una semilla que depende del
diseño y del bloque, y se guarda en el plan. Antes de la primera corrida de cada sesión se hace una corrida
de calentamiento que no se registra (carga librerías y el caché del disco).

Uso:
    python -m laboratorio.experimento correr --diseno 2k3 --bloque 1 --sesion "viernes mañana"
    python -m laboratorio.experimento correr --diseno bifactorial --bloque 1 --sesion "viernes mañana"
    python -m laboratorio.experimento correr --diseno 2k4 --bloque 2 --sesion "viernes tarde"
    python -m laboratorio.experimento confirmar --procesos 4 --parser lxml --formato parquet --lote 10 --sesion "..."
"""

from __future__ import annotations

import argparse
import itertools
import random
import zlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from laboratorio.banco_sniim import correr as correr_banco

RESULTADOS = Path(__file__).resolve().parent / "resultados"
NIVELES = {
    "procesos": {-1: 1, 1: 4},
    "parser": {-1: "html.parser", 1: "lxml"},
    "formato": {-1: "csv", 1: "parquet"},
    "lote": {-1: 1, 1: 25},
}
LOTE_FIJO = 10
FORMATO_FIJO = "csv"


def matriz_2k(factores: list[str]) -> pd.DataFrame:
    """Matriz en orden estándar (Yates): el primer factor alterna más rápido."""
    filas = []
    for signos in itertools.product([-1, 1], repeat=len(factores)):
        filas.append(dict(zip(factores, reversed(signos), strict=True)))
    m = pd.DataFrame(filas)[factores]
    m.insert(0, "corrida_std", range(1, len(m) + 1))
    return m


def plan(diseno: str) -> pd.DataFrame:
    if diseno == "2k3":
        m = matriz_2k(["procesos", "parser", "formato"])
        m["lote"] = 0
    elif diseno == "2k4":
        m = matriz_2k(["procesos", "parser", "formato", "lote"])
        m["en_media_fraccion"] = (m["procesos"] * m["parser"] * m["formato"] * m["lote"]) == 1
    elif diseno == "bifactorial":
        filas = [{"procesos_n": p, "parser": b} for b in (-1, 1) for p in (1, 2, 4)]
        m = pd.DataFrame(filas)
        m.insert(0, "corrida_std", range(1, len(m) + 1))
    else:
        raise ValueError(f"diseño desconocido: {diseno}")
    return m


def configuracion(diseno: str, fila: pd.Series) -> dict:
    if diseno == "bifactorial":
        return {
            "procesos": int(fila["procesos_n"]),
            "parser": NIVELES["parser"][fila["parser"]],
            "formato": FORMATO_FIJO,
            "lote": LOTE_FIJO,
        }
    return {
        "procesos": NIVELES["procesos"][fila["procesos"]],
        "parser": NIVELES["parser"][fila["parser"]],
        "formato": NIVELES["formato"][fila["formato"]],
        "lote": NIVELES["lote"][fila["lote"]] if fila["lote"] != 0 else LOTE_FIJO,
    }


def semilla(diseno: str, bloque: int) -> int:
    return zlib.crc32(f"{diseno}-bloque-{bloque}".encode())


def guardar(filas: list[dict], archivo: str) -> Path:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta = RESULTADOS / archivo
    nuevo = pd.DataFrame(filas)
    if ruta.exists():
        nuevo = pd.concat([pd.read_csv(ruta), nuevo], ignore_index=True)
    nuevo.to_csv(ruta, index=False)
    return ruta


def calentar() -> None:
    print("Calentamiento (no se registra)...", flush=True)
    correr_banco(1, "lxml", "csv", LOTE_FIJO)


def correr_diseno(diseno: str, bloque: int, sesion: str) -> Path:
    ruta = RESULTADOS / f"{diseno}.csv"
    if ruta.exists() and (pd.read_csv(ruta)["bloque"] == bloque).any():
        raise SystemExit(f"El bloque {bloque} de {diseno} ya está registrado; usa otro número de bloque.")
    m = plan(diseno)
    orden = list(m.index)
    s = semilla(diseno, bloque)
    random.Random(s).shuffle(orden)
    calentar()
    filas = []
    for posicion, i in enumerate(orden, start=1):
        fila = m.loc[i]
        cfg = configuracion(diseno, fila)
        print(f"[{posicion}/{len(orden)}] corrida {fila['corrida_std']}: {cfg}", flush=True)
        inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
        res = correr_banco(**cfg)
        print(f"        tiempo {res['tiempo_s']:.2f} s · error {res['tasa_error']} %", flush=True)
        filas.append(
            {
                "diseno": diseno,
                "bloque": bloque,
                "sesion": sesion,
                "semilla": s,
                "orden": posicion,
                **{k: v for k, v in fila.items()},
                **{f"{k}_valor": v for k, v in cfg.items()},
                **res,
                "inicio_utc": inicio,
            }
        )
    return guardar(filas, f"{diseno}.csv")


BASE = {"procesos": 1, "parser": "html.parser", "formato": "csv", "lote": LOTE_FIJO}


def confirmar(cfg: dict, sesion: str, repeticiones: int = 5) -> Path:
    """Corre la mejor configuración y la actual (BASE) `repeticiones` veces cada una, intercaladas al azar.

    Las dos van en la misma sesión porque el bloque pesa mucho: así se confirma la razón de tiempos
    (cuántas veces más rápido), que no depende de la sesión, además del tiempo absoluto.
    """
    tareas = [("mejor", cfg)] * repeticiones + [("actual", BASE)] * repeticiones
    s = semilla("confirmacion", repeticiones)
    random.Random(s).shuffle(tareas)
    calentar()
    filas = []
    for k, (etiqueta, c) in enumerate(tareas, start=1):
        inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
        res = correr_banco(**c)
        print(f"[{k}/{len(tareas)}] {etiqueta}: {c}", flush=True)
        print(f"        tiempo {res['tiempo_s']:.2f} s · error {res['tasa_error']} %", flush=True)
        filas.append(
            {
                "sesion": sesion,
                "semilla": s,
                "orden": k,
                "configuracion": etiqueta,
                **{f"{n}_valor": v for n, v in c.items()},
                **res,
                "inicio_utc": inicio,
            }
        )
    return guardar(filas, "confirmacion.csv")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    c = sub.add_parser("correr")
    c.add_argument("--diseno", required=True, choices=["2k3", "bifactorial", "2k4"])
    c.add_argument("--bloque", type=int, required=True)
    c.add_argument("--sesion", required=True)
    f = sub.add_parser("confirmar")
    f.add_argument("--procesos", type=int, required=True)
    f.add_argument("--parser", required=True)
    f.add_argument("--formato", required=True)
    f.add_argument("--lote", type=int, default=LOTE_FIJO)
    f.add_argument("--sesion", required=True)
    f.add_argument("--repeticiones", type=int, default=5)
    a = ap.parse_args(argv)
    if a.accion == "correr":
        ruta = correr_diseno(a.diseno, a.bloque, a.sesion)
    else:
        cfg = {"procesos": a.procesos, "parser": a.parser, "formato": a.formato, "lote": a.lote}
        ruta = confirmar(cfg, a.sesion, a.repeticiones)
    print(f"Resultados en {ruta.relative_to(Path.cwd()) if ruta.is_relative_to(Path.cwd()) else ruta}")


if __name__ == "__main__":
    main()
