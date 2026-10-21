"""Miniatura 1280x720 (<2 MB) desde guion.json["miniatura"].

Uso: python thumbnail.py <proyecto_dir>
miniatura: {"linea1": "...", "linea2": "...", "etiqueta": "LECCIÓN 3 · LUNES", "imagen": "<id escena>"}
Si existe <proyecto_dir>/miniatura_base.jpg|png (p. ej. de Canva) se usa como fondo.
Escribe salida/miniatura.jpg
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from common import font_path, load_json

SKILL_DIR = Path(__file__).resolve().parent.parent
TW, TH = 1280, 720


def fit_font(text, max_w, start, bold=True):
    size = start
    while size > 40:
        f = ImageFont.truetype(font_path(bold, SKILL_DIR), size)
        if f.getbbox(text)[2] <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(font_path(bold, SKILL_DIR), size)


def main():
    proj = Path(sys.argv[1])
    g = load_json(proj / "guion.json")
    m = g["miniatura"]
    brand = tuple(g.get("color_marca", [212, 168, 83]))
    base = next((p for p in [proj / "miniatura_base.png", proj / "miniatura_base.jpg"] if p.exists()), None)
    if base is None:
        sid = m.get("imagen") or g["escenas"][0]["id"]
        base = proj / "imagenes" / f"{sid}.jpg"
    bg = Image.open(base).convert("RGB")
    r = max(TW / bg.width, TH / bg.height)
    bg = bg.resize((int(bg.width * r) + 1, int(bg.height * r) + 1), Image.LANCZOS)
    bg = bg.crop((0, 0, TW, TH))
    bg = ImageEnhance.Contrast(ImageEnhance.Color(bg).enhance(1.25)).enhance(1.1).convert("RGBA")

    shade = Image.new("RGBA", (TW, TH))
    d = ImageDraw.Draw(shade)
    for x in range(TW):
        a = int(225 * max(0, 1 - x / (TW * 0.78)) ** 0.9)
        d.line([(x, 0), (x, TH)], fill=(5, 8, 18, a))
    img = Image.alpha_composite(bg, shade)
    d = ImageDraw.Draw(img)

    if m.get("etiqueta"):
        f = ImageFont.truetype(font_path(True, SKILL_DIR), 34)
        w = f.getbbox(m["etiqueta"])[2]
        d.rounded_rectangle([56, 52, 56 + w + 40, 112], 12, fill=brand)
        d.text((76, 60), m["etiqueta"], font=f, fill=(15, 15, 20))

    lineas = [(t.upper(), c, fit_font(t.upper(), 760, s))
              for t, c, s in [(m["linea1"], (255, 255, 255), 118), (m.get("linea2", ""), brand, 132)] if t]
    alto = sum(f.getbbox(t)[3] for t, _, f in lineas) + 30 * (len(lineas) - 1)
    y = max(150, (TH - alto) // 2 + 30)  # bloque centrado verticalmente, bajo la etiqueta
    for txt, col, f in lineas:
        d.text((60, y), txt, font=f, fill=col, stroke_width=6, stroke_fill=(0, 0, 0))
        y += f.getbbox(txt)[3] + 30

    out = proj / "salida" / "miniatura.jpg"
    out.parent.mkdir(exist_ok=True)
    img.convert("RGB").save(out, quality=90, optimize=True)
    print(f"OK {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
