"""Investigación semanal gratuita (sin Claude): qué funcionó en tu canal y qué está explotando en tu nicho.

Escribe investigacion/<canal>.md con:
  1. Tus videos de los últimos 28 días por vistas, duración media vista y % visto (YouTube Analytics).
  2. Los videos del nicho más vistos de los últimos 7 días, con vistas por hora (outliers) (YouTube Data API).
Claude solo lee este resumen corto el domingo para elegir el video insignia de la semana.
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from runner import token_file  # noqa: E402


def creds(canal):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    info = json.loads((Path.home() / ".yt-agent" / f"token_{canal}.json").read_text())
    info.pop("scopes", None)  # sin limitar permisos: así el token trae también YouTube Analytics
    c = Credentials.from_authorized_user_info(info)
    c._token_uri = "https://www.googleapis.com/oauth2/v4/token"
    c.refresh(Request())
    return c


def propios_data_api(yt, hoy, dias=28):
    """Tus videos de los últimos `dias` con vistas, likes y comentarios públicos (YouTube Data API)."""
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    desde = hoy - timedelta(days=dias)
    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50, pageToken=tok).execute()
        for it in r.get("items", []):
            pub = it["contentDetails"].get("videoPublishedAt")
            if pub and datetime.fromisoformat(pub.replace("Z", "+00:00")) >= desde:
                ids.append(it["contentDetails"]["videoId"])
        tok = r.get("nextPageToken")
        if not tok or len(ids) >= 200:
            break
    filas = []
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50])).execute()["items"]:
            s = v["statistics"]
            pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            dias_pub = max(1.0, (hoy - pub).total_seconds() / 86400)
            n = int(s.get("viewCount", 0))
            filas.append((n / dias_pub, n, int(s.get("likeCount", 0)), int(s.get("commentCount", 0)),
                          v["snippet"]["title"][:70], pub.strftime("%Y-%m-%d")))
    L = [f"## Tus videos de los últimos {dias} días (Data API, respaldo sin Analytics)",
         f"{len(filas)} videos publicados. Orden: vistas por día desde su publicación.\n",
         "| Video | Publicado | Vistas | Vistas/día | Likes | Comentarios |", "|---|---|---|---|---|---|"]
    for vpd, n, lk, cm, t, f in sorted(filas, reverse=True)[:15]:
        L.append(f"| {t} | {f} | {n} | {vpd:.1f} | {lk} | {cm} |")
    return L


def historial_canal(yt, canal, hoy, out_dir):
    """Guarda cada semana suscriptores, vistas y número de videos del canal (para seguir la monetización)."""
    s = yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    p = out_dir / f"{canal}.historial.json"
    h = json.loads(p.read_text()) if p.exists() else []
    fila = {"fecha": hoy.strftime("%Y-%m-%d"), "suscriptores": int(s.get("subscriberCount", 0)),
            "vistas": int(s.get("viewCount", 0)), "videos": int(s.get("videoCount", 0))}
    h = [x for x in h if x.get("fecha") != fila["fecha"]] + [fila]
    p.write_text(json.dumps(h[-104:], ensure_ascii=False, indent=2))


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
            # Respaldo con la Data API (no necesita permiso de Analytics): vistas, likes y comentarios públicos
            try:
                L += propios_data_api(yt, hoy)
            except Exception as e2:
                L.append(f"_Respaldo Data API no disponible: {str(e2)[:120]}_")
        try:
            historial_canal(yt, canal, hoy, out_dir)
        except Exception as e:
            print(f"Aviso historial {canal}: {str(e)[:120]}")
        # 2) Outliers del nicho (últimos 7 días)
        L.append("\n## Lo más visto del nicho (7 días)\n| Video | Canal | Vistas | Vistas/hora |\n|---|---|---|---|")
        desde = (hoy - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        vistos = {}
        for q in cfg.get("nicho", [])[:5]:
            res = yt.search().list(part="id", q=q, type="video", order="viewCount", publishedAfter=desde,
                                   maxResults=10, relevanceLanguage=cfg.get("idioma", "es")).execute()
            for it in res.get("items", []):
                vistos[it["id"]["videoId"]] = q
        etiquetas, hashtags = Counter(), Counter()
        try:
            propio = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
        except Exception:
            propio = None
        if vistos:
            filas = []
            ids = list(vistos)
            for i in range(0, len(ids), 50):
                for v in yt.videos().list(part="snippet,statistics", id=",".join(ids[i:i + 50])).execute()["items"]:
                    pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
                    h = max(1, (hoy - pub).total_seconds() / 3600)
                    n = int(v["statistics"].get("viewCount", 0))
                    filas.append((n / h, n, v["snippet"]["title"][:70], v["snippet"]["channelTitle"][:30]))
                    if v["snippet"]["channelId"] != propio:
                        etiquetas.update({t.strip().lower() for t in v["snippet"].get("tags", []) if 2 < len(t.strip()) <= 30})
                        hashtags.update({x.lower() for x in re.findall(r"#(\w{3,30})", v["snippet"].get("description", ""))})
            for vph, n, t, ch in sorted(filas, reverse=True)[:15]:
                L.append(f"| {t} | {ch} | {n} | {vph:.0f} |")
        # SEO del nicho para metadata.py: etiquetas y hashtags que más repiten los videos que están funcionando
        generic = {"shorts", "short", "youtube", "viral", "video", "fyp", "parati", "foryou", "trending", "reels"}
        (out_dir / f"{canal}.seo.json").write_text(json.dumps({
            "fecha": hoy.strftime("%Y-%m-%d"),
            "tags": [t for t, n in etiquetas.most_common(40) if n >= 2 and t.replace(" ", "") not in generic][:20],
            "hashtags": [h for h, n in hashtags.most_common(20) if n >= 2 and h not in generic][:5],
        }, ensure_ascii=False, indent=2))
        (out_dir / f"{canal}.md").write_text("\n".join(L) + "\n")
        print(f"OK investigacion/{canal}.md")


if __name__ == "__main__":
    main()
