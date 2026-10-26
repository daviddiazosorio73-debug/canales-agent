"""Miniatura de impacto del Top 10 (1280x720): miniatura del #1 en vistas como protagonista, "TOP 10" gigante,
cifra real del #1 y semana. Reemplaza salida/miniatura.jpg (corre después de thumbnail.py).
Uso: python top10_miniatura.py <proyecto_dir>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from top10_fichas import anton, mont  # noqa: E402
from top10_visuales import bajar, recortar_barras  # noqa: E402

TW, TH = 1280, 720
ROSA, AMARILLO = (255, 45, 120), (255, 214, 0)


def cifra(n):
    if n >= 1_000_000:
        m = n / 1_000_000
        return (f"{int(m)}" if m >= 10 else f"{m:.1f}".replace(".", ",").replace(",0", "")) + " MILLONES"
    return f"{n // 1000} MIL"


def main():
    proj = Path(sys.argv[1])
    cats = proj / "categorias3.json"
    if not cats.exists():
        print("Sin categorias3.json: queda la miniatura estándar.")
        return
    g = json.loads((proj / "guion.json").read_text())
    top = json.loads(cats.read_text())["views"][0]
    sem = g.get("semana", "")
    semana = f"SEMANA {sem.split('W')[-1]}" if "W" in sem else sem.upper()
    th = bajar(top["post_id"], ["maxresdefault", "hq720", "sddefault", "hqdefault"])
    if th is None:
        print("Sin miniatura del #1: queda la miniatura estándar.")
        return
    th = ImageEnhance.Contrast(ImageEnhance.Color(recortar_barras(th)).enhance(1.35)).enhance(1.12)
    # Fondo: la misma imagen desenfocada y oscura
    bg = th.resize((TW, int(TW * th.height / th.width))).resize((TW, TH)).filter(ImageFilter.GaussianBlur(30))
    bg = bg.point(lambda p: int(p * 0.35)).convert("RGBA")
    capa = Image.new("RGBA", (TW, TH))
    d = ImageDraw.Draw(capa)
    for x in range(TW):
        d.line([(x, 0), (x, TH)], fill=(8, 6, 16, int(235 * max(0.0, 1 - x / 760))))
    im = Image.alpha_composite(bg, capa)
    d = ImageDraw.Draw(im)
    # Protagonista: miniatura del #1 con marco y medalla
    w, h = 740, 416
    hero = th.resize((w, max(h, int(w * th.height / th.width))))
    hero = hero.crop((0, (hero.height - h) // 2, w, (hero.height - h) // 2 + h))
    x0, y0 = TW - w - 40, 100
    d.rounded_rectangle([x0 - 12, y0 - 12, x0 + w + 12, y0 + h + 12], 22, fill=AMARILLO)
    im.paste(hero, (x0, y0))
    cx, cy, r = x0 + 8, y0 + 8, 92
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ROSA, outline=(255, 255, 255), width=8)
    f1 = anton(120)
    d.text((cx - d.textlength("#1", font=f1) / 2, cy - 92), "#1", font=f1, fill=(255, 255, 255))
    # Texto
    d.text((40, 40), "TOP", font=anton(190), fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((40, 250), "10", font=anton(260), fill=AMARILLO, stroke_width=8, stroke_fill=(0, 0, 0))
    c = cifra(int(top.get("views") or 0)) + " DE VISTAS"
    fc = anton(96)
    while d.textlength(c, font=fc) > 760:
        fc = anton(fc.size - 4)
    d.text((x0, y0 + h + 34), c, font=fc, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((x0 + 4, y0 + h + 34 + fc.size + 24), "EL MÁS VISTO DE LA SEMANA", font=mont(38), fill=AMARILLO,
           stroke_width=3, stroke_fill=(0, 0, 0))
    fp = mont(34)
    d.rounded_rectangle([40, 616, 80 + d.textlength(f"{semana} · LATAM", font=fp), 676], 30, fill=ROSA)
    d.text((60, 625), f"{semana} · LATAM", font=fp, fill=(255, 255, 255))
    out = proj / "salida" / "miniatura.jpg"
    out.parent.mkdir(exist_ok=True)
    im.convert("RGB").save(out, quality=90, optimize=True)
    print(f"OK miniatura de impacto ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
