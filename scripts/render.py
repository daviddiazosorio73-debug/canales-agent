"""Render final: Ken Burns + tarjetas de texto + subtítulos + música + loudnorm.

Uso: python render.py <proyecto_dir> [--sin-subtitulos-quemados] [--calidad borrador|final]
Requiere audio/ (tts.py) e imagenes/ (visuals.py).
Escribe salida/video.mp4, salida/subtitulos.srt, salida/capitulos.json
"""
import os
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import FPS, H, W, VERTICAL, duration, font_path, load_json, run, save_json, ts

SKILL_DIR = Path(__file__).resolve().parent.parent
PAD = 0.6          # silencio tras cada escena (respiro)
FADE = 0.35
MOVES = [  # (zoom inicio, zoom fin, x, y) alternados por escena
    (1.00, 1.12, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    (1.12, 1.00, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    (1.08, 1.08, "(iw-iw/zoom)*on/{N}", "ih/2-(ih/zoom/2)"),
    (1.00, 1.10, "(iw-iw/zoom)", "(ih-ih/zoom)/3"),
]


def overlay(e, path, brand):
    """PNG transparente: viñeta, tarjeta de texto (cita/idea clave) y logo."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(260):  # degradado inferior para legibilidad de subtítulos
        a = int(170 * (i / 260) ** 1.6)
        d.line([(0, H - 260 + i), (W, H - 260 + i)], fill=(0, 0, 0, a))
    txt = e.get("texto_pantalla")
    if txt:
        f_ref = ImageFont.truetype(font_path(True, SKILL_DIR), 54)
        f_txt = ImageFont.truetype(font_path(not VERTICAL and False or VERTICAL, SKILL_DIR), 64 if VERTICAL else 46)
        ref = e.get("referencia", "")
        lines = textwrap.wrap(txt, 24 if VERTICAL else 46)[:5]
        lh = 84 if VERTICAL else 62
        box_h = 70 + len(lines) * lh + (80 if ref else 0)
        x0, y0 = (70, 330) if VERTICAL else (120, 140)
        bw = W - 2 * x0 if VERTICAL else 1100
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + box_h], 24, fill=(10, 14, 28, 190))
        d.rectangle([x0, y0 + 24, x0 + 10, y0 + box_h - 24], fill=brand)
        y = y0 + 40
        for ln in lines:
            d.text((x0 + 50, y), ln, font=f_txt, fill=(255, 255, 255, 255))
            y += lh
        if ref:
            d.text((x0 + 50, y + 14), ref, font=f_ref, fill=brand + (255,))
    av = os.environ.get("AVATAR")
    if av and Path(av).exists():  # presentador del canal (imagen) en círculo, sobre la zona de subtítulos
        from PIL import ImageOps
        a = Image.open(av).convert("RGB")
        lado = int(min(a.width, a.height * 0.62))
        a = a.crop(((a.width - lado) // 2, int(a.height * 0.03), (a.width - lado) // 2 + lado, int(a.height * 0.03) + lado))
        tam = 300 if VERTICAL else 250
        a = ImageOps.fit(a, (tam, tam))
        mask = Image.new("L", (tam, tam), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, tam - 1, tam - 1], fill=255)
        borde = Image.new("RGBA", (tam + 12, tam + 12), (0, 0, 0, 0))
        ImageDraw.Draw(borde).ellipse([0, 0, tam + 11, tam + 11], fill=brand + (255,))
        x0, y0 = (40, H - tam - 520) if VERTICAL else (40, H - tam - 230)
        img.alpha_composite(borde, (x0 - 6, y0 - 6))
        img.paste(a, (x0, y0), mask)
    logo = SKILL_DIR / "assets" / "logo.png"
    if logo.exists():
        lg = Image.open(logo).convert("RGBA")
        lg.thumbnail((180, 180))
        img.alpha_composite(lg, (W - lg.width - 60, 50))
    img.save(path)


def scene_clip(i, e, proj, tmp, preset, brand):
    img = proj / "imagenes" / f"{e['id']}.jpg"
    aud = proj / "audio" / f"{e['id']}.mp3"
    dur = duration(aud) + PAD
    n = int(dur * FPS)
    z0, z1, x, y = MOVES[i % len(MOVES)]
    z = f"{z0}+({z1}-{z0})*on/{n}"
    ov = tmp / f"{e['id']}_ov.png"
    overlay(e, ov, brand)
    out = tmp / f"{i:03d}.mp4"
    if e.get("secuencia"):  # varios tramos: imagen en movimiento o congelada
        partes = []
        for k, sgm in enumerate(e["secuencia"]):
            nf = max(1, int(float(sgm["dur"]) * FPS))
            src = proj / sgm["img"]
            pz = "1.0+0.12*on/{}".format(nf) if sgm.get("mov") else "1.0"
            parte = tmp / f"{e['id']}_seg{k:02d}.mp4"
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(src),
                 "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                        f"zoompan=z='{pz}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p",
                 "-frames:v", str(nf), "-c:v", "libx264", "-preset", preset, "-crf", "19", str(parte)])
            partes.append(parte)
        lst = tmp / f"{e['id']}_segs.txt"
        lst.write_text("".join(f"file '{x.name}'\n" for x in partes))
        bg = tmp / f"{e['id']}_bg.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(bg)])
        t_limpio, acc = None, 0.0
        for sgm in e["secuencia"]:
            if sgm.get("limpio") and t_limpio is None:
                t_limpio = acc
            acc += max(1, int(float(sgm["dur"]) * FPS)) / FPS
        ov2 = ov
        if t_limpio is not None:  # en las fichas no va la caja de texto (la ficha ya lo dice todo)
            ov2 = tmp / f"{e['id']}_ov_limpio.png"
            overlay({k: v for k, v in e.items() if k != "texto_pantalla"}, ov2, brand)
            ovf = (f"[bg][1:v]overlay=0:0:enable='lt(t,{t_limpio:.3f})'[b1];"
                   f"[b1][3:v]overlay=0:0:enable='gte(t,{t_limpio:.3f})',")
        else:
            ovf = "[bg][1:v]overlay=0:0,"
        fc = (f"[0:v]format=yuv420p[bg];{ovf}"
              f"fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE:.3f}:d={FADE}[v];"
              f"[2:a]apad=pad_dur={PAD},aresample=48000[a]")
        run(["ffmpeg", "-y", "-v", "error", "-i", str(bg),
             "-loop", "1", "-framerate", str(FPS), "-i", str(ov), "-i", str(aud),
             "-loop", "1", "-framerate", str(FPS), "-i", str(ov2),
             "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-preset", preset, "-crf", "19", "-c:a", "aac", "-b:a", "192k",
             str(out)])
        return out, dur
    fc = (f"[0:v]zoompan=z='{z}':x='{x.format(N=n)}':y='{y.format(N=n)}':d=1:s={W}x{H}:fps={FPS},"
          f"format=yuv420p[bg];[bg][1:v]overlay=0:0,"
          f"fade=t=in:st=0:d={FADE},fade=t=out:st={dur - FADE:.3f}:d={FADE}[v];"
          f"[2:a]apad=pad_dur={PAD},aresample=48000[a]")
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(img),
         "-loop", "1", "-framerate", str(FPS), "-i", str(ov), "-i", str(aud),
         "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", preset, "-crf", "19", "-c:a", "aac", "-b:a", "192k",
         str(out)])
    return out, dur


def words_from_align(al, offset):
    words, cur, st = [], "", None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"],
                        al["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                words.append((cur, st + offset, last + offset))
            cur, st = "", None
            continue
        if st is None:
            st = s
        cur += ch
        last = e
    if cur:
        words.append((cur, st + offset, last + offset))
    return words


def cues(words, max_chars=None):
    max_chars = max_chars or (26 if VERTICAL else 42)
    out, buf = [], []
    for w in words:
        if buf and len(" ".join(x[0] for x in buf + [w])) > max_chars:
            out.append(buf)
            buf = []
        buf.append(w)
        if w[0][-1] in ".?!;:" and len(" ".join(x[0] for x in buf)) > 18:
            out.append(buf)
            buf = []
    if buf:
        out.append(buf)
    return [(" ".join(x[0] for x in c), c[0][1], c[-1][2]) for c in out]


def write_subs(all_cues, srt, ass):
    # extiende cada subtítulo 0.15 s sin solaparse con el siguiente
    all_cues = [(t, a, min(b + 0.15, all_cues[k + 1][1] - 0.02) - 0.15 if k + 1 < len(all_cues) else b)
                for k, (t, a, b) in enumerate(all_cues)]
    with open(srt, "w", encoding="utf-8") as f:
        for k, (t, a, b) in enumerate(all_cues, 1):
            f.write(f"{k}\n{ts(a, True)} --> {ts(b + 0.15, True)}\n{t}\n\n")

    def at(x):
        cs = int(round(x * 100))
        return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"
    fname = ImageFont.truetype(font_path(True, SKILL_DIR), 10).getname()[0]
    with open(ass, "w", encoding="utf-8") as f:
        style = (f"Style: Default,{fname},78,&H0000FFFF,&H00000000,&H64000000,1,1,4,1,2,620\n\n" if VERTICAL
                 else f"Style: Default,{fname},62,&H00FFFFFF,&H00000000,&H64000000,1,1,3,1,2,70\n\n")
        f.write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, "
                "BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV\n"
                + style +
                "[Events]\nFormat: Layer, Start, End, Style, Text\n")
        for t, a, b in all_cues:
            f.write(f"Dialogue: 0,{at(a)},{at(b + 0.15)},Default,{t}\n")


def pantalla_final(g, tmp, preset, brand, seg):
    """Cola para la pantalla final de YouTube: va DESPUÉS de todo el contenido, así los elementos
    (suscribirse, lista) nunca tapan la presentación del #1. Sin voz; la música sigue debajo."""
    es = g.get("lang", "es") == "es"
    im = Image.new("RGB", (W, H), (10, 8, 20))
    d = ImageDraw.Draw(im)
    for y in range(H):  # degradado suave hacia el color de la marca
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c * 0.35 * k + 10 * (1 - k)) for c in brand))
    try:
        from top10_fichas import anton, mont
        f1, f2 = anton(int(H * 0.13)), mont(int(H * 0.04))
    except Exception:
        f1 = ImageFont.truetype(font_path(True, SKILL_DIR), int(H * 0.11))
        f2 = ImageFont.truetype(font_path(False, SKILL_DIR), int(H * 0.04))
    t1 = "#Top10RS"
    t2 = ("Suscríbete · Sigue la vuelta al mundo" if es else "Subscribe · Keep touring the world")
    t3 = ("¿Premiación en vivo? Comenta #PremiosTop10RS" if es else "Live awards? Comment #PremiosTop10RS")
    y = int(H * 0.08)
    for txt, f, col in ((t1, f1, (255, 255, 255)), (t2, f2, (255, 214, 0)), (t3, f2, (255, 255, 255))):
        d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=col, stroke_width=3, stroke_fill=(0, 0, 0))
        y += int(f.size * 1.35)
    png = tmp / "pantalla_final.png"
    im.save(png)
    out = tmp / "999_final.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(png),
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-vf", f"fade=t=in:st=0:d={FADE},format=yuv420p", "-t", f"{seg:.3f}",
         "-c:v", "libx264", "-preset", preset, "-crf", "19", "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


def main():
    proj = Path(sys.argv[1])
    burn = "--sin-subtitulos-quemados" not in sys.argv
    preset = "ultrafast" if "borrador" in sys.argv else "medium"
    g = load_json(proj / "guion.json")
    brand = tuple(g.get("color_marca", [212, 168, 83]))
    tmp = proj / "tmp"
    tmp.mkdir(exist_ok=True)
    salida = proj / "salida"
    salida.mkdir(exist_ok=True)

    clips, t, all_cues, caps = [], 0.0, [], []
    for i, e in enumerate(g["escenas"]):
        clip, dur = scene_clip(i, e, proj, tmp, preset, brand)
        clips.append(clip)
        al = load_json(proj / "audio" / f"{e['id']}.align.json")
        all_cues += cues(words_from_align(al, t))
        if e.get("capitulo"):
            caps.append({"t": round(t, 2), "titulo": e["capitulo"]})
        t += dur
        print(f"+ escena {e['id']} {dur:.1f}s")

    seg_final = float(g.get("pantalla_final_seg", 15 if g.get("tipo") == "top10" and not VERTICAL else 0))
    if seg_final > 0:
        clips.append(pantalla_final(g, tmp, preset, brand, seg_final))
        t += seg_final
        print(f"+ pantalla final {seg_final:.0f}s")

    (tmp / "lista.txt").write_text("".join(f"file '{c.name}'\n" for c in clips))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"),
         "-c", "copy", str(tmp / "unido.mp4")])

    srt, ass = salida / "subtitulos.srt", tmp / "subs.ass"
    write_subs(all_cues, srt, ass)

    musica = next(iter(sorted((proj).glob("musica.*")) + sorted((SKILL_DIR / "assets" / "musica").glob("*.mp3"))), None)
    inputs = ["-i", str(tmp / "unido.mp4")]
    fdir = str(Path(font_path(True, SKILL_DIR)).parent)
    # 4K (3840x2160) en videos insignia y Top 10: YouTube les da mayor tasa de bits y calidad. Los subtítulos se
    # dibujan después del escalado, nítidos a 4K. Shorts: siempre 1080x1920.
    es4k = bool(os.environ.get("RES_4K")) and not VERTICAL
    esc = "scale=3840:2160:flags=lanczos,unsharp=5:5:0.5," if es4k else ""
    vf = f"[0:v]{esc}ass={ass}:fontsdir={fdir}[v]" if burn else f"[0:v]{esc or 'null,'}null[v]"
    if es4k and preset == "medium":
        preset = "fast"
    if musica:
        inputs += ["-stream_loop", "-1", "-i", str(musica)]
        af = ("[1:a]volume=0.22,aresample=48000[m];[0:a]asplit=2[n][sc];"
              "[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
              "[n][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        af = "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", f"{vf};{af}",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", preset, "-crf", "19",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", "-t", f"{t:.3f}", str(salida / "video.mp4")])
    save_json({"duracion": round(t, 2), "capitulos": caps}, salida / "capitulos.json")
    print(f"OK salida/video.mp4 ({ts(t)})")


if __name__ == "__main__":
    main()
