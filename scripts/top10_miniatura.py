"""Miniatura de impacto del Top 10 (1280x720) SIN revelar el podio: mosaico con 3 videos del conteo (puestos 4-10),
casilla misteriosa "#1 ?", "TOP 10" gigante y la cifra del #1 como pregunta. Reemplaza salida/miniatura.jpg (corre después de thumbnail.py).
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
    D = json.loads(cats.read_text())
    top = D["views"][0]
    sem = g.get("semana", "")
    semana = f"SEMANA {sem.split('W')[-1]}" if "W" in sem else sem.upper()
    # SUSPENSO: nunca se muestra quién es el #1 ni el podio. Se usan puestos 4 al 10 y una casilla misteriosa.
    pool = [r for k in ("views", "likes", "comments") for r in D.get(k, [])[3:10]]
    vistos, tiles = set(), []
    for r in pool:
        if len(tiles) == 3:
            break
        if r["post_id"] in vistos or r["post_id"] in {x["post_id"] for k in D if k != "vetados" for x in D[k][:3]}:
            continue
        im0 = bajar(r["post_id"], ["maxresdefault", "hq720", "sddefault", "hqdefault"])
        if im0 is not None:
            tiles.append(ImageEnhance.Contrast(ImageEnhance.Color(recortar_barras(im0)).enhance(1.35)).enhance(1.12))
            vistos.add(r["post_id"])
    if len(tiles) < 3:
        print("Faltan miniaturas: queda la miniatura estándar.")
        return
    bg = tiles[0].resize((TW, TH)).filter(ImageFilter.GaussianBlur(30)).point(lambda p: int(p * 0.3)).convert("RGBA")
    capa = Image.new("RGBA", (TW, TH))
    d = ImageDraw.Draw(capa)
    for x in range(TW):
        d.line([(x, 0), (x, TH)], fill=(8, 6, 16, int(235 * max(0.0, 1 - x / 700))))
    im = Image.alpha_composite(bg, capa)
    d = ImageDraw.Draw(im)
    # Mosaico 2x2: tres videos del conteo + casilla misteriosa del #1
    w, h, gap = 360, 203, 16
    x0, y0 = TW - 2 * w - gap - 40, 70
    pos = [(x0, y0), (x0 + w + gap, y0), (x0, y0 + h + gap), (x0 + w + gap, y0 + h + gap)]
    for (x, y), t in zip(pos[:3], tiles):
        t = t.resize((w, max(h, int(w * t.height / t.width))))
        t = t.crop((0, (t.height - h) // 2, w, (t.height - h) // 2 + h))
        d.rounded_rectangle([x - 6, y - 6, x + w + 6, y + h + 6], 12, fill=(255, 255, 255))
        im.paste(t, (x, y))
    x, y = pos[3]
    d.rounded_rectangle([x - 6, y - 6, x + w + 6, y + h + 6], 12, fill=AMARILLO)
    d.rounded_rectangle([x, y, x + w, y + h], 8, fill=ROSA)
    fq = anton(170)
    txt = "#1 ?"
    d.text((x + w / 2 - d.textlength(txt, font=fq) / 2, y - 22), txt, font=fq, fill=(255, 255, 255),
           stroke_width=5, stroke_fill=(0, 0, 0))
    # Texto
    d.text((40, 40), "TOP", font=anton(190), fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((40, 250), "10", font=anton(260), fill=AMARILLO, stroke_width=8, stroke_fill=(0, 0, 0))
    c = f"¿QUIÉN LOGRÓ {cifra(int(top.get('views') or 0))}?"
    fc = anton(88)
    while d.textlength(c, font=fc) > 2 * w + gap:
        fc = anton(fc.size - 4)
    yb = y0 + 2 * h + gap + 34
    d.text((x0, yb), c, font=fc, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((x0 + 4, yb + fc.size + 26), "DE VISTAS EN LATINOAMÉRICA", font=mont(36), fill=AMARILLO,
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
