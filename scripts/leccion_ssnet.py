"""Respaldo de los temas del día (orden del Fundador, 27-nov-2026): si el índice
investigacion/leccion_<año>T<n>.json tiene días sin verificar ("dia": null) en los próximos 10 días, los toma de
ssnet.org (texto oficial de la Guía de Estudio de la Biblia para adultos, en inglés) y guarda la traducción al
español en "dia" + el original en "dia_en" y "fuente_dia". Nunca pisa un día ya verificado (la fuente en español,
escuelasabaticamaestros.com, manda cuando llega primero). Solo títulos; nunca el texto de la lección.
Uso: python scripts/leccion_ssnet.py [--probar]
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MESES = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                     "September", "October", "November", "December"], 1)}
DIAS = "Sunday|Monday|Tuesday|Wednesday|Thursday|Friday"


def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (canales-agent)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def texto(htm):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", htm)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|h\d|li|tr|td|table|section)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return "\n".join(re.sub(r"[ \t ]+", " ", x).strip() for x in t.splitlines())


def parsear(htm, anio):
    """{fecha: titulo_en} de domingo a viernes."""
    t = texto(htm)
    out = {}
    pat = rf"\b({DIAS})\b[^\n]*?\b({'|'.join(MESES)})\s+(\d{{1,2}})\s*\n+\s*([^\n]{{3,120}})"
    for _, mes, dia, tit in re.findall(pat, t):
        m = MESES[mes]
        try:
            f = date(anio, m, int(dia))
        except ValueError:
            continue
        out[str(f)] = tit.strip(" #*")
    return out


def traducir(txt, lang="es"):
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source="en", target=lang).translate(txt).strip()


def main():
    hoy = date.today()
    trimestre = f"{hoy.year}T{(hoy.month - 1) // 3 + 1}"
    p = ROOT / "investigacion" / f"leccion_{trimestre}.json"
    if not p.exists():
        print("sin índice", p.name)
        return
    idx = json.loads(p.read_text())
    faltan = sorted(f for f, v in idx["fechas"].items()
                    if not v.get("dia") and str(hoy) <= f <= str(hoy + timedelta(days=10)))
    if not faltan:
        print("OK: no faltan temas en los próximos 10 días")
        return
    lecciones = sorted({idx["fechas"][f]["leccion"] for f in faltan})
    letra = "abcd"[int(trimestre[-1]) - 1]
    cambios = 0
    for n in lecciones:
        url = f"https://ssnet.org/lessons/{str(hoy.year)[2:]}{letra}/less{n:02d}.html"
        try:
            dias = parsear(bajar(url), hoy.year)
        except Exception as ex:
            print("no se pudo leer", url, str(ex)[:100])
            continue
        print(f"lección {n}: {len(dias)} días en {url}")
        for f, en in sorted(dias.items()):
            print(f"  {f}: {en}")
            v = idx["fechas"].get(f)
            if not v or v.get("dia") or v.get("leccion") != n or "--probar" in sys.argv:
                continue
            try:
                es = traducir(en)
            except Exception as ex:
                print("  traducción falló:", str(ex)[:80])
                continue
            v.update(dia=es, dia_en=en, fuente_dia=f"{url} (título oficial en inglés, traducido)")
            cambios += 1
            print(f"+ {f} · {es}")
        if url not in idx.get("fuentes", []):
            idx.setdefault("fuentes", []).append(url)
    if cambios and "--probar" not in sys.argv:
        p.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    print(f"OK {p.name}: {cambios} días completados desde ssnet.org")


if __name__ == "__main__":
    main()
