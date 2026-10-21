"""Sube video + miniatura + subtítulos a YouTube (Data API v3, OAuth).

Uso: python upload.py <proyecto_dir> [--canal es|pt]
Credenciales (por canal):  ~/.yt-agent/client_secret.json  (OAuth "Desktop app")
Token guardado en:          ~/.yt-agent/token_<canal>.json  (se crea en el primer login)
Requiere: pip install google-api-python-client google-auth-oauthlib
Nunca publica en público directamente: usa metadata.privacidad (default private)
o programa con metadata.publicar_en (RFC3339).
"""
import sys
from pathlib import Path

from common import load_json, save_json

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
CRED_DIR = Path.home() / ".yt-agent"


def service(canal):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    tok = CRED_DIR / f"token_{canal}.json"
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = CRED_DIR / "client_secret.json"
            if not secret.exists():
                sys.exit(f"Falta {secret}. Ver references/setup.md")
            creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        tok.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def main():
    from googleapiclient.http import MediaFileUpload
    proj = Path(sys.argv[1])
    g = load_json(proj / "guion.json")
    canal = sys.argv[sys.argv.index("--canal") + 1] if "--canal" in sys.argv else g["lang"]
    m = load_json(proj / "salida" / "metadata.json")
    if m["errores"]:
        print("AVISOS de metadata:", *m["errores"], sep="\n - ")
    yt = service(canal)

    status = {"privacyStatus": "private" if m.get("publicar_en") else m["privacidad"],
              "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": bool(g.get("contenido_sintetico", True))}
    if m.get("publicar_en"):
        status["publishAt"] = m["publicar_en"]
    body = {"snippet": {"title": m["titulo"], "description": m["descripcion"], "tags": m["tags"],
                        "categoryId": m["categoria_id"], "defaultLanguage": m["idioma"],
                        "defaultAudioLanguage": m["idioma"]},
            "status": status}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(proj / "salida" / "video.mp4"),
                                                        chunksize=16 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st:
            print(f"subiendo {int(st.progress() * 100)}%")
    vid = resp["id"]
    print("video:", f"https://youtu.be/{vid}")

    yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(proj / "salida" / "miniatura.jpg"))).execute()
    srt = proj / "salida" / "subtitulos.srt"
    if srt.exists():
        yt.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": m["idioma"],
                             "name": m["idioma"].upper(), "isDraft": False}},
                             media_body=MediaFileUpload(str(srt))).execute()
    if m.get("lista_id"):
        yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": m["lista_id"],
                                  "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
    save_json({"video_id": vid, "url": f"https://youtu.be/{vid}", "estado": status},
              proj / "salida" / "publicado.json")
    print("OK publicado.json")


if __name__ == "__main__":
    main()
