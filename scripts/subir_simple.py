"""Sube un video ya hecho con metadatos de un JSON.
Uso: python subir_simple.py items.json
items.json: [{"archivo","titulo","descripcion","tags":[],"publicar_en":null|"RFC3339Z","miniatura":null|ruta,"sintetico":bool}]
Escribe el resultado (id) en el mismo JSON.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import upload  # noqa: E402
from googleapiclient.http import MediaFileUpload  # noqa: E402

p = Path(sys.argv[1])
items = json.loads(p.read_text())
yt = upload.service("es")
for it in items:
    if it.get("id"):
        print("= ya subido", it["titulo"]); continue
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": bool(it.get("sintetico"))}
    if it.get("publicar_en"):
        status.update(privacyStatus="private", publishAt=it["publicar_en"])
    else:
        status["privacyStatus"] = "public"
    body = {"snippet": {"title": it["titulo"][:100], "description": it["descripcion"][:4900],
                        "tags": it.get("tags", []), "categoryId": "29",
                        "defaultLanguage": "es", "defaultAudioLanguage": "es"},
            "status": status}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(it["archivo"], chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    it["id"] = resp["id"]
    if it.get("miniatura"):
        try:
            yt.thumbnails().set(videoId=resp["id"], media_body=MediaFileUpload(it["miniatura"])).execute()
        except Exception as e:  # miniaturas personalizadas pueden requerir canal verificado
            print("AVISO miniatura:", str(e)[:200])
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print("OK", it["titulo"], "https://youtu.be/" + resp["id"], status["privacyStatus"], it.get("publicar_en") or "")
