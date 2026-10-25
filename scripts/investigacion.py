"""Investigación semanal gratuita (sin Claude): qué funcionó en tu canal y qué está explotando en tu nicho.

Escribe investigacion/<canal>.md con:
  1. Tus videos de los últimos 28 días por vistas, duración media vista y % visto (YouTube Analytics).
  2. Los videos del nicho más vistos de los últimos 7 días, con vistas por hora (outliers) (YouTube Data API).
Claude solo lee este resumen corto el domingo para elegir el video insignia de la semana.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from runner import token_file  # noqa: E402


def creds(canal):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    c = Credentials.from_authorized_user_file(str(Path.home() / ".yt-agent" / f"token_{canal}.json"))
    c._token_uri = "https://www.googleapis.com/oauth2/v4/token"
    c.refresh(Request())
    return c


def main():
    from googleapiclient.discovery import build
    canales = json.loads((ROOT / "canales.json").read_text())
    out_dir = ROOT / "investigacion"
    out_dir.mkdir(exist_ok=True)
    hoy = datetime.now(timezone.utc)
    for canal, cfg in canales.items():
        if canal.startswith("_") or not cfg.get("activo") or not token_file(canal, cfg):
            continue
        L = [f"# Investigación {cfg['nombre']} — {hoy:%Y-%m-%d}\n"]
        c = creds(canal)
        yt = build("youtube", "v3", credentials=c, client_options={"api_endpoint": "https://www.googleapis.com/"})
        # 1) Analytics propio (requiere permiso yt-analytics.readonly)
        try:
            ya = build("youtubeAnalytics", "v2", credentials=c, client_options={"api_endpoint": "https://youtubeanalytics.googleapis.com/"})
            r = ya.reports().query(ids="channel==MINE", startDate=(hoy - timedelta(days=28)).strftime("%Y-%m-%d"),
                                   endDate=hoy.strftime("%Y-%m-%d"), metrics="views,averageViewDuration,averageViewPercentage,subscribersGained",
                                   dimensions="video", sort="-views", maxResults=10).execute()
            ids = [row[0] for row in r.get("rows", [])]
            tit = {}
            if ids:
                for v in yt.videos().list(part="snippet", id=",".join(ids)).execute()["items"]:
                    tit[v["id"]] = v["snippet"]["title"]
            L.append("## Tus 10 mejores videos (28 días)\n| Video | Vistas | Dur. media (s) | % visto | Subs |\n|---|---|---|---|---|")
            for vid, views, dur, pct, subs in r.get("rows", []):
                L.append(f"| {tit.get(vid, vid)[:70]} | {views} | {dur} | {pct:.0f}% | {subs} |")
        except Exception as e:
            L.append(f"_Analytics no disponible: {str(e)[:160]}. Renueva el token con el permiso yt-analytics.readonly._")
        # 2) Outliers del nicho (últimos 7 días)
        L.append("\n## Lo más visto del nicho (7 días)\n| Video | Canal | Vistas | Vistas/hora |\n|---|---|---|---|")
        desde = (hoy - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        vistos = {}
        for q in cfg.get("nicho", [])[:5]:
            res = yt.search().list(part="id", q=q, type="video", order="viewCount", publishedAfter=desde,
                                   maxResults=10, relevanceLanguage=cfg.get("idioma", "es")).execute()
            for it in res.get("items", []):
                vistos[it["id"]["videoId"]] = q
        if vistos:
            filas = []
            ids = list(vistos)
            for i in range(0, len(ids), 50):
                for v in yt.videos().list(part="snippet,statistics", id=",".join(ids[i:i + 50])).execute()["items"]:
                    pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
                    h = max(1, (hoy - pub).total_seconds() / 3600)
                    n = int(v["statistics"].get("viewCount", 0))
                    filas.append((n / h, n, v["snippet"]["title"][:70], v["snippet"]["channelTitle"][:30]))
            for vph, n, t, ch in sorted(filas, reverse=True)[:15]:
                L.append(f"| {t} | {ch} | {n} | {vph:.0f} |")
        (out_dir / f"{canal}.md").write_text("\n".join(L) + "\n")
        print(f"OK investigacion/{canal}.md")


if __name__ == "__main__":
    main()
