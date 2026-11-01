"""Narración por escena, 100 % gratis: edge-tts (voces neuronales de Microsoft, sin clave ni cuenta).

Uso: python tts.py <proyecto_dir> [--mock]
Lee <proyecto_dir>/guion.json; escribe audio/<id>.mp3 y audio/<id>.align.json (tiempos por carácter
para los subtítulos).
Voz por idioma: EDGE_VOICE_ES (por defecto es-MX-JorgeNeural) y EDGE_VOICE_PT (pt-BR-AntonioNeural),
o EDGE_VOICE para ambos. Ritmo: EDGE_RATE (por defecto -4%).
--mock: audio en silencio con duración estimada (para probar sin internet).
"""
import asyncio
import os
import sys
from pathlib import Path

from common import load_json, run, save_json

WPS = 2.5  # palabras/segundo para estimación en modo mock
VOZ_DEF = {"es": "es-MX-JorgeNeural", "pt": "pt-BR-AntonioNeural"}
EDGE_RATE = os.environ.get("EDGE_RATE", "-4%")


def voz(lang):
    return (os.environ.get(f"EDGE_VOICE_{lang.upper()}") or os.environ.get("EDGE_VOICE")
            or VOZ_DEF.get(lang, VOZ_DEF["es"]))


def mock_scene(text, mp3, align):
    dur = max(2.0, len(text.split()) / WPS)
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{dur:.2f}", "-c:a", "libmp3lame", "-b:a", "128k", str(mp3)])
    chars = list(text)
    step = dur / max(1, len(chars))
    save_json({"characters": chars,
               "character_start_times_seconds": [i * step for i in range(len(chars))],
               "character_end_times_seconds": [(i + 1) * step for i in range(len(chars))]}, align)


def edge_scene(text, mp3, align, voice):
    import edge_tts

    async def go():
        com = edge_tts.Communicate(text, voice, rate=EDGE_RATE, boundary="WordBoundary")
        words = []
        with open(mp3, "wb") as f:
            async for ch in com.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
        return words

    words = asyncio.run(go())
    chars, st, en = [], [], []
    for i, (s, e, w) in enumerate(words):
        step = (e - s) / max(1, len(w))
        for k, c in enumerate(w):
            chars.append(c); st.append(s + k * step); en.append(s + (k + 1) * step)
        if i + 1 < len(words):
            chars.append(" "); st.append(e); en.append(words[i + 1][0])
    save_json({"characters": chars, "character_start_times_seconds": st,
               "character_end_times_seconds": en}, align)


def main():
    proj = Path(sys.argv[1])
    mock = "--mock" in sys.argv
    g = load_json(proj / "guion.json")
    out = proj / "audio"
    out.mkdir(exist_ok=True)
    voice = voz(g["lang"])
    for e in g["escenas"]:
        mp3, align = out / f"{e['id']}.mp3", out / f"{e['id']}.align.json"
        if mp3.exists() and align.exists():
            print(f"= {e['id']} (ya existe)")
            continue
        if mock:
            mock_scene(e["texto"], mp3, align)
        else:
            edge_scene(e["texto"], mp3, align, voice)
        print(f"+ {e['id']}")


if __name__ == "__main__":
    main()
