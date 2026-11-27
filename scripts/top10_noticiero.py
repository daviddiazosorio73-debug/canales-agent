"""Gráficos de noticiero del Top 10 (orden del Fundador, 27-nov-2026). Se SUMAN a lo aprobado (cuadros + fichas):
  - capa(e, g, W, H, ruta): sello superior «TOP 10 · CONTINENTE | SEMANA n», zócalo inferior con el puesto, el creador
    y el título del video, y la banda del cintillo. Solo mientras se ven los momentos del video (no sobre las fichas).
  - cintillo(g, H, ruta): tira larga de texto que corre de derecha a izquierda (sin spoilers: nunca nombra el podio).
Uso: lo llama render.py en las escenas del Top 10 con "noticiero" en su secuencia.
"""
import re
from pathlib import Path

from PIL import Image, ImageDraw

from top10_fichas import anton, mont

ROJO = (220, 20, 60)
OSCURO = (12, 14, 24)
AMARILLO = (255, 214, 0)
CINT_H = 52  # alto del cintillo (sobre lienzo de 1080)

TXT = {
    "es": {"semana": "SEMANA", "ranking": "RANKING SEMANAL", "cat": {"v": "MÁS VISTOS", "c": "MÁS COMENTADOS", "l": "MÁS LIKES"},
           "cint": ["Cifras de la API oficial de YouTube", "Corte: sábado 23:59, hora local de cada continente",
                    "Un video por creador en cada lista", "Sin música ni noticias", "Videos publicados en los últimos 7 días",
                    "¿Premiación real para los ganadores? Comenta #PremiosTop10RS", "#Top10RS"]},
    "en": {"semana": "WEEK", "ranking": "WEEKLY RANKING", "cat": {"v": "MOST VIEWED", "c": "MOST COMMENTED", "l": "MOST LIKED"},
           "cint": ["Numbers from the official YouTube API", "Cut: Saturday 23:59, local time on each continent",
                    "One video per creator on each list", "No music or news", "Videos posted in the last 7 days",
                    "A real award for the winners? Comment #PremiosTop10RS", "#Top10RS"]},
}


def _t(g):
    return TXT.get(g.get("lang"), TXT["en"])


def _ajusta(d, txt, f_fn, tam, ancho):
    f = f_fn(tam)
    while d.textlength(txt, font=f) > ancho and tam > 18:
        tam -= 2
        f = f_fn(tam)
    return f


def capa(e, g, W, H, ruta, titulo="", creador=""):
    k = H / 1080
    t = _t(g)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # sello superior izquierdo
    cont = (g.get("continente") or "").upper()
    s1 = f"TOP 10 · {cont}" if cont else "TOP 10"
    sem = str(g.get("semana", "")).split("W")[-1]
    s2 = f"{t['semana']} {sem} · {t['cat'].get(e['id'][:1], t['ranking'])}"
    f1, f2 = anton(int(44 * k)), mont(int(30 * k))
    x, y, alto = int(48 * k), int(40 * k), int(66 * k)
    w1 = int(d.textlength(s1, font=f1) + 40 * k)
    w2 = int(d.textlength(s2, font=f2) + 40 * k)
    d.rectangle([x, y, x + w1, y + alto], fill=ROJO + (240,))
    d.text((x + 20 * k, y + (alto - f1.size) / 2 - 4 * k), s1, font=f1, fill=(255, 255, 255))
    d.rectangle([x + w1, y, x + w1 + w2, y + alto], fill=OSCURO + (225,))
    d.text((x + w1 + 20 * k, y + (alto - f2.size) / 2), s2, font=f2, fill=(255, 255, 255))
    # zócalo: puesto + creador + título
    rank = e.get("rank")
    if rank:
        y0, x0 = int(H - 400 * k), int(48 * k)
        caja = int(150 * k)
        d.rectangle([x0, y0, x0 + caja, y0 + caja], fill=ROJO + (245,))
        fr = anton(int(110 * k))
        num = f"#{rank}"
        d.text((x0 + (caja - d.textlength(num, font=fr)) / 2, y0 + (caja - fr.size) / 2 - 10 * k), num, font=fr, fill=(255, 255, 255))
        ancho = int(W * 0.62)
        fc = _ajusta(d, creador or " ", lambda s: anton(s), int(62 * k), ancho - 60 * k)
        d.rectangle([x0 + caja, y0, x0 + caja + ancho, y0 + int(86 * k)], fill=(255, 255, 255, 245))
        d.text((x0 + caja + 28 * k, y0 + (86 * k - fc.size) / 2 - 6 * k), creador, font=fc, fill=OSCURO)
        tit = re.sub(r"\s+", " ", titulo or "").strip()
        ft = mont(int(34 * k))
        while tit and d.textlength(tit, font=ft) > ancho - 60 * k:
            tit = tit[:-2].rstrip() + "…" if not tit.endswith("…") else tit[:-3].rstrip() + "…"
        d.rectangle([x0 + caja, y0 + int(86 * k), x0 + caja + ancho, y0 + caja], fill=OSCURO + (235,))
        if tit:
            d.text((x0 + caja + 28 * k, y0 + 86 * k + (64 * k - ft.size) / 2), tit, font=ft, fill=AMARILLO)
    # banda del cintillo (capa aparte, debajo del texto que corre) + etiqueta roja fija encima
    ch = int(CINT_H * k)
    banda = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(banda).rectangle([0, H - ch, W, H], fill=OSCURO + (235,))
    banda.save(str(ruta).replace(".png", "_banda.png"))
    fl = anton(int(32 * k))
    et = "#Top10RS"
    wl = int(d.textlength(et, font=fl) + 40 * k)
    d.rectangle([0, H - ch, wl, H], fill=ROJO + (255,))
    d.text((20 * k, H - ch + (ch - fl.size) / 2 - 3 * k), et, font=fl, fill=(255, 255, 255))
    im.save(ruta)
    return wl


def cintillo(g, H, ruta, siguiente=""):
    k = H / 1080
    t = _t(g)
    items = list(t["cint"])
    if g.get("corte_txt"):  # ediciones con otro corte (p. ej. la semana 48, cortada el miércoles)
        items = [g["corte_txt"] if ("Corte" in x or "Cut" in x) else x for x in items]
    if siguiente:
        items.insert(1, ("Siguiente parada: " if g.get("lang") == "es" else "Next stop: ") + siguiente)
    txt = "   •   ".join(items) + "   •   "
    f = mont(int(30 * k))
    ch = int(CINT_H * k)
    medida = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(txt, font=f)
    im = Image.new("RGBA", (int(medida) + 10, ch), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, (ch - f.size) / 2 - 2 * k), txt, font=f, fill=(255, 255, 255))
    im.save(ruta)
    return im.width, ch


def latino(t):
    """Solo lo que las fuentes del canal dibujan (alfabeto latino): evita cuadros vacíos en nombres CJK, árabes, hindi…"""
    t = "".join(c for c in (t or "") if ord(c) < 0x250 or c in "…’‘“”–—")
    t = re.sub(r"[#@]\S+", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -|·:")
    return t if sum(c.isalpha() for c in t) >= 3 else ""


def datos_video(proj, vid):
    """Creador y título del video (de categorias3.json)."""
    import json
    p = Path(proj) / "categorias3.json"
    if not p.exists():
        return "", ""
    c = json.loads(p.read_text())
    for k in ("views", "comments", "likes"):
        for v in c.get(k, []):
            if v.get("post_id") == vid:
                cr = latino(v.get("creator_name")) or (v.get("handle") or "").strip()
                return cr, latino(v.get("title", ""))
    return "", ""
