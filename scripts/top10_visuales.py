"""Visuales del Top 10: descarga los fotogramas PÚBLICOS que YouTube genera de cada video (miniatura + 3 cuadros
automáticos hq1/hq2/hq3 de i.ytimg.com) y arma la secuencia de cada escena según la duración de su audio.

Puesto completo ("video_id" + "modo": "completo"): 3 × (3 s en movimiento + 5 s congelado), miniatura y ficha.
Puesto rápido ("modo": "rapido"): miniatura en movimiento y ficha.
Escribe imagenes/<id>_NN.jpg y guarda la lista en escena["secuencia"] para render.py.
Uso: python top10_visuales.py <proyecto_dir>   (después de tts.py)
"""
import io
import json
import sys
from pathlib import Path

import requests
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from common import duration  # noqa: E402

W, H = 1920, 1080
BASE = "https://i.ytimg.com/vi/{vid}/{name}.jpg"


def bajar(vid, nombres):
    for n in nombres:
        try:
            r = requests.get(BASE.format(vid=vid, name=n), timeout=20)
            if r.status_code == 200 and len(r.content) > 2000:
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
                if im.size[0] > 130:  # evita el marcador gris de "no disponible"
                    return im
        except Exception:
            pass
    return None


def recortar_barras(im):
    """Quita bandas negras de los cuadros 4:3 de YouTube."""
    g = im.convert("L")
    w, h = g.size
    filas = [y for y in range(h) if sum(g.getpixel((x, y)) for x in range(0, w, 8)) / (w / 8) > 18]
    cols = [x for x in range(w) if sum(g.getpixel((x, y)) for y in range(0, h, 8)) / (h / 8) > 18]
    if filas and cols:
        im = im.crop((cols[0], filas[0], cols[-1] + 1, filas[-1] + 1))
    return im


def lienzo(im):
    """Imagen centrada sobre fondo desenfocado de sí misma (sirve para videos horizontales y verticales)."""
    im = recortar_barras(im)
    fondo = im.resize((W, int(W * im.height / im.width)) if im.width / im.height < W / H else (int(H * im.width / im.height), H))
    fondo = fondo.crop(((fondo.width - W) // 2, (fondo.height - H) // 2, (fondo.width - W) // 2 + W, (fondo.height - H) // 2 + H))
    fondo = fondo.filter(ImageFilter.GaussianBlur(40)).point(lambda p: int(p * 0.45))
    esc = min(W * 0.86 / im.width, H * 0.86 / im.height)
    fr = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    fondo.paste(fr, ((W - fr.width) // 2, (H - fr.height) // 2))
    return fondo


def main():
    proj = Path(sys.argv[1])
    g = json.loads((proj / "guion.json").read_text())
    img_dir = proj / "imagenes"
    img_dir.mkdir(exist_ok=True)
    for e in g["escenas"]:
        vid = e.get("video_id")
        if not vid:
            continue
        dur = duration(proj / "audio" / f"{e['id']}.mp3") + 0.6
        card = f"imagenes/{e['id']}_card.jpg" if (proj / "imagenes" / f"{e['id']}_card.jpg").exists() else None
        thumb = bajar(vid, ["maxresdefault", "hq720", "sddefault", "hqdefault"])
        frames = [bajar(vid, [f"maxres{k}", f"hq{k}", f"{k}"]) for k in (1, 2, 3)]
        seq = []
        def guarda(im, n):
            ruta = f"imagenes/{e['id']}_{n:02d}.jpg"
            lienzo(im).save(proj / ruta, quality=92)
            return ruta
        if e.get("modo") == "completo":
            for k, f in enumerate(frames, 1):
                if f is None:
                    continue
                r = guarda(f, k)
                seq += [{"img": r, "dur": 3.0, "mov": True}, {"img": r, "dur": 5.0, "mov": False}]
            if thumb is not None:
                seq.append({"img": guarda(thumb, 9), "dur": 4.0, "mov": True})
        else:
            if thumb is not None:
                seq.append({"img": guarda(thumb, 9), "dur": 3.0, "mov": True})
            f2 = frames[1] or frames[0]
            if f2 is not None:
                seq.append({"img": guarda(f2, 2), "dur": 2.5, "mov": False})
        # Cierre de la escena: conteo animado + ficha + (en el #1) tabla. Se reservan al final.
        cola = [{"img": a, "dur": 0.06, "mov": False, "limpio": True} for a in e.get("ficha_anim", [])]
        if card:
            cola.append({"img": card, "dur": 5.0, "mov": False, "limpio": True})
        if e.get("tabla"):
            cola.append({"img": e["tabla"], "dur": 6.0, "mov": False, "limpio": True})
        # Se agrega a la secuencia de la edición 2 sin reemplazarla: la ficha toma lo que sobra (mín. 3 s)
        base = sum(c["dur"] for c in cola if c["img"] != card) + (3.0 if card else 0)
        reserva = min(max(base, dur - sum(s["dur"] for s in seq)), dur * 0.5)
        total = 0.0
        recorte = []
        for s in seq:
            if total >= dur - reserva:
                break
            d = min(s["dur"], dur - reserva - total)
            if d > 0.2:
                recorte.append({**s, "dur": round(d, 3)})
                total += d
        resto = dur - total
        fija = sum(c["dur"] for c in cola if c["img"] != card)
        for c in cola:
            if c["img"] == card:
                c["dur"] = max(1.5, resto - fija)
            recorte.append({**c, "dur": round(c["dur"], 3)})
        if recorte:
            recorte[-1]["dur"] = round(recorte[-1]["dur"] + dur - sum(x["dur"] for x in recorte), 3)
        e["secuencia"] = recorte
        print(f"+ {e['id']}: {len(recorte)} tramos ({sum(1 for f in frames if f)} cuadros, miniatura={'sí' if thumb else 'no'})")
    (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
