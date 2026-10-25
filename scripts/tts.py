"""Narración por escena. Motor por defecto GRATIS: edge-tts (voces neuronales de Microsoft).
Opcional: ElevenLabs si existe ELEVENLABS_API_KEY y TTS_MOTOR=elevenlabs.
Voz edge: variable EDGE_VOICE (por defecto es-MX-JorgeNeural). Ritmo: EDGE_RATE (ej. -5%).

Uso: python tts.py <proyecto_dir> [--mock]
Lee <proyecto_dir>/guion.json; escribe audio/<id>.mp3 y audio/<id>.align.json
--mock: audio en silencio con duración estimada (para probar sin API key).
"""
import base64
import os
import sys
from pathlib import Path

from common import duration, load_json, run, save_json

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


EDGE_VOICE = os.environ.get("EDGE_VOICE", "es-MX-JorgeNeural")
EDGE_RATE = os.environ.get("EDGE_RATE", "-4%")


VOZ_DIR = Path(__file__).resolve().parent.parent / "voces" / os.environ.get("PIPER_VOZ", "vits-piper-es_MX-claude-high")
_TTS = None


def piper_scene(text, mp3, align):
    """Voz neuronal offline gratis (Piper vía sherpa-onnx). Tiempos estimados por longitud de palabra."""
    global _TTS
    import sherpa_onnx, soundfile as sf
    if _TTS is None:
        onnx = next(VOZ_DIR.glob("*.onnx"))
        _TTS = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=str(onnx), tokens=str(VOZ_DIR / "tokens.txt"),
                                                       data_dir=str(VOZ_DIR / "espeak-ng-data")), num_threads=2)))
    a = _TTS.generate(text, sid=0, speed=float(os.environ.get("PIPER_SPEED", "0.93")))
    if len(a.samples) == 0:
        raise RuntimeError("La voz no generó audio (revisar versión de sherpa-onnx; probado con 1.13.8).")
    wav = str(mp3) + ".wav"
    sf.write(wav, a.samples, a.sample_rate)
    run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "44100",
         "-c:a", "libmp3lame", "-b:a", "160k", str(mp3)])
    os.remove(wav)
    dur = len(a.samples) / a.sample_rate
    chars = list(text)
    w = [0.6 if c == " " else (4.0 if c in ".!?" else (2.0 if c in ",;:" else 1.0)) for c in chars]
    k = dur * 0.97 / sum(w)
    st, en, t = [], [], 0.0
    for x in w:
        st.append(t); t += x * k; en.append(t)
    save_json({"characters": chars, "character_start_times_seconds": st,
               "character_end_times_seconds": en}, align)


_CB = None


def chatterbox_scene(text, mp3, align, lang):
    """Voz clonada del Fundador (Chatterbox, MIT). Referencia descifrada en voces/david.wav."""
    global _CB
    import torchaudio as ta
    if _CB is None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        try:
            _CB = ChatterboxMultilingualTTS.from_pretrained(device="cpu", t3_model="v3")
        except TypeError:
            _CB = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    ref = str(Path(__file__).resolve().parent.parent / "voces" / os.environ.get("VOZ_REF", "david.wav"))
    import re as _re
    partes = [p for p in _re.split(r"(?<=[.!?¿¡])\s+", text) if p.strip()]
    trozos, buf = [], ""
    for p in partes:  # bloques de ~250 caracteres para estabilidad
        if len(buf) + len(p) > 250 and buf:
            trozos.append(buf); buf = p
        else:
            buf = (buf + " " + p).strip()
    if buf:
        trozos.append(buf)
    import torch
    wavs = []
    for t in trozos:
        w = _CB.generate(t, language_id=lang, audio_prompt_path=ref,
                         exaggeration=float(os.environ.get("CB_EXAG", "0.5")), cfg_weight=float(os.environ.get("CB_CFG", "0.5")))
        wavs.append(w); wavs.append(torch.zeros(1, int(_CB.sr * 0.25)))
    wav = str(mp3) + ".wav"
    ta.save(wav, torch.cat(wavs, dim=1), _CB.sr)
    run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "44100",
         "-c:a", "libmp3lame", "-b:a", "160k", str(mp3)])
    os.remove(wav)
    dur = duration(mp3)
    chars = list(text)
    w = [0.6 if c == " " else (4.0 if c in ".!?" else (2.0 if c in ",;:" else 1.0)) for c in chars]
    k = dur * 0.97 / sum(w)
    st, en, tt = [], [], 0.0
    for x in w:
        st.append(tt); tt += x * k; en.append(tt)
    save_json({"characters": chars, "character_start_times_seconds": st,
               "character_end_times_seconds": en}, align)


def edge_scene(text, mp3, align):
    import asyncio
    import edge_tts

    async def go():
        com = edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE, boundary="WordBoundary")
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
    lang = g["lang"]
    out = proj / "audio"
    out.mkdir(exist_ok=True)
    escenas = g["escenas"]
    motor = os.environ.get("TTS_MOTOR", "piper")
    voice = voice_for(lang) if (not mock and motor == "elevenlabs") else None
    for i, e in enumerate(escenas):
        mp3, align = out / f"{e['id']}.mp3", out / f"{e['id']}.align.json"
        if mp3.exists() and align.exists():
            print(f"= {e['id']} (ya existe)")
            continue
        if mock:
            mock_scene(e["texto"], mp3, align)
        elif motor == "piper":
            piper_scene(e["texto"], mp3, align)
        elif motor == "chatterbox":
            chatterbox_scene(e["texto"], mp3, align, lang)
        elif motor == "edge":
            edge_scene(e["texto"], mp3, align)
        else:
            prev_t = escenas[i - 1]["texto"] if i else ""
            next_t = escenas[i + 1]["texto"] if i + 1 < len(escenas) else ""
            real_scene(e["texto"], mp3, align, voice, lang, prev_t, next_t)
        print(f"+ {e['id']}")


if __name__ == "__main__":
    main()
