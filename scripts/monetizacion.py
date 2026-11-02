"""Tablero de monetización (sin Claude): avance de cada canal hacia el Programa de Socios de YouTube.

Escribe investigacion/monetizacion.md con suscriptores, horas vistas (365 días, videos largos) y vistas de
Shorts (90 días), frente a las metas vigentes y a las del 1-feb-2027. Datos: YouTube Data API + Analytics.
Nota: YouTube cuenta solo horas PÚBLICAS de videos largos; Analytics se acerca a esa cifra, pero la oficial está
en YouTube Studio → Ganar dinero.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from runner import token_file  # noqa: E402
from investigacion import creds  # noqa: E402

METAS = {"hoy": (1000, 4000, 10_000_000), "2027-02-01": (1000, 8000, 20_000_000)}


def por_tipo(ya, desde, hasta, metrica):
    """{tipo de contenido: valor}; si la dimensión no está disponible, {'TOTAL': valor}."""
    q = dict(ids="channel==MINE", startDate=desde, endDate=hasta, metrics=metrica)
    try:
        r = ya.reports().query(dimensions="creatorContentType", **q).execute()
        return {fila[0]: fila[1] for fila in r.get("rows", [])}
    except Exception:
        r = ya.reports().query(**q).execute()
        return {"TOTAL": (r.get("rows") or [[0]])[0][0]}


def main():
    from googleapiclient.discovery import build
    canales = json.loads((ROOT / "canales.json").read_text())
    hoy = datetime.now(timezone.utc)
    f = lambda d: (hoy - timedelta(days=d)).strftime("%Y-%m-%d")  # noqa: E731
    L = [f"# Monetización — {hoy:%Y-%m-%d}\n",
         "Metas: hoy 1000 suscriptores + 4000 h (365 días) o 10 M de vistas de Shorts (90 días). "
         "Desde el 1-feb-2027: 8000 h o 20 M de Shorts. Cifra oficial: YouTube Studio → Ganar dinero.\n",
         "| Canal | Suscriptores | Horas largos (365 d) | Vistas Shorts (90 d) | Falta para hoy | Falta desde feb-2027 |",
         "|---|---|---|---|---|---|"]
    for canal, cfg in canales.items():
        if canal.startswith("_") or not cfg.get("activo") or not token_file(canal, cfg):
            continue
        try:
            c = creds(canal)
            yt = build("youtube", "v3", credentials=c, client_options={"api_endpoint": "https://www.googleapis.com/"})
            ya = build("youtubeAnalytics", "v2", credentials=c,
                       client_options={"api_endpoint": "https://youtubeanalytics.googleapis.com/"})
            subs = int(yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"].get("subscriberCount", 0))
            minutos = por_tipo(ya, f(365), f(0), "estimatedMinutesWatched")
            vistas = por_tipo(ya, f(90), f(0), "views")
            aprox = "TOTAL" in minutos
            horas = int((minutos.get("VIDEO_ON_DEMAND", 0) if not aprox else minutos["TOTAL"]) / 60)
            shorts = int(vistas.get("SHORTS", 0) if "TOTAL" not in vistas else 0)
            faltas = []
            for clave, (ms, mh, mv) in METAS.items():
                fs, fh, fv = max(0, ms - subs), max(0, mh - horas), max(0, mv - shorts)
                faltas.append("✅ cumple" if fs == 0 and (fh == 0 or fv == 0) else
                              f"{fs} subs + ({fh} h o {fv:,} vistas de Shorts)".replace(",", " "))
            L.append(f"| {cfg['nombre']} | {subs} | {horas}{' (aprox., incluye Shorts)' if aprox else ''} | "
                     f"{shorts:,}".replace(",", " ") + f" | {faltas[0]} | {faltas[1]} |")
        except Exception as e:
            L.append(f"| {cfg['nombre']} | error: {str(e)[:90]} | | | | |")
    (ROOT / "investigacion" / "monetizacion.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
