"""Narración por escena, 100 % gratis. TTS_MOTOR: piper (offline, por defecto), chatterbox (voz del
Fundador) o edge (voces neuronales de Microsoft). ElevenLabs (de pago) fue retirado el 2026-11-01.
Voz edge: variable EDGE_VOICE (por defecto es-MX-JorgeNeural). Ritmo: EDGE_RATE (ej. -5%).

Uso: python tts.py <proyecto_dir> [--mock]
Lee <proyecto_dir>/guion.json; escribe audio/<id>.mp3 y audio/<id>.align.json
--mock: audio en silencio con duración estimada (para probar sin API key).
"""
import os
import sys
from pathlib import Path

from common import duration, load_json, run, save_json

WPS = 2.5  # palabras/segundo para estimación en modo mock


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


# Estilos de locución: (expresividad, cfg [más bajo = más pausado/dramático], tempo, pausa entre frases)
ESTILOS = {
    "gancho":     (0.75, 0.40, 1.04, 0.20),  # enérgico, atrapa en los primeros segundos
    "enfasis":    (0.70, 0.40, 1.00, 0.25),
    "narrativo":  (0.55, 0.50, 1.00, 0.25),  # historias e ilustraciones
    "ensenanza":  (0.45, 0.50, 1.00, 0.25),  # explicación clara
    "agil":       (0.50, 0.55, 1.07, 0.15),  # shorts, listas, repasos
    "calido":     (0.50, 0.45, 0.97, 0.30),  # aplicación, invitación
    "reflexivo":  (0.40, 0.35, 0.94, 0.40),  # preguntas para meditar
    "oracion":    (0.35, 0.30, 0.92, 0.45),  # oración, cierre solemne
}
MAPA_ID = {"gancho": "gancho", "intro": "gancho", "cierre": "reflexivo", "oracion": "oracion",
           "aplicacion": "calido", "reto": "calido", "historia": "narrativo", "lenador": "narrativo",
           "mensaje": "agil"}


def estilo(emocion, text):
    """Elige el estilo: campo 'emocion' de la escena, o lo infiere del id y del texto."""
    e = emocion if emocion in ESTILOS else None
    if not e:
        t = text.lower()
        if "oremos" in t or "amén" in t:
            e = "oracion"
        elif t.count("?") >= 3:
            e = "reflexivo"
        elif t.count("!") >= 2:
            e = "enfasis"
        else:
            e = "ensenanza"
    return ESTILOS[e]


def chatterbox_scene(text, mp3, align, lang, emocion=None):
    """Voz clonada del Fundador (Chatterbox, MIT). Referencia descifrada en voces/david.wav."""
    global _CB
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
    exag, cfg, tempo, pausa = estilo(emocion, text)
    wavs = []
    for t in trozos:
        w = _CB.generate(t, language_id=lang, audio_prompt_path=ref, exaggeration=exag, cfg_weight=cfg)
        wavs.append(w); wavs.append(torch.zeros(1, int(_CB.sr * pausa)))
    wav = str(mp3) + ".wav"
    import soundfile as sf  # torchaudio nuevo exige torchcodec; soundfile no
    sf.write(wav, torch.cat(wavs, dim=1).squeeze(0).cpu().numpy(), _CB.sr)
    estudio = (f"atempo={tempo}," if abs(tempo - 1) > 0.005 else "") + ("highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.5:g=1.5,"
               "deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=1.5,"
               "loudnorm=I=-16:TP=-1.5:LRA=7")
    run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-af", estudio, "-ar", "44100",
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
    if motor not in ("piper", "chatterbox", "edge"):
        sys.exit(f"TTS_MOTOR desconocido: {motor} (usa piper, chatterbox o edge; todo gratis).")
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
            emo = e.get("emocion") or MAPA_ID.get(e["id"].split("-")[0]) or ("agil" if g.get("tipo") == "short" else None)
            chatterbox_scene(e["texto"], mp3, align, lang, emo)
        elif motor == "edge":
            edge_scene(e["texto"], mp3, align)
        print(f"+ {e['id']}")


if __name__ == "__main__":
    main()
