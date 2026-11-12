"""Obtiene una imagen (y, en Shorts, un clip de video) por escena, alusivos al tema.

Uso: python visuals.py <proyecto_dir> [--offline]
Prioridad por escena (consulta = escena.visual.query, en inglés; si falta, el tema):
  1. imagenes/<id>.jpg|png o imagenes/<id>.mp4 ya presentes (Canva, propias o fichas del Top 10)
  2. Shorts: clip de video vertical de Pexels en 4K (PEXELS_API_KEY; si no hay 4K, el de mayor resolución >= 1080)
  3. Foto de Pexels (PEXELS_API_KEY), la más grande
  4. Sin clave: imagen libre de Openverse (CC0 / CC BY / CC BY-SA, uso comercial) o de Wikimedia Commons, >= 2000 px
  5. Fondo degradado generado (último recurso / --offline)
Filtros: sin rostros de Jesús ni profetas como personas identificables (descarta obras/títulos con esos nombres),
sin repetir la misma imagen en el proyecto. Escribe imagenes/<id>.jpg (y <id>.mp4 si hay clip) y creditos.json.
"""
import io
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from common import load_json, save_json

from common import VERTICAL
TARGET = (1620, 2880) if VERTICAL else (2880, 1620)  # margen para el zoom Ken Burns sin perder nitidez en 1080p
PALETTES = [((18, 28, 54), (120, 84, 40)), ((10, 30, 40), (60, 110, 120)),
            ((40, 20, 30), (150, 100, 60)), ((15, 15, 25), (70, 70, 110))]
UA = {"User-Agent": "canales-agent/1.0 (https://github.com/daviddiazosorio73-debug/canales-agent)"}
VETO = ("jesus", "jesús", "christ", "cristo", "messiah", "mesías", "prophet", "profeta", "moses", "moisés", "elijah",
        "elías", "isaiah", "isaías", "jeremiah", "jeremías", "mary", "virgin", "virgen", "saint", "santo", "nude", "naked")


def vetado(*textos):
    t = " ".join(x or "" for x in textos).lower()
    return any(v in t for v in VETO)


def cover(img):
    img = img.convert("RGB")
    r = max(TARGET[0] / img.width, TARGET[1] / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    left = (img.width - TARGET[0]) // 2
    top = (img.height - TARGET[1]) // 2
    return img.crop((left, top, left + TARGET[0], top + TARGET[1]))


def gradient(i):
    a, b = PALETTES[i % len(PALETTES)]
    img = Image.new("RGB", TARGET)
    d = ImageDraw.Draw(img)
    for y in range(TARGET[1]):
        t = y / TARGET[1]
        d.line([(0, y), (TARGET[0], y)], fill=tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)))
    glow = Image.new("L", TARGET, 0)
    ImageDraw.Draw(glow).ellipse([TARGET[0] * .55, -TARGET[1] * .3, TARGET[0] * 1.2, TARGET[1] * .6], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(300))
    return Image.composite(Image.new("RGB", TARGET, (255, 230, 180)), img, glow)


def bajar_img(url):
    import requests
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def pexels_video(query, used, key, dst):
    """Clip vertical (o el que haya) en la mayor resolución disponible, idealmente 4K."""
    import requests
    r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                     params={"query": query, "orientation": "portrait" if VERTICAL else "landscape",
                             "size": "large", "per_page": 15}, timeout=60)
    r.raise_for_status()
    for v in r.json().get("videos", []):
        if ("v", v["id"]) in used or vetado(v.get("url")) or v.get("duration", 0) < 5:
            continue
        fs = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")]
        if VERTICAL:
            fs = [f for f in fs if f["height"] >= f["width"]]
        fs = [f for f in fs if min(f["width"], f["height"]) >= 1080]
        if not fs:
            continue
        f = max(fs, key=lambda f: f["width"] * f["height"])
        used.add(("v", v["id"]))
        with requests.get(f["link"], stream=True, timeout=300) as s:
            s.raise_for_status()
            with open(dst, "wb") as fh:
                for ch in s.iter_content(1 << 20):
                    fh.write(ch)
        img = bajar_img(v["image"]) if v.get("image") else None
        return img, {"autor": v.get("user", {}).get("name", "Pexels"), "url": v["url"],
                     "fuente": "Pexels", "res": f"{f['width']}x{f['height']}"}
    return None, None


def pexels(query, used, key):
    import requests
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key},
                     params={"query": query, "orientation": "portrait" if VERTICAL else "landscape",
                             "size": "large", "per_page": 15}, timeout=60)
    r.raise_for_status()
    for p in r.json().get("photos", []):
        if ("p", p["id"]) in used or vetado(p.get("alt"), p.get("url")):
            continue
        used.add(("p", p["id"]))
        return bajar_img(p["src"]["original"]), {"autor": p["photographer"], "url": p["url"], "fuente": "Pexels"}
    return None, None


def openverse(query, used):
    import requests
    r = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=60,
                     params={"q": query, "license": "cc0,pdm,by,by-sa", "license_type": "commercial",
                             "size": "large", "aspect_ratio": "tall" if VERTICAL else "wide",
                             "mature": "false", "page_size": 20})
    r.raise_for_status()
    for p in r.json().get("results", []):
        if p["id"] in used or vetado(p.get("title"), " ".join(t.get("name", "") for t in p.get("tags") or [])):
            continue
        if (p.get("width") or 0) < 2000 and (p.get("height") or 0) < 2000:
            continue
        try:
            img = bajar_img(p["url"])
        except Exception:
            continue
        used.add(p["id"])
        lic = f"{p.get('license', '').upper()} {p.get('license_version') or ''}".strip()
        return img, {"autor": p.get("creator") or "Openverse", "url": p.get("foreign_landing_url") or p["url"],
                     "fuente": "Openverse", "licencia": lic}
    return None, None


def commons(query, used):
    import requests
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=60, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": 20, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
        "iiurlwidth": 3840})
    r.raise_for_status()
    for p in (r.json().get("query", {}).get("pages") or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        if p["pageid"] in used or vetado(p.get("title")) or max(ii.get("width", 0), ii.get("height", 0)) < 2000:
            continue
        if not any(x in lic for x in ("CC0", "Public domain", "CC BY", "PD")) or "NC" in lic or "ND" in lic:
            continue
        try:
            img = bajar_img(ii.get("thumburl") or ii["url"])
        except Exception:
            continue
        used.add(p["pageid"])
        import re
        autor = re.sub("<[^>]+>", "", (meta.get("Artist") or {}).get("value", "Wikimedia Commons")).strip()[:80]
        return img, {"autor": autor or "Wikimedia Commons", "url": ii.get("descriptionurl", ""),
                     "fuente": "Wikimedia Commons", "licencia": lic}
    return None, None


def buscar(fuentes, query, i, nombre):
    for f in fuentes:
        try:
            img, cred = f(query)
            if img is not None:
                return img, cred
        except Exception as ex:  # una fuente caída no detiene el video
            print(f"  aviso {nombre}: {f.__name__ if hasattr(f, '__name__') else 'fuente'} falló ({ex})", flush=True)
    return None, None


def main():
    proj = Path(sys.argv[1])
    offline = "--offline" in sys.argv or os.environ.get("VISUALES_OFFLINE") == "1"
    key = os.environ.get("PEXELS_API_KEY")
    g = load_json(proj / "guion.json")
    out = proj / "imagenes"
    out.mkdir(exist_ok=True)
    creditos, used = [], set()
    for i, e in enumerate(g["escenas"]):
        dst = out / f"{e['id']}.jpg"
        clip = out / f"{e['id']}.mp4"
        src = next((p for p in [out / f"{e['id']}.png", dst] if p.exists()), None)
        q = (e.get("visual") or {}).get("query") or g.get("tema", "")
        img, cred = None, None
        if src is not None or clip.exists():
            img = Image.open(src) if src is not None else None
        elif not offline:
            fuentes = []
            if key and VERTICAL and not e.get("solo_imagen"):
                fuentes.append(lambda qq: pexels_video(qq, used, key, clip))
            if key:
                fuentes.append(lambda qq: pexels(qq, used, key))
            fuentes += [lambda qq: openverse(qq, used), lambda qq: commons(qq, used)]
            img, cred = buscar(fuentes, q, i, e["id"])
        if img is None and clip.exists():
            from common import run
            run(["ffmpeg", "-y", "-v", "error", "-ss", "1", "-i", str(clip), "-frames:v", "1", str(dst)])
            img = Image.open(dst)
        if img is None:
            img = gradient(i)
        cover(img).save(dst, quality=92)
        if cred:
            creditos.append(cred)
        tipo = "clip " + cred.get("res", "") if cred and clip.exists() else (cred or {}).get("fuente", "propia" if src else "degradado")
        print(f"+ {e['id']} ({tipo}) «{q}»")
    save_json(creditos, proj / "creditos.json")


if __name__ == "__main__":
    main()
