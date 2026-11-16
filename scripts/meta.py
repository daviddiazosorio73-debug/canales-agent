"""Instagram + Facebook (Meta) para los Reels del Fundador. Gratis, API oficial, corre en GitHub Actions.

Dos pasos:
  encolar  <proyecto_dir> --canal <canal>   (runner.py, justo después de subir a YouTube)
      Guarda el MP4 vertical como asset de la release "meta-cola" del repo y lo anota en
      canales/<canal>/meta_cola.json con la misma hora de publicación de YouTube.
  publicar                                    (cada hora, después de runner.py)
      Publica lo que ya llegó a su hora: Reel en Instagram + Reel en la Página de Facebook.
      Borra el asset cuando ambos quedan publicados. Reintenta hasta 3 veces.

Config en canales.json → "meta": {"secreto": "META_PAGE_TOKEN_<CANAL>", "tipos": ["short"]}
El secreto es un token de USUARIO DEL SISTEMA del portafolio del canal (recomendado: no vence ni depende de la sesión) o un token de PÁGINA con permisos pages_show_list, pages_read_engagement,
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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
VER = os.environ.get("META_API_VER", "v26.0")
G = f"https://graph.facebook.com/{VER}"
RELEASE = "meta-cola"
MAX_INTENTOS = 3
ATRASO_H = 2          # más tarde que esto = atrasado
ATRASO_CADA_H = 3     # orden del Fundador (15-nov-2026): 1 atrasado cada 3 h por canal


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
                 "facebook": None if seg <= 90 else "no aplica: dura más de 90 s",
                 # Páginas adicionales (solo Facebook), p. ej. la de la iglesia: {"SECRETO": null | enlace}
                 "extra": {x["secreto"]: (None if seg <= 90 else "no aplica: dura más de 90 s")
                           for x in m.get("extra", [])}})
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


def ids(token, pagina=None):
    """Acepta un token de Página o uno de USUARIO DEL SISTEMA (Business Manager, no vence ni depende de tu sesión):
    con el de sistema toma la Página asignada y su token de Página automáticamente."""
    try:
        r = requests.get(f"{G}/me/accounts", params={"fields": "id,name,access_token,instagram_business_account",
                                                      "access_token": token}, timeout=60)
        cuentas = r.json().get("data") if r.ok else None
    except Exception:
        cuentas = None
    if cuentas:
        pg = cuentas[0]
        if pagina:  # varias Páginas en un mismo negocio: la del canal (id o parte del nombre en canales.json → meta.pagina)
            elegidas = [c for c in cuentas if pagina == c["id"] or pagina.lower() in c.get("name", "").lower()]
            if not elegidas:
                raise RuntimeError(f"la Página «{pagina}» no está asignada a este token")
            pg = elegidas[0]
        return pg["id"], (pg.get("instagram_business_account") or {}).get("id"), pg["access_token"]
    pg = chk(requests.get(f"{G}/me", params={"fields": "id,name,instagram_business_account", "access_token": token}, timeout=60))
    return pg["id"], (pg.get("instagram_business_account") or {}).get("id"), token


def subir_rupload(url, token, archivo):
    data = archivo.read_bytes()
    return chk(requests.post(url, data=data, timeout=900, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))}))


def url_publica(archivo):
    return f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'daviddiazosorio73-debug/canales-agent')}/releases/download/{RELEASE}/{archivo.name}"


def reel_instagram(ig_id, token, archivo, texto):
    try:
        c = chk(requests.post(f"{G}/{ig_id}/media", timeout=60, data={
            "media_type": "REELS", "upload_type": "resumable", "caption": texto, "share_to_feed": "true",
            "access_token": token}))
        subir_rupload(c["uri"], token, archivo)
    except Exception as e:  # p. ej. ProcessingFailedError en la subida directa: Instagram baja el video de la URL pública
        print(f"meta: subida directa a Instagram falló ({str(e)[:120]}); uso la URL pública", flush=True)
        c = chk(requests.post(f"{G}/{ig_id}/media", timeout=60, data={
            "media_type": "REELS", "video_url": url_publica(archivo), "caption": texto, "share_to_feed": "true",
            "access_token": token}))
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
    try:
        subir_rupload(s["upload_url"], token, archivo)
    except Exception as e:  # Facebook también acepta que él mismo baje el video desde una URL pública
        print(f"meta: subida directa a Facebook falló ({str(e)[:120]}); uso la URL pública", flush=True)
        chk(requests.post(s["upload_url"], timeout=300, headers={"Authorization": f"OAuth {token}",
                                                                 "file_url": url_publica(archivo)}))
    chk(requests.post(f"{G}/{page_id}/video_reels", timeout=120, data={
        "upload_phase": "finish", "video_id": s["video_id"], "video_state": "PUBLISHED",
        "description": texto, "access_token": token}))
    return f"https://www.facebook.com/reel/{s['video_id']}"


def publicar():
    canales = json.loads((ROOT / "canales.json").read_text())
    ahora = datetime.now(timezone.utc)
    fallos = []
    for canal, cfg in canales.items():
        if canal.startswith("_") or not isinstance(cfg, dict):
            continue
        m = cfg.get("meta") or {}
        token = os.environ.get(m.get("secreto", "") or "_")
        cola_p = ROOT / "canales" / canal / "meta_cola.json"
        if not token or not cola_p.exists():
            continue
        cola = json.loads(cola_p.read_text())
        pendiente = lambda c: (not c["instagram"] or not c["facebook"]  # noqa: E731
                               or any(v is None and os.environ.get(k) for k, v in (c.get("extra") or {}).items()))
        hora = lambda c: datetime.fromisoformat(c["publicar_en"].replace("Z", "+00:00"))  # noqa: E731
        listos = [c for c in cola if pendiente(c) and c["intentos"] < MAX_INTENTOS and hora(c) <= ahora]
        # Atrasados (más de ATRASO_H horas tarde, p. ej. tras un token vencido): 1 cada ATRASO_CADA_H horas por canal,
        # del más antiguo al más nuevo, para no saturar Instagram/Facebook. Los de su hora salen todos.
        est_p = ROOT / "canales" / canal / "meta_estado.json"
        est = json.loads(est_p.read_text()) if est_p.exists() else {}
        a_tiempo = [c for c in listos if hora(c) > ahora - timedelta(hours=ATRASO_H)]
        atrasados = sorted([c for c in listos if c not in a_tiempo], key=hora)
        ultimo = est.get("ultimo_atraso")
        if atrasados and (not ultimo or datetime.fromisoformat(ultimo) <= ahora - timedelta(hours=ATRASO_CADA_H)):
            a_tiempo.append(atrasados[0])
            est["ultimo_atraso"] = ahora.isoformat()
            est["atrasados_pendientes"] = len(atrasados) - 1
            est_p.write_text(json.dumps(est, indent=2))
        listos = a_tiempo
        if not listos:
            continue
        try:
            page_id, ig_id, token = ids(token, m.get("pagina"))
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
                    try:
                        c["instagram"] = (reel_instagram(ig_id, token, archivo, c["caption"]) if ig_id
                                          else "sin cuenta de Instagram vinculada a la Página")
                    except Exception as e:
                        fallos.append(limpio(f"{canal}: {c['proyecto']} (Instagram): {str(e)[:300]}"))
                if not c["facebook"]:
                    c["facebook"] = reel_facebook(page_id, token, archivo, c["caption"])
                print(f"meta: {canal} {c['proyecto']} → IG {c['instagram']} · FB {c['facebook']}")
                for sec, hecho in (c.get("extra") or {}).items():
                    tok = os.environ.get(sec)
                    if hecho or not tok:
                        continue
                    pid, _, tok = ids(tok)
                    c["extra"][sec] = reel_facebook(pid, tok, archivo, c["caption"])
                    print(f"meta: {canal} {c['proyecto']} → también en {sec}: {c['extra'][sec]}")
            except Exception as e:
                fallos.append(limpio(f"{canal}: {c['proyecto']}: {str(e)[:300]}"))
            finally:
                archivo.unlink(missing_ok=True)
            if not pendiente(c):
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
