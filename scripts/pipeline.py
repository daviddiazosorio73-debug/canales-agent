"""Ejecuta el pipeline completo sobre un proyecto.

Uso: python pipeline.py <proyecto_dir> [--mock] [--offline] [--borrador] [--subir]
  --mock      audio en silencio (sin ElevenLabs) para probar
  --offline   sin Pexels, fondos generados
  --borrador  render rápido (calidad menor)
  --subir     sube a YouTube al final (privado o programado)
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def step(script, *args):
    print(f"\n== {script} ==")
    r = subprocess.run([sys.executable, str(HERE / script), *args])
    if r.returncode:
        sys.exit(f"Paso {script} falló.")


def main():
    proj = sys.argv[1]
    a = sys.argv[2:]
    step("validate.py", proj)
    step("tts.py", proj, *(["--mock"] if "--mock" in a else []))
    step("visuals.py", proj, *(["--offline"] if "--offline" in a else []))
    step("render.py", proj, *(["borrador"] if "--borrador" in a else []))
    step("thumbnail.py", proj)
    step("metadata.py", proj)
    if "--subir" in a:
        if "--mock" in a:
            sys.exit("No se sube un video con audio de prueba (--mock).")
        step("upload.py", proj)
    print(f"\nListo: {Path(proj) / 'salida'}")


if __name__ == "__main__":
    main()
