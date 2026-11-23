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


MM = {"es": "es-ES", "pt": "pt-BR", "en": "en-US", "ar": "ar-SA", "zh": "zh-CN", "ko": "ko-KR", "it": "it-IT", "fr": "fr-FR"}
APAGADO = set()  # motores que fallaron en esta corrida (Google bloquea a los runners de GitHub: TooManyRequests)


def _trozos(texto, n):
    """Corta en frases sin pasar de n caracteres por trozo (en orden)."""
    import re
    piezas = []
    for f in re.split(r"(?<=[.!?…»\n])\s+", texto):
        piezas += [f[i:i + n] for i in range(0, len(f), n)] or [""]
    out, buf = [], ""
    for f in piezas:
        if buf and len(buf) + len(f) + 1 > n:
            out.append(buf)
            buf = ""
        buf = (buf + " " + f).strip()
    if buf:
        out.append(buf)
    return out


def _google(t, o, d):
    from deep_translator import GoogleTranslator
    tr = GoogleTranslator(source=TR.get(o, o), target=TR.get(d, d))
    return " ".join(tr.translate(x) or "" for x in _trozos(t, 4500))


def _mymemory(t, o, d):
    import requests
    out = []
    for x in _trozos(t, 450):
        r = requests.get("https://api.mymemory.translated.net/get", timeout=30,
                         params={"q": x, "langpair": f"{MM.get(o, o)}|{MM.get(d, d)}", "de": "canales-bot@users.noreply.github.com"})
        j = r.json()
        if r.status_code != 200 or int(j.get("responseStatus", 500)) != 200 or "MYMEMORY WARNING" in str(j):
            raise RuntimeError(f"MyMemory {r.status_code}: {str(j.get('responseDetails'))[:120]}")
        out.append(j["responseData"]["translatedText"])
        time.sleep(0.3)
    return " ".join(out)


def _argos(t, o, d):  # offline y sin límite (instalado por producir.yml); pasa por inglés si hace falta
    import argostranslate.translate as at
    cod = {"zh": "zh"}.get(d, d)
    return at.translate(t, o, cod)


def traductor(origen, destino):
    def f(texto):
        if not texto or not texto.strip():
            return texto
        errores = []
        for nombre, motor in (("google", _google), ("mymemory", _mymemory), ("argos", _argos)):
            if nombre in APAGADO:
                continue
            try:
                r = motor(texto, origen, destino)
                if r and r.strip():
                    return r.strip()
            except Exception as ex:
                errores.append(f"{nombre}: {type(ex).__name__}: {str(ex)[:120]}")
                APAGADO.add(nombre)
        raise RuntimeError(f"traducción {origen}->{destino} falló ({' | '.join(errores)})")
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
