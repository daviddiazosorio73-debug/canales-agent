"""Arma metadatos finales de YouTube y valida límites.

Uso: python metadata.py <proyecto_dir>
Combina guion.json["seo"] + salida/capitulos.json + creditos.json -> salida/metadata.json
"""
import sys
from pathlib import Path

from common import load_json, save_json, ts

LIMITS = {"titulo": 100, "descripcion": 5000, "tags_total": 500}
CREDITOS_TXT = {"es": "Imágenes: Pexels", "pt": "Imagens: Pexels"}
CAP_TXT = {"es": "Capítulos", "pt": "Capítulos"}


def main():
    proj = Path(sys.argv[1])
    g = load_json(proj / "guion.json")
    seo, lang = g["seo"], g["lang"]
    caps = load_json(proj / "salida" / "capitulos.json")["capitulos"]
    cred_path = proj / "creditos.json"
    creditos = load_json(cred_path) if cred_path.exists() else []

    errores = []
    if len(caps) >= 3 and caps[0]["t"] == 0:
        bloque_caps = f"\n\n{CAP_TXT[lang]}:\n" + "\n".join(f"{ts(c['t'])} {c['titulo']}" for c in caps)
        if any(b["t"] - a["t"] < 10 for a, b in zip(caps, caps[1:])):
            errores.append("Hay capítulos de menos de 10 s; YouTube no los mostrará.")
    else:
        bloque_caps = ""
        errores.append("Se necesitan ≥3 capítulos y el primero en 00:00 (marca 'capitulo' en la escena 1).")

    desc = seo["descripcion"].strip() + bloque_caps
    if seo.get("hashtags"):
        desc += "\n\n" + " ".join("#" + h.lstrip("#") for h in seo["hashtags"][:8])
    if creditos:
        autores = sorted({c["autor"] for c in creditos})
        desc += f"\n\n{CREDITOS_TXT[lang]} ({', '.join(autores)})"

    # SEO del nicho (investigacion/<canal>.seo.json, semanal): se suman después de las etiquetas propias
    nicho = Path(__file__).resolve().parent.parent / "investigacion" / f"{proj.parent.parent.name}.seo.json"
    extra = load_json(nicho).get("tags", []) if nicho.exists() else []
    tags = []
    for t in list(dict.fromkeys(seo.get("tags", []) + extra)):
        if len(",".join(tags + [t])) <= LIMITS["tags_total"]:
            tags.append(t)
    if len(seo["titulo"]) > LIMITS["titulo"]:
        errores.append(f"Título de {len(seo['titulo'])} caracteres (máx 100).")
    if len(desc) > LIMITS["descripcion"]:
        errores.append(f"Descripción de {len(desc)} caracteres (máx 5000).")

    meta = {
        "titulo": seo["titulo"], "descripcion": desc, "tags": tags,
        "categoria_id": seo.get("categoria_id", "27"),  # 27 = Education
        "idioma": lang, "privacidad": seo.get("privacidad", "private"),
        "publicar_en": seo.get("publicar_en"), "lista_id": seo.get("lista_id"),
        "errores": errores,
    }
    save_json(meta, proj / "salida" / "metadata.json")
    print("OK salida/metadata.json")
    for e in errores:
        print("AVISO:", e)


if __name__ == "__main__":
    main()
