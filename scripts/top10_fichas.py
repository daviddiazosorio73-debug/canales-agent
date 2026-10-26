"""Fichas de resultado del Top 10 (impacto visual), generadas en Actions con PIL.

Lee <proyecto>/categorias3.json (listas views/comments/likes ordenadas del #1 al #10) y, para cada escena con
"video_id" cuyo id empiece por v/c/l, crea:
  imagenes/<id>_card.jpg          ficha final: número gigante, miniatura, creador, cifra protagonista y barra vs el #1
  imagenes/<id>_cnt_NN.jpg        cuadros de conteo (la cifra y la barra suben de 0 al valor real)
  imagenes/tabla_<cat>.jpg        tabla final de la categoría (se muestra al cierre del #1)
Guarda en la escena "ficha_anim" (cuadros de conteo) y, en el #1, "tabla".
Uso: python top10_fichas.py <proyecto_dir>
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from top10_visuales import bajar, recortar_barras  # noqa: E402

W, H = 1920, 1080
F = Path(__file__).resolve().parent.parent / "fuentes"
CAT = {"v": ("views", "VISTAS", "MÁS VISTOS", (255, 45, 120)),
       "c": ("comments", "COMENTARIOS", "MÁS COMENTADOS", (0, 200, 255)),
       "l": ("likes", "LIKES", "MÁS LIKES", (255, 196, 0))}
PAIS = {"MX": "MÉXICO", "BR": "BRASIL", "CO": "COLOMBIA", "AR": "ARGENTINA", "PE": "PERÚ", "CL": "CHILE",
        "EC": "ECUADOR", "VE": "VENEZUELA", "GT": "GUATEMALA", "BO": "BOLIVIA", "UY": "URUGUAY", "PY": "PARAGUAY",
        "DO": "REP. DOMINICANA", "CR": "COSTA RICA", "PA": "PANAMÁ", "HN": "HONDURAS", "SV": "EL SALVADOR",
        "NI": "NICARAGUA", "CU": "CUBA", "PR": "PUERTO RICO", "US": "EE. UU.", "ES": "ESPAÑA"}
N_CNT = 12  # cuadros de conteo


def anton(s):
    return ImageFont.truetype(str(F / "Anton-Regular.ttf"), s)


def mont(s, peso="ExtraBold"):
    f = ImageFont.truetype(str(F / "Montserrat.ttf"), s)
    try:
        f.set_variation_by_name(peso)
    except Exception:
        pass
    return f


def miles(n):
    return f"{int(n):,}".replace(",", ".")


def corta(d, txt, font, ancho):
    if d.textlength(txt, font=font) <= ancho:
        return txt
    while txt and d.textlength(txt + "…", font=font) > ancho:
        txt = txt[:-1]
    return txt.rstrip() + "…"


def fondo(thumb, color):
    if thumb is not None:
        bg = thumb.resize((W, int(W * thumb.height / thumb.width)))
        bg = bg.resize((W, max(H, bg.height))).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(38))
        bg = bg.point(lambda p: int(p * 0.28))
    else:
        bg = Image.new("RGB", (W, H), (12, 12, 20))
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for x in range(W):  # degradado de color de la categoría desde la izquierda
        a = int(120 * max(0.0, 1 - x / 1100))
        d.line([(x, 0), (x, H)], fill=(*color, a))
    return Image.alpha_composite(bg.convert("RGBA"), capa)


def texto_sombra(d, xy, txt, font, fill, sombra=10, stroke=0, stroke_fill=None):
    x, y = xy
    d.text((x + sombra, y + sombra), txt, font=font, fill=(0, 0, 0, 170))
    d.text((x, y), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def ficha(r, rank, letra, maximo, thumb, semana, frac=1.0):
    """Zona libre abajo (y > 860) para los subtítulos quemados; arriba a la derecha queda el logo."""
    k, lab, cat, col = CAT[letra]
    im = fondo(thumb, col)
    d = ImageDraw.Draw(im)
    # Fila superior: categoría + semana + chips
    pill = f"TOP 10 · {cat}"
    fp = mont(44)
    wpill = d.textlength(pill, font=fp) + 60
    d.rounded_rectangle([70, 50, 70 + wpill, 126], 38, fill=col)
    d.text((100, 63), pill, font=fp, fill=(10, 10, 16))
    cx = 70 + wpill + 24
    for c in [semana, PAIS.get(r.get("country"), r.get("country")), (r.get("language") or "").upper()]:
        if not c:
            continue
        wc = d.textlength(c, font=mont(30)) + 40
        d.rounded_rectangle([cx, 62, cx + wc, 114], 26, outline=(255, 255, 255), width=3)
        d.text((cx + 20, 69), c, font=mont(30), fill=(255, 255, 255))
        cx += wc + 14
    # Columna izquierda: número gigante y cifra protagonista
    texto_sombra(d, (64, 96), f"#{rank}", anton(390), (255, 255, 255), sombra=14, stroke=9, stroke_fill=col)
    val = int((r.get(k) or 0) * frac)
    num = miles(val)
    fn = anton(150)
    while d.textlength(num, font=fn) > 830:
        fn = anton(fn.size - 6)
    texto_sombra(d, (72, 560), num, fn, col, sombra=8)
    d.text((76, 748), lab, font=mont(44), fill=(255, 255, 255))
    d.rounded_rectangle([76, 812, 900, 846], 17, fill=(62, 62, 76))
    lleno = int(824 * min(1.0, val / maximo)) if maximo else 0
    if lleno > 34:
        d.rounded_rectangle([76, 812, 76 + lleno, 846], 17, fill=col)
    ref = "EL #1 DE LA CATEGORÍA" if rank == 1 else f"{round(100 * (r.get(k) or 0) / maximo)} % del #1"
    d.text((900 - d.textlength(ref, font=mont(30)), 760), ref, font=mont(30), fill=col)
    # Columna derecha: creador, miniatura enmarcada, título y otras cifras
    x0, tw = 990, 860
    texto_sombra(d, (x0, 150), corta(d, r.get("creator_name") or "", anton(84), tw), anton(84), (255, 255, 255), sombra=6)
    th = int(tw * 9 / 16)
    y0 = 284
    if thumb is not None:
        t = recortar_barras(thumb)
        t = t.resize((tw, max(th, int(tw * t.height / t.width))))
        t = t.crop((0, (t.height - th) // 2, tw, (t.height - th) // 2 + th))
        d.rounded_rectangle([x0 - 12, y0 - 12, x0 + tw + 12, y0 + th + 12], 22, fill=col)
        im.paste(t, (x0, y0))
    d.text((x0, y0 + th + 22), corta(d, r.get("title") or "", mont(34, "SemiBold"), tw), font=mont(34, "SemiBold"), fill=(230, 230, 238))
    otros = [(x, l) for x, l in (("views", "vistas"), ("comments", "comentarios"), ("likes", "likes")) if x != k]
    extra = "  ·  ".join(f"{miles(r.get(x) or 0)} {l}" for x, l in otros if r.get(x) is not None)
    d.text((x0, y0 + th + 70), extra, font=mont(32, "Bold"), fill=col)
    return im.convert("RGB")


def tabla(lista, letra, semana):
    k, lab, cat, col = CAT[letra]
    im = fondo(None, col)
    d = ImageDraw.Draw(im)
    d.text((80, 40), f"TOP 10 · {cat}", font=anton(110), fill=(255, 255, 255))
    d.text((W - 80 - d.textlength(semana, font=mont(40)), 90), semana, font=mont(40), fill=col)
    maximo = max((r.get(k) or 0) for r in lista) or 1
    y = 196
    for i, r in enumerate(lista[:10]):  # termina en y≈856: abajo quedan los subtítulos
        rank = i + 1
        alto = 66
        top = rank <= 3
        d.rounded_rectangle([80, y, W - 80, y + alto - 8], 16, fill=col if rank == 1 else (36, 36, 50))
        tc = (12, 12, 18) if rank == 1 else (255, 255, 255)
        d.text((104, y - 6), f"{rank}", font=anton(52), fill=tc if rank == 1 else (col if top else (255, 255, 255)))
        d.text((210, y + 9), corta(d, r.get("creator_name") or "", mont(36), 780), font=mont(36), fill=tc)
        bx0, bx1 = 1010, 1490
        d.rounded_rectangle([bx0, y + 18, bx1, y + 42], 12, fill=(14, 14, 20))
        bw = int((bx1 - bx0) * (r.get(k) or 0) / maximo)
        if bw > 24:
            d.rounded_rectangle([bx0, y + 18, bx0 + bw, y + 42], 12, fill=(12, 12, 18) if rank == 1 else col)
        v = miles(r.get(k) or 0)
        d.text((W - 104 - d.textlength(v, font=anton(46)), y - 2), v, font=anton(46), fill=tc)
        y += alto
    return im.convert("RGB")


def main():
    proj = Path(sys.argv[1])
    cats = proj / "categorias3.json"
    if not cats.exists():
        print("Sin categorias3.json: se usan las fichas existentes.")
        return
    D = json.loads(cats.read_text())
    g = json.loads((proj / "guion.json").read_text())
    sem = g.get("semana", "")
    semana = f"SEMANA {sem.split('W')[-1]}" if "W" in sem else sem.upper()
    img = proj / "imagenes"
    img.mkdir(exist_ok=True)
    hechas = set()
    for e in g["escenas"]:
        vid, letra = e.get("video_id"), e["id"][0]
        if not vid or letra not in CAT:
            continue
        k = CAT[letra][0]
        lista = D.get(k, [])
        pos = next((i for i, r in enumerate(lista) if r.get("post_id") == vid), None)
        if pos is None:
            continue
        r, rank = lista[pos], pos + 1
        maximo = max((x.get(k) or 0) for x in lista) or 1
        thumb = bajar(vid, ["maxresdefault", "hq720", "sddefault", "hqdefault"])
        ficha(r, rank, letra, maximo, thumb, semana).save(img / f"{e['id']}_card.jpg", quality=93)
        anim = []
        for n in range(N_CNT):
            frac = 1 - (1 - (n + 1) / N_CNT) ** 3  # sube rápido y frena al final
            ruta = f"imagenes/{e['id']}_cnt_{n:02d}.jpg"
            ficha(r, rank, letra, maximo, thumb, semana, frac).save(proj / ruta, quality=88)
            anim.append(ruta)
        e["ficha_anim"] = anim
        if rank == 1 and letra not in hechas:
            tabla(lista, letra, semana).save(img / f"tabla_{k}.jpg", quality=93)
            e["tabla"] = f"imagenes/tabla_{k}.jpg"
            hechas.add(letra)
        print(f"+ ficha {e['id']} (#{rank} {k})")
    (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
