"""Pistas de audio extra (mismo video, otros idiomas) para la función «idiomas de audio» de YouTube. 100 % gratis.

Uso: python audios_extra.py <proyecto_dir>
Se ejecuta en el runner después de render.py si el guion trae "audios_extra": {"es": "es-MX-DaliaNeural", ...}
y cada escena trae "texto_<idioma>". Para cada idioma:
  - narra cada escena con edge-tts (voz neuronal gratuita),
  - la ajusta a la duración exacta de la escena del video (atempo entre 0.80 y 1.30; si sobra, silencio),
  - suma la misma música de fondo y normaliza igual que render.py,
  - escribe salida/audio_<idioma>.m4a y salida/subtitulos_<idioma>.srt (una línea por escena).
YouTube Data API no permite subir pistas de audio: se agregan en YouTube Studio → Idiomas → Agregar audio.
"""
import asyncio
import sys
from pathlib import Path

from common import duration, load_json, run, ts

sys.path.insert(0, str(Path(__file__).parent))
from render import PAD, SKILL_DIR  # noqa: E402


async def _tts(texto, voz, mp3):
    import edge_tts
    await edge_tts.Communicate(texto, voz).save(str(mp3))


def ajustar(src, dst, objetivo):
    """Deja el audio de la escena exactamente en `objetivo` segundos."""
    d = duration(src)
    filtros = []
    if d > objetivo - 0.15:
        f = min(1.30, max(1.0, d / max(0.5, objetivo - 0.15)))
        filtros.append(f"atempo={f:.3f}")
    filtros.append(f"apad=whole_dur={objetivo:.3f}")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", ",".join(filtros), "-ar", "48000", "-ac", "2",
         "-t", f"{objetivo:.3f}", str(dst)])
    return d / objetivo


def main():
    proj = Path(sys.argv[1])
    g = load_json(proj / "guion.json")
    extra = g.get("audios_extra") or {}
    if not extra:
        print("sin audios_extra")
        return
    salida, tmp = proj / "salida", proj / "tmp" / "extra"
    tmp.mkdir(parents=True, exist_ok=True)
    musica = next(iter(sorted(proj.glob("musica.*")) + sorted((SKILL_DIR / "assets" / "musica").glob("*.mp3"))), None)
    seg_final = float(g.get("pantalla_final_seg", 0) or 0)
    for lang, voz in extra.items():
        partes, srt, t = [], [], 0.0
        for i, e in enumerate(g["escenas"]):
            objetivo = duration(proj / "audio" / f"{e['id']}.mp3") + PAD
            texto = e.get(f"texto_{lang}")
            dst = tmp / f"{lang}_{i:03d}.wav"
            if not texto:
                print(f"AVISO: escena {e['id']} sin texto_{lang}: va en silencio")
                run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                     "-t", f"{objetivo:.3f}", str(dst)])
            else:
                mp3 = tmp / f"{lang}_{i:03d}.mp3"
                asyncio.run(_tts(texto, voz, mp3))
                r = ajustar(mp3, dst, objetivo)
                if r > 1.30:
                    print(f"AVISO: escena {e['id']} en {lang} es {r:.2f}x más larga que la original; acorta texto_{lang}")
                srt.append(f"{len(srt) + 1}\n{ts(t, srt=True)} --> {ts(t + objetivo - 0.2, srt=True)}\n{texto}\n")
            partes.append(dst)
            t += objetivo
        if seg_final > 0:
            dst = tmp / f"{lang}_final.wav"
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{seg_final:.3f}", str(dst)])
            partes.append(dst)
            t += seg_final
        lista = tmp / f"{lang}_lista.txt"
        lista.write_text("".join(f"file '{p.name}'\n" for p in partes))
        voz_wav = tmp / f"{lang}_voz.wav"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(voz_wav)])
        out = salida / f"audio_{lang}.m4a"
        if musica:
            af = ("[1:a]volume=0.22,aresample=48000[m];[0:a]asplit=2[n][sc];"
                  "[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
                  "[n][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
            run(["ffmpeg", "-y", "-v", "error", "-i", str(voz_wav), "-stream_loop", "-1", "-i", str(musica),
                 "-filter_complex", af, "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-t", f"{t:.3f}", str(out)])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-i", str(voz_wav), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                 "-c:a", "aac", "-b:a", "192k", str(out)])
        (salida / f"subtitulos_{lang}.srt").write_text("\n".join(srt), encoding="utf-8")
        print(f"OK salida/audio_{lang}.m4a ({ts(t)}) + subtitulos_{lang}.srt")


if __name__ == "__main__":
    main()
