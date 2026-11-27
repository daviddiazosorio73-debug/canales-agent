"""Cambia la hora programada (publishAt) de videos ya subidos y privados. Lee .github/fijar_hora.json:
{"canal": "top10-redes", "videos": {"<video_id>": "2026-11-29T11:30:00Z"}}. Costo: 50 unidades por video."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

cfg = json.loads((Path(__file__).resolve().parent.parent / ".github" / "fijar_hora.json").read_text())
yt = service(cfg["canal"])
for vid, hora in cfg["videos"].items():
    st = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]
    body = {"id": vid, "status": {"privacyStatus": "private", "publishAt": hora,
                                  "selfDeclaredMadeForKids": st.get("selfDeclaredMadeForKids", False)}}
    if "containsSyntheticMedia" in st:
        body["status"]["containsSyntheticMedia"] = st["containsSyntheticMedia"]
    r = yt.videos().update(part="status", body=body).execute()
    print(vid, "→", r["status"].get("publishAt"))
