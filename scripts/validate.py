"""Valida guion.json antes de gastar créditos de voz.

Uso: python validate.py <proyecto_dir>
"""
import re
import sys
from pathlib import Path

from common import load_json

RANGO = {  # palabras (~150 por minuto)
    "intro": (700, 1250),            # 5-8 min
    "diario": (800, 1800),           # 6-12 min
    "resumen_viernes": (550, 1100),  # 4-7 min
    "repaso_sabado": (2200, 3800),   # 15-25 min
    "sermon": (1500, 3600),          # 10-24 min (Semana de Mayordomía)
    "analisis": (1400, 3000),        # 10-20 min (martes/jueves)
    "short": (90, 190),
    "top10": (700, 2700),            # 5-18 min (Top 10 Redes Sociales)              # 40-75 s vertical
}


def main():
    g = load_json(Path(sys.argv[1]) / "guion.json")
    err, warn = [], []
    for k in ["lang", "tipo", "tema", "escenas", "seo", "miniatura"]:
        if k not in g:
            err.append(f"Falta campo '{k}'.")
    if err:
        sys.exit("\n".join(err))
    if g["tipo"] not in RANGO:
        err.append(f"tipo debe ser uno de: {', '.join(RANGO)}.")
    if g["lang"] not in ("es", "pt"):
        err.append("lang debe ser 'es' o 'pt'.")
    ids = [e.get("id") for e in g["escenas"]]
    if len(set(ids)) != len(ids) or not all(ids):
        err.append("Cada escena necesita un 'id' único.")
    for e in g["escenas"]:
        if not re.fullmatch(r"[a-z0-9_-]+", e.get("id", "")):
            err.append(f"id inválido: {e.get('id')} (solo a-z, 0-9, _ -)")
        if len(e.get("texto", "")) > 4500:
            err.append(f"Escena {e['id']}: texto > 4500 caracteres; divídela.")
    caps = [e for e in g["escenas"] if e.get("capitulo")]
    if g["tipo"] != "short" and (not g["escenas"][0].get("capitulo") or len(caps) < 3):
        err.append("Se necesitan ≥3 escenas con 'capitulo' y la primera debe tenerlo.")
    palabras = sum(len(e["texto"].split()) for e in g["escenas"])
    lo, hi = RANGO.get(g["tipo"], (0, 99999))
    if not lo <= palabras <= hi:
        warn.append(f"{palabras} palabras; esperado {lo}-{hi} para tipo '{g['tipo']}'.")
    if len(g["seo"].get("titulo", "")) > 100:
        err.append("seo.titulo > 100 caracteres.")
    for k in ["linea1"]:
        if not g["miniatura"].get(k):
            err.append(f"miniatura.{k} vacío.")
    for w in warn:
        print("AVISO:", w)
    if err:
        sys.exit("ERRORES:\n - " + "\n - ".join(err))
    print(f"OK guion: {len(ids)} escenas, {palabras} palabras (~{palabras / 150:.1f} min)")


if __name__ == "__main__":
    main()
