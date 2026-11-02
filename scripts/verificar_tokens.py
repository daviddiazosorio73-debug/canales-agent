"""Verifica los tokens de YouTube (sin Claude): que cada secreto REFRESH_TOKEN_<CANAL> abra el canal correcto
(youtube_id de canales.json) y que tenga el permiso de estadísticas (YouTube Analytics).
Sale con error (GitHub avisa por correo) si algún token apunta a otro canal, falta o no tiene Analytics.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from runner import token_file  # noqa: E402
from investigacion import creds  # noqa: E402


def main():
    from googleapiclient.discovery import build
    canales = json.loads((ROOT / "canales.json").read_text())
    hoy = datetime.now(timezone.utc)
    malos = []
    for canal, cfg in canales.items():
        if canal.startswith("_") or not cfg.get("activo"):
            continue
        if not token_file(canal, cfg):
            malos.append(f"{canal}: falta el secreto {cfg['secreto']}")
            continue
        try:
            c = creds(canal)
            yt = build("youtube", "v3", credentials=c, client_options={"api_endpoint": "https://www.googleapis.com/"})
            ch = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
            if ch["id"] != cfg.get("youtube_id"):
                malos.append(f"{canal}: el token abre «{ch['snippet']['title']}» ({ch['id']}), no {cfg.get('youtube_id')}")
                continue
            ya = build("youtubeAnalytics", "v2", credentials=c, client_options={"api_endpoint": "https://youtubeanalytics.googleapis.com/"})
            r = ya.reports().query(ids="channel==MINE", startDate=(hoy - timedelta(days=28)).strftime("%Y-%m-%d"),
                                   endDate=hoy.strftime("%Y-%m-%d"), metrics="views,estimatedMinutesWatched").execute()
            fila = (r.get("rows") or [[0, 0]])[0]
            print(f"OK {canal}: {ch['snippet']['title']} · 28 días: {fila[0]} vistas, {fila[1]} minutos vistos")
        except Exception as e:
            malos.append(f"{canal}: {str(e)[:200]}")
    if malos:
        print("PROBLEMAS:\n - " + "\n - ".join(malos))
        sys.exit(1)


if __name__ == "__main__":
    main()
