"""Traduce un guion a los idiomas extra del canal (orden del Fundador, 23-nov-2026). Gratis, sin clave.

Uso: python traducir.py <proyecto_dir> en pt ar zh ko
- Cada escena sin "texto_<idioma>" recibe la traducción de su "texto" (lo que se narra = el audio).
- seo.localizaciones recibe título y descripción traducidos (YouTube los muestra según el idioma del espectador).
- No pisa lo que ya escribió Claude o el Fundador. El idioma propio del guion se salta.
- Si el traductor falla, ese idioma se omite con un AVISO (el video sale igual).
"""
import json
import sys
import time
from pathlib import Path

# idioma del canal → código del traductor y de YouTube
TR = {"en": "en", "pt": "pt", "ar": "ar", "zh": "zh-CN", "ko": "ko", "es": "es", "it": "it", "fr": "fr"}
YT = {"zh": "zh-Hans"}


def traductor(origen, destino):
    from deep_translator import GoogleTranslator
    t = GoogleTranslator(source=TR.get(origen, origen), target=TR.get(destino, destino))

    def f(texto):
        if not texto or not texto.strip():
            return texto
        for intento in range(3):
            try:
                partes, buf = [], ""
                for p in texto.split("\n"):  # el servicio acepta ~5000 caracteres por llamada
                    if len(buf) + len(p) > 4000:
                        partes.append(buf)
                        buf = ""
                    buf += p + "\n"
                partes.append(buf)
                return "\n".join(t.translate(x.rstrip("\n")) or "" for x in partes if x.strip()).strip()
            except Exception:
                time.sleep(2 + 3 * intento)
        raise RuntimeError(f"traducción {origen}->{destino} falló")
    return f


def main():
    proj = Path(sys.argv[1])
    idiomas = sys.argv[2:]
    gj = proj / "guion.json"
    g = json.loads(gj.read_text())
    origen = g["lang"]
    seo = g.setdefault("seo", {})
    locs = seo.setdefault("localizaciones", {}) or {}
    seo["localizaciones"] = locs
    for lang in idiomas:
        if lang == origen:
            continue
        try:
            tr = traductor(origen, lang)
            for e in g["escenas"]:
                if e.get("texto") and not e.get(f"texto_{lang}"):
                    e[f"texto_{lang}"] = tr(e["texto"])
            code = YT.get(lang, lang)
            if code not in locs:
                titulo = seo.get("titulo", "")
                sufijo = " #shorts" if "#shorts" in titulo.lower() else ""
                base = titulo.replace("#shorts", "").replace("#Shorts", "").strip()
                t = (tr(base) + sufijo).strip()
                locs[code] = {"title": t[:100], "description": tr(seo.get("descripcion", ""))[:4800]}
            print(f"OK {lang}")
        except Exception as ex:
            print(f"AVISO: idioma {lang} omitido ({ex})", flush=True)
    gj.write_text(json.dumps(g, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
