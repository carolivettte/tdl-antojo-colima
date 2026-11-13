"""Fiabilidad y disponibilidad de la captura diaria, calculadas solo con la bitácora.

Servicio medido: "los precios del día del SNIIM quedan capturados en bronce".
Hora esperada: una ejecución programada por día entre las 16:00 y las 18:00 UTC
(10:15 hora de Colima en el schedule de GitHub; 10:30 en el disparador externo cron-job.org).

Reglas (las mismas del objetivo de calidad 1, calidad/objetivos.md):
  - Una ejecución en esa ventana es "programada"; cualquier otra es manual y no cuenta en la tasa.
  - Un día es exitoso si su ejecución programada terminó "ok", o "vacio" con la fuente sin publicar.
  - Un día sin ejecución programada, o con "error", es una falla.
  - Tiempo de reparación de una falla = desde la hora esperada (16:15 UTC) hasta la siguiente
    ejecución exitosa de esa fuente (programada o manual).

Métricas:
  tasa de éxito = días exitosos / días esperados
  MTBF = tiempo en operación / número de fallas
  MTTR = suma de tiempos de reparación / número de fallas
  A    = MTBF / (MTBF + MTTR)

Uso:
    python -m scripts.fiabilidad    # escribe calidad/fiabilidad.md y data/bitacora/fiabilidad.json
"""

import json
from datetime import datetime, time, timedelta, timezone

import pandas as pd

from extractores.config import DATA, RAIZ

BITACORA = DATA / "bitacora" / "ejecuciones.csv"
INCIDENTES = RAIZ / "calidad" / "incidentes.csv"
REPORTE = RAIZ / "calidad" / "fiabilidad.md"
JSON = DATA / "bitacora" / "fiabilidad.json"

INICIO_OPERACION = pd.Timestamp("2026-11-09", tz="UTC")  # primer día con captura programada
HORA_ESPERADA = time(16, 15)
VENTANA = (time(16, 0), time(18, 0))
OBJETIVO = 0.95
VENTANA_E1 = ("2026-11-06", "2026-11-13")  # ventana que pide la rúbrica de E1


def cargar(ruta=BITACORA) -> pd.DataFrame:
    df = pd.read_csv(ruta)
    df["inicio_utc"] = pd.to_datetime(df["inicio_utc"], utc=True, format="ISO8601")
    df["fin_utc"] = pd.to_datetime(df["fin_utc"], utc=True, format="ISO8601")
    hora = df["inicio_utc"].dt.time
    df["tipo"] = ((hora >= VENTANA[0]) & (hora < VENTANA[1]) & df["modo"].eq("diaria")).map({True: "programada", False: "manual"})
    return df


def dias_esperados(ahora: pd.Timestamp) -> list[pd.Timestamp]:
    """Días cuya ventana programada ya cerró (el día de hoy cuenta solo después de las 18:00 UTC)."""
    ultimo = ahora.normalize() if ahora.time() >= VENTANA[1] else ahora.normalize() - timedelta(days=1)
    return list(pd.date_range(INICIO_OPERACION, ultimo, freq="D"))


def evaluar(df: pd.DataFrame, ahora: pd.Timestamp, fuente: str = "sniim") -> dict:
    sniim = df[df["fuente"] == fuente]
    exitos = sniim[sniim["estado"].isin(["ok", "vacio"])]
    programadas = sniim[sniim["tipo"] == "programada"]
    dias, fallas = [], []
    for dia in dias_esperados(ahora):
        esperado = datetime.combine(dia.date(), HORA_ESPERADA, tzinfo=timezone.utc)
        del_dia = programadas[programadas["inicio_utc"].dt.normalize() == dia]
        ok = del_dia["estado"].isin(["ok", "vacio"]).any()
        estado = "ok" if ok else ("error" if len(del_dia) else "no se ejecuto")
        dias.append({"dia": dia.date().isoformat(), "estado": estado, "ejecuciones": len(del_dia)})
        if not ok:
            siguiente = exitos[exitos["inicio_utc"] > pd.Timestamp(esperado)]["fin_utc"].min()
            reparada = pd.notna(siguiente)
            fin = siguiente if reparada else ahora
            fallas.append(
                {
                    "dia": dia.date().isoformat(),
                    "tipo": estado,
                    "esperada_utc": esperado.isoformat(),
                    "restablecida_utc": fin.isoformat() if reparada else "",
                    "horas_reparacion": round((fin - pd.Timestamp(esperado)).total_seconds() / 3600, 2),
                }
            )
    periodo_h = (ahora - INICIO_OPERACION).total_seconds() / 3600
    caido_h = sum(f["horas_reparacion"] for f in fallas)
    n = len(fallas)
    mtbf = (periodo_h - caido_h) / n if n else None
    mttr = caido_h / n if n else 0.0
    disp = mtbf / (mtbf + mttr) if n else 1.0
    exitosos = sum(d["estado"] == "ok" for d in dias)
    # Tasa por ejecución: cada corrida de cualquier fuente cuenta; éxito = terminó sin error.
    total_ej = len(df)
    ok_ej = int(df["estado"].isin(["ok", "vacio"]).sum())
    prog = df[(df["fuente"] == fuente) & (df["tipo"] == "programada")]
    ok_prog = int(prog["estado"].isin(["ok", "vacio"]).sum())
    return {
        "calculado_utc": ahora.isoformat(timespec="seconds"),
        "fuente": fuente,
        "periodo": {
            "desde": INICIO_OPERACION.date().isoformat(),
            "hasta": ahora.isoformat(timespec="minutes"),
            "horas": round(periodo_h, 1),
        },
        "ventana_pedida": {"desde": VENTANA_E1[0], "hasta": VENTANA_E1[1]},
        "ejecuciones_totales": total_ej,
        "ejecuciones_exitosas": ok_ej,
        "tasa_exito_ejecucion": round(ok_ej / total_ej, 4) if total_ej else None,
        "ejecuciones_programadas": len(prog),
        "tasa_exito_programadas": round(ok_prog / len(prog), 4) if len(prog) else None,
        "dias_esperados": len(dias),
        "dias_exitosos": exitosos,
        "tasa_exito": round(exitosos / len(dias), 4) if dias else None,
        "objetivo": OBJETIVO,
        "fallas": fallas,
        "mtbf_h": round(mtbf, 2) if mtbf is not None else None,
        "mttr_h": round(mttr, 2),
        "disponibilidad": round(disp, 4),
        "dias": dias,
        "ejecuciones_por_estado": df.groupby(["fuente", "tipo", "estado"]).size().reset_index(name="n").to_dict("records"),
    }


def _hora(iso: str) -> str:
    return iso[:16].replace("T", " ") if iso else "pendiente"


def escribir_reporte(r: dict) -> None:
    def pct(x):
        return "—" if x is None else f"{x * 100:.1f} %"

    cumple = r["tasa_exito"] is not None and r["tasa_exito"] >= r["objetivo"]
    veredicto = f"objetivo ≥ {r['objetivo']:.0%}: {'cumple' if cumple else 'no cumple'}"
    lineas = [
        "# Fiabilidad y disponibilidad de la captura",
        "",
        f"Generado automáticamente por `scripts/fiabilidad.py` el {r['calculado_utc']} a partir de "
        "`data/bitacora/ejecuciones.csv`. Se recalcula después de cada captura.",
        "",
        f"Servicio medido: captura diaria del SNIIM en bronce. Periodo: {r['periodo']['desde']} a "
        f"{r['periodo']['hasta']} UTC ({r['periodo']['horas']} h).",
        "",
        f"Ventana que pide E1: {r['ventana_pedida']['desde']} a {r['ventana_pedida']['hasta']}. La captura programada "
        f"empezó a operar el {r['periodo']['desde']}: los días anteriores no había sistema que medir, así que "
        f"la medición cubre {r['dias_esperados']} días y no 7.",
        "",
        "| Métrica | Valor | Cómo se calcula |",
        "|---|---|---|",
        f"| **Tasa de éxito por ejecución** | **{pct(r['tasa_exito_ejecucion'])}** | "
        f"{r['ejecuciones_exitosas']} de {r['ejecuciones_totales']} ejecuciones de todas las fuentes terminaron sin error |",
        f"| Tasa de éxito de las ejecuciones programadas | {pct(r['tasa_exito_programadas'])} | "
        f"de {r['ejecuciones_programadas']} ejecuciones programadas del SNIIM |",
        f"| Días esperados | {r['dias_esperados']} | Un día por cada ventana programada cerrada (16:00–18:00 UTC) |",
        f"| Días exitosos | {r['dias_exitosos']} | Ejecución programada con estado ok |",
        f"| **Tasa de éxito por día** | **{pct(r['tasa_exito'])}** | exitosos / esperados ({veredicto}) |",
        f"| Fallas | {len(r['fallas'])} | Días sin ejecución programada o con error |",
        f"| **MTBF** | **{r['mtbf_h']} h** | tiempo en operación / fallas |",
        f"| **MTTR** | **{r['mttr_h']} h** | tiempo de reparación total / fallas |",
        f"| **Disponibilidad A** | **{pct(r['disponibilidad'])}** | MTBF / (MTBF + MTTR) |",
        "",
        "## Fallas",
        "",
        "| Día | Tipo | Hora esperada (UTC) | Restablecida (UTC) | Horas de reparación |",
        "|---|---|---|---|---|",
    ]
    lineas += [
        f"| {f['dia']} | {f['tipo']} | {f['esperada_utc'][11:16]} | {_hora(f['restablecida_utc'])} | {f['horas_reparacion']} |"
        for f in r["fallas"]
    ] or ["| — | — | — | — | — |"]
    lineas += [
        "",
        "Causas y acciones correctivas: `calidad/incidentes.csv`.",
        "",
        "## Día por día",
        "",
        "| Día | Estado | Ejecuciones programadas |",
        "|---|---|---|",
    ]
    lineas += [f"| {d['dia']} | {d['estado']} | {d['ejecuciones']} |" for d in r["dias"]]
    lineas += [
        "",
        "## Todas las ejecuciones por fuente, tipo y estado",
        "",
        "| Fuente | Tipo | Estado | Ejecuciones |",
        "|---|---|---|---|",
    ]
    lineas += [f"| {e['fuente']} | {e['tipo']} | {e['estado']} | {e['n']} |" for e in r["ejecuciones_por_estado"]]
    lineas.append("")
    REPORTE.write_text("\n".join(lineas), encoding="utf-8")


def main() -> None:
    r = evaluar(cargar(), pd.Timestamp.now(tz="UTC"))
    JSON.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_reporte(r)
    print(f"Tasa de éxito {r['tasa_exito']}, MTBF {r['mtbf_h']} h, MTTR {r['mttr_h']} h, A {r['disponibilidad']}")


if __name__ == "__main__":
    main()
