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
    "divulgacion": (1000, 2600),     # 7-17 min (Cryptuline: ciencia de la espirulina)
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
    if g["lang"] not in ("es", "pt", "en", "fr"):
        err.append("lang debe ser 'es', 'pt', 'en' o 'fr'.")
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
    # SEO y calendario (avisos)
    seo = g["seo"]
    if g["tipo"] == "short" and "#shorts" not in seo.get("titulo", "").lower():
        warn.append("Short sin #shorts en el título.")
    if not seo.get("descripcion"):
        warn.append("seo.descripcion vacía.")
    if seo.get("privacidad") != "private":
        warn.append("seo.privacidad debería ser 'private' (YouTube lo publica a la hora de publicar_en).")
    pub = seo.get("publicar_en")
    if pub:
        from datetime import datetime, timezone
        try:
            if datetime.fromisoformat(pub.replace("Z", "+00:00")) <= datetime.now(timezone.utc):
                warn.append(f"publicar_en {pub} ya pasó.")
        except ValueError:
            err.append(f"publicar_en inválido: {pub} (usa AAAA-MM-DDTHH:MM:SSZ).")
    # Cryptuline: cumplimiento (+18, consulta médica, sin espirulina, sin promesas de cura)
    if "cryptuline" in str(Path(sys.argv[1]).resolve()):
        texto = " ".join(e["texto"] for e in g["escenas"]).lower() + " " + seo.get("titulo", "").lower()
        desc = seo.get("descripcion", "").lower()
        if "espirulina" in texto or "spirulina" in texto:
            err.append("Cryptuline: la espirulina está fuera hasta nuevo aviso del Fundador.")
        if "18 años" not in desc and "+18" not in desc:
            err.append("Cryptuline: falta el aviso de público mayor de 18 años en la descripción.")
        if "médico" not in desc:
            err.append("Cryptuline: falta «consulta a tu médico» en la descripción.")
        if "pubmed.ncbi.nlm.nih.gov" not in desc:
            warn.append("Cryptuline: la descripción no tiene enlaces de PubMed.")
        for w in ("cura ", "curar", "previene", "prevenir", "garantiza", "milagro"):
            if w in texto:
                warn.append(f"Cryptuline: revisar «{w.strip()}» (sin promesas de cura o prevención).")
        if g.get("revision_medica") not in ("pendiente", "aprobada", "observada"):
            warn.append("Cryptuline: falta revision_medica (pendiente | aprobada | observada).")
    for w in warn:
        print("AVISO:", w)
    if err:
        sys.exit("ERRORES:\n - " + "\n - ".join(err))
    print(f"OK guion: {len(ids)} escenas, {palabras} palabras (~{palabras / 150:.1f} min)")


if __name__ == "__main__":
    main()
