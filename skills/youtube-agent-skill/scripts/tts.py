"""Narración por escena con ElevenLabs (incluye tiempos por carácter para subtítulos).

Uso: python tts.py <proyecto_dir> [--mock]
Lee <proyecto_dir>/guion.json; escribe audio/<id>.mp3 y audio/<id>.align.json
--mock: audio en silencio con duración estimada (para probar sin API key).
"""
import base64
import os
import sys
from pathlib import Path

from common import load_json, run, save_json

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
WPS = 2.5  # palabras/segundo para estimación en modo mock


def voice_for(lang):
    v = os.environ.get(f"ELEVENLABS_VOICE_ID_{lang.upper()}") or os.environ.get("ELEVENLABS_VOICE_ID")
    if not v:
        sys.exit(f"Falta ELEVENLABS_VOICE_ID_{lang.upper()} (o ELEVENLABS_VOICE_ID).")
    return v


def mock_scene(text, mp3, align):
    words = text.split()
    dur = max(2.0, len(words) / WPS)
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{dur:.2f}", "-c:a", "libmp3lame", "-b:a", "128k", str(mp3)])
    starts, ends, chars = [], [], list(text)
    step = dur / max(1, len(chars))
    for i in range(len(chars)):
        starts.append(i * step)
        ends.append((i + 1) * step)
    save_json({"characters": chars, "character_start_times_seconds": starts,
               "character_end_times_seconds": ends}, align)


def real_scene(text, mp3, align, voice, lang, prev_text, next_text):
    import requests
    key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("Falta ELEVENLABS_API_KEY.")
    body = {
        "text": text,
        "model_id": MODEL,
        "language_code": lang,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15,
                           "use_speaker_boost": True},
    }
    if prev_text:
        body["previous_text"] = prev_text[-500:]
    if next_text:
        body["next_text"] = next_text[:500]
    r = requests.post(API.format(voice=voice), params={"output_format": "mp3_44100_128"},
                      headers={"xi-api-key": key}, json=body, timeout=300)
    if r.status_code == 400 and "language_code" in r.text:
        body.pop("language_code")  # algunos modelos no aceptan language_code
        r = requests.post(API.format(voice=voice), params={"output_format": "mp3_44100_128"},
                          headers={"xi-api-key": key}, json=body, timeout=300)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs {r.status_code}: {r.text[:500]}")
    data = r.json()
    Path(mp3).write_bytes(base64.b64decode(data["audio_base64"]))
    save_json(data.get("alignment") or data.get("normalized_alignment"), align)


def main():
    proj = Path(sys.argv[1])
    mock = "--mock" in sys.argv
    g = load_json(proj / "guion.json")
    lang = g["lang"]
    out = proj / "audio"
    out.mkdir(exist_ok=True)
    escenas = g["escenas"]
    voice = None if mock else voice_for(lang)
    for i, e in enumerate(escenas):
        mp3, align = out / f"{e['id']}.mp3", out / f"{e['id']}.align.json"
        if mp3.exists() and align.exists():
            print(f"= {e['id']} (ya existe)")
            continue
        if mock:
            mock_scene(e["texto"], mp3, align)
        else:
            prev_t = escenas[i - 1]["texto"] if i else ""
            next_t = escenas[i + 1]["texto"] if i + 1 < len(escenas) else ""
            real_scene(e["texto"], mp3, align, voice, lang, prev_t, next_t)
        print(f"+ {e['id']}")


if __name__ == "__main__":
    main()
