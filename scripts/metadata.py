"""Arma metadatos finales de YouTube y valida límites.

Uso: python metadata.py <proyecto_dir>
Combina guion.json["seo"] + salida/capitulos.json + creditos.json -> salida/metadata.json
"""
import json
import sys
from pathlib import Path

from common import load_json, save_json, ts

LIMITS = {"titulo": 100, "descripcion": 5000, "tags_total": 500}
GEO_TXT = {"es": {"resumen": "En resumen", "preguntas": "Preguntas que responde este video", "refs": "Referencias"},
           "pt": {"resumen": "Em resumo", "preguntas": "Perguntas que este vídeo responde", "refs": "Referências"},
           "en": {"resumen": "In short", "preguntas": "Questions this video answers", "refs": "References"},
           "it": {"resumen": "In breve", "preguntas": "Domande a cui risponde questo video", "refs": "Riferimenti"}}
CREDITOS_TXT = {"es": "Imágenes y videos", "pt": "Imagens e vídeos", "en": "Images and footage", "fr": "Images et vidéos", "it": "Immagini e video"}
CAP_TXT = {"es": "Capítulos", "pt": "Capítulos", "en": "Chapters", "fr": "Chapitres", "it": "Capitoli"}


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

    # GEO (generative engine optimization, orden del Fundador 23-nov-2026): respuesta directa arriba,
    # preguntas que responde el video y referencias explícitas, para que buscadores con IA lo entiendan y lo citen.
    G = GEO_TXT.get(lang, GEO_TXT["es"])
    desc = seo["descripcion"].strip()
    # Recorrido completo (MayorDom): cada video nuevo invita a empezar desde la Noche 1, dentro de nuestra lista
    rec = proj.parent.parent / "recorrido.json"
    if rec.exists():
        r = json.loads(rec.read_text())
        if r.get("enlace") and "Recorre todo" not in desc:
            desc = f"▶ Recorre todo MayorDom desde la Noche 1: {r['enlace']}\n\n" + desc
    if seo.get("resumen"):
        desc = f"{G['resumen']}: {seo['resumen'].strip()}\n\n" + desc
    if seo.get("preguntas"):
        desc += f"\n\n{G['preguntas']}:\n" + "\n".join(f"• {q.strip()}" for q in seo["preguntas"][:6])
    refs = list(dict.fromkeys(r.strip() for e in g.get("escenas", []) for r in str(e.get("referencia") or "").split("·") if r.strip()))
    faltan = [r for r in refs if r not in desc]
    if faltan:
        desc += f"\n\n{G['refs']}: " + " · ".join(faltan[:12])
    desc += bloque_caps
    if seo.get("hashtags"):
        desc += "\n\n" + " ".join("#" + h.lstrip("#") for h in seo["hashtags"][:8])
    base_desc = desc  # sin créditos: se usa si hay que acortar
    if creditos:
        lineas = []
        for c in creditos:  # CC BY / BY-SA exigen autor, fuente y licencia
            l = f"{c.get('autor', '')} · {c.get('fuente', 'Pexels')}" + (f" · {c['licencia']}" if c.get("licencia") else "")
            if c.get("licencia") and c.get("url"):
                l += f" · {c['url']}"
            if l not in lineas:
                lineas.append(l)
        desc += f"\n\n{CREDITOS_TXT.get(lang, CREDITOS_TXT['es'])}: " + "; ".join(lineas)

    # SEO del nicho (investigacion/<canal>.seo.json, semanal): se suman después de las etiquetas propias
    nicho = Path(__file__).resolve().parent.parent / "investigacion" / f"{proj.parent.parent.name}.seo.json"
    extra = load_json(nicho).get("tags", []) if nicho.exists() else []
    import re as _re

    def limpia(t):  # YouTube rechaza < > y etiquetas raras; cada etiqueta con espacios cuenta 2 caracteres extra
        t = _re.sub(r"[<>\"#@,]", " ", str(t))
        t = _re.sub(r"[^\w\s\-'.&áéíóúüñÁÉÍÓÚÜÑçãõâêôàèìòù]", "", t)
        return _re.sub(r"\s+", " ", t).strip()[:60]
    tags = []
    total = 0
    for t in list(dict.fromkeys(limpia(x) for x in seo.get("tags", []) + extra)):
        if not t:
            continue
        coste = len(t) + (2 if " " in t else 0) + (1 if tags else 0)
        if total + coste > 480:
            continue
        total += coste
        if len(",".join(tags + [t])) <= LIMITS["tags_total"]:
            tags.append(t)
    if len(seo["titulo"]) > LIMITS["titulo"]:
        errores.append(f"Título de {len(seo['titulo'])} caracteres (máx 100).")
    # YouTube cuenta BYTES (máx 5000): si no cabe, créditos compactos (autor · fuente · licencia, sin URL)
    MAXB = 4900
    if len(desc.encode()) > MAXB and creditos:
        cortos = list(dict.fromkeys(f"{c.get('autor', '')} · {c.get('fuente', 'Pexels')}" + (f" · {c['licencia']}" if c.get("licencia") else "") for c in creditos))
        pie = f"\n\n{CREDITOS_TXT.get(lang, CREDITOS_TXT['es'])}: "
        desc = base_desc + pie
        for i, l in enumerate(cortos):
            sep = "" if i == 0 else "; "
            if len((desc + sep + l).encode()) > MAXB - 4:
                desc += " …"
                break
            desc += sep + l
        errores.append("Descripción larga: créditos compactados para caber en 5000 bytes.")
    if len(desc.encode()) > MAXB:
        desc = desc.encode()[:MAXB].decode(errors="ignore").rstrip()
        errores.append("Descripción recortada a 5000 bytes.")

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
