"""Instagram + Facebook (Meta) para los Reels del Fundador. Gratis, API oficial, corre en GitHub Actions.

Dos pasos:
  encolar  <proyecto_dir> --canal <canal>   (runner.py, justo después de subir a YouTube)
      Guarda el MP4 vertical como asset de la release "meta-cola" del repo y lo anota en
      canales/<canal>/meta_cola.json con la misma hora de publicación de YouTube.
  publicar                                    (cada hora, después de runner.py)
      Publica lo que ya llegó a su hora: Reel en Instagram + Reel en la Página de Facebook.
      Borra el asset cuando ambos quedan publicados. Reintenta hasta 3 veces.

Config en canales.json → "meta": {"secreto": "META_PAGE_TOKEN_<CANAL>", "tipos": ["short"]}
El secreto es el token de PÁGINA (no vence) con permisos pages_show_list, pages_read_engagement,
pages_manage_posts, instagram_basic, instagram_content_publish. El id de la Página y el de Instagram se
obtienen solos con ese token. Si falta el secreto, no se hace nada (no falla).
Nunca imprime tokens (el repo es público y sus registros también).
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
VER = os.environ.get("META_API_VER", "v26.0")
G = f"https://graph.facebook.com/{VER}"
RELEASE = "meta-cola"
MAX_INTENTOS = 3


def gh(*args, check=True):
    return subprocess.run(["gh", *args], check=check, capture_output=True, text=True)


def caption(g):
    seo = g.get("seo", {})
    desc = (seo.get("descripcion") or "").strip().split("\n\n")[0]
    tags = " ".join("#" + h.lstrip("#") for h in seo.get("hashtags", [])[:8])
    txt = f"{seo.get('titulo', '')}\n\n{desc}\n\n{tags}".strip()
    txt = re.sub(r"\s*#shorts\b", "", txt, flags=re.I)  # etiqueta propia de YouTube
    return txt[:2100]


def encolar(proj, canal):
    canales = json.loads((ROOT / "canales.json").read_text())
    cfg = canales[canal]
    m = cfg.get("meta") or {}
    g = json.loads((proj / "guion.json").read_text())
    if not m or not os.environ.get(m.get("secreto", "")) or g.get("tipo") not in m.get("tipos", ["short"]):
        print("meta: no aplica (sin configuración, sin token o tipo no incluido)")
        return
    video = proj / "salida" / "video.mp4"
    asset = f"{canal}__{proj.name}.mp4"
    if gh("release", "view", RELEASE, check=False).returncode:
        gh("release", "create", RELEASE, "--title", "Cola de Reels para Instagram y Facebook",
           "--notes", "Archivos temporales: se borran solos al publicarse en Meta.")
    tmp = proj / "salida" / asset
    tmp.write_bytes(video.read_bytes())
    gh("release", "upload", RELEASE, str(tmp), "--clobber")
    cola_p = ROOT / "canales" / canal / "meta_cola.json"
    cola = json.loads(cola_p.read_text()) if cola_p.exists() else []
    cuando = (g.get("seo", {}).get("publicar_en") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    cola = [c for c in cola if c["asset"] != asset]
    sys.path.insert(0, str(Path(__file__).parent))
    from common import duration
    seg = duration(video)
    cola.append({"proyecto": proj.name, "asset": asset, "publicar_en": cuando, "caption": caption(g),
                 "instagram": None, "intentos": 0, "segundos": round(seg, 1),
                 # Reels de Facebook por API: de 3 a 90 s
                 "facebook": None if seg <= 90 else "no aplica: dura más de 90 s"})
    cola_p.write_text(json.dumps(cola, ensure_ascii=False, indent=2))
    print(f"meta: en cola {asset} para {cuando}")


def limpio(msg):
    """Quita cualquier token de un mensaje antes de imprimirlo o guardarlo (repo público)."""
    for k, v in os.environ.items():
        if k.startswith("META_") and v and len(v) > 20:
            msg = msg.replace(v, "***")
    return msg


def chk(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Meta {r.status_code}: {r.text[:300]}")
    return r.json()


def ids(token):
    pg = chk(requests.get(f"{G}/me", params={"fields": "id,name,instagram_business_account", "access_token": token}, timeout=60))
    return pg["id"], (pg.get("instagram_business_account") or {}).get("id")


def subir_rupload(url, token, archivo):
    data = archivo.read_bytes()
    return chk(requests.post(url, data=data, timeout=900, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))}))


def reel_instagram(ig_id, token, archivo, texto):
    c = chk(requests.post(f"{G}/{ig_id}/media", timeout=60, data={
        "media_type": "REELS", "upload_type": "resumable", "caption": texto, "share_to_feed": "true",
        "access_token": token}))
    subir_rupload(c["uri"], token, archivo)
    for _ in range(20):  # hasta ~10 min procesando
        st = chk(requests.get(f"{G}/{c['id']}", params={"fields": "status_code,status", "access_token": token}, timeout=60))
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram no procesó el video: {st}")
        time.sleep(30)
    else:
        raise RuntimeError("Instagram tardó demasiado en procesar el video")
    p = chk(requests.post(f"{G}/{ig_id}/media_publish", data={"creation_id": c["id"], "access_token": token}, timeout=60))
    link = chk(requests.get(f"{G}/{p['id']}", params={"fields": "permalink", "access_token": token}, timeout=60))
    return link.get("permalink") or p["id"]


def reel_facebook(page_id, token, archivo, texto):
    s = chk(requests.post(f"{G}/{page_id}/video_reels", data={"upload_phase": "start", "access_token": token}, timeout=60))
    subir_rupload(s["upload_url"], token, archivo)
    chk(requests.post(f"{G}/{page_id}/video_reels", timeout=120, data={
        "upload_phase": "finish", "video_id": s["video_id"], "video_state": "PUBLISHED",
        "description": texto, "access_token": token}))
    return f"https://www.facebook.com/reel/{s['video_id']}"


def publicar():
    canales = json.loads((ROOT / "canales.json").read_text())
    ahora = datetime.now(timezone.utc)
    fallos = []
    for canal, cfg in canales.items():
        m = cfg.get("meta") or {}
        token = os.environ.get(m.get("secreto", "") or "_")
        cola_p = ROOT / "canales" / canal / "meta_cola.json"
        if not token or not cola_p.exists():
            continue
        cola = json.loads(cola_p.read_text())
        listos = [c for c in cola if (not c["instagram"] or not c["facebook"]) and c["intentos"] < MAX_INTENTOS
                  and datetime.fromisoformat(c["publicar_en"].replace("Z", "+00:00")) <= ahora]
        if not listos:
            continue
        try:
            page_id, ig_id = ids(token)
        except Exception as e:
            fallos.append(limpio(f"{canal}: token de Meta inválido o vencido ({str(e)[:160]})"))
            continue
        for c in listos:
            c["intentos"] += 1
            d = ROOT / "tmp_meta"
            d.mkdir(exist_ok=True)
            archivo = d / c["asset"]
            try:
                gh("release", "download", RELEASE, "-p", c["asset"], "-D", str(d), "--clobber")
                if not c["instagram"]:
                    if ig_id:
                        c["instagram"] = reel_instagram(ig_id, token, archivo, c["caption"])
                    else:
                        c["instagram"] = "sin cuenta de Instagram vinculada a la Página"
                if not c["facebook"]:
                    c["facebook"] = reel_facebook(page_id, token, archivo, c["caption"])
                print(f"meta: {canal} {c['proyecto']} → IG {c['instagram']} · FB {c['facebook']}")
            except Exception as e:
                fallos.append(limpio(f"{canal}: {c['proyecto']}: {str(e)[:300]}"))
            finally:
                archivo.unlink(missing_ok=True)
            if c["instagram"] and c["facebook"]:
                gh("release", "delete-asset", RELEASE, c["asset"], "--yes", check=False)
            cola_p.write_text(json.dumps(cola, ensure_ascii=False, indent=2))
    if fallos:
        rep = ROOT / "reporte.md"
        rep.write_text((rep.read_text() if rep.exists() else "") + "\n## Instagram/Facebook\n" + "".join(f"- {f}\n" for f in fallos))
        print("\n".join(fallos))


if __name__ == "__main__":
    if sys.argv[1] == "encolar":
        encolar(Path(sys.argv[2]), sys.argv[sys.argv.index("--canal") + 1])
    else:
        publicar()
