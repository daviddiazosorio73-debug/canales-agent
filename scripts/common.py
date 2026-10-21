"""Utilidades compartidas del pipeline."""
import json
import os
import subprocess
import sys
from pathlib import Path

import os as _os
VERTICAL = _os.environ.get("VERTICAL") == "1"
W, H, FPS = (1080, 1920, 30) if VERTICAL else (1920, 1080, 30)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_REG_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def font_path(bold=True, skill_dir=None):
    """Prefiere fuentes de assets/fonts; si no, del sistema."""
    if skill_dir:
        name = "Bold" if bold else "Regular"
        for p in sorted((Path(skill_dir) / "assets" / "fonts").glob(f"*{name}*.ttf")):
            return str(p)
    for p in (FONT_CANDIDATES if bold else FONT_REG_CANDIDATES):
        if os.path.exists(p):
            return p
    sys.exit("No se encontró una fuente TTF. Coloca una en assets/fonts/.")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"Falló: {' '.join(map(str, cmd[:6]))} ...")
    return r.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def ts(sec, srt=False):
    ms = int(round(sec * 1000))
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
