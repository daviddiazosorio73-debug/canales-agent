"""Fichas verticales (1620x2880) para los Shorts del Top 10. Se ejecuta en el runner antes de visuals.py.

Escena con "video_id": baja la miniatura del video (i.ytimg.com) y arma imagenes/<id>.jpg:
fondo desenfocado + miniatura nítida + (si es puesto) número gigante, creador, cifra exacta y categoría.
"solo_fondo": true -> solo fondo + miniatura (gancho y cierre, sin revelar nada).
Uso: python top10_short_visual.py <proyecto_dir>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from top10_fichas import anton, corta, mont  # noqa: E402
from top10_visuales import bajar, recortar_barras  # noqa: E402

W, H = 1620, 2880
COL = {"VIEWS": (255, 45, 120), "VISTAS": (255, 45, 120), "COMMENTS": (0, 200, 255), "COMENTARIOS": (0, 200, 255),
       "LIKES": (255, 196, 0)}


def miles(n, lang):
    t = f"{int(n):,}"
    return t if lang == "en" else t.replace(",", ".")


def lienzo(im):
    im = recortar_barras(im)
    esc = max(W / im.width, H / im.height)
    f = im.resize((int(im.width * esc) + 1, int(im.height * esc) + 1))
    f = f.crop(((f.width - W) // 2, (f.height - H) // 2, (f.width - W) // 2 + W, (f.height - H) // 2 + H))
    f = f.filter(ImageFilter.GaussianBlur(45)).point(lambda p: int(p * 0.4))
    a = int(W * 0.86)
    fr = im.resize((a, int(im.height * a / im.width)), Image.LANCZOS)
    y = 930 - fr.height // 2
    f.paste(fr, ((W - a) // 2, y))
    return f, y + fr.height


def main():
    proj = Path(sys.argv[1])
    g = json.loads((proj / "guion.json").read_text())
    lang = g.get("lang", "es")
    out = proj / "imagenes"
    out.mkdir(exist_ok=True)
    for e in g["escenas"]:
        if not e.get("video_id"):
            continue
        im = bajar(e["video_id"], ["maxresdefault", "sddefault", "hqdefault"])
        if im is None:
            print(f"AVISO: sin miniatura para {e['id']}")
            continue
        f, y_fin = lienzo(im)
        d = ImageDraw.Draw(f)
        if e.get("puesto"):
            col = COL.get(e.get("categoria", ""), (255, 45, 120))
            d.text((W // 2, 330), f"#{e['puesto']}", font=anton(330), fill=col, anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0))
            d.text((W // 2, y_fin + 95), corta(d, e.get("creador", ""), mont(92), W - 160), font=mont(92), fill="white",
                   anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
            d.text((W // 2, y_fin + 225), miles(e.get("cifra", 0), lang), font=anton(190), fill=col, anchor="mm",
                   stroke_width=8, stroke_fill=(0, 0, 0))
            d.text((W // 2, y_fin + 345), e.get("categoria", ""), font=mont(70), fill="white", anchor="mm",
                   stroke_width=5, stroke_fill=(0, 0, 0))
        f.save(out / f"{e['id']}.jpg", quality=92)
        print(f"+ ficha vertical {e['id']}")


if __name__ == "__main__":
    main()
