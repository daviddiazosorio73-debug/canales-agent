"""Tecno Log IA (@tecnologiapperu): publica Shorts en YouTube, Facebook e Instagram.
Desde el 24-nov-2026: 7 diarios dom-vie (sábado descanso), generados del catálogo por tecnologia_gen.py.

Cola: canales/tecnologia/cola.json  →  [{"clave","archivo","titulo","descripcion","tags","publicar_en"(RFC3339Z), ...}]
Videos: canales/tecnologia/videos/<archivo>  (vertical 1080x1920, ya renderizados; sin voz).

Cada hora (workflow tecnologia.yml):
  1) YouTube: sube programado (privado + publishAt) lo que sale en las próximas 36 h.
     Si la hora ya pasó (p. ej. el secreto llegó tarde), lo publica al momento, pero solo 1 atrasado por corrida.
  2) Facebook + Instagram (Reels): publica lo que ya llegó a su hora.
Secretos: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REFRESH_TOKEN_TECNOLOGIA, META_PAGE_TOKEN_TECNOLOGIA.
Si falta un secreto, esa red se salta sin fallar. Nunca imprime tokens (repo público).
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "canales" / "tecnologia"
COLA = DIR / "cola.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "daviddiazosorio73-debug/canales-agent")
VENTANA_H = 30
CUOTA_F = ROOT / "canales" / "cuota.json"  # pausa compartida con el motor (cuota diaria de YouTube)


def ahora():
    return datetime.now(timezone.utc)


def fecha(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def guardar(cola):
    COLA.write_text(json.dumps(cola, ensure_ascii=False, indent=2) + "\n")


def token_youtube():
    rt = os.environ.get("REFRESH_TOKEN_TECNOLOGIA")
    if not (rt and os.environ.get("GOOGLE_CLIENT_ID")):
        return False
    d = Path.home() / ".yt-agent"
    d.mkdir(exist_ok=True)
    (d / "token_tecnologia.json").write_text(json.dumps({
        "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": rt, "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]}))
    return True


def youtube(cola):
    if not token_youtube():
        print("YouTube: falta REFRESH_TOKEN_TECNOLOGIA; no se sube nada.")
        return
    import upload
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    if CUOTA_F.exists():
        hasta = fecha(json.loads(CUOTA_F.read_text())["hasta"])
        if ahora() < hasta:
            print("YouTube: cuota en pausa hasta", hasta.isoformat(), "(la comparten todos los canales)")
            return
    yt = upload.service("tecnologia")
    import tecnologia_gen
    atrasados = 0
    for it in sorted(cola, key=lambda x: x["publicar_en"]):
        if it.get("youtube_id") or it.get("pausado"):
            continue
        t = fecha(it["publicar_en"])
        if t > ahora() + timedelta(hours=VENTANA_H):
            continue
        status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}
        if t > ahora() + timedelta(minutes=5):
            status.update(privacyStatus="private", publishAt=it["publicar_en"])
        else:
            if atrasados >= 1:
                continue
            atrasados += 1
            status["privacyStatus"] = "public"
        body = {"snippet": {"title": it["titulo"][:100], "description": it["descripcion"][:4900],
                            "tags": it.get("tags", []), "categoryId": "26",
                            "defaultLanguage": "es", "defaultAudioLanguage": "es"}, "status": status}
        try:
            archivo = tecnologia_gen.asegurar_video(it)
        except Exception as e:
            print("Render: error", it["clave"], str(e)[:300])
            it["render_error"] = str(e)[:300]
            guardar(cola)
            continue
        try:
            req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(
                str(archivo), chunksize=8 * 1024 * 1024, resumable=True))
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
        except HttpError as e:
            print("YouTube: error", it["clave"], upload.razon(e) if hasattr(upload, "razon") else str(e)[:200])
            if any(k in str(e) for k in upload.CUOTA):
                # Pausa compartida hasta el reinicio (07:00 UTC = 02:00 Lima), igual que el motor
                h = ahora().replace(hour=7, minute=5, second=0, microsecond=0)
                if h <= ahora():
                    h += timedelta(days=1)
                CUOTA_F.write_text(json.dumps({"hasta": h.strftime("%Y-%m-%dT%H:%M:%SZ"), "motivo": "Tecno Log IA: cuota agotada"}))
                print("YouTube: cuota agotada; pausa hasta", h.isoformat())
                return
            continue
        it["youtube_id"] = resp["id"]
        it["youtube_url"] = "https://youtube.com/shorts/" + resp["id"]
        guardar(cola)
        print("YouTube OK", it["clave"], it["youtube_url"], status["privacyStatus"], status.get("publishAt", ""))


def meta_reels(cola):
    tok = os.environ.get("META_PAGE_TOKEN_TECNOLOGIA")
    if not tok:
        print("Meta: falta META_PAGE_TOKEN_TECNOLOGIA; no se publica en Facebook/Instagram.")
        return
    import meta
    try:
        page_id, ig_id, ptok = meta.ids(tok, os.environ.get("META_PAGINA_TECNOLOGIA") or None)
    except Exception as e:
        print("Meta: no pude leer la Página:", meta.limpio(str(e))[:200])
        return
    for it in sorted(cola, key=lambda x: x["publicar_en"]):
        if fecha(it["publicar_en"]) > ahora() or it.get("pausado"):
            continue
        if it.get("meta_intentos", 0) >= 3:
            continue
        try:
            import tecnologia_gen
            archivo = tecnologia_gen.asegurar_video(it)
        except Exception as e:
            print("Render (Meta): error", it["clave"], str(e)[:200])
            continue
        texto = it.get("texto_reel") or it["descripcion"]
        hecho = False
        for red, campo in (("facebook", "facebook_url"), ("instagram", "instagram_url")):
            if it.get(campo) or (red == "instagram" and not ig_id):
                continue
            try:
                if red == "facebook":
                    url = meta.reel_facebook(page_id, ptok, archivo, texto)
                else:
                    url = meta.reel_instagram(ig_id, ptok, archivo, texto)
                it[campo] = url
                hecho = True
                print("Meta OK", red, it["clave"], url)
            except Exception as e:
                it["meta_intentos"] = it.get("meta_intentos", 0) + 1
                it["meta_error"] = meta.limpio(str(e))[:300]
                print("Meta: error", red, it["clave"], it["meta_error"])
            guardar(cola)
        if hecho:
            return  # un Reel por corrida y por red: evita ráfagas


def necesita_render(cola):
    """¿Hay Shorts generados por subir en la ventana sin su MP4? (para instalar el navegador solo si hace falta)"""
    lim = ahora() + timedelta(hours=VENTANA_H)
    return any(it.get("gen") and not it.get("youtube_id") and fecha(it["publicar_en"]) <= lim
               and not (DIR / "videos" / it["archivo"]).exists() for it in cola)


if __name__ == "__main__":
    cola = json.loads(COLA.read_text())
    if "--necesita-render" in sys.argv:
        try:
            import tecnologia_gen
            tecnologia_gen.planificar(cola)
            guardar(cola)
        except Exception:
            print("si"); sys.exit(0)
        print("si" if necesita_render(cola) else "no")
        sys.exit(0)
    try:
        import tecnologia_gen
        n = tecnologia_gen.planificar(cola)
        guardar(cola)
        print("Plan:", n, "Shorts agregados o reubicados")
    except Exception as e:
        print("Plan: no pude leer el catálogo:", str(e)[:200])
    youtube(cola)
    meta_reels(cola)
    guardar(cola)
