"""Obtiene una imagen por escena.

Uso: python visuals.py <proyecto_dir> [--offline]
Prioridad por escena:
  1. imagenes/<id>.jpg|png ya presente (p. ej. generada con Canva o propia)
  2. Pexels API (PEXELS_API_KEY) con escena.visual.query
  3. Fondo degradado generado (fallback / --offline)
Escribe imagenes/<id>.jpg (3840x2160) y creditos.json.
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


def pexels(query, used, key):
    import requests
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": key},
                     params={"query": query, "orientation": "landscape", "size": "large",
                             "per_page": 15}, timeout=60)
    r.raise_for_status()
    for p in r.json().get("photos", []):
        if p["id"] in used:
            continue
        used.add(p["id"])
        img = requests.get(p["src"]["original"], timeout=120).content
        return Image.open(io.BytesIO(img)), {"autor": p["photographer"], "url": p["url"]}
    return None, None


def main():
    proj = Path(sys.argv[1])
    offline = "--offline" in sys.argv
    key = os.environ.get("PEXELS_API_KEY")
    g = load_json(proj / "guion.json")
    out = proj / "imagenes"
    out.mkdir(exist_ok=True)
    creditos, used = [], set()
    for i, e in enumerate(g["escenas"]):
        dst = out / f"{e['id']}.jpg"
        src = next((p for p in [out / f"{e['id']}.png", dst] if p.exists()), None)
        cred = None
        if src is not None:
            img = Image.open(src)
        elif key and not offline:
            img, cred = pexels(e.get("visual", {}).get("query", g["tema"]), used, key)
            if img is None:
                img = gradient(i)
        else:
            img = gradient(i)
        cover(img).save(dst, quality=92)
        if cred:
            creditos.append(cred)
        print(f"+ {e['id']} {'(Pexels)' if cred else ''}")
    save_json(creditos, proj / "creditos.json")


if __name__ == "__main__":
    main()
